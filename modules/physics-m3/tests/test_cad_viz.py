#!/usr/bin/env python3
"""Tests for upgraded CAD/Visualization module — 3D heat maps, M3, BL."""
import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))
import numpy as np

from cad_visualization import (
    AirfoilCoordinates, BladeGeometry, stress_color_map, beam_stress_diagram,
    HeatMap3D, M3Visualizer, StressField, BoundaryLayerView,
    LaminateView, WindRose, FailureEnvelope, geometry_to_stl,
    failure_envelope_points,
)


def test_airfoil():
    af = AirfoilCoordinates("NACA0012")
    x, y = af.coordinates()
    assert len(x) >= 50


def test_blade():
    b = BladeGeometry(length_m=1.5)
    assert len(b.blade_sections()) == b.n_sections


def test_stress_color():
    assert stress_color_map(10, 100) == "green"
    assert stress_color_map(85, 100) == "orange"
    assert stress_color_map(95, 100) == "red"


def test_beam_diagram():
    d = beam_stress_diagram(1.0, [100], [0.5])
    assert len(d["shear_N"]) == 100


def test_heatmap_scatter():
    x = np.random.rand(50) * 10
    y = np.random.rand(50) * 10
    z = np.random.rand(50) * 5
    vals = np.random.rand(50) * 100
    hm = HeatMap3D(x, y, z, vals)
    fig = hm.plot_scatter(title="Test")
    assert fig is not None


def test_heatmap_surface():
    x = np.linspace(0, 10, 20)
    y = np.linspace(0, 10, 20)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y) * 5
    C = np.abs(Z) * 10
    hm = HeatMap3D(X, Y, Z, C)
    fig = hm.plot_surface(title="Test Surface")
    assert fig is not None


def test_m3_visualizer():
    macro = {"temperature_C": 25, "humidity_pct": 65, "wind_speed_ms": 5}
    meso = {"layers": 3, "total_thickness_mm": 9.0, "angles": [0, 45, -45]}
    micro = {"Vf": 0.15, "voids": 0.05, "fiber_diameter_um": 15}
    mv = M3Visualizer(macro_data=macro, meso_data=meso, micro_data=micro)
    assert mv.macro_data["temperature_C"] == 25


def test_m3_plot():
    mv = M3Visualizer()
    fig = mv.plot(title="Test M3")
    assert fig is not None


def test_stress_field():
    nodes = np.random.rand(20, 3) * 10
    stress = np.random.rand(20) * 100
    sf = StressField(nodes, stress)
    fig = sf.plot(title="Test Stress")
    assert fig is not None


def test_boundary_layer():
    bl = BoundaryLayerView()
    fig = bl.plot()
    assert fig is not None


def test_failure_envelope():
    env = failure_envelope_points("tsai_wu", Xt=50, Xc=30, Yt=15, Yc=10, S=8)
    assert len(env["sigma_11"]) > 0


def test_laminate():
    lam = LaminateView()
    data = lam.stacking_data()
    assert data["n_layers"] > 0


def test_laminate_3d():
    lam = LaminateView()
    fig = lam.plot_3d()
    assert fig is not None


def test_wind_rose():
    wr = WindRose()
    data = wr.polar_data()
    assert len(data["theta"]) == 8


def test_wind_rose_plot():
    wr = WindRose()
    fig = wr.plot()
    assert fig is not None


def test_stl_export():
    verts = np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0]])
    faces = np.array([[0,1,2],[1,3,2]])
    tmp = tempfile.mktemp(suffix=".stl")
    geometry_to_stl(verts, faces, tmp)
    with open(tmp) as f:
        assert "solid" in f.read()
    os.unlink(tmp)


def test_register_path():
    from cad_visualization import _ensure_plots_dir
    path = _ensure_plots_dir()
    assert path.endswith("data/plots")
