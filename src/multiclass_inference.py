# pyright: reportMissingImports=false
"""Multiclass inference pipeline for CAN Bus IDS.

Upgrades the binary detector to five classes:
Normal, DoS, Fuzzy, Gear, RPM

Workflow:
1. Build sequences from each dataset CSV.
2. Score all sequences with DistilBERT anomaly scoring.
3. Train a RandomForest on attack-only engineered features.
4. Predict multiclass labels using threshold + score-range + RF fusion.
5. Save confusion matrix image and a PDF report.
"""

from __future__ import annotations

import gc
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn.functional as F
from matplotlib import pyplot as plt
from reportlab.lib import colors  # pyright: ignore[reportMissingImports]
from reportlab.lib.pagesizes import A4  # pyright: ignore[reportMissingImports]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # pyright: ignore[reportMissingImports]
from reportlab.lib.units import inch  # pyright: ignore[reportMissingImports]
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # pyright: ignore[reportMissingImports]
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm
from transformers import DistilBertConfig, DistilBertForMaskedLM


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

VOCAB_PATH = DATA_DIR / "vocab.json"
MODEL_PATH = MODELS_DIR / "best_model.pt"
THRESHOLD_PATH = MODELS_DIR / "threshold.json"

DATASET_MAP = {
    "DoS": DATA_DIR / "DoS_dataset.csv",
    "Fuzzy": DATA_DIR / "Fuzzy_dataset.csv",
    "Gear": DATA_DIR / "gear_dataset.csv",
    "RPM": DATA_DIR / "RPM_dataset.csv",
    "Normal": DATA_DIR / "normal_traffic.csv",
}

WINDOW_SIZE = 64
MASK_RATIO = 0.15
BATCH_SIZE = 128

PAD_ID = 0
MASK_ID = 1
UNK_ID = 2

CLASS_ORDER = ["Normal", "DoS", "Fuzzy", "Gear", "RPM"]
ATTACK_CLASSES = ["DoS", "Fuzzy", "Gear", "RPM"]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_vocab(path: Path) -> Dict[str, int]:
    ensure_exists(path, "vocab.json")
    vocab = load_json(path)
    return {str(k).lower(): int(v) for k, v in vocab.items()}


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


def load_model(path: Path, vocab_size: int) -> DistilBertForMaskedLM:
    ensure_exists(path, "best_model.pt")
    checkpoint = torch.load(path, map_location=DEVICE, weights_only=False)

    model = build_model(vocab_size)
    model.load_state_dict(checkpoint["model_state"])
    model.to(DEVICE)
    model.eval()
    return model


def normalize_can_id(raw: str) -> str:
    token = str(raw).strip().lower()
    if token.startswith("0x"):
        token = token[2:]
    return token.zfill(4)


def extract_id_series(df_chunk: pd.DataFrame) -> Iterable[str]:
    if "ID" in df_chunk.columns:
        return df_chunk["ID"].astype(str)
    if len(df_chunk.columns) > 1:
        return df_chunk.iloc[:, 1].astype(str)
    return df_chunk.iloc[:, 0].astype(str)


def csv_to_sequences(csv_path: Path, vocab: Dict[str, int]) -> torch.Tensor:
    ensure_exists(csv_path, csv_path.name)

    col_names = [
        "Timestamp", "ID", "DLC", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "Flag"
    ]

    buffer_tokens: List[int] = []
    sequences: List[List[int]] = []

    reader = pd.read_csv(
        csv_path,
        header=None,
        names=col_names,
        chunksize=150_000,
        on_bad_lines="skip",
        dtype=str,
        low_memory=False,
    )

    for chunk in reader:
        ids = extract_id_series(chunk)
        for raw in ids:
            buffer_tokens.append(vocab.get(normalize_can_id(raw), UNK_ID))

            if len(buffer_tokens) >= WINDOW_SIZE:
                sequences.append(buffer_tokens[:WINDOW_SIZE])
                buffer_tokens = buffer_tokens[WINDOW_SIZE:]

    if not sequences:
        raise ValueError(f"No sequences built from {csv_path}")

    return torch.tensor(sequences, dtype=torch.long)


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


