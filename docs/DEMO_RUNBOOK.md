# Local Demo Runbook

## Setup

```powershell
Set-Location C:\SIH
.\scripts\setup.ps1
```

## Start backend and frontend

```powershell
.\scripts\start-demo.ps1
```

The frontend is served by the backend at `http://127.0.0.1:8000/dashboard/app/scan.html`; no separate Node build is required.

## Verify health

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Run tests

```powershell
.\scripts\run-tests.ps1
```

## Demo single onion or tray

Open the scan page, choose Single onion or Tray / batch, select a camera frame or image, and press **Scan captured image**. Use `C:\SIH\demo\tray_calibrated.png` for the calibrated golden path.

## Demo non-onion

Choose a clearly unrelated image. The detector/OOD gate must refuse grading; do not interpret low-confidence output as a pass.

## Demo calibration

Use `demo\tray_calibrated.png` to show measured millimetres. Use `demo\tray_composed.png` to show calibration unavailable/manual review when required.

## Demo acoustic

Use localhost or HTTPS, allow microphone access, record ambient baseline, place the phone 2–5 cm from the onion on a stable surface, then run chirp or guided tap. Explain that capture and DSP are real while the classifier is synthetic-only and research-only.

## Generate report

Tray scans automatically generate a tamper-evident report. The response shows the report ID and annotated evidence. Reports are stored under `C:\SIH\reports`.

## Troubleshooting

- Microphone unavailable: use Chrome/Edge on localhost and allow permission.
- Port busy: stop the existing process using port 8000 before starting.
- Missing environment: rerun `scripts\setup.ps1`.
- Test temp permission errors: always use `scripts\run-tests.ps1`, which uses a workspace-local temp directory.
