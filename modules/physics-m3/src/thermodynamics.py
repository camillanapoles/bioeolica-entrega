#!/usr/bin/env python3
"""
Thermodynamics & Energy Systems Module.

Per INSTRUCTIONS.md KDI: termo + energia domains.
  - Thermodynamic cycles (Rankine, Brayton, Otto)
  - Heat transfer (conduction, convection, radiation)
  - Energy efficiency, exergy analysis
  - Phase change (drying, curing of composites)
  - Heat exchanger modeling

Usage:
    from thermodynamics import (
        HeatTransfer, Conduction, Convection,
        efficiency_rankine, heat_exchanger_effectiveness
    )
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict


# ═══════════════════════════════════════════════════════════════
#  HEAT TRANSFER
# ═══════════════════════════════════════════════════════════════

def conduction_1D(k_WmK: float, A_m2: float, dT_K: float, dx_m: float) -> float:
    """1D steady-state conduction heat flux (W)."""
    return k_WmK * A_m2 * dT_K / dx_m


def convection(h_Wm2K: float, A_m2: float, dT_K: float) -> float:
    """Convection heat transfer (W)."""
    return h_Wm2K * A_m2 * dT_K


def radiation(epsilon: float, A_m2: float, T1_K: float, T2_K: float) -> float:
    """Radiation heat transfer (W), Stefan-Boltzmann."""
    sigma = 5.67e-8
    return epsilon * sigma * A_m2 * (T1_K**4 - T2_K**4)


def overall_heat_transfer(U_Wm2K: float, A_m2: float, dT_lm: float) -> float:
    """Overall heat transfer rate (W) using LMTD."""
    return U_Wm2K * A_m2 * dT_lm


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE DRYING & CURING (process thermodynamics)
# ═══════════════════════════════════════════════════════════════

@dataclass
class DryingProcess:
    """Composite material drying/curing thermodynamics."""
    mass_kg: float = 1.0
    water_content_pct: float = 60
    initial_temp_C: float = 25
    drying_temp_C: float = 60
    Cp_material_JkgK: float = 1500
    Cp_water_JkgK: float = 4186
    h_latent_Jkg: float = 2.26e6

    def energy_to_heat_J(self) -> float:
        """Energy to raise material to drying temperature (J)."""
        dT = self.drying_temp_C - self.initial_temp_C
        m_mat = self.mass_kg * (1 - self.water_content_pct / 100)
        m_water = self.mass_kg * (self.water_content_pct / 100)
        E_mat = m_mat * self.Cp_material_JkgK * dT
        E_water = m_water * self.Cp_water_JkgK * dT
        return E_mat + E_water

    def energy_to_evaporate_J(self) -> float:
        """Energy to evaporate water content (J)."""
        m_water = self.mass_kg * (self.water_content_pct / 100)
        return m_water * self.h_latent_Jkg

    def total_energy_MJ(self) -> float:
        """Total thermal energy required (MJ)."""
        return (self.energy_to_heat_J() + self.energy_to_evaporate_J()) / 1e6


# ═══════════════════════════════════════════════════════════════
#  THERMODYNAMIC CYCLES
# ═══════════════════════════════════════════════════════════════

def carnot_efficiency(T_hot_K: float, T_cold_K: float) -> float:
    """Carnot ideal cycle efficiency (reversible)."""
    if T_hot_K <= 0:
        return 0
    return 1 - T_cold_K / T_hot_K


def rankine_cycle_efficiency(p_high_MPa: float, p_low_MPa: float,
                             T_superheat_K: float = 0) -> Dict:
    """Simple Rankine cycle efficiency estimate."""
    T_sat_high = 150 + 20 * np.log(p_high_MPa)  # approximation
    T_sat_low = 45 + 10 * np.log(p_low_MPa)
    T_high_K = (T_sat_high + T_superheat_K) + 273
    T_low_K = T_sat_low + 273

    eta_carnot = carnot_efficiency(T_high_K, T_low_K)
    eta_rankine = eta_carnot * 0.6  # typical Rankine vs Carnot ratio

    return {
        "carnot_efficiency_pct": round(eta_carnot * 100, 1),
        "rankine_efficiency_pct": round(eta_rankine * 100, 1),
        "T_high_K": round(T_high_K, 1),
        "T_low_K": round(T_low_K, 1),
    }


def heat_pump_COP(T_hot_K: float, T_cold_K: float) -> Dict:
    """Heat pump coefficient of performance."""
    if T_hot_K <= T_cold_K:
        return {"COP_heating": float('inf'), "COP_cooling": float('inf')}
    cop_h = T_hot_K / (T_hot_K - T_cold_K)
    cop_c = T_cold_K / (T_hot_K - T_cold_K)
    return {
        "COP_heating": round(cop_h, 2),
        "COP_cooling": round(cop_c, 2),
    }


# ═══════════════════════════════════════════════════════════════
#  EXERGY ANALYSIS
# ═══════════════════════════════════════════════════════════════

def exergy(Q_J: float, T_source_K: float, T_dead_K: float = 298) -> Dict:
    """Exergy (available energy) of a heat source."""
    eta_c = carnot_efficiency(T_source_K, T_dead_K)
    ex = Q_J * eta_c
    anergy = Q_J - ex
    return {
        "exergy_J": round(ex, 1),
        "anergy_J": round(anergy, 1),
        "exergy_fraction_pct": round(eta_c * 100, 1),
    }
