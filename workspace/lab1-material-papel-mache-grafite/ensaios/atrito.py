"""ensaios/atrito.py — coeficiente de atrito + desgaste por Archard.

Refs: Archard, J.F. (1953) J. Appl. Phys. 24:981-988.
"""
from __future__ import annotations

from dataclasses import dataclass


def forca_atrito(mu: float, N: float) -> float:
    """Lei de Coulomb: F = mu * N."""
    return mu * N


@dataclass
class ArchardInputs:
    K_desgaste: float     # constante adimensional de desgaste (~1e-3 a 1e-8)
    carga_N: float
    deslizamento_m: float
    dureza_pa: float      # dureza (Pa) — aproximação por sigma_y


def volume_desgaste(a: ArchardInputs) -> float:
    """V = K * F * s / H."""
    if a.dureza_pa <= 0:
        return 0.0
    return a.K_desgaste * a.carga_N * a.deslizamento_m / a.dureza_pa
