"""gerador/integrador.py — acoplamento aerodinâmico ↔ gerador (matching).

Equilibra torque da turbina com torque resistivo do PMG para um dado vento.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import get
from l2_aerodinamica.savonius import (
    SavoniusCurve,
    coeficiente_potencia,
    potencia_disponivel,
    potencia_turbina,
)

from l2_gerador.pmg import PMGParams, eficiencia, potencia_saida


@dataclass
class SistemaEolico:
    rho_ar: float = field(default_factory=lambda: get("fisica.rho_ar"))  # kg/m3 — schema unificado (P$1)
    diametro_m: float = 1.0
    altura_m: float = 1.5
    tsr: float = 0.8
    curve: SavoniusCurve = None      # type: ignore
    pmg: PMGParams = None            # type: ignore

    def __post_init__(self):
        if self.curve is None:
            self.curve = SavoniusCurve()
        if self.pmg is None:
            self.pmg = PMGParams()  # usa defaults realistas da dataclass (Ke=2.0, R=1.5)


def varrer_vento(s: SistemaEolico, v_list: list[float]) -> list[dict]:
    """Produz curva de potência em função da velocidade do vento."""
    from l2_aerodinamica.savonius import area_varrida_savonius
    A = area_varrida_savonius(s.diametro_m, s.altura_m)
    out = []
    for v in v_list:
        p_disp = potencia_disponivel(s.rho_ar, A, v)
        p_turb = potencia_turbina(s.rho_ar, A, v, s.tsr, s.curve)
        # ω = λ*v/R; r ~ D/2
        r = s.diametro_m / 2.0
        omega = s.tsr * v / r if r > 0 else 0.0
        # torque da turbina
        T_turb = p_turb / omega if omega > 0 else 0.0
        p_out = potencia_saida(T_turb, omega, s.pmg)
        ef = eficiencia(T_turb, omega, s.pmg) if p_turb > 0 else 0.0
        cp = coeficiente_potencia(s.tsr, s.curve)
        out.append({
            "v_mps": v,
            "p_disponivel_w": p_disp,
            "p_turbina_w": p_turb,
            "p_gerador_w": p_out,
            "omega_rad_s": omega,
            "torque_nm": T_turb,
            "eficiencia": ef,
            "cp": cp,
        })
    return out
