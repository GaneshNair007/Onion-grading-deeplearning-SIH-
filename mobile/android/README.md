# ONION-Q Android — reference implementation

> **Not compiled.** No Android SDK/Gradle toolchain exists in this development
> environment, so this module is a documented integration boundary, not shipped
> code. It is written so a mobile engineer can lift the structure directly.

## Files

| File | Purpose |
|---|---|
| `app/src/main/AndroidManifest.xml` | Camera + microphone permissions, offline-first services |
| `app/build.gradle.kts` | Dependencies: CameraX, ONNX Runtime Mobile, WorkManager, Kotlin serialisation |
| `app/src/main/java/in/onionq/scan/MainActivity.kt` | Guided capture UI (batch / deep scan), calls the inference bridge |
| `app/src/main/java/in/onionq/scan/VisionAnalyzer.kt` | ONNX Runtime Mobile session, letterboxing, NMS, attribute heads |
| `app/src/main/java/in/onionq/scan/AcousticRecorder.kt` | Ambient baseline, chirp playback, AudioRecord capture, quality metadata |
| `app/src/main/java/in/onionq/scan/OfflineStore.kt` | Append-only journal + WorkManager sync (idempotent record ids) |

## Division of responsibility

The app **does not decide grades**. It captures, runs models and sends
measurements; the decision comes from the policy engine. Two supported
deployments:

1. **Server-backed (recommended for SIH demo):** the app posts images/audio to
   `server/app.py` and receives the decision + reason codes. Works offline via
   the journal, then syncs.
2. **On-device:** ONNX Runtime Mobile runs the detector + attribute model, and
   the *same* policy rules are applied by a Kotlin port — only acceptable if the
   policy JSON is shipped and hashed identically, so a decision is reproducible.

## Contracts the app must honour

* Never grade without a model — surface `model_unavailable`.
* Never show millimetres without a detected calibration marker.
* Always show `manual_review` **with its reason**; never hide uncertainty.
* Record device model, OS, sample rate, capture method and ambient score with
  every acoustic measurement.
* Mark browser/web audio as `capture_method = "browser"`; it is not equivalent
  to native capture.

## Model export status

The PyTorch artifacts have **not** been exported to ONNX/TFLite here
(`onnx` is not installed in this environment). The export step is:

```bash
pip install onnx onnxruntime onnxruntime-tools
python - <<'PY'
import torch
from src.vision.model import OnionAttributeNet
net = OnionAttributeNet(pretrained=False)
net.load_state_dict(torch.load("models/vision/attributes/attributes_v0.1_128px.pt",
                               map_location="cpu"))
net.eval()
torch.onnx.export(net, torch.randn(1, 3, 128, 128), "attributes_v0.1.onnx",
                  input_names=["input"], output_names=["quality_logits", "defect_logits"],
                  dynamic_axes={"input": {0: "batch"}})
PY
```

Record the resulting file size and on-device latency in
`docs/MODEL_CARDS.md` — do not claim a mobile number before measuring one.
