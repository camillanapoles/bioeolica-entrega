"""
tests/test_digital_twin.py — Unit tests for the DigitalTwin module.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from modules.digital_twin import DigitalTwin


class TestDigitalTwin:
    """Test suite for DigitalTwin."""

    def test_initialization(self):
        """Test default initialization."""
        dt = DigitalTwin()
        assert dt.dt == pytest.approx(0.01)
        assert dt.Q == pytest.approx(1e-4)
        assert dt.R == pytest.approx(1e-2)
        assert dt.health_threshold == pytest.approx(1.0)

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        dt = DigitalTwin(dt=0.05, process_noise=1e-3, measurement_noise=5e-2)
        assert dt.dt == pytest.approx(0.05)
        assert dt.Q == pytest.approx(1e-3)
        assert dt.R == pytest.approx(5e-2)

    def test_invalid_dt_raises(self):
        """Test that non-positive dt raises ValueError."""
        with pytest.raises(ValueError, match="Time step dt must be positive"):
            DigitalTwin(dt=0.0)
        with pytest.raises(ValueError, match="Time step dt must be positive"):
            DigitalTwin(dt=-0.1)

    def test_invalid_noise_raises(self):
        """Test that non-positive noise raises ValueError."""
        with pytest.raises(ValueError, match="Noise covariances must be positive"):
            DigitalTwin(process_noise=0.0)
        with pytest.raises(ValueError, match="Noise covariances must be positive"):
            DigitalTwin(measurement_noise=-1e-4)

    def test_simulate_temperature(self):
        """Test temperature sensor simulation."""
        dt = DigitalTwin(dt=0.01)
        t, temp = dt.simulate_sensor("temperature", duration=5.0)
        assert len(t) == len(temp) > 0
        # Temperature should be around 50 C
        assert np.mean(temp) > 40.0
        assert np.mean(temp) < 60.0

    def test_simulate_strain(self):
        """Test strain sensor simulation."""
        dt = DigitalTwin(dt=0.01)
        t, strain = dt.simulate_sensor("strain", duration=2.0)
        assert len(strain) > 0
        # Strain should be around 200 microstrain
        assert np.mean(strain) > 150.0
        assert np.mean(strain) < 250.0

    def test_simulate_vibration(self):
        """Test vibration sensor simulation."""
        dt = DigitalTwin(dt=0.001)
        t, vib = dt.simulate_sensor("vibration", duration=0.1)
        assert len(vib) > 0
        # Vibration should have amplitude around 5+3=8 plus noise
        assert np.max(np.abs(vib)) > 5.0

    def test_unknown_sensor_raises(self):
        """Test that unknown sensor type raises ValueError."""
        dt = DigitalTwin()
        with pytest.raises(ValueError, match="Unknown sensor type"):
            dt.simulate_sensor("pressure", duration=1.0)

    def test_sensor_with_fault(self):
        """Test sensor simulation with injected fault."""
        dt = DigitalTwin(dt=0.01)
        t, temp = dt.simulate_sensor(
            "temperature", duration=10.0, fault_time=5.0, fault_severity=3.0
        )
        # After fault time, signal should increase
        pre_fault = temp[:400]
        post_fault = temp[600:]
        assert np.mean(post_fault) > np.mean(pre_fault)

    def test_kalman_update_state_convergence(self):
        """Test that Kalman filter converges toward measurement."""
        dt = DigitalTwin(dt=0.01, process_noise=1e-4, measurement_noise=1e-1)
        measurements = 5.0 * np.ones(50)
        for m in measurements:
            state, cov = dt.kalman_update(m)
        # State should be close to the constant measurement value
        assert abs(state[0] - 5.0) < 0.5

    def test_kalman_tracking(self):
        """Test Kalman filter tracking of a linear ramp."""
        dt = DigitalTwin(dt=0.01, process_noise=1e-2, measurement_noise=0.5)
        true_positions = np.linspace(0.0, 10.0, 100)
        for pos in true_positions:
            state, cov = dt.kalman_update(pos)
        # Final position should be near 10
        assert abs(state[0] - 10.0) < 2.0

    def test_get_state(self):
        """Test get_state returns current state and covariance."""
        dt = DigitalTwin()
        state, cov = dt.get_state()
        assert state.shape == (2,)
        assert cov.shape == (2, 2)
        assert np.allclose(state, 0.0)

    def test_reset_state(self):
        """Test reset_state clears and reinitializes."""
        dt = DigitalTwin()
        dt.kalman_update(3.0)
        dt.reset_state()
        state, _ = dt.get_state()
        assert np.allclose(state, 0.0)
        assert len(dt._residual_history) == 0

    def test_detect_anomaly_normal(self):
        """Test anomaly detection on normal signal."""
        dt = DigitalTwin(dt=0.01, process_noise=1e-3, measurement_noise=1.0)
        t, sig = dt.simulate_sensor("temperature", duration=2.0)
        for m in sig[:20]:
            result = dt.detect_anomaly(m, threshold=3.0)
        # Normal signal should not trigger anomaly
        assert "is_anomaly" in result
        assert "residual" in result
        assert "z_score" in result

    def test_detect_anomaly_outlier(self):
        """Test anomaly detection catches large outlier."""
        dt = DigitalTwin(dt=0.01, process_noise=1e-6, measurement_noise=0.1)
        # Initialize on normal data
        for _ in range(10):
            dt.kalman_update(0.0)
        # Large outlier should be detected
        result = dt.detect_anomaly(100.0, threshold=3.0)
        assert result["is_anomaly"] == True
        assert result["z_score"] > 3.0

    def test_estimate_rul_healthy(self):
        """Test RUL estimation for healthy system."""
        dt = DigitalTwin()
        result = dt.estimate_rul(
            current_degradation=0.2, degradation_rate=0.01, use_mc=True
        )
        assert result["rul_mean"] > 0.0
        assert result["rul_std"] > 0.0
        assert result["rul_p10"] < result["rul_p90"]

    def test_estimate_rul_failed(self):
        """Test RUL estimation for already-failed system."""
        dt = DigitalTwin()
        result = dt.estimate_rul(
            current_degradation=1.5, degradation_rate=0.01
        )
        assert result["rul_mean"] == pytest.approx(0.0)

    def test_estimate_rul_deterministic(self):
        """Test RUL estimation without Monte Carlo."""
        dt = DigitalTwin()
        result = dt.estimate_rul(
            current_degradation=0.5, degradation_rate=0.02, use_mc=False
        )
        # remaining = 0.5, rate = 0.02 => 25 time units
        assert result["rul_mean"] > 0.0
        assert result["rul_std"] == pytest.approx(0.0)

    def test_update_model(self):
        """Test model parameter update via least-squares."""
        dt = DigitalTwin()
        measured = np.array([1.0, 2.0], dtype=np.float64)
        predicted = np.array([1.1, 1.8], dtype=np.float64)
        J = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float64)
        delta = dt.update_model(measured, predicted, J)
        assert delta.shape == (2,)
        assert not np.any(np.isnan(delta))

    def test_update_model_singular(self):
        """Test model update with singular matrix (fallback to pinv)."""
        dt = DigitalTwin()
        measured = np.array([1.0, 2.0], dtype=np.float64)
        predicted = np.array([0.9, 2.2], dtype=np.float64)
        J = np.array([[1.0], [0.0]], dtype=np.float64)  # 2 meas, 1 param
        delta = dt.update_model(measured, predicted, J)
        assert not np.any(np.isnan(delta))
