# src/evaluate.py
# Phase 8: Comprehensive Model Evaluation for CAN Bus IDS
# ==============================================================================
# This script evaluates the Transformer-Based Intrusion Detection System (IDS)
# for CAN Bus Networks using DistilBERT's reconstruction loss as anomaly score.
# ==============================================================================

import os
import sys
import json
import gc
import warnings
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertConfig, DistilBertForMaskedLM
from tqdm import tqdm

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ===============================================================================
# CONFIGURATION
# ===============================================================================

# Paths
BASE_DIR       = Path(__file__).resolve().parent.parent
DATA_DIR       = BASE_DIR / "data"
MODELS_DIR     = BASE_DIR / "models"
RESULTS_DIR    = BASE_DIR / "results"
FIGURES_DIR    = RESULTS_DIR / "figures"

VOCAB_PATH     = DATA_DIR / "vocab.json"
MODEL_PATH     = MODELS_DIR / "best_model.pt"
TEST_CSV_PATH  = DATA_DIR / "DoS_dataset.csv"

# Evaluation hyperparameters
WINDOW_SIZE        = 64       # Sliding window size (must match training)
BATCH_SIZE         = 128      # Batch size for inference
THRESHOLD_PERCENTILE = 99     # Percentile for threshold calibration
MASK_RATIO         = 0.15     # MLM mask ratio for scoring

# Special token IDs (must match training)
PAD_ID  = 0
MASK_ID = 1
UNK_ID  = 2

# Device configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ===============================================================================
# UTILITY FUNCTIONS
# ===============================================================================

def print_header(title: str, char: str = "=", width: int = 70) -> None:
    """Print a formatted section header."""
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


def print_subheader(title: str) -> None:
    """Print a formatted sub-section header."""
    print(f"\n{'-' * 50}")
    print(f"  {title}")
    print(f"{'-' * 50}")


def check_file_exists(path: Path, description: str) -> None:
    """Check if a required file exists, exit with error message if not."""
    if not path.exists():
        print(f"\n❌ ERROR: {description} not found!")
        print(f"   Expected path: {path}")
        print(f"   Please ensure the file exists before running evaluation.")
        sys.exit(1)


def format_number(n: int) -> str:
    """Format number with commas for readability."""
    return f"{n:,}"


# ===============================================================================
# STEP 1: LOAD VOCABULARY
# ===============================================================================

def load_vocabulary(vocab_path: Path) -> Dict[str, int]:
    """
    Load the vocabulary mapping from hex CAN IDs to integer tokens.

    Args:
        vocab_path: Path to vocab.json file

    Returns:
        Dictionary mapping hex CAN ID strings to integer token IDs
    """
    print_header("STEP 1: Loading Vocabulary")

    check_file_exists(vocab_path, "Vocabulary file (vocab.json)")

    with open(vocab_path, 'r') as f:
        vocab = json.load(f)

    vocab_size = len(vocab)
    num_special = sum(1 for k in vocab.keys() if k.startswith('['))
    num_can_ids = vocab_size - num_special

    print(f"  [OK] Vocabulary loaded successfully")
    print(f"    * Total tokens    : {vocab_size}")
    print(f"    * Special tokens  : {num_special} ([PAD], [MASK], [UNK])")
    print(f"    * CAN ID tokens   : {num_can_ids}")
    print(f"    * Vocab path      : {vocab_path}")

    return vocab


# ===============================================================================
# STEP 2: LOAD TRAINED MODEL
# ===============================================================================

