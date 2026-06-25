import numpy as np; import pytest
from modules.uncertainty import UncertainValue, confidence_interval, MonteCarloSampler, propagate_error

def test_init():
    u = UncertainValue(nominal=100, std=5)
    assert u.nominal == 100

def test_confidence():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    m, lo, hi = confidence_interval(data)
    assert isinstance(m, (float, np.floating))

def test_mc_init():
    s = MonteCarloSampler(n_samples=100)
    assert s.n_samples == 100
