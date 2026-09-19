#!/usr/bin/env python3
"""Clean-clone smoke test: fail loudly if the repository depends on
anything that is not tracked.

Checks
------
1. Required directories and files exist.
2. JSON/config files parse.
3. The dataset manifest is readable and its annotation files are present.
4. The model registry parses (if present).
5. **No tracked source file references a machine-specific path** (e.g.
   `C:\\SIH`) or imports from the previously untracked `backend/` tree.
6. Core modules import without the local-only directories.
7. Training entry points respond to `--help`.
8. No tracked file is near or over the GitHub 100 MiB limit.

`--tracked-copy` additionally performs a REAL clean-clone test: it copies
exactly the files git would deliver (`git ls-files -co --exclude-standard`, i.e.
tracked + untracked-but-not-ignored, in their current working-tree state) into a
fresh temporary directory and runs the checks and a fast test subset **there**.
That is the check that proves no untracked local directory is required.

Exit code 0 = the repository is self-contained.

Usage:
    python scripts/clean_clone_smoke_test.py
    python scripts/clean_clone_smoke_test.py --tracked-copy
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

REQUIRED_PATHS = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    ".env.example",
    "dataset/MANIFEST.csv",
    "dataset-acoustic/README.md",
    "dataset-acoustic/MANIFEST.csv",
    "docs/ARCHITECTURE.md",
    "src/data/dataset_registry.py",
    "src/data/labels.py",
    "src/vision/model.py",
    "src/vision/rejection.py",
    "src/acoustic/features.py",
    "src/acoustic/quality.py",
    "src/fusion/fusion.py",
    "src/grading/policy.py",
    "src/grading/engine.py",
    "src/reporting/generator.py",
    "training/train_attribute_model.py",
    "training/train_detector.py",
    "inference/vision_inference.py",
    "inference/acoustic_inference.py",
    "scripts/demo_batch_scan.py",
    "scripts/demo_deep_scan.py",
    # Added in the consolidation pass: contracts, version identity,
    # evidence hashing, governance, tooling and the serving layer.
    "src/common/contracts.py",
    "src/common/version.py",
    "src/common/reasons.py",
    "src/reporting/evidence.py",
    "src/reporting/qr.py",
    "src/vision/detector.py",
    "src/vision/size.py",
    "src/vision/multi_view.py",
    "src/vision/capture_quality.py",
    "src/mobile/offline_store.py",
    "src/mobile/capture_protocol.py",
    "inference/batch_scan.py",
    "inference/deep_scan.py",
    "inference/combined_scan.py",
    "server/app.py",
    "server/store.py",
    "dashboard/index.html",
    "config/grading/demo_policy.json",
    "config/grading/schema.json",
    "docs/FEATURE_STATUS.md",
    "docs/DEPLOYMENT_STATUS.md",
    "docs/ONION_Q_TECHNICAL_WHITEPAPER.md",
    "docs/ANDROID_BUILD_STATUS.md",
    "docs/REAL_DATA_TOOLING.md",
    "docs/PHYSICAL_SIZE_VALIDATION_PROTOCOL.md",
    "scripts/dataset_governance.py",
    "scripts/audit_detection_dataset.py",
    "scripts/add_labelled_images.py",
    "scripts/collect_acoustic_sample.py",
    "scripts/add_cut_open_ground_truth.py",
    "scripts/benchmark_inference.py",
    "scripts/export_onnx.py",
    "scripts/export_review_queue.py",
    "pytest.ini",
    ".github/workflows/test.yml",
]

FORBIDDEN_PATTERNS = [
    (r"C:\\+SIH", "machine-specific absolute path (C:\\SIH)"),
    (r"C:/SIH", "machine-specific absolute path (C:/SIH)"),
    (r"C:\\+Users", "machine-specific absolute user path (C:\\Users)"),
    (r"sys\.path\.append\([^)]*backend", "sys.path hack pointing at the untracked backend/ tree"),
    (r"from\s+app\.", "import from the untracked `app` package (backend/)"),
    (r"import\s+app\.", "import from the untracked `app` package (backend/)"),
]

#: GitHub rejects files >= 100 MiB; stop well before that.
MAX_TRACKED_BYTES = 95_000_000

SCAN_SUFFIXES = {".py"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules",
             "dataset", "dataset-acoustic", "logs", ".freebuff", ".pytest_cache",
             "backend"}
#: This file necessarily contains the forbidden patterns as regex literals.
SELF = "scripts/clean_clone_smoke_test.py"


def tracked_python_files() -> list[Path]:
    """The files a clean clone actually receives (git-tracked), if git is available."""
    try:
        proc = subprocess.run(["git", "ls-files", "*.py"], cwd=PROJECT_ROOT,
                              capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and proc.stdout.strip():
            return [PROJECT_ROOT / line.strip()
                    for line in proc.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return sorted(PROJECT_ROOT.rglob("*.py"))


def scan_for_forbidden() -> list[str]:
    problems: list[str] = []
    for path in sorted(tracked_python_files()):
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel == SELF:
            continue
        rel_parts = set(path.relative_to(PROJECT_ROOT).parts[:-1])
        if rel_parts & SKIP_DIRS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, description in FORBIDDEN_PATTERNS:
            for match in re.finditer(pattern, text):
                line = text[: match.start()].count("\n") + 1
                problems.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{line}: {description}")
    return problems


def check_required_paths() -> list[str]:
    return [p for p in REQUIRED_PATHS if not (PROJECT_ROOT / p).exists()]


def check_manifest() -> list[str]:
    problems = []
    manifest = PROJECT_ROOT / "dataset" / "MANIFEST.csv"
    if not manifest.exists():
        return ["dataset/MANIFEST.csv missing"]
    import csv
    try:
        with open(manifest, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            problems.append("dataset/MANIFEST.csv has no rows")
        missing = 0
        for row in rows:
            if not row["path_in_repo"].endswith(".json"):
                continue
            p = PROJECT_ROOT / "dataset" / row["part"] / row["path_in_repo"]
            if not p.exists():
                missing += 1
        if missing:
            problems.append(f"{missing} annotation files listed in the manifest are absent from this checkout")
    except Exception as exc:  # pragma: no cover
        problems.append(f"dataset/MANIFEST.csv unreadable: {exc}")
    return problems


def check_json_files() -> list[str]:
    problems = []
    for path in sorted(PROJECT_ROOT.rglob("*.json")):
        rel = set(path.relative_to(PROJECT_ROOT).parts[:-1])
        if rel & {"dataset", "dataset-acoustic", ".git", "node_modules", ".freebuff"}:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.relative_to(PROJECT_ROOT)}: invalid JSON ({exc})")
    return problems


def check_imports() -> list[str]:
    problems = []
    modules = [
        "src.data.dataset_registry",
        "src.data.labels",
        "src.vision.rejection",
        "src.acoustic.features",
        "src.acoustic.quality",
        "src.fusion.fusion",
        "src.grading.policy",
        "src.grading.engine",
        "src.reporting.generator",
    ]
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "import importlib;"
        "bad=[]\n"
        "for m in %r:\n"
        "    try: importlib.import_module(m)\n"
        "    except Exception as e: bad.append(f'{m}: {type(e).__name__}: {e}')\n"
        "print('\\n'.join(bad) if bad else 'IMPORTS_OK')"
    ) % (str(PROJECT_ROOT), modules)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    if out != "IMPORTS_OK":
        problems.append("module import failures:\n" + out)
    if proc.returncode != 0 and not out:
        problems.append(f"import check crashed: {proc.stderr.strip()[:400]}")
    return problems


def check_entrypoints() -> list[str]:
    problems = []
    for script in ("training/train_attribute_model.py", "training/train_detector.py",
                   "scripts/inspect_dataset.py"):
        path = PROJECT_ROOT / script
        if not path.exists():
            continue
        proc = subprocess.run([sys.executable, str(path), "--help"],
                              capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            problems.append(f"{script} --help failed: {proc.stderr.strip()[:200]}")
    return problems


def check_large_files() -> list[str]:
    """No file that would be committed may approach the GitHub 100 MiB limit."""
    problems: list[str] = []
    for rel in deliverable_files():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            problems.append(f"{rel} is {size / 1e6:.1f} MB — would be rejected "
                            f"by GitHub (limit 100 MiB) and is over the "
                            f"{MAX_TRACKED_BYTES / 1e6:.0f} MB project ceiling")
    return problems


def deliverable_files() -> list[str]:
    """Exactly the files git would deliver from this working tree.

    ``git ls-files -co --exclude-standard`` lists tracked files plus
    untracked-but-not-ignored files, which is what a commit of this state would
    contain. Ignored artefacts (weights, logs, local scratch) are excluded by
    git itself rather than by a hand-maintained list.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"], cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=120)
        if proc.returncode == 0:
            return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return []


