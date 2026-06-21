"""Train the tile number + color CNN.

Checkpoint picked by joint val accuracy (both heads right).
"""

import csv
import json
import os
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from tqdm import tqdm

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from rummikub.paths import DATA_DIR, MODELS_DIR, resolve_data_path
from rummikub.stage2_classification.model import (
    COLOR_CLASSES,
    NUMBER_CLASSES,
    TileClassifier,
    _TIMM_AVAILABLE,
    backbone_name,
)

MANIFEST_AUG = DATA_DIR / "stage2_v4" / "manifest_aug.csv"
RUN_DIR      = MODELS_DIR / "stage2_classification" / "rummikub-classifier-v4"
DATASET_INFO = DATA_DIR / "stage2_v4" / "dataset_info.json"   # has preprocess flag

INPUT_SIZE    = 128
BATCH         = 128
EPOCHS        = 80
PATIENCE      = 15       # early stop on joint val acc
LR            = 3e-4
LR_MIN        = 1e-6
WARMUP_EPOCHS = 3
WEIGHT_DECAY  = 1e-4
SEED          = 42

# ImageNet norm — don't change without retraining
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD  = [0.229, 0.224, 0.225]

NUM2IDX = {c: i for i, c in enumerate(NUMBER_CLASSES)}
COL2IDX = {c: i for i, c in enumerate(COLOR_CLASSES)}

def _norm(img_rgb: np.ndarray) -> torch.Tensor:
    """RGB uint8 → normalized CHW tensor."""
    x = img_rgb.astype(np.float32) / 255.0
    mean = np.array(NORM_MEAN, dtype=np.float32).reshape(1, 1, 3)
    std  = np.array(NORM_STD,  dtype=np.float32).reshape(1, 1, 3)
    x = (x - mean) / std
    return torch.from_numpy(x.transpose(2, 0, 1))  # CHW

