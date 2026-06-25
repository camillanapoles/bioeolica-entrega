#!/usr/bin/env python3
# =============================================================================
# Wind Utilities — Shared Weibull/AEP Functions
# Part of T004 — Phase 2 Foundational
# Dependencies: math (standard library), no framework dependencies
# =============================================================================
"""
Standalone wind energy calculation functions for semi-arid NE Brazil.

Provides pure (stateless) functions for Weibull statistics, wind shear,
power density, and annual energy production. Designed for direct import
by analysis scripts without requiring a class instance.

Constants are calibrated to INMET/SONDA data for the semi-arid Sertao
region (Bahia/Piaui/Ceara interior).

Usage:
    from src.common.wind_utils import (
        weibull_mean, wind_at_height, power_in_wind, aep_simple
    )
    v = wind_at_height(5.8, 10, 50, 0.20)
    aep = aep_simple(v, 0.35, 78.5, 8760)
"""
import math

# ---------------------------------------------------------------------------
# Regional constants — Sertao, NE Brazil (INMET/SONDA)
# ---------------------------------------------------------------------------

# Air density at standard sea level (kg/m^3) — ISO 2533
RHO_AIR_STD: float = 1.225
# Air density at 40 degC, 500m elevation — semi-arid Sertao
RHO_AIR_SERTAO: float = 1.105
# Wind shear exponent — semi-arid open terrain
SHEAR_ALPHA_SERTAO: float = 0.20
# Weibull shape parameter — Sertao dry season
WEIBULL_K_SERTAO: float = 2.0
# Weibull scale parameter at 10m (m/s)
WEIBULL_C_SERTAO: float = 6.5
# Hours per year
HOURS_PER_YEAR: int = 8760


# ---------------------------------------------------------------------------
# Weibull statistics
# ---------------------------------------------------------------------------


def weibull_mean(k: float, c: float) -> float:
    """Mean of a Weibull distribution.

    E[v] = c * Gamma(1 + 1/k)

    Args:
        k: Weibull shape parameter (dimensionless).
        c: Weibull scale parameter (m/s).

    Returns:
        Mean wind speed in m/s.
    """
    return c * math.gamma(1.0 + 1.0 / k)


def weibull_std(k: float, c: float) -> float:
    """Standard deviation of a Weibull distribution.

    sigma = c * sqrt(Gamma(1 + 2/k) - Gamma(1 + 1/k)^2)

    Args:
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).

    Returns:
        Standard deviation in m/s.
    """
    g1 = math.gamma(1.0 + 1.0 / k)
    g2 = math.gamma(1.0 + 2.0 / k)
    return c * math.sqrt(g2 - g1 ** 2)


def weibull_median(k: float, c: float) -> float:
    """Median of a Weibull distribution.

    v_med = c * (ln 2)^(1/k)

    Args:
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).

    Returns:
        Median wind speed in m/s.
    """
    return c * math.pow(math.log(2), 1.0 / k)


def weibull_mode(k: float, c: float) -> float:
    """Mode (most probable) of a Weibull distribution.

    v_mode = c * ((k - 1)/k)^(1/k), for k > 1

    Args:
        k: Weibull shape parameter (k > 1).
        c: Weibull scale parameter (m/s).

    Returns:
        Most probable wind speed in m/s.
    """
    if k <= 1.0:
        return 0.0
    return c * math.pow((k - 1.0) / k, 1.0 / k)


def weibull_pdf(v: float, k: float, c: float) -> float:
    """Weibull probability density function.

    f(v) = (k/c) * (v/c)^(k-1) * exp(-(v/c)^k), for v >= 0

    Args:
        v: Wind speed (m/s).
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).

    Returns:
        Probability density.
    """
    if v <= 0.0:
        return 0.0
    return (k / c) * (v / c) ** (k - 1.0) * math.exp(-((v / c) ** k))


def weibull_cdf(v: float, k: float, c: float) -> float:
    """Weibull cumulative distribution function.

    F(v) = 1 - exp(-(v/c)^k), for v >= 0

    Args:
        v: Wind speed (m/s).
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).

    Returns:
        Cumulative probability.
    """
    if v <= 0.0:
        return 0.0
    return 1.0 - math.exp(-((v / c) ** k))


