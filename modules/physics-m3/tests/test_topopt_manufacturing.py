"""Tests for topopt_manufacturing — aligned with actual module API."""

import numpy as np
import pytest

from modules.topopt_manufacturing import TopOptManufacturing
from modules.topology_optimization import TopOpt


class TestInit:
    def test_valid_defaults(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        assert m.overhang_angle == 45.0
        assert m.min_feature_size == 2
        assert abs(m.anisotropy_factor - 1.0) < 1e-10

    def test_invalid_overhang(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        with pytest.raises(ValueError):
            TopOptManufacturing(opt, overhang_angle=0)

    def test_invalid_anisotropy(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        with pytest.raises(ValueError):
            TopOptManufacturing(opt, anisotropy_factor=1.5)


class TestOverhang:
    def test_solid_unchanged(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        d = np.ones((6, 10), dtype=np.float64)
        c = m.apply_overhang_constraint(d)
        assert np.all(c == d)

    def test_void_unchanged(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        d = np.zeros((6, 10), dtype=np.float64)
        c = m.apply_overhang_constraint(d)
        assert np.allclose(c, d)


class TestMinFeature:
    def test_uniform_preserved(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt, min_feature_size=2)
        d = m.apply_min_feature(0.5 * np.ones((6, 10)))
        assert d.shape == (6, 10)
        assert np.all(d >= 0) and np.all(d <= 1)


class TestSupportVolume:
    def test_solid_zero(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        assert m.estimate_support_volume(np.ones((6, 10))) == 0.0

    def test_cantilever_positive(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt, overhang_angle=30)
        d = np.zeros((6, 10), dtype=np.float64)
        d[0, 2:5] = 1.0
        assert m.estimate_support_volume(d) > 0


class TestPrintability:
    def test_returns_dict_with_keys(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        r = m.check_printability()
        for k in ("printable", "overhang_ratio", "min_feature_pass",
                  "anisotropy_factor", "support_volume"):
            assert k in r, f"missing key: {k}"

    def test_solid_printable(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        r = m.check_printability(np.ones((6, 10)))
        assert r["overhang_ratio"] == 0.0


class TestStepSolve:
    def test_step_positive(self):
        opt = TopOpt(nelx=8, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        assert m.step() > 0

    def test_solve_returns_density(self):
        opt = TopOpt(nelx=8, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        d = m.solve(max_iter=5)
        assert d.shape == (6, 8)
        assert np.all(d >= 0) and np.all(d <= 1)


class TestProperties:
    def test_support_volume(self):
        opt = TopOpt(nelx=10, nely=6, volfrac=0.4)
        m = TopOptManufacturing(opt)
        assert type(m.support_volume) == float
        m.step()
        assert m.support_volume >= 0
