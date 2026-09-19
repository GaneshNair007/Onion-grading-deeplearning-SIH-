# ONION-Q — Judge Q&A

Short, factual answers with the command or file that proves each one. Where the
honest answer is "we cannot yet", it says so.

---

**Q: What exactly does the AI decide?**
Nothing. Models produce *measurements* (defect probabilities, a calibrated
diameter, an acoustic quality score). `src/grading/engine.py` converts those
into a decision under a hashed policy. Proof: `tests/grading/test_policy_and_engine.py`.

**Q: Why is that better than a model that outputs "Grade A"?**
Because procurement standards change. We measured the alternative: a 4-class
grade head scores macro-F1 **0.312** (chance ≈ 0.25) on a leak-free split, while
the `rotten`/`sprout` attribute heads score F1 0.928 / 0.784. Measurements are
learnable; policy decisions are not a learning problem.
`python -c "import json;print(json.load(open('models/vision/attributes/metrics.json'))['quality_test'])"`

**Q: What is your detection accuracy?**
AP@0.50 = 0.639, recall@0.5 = 0.586, on 562 unseen test images from a grouped,
leak-safe split — 2,622 training images, 8 epochs, CPU. Our first baseline scored
0.256 on 40 official-split images; re-scored apples-to-apples on the leak-safe
split it scores 0.134, and both results are preserved in
`evaluation/detector_comparison.json`. The current detector is `experimental`,
not field-ready: its failures (crowded trays, tight crops) are documented with
image galleries in `evaluation/detector_gallery/`.

**Q: Did any of your numbers come from leakage?**
Yes, once — and we found it ourselves. Training on the official splits gave
`valid` accuracy 0.938 vs `test` 0.168. `evaluation/split_leakage.json` proves the
official `valid` split is **85.2 % near-duplicates of train** (median embedding
cosine 0.9986) vs 1.0 % for `test`. All headline numbers now use the grouped,
near-duplicate-aware split (`src/data/splits.py`), and the leaky metrics are kept
only as a record.

**Q: Can it detect internal rot with the phone's microphone?**
No — and no one can yet. There is **no public onion acoustic dataset**; the one
onion vibrometry study we found is `paper_only`
(DOI `10.1016/j.biosystemseng.2022.07.004`). Our acoustic model is a labelled
**synthetic demo**; the pipeline reports `ACOUSTIC_NOT_VALIDATED` and refuses to
let it change a grade. We ship the collection protocol
(`dataset-acoustic/collection_protocol.md`) and a metadata schema so the data can
be collected properly.

**Q: Did you use a general fruit/coconut audio dataset as onion data?**
No. The coconut tapping dataset is documented as `related_produce_acoustic`,
is **not redistributed** (CC BY-NC-ND) and is not in the training path.
`dataset-acoustic/SOURCES.md`.

**Q: How do you measure size?**
With a printed ArUco mat: 4 markers at a declared physical edge give a px/mm
scale, then an equivalent circular diameter from the mask area or the bounding
box. Geometry self-check: 0.21 % px/mm error on the rendered mat. Without a
marker, **no millimetre value is reported at all** — the code returns
`size_method="uncalibrated"` with a pixel note and the policy escalates.
`tests/vision/test_size_and_multiview.py`

**Q: What stops a confident wrong answer?**
Five gates, each producing a reason code: model confidence, occlusion/crowding,
missing calibration, unavailable-but-required measurement, multimodal
disagreement. Plus: poor audio → vision-only fallback; missing model artifact →
`model_unavailable` and nothing is graded.

**Q: Is this just an anomaly detector dressed as fraud detection?**
We make no fraud claim. The system records counts, reason codes and hashes.

**Q: Are the reports tamper-proof?**
No — tamper-**evident**. Editing a report breaks its canonical hash. Prove it in
under a minute: `docs/DEMO_SCRIPT.md` §5.

**Q: What about the dataset licence for the third source?**
*Onion Leaves and Bulb* has **no detected licence**, so
`src/data/provenance.py` sets `license_status = unresolved`,
`training_allowed = false`, and excludes it from
`dataset/training_manifest.csv`. It is not silently used.

**Q: Does it work offline?**
Yes. Captures and reports are journalled append-only; sync failures are retried;
a synced record is marked, never deleted; and a truncated write cannot hide
earlier records (`tests/e2e/test_field_workflow.py`).

**Q: What is the mobile story?**
A Kotlin reference module (`mobile/android/`) with CameraX, ONNX Runtime Mobile,
AudioRecord/chirp capture and WorkManager sync. It is **not compiled here** — no
Android SDK in this environment — and the PyTorch→ONNX export step is documented
rather than claimed. All latency numbers are desktop CPU.

**Q: Why should we trust the pipeline rather than a notebook?**
`python scripts/clean_clone_smoke_test.py` fails if any tracked file references a
machine-specific path or the untracked `backend/` tree; `models/registry.json` is
generated from artifacts on disk with a `metrics_confidence` field; every model
card lists split, support, metric definition and date.

**Q: What would you do with one more week?**
1. Retrain the detector longer (command ready) and re-measure.
2. Collect ~40 onions with the protocol, cut them open, and validate the acoustic
   features honestly.
3. Collect negatives (`scripts/build_negative_set.py`) and report a real
   false-onion rate.
4. Obtain an official procurement specification and set `source_verified = true`.

---

## DATA

**Q: How many real images, from which datasets, under which licences?**
3 746 annotated images: *Onion Grading v7* (2 963 images, CC BY 4.0) and *onions
v1* (783 images, Public Domain). A third source, *Onion Leaves and Bulb*, is in
the dataset but has **no detected licence**, so it is excluded from training.
`evaluation/dataset_governance.json`, `docs/DATASET_GOVERNANCE.md`.