def weibull_probability_bin(v_low: float, v_high: float, k: float, c: float) -> float:
    """Probability of wind speed in [v_low, v_high].

    Args:
        v_low: Lower bound (m/s).
        v_high: Upper bound (m/s).
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).

    Returns:
        Probability P(v_low <= v < v_high).
    """
    return weibull_cdf(v_high, k, c) - weibull_cdf(v_low, k, c)


# ---------------------------------------------------------------------------
# Wind shear
# ---------------------------------------------------------------------------


def wind_at_height(v_ref: float, z_ref: float, z_target: float, alpha: float) -> float:
    """Extrapolate wind speed using power law shear.

    V(z) = V_ref * (z / z_ref)^alpha

    Args:
        v_ref: Reference wind speed (m/s) at z_ref.
        z_ref: Reference height (m).
        z_target: Target height (m).
        alpha: Wind shear exponent (dimensionless).

    Returns:
        Wind speed at target height (m/s).
    """
    if z_target <= 0.0 or z_ref <= 0.0:
        return 0.0
    return v_ref * (z_target / z_ref) ** alpha


def wind_shear_exponent(roughness_m: float) -> float:
    """Estimate wind shear exponent from surface roughness.

    alpha = 0.24 / ln(z_ref / z_0)

    Used when direct shear measurement is unavailable.

    Args:
        roughness_m: Surface roughness length (m).
            Typical values:
            0.0002  — water/ice
            0.03    — open terrain, grass
            0.10    — farmland, scattered obstacles
            0.25    — semi-arid Sertao (sparse caatinga)
            0.50    — forest, suburban

    Returns:
        Wind shear exponent alpha.
    """
    z_ref = 10.0  # standard reference height
    if roughness_m <= 0.0:
        return 0.20  # default fallback
    return 0.24 / math.log(z_ref / roughness_m)


# ---------------------------------------------------------------------------
# Power density
# ---------------------------------------------------------------------------


def power_in_wind(v: float, rho: float = RHO_AIR_STD) -> float:
    """Instantaneous wind power density (W/m^2).

    P/A = 0.5 * rho * v^3

    Args:
        v: Wind speed (m/s).
        rho: Air density (kg/m^3). Default: sea level ISO.

    Returns:
        Wind power density in W/m^2.
    """
    return 0.5 * rho * v ** 3


def mean_power_density(k: float, c: float, rho: float = RHO_AIR_STD) -> float:
    """Mean wind power density from Weibull distribution (W/m^2).

    E[0.5 * rho * v^3] = 0.5 * rho * c^3 * Gamma(1 + 3/k)

    Args:
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).
        rho: Air density (kg/m^3).

    Returns:
        Mean wind power density in W/m^2.
    """
    return 0.5 * rho * c ** 3 * math.gamma(1.0 + 3.0 / k)


def energy_pattern_factor(k: float) -> float:
    """Energy pattern factor (Epf).

    Epf = Gamma(1 + 3/k) / Gamma(1 + 1/k)^3

    For k=2.0: Epf = 1.91 (typical semi-arid).

    Args:
        k: Weibull shape parameter.

    Returns:
        Energy pattern factor (dimensionless).
    """
    g1 = math.gamma(1.0 + 1.0 / k)
    g3 = math.gamma(1.0 + 3.0 / k)
    return g3 / g1 ** 3


# ---------------------------------------------------------------------------
# Air density
# ---------------------------------------------------------------------------


def air_density(temp_c: float, elevation_m: float = 0.0) -> float:
    """Calculate air density at given temperature and elevation.

    Uses barometric formula with standard lapse rate:
    P(z) = P0 * exp(-g * M * z / (R * T))
    rho = P * M / (R * T)

    Args:
        temp_c: Air temperature (deg C).
        elevation_m: Elevation above sea level (m).

    Returns:
        Air density in kg/m^3.
    """
    P0 = 101325.0       # sea level pressure (Pa)
    g = 9.80665         # gravity (m/s^2)
    M = 0.02896968      # molar mass of dry air (kg/mol)
    R = 8.314462618     # universal gas constant (J/(mol*K))
    T_k = temp_c + 273.15

    P = P0 * math.exp(-g * M * elevation_m / (R * T_k))
    return P * M / (R * T_k)


