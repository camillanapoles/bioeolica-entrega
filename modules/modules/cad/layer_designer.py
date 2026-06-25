"""
N×M multimaterial layer composer.

Refactored from ai_assist_cad/layer_designer.py with CadQuery geometry output.
"""

from __future__ import annotations

import json
from typing import Any

import cadquery as cq

from .parametric import ParametricModel


class LayerPattern:
    """A single layer pattern with material(s) and process."""

    def __init__(self, materials: list[dict], binder: str | None = None,
                 thickness_mm: float = 1.0, process: str | None = None):
        self.materials = materials
        self.binder = binder
        self.thickness_mm = thickness_mm
        self.process = process

    @property
    def total_height(self) -> float:
        return self.thickness_mm


class CompositeStack:
    """Composite of N×M layers with homogenized properties."""

    def __init__(self, layers: list[LayerPattern], base_model: ParametricModel):
        self.layers = layers
        self.base = base_model
        self._validate()

    def _validate(self):
        """Validate layer thicknesses sum to base depth."""
        total = sum(l.total_height for l in self.layers)
        if abs(total - self.base.depth) > 0.01:
            raise ValueError(
                f"Layer thickness sum ({total:.1f}mm) != base depth ({self.base.depth}mm)"
            )

    def build(self) -> cq.Workplane:
        """Build layered composite CadQuery model."""
        result = None
        z_offset = -self.base.depth / 2
        for i, layer in enumerate(self.layers):
            wp = cq.Workplane("XY").box(
                self.base.width, self.base.height, layer.thickness_mm
            ).translate((0, 0, z_offset + layer.thickness_mm / 2))
            if result is None:
                result = wp
            else:
                result = result.union(wp)
            z_offset += layer.thickness_mm
        return result or cq.Workplane("XY")


def load_layer_config(path: str) -> list[LayerPattern]:
    """Load layer configuration from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [LayerPattern(**layer) for layer in data.get("layers", [])]
