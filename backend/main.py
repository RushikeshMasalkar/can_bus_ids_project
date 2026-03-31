"""Production-ready FastAPI backend for CAN Bus IDS."""

from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import joblib
import numpy as np
import torch
import torch.nn.functional as F
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from transformers import DistilBertConfig, DistilBertForMaskedLM

from backend.config import settings
from src.multiclass_inference import predict_attack_type


BASE_DIR = settings.PROJECT_ROOT
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

# StaticFiles validates the directory when mounted, so create it at import time.
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VOCAB_PATH = settings.VOCAB_PATH
MODEL_PATH = settings.MODEL_PATH
THRESHOLD_PATH = settings.THRESHOLD_PATH
SEQUENCES_PATH = DATA_DIR / "sequences.pt"
RF_CLASSIFIER_PATH = MODELS_DIR / "attack_classifier.pkl"
RF_META_PATH = MODELS_DIR / "attack_classifier_meta.json"

WINDOW_SIZE = 64
MASK_RATIO = 0.15

PAD_ID = 0
MASK_ID = 1
UNK_ID = 2

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

UVICORN_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": False,
    "log_level": "info",
}


class PredictRequest(BaseModel):
    sequence: List[str] = Field(
        ...,
        min_length=WINDOW_SIZE,
        max_length=WINDOW_SIZE,
        description="List of 64 hex CAN IDs",
    )
    return_details: bool = Field(default=True)

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, value: List[str]) -> List[str]:
        if len(value) != WINDOW_SIZE:
            raise ValueError(f"sequence must contain exactly {WINDOW_SIZE} CAN IDs")
        for item in value:
            if not str(item).strip():
                raise ValueError("sequence entries cannot be empty")
        return value


class PredictResponse(BaseModel):
    anomaly_score: float
    threshold: float
    label: str
    attack_type: Optional[str]
    confidence: float
    is_attack: bool
    processing_time_ms: float
    details: Optional[Dict[str, Any]] = None


class BatchPredictRequest(BaseModel):
    sequences: List[List[str]] = Field(..., min_length=1, max_length=1000)
    return_details: bool = Field(default=False)

    @field_validator("sequences")
    @classmethod
    def validate_sequences(cls, sequences: List[List[str]]) -> List[List[str]]:
        for idx, seq in enumerate(sequences):
            if len(seq) != WINDOW_SIZE:
                raise ValueError(f"sequence at index {idx} must contain exactly {WINDOW_SIZE} CAN IDs")
            if any(not str(item).strip() for item in seq):
                raise ValueError(f"sequence at index {idx} contains empty token")
        return sequences


class BatchPredictResponse(BaseModel):
    total: int
    attacks: int
    normals: int
    average_score: float
    predictions: List[PredictResponse]


class ThresholdUpdateRequest(BaseModel):
    threshold: float = Field(..., gt=0.0, le=20.0)
    persist: bool = Field(default=True)


class StreamConfigUpdateRequest(BaseModel):
    interval_ms: int = Field(..., ge=100, le=5000)


@dataclass
class RuntimeState:
    model: Optional[DistilBertForMaskedLM] = None
    vocab: Dict[str, int] = field(default_factory=dict)
    threshold_data: Dict[str, Any] = field(default_factory=dict)
    rf_classifier: Optional[Any] = None
    rf_meta: Dict[str, Any] = field(default_factory=dict)
    demo_sequences: Optional[torch.Tensor] = None
    demo_index: int = 0
    stream_interval_ms: int = 650
    loaded: bool = False


