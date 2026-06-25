"""
Module for comparing simulation results with experimental data using
quantitative metrics.

Provides the :class:`SimulationComparison` class, which stores paired
simulation/experimental data arrays and computes standard error and
goodness-of-fit metrics (RMSE, MAE, R2, max error, relative error,
Pearson correlation) along with matplotlib visualisations.

Typical usage::

    sc = SimulationComparison()
    sc.add_pair("case_01", sim_x, sim_y, exp_x, exp_y, exp_y_err=std_y)
    metrics = sc.all_metrics("case_01")
    print(sc.report())
"""

from __future__ import annotations

__all__ = ["SimulationComparison"]

from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _to_array(v, name: str) -> np.ndarray:
    """Convert *v* to a 1-D float64 array or raise."""
    a = np.asarray(v, dtype=np.float64).ravel()
    if a.ndim != 1 or a.size == 0:
        raise ValueError(f"{name} must be a non-empty 1-D sequence")
    return a


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class SimulationComparison:
    """Accumulate simulation-vs-experiment pairs and compute metrics.

    Each pair is stored under a user-provided *name* (key) and consists of
    the abscissae and ordinates for both simulation and experimental data.
    Experimental uncertainties (standard errors) are optional.

    Examples
    --------
    >>> sc = SimulationComparison()
    >>> sc.add_pair("beam_deflection", [0,1,2], [0,0.5,2],
    ...              [0,1,2], [0,0.48,2.1], exp_y_err=[0.01,0.02,0.02])
    >>> sc.rmse("beam_deflection")
    0.0707...
    """

    def __init__(self) -> None:
        self._pairs: Dict[str, dict] = {}

    # -- Pair management ---------------------------------------------------

    def add_pair(
        self,
        name: str,
        sim_x: Sequence[float],
        sim_y: Sequence[float],
        exp_x: Sequence[float],
        exp_y: Sequence[float],
        exp_y_err: Optional[Sequence[float]] = None,
    ) -> None:
        """Register a simulation/experiment data pair.

        Parameters
        ----------
        name : str
            Identifier for this pair.  Overwrites any previously registered
            pair with the same name.
        sim_x : array-like, 1-D
            Abscissa (independent variable) for simulation data.
        sim_y : array-like, 1-D
            Ordinate (dependent variable) for simulation data.
        exp_x : array-like, 1-D
            Abscissa for experimental / reference data.
        exp_y : array-like, 1-D
            Ordinate for experimental / reference data.
        exp_y_err : array-like, 1-D, optional
            Standard uncertainty (e.g. standard deviation) associated with
            each experimental ordinate.

        Raises
        ------
        ValueError
            If any of the inputs are empty or not 1-D.
        """
        self._pairs[name] = {
            "sim_x": _to_array(sim_x, "sim_x"),
            "sim_y": _to_array(sim_y, "sim_y"),
            "exp_x": _to_array(exp_x, "exp_x"),
            "exp_y": _to_array(exp_y, "exp_y"),
            "exp_y_err": (
                None
                if exp_y_err is None
                else _to_array(exp_y_err, "exp_y_err")
            ),
        }

    def _get(self, name: str) -> dict:
        if name not in self._pairs:
            raise KeyError(
                f"No pair registered under '{name}'. "
                f"Available: {list(self._pairs)}"
            )
        return self._pairs[name]

    def _projected(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        """Project simulation y onto experimental x via linear interpolation.

        Returns
        -------
        sim_on_exp : ndarray
            Simulated ordinates evaluated at experimental abscissae.
        exp_y : ndarray
            Experimental ordinates.
        """
        p = self._get(name)
        sim_on_exp = np.interp(p["exp_x"], p["sim_x"], p["sim_y"])
        return sim_on_exp, p["exp_y"]

    # -- Per-metric methods ------------------------------------------------

    def rmse(self, name: str) -> float:
        """Root mean square error.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            :math:`\\sqrt{ \\frac{1}{n} \\sum (y_{\\text{sim}} -
            y_{\\text{exp}})^2 }`.
        """
        s, e = self._projected(name)
        return float(np.sqrt(np.mean((s - e) ** 2)))

    def mae(self, name: str) -> float:
        """Mean absolute error.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            :math:`\\frac{1}{n} \\sum |y_{\\text{sim}} - y_{\\text{exp}}|`.
        """
        s, e = self._projected(name)
        return float(np.mean(np.abs(s - e)))

    def r2(self, name: str) -> float:
        """Coefficient of determination (R-squared).

        Uses the experimental mean as the baseline model.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            :math:`R^2 = 1 - \\frac{\\sum (y_{\\text{sim}} - y_{\\text{exp}})^2}
            {\\sum (y_{\\text{exp}} - \\bar{y}_{\\text{exp}})^2}`.

        Notes
        -----
        Values may be negative when the simulation is a worse predictor than
        the constant experimental mean.
        """
        s, e = self._projected(name)
        ss_res = np.sum((s - e) ** 2)
        ss_tot = np.sum((e - np.mean(e)) ** 2)
        if ss_tot == 0.0:
            return float("nan")
        return float(1.0 - ss_res / ss_tot)

    def max_error(self, name: str) -> float:
        """Maximum absolute error.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            :math:`\\max |y_{\\text{sim}} - y_{\\text{exp}}|`.
        """
        s, e = self._projected(name)
        return float(np.max(np.abs(s - e)))

    def relative_error(self, name: str) -> float:
        """Mean absolute relative error in percent.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            :math:`\\frac{100}{n} \\sum
            \\left| \\frac{y_{\\text{sim}} - y_{\\text{exp}}}{y_{\\text{exp}}}
            \\right|`.

        Notes
        -----
        Zero-valued experimental ordinates are omitted to avoid division by
        zero; the function emits a warning when this occurs.
        """
        s, e = self._projected(name)
        mask = e != 0.0
        if not np.all(mask):
            import warnings

            warnings.warn(
                f"relative_error('{name}'): {int(np.sum(~mask))} "
                "zero-valued experimental ordinates were excluded."
            )
        if mask.sum() == 0:
            return float("nan")
        return float(100.0 * np.mean(np.abs((s[mask] - e[mask]) / e[mask])))

    def correlation(self, name: str) -> float:
        """Pearson product-moment correlation coefficient.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        float
            Correlation coefficient in [-1, 1].  Returns NaN if either series
            has zero variance.
        """
        s, e = self._projected(name)
        return float(np.corrcoef(s, e)[0, 1])

    def all_metrics(self, name: str) -> Dict[str, float]:
        """Return a dictionary of every available metric for *name*.

        Parameters
        ----------
        name : str
            Pair identifier.

        Returns
        -------
        dict
            Keys: ``rmse``, ``mae``, ``r2``, ``max_error``,
            ``relative_error``, ``correlation``.
        """
        return {
            "rmse": self.rmse(name),
            "mae": self.mae(name),
            "r2": self.r2(name),
            "max_error": self.max_error(name),
            "relative_error": self.relative_error(name),
            "correlation": self.correlation(name),
        }

    # -- Plotting -----------------------------------------------------------

    def plot_comparison(
        self,
        name: str,
        title: Optional[str] = None,
    ) -> None:
        """Plot simulation vs. experimental data as an overlay.

        Parameters
        ----------
        name : str
            Pair identifier.
        title : str, optional
            Plot title.  Defaults to ``"Comparison: {name}"``.

        Notes
        -----
        Requires ``matplotlib``.  The experimental data is plotted as markers
        with error bars (if *exp_y_err* was provided); the simulation is
        plotted as a solid line.

        Raises
        ------
        ImportError
            If ``matplotlib`` is not available.
        """
        import matplotlib.pyplot as plt  # fmt: skip

        p = self._get(name)
        title = title or f"Comparison: {name}"

        fig, ax = plt.subplots()
        ax.plot(p["sim_x"], p["sim_y"], "-", label="Simulation")
        ax.errorbar(
            p["exp_x"],
            p["exp_y"],
            yerr=p["exp_y_err"],
            fmt="o",
            capsize=3,
            label="Experimental",
        )
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(title)
        ax.legend()
        plt.show()

    def plot_residuals(self, name: str) -> None:
        """Plot residuals (simulation - experiment) vs. experimental x.

        Parameters
        ----------
        name : str
            Pair identifier.

        Notes
        -----
        Requires ``matplotlib``.  A horizontal dashed line at zero is drawn
        for reference.

        Raises
        ------
        ImportError
            If ``matplotlib`` is not available.
        """
        import matplotlib.pyplot as plt  # fmt: skip

        p = self._get(name)
        sim_on_exp, exp_y = self._projected(name)
        residuals = sim_on_exp - exp_y

        fig, ax = plt.subplots()
        ax.errorbar(
            p["exp_x"],
            residuals,
            yerr=p["exp_y_err"],
            fmt="o",
            capsize=3,
        )
        ax.axhline(0, color="gray", linestyle="--")
        ax.set_xlabel("x")
        ax.set_ylabel("Residual (sim - exp)")
        ax.set_title(f"Residuals: {name}")
        plt.show()

    # -- Report -------------------------------------------------------------

    def report(self, names: Optional[Sequence[str]] = None) -> str:
        """Return a multi-line formatted report.

        Parameters
        ----------
        names : list of str, optional
            Subset of pairs to report.  Defaults to all registered pairs.

        Returns
        -------
        str
            Formatted text table.
        """
        if names is None:
            names = list(self._pairs)

        lines = [
            f"{'Name':<20} {'RMSE':>10} {'MAE':>10} {'R2':>8} "
            f"{'MaxErr':>10} {'RelErr%':>8} {'Corr':>6}"
        ]
        lines.append("-" * 76)

        for n in names:
            m = self.all_metrics(n)
            lines.append(
                f"{n:<20} {m['rmse']:>10.4f} {m['mae']:>10.4f} "
                f"{m['r2']:>8.4f} {m['max_error']:>10.4f} "
                f"{m['relative_error']:>8.2f} {m['correlation']:>6.4f}"
            )
        return "\n".join(lines)
