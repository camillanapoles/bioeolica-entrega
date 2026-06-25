#!/usr/bin/env python3
"""Tests for normativo.py — Standards Compliance Checker."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import numpy as np
from normativo import (
    StandardsCheck,
    check_astm_d790,
    check_astm_d3039,
    check_astm_d3410,
    check_iec_61400,
    check_iso_61400,
    check_nbr_6123,
    run_all_checks,
)


def test_astm_d790_pass():
    """ASTM D790 should pass for a material exceeding all minimums."""
    result = check_astm_d790(
        flexural_modulus_GPa=5.0,
        flexural_strength_MPa=50.0,
        span_mm=80, thickness_mm=5, width_mm=25,
    )
    assert result["overall"] == "PASS", f"Expected PASS, got {result['overall']}"
    checks = result["checks"]
    assert checks["span_to_thickness_ratio"]["passed"] == True
    assert checks["flexural_modulus"]["passed"] == True
    assert checks["flexural_strength"]["passed"] == True


def test_astm_d790_fail():
    """ASTM D790 should FAIL for material below strength minimum."""
    result = check_astm_d790(
        flexural_modulus_GPa=0.5,
        flexural_strength_MPa=2.0,
        span_mm=80, thickness_mm=5, width_mm=25,
    )
    assert result["overall"] == "FAIL", f"Expected FAIL, got {result['overall']}"
    assert result["checks"]["flexural_modulus"]["passed"] is False
    assert result["checks"]["flexural_strength"]["passed"] is False


def test_astm_d3039_pass():
    """ASTM D3039 should pass for valid tensile specimen."""
    result = check_astm_d3039(
        tensile_modulus_GPa=3.0, tensile_strength_MPa=40.0,
        elongation_pct=1.2, width_mm=25, thickness_mm=5,
    )
    assert result["overall"] == "PASS"
    assert result["checks"]["tensile_modulus"]["passed"] == True
    assert result["checks"]["tensile_strength"]["passed"] == True


def test_astm_d3039_elongation_fail():
    """ASTM D3039 should fail if elongation exceeds standard max."""
    result = check_astm_d3039(
        tensile_modulus_GPa=5.0, tensile_strength_MPa=50.0,
        elongation_pct=5.0, width_mm=25, thickness_mm=5,
    )
    assert result["overall"] == "FAIL"
    assert result["checks"]["elongation"]["passed"] is False


def test_astm_d3410_pass():
    """ASTM D3410 should pass for valid compression specimen."""
    result = check_astm_d3410(
        compressive_modulus_GPa=3.0, compressive_strength_MPa=20.0,
        gage_length_mm=20.0,
    )
    assert result["overall"] == "PASS"


def test_iec_61400_pass():
    """IEC 61400-2 should pass for a valid small wind turbine."""
    result = check_iec_61400(
        rotor_diameter_m=2.5, rated_power_W=500,
        annual_avg_wind_ms=6.0, safety_class="III",
        tower_height_m=6.0,
    )
    assert result["overall"] == "PASS", f"Expected PASS, got {result['overall']}"


def test_iec_61400_invalid_class():
    """IEC 61400-2 should return error for unknown safety class."""
    result = check_iec_61400(
        rotor_diameter_m=2.5, rated_power_W=500,
        annual_avg_wind_ms=6.0, safety_class="INVALID",
    )
    assert result["overall"] == "FAIL"
    assert "error" in result


def test_iso_61400_deflection_fail():
    """ISO 61400-1 should fail if blade deflection exceeds limit."""
    result = check_iso_61400(
        tower_height_m=30.0, max_blade_deflection_m=2.0,
        blade_length_m=10.0, safety_class="normal",
    )
    assert result["overall"] == "FAIL"
    assert result["checks"]["tip_deflection"]["passed"] is False


def test_nbr_6123_wind_loads():
    """ABNT NBR 6123 should compute characteristic wind speed correctly."""
    result = check_nbr_6123(
        height_m=15.0, terrain_category="B",
        basic_velocity_ms=35.0, gust_factor=2.0,
    )
    assert result["overall"] == "PASS"
    assert result["Vk_ms"] > 0
    assert result["dynamic_pressure_Pa"] > 200


def test_nbr_6123_invalid_terrain():
    """ABNT NBR 6123 should error for unknown terrain category."""
    result = check_nbr_6123(
        height_m=10.0, terrain_category="X",
        basic_velocity_ms=35.0,
    )
    assert "error" in result
    assert result["overall"] == "FAIL"


def test_standards_check_class():
    """StandardsCheck class should accumulate results correctly."""
    sc = StandardsCheck(
        material="test_composite",
        E_modulus_GPa=5.0, tensile_MPa=40.0,
        flexural_MPa=35.0, compressive_MPa=20.0,
    )
    sc.check_astm_d790()
    sc.check_astm_d3039()
    sc.check_astm_d3410()
    sc.check_iec_61400()
    sc.check_nbr_6123()

    summary = sc.summary()
    assert summary["checks_performed"] >= 5
    assert summary["passed"] >= 1
    assert summary["compliance_score_pct"] > 0


def test_standards_check_summary():
    """StandardsCheck summary should report overall status correctly."""
    sc = StandardsCheck(material="failing", E_modulus_GPa=0.1, tensile_MPa=0.5)
    sc.check_astm_d790()
    sc.check_astm_d3039()
    summary = sc.summary()
    assert summary["overall"] == "FAIL"
    assert summary["failed"] > 0


def test_run_all_checks():
    """run_all_checks convenience function should return valid summary."""
    summary = run_all_checks(
        E_modulus_GPa=5.0, tensile_MPa=50.0,
        flexural_MPa=45.0, compressive_MPa=25.0,
    )
    assert summary["checks_performed"] >= 6
    assert "material" in summary
    assert summary["compliance_score_pct"] > 0
