"""Deployment must select the registered model, not a leftover experiment."""
import json

import pytest

from src.vision import detector


@pytest.fixture
def deployment(tmp_path, monkeypatch):
    directory = tmp_path / "models" / "vision" / "detector"
    directory.mkdir(parents=True)
    for name in ("best.pt", "last.pt", "zzz_experiment.pt"):
        (directory / name).touch()
    registry = tmp_path / "models" / "registry.json"
    registry.write_text(json.dumps({"models": {
        "vision-detector-v0.2": {
            "artifact_path": "models/vision/detector/best.pt"}}}), encoding="utf-8")
    monkeypatch.setattr(detector, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(detector, "DETECTOR_DIR", directory)
    monkeypatch.setattr(detector, "REGISTRY_PATH", registry)
    return directory, registry


def test_registered_best_beats_alphabetically_last_checkpoint(deployment):
    directory, _ = deployment
    assert detector.MODEL_ID == "vision-detector-v0.2"
    assert detector.resolve_detector() == directory / "best.pt"


@pytest.mark.parametrize("problem", ["missing_registry", "missing_entry",
                                     "malformed_registry", "missing_artifact"])
def test_bad_deployment_never_silently_uses_another_checkpoint(deployment, problem):
    directory, registry = deployment
    if problem == "missing_registry":
        registry.unlink()
    elif problem == "missing_entry":
        registry.write_text('{"models": {}}', encoding="utf-8")
    elif problem == "malformed_registry":
        registry.write_text("broken", encoding="utf-8")
    else:
        (directory / "best.pt").unlink()
    assert detector.resolve_detector() is None


def test_explicit_artifact_requires_a_file(deployment):
    directory, _ = deployment
    assert detector.resolve_detector(str(directory / "last.pt")) == directory / "last.pt"
    assert detector.resolve_detector(str(directory / "absent.pt")) is None
    assert detector.resolve_detector(str(directory)) is None
