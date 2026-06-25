#!/usr/bin/env python3
"""Tests for Physics M³ Workspace — Lab 1 Material Characterization."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from m3_analysis import M3Analysis, PlyLayer
from composite_model import CompositeMaterial, FabricationProcess
from mechanical_tests import run_all_tests, flexure_test, tensile_test


def test_m3_analysis_run():
    a = M3Analysis("test")
    a.meso.add_layer(PlyLayer("core", thickness_mm=5, elastic_modulus_GPa=3))
    r = a.run()
    assert r["material"] == "test"
    assert r["meso"]["n_layers"] == 1
    assert r["meso"]["equivalent_modulus_GPa"] > 0


def test_composite_defaults():
    mat = CompositeMaterial()
    s = mat.summary()
    assert s["fiber"] is not None
    assert s["elastic"]["E1_longitudinal_GPa"] > 0
    assert s["strength"]["tensile_longitudinal_MPa"] > 0


def test_fabrication_energy():
    fab = FabricationProcess()
    e = fab.total_energy_kWh(0.5)
    assert e["total_kWh"] > 0


def test_mechanical_tests():
    E, st = 3.5, 50.0
    r = run_all_tests(E, st, length_mm=100, width_mm=25, thickness_mm=5)
    assert r["flexao"]["max_force_N"] > 0
    assert r["tracao"]["tensile_strength_MPa"] > 0
    assert r["compressao"]["compressive_strength_MPa"] > 0
    assert r["flambagem"]["critical_load_N"] > 0


def test_stress_strain_curve():
    r = flexure_test(3.5, 100, 25, 5, strength_MPa=50)
    assert len(r["stress_strain"]["stress_MPa"]) > 0
    assert len(r["stress_strain"]["strain_pct"]) > 0


def test_void_effect():
    mat1 = CompositeMaterial(void_fraction=0.02)
    mat2 = CompositeMaterial(void_fraction=0.15)
    assert mat1.estimate_strength()["tensile_longitudinal_MPa"] > \
           mat2.estimate_strength()["tensile_longitudinal_MPa"]
