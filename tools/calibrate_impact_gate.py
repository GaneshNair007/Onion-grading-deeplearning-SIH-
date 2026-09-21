#!/usr/bin/env python3
"""Calibrate the impact gate on REAL phone recordings.

Reads the calibration captures saved by the scan page (section 4) via
``POST /acoustic/calibration-capture`` from ``local_data/gate_calibration/``,
runs the REAL gate (``src/acoustic/impact_gate.check_impact_present``) on
every recording, and:

1. reports the current gate's verdict per recording against expectations
   (``*_valid`` must pass; everything else must be rejected);
2. reports, per metric, the measured separation between recordings that MUST
   pass and MUST be rejected — stating plainly when a metric cannot separate
   the classes at all (the fix is then capture technique or scope, not a
   threshold);
3. sweeps candidate thresholds by patching the gate's own module constants
   and re-running the real gate — so every candidate is evaluated by the
   exact production code path, not a copy of it.

Nothing is auto-edited: the output ends with the exact values to place in
``src/acoustic/impact_gate.py`` for a human to apply, then the regression
suite must be re-run.

Note on scope: the chirp branch verifies that an excitation occurred
(sustained energy over the pre-excitation floor). It cannot, by itself,
prove the onion *responded* — if ``chirp_room`` shows no separation from
``chirp_valid`` on these metrics, that is a reported finding: the no-onion
case must then be handled by the model stage + confidence labels, not the
gate.

Usage:
    python tools/calibrate_impact_gate.py [--dir local_data/gate_calibration]
"""
from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from itertools import product
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.acoustic import impact_gate as gate_mod  # noqa: E402
from src.acoustic.impact_gate import check_impact_present  # noqa: E402
from src.acoustic.loading import load_wav  # noqa: E402

MUST_PASS = {"chirp_valid", "tap_valid"}
CANDIDATES = {
    "MIN_PEAK_AMPLITUDE": [0.015, 0.020, 0.030, 0.040],
    "MIN_CREST_FACTOR": [2.5, 3.0, 3.5, 4.0],
    "MIN_DECAY_RATE_PER_S": [0.5, 0.8, 1.5, 2.0],
    # Speaker chirps commonly show 20-30 dB excess over the room floor; the
    # onion-absence gap (if any) lives somewhere in that range.
    "CHIRP_MIN_EXCESS_DB": [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0,
                            18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0],
}
# MIN_SNR_TO_FLOOR_DB stays fixed: it is a physical floor (transient vs
# ambient), not a tunable class separator, and sweeping 4 constants is
# already 1296 gate runs per pass.


def capture_method_for(kind: str):
    if kind.startswith("chirp"):
        return "phone_chirp"
    if kind.startswith("tap"):
        return "phone_tap"
    return None  # noise kinds hit the unknown-method branch, like real scans


def load_set(directory: Path) -> list:
    rows = []
    for wav in sorted(directory.glob("*.wav")):
        meta_path = wav.with_suffix(".json")
        if not meta_path.exists():
            print(f"  (skip, no sidecar: {wav.name})")
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        kind = meta.get("kind", "unknown")
        try:
            sr, sig = load_wav(str(wav))
        except Exception as exc:
            print(f"  (skip, unreadable: {wav.name}: {exc})")
            continue
        rows.append({
            "file": wav.name, "kind": kind,
            "must_pass": kind in MUST_PASS,
            "sig": np.asarray(sig, dtype=np.float64).ravel(),
            "sr": int(sr),
        })
    return rows


def current_verdicts(rows: list) -> None:
    print("current gate verdicts (defaults):")
    for r in rows:
        g = check_impact_present(r["sig"], r["sr"],
                                 capture_method=capture_method_for(r["kind"]))
        ok = g["passed"] == r["must_pass"]
        m = g["measured"]
        print(f"  {'OK ' if ok else 'BAD'} {r['kind']:<12} "
              f"gate {'pass' if g['passed'] else 'REJECT'} "
              f"(expect {'pass' if r['must_pass'] else 'reject'}) "
              f"peak={m.get('peak_amplitude')} crest={m.get('crest_factor')} "
              f"decay={m.get('post_peak_decay_rate_per_s', 'n/a')} "
              f"excess={m.get('rms_excess_over_floor_db', 'n/a')}dB "
              f"floor={m.get('noise_floor_rms')}({m.get('floor_source')})")
        if not ok and g["reasons"]:
            print(f"       reasons: {'; '.join(g['reasons'])}")
        r["measured"] = g["measured"]


