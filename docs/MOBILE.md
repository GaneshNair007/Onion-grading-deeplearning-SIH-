# ONION-Q — Mobile

## 1. What the phone does

The app is a **camera + microphone + offline store** client. All decision logic
lives in the tracked Python library, so the app, the local demo and the tests
exercise the same code path.

| App function | Python implementation | Notes |
|---|---|---|
| `scanOnionImage(image)` | `inference/combined_scan.py::scan_onion_image` | detect + classify + policy decision |
| tray batch scan | `scan_tray_batch` | one image → many onions |
| `deepScan(views, audio)` | `deep_scan_onion` | four guided views, optional audio |
| `classifyVision(image)` | `classify_vision` | shared vision contract |
| `classifyAcoustic(audio)` | `classify_acoustic` | shared acoustic contract |
| `recordAmbientBaseline(wav)` | `record_ambient_baseline` | room-noise gate |
| `runPhoneAcousticTest(...)` | `run_phone_acoustic_test` | chirp → tap fallback, quality gated |
| `fuseResults(v, a)` | `fuse_results` | confidence-aware fusion |
| `saveScanResult(result)` | `save_scan_result` | append-only offline journal |

## 2. Capture protocol (phone-only, no external hardware)

```
1. Ask the inspector to reduce background noise
2. Record ~1 s ambient baseline            → refuse to continue if too noisy
3. Play a controlled logarithmic chirp      → record the response
   (fallback) guide a standardised tap on neck / equator / base
4. Quality gates: silence, clipping, SNR, duration, sample rate, tap consistency
5. Retest up to 3 times (chirp → tap)       → then report "retest required"
6. Extract features → acoustic model
7. Report internal-defect probability + audio quality + confidence,
   or "retest required"
```

**No piezo sensor, no USB ADC, no Raspberry Pi.** The industry vibrometry rig
described in `onion-master-plan-updated.md` is a future research track and is
not part of the phone app.

Device metadata recorded with every recording (because phone speakers and
microphones are inconsistent): device model, OS version, sample rate, recording
volume setting, capture method, ambient-noise score, timestamp —
schema in `dataset-acoustic/metadata_schema.json`.

## 3. Offline-first behaviour

`src/mobile/offline_store.py`:

* append-only JSONL journal per centre (`local_data/scans/<centre>/scans.jsonl`);
* every record carries a client UUID, so a retry is idempotent server-side;
* sync failures leave records `failed` with the error and retry later;
* **nothing is ever deleted** — a synced record is marked `sent`, not removed;
* a truncated final line (crash mid-write) cannot hide earlier records.

```python
from src.mobile.offline_store import ScanStore, sync_records
store = ScanStore("MH-NSK", root="local_data/scans", device_id="pixel-7")
store.save_scan_result(scan_result)
sync_records(store, sender=lambda record: api.put_scan(record))
```

## 4. Inference runtime

| Model | Suggested runtime | Artifact | Size |
|---|---|---|---|
| Onion detector | ONNX Runtime Mobile / TFLite (export pending) | `detector_v0.1_cpu.pt` | 76 MB |
| Attribute model | ONNX Runtime Mobile / TFLite (small enough for most phones) | `attributes_v0.1_128px.pt` | 4.4 MB |
| Acoustic baseline | scikit-learn → ONNX or a small port | `acoustic_baseline.joblib` | < 1 MB |

**Honest statement:** the artifacts are PyTorch and have **not** been converted
or benchmarked on a phone. `onnxruntime` is installed, `onnx` (the exporter) is
not, so the export step is documented rather than claimed as done. No mobile
latency figure exists — the 117 ms and 10.9 ms numbers in
`docs/MODEL_CARDS.md` are desktop CPU.

## 5. Reference Android module

`mobile/android/` contains a **Kotlin reference implementation**:
`MainActivity.kt` (camera + guided capture UI), `VisionAnalyzer.kt` (ONNX
Runtime Mobile wrapper), `AcousticRecorder.kt` (AudioRecord + chirp playback +
quality metadata), `OfflineStore.kt` (journal + WorkManager sync).

> **It is not compiled.** No Android SDK/Gradle toolchain exists in this
> environment. The module documents the integration boundary and the exact
> contracts; treat it as a starting point, not as shipped code.

If the target is Flutter or React Native instead, the same boundary applies:
implement the native camera/audio side and call the backend (or an embedded
ONNX session) with the contracts listed in §1.

## 6. Web boundary

A browser client is supported **only** through the `server/` API. Browser
microphone capture is explicitly **not** treated as equivalent to native phone
capture (no control over playback level, device response or sample rate), and
its results are marked with `capture_method = "browser"` so an auditor can see
the difference.
