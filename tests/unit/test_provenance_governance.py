"""Governance regression tests.

The audit found a real defect: a source group that has images in
``dataset/MANIFEST.csv`` but no COCO annotation file was invisible to a
COCO-driven provenance report, so the report claimed ``excluded_sources: []``
while an unlicensed source sat in the dataset directory. These tests pin the
fixed behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data.dataset_registry import DatasetRegistry
from src.data.provenance import (
    build_training_manifest,
    governance_report,
    render_governance_markdown,
    source_group_stats,
    verify_manifest,
)
from src.data.labels import LICENSE_STATUS


def _has_dataset() -> bool:
    return (Path(__file__).resolve().parents[2] / "dataset" / "MANIFEST.csv").exists()


requires_dataset = pytest.mark.skipif(
    not _has_dataset(),
    reason="dataset/MANIFEST.csv not present in this checkout")


@pytest.fixture(scope="module")
def registry():
    return DatasetRegistry()


@requires_dataset
def test_unresolved_manifest_source_is_not_silently_ignored(registry):
    """A source with images but no COCO annotations must still be reported."""
    groups = {g["source_group"] for g in source_group_stats(registry)}
    coco_groups = {s.source_group for s in registry.sources()}

    unannotated = groups - coco_groups
    assert unannotated, (
        "expected at least one manifest source group without COCO annotations; "
        "if the dataset changed, this test must be re-derived from the manifest")

    report = governance_report(registry)
    for group in unannotated:
        assert group in report["categories"]["unresolved_sources"] or \
            group in report["categories"]["restricted_sources"], (
                f"unannotated source '{group}' is absent from the governance "
                "exclusion categories")
        row = next(g for g in report["source_groups"]
                   if g["source_group"] == group)
        assert row["training_allowed"] is False
        assert row["reason_for_exclusion"]
        assert row["annotation_format"] == "none"


@requires_dataset
def test_onion_leaves_and_bulb_is_excluded_with_a_reason(registry):
    report = governance_report(registry)
    excluded = {g["source_group"]: g for g in report["source_groups"]}
    assert "onion-leaves-and-bulb" in excluded
    entry = excluded["onion-leaves-and-bulb"]
    assert entry["license_status"] == "unresolved"
    assert entry["training_allowed"] is False
    assert "not sufficiently verified" in entry["reason_for_exclusion"]
    assert entry["file_count"] > 0
    assert entry["total_bytes"] > 0
    assert "onion-leaves-and-bulb" in report["categories"]["excluded_sources"]
    assert "onion-leaves-and-bulb" in report["categories"]["auxiliary_sources"]
    assert "onion-leaves-and-bulb" not in report["categories"]["training_sources"]


@requires_dataset
def test_manifest_never_contains_disallowed_sources(registry, tmp_path):
    out = tmp_path / "training_manifest.csv"
    summary = build_training_manifest(registry, out_path=out)
    assert summary["excluded_sources"], "excluded_sources must be reported"

    allowed = {g for g, meta in LICENSE_STATUS.items()
               if meta.get("training_allowed")}
    check = verify_manifest(out)
    assert check["valid"] is True, check
    assert check["disallowed_rows"] == []

    import csv
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows, "training manifest must not be empty"
    assert {r["source"] for r in rows} <= allowed
    assert all(r["dataset_fingerprint"] == summary["dataset_fingerprint"]
               for r in rows)


@requires_dataset
def test_governance_report_renders_and_is_serialisable(registry, tmp_path):
    report = governance_report(registry)
    json.dumps(report)                    # must be JSON-serialisable
    md = render_governance_markdown(report)
    assert "Dataset Governance" in md
    assert report["total_manifest_files"] > 0
    for key in ("training_sources", "excluded_sources", "unresolved_sources",
                "auxiliary_sources"):
        assert key in report["categories"]


@requires_dataset
def test_governance_report_counts_every_manifest_group(registry):
    report = governance_report(registry)
    manifest_groups = set(registry.source_groups())
    reported = {g["source_group"] for g in report["source_groups"]}
    assert manifest_groups == reported
    assert report["total_manifest_files"] == len(registry.rows())
    assert report["duplicate_files"] == len(registry.duplicates())