class TileDataset(Dataset):
    """Manifest rows → (image, number_idx, color_idx)."""
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r   = self.rows[idx]
        img = cv2.imread(str(resolve_data_path(r["filepath"])))
        if img is None:
            img = np.full((INPUT_SIZE, INPUT_SIZE, 3), 114, dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return (
            _norm(img),
            NUM2IDX[r["number"]],
            COL2IDX[r["color"]],
        )

def make_sampler(rows: list[dict]) -> WeightedRandomSampler:
    """Oversample rare numbers so batches aren't dominated by 1–5."""
    num_counts = defaultdict(int)
    for r in rows:
        num_counts[r["number"]] += 1
    weights = [1.0 / num_counts[r["number"]] for r in rows]
    return WeightedRandomSampler(weights, num_samples=len(rows), replacement=True)

class WarmupCosineScheduler:
    """Warm up LR linearly, then cosine decay."""
    def __init__(self, optimizer, warmup_epochs, total_epochs, lr_min):
        self.opt           = optimizer
        self.warmup_epochs = warmup_epochs
        self.total_epochs  = total_epochs
        self.lr_base       = optimizer.param_groups[0]["lr"]
        self.lr_min        = lr_min
        self.epoch         = 0

    def step(self):
        """Advance one epoch and update learning rate."""
        self.epoch += 1
        if self.epoch <= self.warmup_epochs:
            lr = self.lr_base * self.epoch / self.warmup_epochs
        else:
            progress = (self.epoch - self.warmup_epochs) / max(1, self.total_epochs - self.warmup_epochs)
            lr = self.lr_min + 0.5 * (self.lr_base - self.lr_min) * (1 + np.cos(np.pi * progress))
        for pg in self.opt.param_groups:
            pg["lr"] = lr
        return lr

@torch.no_grad()
def evaluate(model, loader, device, scaler_ctx):
    """Val accuracy + loss for both heads."""
    model.eval()
    total = num_correct = col_correct = joint_correct = 0
    num_loss_sum = col_loss_sum = 0.0
    ce = nn.CrossEntropyLoss()

    for imgs, num_labels, col_labels in tqdm(loader, desc="  val", leave=False, unit="batch", dynamic_ncols=True):
        imgs       = imgs.to(device)
        num_labels = num_labels.to(device)
        col_labels = col_labels.to(device)

        with torch.autocast(device_type="cuda", dtype=torch.float16):
            num_logits, col_logits = model(imgs)
            num_loss_sum += ce(num_logits, num_labels).item() * len(imgs)
            col_loss_sum += ce(col_logits, col_labels).item() * len(imgs)

        num_pred = num_logits.argmax(1)
        col_pred = col_logits.argmax(1)
        num_correct   += (num_pred == num_labels).sum().item()
        col_correct   += (col_pred == col_labels).sum().item()
        joint_correct += ((num_pred == num_labels) & (col_pred == col_labels)).sum().item()
        total += len(imgs)

    n = max(1, total)
    return {
        "num_acc":   num_correct   / n,
        "col_acc":   col_correct   / n,
        "joint_acc": joint_correct / n,
        "num_loss":  num_loss_sum  / n,
        "col_loss":  col_loss_sum  / n,
    }

@torch.no_grad()
def confusion_analysis(model, loader, device):
    """Print per-class errors; flag 6/9 and red/orange mixups."""
    model.eval()
    num_cm = defaultdict(Counter)
    col_cm = defaultdict(Counter)

    for imgs, num_labels, col_labels in loader:
        imgs = imgs.to(device)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            nl, cl = model(imgs)
        for true, pred in zip(num_labels.tolist(), nl.argmax(1).tolist()):
            num_cm[NUMBER_CLASSES[true]][NUMBER_CLASSES[pred]] += 1
        for true, pred in zip(col_labels.tolist(), cl.argmax(1).tolist()):
            col_cm[COLOR_CLASSES[true]][COLOR_CLASSES[pred]] += 1

    print("\n-- Number confusion (accuracy per class) --")
    for cls in NUMBER_CLASSES:
        counts = num_cm[cls]
        tot = sum(counts.values())
        if tot == 0:
            continue
        acc = counts[cls] / tot
        errors = {k: v for k, v in counts.items() if k != cls and v > 0}
        flag = " (!)" if (cls in ("6", "9") and errors) else ""
        print(f"  {cls:>5}: {acc:.3f}  errors={errors}{flag}")

    print("\n-- Color confusion (accuracy per class) --")
    for cls in COLOR_CLASSES:
        counts = col_cm[cls]
        tot = sum(counts.values())
        if tot == 0:
            continue
        acc = counts[cls] / tot
        errors = {k: v for k, v in counts.items() if k != cls and v > 0}
        flag = " (!)" if (cls in ("red", "orange") and errors) else ""
        print(f"  {cls:>7}: {acc:.3f}  errors={errors}{flag}")

def main():
    """Training loop + test eval + metadata.json."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", help="override manifest_aug.csv path")
    ap.add_argument("--run-dir",  help="override output run dir")
    ap.add_argument("--dataset-info", help="override dataset_info.json path")
    args = ap.parse_args()
    global MANIFEST_AUG, RUN_DIR, DATASET_INFO
    if args.manifest:     MANIFEST_AUG = Path(args.manifest)
    if args.run_dir:      RUN_DIR      = Path(args.run_dir)
    if args.dataset_info: DATASET_INFO = Path(args.dataset_info)

    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device : {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'cpu'})")
    if device.type == "cuda":
        print(f"VRAM   : {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f} GB")
    print(f"Backbone: {'timm EfficientNet-B0 (pretrained)' if _TIMM_AVAILABLE else 'custom CNN (no timm)'}")
    print()

    all_rows = list(csv.DictReader(open(MANIFEST_AUG, encoding="utf-8")))

    train_rows = [r for r in all_rows if r["split"] == "train"]
    val_rows   = [r for r in all_rows if r["split"] == "val"]
    test_rows  = [r for r in all_rows if r["split"] == "test"]

    print(f"Train: {len(train_rows)}  Val: {len(val_rows)}  Test: {len(test_rows)}")

    train_ds = TileDataset(train_rows)
    val_ds   = TileDataset(val_rows)
    test_ds  = TileDataset(test_rows)

    train_loader = DataLoader(
        train_ds,
        batch_size  = BATCH,
        sampler     = make_sampler(train_rows),
        num_workers = 0,
        pin_memory  = True,
        drop_last   = True,
    )
    val_loader  = DataLoader(val_ds,  batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True)

    model = TileClassifier(n_numbers=len(NUMBER_CLASSES), n_colors=len(COLOR_CLASSES))
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"Params : {total_params:.2f}M")

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = WarmupCosineScheduler(optimizer, WARMUP_EPOCHS, EPOCHS, LR_MIN)
    scaler    = torch.amp.GradScaler("cuda")
    ce        = nn.CrossEntropyLoss()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    results_csv = open(RUN_DIR / "results.csv", "w", newline="", encoding="utf-8")
    csv_writer  = csv.writer(results_csv)
    csv_writer.writerow(["epoch", "lr", "train_num_loss", "train_col_loss",
                         "val_num_acc", "val_col_acc", "val_joint_acc", "epoch_sec"])

    best_joint = 0.0
    patience_counter = 0

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        model.train()
        lr = scheduler.step()

        num_loss_sum = col_loss_sum = 0.0
        batches = 0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch:3d}/{EPOCHS}", leave=False,
                    unit="batch", dynamic_ncols=True)
        for imgs, num_labels, col_labels in pbar:
            imgs       = imgs.to(device, non_blocking=True)
            num_labels = num_labels.to(device, non_blocking=True)
            col_labels = col_labels.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with torch.autocast(device_type="cuda", dtype=torch.float16):
                num_logits, col_logits = model(imgs)
                loss = ce(num_logits, num_labels) + ce(col_logits, col_labels)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()

            n_loss = ce(num_logits.detach(), num_labels).item()
            c_loss = ce(col_logits.detach(), col_labels).item()
            num_loss_sum += n_loss
            col_loss_sum += c_loss
            batches += 1
            pbar.set_postfix(num_loss=f"{n_loss:.3f}", col_loss=f"{c_loss:.3f}", lr=f"{lr:.1e}")

        val_metrics = evaluate(model, val_loader, device, scaler)
        elapsed = time.time() - t0

        joint = val_metrics["joint_acc"]
        print(
            f"[{epoch:3d}/{EPOCHS}]  lr={lr:.2e}  "
            f"train_num_loss={num_loss_sum/batches:.4f}  "
            f"train_col_loss={col_loss_sum/batches:.4f}  "
            f"val_num={val_metrics['num_acc']:.4f}  "
            f"val_col={val_metrics['col_acc']:.4f}  "
            f"val_joint={joint:.4f}  "
            f"[{elapsed:.0f}s]"
        )
        csv_writer.writerow([
            epoch, f"{lr:.2e}",
            f"{num_loss_sum/batches:.4f}", f"{col_loss_sum/batches:.4f}",
            f"{val_metrics['num_acc']:.4f}", f"{val_metrics['col_acc']:.4f}",
            f"{joint:.4f}", f"{elapsed:.0f}",
        ])
        results_csv.flush()

        # always keep last.pt
        torch.save(model.state_dict(), RUN_DIR / "last.pt")

        # best.pt tracks joint val acc
        if joint > best_joint:
            best_joint = joint
            patience_counter = 0
            torch.save(model.state_dict(), RUN_DIR / "best.pt")
            print(f"  ^ new best joint val acc: {best_joint:.4f}  (saved best.pt)")
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"\nEarly stop: no improvement for {PATIENCE} epochs.")
                break

    results_csv.close()

    # stash preprocess in metadata so inference matches training
    preprocess = "none"
    if DATASET_INFO.exists():
        preprocess = json.loads(DATASET_INFO.read_text(encoding="utf-8")).get("preprocess", "none")

    metadata = {
        "number_classes": NUMBER_CLASSES,
        "color_classes":  COLOR_CLASSES,
        "input_size":     INPUT_SIZE,
        "normalize_mean": NORM_MEAN,
        "normalize_std":  NORM_STD,
        "backbone":       backbone_name(),
        "preprocess":     preprocess,
    }
    (RUN_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(f"\nLoading best weights for test evaluation: {RUN_DIR / 'best.pt'}")
    model.load_state_dict(torch.load(RUN_DIR / "best.pt", weights_only=True))

    test_metrics = evaluate(model, test_loader, device, None)
    print("\n" + "=" * 55)
    print("TEST SPLIT METRICS (best checkpoint)")
    print("=" * 55)
    print(f"  Number accuracy : {test_metrics['num_acc']:.4f}")
    print(f"  Color  accuracy : {test_metrics['col_acc']:.4f}")
    print(f"  Joint  accuracy : {test_metrics['joint_acc']:.4f}  (headline metric)")
    print("=" * 55)

    confusion_analysis(model, test_loader, device)

    print(f"\nRun dir: {RUN_DIR}")
    print(f"Weights: {RUN_DIR / 'best.pt'}")
    print(f"Metadata: {RUN_DIR / 'metadata.json'}")

if __name__ == "__main__":
    main()
