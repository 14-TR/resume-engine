"""Persistent user configuration for resume-engine.

Config file lives at ~/.config/resume-engine/config.toml (XDG-style).
Falls back to ~/.resume-engine.toml for portability.

Supported keys:
  model     - default LLM backend: ollama | openai | anthropic
  output    - default output path for tailor command
  outdir    - default output directory for batch/package commands
  format    - default output format: md | pdf
  template  - default resume template slug
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = _XDG_CONFIG_HOME / "resume-engine"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# ---------------------------------------------------------------------------
# Valid keys + their allowed values (None = free-form string)
# ---------------------------------------------------------------------------

VALID_KEYS: dict[str, list[str] | None] = {
    "model": ["ollama", "openai", "anthropic"],
    "format": ["md", "pdf"],
    "output": None,
    "outdir": None,
    "template": None,
}


# ---------------------------------------------------------------------------
# TOML helpers (stdlib tomllib for read, hand-rolled for write)
# ---------------------------------------------------------------------------


def _load_raw() -> dict[str, Any]:
    """Load raw config dict from disk. Returns empty dict if not found."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return _fallback_toml_parse(CONFIG_FILE.read_text(encoding="utf-8"))
    with CONFIG_FILE.open("rb") as fh:
        return tomllib.load(fh)


def _fallback_toml_parse(text: str) -> dict[str, Any]:
    """Minimal key = value TOML parser for Python < 3.11 with no tomli."""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            result[k] = v
    return result


def _write(data: dict[str, Any]) -> None:
    """Write config dict to disk as minimal TOML."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# resume-engine configuration\n"]
    for k, v in sorted(data.items()):
        lines.append(f'{k} = "{v}"\n')
    CONFIG_FILE.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load() -> dict[str, Any]:
    """Return the current config dict."""
    return _load_raw()


def get(key: str, default: Any = None) -> Any:
    """Get a single config value."""
    return _load_raw().get(key, default)


def set_value(key: str, value: str) -> None:
    """Set a config key. Raises ValueError for unknown keys or invalid values."""
    if key not in VALID_KEYS:
        raise ValueError(f"Unknown config key '{key}'. Valid keys: {', '.join(VALID_KEYS)}")
    allowed = VALID_KEYS[key]
    if allowed is not None and value not in allowed:
        raise ValueError(f"Invalid value '{value}' for '{key}'. Allowed: {', '.join(allowed)}")
    data = _load_raw()
    data[key] = value
    _write(data)


def unset_value(key: str) -> bool:
    """Remove a config key. Returns True if key existed."""
    data = _load_raw()
    if key not in data:
        return False
    del data[key]
    _write(data)
    return True


def reset() -> None:
    """Remove all config (delete the file)."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def apply_defaults(ctx_params: dict[str, Any]) -> dict[str, Any]:
    """Merge config defaults into Click command params (config fills gaps only).

    Click params that are already set (non-None) take precedence.
    Returns a new dict with config values filled in.
    """
    cfg = _load_raw()
    result = dict(ctx_params)
    for k, v in cfg.items():
        if k in result and result[k] is None:
            result[k] = v
    return result
