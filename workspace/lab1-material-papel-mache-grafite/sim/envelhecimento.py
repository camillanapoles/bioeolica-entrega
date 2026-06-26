"""sim/envelhecimento.py — vida útil por Monte Carlo (degradação cumulativa).

Modelo: degradação linear acumulada por ciclos de carga + térmico.
Cada trajetória amostra fatores aleatórios; P(volt) = fração que cruza limiar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class EnvelhecimentoConfig:
    E0: float                # módulo inicial (Pa)
    limiar_frac: float       # fração de E0 considerado fim de vida (ex: 0.7)
    n_amostras: int = 1000
    taxa_base_degrad: float = 1e-7   # por ciclo
    sigma_ruido: float = 0.2         # variabilidade relativa
    ciclos_max: int = 10_000_000
    seed: int = 42


def simular_vida_util(cfg: EnvelhecimentoConfig, rng=None) -> dict:
    """Simula n trajetórias e retorna estatísticas de vida útil (ciclos)."""
    import numpy as np
    rng = rng or np.random.default_rng(cfg.seed)
    vidas = []
    E_limiar = cfg.E0 * cfg.limiar_frac
    # taxa por amostra (lognormal multiplicative noise)
    taxas = cfg.taxa_base_degrad * rng.lognormal(mean=0.0, sigma=cfg.sigma_ruido,
                                                 size=cfg.n_amostras)
    for t in taxas:
        # E(N) = E0 - t*N ; vida em N = (E0 - E_limiar)/t
        vida = (cfg.E0 - E_limiar) / t if t > 0 else cfg.ciclos_max
        vidas.append(min(vida, cfg.ciclos_max))
    arr = np.array(vidas)
    return {
        "media_ciclos": float(arr.mean()),
        "mediana_ciclos": float(np.median(arr)),
        "p05_ciclos": float(np.percentile(arr, 5)),
        "p95_ciclos": float(np.percentile(arr, 95)),
        "frac_falha_antes_max": float((arr < cfg.ciclos_max).mean()),
        "n_amostras": cfg.n_amostras,
    }
