"""Integration test: VVVOrchestrator — 6 critérios + certificação PASS/FAIL.

Valida que o fluxo completo de VVV multi-escala C11 funciona:
  1. convergence_errors: [8, 3, 1] → monótono decrescente + convergido < 5%
  2. stability_residuals: [1e-2, 1e-3, 1e-5] → residual < 1e-4
  3. conservation: mass=0.3%, energy=0.5% → ambos < 1%
  4. benchmark: numerical=10.5 vs analytical=10.0 → 5% error < 10%
  5. cross-code: method A vs B → max error < 5%
  6. units: quantities check → pass rate >= 80%
"""
import pytest

from physics_m3.vvv.certificate import VVVCertificate, VVVCriterion, VVVResult
from physics_m3.vvv.orchestrator import VVVOrchestrator


class TestVVVCriteria:
    """Test each criterion independently."""

    def test_criterion_dataclass(self):
        c = VVVCriterion("test", True, 1.0, 5.0, "ok")
        d = c.to_dict()
        assert d["name"] == "test"
        assert d["passed"] is True
        assert d["metric_value"] == 1.0

    def test_criterion_failure(self):
        c = VVVCriterion("test", False, 99.0, 5.0, "exceeded tolerance")
        assert not c.passed


class TestCertificate:
    """Test VVVCertificate aggregation."""

    def test_all_pass(self):
        cert = VVVCertificate(domain="mecanica", scale="meso")
        cert.add_criterion(VVVCriterion("mesh_convergence", True, 2.0, 5.0))
        cert.add_criterion(VVVCriterion("temporal_stability", True, 5e-5, 1e-4))
        cert.add_criterion(VVVCriterion("conservation", True, 0.5, 1.0))
        cert.add_criterion(VVVCriterion("benchmark_correlation", True, 4.0, 10.0))
        cert.add_criterion(VVVCriterion("cross_code", True, 2.0, 5.0))
        cert.add_criterion(VVVCriterion("units_consistency", True, 100.0, 80.0))

        result = cert.evaluate()
        assert result.overall_status == "PASS"
        assert result.return_phase is None

    def test_any_fail_causes_fail(self):
        cert = VVVCertificate()
        cert.add_criterion(VVVCriterion("mesh_convergence", True, 2.0, 5.0))
        cert.add_criterion(VVVCriterion("conservation", False, 2.5, 1.0, "mass error 2.5%"))

        result = cert.evaluate()
        assert result.overall_status == "FAIL"
        assert result.return_phase is not None
        assert "conservation" in result.return_reason or "conservation" in str(result.return_reason)

    def test_return_phase_mapping(self):
        """Each criterion failure should map to correct return phase."""
        pairs = [
            ("mesh_convergence", "F5→F4"),
            ("temporal_stability", "F5→F4"),
            ("conservation", "F5→F3"),
            ("benchmark_correlation", "F5→F3"),
            ("cross_code", "F5→F4"),
            ("units_consistency", "F5→F1"),
        ]
        for criterion_name, expected_phase in pairs:
            cert = VVVCertificate()
            for name in VVVCertificate.CRITERION_NAMES:
                cert.add_criterion(VVVCriterion(name, True, 0, 1))
            # Override the specific one to fail
            cert.criteria[criterion_name] = VVVCriterion(criterion_name, False, 99, 1)
            result = cert.evaluate()
            assert result.overall_status == "FAIL"
            assert result.return_phase == expected_phase, \
                f"{criterion_name}: expected {expected_phase}, got {result.return_phase}"

    def test_metrics_present(self):
        cert = VVVCertificate(domain="fluidos", scale="macro")
        cert.add_criterion(VVVCriterion("mesh_convergence", True, 3.0, 5.0))
        result = cert.evaluate()
        assert "mesh_convergence_value" in result.metrics
        assert result.domain == "fluidos"
        assert result.scale == "macro"