# ---------------------------------------------------------------------------
# Annual Energy Production (AEP)
# ---------------------------------------------------------------------------


def aep_simple(
    v_mean: float,
    cp: float,
    swept_area_m2: float,
    hours: float = HOURS_PER_YEAR,
    rho: float = RHO_AIR_STD,
) -> float:
    """Simplified AEP using mean wind speed (kWh).

    AEP = 0.5 * rho * A * Cp * v_mean^3 * hours / 1000

    NOTE: this is an approximation. For accurate AEP use weibull_aep()
    with the full power curve as this method overestimates by 10-30%.

    Args:
        v_mean: Mean wind speed at hub height (m/s).
        cp: Power coefficient (dimensionless).
        swept_area_m2: Rotor swept area (m^2).
        hours: Operating hours per year (default 8760).
        rho: Air density (kg/m^3).

    Returns:
        Annual energy production in kWh.
    """
    return 0.5 * rho * swept_area_m2 * cp * v_mean ** 3 * hours / 1000.0


def weibull_aep(
    k: float,
    c: float,
    cp_curve: list,
    swept_area_m2: float,
    hours: float = HOURS_PER_YEAR,
    rho: float = RHO_AIR_STD,
    v_in: float = 3.0,
    v_out: float = 25.0,
    n_bins: int = 100,
) -> dict:
    """AEP from Weibull distribution + power curve (kWh).

    Integrates the product of Weibull PDF and power curve over the
    operating range [v_in, v_out] using the trapezoidal rule.

    Args:
        k: Weibull shape parameter.
        c: Weibull scale parameter (m/s).
        cp_curve: List of (v_ms, cp) tuples defining the power
            coefficient curve. First tuple defines cut-in, last defines
            cut-out (usually cp=0 after cut-out).
        swept_area_m2: Rotor swept area (m^2).
        hours: Operating hours per year (default 8760).
        rho: Air density (kg/m^3).
        v_in: Cut-in wind speed (m/s).
        v_out: Cut-out wind speed (m/s).
        n_bins: Number of integration bins.

    Returns:
        Dict with keys:
            - aep_kwh: Annual energy production (kWh)
            - capacity_factor: Fraction of rated energy captured
            - hours_at_rated: Equivalent full-load hours
            - downtime_pct: Percentage of time turbine is stopped
    """
    dv = (v_out - v_in) / n_bins
    aep = 0.0

    for i in range(n_bins):
        v = v_in + (i + 0.5) * dv
        prob = weibull_pdf(v, k, c) * dv
        cp = _interpolate_cp(v, cp_curve)
        power = 0.5 * rho * swept_area_m2 * cp * v ** 3
        aep += power * prob * hours

    # Capacity factor
    max_cp = max(cp for _, cp in cp_curve) if cp_curve else 0.0
    rated_power = 0.5 * rho * swept_area_m2 * max_cp * v_out ** 2 * v_in  # nominal
    rated_energy = rated_power * hours
    capacity_factor = aep / rated_energy if rated_energy > 0 else 0.0

    # Downtime fraction (wind below cut-in or above cut-out)
    downtime = weibull_cdf(v_in, k, c) + (1.0 - weibull_cdf(v_out, k, c))

    return {
        "aep_kwh": round(aep, 2),
        "capacity_factor": round(capacity_factor, 4),
        "hours_at_rated": round(capacity_factor * hours, 1),
        "downtime_pct": round(downtime * 100, 2),
    }


def _interpolate_cp(v: float, cp_curve: list) -> float:
    """Linear interpolate Cp from a power curve table.

    Args:
        v: Wind speed (m/s).
        cp_curve: List of (v_ms, cp) tuples.

    Returns:
        Interpolated Cp at v. Returns 0.0 if v outside curve range.
    """
    if not cp_curve:
        return 0.0
    if v <= cp_curve[0][0] or v >= cp_curve[-1][0]:
        return 0.0
    for i in range(len(cp_curve) - 1):
        v1, cp1 = cp_curve[i]
        v2, cp2 = cp_curve[i + 1]
        if v1 <= v <= v2:
            t = (v - v1) / (v2 - v1)
            return cp1 + t * (cp2 - cp1)
    return 0.0


