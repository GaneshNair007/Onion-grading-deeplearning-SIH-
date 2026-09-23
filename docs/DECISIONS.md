# Final Integration Decisions

- Preserve the current same-origin HTML dashboard; do not replace it with the older remote frontend branch.
- Keep the existing Faster R-CNN/MobileNetV3 stack because artifacts, model cards, and measured evaluations exist.
- Treat model outputs as observations; keep procurement decisions in the versioned policy engine.
- Refuse fabricated millimetres: ArUco calibration is required when policy needs physical size.
- Keep `demo_policy` explicitly unverified until an authoritative primary source is approved.
- Keep acoustic screening separate and research-only; it never changes procurement grade.
- Persist evidence before temporary uploads are deleted and hash both original and annotated files into reports.
- Use SQLite for the reliable local demo while retaining optional Supabase sync for later deployment.
