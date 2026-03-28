# pyright: reportMissingImports=false
"""Model evaluation pipeline for CAN Bus IDS.

This script evaluates the trained DistilBERT anomaly detector by scoring:
- 3000 normal sequences from sequences.pt
- 3000 attack sequences built from attack_traffic.csv

Outputs under reports/:
- confusion_matrix.png (dark-themed)
- roc_curve.png
- pr_curve.png
- score_distribution.png
- metrics_summary.png
- model_evaluation_report.pdf
"""

from __future__ import annotations

import gc
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # pyright: ignore[reportMissingImports]
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm
from transformers import DistilBertConfig, DistilBertForMaskedLM


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

VOCAB_PATH = DATA_DIR / "vocab.json"
SEQUENCES_PATH = DATA_DIR / "sequences.pt"
ATTACK_CSV_PATH = DATA_DIR / "attack_traffic.csv"
MODEL_PATH = MODELS_DIR / "best_model.pt"
THRESHOLD_PATH = MODELS_DIR / "threshold.json"

WINDOW_SIZE = 64
MASK_RATIO = 0.15
BATCH_SIZE = 128
NUM_NORMAL = 3000
NUM_ATTACK = 3000

PAD_ID = 0
MASK_ID = 1
UNK_ID = 2

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def seed_everything(seed: int = 42) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ensure_exists(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_vocab(path: Path) -> Dict[str, int]:
    ensure_exists(path, "vocabulary file")
    vocab = load_json(path)
    if not isinstance(vocab, dict):
        raise ValueError("vocab.json must contain an object mapping token->id")
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


def load_model(path: Path, vocab_size: int) -> Tuple[DistilBertForMaskedLM, Dict]:
    ensure_exists(path, "model checkpoint")
    checkpoint = torch.load(path, map_location=DEVICE, weights_only=False)

    model = build_model(vocab_size)
    state_dict = checkpoint.get("model_state")
    if state_dict is None:
        raise KeyError("Checkpoint does not contain 'model_state'")

    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model, checkpoint


def load_threshold(path: Path) -> Dict[str, float]:
    ensure_exists(path, "threshold.json")
    data = load_json(path)
    if "threshold" not in data:
        raise KeyError("threshold.json must contain 'threshold'")
    return data


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


def load_normal_sequences(path: Path, sample_size: int) -> torch.Tensor:
    ensure_exists(path, "normal sequence tensor")
    payload = torch.load(path, map_location="cpu", weights_only=False)

    if isinstance(payload, torch.Tensor):
        sequences = payload
    elif isinstance(payload, dict) and "sequences" in payload:
        sequences = payload["sequences"]
    else:
        raise ValueError("Unsupported sequences.pt format. Expected Tensor or dict with 'sequences'.")

    if not isinstance(sequences, torch.Tensor):
        raise TypeError("Loaded sequences are not a torch.Tensor")
    if sequences.ndim != 2 or sequences.shape[1] != WINDOW_SIZE:
        raise ValueError(f"Expected tensor shape (N, {WINDOW_SIZE}), got {tuple(sequences.shape)}")

    total = sequences.shape[0]
    if total < sample_size:
        raise ValueError(f"Not enough normal sequences in sequences.pt: found {total}, need {sample_size}")

    indices = torch.randperm(total)[:sample_size]
    return sequences[indices].long()


def build_attack_sequences(path: Path, vocab: Dict[str, int], sample_size: int) -> torch.Tensor:
    ensure_exists(path, "attack_traffic.csv")

    col_names = [
        "Timestamp", "ID", "DLC", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "Flag"
    ]

    token_buffer: List[int] = []
    sequences: List[List[int]] = []

    reader = pd.read_csv(
        path,
        header=None,
        names=col_names,
        chunksize=100_000,
        on_bad_lines="skip",
        dtype=str,
        low_memory=False,
    )

    for chunk in reader:
        ids = extract_id_series(chunk)
        for raw_id in ids:
            can_id = normalize_can_id(raw_id)
            token_buffer.append(vocab.get(can_id, UNK_ID))

            if len(token_buffer) >= WINDOW_SIZE:
                sequences.append(token_buffer[:WINDOW_SIZE])
                token_buffer = token_buffer[WINDOW_SIZE:]

            if len(sequences) >= sample_size:
                break

        if len(sequences) >= sample_size:
            break

    if len(sequences) < sample_size:
        raise ValueError(
            f"Not enough attack sequences generated from attack_traffic.csv. "
            f"Generated {len(sequences)}, need {sample_size}."
        )

    return torch.tensor(sequences[:sample_size], dtype=torch.long)


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


def score_sequences(model: DistilBertForMaskedLM, sequences: torch.Tensor, batch_size: int) -> np.ndarray:
    dataset = TensorDataset(sequences)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_scores: List[np.ndarray] = []
    for (batch,) in tqdm(loader, desc="Scoring", unit="batch"):
        batch_scores = score_batch(model, batch)
        all_scores.append(batch_scores)

        del batch
        gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return np.concatenate(all_scores, axis=0)


def compute_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> Dict:
    y_pred = (scores > threshold).astype(np.int32)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel().tolist()

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    specificity = (tn / (tn + fp)) if (tn + fp) else 0.0

    fpr_curve, tpr_curve, _ = roc_curve(y_true, scores)
    precision_curve, recall_curve, _ = precision_recall_curve(y_true, scores)

    auc_score = roc_auc_score(y_true, scores)
    ap_score = average_precision_score(y_true, scores)

    report_text = classification_report(
        y_true,
        y_pred,
        labels=[0, 1],
        target_names=["Normal", "Attack"],
        digits=4,
        zero_division=0,
    )

    return {
        "y_pred": y_pred,
        "cm": cm,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "specificity": float(specificity),
        "auc": float(auc_score),
        "ap": float(ap_score),
        "fpr_curve": fpr_curve,
        "tpr_curve": tpr_curve,
        "precision_curve": precision_curve,
        "recall_curve": recall_curve,
        "report_text": report_text,
    }


def save_confusion_matrix(cm: np.ndarray, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=True,
        xticklabels=["Pred Normal", "Pred Attack"],
        yticklabels=["True Normal", "True Attack"],
        annot_kws={"color": "#e5e7eb", "fontsize": 14, "fontweight": "bold"},
        ax=ax,
    )

    ax.set_title("Confusion Matrix", color="#f8fafc", fontsize=16, pad=12)
    ax.tick_params(colors="#cbd5e1")
    ax.set_xlabel("Predicted", color="#e2e8f0")
    ax.set_ylabel("Actual", color="#e2e8f0")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)


