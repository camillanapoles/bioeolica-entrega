"""6 critérios VVV — um por módulo."""
from .convergence import MeshConvergenceCriterion
from .stability import TemporalStabilityCriterion
from .conservation import ConservationCriterion
from .benchmark import BenchmarkCorrelationCriterion
from .cross_code import CrossCodeCriterion
from .units import UnitsConsistencyCriterion

__all__ = [
    "MeshConvergenceCriterion",
    "TemporalStabilityCriterion",
    "ConservationCriterion",
    "BenchmarkCorrelationCriterion",
    "CrossCodeCriterion",
    "UnitsConsistencyCriterion",
]
