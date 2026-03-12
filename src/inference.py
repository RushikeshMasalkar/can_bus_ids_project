# src/inference.py
# Phase 6: Inference & Anomaly Detection

import torch
import torch.nn.functional as F
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from transformers import DistilBertConfig, DistilBertForMaskedLM
from torch.utils.data import DataLoader, TensorDataset
import gc
import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent
DATA_DIR        = BASE_DIR / "data"
MODELS_DIR      = BASE_DIR / "models"
VOCAB_PATH      = DATA_DIR / "vocab.json"
SEQUENCES_PATH  = DATA_DIR / "sequences.pt"
ATTACK_CSV      = DATA_DIR / "attack_traffic.csv"
MODEL_PATH      = MODELS_DIR / "best_model.pt"
THRESHOLD_PATH  = MODELS_DIR / "threshold.json"

# ── Config ─────────────────────────────────────────────────────────────
BATCH_SIZE  = 128     # larger = faster inference
WINDOW_SIZE = 64
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Special Tokens ─────────────────────────────────────────────────────
PAD_ID  = 0
MASK_ID = 1
UNK_ID  = 2


# ══════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD MODEL
# ══════════════════════════════════════════════════════════════════════
def load_model(model_path, vocab_size):
    print("\n" + "="*55)
    print("STEP 1 — Loading Trained Model")
    print("="*55)

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=DEVICE, weights_only=False)
    print(f"✅ Checkpoint loaded!")
    print(f"   Saved at epoch : {checkpoint['epoch']}")
    print(f"   Best val loss  : {checkpoint['val_loss']:.4f}")

    # Rebuild model architecture
    config = DistilBertConfig(
        vocab_size              = vocab_size,
        max_position_embeddings = 64,
        dim                     = 256,
        n_layers                = 4,
        n_heads                 = 4,
        hidden_dim              = 1024,
        dropout                 = 0.1,
        attention_dropout       = 0.1,
        pad_token_id            = 0,
    )

    model = DistilBertForMaskedLM(config)
    model.load_state_dict(checkpoint['model_state'])
    model = model.to(DEVICE)
    model.eval()  # inference mode — disables dropout

    print(f"✅ Model loaded & set to eval mode!")
    print(f"   Device : {DEVICE}")
    return model


# ══════════════════════════════════════════════════════════════════════
# STEP 2 — CALCULATE ANOMALY SCORE FOR ONE SEQUENCE
# ══════════════════════════════════════════════════════════════════════
def calculate_anomaly_score(model, sequence_tensor):
    """
    Calculates Cross-Entropy loss for a sequence.
    Higher loss = more anomalous = likely attack.

    Strategy: mask every token one at a time and
    average the prediction loss across all positions.
    This gives a robust anomaly score.
    """
    model.eval()
    total_loss    = 0.0
    seq_len       = sequence_tensor.shape[0]
    num_positions = 0

    with torch.no_grad():
        # Slide a mask across every position
        for pos in range(seq_len):
            input_ids = sequence_tensor.clone().unsqueeze(0)  # (1, 64)
            labels    = torch.full(
                (1, seq_len), -100, dtype=torch.long
            ).to(DEVICE)

            # Mask this position
            original_token      = input_ids[0, pos].item()
            input_ids[0, pos]   = MASK_ID
            labels[0, pos]      = original_token

            input_ids      = input_ids.to(DEVICE)
            attention_mask = torch.ones(1, seq_len, dtype=torch.long).to(DEVICE)

            outputs = model(
                input_ids      = input_ids,
                attention_mask = attention_mask,
                labels         = labels
            )

            total_loss    += outputs.loss.item()
            num_positions += 1

    return total_loss / num_positions


