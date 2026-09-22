#!/usr/bin/env python3
"""
One-command CI gate for the Onion-Q repository.

Runs the exact checks a clean GitHub Actions checkout would run, in order:
  1. Reproducibility smoke test (no untracked/local dependencies)
  2. Import every production module the app actually uses
  3. Unit + integration + contract tests (skip artifact-dependent ones)
  4. Grading + report-integrity gate

Exit 0 = green. Exit nonzero = the failing step is printed.

Usage:
    python scripts/run_ci_gate.py              # run all steps
    python scripts/run_ci_gate.py --step 3     # run only step 3
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable]


def run(cmd: list[str], label: str) -> int:
    print(f"\n===== {label} =====")
    print("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True)
    if proc.stdout:
        # Trim the very long PR-curve dumps in detector metrics prints.
        lines = proc.stdout.splitlines()
        out = []
        for ln in lines:
            if "pr_curve" in ln or "score_sweep" in ln:
                out.append(ln[:200] + ("..." if len(ln) > 200 else ""))
            else:
                out.append(ln)
        print("\n".join(out))
    print(f"--> exit {proc.returncode}")
    return proc.returncode


STEPS = {
    1: ("Reproducibility smoke test",
        [sys.executable, "scripts/clean_clone_smoke_test.py"]),
    2: ("Import every module",
        [sys.executable, "-"],
        "_import_check"),
    3: ("Unit + integration + contract tests",
        [sys.executable, "-m", "pytest", "tests", "server/tests",
         "-q", "-m", "not slow"]),
    4: ("Grading / report-integrity gate",
        [sys.executable, "-m", "pytest",
         "tests/grading", "tests/unit/test_report_integrity.py",
         "tests/e2e/test_production_safety.py", "-q"]),
}


def _import_check() -> int:
    code = """
import importlib
modules = [
    "src.common.contracts", "src.common.version", "src.common.reasons",
    "src.data.labels", "src.data.dataset_registry", "src.data.provenance",
    "src.data.splits", "src.grading.engine", "src.grading.policy",
    "src.grading.batch", "src.fusion.fusion", "src.reporting.audit_hash",
    "src.reporting.evidence", "src.reporting.generator",
    "src.reporting.qr", "src.mobile.offline_store", "src.mobile.capture_protocol",
    "src.vision.model", "src.vision.rejection", "src.vision.size",
    "src.vision.detector", "src.vision.capture_quality", "src.vision.multi_view",
    "src.acoustic.loading", "src.acoustic.quality", "src.acoustic.features",
    "src.acoustic.impact_gate", "src.acoustic.collection",
    "inference.vision_inference", "inference.acoustic_inference",
    "inference.batch_scan", "inference.deep_scan", "inference.combined_scan",
    "server.app",
]
bad = []
for name in modules:
    try:
        importlib.import_module(name)
        print("ok", name)
    except Exception as exc:
        bad.append(f"{name}: {exc}")
        print("FAIL", name, "->", exc)
if bad:
    print("\\nFAILED imports:", len(bad))
    sys.exit(1)
print("\\nAll modules imported.")
"""
    proc = subprocess.run(
        [sys.executable, "-c", code], cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.stdout:
        print(proc.stdout)
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=int, choices=sorted(STEPS),
                        help="Run only this step number")
    args = parser.parse_args()

    steps = [args.step] if args.step else sorted(STEPS)

    failures = []
    for n in steps:
        label, cmd, *rest = STEPS[n]
        if n == 2:
            rc = _import_check()
        else:
            rc = run(cmd, label)
        if rc != 0:
            failures.append(n)

    if failures:
        print(f"\n***** CI GATE FAILED at step(s): {failures} *****")
        sys.exit(1)
    print("\n***** CI GATE PASSED *****")
    sys.exit(0)


if __name__ == "__main__":
    main()
