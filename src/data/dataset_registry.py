"""Dataset registry over the repository's *actual* partitioned layout.

The tracked dataset lives at ``dataset/<part>/<path_in_repo>`` and is
described by ``dataset/MANIFEST.csv`` (columns: part, path_in_repo,
source_group, bytes, sha256, duplicate_of). Nothing here assumes the dataset
was unpacked into its original folder names — that was audit finding P0.3.

Usage:
    from src.data.dataset_registry import DatasetRegistry
    reg = DatasetRegistry()
    for src in reg.sources():
        print(src.source_group, src.split, len(reg.records(src)))
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.data.labels import LICENSE_STATUS, map_categories, supported_tasks

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_NAME = "MANIFEST.csv"
ANNOTATION_SUFFIX = "_annotations.coco.json"


@dataclass(frozen=True)
class ManifestRow:
    part: str
    path_in_repo: str
    source_group: str
    size: int
    sha256: str
    duplicate_of: str = ""

    @property
    def repo_path(self) -> str:
        return f"dataset/{self.part}/{self.path_in_repo}"


@dataclass(frozen=True)
class CocoSource:
    """One COCO annotation file plus its provenance."""

    source_group: str
    split: str
    row: ManifestRow
    license: str
    license_status: str
    training_allowed: bool
    supported_tasks: frozenset = field(default_factory=frozenset)

    @property
    def repo_path(self) -> str:
        return self.row.repo_path


class DatasetRegistry:
    def __init__(self, project_root: Optional[Path] = None,
                 manifest_path: Optional[Path] = None) -> None:
        self.root = Path(project_root) if project_root else PROJECT_ROOT
        self.manifest_path = Path(manifest_path) if manifest_path else (
            self.root / "dataset" / MANIFEST_NAME)
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"dataset manifest not found: {self.manifest_path}. "
                "The registry works from dataset/MANIFEST.csv; on a branch "
                "without the dataset, pass an explicit manifest_path.")
        self._rows: List[ManifestRow] = self._read_manifest()
        self._coco_cache: Dict[str, dict] = {}
        # Image files are NOT guaranteed to sit next to their annotation file:
        # parts were packed by size, so one split can span several parts
        # (verified: grading/train images are in part-001 and part-002).
        self._by_repo_path: Dict[str, ManifestRow] = {
            r.path_in_repo: r for r in self._rows}
        self._by_source_name: Dict[tuple, ManifestRow] = {}
        for r in self._rows:
            self._by_source_name.setdefault(
                (r.source_group, Path(r.path_in_repo).name), r)

    # ------------------------------------------------------------------ io
    def _read_manifest(self) -> List[ManifestRow]:
        rows: List[ManifestRow] = []
        with open(self.manifest_path, newline="", encoding="utf-8") as f:
            for raw in csv.DictReader(f):
                rows.append(ManifestRow(
                    part=raw["part"].strip(),
                    path_in_repo=raw["path_in_repo"].strip(),
                    source_group=raw["source_group"].strip(),
                    size=int(raw["bytes"]),
                    sha256=raw["sha256"].strip(),
                    duplicate_of=raw.get("duplicate_of", "").strip(),
                ))
        return rows

    # --------------------------------------------------------------- query
    def rows(self) -> List[ManifestRow]:
        return list(self._rows)

    def absolute_path(self, row: ManifestRow) -> Path:
        return self.root / "dataset" / row.part / row.path_in_repo

    def source_groups(self) -> List[str]:
        return sorted({r.source_group for r in self._rows})

    def duplicates(self) -> List[ManifestRow]:
        return [r for r in self._rows if r.duplicate_of]

    def sources(self) -> List[CocoSource]:
        """All COCO annotation files, deterministically ordered."""
        out: List[CocoSource] = []
        for row in sorted(self._rows,
                          key=lambda r: (r.source_group, r.path_in_repo)):
            if not row.path_in_repo.endswith(ANNOTATION_SUFFIX):
                continue
            split = Path(row.path_in_repo).parent.name
            meta = LICENSE_STATUS.get(row.source_group, {
                "license": "License not detected",
                "license_status": "unresolved",
                "training_allowed": False,
                "source": "not recorded",
            })
            out.append(CocoSource(
                source_group=row.source_group,
                split=split,
                row=row,
                license=str(meta["license"]),
                license_status=str(meta["license_status"]),
                training_allowed=bool(meta["training_allowed"]),
                supported_tasks=frozenset(supported_tasks(row.source_group)),
            ))
        return out

    def coco(self, source: CocoSource) -> dict:
        key = source.repo_path
        if key not in self._coco_cache:
            path = self.absolute_path(source.row)
            if not path.exists():
                raise FileNotFoundError(
                    f"annotation file missing on disk: {path} "
                    "(is the dataset part present in this checkout?)")
            self._coco_cache[key] = json.loads(path.read_text(encoding="utf-8"))
        return self._coco_cache[key]

    def records(self, source: CocoSource) -> List[dict]:
        """Per-image records with real labels and geometry.

        Each record::

            {
              "image_path": Path,        # absolute, under dataset/part-*/
              "image_id", "file_name", "width", "height",
              "categories": [...],       # raw source category names
              "targets": {...},          # mapped labels (absent key = no label)
              "unknown_categories": [...],
              "boxes": [[x, y, w, h], ...],
              "masks": [polygon_or_None, ...],
            }
        """
        coco = self.coco(source)
        cat_by_id = {c["id"]: c["name"] for c in coco.get("categories", [])}
        anns_by_image: Dict[int, List[dict]] = {}
        for ann in coco.get("annotations", []):
            anns_by_image.setdefault(ann["image_id"], []).append(ann)

        out: List[dict] = []
        for img in coco.get("images", []):
            anns = anns_by_image.get(img["id"], [])
            names = sorted({cat_by_id.get(a["category_id"], "unknown") for a in anns})
            mapped = map_categories(source.source_group, names)
            out.append({
                "image_path": self.resolve_image(source, img["file_name"]),
                "image_id": img["id"],
                "file_name": img["file_name"],
                "width": img.get("width"),
                "height": img.get("height"),
                "categories": names,
                "targets": mapped["targets"],
                "unknown_categories": mapped["unknown"],
                "boxes": [a.get("bbox") for a in anns],
                "masks": [a.get("segmentation") for a in anns],
                # annotation-level detail: lets callers pair geometry with the
                # category it belongs to (needed for deterministic label choice
                # and for detector training targets).
                "annotations": [
                    {
                        "category": cat_by_id.get(a["category_id"], "unknown"),
                        "bbox": a.get("bbox"),
                        "area": a.get("area"),
                        "segmentation": a.get("segmentation"),
                        "iscrowd": a.get("iscrowd", 0),
                    }
                    for a in anns
                ],
            })
        return out

    def resolve_image(self, source: CocoSource, file_name: str) -> Path:
        """Locate an image through the manifest (split may span several parts)."""
        candidates = [f"{source.source_group}/{source.split}/{file_name}", file_name]
        for cand in candidates:
            row = self._by_repo_path.get(cand)
            if row is not None:
                return self.absolute_path(row)
        row = self._by_source_name.get((source.source_group, Path(file_name).name))
        if row is not None:
            return self.absolute_path(row)
        raise FileNotFoundError(
            f"image '{file_name}' of source '{source.source_group}' is not in "
            f"{self.manifest_path.name}; dataset part may be missing from this checkout")

    def image_files(self, source: CocoSource) -> List[Path]:
        return [r["image_path"] for r in self.records(source)]

    # --------------------------------------------------------------- stats
    def stats(self) -> dict:
        stats: dict = {"sources": [], "total_images": 0, "total_annotations": 0,
                       "duplicates": len(self.duplicates())}
        for src in self.sources():
            coco = self.coco(src)
            recs = self.records(src)
            class_counts: Dict[str, int] = {}
            for rec in recs:
                for cat in rec["categories"]:
                    class_counts[cat] = class_counts.get(cat, 0) + 1
            stats["sources"].append({
                "source_group": src.source_group,
                "split": src.split,
                "repo_path": src.repo_path,
                "images": len(coco.get("images", [])),
                "annotations": len(coco.get("annotations", [])),
                "class_counts": class_counts,
                "license": src.license,
                "license_status": src.license_status,
                "training_allowed": src.training_allowed,
                "supported_tasks": sorted(src.supported_tasks),
                "unknown_categories": sorted({
                    c for rec in recs for c in rec["unknown_categories"]}),
            })
            stats["total_images"] += len(coco.get("images", []))
            stats["total_annotations"] += len(coco.get("annotations", []))
        return stats

    def fingerprint(self) -> str:
        """Deterministic hash of the manifest + label mapping.

        Any change to dataset content (part/path/hash) or to the label
        mapping changes this string, which is recorded in every training run.
        """
        h = hashlib.sha256()
        for row in sorted(self._rows, key=lambda r: (r.part, r.path_in_repo)):
            h.update(f"{row.part}|{row.path_in_repo}|{row.sha256}\n".encode())
        mapping_json = json.dumps(
            {k: sorted(v) for k, v in _mapping_signature().items()},
            sort_keys=True)
        h.update(mapping_json.encode())
        return h.hexdigest()


def _mapping_signature() -> Dict[str, list]:
    from src.data.labels import CATEGORY_MAPPING
    return {group: sorted(entries) for group, entries in CATEGORY_MAPPING.items()}


@lru_cache(maxsize=1)
def default_registry() -> DatasetRegistry:
    """Cached registry for convenience in scripts and tests."""
    return DatasetRegistry()
