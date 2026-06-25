"""ai_assist_cad/layer_designer.py"""
from __future__ import annotations
import json
from typing import Dict, List, Optional


class LayerPattern:
    """LayerPattern — agnóstico: qualquer material + binder + processo."""

    def __init__(self, materials: List[Dict], binder: Optional[str] = None,
                 thickness_mm: float = 1.0, process: Optional[str] = None,
                 process_params: Optional[Dict] = None):
        self.materials = materials
        self.binder = binder
        self.thickness_mm = thickness_mm
        self.process = process
        self.process_params = process_params or {}

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "LayerPattern":
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> Dict:
        return {"materials": self.materials, "binder": self.binder,
                "thickness_mm": self.thickness_mm, "process": self.process,
                "process_params": self.process_params}

    @classmethod
    def from_dict(cls, d: Dict) -> "LayerPattern":
        return cls(**{k: v for k, v in d.items() if k in [
            "materials", "binder", "thickness_mm", "process", "process_params"]})


class CompositeStack:
    """CompositeStack — N pilhas de LayerPattern, propriedades homogeneizadas."""

    def __init__(self, layer_pattern: LayerPattern, repetitions: int = 1):
        self.layer_pattern = layer_pattern
        self.repetitions = repetitions
        self._compute_properties()

    def _compute_properties(self):
        mats = self.layer_pattern.materials
        E_voigt = sum(m["E_GPa"] * m["fraction"] for m in mats)
        nu_reuss = 1.0 / sum((1.0 / m.get("nu", 0.3) * m["fraction"]) for m in mats)
        self.effective_properties = {
            "E1_GPa": E_voigt,
            "E2_GPa": E_voigt * 0.9,
            "nu": nu_reuss if nu_reuss < 0.5 else 0.3,
            "G12_GPa": E_voigt / (2 * (1 + 0.3)) * 0.8,
            "total_thickness_mm": self.layer_pattern.thickness_mm * self.repetitions,
            "repetitions": self.repetitions,
            "density_kgm3": sum(m.get("density", 2700) * m["fraction"] for m in mats),
        }