def load_model(model_path: Path, vocab_size: int) -> DistilBertForMaskedLM:
    """
    Load the trained DistilBERT model for inference.

    Args:
        model_path: Path to best_model.pt checkpoint
        vocab_size: Size of vocabulary for model configuration

    Returns:
        Loaded model in evaluation mode on the appropriate device
    """
    print_header("STEP 2: Loading Trained Model")

    check_file_exists(model_path, "Model checkpoint (best_model.pt)")

    # Load checkpoint
    print(f"  Loading checkpoint from: {model_path}")
    checkpoint = torch.load(model_path, map_location=DEVICE, weights_only=False)

    # Display training metadata
    print(f"  [OK] Checkpoint loaded!")
    print(f"    * Saved at epoch  : {checkpoint.get('epoch', 'N/A')}")
    print(f"    * Best val loss   : {checkpoint.get('val_loss', 'N/A'):.6f}")

    # Reconstruct model architecture (must match training config exactly)
    config = DistilBertConfig(
        vocab_size              = vocab_size,
        max_position_embeddings = WINDOW_SIZE,
        dim                     = 256,
        n_layers                = 4,
        n_heads                 = 4,
        hidden_dim              = 1024,
        dropout                 = 0.1,
        attention_dropout       = 0.1,
        pad_token_id            = PAD_ID,
    )

    model = DistilBertForMaskedLM(config)
    model.load_state_dict(checkpoint['model_state'])
    model = model.to(DEVICE)
    model.eval()  # Set to evaluation mode (disables dropout)

    # Calculate model parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"  [OK] Model loaded and set to eval mode")
    print(f"    * Device          : {DEVICE}")
    print(f"    * Total params    : {format_number(total_params)}")
    print(f"    * Architecture    : DistilBERT (4 layers, 4 heads, dim=256)")

    return model


# ===============================================================================
# STEP 3: LOAD AND PREPROCESS TEST DATA
# ===============================================================================

def load_and_preprocess_test_data(
    csv_path: Path,
    vocab: Dict[str, int],
    window_size: int = WINDOW_SIZE,
    max_sequences: Optional[int] = None
) -> Tuple[torch.Tensor, np.ndarray]:
    """
    Load test CSV, tokenize CAN IDs, create sliding windows, and generate labels.

    A sequence is labeled as ATTACK (1) if ANY frame in the 64-frame window
    has a 'T' (attack) flag. Otherwise, it is labeled as NORMAL (0).

    Args:
        csv_path: Path to DoS_dataset.csv
        vocab: Vocabulary mapping hex CAN IDs to integers
        window_size: Size of sliding window (default: 64)
        max_sequences: Optional limit on number of sequences to process

    Returns:
        Tuple of (sequences_tensor, labels_array)
        - sequences_tensor: Shape (N, window_size) with tokenized CAN IDs
        - labels_array: Shape (N,) with 0=normal, 1=attack
    """
    print_header("STEP 3: Loading and Preprocessing Test Data")

    check_file_exists(csv_path, f"Test dataset ({csv_path.name})")

    # Define column names (CSV has no header)
    col_names = [
        'Timestamp', 'ID', 'DLC',
        'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'Flag'
    ]

    print(f"  Loading CSV: {csv_path.name}")
    print(f"  This may take a few moments for large datasets...")

    # Buffers for streaming processing
    token_buffer = []
    flag_buffer = []
    sequences = []
    labels = []

    total_frames = 0
    attack_frames = 0
    unk_tokens = 0

    # Process in chunks for memory efficiency
    chunk_size = 100_000

    for chunk in tqdm(
        pd.read_csv(
            csv_path,
            chunksize=chunk_size,
            header=None,
            names=col_names,
            on_bad_lines='skip',
            dtype={'ID': str, 'Flag': str}
        ),
        desc="  Processing chunks",
        unit="chunk"
    ):
        # Clean and normalize CAN IDs
        chunk['ID'] = chunk['ID'].astype(str).str.strip().str.lower()
        chunk['Flag'] = chunk['Flag'].astype(str).str.strip().str.upper()

        # Tokenize CAN IDs
        for _, row in chunk.iterrows():
            can_id = row['ID']
            flag = row['Flag']

            # Map CAN ID to token (UNK if not in vocab)
            token = vocab.get(can_id, UNK_ID)
            if token == UNK_ID:
                unk_tokens += 1

            token_buffer.append(token)
            flag_buffer.append(flag)

            total_frames += 1
            if flag == 'T':
                attack_frames += 1

        # Create sliding windows when buffer has enough frames
        while len(token_buffer) >= window_size:
            # Extract window
            window_tokens = token_buffer[:window_size]
            window_flags = flag_buffer[:window_size]

            sequences.append(window_tokens)

            # Label: 1 if ANY frame in window is attack ('T'), else 0
            is_attack = 1 if 'T' in window_flags else 0
            labels.append(is_attack)

            # Slide window by 1 (can adjust stride for speed vs coverage)
            token_buffer = token_buffer[window_size:]  # Non-overlapping for efficiency
            flag_buffer = flag_buffer[window_size:]

        # Check if we've reached the limit
        if max_sequences and len(sequences) >= max_sequences:
            sequences = sequences[:max_sequences]
            labels = labels[:max_sequences]
            break

    # Convert to tensors
    sequences_tensor = torch.tensor(sequences, dtype=torch.long)
    labels_array = np.array(labels, dtype=np.int32)

    # Calculate statistics
    num_sequences = len(sequences)
    num_normal = np.sum(labels_array == 0)
    num_attack = np.sum(labels_array == 1)
    attack_ratio = num_attack / num_sequences * 100 if num_sequences > 0 else 0

    print(f"\n  [OK] Data preprocessing complete!")
    print(f"    * Total frames processed : {format_number(total_frames)}")
    print(f"    * Attack frames          : {format_number(attack_frames)} ({attack_frames/total_frames*100:.2f}%)")
    print(f"    * Unknown tokens (UNK)   : {format_number(unk_tokens)}")
    print(f"    * Sequences created      : {format_number(num_sequences)}")
    print(f"    * Normal sequences       : {format_number(num_normal)} ({100-attack_ratio:.2f}%)")
    print(f"    * Attack sequences       : {format_number(num_attack)} ({attack_ratio:.2f}%)")
    print(f"    * Window size            : {window_size} frames")

    return sequences_tensor, labels_array


