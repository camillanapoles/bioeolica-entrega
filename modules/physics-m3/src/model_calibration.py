#!/usr/bin/env python3
"""
Model Calibration Module — Constitutive Parameter Estimation from Experimental Data.

Calibrates constitutive model parameters to fit experimental measurements using
optimization and uncertainty quantification methods. Supports least-squares fitting,
Monte Carlo uncertainty propagation, and Bayesian MCMC sampling.

Features:
  - Nonlinear least-squares fitting via scipy.optimize (trust-region reflective,
    Levenberg-Marquardt, differential evolution)
  - Monte Carlo calibration with resampled experimental noise for uncertainty bounds
  - Bayesian MCMC sampling via emcee (optional dependency; falls back to Monte Carlo)
  - Goodness-of-fit metrics (RMSE, R², AIC, BIC, reduced chi-squared)
  - Holdout validation and prediction with uncertainty bands
  - Visualization: fitted curves with confidence envelopes, corner plots

Usage:
    >>> import numpy as np
    >>> def my_model(params, x):
    ...     E, nu = params
    ...     return E * x**2 + nu * x
    >>> x_data = np.linspace(0, 1, 20)
    >>> y_data = 2.5 * x_data**2 + 0.3 * x_data + 0.05 * np.random.randn(20)
    >>> mc = ModelCalibration(my_model, ["E", "nu"], [1.0, 0.1])
    >>> mc.set_experimental_data(x_data, y_data)
    >>> mc.calibrate(method="least_squares")
    >>> print(mc.results())

References
----------
  - scipy.optimize.least_squares : https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html
  - emcee : The MCMC Hammer (Foreman-Mackey et al. 2013)
  - D7 Quality Metrics (KDI) : numerical precision targets per method
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple, Any, Union
import warnings

# ---------------------------------------------------------------------------
#  Optional dependency: emcee for Bayesian MCMC
# ---------------------------------------------------------------------------
try:
    import emcee

    _HAS_EMCEE = True
except ImportError:
    _HAS_EMCEE = False

# ---------------------------------------------------------------------------
#  Optional dependency: corner.py for corner plots
# ---------------------------------------------------------------------------
try:
    import corner

    _HAS_CORNER = True
except ImportError:
    _HAS_CORNER = False

# ---------------------------------------------------------------------------
#  scipy optimization
# ---------------------------------------------------------------------------
from scipy import optimize as sp_optimize
from scipy import stats as sp_stats


# ═══════════════════════════════════════════════════════════════════════════
#  Helper / result dataclass
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class CalibrationResult:
    """Container for calibration results.

    Attributes
    ----------
    params_opt : np.ndarray
        Optimized parameter vector (best-fit).
    params_std : np.ndarray
        Standard deviation of each parameter (from covariance or MC).
    param_names : List[str]
        Names of the calibrated parameters.
    nfev : int
        Number of function evaluations (optimization only).
    success : bool
        Whether the optimization converged.
    method : str
        Calibration method used.
    rmse : float
        Root-mean-square error on training data.
    r_squared : float
        Coefficient of determination (R²) on training data.
    aic : float
        Akaike Information Criterion.
    bic : float
        Bayesian Information Criterion.
    reduced_chi2 : float
        Reduced chi-squared statistic (if y_err provided).
    covariance : Optional[np.ndarray]
        Parameter covariance matrix (if available).
    samples : Optional[np.ndarray]
        Posterior samples (MC or MCMC).
    log_likelihood : Optional[float]
        Log-likelihood at optimum.
    """

    params_opt: np.ndarray
    params_std: np.ndarray
    param_names: List[str]
    nfev: int = 0
    success: bool = True
    method: str = "least_squares"
    rmse: float = np.nan
    r_squared: float = np.nan
    aic: float = np.nan
    bic: float = np.nan
    reduced_chi2: float = np.nan
    covariance: Optional[np.ndarray] = None
    samples: Optional[np.ndarray] = None
    log_likelihood: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export result to a JSON-serializable dictionary."""
        return {
            "params_opt": self.params_opt.tolist(),
            "params_std": self.params_std.tolist(),
            "param_names": self.param_names,
            "nfev": self.nfev,
            "success": self.success,
            "method": self.method,
            "rmse": self.rmse,
            "r_squared": self.r_squared,
            "aic": self.aic,
            "bic": self.bic,
            "reduced_chi2": self.reduced_chi2,
            "covariance": self.covariance.tolist() if self.covariance is not None else None,
            "samples": self.samples.tolist() if self.samples is not None else None,
            "log_likelihood": self.log_likelihood,
        }

    def __str__(self) -> str:
        lines = [f"Calibration Result ({self.method})", f"  Success:  {self.success}"]
        for name, val, std in zip(self.param_names, self.params_opt, self.params_std):
            lines.append(f"  {name:>12s} = {val:12.6f} ± {std:10.6f}")
        lines.append(f"  RMSE:     {self.rmse:.6f}")
        lines.append(f"  R²:       {self.r_squared:.6f}")
        lines.append(f"  AIC:      {self.aic:.2f}")
        if self.nfev:
            lines.append(f"  nfev:     {self.nfev}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  ModelCalibration
# ═══════════════════════════════════════════════════════════════════════════


class ModelCalibration:
    """Calibrate constitutive model parameters to fit experimental data.

    Wraps a simulation model function ``model_func(params, x) -> y_predicted``
    and provides optimization, uncertainty quantification, and validation
    methods for parameter estimation.

    Parameters
    ----------
    model_func : Callable[[np.ndarray, np.ndarray], np.ndarray]
        The simulation or constitutive model to calibrate.
        Signature: ``model_func(params, x) -> y_predicted`` where:
          - ``params`` is a 1-D array of model parameters
          - ``x`` is a 1-D or 2-D array of independent variables
          - returns a 1-D array of predicted values
    param_names : List[str]
        Names of each parameter (for labelling output and plots).
    initial_guess : List[float]
        Starting values for the optimization.
    bounds : Optional[List[Tuple[float, float]]], optional
        Bounds for each parameter as ``(min, max)`` pairs.
        ``None`` means unbounded.  Use ``(0, np.inf)`` for strictly positive
        parameters, ``(-np.inf, np.inf)`` for unconstrained.

    Attributes
    ----------
    result_ : Optional[CalibrationResult]
        Result object populated after calling ``calibrate()``.
    x_ : Optional[np.ndarray]
        Training independent variable, set by ``set_experimental_data()``.
    y_ : Optional[np.ndarray]
        Training dependent variable, set by ``set_experimental_data()``.
    y_err_ : Optional[np.ndarray]
        Training measurement uncertainty, set by ``set_experimental_data()``.

    Examples
    --------
    >>> def hooke_law(params, strain):
    ...     E = params[0]
    ...     return E * strain
    >>> mc = ModelCalibration(hooke_law, ["E"], [10.0], bounds=[(0, 100)])
    >>> strain = np.linspace(0, 0.01, 10)
    >>> stress = 70e3 * strain + 5 * np.random.randn(10)
    >>> mc.set_experimental_data(strain, stress, y_err=5 * np.ones(10))
    >>> mc.calibrate(method="least_squares")
    >>> mc.plot_fit()
    """

    def __init__(
        self,
        model_func: Callable[[np.ndarray, np.ndarray], np.ndarray],
        param_names: List[str],
        initial_guess: List[float],
        bounds: Optional[List[Tuple[float, float]]] = None,
    ) -> None:
        # Validate inputs
        n_params = len(initial_guess)
        if len(param_names) != n_params:
            raise ValueError(
                f"param_names length ({len(param_names)}) must match "
                f"initial_guess length ({n_params})"
            )
        if bounds is not None and len(bounds) != n_params:
            raise ValueError(
                f"bounds length ({len(bounds)}) must match "
                f"initial_guess length ({n_params})"
            )

        self.model_func = model_func
        self.param_names = list(param_names)
        self.initial_guess = np.asarray(initial_guess, dtype=float)
        self.bounds = bounds

        # Experimental data (filled by set_experimental_data)
        self.x_: Optional[np.ndarray] = None
        self.y_: Optional[np.ndarray] = None
        self.y_err_: Optional[np.ndarray] = None

        # Calibration result (filled by calibrate* methods)
        self.result_: Optional[CalibrationResult] = None
        self._n_params = n_params

    # ------------------------------------------------------------------
    #  Data input
    # ------------------------------------------------------------------

    def set_experimental_data(
        self,
        x: np.ndarray,
        y: np.ndarray,
        y_err: Optional[np.ndarray] = None,
    ) -> "ModelCalibration":
        """Set the experimental (or reference) data for calibration.

        Parameters
        ----------
        x : np.ndarray
            Independent variable(s), shape ``(n_pts,)`` or ``(n_pts, n_dim)``.
        y : np.ndarray
            Dependent variable (response), shape ``(n_pts,)``.
        y_err : Optional[np.ndarray], optional
            Standard deviation of measurement noise for each point,
            shape ``(n_pts,)``.  If ``None``, homoscedastic noise is
            estimated from the residual after fitting.

        Returns
        -------
        ModelCalibration
            Self, for method chaining.

        Raises
        ------
        ValueError
            If ``x`` and ``y`` have inconsistent lengths.
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float).ravel()

        if x.shape[0] != y.shape[0]:
            raise ValueError(
                f"x shape {x.shape} first dimension must match y length "
                f"{len(y)}"
            )

        self.x_ = x
        self.y_ = y
        self.y_err_ = np.asarray(y_err, dtype=float).ravel() if y_err is not None else None
        return self

    # ------------------------------------------------------------------
    #  Least-squares / optimization calibration
    # ------------------------------------------------------------------

    def _residual(self, params: np.ndarray) -> np.ndarray:
        """Compute weighted residuals: (y - y_pred) / sigma."""
        y_pred = self.model_func(params, self.x_)
        if self.y_err_ is not None:
            return (self.y_ - y_pred) / self.y_err_
        return self.y_ - y_pred

    def _compute_goodness(self, params: np.ndarray) -> Dict[str, float]:
        """Compute goodness-of-fit metrics for given parameter vector."""
        y_pred = self.model_func(params, self.x_)
        residual = self.y_ - y_pred
        n = len(self.y_)
        p = len(params)

        ss_res = np.sum(residual ** 2)
        ss_tot = np.sum((self.y_ - np.mean(self.y_)) ** 2)
        rmse = np.sqrt(np.mean(residual ** 2))
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

        # Log-likelihood
        if self.y_err_ is not None:
            sigma2 = self.y_err_ ** 2
            log_likelihood = -0.5 * np.sum(
                np.log(2 * np.pi * sigma2) + residual ** 2 / sigma2
            )
        else:
            sigma2_est = ss_res / max(n - p, 1)
            log_likelihood = -0.5 * (
                n * np.log(2 * np.pi * sigma2_est) + ss_res / sigma2_est
            )

        aic = 2 * p - 2 * log_likelihood
        bic = p * np.log(n) - 2 * log_likelihood

        # Reduced chi-squared
        if self.y_err_ is not None:
            reduced_chi2 = np.mean((residual / self.y_err_) ** 2)
        else:
            reduced_chi2 = ss_res / max(n - p, 1) / np.var(self.y_) if np.var(self.y_) > 0 else np.nan

        return {
            "rmse": rmse,
            "r_squared": r_squared,
            "aic": aic,
            "bic": bic,
            "reduced_chi2": reduced_chi2,
            "log_likelihood": log_likelihood,
        }

    def calibrate(
        self,
        method: str = "least_squares",
        **kwargs,
    ) -> CalibrationResult:
        """Run deterministic optimization to calibrate model parameters.

        Parameters
        ----------
        method : str, optional
            Optimization method:

            - ``"least_squares"`` : scipy.optimize.least_squares
              (trust-region reflective; supports bounds).
            - ``"curve_fit"`` : scipy.optimize.curve_fit
              (Levenberg-Marquardt; covariance matrix returned).
            - ``"differential_evolution"`` : global optimisation via
              scipy.optimize.differential_evolution (bounds required).
            - ``"basinhopping"`` : global optimisation via
              scipy.optimize.basinhopping.

        **kwargs
            Additional keyword arguments passed to the underlying
            scipy.optimize function (e.g. ``max_nfev``, ``ftol``,
            ``xtol``, ``gtol``, ``seed``).

        Returns
        -------
        CalibrationResult
            Result container with optimised parameters, uncertainty
            estimates, and goodness-of-fit metrics.

        Raises
        ------
        RuntimeError
            If experimental data has not been set via
            ``set_experimental_data()``.
        ValueError
            If the method is not recognised.
        """
        if self.x_ is None or self.y_ is None:
            raise RuntimeError(
                "Call set_experimental_data() before calibrate()."
            )

        method = method.lower()

        # Build bounds arrays for scipy
        lb, ub = self._format_bounds()

        if method == "least_squares":
            result = sp_optimize.least_squares(
                self._residual,
                self.initial_guess,
                bounds=(lb, ub) if self.bounds is not None else (-np.inf, np.inf),
                **kwargs,
            )
            params_opt = result.x
            nfev = result.nfev
            success = result.success

            # Approximate covariance from Jacobian
            try:
                J = result.jac
                _, s, VT = np.linalg.svd(J, full_matrices=False)
                threshold = np.finfo(float).eps * max(J.shape) * s[0]
                s_inv = np.array([1 / si if si > threshold else 0 for si in s])
                cov = (VT.T * s_inv) @ (VT.T * s_inv).T
                params_std = np.sqrt(np.diag(cov))
            except Exception:
                cov = None
                params_std = np.full(self._n_params, np.nan)

        elif method == "curve_fit":
            # sigma for curve_fit expects std dev
            sigma = self.y_err_ if self.y_err_ is not None else None
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", sp_optimize.OptimizeWarning)
                popt, pcov = sp_optimize.curve_fit(
                    lambda x, *p: self.model_func(np.array(p), x),
                    self.x_,
                    self.y_,
                    p0=self.initial_guess,
                    sigma=sigma,
                    bounds=self.bounds if self.bounds else (-np.inf, np.inf),
                    **kwargs,
                )
            params_opt = popt
            nfev = 0  # curve_fit does not expose nfev
            success = True
            cov = pcov if np.all(np.isfinite(pcov)) else None
            params_std = np.sqrt(np.diag(pcov)) if cov is not None else np.full(self._n_params, np.nan)

        elif method == "differential_evolution":
            if self.bounds is None:
                raise ValueError(
                    "bounds are required for differential_evolution"
                )

            def de_objective(p):
                return np.sum(self._residual(p) ** 2)

            result = sp_optimize.differential_evolution(
                de_objective,
                bounds=self.bounds,
                x0=self.initial_guess,
                **kwargs,
            )
            params_opt = result.x
            nfev = result.nfev
            success = result.success
            cov = None
            params_std = np.full(self._n_params, np.nan)

        elif method == "basinhopping":
            def bh_objective(p):
                return np.sum(self._residual(p) ** 2)

            result = sp_optimize.basinhopping(
                bh_objective,
                self.initial_guess,
                **kwargs,
            )
            params_opt = result.x
            nfev = result.nfev if hasattr(result, "nfev") else 0
            success = result.lowest_optimization_result.success if result.lowest_optimization_result else True
            cov = None
            params_std = np.full(self._n_params, np.nan)

        else:
            raise ValueError(
                f"Unknown method '{method}'.  Choose from: "
                "least_squares, curve_fit, differential_evolution, basinhopping."
            )

        # Goodness-of-fit
        gof = self._compute_goodness(params_opt)

        self.result_ = CalibrationResult(
            params_opt=params_opt,
            params_std=params_std,
            param_names=self.param_names,
            nfev=nfev,
            success=success,
            method=method,
            rmse=gof["rmse"],
            r_squared=gof["r_squared"],
            aic=gof["aic"],
            bic=gof["bic"],
            reduced_chi2=gof["reduced_chi2"],
            covariance=cov,
            log_likelihood=gof["log_likelihood"],
        )
        return self.result_

    # ------------------------------------------------------------------
    #  Monte Carlo calibration
    # ------------------------------------------------------------------

    def calibrate_monte_carlo(
        self,
        n_samples: int = 1000,
        method: str = "least_squares",
        seed: Optional[int] = None,
        **kwargs,
    ) -> CalibrationResult:
        """Calibrate parameters with Monte Carlo uncertainty propagation.

        Resamples the experimental data assuming Gaussian noise (using
        ``y_err`` if available, otherwise the RMSE of the best fit) and
        re-runs the optimisation for each resample.  The distribution of
        optimised parameters provides uncertainty bounds that account for
        measurement noise.

        Parameters
        ----------
        n_samples : int, optional
            Number of Monte Carlo resamples (default 1000).
        method : str, optional
            Optimisation method passed to ``calibrate()``
            (default ``"least_squares"``).
        seed : Optional[int], optional
            Random seed for reproducibility.
        **kwargs
            Additional keyword arguments passed to ``calibrate()``.

        Returns
        -------
        CalibrationResult
            Result with ``params_opt`` set to the median of the MC
            distribution, ``params_std`` to the standard deviation,
            and ``samples`` containing all MC realisations.

        Notes
        -----
        This method is significantly more expensive than a single
        calibration.  For complex models, reduce ``n_samples`` or use
        a fast optimisation method.
        """
        if self.x_ is None or self.y_ is None:
            raise RuntimeError(
                "Call set_experimental_data() before calibrate_monte_carlo()."
            )

        rng = np.random.default_rng(seed)

        # If y_err not provided, estimate from a preliminary fit
        if self.y_err_ is None:
            # Temporarily fit to estimate residual std
            temp = self.calibrate(method=method, **kwargs)
            y_pred = self.model_func(temp.params_opt, self.x_)
            residual_std = np.std(self.y_ - y_pred)
            sigma = residual_std * np.ones_like(self.y_)
        else:
            sigma = self.y_err_

        # Storage for MC samples
        mc_params = np.zeros((n_samples, self._n_params))
        n_success = 0

        for i in range(n_samples):
            # Resample: y_synth = y + noise
            noise = rng.normal(0, sigma)
            y_synth = self.y_ + noise

            # Temporarily swap data; fit; restore
            y_orig = self.y_
            self.y_ = y_synth

            try:
                res = self.calibrate(method=method, **kwargs)
                if res.success:
                    mc_params[n_success] = res.params_opt
                    n_success += 1
            except Exception:
                pass

            self.y_ = y_orig

        # Trim unused rows
        mc_params = mc_params[:n_success]

        if n_success == 0:
            raise RuntimeError(
                "All Monte Carlo samples failed to converge.  "
                "Check model, data, and initial guess."
            )

        # Compute statistics
        params_median = np.median(mc_params, axis=0)
        params_std = np.std(mc_params, axis=0, ddof=1)
        gof = self._compute_goodness(params_median)

        self.result_ = CalibrationResult(
            params_opt=params_median,
            params_std=params_std,
            param_names=self.param_names,
            nfev=n_samples,
            success=True,
            method=f"monte_carlo({method})",
            rmse=gof["rmse"],
            r_squared=gof["r_squared"],
            aic=gof["aic"],
            bic=gof["bic"],
            reduced_chi2=gof["reduced_chi2"],
            samples=mc_params,
            log_likelihood=gof["log_likelihood"],
        )
        return self.result_

    # ------------------------------------------------------------------
    #  Bayesian MCMC calibration (emcee)
    # ------------------------------------------------------------------

    def calibrate_bayesian(
        self,
        n_walkers: int = 32,
        n_steps: int = 2000,
        n_burn: int = 500,
        method: str = "least_squares",
        seed: Optional[int] = None,
        **kwargs,
    ) -> CalibrationResult:
        """Calibrate parameters using Bayesian MCMC sampling via emcee.

        Defines a Gaussian log-likelihood and flat (uniform) priors within
        the parameter bounds, then samples the posterior with the
        affine-invariant ensemble sampler.

        Parameters
        ----------
        n_walkers : int, optional
            Number of MCMC walkers (default 32).  Must be at least
            ``2 * n_params``.
        n_steps : int, optional
            Number of MCMC steps per walker (default 2000).
        n_burn : int, optional
            Number of initial steps discarded as burn-in (default 500).
        method : str, optional
            Optimisation method used to initialise walkers near the
            maximum-likelihood point (default ``"least_squares"``).
        seed : Optional[int], optional
            Random seed for reproducibility.
        **kwargs
            Additional keyword arguments forwarded to ``calibrate()``.

        Returns
        -------
        CalibrationResult
            Result with posterior statistics (median and std from
            flattened chain), ``samples`` containing the full chain,
            and covariance estimated from the posterior.

        Raises
        ------
        RuntimeError
            If emcee is not installed.
        """
        if not _HAS_EMCEE:
            warnings.warn(
                "emcee is not installed.  Falling back to "
                "calibrate_monte_carlo().  Install with: "
                "pip install emcee",
                UserWarning,
            )
            return self.calibrate_monte_carlo(
                n_samples=n_walkers * n_steps // 10,
                method=method,
                seed=seed,
            )

        if self.x_ is None or self.y_ is None:
            raise RuntimeError(
                "Call set_experimental_data() before calibrate_bayesian()."
            )

        rng = np.random.default_rng(seed)

        # Seed the fit to initialise walkers near the optimum
        best_fit = self.calibrate(method=method, **kwargs)
        p0_best = best_fit.params_opt
        p0_std = np.where(np.isfinite(best_fit.params_std), best_fit.params_std, 0.1 * np.abs(p0_best) + 0.01)

        n_walkers = max(n_walkers, 2 * self._n_params)

        # ---- Log-probability (posterior) ----

        def log_likelihood(params: np.ndarray) -> float:
            y_pred = self.model_func(params, self.x_)
            residual = self.y_ - y_pred
            if self.y_err_ is not None:
                return -0.5 * np.sum(
                    np.log(2 * np.pi * self.y_err_ ** 2)
                    + (residual / self.y_err_) ** 2
                )
            # Estimate sigma from residual
            n = len(self.y_)
            sigma2 = np.sum(residual ** 2) / max(n - self._n_params, 1)
            return -0.5 * (n * np.log(2 * np.pi * sigma2) + np.sum(residual ** 2) / sigma2)

        def log_prior(params: np.ndarray) -> float:
            lb, ub = self._format_bounds()
            if self.bounds is not None:
                if np.any(params < lb) or np.any(params > ub):
                    return -np.inf
            # Flat prior; no additional constraints
            return 0.0

        def log_posterior(params: np.ndarray) -> float:
            lp = log_prior(params)
            if not np.isfinite(lp):
                return -np.inf
            ll = log_likelihood(params)
            if not np.isfinite(ll):
                return -np.inf
            return lp + ll

        # ---- Initialise walkers ----
        ndim = self._n_params
        initial_positions = p0_best + p0_std * rng.normal(size=(n_walkers, ndim))

        # Clip to bounds
        if self.bounds is not None:
            lb_arr, ub_arr = self._format_bounds()
            for i in range(n_walkers):
                initial_positions[i] = np.clip(initial_positions[i], lb_arr, ub_arr)

        # ---- Run sampler ----
        sampler = emcee.EnsembleSampler(n_walkers, ndim, log_posterior)
        sampler.run_mcmc(initial_positions, n_steps, progress=False, **kwargs)

        # ---- Extract chain ----
        chain = sampler.get_chain(discard=n_burn, flat=True)
        log_prob_chain = sampler.get_log_prob(discard=n_burn, flat=True)

        params_median = np.median(chain, axis=0)
        params_std = np.std(chain, axis=0, ddof=1)
        cov = np.cov(chain, rowvar=False)
        gof = self._compute_goodness(params_median)

        self.result_ = CalibrationResult(
            params_opt=params_median,
            params_std=params_std,
            param_names=self.param_names,
            nfev=n_walkers * n_steps,
            success=True,
            method="mcmc(emcee)",
            rmse=gof["rmse"],
            r_squared=gof["r_squared"],
            aic=gof["aic"],
            bic=gof["bic"],
            reduced_chi2=gof["reduced_chi2"],
            covariance=cov,
            samples=chain,
            log_likelihood=gof["log_likelihood"],
        )
        return self.result_

    # ------------------------------------------------------------------
    #  Result / prediction / validation
    # ------------------------------------------------------------------

    def results(self) -> CalibrationResult:
        """Return the current calibration result.

        Returns
        -------
        CalibrationResult
            The result from the most recent ``calibrate()``,
            ``calibrate_monte_carlo()``, or ``calibrate_bayesian()`` call.

        Raises
        ------
        RuntimeError
            If no calibration has been run yet.
        """
        if self.result_ is None:
            raise RuntimeError(
                "No calibration result available.  "
                "Run calibrate(), calibrate_monte_carlo(), "
                "or calibrate_bayesian() first."
            )
        return self.result_

    def predict(self, x_new: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict using the calibrated model with uncertainty.

        Parameters
        ----------
        x_new : np.ndarray
            New independent variable(s) at which to evaluate the model.

        Returns
        -------
        y_pred : np.ndarray
            Predicted values using the optimised parameters.
        y_lower : np.ndarray
            Lower 95 % prediction interval.
        y_upper : np.ndarray
            Upper 95 % prediction interval.

        Notes
        -----
        Prediction intervals are computed from posterior samples (MC or
        MCMC) if available, otherwise from the parameter covariance
        propagated via a first-order (delta-method) approximation.
        """
        res = self.results()
        x_new = np.asarray(x_new, dtype=float)

        # Point prediction
        y_pred = self.model_func(res.params_opt, x_new)

        if res.samples is not None and len(res.samples) > 10:
            # Full posterior propagation
            n_plot = min(1000, len(res.samples))
            idx = np.linspace(0, len(res.samples) - 1, n_plot, dtype=int)
            pred_samples = np.array([self.model_func(res.samples[i], x_new) for i in idx])
            y_lower = np.percentile(pred_samples, 2.5, axis=0)
            y_upper = np.percentile(pred_samples, 97.5, axis=0)
        elif res.covariance is not None:
            # First-order delta method
            eps = 1e-6
            J = np.zeros((len(x_new), self._n_params))
            p0 = res.params_opt
            y0 = self.model_func(p0, x_new)
            for j in range(self._n_params):
                p_pert = p0.copy()
                p_pert[j] += eps
                y_pert = self.model_func(p_pert, x_new)
                J[:, j] = (y_pert - y0) / eps
            pred_var = np.einsum("ij,jk,ik->i", J, res.covariance, J)
            y_lower = y_pred - 1.96 * np.sqrt(np.clip(pred_var, 0, None))
            y_upper = y_pred + 1.96 * np.sqrt(np.clip(pred_var, 0, None))
        else:
            # No uncertainty information
            y_lower = y_pred
            y_upper = y_pred

        return y_pred, y_lower, y_upper

    def validate(
        self,
        x_val: np.ndarray,
        y_val: np.ndarray,
        y_val_err: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Validate the calibrated model on holdout data.

        Parameters
        ----------
        x_val : np.ndarray
            Independent variable(s) for validation.
        y_val : np.ndarray
            Observed values for validation.
        y_val_err : Optional[np.ndarray], optional
            Measurement uncertainty for each validation point.

        Returns
        -------
        Dict[str, float]
            Validation metrics:

            - ``"rmse"`` : root-mean-square error
            - ``"r_squared"`` : coefficient of determination
            - ``"mae"`` : mean absolute error
            - ``"max_abs_error"`` : maximum absolute error
            - ``"coverage_95"`` : fraction of points within the 95 %
              prediction interval (requires posterior samples or
              covariance)
            - ``"mean_std_error"`` : mean normalised error relative
              to ``y_val_err`` (if provided)
            - ``"n_val"`` : number of validation points
        """
        res = self.results()
        x_val = np.asarray(x_val, dtype=float)
        y_val = np.asarray(y_val, dtype=float).ravel()

        y_pred, y_lower, y_upper = self.predict(x_val)
        residual = y_val - y_pred

        n = len(y_val)
        ss_res = np.sum(residual ** 2)
        ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)

        metrics: Dict[str, float] = {
            "rmse": float(np.sqrt(np.mean(residual ** 2))),
            "r_squared": float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan,
            "mae": float(np.mean(np.abs(residual))),
            "max_abs_error": float(np.max(np.abs(residual))),
            "n_val": float(n),
        }

        # Coverage of 95 % prediction interval
        if not np.allclose(y_lower, y_pred):
            in_interval = np.sum((y_val >= y_lower) & (y_val <= y_upper))
            metrics["coverage_95"] = float(in_interval / n)

        # Normalised error
        if y_val_err is not None:
            y_val_err = np.asarray(y_val_err, dtype=float).ravel()
            norm_err = np.mean(np.abs(residual) / y_val_err)
            metrics["mean_std_error"] = float(norm_err)

        return metrics

    # ------------------------------------------------------------------
    #  Plotting
    # ------------------------------------------------------------------

    def plot_fit(
        self,
        n_curves: int = 100,
        ax=None,
        show: bool = True,
    ) -> Any:
        """Plot the calibrated fit with uncertainty band.

        Parameters
        ----------
        n_curves : int, optional
            Number of posterior samples to draw for the uncertainty
            envelope (default 100).  Ignored if no posterior samples.
        ax : matplotlib.axes.Axes, optional
            Axes to plot on.  Created if not provided.
        show : bool, optional
            Whether to call ``plt.show()`` (default ``True``).

        Returns
        -------
        matplotlib.axes.Axes
            The axes object with the plot.
        """
        import matplotlib.pyplot as plt

        res = self.results()

        if ax is None:
            _, ax = plt.subplots(figsize=(8, 5))

        # Sort x for clean plot
        x_sorted = np.sort(self.x_.ravel()) if self.x_ is not None else np.array([])
        x_plot = np.linspace(x_sorted[0], x_sorted[-1], 200) if len(x_sorted) > 1 else np.linspace(0, 1, 200)

        # Prediction with uncertainty
        y_pred, y_low, y_high = self.predict(x_plot)

        # Draw posterior sample curves
        if res.samples is not None and len(res.samples) > 1:
            n_curves = min(n_curves, len(res.samples))
            idx = np.linspace(0, len(res.samples) - 1, n_curves, dtype=int)
            for i in idx:
                y_s = self.model_func(res.samples[i], x_plot)
                ax.plot(x_plot, y_s, color="C0", alpha=0.08, lw=0.6)

        # Shaded confidence band
        ax.fill_between(x_plot, y_low, y_high, color="C0", alpha=0.2, label="95 % CI")

        # Best-fit curve
        ax.plot(x_plot, y_pred, "C0-", lw=2.0, label="Best fit")

        # Experimental data
        if self.x_ is not None and self.y_ is not None:
            if self.y_err_ is not None:
                ax.errorbar(
                    self.x_.ravel(),
                    self.y_,
                    yerr=self.y_err_,
                    fmt="ok",
                    ms=4,
                    capsize=2,
                    label="Data",
                )
            else:
                ax.plot(self.x_.ravel(), self.y_, "ok", ms=4, label="Data")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title("Model Calibration")
        ax.legend()
        ax.grid(True, alpha=0.3)

        if show:
            plt.tight_layout()
            plt.show()

        return ax

    def plot_corner(self, show: bool = True) -> Optional[Any]:
        """Plot a corner plot of parameter correlations.

        Requires ``corner.py`` and posterior samples from
        ``calibrate_monte_carlo()`` or ``calibrate_bayesian()``.

        Parameters
        ----------
        show : bool, optional
            Whether to call ``plt.show()`` (default ``True``).

        Returns
        -------
        matplotlib.figure.Figure or None
            The corner figure, or ``None`` if ``corner`` is not
            installed or no posterior samples exist.
        """
        import matplotlib.pyplot as plt

        res = self.results()
        if res.samples is None or len(res.samples) < 10:
            print("No posterior samples available for corner plot.")
            return None

        if not _HAS_CORNER:
            print(
                "corner.py is not installed.  Install with: pip install corner"
            )
            return None

        figure = corner.corner(
            res.samples,
            labels=self.param_names,
            quantiles=[0.16, 0.5, 0.84],
            show_titles=True,
            title_fmt=".4f",
            title_kwargs={"fontsize": 10},
            label_kwargs={"fontsize": 11},
            smooth=True,
            truths=res.params_opt if res.params_opt is not None else None,
            truth_color="C3",
        )

        if show:
            plt.tight_layout()
            plt.show()

        return figure

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _format_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """Format bounds as (lb_array, ub_array) for scipy optimizers."""
        if self.bounds is not None:
            lb = np.array([b[0] for b in self.bounds], dtype=float)
            ub = np.array([b[1] for b in self.bounds], dtype=float)
        else:
            lb = np.full(self._n_params, -np.inf)
            ub = np.full(self._n_params, np.inf)
        return lb, ub


# ═══════════════════════════════════════════════════════════════════════════
#  Factory / convenience helpers
# ═══════════════════════════════════════════════════════════════════════════


def calibrate_model(
    model_func: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x: np.ndarray,
    y: np.ndarray,
    param_names: List[str],
    initial_guess: List[float],
    bounds: Optional[List[Tuple[float, float]]] = None,
    y_err: Optional[np.ndarray] = None,
    method: str = "least_squares",
    **kwargs,
) -> CalibrationResult:
    """One-shot convenience function for model calibration.

    Combines ``ModelCalibration.__init__()``,
    ``set_experimental_data()``, and ``calibrate()`` into a single call.

    Parameters
    ----------
    model_func : Callable
        The simulation model ``(params, x) -> y_predicted``.
    x : np.ndarray
        Independent variable.
    y : np.ndarray
        Observed dependent variable.
    param_names : List[str]
        Names of model parameters.
    initial_guess : List[float]
        Starting values for optimisation.
    bounds : Optional[List[Tuple[float, float]]], optional
        Parameter bounds.
    y_err : Optional[np.ndarray], optional
        Measurement uncertainties.
    method : str, optional
        Optimisation method (default ``"least_squares"``).
    **kwargs
        Additional arguments forwarded to ``calibrate()``.

    Returns
    -------
    CalibrationResult
    """
    mc = ModelCalibration(model_func, param_names, initial_guess, bounds=bounds)
    mc.set_experimental_data(x, y, y_err=y_err)
    return mc.calibrate(method=method, **kwargs)