@dataclass
class DetectionStats:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_analyzed: int = 0
    attacks_detected: int = 0
    normals_detected: int = 0
    score_sum: float = 0.0
    attack_type_counts: Counter = field(default_factory=Counter)
    last_prediction: Dict[str, Any] = field(default_factory=dict)

    def update(self, result: Dict[str, Any]) -> None:
        self.total_analyzed += 1
        self.score_sum += float(result["anomaly_score"])
        if result["is_attack"]:
            self.attacks_detected += 1
            if result.get("attack_type"):
                self.attack_type_counts[result["attack_type"]] += 1
        else:
            self.normals_detected += 1

        self.last_prediction = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "label": result["label"],
            "attack_type": result.get("attack_type"),
            "score": result["anomaly_score"],
            "confidence": result["confidence"],
        }

    def snapshot(self) -> Dict[str, Any]:
        avg_score = self.score_sum / self.total_analyzed if self.total_analyzed else 0.0
        detection_rate = (self.attacks_detected / self.total_analyzed * 100.0) if self.total_analyzed else 0.0
        uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()

        return {
            "total_analyzed": self.total_analyzed,
            "attacks_detected": self.attacks_detected,
            "normals_detected": self.normals_detected,
            "detection_rate": round(detection_rate, 4),
            "average_anomaly_score": round(avg_score, 6),
            "attack_type_breakdown": dict(self.attack_type_counts),
            "last_prediction": self.last_prediction,
            "uptime_seconds": round(uptime, 2),
        }


