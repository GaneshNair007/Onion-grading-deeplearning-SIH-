"""Dataset provenance and training-manifest governance.

Every image that trains a model must be traceable to a source with a recorded
license, a content hash and a split. Sources whose redistribution/training
rights are unresolved are **excluded** from training manifests — they are not
silently used.

This module is the single place that answers "may we train on this?" so that
no training script can make that call ad hoc.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_NAME = "training_manifest.csv"

MANIFEST_FIELDS = ["source", "license", "license_status", "training_allowed",
                   "split", "label", "categories", "path", "sha256",
                   "group_id", "dataset_fingerprint"]


@dataclass
class DatasetProvenance:
    """One dataset source and the rights we can actually support."""

    source_group: str
    name: str
    url: str
    license: str
    license_status: str          # verified | unresolved | restricted
    training_allowed: bool
    redistribution_allowed: bool
    images: int = 0
    annotations: int = 0
    labels: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _status_to_flags(status: str) -> tuple:
    """Map a license status to (training_allowed, redistribution_allowed)."""
    status = (status or "unresolved").lower()
    if status == "verified":
        return True, True
    if status == "restricted":
        return False, False
    return False, False   # unresolved ⇒ excluded until a human verifies


def provenance_from_registry(registry: Any) -> List[DatasetProvenance]:
    """Build provenance records from the dataset registry (real data only)."""
    out: List[DatasetProvenance] = []
    for src in registry.sources():
        training_allowed, redistribution = _status_to_flags(src.license_status)
        out.append(DatasetProvenance(
            source_group=src.source_group,
            name=src.source_group,
            url="see dataset/LICENSES_AND_SOURCES.md",
            license=src.license,
            license_status=src.license_status,
            training_allowed=training_allowed,
            redistribution_allowed=redistribution,
            labels=sorted(src.supported_tasks),
            limitations=(
                ["license not verified — excluded from training"] +
                ([] if training_allowed else
                 ["no per-image provenance beyond the source group"])),
        ))
    return out


def sha256_for_path(registry: Any, image_path: Path) -> str:
    """Look up the manifest SHA-256 for an image stored under dataset/part-*."""
    try:
        rel = image_path.relative_to(PROJECT_ROOT / "dataset")
    except ValueError:
        return ""
    path_in_repo = "/".join(rel.parts[1:])      # drop the part-NNN component
    row = registry._by_repo_path.get(path_in_repo)   # noqa: SLF001 - manifest index
    if row is not None:
        return row.sha256
    name = image_path.name
    for candidate in registry._by_repo_path.values():  # noqa: SLF001
        if Path(candidate.path_in_repo).name == name:
            return candidate.sha256
    return ""


def build_training_manifest(registry: Any, out_path: Optional[Path] = None,
                            split_of: Optional[Dict[str, str]] = None,
                            split_mode: str = "grouped") -> Dict[str, Any]:
    """Write the per-image training manifest, excluding disallowed sources.

    Returns a summary dict; the CSV is written to
    ``dataset/training_manifest.csv`` by default (tracked, because it is small
    and it is the governance artefact).
    """
    from src.data.splits import embed_images, grouped_split

    from src.data.labels import LICENSE_STATUS

    rows: List[Dict[str, Any]] = []
    excluded: List[Dict[str, str]] = []
    fingerprint = registry.fingerprint()

    # Sources that carry images but no COCO annotations (for example the
    # unresolved *Onion Leaves and Bulb* set) never appear as a CocoSource, so
    # they are reported here directly — otherwise the governance summary could
    # claim "nothing excluded" while an unlicensed source sits in dataset/.
    trainable_groups = {src.source_group for src in registry.sources()
                        if src.training_allowed}
    for group in registry.source_groups():
        if group in trainable_groups:
            continue
        meta = LICENSE_STATUS.get(group, {})
        excluded.append({
            "source_group": group,
            "reason": (f"license_status={meta.get('license_status', 'unresolved')}"
                       f" (licence: {meta.get('license', 'not detected')}); "
                       "excluded from training"),
        })

    for src in registry.sources():
        records = registry.records(src)
        if not src.training_allowed:
            # Already reported by the group loop above; never trained on.
            continue

        if split_mode == "official":
            groups = [(r, src.split) for r in records]
        else:
            # Whole near-duplicate groups move together, so augmented copies of
            # one photograph never straddle train and test.
            paths = [Path(r["image_path"]) for r in records]
            split = grouped_split(paths, embed_images(paths))
            groups = [(r, split.assignment[str(Path(r["image_path"]))])
                      for r in records]

        for record, assigned_split in groups:
            path = Path(record["image_path"])
            rows.append({
                "source": src.source_group,
                "license": src.license,
                "license_status": src.license_status,
                "training_allowed": True,
                "split": assigned_split,
                "label": "|".join(sorted(record["targets"].keys())),
                "categories": "|".join(record["categories"]),
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "sha256": sha256_for_path(registry, path),
                "group_id": f"{src.source_group}:{record['file_name']}",
                "dataset_fingerprint": fingerprint,
            })

    out_path = Path(out_path) if out_path else \
        PROJECT_ROOT / "dataset" / MANIFEST_NAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["source"], r["split"], r["path"])):
            writer.writerow(row)

    return {
        "manifest": str(out_path),
        "rows": len(rows),
        "excluded_sources": excluded,
        "split_mode": split_mode,
        "dataset_fingerprint": fingerprint,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statement": (
            "Only sources with license_status=verified are included. "
            "Unresolved sources are listed under excluded_sources and are not "
            "used for training."),
    }


def verify_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Check that a manifest contains no disallowed sources."""
    path = Path(manifest_path)
    if not path.exists():
        return {"valid": False, "reason": f"manifest not found: {path}"}
    bad = []
    total = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            total += 1
            if str(row.get("training_allowed", "")).lower() not in {"true", "1"}:
                bad.append(row.get("source", "?"))
    return {"valid": not bad, "rows": total,
            "disallowed_rows": sorted(set(bad)),
            "reason": "all rows allowed" if not bad
            else "manifest contains rows from disallowed sources"}


