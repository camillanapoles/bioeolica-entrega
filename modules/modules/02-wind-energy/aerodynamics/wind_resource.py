#!/usr/bin/env python3
# =============================================================================
# Wind Resource Characterization — Composite Biomaterial for Wind Energy
# Phase 6 — Wind Energy System Sizing | T048
# Reference: INMET (Instituto Nacional de Meteorologia), SONDA (Sistema de
#            Organizacao Nacional de Dados Ambientais), semi-arid NE Brazil
# =============================================================================
"""
Wind resource characterization for semi-arid Northeast Brazil.

Uses Weibull distribution parameters calibrated to INMET/SONDA data for
the semi-arid Sertao region (Bahia/Piaui/Ceara interior). Provides:

  - Weibull annual distribution (shape k=2.0, scale c=6.5 m/s at 10m)
  - Wind shear extrapolation to hub heights (power law, alpha=0.20)
  - Monthly wind speed profiles (dry season peak, rainy season minimum)
  - Wind power density calculation
  - Turbulence intensity per IEC 61400-2 Class S

Typical semi-arid NE Brazil wind regime:
  - Annual mean at 10m: 5.8 m/s
  - Annual mean at 30m: 7.1 m/s
  - Prevailing direction: ESE (east-southeast)
  - Dry season (May-Oct): stronger, more consistent
  - Rainy season (Nov-Apr): weaker, more variable

Usage:
    python wind_resource.py

    Prints wind resource summary for the selected site.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

# Path setup
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Air density at 40°C, 500m elevation (semi-arid Sertao)
RHO_AIR_KG_M3 = 1.105

# Weibull parameters at 10m (INMET/SONDA stations: Juazeiro-BA, Petrolina-PE)
WEIBULL_SHAPE_K = 2.0
WEIBULL_SCALE_C_MS = 6.5

# Wind shear exponent (semi-arid open terrain, few obstacles)
SHEAR_ALPHA = 0.20

# Prevailing wind direction (meteorological degrees)
PREVAILING_DIRECTION_DEG = 110  # ESE

# Turbulence class (IEC 61400-2 Class S, semi-arid open terrain)
TURBULENCE_INTENSITY_REF = 0.12

# ---------------------------------------------------------------------------
# Wind regime model
# ---------------------------------------------------------------------------


@dataclass
class WeibullWindResource:
    """Weibull-based wind resource model.

    Attributes:
        shape: Weibull shape parameter k (dimensionless).
        scale: Weibull scale parameter c (m/s) at reference height.
        ref_height_m: Reference height for Weibull parameters.
        shear_alpha: Wind shear exponent (power law).
        rho_air: Air density (kg/m^3).
        turbulence_intensity: Reference turbulence intensity (Iref).
    """
    shape: float = WEIBULL_SHAPE_K
    scale: float = WEIBULL_SCALE_C_MS
    ref_height_m: float = 10.0
    shear_alpha: float = SHEAR_ALPHA
    rho_air: float = RHO_AIR_KG_M3
    turbulence_intensity: float = TURBULENCE_INTENSITY_REF

    def mean_wind_at_height(self, height_m: float) -> float:
        """Mean wind speed at a given height using power law shear.

        V(z) = V_ref * (z / z_ref)^alpha

        Args:
            height_m: Target height in meters.

        Returns:
            Mean wind speed in m/s.
        """
        if height_m <= 0:
            return 0.0
        mean_ref = self.scale * math.gamma(1.0 + 1.0 / self.shape)
        return mean_ref * (height_m / self.ref_height_m) ** self.shear_alpha

    def scale_at_height(self, height_m: float) -> float:
        """Weibull scale parameter at a given height."""
        mean_at_h = self.mean_wind_at_height(height_m)
        # c = mean / Gamma(1 + 1/k)
        return mean_at_h / math.gamma(1.0 + 1.0 / self.shape)

    def pdf(self, v: float, height_m: float | None = None) -> float:
        """Weibull PDF at a given wind speed and height.

        Args:
            v: Wind speed (m/s).
            height_m: Height in meters (defaults to ref_height_m).

        Returns:
            Probability density.
        """
        if v <= 0:
            return 0.0
        c = self.scale_at_height(height_m) if height_m else self.scale
        return (
            (self.shape / c)
            * (v / c) ** (self.shape - 1.0)
            * math.exp(-((v / c) ** self.shape))
        )

    def cdf(self, v: float, height_m: float | None = None) -> float:
        """Weibull CDF at a given wind speed and height."""
        if v <= 0:
            return 0.0
        c = self.scale_at_height(height_m) if height_m else self.scale
        return 1.0 - math.exp(-((v / c) ** self.shape))

    def probability_bin(
        self, v_low: float, v_high: float, height_m: float | None = None
    ) -> float:
        """Probability of wind speed in [v_low, v_high]."""
        return self.cdf(v_high, height_m) - self.cdf(v_low, height_m)

    def power_density(self, v_ms: float) -> float:
        """Instantaneous wind power density (W/m^2) at a given wind speed.

        P/A = 0.5 * rho * v^3
        """
        return 0.5 * self.rho_air * v_ms ** 3

    def mean_power_density(self, height_m: float | None = None) -> float:
        """Mean wind power density (W/m^2) from Weibull distribution.

        E[0.5 * rho * v^3] = 0.5 * rho * c^3 * Gamma(1 + 3/k)
        """
        c = self.scale_at_height(height_m) if height_m else self.scale
        return 0.5 * self.rho_air * c ** 3 * math.gamma(1.0 + 3.0 / self.shape)

    def energy_pattern_factor(self) -> float:
        """Energy pattern factor (Epf) — ratio of mean of cubes to cube of mean.

        Epf = Gamma(1 + 3/k) / Gamma(1 + 1/k)^3

        For k=2.0: Epf = 1.91 (typical for semi-arid sites)
        """
        g1 = math.gamma(1.0 + 1.0 / self.shape)
        g3 = math.gamma(1.0 + 3.0 / self.shape)
        return g3 / g1 ** 3

    def monthly_mean_winds(self) -> list[dict]:
        """Monthly mean wind speeds based on semi-arid NE Brazil seasonality.

        Returns:
            List of dicts with month, mean_wind_ms, and notes.
        """
        base = self.mean_wind_at_height(self.ref_height_m)
        # Seasonal modulation: dry season (May-Oct) stronger,
        # rainy season (Nov-Apr) weaker
        modulation = [
            -0.12,  # Jan (rainy peak)
            -0.10,  # Feb
            -0.08,  # Mar
            -0.05,  # Apr (transition)
            0.05,   # May (dry start)
            0.12,   # Jun
            0.18,   # Jul (peak dry)
            0.15,   # Aug
            0.10,   # Sep
            0.05,   # Oct (transition)
            -0.05,  # Nov (rainy start)
            -0.10,  # Dec
        ]
        months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        result = []
        for month, mod in zip(months, modulation):
            v = base * (1.0 + mod)
            result.append({
                "month": month,
                "mean_wind_ms": round(v, 2),
                "modulation": mod,
                "season": "rainy" if mod < 0 else "dry",
            })
        return result

    def turbulence_std(self, v_ms: float) -> float:
        """Standard deviation of turbulent fluctuations per IEC 61400-2 NTM.

        sigma_u = I_ref * (0.75 * v + 5.6)
        """
        return self.turbulence_intensity * (0.75 * v_ms + 5.6)

    def turbulence_intensity_at(self, v_ms: float) -> float:
        """Turbulence intensity at a given wind speed.

        TI(v) = sigma_u(v) / v
        """
        if v_ms <= 0:
            return 0.0
        return self.turbulence_std(v_ms) / v_ms

    def summary(self, height_m: float = 30.0) -> str:
        """Multi-line wind resource summary."""
        v_mean = self.mean_wind_at_height(height_m)
        mpd = self.mean_power_density(height_m)
        epf = self.energy_pattern_factor()

        lines = [
            f"Wind Resource Summary (Sertao NE Brazil):",
            f"  Weibull distribution:  k = {self.shape}, c = {self.scale} m/s at {self.ref_height_m}m",
            f"  Reference height:     {self.ref_height_m} m",
            f"  Target hub height:    {height_m} m",
            f"  Shear exponent:       {self.shear_alpha}",
            f"  Air density:          {self.rho_air} kg/m^3",
            f"",
            f"  Mean wind at {height_m}m:  {v_mean:.1f} m/s",
            f"  Scale c at {height_m}m:    {self.scale_at_height(height_m):.1f} m/s",
            f"  Energy pattern factor: {epf:.2f}",
            f"  Mean power density:    {mpd:.1f} W/m^2",
            f"  Annual energy flux:    {mpd * 8760 / 1000:.0f} kWh/m^2/yr",
            f"  Turbulence class:     Iref = {self.turbulence_intensity} (Class S)",
            f"",
            f"  Monthly means at {height_m}m:",
        ]
        for m in self.monthly_mean_winds():
            v_at_h = m["mean_wind_ms"] * (height_m / self.ref_height_m) ** self.shear_alpha
            lines.append(
                f"    {m['month']}: {v_at_h:.1f} m/s ({m['season']}, "
                f"mod {m['modulation']:+.0%})"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    resource = WeibullWindResource()

    print("=" * 72)
    print("  T048 — Wind Resource Characterization")
    print("  Semi-arid Sertao, Northeast Brazil (INMET/SONDA calibrated)")
    print("=" * 72)
    print()
    print(resource.summary(height_m=30.0))
    print()

    # Power density breakdown at typical heights
    print(f"  Wind power density by height:")
    print(f"  {'Height (m)':<12} {'Mean wind (m/s)':<18} {'Power dens. (W/m2)':<20} "
          f"{'Annual flux (kWh/m2)':<20}")
    print(f"  {'-' * 70}")
    for h in [10, 20, 30, 40, 50]:
        v = resource.mean_wind_at_height(h)
        pd = resource.mean_power_density(h)
        flux = pd * 8760 / 1000
        print(f"  {h:<12} {v:<18.2f} {pd:<20.1f} {flux:<20.0f}")
    print()
    print(f"  {'=' * 72}")
    print(f"  SC-005 wind resource: READY")
    print(f"  {'=' * 72}")


if __name__ == "__main__":
    main()