def separation(rows: list, key: str, kinds_filter=None) -> None:
    subset = [r for r in rows if kinds_filter is None or r["kind"] in kinds_filter]
    pos = [r["measured"][key] for r in subset
           if r["must_pass"] and r["measured"].get(key) is not None]
    neg = [r["measured"][key] for r in subset
           if not r["must_pass"] and r["measured"].get(key) is not None]
    if not pos or not neg:
        print(f"  {key:<22} insufficient data (pass={len(pos)}, reject={len(neg)})")
        return
    lo_p, hi_p = min(pos), max(pos)
    lo_n, hi_n = min(neg), max(neg)
    if hi_p < lo_n:
        note = f"separable — any threshold in [{hi_p:.3g}, {lo_n:.3g}]"
    elif hi_n < lo_p:
        note = f"separable (inverted) — threshold in [{hi_n:.3g}, {lo_p:.3g}]"
    else:
        note = "NO SEPARATION — classes overlap; fix capture technique or scope"
    print(f"  {key:<22} pass [{lo_p:.3g}, {hi_p:.3g}]  "
          f"reject [{lo_n:.3g}, {hi_n:.3g}]  -> {note}")


@contextmanager
def run_with_constants(**overrides):
    saved = {k: getattr(gate_mod, k) for k in overrides}
    for k, v in overrides.items():
        setattr(gate_mod, k, v)
    try:
        yield_flag = True
        while yield_flag:
            yield_flag = False
            yield
    finally:
        for k, v in saved.items():
            setattr(gate_mod, k, v)


def sweep(rows: list) -> None:
    keys = list(CANDIDATES)
    combos = list(product(*(CANDIDATES[k] for k in keys)))
    best = []
    for combo in combos:
        overrides = dict(zip(keys, combo))
        with run_with_constants(**overrides):
            correct = sum(
                1 for r in rows
                if check_impact_present(
                    r["sig"], r["sr"],
                    capture_method=capture_method_for(r["kind"]))["passed"]
                == r["must_pass"])
        best.append((correct, overrides))
    best.sort(key=lambda t: (-t[0], json.dumps(t[1], sort_keys=True)))
    total = len(rows)
    print(f"\nsweep over {len(combos)} threshold sets (real gate each time) — "
          f"best {best[0][0]}/{total}:")
    print("  " + "  ".join(f"{k.replace('MIN_', '').replace('PER_S', ''):<10}"
                           for k in keys) + "  correct")
    perfect_seen = False
    for correct, overrides in best[:6]:
        if perfect_seen and correct < best[0][0]:
            break
        if correct == total:
            perfect_seen = True
        print("  " + "  ".join(f"{overrides[k]:<10.3g}" for k in keys)
              + f"  {correct}/{total}")
    if best[0][0] == total:
        print(f"\n  perfect configuration(s) found. First one: "
              f"{json.dumps(best[0][1], indent=2)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path,
                    default=PROJECT_ROOT / "local_data" / "gate_calibration")
    args = ap.parse_args()
    rows = load_set(args.dir)
    if len(rows) < 6:
        print(f"only {len(rows)} calibration recordings — capture at least "
              "3× chirp_valid, 3× chirp_room, 3× tap_valid and a few noise "
              "clips via the scan page (section 4) first.")
        return 1
    kinds = sorted({r["kind"] for r in rows})
    missing = ({"chirp_valid", "chirp_room", "tap_valid"} - set(kinds))
    if missing:
        print(f"warning: no recordings for {sorted(missing)} — the sweep "
              "cannot validate those paths")

    current_verdicts(rows)

    print("\nper-metric separation (what the thresholds must respect):")
    separation(rows, "peak_amplitude")
    separation(rows, "transient_snr_db")
    separation(rows, "crest_factor", kinds_filter={"tap_valid"})
    separation(rows, "post_peak_decay_rate_per_s", kinds_filter={"tap_valid"})
    separation(rows, "rms_excess_over_floor_db",
               kinds_filter={"chirp_valid", "chirp_room"})

    sweep(rows)

    print("\nnext step (human applies, nothing is auto-edited):")
    print("  1. pick the threshold set above where every MUST-pass kind passes")
    print("     and every MUST-reject kind fails — prefer values closest to")
    print("     the current defaults when several are perfect;")
    print("  2. set those constants in src/acoustic/impact_gate.py;")
    print("  3. run: python -m pytest tests/acoustic -q   (regression suite)")
    print("  4. re-capture one clip of each kind and confirm the page shows")
    print("     no MISMATCH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
