#!/usr/bin/env python3
# =============================================================================
# Fatigue Analysis — Composite Biomaterial for Wind Energy
# Phase 5 — Wind Turbine Blade Application | T042
# Reference: IEC 61400-2 (small wind turbines), Palmgren-Miner rule
# Material: Paper mache + graphite composite (S-N slope k=10, UTS=12.5 MPa)
# =============================================================================
"""
Palmgren-Miner cumulative fatigue damage analysis for the paper mache +
graphite composite wind turbine blade.

Uses a Weibull wind speed distribution (semi-arid Brazilian climate) and
S-N curve approach per IEC 61400-2 to compute 20-year cumulative damage.

Usage:
    python fatigue_analysis.py

    Prints fatigue damage summary with PASS/FAIL status.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Constants (matches blade_geometry.py)
# ---------------------------------------------------------------------------

# Material properties (from T032 calibration)
UTS_MPA: float = 12.5           # Ultimate tensile strength (MPa)
S_N_SLOPE_K: float = 10.0       # S-N curve slope for paper mache composite
                                 # (k=10 typical for polymer-matrix composites;
                                 #  k=5-8 for glass/epoxy, k=10+ for paper/polymer)

# Design parameters
BLADE_LENGTH_M: float = 3.5
NUM_BLADES: int = 3
HUB_RADIUS_M: float = 0.15
ROTOR_RADIUS_M: float = BLADE_LENGTH_M + HUB_RADIUS_M

# Design wind speeds (from blade_geometry.py)
RATED_WIND_MS: float = 8.0
EXTREME_WIND_MS: float = 40.0
CUT_IN_WIND_MS: float = 3.0
CUT_OUT_WIND_MS: float = 25.0

# Weibull wind parameters (semi-arid Northeast Brazil)
WEIBULL_SHAPE: float = 2.0      # Shape parameter k (typical 1.5-2.5)
WEIBULL_SCALE: float = 6.5      # Scale parameter c (m/s) — semi-arid average

# Turbine operational parameters
DESIGN_LIFE_YEARS: float = 20.0
RATED_RPM: float = 125.0        # Approx RPM at rated wind (TSR ~6 for small turbine)
AVAILABILITY: float = 0.90      # 90% operational availability
OPERATING_HOURS_PER_YEAR: float = 8760.0 * AVAILABILITY

# Fatigue limit ratio (stress below which infinite life)
# For paper composites: ~30% of UTS
FATIGUE_LIMIT_RATIO: float = 0.30

# Number of wind speed bins for integration
NUM_WIND_BINS: int = 50

# Safety factor on fatigue (per IEC 61400-2)
FATIGUE_SAFETY_FACTOR: float = 2.0

# ---------------------------------------------------------------------------
# Wind regime model
# ---------------------------------------------------------------------------


@dataclass
class WeibullWind:
    """Weibull distribution for wind speed.

    Attributes:
        shape: Shape parameter k (dimensionless).
        scale: Scale parameter c (m/s).
    """
    shape: float = WEIBULL_SHAPE
    scale: float = WEIBULL_SCALE

    def pdf(self, v: float) -> float:
        """Probability density function at wind speed v (m/s)."""
        if v <= 0:
            return 0.0
        return (
            (self.shape / self.scale)
            * (v / self.scale) ** (self.shape - 1.0)
            * math.exp(-((v / self.scale) ** self.shape))
        )

    def cdf(self, v: float) -> float:
        """Cumulative distribution function at wind speed v (m/s)."""
        if v <= 0:
            return 0.0
        return 1.0 - math.exp(-((v / self.scale) ** self.shape))

    def probability_bin(self, v_low: float, v_high: float) -> float:
        """Probability of wind speed in [v_low, v_high]."""
        return self.cdf(v_high) - self.cdf(v_low)


# ---------------------------------------------------------------------------
# S-N curve model
# ---------------------------------------------------------------------------


@dataclass
class SCurve:
    """S-N (Wöhler) curve for the composite material.

    N_f = (S_uts / S_a) ^ k     for S_a > fatigue_limit
    N_f = infinity                for S_a <= fatigue_limit

    Attributes:
        uts_mpa: Ultimate tensile strength (MPa).
        slope_k: Slope of S-N curve in log-log space.
        fatigue_limit_ratio: Stress ratio below which infinite life.
    """
    uts_mpa: float = UTS_MPA
    slope_k: float = S_N_SLOPE_K
    fatigue_limit_ratio: float = FATIGUE_LIMIT_RATIO

    @property
    def fatigue_limit_mpa(self) -> float:
        """Fatigue endurance limit (MPa)."""
        return self.uts_mpa * self.fatigue_limit_ratio

    def cycles_to_failure(self, stress_range_mpa: float) -> float:
        """Number of cycles to failure at given stress range (MPa).

        Args:
            stress_range_mpa: Alternating stress amplitude (MPa).

        Returns:
            Cycles to failure. Returns infinity if stress <= fatigue limit.
        """
        if stress_range_mpa <= self.fatigue_limit_mpa:
            return float("inf")
        return (self.uts_mpa / stress_range_mpa) ** self.slope_k


# ---------------------------------------------------------------------------
# Load model — aerodynamic stress proportional to dynamic pressure
# ---------------------------------------------------------------------------


class LoadModel:
    """Fatigue load model — turbulence-based alternating stress.

    For a wind turbine blade, the primary fatigue damage comes from
    turbulent wind fluctuations around the mean, not the steady bending
    stress. This model uses the IEC 61400-2 Normal Turbulence Model (NTM)
    to estimate the alternating stress component.

    Per IEC 61400-2, the standard deviation of wind turbulence is:
      sigma_u = I_ref * (0.75 * V_avg + 5.6)   [Class S, eq. 4.6]

    The characteristic alternating stress range (2*sigma) at a given
    mean wind speed is proportional to:
      sigma_alt(v) = sigma_steady(v) * (2 * sigma_u(v) / v)

    Where:
      sigma_steady(v) = steady bending stress at mean wind speed v
      sigma_u(v)      = standard deviation of wind speed at v
      sigma_u(v)/v    = turbulence intensity at v (dimensionless)
      2 * sigma_u(v)  = 2-standard-deviation range (95% of fluctuations)

    Reference stress (steady bending at rated 8 m/s):
      Analytical beam model with NACA 0018 at root, 120 Pa surface pressure,
      M = 0.5*w*L^2 ~ 257 Nm, section modulus ~ 0.003 m^3,
      sigma ~ 86 kPa. Conservative: 0.5 MPa including safety margin.

    This approach accounts for the fact that for a lightweight composite
    blade (~12 kg), gravity-induced alternating stress is negligible and
    the primary fatigue mechanism is wind turbulence.

    References:
      - IEC 61400-2:2013, Section 7.4, Normal Turbulence Model
      - Burton et al., Wind Energy Handbook, 3rd ed., Ch. 8
    """

    # Steady bending stress at rated wind (8 m/s), MPa, at blade root
    REF_STRESS_RATED_MPA: float = 0.5

    # Stress concentration factor (root geometry + material discontinuity)
    STRESS_CONCENTRATION: float = 2.0

    # Turbulence class IV per IEC 61400-2 (flat semi-arid terrain)
    TURBULENCE_INTENSITY_REF: float = 0.12

    def __init__(
        self,
        ref_stress_mpa: float = REF_STRESS_RATED_MPA,
        scf: float = STRESS_CONCENTRATION,
        turbulence_intensity: float = TURBULENCE_INTENSITY_REF,
    ):
        self.ref_stress_mpa = ref_stress_mpa
        self.scf = scf
        self.turbulence_intensity = turbulence_intensity

    def steady_stress_at_wind(self, v_ms: float) -> float:
        """Steady (mean) bending stress at given wind speed (MPa).

        Scales with dynamic pressure: sigma ∝ 0.5 * rho * v^2.
        """
        load_ratio = (v_ms / RATED_WIND_MS) ** 2
        return self.ref_stress_mpa * load_ratio * self.scf

    def turb_std_dev(self, v_ms: float) -> float:
        """Standard deviation of wind speed due to turbulence (m/s).

        Per IEC 61400-2 NTM:
          sigma_u(v) = I_ref * (0.75 * v + 5.6)

        Args:
            v_ms: Mean wind speed (m/s).

        Returns:
            Standard deviation of turbulent fluctuations (m/s).
        """
        return self.turbulence_intensity * (0.75 * v_ms + 5.6)

    def alternating_stress_at_wind(self, v_ms: float) -> float:
        """Characteristic alternating stress amplitude at mean wind v (MPa).

        The alternating component is the steady stress scaled by the
        turbulence intensity at that wind speed. The factor 2 captures
        the 2-standard-deviation range of the load spectrum.

        sigma_alt(v) = sigma_steady(v) * (2 * sigma_u(v) / v)

        Args:
            v_ms: Mean wind speed (m/s).

        Returns:
            Alternating stress amplitude for fatigue (MPa).
        """
        if v_ms <= 0:
            return 0.0
        steady = self.steady_stress_at_wind(v_ms)
        sigma_u = self.turb_std_dev(v_ms)
        turb_coeff = 2.0 * sigma_u / v_ms
        return steady * turb_coeff


# ---------------------------------------------------------------------------
# Fatigue damage computation
# ---------------------------------------------------------------------------


@dataclass
class FatigueResult:
    """Fatigue analysis results.

    Attributes:
        cumulative_damage_D: Palmgren-Miner cumulative damage (D < 1.0 PASS).
        design_life_years: Design life used in analysis.
        equivalent_stress_mpa: Equivalent constant-amplitude stress (MPa).
        num_wind_bins: Number of wind speed bins used.
        status: PASS if D < 1.0, FAIL otherwise.
        total_reference_cycles: Total reference cycles over design life.
    """
    cumulative_damage_D: float
    design_life_years: float
    equivalent_stress_mpa: float
    num_wind_bins: int
    status: str
    total_reference_cycles: float

    def summary(self) -> str:
        """Multi-line fatigue analysis summary."""
        lines = [
            f"Fatigue Analysis Summary:",
            f"  Design life:              {self.design_life_years:.0f} years",
            f"  Palmgen-Miner D:          {self.cumulative_damage_D:.4f}",
            f"  Equivalent stress (MPa):  {self.equivalent_stress_mpa:.3f}",
            f"  Total ref. cycles:        {self.total_reference_cycles:.2e}",
            f"  Wind bins:                {self.num_wind_bins}",
            f"  IEC 61400-2 D < 1.0:      {self.status}",
        ]
        return "\n".join(lines)


def compute_fatigue_damage(
    s_curve: SCurve,
    wind: WeibullWind,
    load_model: LoadModel,
    design_life_years: float = DESIGN_LIFE_YEARS,
    num_bins: int = NUM_WIND_BINS,
) -> FatigueResult:
    """Compute Palmgren-Miner cumulative fatigue damage.

    Integrates over the Weibull wind speed distribution to compute
    total fatigue damage over the design life.

    Args:
        s_curve: S-N curve model.
        wind: Weibull wind distribution.
        load_model: Load-stress relationship.
        design_life_years: Design life in years.
        num_bins: Number of wind speed bins.

    Returns:
        FatigueResult with cumulative damage and status.
    """
    # Cycles per year at rated RPM (one cycle = one revolution)
    cycles_per_year = RATED_RPM * 60.0 * OPERATING_HOURS_PER_YEAR

    # Wind speed bins from cut-in to cut-out
    v_step = (CUT_OUT_WIND_MS - CUT_IN_WIND_MS) / num_bins

    total_damage = 0.0
    max_cycles_to_failure = 0.0
    dominant_stress = 0.0

    for i in range(num_bins):
        v_low = CUT_IN_WIND_MS + i * v_step
        v_high = v_low + v_step
        v_mid = (v_low + v_high) / 2.0

        # Probability of wind in this bin
        p_bin = wind.probability_bin(v_low, v_high)

        # Cycles in this bin over design life
        n_cycles = p_bin * cycles_per_year * design_life_years

        # Stress amplitude at this wind speed (turbulence-based)
        stress = load_model.alternating_stress_at_wind(v_mid)

        # Cycles to failure at this stress level
        n_failure = s_curve.cycles_to_failure(stress)

        # Palmgren-Miner damage increment
        if math.isfinite(n_failure) and n_failure > 0:
            d_increment = n_cycles / n_failure
            total_damage += d_increment

            if n_failure > max_cycles_to_failure and n_cycles > 0:
                max_cycles_to_failure = n_failure
                dominant_stress = stress

    # Equivalent constant-amplitude stress for total damage
    total_cycles = cycles_per_year * design_life_years
    if total_damage > 0:
        # Damage-equivalent stress at 1 Hz over design life
        neq = total_cycles
        eq_stress = s_curve.uts_mpa * (total_damage / neq) ** (1.0 / s_curve.slope_k)
    else:
        eq_stress = 0.0

    # Apply fatigue safety factor per IEC 61400-2
    damage_with_sf = total_damage * FATIGUE_SAFETY_FACTOR

    status = "PASS" if damage_with_sf < 1.0 else "FAIL"

    return FatigueResult(
        cumulative_damage_D=round(damage_with_sf, 6),
        design_life_years=design_life_years,
        equivalent_stress_mpa=round(eq_stress, 4) if math.isfinite(eq_stress) else 0.0,
        num_wind_bins=num_bins,
        status=status,
        total_reference_cycles=round(total_cycles),
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    s_curve = SCurve()
    wind = WeibullWind()
    load_model = LoadModel()

    print("=" * 70)
    print("  T042 — Blade Fatigue Analysis (IEC 61400-2)")
    print("=" * 70)
    print(f"  Material:    Paper mache + graphite composite")
    print(f"  UTS:         {UTS_MPA} MPa")
    print(f"  S-N slope:   k = {S_N_SLOPE_K}")
    print(f"  Fatigue lim: {s_curve.fatigue_limit_mpa:.2f} MPa ({FATIGUE_LIMIT_RATIO*100:.0f}% UTS)")
    print(f"  Wind:        Weibull({WEIBULL_SHAPE}, {WEIBULL_SCALE}) m/s")
    print(f"  Life:        {DESIGN_LIFE_YEARS} years")
    print(f"  Safety fac:  {FATIGUE_SAFETY_FACTOR:.1f}")
    print()

    result = compute_fatigue_damage(s_curve, wind, load_model)
    print(result.summary())
    print()

    # Per-bin breakdown (top 5 contributing wind speeds)
    print("  Wind speed damage contribution:")
    cycles_per_year = RATED_RPM * 60.0 * OPERATING_HOURS_PER_YEAR
    v_step = (CUT_OUT_WIND_MS - CUT_IN_WIND_MS) / NUM_WIND_BINS
    contributors = []

    for i in range(NUM_WIND_BINS):
        v_low = CUT_IN_WIND_MS + i * v_step
        v_high = v_low + v_step
        v_mid = (v_low + v_high) / 2.0
        p_bin = wind.probability_bin(v_low, v_high)
        stress = load_model.alternating_stress_at_wind(v_mid)
        n_failure = s_curve.cycles_to_failure(stress)
        n_cycles = p_bin * cycles_per_year * DESIGN_LIFE_YEARS
        if math.isfinite(n_failure) and n_failure > 0 and n_cycles > 0:
            d_inc = n_cycles / n_failure
            contributors.append((v_mid, p_bin, stress, n_failure, d_inc))

    if contributors:
        contributors.sort(key=lambda x: x[4], reverse=True)
        print(f"  Top 5 contributors:")
        print(f"  {'v (m/s)':<12} {'p_bin':<12} {'Stress(MPa)':<14} {'N_fail':<14} {'D_inc':<12}")
        print(f"  {'-'*64}")
        for v, p, s, nf, di in contributors[:5]:
            nf_str = f"{nf:.2e}" if math.isfinite(nf) else "inf"
            print(f"  {v:<12.2f} {p:<12.6f} {s:<14.4f} {nf_str:<14} {di:<12.2e}")
    else:
        # All stresses below fatigue limit — find max alternation for info
        max_stress = max(
            load_model.alternating_stress_at_wind(CUT_IN_WIND_MS + (i + 0.5) * v_step)
            for i in range(NUM_WIND_BINS)
        )
        margin = s_curve.fatigue_limit_mpa / max_stress if max_stress > 0 else float("inf")
        print(f"  All alternating stresses below fatigue limit ({s_curve.fatigue_limit_mpa:.2f} MPa).")
        print(f"  Max alternating stress: {max_stress:.4f} MPa  (fatigue margin: {margin:.1f}x)")
        print(f"  Infinite fatigue life — no damage accumulation.")

    print()
    print(f"  Fatigue limit stress: {s_curve.fatigue_limit_mpa:.2f} MPa")
    print(f"  Operating range: {CUT_IN_WIND_MS:.0f}-{CUT_OUT_WIND_MS:.0f} m/s")
    print()

    # SC-003 status
    if result.status == "PASS":
        print(f"  {'SC-003 (Fatigue)':30s} ✅ PASS (D={result.cumulative_damage_D:.4f} < 1.0)")
    else:
        print(f"  {'SC-003 (Fatigue)':30s} ❌ FAIL (D={result.cumulative_damage_D:.4f} >= 1.0)")

    print("=" * 70)


def _debug_self_check() -> None:
    """Self-check: verify basic physical consistency."""
    s_curve = SCurve()
    wind = WeibullWind()
    load_model = LoadModel()

    # Self-check 1: Steady stress at rated wind should equal ref * scf
    s_steady_rated = load_model.steady_stress_at_wind(RATED_WIND_MS)
    assert abs(s_steady_rated - load_model.REF_STRESS_RATED_MPA * load_model.STRESS_CONCENTRATION) < 1e-6, \
        f"Rated steady stress mismatch: {s_steady_rated}"

    # Self-check 2: Alternating stress should be less than steady stress
    s_alt_rated = load_model.alternating_stress_at_wind(RATED_WIND_MS)
    assert s_alt_rated < s_steady_rated, \
        f"Alternating stress ({s_alt_rated}) must be < steady stress ({s_steady_rated})"

    # Self-check 3: Weibull CDF at large v should approach 1
    assert wind.cdf(50.0) > 0.99, "Weibull CDF at 50 m/s should be near 1"

    # Self-check 4: Fatigue limit should be less than UTS
    assert s_curve.fatigue_limit_mpa < s_curve.uts_mpa, "Fatigue limit must be < UTS"

    # Self-check 5: Cycles to failure at UTS should be 1
    n_at_uts = s_curve.cycles_to_failure(s_curve.uts_mpa)
    assert abs(n_at_uts - 1.0) < 1e-6, f"Cycles at UTS should be 1, got {n_at_uts}"

    # Self-check 6: Cycles below fatigue limit should be infinite
    n_below = s_curve.cycles_to_failure(s_curve.fatigue_limit_mpa * 0.5)
    assert math.isinf(n_below), "Stress below fatigue limit should give infinite life"

    print(f"  [OK] All self-checks passed.")


if __name__ == "__main__":
    _debug_self_check()
    print()
    main()