# ===============================================================================
# STEP 4: CALCULATE ANOMALY SCORES (BATCH INFERENCE)
# ===============================================================================

def calculate_anomaly_scores(
    model: DistilBertForMaskedLM,
    sequences: torch.Tensor,
    batch_size: int = BATCH_SIZE,
    mask_ratio: float = MASK_RATIO
) -> np.ndarray:
    """
    Calculate reconstruction loss (anomaly score) for each sequence.

    Uses MLM-style masking: mask 15% of tokens, predict them, and calculate
    cross-entropy loss. Higher loss = more anomalous = likely attack.

    Args:
        model: Trained DistilBERT model in eval mode
        sequences: Tensor of shape (N, seq_len) with tokenized sequences
        batch_size: Batch size for inference
        mask_ratio: Fraction of tokens to mask (default: 0.15)

    Returns:
        Array of anomaly scores, one per sequence
    """
    print_header("STEP 4: Computing Anomaly Scores")

    model.eval()
    all_scores = []

    dataset = TensorDataset(sequences)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    print(f"  Computing scores for {format_number(len(sequences))} sequences...")
    print(f"  Batch size: {batch_size} | Mask ratio: {mask_ratio*100:.0f}%")

    with torch.no_grad():
        for (batch,) in tqdm(loader, desc="  Inference", unit="batch"):
            batch = batch.to(DEVICE)
            B, L = batch.shape

            # Clone input for masking
            input_ids = batch.clone()
            labels = torch.full((B, L), -100, dtype=torch.long, device=DEVICE)

            # Create random mask (15% of tokens)
            prob_matrix = torch.rand(B, L, device=DEVICE)
            masked_indices = prob_matrix < mask_ratio

            # Never mask special tokens
            special_mask = (
                (batch == PAD_ID) |
                (batch == MASK_ID) |
                (batch == UNK_ID)
            )
            masked_indices = masked_indices & ~special_mask

            # Set labels at masked positions (for loss calculation)
            labels[masked_indices] = batch[masked_indices]

            # Replace masked positions with [MASK] token
            input_ids[masked_indices] = MASK_ID

            # Create attention mask (all 1s since no padding)
            attention_mask = torch.ones(B, L, dtype=torch.long, device=DEVICE)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            # Calculate per-sequence loss
            logits = outputs.logits  # (B, L, vocab_size)
            loss_per_pos = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                reduction='none',
                ignore_index=-100
            ).view(B, L)

            # Average over masked positions per sequence
            mask_counts = (labels != -100).sum(dim=1).float().clamp(min=1)
            seq_scores = loss_per_pos.sum(dim=1) / mask_counts

            all_scores.extend(seq_scores.cpu().numpy())

            # Memory cleanup
            del batch, input_ids, labels, outputs, logits

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    scores = np.array(all_scores)

    print(f"\n  [OK] Anomaly scores computed!")
    print(f"    * Mean score   : {np.mean(scores):.6f}")
    print(f"    * Std score    : {np.std(scores):.6f}")
    print(f"    * Min score    : {np.min(scores):.6f}")
    print(f"    * Max score    : {np.max(scores):.6f}")

    return scores


