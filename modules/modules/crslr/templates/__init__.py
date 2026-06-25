"""Jinja2 templates for CRSLR report generation."""

from __future__ import annotations

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def get_template(name: str) -> str:
    """Read template file content."""
    path = TEMPLATES_DIR / name
    return path.read_text()
