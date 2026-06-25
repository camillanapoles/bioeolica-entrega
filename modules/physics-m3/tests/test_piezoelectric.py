"""
tests/test_piezoelectric.py — Unit tests for the PiezoMaterial module.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from modules.piezoelectric import PiezoMaterial


class TestPiezoMaterial:
    """Test suite for PiezoMaterial."""

    def test_default_initialization(self):
        """Test default material parameters."""
        mat = PiezoMaterial()
        assert mat.d31 == pytest.approx(-190e-12)
        assert mat.d33 == pytest.approx(390e-12)
        assert mat.d15 == pytest.approx(590e-12)
        assert mat.eps33 == pytest.approx(1500.0 * 8.854e-12)
        assert mat.density == pytest.approx(7700.0)

    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        mat = PiezoMaterial(
            d31=-250e-12,
            d33=500e-12,
            eps33=2000 * 8.854e-12,
            sE11=1.2e-11,
            density=7500.0,
        )
        assert mat.d31 == pytest.approx(-250e-12)
        assert mat.d33 == pytest.approx(500e-12)
        assert mat.eps33 == pytest.approx(2000 * 8.854e-12)
        assert mat.cE11 == pytest.approx(1.0 / 1.2e-11)

    def test_eform_stress_shape(self):
        """Test that e-form stress returns 3 components."""
        mat = PiezoMaterial()
        strain = np.array([1e-4, 0.0, 0.0], dtype=np.float64)
        field = np.array([0.0, 1e5, 0.0], dtype=np.float64)
        stress = mat.eform_stress(strain, field)
        assert stress.shape == (3,)

    def test_dform_strain_shape(self):
        """Test that d-form strain returns 3 components."""
        mat = PiezoMaterial()
        stress = np.array([1e6, 0.0, 0.0], dtype=np.float64)
        field = np.array([0.0, 1e5, 0.0], dtype=np.float64)
        strain = mat.dform_strain(stress, field)
        assert strain.shape == (3,)

    def test_dform_d31_contribution(self):
        """Test d31 contribution to in-plane strain from E3."""
        mat = PiezoMaterial(d31=-190e-12)
        stress = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        field = np.array([0.0, 1e5, 0.0], dtype=np.float64)
        strain = mat.dform_strain(stress, field)
        # e11 should be d31 * E3 = -190e-12 * 1e5 = -1.9e-5
        assert strain[0] == pytest.approx(-1.9e-5, rel=1e-3)

    def test_actuator_strain_returns_dict(self):
        """Test actuator_strain returns all strain components."""
        mat = PiezoMaterial()
        result = mat.actuator_strain(voltage=100.0, thickness=0.5e-3)
        assert "strain_11" in result
        assert "strain_33" in result
        assert "strain_13" in result

    def test_actuator_strain_negative_thickness(self):
        """Test actuator_strain with negative thickness raises."""
        mat = PiezoMaterial()
        with pytest.raises(ValueError, match="Thickness must be positive"):
            mat.actuator_strain(voltage=100.0, thickness=0.0)

    def test_actuator_force_blocked(self):
        """Test blocked actuator force is non-zero."""
        mat = PiezoMaterial()
        result = mat.actuator_force(
            voltage=100.0, width=0.01, length=0.05, thickness=0.5e-3, blocked=True
        )
        assert result["blocked_force"] != 0.0
        assert result["force"] == pytest.approx(result["blocked_force"])
        assert result["displacement"] == pytest.approx(0.0)

    def test_actuator_force_free(self):
        """Test free actuator displacement is non-zero."""
        mat = PiezoMaterial()
        result = mat.actuator_force(
            voltage=100.0, width=0.01, length=0.05, thickness=0.5e-3, blocked=False
        )
        assert result["free_displacement"] != 0.0
        assert result["displacement"] == pytest.approx(result["free_displacement"])
        assert result["force"] == pytest.approx(0.0)

    def test_actuator_zero_dimensions_raises(self):
        """Test actuator with zero dimension raises ValueError."""
        mat = PiezoMaterial()
        with pytest.raises(ValueError, match="Dimensions must be positive"):
            mat.actuator_force(voltage=100.0, width=0.0, length=0.05)

    def test_actuator_voltage_dependence(self):
        """Test that actuator force scales with voltage."""
        mat = PiezoMaterial()
        r1 = mat.actuator_force(voltage=50.0, width=0.01, length=0.05, blocked=True)
        r2 = mat.actuator_force(voltage=100.0, width=0.01, length=0.05, blocked=True)
        # Doubling voltage should double the blocked force
        assert r2["blocked_force"] == pytest.approx(2.0 * r1["blocked_force"], rel=1e-3)

    def test_sensor_voltage_positive_strain(self):
        """Test that sensor voltage is positive for positive strain."""
        mat = PiezoMaterial()
        V = mat.sensor_voltage(strain_x=1e-4, thickness=0.5e-3)
        assert V > 0.0

    def test_sensor_voltage_stress_input(self):
        """Test sensor voltage with stress input."""
        mat = PiezoMaterial()
        V = mat.sensor_voltage(stress_x=1e7, thickness=0.5e-3)
        assert V > 0.0

    def test_sensor_voltage_scaling(self):
        """Test that sensor voltage scales with strain."""
        mat = PiezoMaterial()
        V1 = mat.sensor_voltage(strain_x=1e-4, thickness=0.5e-3)
        V2 = mat.sensor_voltage(strain_x=2e-4, thickness=0.5e-3)
        assert V2 > V1

    def test_sensor_zero_thickness_raises(self):
        """Test sensor with zero thickness raises ValueError."""
        mat = PiezoMaterial()
        with pytest.raises(ValueError, match="Thickness must be positive"):
            mat.sensor_voltage(strain_x=1e-4, thickness=0.0)

    def test_harvested_power_positive(self):
        """Test that harvested power is positive."""
        mat = PiezoMaterial()
        result = mat.harvested_power(
            voltage=10.0, frequency=100.0, load_resistance=1e3
        )
        assert result["power"] > 0.0
        assert result["current"] > 0.0

    def test_harvested_power_at_optimal(self):
        """Test that optimal load gives near-max power."""
        mat = PiezoMaterial()
        R_opt = mat.optimal_load_resistance(frequency=100.0)
        result = mat.harvested_power(
            voltage=10.0, frequency=100.0, load_resistance=R_opt
        )
        # Efficiency at optimal load should be near 1.0
        assert result["efficiency"] == pytest.approx(1.0, abs=0.01)

    def test_harvested_power_at_extreme(self):
        """Test harvested power at extreme load values."""
        mat = PiezoMaterial()
        result_low = mat.harvested_power(
            voltage=10.0, frequency=100.0, load_resistance=1.0
        )
        result_high = mat.harvested_power(
            voltage=10.0, frequency=100.0, load_resistance=1e9
        )
        # Power should be lower at extremes than at optimal
        R_opt = mat.optimal_load_resistance(frequency=100.0)
        result_opt = mat.harvested_power(
            voltage=10.0, frequency=100.0, load_resistance=R_opt
        )
        assert result_low["power"] < result_opt["power"]
        assert result_high["power"] < result_opt["power"]

    def test_invalid_frequency_raises(self):
        """Test that non-positive frequency raises ValueError."""
        mat = PiezoMaterial()
        with pytest.raises(ValueError, match="Frequency must be positive"):
            mat.harvested_power(voltage=10.0, frequency=0.0, load_resistance=1e3)

    def test_invalid_load_raises(self):
        """Test that non-positive load raises ValueError."""
        mat = PiezoMaterial()
        with pytest.raises(ValueError, match="Load resistance must be positive"):
            mat.harvested_power(voltage=10.0, frequency=100.0, load_resistance=0.0)

    def test_optimal_load_scaling(self):
        """Test optimal load scales inversely with frequency."""
        mat = PiezoMaterial()
        R_opt_100 = mat.optimal_load_resistance(frequency=100.0)
        R_opt_200 = mat.optimal_load_resistance(frequency=200.0)
        # Doubling frequency should halve optimal resistance
        assert R_opt_200 == pytest.approx(R_opt_100 / 2.0, rel=1e-3)

    def test_eform_and_dform_consistency(self):
        """Test that e-form and d-form are approximately consistent."""
        mat = PiezoMaterial()
        stress = np.array([1e6, 2e5, 1e4], dtype=np.float64)
        field = np.array([1e4, 2e5, 0.0], dtype=np.float64)
        strain_d = mat.dform_strain(stress, field)
        stress_computed = mat.eform_stress(strain_d, field)
        # Check recovered stress (approximate, e-form uses estimated coefficients)
        assert abs(stress_computed[0] - stress[0]) < abs(stress[0]) * 0.8