def score_batch(model: DistilBertForMaskedLM, batch: torch.Tensor) -> np.ndarray:
    batch = batch.to(DEVICE)
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
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
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


def score_sequences(model: DistilBertForMaskedLM, sequences: torch.Tensor, batch_size: int = BATCH_SIZE) -> np.ndarray:
    loader = DataLoader(TensorDataset(sequences), batch_size=batch_size, shuffle=False)
    all_scores: List[np.ndarray] = []

    for (batch,) in tqdm(loader, desc="Scoring", unit="batch"):
        all_scores.append(score_batch(model, batch))
        del batch
        gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return np.concatenate(all_scores, axis=0)


def build_feature_matrix(sequences: torch.Tensor, scores: np.ndarray) -> np.ndarray:
    seq_np = sequences.cpu().numpy().astype(np.float32)
    mean_token_id = seq_np.mean(axis=1)
    std_token_id = seq_np.std(axis=1)
    unique_token_ratio = np.array([len(np.unique(row)) / row.size for row in seq_np], dtype=np.float32)
    max_token_id = seq_np.max(axis=1)
    min_token_id = seq_np.min(axis=1)

    return np.column_stack(
        [
            scores.astype(np.float32),
            mean_token_id,
            std_token_id,
            unique_token_ratio,
            max_token_id,
            min_token_id,
        ]
    )