def source_group_stats(registry: Any) -> List[Dict[str, Any]]:
    """Per-source-group inventory taken from the *master* manifest.

    This deliberately enumerates every ``source_group`` present in
    ``dataset/MANIFEST.csv`` — including groups that carry no COCO annotations
    at all (audit finding: ``onion-leaves-and-bulb`` has images but no
    annotation JSON, so a COCO-driven report would silently miss it).
    """
    from src.data.labels import LICENSE_STATUS

    grouped: Dict[str, List[Any]] = {}
    for row in registry.rows():
        grouped.setdefault(row.source_group, []).append(row)

    out: List[Dict[str, Any]] = []
    for group in sorted(grouped):
        rows = grouped[group]
        meta = LICENSE_STATUS.get(group, {})
        status = str(meta.get("license_status", "unresolved"))
        training_allowed, redistribution = _status_to_flags(status)
        annotated = [r for r in rows if r.path_in_repo.endswith("coco.json")]
        images = [r for r in rows
                  if Path(r.path_in_repo).suffix.lower() in {'.jpg', '.jpeg', '.png'}]
        annotation_format = ("coco_json" if annotated else "none")
        reason = ""
        if not training_allowed:
            reason = ("Redistribution/training permission not sufficiently "
                      f"verified (license_status={status}; license: "
                      f"{meta.get('license', 'not detected')}).")
            if not annotated:
                reason += (" The source also carries no COCO annotations, so it "
                           "cannot be used for supervised training as packaged.")
        out.append({
            "source_group": group,
            "file_count": len(rows),
            "image_count": len(images),
            "annotation_file_count": len(annotated),
            "total_bytes": sum(r.size for r in rows),
            "license": str(meta.get("license", "License not detected")),
            "license_status": status,
            "license_source": str(meta.get("source", "not recorded")),
            "training_allowed": training_allowed,
            "redistribution_allowed": redistribution,
            "annotation_format": annotation_format,
            "duplicate_files": sum(1 for r in rows if r.duplicate_of),
            "reason_for_exclusion": reason,
        })
    return out