# ══════════════════════════════════════════════════════════════════════
# STEP 3 — FAST BATCH ANOMALY SCORING
# ══════════════════════════════════════════════════════════════════════
def calculate_batch_anomaly_scores(model, sequences_tensor, batch_size=128):
    """
    Fast version: masks 15% of tokens per sequence
    and calculates average loss across the batch.
    Used for large-scale threshold calibration.
    """
    model.eval()
    all_scores = []
    total      = len(sequences_tensor)

    print(f"   Scoring {total:,} sequences in batches of {batch_size}...")

    dataset    = TensorDataset(sequences_tensor)
    loader     = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    with torch.no_grad():
        for batch_idx, (batch,) in enumerate(loader):
            batch     = batch.to(DEVICE)          # (B, 64)
            B, L      = batch.shape

            input_ids = batch.clone()
            labels    = torch.full(
                (B, L), -100, dtype=torch.long
            ).to(DEVICE)

            # Mask 15% randomly per sequence
            prob_matrix    = torch.rand(B, L).to(DEVICE)
            masked_indices = prob_matrix < 0.15

            # Avoid masking special tokens
            special = (
                (batch == PAD_ID)  |
                (batch == MASK_ID) |
                (batch == UNK_ID)
            )
            masked_indices = masked_indices & ~special

            # Store labels at masked positions
            labels[masked_indices] = batch[masked_indices]

            # Replace masked positions with [MASK]
            input_ids[masked_indices] = MASK_ID

            attention_mask = torch.ones(B, L, dtype=torch.long).to(DEVICE)

            outputs = model(
                input_ids      = input_ids,
                attention_mask = attention_mask,
                labels         = labels
            )

            # Per-sequence loss
            # Recompute manually for per-sample scores
            logits      = outputs.logits          # (B, L, vocab_size)
            loss_per_pos = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                reduction   = 'none',
                ignore_index = -100
            ).view(B, L)                          # (B, L)

            # Average over masked positions per sequence
            mask_counts = (labels != -100).sum(dim=1).float()
            mask_counts = mask_counts.clamp(min=1)  # avoid div by zero
            seq_scores  = loss_per_pos.sum(dim=1) / mask_counts

            all_scores.extend(seq_scores.cpu().numpy())

            if (batch_idx + 1) % 50 == 0:
                pct = (batch_idx + 1) / len(loader) * 100
                print(f"   Progress: {pct:.1f}% — "
                      f"{len(all_scores):,} sequences scored")

            del batch, input_ids, labels, outputs, logits
            gc.collect()

    return np.array(all_scores)


# ══════════════════════════════════════════════════════════════════════
# STEP 4 — CALIBRATE THRESHOLD (99th Percentile on Normal Data)
# ══════════════════════════════════════════════════════════════════════
def calibrate_threshold(model, normal_sequences, percentile=99):
    print("\n" + "="*55)
    print("STEP 4 — Calibrating Anomaly Threshold")
    print("="*55)
    print(f"   Using {len(normal_sequences):,} normal sequences")
    print(f"   Percentile target: {percentile}th")

    # Score all normal sequences
    normal_scores = calculate_batch_anomaly_scores(
        model, normal_sequences, batch_size=BATCH_SIZE
    )

    # Calculate statistics
    threshold = float(np.percentile(normal_scores, percentile))
    mean_score = float(np.mean(normal_scores))
    std_score  = float(np.std(normal_scores))
    min_score  = float(np.min(normal_scores))
    max_score  = float(np.max(normal_scores))

    print(f"\n📊 Normal Traffic Score Statistics:")
    print(f"   Mean score  : {mean_score:.4f}")
    print(f"   Std score   : {std_score:.4f}")
    print(f"   Min score   : {min_score:.4f}")
    print(f"   Max score   : {max_score:.4f}")
    print(f"\n🎯 Threshold ({percentile}th percentile): {threshold:.4f}")
    print(f"   → Any score above {threshold:.4f} = ATTACK")

    # Save threshold
    threshold_data = {
        "threshold"   : threshold,
        "percentile"  : percentile,
        "mean_normal" : mean_score,
        "std_normal"  : std_score,
        "min_normal"  : min_score,
        "max_normal"  : max_score,
        "num_samples" : len(normal_scores)
    }

    with open(THRESHOLD_PATH, 'w') as f:
        json.dump(threshold_data, f, indent=2)

    print(f"\n💾 Threshold saved → {THRESHOLD_PATH}")
    return threshold, normal_scores


# ══════════════════════════════════════════════════════════════════════
# STEP 5 — BUILD ATTACK SEQUENCES FROM attack_traffic.csv
# ══════════════════════════════════════════════════════════════════════
def build_attack_sequences(vocab, num_sequences=5000):
    print("\n" + "="*55)
    print("STEP 5 — Building Attack Sequences")
    print("="*55)

    col_names = [
        'Timestamp', 'ID', 'DLC',
        'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'Flag'
    ]

    token_buffer = []
    sequences    = []

    for chunk in pd.read_csv(
        ATTACK_CSV,
        chunksize   = 100_000,
        header      = None,
        names       = col_names,
        on_bad_lines = 'skip'
    ):
        chunk['ID'] = chunk['ID'].astype(str).str.strip().str.lower()
        tokens = chunk['ID'].map(
            lambda x: vocab.get(x, UNK_ID)
        ).tolist()
        token_buffer.extend(tokens)

        while len(token_buffer) >= WINDOW_SIZE:
            sequences.append(token_buffer[:WINDOW_SIZE])
            token_buffer = token_buffer[WINDOW_SIZE:]

            if len(sequences) >= num_sequences:
                break

        if len(sequences) >= num_sequences:
            break

    print(f"✅ Built {len(sequences):,} attack sequences")
    return torch.tensor(sequences, dtype=torch.long)


