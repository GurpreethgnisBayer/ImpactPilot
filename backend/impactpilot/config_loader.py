"""Load and validate external YAML configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ConfigBundle(BaseModel):
    value_chain: dict[str, Any] = Field(default_factory=dict)
    dimensions: dict[str, Any] = Field(default_factory=dict)
    focus_areas: dict[str, Any] = Field(default_factory=dict)
    reference_values: dict[str, Any] = Field(default_factory=dict)
    cost_categories: dict[str, Any] = Field(default_factory=dict)
    scoring: dict[str, Any] = Field(default_factory=dict)
    llm_endpoints: dict[str, Any] = Field(default_factory=dict)


REQUIRED_FILES = (
    "value_chain.yaml",
    "dimensions.yaml",
    "focus_areas.yaml",
    "reference_values.yaml",
    "cost_categories.yaml",
    "scoring.yaml",
    "llm_endpoints.yaml",
)


def _default_config_dir() -> Path:
    env = os.environ.get("IMPACTPILOT_CONFIG_DIR")
    if env:
        return Path(env).resolve()
    # backend/impactpilot/config_loader.py -> repo root config/
    return Path(__file__).resolve().parents[2] / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file missing: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config {path.name} must be a mapping")
    return data


def load_config(config_dir: Path | None = None) -> ConfigBundle:
    root = config_dir or _default_config_dir()
    payload: dict[str, Any] = {}
    for name in REQUIRED_FILES:
        key = name.replace(".yaml", "")
        payload[key] = _load_yaml(root / name)
    return ConfigBundle.model_validate(payload)


@lru_cache(maxsize=1)
def get_config() -> ConfigBundle:
    return load_config()


def reload_config() -> ConfigBundle:
    get_config.cache_clear()
    return get_config()
