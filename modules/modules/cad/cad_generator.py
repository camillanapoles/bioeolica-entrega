"""
CadQuery geometry builder from ParametricModel.

Refactored from ai_assist_cad/cad_generator.py — replaces placeholder STEP
with real CadQuery geometry generation.
"""

from __future__ import annotations

from typing import Any

import cadquery as cq

from .parametric import ParametricModel

# Machine templates with default dimensions (mm)
MACHINE_TEMPLATES = {
    "generator": {
        "stator": {"shape": "cylinder", "diameter_mm": 400, "height_mm": 200},
        "rotor": {"shape": "cylinder", "diameter_mm": 310, "height_mm": 180},
        "shaft": {"shape": "cylinder", "diameter_mm": 80, "height_mm": 500},
    },
    "motor": {
        "stator": {"shape": "cylinder", "diameter_mm": 350, "height_mm": 180},
        "rotor": {"shape": "cylinder", "diameter_mm": 280, "height_mm": 160},
        "shaft": {"shape": "cylinder", "diameter_mm": 70, "height_mm": 400},
    },
    "generic": {
        "body": {"shape": "box", "width": 100, "height": 50, "depth": 20},
    },
}


def build_shape(shape_def: dict) -> cq.Workplane:
    """Build a CadQuery Workplane from a shape definition dict."""
    shape_type = shape_def.get("shape", "box")
    wp = cq.Workplane("XY")
    if shape_type == "box":
        return wp.box(
            shape_def.get("width", 100),
            shape_def.get("height", 50),
            shape_def.get("depth", 20),
        )
    elif shape_type == "cylinder":
        return wp.cylinder(
            shape_def.get("height_mm", 100),
            shape_def.get("diameter_mm", 50) / 2,
        )
    else:
        return wp.box(100, 50, 20)


class CADGenerator:
    """Generates CadQuery geometry from parametric models."""

    def __init__(self):
        self.components: list[dict[str, Any]] = []

    def generate(self, model: ParametricModel) -> cq.Workplane:
        """Generate full CAD assembly from ParametricModel."""
        template = MACHINE_TEMPLATES.get(model.machine_type, MACHINE_TEMPLATES["generic"])

        # If generic, use the model's dimensions directly
        if model.machine_type == "generic":
            return cq.Workplane("XY").box(model.width, model.height, model.depth)

        # Build components from template
        result = None
        for comp_name, comp_def in template.items():
            wp = build_shape(comp_def)
            if result is None:
                result = wp
            else:
                result = result.union(wp)

        return result or cq.Workplane("XY").box(model.width, model.height, model.depth)