# ══════════════════════════════════════════════════════════════════════
# STEP 6 — EVALUATE: NORMAL vs ATTACK
# ══════════════════════════════════════════════════════════════════════
def evaluate_detection(
    model, normal_sequences, attack_sequences, threshold
):
    print("\n" + "="*55)
    print("STEP 6 — Evaluating Detection Performance")
    print("="*55)

    # Score attack sequences
    print("Scoring attack sequences...")
    attack_scores = calculate_batch_anomaly_scores(
        model, attack_sequences, batch_size=BATCH_SIZE
    )

    # Score sample of normal sequences for comparison
    print("Scoring normal sequences (sample)...")
    sample_size    = min(5000, len(normal_sequences))
    indices        = torch.randperm(len(normal_sequences))[:sample_size]
    normal_sample  = normal_sequences[indices]
    normal_scores  = calculate_batch_anomaly_scores(
        model, normal_sample, batch_size=BATCH_SIZE
    )

    # Calculate metrics
    # True Positives: attacks correctly flagged
    tp = np.sum(attack_scores > threshold)
    # False Negatives: attacks missed
    fn = np.sum(attack_scores <= threshold)
    # True Negatives: normal correctly passed
    tn = np.sum(normal_scores <= threshold)
    # False Positives: normal wrongly flagged
    fp = np.sum(normal_scores > threshold)

    total_attacks = len(attack_scores)
    total_normal  = len(normal_scores)

    detection_rate = tp / total_attacks * 100
    false_alarm    = fp / total_normal  * 100
    precision      = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall         = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1             = (2 * precision * recall /
                     (precision + recall)
                     if (precision + recall) > 0 else 0)

    print(f"\n📊 Detection Results:")
    print(f"   Threshold          : {threshold:.4f}")
    print(f"   ─────────────────────────────────")
    print(f"   Attacks detected   : {tp}/{total_attacks} "
          f"({detection_rate:.1f}%)")
    print(f"   Attacks missed     : {fn}/{total_attacks}")
    print(f"   Normal correct     : {tn}/{total_normal}")
    print(f"   False alarms       : {fp}/{total_normal} "
          f"({false_alarm:.1f}%)")
    print(f"   ─────────────────────────────────")
    print(f"   Precision          : {precision:.4f}")
    print(f"   Recall             : {recall:.4f}")
    print(f"   F1 Score           : {f1:.4f}")

    return {
        'normal_scores' : normal_scores,
        'attack_scores' : attack_scores,
        'threshold'     : threshold,
        'detection_rate': detection_rate,
        'false_alarm'   : false_alarm,
        'precision'     : precision,
        'recall'        : recall,
        'f1'            : f1
    }


# ══════════════════════════════════════════════════════════════════════
# STEP 7 — PLOT RESULTS
# ══════════════════════════════════════════════════════════════════════
def plot_results(results):
    print("\n" + "="*55)
    print("STEP 7 — Plotting Results")
    print("="*55)

    normal_scores = results['normal_scores']
    attack_scores = results['attack_scores']
    threshold     = results['threshold']

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        'CAN Bus Intrusion Detection System — Results',
        fontsize=16, fontweight='bold'
    )

    # Plot 1: Score distributions
    ax1 = axes[0]
    ax1.hist(
        normal_scores, bins=50,
        color='steelblue', alpha=0.7,
        label='Normal Traffic', density=True
    )
    ax1.hist(
        attack_scores, bins=50,
        color='crimson', alpha=0.7,
        label='Attack Traffic', density=True
    )
    ax1.axvline(
        threshold, color='orange',
        linestyle='--', linewidth=2.5,
        label=f'Threshold: {threshold:.3f}'
    )
    ax1.set_title('Anomaly Score Distribution', fontsize=13)
    ax1.set_xlabel('Anomaly Score (Loss)')
    ax1.set_ylabel('Density')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Score timeline
    ax2 = axes[1]
    ax2.plot(
        normal_scores[:500], color='steelblue',
        alpha=0.6, linewidth=0.8, label='Normal'
    )
    ax2.plot(
        range(len(normal_scores[:500]),
              len(normal_scores[:500]) + len(attack_scores[:500])),
        attack_scores[:500],
        color='crimson', alpha=0.6,
        linewidth=0.8, label='Attack'
    )
    ax2.axhline(
        threshold, color='orange',
        linestyle='--', linewidth=2,
        label=f'Threshold: {threshold:.3f}'
    )
    ax2.set_title('Anomaly Score Timeline', fontsize=13)
    ax2.set_xlabel('Sequence Index')
    ax2.set_ylabel('Anomaly Score')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Metrics bar chart
    ax3 = axes[2]
    metrics = {
        'Detection\nRate'  : results['detection_rate'] / 100,
        'Precision'        : results['precision'],
        'Recall'           : results['recall'],
        'F1 Score'         : results['f1'],
        'False Alarm\nRate': results['false_alarm'] / 100,
    }
    colors = ['green', 'steelblue', 'steelblue', 'purple', 'crimson']
    bars   = ax3.bar(
        metrics.keys(), metrics.values(),
        color=colors, edgecolor='black', alpha=0.85
    )
    ax3.set_title('Detection Metrics', fontsize=13)
    ax3.set_ylabel('Score')
    ax3.set_ylim(0, 1.1)
    ax3.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax3.grid(True, alpha=0.3, axis='y')

    for bar, val in zip(bars, metrics.values()):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f'{val:.3f}', ha='center',
            va='bottom', fontsize=10, fontweight='bold'
        )

    plt.tight_layout()
    output_path = DATA_DIR / "detection_results.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"✅ Results chart saved → {output_path}")