def save_roc_curve(fpr: np.ndarray, tpr: np.ndarray, auc_score: float, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color="#2563eb", linewidth=2.5, label=f"ROC (AUC={auc_score:.4f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#9ca3af", linewidth=1.5)
    ax.set_title("ROC Curve", fontsize=15)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close(fig)


def save_pr_curve(recall: np.ndarray, precision: np.ndarray, ap_score: float, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(recall, precision, color="#0f766e", linewidth=2.5, label=f"PR (AP={ap_score:.4f})")
    ax.set_title("Precision-Recall Curve", fontsize=15)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close(fig)


def save_score_distribution(normal_scores: np.ndarray, attack_scores: np.ndarray, threshold: float, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(normal_scores, bins=45, alpha=0.7, color="#2563eb", label="Normal", density=True)
    ax.hist(attack_scores, bins=45, alpha=0.65, color="#dc2626", label="Attack", density=True)
    ax.axvline(threshold, color="#f97316", linestyle="--", linewidth=2.2, label=f"Threshold={threshold:.4f}")
    ax.set_title("Anomaly Score Distribution", fontsize=15)
    ax.set_xlabel("Anomaly Score")
    ax.set_ylabel("Density")
    ax.grid(alpha=0.22)
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close(fig)


def save_metrics_summary(metrics: Dict[str, float], out_path: Path) -> None:
    labels = ["Accuracy", "Precision", "Recall", "F1", "Specificity", "AUC", "AP"]
    values = [
        metrics["accuracy"],
        metrics["precision"],
        metrics["recall"],
        metrics["f1"],
        metrics["specificity"],
        metrics["auc"],
        metrics["ap"],
    ]

    colors_list = ["#1d4ed8", "#2563eb", "#0f766e", "#16a34a", "#4f46e5", "#dc2626", "#f59e0b"]

    fig, ax = plt.subplots(figsize=(9, 5.8))
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors_list, alpha=0.9)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score")
    ax.set_title("Metrics Summary", fontsize=15)
    ax.grid(axis="x", alpha=0.2)

    for idx, bar in enumerate(bars):
        ax.text(values[idx] + 0.01, bar.get_y() + bar.get_height() / 2, f"{values[idx]:.4f}", va="center")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close(fig)


def _summary_conclusion(metrics: Dict[str, float], threshold: float) -> str:
    quality = "strong"
    if metrics["f1"] < 0.8 or metrics["auc"] < 0.85:
        quality = "moderate"
    if metrics["f1"] < 0.65 or metrics["auc"] < 0.75:
        quality = "limited"

    return (
        f"The DistilBERT-based CAN IDS demonstrates {quality} detection performance under the "
        f"selected threshold ({threshold:.4f}). The anomaly score distributions indicate separation "
        "between normal and attack traffic, while ROC and PR trends confirm ranking quality for "
        "attack detection. Threshold calibration and periodic retraining are recommended for long-term "
        "deployment stability as vehicle traffic profiles evolve."
    )


def generate_pdf_report(
    output_pdf: Path,
    model_info: Dict[str, str],
    metrics: Dict[str, float],
    chart_paths: Dict[str, Path],
) -> None:
    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4, title="CAN Bus IDS Model Evaluation")
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        leading=18,
    )
    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
    )

    story: List = []

    # Title page
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("CAN Bus Intrusion Detection System", title_style))
    story.append(Paragraph("Model Evaluation Report", title_style))
    story.append(Spacer(1, 0.25 * inch))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            "Architecture: DistilBERT (4 layers, 4 heads, dim=256)",
            subtitle_style,
        )
    )
    story.append(PageBreak())

    # Model info table
    story.append(Paragraph("Model Information", heading_style))
    model_rows = [["Field", "Value"]] + [[k, str(v)] for k, v in model_info.items()]
    model_table = Table(model_rows, colWidths=[2.2 * inch, 4.8 * inch])
    model_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(model_table)
    story.append(Spacer(1, 0.3 * inch))

    # Metrics table
    story.append(Paragraph("Evaluation Metrics", heading_style))
    metric_rows = [
        ["Metric", "Value"],
        ["Accuracy", f"{metrics['accuracy']:.4f}"],
        ["Precision", f"{metrics['precision']:.4f}"],
        ["Recall", f"{metrics['recall']:.4f}"],
        ["F1", f"{metrics['f1']:.4f}"],
        ["Specificity", f"{metrics['specificity']:.4f}"],
        ["AUC", f"{metrics['auc']:.4f}"],
        ["AP", f"{metrics['ap']:.4f}"],
    ]
    metric_table = Table(metric_rows, colWidths=[2.2 * inch, 2.1 * inch])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#eff6ff")),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(metric_table)
    story.append(PageBreak())

    chart_titles = [
        ("Confusion Matrix", "confusion_matrix"),
        ("ROC Curve", "roc_curve"),
        ("Precision-Recall Curve", "pr_curve"),
        ("Score Distribution", "score_distribution"),
        ("Metrics Summary", "metrics_summary"),
    ]

    for idx, (title, key) in enumerate(chart_titles):
        story.append(Paragraph(title, heading_style))
        chart_path = chart_paths[key]
        story.append(Image(str(chart_path), width=6.7 * inch, height=4.1 * inch))
        if idx != len(chart_titles) - 1:
            story.append(PageBreak())

    story.append(PageBreak())
    story.append(Paragraph("Summary Conclusion", heading_style))
    story.append(Paragraph(_summary_conclusion(metrics, float(model_info["Threshold"])), body_style))

    doc.build(story)


