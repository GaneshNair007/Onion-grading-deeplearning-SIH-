#!/usr/bin/env python3
"""Read-only: per-class counts, nesting depth check, CRC-32 zip-vs-extracted verification."""
import zipfile
import zlib
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent

d = ROOT / "Onion Leaves and Bulb Dataset" / "New Onion - Copy"
print("Leaves/Bulb class folders:")
for cls in sorted(d.iterdir()):
    if cls.is_dir():
        files = [p for p in cls.rglob("*") if p.is_file()]
        deeper = sorted({str(p.relative_to(cls)).split("\\")[0] for p in files})[:5]
        print(f"  {cls.name}: {len(files)} files, {sum(f.stat().st_size for f in files):,} bytes, sample={deeper}")

for name in ["Onion Grading.v7i.coco-segmentation", "onions.v1i.coco-mmdetection"]:
    dd = ROOT / name
    for sub in sorted(p.name for p in dd.iterdir() if p.is_dir()):
        n = sum(1 for p in (dd / sub).rglob("*") if p.is_file())
        print(f"  {name}/{sub}: {n} files")

print("\nCRC-32 verification (zip entry vs extracted file):")
for zname, dirname in [
    ("Onion Grading.v7i.coco-segmentation.zip", "Onion Grading.v7i.coco-segmentation"),
    ("Onion Leaves and Bulb Dataset.zip", "Onion Leaves and Bulb Dataset"),
    ("onions.v1i.coco-mmdetection.zip", "onions.v1i.coco-mmdetection"),
]:
    bad = 0
    with zipfile.ZipFile(ROOT / zname) as z:
        for i in z.infolist():
            if i.is_dir():
                continue
            f = ROOT / dirname / i.filename
            if zlib.crc32(f.read_bytes()) != i.CRC:
                bad += 1
                print(f"  MISMATCH {i.filename}")
    print(f"  {zname}: {bad} mismatches")
