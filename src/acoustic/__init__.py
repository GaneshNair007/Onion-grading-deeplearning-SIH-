"""Onion acoustic processing package.

Signal-processing pipeline for the phone-only acoustic path (master plan,
Architecture A). Operates on WAV recordings such as those described by
dataset-acoustic/metadata_schema.json.

Modules
-------
loading   : WAV loading, mono conversion, normalization, rate inspection
quality   : recording quality gates (clipping, silence, SNR, duration, rate)
features  : FFT/STFT, log-mel spectrograms, acoustic feature extraction,
            CSV/Parquet feature export
splits    : onion-level (not recording-level) train/validation/test splits
"""