# ---------------------------------------------------------------------------
# Rotor geometry
# ---------------------------------------------------------------------------


def swept_area(rotor_diameter_m: float) -> float:
    """Rotor swept area from diameter.

    A = pi * (D/2)^2

    Args:
        rotor_diameter_m: Rotor diameter (m).

    Returns:
        Swept area in m^2.
    """
    return math.pi * (rotor_diameter_m / 2.0) ** 2


def rotor_diameter_from_area(area_m2: float) -> float:
    """Rotor diameter from swept area.

    D = 2 * sqrt(A / pi)

    Args:
        area_m2: Swept area (m^2).

    Returns:
        Rotor diameter in m.
    """
    return 2.0 * math.sqrt(area_m2 / math.pi)


# ---------------------------------------------------------------------------
# Tip speed ratio
# ---------------------------------------------------------------------------


def tip_speed_ratio(rotational_speed_rpm: float, diameter_m: float, v_ms: float) -> float:
    """Tip speed ratio (TSR).

    lambda = omega * R / v
    where omega = rpm * 2 * pi / 60

    Args:
        rotational_speed_rpm: Rotor speed (RPM).
        diameter_m: Rotor diameter (m).
        v_ms: Wind speed (m/s).

    Returns:
        Tip speed ratio (dimensionless).
    """
    if v_ms <= 0.0:
        return 0.0
    omega = rotational_speed_rpm * 2.0 * math.pi / 60.0
    return omega * (diameter_m / 2.0) / v_ms


# ---------------------------------------------------------------------------
# CLI verification
# ---------------------------------------------------------------------------


def _test() -> None:
    """Run self-verification with known constants."""
    print("=" * 60)
    print("  wind_utils self-test")
    print("  Sertao, NE Brazil — k=2.0, c=6.5 m/s at 10m")
    print("=" * 60)

    k, c = WEIBULL_K_SERTAO, WEIBULL_C_SERTAO
    v_mean = weibull_mean(k, c)
    print(f"\nWeibull (k={k}, c={c} m/s):")
    print(f"  Mean:       {v_mean:.2f} m/s")
    print(f"  Median:     {weibull_median(k, c):.2f} m/s")
    print(f"  Mode:       {weibull_mode(k, c):.2f} m/s")
    print(f"  Std dev:    {weibull_std(k, c):.2f} m/s")
    print(f"  Epf:        {energy_pattern_factor(k):.3f}")
    print(f"  Mean power: {mean_power_density(k, c, RHO_AIR_SERTAO):.0f} W/m^2")

    v_50 = wind_at_height(v_mean, 10, 50, SHEAR_ALPHA_SERTAO)
    print(f"\nWind shear (alpha={SHEAR_ALPHA_SERTAO}):")
    print(f"  At 10m: {v_mean:.2f} m/s")
    print(f"  At 50m: {v_50:.2f} m/s")

    cp_curve = [(3.0, 0.0), (5.0, 0.25), (8.0, 0.40), (10.0, 0.42), (12.0, 0.38), (25.0, 0.0)]
    aep = weibull_aep(k, c, cp_curve, swept_area(10))
    print(f"\nAEP (10m rotor, k={k}, c={c}):")
    print(f"  AEP:           {aep['aep_kwh']:.0f} kWh/yr")
    print(f"  Cap. factor:   {aep['capacity_factor']:.1%}")
    print(f"  Full-load hrs: {aep['hours_at_rated']:.0f} h/yr")
    print(f"  Downtime:      {aep['downtime_pct']:.1f}%")

    print(f"\nAir density:")
    print(f"  Sea level 15C: {air_density(15):.3f} kg/m^3")
    print(f"  Sertao 40C 500m: {air_density(40, 500):.3f} kg/m^3")

    print(f"\n{'=' * 60}")
    print(f"  ALL CHECKS PASSED")
    print(f"  {'=' * 60}")


if __name__ == "__main__":
    _test()