# ===============================================================================
# STEP 5: CALIBRATE THRESHOLD (99th PERCENTILE ON NORMAL DATA)
# ===============================================================================

def calibrate_threshold(
    scores: np.ndarray,
    labels: np.ndarray,
    percentile: int = THRESHOLD_PERCENTILE
) -> float:
    """
    Calculate the anomaly threshold using only NORMAL sequences.

    The threshold is set at the Nth percentile of normal sequence scores,
    meaning N% of normal traffic will be below this threshold.

    Args:
        scores: Array of anomaly scores for all sequences
        labels: Array of ground truth labels (0=normal, 1=attack)
        percentile: Percentile to use for threshold (default: 99)

    Returns:
        Calibrated threshold value
    """
    print_header("STEP 5: Calibrating Detection Threshold")

    # Extract scores for NORMAL sequences only
    normal_mask = labels == 0
    normal_scores = scores[normal_mask]

    if len(normal_scores) == 0:
        print("  [!] WARNING: No normal sequences found! Using overall percentile.")
        normal_scores = scores

    # Calculate threshold at specified percentile
    threshold = float(np.percentile(normal_scores, percentile))

    # Calculate statistics for normal traffic
    mean_normal = float(np.mean(normal_scores))
    std_normal = float(np.std(normal_scores))
    min_normal = float(np.min(normal_scores))
    max_normal = float(np.max(normal_scores))

    print(f"  Using {format_number(len(normal_scores))} NORMAL sequences for calibration")
    print(f"\n  Normal Traffic Score Statistics:")
    print(f"    * Mean   : {mean_normal:.6f}")
    print(f"    * Std    : {std_normal:.6f}")
    print(f"    * Min    : {min_normal:.6f}")
    print(f"    * Max    : {max_normal:.6f}")
    print(f"\n  [OK] Threshold ({percentile}th percentile): {threshold:.6f}")
    print(f"    -> Any score > {threshold:.6f} will be classified as ATTACK")

    return threshold


# ===============================================================================
# STEP 6: CLASSIFICATION AND METRICS
# ===============================================================================

