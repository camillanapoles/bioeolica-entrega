# =============================================================================
# VVV Framework Utilities — Verification, Validation, Certification
# Part of T012 — Phase 2 Foundational
# Reference: INSTRUCTIONS.md M3 (VVV protocol), contracts/schema-validation.sql
# =============================================================================
"""
Verification, Validation, and Certification (VVV) framework.

Provides:
  - Verification: mesh convergence, temporal stability, conservation checks
  - Validation: experimental correlation, cross-code benchmarks
  - Certification: PASS/FAIL decision with 6-criterion checklist

Usage:
    from src.common.validation import verify_convergence, validate_correlation, certify_result
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """Results from a verification check (mesh, temporal, conservation).

    Attributes:
        metric: Name of the verification metric (e.g. 'mesh_convergence')
        value: Computed value
        threshold: Acceptance threshold
        passed: True if value meets threshold criterion
        detail: Human-readable explanation
    """
    metric: str
    value: float
    threshold: float
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    """Results from a validation check (experimental correlation, cross-code).

    Attributes:
        reference: Name/ID of reference (experiment, benchmark, or cross-code)
        metric_type: 'correlation', 'rmse', 'max_error', 'relative_error'
        value: Computed metric value
        threshold: Acceptance threshold
        passed: True if value meets threshold
    """
    reference: str
    metric_type: str
    value: float
    threshold: float
    passed: bool


@dataclass
class CertificationReport:
    """Complete VVV certification report for a single result.

    Attributes:
        object_id: UUID v4 of the certified object
        object_type: Type of object certified
        verification_results: List of individual verification checks
        validation_results: List of individual validation checks
        all_verification_pass: True if every verification check passed
        all_validation_pass: True if every validation check passed
        certification_status: 'PASS' if all checks pass, else 'FAIL'
        error_metrics: Dict of aggregate error metrics (precision, convergence, fidelity)
    """
    object_id: str
    object_type: str
    verification_results: List[VerificationResult] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    error_metrics: Dict[str, Optional[float]] = field(default_factory=dict)

    @property
    def all_verification_pass(self) -> bool:
        return all(v.passed for v in self.verification_results)

    @property
    def all_validation_pass(self) -> bool:
        return all(v.passed for v in self.validation_results)

    @property
    def certification_status(self) -> str:
        return "PASS" if (self.all_verification_pass and self.all_validation_pass) else "FAIL"


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------

def verify_mesh_convergence(
    values: List[float],
    threshold_pct: float = 5.0,
) -> VerificationResult:
    """Check mesh convergence from a sequence of refinement values.

    Compares variation between successive mesh refinements against threshold.

    Args:
        values: List of quantity values across mesh refinements (coarse → fine).
        threshold_pct: Maximum allowable variation between last two refinements (%).

    Returns:
        VerificationResult with pass/fail and variation detail.
    """
    if len(values) < 2:
        return VerificationResult(
            metric="mesh_convergence",
            value=float("inf"),
            threshold=threshold_pct,
            passed=False,
            detail=f"Need at least 2 refinement levels, got {len(values)}",
        )

    # Use relative variation between final two refinements
    v_coarse = values[-2]
    v_fine = values[-1]
    if v_coarse == 0:
        return VerificationResult(
            metric="mesh_convergence",
            value=float("inf"),
            threshold=threshold_pct,
            passed=False,
            detail="Zero value in coarse mesh — possible numerical issue",
        )

    variation_pct = 100.0 * abs(v_fine - v_coarse) / abs(v_coarse)
    passed = variation_pct <= threshold_pct

    return VerificationResult(
        metric="mesh_convergence",
        value=round(variation_pct, 2),
        threshold=threshold_pct,
        passed=passed,
        detail=f"Variation between refinements: {variation_pct:.2f}% (threshold: {threshold_pct}%)",
    )


def verify_conservation(
    energy_in: float,
    energy_out: float,
    tolerance: float = 0.01,
) -> VerificationResult:
    """Check conservation of energy/mass (imbalance must be below tolerance).

    Args:
        energy_in: Energy or mass entering the system.
        energy_out: Energy or mass leaving the system.
        tolerance: Maximum allowable imbalance fraction (default 0.01 = 1%).

    Returns:
        VerificationResult with pass/fail.
    """
    if energy_in == 0:
        return VerificationResult(
            metric="conservation",
            value=float("inf"),
            threshold=tolerance,
            passed=False,
            detail="Zero input energy — check boundary conditions",
        )

    imbalance = abs(energy_in - energy_out) / abs(energy_in)
    passed = imbalance <= tolerance

    return VerificationResult(
        metric="conservation",
        value=round(imbalance, 6),
        threshold=tolerance,
        passed=passed,
        detail=f"Energy/mass imbalance: {100*imbalance:.2f}% (tolerance: {100*tolerance:.2f}%)",
    )


def verify_temporal_stability(
    residuals: List[float],
    threshold: float = 1e-4,
) -> VerificationResult:
    """Check temporal convergence by residual decay.

    Args:
        residuals: List of residual values at each time step/iteration.
        threshold: Final residual must be below this value.

    Returns:
        VerificationResult with pass/fail.
    """
    if not residuals:
        return VerificationResult(
            metric="temporal_stability", value=float("inf"),
            threshold=threshold, passed=False,
            detail="No residual data provided",
        )

    final_residual = residuals[-1]
    passed = final_residual <= threshold

    return VerificationResult(
        metric="temporal_stability",
        value=final_residual,
        threshold=threshold,
        passed=passed,
        detail=f"Final residual: {final_residual:.6e} (threshold: {threshold:.1e})",
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_correlation(
    experimental_values: List[float],
    simulated_values: List[float],
    reference_name: str = "experimental",
    threshold: float = 0.95,
) -> ValidationResult:
    """Compute Pearson correlation between experimental and simulated values.

    Args:
        experimental_values: Measured data points.
        simulated_values: Computed data points (same length as experimental).
        reference_name: Label for this reference.
        threshold: Minimum acceptable correlation coefficient.

    Returns:
        ValidationResult with pass/fail.
    """
    if len(experimental_values) != len(simulated_values) or len(experimental_values) < 2:
        return ValidationResult(
            reference=reference_name, metric_type="correlation",
            value=0.0, threshold=threshold, passed=False,
        )

    n = len(experimental_values)
    mean_exp = sum(experimental_values) / n
    mean_sim = sum(simulated_values) / n

    num = sum((e - mean_exp) * (s - mean_sim) for e, s in zip(experimental_values, simulated_values))
    denom_exp = math.sqrt(sum((e - mean_exp) ** 2 for e in experimental_values))
    denom_sim = math.sqrt(sum((s - mean_sim) ** 2 for s in simulated_values))

    if denom_exp == 0 or denom_sim == 0:
        return ValidationResult(
            reference=reference_name, metric_type="correlation",
            value=0.0, threshold=threshold, passed=False,
        )

    r = num / (denom_exp * denom_sim)
    passed = r >= threshold

    return ValidationResult(
        reference=reference_name, metric_type="correlation",
        value=round(r, 4), threshold=threshold, passed=passed,
    )


def validate_relative_error(
    experimental: float,
    simulated: float,
    reference_name: str = "experimental",
    threshold: float = 10.0,
) -> ValidationResult:
    """Compute relative error between simulated and experimental values.

    Args:
        experimental: Reference experimental value.
        simulated: Computed value.
        reference_name: Label for this reference.
        threshold: Maximum acceptable relative error in percent.

    Returns:
        ValidationResult with pass/fail.
    """
    if experimental == 0:
        return ValidationResult(
            reference=reference_name, metric_type="relative_error",
            value=float("inf"), threshold=threshold, passed=False,
        )

    error_pct = 100.0 * abs(simulated - experimental) / abs(experimental)
    passed = error_pct <= threshold

    return ValidationResult(
        reference=reference_name, metric_type="relative_error",
        value=round(error_pct, 2), threshold=threshold, passed=passed,
    )


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

def certify_result(
    object_id: str,
    object_type: str,
    verification_results: List[VerificationResult],
    validation_results: Optional[List[ValidationResult]] = None,
    error_metrics: Optional[Dict[str, Optional[float]]] = None,
) -> CertificationReport:
    """Generate a complete VVV certification report.

    All verification checks must pass for certification PASS.
    Validation checks are optional (model-only objects may not have
    experimental data yet), but if present must also all pass.

    Args:
        object_id: UUID v4 of the object being certified.
        object_type: Type of object.
        verification_results: List of completed verification checks.
        validation_results: Optional list of completed validation checks.
        error_metrics: Optional aggregate error metrics.

    Returns:
        CertificationReport with full status.
    """
    report = CertificationReport(
        object_id=object_id,
        object_type=object_type,
        verification_results=verification_results,
        validation_results=validation_results or [],
        error_metrics=error_metrics or {},
    )

    # Aggregate error metrics
    if verification_results:
        report.error_metrics.setdefault("verification_pass_rate",
            sum(1 for v in verification_results if v.passed) / len(verification_results))

    return report
