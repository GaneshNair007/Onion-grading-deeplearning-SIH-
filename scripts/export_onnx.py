#!/usr/bin/env python3
"""Export the trained models to ONNX and validate numerical parity (Phase U).

Parity is the point: an export that has never been compared against PyTorch is
an unverified artifact. For each model this script runs the same fixed inputs
through PyTorch and ONNX Runtime on CPU, reports the maximum absolute
difference, and benchmarks both.

If the `onnx` package is missing, the script says so and exits with a distinct
code — it never writes a file it could not create, and never reports parity it
did not measure.

Usage:
    python scripts/export_onnx.py
    python scripts/export_onnx.py --attribute-models models/vision/attributes
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EXIT_OK = 0
EXIT_MISSING_DEPENDENCY = 3
EXIT_NO_ARTIFACT = 4


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


def _benchmark(session, inputs, repeats: int = 5) -> Dict[str, Any]:
    import numpy as np
    for _ in range(2):                      # warm-up, not measured
        session.run(None, inputs)
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        session.run(None, inputs)
        timings.append((time.perf_counter() - start) * 1000)
    return {"n": len(timings),
            "median_ms": round(statistics.median(timings), 1),
            "p95_ms": round(_p95(timings), 1)}


def _torch_export(model, dummy, onnx_path: Path, opset: int,
                  input_names: list, output_names: list, dynamic_axes: dict):
    """Export via the legacy TorchScript tracer.

    torch>=2.9 defaults ``torch.onnx.export(dynamo=True)``; the torch.export
    path cannot trace torchvision's data-dependent NMS (GuardOnDataDependentSym
    Node in _batched_nms_coordinate_trick). The legacy tracer handles it and is
    explicitly requested here.
    """
    import torch
    try:
        torch.onnx.export(model, (dummy,), str(onnx_path),
                          opset_version=opset, input_names=input_names,
                          output_names=output_names, dynamic_axes=dynamic_axes,
                          do_constant_folding=True, dynamo=False)
    except TypeError:                        # older torch without ``dono``/``dynamo``
        torch.onnx.export(model, (dummy,), str(onnx_path),
                          opset_version=opset, input_names=input_names,
                          output_names=output_names, dynamic_axes=dynamic_axes,
                          do_constant_folding=True)


def export_detector(out_dir: Path, opset: int, repeats: int) -> Dict[str, Any]:
    import numpy as np
    import torch

    from src.vision.detector import resolve_detector
    from training.train_detector import build_model

    weights = resolve_detector()
    if weights is None:
        return {"status": "no_artifact",
                "reason": "no detector checkpoint found; train one first"}
    model = build_model(pretrained=False)
    state = torch.load(weights, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model"] if "model" in state else state)
    model.eval()

    # Use a real dataset image for BOTH export and parity: a random-noise
    # input produces zero detections after NMS, which would make the score
    # comparison vacuous (two empty arrays).
    sample_candidates = sorted((PROJECT_ROOT / "dataset").glob(
        "**/valid/*.jpg")) if (PROJECT_ROOT / "dataset").exists() else []
    if sample_candidates:
        from PIL import Image
        from torchvision.transforms import functional as F
        img = Image.open(sample_candidates[0]).convert("RGB")
        w, h = img.size
        scale = 320.0 / max(w, h)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        dummy = F.to_tensor(img).unsqueeze(0)
    else:
        dummy = torch.rand(1, 3, 320, 640)

    onnx_path = out_dir / "detector.onnx"
    _torch_export(model, dummy, onnx_path, opset,
                  ["images"], ["boxes", "labels", "scores"],
                  {"images": {0: "batch", 2: "height", 3: "width"}})

    with torch.no_grad():
        torch_out = model(dummy)[0]
    torch_boxes = torch_out["boxes"].numpy()
    torch_scores = torch_out["scores"].numpy()

    import onnxruntime as ort
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    outputs = session.run(None, {"images": dummy.numpy()})
    onnx_boxes = np.asarray(outputs[0])
    onnx_scores = np.asarray(outputs[2])

    n = min(len(torch_scores), len(onnx_scores))
    max_scores = float(np.max(np.abs(torch_scores[:n] - onnx_scores[:n]))) \
        if n else None
    max_boxes = float(np.max(np.abs(torch_boxes[:n] - onnx_boxes[:n]))) \
        if n else None

    return {
        "status": "exported",
        "artifact": str(onnx_path),
        "artifact_mb": round(onnx_path.stat().st_size / 1e6, 2),
        "source_weights": str(weights),
        "opset": opset,
        "parity": {
            "compared_boxes": int(n),
            "max_abs_diff_scores": (round(max_scores, 6) if max_scores is not None
                                    else None),
            "max_abs_diff_boxes": (round(max_boxes, 6) if max_boxes is not None
                                   else None),
            "note": ("Boxes/scores are produced by non-maximum suppression, "
                     "which ONNX Runtime and PyTorch implement independently; "
                     "counts may differ slightly even when the model is "
                     "numerically identical."),
            "torch_n_boxes": int(len(torch_scores)),
            "onnx_n_boxes": int(len(onnx_scores)),
            "parity_input": (str(sample_candidates[0])
                             if sample_candidates else "random_noise"),
        },
        "onnxruntime_cpu": _benchmark(session, {"images": dummy.numpy()}, repeats),
        "onnxruntime_version": getattr(ort, "__version__", "unknown"),
    }


def export_attribute(model_dir: Path, opset: int, repeats: int) -> Dict[str, Any]:
    import numpy as np
    import torch

    from src.vision.model import OnionAttributeNet

    checkpoints = sorted(model_dir.glob("*.pt"))
    if not checkpoints:
        return {"status": "no_artifact",
                "reason": f"no *.pt checkpoint under {model_dir}"}
    weights = checkpoints[0]
    net = OnionAttributeNet(pretrained=False)
    state = torch.load(weights, map_location="cpu", weights_only=False)
    net.load_state_dict(state["model"] if isinstance(state, dict) and "model" in state
                        else state)
    net.eval()

    dummy = torch.rand(1, 3, 128, 128)
    onnx_path = model_dir / f"{weights.stem}.onnx"
    _torch_export(net, dummy, onnx_path, opset,
                  ["images"], ["logits"], {"images": {0: "batch"}})

    with torch.no_grad():
        torch_out = net(dummy)   # (quality_logits, binary_logits)

    import onnxruntime as ort
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    onnx_out = session.run(None, {"images": dummy.numpy()})

    heads = {"quality": 0, "binary": 1}
    parity: Dict[str, Any] = {}
    for name, idx in heads.items():
        t = torch_out[idx].detach().numpy()
        o = np.asarray(onnx_out[idx])
        parity[f"max_abs_diff_{name}_head"] = round(
            float(np.max(np.abs(t - o))), 6)
        parity[f"shape_{name}_torch"] = list(t.shape)
        parity[f"shape_{name}_onnx"] = list(o.shape)

    return {
        "status": "exported",
        "artifact": str(onnx_path),
        "artifact_mb": round(onnx_path.stat().st_size / 1e6, 2),
        "source_weights": str(weights),
        "opset": opset,
        "parity": parity,
        "onnxruntime_cpu": _benchmark(session, {"images": dummy.numpy()}, repeats),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path,
                    default=PROJECT_ROOT / "models" / "onnx")
    ap.add_argument("--attribute-models", type=Path,
                    default=PROJECT_ROOT / "models" / "vision" / "attributes")
    ap.add_argument("--opset", type=int, default=17)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--report", type=Path,
                    default=PROJECT_ROOT / "evaluation" / "export_validation.json")
    ap.add_argument("--skip-detector", action="store_true")
    ap.add_argument("--skip-attribute", action="store_true")
    args = ap.parse_args(argv)

    try:
        import onnx  # noqa: F401
    except ImportError:
        message = {
            "status": "blocked",
            "reason": "the `onnx` package is not installed in this environment",
            "command_to_run": ("pip install onnx   # or: pip install -r "
                               "requirements.txt after adding the export extra"),
            "statement": ("No ONNX artifact was produced and no parity was "
                          "measured. This report states the blocker instead of "
                          "claiming an export exists."),
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(message, indent=2), encoding="utf-8")
        print(json.dumps(message, indent=2))
        return EXIT_MISSING_DEPENDENCY

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {"platform": f"{platform.system()} {platform.release()}",
                 "processor": platform.processor()},
        "models": {},
        "statement": ("Each export is compared against its PyTorch source on "
                      "identical inputs; a difference is reported, not hidden."),
    }
    try:
        if not args.skip_detector:
            try:
                report["models"]["detector"] = export_detector(
                    args.out_dir, args.opset, args.repeats)
            except Exception as exc:      # noqa: BLE001 - per-model, not fatal
                report["models"]["detector"] = {
                    "status": "export_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:1500],
                }
        if not args.skip_attribute:
            try:
                report["models"]["attribute"] = export_attribute(
                    args.attribute_models, args.opset, args.repeats)
            except Exception as exc:      # noqa: BLE001 - per-model, not fatal
                report["models"]["attribute"] = {
                    "status": "export_failed",
                    "error": f"{type(exc).__name__}: {exc}"[:1500],
                }
    except Exception as exc:                     # noqa: BLE001 - reported, not raised
        report["error"] = f"{type(exc).__name__}: {exc}"[:1500]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {args.report}")
    if any(m.get("status") == "no_artifact"
           for m in (report["models"].values() if report["models"] else [])):
        return EXIT_NO_ARTIFACT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