**Q: What labels exist?**
Two kinds, kept separate: commercial classes (`Class 1`, `Class 2`,
`Extra Class`, `Reject`) and defect classes (`rotten`, `sprout`). We do not
invent the classes the data does not contain -- no `damaged`, no `undersized`,
no `bruising`, no shelf-life. `docs/LABEL_MAPPING.md` maps every source category
to a model label and states the limitation.

**Q: How was leakage handled?**
Measured, then removed. `evaluation/split_leakage.json` records that the official
`valid` split is 85.2 percent near-duplicate with `train` (median embedding
cosine 0.9986 vs 1.0 percent for `test`). `src/data/splits.py` groups
near-duplicates with an ImageNet-pretrained embedder and assigns whole groups to
splits: 3 746 images to 2 272 groups, zero groups spanning two splits. Detector
splits use the same method (`evaluation/detection_split.json`).

**Q: Which split do your headline numbers use?**
The grouped, leak-free split, not the official one. The detector numbers in
`docs/DETECTOR_EXPERIMENTS.md` are measured on the grouped test split, which is
harder than the source splits and includes the defect source that the official
validation split did not contain at all.

## MODEL

**Q: Why MobileNetV3?**
It is the smallest COCO-pretrained backbone in torchvision, it is BSD-3-Clause,
it exports to ONNX, and it fits a phone target. Trade-off stated: it is not the
most accurate option available.

**Q: Why Faster R-CNN and not YOLO?**
Because `ultralytics` is not installed in this environment and is a large,
licence-distinct dependency, while torchvision is already required. This is a
documented trade-off, not a claim that Faster R-CNN is better: it is heavier at
inference, and the export script exists so the model can be re-hosted elsewhere.
If a YOLO-family model is installed and beats the baseline on the same leak-safe
split, it should replace it -- the comparison table in
`docs/DETECTOR_EXPERIMENTS.md` is the decision record.

**Q: Why not predict the procurement grade directly from the image?**
We tried it. The 4-class commercial head scores macro-F1 0.312 (chance 0.25) on
leak-free data, while the attribute heads score F1 0.928 for rot and 0.784 for
sprout. Grade prediction is also structurally wrong for procurement, because the
rules change and the weights do not.

**Q: Where does the detector fail?**
See the false-positive, false-negative and localisation-error galleries in
`evaluation/detector_gallery/`. Typical failures: crowded trays with heavy
overlap, small distant onions, and glare. Onions below the confidence floor are
reported in a review zone rather than counted as detected.

## POLICY

**Q: Why separate the AI from the standard?**
Because procurement rules change. Our own `demo_policy.json` follows a Grade A
band of 45 to 65 mm reported in press context, while the relaxed (URS) class has
been introduced and withdrawn repeatedly. If the standard lived in model
weights, every change would require retraining and re-validation.

**Q: What if NAFED or the ministry changes the size requirement tomorrow?**
We edit one JSON file. The same model, the same measurements and the same
evidence produce a different decision, and every decision records the policy id,
version and hash used. Demonstrate it live by switching policy in the demo.

**Q: Are your thresholds official?**
No, and the system says so. `source_verified` is false, the policy summary
reads `Demonstration grading configuration`, and every decision carries
`POLICY_UNVERIFIED`. The loader **refuses** a policy that claims verification
without a source URL, a verification date and an official source type, so a news
article can never be promoted to a standard by editing a boolean.

## DEPLOYMENT

**Q: Does it work offline?**
Yes. Field captures are written to an append-only journalled store with fsync
per record; sync failures are retried; synced records are marked, never deleted;
a truncated final line cannot hide earlier records.
`tests/e2e/test_field_workflow.py`.

**Q: How are models updated in the field?**
The model identity travels with every report (`models/registry.json`,
model card, artifact hash). A new model is published as a new registry entry with
its own dataset fingerprint and metrics, so results produced by different model
versions are never silently pooled.

**Q: How do you prevent duplicate sync?**
Every record carries a client-generated UUID and the server upserts on it. The
same payload sent twice stores one row -- tested in
`test_sync_is_idempotent`.

## TRUST

**Q: Can a report be manipulated?**
It can be modified, and the modification is detectable. The report carries a
canonical-JSON SHA-256 and hashes of its input evidence; changing a percentage by
0.01, the inspector id, or an evidence hash each fails verification
(`tests/unit/test_report_integrity.py`). We are precise: tamper-**evident**, not
tamper-proof, and we make no fraud-detection claim.

**Q: What happens when the AI is uncertain?**
Uncertainty is never converted into a confident answer. Low confidence,
crowding, missing calibration, unavailable-but-required measurements and
multimodal disagreement all escalate to `manual_review` with a machine-readable
reason code, and the batch report keeps manual review as its own visible class.

**Q: Can an inspector override the system?**
Yes, and the override is stored beside the machine decision -- never in place of
it -- with inspector id, timestamp, the machine decision, its confidence, the
reason code and the model version. `/dashboard/overrides` reports the override
rate and the AI-versus-human disagreement rate by reason and model version.

## COST

**Q: What hardware is required?**
An Android phone (camera, speaker, microphone) and a printed calibration mat. No
piezo sensor, no ADC, no Raspberry Pi in the core mobile path: that is a future
research track, not this product.

**Q: What does the deployment actually run today?**
A Python CLI and a FastAPI service over SQLite, both from this repository. The
Android source exists but has not been compiled in this environment -- stated in
`docs/ANDROID_BUILD_STATUS.md` rather than implied.