def tracked_copy_check() -> list[str]:
    """Copy the deliverable file set elsewhere and run the checks there."""
    problems: list[str] = []
    files = deliverable_files()
    if not files:
        return ["git is unavailable, so the tracked-copy check cannot run"]

    import shutil
    import tempfile

    tmp_root = Path(tempfile.mkdtemp(prefix="onionq-clean-test-"))
    try:
        copied = 0
        skipped: list[str] = []
        for rel in files:
            source = PROJECT_ROOT / rel
            if not source.is_file():
                continue
            if source.stat().st_size > MAX_TRACKED_BYTES:
                skipped.append(rel)
                continue
            destination = tmp_root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied += 1
        print(f"      copied {copied} file(s) to {tmp_root}")
        if skipped:
            problems.append(f"large files not copied: {skipped}")

        proc = subprocess.run(
            [sys.executable, "scripts/clean_clone_smoke_test.py"],
            cwd=tmp_root, capture_output=True, text=True, timeout=900)
        if proc.returncode != 0:
            problems.append("smoke test failed in the copied tree:\n"
                            + (proc.stdout or "")[-1500:])
        else:
            print("      smoke test passed in the copied tree")

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/grading", "tests/contracts",
             "tests/unit/test_report_integrity.py", "server/tests", "-q"],
            cwd=tmp_root, capture_output=True, text=True, timeout=1800)
        tail = (proc.stdout or "").strip().splitlines()[-3:]
        if proc.returncode != 0:
            problems.append("tests failed in the copied tree:\n" + "\n".join(tail))
        else:
            print("      tests passed in the copied tree: " + " | ".join(tail))
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    return problems


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tracked-copy", action="store_true",
                    help="also copy the deliverable files to a temp directory "
                         "and run the checks there")
    args = ap.parse_args(argv)

    checks = {
        "required paths": check_required_paths(),
        "forbidden references": scan_for_forbidden(),
        "dataset manifest": check_manifest(),
        "json files": check_json_files(),
        "module imports": check_imports(),
        "entry points": check_entrypoints(),
        "file sizes": check_large_files(),
    }
    if args.tracked_copy:
        checks["tracked-copy clean run"] = tracked_copy_check()
    failed = False
    for name, problems in checks.items():
        if problems:
            failed = True
            print(f"FAIL  {name}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"ok    {name}")
    print()
    if failed:
        print("CLEAN-CLONE SMOKE TEST FAILED — the repository is not self-contained.")
        return 1
    print("CLEAN-CLONE SMOKE TEST PASSED — no hidden local dependency detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
