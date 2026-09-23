# Judge Technical Notes

- **Why detection, not only classification?** A tray needs one record and one auditable decision per onion; image-level classification cannot produce correct counts or evidence.
- **Why boxes rather than masks today?** The measured detector artifact is the currently integrated baseline. Segmentation labels exist, but no stronger validated segmentation artifact is claimed.
- **How is diameter measured?** An OpenCV ArUco marker gives pixels per millimetre; the current prototype uses the calibrated bounding-box long side. Without a marker, millimetres are null.
- **What is URS?** Under Relaxed Specification, represented as the policy engine's `relaxed` decision. The included thresholds are demonstration settings, not claimed government rules.
- **Why a policy engine?** Models observe rot, sprout, confidence and size; a versioned, reviewable policy makes the procurement decision and records the reasons.
- **Why acoustic?** It explores internal response patterns invisible to a camera. It is separate from procurement grading.
- **How does acoustic analysis work?** Browser audio captures a chirp/tap response; the backend checks noise/impact validity and extracts time/frequency-domain features.
- **Is acoustic validated on onions?** No. The current classifier is synthetic-only. Real data collection and cut-open labelling are implemented, and invalid audio produces no prediction.
- **What happens in noise?** Ambient and signal-quality gates request a retest instead of returning a grade-like answer.
- **What about a potato or random image?** Detector confidence plus an embedding-distance rejection reference prevents unsupported inputs from entering grading; uncertain cases are refused or reviewed, not named as a potato without a trained class.
- **What happens at low confidence?** The policy emits Manual Review with reason codes.
- **Models and measured accuracy?** Faster R-CNN MobileNetV3 detector: leak-safe test AP@0.50 0.1339, AP@0.50:0.95 0.0303, F1 0.2075 at score 0.5. MobileNetV3 attribute head carveout: rot F1 0.9427 and sprout F1 0.8545; these are not independent field results. Broad quality test macro-F1 is 0.1202 and is not presented as production quality.
- **How does it scale?** Models load once per process, batch scans reuse them, SQLite supports the local demo, and optional Supabase synchronization provides a migration path.
