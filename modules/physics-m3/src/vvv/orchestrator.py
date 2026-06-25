"""VVVOrchestrator — executa os 6 critérios, gera PASS/FAIL + return_phase.

Usa VVVCertificate como container e reusa VVVReport do vvv_protocol
quando aplicável (convergência, correlação analítica, cross-code).
"""
from typing import Dict, List, Optional, Tuple

from physics_m3.vvv.certificate import VVVCertificate, VVVCriterion, VVVResult
from physics_m3.vvv.criteria.convergence import MeshConvergenceCriterion
from physics_m3.vvv.criteria.stability import TemporalStabilityCriterion
from physics_m3.vvv.criteria.conservation import ConservationCriterion
from physics_m3.vvv.criteria.benchmark import BenchmarkCorrelationCriterion
from physics_m3.vvv.criteria.cross_code import CrossCodeCriterion
from physics_m3.vvv.criteria.units import UnitsConsistencyCriterion


class VVVOrchestrator:
    """Orquestrador VVV — executa 6 critérios em sequência e certifica."""

    def __init__(self, domain: str = "general", scale: str = "meso"):
        self.domain = domain
        self.scale = scale
        self.certificate = VVVCertificate(domain=domain, scale=scale)

        self.convergence = MeshConvergenceCriterion()
        self.stability = TemporalStabilityCriterion()
        self.conservation = ConservationCriterion()
        self.benchmark = BenchmarkCorrelationCriterion()
        self.cross_code = CrossCodeCriterion()
        self.units = UnitsConsistencyCriterion()

    def run_all(self, *,  # keyword-only args for clarity
                convergence_errors: Optional[List[float]] = None,
                convergence_h: Optional[List[float]] = None,
                stability_residuals: Optional[List[float]] = None,
                mass_balance_error: float = 0.0,
                energy_balance_error: float = 0.0,
                numerical_value: float = 0.0,
                analytical_value: float = 0.0,
                cross_code_a: Optional[List[float]] = None,
                cross_code_b: Optional[List[float]] = None,
                units_quantities: Optional[Dict] = None,
                ) -> VVVResult:
        """Execute all 6 VVV criteria and return certification result."""

        # C1: Mesh convergence
        if convergence_errors is not None and convergence_h is not None:
            c1 = self.convergence.evaluate(convergence_errors, convergence_h)
        else:
            c1 = VVVCriterion("mesh_convergence", True, 0, 5, "skipped (no data)")
        self.certificate.add_criterion(c1)

        # C2: Temporal stability
        if stability_residuals is not None:
            c2 = self.stability.evaluate(stability_residuals)
        else:
            c2 = VVVCriterion("temporal_stability", True, 0, 1e-4, "skipped (no data)")
        self.certificate.add_criterion(c2)

        # C3: Conservation
        c3 = self.conservation.evaluate(mass_balance_error, energy_balance_error)
        self.certificate.add_criterion(c3)

        # C4: Benchmark correlation
        if numerical_value != 0.0 or analytical_value != 0.0:
            c4 = self.benchmark.evaluate_analytical(numerical_value, analytical_value)
        else:
            c4 = VVVCriterion("benchmark_correlation", True, 0, 10, "skipped (no data)")
        self.certificate.add_criterion(c4)

        # C5: Cross-code
        if cross_code_a is not None and cross_code_b is not None:
            c5 = self.cross_code.evaluate(cross_code_a, cross_code_b)
        else:
            c5 = VVVCriterion("cross_code", True, 0, 5, "skipped (no data)")
        self.certificate.add_criterion(c5)

        # C6: Units consistency
        if units_quantities is not None:
            c6 = self.units.evaluate(units_quantities)
        else:
            c6 = VVVCriterion("units_consistency", True, 100, 80, "skipped (no data)")
        self.certificate.add_criterion(c6)

        # Evaluate all
        return self.certificate.evaluate()
