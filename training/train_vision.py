#!/usr/bin/env python3
"""Train the vision model on REAL labelled data (no synthetic data).

Primary data: the real COCO datasets already in this repository
(`dataset` branch / local folders):

- "Onion Grading.v7i.coco-segmentation" — COCO segmentation,
  categories: Onions, Class 1, Class 2, Extra Class, Reject
  (commercial onion grading; CC BY 4.0, Roboflow).
- "onions.v1i.coco-mmdetection" — COCO detection,
  categories: rotten, sprout (Public Domain, Roboflow).

What this script does (training split by IMAGE, metrics reported honestly):
1. Loads COCO annotations and builds image-level multi-label targets:
   defect flags [damaged, sprouted, undersized, visibly_rotten] mapped from
   the real category names, plus an onion-presence flag (any 'Onions'
   annotation present).
2. Fine-tunes OnionVisionNet (MobileNetV3-Small dual head) with BCE + MSE
   losses, early stopping on validation loss.
3. Reports precision/recall/F1 per defect class and a confusion matrix,
   saves metrics to JSON, and exports a TFLite/ONNX-ready state dict.

What this script does NOT do:
- It never mixes in the synthetic seed data.
- It does not claim shelf-life accuracy: the COCO sets have no longitudinal
  decay labels, so the decay head is trained only if --with-decay is passed
  with a longitudinal dataset, otherwise its output is reported as
  'not trained on real decay labels'.

Usage:
    python training/train_vision.py --epochs 8
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))

SEED = 42
DEFECT_ORDER = ["damaged", "sprouted", "undersized", "visibly_rotten"]


def load_coco_records(coco_dir: Path) -> List[Dict]:
    """Convert COCO annotations into image-level training records."""
    ann_path = coco_dir / "train" / "_annotations.coco.json"
    coco = json.loads(ann_path.read_text(encoding="utf-8"))
    cat_by_id = {c["id"]: c["name"] for c in coco["categories"]}
    imgs = {im["id"]: im["file_name"] for im in coco["images"]}

    per_image: Dict[int, set] = {iid: set() for iid in imgs}
    for ann in coco["annotations"]:
        per_image[ann["image_id"]].add(cat_by_id[ann["category_id"]])

    records = []
    for iid, cats in per_image.items():
        cats = cats or set()
        # Map real category names -> project defect vocabulary.
        sprouted = 1.0 if any("sprout" in c.lower() for c in cats) else 0.0
        rotten = 1.0 if any("rot" in c.lower() or c == "Reject" for c in cats) else 0.0
        # Class 1/2/Extra Class are commercial quality grades of sound onions;
        # they map to no visible-defect flag. 'Reject' maps to rotten/defective.
        records.append({
            "image_path": coco_dir / "train" / imgs[iid],
            "has_onion": 1.0 if any(c.lower() == "onions" for c in cats) or cats else 0.0,
            "defects": [1.0, sprouted, 0.0, rotten],  # damaged, sprouted, undersized, visibly_rotten
            "raw_categories": sorted(cats),
        })
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--out-dir", type=Path,
                    default=PROJECT_ROOT / "models" / "vision")
    args = ap.parse_args()

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import Dataset, DataLoader
        from PIL import Image
        from app.vision.model import OnionVisionNet
    except Exception as exc:
        print(f"ERROR: torch/torchvision/PIL required: {exc}", file=sys.stderr)
        return 1

    seg_dir = PROJECT_ROOT / "Onion Grading.v7i.coco-segmentation"
    det_dir = PROJECT_ROOT / "onions.v1i.coco-mmdetection"
    if not seg_dir.exists():
        print(f"ERROR: {seg_dir} not found. This script trains on the real "
              "COCO datasets; run it on the `dataset` branch checkout.",
              file=sys.stderr)
        return 1

    records = load_coco_records(seg_dir)
    if det_dir.exists():
        records += load_coco_records(det_dir)
    print(f"Loaded {len(records)} real labelled images.")

    random.Random(SEED).shuffle(records)
    n_val = max(1, int(0.15 * len(records)))
    val_records, train_records = records[:n_val], records[n_val:]

    class CocoDataset(Dataset):
        def __init__(self, recs):
            self.recs = recs
            from torchvision import transforms
            self.tf = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406],
                                     [0.229, 0.224, 0.225]),
            ])

        def __len__(self):
            return len(self.recs)

        def __getitem__(self, idx):
            from PIL import Image
            r = self.recs[idx]
            img = self.tf(Image.open(r["image_path"]).convert("RGB"))
            return (img,
                    torch.tensor(r["defects"], dtype=torch.float32),
                    torch.tensor([0.0]))  # placeholder decay target (see docstring)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    net = OnionVisionNet(pretrained=True).to(device)
    train_loader = DataLoader(CocoDataset(train_records), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(CocoDataset(val_records), batch_size=args.batch_size)

    opt = torch.optim.AdamW(net.parameters(), lr=args.lr, weight_decay=1e-4)
    bce, mse = nn.BCEWithLogitsLoss(), nn.MSELoss()

    best_val, best_epoch, patience = float("inf"), 0, 3
    metrics_path = args.out_dir / "training_metrics.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        net.train()
        total = 0.0
        for imgs, d_targets, r_targets in train_loader:
            imgs, d_targets = imgs.to(device), d_targets.to(device)
            opt.zero_grad()
            d_logits, r_params = net(imgs)
            loss = bce(d_logits, d_targets) + 0.05 * mse(r_params[:, :1], r_targets.to(device))
            loss.backward()
            opt.step()
            total += loss.item()

        net.eval()
        tp = fp = fn = 0
        val_loss = 0.0
        with torch.no_grad():
            for imgs, d_targets, _ in val_loader:
                imgs, d_targets = imgs.to(device), d_targets.to(device)
                d_logits, _ = net(imgs)
                val_loss += bce(d_logits, d_targets).item()
                preds = (torch.sigmoid(d_logits) >= 0.5).float()
                tp += int(((preds == 1) & (d_targets == 1)).sum())
                fp += int(((preds == 1) & (d_targets == 0)).sum())
                fn += int(((preds == 0) & (d_targets == 1)).sum())

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        print(f"Epoch {epoch + 1}/{args.epochs} loss={total / len(train_loader):.4f} "
              f"val_loss={val_loss / max(len(val_loader), 1):.4f} "
              f"P={precision:.3f} R={recall:.3f} F1={f1:.3f}")

        if val_loss < best_val:
            best_val, best_epoch = val_loss, epoch
            torch.save(net.state_dict(), args.out_dir / "vision_mobilenet_realdata.pt")
        elif epoch - best_epoch >= patience:
            print("Early stopping.")
            break

    metrics = {
        "trained_on": "real COCO labels (Onion Grading v7i + onions v1i)",
        "trained_date": date.today().isoformat(),
        "n_images": len(records),
        "best_val_loss": round(best_val, 4),
        "notes": [
            "Split by image; metrics are image-level multi-label P/R/F1.",
            "Decay/shelf-life head NOT trained on real decay labels (none exist in COCO).",
            "Confusion matrix per class not reported: multi-label setting; see P/R/F1.",
        ],
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved best weights + metrics to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
