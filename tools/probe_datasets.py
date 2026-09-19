#!/usr/bin/env python3
"""Read-only probes: (1) do extracted dirs cover ZIP contents? (2) folder class structure."""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- 1. ZIP vs extracted folder comparison (central-directory listing only) ---
for zname, dirname in [
    ("Onion Grading.v7i.coco-segmentation.zip", "Onion Grading.v7i.coco-segmentation"),
    ("Onion Leaves and Bulb Dataset.zip", "Onion Leaves and Bulb Dataset"),
    ("onions.v1i.coco-mmdetection.zip", "onions.v1i.coco-mmdetection"),
]:
    with zipfile.ZipFile(ROOT / zname) as z:
        zi = [(i.filename, i.file_size) for i in z.infolist() if not i.is_dir()]
    d = ROOT / dirname
    dmap = {str(p.relative_to(d)).replace("\\", "/"): p.stat().st_size
            for p in d.rglob("*") if p.is_file()}
    missing = [(fn, s) for fn, s in zi if fn not in dmap or dmap[fn] != s]
    print(f"{zname}: {len(zi)} entries; missing/differing in extracted dir: {len(missing)}")
    for fn, s in missing[:5]:
        print(f"   {fn}  {s:,}")

# --- 2. Folder structure of the big dataset ---
d = ROOT / "Onion Leaves and Bulb Dataset"
print("\nStructure of 'Onion Leaves and Bulb Dataset':")
for lvl2 in sorted(d.iterdir()):
    if lvl2.is_dir():
        files = list(lvl2.rglob("*"))
        nf = sum(1 for p in files if p.is_file())
        nb = sum(p.stat().st_size for p in files if p.is_file())
        subs = sorted(x.name for x in lvl2.iterdir() if x.is_dir())
        print(f"  DIR {lvl2.name}/  files={nf}  bytes={nb:,}  subdirs={subs[:12]}")
    else:
        print(f"  FILE {lvl2.name}  {lvl2.stat().st_size:,}")

# --- 3. Hidden/macOS junk that would break exact ZIP matching ---
junk = [p.name for p in d.rglob("*") if p.name.startswith("._") or p.name == ".DS_Store"]
print(f"\njunk files in extracted dir: {len(junk)}", junk[:10])

# --- 4. Small dataset classes ---
d2 = ROOT / "Onion Grading.v7i.coco-segmentation"
print("\nSubfolders of 'Onion Grading.v7i.coco-segmentation':",
      sorted(x.name for x in d2.iterdir() if x.is_dir()))
with open(d2 / "README.dataset.txt", encoding="utf-8", errors="replace") as f:
    print((f.read()[:600]))
