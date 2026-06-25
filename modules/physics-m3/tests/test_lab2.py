#!/usr/bin/env python3
"""Tests for Physics M³ Workspace — Lab 2 Structural Design."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from structural_analysis import BeamSection, CompositeLaminate, PlyProperties
from structural_analysis import von_mises_stress, tsai_wu_failure, safety_factor
from fluid_dynamics import wind_profile, bem_theory, turbine_power, Airfoil
from thermodynamics import DryingProcess, carnot_efficiency
from electromechanical import PMSG, BatteryStorage, power_conversion_chain


def test_beam_bending():
    b = BeamSection(width_mm=50, height_mm=10, E_modulus_GPa=10)
    s = b.bending_stress(100)
    assert s > 0


def test_composite_laminate():
    lam = CompositeLaminate()
    lam.add_ply(PlyProperties(E1_GPa=10, E2_GPa=5, G12_GPa=2, nu12=0.3))
    abd = lam.ABD_matrix()
    assert abd["A"][0,0] > 0


def test_von_mises():
    vm = von_mises_stress(100, 50, txy=30)
    assert 95 < vm < 105


def test_tsai_wu():
    r = tsai_wu_failure(10, 5, 2, Xt=50, Xc=30, Yt=15, Yc=10, S=8)
    assert "failure_index" in r


def test_wind_profile():
    v = wind_profile(20, 6.0)
    assert v > 6.0


def test_bem():
    r = bem_theory(v_wind_ms=6, rpm=200, R_m=1.5)
    assert r["power_W"] > 0


def test_turbine_power():
    p = turbine_power(6, 1.5)
    assert p["power_W"] > 0


def test_drying():
    d = DryingProcess(mass_kg=1.0)
    assert d.total_energy_MJ() > 0


def test_carnot():
    eta = carnot_efficiency(500, 300)
    assert 0.3 < eta < 0.5


def test_pmsg():
    g = PMSG()
    assert g.efficiency(1500) > 80


def test_battery():
    b = BatteryStorage()
    assert b.energy_available_Wh() > 0


def test_power_conversion():
    c = power_conversion_chain(1000)
    assert c["total_efficiency_pct"] > 80
