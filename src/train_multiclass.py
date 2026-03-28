"""Train Stage-2 multiclass attack classifier for CAN Bus IDS.

This script trains a lightweight classifier that predicts attack category
(DoS, Fuzzy, Gear, RPM) from a sequence window of CAN IDs.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from backend.config import settings

WINDOW_SIZE = 64
CLASS_LABELS = ("DoS", "Fuzzy", "Gear", "RPM")

DATASET_PATHS = {
    "DoS": settings.PROJECT_ROOT / "data" / "DoS_dataset.csv",
    "Fuzzy": settings.PROJECT_ROOT / "data" / "Fuzzy_dataset.csv",
    "Gear": settings.PROJECT_ROOT / "data" / "gear_dataset.csv",
    "RPM": settings.PROJECT_ROOT / "data" / "RPM_dataset.csv",
}

MODEL_OUTPUT_PATH = settings.MULTICLASS_MODEL_PATH
VECTORIZER_OUTPUT_PATH = settings.MULTICLASS_VECTORIZER_PATH
METRICS_OUTPUT_PATH = settings.PROJECT_ROOT / "reports" / "multiclass_training_metrics.json"

CSV_COLUMN_NAMES = [
    "Timestamp",
    "ID",
    "DLC",
    "D0",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "Flag",
]


def normalize_can_id(raw: str) -> str:
    token = str(raw).strip().lower()
    if token.startswith("0x"):
        token = token[2:]
    return token.zfill(4)


def can_id_to_int(can_id: str) -> int:
    try:
        return int(can_id, 16)
    except ValueError:
        return 0


def iter_can_ids(csv_path: Path, chunk_size: int = 200_000) -> Iterable[str]:
    reader = pd.read_csv(
        csv_path,
        header=None,
        names=CSV_COLUMN_NAMES,
        chunksize=chunk_size,
        on_bad_lines="skip",
        dtype=str,
        low_memory=False,
    )

    for chunk in reader:
        ids = chunk["ID"].fillna("").astype(str)
        for raw in ids:
            can_id = normalize_can_id(raw)
            if can_id:
                yield can_id


def numeric_sequence_features(can_ids: Sequence[str], token_ids: Sequence[int]) -> np.ndarray:
    counts = Counter(can_ids)
    probs = np.array(list(counts.values()), dtype=np.float32)
    probs /= max(float(len(can_ids)), 1.0)

    entropy = float(-np.sum(probs * np.log2(np.clip(probs, 1e-12, 1.0))))
    unique_ratio = float(len(counts) / max(len(can_ids), 1))
    top_ratio = float(max(counts.values()) / max(len(can_ids), 1)) if counts else 0.0

    token_arr = np.asarray(token_ids, dtype=np.float32)
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


def build_windows(
    csv_path: Path,
    max_windows: int,
    stride: int,
    window_size: int = WINDOW_SIZE,
) -> Tuple[List[str], List[np.ndarray]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    docs: List[str] = []
    numeric_features: List[np.ndarray] = []

    rolling_window: Deque[str] = deque(maxlen=window_size)
    seen = 0

    for can_id in iter_can_ids(csv_path):
        rolling_window.append(can_id)
        seen += 1

        if len(rolling_window) < window_size:
            continue

        if (seen - window_size) % stride != 0:
            continue

        ids = list(rolling_window)
        tokens = [can_id_to_int(item) for item in ids]

        docs.append(" ".join(ids))
        numeric_features.append(numeric_sequence_features(ids, tokens))

        if len(docs) >= max_windows:
            break

    if not docs:
        raise ValueError(f"No windows were extracted from {csv_path}")

    return docs, numeric_features


def train_model(
    max_windows_per_class: int,
    stride: int,
    tfidf_max_features: int,
    random_state: int,
) -> None:
    all_docs: List[str] = []
    all_numeric: List[np.ndarray] = []
    all_labels: List[str] = []
    per_class_counts: Dict[str, int] = {}

    print("=" * 78)
    print("Stage-2 Multiclass Training (DoS/Fuzzy/Gear/RPM)")
    print("=" * 78)

    for label in CLASS_LABELS:
        dataset_path = DATASET_PATHS[label]
        print(f"Loading {label} windows from {dataset_path} ...")
        docs, numeric = build_windows(
            csv_path=dataset_path,
            max_windows=max_windows_per_class,
            stride=stride,
        )

        per_class_counts[label] = len(docs)
        all_docs.extend(docs)
        all_numeric.extend(numeric)
        all_labels.extend([label] * len(docs))
        print(f"  -> {len(docs):,} windows ready")

    numeric_matrix = np.vstack(all_numeric).astype(np.float32)

    vectorizer = TfidfVectorizer(
        token_pattern=r"(?u)\b[0-9a-f]{3,8}\b",
        ngram_range=(1, 2),
        max_features=tfidf_max_features,
        lowercase=False,
        sublinear_tf=True,
        dtype=np.float32,
    )

    print("Fitting TF-IDF vectorizer...")
    text_matrix = vectorizer.fit_transform(all_docs)
    feature_matrix = hstack([text_matrix, csr_matrix(numeric_matrix)], format="csr")

    y = np.asarray(all_labels, dtype=object)

    X_train, X_test, y_train, y_test = train_test_split(
        feature_matrix,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    classifier = RandomForestClassifier(
        n_estimators=320,
        max_depth=26,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )

    print("Training classifier...")
    classifier.fit(X_train, y_train)

    preds = classifier.predict(X_test)
    accuracy = float(accuracy_score(y_test, preds))
    report = classification_report(y_test, preds, labels=list(CLASS_LABELS), output_dict=True)

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTORIZER_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(classifier, MODEL_OUTPUT_PATH)
    joblib.dump(vectorizer, VECTORIZER_OUTPUT_PATH)

    metrics_payload = {
        "accuracy": accuracy,
        "class_counts": per_class_counts,
        "window_size": WINDOW_SIZE,
        "stride": stride,
        "max_windows_per_class": max_windows_per_class,
        "tfidf_max_features": tfidf_max_features,
        "classification_report": report,
        "model_path": str(MODEL_OUTPUT_PATH),
        "vectorizer_path": str(VECTORIZER_OUTPUT_PATH),
    }

    with METRICS_OUTPUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(metrics_payload, fp, indent=2)

    print("\nTraining complete")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Model saved to: {MODEL_OUTPUT_PATH}")
    print(f"Vectorizer saved to: {VECTORIZER_OUTPUT_PATH}")
    print(f"Metrics saved to: {METRICS_OUTPUT_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train multiclass CAN attack classifier")
    parser.add_argument("--max-windows-per-class", type=int, default=5000)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--tfidf-max-features", type=int, default=3000)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_windows_per_class < 100:
        raise ValueError("--max-windows-per-class must be at least 100 for stable training")
    if args.stride < 1:
        raise ValueError("--stride must be >= 1")
    if args.tfidf_max_features < 128:
        raise ValueError("--tfidf-max-features must be >= 128")

    train_model(
        max_windows_per_class=args.max_windows_per_class,
        stride=args.stride,
        tfidf_max_features=args.tfidf_max_features,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
