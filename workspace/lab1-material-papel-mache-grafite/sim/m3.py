"""sim/m3.py — análise Macro-Meso-Micro (KDI methodology_m3).

Cada escala recebe um dict de métricas; a função agrega e gera coverage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EscalaAnalise:
    nome: str
    elementos: dict[str, Any] = field(default_factory=dict)

    def coverage(self) -> float:
        if not self.elementos:
            return 0.0
        preenchidos = sum(1 for v in self.elementos.values() if v is not None)
        return preenchidos / len(self.elementos)


@dataclass
class AnaliseM3:
    macro: EscalaAnalise
    meso: EscalaAnalise
    micro: EscalaAnalise

    def cobertura_total(self) -> float:
        a, b, c = self.macro.coverage(), self.meso.coverage(), self.micro.coverage()
        return (a + b + c) / 3.0

    def domain_map(self) -> dict[str, Any]:
        return {
            "macro": {"coverage": self.macro.coverage(), "elementos": self.macro.elementos},
            "meso": {"coverage": self.meso.coverage(), "elementos": self.meso.elementos},
            "micro": {"coverage": self.micro.coverage(), "elementos": self.micro.elementos},
            "cobertura_total": self.cobertura_total(),
        }


def analise_material_m3(propriedades: dict[str, Any]) -> AnaliseM3:
    """M³ default para o compósito do Lab1 (preenchido com props do material)."""
    macro = EscalaAnalise("macro", {
        "aplicacao": propriedades.get("aplicacao", "gerador eolico savonius"),
        "ambiente": propriedades.get("ambiente", "Nordeste/CO Brasil"),
        "regulamentacao": propriedades.get("regulamentacao", "IEC 61400"),
    })
    meso = EscalaAnalise("meso", {
        "interface_pa_matriz": propriedades.get("interface_pa_matriz"),
        "acoplamento_mecanico": propriedades.get("acoplamento_mecanico"),
        "troca_termica": propriedades.get("troca_termica"),
    })
    micro = EscalaAnalise("micro", {
        "densidade": propriedades.get("densidade"),
        "modulo_young": propriedades.get("modulo_young"),
        "resistencia": propriedades.get("resistencia"),
        "microestrutura": propriedades.get("microestrutura"),
        "mecanismo_falha": propriedades.get("mecanismo_falha"),
    })
    return AnaliseM3(macro=macro, meso=meso, micro=micro)
