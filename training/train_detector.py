#!/usr/bin/env python3
"""Train the onion instance detector on REAL boxes (no synthetic data).

Data
----
Every annotation box in the tracked COCO datasets describes an onion instance
(the quality classes in *Onion Grading v7* and the rotten/sprout classes in
*onions v1*), so this is a **single-class** detector: {0: background, 1: onion}.

Splitting (Phase C.2)
---------------------
``--split-file evaluation/detection_split.json`` (default when present) uses
the leak-safe grouped split built by ``scripts/audit_detection_dataset.py``:
whole near-duplicate families are kept together, verified 0 groups span two
splits. ``--split-file none`` falls back to the *official* source splits
(train/valid/test) for comparison only — that evaluation is leak-prone and is
never used for model selection.

Model choice (documented, audit §8)
-----------------------------------
``fasterrcnn_mobilenet_v3_large_320_fpn`` — torchvision's mobile-oriented
detector with a COCO-pretrained backbone. Why not YOLO: ``ultralytics`` is not
installed here and is a licence-distinct heavy dependency; torchvision is
already required, BSD-3-Clause, and exports to ONNX. Documented trade-off:
Faster R-CNN is heavier at inference than YOLO-nano; the export script exists
so the mobile team can re-host it in ONNX Runtime Mobile.

Training hygiene
----------------
* checkpoints every epoch: ``last.pt`` (crash recovery) and ``best.pt``
  (best validation AP@0.50:0.95) — an interrupted run never loses an hour;
* ``history.json`` is rewritten every epoch, so metrics survive a crash;
* early stopping on validation AP with ``--patience``;
* ``--resume`` continues from ``last.pt``;
* ``--limit-train`` supports the staged experiments (500 / 1000 / all).

Metrics are self-contained (no pycocotools): AP@0.50, AP@0.50:0.95 and
precision/recall/F1 at a tunable score threshold, plus PR-curve material and
false-positive / false-negative galleries for visual inspection.

Usage:
    python training/train_detector.py --model-id vision-detector-v0.2 \
        --epochs 8 --min-size 320 --batch-size 4
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data.dataset_registry import DatasetRegistry, default_registry  # noqa: E402

SEED = 42
ONION = "onion-grading-coco-segmentation"
MMDET = "onion-coco-mmdetection"
ARTIFACT_DIR = PROJECT_ROOT / "models" / "vision" / "detector"
DEFAULT_SPLIT_FILE = PROJECT_ROOT / "evaluation" / "detection_split.json"
DEFAULT_EVAL_DIR = PROJECT_ROOT / "evaluation"
TRAINABLE = (ONION, MMDET)


def set_seeds(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ------------------------------------------------------------------ data
def _usable_boxes(rec: dict) -> Tuple[List[List[float]], List[str]]:
    """COCO [x, y, w, h] boxes that survive sanity filtering."""
    boxes: List[List[float]] = []
    categories: List[str] = []
    img_w = float(rec.get("width") or 0)
    img_h = float(rec.get("height") or 0)
    for ann in rec["annotations"]:
        bbox = ann.get("bbox")
        if not bbox or len(bbox) != 4 or ann.get("iscrowd"):
            continue
        x, y, bw, bh = (float(v) for v in bbox)
        # Degenerate/zero-area annotations exist in the source data (found by
        # running training, not by assumption) and break the box assertion.
        if bw < 2.0 or bh < 2.0:
            continue
        if img_w and img_h:
            x = max(0.0, min(x, img_w - 1))
            y = max(0.0, min(y, img_h - 1))
            bw = min(bw, img_w - x)
            bh = min(bh, img_h - y)
        if bw < 2.0 or bh < 2.0:
            continue
        boxes.append([x, y, bw, bh])
        categories.append(str(ann.get("category")))
    return boxes, categories


def all_annotated_samples(reg: DatasetRegistry) -> List[dict]:
    """Every annotated image of the two trainable sources, deterministic order."""
    out: List[dict] = []
    for src in reg.sources():
        if src.source_group not in TRAINABLE:
            continue
        for rec in reg.records(src):
            boxes, cats = _usable_boxes(rec)
            if not boxes:
                continue
            out.append({
                "image_path": rec["image_path"],
                "source": src.source_group,
                "source_split": src.split,
                "boxes": boxes,
                "categories": cats,
            })
    return out


def apply_split_file(samples: List[dict], split_file: Path,
                     only_splits: Optional[Tuple[str, ...]] = None) -> Dict[str, List[dict]]:
    """Assign samples using the leak-safe grouped split file."""
    data = json.loads(Path(split_file).read_text(encoding="utf-8"))
    assignment = data["assignment"]
    key_alias = {}
    for sample in samples:
        key_alias[str(Path(sample["image_path"]).resolve())] = str(sample["image_path"])

    out: Dict[str, List[dict]] = {"train": [], "validation": [], "test": []}
    missing = 0
    for sample in samples:
        raw = str(sample["image_path"])
        target = assignment.get(raw)
        if target is None:
            # The split file is keyed by the path string produced on the same
            # machine; tolerate separators differing between runs.
            target = assignment.get(raw.replace("\\", "/"))
        if target is None:
            target = assignment.get(key_alias.get(str(Path(raw).resolve()), ""))
        if target is None:
            missing += 1
            continue
        out.setdefault(target, []).append(sample)
    if missing:
        raise SystemExit(
            f"{missing}/{len(samples)} images are absent from {split_file}; "
            "regenerate it with scripts/audit_detection_dataset.py")
    if only_splits:
        out = {k: v for k, v in out.items() if k in only_splits}
    return out


def gather_official_splits(reg: DatasetRegistry) -> Dict[str, List[dict]]:
    """Official source splits — kept for comparison, not for model selection."""
    out: Dict[str, List[dict]] = {"train": [], "validation": [], "test": []}
    for src in reg.sources():
        if src.source_group not in TRAINABLE:
            continue
        target = {"train": "train", "valid": "validation", "test": "test"}.get(src.split)
        if target is None:
            continue
        for rec in reg.records(src):
            boxes, cats = _usable_boxes(rec)
            if not boxes:
                continue
            out[target].append({
                "image_path": rec["image_path"],
                "source": src.source_group,
                "source_split": src.split,
                "boxes": boxes,
                "categories": cats,
            })
    return out


def build_model(num_classes: int = 2, pretrained: bool = True):
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn)
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    weights = (FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.COCO_V1
               if pretrained else None)
    model = fasterrcnn_mobilenet_v3_large_320_fpn(weights=weights)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


class DetectionDataset(torch.utils.data.Dataset):
    """Yields (image_tensor, target) with xyxy boxes."""

    def __init__(self, samples: List[dict], min_size: int = 320):
        self.samples = samples
        self.min_size = min_size

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        from PIL import Image
        from torchvision.transforms import functional as F
        s = self.samples[idx]
        img = Image.open(s["image_path"]).convert("RGB")
        w, h = img.size
        scale = 1.0
        if max(w, h) > self.min_size:
            scale = self.min_size / max(w, h)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        tensor = F.to_tensor(img)
        new_w, new_h = img.size

        # Source boxes are COCO [x, y, w, h]; torchvision needs [x1, y1, x2, y2].
        # Both the conversion AND the scaling must happen here — getting either
        # wrong makes the detector assert on "positive height and width".
        xyxy = []
        for x, y, bw, bh in s["boxes"]:
            x1 = max(0.0, x * scale)
            y1 = max(0.0, y * scale)
            x2 = min(float(new_w), (x + bw) * scale)
            y2 = min(float(new_h), (y + bh) * scale)
            if x2 - x1 < 2.0 or y2 - y1 < 2.0:
                continue
            xyxy.append([x1, y1, x2, y2])

        boxes = torch.tensor(xyxy, dtype=torch.float32) if xyxy else \
            torch.zeros((0, 4), dtype=torch.float32)
        labels = torch.ones((boxes.shape[0],), dtype=torch.int64)
        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([idx]),
            "area": boxes[:, 2] * boxes[:, 3] if boxes.numel() else torch.zeros(0),
            "iscrowd": torch.zeros((boxes.shape[0],), dtype=torch.int64),
        }
        return tensor, target


def collate(batch):
    """Keep only samples that still have at least one valid box."""
    kept = [(img, tgt) for img, tgt in batch if tgt["boxes"].shape[0] > 0]
    if not kept:
        return tuple(), tuple()
    return tuple(zip(*kept))


# --------------------------------------------------------------- metrics
def iou_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """IoU between xyxy boxes a (N,4) and b (M,4)."""
    a = np.asarray(a, dtype=float).reshape(-1, 4)
    b = np.asarray(b, dtype=float).reshape(-1, 4)
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    ax1, ay1, ax2, ay2 = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    bx1, by1, bx2, by2 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    ix1 = np.maximum(ax1[:, None], bx1[None, :])
    iy1 = np.maximum(ay1[:, None], by1[None, :])
    ix2 = np.minimum(ax2[:, None], bx2[None, :])
    iy2 = np.minimum(ay2[:, None], by2[None, :])
    iw = np.clip(ix2 - ix1, 0, None)
    ih = np.clip(iy2 - iy1, 0, None)
    inter = iw * ih
    area_a = np.clip(ax2 - ax1, 0, None) * np.clip(ay2 - ay1, 0, None)
    area_b = np.clip(bx2 - bx1, 0, None) * np.clip(by2 - by1, 0, None)
    union = area_a[:, None] + area_b[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


def average_precision(dets: List[dict], gts: List[dict], iou_thr: float) -> float:
    """Single-class AP via COCO-style all-point interpolation."""
    n_gt = sum(len(g["boxes"]) for g in gts)
    if n_gt == 0:
        return float("nan")
    all_dets = []
    for img_idx, d in enumerate(dets):
        for box, score in zip(d["boxes"], d["scores"]):
            all_dets.append((score, img_idx, box))
    all_dets.sort(key=lambda x: -x[0])
    matched = {i: np.zeros(len(g["boxes"]), dtype=bool) for i, g in enumerate(gts)}
    tp = np.zeros(len(all_dets))
    fp = np.zeros(len(all_dets))
    for k, (_, img_idx, box) in enumerate(all_dets):
        gboxes = np.asarray(gts[img_idx]["boxes"], dtype=float).reshape(-1, 4)
        if len(gboxes) == 0:
            fp[k] = 1
            continue
        ious = iou_matrix([box], gboxes)[0]
        best = int(np.argmax(ious))
        if ious[best] >= iou_thr and not matched[img_idx][best]:
            tp[k] = 1
            matched[img_idx][best] = True
        else:
            fp[k] = 1
    if tp.sum() == 0:
        return 0.0
    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)
    recall = tp_cum / n_gt
    precision = tp_cum / np.maximum(tp_cum + fp_cum, 1e-9)
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([0.0], precision, [0.0]))
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def pr_points(dets: List[dict], gts: List[dict], iou_thr: float = 0.5,
              max_points: int = 200) -> dict:
    """Material for a precision-recall / confidence-threshold curve."""
    n_gt = sum(len(g["boxes"]) for g in gts)
    if n_gt == 0:
        return {"recall": [], "precision": [], "score": []}
    entries = []
    for img_idx, d in enumerate(dets):
        for box, score in zip(d["boxes"], d["scores"]):
            entries.append((float(score), img_idx, box))
    entries.sort(key=lambda x: -x[0])
    matched = {i: np.zeros(len(g["boxes"]), dtype=bool) for i, g in enumerate(gts)}
    tp = np.zeros(len(entries))
    fp = np.zeros(len(entries))
    for k, (_, img_idx, box) in enumerate(entries):
        gboxes = np.asarray(gts[img_idx]["boxes"], dtype=float).reshape(-1, 4)
        if len(gboxes) == 0:
            fp[k] = 1
            continue
        ious = iou_matrix([box], gboxes)[0]
        best = int(np.argmax(ious))
        if ious[best] >= iou_thr and not matched[img_idx][best]:
            tp[k] = 1
            matched[img_idx][best] = True
        else:
            fp[k] = 1
    if len(entries) == 0:
        return {"recall": [], "precision": [], "score": []}
    tp_cum, fp_cum = np.cumsum(tp), np.cumsum(fp)
    recall = (tp_cum / n_gt).tolist()
    precision = (tp_cum / np.maximum(tp_cum + fp_cum, 1e-9)).tolist()
    scores = [e[0] for e in entries]
    step = max(1, len(entries) // max_points)
    return {
        "recall": [round(r, 4) for r in recall[::step]],
        "precision": [round(p, 4) for p in precision[::step]],
        "score": [round(s, 4) for s in scores[::step]],
        "iou_threshold": iou_thr,
        "n_gt": n_gt,
    }


def score_sweep(dets: List[dict], gts: List[dict]) -> List[dict]:
    """Precision/recall/F1 as the confidence threshold moves."""
    out = []
    for thr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        m = precision_recall_at(dets, gts, thr)
        out.append({"score_threshold": thr,
                    "precision": round(m["precision"], 4),
                    "recall": round(m["recall"], 4),
                    "f1": round(m["f1"], 4)})
    return out


def precision_recall_at(dets: List[dict], gts: List[dict],
                        score_thr: float = 0.5, iou_thr: float = 0.5) -> dict:
    tp = fp = fn = 0
    for d, g in zip(dets, gts):
        boxes = np.asarray(d["boxes"], dtype=float).reshape(-1, 4)
        scores = np.asarray(d["scores"], dtype=float)
        keep = boxes[scores >= score_thr] if len(boxes) else boxes
        gboxes = np.asarray(g["boxes"], dtype=float).reshape(-1, 4)
        if len(gboxes) == 0:
            fp += len(keep)
            continue
        matched = np.zeros(len(gboxes), dtype=bool)
        for box in keep:
            ious = iou_matrix([box], gboxes)[0]
            best = int(np.argmax(ious))
            if ious[best] >= iou_thr and not matched[best]:
                matched[best] = True
                tp += 1
            else:
                fp += 1
        fn += int((~matched).sum())
    precision = tp / max(tp + fp, 1e-9)
    recall = tp / max(tp + fn, 1e-9)
    return {"precision": precision, "recall": recall,
            "f1": 2 * precision * recall / max(precision + recall, 1e-9),
            "tp": tp, "fp": fp, "fn": fn}


def collect_predictions(model, loader, device, score_floor: float = 0.05
                        ) -> Tuple[List[dict], List[dict], List[int], List[dict]]:
    """Run inference once; return dets, gts, dataset indices and raw outputs.

    The third element maps each returned prediction back to
    ``loader.dataset.samples`` so galleries stay correct even when the
    collate step drops a box-less sample.
    """
    model.eval()
    dets: List[dict] = []
    gts: List[dict] = []
    sample_ids: List[int] = []
    raw: List[dict] = []
    with torch.no_grad():
        for images, targets in loader:
            if not images:
                continue
            outputs = model([img.to(device) for img in images])
            for out, tgt in zip(outputs, targets):
                boxes = out["boxes"].cpu().numpy()
                scores = out["scores"].cpu().numpy()
                keep = scores >= score_floor
                dets.append({"boxes": boxes[keep].tolist(),
                             "scores": scores[keep].tolist()})
                # DetectionDataset returns loader-scaled xyxy for both model
                # input and GT, and torchvision's postprocess maps boxes back to
                # the input tensor size — so the two stay aligned.
                gts.append({"boxes": tgt["boxes"].numpy().tolist()})
                raw.append({"boxes": boxes.tolist(), "scores": scores.tolist()})
                sample_ids.append(int(tgt["image_id"][0]))
    return dets, gts, sample_ids, raw


def evaluate_detector(model, loader, device, score_thr: float = 0.5) -> dict:
    dets, gts, _, _ = collect_predictions(model, loader, device)
    aps = {thr: average_precision(dets, gts, thr) for thr in (0.5, 0.75)}
    ap5095 = float(np.nanmean([average_precision(dets, gts, t)
                               for t in np.arange(0.5, 0.96, 0.05)]))
    pr = precision_recall_at(dets, gts, score_thr)
    return {
        "AP@0.50": round(float(aps[0.5]), 4),
        "AP@0.75": round(float(aps[0.75]), 4),
        "AP@0.50:0.95": round(ap5095, 4),
        "precision@0.5score": round(pr["precision"], 4),
        "recall@0.5score": round(pr["recall"], 4),
        "f1@0.5score": round(pr["f1"], 4),
        "tp": pr["tp"], "fp": pr["fp"], "fn": pr["fn"],
        "score_threshold": score_thr,
        "n_images": len(gts),
        "n_gt_boxes": int(sum(len(g["boxes"]) for g in gts)),
    }


def write_error_gallery(samples: List[dict], dets: List[dict], gts: List[dict],
                        out_dir: Path, min_size: int, limit: int = 6,
                        sample_ids: Optional[List[int]] = None) -> dict:
    """Save JPEGs of false positives / false negatives / localisation errors."""
    import cv2
    out_dir.mkdir(parents=True, exist_ok=True)
    if sample_ids is not None:
        samples = [samples[i] for i in sample_ids]
    fp_items, fn_items, loc_items = [], [], []
    for idx, (d, g) in enumerate(zip(dets, gts)):
        boxes = np.asarray(d["boxes"], dtype=float).reshape(-1, 4)
        scores = np.asarray(d["scores"], dtype=float)
        keep = boxes[scores >= 0.5] if len(boxes) else boxes
        gboxes = np.asarray(g["boxes"], dtype=float).reshape(-1, 4)
        matched = np.zeros(len(gboxes), dtype=bool)
        n_fp = 0
        for box in keep:
            if len(gboxes) == 0:
                n_fp += 1
                continue
            ious = iou_matrix([box], gboxes)[0]
            best = int(np.argmax(ious))
            if ious[best] >= 0.5 and not matched[best]:
                matched[best] = True
            elif ious[best] >= 0.1:
                loc_items.append((idx, box, gboxes[best]))
            else:
                n_fp += 1
        if n_fp:
            fp_items.append(idx)
        if (~matched).any():
            fn_items.append(idx)

    def draw(idx: int, boxes: List[np.ndarray], gts_: List[np.ndarray], name: str):
        from PIL import Image
        img = Image.open(samples[idx]["image_path"]).convert("RGB")
        w, h = img.size
        scale = 1.0
        if max(w, h) > min_size:
            scale = min_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)))
        canvas = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        for b in boxes:
            x1, y1, x2, y2 = [int(v) for v in b]
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)
        for b in gts_:
            x1, y1, x2, y2 = [int(v) for v in b]
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 200, 0), 1)
        cv2.imwrite(str(out_dir / name), canvas)

    for i, idx in enumerate(fp_items[:limit]):
        d = dets[idx]
        boxes = np.asarray(d["boxes"], dtype=float).reshape(-1, 4)
        scores = np.asarray(d["scores"], dtype=float)
        draw(idx, boxes[scores >= 0.5], np.asarray(gts[idx]["boxes"], dtype=float)
             .reshape(-1, 4), f"false_positive_{i:02d}.jpg")
    for i, idx in enumerate(fn_items[:limit]):
        d = dets[idx]
        boxes = np.asarray(d["boxes"], dtype=float).reshape(-1, 4)
        scores = np.asarray(d["scores"], dtype=float)
        draw(idx, boxes[scores >= 0.5], np.asarray(gts[idx]["boxes"], dtype=float)
             .reshape(-1, 4), f"false_negative_{i:02d}.jpg")
    for i, (idx, det, gt) in enumerate(loc_items[:limit]):
        draw(idx, [det], [gt], f"localisation_error_{i:02d}.jpg")

    return {"dir": str(out_dir), "false_positives": len(fp_items),
            "false_negatives": len(fn_items),
            "localisation_errors": len(loc_items),
            "images_saved": min(len(fp_items), limit) + min(len(fn_items), limit)
                            + min(len(loc_items), limit)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-id", default="vision-detector-v0.2")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--valid-max", type=int, default=0,
                    help="cap validation images (0 = all)")
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--min-size", type=int, default=320)
    ap.add_argument("--limit-train", type=int, default=0,
                    help="staged experiment: train on the first N images (0 = all)")
    ap.add_argument("--eval-every", type=int, default=1)
    ap.add_argument("--patience", type=int, default=3,
                    help="early-stop after N epochs without validation improvement")
    ap.add_argument("--split-file", default=str(DEFAULT_SPLIT_FILE),
                    help="leak-safe split JSON, or 'none' for official splits")
    ap.add_argument("--out-dir", type=Path, default=ARTIFACT_DIR)
    ap.add_argument("--resume", action="store_true",
                    help="continue from <out-dir>/last.pt")
    ap.add_argument("--eval-only", action="store_true",
                    help="load <out-dir>/best.pt and only evaluate + write galleries")
    ap.add_argument("--weights", default=None,
                    help="with --eval-only: evaluate THIS checkpoint instead of "
                         "<out-dir>/best.pt (used to score the preserved "
                         "baseline on the same leak-safe split as a candidate)")
    ap.add_argument("--no-pretrained", action="store_true")
    ap.add_argument("--gallery-dir", type=Path, default=None,
                    help="where error galleries are written (default: "
                         "evaluation/detector_gallery; give a distinct dir when "
                         "evaluating an older checkpoint so v0.2 galleries "
                         "are not overwritten)")
    args = ap.parse_args()

    set_seeds()
    device = torch.device("cpu")
    reg = default_registry()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    eval_dir = args.gallery_dir or DEFAULT_EVAL_DIR

    samples = all_annotated_samples(reg)
    split_file = None if str(args.split_file).lower() == "none" else Path(args.split_file)
    if split_file and split_file.exists():
        parts = apply_split_file(samples, split_file)
        split_source = str(split_file)
        split_kind = "grouped_leak_safe"
    else:
        if split_file:
            print(f"WARNING: {split_file} not found — falling back to official "
                  "splits (leak-prone, comparison only)", file=sys.stderr)
        parts = gather_official_splits(reg)
        split_source = "official_source_splits"
        split_kind = "official_leak_prone"
    if args.valid_max:
        parts["validation"] = parts["validation"][: args.valid_max]
        parts["test"] = parts["test"][: args.valid_max]
    if args.limit_train:
        parts["train"] = parts["train"][: args.limit_train]

    print(f"detector samples — train {len(parts['train'])}, "
          f"valid {len(parts['validation'])}, test {len(parts['test'])} "
          f"(split={split_kind})", flush=True)
    if not parts["train"]:
        print("ERROR: no labelled training boxes found.", file=sys.stderr)
        return 1

    train_loader = torch.utils.data.DataLoader(
        DetectionDataset(parts["train"], args.min_size),
        batch_size=args.batch_size, shuffle=True,
        collate_fn=collate, num_workers=0)
    valid_loader = torch.utils.data.DataLoader(
        DetectionDataset(parts["validation"], args.min_size),
        batch_size=1, shuffle=False, collate_fn=collate, num_workers=0)
    test_loader = torch.utils.data.DataLoader(
        DetectionDataset(parts["test"], args.min_size),
        batch_size=1, shuffle=False, collate_fn=collate, num_workers=0)

    model = build_model(pretrained=not args.no_pretrained).to(device)
    history: List[dict] = []
    start_epoch = 1

    last_path = args.out_dir / "last.pt"
    best_path = args.out_dir / "best.pt"
    history_path = args.out_dir / "history.json"
    if args.resume and last_path.exists():
        state = torch.load(last_path, map_location=device, weights_only=False)
        model.load_state_dict(state["model"])
        history = state.get("history", [])
        start_epoch = int(state.get("epoch", 0)) + 1
        print(f"resumed from {last_path} at epoch {start_epoch}", flush=True)

    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=args.lr, weight_decay=1e-4)

    best_score = max((h.get("valid", {}).get("AP@0.50:0.95", -1.0)
                      for h in history), default=-1.0)
    epochs_without_gain = 0
    started = time.time()

    eval_source = Path(args.weights) if args.weights else best_path
    if args.eval_only and not eval_source.exists():
        print(f"ERROR: --eval-only but no checkpoint at {eval_source}",
              file=sys.stderr)
        return 2

    if not (args.eval_only and eval_source.exists()):
        for epoch in range(start_epoch, args.epochs + 1):
            model.train()
            running = 0.0
            steps = 0
            epoch_started = time.time()
            for step, (images, targets) in enumerate(train_loader, 1):
                if not images:
                    continue
                images = [img.to(device) for img in images]
                targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
                loss_dict = model(images, targets)
                loss = sum(loss_dict.values())
                opt.zero_grad()
                loss.backward()
                opt.step()
                running += float(loss.item())
                steps += 1
                if step % 25 == 0:
                    print(f"  epoch {epoch} step {step}/{len(train_loader)} "
                          f"loss={running / max(steps, 1):.4f}", flush=True)

            entry = {"epoch": epoch,
                     "mean_loss": round(running / max(steps, 1), 4),
                     "epoch_seconds": round(time.time() - epoch_started, 1)}
            improved = False
            if epoch % args.eval_every == 0 and parts["validation"]:
                vm = evaluate_detector(model, valid_loader, device)
                entry["valid"] = vm
                score = vm["AP@0.50:0.95"]
                entry["selection_metric"] = score
                improved = score > best_score
                if improved:
                    best_score = score
                    torch.save({"model": model.state_dict(), "epoch": epoch,
                                "history": history + [entry],
                                "model_id": args.model_id,
                                "split_source": split_source}, best_path)
                    epochs_without_gain = 0
                else:
                    epochs_without_gain += 1
                print(f"epoch {epoch}: loss={entry['mean_loss']} "
                      f"AP@0.50={vm['AP@0.50']} AP@0.50:0.95={vm['AP@0.50:0.95']} "
                      f"best={best_score:.4f} "
                      f"({entry['epoch_seconds']}s)", flush=True)
            else:
                print(f"epoch {epoch}: loss={entry['mean_loss']} "
                      f"({entry['epoch_seconds']}s)", flush=True)

            history.append(entry)
            history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
            # Crash-safe: always keep a resumable checkpoint.
            torch.save({"model": model.state_dict(), "epoch": epoch,
                        "history": history, "model_id": args.model_id,
                        "split_source": split_source}, last_path)
            (args.out_dir / "training_config.json").write_text(json.dumps({
                "model_id": args.model_id, "epochs": args.epochs,
                "batch_size": args.batch_size, "lr": args.lr,
                "min_size": args.min_size, "limit_train": args.limit_train,
                "split_source": split_source, "split_kind": split_kind,
                "patience": args.patience, "seed": SEED,
                "dataset_fingerprint": reg.fingerprint(),
            }, indent=2), encoding="utf-8")

            if args.patience and epochs_without_gain >= args.patience:
                print(f"early stop: no validation improvement for "
                      f"{epochs_without_gain} epoch(s)", flush=True)
                break

    train_seconds = time.time() - started

    eval_weights = Path(args.weights) if args.weights else best_path
    if eval_weights.exists():
        state = torch.load(eval_weights, map_location=device, weights_only=False)
        model.load_state_dict(state["model"] if "model" in state else state)
        selected_epoch = state.get("epoch") if isinstance(state, dict) else None
    else:
        selected_epoch = None
        torch.save({"model": model.state_dict(), "epoch": start_epoch,
                    "history": history, "model_id": args.model_id}, best_path)

    metrics: Dict[str, object] = {"training": {
        "model_id": args.model_id,
        "epochs_requested": args.epochs,
        "selected_epoch": selected_epoch,
        "batch_size": args.batch_size, "lr": args.lr,
        "min_size": args.min_size, "train_images": len(parts["train"]),
        "valid_images": len(parts["validation"]),
        "test_images": len(parts["test"]),
        "wall_seconds": round(train_seconds, 1), "device": str(device),
        "split_source": split_source, "split_kind": split_kind,
        "history": history,
    }}

    if parts["validation"]:
        vd, vg, _, _ = collect_predictions(model, valid_loader, device)
        metrics["validation"] = evaluate_detector(model, valid_loader, device)
        metrics["validation"]["pr_curve"] = pr_points(vd, vg)
        metrics["validation"]["score_sweep"] = score_sweep(vd, vg)
    if parts["test"]:
        td, tg, tids, _ = collect_predictions(model, test_loader, device)
        metrics["test"] = evaluate_detector(model, test_loader, device)
        metrics["test"]["pr_curve"] = pr_points(td, tg)
        metrics["test"]["score_sweep"] = score_sweep(td, tg)
        gallery = write_error_gallery(parts["test"], td, tg,
                                      eval_dir / "detector_gallery", args.min_size,
                                      sample_ids=tids)
        metrics["error_gallery"] = gallery

    # Latency on one real test image.
    from PIL import Image
    from torchvision.transforms import functional as F
    ref = (parts["test"] or parts["validation"] or parts["train"])[0]
    sample_img = Image.open(ref["image_path"]).convert("RGB")
    w, h = sample_img.size
    if max(w, h) > args.min_size:
        s = args.min_size / max(w, h)
        sample_img = sample_img.resize((int(w * s), int(h * s)))
    tensor = F.to_tensor(sample_img)
    model.eval()
    timings = []
    with torch.no_grad():
        model([tensor])
        for _ in range(5):
            t0 = time.time()
            model([tensor])
            timings.append((time.time() - t0) * 1000)
    latency_ms = float(np.median(timings))
    metrics["latency"] = {
        "cpu_median_ms": round(latency_ms, 1),
        "cpu_p95_ms": round(float(np.percentile(timings, 95)), 1),
        "n_runs": len(timings),
        "input_long_side_px": args.min_size,
        "device": str(device),
    }

    # Selected-threshold recommendation from the validation sweep.
    sweep = metrics.get("validation", {}).get("score_sweep", [])
    if sweep:
        best = max(sweep, key=lambda s: s["f1"])
        metrics["recommended_threshold"] = {
            "score_threshold": best["score_threshold"],
            "precision": best["precision"], "recall": best["recall"],
            "f1": best["f1"],
            "note": "Chosen by validation F1 only; deployment may prefer higher "
                    "recall (review zone) — see docs/DETECTOR_EXPERIMENTS.md.",
        }

    artifact = eval_source if args.eval_only else best_path
    size_mb = artifact.stat().st_size / 1e6

    try:
        artifact_rel = str(artifact.relative_to(PROJECT_ROOT))
    except ValueError:
        artifact_rel = str(artifact)

    card = {
        "model_id": args.model_id,
        "task": "onion_instance_detection",
        "architecture": "torchvision fasterrcnn_mobilenet_v3_large_320_fpn",
        "classes": {"0": "background", "1": "onion"},
        "dataset_fingerprint": reg.fingerprint(),
        "split_strategy": split_kind,
        "split_source": split_source,
        "evaluated_weights": str(artifact),
        "training_config_file": str(args.out_dir / "training_config.json"),
        "trained_at": date.today().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_path": artifact_rel,
        "artifact_size_mb": round(size_mb, 2),
        "cpu_latency_ms_per_image": round(latency_ms, 1),
        "host": f"{platform.system()} {platform.release()} / {platform.processor()}",
        "metrics": metrics,
        "training_data": {
            "sources": list(TRAINABLE),
            "licenses": {"onion-grading-coco-segmentation": "CC BY 4.0",
                         "onion-coco-mmdetection": "Public Domain"},
            "split_counts": {k: len(v) for k, v in parts.items()},
        },
        "limitations": [
            "Single-class (onion) detector; no non-onion object classes trained.",
            "CPU training; not field-validated on procurement hardware.",
            "Metrics are valid only on the leak-safe grouped split recorded here.",
            "No mobile latency measured (desktop CPU only).",
        ],
    }
    (args.out_dir / "model_card.json").write_text(json.dumps(card, indent=2),
                                                  encoding="utf-8")
    (args.out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2),
                                                encoding="utf-8")
    print(json.dumps({k: v for k, v in metrics.items()
                      if k not in ("training",)}, indent=2)[:2000])
    print(f"\nSaved {artifact} ({size_mb:.2f} MB), latency "
          f"{latency_ms:.0f} ms/image (CPU, {args.min_size}px long side)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