def main() -> None:
    seed_everything(42)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("CAN Bus IDS - Model Evaluation")
    print("=" * 76)
    print(f"Device: {DEVICE}")

    vocab = load_vocab(VOCAB_PATH)
    threshold_data = load_threshold(THRESHOLD_PATH)
    threshold = float(threshold_data["threshold"])

    model, checkpoint = load_model(MODEL_PATH, vocab_size=len(vocab))

    print("Loading normal and attack samples...")
    normal_sequences = load_normal_sequences(SEQUENCES_PATH, NUM_NORMAL)
    attack_sequences = build_attack_sequences(ATTACK_CSV_PATH, vocab, NUM_ATTACK)

    print(f"Normal sample shape: {tuple(normal_sequences.shape)}")
    print(f"Attack sample shape: {tuple(attack_sequences.shape)}")

    print("Scoring normal sequences...")
    normal_scores = score_sequences(model, normal_sequences, BATCH_SIZE)

    print("Scoring attack sequences...")
    attack_scores = score_sequences(model, attack_sequences, BATCH_SIZE)

    all_scores = np.concatenate([normal_scores, attack_scores])
    y_true = np.concatenate([
        np.zeros(len(normal_scores), dtype=np.int32),
        np.ones(len(attack_scores), dtype=np.int32),
    ])

    metrics = compute_metrics(y_true=y_true, scores=all_scores, threshold=threshold)

    print("\nClassification Report")
    print("-" * 76)
    print(metrics["report_text"])
    print("-" * 76)
    print(
        "Exact metrics: "
        f"Accuracy={metrics['accuracy']:.6f}, "
        f"Precision={metrics['precision']:.6f}, "
        f"Recall={metrics['recall']:.6f}, "
        f"F1={metrics['f1']:.6f}, "
        f"Specificity={metrics['specificity']:.6f}, "
        f"AUC={metrics['auc']:.6f}, "
        f"AP={metrics['ap']:.6f}"
    )

    chart_paths = {
        "confusion_matrix": REPORTS_DIR / "confusion_matrix.png",
        "roc_curve": REPORTS_DIR / "roc_curve.png",
        "pr_curve": REPORTS_DIR / "pr_curve.png",
        "score_distribution": REPORTS_DIR / "score_distribution.png",
        "metrics_summary": REPORTS_DIR / "metrics_summary.png",
    }

    save_confusion_matrix(metrics["cm"], chart_paths["confusion_matrix"])
    save_roc_curve(metrics["fpr_curve"], metrics["tpr_curve"], metrics["auc"], chart_paths["roc_curve"])
    save_pr_curve(metrics["recall_curve"], metrics["precision_curve"], metrics["ap"], chart_paths["pr_curve"])
    save_score_distribution(normal_scores, attack_scores, threshold, chart_paths["score_distribution"])
    save_metrics_summary(metrics, chart_paths["metrics_summary"])

    model_info = {
        "Project": "CAN Bus Intrusion Detection System",
        "Architecture": "DistilBERT (4 layers, 4 heads, dim=256)",
        "Checkpoint Epoch": str(checkpoint.get("epoch", "N/A")),
        "Validation Loss": f"{float(checkpoint.get('val_loss', float('nan'))):.6f}",
        "Threshold": f"{threshold:.6f}",
        "Threshold Percentile": str(threshold_data.get("percentile", "N/A")),
        "Masking Ratio": f"{MASK_RATIO:.2f}",
        "Normal Samples": str(NUM_NORMAL),
        "Attack Samples": str(NUM_ATTACK),
        "Device": str(DEVICE),
    }

    pdf_path = REPORTS_DIR / "model_evaluation_report.pdf"
    generate_pdf_report(pdf_path, model_info, metrics, chart_paths)

    # Persist a frontend-friendly metrics file.
    metrics_json_path = REPORTS_DIR / "metrics.json"
    metrics_payload = {
        "generated_at": datetime.now().isoformat(),
        "threshold": threshold,
        "threshold_info": threshold_data,
        "samples": {"normal": NUM_NORMAL, "attack": NUM_ATTACK},
        "metrics": {
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "specificity": metrics["specificity"],
            "auc": metrics["auc"],
            "ap": metrics["ap"],
            "tn": metrics["tn"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "tp": metrics["tp"],
        },
    }
    with metrics_json_path.open("w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("\nSaved outputs:")
    for key, value in chart_paths.items():
        print(f"  {key}: {value}")
    print(f"  pdf: {pdf_path}")
    print(f"  metrics_json: {metrics_json_path}")


if __name__ == "__main__":
    main()
