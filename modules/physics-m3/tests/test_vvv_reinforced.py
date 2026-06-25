"""Tests for VVVReinforced module."""

import numpy as np
import pytest

from modules.vvv_reinforced import VVVReinforced, VVVResult


@pytest.fixture
def vvv():
    return VVVReinforced()


def test_init(vvv):
    assert len(vvv.results) == 0


def test_validate_perfect(vvv):
    y = np.array([0.0, 1.0, 2.0, 3.0])
    r = vvv.validate("perfect", y, y)
    assert r.rmse == 0.0
    assert r.r2 == 1.0
    assert r.certified


def test_validate_close(vvv):
    sim = np.array([0.0, 1.0, 2.0, 3.0])
    exp = np.array([0.05, 1.02, 1.98, 3.05])
    r = vvv.validate("close", sim, exp)
    assert r.rmse < 0.05
    assert r.r2 > 0.99


def test_validate_bad_not_certified(vvv):
    sim = np.array([0.0, 1.0, 2.0, 3.0])
    exp = np.array([5.0, 6.0, 7.0, 8.0])
    r = vvv.validate("bad", sim, exp)
    assert not r.certified


def test_certify(vvv):
    y = np.array([1.0, 2.0, 3.0])
    vvv.validate("test", y, y)
    assert vvv.certify("test")
    assert not vvv.certify("nonexistent")


def test_cross_code(vvv):
    a = np.array([0.0, 1.0, 2.0])
    b = np.array([0.01, 1.02, 1.99])
    r = vvv.validate_cross_code("cross", a, b)
    assert "(cross-code)" in r.name
    assert r.r2 > 0.99


def test_report(vvv):
    y1 = np.array([0.0, 1.0, 2.0])
    y2 = np.array([10.0, 11.0, 12.0])
    vvv.validate("good", y1, y1)
    vvv.validate("bad", y2, y1)
    r = vvv.report()
    assert "good" in r
    assert "bad" in r
    assert "CERTIFIED" in r
    assert "FAILED" in r


def test_summary(vvv):
    y = np.array([1.0, 2.0, 3.0])
    vvv.validate("a", y, y)
    vvv.validate("b", y, y + 5)
    s = vvv.summary()
    assert s["n_cases"] == 2
    assert s["n_certified"] >= 1
    assert s["n_certified"] <= 2


def test_custom_criteria(vvv):
    y = np.array([0.0, 1.0, 2.0])
    r = vvv.validate("strict", y, y + 0.5, criteria={"rmse": 0.01})
    assert not r.certified


def test_validate_shape_mismatch(vvv):
    sim = np.array([0.0, 1.0, 2.0])
    exp = np.array([0.0, 1.0])
    with pytest.raises(ValueError):
        vvv.validate("mismatch", sim, exp)
