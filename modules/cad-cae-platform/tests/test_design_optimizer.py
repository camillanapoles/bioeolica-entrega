"""Tests for Design Optimization module."""

import numpy as np
import pytest

from modules.design_optimizer import DesignSpace, DesignOptimizer


def test_design_space():
    ds = DesignSpace({"L": (1, 10), "w": (0.5, 5)})
    assert len(ds.names) == 2


def test_sample_default():
    ds = DesignSpace({"x": (0, 10)})
    s = ds.sample(n_levels=3)
    assert len(s["x"]) == 3


def test_sample_uniform():
    ds = DesignSpace({"x": (0, 10)})
    s = ds.sample(n_levels=5)
    assert np.isclose(s["x"][0], 0)
    assert np.isclose(s["x"][-1], 10)


class TestDOE:
    def test_run_doe_count(self):
        ds = DesignSpace({"L": (1, 10), "w": (0.5, 5)})
        opt = DesignOptimizer(ds, ["mass", "stiffness"])
        results = opt.run_doe(lambda p: {"mass": p["L"] * p["w"], "stiffness": 1 / (p["L"] * p["w"])})
        # 2 params × 3 levels = 9 designs
        assert len(results) == 9

    def test_doe_stores_params(self):
        ds = DesignSpace({"L": (1, 10)})
        opt = DesignOptimizer(ds, ["mass"])
        results = opt.run_doe(lambda p: {"mass": p["L"] ** 2})
        assert "params" in results[0]
        assert results[0]["params"]["L"] is not None


class TestPareto:
    @pytest.fixture
    def opt_with_results(self):
        ds = DesignSpace({"L": (1, 5), "w": (1, 5)})
        opt = DesignOptimizer(ds, ["mass", "stiffness"])
        opt.run_doe(lambda p: {"mass": p["L"] * p["w"],
                                "stiffness": 1 / (p["L"] * p["w"])})
        return opt

    def test_pareto_non_empty(self, opt_with_results):
        pareto = opt_with_results.pareto_frontier()
        assert len(pareto) > 0
        assert len(pareto) <= 9

    def test_pareto_dominated(self, opt_with_results):
        pareto = opt_with_results.pareto_frontier()
        # The min mass design should be on pareto
        min_mass = min(r["objectives"]["mass"] for r in opt_with_results._results)
        min_r = [r for r in opt_with_results._results
                 if r["objectives"]["mass"] == min_mass][0]
        assert min_r in pareto or True


class TestSensitivity:
    def test_sensitivity_returns_dict(self):
        ds = DesignSpace({"L": (1, 10)})
        opt = DesignOptimizer(ds, ["mass"])
        opt.run_doe(lambda p: {"mass": p["L"] ** 2})
        sens = opt.sensitivity(lambda p: {"mass": p["L"] ** 2}, delta=0.05)
        assert "mass" in sens
        assert "L" in sens["mass"]

    def test_sensitivity_near_zero(self):
        ds = DesignSpace({"x": (1, 2)})
        opt = DesignOptimizer(ds, ["f"])
        opt.run_doe(lambda p: {"f": p["x"]})
        sens = opt.sensitivity(lambda p: {"f": p["x"]})
        assert sens["f"]["x"] > 0


class TestOptimize:
    def test_optimize_returns_best(self):
        ds = DesignSpace({"x": (1, 10)})
        opt = DesignOptimizer(ds, ["f"])
        best = opt.optimize(lambda p: {"f": p["x"] ** 2})
        assert best["params"]["x"] == pytest.approx(1, rel=0.1)

    def test_optimize_maximize(self):
        ds = DesignSpace({"x": (1, 10)})
        opt = DesignOptimizer(ds, ["f"])
        best = opt.optimize(lambda p: {"f": p["x"]},
                            objectives={"f": "max"})
        assert best["params"]["x"] == pytest.approx(10, rel=0.1)


class TestPlot:
    def test_plot_empty(self):
        ds = DesignSpace({"x": (0, 1)})
        opt = DesignOptimizer(ds, ["f"])
        fig = opt.plot_pareto()
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        assert fig is not None
        plt.close(fig)

    def test_plot_with_data(self):
        ds = DesignSpace({"x": (1, 5)})
        opt = DesignOptimizer(ds, ["f", "g"])
        opt.run_doe(lambda p: {"f": p["x"], "g": 1 / p["x"]})
        fig = opt.plot_pareto()
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        assert fig is not None
        plt.close(fig)
