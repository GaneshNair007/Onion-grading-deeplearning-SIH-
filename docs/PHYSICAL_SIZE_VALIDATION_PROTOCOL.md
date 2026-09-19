# Physical size validation protocol

**Status: PHYSICAL VALIDATION PENDING.**

The software can prove that the ArUco pipeline works on *rendered* mats: markers
are detected, the homography is computed, and measured pixel distances convert
to millimetres consistently. It cannot prove that a *printed* mat measures what
it claims — that depends on printer scaling, paper distortion and the camera.
Only a physical measurement can settle it.

Until the steps below are completed and recorded, every size output must be
described as uncalibrated or awaiting physical validation. Do not quote a
millimetre accuracy figure.

## 1. Print the mat correctly

```bash
python scripts/make_calibration_mat.py --out demo/calibration_mat_A4_300dpi.png --dpi 300
```

* Print at **100 % scale** (disable "fit to page" / "shrink to fit").
* Use matte paper if possible: glossy sheets glare and cost you marker detections.
* Prefer A3 for trays larger than ~25 cm; the A4 mat is the demo default.

## 2. Verify the printed reference

Measure the printed marker edge with a steel rule or digital caliper:

| Measurement | Expected | Measured | Pass? |
|---|---|---|---|
| ArUco marker side (mm) | 40.0 (configurable) | _pending_ | _pending_ |
| Grid cell size (mm) | as generated | _pending_ | _pending_ |
| Distance marker-centre to marker-centre (mm) | as generated | _pending_ | _pending_ |

Acceptance: within **±0.5 mm** of nominal. If it fails, the printer scaled the
page — reprint before measuring anything else.

## 3. Photograph objects of known size

Use at least **10** objects spanning the grades you care about, e.g. steel
washers, coins, or measured onions:

1. measure the true maximum diameter with a caliper (±0.1 mm);
2. place the object flat on the mat, inside the marker rectangle;
3. photograph from directly above, filling the frame, mat fully visible;
4. repeat at three camera heights (≈20, 35, 50 cm) and with a ±15° tilt.

## 4. Measure with the project code

```python
from src.vision.size import measure_size
result = measure_size("photo.jpg", bbox_xywh=(x, y, w, h))
print(result["diameter_mm"], result["size_method"], result["calibration_confidence"])
```

Record `diameter_mm`, `size_method`, `markers_detected` and
`calibration_confidence` for each photo.

## 5. Compute the error and report it

For each object: `error_mm = predicted − true`, `relative_error = error_mm / true`.

Record in `evaluation/size_physical_validation.json`:

```json
{
  "validated": true,
  "n_objects": 10,
  "printer_scale_verified": true,
  "marker_side_mm_nominal": 40.0,
  "marker_side_mm_measured": 0.0,
  "mae_mm": 0.0,
  "mae_pct": 0.0,
  "max_abs_error_mm": 0.0,
  "by_camera_height": {},
  "by_tilt": {},
  "notes": "",
  "measured_by": "",
  "measured_on": ""
}
```

Report MAE and worst-case error, never a best case. If error exceeds the
procurement tolerance the policy depends on, the honest conclusion is that
calibrated sizing is not yet trustworthy for that tolerance — say so.

## 6. What remains true even after validation

* Validation is **per camera and per mat**. A different phone, lens or print
  scale invalidates the numbers until re-measured.
* Onions are not perfect spheres: "equivalent diameter" from a single top view
  is a proxy. Multi-view sizing reduces, but does not remove, that assumption.
* The pipeline reports `size_method = "uncalibrated"` and `diameter_mm = null`
  when markers are missing — it never extrapolates a millimetre figure.
