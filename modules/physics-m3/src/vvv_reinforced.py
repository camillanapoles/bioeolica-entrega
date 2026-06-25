"""
VVV Reinforced — Validação Experimental Reforçada
===================================================

Pipeline de validação VVV (Verificação, Validação, Certificação) reforçado
com comparação sistemática contra dados experimentais, calibração de
modelos constitutivos, e métricas de certificação quantitativas.

Referências
-----------
- ASME V&V 10-2006: Guide for Verification and Validation in Computational
  Solid Mechanics
- ASME V&V 20-2009: Standard for Verification and Validation in CFD and
  Heat Transfer
- Oberkampf, W. L., & Roy, C. J. (2010). Verification and Validation in
  Scientific Computing. Cambridge University Press.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from modules._config_shim import resolve


@dataclass
class VVVResult:
    """Result of a VVV validation cycle.

    Attributes
    ----------
    name : str
        Name of the validation case.
    rmse : float
        Root mean square error.
    r2 : float
        Coefficient of determination.
    max_error : float
        Maximum absolute error.
    relative_error : float
        Mean relative error (percent).
    n_points : int
        Number of comparison points.
    certified : bool
        Whether criteria are met for certification.
    criteria : dict
        Validation criteria used.
    metadata : dict
        Additional metadata.
    """

    name: str
    rmse: float = 0.0
    r2: float = 0.0
    max_error: float = 0.0
    relative_error: float = 0.0
    n_points: int = 0
    certified: bool = False
    criteria: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


class VVVReinforced:
    """Reinforced VVV validation pipeline.

    Manages validation cases against experimental data, computes
    certification metrics, and generates validation reports.
    """

    def __init__(
        self,
        cfg: Optional[Any] = None,
        rmse_threshold: Optional[float] = None,
        r2_threshold: Optional[float] = None,
        max_error_threshold: Optional[float] = None,
        relative_error_threshold: Optional[float] = None,
    ) -> None:
        self.rmse_threshold = (
            rmse_threshold if rmse_threshold is not None
            else resolve(cfg, "vvv.rmse_threshold", 0.15)
        )
        self.r2_threshold = (
            r2_threshold if r2_threshold is not None
            else resolve(cfg, "vvv.r2_threshold", 0.85)
        )
        self.max_error_threshold = (
            max_error_threshold if max_error_threshold is not None
            else resolve(cfg, "vvv.max_error_threshold", 0.30)
        )
        self.relative_error_threshold = (
            relative_error_threshold if relative_error_threshold is not None
            else resolve(cfg, "vvv.relative_error_threshold", 15.0)
        )
        self.results: dict[str, VVVResult] = {}

    def validate(
        self,
        name: str,
        sim_y: np.ndarray,
        exp_y: np.ndarray,
        criteria: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> VVVResult:
        """Run validation for a sim vs exp comparison.

        Parameters
        ----------
        name : str
            Validation case name.
        sim_y : np.ndarray
            Simulation results.
        exp_y : np.ndarray
            Experimental data.
        criteria : dict, optional
            Custom validation criteria overrides.
        metadata : dict, optional
            Additional metadata.

        Returns
        -------
        VVVResult
            Validation result with metrics and certification status.
        """
        sim = np.asarray(sim_y, dtype=float)
        exp = np.asarray(exp_y, dtype=float)
        n = len(sim)
        residuals = sim - exp

        # Metrics
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        max_err = float(np.max(np.abs(residuals)))
        rel_err = float(np.mean(np.abs(residuals) / (np.abs(exp) + 1e-12)) * 100)

        # R²
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((exp - np.mean(exp)) ** 2)
        r2 = 1.0 - ss_res / (ss_tot + 1e-12)

        # Criteria
        c = {
            "rmse": self.rmse_threshold,
            "r2": self.r2_threshold,
            "max_error": self.max_error_threshold,
            "relative_error": self.relative_error_threshold,
        }
        if criteria:
            c.update(criteria)

        certified = (
            rmse <= c["rmse"]
            and r2 >= c["r2"]
            and max_err <= c["max_error"]
            and rel_err <= c["relative_error"]
        )

        result = VVVResult(
            name=name,
            rmse=round(rmse, 6),
            r2=round(r2, 6),
            max_error=round(max_err, 6),
            relative_error=round(rel_err, 6),
            n_points=n,
            certified=certified,
            criteria=c,
            metadata=metadata or {},
        )
        self.results[name] = result
        return result

    def validate_cross_code(
        self,
        name: str,
        sim_a: np.ndarray,
        sim_b: np.ndarray,
        metadata: Optional[dict] = None,
    ) -> VVVResult:
        """Validate by cross-code comparison (two independent implementations).

        Parameters
        ----------
        name : str
            Validation case name.
        sim_a : np.ndarray
            Results from implementation A.
        sim_b : np.ndarray
            Results from implementation B.
        metadata : dict, optional
            Additional metadata.

        Returns
        -------
        VVVResult
            Validation result.
        """
        return self.validate(
            name=f"{name} (cross-code)",
            sim_y=sim_a,
            exp_y=sim_b,
            criteria={"rmse": 0.10, "r2": 0.90},
            metadata={"type": "cross_code", **(metadata or {})},
        )

    def certify(self, name: str) -> bool:
        """Check if a validation case is certified.

        Parameters
        ----------
        name : str
            Validation case name.

        Returns
        -------
        certified : bool
        """
        if name not in self.results:
            return False
        return self.results[name].certified

    def report(self, names: Optional[list[str]] = None) -> str:
        """Generate formatted VVV report.

        Parameters
        ----------
        names : list of str, optional
            Cases to include. All if None.

        Returns
        -------
        report : str
            Formatted report.
        """
        cases = names if names else list(self.results.keys())
        lines = ["VVV VALIDATION REPORT", "=" * 60, ""]
        for name in cases:
            if name not in self.results:
                continue
            r = self.results[name]
            status = "CERTIFIED ✅" if r.certified else "FAILED ❌"
            lines.append(f"Case: {name}")
            lines.append(f"  Status:     {status}")
            lines.append(f"  RMSE:       {r.rmse:.6f}  (threshold: {r.criteria['rmse']})")
            lines.append(f"  R²:         {r.r2:.6f}  (threshold: {r.criteria['r2']})")
            lines.append(f"  Max Error:  {r.max_error:.6f}  (threshold: {r.criteria['max_error']})")
            lines.append(f"  Rel Error:  {r.relative_error:.2f}%  (threshold: {r.criteria['relative_error']:.1f}%)")
            lines.append(f"  N Points:   {r.n_points}")
            lines.append("")
        n_cert = sum(1 for n in self.results if self.results[n].certified)
        n_total = len(self.results)
        lines.append("-" * 60)
        lines.append(f"Certified: {n_cert}/{n_total}")
        lines.append(f"Overall:   {'PASS ✅' if n_cert == n_total else f'{n_total - n_cert} FAILURES ❌'}")
        return "\n".join(lines)

    def summary(self) -> dict:
        """Return summary dict of all results."""
        return {
            "n_cases": len(self.results),
            "n_certified": sum(1 for r in self.results.values() if r.certified),
            "certified": [n for n, r in self.results.items() if r.certified],
            "failed": [n for n, r in self.results.items() if not r.certified],
        }
