# Android build status

**Status: SOURCE IMPLEMENTED — BUILD UNVERIFIED — APK NOT PRODUCED.**

This document exists so nobody mistakes `.kt` files for a working application.
The Kotlin sources are real, reviewed code, but they have **never been compiled
in this environment**, because the toolchain is absent. That is a fact about
this workstation, not a claim about the code's correctness.

## Why it is unverified

Checked on the build machine (2026-09-19):

| Requirement | Result |
|---|---|
| `java` / JDK | **not installed** (`java: command not found`) |
| `gradle` | **not installed** |
| `ANDROID_HOME` / `ANDROID_SDK_ROOT` | unset |
| Android SDK under `%LOCALAPPDATA%\Android\Sdk` | absent |
| Gradle wrapper (`gradlew`) | not committed |
| APK artifact | none produced |

Without a JDK and the Android SDK, `gradlew assembleDebug` cannot run at all,
so no compile errors have been surfaced or fixed. Nothing in this repository
should be described as "an Android app that works" — only as Android source
plus a documented integration boundary.

## What the source contains

`mobile/android/app/src/main/java/in/onionq/scan/`

| File | Responsibility |
|---|---|
| `MainActivity.kt` | CameraX preview + capture, scan flow, result rendering |
| `VisionAnalyzer.kt` | On-device inference wiring (ONNX Runtime Mobile / TFLite boundary) |
| `AcousticRecorder.kt` | Ambient baseline + tap/chirp capture to WAV via `AudioRecord`, chirp playback |
| `OfflineStore.kt` | Append-only local journal, pending-queue sync boundary |

`mobile/android/app/build.gradle.kts` declares CameraX, ONNX Runtime Mobile and
Kotlin. `mobile/android/README.md` describes the integration contract and the
JSON shapes exchanged with the Python pipeline (`inference/combined_scan.py`).

## Exact commands to build (for the team, on a machine with the SDK)

```bash
# 1. Install a JDK 17+ and the Android SDK command-line tools, then:
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# 2. From the repository, in mobile/android/:
cd mobile/android
gradle wrapper --gradle-version 8.7      # creates gradlew (not committed yet)
./gradlew assembleDebug

# 3. Expected artifact:
ls app/build/outputs/apk/debug/app-debug.apk

# 4. Install on a device:
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

When the build is first run, expect to fix at minimum:

* Gradle/AGP versions vs the installed JDK;
* ONNX Runtime Mobile artifact coordinates and ABI splits (x86_64 emulator vs
  arm64 device);
* CameraX `ImageAnalysis` output format expectations in `VisionAnalyzer.kt`;
* runtime permissions in `AndroidManifest.xml` (`CAMERA`, `RECORD_AUDIO`).

## What is verified instead

Because the app cannot be compiled, the *contract* the app depends on is
verified on the Python side, which is the honest substitute available today:

* `tests/integration/test_batch_scan.py`, `tests/e2e/test_field_workflow.py` and
  `server/tests/test_api.py` exercise the same functions the app calls
  (`scan_onion_image`, `classify_vision`, `classify_acoustic`, `fuse_results`,
  `save_scan_result`, `/scan/batch`, `/scan/deep`, `/sync/scans`,
  `/review/override`);
* `src/mobile/offline_store.py` implements and tests the offline-first journal
  and idempotent sync semantics the Kotlin `OfflineStore.kt` must match;
* the API is the integration boundary: an app that cannot be compiled today can
  still be wired to a running backend tomorrow without changing the Python side.

## What must NOT be claimed

* "The Android app works" — it has not been built.
* "The APK is available" — there is none.
* "On-device inference is validated" — no runtime measurement exists; the only
  latency numbers in this repository are desktop CPU measurements
  (`evaluation/export_validation.json`, `docs/DETECTOR_EXPERIMENTS.md`).

Once `gradlew assembleDebug` produces an APK, replace this document's status
line with the build log and the measured on-device latency.
