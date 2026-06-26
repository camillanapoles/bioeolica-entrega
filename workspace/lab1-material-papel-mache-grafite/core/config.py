"""core/config.py — carregador de config declarativa (P$1: nada hardcoded)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path | str) -> dict[str, Any]:
    """Carrega config YAML ou JSON. Único ponto de entrada para parâmetros."""
    p = Path(path)
    text = p.read_text()
    if p.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    if p.suffix.lower() == ".json":
        return json.loads(text)
    # tenta YAML como fallback
    return yaml.safe_load(text) or {}


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge raso de dicionários (override vence)."""
    out = dict(base)
    out.update(override)
    return out