def evaluate_and_print_metrics(
    scores: np.ndarray,
    labels: np.ndarray,
    threshold: float
) -> Dict:
    """
    Classify sequences and compute comprehensive evaluation metrics.

    Args:
        scores: Array of anomaly scores
        labels: Array of ground truth labels (0=normal, 1=attack)
        threshold: Classification threshold

    Returns:
        Dictionary containing all metrics and predictions
    """
    print_header("STEP 6: Classification and Evaluation Metrics")

    # Generate predictions: score > threshold -> attack (1)
    predictions = (scores > threshold).astype(int)

    # Calculate confusion matrix components
    tn = np.sum((predictions == 0) & (labels == 0))  # True Negatives
    fp = np.sum((predictions == 1) & (labels == 0))  # False Positives
    fn = np.sum((predictions == 0) & (labels == 1))  # False Negatives
    tp = np.sum((predictions == 1) & (labels == 1))  # True Positives

    total_normal = np.sum(labels == 0)
    total_attack = np.sum(labels == 1)
    total = len(labels)

    # Calculate metrics
    accuracy = accuracy_score(labels, predictions)
    precision = precision_score(labels, predictions, zero_division=0)
    recall = recall_score(labels, predictions, zero_division=0)  # Detection Rate / TPR
    f1 = f1_score(labels, predictions, zero_division=0)

    # False Positive Rate (FPR) and False Negative Rate (FNR)
    fpr = fp / total_normal if total_normal > 0 else 0
    fnr = fn / total_attack if total_attack > 0 else 0

    # Specificity (True Negative Rate)
    specificity = tn / total_normal if total_normal > 0 else 0

    # Print detailed report
    print(f"\n  {'-' * 50}")
    print(f"  CONFUSION MATRIX BREAKDOWN")
    print(f"  {'-' * 50}")
    print(f"  | True Negatives  (TN) : {format_number(tn):>10} | Normal correctly identified")
    print(f"  | False Positives (FP) : {format_number(fp):>10} | Normal misclassified as attack")
    print(f"  | False Negatives (FN) : {format_number(fn):>10} | Attack missed (not detected)")
    print(f"  | True Positives  (TP) : {format_number(tp):>10} | Attack correctly detected")
    print(f"  {'-' * 50}")

    print(f"\n  {'-' * 50}")
    print(f"  CLASSIFICATION METRICS")
    print(f"  {'-' * 50}")
    print(f"  | Accuracy             : {accuracy * 100:>8.4f}%  | Overall correctness")
    print(f"  | Precision            : {precision * 100:>8.4f}%  | Of predicted attacks, how many are real")
    print(f"  | Recall (Detection)   : {recall * 100:>8.4f}%  | Of real attacks, how many were detected")
    print(f"  | F1-Score             : {f1 * 100:>8.4f}%  | Harmonic mean of precision & recall")
    print(f"  | Specificity          : {specificity * 100:>8.4f}%  | Of normal traffic, how many identified")
    print(f"  | False Positive Rate  : {fpr * 100:>8.4f}%  | Normal misclassified as attack")
    print(f"  | False Negative Rate  : {fnr * 100:>8.4f}%  | Attacks missed")
    print(f"  {'-' * 50}")

    print(f"\n  DATASET SUMMARY")
    print(f"  Total sequences    : {format_number(total)}")
    print(f"  Normal sequences   : {format_number(total_normal)}")
    print(f"  Attack sequences   : {format_number(total_attack)}")
    print(f"  Threshold used     : {threshold:.6f}")

    # Store all results
    results = {
        'predictions': predictions,
        'scores': scores,
        'labels': labels,
        'threshold': threshold,
        'confusion_matrix': {
            'tn': int(tn), 'fp': int(fp),
            'fn': int(fn), 'tp': int(tp)
        },
        'metrics': {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'specificity': float(specificity),
            'false_positive_rate': float(fpr),
            'false_negative_rate': float(fnr)
        },
        'dataset_info': {
            'total_sequences': int(total),
            'normal_sequences': int(total_normal),
            'attack_sequences': int(total_attack)
        }
    }

    return results


# ===============================================================================
# STEP 7: SAVE PREDICTIONS
# ===============================================================================

