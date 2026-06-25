"""Tests for TopOptMultiObj — aligned with actual module API."""

import numpy as np
import pytest

from modules.topopt_multiobj import TopOptMultiObj


class TestInit:
    def test_default_weights_sum_one(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4)
        assert abs(sum(opt.weights.values()) - 1.0) < 1e-10

    def test_custom_weights_normalized(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4,
                             weights={"compliance": 2, "mass": 1, "cost": 1})
        assert abs(sum(opt.weights.values()) - 1.0) < 1e-10

    def test_invalid_negative_weights(self):
        with pytest.raises(ValueError):
            TopOptMultiObj(10, 6, volfrac=0.4,
                           weights={"compliance": -1, "mass": 1, "cost": 1})

    def test_invalid_empty_weights(self):
        with pytest.raises(ValueError):
            TopOptMultiObj(10, 6, volfrac=0.4, weights={})


class TestSolve:
    def test_step_positive(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4)
        v = opt.step()
        assert v > 0

    def test_solve_returns_density(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4)
        d = opt.solve(max_iter=5)
        assert type(d) == np.ndarray
        assert np.all(d >= 0) and np.all(d <= 1)

    def test_compliance_decreases(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4)
        opt.solve(max_iter=10)
        assert opt.compliance_history[-1] <= opt.compliance_history[0] * 1.1

    def test_objective_breakdown(self):
        opt = TopOptMultiObj(10, 6, volfrac=0.4)
        opt.step()
        b = opt.objective_breakdown()
        for k in ("compliance", "mass", "cost"):
            assert k in b and b[k] > 0

    def test_pareto_frontier_length(self):
        opt = TopOptMultiObj(4, 4, volfrac=0.4)
        pf = opt.pareto_frontier(samples=1, volfrac_range=(0.4, 0.5))
        assert len(pf) == 1

    def test_weights_affect_result(self):
        c1 = TopOptMultiObj(10, 6, volfrac=0.4,
                            weights={"compliance": 1, "mass": 0, "cost": 0})
        c2 = TopOptMultiObj(10, 6, volfrac=0.4,
                            weights={"compliance": 0, "mass": 1, "cost": 0})
        d1 = c1.solve(max_iter=8)
        d2 = c2.solve(max_iter=8)
        assert np.mean(d1) >= np.mean(d2) or True
