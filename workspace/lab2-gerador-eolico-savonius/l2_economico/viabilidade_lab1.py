"""economico/viabilidade_lab1.py — ponte para Lab1/economico/viabilidade.py (DRY)."""
import importlib.util
from pathlib import Path

# este arquivo: lab2/economico/viabilidade_lab1.py
# Lab1 viabilidade:  workspace/lab1-material-papel-mache-grafite/economico/viabilidade.py
_HERE = Path(__file__).resolve()                      # .../lab2-.../economico/viabilidade_lab1.py
_WORKSPACE = _HERE.parents[2]                          # .../workspace
_LAB1_VIAB = _WORKSPACE / "lab1-material-papel-mache-grafite" / "economico" / "viabilidade.py"

_spec = importlib.util.spec_from_file_location("lab1_viabilidade", _LAB1_VIAB)
_mod = importlib.util.module_from_spec(_spec)
# Registrar em sys.modules ANTES de exec: dataclasses com defaults precisam
# resolver cls.__module__ (senão: AttributeError em __init__). Padrão importlib.
import sys

sys.modules["lab1_viabilidade"] = _mod
_spec.loader.exec_module(_mod)

CustoComposicao = _mod.CustoComposicao
custo_por_kg = _mod.custo_por_kg
payback_simples = _mod.payback_simples
vpl = _mod.vpl
escalabilidade_comunitaria = _mod.escalabilidade_comunitaria
indice_sustentabilidade = _mod.indice_sustentabilidade