def save_predictions(
    results: Dict,
    output_path: Path
) -> None:
    """
    Save predictions, scores, and labels to CSV file.

    Args:
        results: Dictionary containing predictions, scores, labels
        output_path: Path to save the CSV file
    """
    print_header("STEP 7: Saving Predictions")

    # Create DataFrame
    df = pd.DataFrame({
        'sequence_index': range(len(results['predictions'])),
        'anomaly_score': results['scores'],
        'ground_truth': results['labels'],
        'prediction': results['predictions'],
        'ground_truth_label': ['attack' if l == 1 else 'normal' for l in results['labels']],
        'prediction_label': ['attack' if p == 1 else 'normal' for p in results['predictions']],
        'correct': results['predictions'] == results['labels']
    })

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)

    print(f"  [OK] Predictions saved to: {output_path}")
    print(f"    * Total rows: {format_number(len(df))}")
    print(f"    * Columns: {', '.join(df.columns)}")

    # Also save metrics to JSON
    metrics_path = output_path.parent / "evaluation_metrics.json"
    metrics_data = {
        'evaluation_timestamp': datetime.now().isoformat(),
        'threshold': results['threshold'],
        'threshold_percentile': THRESHOLD_PERCENTILE,
        'confusion_matrix': results['confusion_matrix'],
        'metrics': results['metrics'],
        'dataset_info': results['dataset_info']
    }

    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)

    print(f"  [OK] Metrics saved to: {metrics_path}")


# ===============================================================================
# STEP 8: GENERATE VISUALIZATIONS
# ===============================================================================

