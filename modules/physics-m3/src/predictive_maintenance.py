"""Predictive maintenance — RUL estimation, anomaly detection, degradation models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class RULResult:
    """Remaining Useful Life estimation result."""
    rul: float
    confidence_upper: float
    confidence_lower: float
    degradation_rate: float
    failure_threshold: float
    method: str


class RULEstimator:
    """Remaining Useful Life estimation from degradation signals.

    Parameters
    ----------
    failure_threshold : float
        Signal value at which failure occurs.
    window : int
        Moving average window for smoothing.
    """

    def __init__(self, failure_threshold: float = 10.0, window: int = 5):
        self.failure_threshold = failure_threshold
        self.window = window
        self._history: list[float] = []
        self._time: list[float] = []

    def add_observation(self, value: float, time: float) -> None:
        """Add a sensor observation at a given time."""
        self._history.append(value)
        self._time.append(time)

    def estimate(self, method: str = "linear") -> RULResult:
        """Estimate remaining useful life.

        Parameters
        ----------
        method : str
            'linear', 'exponential', or 'wiener'.

        Returns
        -------
        RULResult
        """
        if len(self._history) < 3:
            return RULResult(0, 0, 0, 0, self.failure_threshold, method)

        y = np.array(self._history[-self.window:], dtype=float)
        t = np.array(self._time[-self.window:], dtype=float)

        if method == "exponential":
            log_y = np.log(np.maximum(y, 1e-10))
            coeffs = np.polyfit(t, log_y, 1)
            rate = coeffs[0]
            # Extrapolate: y(t) = exp(intercept + rate * t)
            if rate <= 0:
                return RULResult(float("inf"), float("inf"), 0, 0, self.failure_threshold, method)
            last_t = t[-1]
            last_y = np.exp(coeffs[1] + rate * last_t)
            t_fail = (np.log(self.failure_threshold) - coeffs[1]) / rate
        else:  # linear
            coeffs = np.polyfit(t, y, 1)
            rate = coeffs[0]
            if rate <= 0:
                return RULResult(float("inf"), float("inf"), 0, 0, self.failure_threshold, method)
            last_t = t[-1]
            last_y = coeffs[1] + rate * last_t
            t_fail = (self.failure_threshold - coeffs[1]) / rate

        rul = max(0, t_fail - last_t)
        # Confidence: ±20% or ±1 std of residuals
        residuals = y - (coeffs[1] + rate * t)
        std_res = max(np.std(residuals), 1e-6)
        ci = 0.2 * rul + 1.96 * std_res / abs(rate + 1e-6)

        return RULResult(
            rul=round(rul, 3),
            confidence_upper=round(rul + ci, 3),
            confidence_lower=round(max(0, rul - ci), 3),
            degradation_rate=round(rate, 6),
            failure_threshold=self.failure_threshold,
            method=method,
        )

    def reset(self) -> None:
        """Clear observation history."""
        self._history.clear()
        self._time.clear()

    @property
    def n_observations(self) -> int:
        return len(self._history)

    @property
    def current_value(self) -> Optional[float]:
        return self._history[-1] if self._history else None


class AnomalyDetector:
    """Anomaly detection for sensor data streams.

    Uses z-score thresholding and moving statistics.
    """

    def __init__(self, threshold: float = 3.0, window: int = 20):
        self.threshold = threshold
        self.window = window
        self._data: list[float] = []

    def add(self, value: float) -> None:
        self._data.append(value)

    def is_anomaly(self, value: float) -> bool:
        """Check if a value is anomalous based on recent history."""
        if len(self._data) < self.window:
            self._data.append(value)
            return False
        recent = np.array(self._data[-self.window:], dtype=float)
        mu, sigma = np.mean(recent), np.std(recent)
        if sigma < 1e-10:
            return False
        z = abs(value - mu) / sigma
        return z > self.threshold

    def anomalies(self) -> list[tuple[int, float, float]]:
        """Return list of (index, value, z_score) for all detected anomalies."""
        if len(self._data) < self.window:
            return []
        results = []
        for i in range(self.window, len(self._data)):
            recent = np.array(self._data[i - self.window:i], dtype=float)
            mu, sigma = np.mean(recent), np.std(recent)
            if sigma < 1e-10:
                continue
            z = abs(self._data[i] - mu) / sigma
            if z > self.threshold:
                results.append((i, self._data[i], round(z, 3)))
        return results

    @property
    def n_detected(self) -> int:
        return len(self.anomalies())

    @property
    def anomaly_rate(self) -> float:
        """Fraction of observations that are anomalous."""
        if len(self._data) < self.window + 1:
            return 0.0
        return self.n_detected / (len(self._data) - self.window)


class DegradationModel:
    """Physics-based degradation model using exponential or power-law.

    Parameters
    ----------
    model_type : str
        'exponential' or 'power_law'.
    initial_value : float
        Initial health value (1.0 = pristine).
    """

    def __init__(self, model_type: str = "exponential", initial_value: float = 1.0):
        self.model_type = model_type
        self.initial_value = initial_value
        self.params: dict[str, float] = {}

    def fit(self, time: np.ndarray, signal: np.ndarray) -> dict:
        """Fit degradation model to observed data.

        Parameters
        ----------
        time : (N,) array
            Observation times.
        signal : (N,) array
            Degradation signal values.

        Returns
        -------
        params : dict
            Fitted parameters.
        """
        t, s = np.asarray(time, dtype=float), np.asarray(signal, dtype=float)
        if self.model_type == "exponential":
            coeffs = np.polyfit(t, np.log(np.maximum(s, 1e-10)), 1)
            self.params = {"rate": coeffs[0], "intercept": coeffs[1]}
        else:  # power_law
            coeffs = np.polyfit(np.log(np.maximum(t, 1e-10)), np.log(np.maximum(s, 1e-10)), 1)
            self.params = {"exponent": coeffs[0], "intercept": coeffs[1]}
        return self.params

    def predict(self, t: np.ndarray) -> np.ndarray:
        """Predict degradation at given times."""
        if not self.params:
            return np.full_like(t, self.initial_value, dtype=float)
        if self.model_type == "exponential":
            return np.exp(self.params["intercept"] + self.params["rate"] * t)
        return np.exp(self.params["intercept"]) * (t ** self.params["exponent"])
