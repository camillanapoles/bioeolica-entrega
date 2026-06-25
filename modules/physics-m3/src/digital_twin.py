"""
digital_twin.py — Digital Twin Simulation and Estimation Module
================================================================

Sensor data simulation (temperature, strain, vibration), Kalman filter
for state estimation, anomaly detection via residual-based thresholding,
remaining useful life (RUL) estimation, and model updating with
parameter correction.

Classes
-------
DigitalTwin : Core digital twin class for sensor fusion and prognosis.

Dependencies
------------
numpy, scipy (linalg, stats, signal)

Usage Example
-------------
>>> import numpy as np
>>> from modules.digital_twin import DigitalTwin
>>> dt = DigitalTwin(dt=0.01, process_noise=1e-4, measurement_noise=1e-2)
>>> t, temp = dt.simulate_sensor("temperature", duration=10.0, freq_noise_amp=0.5)
>>> state, cov = dt.kalman_update(temp[0], np.array([0.0]))
>>> anomaly = dt.detect_anomaly(temp[0], threshold=3.0)
>>> rul = dt.estimate_rul(current_degradation=0.3)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import linalg, signal, stats


class DigitalTwin:
    """Digital twin for real-time monitoring, state estimation, and prognosis.

    Simulates sensor data for temperature, strain, and vibration channels.
    Uses a linear Kalman filter for state estimation, residual-based
    anomaly detection, and empirical RUL estimation.

    Parameters
    ----------
    dt : float
        Sampling time step (seconds).
    process_noise : float
        Process noise covariance scaling factor Q.
    measurement_noise : float
        Measurement noise covariance scaling factor R.
    health_threshold : float
        Degradation threshold for end-of-life (default 1.0).
    """

    def __init__(
        self,
        dt: float = 0.01,
        process_noise: float = 1e-4,
        measurement_noise: float = 1e-2,
        health_threshold: float = 1.0,
    ) -> None:
        if dt <= 0.0:
            raise ValueError("Time step dt must be positive.")
        if process_noise <= 0.0 or measurement_noise <= 0.0:
            raise ValueError("Noise covariances must be positive.")

        self.dt = float(dt)
        self.Q = float(process_noise)
        self.R = float(measurement_noise)
        self.health_threshold = float(health_threshold)

        self._state: NDArray[np.float64] = np.zeros(2, dtype=np.float64)
        self._cov: NDArray[np.float64] = np.eye(2, dtype=np.float64) * 0.1
        self._t: float = 0.0
        self._residual_history: list[float] = []

    # ------------------------------------------------------------------
    # Sensor simulation
    # ------------------------------------------------------------------

    @staticmethod
    def _base_signal(
        t: NDArray[np.float64],
        mean: float,
        amplitude: float,
        frequency: float,
        noise_amp: float,
        trend: float = 0.0,
    ) -> NDArray[np.float64]:
        """Generate a base sinusoidal signal with noise."""
        signal_component: NDArray[np.float64] = mean + amplitude * np.sin(
            2.0 * np.pi * frequency * t
        )
        noise: NDArray[np.float64] = noise_amp * np.random.default_rng().normal(
            size=t.shape
        )
        trend_component: NDArray[np.float64] = trend * t
        return signal_component + noise + trend_component

    def simulate_sensor(
        self,
        sensor_type: str,
        duration: float = 10.0,
        freq_noise_amp: float = 0.5,
        fault_time: float | None = None,
        fault_severity: float = 2.0,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Simulate sensor time-series data for a given sensor type.

        Parameters
        ----------
        sensor_type : {"temperature", "strain", "vibration"}
            Type of sensor to simulate.
        duration : float
            Total simulation time (seconds).
        freq_noise_amp : float
            Amplitude of random noise.
        fault_time : float or None
            Time at which a fault/growth begins (None = no fault).
        fault_severity : float
            Severity multiplier for the fault signal.

        Returns
        -------
        tuple of NDArray
            (time_array, sensor_signal).
        """
        n_steps = max(2, int(duration / self.dt))
        t = np.linspace(0.0, duration, n_steps, dtype=np.float64)

        if sensor_type == "temperature":
            signal_val = self._base_signal(
                t, mean=50.0, amplitude=2.0, frequency=0.1, noise_amp=freq_noise_amp * 0.2
            )
        elif sensor_type == "strain":
            signal_val = self._base_signal(
                t, mean=200.0, amplitude=10.0, frequency=5.0, noise_amp=freq_noise_amp * 2.0
            )
        elif sensor_type == "vibration":
            # Vibration with multiple frequency components
            sig1: NDArray[np.float64] = 5.0 * np.sin(2.0 * np.pi * 30.0 * t)
            sig2: NDArray[np.float64] = 3.0 * np.sin(2.0 * np.pi * 60.0 * t)
            rng = np.random.default_rng()
            noise: NDArray[np.float64] = freq_noise_amp * rng.normal(size=t.shape)
            signal_val = sig1 + sig2 + noise
        else:
            raise ValueError(
                f"Unknown sensor type '{sensor_type}'. "
                f"Use 'temperature', 'strain', or 'vibration'."
            )

        # Inject fault (growing anomaly)
        if fault_time is not None:
            fault_idx = int(fault_time / self.dt)
            if fault_idx < len(t):
                growth: NDArray[np.float64] = fault_severity * np.maximum(
                    0.0, (t[fault_idx:] - t[fault_idx])
                )
                signal_val[fault_idx:] += growth

        return t, signal_val

    # ------------------------------------------------------------------
    # Kalman filter
    # ------------------------------------------------------------------

    def kalman_update(
        self,
        measurement: float,
        control_input: NDArray[np.float64] | None = None,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Perform one Kalman filter update step.

        Uses a linear kinematic model:
            x_{k+1} = F * x_k + B * u_k + w
            z_k = H * x_k + v

        where state = [position, velocity].

        Parameters
        ----------
        measurement : float
            Observed scalar measurement (position).
        control_input : NDArray or None
            Control input vector (2,) — default zeros.

        Returns
        -------
        tuple of NDArray
            (updated_state, updated_covariance).
        """
        # State transition
        dt = self.dt
        F: NDArray[np.float64] = np.array(
            [[1.0, dt], [0.0, 1.0]], dtype=np.float64
        )
        B: NDArray[np.float64] = np.array(
            [[0.5 * dt**2], [dt]], dtype=np.float64
        )
        H: NDArray[np.float64] = np.array([[1.0, 0.0]], dtype=np.float64)

        Q_mat: NDArray[np.float64] = np.eye(2, dtype=np.float64) * self.Q
        R_mat: NDArray[np.float64] = np.eye(1, dtype=np.float64) * self.R

        # Predict
        u = np.zeros(2, dtype=np.float64) if control_input is None else control_input
        x_pred: NDArray[np.float64] = F @ self._state + (B @ u[:1]).flatten()
        P_pred: NDArray[np.float64] = F @ self._cov @ F.T + Q_mat

        # Update
        y: NDArray[np.float64] = np.array([measurement], dtype=np.float64) - H @ x_pred
        S: NDArray[np.float64] = H @ P_pred @ H.T + R_mat
        K: NDArray[np.float64] = P_pred @ H.T @ linalg.inv(S)

        self._state = x_pred + (K @ y)
        self._cov = (np.eye(2, dtype=np.float64) - K @ H) @ P_pred

        # Store residual
        self._residual_history.append(float(np.abs(y[0])))

        return self._state.copy(), self._cov.copy()

    def get_state(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return current state estimate and covariance.

        Returns
        -------
        tuple of NDArray
            (state, covariance).
        """
        return self._state.copy(), self._cov.copy()

    def reset_state(
        self,
        state: NDArray[np.float64] | None = None,
        cov: NDArray[np.float64] | None = None,
    ) -> None:
        """Reset the filter state.

        Parameters
        ----------
        state : NDArray or None
            New state vector (default zeros).
        cov : NDArray or None
            New covariance matrix (default identity * 0.1).
        """
        self._state = np.zeros(2, dtype=np.float64) if state is None else state.copy()
        self._cov = (np.eye(2, dtype=np.float64) * 0.1) if cov is None else cov.copy()
        self._residual_history.clear()

    # ------------------------------------------------------------------
    # Anomaly detection
    # ------------------------------------------------------------------

    def detect_anomaly(
        self,
        measurement: float,
        threshold: float = 3.0,
    ) -> dict[str, Any]:
        """Detect anomalies via residual-based thresholding.

        Performs one Kalman update and compares the innovation residual
        (|z - H*x_pred|) against a threshold scaled by the innovation
        covariance.

        Parameters
        ----------
        measurement : float
            New measurement value.
        threshold : float
            Number of standard deviations for anomaly threshold.

        Returns
        -------
        dict
            Keys: 'is_anomaly' (bool), 'residual' (float),
            'threshold_value' (float), 'z_score' (float).
        """
        dt = self.dt
        F: NDArray[np.float64] = np.array([[1.0, dt], [0.0, 1.0]], dtype=np.float64)
        H: NDArray[np.float64] = np.array([[1.0, 0.0]], dtype=np.float64)

        x_pred: NDArray[np.float64] = F @ self._state
        P_pred: NDArray[np.float64] = F @ self._cov @ F.T + np.eye(2, dtype=np.float64) * self.Q

        y_res: NDArray[np.float64] = np.array([measurement], dtype=np.float64) - H @ x_pred
        S: NDArray[np.float64] = H @ P_pred @ H.T + np.eye(1, dtype=np.float64) * self.R
        innov_std: float = float(np.sqrt(S[0, 0]))

        residual = float(np.abs(y_res[0]))
        threshold_val = threshold * innov_std

        # Update state anyway
        K: NDArray[np.float64] = P_pred @ H.T @ linalg.inv(S)
        self._state = x_pred + (K @ y_res)
        self._cov = (np.eye(2, dtype=np.float64) - K @ H) @ P_pred
        self._residual_history.append(residual)

        return {
            "is_anomaly": residual > threshold_val,
            "residual": residual,
            "threshold_value": threshold_val,
            "z_score": residual / max(innov_std, 1e-12),
        }

    # ------------------------------------------------------------------
    # RUL estimation
    # ------------------------------------------------------------------

    def estimate_rul(
        self,
        current_degradation: float = 0.0,
        degradation_rate: float = 0.01,
        use_mc: bool = True,
        n_mc_samples: int = 1000,
    ) -> dict[str, float]:
        """Estimate remaining useful life based on degradation.

        Uses a simple linear degradation model with optional Monte Carlo
        uncertainty propagation.

        Parameters
        ----------
        current_degradation : float
            Current degradation level (0 = healthy, 1 = failed).
        degradation_rate : float
            Degradation rate per time unit (fraction/time).
        use_mc : bool
            If True, propagate uncertainty via Monte Carlo.
        n_mc_samples : int
            Number of Monte Carlo samples.

        Returns
        -------
        dict
            Keys: 'rul_mean', 'rul_std', 'rul_p10', 'rul_p90',
            'degradation_at_failure'.
        """
        if current_degradation < 0.0:
            raise ValueError("Degradation must be non-negative.")
        if current_degradation >= self.health_threshold:
            return {
                "rul_mean": 0.0,
                "rul_std": 0.0,
                "rul_p10": 0.0,
                "rul_p90": 0.0,
                "degradation_at_failure": current_degradation,
            }

        remaining = self.health_threshold - current_degradation

        if use_mc:
            rng = np.random.default_rng()
            rate_samples: NDArray[np.float64] = (
                degradation_rate * (1.0 + 0.2 * rng.normal(size=n_mc_samples))
            )
            rate_samples = np.maximum(rate_samples, 1e-12)
            rul_samples: NDArray[np.float64] = remaining / rate_samples
            return {
                "rul_mean": float(np.mean(rul_samples)),
                "rul_std": float(np.std(rul_samples)),
                "rul_p10": float(np.percentile(rul_samples, 10)),
                "rul_p90": float(np.percentile(rul_samples, 90)),
                "degradation_at_failure": self.health_threshold,
            }

        rul = remaining / max(degradation_rate, 1e-12)
        return {
            "rul_mean": rul,
            "rul_std": 0.0,
            "rul_p10": rul * 0.8,
            "rul_p90": rul * 1.2,
            "degradation_at_failure": self.health_threshold,
        }

    # ------------------------------------------------------------------
    # Model updating
    # ------------------------------------------------------------------

    def update_model(
        self,
        measured_output: NDArray[np.float64],
        predicted_output: NDArray[np.float64],
        sensitivity_matrix: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Update model parameters based on measured vs predicted output.

        Uses a weighted least-squares correction:
            delta_param = (J^T W J)^{-1} J^T W (y_meas - y_pred)

        Parameters
        ----------
        measured_output : NDArray
            Measured system output vector.
        predicted_output : NDArray
            Predicted system output vector (from model).
        sensitivity_matrix : NDArray
            Jacobian of outputs w.r.t. parameters (n_meas x n_param).

        Returns
        -------
        NDArray
            Parameter correction vector (delta_param).
        """
        residual: NDArray[np.float64] = measured_output - predicted_output
        J = np.asarray(sensitivity_matrix, dtype=np.float64)
        W: NDArray[np.float64] = np.eye(len(residual), dtype=np.float64) / self.R

        try:
            JT_W = J.T @ W
            delta: NDArray[np.float64] = linalg.solve(JT_W @ J, JT_W @ residual, assume_a="pos")
        except linalg.LinAlgError:
            # Fall back to pseudo-inverse
            delta = linalg.pinv(J) @ residual

        return delta


# ------------------------------------------------------------------
# Usage example
# ------------------------------------------------------------------
if __name__ == "__main__":
    import doctest

    doctest.testmod()

    dt = DigitalTwin(dt=0.01, process_noise=1e-4, measurement_noise=1e-2)

    print("Simulating temperature sensor (10 seconds)...")
    t, temp = dt.simulate_sensor("temperature", duration=10.0)
    print(f"  Temperature range: [{temp.min():.2f}, {temp.max():.2f}]")

    print("Running Kalman filter on first 100 samples...")
    for i in range(100):
        dt.kalman_update(temp[i])
    state, cov = dt.get_state()
    print(f"  State: {state}")
    print(f"  Covariance diagonal: {np.diag(cov)}")

    print("Detecting anomalies on measurement 101...")
    result = dt.detect_anomaly(temp[100], threshold=3.0)
    print(f"  Anomaly: {result['is_anomaly']} (residual={result['residual']:.4f})")

    print("Estimating RUL (degradation = 0.3)...")
    rul = dt.estimate_rul(current_degradation=0.3, degradation_rate=0.01)
    print(f"  RUL mean: {rul['rul_mean']:.2f} s, p10: {rul['rul_p10']:.2f}, p90: {rul['rul_p90']:.2f}")

    print("DigitalTwin module OK.")