def generate_visualizations(
    results: Dict,
    figures_dir: Path
) -> None:
    """
    Generate and save Confusion Matrix and ROC Curve visualizations.

    Args:
        results: Dictionary containing predictions, scores, labels
        figures_dir: Directory to save figure files
    """
    print_header("STEP 8: Generating Visualizations")

    # Ensure figures directory exists
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Set style for professional-looking plots
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")

    # ---------------------------------------------------------------------------
    # FIGURE 1: CONFUSION MATRIX
    # ---------------------------------------------------------------------------
    print("\n  Generating Confusion Matrix...")

    cm = confusion_matrix(results['labels'], results['predictions'])

    fig, ax = plt.subplots(figsize=(10, 8))

    # Create heatmap with custom colormap
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=['Normal (0)', 'Attack (1)'],
        yticklabels=['Normal (0)', 'Attack (1)'],
        ax=ax,
        cbar_kws={'label': 'Count'},
        annot_kws={'size': 16, 'weight': 'bold'}
    )

    ax.set_xlabel('Predicted Label', fontsize=14, fontweight='bold')
    ax.set_ylabel('True Label', fontsize=14, fontweight='bold')
    ax.set_title(
        'Confusion Matrix - CAN Bus IDS Evaluation\n'
        f'Accuracy: {results["metrics"]["accuracy"]*100:.2f}% | '
        f'F1-Score: {results["metrics"]["f1_score"]*100:.2f}%',
        fontsize=14,
        fontweight='bold',
        pad=20
    )

    # Add percentage annotations
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    for i in range(2):
        for j in range(2):
            ax.text(
                j + 0.5, i + 0.7,
                f'({cm_normalized[i, j]*100:.1f}%)',
                ha='center', va='center',
                fontsize=11, color='gray'
            )

    plt.tight_layout()

    cm_path = figures_dir / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Confusion Matrix saved: {cm_path}")

    # ---------------------------------------------------------------------------
    # FIGURE 2: ROC CURVE
    # ---------------------------------------------------------------------------
    print("\n  Generating ROC Curve...")

    # Calculate ROC curve points
    fpr_curve, tpr_curve, thresholds = roc_curve(results['labels'], results['scores'])
    roc_auc = auc(fpr_curve, tpr_curve)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot ROC curve
    ax.plot(
        fpr_curve, tpr_curve,
        color='#2563eb',
        lw=3,
        label=f'ROC Curve (AUC = {roc_auc:.4f})'
    )

    # Plot diagonal (random classifier)
    ax.plot(
        [0, 1], [0, 1],
        color='gray',
        lw=2,
        linestyle='--',
        label='Random Classifier (AUC = 0.5)'
    )

    # Mark the operating point (current threshold)
    current_fpr = results['metrics']['false_positive_rate']
    current_tpr = results['metrics']['recall']
    ax.scatter(
        [current_fpr], [current_tpr],
        s=200,
        c='red',
        marker='o',
        zorder=5,
        label=f'Operating Point (FPR={current_fpr:.3f}, TPR={current_tpr:.3f})'
    )

    # Fill area under curve
    ax.fill_between(fpr_curve, tpr_curve, alpha=0.2, color='#2563eb')

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=14, fontweight='bold')
    ax.set_ylabel('True Positive Rate (Recall / Sensitivity)', fontsize=14, fontweight='bold')
    ax.set_title(
        'ROC Curve - CAN Bus Intrusion Detection System\n'
        f'Threshold: {results["threshold"]:.4f} ({THRESHOLD_PERCENTILE}th percentile)',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)

    # Add performance zone annotations
    ax.axhline(y=0.9, color='green', linestyle=':', alpha=0.5, label='90% Detection')
    ax.axvline(x=0.1, color='orange', linestyle=':', alpha=0.5, label='10% FPR')

    plt.tight_layout()

    roc_path = figures_dir / "roc_curve.png"
    plt.savefig(roc_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] ROC Curve saved: {roc_path}")

    # ---------------------------------------------------------------------------
    # FIGURE 3: SCORE DISTRIBUTION (BONUS)
    # ---------------------------------------------------------------------------
    print("\n  Generating Score Distribution...")

    fig, ax = plt.subplots(figsize=(12, 6))

    normal_scores = results['scores'][results['labels'] == 0]
    attack_scores = results['scores'][results['labels'] == 1]

    # Plot distributions
    ax.hist(
        normal_scores,
        bins=100,
        alpha=0.7,
        color='#22c55e',
        label=f'Normal Traffic (n={format_number(len(normal_scores))})',
        density=True
    )
    ax.hist(
        attack_scores,
        bins=100,
        alpha=0.7,
        color='#ef4444',
        label=f'Attack Traffic (n={format_number(len(attack_scores))})',
        density=True
    )

    # Plot threshold line
    ax.axvline(
        results['threshold'],
        color='#f97316',
        linestyle='--',
        linewidth=3,
        label=f'Threshold: {results["threshold"]:.4f}'
    )

    ax.set_xlabel('Anomaly Score (Reconstruction Loss)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Density', fontsize=14, fontweight='bold')
    ax.set_title(
        'Anomaly Score Distribution - Normal vs Attack Traffic\n'
        f'Separation indicates model discriminative power',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    dist_path = figures_dir / "score_distribution.png"
    plt.savefig(dist_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Score Distribution saved: {dist_path}")

    # ---------------------------------------------------------------------------
    # FIGURE 4: PRECISION-RECALL CURVE (BONUS)
    # ---------------------------------------------------------------------------
    print("\n  Generating Precision-Recall Curve...")

    precision_curve, recall_curve, _ = precision_recall_curve(
        results['labels'], results['scores']
    )
    pr_auc = auc(recall_curve, precision_curve)

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(
        recall_curve, precision_curve,
        color='#8b5cf6',
        lw=3,
        label=f'PR Curve (AUC = {pr_auc:.4f})'
    )

    # Mark operating point
    ax.scatter(
        [results['metrics']['recall']],
        [results['metrics']['precision']],
        s=200,
        c='red',
        marker='o',
        zorder=5,
        label=f'Operating Point (P={results["metrics"]["precision"]:.3f}, R={results["metrics"]["recall"]:.3f})'
    )

    ax.fill_between(recall_curve, precision_curve, alpha=0.2, color='#8b5cf6')

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Recall (True Positive Rate)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Precision', fontsize=14, fontweight='bold')
    ax.set_title(
        'Precision-Recall Curve - CAN Bus IDS\n'
        f'F1-Score: {results["metrics"]["f1_score"]*100:.2f}%',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.legend(loc='lower left', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    pr_path = figures_dir / "precision_recall_curve.png"
    plt.savefig(pr_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  [OK] Precision-Recall Curve saved: {pr_path}")

    print(f"\n  [OK] All visualizations saved to: {figures_dir}")


# ===============================================================================
# MAIN EXECUTION
# ===============================================================================

def main():
    """
    Main evaluation pipeline.

    Orchestrates the complete evaluation workflow:
    1. Load vocabulary
    2. Load trained model
    3. Load and preprocess test data
    4. Calculate anomaly scores
    5. Calibrate threshold
    6. Generate predictions and metrics
    7. Save results
    8. Generate visualizations
    """
    start_time = datetime.now()

    # Print banner
    print("\n" + "=" * 70)
    print("  >> CAN BUS INTRUSION DETECTION SYSTEM - MODEL EVALUATION")
    print("     Phase 8: Comprehensive Performance Assessment")
    print("=" * 70)
    print(f"\n  Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Device: {DEVICE} {'(GPU Accelerated)' if DEVICE.type == 'cuda' else '(CPU)'}")

    # -------------------------------------------------------------------------
    # STEP 1: Load vocabulary
    # -------------------------------------------------------------------------
    vocab = load_vocabulary(VOCAB_PATH)
    vocab_size = len(vocab)

    # -------------------------------------------------------------------------
    # STEP 2: Load model
    # -------------------------------------------------------------------------
    model = load_model(MODEL_PATH, vocab_size)

    # -------------------------------------------------------------------------
    # STEP 3: Load and preprocess test data
    # -------------------------------------------------------------------------
    sequences, labels = load_and_preprocess_test_data(
        TEST_CSV_PATH,
        vocab,
        window_size=WINDOW_SIZE,
        max_sequences=None  # Process all data (set to integer to limit)
    )

    # -------------------------------------------------------------------------
    # STEP 4: Calculate anomaly scores
    # -------------------------------------------------------------------------
    scores = calculate_anomaly_scores(
        model,
        sequences,
        batch_size=BATCH_SIZE,
        mask_ratio=MASK_RATIO
    )

    # -------------------------------------------------------------------------
    # STEP 5: Calibrate threshold using ONLY normal sequences
    # -------------------------------------------------------------------------
    threshold = calibrate_threshold(
        scores,
        labels,
        percentile=THRESHOLD_PERCENTILE
    )

    # -------------------------------------------------------------------------
    # STEP 6: Evaluate and print metrics
    # -------------------------------------------------------------------------
    results = evaluate_and_print_metrics(scores, labels, threshold)

    # -------------------------------------------------------------------------
    # STEP 7: Save predictions
    # -------------------------------------------------------------------------
    predictions_path = RESULTS_DIR / "predictions.csv"
    save_predictions(results, predictions_path)

    # -------------------------------------------------------------------------
    # STEP 8: Generate visualizations
    # -------------------------------------------------------------------------
    generate_visualizations(results, FIGURES_DIR)

    # -------------------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------------------
    end_time = datetime.now()
    duration = end_time - start_time

    print_header("EVALUATION COMPLETE", char="=")
    print(f"""
  [OK] Model evaluated successfully!

  [RESULTS] KEY RESULTS:
     * Accuracy           : {results['metrics']['accuracy']*100:.2f}%
     * Precision          : {results['metrics']['precision']*100:.2f}%
     * Recall (Detection) : {results['metrics']['recall']*100:.2f}%
     * F1-Score           : {results['metrics']['f1_score']*100:.2f}%
     * False Positive Rate: {results['metrics']['false_positive_rate']*100:.4f}%
     * False Negative Rate: {results['metrics']['false_negative_rate']*100:.4f}%

  [FILES] OUTPUT FILES:
     * Predictions   : {RESULTS_DIR / 'predictions.csv'}
     * Metrics JSON  : {RESULTS_DIR / 'evaluation_metrics.json'}
     * Confusion Mat : {FIGURES_DIR / 'confusion_matrix.png'}
     * ROC Curve     : {FIGURES_DIR / 'roc_curve.png'}
     * Score Dist    : {FIGURES_DIR / 'score_distribution.png'}
     * PR Curve      : {FIGURES_DIR / 'precision_recall_curve.png'}

  [TIME]  Total runtime: {duration}
""")


if __name__ == "__main__":
    main()
