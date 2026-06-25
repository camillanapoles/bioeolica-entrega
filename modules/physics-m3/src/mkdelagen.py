#!/usr/bin/env python3
"""
MKDELAGEN — Model Generation Pipeline (Design → Mesh → Simulation).

Pipeline de geração de modelos paramétricos para análise estrutural:
  - Geometry primitives (blade, beam, plate, shell)
  - Automatic mesh generation
  - Material assignment
  - Load case specification
  - Export to simulation-ready format

Uso:
    from mkdelagen import ParametricBlade, MeshGenerator, LoadCase
    blade = ParametricBlade(length=1.5)
    blade.set_material(E=3.5e9, nu=0.3, rho=1200)
    mesh = MeshGenerator(blade, element_size=0.05)
    print(mesh.summary())
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MaterialSpec:
    """Material specification for model generation."""
    name: str = "composite"
    E_GPa: float = 10.0
    nu: float = 0.3
    rho_kgm3: float = 1200.0
    yield_MPa: float = 50.0
    color: str = "#D2B48C"


@dataclass
class ParametricBlade:
    """Parametric wind turbine blade geometry."""
    length_m: float = 1.5
    root_chord_m: float = 0.3
    tip_chord_m: float = 0.1
    n_sections: int = 20
    twist_deg: float = 10.0
    material: MaterialSpec = field(default_factory=MaterialSpec)

    def set_material(self, E_GPa: float, nu: float, rho: float):
        self.material.E_GPa = E_GPa
        self.material.nu = nu
        self.material.rho_kgm3 = rho

    def chord_at(self, r: float) -> float:
        r_norm = r / self.length_m
        return self.root_chord_m - (self.root_chord_m - self.tip_chord_m) * r_norm

    def section_points(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        xs, ys, zs = [], [], []
        for i in range(self.n_sections):
            r = i * self.length_m / (self.n_sections - 1)
            c = self.chord_at(r)
            for j in range(12):
                theta = 2 * np.pi * j / 12
                xs.append(c * 0.5 * (1 + np.cos(theta)) * 0.1)
                ys.append(r)
                zs.append(c * np.sin(theta) * 0.05)
        return np.array(xs), np.array(ys), np.array(zs)

    def summary(self) -> Dict:
        return {
            "length_m": self.length_m,
            "root_chord_m": self.root_chord_m,
            "n_sections": self.n_sections,
            "material": self.material.name,
            "E_GPa": self.material.E_GPa,
            "mass_est_kg": round(self.length_m * 0.3 * 0.1 * self.material.rho_kgm3, 2),
        }


@dataclass
class MeshGenerator:
    """Generate simulation mesh from parametric model."""
    model: Optional[ParametricBlade] = None
    element_size: float = 0.05
    n_elements: int = 0
    n_nodes: int = 0

    def generate(self) -> Dict:
        if self.model is None:
            return {"n_elements": 0, "n_nodes": 0}
        self.n_elements = int(self.model.length_m / self.element_size) * self.model.n_sections
        self.n_nodes = self.n_elements * 4
        return self.summary()

    def summary(self) -> Dict:
        return {
            "n_elements": self.n_elements,
            "n_nodes": self.n_nodes,
            "element_size_m": self.element_size,
            "element_type": "quad4",
        }


@dataclass
class LoadCase:
    """Load case specification for structural analysis."""
    name: str = "Operating"
    tip_force_N: float = 100.0
    wind_speed_ms: float = 10.0
    pressure_Pa: float = 0.0
    temperature_C: float = 25.0
    safety_factor: float = 1.5

    def design_force(self) -> float:
        return self.tip_force_N * self.safety_factor
