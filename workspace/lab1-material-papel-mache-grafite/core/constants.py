"""core/constants.py — acessor do schema unificado de constantes (P$1: ZERO hardcoded).

Único ponto de leitura para todas as constantes físico-científicas e de modelo.
Os módulos importam deste; os valores vivem em config/constants.json.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config

DEFAULT_CONSTANTS = Path(__file__).resolve().parent.parent / "config" / "constants.json"

_CACHE: dict[str, Any] | None = None


def load_constants(path: Path | str | None = None) -> dict[str, Any]:
    """Carrega (e cacheia) o schema unificado de constantes."""
    global _CACHE
    if path is not None:
        return load_config(path)
    if _CACHE is None:
        _CACHE = load_config(DEFAULT_CONSTANTS)
    return _CACHE


def get(path_dotted: str, default: Any = None) -> Any:
    """Acesso por camho pontuado: get('fisica.R_GAS')."""
    node: Any = load_constants()
    for part in path_dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node
