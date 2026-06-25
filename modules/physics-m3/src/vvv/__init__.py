"""VVV — Verificação, Validação, Certificação — Multi-Escala C11.

6 critérios binários + orquestrador que gera PASS/FAIL com return_phase.
"""
from .certificate import VVVCertificate, VVVCriterion, VVVResult
from .orchestrator import VVVOrchestrator
from .criteria.convergence import MeshConvergenceCriterion
from .criteria.stability import TemporalStabilityCriterion
from .criteria.conservation import ConservationCriterion
from .criteria.benchmark import BenchmarkCorrelationCriterion
from .criteria.cross_code import CrossCodeCriterion
from .criteria.units import UnitsConsistencyCriterion

__all__ = [
    "VVVCertificate", "VVVCriterion", "VVVResult",
    "VVVOrchestrator",
    "MeshConvergenceCriterion", "TemporalStabilityCriterion",
    "ConservationCriterion", "BenchmarkCorrelationCriterion",
    "CrossCodeCriterion", "UnitsConsistencyCriterion",
]
