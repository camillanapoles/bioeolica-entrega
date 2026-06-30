"""Tests for KDI Multi-Physics coupling."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from kdi_m3.kdi_multiphysics import MultiPhysicsAnalysis, MultiPhysicsConfig


class TestFluid:
    def test_run_fluid(self):
        ma = MultiPhysicsAnalysis()
        r = ma.run_fluid({"Reynolds": 1e5, "velocity_ms": 10})
        assert "boundary_layer_thickness_m" in r
        assert r["status"] == "PASS"


class TestThermal:
    def test_run_thermal(self):
        ma = MultiPhysicsAnalysis()
        r = ma.run_thermal({"heat_flux_Wm2": 1000, "conductivity_WmK": 0.5})
        assert r["temperature_gradient_K"] > 0
        assert r["status"] == "PASS"

    def test_thermal_zero_k(self):
        ma = MultiPhysicsAnalysis()
        r = ma.run_thermal({"heat_flux_Wm2": 100, "conductivity_WmK": 0})
        assert r["temperature_gradient_K"] == 0


class TestStructural:
    def test_run_structural(self):
        ma = MultiPhysicsAnalysis()
        r = ma.run_structural({"E_GPa": 210, "force_N": 5000})
        assert r["displacement_mm"] > 0
        assert r["status"] == "PASS"

    def test_structural_zero_area(self):
        ma = MultiPhysicsAnalysis()
        r = ma.run_structural({"force_N": 1000, "area_m2": 0})
        assert r["stress_MPa"] == 0


class TestCoupled:
    @pytest.fixture
    def ma(self):
        return MultiPhysicsAnalysis(MultiPhysicsConfig(coupling_iterations=3, relaxation=0.5))

    def test_couple(self, ma):
        f = ma.run_fluid()
        t = ma.run_thermal()
        s = ma.run_structural()
        r = ma.couple(f, t, s)
        assert r["method"] == "partitioned_FSI"
        assert len(r["convergence"]) == 3

    def test_run_all(self, ma):
        r = ma.run_all()
        assert "fluid" in r
        assert "thermal" in r
        assert "structural" in r
        assert "coupled" in r

    def test_report(self, ma):
        ma.run_all()
        r = ma.report()
        assert "MULTI-PHYSICS" in r
        assert "FLUID" in r
        assert "THERMAL" in r
        assert "STRUCTURAL" in r