# ══════════════════════════════════════════════════════════════════════
# STEP 8 — LIVE SINGLE SEQUENCE DETECTOR
# ══════════════════════════════════════════════════════════════════════
def detect_single_sequence(model, sequence, vocab, threshold):
    """
    Takes one raw sequence of CAN IDs and returns
    whether it's Normal or an Attack.
    This is what the dashboard will call in Phase 7.
    """
    # Tokenize
    if isinstance(sequence[0], str):
        tokens = [vocab.get(x.strip().lower(), UNK_ID) for x in sequence]
    else:
        tokens = sequence

    tensor = torch.tensor(
        [tokens], dtype=torch.long
    ).to(DEVICE)

    # Score it
    model.eval()
    with torch.no_grad():
        input_ids  = tensor.clone()
        labels_    = torch.full((1, len(tokens)), -100).to(DEVICE)
        prob_mat   = torch.rand(1, len(tokens))
        mask_idx   = prob_mat < 0.15
        labels_[mask_idx]     = tensor[mask_idx]
        input_ids[mask_idx]   = MASK_ID
        attn_mask  = torch.ones(1, len(tokens), dtype=torch.long).to(DEVICE)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attn_mask,
            labels=labels_
        )
        score = outputs.loss.item()

    result = "🚨 ATTACK DETECTED" if score > threshold else "✅ NORMAL"

    print(f"\n{'='*40}")
    print(f"Single Sequence Detection")
    print(f"{'='*40}")
    print(f"Anomaly Score : {score:.4f}")
    print(f"Threshold     : {threshold:.4f}")
    print(f"Result        : {result}")
    print(f"{'='*40}")

    return score, result


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n🚀 Phase 6: Inference & Anomaly Detection")
    print(f"   Device: {DEVICE}\n")

    # Load vocab
    with open(VOCAB_PATH, 'r') as f:
        vocab = json.load(f)
    VOCAB_SIZE = len(vocab)
    print(f"✅ Vocab loaded: {VOCAB_SIZE} tokens")

    # Load model
    model = load_model(MODEL_PATH, VOCAB_SIZE)

    # Load normal sequences (use 10k sample for speed)
    print("\n📦 Loading normal sequences...")
    all_sequences = torch.load(SEQUENCES_PATH, weights_only=False)
    sample_idx    = torch.randperm(len(all_sequences))[:10000]
    normal_sample = all_sequences[sample_idx]
    print(f"✅ Normal sample: {len(normal_sample):,} sequences")
    del all_sequences
    gc.collect()

    # Calibrate threshold
    threshold, normal_scores = calibrate_threshold(
        model, normal_sample, percentile=99
    )

    # Build attack sequences
    attack_sequences = build_attack_sequences(vocab, num_sequences=5000)

    # Evaluate
    results = evaluate_detection(
        model, normal_sample, attack_sequences, threshold
    )

    # Plot
    plot_results(results)

    print("\n" + "="*55)
    print("🎉 Phase 6 Complete!")
    print("="*55)
    print(f"✅ Threshold saved → {THRESHOLD_PATH}")
    print(f"✅ Results chart   → {DATA_DIR}/detection_results.png")
    print(f"\n➡️  Ready for Phase 7: Dashboard!")