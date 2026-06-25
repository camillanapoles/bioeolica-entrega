"""
ai_assist_cad/knowledge_engine.py — Knowledge Engine v2

Dimensioning formulas for 10 engineering domains (M³-compliant).
Single Source of Truth: material data lives in data/*.json.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Optional


class KnowledgeEngine:
    """Multi-domain knowledge engine with dimensioning for 10 engineering domains."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.materials: dict[str, Any] = {}
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "materials.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.materials = json.load(f)

    def get_material(self, name: str) -> Optional[dict]:
        return self.materials.get(name)

    def list_materials(self) -> list[str]:
        return list(self.materials.keys())

    # ── Domain 1: Mecânica (torção, flexão, fadiga) ──

    def dimension_shaft(self, torque_Nm: float, tau_adm_MPa: float = 80) -> dict:
        """d = (16*T/pi/tau)^(1/3) — torção em eixo maciço (ASME B106.1M)."""
        d_mm = ((16 * torque_Nm * 1000) / (math.pi * tau_adm_MPa)) ** (1 / 3) * 1.5
        return {"diameter_mm": round(d_mm, 1), "torque_Nm": torque_Nm}

    def dimension_beam_bending(self, moment_Nm: float, sigma_adm_MPa: float = 150) -> dict:
        """W = M/sigma_adm — módulo de resistência à flexão."""
        W_mm3 = moment_Nm * 1000 / sigma_adm_MPa
        h_mm = (6 * W_mm3) ** (1 / 3)  # seção quadrada
        return {"section_modulus_mm3": round(W_mm3, 1), "height_mm": round(h_mm, 1)}

    # ── Domain 2: Fluidos (escoamento, bomba, perda de carga) ──

    def dimension_pump_power(self, rho_kgm3: float, Q_m3s: float,
                              head_m: float, eta: float = 0.7) -> dict:
        """P = rho*g*Q*H/eta — potência hidráulica (W)."""
        P_W = rho_kgm3 * 9.81 * Q_m3s * head_m / eta
        return {"power_W": round(P_W, 1), "power_kW": round(P_W / 1000, 2)}

    def dimension_pipe_diameter(self, Q_m3s: float, v_max_ms: float = 3.0) -> dict:
        """D = sqrt(4*Q/pi/v) — diâmetro de tubulação por velocidade máxima."""
        D_m = math.sqrt(4 * Q_m3s / (math.pi * v_max_ms))
        return {"diameter_mm": round(D_m * 1000, 1), "velocity_ms": v_max_ms}

    # ── Domain 3: Termo (condução, convecção, expansão) ──

    def dimension_heat_exchanger(self, Q_W: float, U_Wm2K: float = 500,
                                  delta_T_log_K: float = 30) -> dict:
        """A = Q/(U*delta_T_log) — área de troca térmica (m²)."""
        A_m2 = Q_W / (U_Wm2K * delta_T_log_K)
        return {"area_m2": round(A_m2, 2), "heat_load_W": Q_W}

    def thermal_expansion(self, L0_m: float, delta_T_K: float,
                           alpha_1K: float = 1.2e-5) -> dict:
        """delta_L = L0*alpha*delta_T — dilatação térmica linear."""
        delta_L_mm = L0_m * alpha_1K * delta_T_K * 1000
        return {"expansion_mm": round(delta_L_mm, 3), "final_length_m": round(L0_m + delta_L_mm / 1000, 4)}

    # ── Domain 4: Energia (potência, eficiência, bateria) ──

    def dimension_battery_capacity(self, P_W: float, t_h: float,
                                    V_V: float = 48, DoD: float = 0.8) -> dict:
        """C = P*t/(V*DoD) — capacidade de bateria (Ah)."""
        C_Ah = P_W * t_h / (V_V * DoD)
        return {"capacity_Ah": round(C_Ah, 1), "energy_Wh": round(P_W * t_h, 0)}

    # ── Domain 5: Eletricidade (motor, gerador, transformador) ──

    def dimension_stator_outer(self, power_kW: float, rpm: float = 1500,
                                poles: int = 4) -> dict:
        """D_est ≈ 250 * P^0.4 * (1500/n)^0.25 — escalonamento empírico."""
        D_mm = 250 * (power_kW / 100) ** 0.4 * (1500 / rpm) ** 0.25
        return {"diameter_mm": round(D_mm, 1), "poles": poles,
                "frequency_Hz": round(poles * rpm / 120, 1)}

    def dimension_transformer(self, S_kVA: float, B_T: float = 1.5,
                               J_Amm2: float = 3.0, f_Hz: float = 60) -> dict:
        """A_nucleo = S/(4.44*f*B*J) — área de núcleo de transformador."""
        A_core_cm2 = S_kVA * 1000 / (4.44 * f_Hz * B_T * J_Amm2 * 1e4) * 1e4
        return {"core_area_cm2": round(A_core_cm2, 1), "power_kVA": S_kVA}

    # ── Domain 6: Materiais (massa, tensão, custo) ──

    def estimate_mass(self, volume_m3: float, material_key: str) -> Optional[float]:
        mat = self.get_material(material_key)
        if mat:
            return round(volume_m3 * mat["density"], 1)
        return None

    def material_cost(self, mass_kg: float, material_key: str,
                       cost_per_kg: float = 5.0) -> dict:
        return {"cost_USD": round(mass_kg * cost_per_kg, 2), "mass_kg": round(mass_kg, 1)}

    # ── Domain 7: Construção (soldagem, parafuso, tolerância) ──

    def dimension_bolt(self, force_N: float, sigma_adm_MPa: float = 200) -> dict:
        """A = F/sigma_adm — área de parafuso sob tração."""
        A_mm2 = force_N / sigma_adm_MPa
        d_mm = math.sqrt(4 * A_mm2 / math.pi)
        return {"diameter_mm": round(d_mm, 1), "tensile_area_mm2": round(A_mm2, 1)}

    def weld_throat(self, force_N: float, weld_length_mm: float,
                     tau_adm_MPa: float = 100) -> dict:
        """a = F/(l*tau_adm) — garganta de solda (mm)."""
        a_mm = force_N / (weld_length_mm * tau_adm_MPa)
        return {"throat_mm": round(a_mm, 2), "leg_mm": round(a_mm * 1.414, 2)}

    # ── Domain 8: Ambiente (vento, onda, temperatura) ──

    def wind_load(self, rho_kgm3: float, v_ms: float, A_m2: float,
                   Cd: float = 1.2) -> dict:
        """F = 0.5*rho*v²*Cd*A — força de arrasto do vento."""
        F_N = 0.5 * rho_kgm3 * v_ms ** 2 * Cd * A_m2
        return {"force_N": round(F_N, 1), "pressure_Pa": round(F_N / A_m2, 1)}

    def thermal_flux_solar(self, area_m2: float, irradiance_Wm2: float = 1000,
                            efficiency: float = 0.2) -> dict:
        """P = G*A*eta — potência solar coletada."""
        P_W = irradiance_Wm2 * area_m2 * efficiency
        return {"power_W": round(P_W, 1), "irradiance_Wm2": irradiance_Wm2}

    # ── Domain 9: Normativo (coeficientes de segurança) ──

    def safety_factor_yield(self, sigma_yield_MPa: float,
                             sigma_applied_MPa: float) -> dict:
        """FS = sigma_yield / sigma_applied."""
        FS = sigma_yield_MPa / sigma_applied_MPa if sigma_applied_MPa > 0 else float("inf")
        return {"safety_factor": round(FS, 2), "status": "PASS" if FS >= 1.5 else "FAIL"}

    # ── Domain 10: Econômico (LCC, ROI) ──

    def lifecycle_cost(self, initial_cost: float, annual_opex: float,
                        years: int = 10, discount_rate: float = 0.1) -> dict:
        """LCC = C0 + Σ(C_anual/(1+r)^t) — custo do ciclo de vida."""
        total = initial_cost
        for t in range(1, years + 1):
            total += annual_opex / (1 + discount_rate) ** t
        return {"LCC_USD": round(total, 0), "years": years}

    # ── Multi-domain query ──

    def dimension_all(self, context: dict) -> dict:
        """Run dimensioning across all applicable domains based on context."""
        results = {}
        if "torque_Nm" in context:
            results["shaft"] = self.dimension_shaft(context["torque_Nm"])
        if "power_kW" in context:
            results["stator"] = self.dimension_stator_outer(context["power_kW"])
        if "Q_m3s" in context:
            results["pipe"] = self.dimension_pipe_diameter(context["Q_m3s"])
        if "force_N" in context:
            results["bolt"] = self.dimension_bolt(context["force_N"])
        if "volume_m3" in context and "material" in context:
            m = self.estimate_mass(context["volume_m3"], context["material"])
            results["mass_kg"] = m
        return results
