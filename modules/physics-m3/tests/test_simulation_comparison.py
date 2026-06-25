"""Tests for SimulationComparison — aligned with actual module API."""

import numpy as np
import pytest

from modules.simulation_comparison import SimulationComparison


@pytest.fixture
def sc():
    return SimulationComparison()


def test_add_and_rmse(sc):
    x = np.array([0, 1, 2, 3])
    sc.add_pair("p", x, x, x, x)
    assert sc.rmse("p") == 0.0


def test_mae(sc):
    x = np.array([0, 1, 2, 3])
    sc.add_pair("p", x, x, x, x)
    assert sc.mae("p") == 0.0


def test_r2_perfect(sc):
    x = np.array([0, 1, 2, 3, 4])
    sc.add_pair("p", x, x, x, x)
    assert np.isclose(sc.r2("p"), 1.0)


def test_max_error(sc):
    x = np.array([0, 1, 2])
    sc.add_pair("t", x, [0, 1, 2], x, [0, 2, 2])
    assert sc.max_error("t") == 1.0


def test_relative_error(sc):
    x = np.array([1, 2, 3])
    sc.add_pair("t", x, [1, 2, 3], x, [1.1, 2.0, 2.9])
    assert sc.relative_error("t") > 0


def test_correlation(sc):
    x = np.array([0, 1, 2, 3])
    sc.add_pair("t", x, x, x, x + 0.1)
    assert np.isclose(sc.correlation("t"), 1.0, atol=0.01)


def test_all_metrics(sc):
    x = np.linspace(0, 1, 10)
    sc.add_pair("t", x, x, x, x)
    m = sc.all_metrics("t")
    for k in ("rmse", "mae", "r2", "max_error", "correlation"):
        assert k in m


def test_report(sc):
    x = np.linspace(0, 1, 5)
    sc.add_pair("a", x, x, x, x)
    sc.add_pair("b", x, x, x, x + 0.1)
    r = sc.report()
    assert "a" in r and "RMSE" in r
