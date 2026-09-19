#!/usr/bin/env python3
"""DEPRECATED — replaced because it fabricated training labels.

This script previously built targets as::

    "defects": [1.0, sprouted, 0.0, rotten]   # damaged hard-coded to 1.0

which taught the model that **every** onion was damaged and that `undersized`
was constant (audit finding P0.2). It also read an untracked local folder
(`<root>/Onion Grading.v7i.coco-segmentation`) instead of the tracked
partitioned dataset (audit finding P0.3).

Use instead:

    python training/train_attribute_model.py     # quality class + rotten/sprout
    python training/train_detector.py            # onion instance detection

Both read the tracked dataset through `src/data/dataset_registry.py` and only
supervise tasks for which real labels exist.
"""
from __future__ import annotations

import sys

MESSAGE = __doc__


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
