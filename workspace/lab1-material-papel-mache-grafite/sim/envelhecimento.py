"""sim/envelhecimento.py — vida útil por Monte Carlo (degradação cumulativa).

Modelo: decaimento FRACTIONAL linear por ciclo.
    dE/dN = -taxa * E0   ->   E(N) = E0 * (1 - taxa*N)
    Vida N_f quando E = limiar*E0:  N_f = (1 - limiar)/taxa

taxa é FRACTIONAL (1/ciclo, adimensional), não Pa/ciclo.
Refs: Ashby, Materials Selection in Mechanical Design, cap. 6 (degradação).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.constants import get


@dataclass
class EnvelhecimentoConfig:
    E0: float                       # módulo inicial (Pa) — referência
    limiar_frac: float              # fração de E0 considerado fim de vida (ex: 0.7)
    n_amostras: int = 1000
    # taxa fractional base: polímero perde ~30% em ~3e8 ciclos -> taxa ~ 1e-9/ciclo
    taxa_base_degrad: float = field(default_factory=lambda: get("sim.envelhecimento.taxa_base_degrad"))
    sigma_ruido: float = field(default_factory=lambda: get("sim.envelhecimento.sigma_ruido"))
    ciclos_max: int = field(default_factory=lambda: int(get("sim.envelhecimento.ciclos_max")))
    seed: int = 42


def simular_vida_util(cfg: EnvelhecimentoConfig, rng=None) -> dict:
    """Simula n trajetórias e retorna estatísticas de vida útil (ciclos)."""
    import numpy as np
    rng = rng or np.random.default_rng(cfg.seed)
    # taxa fractional por amostra (lognormal multiplicative noise)
    taxas = cfg.taxa_base_degrad * rng.lognormal(mean=0.0, sigma=cfg.sigma_ruido,
                                                 size=cfg.n_amostras)
    # N_f = (1 - limiar)/taxa  (capado em ciclos_max)
    delta_frac = max(0.0, 1.0 - cfg.limiar_frac)
    vidas = np.where(taxas > 0,
                     np.minimum(delta_frac / taxas, cfg.ciclos_max),
                     cfg.ciclos_max)
    return {
        "media_ciclos": float(vidas.mean()),
        "mediana_ciclos": float(np.median(vidas)),
        "p05_ciclos": float(np.percentile(vidas, 5)),
        "p95_ciclos": float(np.percentile(vidas, 95)),
        "frac_falha_antes_max": float((vidas < cfg.ciclos_max).mean()),
        "n_amostras": cfg.n_amostras,
    }