def compute_score_ranges(scores_by_label: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    ranges: Dict[str, Dict[str, float]] = {}
    for label in ATTACK_CLASSES:
        arr = scores_by_label[label]
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        low = float(np.percentile(arr, 10))
        high = float(np.percentile(arr, 90))
        ranges[label] = {
            "low": low,
            "high": high,
            "mean": mean,
            "std": std if std > 1e-8 else 1e-8,
        }
    return ranges


def range_based_attack_label(score: float, score_ranges: Dict[str, Dict[str, float]]) -> str:
    matching = [
        label
        for label, params in score_ranges.items()
        if params["low"] <= score <= params["high"]
    ]
    if matching:
        return min(matching, key=lambda lbl: abs(score - score_ranges[lbl]["mean"]))

    return min(score_ranges.keys(), key=lambda lbl: abs(score - score_ranges[lbl]["mean"]))


def range_confidence(score: float, label: str, score_ranges: Dict[str, Dict[str, float]]) -> float:
    params = score_ranges[label]
    dist = abs(score - params["mean"]) / params["std"]
    conf = float(np.exp(-0.5 * dist))
    return max(0.05, min(0.99, conf))


def _classify_attack_from_components(
    score: float,
    feature_vector: np.ndarray,
    threshold: float,
    rf_classifier: RandomForestClassifier,
    score_ranges: Dict[str, Dict[str, float]],
) -> Tuple[str, float]:
    if score <= threshold:
        return "Normal", max(0.5, min(0.99, (threshold - score) / max(threshold, 1e-8)))

    rf_probs = rf_classifier.predict_proba(feature_vector.reshape(1, -1))[0]
    rf_classes = list(rf_classifier.classes_)
    rf_idx = int(np.argmax(rf_probs))
    rf_label = rf_classes[rf_idx]
    rf_conf = float(rf_probs[rf_idx])

    range_label = range_based_attack_label(score, score_ranges)
    range_conf = range_confidence(score, range_label, score_ranges)

    if rf_label == range_label:
        return rf_label, max(rf_conf, range_conf)

    combined_rf = 0.65 * rf_conf
    combined_range = 0.35 * range_conf

    if combined_rf >= combined_range:
        return rf_label, rf_conf
    return range_label, range_conf


def classify_attack_type(
    sequence: Sequence[str] | Sequence[int],
    model: DistilBertForMaskedLM,
    vocab: Dict[str, int],
    threshold: float,
    rf_classifier: RandomForestClassifier,
) -> Dict[str, float | str]:
    """Classify a single sequence into attack type with confidence.

    Returns:
        {"label": "DoS", "confidence": 0.94, "anomaly_score": 0.82}
    """

    if len(sequence) != WINDOW_SIZE:
        raise ValueError(f"Expected sequence length {WINDOW_SIZE}, got {len(sequence)}")

    if sequence and isinstance(sequence[0], str):
        tokenized = [vocab.get(normalize_can_id(item), UNK_ID) for item in sequence]
    else:
        tokenized = [int(item) for item in sequence]

    seq_tensor = torch.tensor([tokenized], dtype=torch.long)
    score = float(score_sequences(model, seq_tensor, batch_size=1)[0])
    features = build_feature_matrix(seq_tensor, np.array([score], dtype=np.float32))[0]

    score_ranges = getattr(rf_classifier, "score_ranges_", None)
    if not score_ranges:
        score_ranges = {label: {"low": threshold, "high": threshold * 2.0, "mean": threshold * 1.2, "std": 0.2} for label in ATTACK_CLASSES}

    label, confidence = _classify_attack_from_components(
        score=score,
        feature_vector=features,
        threshold=threshold,
        rf_classifier=rf_classifier,
        score_ranges=score_ranges,
    )

    return {
        "label": label,
        "confidence": round(float(confidence), 4),
        "anomaly_score": round(score, 4),
    }


def save_multiclass_confusion_matrix(cm: np.ndarray, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_ORDER,
        yticklabels=CLASS_ORDER,
        cbar=True,
        ax=ax,
    )
    ax.set_title("Multiclass Confusion Matrix", fontsize=16)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close(fig)


def generate_multiclass_pdf(
    out_pdf: Path,
    class_counts: Dict[str, int],
    overall_accuracy: float,
    macro_f1: float,
    cm_path: Path,
    per_class_rows: List[List[str]],
) -> None:
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, title="CAN IDS Multiclass Report")
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MulticlassTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        spaceAfter=16,
    )
    body_style = ParagraphStyle(
        "MulticlassBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
    )

    story: List = []

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("CAN Bus IDS - Multiclass Attack Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 0.2 * inch))

    summary_table = Table(
        [
            ["Metric", "Value"],
            ["Overall Accuracy", f"{overall_accuracy:.4f}"],
            ["Macro F1", f"{macro_f1:.4f}"],
            ["Classes", ", ".join(CLASS_ORDER)],
            ["Counts", ", ".join(f"{k}:{v}" for k, v in class_counts.items())],
        ],
        colWidths=[2.2 * inch, 4.6 * inch],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.28 * inch))

    story.append(Image(str(cm_path), width=6.5 * inch, height=4.3 * inch))
    story.append(Spacer(1, 0.25 * inch))

    metrics_table = Table([ ["Class", "Precision", "Recall", "F1", "Support"] ] + per_class_rows)
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#eef2ff")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(metrics_table)

    doc.build(story)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    vocab = load_vocab(VOCAB_PATH)
    threshold = float(load_json(THRESHOLD_PATH)["threshold"])
    model = load_model(MODEL_PATH, vocab_size=len(vocab))

    print("=" * 76)
    print("CAN Bus IDS - Multiclass Inference")
    print("=" * 76)
    print(f"Device: {DEVICE}")
    print(f"Threshold: {threshold:.6f}")

    sequences_by_label: Dict[str, torch.Tensor] = {}
    scores_by_label: Dict[str, np.ndarray] = {}
    features_by_label: Dict[str, np.ndarray] = {}

    for label in CLASS_ORDER:
        csv_path = DATASET_MAP[label]
        print(f"\nLoading {label} sequences from {csv_path.name}...")
        seq = csv_to_sequences(csv_path, vocab)
        print(f"  {label} sequences: {len(seq):,}")

        print(f"Scoring {label} sequences...")
        scores = score_sequences(model, seq, batch_size=BATCH_SIZE)

        sequences_by_label[label] = seq
        scores_by_label[label] = scores
        features_by_label[label] = build_feature_matrix(seq, scores)

    print("\nTraining RandomForestClassifier for attack-type identification...")
    attack_X = np.concatenate([features_by_label[label] for label in ATTACK_CLASSES], axis=0)
    attack_y = np.concatenate([
        np.full(len(features_by_label[label]), label, dtype=object) for label in ATTACK_CLASSES
    ])

    rf_classifier = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    rf_classifier.fit(attack_X, attack_y)

    score_ranges = compute_score_ranges(scores_by_label)
    rf_classifier.score_ranges_ = score_ranges
    rf_classifier.class_labels_ = ATTACK_CLASSES

    model_out_path = MODELS_DIR / "attack_classifier.pkl"
    joblib.dump(rf_classifier, model_out_path)

    metadata_out = {
        "created_at": datetime.now().isoformat(),
        "classes": ATTACK_CLASSES,
        "score_ranges": score_ranges,
        "feature_order": [
            "anomaly_score",
            "mean_token_id",
            "std_token_id",
            "unique_token_ratio",
            "max_token_id",
            "min_token_id",
        ],
    }
    with (MODELS_DIR / "attack_classifier_meta.json").open("w", encoding="utf-8") as f:
        json.dump(metadata_out, f, indent=2)

    print(f"Saved attack classifier: {model_out_path}")

    y_true: List[str] = []
    y_pred: List[str] = []

    print("\nRunning multiclass prediction (threshold + ranges + RF)...")
    for label in CLASS_ORDER:
        label_scores = scores_by_label[label]
        label_features = features_by_label[label]

        for idx in range(len(label_scores)):
            score = float(label_scores[idx])
            features = label_features[idx]

            pred, _ = _classify_attack_from_components(
                score=score,
                feature_vector=features,
                threshold=threshold,
                rf_classifier=rf_classifier,
                score_ranges=score_ranges,
            )

            y_true.append(label)
            y_pred.append(pred)

    cm = confusion_matrix(y_true, y_pred, labels=CLASS_ORDER)
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=CLASS_ORDER,
        target_names=CLASS_ORDER,
        output_dict=True,
        zero_division=0,
    )

    overall_accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = float(report_dict["macro avg"]["f1-score"])

    print("\nPer-class Precision / Recall / F1")
    print("-" * 76)
    per_class_rows: List[List[str]] = []
    for cls in CLASS_ORDER:
        row = report_dict[cls]
        per_class_rows.append(
            [
                cls,
                f"{row['precision']:.4f}",
                f"{row['recall']:.4f}",
                f"{row['f1-score']:.4f}",
                str(int(row['support'])),
            ]
        )
        print(
            f"{cls:>6} -> "
            f"Precision={row['precision']:.4f}, "
            f"Recall={row['recall']:.4f}, "
            f"F1={row['f1-score']:.4f}, "
            f"Support={int(row['support'])}"
        )

    print("-" * 76)
    print(f"Overall Accuracy: {overall_accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")

    cm_path = REPORTS_DIR / "multiclass_confusion_matrix.png"
    save_multiclass_confusion_matrix(cm, cm_path)

    pdf_path = REPORTS_DIR / "multiclass_report.pdf"
    class_counts = {label: int(np.sum(np.array(y_true) == label)) for label in CLASS_ORDER}
    generate_multiclass_pdf(
        out_pdf=pdf_path,
        class_counts=class_counts,
        overall_accuracy=overall_accuracy,
        macro_f1=macro_f1,
        cm_path=cm_path,
        per_class_rows=per_class_rows,
    )

    with (REPORTS_DIR / "multiclass_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "class_order": CLASS_ORDER,
                "accuracy": overall_accuracy,
                "macro_f1": macro_f1,
                "classification_report": report_dict,
            },
            f,
            indent=2,
        )

    print("\nSaved outputs:")
    print(f"  Confusion matrix: {cm_path}")
    print(f"  PDF report: {pdf_path}")
    print(f"  Classifier: {model_out_path}")


if __name__ == "__main__":
    main()
