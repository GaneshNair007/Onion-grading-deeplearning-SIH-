#!/usr/bin/env python3
"""Fine-tune the onion attribute model on REAL labels only.

Supervised tasks (driven by what the tracked dataset actually labels):

* ``quality_class`` (4-class) — Roboflow *Onion Grading v7* (CC BY 4.0)
* ``rotten`` / ``sprout`` (binary) — Roboflow *onions v1* (Public Domain)

No synthetic images. No fabricated labels: an image that is not annotated for
a task contributes no gradient for that task (audit finding P0.2).

Splits:
* ``--split-mode grouped`` (DEFAULT — leak-free): images from **all** sources
  are embedded with an ImageNet backbone and clustered by near-duplicate, and
  whole clusters are assigned to train/validation/test. This exists because
  the official Roboflow ``valid`` split was measured to be **85.2 %
  near-duplicate with train** (`evaluation/split_leakage.json`), which made
  valid-set metrics meaningless.
* ``--split-mode official``: uses the source splits as published (kept for
  comparison and reported separately, with the leakage caveat attached).

Usage:
    python training/train_attribute_model.py --epochs 4 --split-mode grouped
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.dataset_registry import DatasetRegistry, default_registry  # noqa: E402
from src.vision.model import (ATTRIBUTE_TASKS, BINARY_HEADS,  # noqa: E402
                              OnionAttributeNet, QUALITY_CLASSES, describe)

SEED = 42
QUALITY_SOURCE = "onion-grading-coco-segmentation"
DEFECT_SOURCE = "onion-coco-mmdetection"
ARTIFACT_DIR = PROJECT_ROOT / "models" / "vision" / "attributes"


def set_seeds(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)  # CPU kernels vary; documented


def build_quality_index(reg: DatasetRegistry) -> Dict[str, List[Tuple[Path, int]]]:
    """image path → quality class index.

    The label is the quality class of the **largest-area annotation** on the
    image (deterministic and documented); images whose annotations carry no
    mapped quality class are skipped rather than guessed.
    """
    from src.data.labels import map_categories

    index: Dict[str, List[Tuple[Path, int]]] = {}
    for src in reg.sources():
        if src.source_group != QUALITY_SOURCE:
            continue
        labelled: List[Tuple[Path, int]] = []
        for rec in reg.records(src):
            best_area, best_class = -1.0, None
            for ann in rec["annotations"]:
                mapped = map_categories(src.source_group, [ann["category"]])
                qc = mapped["targets"].get("quality_class")
                if qc not in QUALITY_CLASSES:
                    continue
                bbox = ann.get("bbox")
                area = float(ann.get("area") or (bbox[2] * bbox[3] if bbox else 0.0))
                if area > best_area:
                    best_area, best_class = area, qc
            if best_class in QUALITY_CLASSES:
                labelled.append((rec["image_path"], QUALITY_CLASSES.index(best_class)))
        index[src.split] = labelled
    return index


def build_binary_index(reg: DatasetRegistry) -> Dict[str, List[Tuple[Path, List[int]]]]:
    """image path → [rotten, sprout] labels (1 only when annotated)."""
    index: Dict[str, List[Tuple[Path, List[int]]]] = {}
    for src in reg.sources():
        if src.source_group != DEFECT_SOURCE:
            continue
        labelled = []
        for rec in reg.records(src):
            targets = rec["targets"]
            if not rec["categories"]:
                continue  # unannotated image: no supervision for this task
            labelled.append((rec["image_path"],
                             [1 if targets.get("rotten") else 0,
                              1 if targets.get("sprout") else 0]))
        index[src.split] = labelled
    return index


def deterministic_split(items: List, val_frac: float = 0.2, seed: int = SEED):
    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    n_val = max(1, int(round(val_frac * len(shuffled))))
    return shuffled[n_val:], shuffled[:n_val]


def make_loader(items, input_size: int, batch_size: int, shuffle: bool,
                quality: bool):
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms

    tf_train = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    tf_eval = transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    class OnionDataset(Dataset):
        def __init__(self, rows):
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, idx):
            path, label = self.rows[idx]
            img = Image.open(path).convert("RGB")
            tensor = (tf_train if shuffle else tf_eval)(img)
            if quality:
                return tensor, torch.tensor(label, dtype=torch.long)
            return tensor, torch.tensor(label, dtype=torch.float32)

    return DataLoader(OnionDataset(items), batch_size=batch_size,
                      shuffle=shuffle, num_workers=0)


def evaluate(net, loader, device, quality: bool):
    net.eval()
    preds, gts, probs = [], [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            q_logits, b_logits = net(x)
            if quality:
                p = torch.softmax(q_logits, dim=1)
                preds.extend(p.argmax(1).cpu().tolist())
                probs.extend(p.cpu().tolist())
                gts.extend(y.tolist())
            else:
                p = torch.sigmoid(b_logits)
                preds.extend((p >= 0.5).int().cpu().tolist())
                probs.extend(p.cpu().tolist())
                gts.extend(y.int().tolist())
    return np.array(gts), np.array(preds), np.array(probs)


def classification_metrics(y_true, y_pred, y_prob, classes: List[str]) -> dict:
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(classes))), zero_division=0)
    per_class = {}
    for i, name in enumerate(classes):
        per_class[name] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }
    return {
        "accuracy": round(float((y_true == y_pred).mean()), 4) if len(y_true) else None,
        "macro_f1": round(float(np.mean(f1)), 4),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=list(range(len(classes)))).tolist(),
        "n": int(len(y_true)),
    }


def binary_metrics(y_true, y_pred, y_prob, names: List[str]) -> dict:
    from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
    out = {}
    for i, name in enumerate(names):
        gt, pr = y_true[:, i], y_pred[:, i]
        _, _, f1, support = precision_recall_fscore_support(
            gt, pr, average="binary", zero_division=0)
        prec, rec, _, _ = precision_recall_fscore_support(
            gt, pr, average="binary", zero_division=0)
        entry = {
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "positives": int(gt.sum()),
            "support": int(len(gt)),
        }
        if len(set(gt.tolist())) > 1:
            entry["roc_auc"] = round(float(roc_auc_score(gt, y_prob[:, i])), 4)
        out[name] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--input-size", type=int, default=160)
    ap.add_argument("--lr", type=float, default=8e-4)
    ap.add_argument("--max-images", type=int, default=0,
                    help="debug: cap images per source (0 = all)")
    ap.add_argument("--split-mode", choices=["grouped", "official"],
                    default="grouped",
                    help="grouped = leak-free near-duplicate grouping (default); "
                         "official = source splits as published (leaky, see docstring)")
    ap.add_argument("--out-dir", type=Path, default=ARTIFACT_DIR)
    args = ap.parse_args()

    set_seeds()
    device = torch.device("cpu")
    reg = default_registry()

    quality_idx = build_quality_index(reg)
    binary_idx = build_binary_index(reg)
    if args.max_images:
        for d in (quality_idx, binary_idx):
            for k in d:
                d[k] = d[k][: args.max_images]

    split_mode = args.split_mode
    if split_mode == "official":
        q_train = quality_idx.get("train", [])
        q_val = quality_idx.get("valid", [])
        q_test = quality_idx.get("test", [])
        d_all = binary_idx.get("train", [])
        d_train, d_val = deterministic_split(d_all)
        split_info = {
            "mode": "official",
            "warning": ("the official valid split is 85.2% near-duplicate with "
                        "train (evaluation/split_leakage.json); metrics from this "
                        "mode are optimistic"),
        }
    else:
        from src.data.splits import (embed_images, grouped_split,
                                     split_summary)
        # One coherent pool: quality-labelled + defect-labelled images.
        q_img = {str(p): (p, lbl) for split_items in quality_idx.values()
                 for p, lbl in split_items}
        d_img = {str(p): (p, lbl) for split_items in binary_idx.values()
                 for p, lbl in split_items}
        pooled = sorted(set(q_img) | set(d_img))
        pool_paths = [Path(p) for p in pooled]
        print(f"grouping {len(pool_paths)} images by near-duplicate "
              "(ImageNet embeddings)...", flush=True)
        embs = embed_images(pool_paths, input_size=128)
        grouped = grouped_split(pool_paths, embs)
        split_info = split_summary(grouped)
        split_info["mode"] = "grouped"
        print(f"grouped split: {split_info['counts']} over "
              f"{split_info['n_groups']} groups", flush=True)

        def take(index, split_name):
            return [index[k] for k, s in grouped.assignment.items()
                    if s == split_name and k in index]

        q_train = take(q_img, "train")
        q_val = take(q_img, "validation")
        q_test = take(q_img, "test")
        d_train = take(d_img, "train")
        d_val = take(d_img, "validation")

    if not q_train or not d_train:
        print("ERROR: labelled data not found; check the dataset checkout.",
              file=sys.stderr)
        return 1

    print(f"quality train/valid/test: {len(q_train)}/{len(q_val)}/{len(q_test)}")
    print(f"defect  train/val       : {len(d_train)}/{len(d_val)}")
    print(f"split mode: {split_info['mode']}")

    net = OnionAttributeNet(pretrained=True).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=args.lr, weight_decay=1e-4)
    ce = nn.CrossEntropyLoss()
    bce = nn.BCEWithLogitsLoss()

    q_loader = make_loader(q_train, args.input_size, args.batch_size, True, True)
    d_loader = make_loader(d_train, args.input_size, args.batch_size, True, False)

    started = time.time()
    history = []
    for epoch in range(1, args.epochs + 1):
        net.train()
        q_loss_sum = d_loss_sum = 0.0
        # Interleave the two tasks so both heads see gradient each epoch.
        for (qx, qy), (dx, dy) in zip(q_loader, d_loader):
            opt.zero_grad()
            q_logits, b_logits = net(qx.to(device))
            loss = ce(q_logits, qy.to(device))
            bx, by = dx.to(device), dy.to(device)
            _, b_logits2 = net(bx)
            loss = loss + bce(b_logits2, by)
            loss.backward()
            opt.step()
            q_loss_sum += float(ce(q_logits, qy.to(device)).item())
            d_loss_sum += float(bce(b_logits2, by).item())
        steps = max(min(len(q_loader), len(d_loader)), 1)
        print(f"epoch {epoch}/{args.epochs}  quality_loss="
              f"{q_loss_sum / steps:.4f}  defect_loss={d_loss_sum / steps:.4f}")
        history.append({"epoch": epoch, "quality_loss": q_loss_sum / steps,
                        "defect_loss": d_loss_sum / steps})
    train_seconds = time.time() - started

    metrics: Dict[str, object] = {
        "split": split_info,
        "training": {
            "epochs": args.epochs, "input_size": args.input_size,
            "batch_size": args.batch_size, "lr": args.lr,
            "quality_train_n": len(q_train), "defect_train_n": len(d_train),
            "wall_seconds": round(train_seconds, 1), "device": str(device),
            "history": history,
        }}

    for name, items in (("valid", q_val), ("test", q_test)):
        if not items:
            continue
        gt, pr, pb = evaluate(net, make_loader(items, args.input_size,
                                               args.batch_size, False, True),
                              device, True)
        metrics[f"quality_{name}"] = classification_metrics(gt, pr, pb, QUALITY_CLASSES)

    gt, pr, pb = evaluate(net, make_loader(d_val, args.input_size,
                                           args.batch_size, False, False),
                          device, False)
    metrics["defects_val_mmdet_carveout"] = binary_metrics(gt, pr, pb, BINARY_HEADS)

    # Latency / size
    net.eval()
    dummy = torch.randn(1, 3, args.input_size, args.input_size)
    with torch.no_grad():
        net(dummy)
        t0 = time.time()
        for _ in range(10):
            net(dummy)
        latency_ms = (time.time() - t0) / 10 * 1000

    args.out_dir.mkdir(parents=True, exist_ok=True)
    artifact = args.out_dir / f"attributes_v0.1_{args.input_size}px.pt"
    torch.save(net.state_dict(), artifact)
    size_mb = artifact.stat().st_size / 1e6
    try:
        artifact_rel = str(artifact.relative_to(PROJECT_ROOT))
    except ValueError:  # out-dir outside the repository (e.g. a temp debug run)
        artifact_rel = str(artifact)

    card = {
        "model_id": f"vision-attributes-v0.1-{split_mode}",
        "task": ["quality_class", "rotten", "sprout"],
        "architecture": describe()["architecture"],
        "dataset_fingerprint": reg.fingerprint(),
        "split": split_info,
        "trained_at": f"{date.today().isoformat()}",
        "artifact_path": artifact_rel,
        "input_size": [args.input_size, args.input_size],
        "artifact_size_mb": round(size_mb, 2),
        "cpu_latency_ms_per_image": round(latency_ms, 1),
        "host": f"{platform.system()} {platform.release()} / {platform.processor()}",
        "metrics": metrics,
        "training_data": {
            "quality": {"sources": [QUALITY_SOURCE], "license": "CC BY 4.0",
                        "splits_used": ["train", "valid", "test"]},
            "defects": {"sources": [DEFECT_SOURCE], "license": "Public Domain",
                        "note": "no official split; deterministic 80/20 carve-out"},
        },
        "limitations": [
            "Quality classes are the Roboflow commercial grades, not a verified government standard.",
            "Binary defect labels come from one source and one annotation protocol.",
            "No negative (non-onion) images were used; rejection is handled separately.",
            "CPU training on the available data; not field-validated.",
            "damaged/undersized/bruising/shelf-life are NOT modelled (no labels exist).",
            "The published 'valid' split leaks near-duplicates of train (85.2% measured); "
            "grouped-split metrics are the honest reference.",
        ],
    }
    (args.out_dir / "model_card.json").write_text(
        json.dumps(card, indent=2), encoding="utf-8")
    (args.out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in metrics.items() if k != "training"},
                     indent=2))
    print(f"\nSaved {artifact} ({size_mb:.2f} MB), latency "
          f"{latency_ms:.1f} ms/image on CPU")
    return 0


if __name__ == "__main__":
    sys.exit(main())
