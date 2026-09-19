# Experiments

One directory per serious training or evaluation run. Console logs are not a
record: a run is only reproducible if its configuration, data fingerprint,
metrics and the commit it ran at are stored together.

```
experiments/
└── 2026-09-detector-v0.2/
    ├── config.json        # exact hyperparameters (copied from the run)
    ├── metrics.json       # the run's own metrics file, verbatim
    ├── model_card.json    # the run's model card, verbatim
    ├── history.json       # per-epoch loss and validation metrics
    └── NOTES.md           # why this run exists, what changed, what it means
```

Rules that keep these records honest:

* **Copy, never rewrite.** If a metric was wrong, supersede the run with a new
  directory; do not edit history.
* **No run without a dataset fingerprint.** `dataset_fingerprint` is in the
  config; a run whose data changed is a different run.
* **No run without a split strategy.** `grouped_leak_safe` and `official` are
  not interchangeable, and only grouped splits support metric claims
  (`models/registry.json` records which was used).
* **Negative results stay.** A run that failed to improve the baseline is the
  evidence for the decision not to promote a model.

## Snapshotting a run

```bash
python - <<'PY'
import json, shutil
from pathlib import Path
src = Path("models/vision/detector")
dst = Path("experiments/2026-09-detector-v0.2")
dst.mkdir(parents=True, exist_ok=True)
for name in ("training_config.json", "metrics.json", "model_card.json", "history.json"):
    if (src / name).exists():
        shutil.copy2(src / name, dst / {"training_config.json": "config.json"}.get(name, name))
print("snapshotted", sorted(p.name for p in dst.iterdir()))
PY
```

Weights are **not** copied here: `.gitignore` excludes `*.pt`, and a 76 MB
checkpoint per experiment would bloat the repository. The config, the metrics
and the fingerprint are enough to reproduce the run from the dataset.