class TestVVVOrchestrator:
    """Test full orchestrator with real criteria objects."""

    def test_all_criteria_pass(self):
        """Simulação de uma análise bem-sucedida — todos os 6 critérios PASS."""
        orch = VVVOrchestrator(domain="mecanica", scale="macro")
        result = orch.run_all(
            convergence_errors=[8.0, 3.0, 1.2],
            convergence_h=[0.5, 0.25, 0.125],
            stability_residuals=[1e-2, 1e-3, 5e-5],
            mass_balance_error=0.3,
            energy_balance_error=0.5,
            numerical_value=10.5,
            analytical_value=10.0,
            cross_code_a=[100, 200, 300],
            cross_code_b=[102, 198, 305],
            units_quantities={
                "stress": (1e6, "pressure"),
                "velocity": (10.0, "velocity"),
            },
        )
        assert result.overall_status == "PASS", f"Expected PASS, got {result.overall_status}"
        assert result.return_phase is None
        assert result.simulation_id is not None

    def test_convergence_fails(self):
        """Malha não converge → FAIL + retorna F5→F4."""
        orch = VVVOrchestrator()
        result = orch.run_all(
            convergence_errors=[2.0, 3.0, 6.0],  # increasing → diverging
            convergence_h=[0.5, 0.25, 0.125],
            stability_residuals=[1e-3, 1e-4, 1e-5],
            mass_balance_error=0.1,
            energy_balance_error=0.2,
        )
        assert result.overall_status == "FAIL"
        assert result.return_phase == "F5→F4"

    def test_conservation_fails(self):
        """Erro de conservação > 1% → FAIL + retorna F5→F3."""
        orch = VVVOrchestrator()
        result = orch.run_all(
            convergence_errors=[8, 3, 1],
            convergence_h=[0.5, 0.25, 0.125],
            mass_balance_error=2.5,  # > 1%
            energy_balance_error=0.3,
        )
        assert result.overall_status == "FAIL"
        assert result.return_phase == "F5→F3"

    def test_units_fails(self):
        """Unidades inconsistentes → FAIL + retorna F5→F1."""
        orch = VVVOrchestrator()
        result = orch.run_all(
            convergence_errors=[8, 3, 1],
            convergence_h=[0.5, 0.25, 0.125],
            mass_balance_error=0.1,
            energy_balance_error=0.2,
            units_quantities={
                "stress": (1e6, "pressure"),
                "bad_quantity": (None, "unknown_dim"),  # invalid
            },
        )
        assert result.overall_status == "FAIL"
        assert result.return_phase == "F5→F1"

    def test_skip_criteria(self):
        """Critérios sem dados → skipped (não falham)."""
        orch = VVVOrchestrator()
        result = orch.run_all(
            mass_balance_error=0.0,
            energy_balance_error=0.0,
        )
        # All skipped criteria default to PASS, conservation at 0% → PASS
        assert result.overall_status == "PASS"

    def test_result_dict_format(self):
        """VVVResult.to_dict() deve ter todos os campos esperados."""
        orch = VVVOrchestrator()
        result = orch.run_all(
            convergence_errors=[8, 3, 1],
            convergence_h=[0.5, 0.25, 0.125],
            mass_balance_error=0.1,
            energy_balance_error=0.2,
        )
        d = result.to_dict()
        assert "simulation_id" in d
        assert "timestamp" in d
        assert "criteria" in d
        assert "overall_status" in d
        assert "metrics" in d
        assert len(d["criteria"]) == 6

    def test_vvvreport_reuse_compatibility(self):
        """Verificar compatibilidade com vvv_protocol existente."""
        from physics_m3.vvv_protocol import VVVReport
        vvv = VVVReport(study_name="Orchestrator Compat Test")
        v_result = vvv.validate_analytical(10.5, 10.0, 10.0)
        assert v_result["status"] == "PASS"
        assert round(v_result["error_pct"], 1) == 5.0
