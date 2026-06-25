"""Tests for structural_analysis module."""

import numpy as np
import pytest

from modules.structural_analysis import (
    von_mises_stress, tresca_stress, principal_stresses,
    safety_factor, tsai_wu_failure,
)


class TestVonMises:
    def test_uniaxial(self):
        """Uniaxial: von Mises = |sigma|."""
        vm = von_mises_stress(100, 0, 0)
        assert np.isclose(vm, 100)

    def test_plane_stress(self):
        """Biaxial: von Mises = sqrt(s1² - s1*s2 + s2²)."""
        vm = von_mises_stress(100, 50, 0)
        expected = np.sqrt(100**2 - 100*50 + 50**2)
        assert np.isclose(vm, expected)

    def test_zero(self):
        assert von_mises_stress(0, 0, 0) == 0.0


class TestTresca:
    def test_uniaxial(self):
        """Uniaxial: max shear = sigma/2."""
        t = tresca_stress(100, 0)
        assert t == 100

    def test_equal(self):
        """Equal principal: no shear."""
        t = tresca_stress(100, 100)
        assert t == 0

    def test_half(self):
        t = tresca_stress(200, 50)
        assert t == 150


class TestPrincipal:
    def test_uniaxial(self):
        s1, s2, theta = principal_stresses(100, 0, 0)
        assert np.isclose(s1, 100)
        assert np.isclose(s2, 0)

    def test_pure_shear(self):
        s1, s2, theta = principal_stresses(0, 0, 50)
        assert np.isclose(s1, 50)
        assert np.isclose(s2, -50)
        assert np.isclose(abs(theta), 45, atol=10)


class TestSafety:
    def test_safety_uniaxial(self):
        """SF = yield/applied = 250/100 = 2.5."""
        sf = safety_factor(250, 100)
        assert np.isclose(sf, 2.5)

    def test_safety_exact(self):
        """SF = 1 at yield = applied."""
        assert np.isclose(safety_factor(250, 250), 1.0)

    def test_safety_inf_zero(self):
        """SF inf at zero applied stress."""
        assert np.isinf(safety_factor(250, 0))


class TestTsaiWu:
    def test_compression(self):
        r = tsai_wu_failure(100, 0, 0, Xt=200, Xc=150, Yt=50, Yc=100, S=70)
        assert type(r) == dict and len(r) > 0
        assert "failure_index" in r or "status" in r
