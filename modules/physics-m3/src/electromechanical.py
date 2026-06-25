#!/usr/bin/env python3
"""
Electromechanical Module — Generators, Motors & Power Conversion.

Per INSTRUCTIONS.md KDI: eletricidade + energia domains.
  - Permanent magnet synchronous generator (PMSG)
  - DC motor/generator model
  - Power conversion, losses, efficiency
  - Torque-speed characteristics
  - Energy storage (battery, flywheel)
  - Grid connection (inverter, transformer)

Usage:
    from electromechanical import (
        PMSG, DCMachine, TorqueSpeedCurve,
        power_efficiency, energy_storage
    )
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════
#  PERMANENT MAGNET SYNCHRONOUS GENERATOR (PMSG)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PMSG:
    """Permanent Magnet Synchronous Generator model."""
    power_rated_W: float = 3000.0
    voltage_V: float = 48.0
    poles: int = 8
    rpm_rated: float = 400.0
    R_s_ohm: float = 0.1      # Stator resistance
    L_d_H: float = 0.001       # d-axis inductance
    L_q_H: float = 0.001       # q-axis inductance
    psi_PM_Wb: float = 0.1     # PM flux linkage

    @property
    def electrical_freq_Hz(self) -> float:
        """Electrical frequency at rated speed."""
        return self.rpm_rated * self.poles / 120

    def emf_V(self, rpm: float) -> float:
        """Back EMF (line-to-line) at given speed."""
        omega_e = rpm * np.pi * self.poles / 60
        return round(omega_e * self.psi_PM_Wb * np.sqrt(3), 2)

    def torque_max_Nm(self) -> float:
        """Maximum electromagnetic torque."""
        return round(3 * self.poles / 2 * self.psi_PM_Wb * self.power_rated_W /
                     (self.voltage_V * np.sqrt(3)), 2)

    def efficiency(self, output_W: float) -> float:
        """Generator efficiency at given output power."""
        if output_W <= 0:
            return 0
        # Copper losses + iron losses
        I = output_W / (self.voltage_V * np.sqrt(3) * 0.85)
        P_cu = 3 * I**2 * self.R_s_ohm
        P_fe = 0.02 * self.power_rated_W
        P_loss = P_cu + P_fe
        eta = output_W / (output_W + P_loss)
        return round(eta * 100, 2)

    def summary(self) -> Dict:
        return {
            "type": "PMSG",
            "power_rated_W": self.power_rated_W,
            "voltage_V": self.voltage_V,
            "poles": self.poles,
            "rpm_rated": self.rpm_rated,
            "electrical_freq_Hz": round(self.electrical_freq_Hz, 1),
            "emf_at_rated_V": self.emf_V(self.rpm_rated),
            "max_torque_Nm": self.torque_max_Nm(),
            "efficiency_at_rated_pct": self.efficiency(self.power_rated_W),
        }


# ═══════════════════════════════════════════════════════════════
#  DC MACHINE (Motor/Generator)
# ═══════════════════════════════════════════════════════════════

@dataclass
class DCMachine:
    """DC motor/generator model."""
    voltage_V: float = 24.0
    current_A: float = 10.0
    R_a_ohm: float = 0.5        # Armature resistance
    K_T_Nm_A: float = 0.1       # Torque constant
    K_E_Vs_rad: float = 0.1     # Back-EMF constant

    def torque_Nm(self) -> float:
        """Electromagnetic torque."""
        return self.K_T_Nm_A * self.current_A

    def speed_rads(self) -> float:
        """No-load speed (rad/s)."""
        return (self.voltage_V - self.current_A * self.R_a_ohm) / self.K_E_Vs_rad

    def speed_rpm(self) -> float:
        """Speed in RPM."""
        return self.speed_rads() * 60 / (2 * np.pi)

    def power_W(self) -> Dict:
        """Electrical and mechanical power."""
        P_elec = self.voltage_V * self.current_A
        P_mech = self.torque_Nm() * self.speed_rads()
        eta = P_mech / P_elec * 100 if P_elec > 0 else 0
        return {
            "electrical_W": round(P_elec, 1),
            "mechanical_W": round(P_mech, 1),
            "efficiency_pct": round(eta, 1),
            "torque_Nm": round(self.torque_Nm(), 2),
            "speed_rpm": round(self.speed_rpm(), 1),
        }


# ═══════════════════════════════════════════════════════════════
#  POWER ELECTRONICS & CONVERSION
# ═══════════════════════════════════════════════════════════════

def rectifier_efficiency(AC_power_W: float, topology: str = "3phase") -> float:
    """Rectifier efficiency estimate."""
    eff = {"3phase": 0.97, "single": 0.95}
    return eff.get(topology, 0.95)


def inverter_efficiency(DC_power_W: float) -> float:
    """Inverter efficiency (typical 95-98%)."""
    return 0.96 + 0.02 * (1 - np.exp(-DC_power_W / 1000))


def transformer_efficiency(S_rated_VA: float, load_pct: float) -> float:
    """Transformer efficiency at given load."""
    P_fe = 0.01 * S_rated_VA  # Fixed iron losses
    P_cu = 0.02 * S_rated_VA * (load_pct / 100)**2  # Copper losses (I²R)
    P_out = S_rated_VA * (load_pct / 100)
    return P_out / (P_out + P_fe + P_cu)


def power_conversion_chain(DC_power_W: float) -> Dict:
    """Full power conversion chain efficiency."""
    eta_inv = inverter_efficiency(DC_power_W)
    eta_trans = transformer_efficiency(1000, DC_power_W / 1000 * 100)
    eta_total = eta_inv * eta_trans
    return {
        "inverter_efficiency_pct": round(eta_inv * 100, 2),
        "transformer_efficiency_pct": round(eta_trans * 100, 2),
        "total_efficiency_pct": round(eta_total * 100, 2),
        "loss_W": round(DC_power_W * (1 - eta_total), 1),
    }


# ═══════════════════════════════════════════════════════════════
#  ENERGY STORAGE (Battery model)
# ═══════════════════════════════════════════════════════════════

@dataclass
class BatteryStorage:
    """Simple battery model for wind energy storage."""
    capacity_Wh: float = 2000.0
    voltage_nominal_V: float = 48.0
    chemistry: str = "LiFePO4"
    soc_pct: float = 50.0

    @property
    def capacity_Ah(self) -> float:
        return self.capacity_Wh / self.voltage_nominal_V

    def energy_available_Wh(self, depth_of_discharge_pct: float = 80) -> float:
        """Usable energy considering DoD."""
        return self.capacity_Wh * depth_of_discharge_pct / 100

    def charge_time_h(self, power_W: float, efficiency: float = 0.95) -> float:
        """Time to fully charge from current SOC."""
        energy_needed = self.capacity_Wh * (1 - self.soc_pct / 100)
        return energy_needed / (power_W * efficiency)

    def summary(self) -> Dict:
        return {
            "type": self.chemistry,
            "capacity_Wh": self.capacity_Wh,
            "capacity_Ah": round(self.capacity_Ah, 1),
            "voltage_V": self.voltage_nominal_V,
            "soc_pct": self.soc_pct,
            "usable_energy_80DoD_Wh": round(self.energy_available_Wh(), 1),
        }
