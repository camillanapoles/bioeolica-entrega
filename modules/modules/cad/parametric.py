"""
Parametric model from JSON spec.

Refactored from ai_assist_cad/nlp_parser.py with Pydantic-like validation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

import cadquery as cq


@dataclass
class ParametricModel:
    """Engineering parameters for CAD generation.

    All dimensions in mm. Validates positivity on construction.
    """

    model_id: str
    name: str
    machine_type: str = "generic"
    width: float = 100.0
    height: float = 50.0
    depth: float = 20.0
    material: str = "steel"
    power_kw: float = 0.0
    layers: list[dict] = field(default_factory=list)
    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        for dim_name in ("width", "height", "depth"):
            val = getattr(self, dim_name)
            if val <= 0:
                raise ValueError(f"{dim_name} must be positive, got {val}")

    def to_cq_box(self) -> cq.Workplane:
        """Generate CadQuery box Workplane from parameters."""
        return cq.Workplane("XY").box(self.width, self.height, self.depth)

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "machine_type": self.machine_type,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "material": self.material,
            "power_kw": self.power_kw,
            "layers": self.layers,
        }


def parse_parameters(source: str | dict) -> ParametricModel:
    """Load ParametricModel from JSON file path, string, or dict."""
    if isinstance(source, str):
        if source.endswith(".json"):
            with open(source) as f:
                data = json.load(f)
        else:
            data = json.loads(source)
    else:
        data = source
    return ParametricModel(**data)


