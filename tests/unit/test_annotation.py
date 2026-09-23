from pathlib import Path

from PIL import Image

from src.reporting.annotation import persist_annotated_evidence


def test_annotation_persists_original_and_overlay(tmp_path: Path):
    source = tmp_path / "tray.png"
    Image.new("RGB", (240, 160), "#dddddd").save(source)
    result = {"onions": [{
        "onion_id": "ONION-001",
        "source_image": str(source),
        "instance": {"bbox": [20, 30, 120, 130]},
        "measurements": {"diameter_mm": 51.3},
        "decision": {"decision": "grade_a"},
    }]}

    files = persist_annotated_evidence([str(source)], result, tmp_path / "evidence")

    assert Path(files[0]["original_path"]).is_file()
    annotated = Path(files[0]["annotated_path"])
    assert annotated.is_file()
    with Image.open(annotated) as output:
        assert output.size == (240, 160)
