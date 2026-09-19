#!/usr/bin/env python3
"""One-time read-only inventory of dataset files under the project root.

Prints: per top-level directory -> file count, total bytes, extension counts,
files > 95 MiB, and grand totals. Skips ignored directories.
"""
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
               "build", "checkpoints", "runs", "outputs", "logs", ".freebuff",
               ".pytest_cache", "storage", "dataset", "tools"}
IGNORE_EXT = {".pt", ".pth", ".onnx", ".h5", ".tflite", ".pyc", ".tmp", ".log"}

tops = {}
grand_count = 0
grand_bytes = 0
oversize_all = []

for child in sorted(ROOT.iterdir()):
    if child.name in IGNORE_DIRS:
        continue
    files = [p for p in child.rglob("*") if p.is_file()] if child.is_dir() else [child]
    files = [p for p in files
             if not any(part in IGNORE_DIRS for part in p.parts)
             and p.suffix.lower() not in IGNORE_EXT]
    n, total = len(files), sum(f.stat().st_size for f in files)
    exts = Counter(f.suffix.lower() or "(no ext)" for f in files)
    oversize = [(f, f.stat().st_size) for f in files if f.stat().st_size > 95 * 1024 * 1024]
    tops[child.name] = (n, total, exts, oversize)
    grand_count += n
    grand_bytes += total
    oversize_all += [(p, s, child.name) for p, s in oversize]

print(f"{'TOP-LEVEL ITEM':52} {'FILES':>7} {'BYTES':>14}")
print("-" * 80)
for name, (n, total, exts, oversize) in tops.items():
    print(f"{name[:52]:52} {n:>7} {total:>14,}")
    print(f"   ext: {dict(exts.most_common(8))}")
    for f, s in oversize:
        print(f"   >95MiB: {f.relative_to(ROOT)}  {s:,} bytes")
print("-" * 80)
print(f"{'TOTAL':52} {grand_count:>7} {grand_bytes:>14,}")
print(f"\nFiles larger than 95 MiB overall: {len(oversize_all)}")
for p, s, top in oversize_all:
    print(f"  {p.relative_to(ROOT)}  {s:,} bytes  ({top})")