# ONION-Q — task shortcuts.
# Windows: run these from Git Bash, or copy the command out of the recipe.
# Requires: Python 3.12, `make` optional (every target is a plain command).

PYTHON ?= python
DATA ?= demo/tray_calibrated.png
AUDIO ?= dataset-acoustic/synthetic/demo_chirp_responses/synthetic_firmlike_001.wav

.PHONY: help setup smoke test test-fast fixtures batch deep report verify \
        registry manifest governance audit-detection benchmark export-onnx \
        review-queue train-attributes train-detector train-acoustic \
        api dashboard clean-generated

help:
	@echo "ONION-Q targets:"
	@echo "  setup              install dependencies"
	@echo "  smoke              clean-clone self-containment check"
	@echo "  test               full test suite"
	@echo "  test-fast          unit + grading + vision + acoustic only"
	@echo "  fixtures           build the composed tray fixture and calibration mat"
	@echo "  batch              quick batch scan demo + report"
	@echo "  deep               deep scan demo (4 views + audio)"
	@echo "  verify             verify the newest report's hash"
	@echo "  registry           regenerate models/registry.json"
	@echo "  manifest           regenerate dataset/training_manifest.csv"
	@echo "  governance         dataset governance report (licences, exclusions)"
	@echo "  audit-detection    detection data audit + leak-safe split"
	@echo "  benchmark          measure inference latency (with sample counts)"
	@echo "  export-onnx        export models to ONNX and check parity"
	@echo "  review-queue       export the human review / active-learning queue"
	@echo "  train-attributes   retrain the attribute model (leak-free split)"
	@echo "  train-detector     retrain the onion detector (leak-safe split)"
	@echo "  train-acoustic     retrain the SYNTHETIC acoustic demo baseline"
	@echo "  api                run the FastAPI service"
	@echo "  dashboard          serve the dashboard"

setup:
	$(PYTHON) -m pip install -r requirements.txt

smoke:
	$(PYTHON) scripts/clean_clone_smoke_test.py

test:
	$(PYTHON) -m pytest tests server/tests -q

test-fast:
	$(PYTHON) -m pytest tests/unit tests/grading tests/vision tests/acoustic -q

fixtures:
	$(PYTHON) scripts/make_calibration_mat.py
	$(PYTHON) scripts/compose_tray_image.py --count 9 --with-mat --out $(DATA)

batch:
	$(PYTHON) scripts/demo_batch_scan.py --images $(DATA) --lot LOT-DEMO-0001

deep:
	$(PYTHON) scripts/demo_deep_scan.py --demo-views 4 --audio $(AUDIO)

report:
	$(PYTHON) scripts/generate_report.py --from-scan local_data/scans/MH-NSK/scans.jsonl --qr

verify:
	$(PYTHON) scripts/generate_report.py --verify $$(ls -t reports/REPORT-*.json | head -1)

registry:
	$(PYTHON) scripts/build_model_registry.py

manifest:
	$(PYTHON) scripts/dataset_governance.py

governance:
	$(PYTHON) scripts/dataset_governance.py

audit-detection:
	$(PYTHON) scripts/audit_detection_dataset.py

benchmark:
	$(PYTHON) scripts/benchmark_inference.py --images 15

export-onnx:
	$(PYTHON) scripts/export_onnx.py

review-queue:
	$(PYTHON) scripts/export_review_queue.py

train-attributes:
	$(PYTHON) training/train_attribute_model.py --epochs 6 --input-size 160 --split-mode grouped

train-detector:
	$(PYTHON) training/train_detector.py --epochs 8 --batch-size 4 --min-size 320 --patience 3

train-acoustic:
	$(PYTHON) training/train_acoustic.py --data dataset-acoustic/synthetic/demo_chirp_responses

train-acoustic-real:
	$(PYTHON) training/train_acoustic.py --data dataset-acoustic/raw --require-verified-onion-data

api:
	$(PYTHON) -m uvicorn server.app:app --reload --port 8000

dashboard:
	$(PYTHON) -m http.server 8081 --directory dashboard

clean-generated:
	@echo "Removing generated artefacts only (never dataset or source):"
	rm -rf reports local_data demo/tray_composed.png demo/tray_composed.provenance.json
