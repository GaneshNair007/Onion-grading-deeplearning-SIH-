# raw/ — Verified raw onion acoustic recordings

**Currently empty — no verified onion acoustic recordings exist yet.**

This directory is reserved for real phone-only onion recordings collected
under `collection_protocol.md`:

```
raw/onion_bulbs/ONION_000001/AUDIO_000001.wav
raw/onion_bulbs/ONION_000001/AUDIO_000001.json   <- sidecar metadata per metadata_schema.json
raw/onion_bulbs/ONION_000001/AUDIO_000001_ambient.wav
```

Requirements before any file may be placed here:

1. `dataset_type: verified_onion_acoustic` in its sidecar metadata.
2. A real recording device recorded in `capture_metadata.device_model`.
3. `internal_label` filled only by a documented `ground_truth_method`
   (`cut_open` or `expert_inspection`) — never inferred.
4. License/redistribution status recorded in `SOURCES.md`.

`tools/prepare_acoustic_dataset.py` will refuse to pack files from this
directory into `parts/` unless a valid sidecar metadata JSON exists.
