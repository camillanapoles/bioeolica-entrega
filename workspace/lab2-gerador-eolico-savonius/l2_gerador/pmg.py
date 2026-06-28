"""gerador/pmg.py — gerador síncrono de ímãs permanentes (PMG) simplificado.

Relações (máquina CC/PMSG idealizada):
- EMF: E = Ke * omega
- Torque: T = Ke * I   ->   I = T / Ke
- Pin = T * omega = E * I
- Pout = E*I - I^2*R - perdas_constantes
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import get


@dataclass
class PMGParams:
    """Constantes de um PMG (PMSG) de pequeno porte.

    Defaults: Ke=2.0 V·s/rad (típico PMG ~100-500W), R=1.5 ohm, perdas 3W.
    Refs: Boldea, I. Variable Speed Generators (CRC 2015); IEC 61400-2.
    """
    Ke: float = field(default_factory=lambda: get("lab2.pmg.Ke"))              # V·s/rad = N·m/A
    R_interno_ohm: float = field(default_factory=lambda: get("lab2.pmg.R_interno_ohm"))
    perdas_constantes_w: float = field(default_factory=lambda: get("lab2.pmg.perdas_constantes_w"))


def fem(omega_rad_s: float, p: PMGParams) -> float:
    return p.Ke * omega_rad_s


def corrente(torque_nm: float, p: PMGParams) -> float:
    if p.Ke <= 0:
        return 0.0
    return torque_nm / p.Ke


def potencia_saida(torque_nm: float, omega_rad_s: float, p: PMGParams) -> float:
    """Pout = E*I - I^2*R - perdas_constantes."""
    if p.Ke <= 0:
        return 0.0
    I = corrente(torque_nm, p)
    pin = torque_nm * omega_rad_s          # = E*I
    perdas_joule = I ** 2 * p.R_interno_ohm
    return max(0.0, pin - perdas_joule - p.perdas_constantes_w)


def eficiencia(torque_nm: float, omega_rad_s: float, p: PMGParams) -> float:
    pin = torque_nm * omega_rad_s
    if pin <= 0:
        return 0.0
    return potencia_saida(torque_nm, omega_rad_s, p) / pin
