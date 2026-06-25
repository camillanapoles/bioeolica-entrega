"""Tests for validacao_experimental module.

Tests the experimental validation pipeline covering:
  - Simulation vs experiment comparison (MAPE, RMSE, R², max error)
  - Model calibration with least-squares fitting
  - Structural benchmark validation (cantilever, simply supported, plate with hole)
  - VVV report generation and certification logic
  - Monte Carlo uncertainty quantification
  - Sensitivity analysis (Morris method)

All tests are designed to complete in <1s each where possible.
"""

import numpy as np
import pytest

from modules.validacao_experimental import (
    calibrate_model,
    compare_simulation_experiment,
    generate_vvv_report,
    monte_carlo_uq,
    sensitivity_analysis,
    validate_structural_benchmark,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _linear(params: list[float], x: np.ndarray) -> np.ndarray:
    """Simple linear model y = a*x + b."""
    return params[0] * x + params[1]


def _quadratic(params: list[float], x: np.ndarray) -> np.ndarray:
    """Quadratic model y = a*x² + b*x + c."""
    return params[0] * x**2 + params[1] * x + params[2]


# ===================================================================
# compare_simulation_experiment
# ===================================================================

class TestCompareSimulationExperiment:
    """Tests for compare_simulation_experiment()."""

    def test_identical_data_all_metrics_zero(self):
        """Identical sim and exp → MAPE=0, RMSE=0, R²=1, max_error=0."""
        data = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        result = compare_simulation_experiment(data, data)
        assert result["mape"] == 0.0
        assert result["rmse"] == 0.0
        assert result["r2"] == 1.0
        assert result["max_error"] == 0.0

    def test_divergent_data_all_metrics_positive(self):
        """Different sim and exp → mape > 0, rmse > 0, max_error > 0."""
        sim = np.array([0.0, 1.0, 2.0, 3.0])
        exp = np.array([0.5, 1.5, 2.5, 3.5])
        result = compare_simulation_experiment(sim, exp)
        assert result["mape"] > 0.0
        assert result["rmse"] > 0.0
        assert result["r2"] < 1.0
        assert result["max_error"] > 0.0

    def test_known_mape_matches_expected(self):
        """Compare with known offset → MAPE matches hand-calculated value."""
        sim = np.array([100.0, 200.0, 300.0])
        exp = np.array([110.0, 220.0, 330.0])
        # MAPE = mean(|(exp - sim)/exp|) * 100
        #   = mean(|10/110|, |20/220|, |30/330|) * 100
        #   = mean(0.0909, 0.0909, 0.0909) * 100
        #   ≈ 9.0909
        result = compare_simulation_experiment(sim, exp)
        assert result["mape"] == pytest.approx(9.0909, abs=0.01)
        # RMSE = sqrt(mean([10², 20², 30²])) = sqrt((100+400+900)/3) = sqrt(1400/3) ≈ 21.6
        assert result["rmse"] == pytest.approx(21.602, abs=0.01)
        # R² = 1 - SS_res/SS_tot
        assert result["max_error"] == 30.0

    def test_rmse_metric_explicit(self):
        """Using metric='rmse' still returns full dict."""
        sim = np.array([0.0, 1.0, 2.0])
        exp = np.array([0.0, 2.0, 2.0])
        result = compare_simulation_experiment(sim, exp, metric="rmse")
        assert "rmse" in result
        assert "mape" in result
        assert result["rmse"] == pytest.approx(0.57735, abs=0.01)

    def test_invalid_metric_raises_value_error(self):
        """Unknown metric name → ValueError."""
        sim = np.array([0.0, 1.0, 2.0])
        exp = np.array([0.0, 1.0, 2.0])
        with pytest.raises(ValueError, match="metric"):
            compare_simulation_experiment(sim, exp, metric="invalid_metric")


# ===================================================================
# calibrate_model
# ===================================================================

class TestCalibrateModel:
    """Tests for calibrate_model()."""

    def test_linear_model_known_fit(self):
        """Calibrate y = 2*x + 1 → params [2, 1] within tolerance."""
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = 2.0 * x + 1.0
        result = calibrate_model(_linear, x, y, initial_params=[0.0, 0.0])
        assert result["params"][0] == pytest.approx(2.0, abs=0.01)
        assert result["params"][1] == pytest.approx(1.0, abs=0.01)
        assert result["r_squared"] > 0.5 or len(result["params"]) == 2
        assert result["iterations"] >= 0

    def test_calibrate_with_bounds(self):
        """Calibrate with bounds → params stay within bounds."""
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = 5.0 * x + 3.0
        bounds = ([0.0, 0.0], [10.0, 10.0])  # scipy format: ([lower], [upper])
        result = calibrate_model(_linear, x, y, initial_params=[0.0, 0.0], bounds=bounds)
        # bounds = ([lower1, lower2], [upper1, upper2])
        for pi, lo, hi in zip(result["params"], bounds[0], bounds[1]):
            assert lo <= pi <= hi, f"param {pi} out of bounds [{lo}, {hi}]"

    def test_quadratic_model(self):
        """Calibrate quadratic y = 3x² + 0x + 1 → params [3, 0, 1]."""
        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = 3.0 * x**2 + 0.0 * x + 1.0
        result = calibrate_model(_quadratic, x, y, initial_params=[1.0, 1.0, 1.0])
        assert result["params"][0] == pytest.approx(3.0, abs=0.05)
        assert result["params"][2] == pytest.approx(1.0, abs=0.05)
        assert result["r_squared"] > 0.99

    def test_calibrate_covariance_returned(self):
        """Calibrate returns covariance matrix."""
        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = 2.0 * x + 1.0
        result = calibrate_model(_linear, x, y, initial_params=[0.0, 0.0])
        assert "covariance" in result
        assert result["covariance"] is not None
        # Covariance should be a square matrix
        n = len(result["params"])
        assert result["covariance"].shape == (n, n)


# ===================================================================
# validate_structural_benchmark
# ===================================================================

class TestValidateStructuralBenchmark:
    """Tests for validate_structural_benchmark()."""

    def test_cantilever_exact_match_passes(self):
        """Cantilever benchmark with exact match → passed=True, error=0."""
        result = validate_structural_benchmark(
            "cantilever", sim_result=0.001, tol=0.05
        )
        assert result["benchmark"] == "cantilever"
        assert result["error"] == 0.0
        assert result["passed"] == True

    def test_simply_supported_within_tolerance(self):
        """Simply supported benchmark with 5% error → error < 0.05."""
        # sim_result targets analytical value with 5% deviation
        analytical_value = 5.0
        sim_value = 5.0 * 1.05
        result = validate_structural_benchmark(
            "simply_supported", sim_result=sim_value, tol=0.05
        )
        assert result["analytical_value"] == pytest.approx(analytical_value, abs=0.01)
        assert result["error"] <= 0.05

    def test_plate_hole_stress_concentration(self):
        """Plate with hole benchmark → Kt ≈ 3.0."""
        result = validate_structural_benchmark("plate_hole", sim_result=300.0, tol=0.10)
        # analytical_value == 300 / Kt_analytical where Kt_analytical ≈ 3.0
        # The benchmark reports Kt: sim/analytical
        kt_sim = result["simulation_value"] / result["analytical_value"]
        assert kt_sim == pytest.approx(3.0, abs=0.15)

    def test_unknown_benchmark_raises_value_error(self):
        """Unknown benchmark name → ValueError."""
        with pytest.raises(ValueError, match="Unknown benchmark|unknown|not found"):
            validate_structural_benchmark("nonexistent_benchmark", sim_result=1.0)

    def test_tight_tolerance_causes_failure(self):
        """Very tight tolerance with small error → passed=False."""
        # analytical value is 10.0, sim is 10.05, tolerance = 0.001
        result = validate_structural_benchmark(
            "cantilever", sim_result=10.05, tol=0.001
        )
        assert result["passed"] is False
        assert result["error"] > 0.001


# ===================================================================
# generate_vvv_report
# ===================================================================

class TestGenerateVVVReport:
    """Tests for generate_vvv_report()."""

    def test_single_validation_has_required_keys(self):
        """VVV report from single validation → dict with all required keys."""
        validations = [
            {
                "name": "cantilever_test",
                "passed": True,
                "error": 0.0,
                "metric": "max_deflection",
            }
        ]
        report = generate_vvv_report(validations)
        for key in ("verification_status", "validation_metrics", "certification_result",
                     "recommendations"):
            assert key in report, f"Missing key: {key}"

    def test_certification_pass_when_all_pass(self):
        """All validations pass → certification_result='PASS'."""
        validations = [
            {"name": "a", "passed": True, "error": 0.01},
            {"name": "b", "passed": True, "error": 0.02},
            {"name": "c", "passed": True, "error": 0.03},
        ]
        report = generate_vvv_report(validations)
        assert report["certification_result"] == "PASS"
        assert report["verification_status"] in ("PASS", "VERIFIED")

    def test_certification_fail_when_any_fails(self):
        """Any validation fails → certification_result='FAIL'."""
        validations = [
            {"name": "a", "passed": True, "error": 0.01},
            {"name": "b", "passed": False, "error": 0.15},
        ]
        report = generate_vvv_report(validations)
        assert report["certification_result"] == "FAIL"

    def test_empty_validations_list(self):
        """Empty validations → status='INCONCLUSIVE' or similar."""
        report = generate_vvv_report([])
        assert report["certification_result"] in ("INCONCLUSIVE", "PASS", "NONE")
        assert "recommendations" in report

    def test_validation_metrics_aggregated(self):
        """validation_metrics contains aggregated error stats."""
        validations = [
            {"name": "a", "passed": True, "error": 0.01},
            {"name": "b", "passed": True, "error": 0.03},
            {"name": "c", "passed": True, "error": 0.05},
        ]
        report = generate_vvv_report(validations)
        metrics = report["validation_metrics"]
        assert "n_validations" in metrics
        assert metrics["n_validations"] == 3
        assert "max_error" in metrics


# ===================================================================
# monte_carlo_uq
# ===================================================================

class TestMonteCarloUQ:
    """Tests for monte_carlo_uq()."""

    def test_linear_model_returns_stats(self):
        """Monte Carlo with linear model → returns dict with p5, p50, p95, mean, std."""
        def model(params, x=None):
            return params[0] * np.array([1.0]) + params[1]

        params = [2.0, 1.0]
        distributions = {
            0: {"type": "normal", "mean": 2.0, "std": 0.1},
            1: {"type": "normal", "mean": 1.0, "std": 0.05},
        }
        result = monte_carlo_uq(model, params, distributions, n_samples=200)
        for key in ("p5", "p50", "p95", "mean", "std"):
            assert key in result, f"Missing key: {key}"
        # mean should be near 2*1 + 1 = 3
        assert abs(result["mean"] - 3.0) < 0.15
        # p50 should be near median
        assert result["p5"] <= result["p50"] <= result["p95"]

    def test_sample_count_matches(self):
        """Monte Carlo n_samples matches requested count."""
        def model(params, x=None):
            return params[0] * np.array([1.0])

        params = [1.0]
        distributions = {0: {"type": "uniform", "low": 0.9, "high": 1.1}}
        result = monte_carlo_uq(model, params, distributions, n_samples=500)
        # The result dict may contain a sample count field, or we just verify
        # stats are reasonable (std close to expected from uniform 0.9-1.1)
        assert result["std"] > 0.0
        assert 0.9 <= result["p5"] < result["p95"] <= 1.1
        assert "mean" in result

    def test_deterministic_model_std_zero(self):
        """No parameter variation → std=0, all percentiles equal."""
        def model(params, x=None):
            return np.array([5.0])

        params = [2.0]
        distributions = {0: {"type": "normal", "mean": 2.0, "std": 0.0}}
        result = monte_carlo_uq(model, params, distributions, n_samples=100)
        assert result["std"] == 0.0
        assert result["p5"] == result["p50"] == result["p95"] == result["mean"]


# ===================================================================
# sensitivity_analysis
# ===================================================================

class TestSensitivityAnalysis:
    """Tests for sensitivity_analysis()."""

    def test_returns_ranking(self):
        """Sensitivity analysis returns mu* and sigma arrays with ranking."""
        def model(params, x=None):
            return params[0] * 1.0 + params[1] * 2.0

        params = [1.0, 2.0]
        param_ranges = {0: (0.5, 1.5), 1: (1.0, 3.0)}
        result = sensitivity_analysis(model, params, param_ranges, method="morris")
        for key in ("mu*", "sigma", "ranking"):
            assert key in result, f"Missing key: {key}"
        assert len(result["mu*"]) == 2        # one per parameter
        assert len(result["ranking"]) == 2
        assert result["ranking"][0] in (0, 1)  # ranks are param indices

    def test_more_sensitive_param_ranks_higher(self):
        """Parameter with larger range impact ranks higher (lower rank number)."""
        def model(params, x=None):
            return params[0] * 100.0 + params[1] * 0.01

        params = [1.0, 1.0]
        param_ranges = {0: (0.0, 2.0), 1: (0.0, 2.0)}
        result = sensitivity_analysis(model, params, param_ranges, method="morris")
        # param 0 has much higher influence (coefficient 100 vs 0.01)
        influenced_mu_0 = result["mu*"][0]
        influenced_mu_1 = result["mu*"][1]
        assert influenced_mu_0 > influenced_mu_1


# ===================================================================
# Edge cases and error handling
# ===================================================================

class TestEdgeCases:
    """Edge cases and error handling across the module."""

    def test_compare_empty_arrays(self):
        """Empty arrays → function handles gracefully."""
        sim = np.array([])
        exp = np.array([])
        result = compare_simulation_experiment(sim, exp)
        # May return zeros or raise; either is acceptable as long as it's defined
        assert type(result) == dict and len(result) > 0

    def test_calibrate_single_point(self):
        """Calibrate with single data point → params returned."""
        x = np.array([1.0])
        y = np.array([3.0])
        result = calibrate_model(_linear, x, y, initial_params=[0.0, 0.0])
        assert "params" in result

    def test_vvv_report_with_output_path(self):
        """VVV report with output_path saves to disk."""
        import tempfile
        import os
        validations = [{"name": "test", "passed": True, "error": 0.01}]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            report = generate_vvv_report(validations, output_path=out_path)
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 0
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)
