"""Root pytest configuration shared by every test directory.

Puts the project root on `sys.path` so tests import `src.*`, `inference.*` and
`server.*` exactly the way the application does — a clean clone must not need
any extra setup to run the suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def policy():
    from src.grading.policy import active_policy
    return active_policy("demo_policy")


@pytest.fixture(scope="session")
def real_onion_image():
    """One real, licensed dataset photograph (skips if the dataset is absent)."""
    from src.data.dataset_registry import default_registry
    reg = default_registry()
    for source in reg.sources():
        if not source.training_allowed:
            continue
        records = reg.records(source)
        if records:
            return records[0]["image_path"]
    pytest.skip("no real onion image available in this checkout")


@pytest.fixture(scope="session")
def artifact_present():
    """True when a trained detector artifact exists (otherwise skip)."""
    from src.vision.detector import resolve_detector
    return resolve_detector() is not None
