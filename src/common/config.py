"""Loader for ``config/models.yaml`` — the single source of truth for
inference and fusion thresholds.

Why this exists: the project rule is *no hardcoded model outputs or
thresholds in Python source*. Decision behaviour must be inspectable and
changeable without touching code. ``get_setting`` returns ``None`` when a
value is absent or explicitly ``null`` in the YAML; callers decide what a
``None`` means (typically: the check is disabled), so a missing value can
never silently become an invented number.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "models.yaml"


@functools.lru_cache(maxsize=1)
def load_models_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load (and cache) the models config. Missing file -> empty dict."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def get_setting(key: str, default: Any = None) -> Any:
    """Return a config value. YAML ``null``/absent wins over ``default``."""
    value = load_models_config().get(key, default)
    return default if value is None else value
