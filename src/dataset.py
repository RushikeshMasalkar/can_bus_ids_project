# src/dataset.py
# Phase 4: MLM Dataset Preparation for CAN Bus IDS

import torch
import json
import numpy as np
from torch.utils.data import Dataset, DataLoader, random_split
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent.parent
DATA_DIR       = BASE_DIR / "data"
SEQUENCES_PATH = DATA_DIR / "sequences.pt"
VOCAB_PATH     = DATA_DIR / "vocab.json"

# ── Special Token IDs ──────────────────────────────────────────────────
PAD_ID  = 0
MASK_ID = 1
UNK_ID  = 2

# ══════════════════════════════════════════════════════════════════════
# CORE DATASET CLASS
# ══════════════════════════════════════════════════════════════════════
class CANBusMLMDataset(Dataset):
    """
    Loads CAN bus sequences and applies BERT-style 15% MLM masking.

    Returns:
        input_ids    : sequence with 15% tokens masked
        attention_mask: 1 for real tokens, 0 for padding
        labels       : original token IDs at masked positions,
                       -100 everywhere else (ignored by loss)
    """

    def __init__(
        self,
        sequences_path = SEQUENCES_PATH,
        vocab_path     = VOCAB_PATH,
        mask_prob      = 0.15,    # 15% of tokens get masked
        max_seq_len    = 64,      # must match Phase 3 window size
        seed           = 42
    ):
        super().__init__()

        self.mask_prob   = mask_prob
        self.max_seq_len = max_seq_len
        self.seed        = seed

        # ── Load vocabulary ───────────────────────────────────────────
        print("📖 Loading vocabulary...")
        with open(vocab_path, 'r') as f:
            self.vocab = json.load(f)

        self.vocab_size = len(self.vocab)
        self.pad_id     = PAD_ID
        self.mask_id    = MASK_ID
        self.unk_id     = UNK_ID

        print(f"  ✅ Vocab size: {self.vocab_size}")

        # ── Load sequences tensor ─────────────────────────────────────
        print("📦 Loading sequences tensor...")
        self.sequences = torch.load(sequences_path)

        # Validate shape
        assert self.sequences.ndim == 2, \
            f"Expected 2D tensor, got shape {self.sequences.shape}"
        assert self.sequences.shape[1] == max_seq_len, \
            f"Expected seq len {max_seq_len}, got {self.sequences.shape[1]}"

        self.num_sequences = self.sequences.shape[0]
        print(f"  ✅ Sequences loaded: {self.num_sequences:,}")
        print(f"  ✅ Sequence length : {self.sequences.shape[1]}")

    # ── Dataset length ────────────────────────────────────────────────
    def __len__(self):
        return self.num_sequences

    # ── Get one training sample ───────────────────────────────────────
    def __getitem__(self, idx):
        # Get original sequence
        original = self.sequences[idx].clone()  # shape: (64,)

        # Apply MLM masking
        input_ids, labels = self._apply_masking(original)

        # Attention mask: 1 for all real tokens (no padding in our case)
        attention_mask = torch.ones(self.max_seq_len, dtype=torch.long)

        return {
            "input_ids"     : input_ids,       # masked sequence
            "attention_mask": attention_mask,  # all 1s
            "labels"        : labels           # -100 except at masked pos
        }

    # ── Core MLM Masking Logic ────────────────────────────────────────
    def _apply_masking(self, sequence):
        """
        Applies BERT-style masking to one sequence.

        For each selected position:
          80% → replace with [MASK]
          10% → replace with random token
          10% → keep original

        Labels:
          masked positions → original token ID
          all other positions → -100 (ignored by CrossEntropyLoss)
        """
        input_ids = sequence.clone()
        labels    = torch.full(
            sequence.shape, -100, dtype=torch.long
        )  # -100 = ignore in loss calculation

        # Find positions to mask (15% of all tokens)
        # torch.rand gives uniform [0,1] for each position
        probability_matrix = torch.rand(sequence.shape)
        masked_indices     = probability_matrix < self.mask_prob

        # Never mask [PAD], [MASK], or [UNK] special tokens
        special_tokens_mask = (
            (sequence == self.pad_id)  |
            (sequence == self.mask_id) |
            (sequence == self.unk_id)
        )
        masked_indices = masked_indices & ~special_tokens_mask

        # Set labels: original token ID at masked positions
        labels[masked_indices] = sequence[masked_indices]

        # ── 80%: Replace with [MASK] token ───────────────────────────
        replace_with_mask = (
            torch.rand(sequence.shape) < 0.8
        ) & masked_indices
        input_ids[replace_with_mask] = self.mask_id

        # ── 10%: Replace with random token ───────────────────────────
        # Of remaining 20%, half get random token
        replace_with_random = (
            torch.rand(sequence.shape) < 0.5
        ) & masked_indices & ~replace_with_mask

        random_tokens = torch.randint(
            low   = 3,                  # start after special tokens
            high  = self.vocab_size,
            size  = sequence.shape,
            dtype = torch.long
        )
        input_ids[replace_with_random] = random_tokens[replace_with_random]

        # ── 10%: Keep original (already unchanged) ───────────────────
        # No action needed — input_ids already has original values

        return input_ids, labels

    # ── Helper: Show masking statistics ──────────────────────────────
    def get_masking_stats(self, num_samples=1000):
        total_tokens  = 0
        masked_tokens = 0

        for i in range(min(num_samples, len(self))):
            sample = self[i]
            labels = sample['labels']
            total_tokens  += self.max_seq_len
            masked_tokens += (labels != -100).sum().item()

        avg_mask_rate = masked_tokens / total_tokens * 100
        print(f"\n📊 Masking Statistics (over {num_samples} samples):")
        print(f"   Total tokens    : {total_tokens:,}")
        print(f"   Masked tokens   : {masked_tokens:,}")
        print(f"   Avg mask rate   : {avg_mask_rate:.2f}% (target: 15%)")
        return avg_mask_rate


