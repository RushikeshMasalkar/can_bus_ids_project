"""Stage-2 multiclass inference for CAN Bus IDS.

This module loads the trained classifier artifacts and predicts
one of: DoS, Fuzzy, Gear, RPM.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional, Sequence, Tuple

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

from backend.config import settings

MULTICLASS_MODEL_PATH = settings.MULTICLASS_MODEL_PATH
VECTORIZER_PATH = settings.MULTICLASS_VECTORIZER_PATH

_model = None
_vectorizer = None
_artifacts_checked = False
_warned_missing = False


def normalize_can_id(raw: str) -> str:
    token = str(raw).strip().lower()
    if token.startswith("0x"):
        token = token[2:]
    return token.zfill(4)


def token_to_hex(token: int) -> str:
    return format(int(token), "04x")


def _numeric_sequence_features(sequence_of_tokens: Sequence[int], raw_can_ids: Sequence[str]) -> np.ndarray:
    clean_ids = [normalize_can_id(item) for item in raw_can_ids]
    counts = Counter(clean_ids)
    probs = np.array(list(counts.values()), dtype=np.float32)
    probs /= max(float(len(clean_ids)), 1.0)

    entropy = float(-np.sum(probs * np.log2(np.clip(probs, 1e-12, 1.0)))) if probs.size else 0.0
    unique_ratio = float(len(counts) / max(len(clean_ids), 1))
    top_ratio = float(max(counts.values()) / max(len(clean_ids), 1)) if counts else 0.0

    token_arr = np.asarray(sequence_of_tokens, dtype=np.float32)
    mean_token = float(token_arr.mean()) if token_arr.size else 0.0
    std_token = float(token_arr.std()) if token_arr.size else 0.0
    repeat_ratio = float(1.0 - unique_ratio)

    return np.array(
        [
            unique_ratio,
            top_ratio,
            entropy,
            mean_token,
            std_token,
            repeat_ratio,
        ],
        dtype=np.float32,
    )


def _load_artifacts() -> Tuple[Optional[object], Optional[object]]:
    global _model, _vectorizer, _artifacts_checked, _warned_missing

    if _artifacts_checked:
        return _model, _vectorizer

    _artifacts_checked = True

    if not MULTICLASS_MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        if not _warned_missing:
            print(
                "Multiclass artifacts missing. "
                f"Expected {MULTICLASS_MODEL_PATH} and {VECTORIZER_PATH}."
            )
            _warned_missing = True
        return None, None

    try:
        _model = joblib.load(MULTICLASS_MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
    except Exception as exc:
        if not _warned_missing:
            print(f"Failed to load multiclass artifacts: {exc}")
            _warned_missing = True
        _model = None
        _vectorizer = None

    return _model, _vectorizer


def predict_attack_type(sequence_of_tokens: Sequence[int], raw_can_ids: Sequence[str]) -> str:
    """Predict Stage-2 attack label from an anomalous CAN sequence.

    Returns one of "DoS", "Fuzzy", "Gear", "RPM" when artifacts are available.
    Returns "Unknown" if model/vectorizer artifacts are not available or prediction fails.
    """

    if not sequence_of_tokens and not raw_can_ids:
        return "Unknown"

    model, vectorizer = _load_artifacts()
    if model is None or vectorizer is None:
        return "Unknown"

    try:
        if raw_can_ids:
            normalized_ids = [normalize_can_id(item) for item in raw_can_ids]
        else:
            normalized_ids = [token_to_hex(token) for token in sequence_of_tokens]

        if sequence_of_tokens:
            tokens = [int(token) for token in sequence_of_tokens]
        else:
            tokens = [int(item, 16) for item in normalized_ids]

        text_features = vectorizer.transform([" ".join(normalized_ids)])
        numeric_features = _numeric_sequence_features(tokens, normalized_ids)
        combined = hstack([text_features, csr_matrix(numeric_features.reshape(1, -1))], format="csr")

        prediction = model.predict(combined)[0]
        return str(prediction)
    except Exception:
        return "Unknown"


__all__ = ["predict_attack_type"]
