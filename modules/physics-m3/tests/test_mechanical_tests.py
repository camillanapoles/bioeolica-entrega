"""Tests for mechanical_tests module — composit-domain API."""

import numpy as np
import pytest

from modules.mechanical_tests import (
    flexure_test, tensile_test, compression_test,
    buckling_test, impact_test, hardness_test,
)


def test_tensile_returns_dict():
    r = tensile_test(E_GPa=50, width_mm=10, thickness_mm=2, tensile_strength_MPa=100)
    assert type(r) == dict


def test_compression_returns_dict():
    r = compression_test(E_GPa=50, width_mm=10, thickness_mm=2, compressive_strength_MPa=80)
    assert type(r) == dict


def test_flexure_accepts_kwargs():
    r = flexure_test(E_GPa=50, length_mm=80, width_mm=10, thickness_mm=2, strength_MPa=80)
    assert type(r) == dict


def test_buckling_requires_length():
    r = buckling_test(E_GPa=50, length_mm=200, width_mm=10, thickness_mm=2)
    assert type(r) == dict
    assert "critical_load" in r or "load" in r or "buckling" in str(r).lower()


def test_impact_simple():
    r = impact_test(impact_energy_J=5.0, cross_section_mm2=100, material_toughness_kJm2=15)
    assert type(r) == dict


def test_hardness_simple():
    r = hardness_test(E_GPa=50, yield_strength_MPa=200, method='shore_d')
    assert type(r) == dict


def test_tensile_curve_length():
    r = tensile_test(E_GPa=50, width_mm=10, thickness_mm=2, tensile_strength_MPa=100, n_points=50)
    curve = r.get("curve", r.get("stress_strain", []))
    if isinstance(curve, (list, np.ndarray)):
        assert len(curve) == 50