# ══════════════════════════════════════════════════════════════════════
# DATALOADER BUILDER
# ══════════════════════════════════════════════════════════════════════
def build_dataloaders(
    batch_size   = 64,
    train_split  = 0.9,    # 90% train, 10% validation
    num_workers  = 0,      # 0 = safe for Windows
    seed         = 42
):
    """
    Builds train and validation DataLoaders from the MLM dataset.
    """
    print("\n" + "="*50)
    print("Building DataLoaders...")
    print("="*50)

    # Create full dataset
    full_dataset = CANBusMLMDataset()

    # Split into train / validation
    total      = len(full_dataset)
    train_size = int(total * train_split)
    val_size   = total - train_size

    print(f"\n📊 Dataset split:")
    print(f"   Total      : {total:,}")
    print(f"   Train      : {train_size:,} ({train_split*100:.0f}%)")
    print(f"   Validation : {val_size:,} ({(1-train_split)*100:.0f}%)")

    generator = torch.Generator().manual_seed(seed)
    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=generator
    )

    # Build DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size  = batch_size,
        shuffle     = True,
        num_workers = num_workers,
        pin_memory  = True    # faster GPU transfer
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size  = batch_size,
        shuffle     = False,
        num_workers = num_workers,
        pin_memory  = True
    )

    print(f"\n   Train batches : {len(train_loader):,}")
    print(f"   Val batches   : {len(val_loader):,}")
    print(f"   Batch size    : {batch_size}")
    print(f"\n✅ DataLoaders ready!")

    return train_loader, val_loader, full_dataset.vocab_size


# ══════════════════════════════════════════════════════════════════════
# MAIN — Test the Dataset
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n🚀 Phase 4: Testing MLM Dataset\n")

    # Build dataset
    dataset = CANBusMLMDataset()

    # Test single sample
    print("\n--- Testing single sample ---")
    sample = dataset[0]
    print(f"input_ids shape      : {sample['input_ids'].shape}")
    print(f"attention_mask shape : {sample['attention_mask'].shape}")
    print(f"labels shape         : {sample['labels'].shape}")

    # Show masking in action
    print("\n--- Masking visualization ---")
    original  = dataset.sequences[0]
    masked    = sample['input_ids']
    labels    = sample['labels']

    print(f"{'Position':<10} {'Original':<12} {'Masked':<12} {'Label':<10}")
    print("-" * 45)
    for i in range(20):  # show first 20 positions
        orig  = original[i].item()
        mask  = masked[i].item()
        label = labels[i].item()
        flag  = " ← MASKED" if label != -100 else ""
        print(f"{i:<10} {orig:<12} {mask:<12} {label:<10}{flag}")

    # Run masking stats
    dataset.get_masking_stats(num_samples=500)

    # Test DataLoaders
    print("\n--- Testing DataLoaders ---")
    train_loader, val_loader, vocab_size = build_dataloaders(batch_size=64)

    batch = next(iter(train_loader))
    print(f"\nFirst batch shapes:")
    print(f"  input_ids      : {batch['input_ids'].shape}")
    print(f"  attention_mask : {batch['attention_mask'].shape}")
    print(f"  labels         : {batch['labels'].shape}")

    print(f"\n✅ Vocab size for model : {vocab_size}")
    print("\n🎉 Phase 4 Complete! Ready for Phase 5: Model Training")