#!/usr/bin/env python3
# =============================================================================
# Blade Geometry Definition — Composite Biomaterial for Wind Energy
# Phase 5 — Wind Turbine Blade Application | T038
# Reference: NACA 0018 symmetric airfoil, 3.5m blade length, 3 blades
# Material: Paper mache + graphite composite (calibrated properties)
# Design standard: IEC 61400-2 (small wind turbines)
# =============================================================================
"""
Blade geometry definition and STEP export for the paper mache + graphite
composite wind turbine blade.

Generates:
  - NACA 0018 airfoil coordinates at spanwise stations
  - 3D blade surface (twisted, tapered)
  - STEP file export for CAD/FEM import

Usage:
    python blade_geometry.py

    Prints blade geometry summary and exports STEP file.
    Can also be imported as a module::

        from src.common.blade_geometry import BladeGeometry, naca_0018_coordinates
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Design parameters (per IEC 61400-2, small wind)
BLADE_LENGTH_M = 3.5          # Blade length in meters
NUM_BLADES = 3                # Number of blades
HUB_RADIUS_M = 0.15           # Hub radius
ROTOR_RADIUS_M = BLADE_LENGTH_M + HUB_RADIUS_M  # Tip radius

# Aerodynamic profile
AIRFOIL = "NACA 0018"         # Symmetric profile, good for low Re
MAX_THICKNESS_PCT = 0.18      # t/c = 18%

# Twist distribution (linear from root to tip, degrees)
TWIST_ROOT_DEG = 12.0
TWIST_TIP_DEG = 2.0

# Chord distribution (linear taper from root to tip, meters)
CHORD_ROOT_M = 0.35
CHORD_TIP_M = 0.12

# Material properties (from calibrated composite model T032)
# Paper mache + graphite composite
E_MODULUS_MPA = 4669.0        # Effective Young's modulus (from T031 micro model)
POISSON_RATIO = 0.35          # Poisson ratio
DENSITY_KG_M3 = 920.0         # Composite density (paper mache ~800 + graphite ~1800 coating)
TENSILE_STRENGTH_MPA = 12.5   # Composite tensile strength
FLEXURAL_MODULUS_GPA = 3.8    # Flexural modulus
DENSITY_TONNE_MM3 = 920.0 / 1e9  # Density in tonne/mm^3 for CalculiX

# Design wind speeds
RATED_WIND_SPEED_MS = 8.0     # Rated wind speed (m/s)
EXTREME_WIND_SPEED_MS = 40.0  # Survival gust (m/s)
CUT_IN_WIND_SPEED_MS = 3.0    # Cut-in wind speed
CUT_OUT_WIND_SPEED_MS = 25.0  # Cut-out wind speed

# Number of spanwise stations for geometry definition
NUM_STATIONS = 11              # 0% to 100% in 10% increments

# ---------------------------------------------------------------------------
# NACA 0018 airfoil coordinates
# ---------------------------------------------------------------------------

def naca_0018_coordinates(
    num_points: int = 100,
    cosine_spacing: bool = True,
) -> List[Tuple[float, float]]:
    """Generate NACA 0018 symmetric airfoil coordinates.

    The 4-digit NACA 0018 profile has:
      - 0% camber (symmetric)
      - 0% max camber position
      - 18% maximum thickness-to-chord ratio

    Args:
        num_points: Number of points per side (upper + lower = 2 * num_points).
        cosine_spacing: Use cosine clustering near leading/trailing edges.

    Returns:
        List of (x, y) tuples for the full airfoil (upper surface then lower,
        starting at trailing edge, going around leading edge, back to trailing edge).
    """
    # Generate x stations
    if cosine_spacing:
        # Cosine: clustered near LE and TE
        beta = [math.pi * i / (num_points - 1) for i in range(num_points)]
        x = [(1.0 - math.cos(b)) / 2.0 for b in beta]
    else:
        x = [i / (num_points - 1) for i in range(num_points)]

    # NACA 4-digit thickness distribution
    # y_t = (t/0.2) * (0.2969*sqrt(x) - 0.1260*x - 0.3516*x^2 + 0.2843*x^3 - 0.1015*x^4)
    t = MAX_THICKNESS_PCT
    coefficients = (0.2969, -0.1260, -0.3516, 0.2843, -0.1015)

    def thickness_y(xc: float) -> float:
        return (t / 0.2) * (
            coefficients[0] * math.sqrt(xc)
            + coefficients[1] * xc
            + coefficients[2] * xc ** 2
            + coefficients[3] * xc ** 3
            + coefficients[4] * xc ** 4
        )

    # Upper surface: x from 0 to 1 (LE to TE)
    upper = [(xi, thickness_y(xi)) for xi in x]
    # Lower surface: x from 1 to 0 (TE to LE)
    lower = [(xi, -thickness_y(xi)) for xi in reversed(x)]

    return upper + lower


# ---------------------------------------------------------------------------
# Blade geometry dataclass
# ---------------------------------------------------------------------------

@dataclass
class SpanStation:
    """A single spanwise station of the blade.

    Attributes:
        fraction: Span fraction from root (0.0) to tip (1.0).
        radius_m: Distance from hub center (hub_radius + fraction * blade_length).
        chord_m: Chord length at this station.
        twist_deg: Twist angle at this station.
        airfoil: Airfoil profile name.
    """
    fraction: float
    radius_m: float
    chord_m: float
    twist_deg: float
    airfoil: str = "NACA 0018"


@dataclass
class BladeGeometry:
    """Complete blade geometry definition.

    Attributes:
        blade_length_m: Total blade length (root to tip).
        num_blades: Number of blades in rotor.
        hub_radius_m: Hub radius.
        stations: List of spanwise stations.
        airfoil_points: NACA airfoil coordinates (normalized, unit chord).
    """

    blade_length_m: float = BLADE_LENGTH_M
    num_blades: int = NUM_BLADES
    hub_radius_m: float = HUB_RADIUS_M
    stations: List[SpanStation] = field(default_factory=list)
    airfoil_points: List[Tuple[float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stations:
            self.stations = self._generate_stations()
        if not self.airfoil_points:
            self.airfoil_points = naca_0018_coordinates()

    @property
    def rotor_diameter_m(self) -> float:
        """Rotor diameter including hub."""
        return 2.0 * (self.blade_length_m + self.hub_radius_m)

    @property
    def swept_area_m2(self) -> float:
        """Rotor swept area."""
        r = self.blade_length_m + self.hub_radius_m
        return math.pi * r ** 2

    def _generate_stations(self) -> List[SpanStation]:
        """Generate spanwise stations with linear twist and taper."""
        stations = []
        for i in range(NUM_STATIONS):
            fraction = i / (NUM_STATIONS - 1) if NUM_STATIONS > 1 else 0.0
            radius = self.hub_radius_m + fraction * self.blade_length_m
            chord = CHORD_ROOT_M + fraction * (CHORD_TIP_M - CHORD_ROOT_M)
            twist = TWIST_ROOT_DEG + fraction * (TWIST_TIP_DEG - TWIST_ROOT_DEG)
            stations.append(SpanStation(
                fraction=fraction,
                radius_m=round(radius, 4),
                chord_m=round(chord, 4),
                twist_deg=round(twist, 2),
            ))
        return stations

    def get_station(self, fraction: float) -> SpanStation:
        """Interpolate station at an arbitrary span fraction (0-1).

        Args:
            fraction: Span fraction (0.0 = root, 1.0 = tip).

        Returns:
            Interpolated SpanStation.
        """
        if fraction <= self.stations[0].fraction:
            return self.stations[0]
        if fraction >= self.stations[-1].fraction:
            return self.stations[-1]

        for i in range(len(self.stations) - 1):
            s0 = self.stations[i]
            s1 = self.stations[i + 1]
            if s0.fraction <= fraction <= s1.fraction:
                t = (fraction - s0.fraction) / (s1.fraction - s0.fraction)
                return SpanStation(
                    fraction=fraction,
                    radius_m=s0.radius_m + t * (s1.radius_m - s0.radius_m),
                    chord_m=s0.chord_m + t * (s1.chord_m - s0.chord_m),
                    twist_deg=s0.twist_deg + t * (s1.twist_deg - s0.twist_deg),
                )
        return self.stations[-1]

    def chord_at(self, fraction: float) -> float:
        """Chord length at a given span fraction."""
        return self.get_station(fraction).chord_m

    def twist_at(self, fraction: float) -> float:
        """Twist angle (degrees) at a given span fraction."""
        return self.get_station(fraction).twist_deg

    def radius_at(self, fraction: float) -> float:
        """Radius from hub center at a given span fraction."""
        return self.get_station(fraction).radius_m

    def summary(self) -> str:
        """Multi-line geometry summary."""
        lines = [
            f"Blade Geometry Summary:",
            f"  Airfoil:          {AIRFOIL} (t/c = {MAX_THICKNESS_PCT:.0%})",
            f"  Blade length:     {self.blade_length_m:.1f} m",
            f"  Hub radius:       {self.hub_radius_m:.2f} m",
            f"  Rotor diameter:   {self.rotor_diameter_m:.1f} m",
            f"  Swept area:       {self.swept_area_m2:.1f} m^2",
            f"  Number of blades: {self.num_blades}",
            f"  Stations:         {len(self.stations)}",
            f"",
            f"  Twist range:      {TWIST_ROOT_DEG:.0f}° (root) to {TWIST_TIP_DEG:.0f}° (tip)",
            f"  Chord range:      {CHORD_ROOT_M:.2f} m (root) to {CHORD_TIP_M:.2f} m (tip)",
            f"",
            f"  Material:         Paper mache + graphite composite",
            f"  E_modulus:        {E_MODULUS_MPA:.0f} MPa",
            f"  Density:          {DENSITY_KG_M3:.0f} kg/m^3",
            f"  Tensile strength: {TENSILE_STRENGTH_MPA:.1f} MPa",
            f"",
            f"  Stations:",
        ]
        lines.append(f"  {'#':<4} {'Fraction':<10} {'Radius(m)':<12} "
                      f"{'Chord(m)':<12} {'Twist(°)':<10}")
        for i, s in enumerate(self.stations):
            lines.append(f"  {i:<4} {s.fraction:<10.2f} {s.radius_m:<12.4f} "
                          f"{s.chord_m:<12.4f} {s.twist_deg:<10.2f}")
        return "\n".join(lines)

    def to_step(self, filepath: str) -> str:
        """Export blade geometry as a simplified STEP file.

        The STEP file contains the lofted blade surface defined by airfoil
        sections at each span station, with appropriate scaling and rotation.

        Args:
            filepath: Output STEP file path.

        Returns:
            The absolute path to the generated STEP file.
        """
        abs_path = os.path.abspath(filepath)
        airfoil_pts = self.airfoil_points  # unit chord, normalized

        with open(abs_path, "w") as f:
            f.write("ISO-10303-21;\n")
            f.write("HEADER;\n")
            f.write(f"FILE_DESCRIPTION(('Blade geometry: {AIRFOIL}, "
                    f"{self.blade_length_m}m'),'2;1');\n")
            f.write(f"FILE_NAME('blade_{self.blade_length_m}m.stp',"
                    f"'{__file__}');\n")
            f.write("FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\n")
            f.write("ENDSEC;\n")
            f.write("DATA;\n")

            # Write each station as a set of points and a B-spline curve
            point_id = 1
            curve_id = 1
            for si, station in enumerate(self.stations):
                scale = station.chord_m
                angle_rad = math.radians(station.twist_deg)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)
                station_points = []

                for x_norm, y_norm in airfoil_pts:
                    # Scale to chord
                    x_local = x_norm * scale
                    y_local = y_norm * scale
                    # Rotate by twist angle
                    x_rot = x_local * cos_a - y_local * sin_a
                    y_rot = x_local * sin_a + y_local * cos_a
                    # Translate to station radius (blade along Y axis)
                    # Y = radial direction, X = chordwise, Z = thickness
                    z_pos = x_rot  # chordwise
                    x_pos = y_rot  # thickness
                    y_pos = station.radius_m  # span

                    f.write(f"#{point_id}=CARTESIAN_POINT('',"
                            f"({x_pos:.6f},{y_pos:.6f},{z_pos:.6f}));\n")
                    station_points.append(f"#{point_id}")
                    point_id += 1

                # B-spline curve for this station
                pts_str = ",".join(station_points)
                n_pts = len(station_points)
                f.write(f"#{curve_id}=B_SPLINE_CURVE_WITH_KNOTS('',{n_pts},"
                        f"({pts_str}),.UNSPECIFIED.,.F.,.F.,"
                        f"(4,{n_pts - 4}),.UNSPECIFIED.);\n")
                curve_id += 1

            f.write("ENDSEC;\n")
            f.write("END-ISO-10303-21;\n")

        return abs_path


# ---------------------------------------------------------------------------
# Default geometry instance
# ---------------------------------------------------------------------------

DEFAULT_BLADE = BladeGeometry()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    blade = DEFAULT_BLADE
    print("=" * 70)
    print("  T038 — Blade Geometry Definition")
    print("=" * 70)
    print()
    print(blade.summary())
    print()
    print(f"  Rotor diameter:  {blade.rotor_diameter_m:.2f} m")
    print(f"  Swept area:      {blade.swept_area_m2:.2f} m^2")
    print(f"  Tip speed ratio: {blade.rotor_diameter_m * math.pi * 1.0:.2f} m at 1 rad/s")
    print()

    # Export STEP
    step_dir = os.path.join(_project_root, "data", "geometry")
    os.makedirs(step_dir, exist_ok=True)
    step_path = os.path.join(step_dir, f"blade_{blade.blade_length_m}m.stp")
    exported = blade.to_step(step_path)
    print(f"  STEP file exported: {exported}")
    print("=" * 70)


if __name__ == "__main__":
    main()
