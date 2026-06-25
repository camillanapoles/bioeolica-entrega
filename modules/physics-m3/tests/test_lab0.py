#!/usr/bin/env python3
"""Tests for Physics M³ Workspace — Lab 0 CAD/Visualization."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from cad_visualization import (
    AirfoilCoordinates, BladeGeometry, LaminateView,
    WindRose, stress_color_map, beam_stress_diagram,
    geometry_to_stl, failure_envelope_points
)


def test_airfoil_coordinates():
    af = AirfoilCoordinates("NACA0012", chord_m=0.3)
    x, y = af.coordinates()
    assert len(x) == len(y) > 50


def test_blade_sections():
    b = BladeGeometry(length_m=1.5)
    sections = b.blade_sections()
    assert len(sections) == b.n_sections


def test_blade_surface():
    b = BladeGeometry()
    X, Y, Z = b.surface_points()
    assert len(X) > 0 and len(Y) > 0 and len(Z) > 0


def test_laminate_view():
    lam = LaminateView()
    data = lam.stacking_data()
    assert data["n_layers"] > 0
    assert data["total_thickness_mm"] > 0


def test_stress_color():
    assert stress_color_map(10, 100) == "green"
    assert stress_color_map(85, 100) == "orange"
    assert stress_color_map(95, 100) == "red"


def test_beam_diagram():
    d = beam_stress_diagram(1.0, [100], [0.5])
    assert len(d["x_m"]) == 100
    assert max(d["moment_Nm"]) > 0


def test_wind_rose():
    wr = WindRose()
    data = wr.polar_data()
    assert len(data["theta"]) == 8
    assert len(data["frequencies"]) == 8


def test_failure_envelope():
    env = failure_envelope_points("tsai_wu", Xt=50, Xc=30, Yt=15, Yc=10, S=8)
    assert "sigma_11" in env
    assert len(env["sigma_11"]) > 0
