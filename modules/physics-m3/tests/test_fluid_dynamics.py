"""Tests for fluid_dynamics.py — CFD & Aerodynamics Module."""
import numpy as np
import pytest
from modules.fluid_dynamics import (
    Airfoil, wind_profile, atmospheric_boundary_layer_height,
    reynolds_number, flow_regime, boundary_layer_thickness,
    bem_theory, betz_limit, wind_power_density, turbine_power,
)


class TestWindProfile:
    """wind_profile: power-law wind shear."""

    def test_import(self):
        assert wind_profile is not None

    def test_basic_profile(self):
        v = wind_profile(z_m=50, v_ref_ms=10, z_ref_m=10)
        assert v == pytest.approx(10 * (50 / 10) ** 0.14)
        assert v > 0

    def test_terrain_open(self):
        v_sub = wind_profile(z_m=10, v_ref_ms=10, z_ref_m=10, terrain="open")
        assert v_sub == pytest.approx(10.0)

    def test_terrain_suburban(self):
        v_sub = wind_profile(z_m=10, v_ref_ms=10, terrain="suburban")
        assert v_sub == pytest.approx(10.0 * (10 / 10) ** 0.22)

    def test_terrain_urban(self):
        v_sub = wind_profile(z_m=10, v_ref_ms=10, terrain="urban")
        assert v_sub == pytest.approx(10.0 * (10 / 10) ** 0.33)

    def test_unknown_terrain_falls_back_to_alpha(self):
        v = wind_profile(z_m=50, v_ref_ms=10, alpha=0.30, terrain="custom")
        assert v == pytest.approx(10 * (50 / 10) ** 0.30)


class TestAtmosphericBoundaryLayer:
    def test_heights(self):
        h = atmospheric_boundary_layer_height("open")
        assert h == 300
        h = atmospheric_boundary_layer_height("urban")
        assert h == 500

    def test_unknown_terrain(self):
        h = atmospheric_boundary_layer_height("unknown")
        assert h == 300  # default


class TestReynoldsNumber:
    def test_basic(self):
        Re = reynolds_number(velocity_ms=10, chord_m=0.3)
        assert Re == pytest.approx(10 * 0.3 / 1.516e-5)
        assert Re > 0

    def test_zero_velocity(self):
        assert reynolds_number(0, 0.3) == 0.0


class TestFlowRegime:
    def test_laminar(self):
        assert flow_regime(1000) == "laminar"
        assert flow_regime(1999) == "laminar"

    def test_transitional(self):
        assert flow_regime(2000) == "transitional"
        assert flow_regime(39999) == "transitional"

    def test_turbulent(self):
        assert flow_regime(40000) == "turbulent"
        assert flow_regime(1e6) == "turbulent"


class TestBoundaryLayerThickness:
    def test_returns_dict_with_expected_keys(self):
        bl = boundary_layer_thickness(x_m=0.5, Re_x=1e5)
        assert type(bl) == dict
        for key in ("laminar_delta_mm", "turbulent_delta_mm",
                    "displacement_thickness_mm", "momentum_thickness_mm"):
            assert key in bl

    def test_positive_thickness(self):
        bl = boundary_layer_thickness(x_m=1.0, Re_x=1e6)
        for v in bl.values():
            assert v > 0

    def test_laminar_larger_at_same_x(self):
        bl = boundary_layer_thickness(x_m=0.5, Re_x=1e4)
        assert bl["laminar_delta_mm"] > bl["displacement_thickness_mm"]


class TestAirfoil:
    def test_default_instantiation(self):
        af = Airfoil()
        assert af.name == "NACA0012"
        assert af.chord_m == 0.3

    def test_cl_alpha_zero(self):
        af = Airfoil()
        cl = af.cl_alpha(0)
        assert cl == pytest.approx(0.0, abs=1e-10)

    def test_cl_alpha_linear_region(self):
        af = Airfoil()
        cl_5 = af.cl_alpha(5)
        cl_10 = af.cl_alpha(10)
        assert cl_10 > cl_5 > 0

    def test_cl_alpha_stall(self):
        af = Airfoil()
        cl_high = af.cl_alpha(25)
        assert cl_high > 0

    def test_cd_alpha_zero(self):
        af = Airfoil()
        cd = af.cd_alpha(0)
        assert cd > 0  # profile drag always present

    def test_cd_increases_with_alpha(self):
        af = Airfoil()
        cd_0 = af.cd_alpha(0)
        cd_10 = af.cd_alpha(10)
        assert cd_10 > cd_0


class TestBEMTheory:
    def test_basic_bem(self):
        res = bem_theory(v_wind_ms=10, rpm=15, R_m=50)
        assert type(res) == dict
        assert res["TSR"] > 0
        assert res["power_W"] > 0
        assert res["thrust_N"] > 0

    def test_zero_wind_returns_zeros(self):
        res = bem_theory(v_wind_ms=0, rpm=15, R_m=50)
        assert res["TSR"] == 0
        assert res["power_W"] == 0

    def test_zero_rpm_returns_zeros(self):
        res = bem_theory(v_wind_ms=10, rpm=0, R_m=50)
        assert res["TSR"] == 0
        assert res["power_W"] == 0


class TestBetzLimit:
    def test_betz_value(self):
        assert betz_limit() == pytest.approx(16 / 27)

    def test_betz_lessthan_one(self):
        assert betz_limit() < 1.0


class TestWindPowerDensity:
    def test_basic(self):
        wpd = wind_power_density(v_ms=10)
        assert wpd == pytest.approx(0.5 * 1.225 * 1000)

    def test_cubic_dependence(self):
        wpd_10 = wind_power_density(10)
        wpd_20 = wind_power_density(20)
        assert wpd_20 == pytest.approx(8 * wpd_10)


class TestTurbinePower:
    def test_turbine_power_dict(self):
        res = turbine_power(v_wind_ms=10, R_m=50, Cp=0.40)
        assert type(res) == dict
        assert res["power_W"] > 0
        assert res["rotor_area_m2"] > 0

    def test_cp_efficiency(self):
        res = turbine_power(v_wind_ms=10, R_m=50, Cp=0.40)
        assert 0 < res["betz_efficiency_pct"] < 100

    def test_radius_scales_power(self):
        r1 = turbine_power(v_wind_ms=10, R_m=50)
        r2 = turbine_power(v_wind_ms=10, R_m=100)
        assert r2["power_W"] > r1["power_W"]