def governance_report(registry: Any) -> Dict[str, Any]:
    """Full data-governance summary over the master manifest."""
    groups = source_group_stats(registry)
    categories = {
        "training_sources": [g["source_group"] for g in groups if g["training_allowed"]],
        "excluded_sources": [g["source_group"] for g in groups
                            if not g["training_allowed"]],
        "unresolved_sources": [g["source_group"] for g in groups
                               if g["license_status"] == "unresolved"],
        "restricted_sources": [g["source_group"] for g in groups
                               if g["license_status"] == "restricted"],
        "auxiliary_sources": [g["source_group"] for g in groups
                              if g["annotation_format"] == "none"],
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(getattr(registry, "manifest_path", "")),
        "dataset_fingerprint": registry.fingerprint(),
        "total_manifest_files": len(registry.rows()),
        "total_manifest_bytes": sum(r.size for r in registry.rows()),
        "duplicate_files": len(registry.duplicates()),
        "source_groups": groups,
        "categories": categories,
        "statement": (
            "A source group appears under training_sources only when its "
            "licence could be verified from bundled metadata. Groups whose "
            "rights are unresolved are listed explicitly under "
            "unresolved_sources and are never used for training."),
    }


def render_governance_markdown(report: Dict[str, Any]) -> str:
    """Human-readable rendering of :func:`governance_report`."""
    lines = [
        "# Dataset Governance",
        "",
        "Generated from `dataset/MANIFEST.csv` by "
        "`python scripts/dataset_governance.py`. Every source group present in "
        "the manifest is listed, whether or not it carries COCO annotations.",
        "",
        f"* Manifest files: **{report['total_manifest_files']}**",
        f"* Manifest bytes: **{report['total_manifest_bytes']:,}**",
        f"* Duplicate files (skipped by SHA-256): **{report['duplicate_files']}**",
        f"* Dataset fingerprint: `{report['dataset_fingerprint']}`",
        f"* Generated: {report['generated_at']}",
        "",
        "## Source groups",
        "",
        "| Source group | Files | Images | Bytes | License | Status | Trained on | Format |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for g in report["source_groups"]:
        lines.append(
            f"| `{g['source_group']}` | {g['file_count']} | {g['image_count']} | "
            f"{g['total_bytes']:,} | {g['license']} | {g['license_status']} | "
            f"{'yes' if g['training_allowed'] else 'no'} | {g['annotation_format']} |")

    lines += ["", "## Exclusions", ""]
    excluded = [g for g in report["source_groups"] if not g["training_allowed"]]
    if not excluded:
        lines.append("No source group is excluded.")
    for g in excluded:
        lines.append(f"* **`{g['source_group']}`** — {g['reason_for_exclusion']}")

    lines += ["", "## Categories", ""]
    for name, values in report["categories"].items():
        lines.append(f"* `{name}`: {', '.join(f'`{v}`' for v in values) or '(none)'}")
    lines += ["", report["statement"], ""]
    return "\n".join(lines)


def write_governance_report(registry: Any,
                            json_path: Optional[Path] = None,
                            md_path: Optional[Path] = None) -> Dict[str, Any]:
    """Write ``evaluation/dataset_governance.json`` and its Markdown twin."""
    report = governance_report(registry)
    json_path = Path(json_path) if json_path else \
        PROJECT_ROOT / "evaluation" / "dataset_governance.json"
    md_path = Path(md_path) if md_path else \
        PROJECT_ROOT / "docs" / "DATASET_GOVERNANCE.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_governance_markdown(report), encoding="utf-8")
    report["json_path"] = str(json_path)
    report["markdown_path"] = str(md_path)
    return report


if __name__ == "__main__":
    from src.data.dataset_registry import default_registry
    reg = default_registry()
    summary = build_training_manifest(reg)
    print(json.dumps(summary, indent=2))
    print(json.dumps(verify_manifest(Path(summary["manifest"])), indent=2))
    gov = write_governance_report(reg)
    print(json.dumps({"governance_json": gov["json_path"],
                      "governance_md": gov["markdown_path"],
                      "unresolved_sources": gov["categories"]["unresolved_sources"]},
                     indent=2))
