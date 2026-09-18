#!/usr/bin/env python3
"""Download external acoustic datasets that are NOT redistributed via GitHub.

This script is run manually by the user. It downloads to a local folder of
your choice (outside the repository by default) and records provenance. No
downloaded byte is ever committed: datasets listed here are either under
NoDerivatives licenses, oversized for GitHub, or otherwise restricted — see
dataset-acoustic/SOURCES.md ("Not redistributed").

Items:
    coconut   Acoustic Signal Dataset: Tall Coconut Fruit Species
              (Mendeley Data, CC BY-NC-ND 4.0, 278 MB XLSX)

Usage:
    python tools/download_external_acoustic_data.py --item coconut --dest ../external_data
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ITEMS = {
    "coconut": {
        "url": "https://data.mendeley.com/public-files/datasets/hxh8kd3snj/files/13c4f544-948d-48ca-8afc-f8b1e2a0b1c5/file_downloaded",
        "filename": "coconut_acoustic_signals.xlsx",
        "sha256": "629fbc02a8ffac1a40222a2c6a536a1e4a51e812fe9defaaed93417e6c151971",
        "license": "CC BY-NC-ND 4.0",
        "source_url": "https://data.mendeley.com/datasets/hxh8kd3snj/1",
        "doi": "10.17632/hxh8kd3snj.1",
        "size_bytes": 278424725,
        "dataset_type": "related_produce_acoustic",
        "warning": ("CC BY-NC-ND 4.0: you may download and use it locally for "
                    "non-commercial purposes, but you may NOT redistribute a copy "
                    "or a repacked derivative. Do not commit it to git."),
    },
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--item", required=True, choices=sorted(ITEMS))
    ap.add_argument("--dest", type=Path, required=True,
                    help="Local destination folder (outside the repository)")
    args = ap.parse_args()

    item = ITEMS[args.item]
    args.dest.mkdir(parents=True, exist_ok=True)
    target = args.dest / item["filename"]

    print(f"Downloading {item['filename']} ({item['size_bytes']:,} bytes)")
    print(f"  license : {item['license']}")
    print(f"  source  : {item['source_url']}")
    print(f"  WARNING : {item['warning']}")
    print(f"  dest    : {target}\n")

    urllib.request.urlretrieve(item["url"], str(target))

    digest = sha256_of(target)
    ok = digest == item["sha256"]
    print(f"SHA-256: {digest}")
    print(f"Expected: {item['sha256']}")
    print("VERIFIED" if ok else "MISMATCH — do not use this file; re-download or report")

    provenance = {
        "item": args.item,
        "downloaded_date": date.today().isoformat(),
        "url": item["url"],
        "source_url": item["source_url"],
        "doi": item["doi"],
        "license": item["license"],
        "sha256": digest,
        "verified": ok,
        "dataset_type": item["dataset_type"],
    }
    prov_path = target.with_suffix(target.suffix + ".provenance.json")
    prov_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Provenance written to {prov_path}")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
