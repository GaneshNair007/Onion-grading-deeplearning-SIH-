"""Single source of truth for the project's version identity.

Reports, API responses and the dashboard all quote these values, so a judge can
map any output back to the exact code, models and policy that produced it.
Nothing here is hard-coded per caller: the git commit is read from the
repository, the model versions from ``models/registry.json``, and the policy
version from the active grading configuration.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

APP_VERSION = "0.2.0"
SCHEMA_VERSION = "1.0.0"
REPORT_VERSION = "1.0.0"


@lru_cache(maxsize=1)
def git_commit(short: bool = False) -> str:
    """Current commit, or an explicit 'unknown' when git is unavailable."""
    args = ["git", "rev-parse", "--short", "HEAD"] if short else \
        ["git", "rev-parse", "HEAD"]
    try:
        out = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True,
                             text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        pass
    return "unknown"


@lru_cache(maxsize=1)
def git_branch() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                             cwd=PROJECT_ROOT, capture_output=True, text=True,
                             timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        pass
    return "unknown"


def registry_path() -> Path:
    return PROJECT_ROOT / "models" / "registry.json"


def model_versions() -> Dict[str, Any]:
    """Model ids + status from the registry (never invented when absent)."""
    path = registry_path()
    if not path.exists():
        return {"note": "models/registry.json not found; run "
                        "scripts/build_model_registry.py"}
    data = json.loads(path.read_text(encoding="utf-8"))
    models = {}
    for model_id, entry in (data.get("models") or {}).items():
        models[model_id] = {
            "task": entry.get("task"),
            "status": entry.get("status"),
            "artifact_path": entry.get("artifact_path"),
            "model_card": entry.get("model_card"),
            "git_commit": entry.get("git_commit"),
        }
    return {
        "registry_version": data.get("registry_version"),
        "generated_at": data.get("generated_at"),
        "models": models,
        "not_available": data.get("not_available", []),
    }


def policy_version(policy: Optional[Any] = None) -> Dict[str, Any]:
    """Policy identity for a report header."""
    try:
        from src.grading.policy import active_policy
        policy = policy or active_policy()
    except Exception as exc:  # pragma: no cover - policy config optional
        return {"error": f"policy unavailable: {exc}"}
    return {
        "policy_id": policy.policy_id,
        "version": policy.version,
        "policy_hash": policy.policy_hash,
        "source_verified": policy.source_verified,
        "effective_from": policy.effective_from,
    }


def runtime_versions() -> Dict[str, Any]:
    """Compact identity block embedded in reports and API responses."""
    return {
        "app_version": APP_VERSION,
        "schema_version": SCHEMA_VERSION,
        "git_commit": git_commit(),
        "git_commit_short": git_commit(short=True),
        "git_branch": git_branch(),
    }


def environment() -> Dict[str, Any]:
    """Runtime facts needed to interpret any latency or metric claim."""
    info: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    for name in ("torch", "torchvision", "numpy", "cv2", "onnxruntime"):
        try:
            module = __import__(name)
            info[name] = getattr(module, "__version__", "unknown")
        except ImportError:
            info[name] = None
    return info


def full_identity(policy: Optional[Any] = None) -> Dict[str, Any]:
    """Everything a report needs to be traceable."""
    return {
        **runtime_versions(),
        "policy": policy_version(policy),
        "models": model_versions(),
        "environment": environment(),
    }


if __name__ == "__main__":
    print(json.dumps(full_identity(), indent=2))
