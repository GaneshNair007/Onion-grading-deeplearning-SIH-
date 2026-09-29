"""Persist scan evidence and render a compact per-onion annotation overlay."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Sequence

from PIL import Image, ImageDraw, ImageFont


GRADE_COLOURS = {
    "grade_a": "#2ea043",
    "relaxed": "#d29922",
    "reject": "#f85149",
    "manual_review": "#58a6ff",
}


def persist_annotated_evidence(
    image_paths: Sequence[str], result: Dict[str, Any], output_dir: str | Path
) -> List[Dict[str, str]]:
    """Copy originals and draw actual detector boxes with decision labels.

    Returns paths suitable for evidence hashing and browser URL construction.
    The function never changes the uploaded source files.
    """
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    onions = result.get("onions") or []
    saved: List[Dict[str, str]] = []

    for index, source_value in enumerate(image_paths):
        source = Path(source_value)
        token = uuid.uuid4().hex[:12]
        suffix = source.suffix.lower() if source.suffix.lower() in {".jpg", ".jpeg", ".png"} else ".jpg"
        original = destination / f"scan-{token}-original{suffix}"
        annotated = destination / f"scan-{token}-annotated.jpg"
        shutil.copy2(source, original)

        with Image.open(source) as loaded:
            image = loaded.convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=max(12, image.width // 85))
        source_text = str(source)
        candidates = [o for o in onions if str(o.get("source_image")) == source_text]
        if not candidates and len(image_paths) == 1:
            candidates = onions

        for onion in candidates:
            box = (onion.get("instance") or {}).get("bbox")
            if not box or len(box) != 4:
                continue
            x1, y1, x2, y2 = (int(round(float(v))) for v in box)
            decision = str((onion.get("decision") or {}).get("decision", "manual_review"))
            colour = GRADE_COLOURS.get(decision, "#58a6ff")
            diameter = (onion.get("measurements") or {}).get("diameter_mm")
            size_text = f" - {diameter:g} mm" if isinstance(diameter, (int, float)) else ""
            label = f"{onion.get('onion_id', 'ONION')}  {decision.upper()}{size_text}"
            draw.rectangle((x1, y1, x2, y2), outline=colour, width=max(2, image.width // 400))
            left, top, right, bottom = draw.textbbox((x1, y1), label, font=font)
            label_top = max(0, y1 - (bottom - top) - 8)
            draw.rectangle((x1, label_top, min(image.width, x1 + right - left + 8), y1), fill=colour)
            draw.text((x1 + 4, label_top + 2), label, fill="white", font=font)

        image.save(annotated, format="JPEG", quality=92, optimize=True)
        saved.append({"original_path": str(original), "annotated_path": str(annotated)})
    return saved
