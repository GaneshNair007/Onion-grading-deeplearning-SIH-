#!/usr/bin/env python3
"""Audit the detection training data and build a leak-safe detector split.

Outputs
-------
evaluation/detection_dataset_audit.json
    boxes, geometry, degenerate/duplicate annotations, empty images,
    near-duplicate groups, source and label distributions.
evaluation/detection_split.json
    deterministic leak-free train/validation/test assignment over **every**
    annotated image of the two trainable sources, grouped by near-duplicate
    family so augmented siblings never straddle a split.

Why this exists: the attribute-model experiment proved that the official
Roboflow ``valid`` split leaks near-duplicates of ``train`` (85.2 % measured,
see evaluation/split_leakage.json). A split named "valid" is not evidence of
anything, so the detector gets the same grouped treatment.

Usage:
    python scripts/audit_detection_dataset.py [--threshold 0.98] [--no-split]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.dataset_registry import default_registry  # noqa: E402
from src.data.splits import (  # noqa: E402
    cluster_near_duplicates,
    embed_images,
    grouped_split,
    split_summary,
)

TRAINABLE = ("onion-grading-coco-segmentation", "onion-coco-mmdetection")
MIN_BOX_PX = 2.0
TINY_AREA_FRACTION = 5e-4
DUP_IOU = 0.95


def collect(reg) -> tuple[list[dict], list[dict]]:
    """Every annotated image (with boxes) and every annotation (with stats)."""
    images: List[dict] = []
    anns: List[dict] = []
    for src in reg.sources():
        if src.source_group not in TRAINABLE:
            continue
        for rec in reg.records(src):
            img_w = float(rec.get("width") or 0)
            img_h = float(rec.get("height") or 0)
            boxes = []
            for ann in rec["annotations"]:
                bbox = ann.get("bbox")
                row = {
                    "source": src.source_group,
                    "split": src.split,
                    "file_name": rec["file_name"],
                    "category": ann.get("category"),
                    "bbox": bbox,
                    "area": ann.get("area"),
                    "iscrowd": ann.get("iscrowd", 0),
                    "has_segmentation": bool(ann.get("segmentation")),
                }
                if not bbox or len(bbox) != 4:
                    row.update(degenerate=True, degenerate_reason="missing_bbox",
                               width=0.0, height=0.0, aspect=0.0,
                               area_fraction=0.0)
                    anns.append(row)
                    continue
                x, y, w, h = (float(v) for v in bbox)
                area_frac = (w * h) / (img_w * img_h) if img_w and img_h else 0.0
                reasons = []
                if w < MIN_BOX_PX or h < MIN_BOX_PX:
                    reasons.append("sub_2px")
                if x < 0 or y < 0 or (img_w and x + w > img_w + 1) or \
                        (img_h and y + h > img_h + 1):
                    reasons.append("out_of_frame")
                if area_frac and area_frac < TINY_AREA_FRACTION:
                    reasons.append("tiny_area")
                row.update(
                    degenerate=bool(reasons),
                    degenerate_reason="|".join(reasons),
                    width=round(w, 2), height=round(h, 2),
                    aspect=round(w / h, 3) if h else 0.0,
                    area_fraction=round(area_frac, 6),
                )
                anns.append(row)
                boxes.append([x, y, w, h])
            images.append({
                "source": src.source_group,
                "source_split": src.split,
                "file_name": rec["file_name"],
                "image_path": str(rec["image_path"]),
                "width": img_w,
                "height": img_h,
                "n_annotations": len(rec["annotations"]),
                "n_boxes": len(boxes),
                "categories": rec["categories"],
                "boxes": boxes,
                "segmentations": sum(1 for m in rec["masks"] if m),
            })
    return images, anns


def duplicate_annotations(anns: List[dict]) -> List[dict]:
    """Annotation pairs inside one image with IoU >= DUP_IOU."""
    by_image: Dict[tuple, List[dict]] = {}
    for a in anns:
        if a.get("degenerate") or not a.get("bbox"):
            continue
        by_image.setdefault((a["source"], a["split"], a["file_name"]), []).append(a)

    out: List[dict] = []
    for key, group in by_image.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                x1, y1, w1, h1 = group[i]["bbox"]
                x2, y2, w2, h2 = group[j]["bbox"]
                ix = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2))
                iy = max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
                inter = ix * iy
                union = w1 * h1 + w2 * h2 - inter
                iou = inter / union if union > 0 else 0.0
                if iou >= DUP_IOU:
                    out.append({"file_name": key[2], "source": key[0],
                                "iou": round(iou, 4),
                                "categories": [group[i]["category"],
                                               group[j]["category"]]})
    return out


def summarise_boxes(anns: List[dict], images: List[dict]) -> dict:
    widths = np.array([a["width"] for a in anns if not a.get("degenerate")])
    heights = np.array([a["height"] for a in anns if not a.get("degenerate")])
    aspects = np.array([a["aspect"] for a in anns if not a.get("degenerate")])
    fracs = np.array([a["area_fraction"] for a in anns
                      if not a.get("degenerate")])

    def stats(values: np.ndarray) -> dict:
        if values.size == 0:
            return {"n": 0}
        return {
            "n": int(values.size),
            "min": round(float(values.min()), 3),
            "p05": round(float(np.percentile(values, 5)), 3),
            "median": round(float(np.median(values)), 3),
            "p95": round(float(np.percentile(values, 95)), 3),
            "max": round(float(values.max()), 3),
            "mean": round(float(values.mean()), 3),
        }

    degenerate = [a for a in anns if a.get("degenerate")]
    return {
        "images": len(images),
        "images_with_zero_boxes": sum(1 for i in images if i["n_boxes"] == 0),
        "annotations": len(anns),
        "usable_boxes": sum(1 for a in anns if not a.get("degenerate")),
        "degenerate_boxes": len(degenerate),
        "degenerate_by_reason": dict(Counter(a["degenerate_reason"]
                                            for a in degenerate)),
        "box_width_px": stats(widths),
        "box_height_px": stats(heights),
        "box_aspect_ratio": stats(aspects),
        "box_area_fraction": stats(fracs),
        "annotations_with_polygon_mask": sum(
            1 for a in anns if a.get("has_segmentation")),
        "iscrowd_annotations": sum(1 for a in anns if a.get("iscrowd")),
        "images_with_masks": sum(1 for i in images if i["segmentations"]),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=0.98,
                    help="cosine similarity threshold for near-duplicate grouping")
    ap.add_argument("--no-split", action="store_true",
                    help="only write the audit, do not build the split")
    ap.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "evaluation")
    args = ap.parse_args(argv)

    reg = default_registry()
    images, anns = collect(reg)
    usable = [i for i in images if any(
        a["bbox"] and not a.get("degenerate")
        for a in anns if a["file_name"] == i["file_name"]
        and a["source"] == i["source"])]
    print(f"annotated images: {len(images)} (usable: {len(usable)}), "
          f"annotations: {len(anns)}", flush=True)

    dup_anns = duplicate_annotations(anns)
    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_fingerprint": reg.fingerprint(),
        "sources": sorted({i["source"] for i in images}),
        "source_split_counts": dict(Counter(
            f"{i['source']}/{i['source_split']}" for i in images)),
        "category_counts": dict(Counter(
            a["category"] for a in anns if a.get("category"))),
        "geometry": summarise_boxes(anns, images),
        "duplicate_annotations": {
            "count": len(dup_anns),
            "iou_threshold": DUP_IOU,
            "examples": dup_anns[:20],
        },
        "notes": [
            "Boxes are COCO [x, y, w, h] in original image pixels.",
            "Degenerate boxes are dropped by the detector training loader, "
            "not silently relabelled.",
            "Duplicate annotations are reported, not deleted from the source "
            "dataset; the loader keeps them.",
        ],
    }

    split_report = None
    if not args.no_split:
        paths = [Path(i["image_path"]) for i in images]
        print(f"embedding {len(paths)} images for near-duplicate grouping...",
              flush=True)
        embeddings = embed_images(paths)
        groups = cluster_near_duplicates(embeddings, threshold=args.threshold)
        split = grouped_split(paths, embeddings, threshold=args.threshold)
        summary = split_summary(split)

        # Confirm the grouping actually removes cross-split near-duplicates.
        assignment = split.assignment
        leaks = 0
        sizes = Counter(groups)
        for idx, g in enumerate(groups):
            if sizes[g] < 2:
                continue
            splits_in_group = {assignment[str(paths[j])]
                               for j in range(len(paths))
                               if groups[j] == g}
            if len(splits_in_group) > 1:
                leaks += 1
        summary["groups_spanning_splits"] = leaks
        summary["leakage_check"] = ("pass" if leaks == 0 else "FAIL")

        by_split: Dict[str, Counter] = {"train": Counter(), "validation": Counter(),
                                        "test": Counter()}
        boxes_by_split: Counter = Counter()
        for idx, img in enumerate(images):
            s = assignment[str(paths[idx])]
            by_split[s][img["source"]] += 1
            boxes_by_split[s] += img["n_boxes"]
        summary["source_distribution"] = {k: dict(v) for k, v in by_split.items()}
        summary["box_distribution"] = dict(boxes_by_split)
        summary["official_split_for_comparison"] = dict(Counter(
            f"{i['source']}/{i['source_split']}" for i in images))
        split_report = {
            "generated_at": audit["generated_at"],
            "dataset_fingerprint": audit["dataset_fingerprint"],
            "threshold": args.threshold,
            "summary": summary,
            "assignment": assignment,
        }
        audit["near_duplicate_grouping"] = summary

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "detection_dataset_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit["geometry"], indent=2))
    print(f"duplicate annotation pairs (IoU>={DUP_IOU}): {len(dup_anns)}")

    if split_report:
        (args.out_dir / "detection_split.json").write_text(
            json.dumps(split_report, indent=2), encoding="utf-8")
        print(json.dumps(split_report["summary"], indent=2))

    print(f"\nwrote {args.out_dir / 'detection_dataset_audit.json'}")
    if split_report:
        print(f"wrote {args.out_dir / 'detection_split.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
