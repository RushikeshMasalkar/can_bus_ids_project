# src/preprocess.py
# Phase 3: Tokenization & Sequence Engineering

import pandas as pd
import numpy as np
import json
import torch
import os
import gc
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent
DATA_DIR        = BASE_DIR / "data"
NORMAL_CSV      = DATA_DIR / "normal_traffic_augmented.csv"
VOCAB_PATH      = DATA_DIR / "vocab.json"
SEQUENCES_PATH  = DATA_DIR / "sequences.pt"

# ── Config ─────────────────────────────────────────────────────────────────
WINDOW_SIZE     = 64       # each sequence = 64 CAN messages
STEP_SIZE       = 32       # sliding step (50% overlap for more sequences)
CHUNK_SIZE      = 500_000  # rows to read at a time
MAX_SEQUENCES   = 500_000  # cap to avoid RAM issues

# ── Special Tokens ─────────────────────────────────────────────────────────
PAD_TOKEN   = "[PAD]"    # padding short sequences
MASK_TOKEN  = "[MASK]"   # used in training (Phase 4)
UNK_TOKEN   = "[UNK]"    # unknown CAN IDs

# ══════════════════════════════════════════════════════════════════════════
# STEP 3.1 — BUILD VOCABULARY
# ══════════════════════════════════════════════════════════════════════════
def build_vocabulary():
    print("\n" + "="*50)
    print("STEP 3.1 — Building CAN ID Vocabulary")
    print("="*50)

    unique_ids = set()
    chunk_num = 0

    print("📖 Scanning all CAN IDs from dataset...")

    for chunk in pd.read_csv(NORMAL_CSV, chunksize=CHUNK_SIZE):
        # Clean the ID column
        chunk['ID'] = chunk['ID'].astype(str).str.strip().str.lower()
        unique_ids.update(chunk['ID'].unique())
        chunk_num += 1

        if chunk_num % 10 == 0:
            print(f"  Scanned {chunk_num * CHUNK_SIZE:,} rows — "
                  f"{len(unique_ids)} unique IDs found so far...")

        del chunk
        gc.collect()

    print(f"\n✅ Scan complete!")
    print(f"📊 Total unique CAN IDs found: {len(unique_ids)}")

    # Build vocab — reserve 0,1,2 for special tokens
    vocab = {
        PAD_TOKEN:  0,
        MASK_TOKEN: 1,
        UNK_TOKEN:  2,
    }

    # Assign integer to every unique CAN ID starting from 3
    for idx, can_id in enumerate(sorted(unique_ids), start=3):
        vocab[can_id] = idx

    print(f"📋 Vocabulary size: {len(vocab)} entries")
    print(f"   → [PAD]  = 0")
    print(f"   → [MASK] = 1")
    print(f"   → [UNK]  = 2")
    print(f"   → CAN IDs = 3 to {len(vocab)-1}")

    # Save vocab to JSON
    with open(VOCAB_PATH, 'w') as f:
        json.dump(vocab, f, indent=2)

    print(f"\n💾 Saved vocab.json → {VOCAB_PATH}")
    return vocab


# ══════════════════════════════════════════════════════════════════════════
# STEP 3.2 — CREATE SLIDING WINDOW SEQUENCES
# ══════════════════════════════════════════════════════════════════════════
def build_sequences(vocab):
    print("\n" + "="*50)
    print("STEP 3.2 — Creating Sliding Window Sequences")
    print("="*50)
    print(f"⚙️  Window size : {WINDOW_SIZE}")
    print(f"⚙️  Step size   : {STEP_SIZE}")
    print(f"⚙️  Max seqs    : {MAX_SEQUENCES:,}")

    all_sequences = []
    token_buffer  = []   # holds tokenized IDs across chunks
    total_seqs    = 0
    chunk_num     = 0

    for chunk in pd.read_csv(NORMAL_CSV, chunksize=CHUNK_SIZE):
        chunk_num += 1

        # Tokenize: convert each CAN ID hex → integer
        chunk['ID'] = chunk['ID'].astype(str).str.strip().str.lower()
        tokens = chunk['ID'].map(
            lambda x: vocab.get(x, vocab[UNK_TOKEN])
        ).tolist()

        # Add to buffer
        token_buffer.extend(tokens)

        # Slide window over buffer
        while len(token_buffer) >= WINDOW_SIZE:
            window = token_buffer[:WINDOW_SIZE]
            all_sequences.append(window)
            total_seqs += 1

            # Slide forward by STEP_SIZE
            token_buffer = token_buffer[STEP_SIZE:]

            # Stop if we have enough sequences
            if total_seqs >= MAX_SEQUENCES:
                break

        if chunk_num % 10 == 0:
            print(f"  Chunks processed: {chunk_num} — "
                  f"Sequences so far: {total_seqs:,}")

        del chunk, tokens
        gc.collect()

        if total_seqs >= MAX_SEQUENCES:
            print(f"\n⚠️  Reached max sequence cap: {MAX_SEQUENCES:,}")
            break

    print(f"\n✅ Sequence creation complete!")
    print(f"📊 Total sequences created : {total_seqs:,}")
    print(f"📐 Each sequence length    : {WINDOW_SIZE} tokens")

    # Convert to PyTorch tensor and save
    print("\n💾 Converting to PyTorch tensor...")
    tensor = torch.tensor(all_sequences, dtype=torch.long)
    print(f"📐 Tensor shape: {tensor.shape}")
    # Shape should be (total_seqs, WINDOW_SIZE) e.g. (500000, 64)

    torch.save(tensor, SEQUENCES_PATH)
    print(f"💾 Saved sequences.pt → {SEQUENCES_PATH}")

    return tensor


# ══════════════════════════════════════════════════════════════════════════
# MAIN — Run Both Steps
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n🚀 Starting Phase 3: Tokenization & Sequence Engineering")

    # Step 3.1
    vocab = build_vocabulary()

    # Step 3.2
    tensor = build_sequences(vocab)

    print("\n" + "="*50)
    print("🎉 Phase 3 Complete!")
    print("="*50)
    print(f"✅ vocab.json     → {VOCAB_PATH}")
    print(f"✅ sequences.pt   → {SEQUENCES_PATH}")
    print(f"📐 Tensor shape   → {tensor.shape}")
    print(f"📋 Vocab size     → {len(json.load(open(VOCAB_PATH)))}")
    print("\n➡️  Ready for Phase 4: MLM Dataset Preparation")