runtime_state = RuntimeState()
stats_state = DetectionStats()


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_threshold_data(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def normalize_can_id(raw: str) -> str:
    token = str(raw).strip().lower()
    if token.startswith("0x"):
        token = token[2:]
    return token.zfill(4)


def build_model(vocab_size: int) -> DistilBertForMaskedLM:
    config = DistilBertConfig(
        vocab_size=vocab_size,
        max_position_embeddings=WINDOW_SIZE,
        dim=256,
        n_layers=4,
        n_heads=4,
        hidden_dim=1024,
        dropout=0.1,
        attention_dropout=0.1,
        pad_token_id=PAD_ID,
    )
    return DistilBertForMaskedLM(config)


def _load_demo_sequences() -> Optional[torch.Tensor]:
    if not SEQUENCES_PATH.exists():
        return None

    payload = torch.load(SEQUENCES_PATH, map_location="cpu", weights_only=False)
    if isinstance(payload, torch.Tensor):
        seq = payload
    elif isinstance(payload, dict) and "sequences" in payload:
        seq = payload["sequences"]
    else:
        return None

    if seq.ndim != 2 or seq.shape[1] != WINDOW_SIZE:
        return None

    return seq.long()


def load_runtime_assets() -> None:
    ensure_exists(VOCAB_PATH, "vocab.json")
    ensure_exists(MODEL_PATH, "best_model.pt")
    ensure_exists(THRESHOLD_PATH, "threshold.json")

    vocab = load_json(VOCAB_PATH)
    runtime_state.vocab = {str(k).lower(): int(v) for k, v in vocab.items()}

    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
    model = build_model(len(runtime_state.vocab))
    model.load_state_dict(checkpoint["model_state"])
    model.to(DEVICE)
    model.eval()
    runtime_state.model = model

    runtime_state.threshold_data = load_json(THRESHOLD_PATH)

    if RF_CLASSIFIER_PATH.exists():
        runtime_state.rf_classifier = joblib.load(RF_CLASSIFIER_PATH)
    if RF_META_PATH.exists():
        runtime_state.rf_meta = load_json(RF_META_PATH)

    runtime_state.demo_sequences = _load_demo_sequences()
    runtime_state.demo_index = 0
    runtime_state.loaded = True


def _ensure_at_least_one_mask(masked_indices: torch.Tensor, special: torch.Tensor) -> torch.Tensor:
    rows = torch.where(masked_indices.sum(dim=1) == 0)[0]
    if rows.numel() == 0:
        return masked_indices

    for row in rows.tolist():
        candidates = torch.where(~special[row])[0]
        if candidates.numel() == 0:
            candidates = torch.arange(masked_indices.shape[1], device=masked_indices.device)
        pick = candidates[torch.randint(0, candidates.numel(), (1,), device=masked_indices.device)]
        masked_indices[row, pick] = True

    return masked_indices


def score_token_tensor(token_tensor: torch.Tensor) -> np.ndarray:
    if runtime_state.model is None:
        raise RuntimeError("Model is not loaded")

    batch = token_tensor.to(DEVICE)
    bsz, seq_len = batch.shape

    input_ids = batch.clone()
    labels = torch.full((bsz, seq_len), -100, dtype=torch.long, device=DEVICE)

    mask_prob = torch.rand((bsz, seq_len), device=DEVICE)
    masked_indices = mask_prob < MASK_RATIO

    special = (batch == PAD_ID) | (batch == MASK_ID) | (batch == UNK_ID)
    masked_indices = masked_indices & ~special
    masked_indices = _ensure_at_least_one_mask(masked_indices, special)

    labels[masked_indices] = batch[masked_indices]
    input_ids[masked_indices] = MASK_ID

    attention_mask = torch.ones((bsz, seq_len), dtype=torch.long, device=DEVICE)

    with torch.no_grad():
        outputs = runtime_state.model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        logits = outputs.logits
        loss_per_pos = F.cross_entropy(
            logits.view(-1, logits.size(-1)),
            labels.view(-1),
            ignore_index=-100,
            reduction="none",
        ).view(bsz, seq_len)

        mask_counts = (labels != -100).sum(dim=1).clamp(min=1)
        scores = loss_per_pos.sum(dim=1) / mask_counts

    return scores.detach().cpu().numpy()


def tokenize_sequence(sequence: Sequence[str]) -> Tuple[List[int], int]:
    if not runtime_state.vocab:
        raise RuntimeError("Vocabulary not loaded")

    tokens: List[int] = []
    unknown = 0

    for item in sequence:
        can_id = normalize_can_id(str(item))
        token = runtime_state.vocab.get(can_id, UNK_ID)
        if token == UNK_ID:
            unknown += 1
        tokens.append(token)

    return tokens, unknown


def _feature_vector(tokens: Sequence[int], anomaly_score: float) -> np.ndarray:
    arr = np.asarray(tokens, dtype=np.float32)
    unique_ratio = float(len(np.unique(arr)) / max(len(arr), 1))
    return np.array(
        [
            float(anomaly_score),
            float(np.mean(arr)),
            float(np.std(arr)),
            unique_ratio,
            float(np.max(arr)),
            float(np.min(arr)),
        ],
        dtype=np.float32,
    )


def _range_based_label(score: float, score_ranges: Dict[str, Dict[str, float]]) -> str:
    candidates = [
        label
        for label, params in score_ranges.items()
        if float(params["low"]) <= score <= float(params["high"])
    ]

    if candidates:
        return min(candidates, key=lambda lbl: abs(score - float(score_ranges[lbl]["mean"])))

    return min(score_ranges.keys(), key=lambda lbl: abs(score - float(score_ranges[lbl]["mean"])))


def classify_attack(score: float, tokens: Sequence[int], threshold: float) -> Tuple[Optional[str], float]:
    if score <= threshold:
        confidence = max(0.5, min(0.99, (threshold - score) / max(threshold, 1e-8)))
        return None, float(confidence)

    rf_classifier = runtime_state.rf_classifier
    score_ranges = getattr(rf_classifier, "score_ranges_", {}) if rf_classifier is not None else {}

    if rf_classifier is not None:
        features = _feature_vector(tokens, score)
        probs = rf_classifier.predict_proba(features.reshape(1, -1))[0]
        classes = list(rf_classifier.classes_)
        top_idx = int(np.argmax(probs))
        rf_label = str(classes[top_idx])
        rf_conf = float(probs[top_idx])

        if score_ranges:
            range_label = _range_based_label(score, score_ranges)
            range_mean = float(score_ranges[range_label]["mean"])
            range_std = max(float(score_ranges[range_label]["std"]), 1e-8)
            range_conf = float(np.exp(-0.5 * abs(score - range_mean) / range_std))

            if rf_label == range_label:
                return rf_label, float(max(rf_conf, range_conf))

            if 0.65 * rf_conf >= 0.35 * range_conf:
                return rf_label, rf_conf
            return range_label, range_conf

        return rf_label, rf_conf

    # Fallback heuristic when RF model is unavailable.
    delta = score - threshold
    if delta > threshold * 0.9:
        label = "DoS"
    elif delta > threshold * 0.6:
        label = "Fuzzy"
    elif delta > threshold * 0.35:
        label = "Gear"
    else:
        label = "RPM"

    confidence = min(0.99, 0.55 + delta / max(threshold, 1e-8) * 0.35)
    return label, float(confidence)


def predict_from_tokens(tokens: Sequence[int], unknown_count: int, return_details: bool) -> Dict[str, Any]:
    start = time.perf_counter()
    threshold = float(runtime_state.threshold_data.get("threshold", 0.0))

    token_tensor = torch.tensor([tokens], dtype=torch.long)
    anomaly_score = float(score_token_tensor(token_tensor)[0])

    attack_type, confidence = classify_attack(anomaly_score, tokens, threshold)
    is_attack = anomaly_score > threshold
    label = "ATTACK" if is_attack else "NORMAL"

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    details = None
    if return_details:
        details = {
            "unknown_tokens": int(unknown_count),
            "unknown_ratio": round(unknown_count / WINDOW_SIZE, 6),
            "score_margin": round(anomaly_score - threshold, 6),
            "device": str(DEVICE),
        }

    result = {
        "anomaly_score": round(anomaly_score, 6),
        "threshold": round(threshold, 6),
        "label": label,
        "attack_type": attack_type,
        "confidence": round(float(confidence), 4),
        "is_attack": bool(is_attack),
        "processing_time_ms": round(elapsed_ms, 3),
        "details": details,
    }
    return result


def get_next_demo_tokens() -> List[int]:
    if runtime_state.demo_sequences is not None and len(runtime_state.demo_sequences) > 0:
        idx = runtime_state.demo_index % len(runtime_state.demo_sequences)
        runtime_state.demo_index += 1
        return runtime_state.demo_sequences[idx].tolist()

    vocab_values = [value for value in runtime_state.vocab.values() if value > UNK_ID]
    if not vocab_values:
        return [UNK_ID] * WINDOW_SIZE

    sampled = np.random.choice(vocab_values, size=WINDOW_SIZE, replace=True)
    return sampled.astype(np.int64).tolist()


def decode_tokens_to_can_ids(tokens: Sequence[int]) -> List[str]:
    reverse_vocab = {int(value): str(can_id) for can_id, value in runtime_state.vocab.items()}
    decoded: List[str] = []

    for token in tokens:
        token_int = int(token)
        decoded.append(reverse_vocab.get(token_int, format(token_int, "04x")))

    return decoded


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        load_runtime_assets()
    except FileNotFoundError as exc:
        runtime_state.loaded = False
        runtime_state.model = None
        runtime_state.vocab = {}
        runtime_state.threshold_data = {}
        runtime_state.rf_classifier = None
        runtime_state.rf_meta = {}
        runtime_state.demo_sequences = None
        runtime_state.demo_index = 0
        print(f"Backend startup warning: {exc}")
    except Exception as exc:  # pragma: no cover - startup hard failure path
        raise RuntimeError(f"Backend startup failed: {exc}") from exc

    yield

    if runtime_state.model is not None:
        del runtime_state.model
        runtime_state.model = None

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="CAN Bus IDS Backend",
    version="1.0.0",
    description="FastAPI backend for DistilBERT CAN bus intrusion detection",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/reports", StaticFiles(directory=str(REPORTS_DIR)), name="static-reports")


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "status": "online",
        "project": "CAN Bus Intrusion Detection System",
        "model": "loaded" if runtime_state.loaded else "not_loaded",
        "device": str(DEVICE),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")

    return {
        "status": "online",
        "model": "loaded",
        "device": str(DEVICE),
    }


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")
    return stats_state.snapshot()


@app.get("/threshold")
async def get_threshold() -> Dict[str, Any]:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")
    return runtime_state.threshold_data


@app.post("/threshold")
async def update_threshold(payload: ThresholdUpdateRequest) -> Dict[str, Any]:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")

    runtime_state.threshold_data["threshold"] = float(payload.threshold)
    runtime_state.threshold_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    if payload.persist:
        try:
            save_threshold_data(THRESHOLD_PATH, runtime_state.threshold_data)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist threshold: {exc}",
            ) from exc

    return {
        "threshold": runtime_state.threshold_data["threshold"],
        "persisted": payload.persist,
        "threshold_data": runtime_state.threshold_data,
    }


