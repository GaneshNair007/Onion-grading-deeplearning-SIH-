# Vision Model — Status and Usage

## Current status (honest)

| Artifact | Trained on | Validated on real onions? | Usable as demo? |
|---|---|---|---|
| `backend/models/artifacts/vision_mobilenet_v1.0.0.pt` | **Synthetic** PIL-drawn onion images (`backend/scripts/seed_dataset.py`) | **No** | Yes, as an unvalidated demo |
| `models/vision/vision_mobilenet_realdata.pt` (produced by `training/train_vision.py`) | **Real** COCO labels: *Onion Grading v7i* (Class 1 / Class 2 / Extra Class / Reject; CC BY 4.0) and *onions v1i* (rotten / sprout; Public Domain) | Partially — metrics are image-level P/R/F1 on a held-out real-image validation split | Yes, and it is the version that should be demoed |

No accuracy number is claimed anywhere in this repository for real-world
performance. The training script writes whatever metrics it achieves to
`models/vision/training_metrics.json`; treat them as validation-set numbers
on Roboflow-style imagery, not as field performance.

## Architecture

`OnionVisionNet` (backend/app/vision/model.py): MobileNetV3-Small backbone,
two heads:

1. **Defect head** — multi-label sigmoid outputs for
   `damaged, sprouted, undersized, visibly_rotten`.
2. **Decay head** — `(mean_days, log_variance)`; **not trained on real
   longitudinal decay labels** (no such public labels exist). Its output is
   surfaced as `freshness_score` but is not a validated shelf-life estimate.

The onion/non-onion gate in `inference/vision_inference.py` is currently a
documented heuristic over the defect head; a dedicated binary
onion-vs-non-onion classifier is the planned replacement (needs negative
examples — photos of non-onion objects — which no current dataset provides).

## Retrain on real data

```bash
python training/train_vision.py --epochs 8
# writes models/vision/vision_mobilenet_realdata.pt + training_metrics.json
```

The script maps the real COCO categories to the defect vocabulary, splits by
image, uses early stopping, and reports precision/recall/F1. It never mixes
in synthetic data.

## Inference

```bash
python inference/vision_inference.py path/to/onion.jpg
```

Returns the shared contract:

```json
{
  "is_onion": true,
  "vision": {"label": "sound", "confidence": 0.88, "defects": {},
             "freshness_score": 0.71, "model_version": "vision-v1 ..."},
  "warnings": ["Vision model trained on synthetic images only; ..."]
}
```

Labels returned: `sound`, `damaged`, `sprouted`, `undersized`,
`visibly_rotten`, or `uncertain` (below the 0.60 confidence threshold).
The `undersized` flag is not trainable from the current COCO sets (no size
reference annotations) and will only trigger if a future dataset defines it.

## Export to mobile

The checkpoint is a plain PyTorch state dict. For TFLite/ONNX deployment:

```bash
# ONNX export sketch (requires onnx + onnxscript):
python - <<'PY'
import torch, sys
sys.path.append('backend')
from app.vision.model import OnionVisionNet
net = OnionVisionNet(pretrained=False)
net.load_state_dict(torch.load('models/vision/vision_mobilenet_realdata.pt', map_location='cpu'))
net.eval()
torch.onnx.export(net, torch.randn(1, 3, 224, 224), 'vision.onnx',
                  input_names=['image'], output_names=['defect_logits', 'decay_params'],
                  opset_version=17, dynamo=True)
PY
```

TFLite conversion then proceeds via ONNX → TF → TFLite, or by rebuilding the
head in TensorFlow and porting weights. Not executed in CI because it needs
heavy dependencies; run locally if mobile deployment is the next milestone.
