"""
export.py — STEP file export with SHA-256 metadata.

Generates CadQuery geometry from ParametricModel and exports to STEP.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .parametric import ParametricModel
from .cad_generator import CADGenerator


def export_step(model: ParametricModel, output_path: str) -> str:
    """
    Generate CadQuery geometry and export as STEP file.

    Returns absolute path to generated STEP file.
    """
    gen = CADGenerator()
    wp = gen.generate(model)
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    cq_query = wp  # CadQuery Workplane
    # Export as STEP
    from cadquery import exporters
    exporters.export(cq_query, str(path), exporters.ExportTypes.STEP)
    return str(path)


def step_checksum(path: str) -> str:
    """Return SHA-256 checksum of STEP file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