@app.get("/stream/config")
async def get_stream_config() -> Dict[str, Any]:
    return {
        "interval_ms": runtime_state.stream_interval_ms,
        "frames_per_second": round(1000.0 / runtime_state.stream_interval_ms, 3),
    }


@app.post("/stream/config")
async def update_stream_config(payload: StreamConfigUpdateRequest) -> Dict[str, Any]:
    runtime_state.stream_interval_ms = int(payload.interval_ms)
    return {
        "interval_ms": runtime_state.stream_interval_ms,
        "frames_per_second": round(1000.0 / runtime_state.stream_interval_ms, 3),
    }


@app.get("/vocab/size")
async def get_vocab_size() -> Dict[str, int]:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")
    return {"vocab_size": len(runtime_state.vocab)}


@app.get("/reports/manifest")
async def get_reports_manifest() -> Dict[str, Any]:
    expected = [
        "confusion_matrix.png",
        "roc_curve.png",
        "pr_curve.png",
        "score_distribution.png",
        "metrics_summary.png",
        "model_evaluation_report.pdf",
        "multiclass_confusion_matrix.png",
        "multiclass_report.pdf",
    ]

    available = []
    for name in expected:
        path = REPORTS_DIR / name
        if path.exists():
            available.append(
                {
                    "name": name,
                    "url": f"/static/reports/{name}",
                    "size_bytes": path.stat().st_size,
                }
            )

    metrics = {}
    metrics_path = REPORTS_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = load_json(metrics_path)

    multiclass_metrics = {}
    multiclass_path = REPORTS_DIR / "multiclass_metrics.json"
    if multiclass_path.exists():
        multiclass_metrics = load_json(multiclass_path)

    return {
        "available_files": available,
        "metrics": metrics,
        "multiclass_metrics": multiclass_metrics,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest) -> PredictResponse:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")

    try:
        tokens, unknown_count = tokenize_sequence(payload.sequence)
        result = predict_from_tokens(tokens, unknown_count, payload.return_details)
        stats_state.update(result)
        return PredictResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(payload: BatchPredictRequest) -> BatchPredictResponse:
    if not runtime_state.loaded:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")

    predictions: List[PredictResponse] = []

    try:
        for sequence in payload.sequences:
            tokens, unknown_count = tokenize_sequence(sequence)
            result = predict_from_tokens(tokens, unknown_count, payload.return_details)
            stats_state.update(result)
            predictions.append(PredictResponse(**result))

        attacks = sum(1 for item in predictions if item.is_attack)
        normals = len(predictions) - attacks
        average_score = float(np.mean([item.anomaly_score for item in predictions])) if predictions else 0.0

        return BatchPredictResponse(
            total=len(predictions),
            attacks=attacks,
            normals=normals,
            average_score=round(average_score, 6),
            predictions=predictions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            tokens = get_next_demo_tokens()
            unknown_count = int(np.sum(np.asarray(tokens) == UNK_ID))
            result = predict_from_tokens(tokens, unknown_count, return_details=False)

            if result["is_attack"]:
                raw_can_ids = decode_tokens_to_can_ids(tokens)
                result["attack_type"] = predict_attack_type(tokens, raw_can_ids)
            else:
                result["attack_type"] = None

            stats_state.update(result)

            payload = {
                "score": result["anomaly_score"],
                "is_attack": result["is_attack"],
                "label": result["label"],
                "attack_type": result["attack_type"],
                "confidence": result["confidence"],
                "threshold": result["threshold"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(runtime_state.stream_interval_ms / 1000.0)
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"error": str(exc)})
            await websocket.close(code=1011)
        except Exception:
            return


@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})


if __name__ == "__main__":
    uvicorn.run("backend.main:app", **UVICORN_CONFIG)
