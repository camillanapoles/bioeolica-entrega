"""
erosion.py — Erosion Modeling Module
=====================================

Finnie erosion model for particle impact, depth of erosion vs particle
count and velocity, leading edge erosion for wind turbine blades,
erosion rate vs impact angle, and time to critical erosion depth.

Classes
-------
ErosionModel : Solid particle erosion prediction using Finnie's model.

Dependencies
------------
numpy, scipy (integrate, optimize, interpolate)

Usage Example
-------------
>>> import numpy as np
>>> from modules.erosion import ErosionModel
>>> em = ErosionModel(material_density=2700.0, hardness=3e9, k=2.0)
>>> depth, rate = em.finnie_erosion(mass=1e-6, velocity=50.0, angle=30.0)
>>> t_crit = em.time_to_failure(current_depth=0.5e-3, critical_depth=2e-3,
...                              erosion_rate=rate)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import integrate, interpolate, optimize


class ErosionModel:
    """Solid particle erosion prediction using Finnie's erosion model.

    Implements Finnie's erosion theory for ductile materials under
    particle impact, including angular dependence, velocity exponents,
    and cumulative damage. Extends to wind turbine blade leading edge
    erosion.

    Parameters
    ----------
    material_density : float
        Density of the target material (kg/m^3).
    hardness : float
        Hardness of the target material (Pa).
    k : float
        Finnie's empirical constant (dimensionless).
    n : float
        Velocity exponent (default 2.0 for Finnie).
    fracture_toughness : float or None
        Fracture toughness (Pa·m^0.5) for brittle erosion component.
    """

    def __init__(
        self,
        material_density: float = 2700.0,
        hardness: float = 3e9,
        k: float = 2.0,
        n: float = 2.0,
        fracture_toughness: float | None = None,
    ) -> None:
        if material_density <= 0.0:
            raise ValueError("Material density must be positive.")
        if hardness <= 0.0:
            raise ValueError("Hardness must be positive.")
        if k <= 0.0:
            raise ValueError("Constant k must be positive.")
        if n <= 0.0:
            raise ValueError("Velocity exponent n must be positive.")

        self.material_density = float(material_density)
        self.hardness = float(hardness)
        self.k = float(k)
        self.n = float(n)
        self.fracture_toughness = (
            float(fracture_toughness) if fracture_toughness is not None else None
        )

    # ------------------------------------------------------------------
    # Finnie erosion model
    # ------------------------------------------------------------------

    def finnie_erosion(
        self,
        mass: float = 1e-6,
        velocity: float = 50.0,
        angle: float = 30.0,
        particle_density: float = 2650.0,
    ) -> dict[str, float]:
        """Compute erosion volume and rate using Finnie's model.

        Finnie's erosion model for a single particle impact:
            Q = (M * V^2) / (p * K) * f(alpha)

        where f(alpha) accounts for impact angle dependence.

        Parameters
        ----------
        mass : float
            Particle mass (kg).
        velocity : float
            Particle impact velocity (m/s).
        angle : float
            Impact angle measured from surface (degrees).
        particle_density : float
            Density of the erodent particle (kg/m^3).

        Returns
        -------
        dict
            Keys: 'volume_removed' (m^3), 'mass_loss' (kg),
            'erosion_rate' (kg/kg), 'depth_per_particle' (m),
            'angle_function' (dimensionless).
        """
        if mass <= 0.0:
            raise ValueError("Particle mass must be positive.")
        if velocity <= 0.0:
            raise ValueError("Velocity must be positive.")
        if not (0.0 < angle <= 90.0):
            raise ValueError("Impact angle must be in (0, 90] degrees.")

        alpha = np.radians(float(angle))
        M, V, H, K = float(mass), float(velocity), self.hardness, self.k

        # Angle function for ductile erosion (Finnie)
        sin2a = np.sin(2.0 * alpha)
        sin2a2 = np.sin(alpha) ** 2.0

        if alpha <= np.radians(45.0):
            angle_fn = sin2a - 3.0 * sin2a2
        else:
            angle_fn = (1.0 / 3.0) * np.cos(alpha) ** 2.0

        angle_fn = max(angle_fn, 0.0)

        # Volume removed (Finnie)
        volume = (M * V**self.n) / (H * K) * angle_fn

        # Mass loss
        mass_loss = volume * self.material_density

        # Erosion rate (kg removed per kg erodent)
        erosion_rate = mass_loss / max(M, 1e-30)

        # Approximate depth per particle (assuming spherical impact area)
        particle_volume = M / float(particle_density)
        particle_radius = (3.0 * particle_volume / (4.0 * np.pi)) ** (1.0 / 3.0)
        impact_area = np.pi * particle_radius**2
        depth_per_particle = volume / max(impact_area, 1e-30)

        return {
            "volume_removed": float(volume),
            "mass_loss": float(mass_loss),
            "erosion_rate": float(erosion_rate),
            "depth_per_particle": float(depth_per_particle),
            "angle_function": float(angle_fn),
        }

    def erosion_vs_angle(
        self,
        velocity: float = 50.0,
        mass: float = 1e-6,
        angles: NDArray[np.float64] | None = None,
    ) -> dict[str, Any]:
        """Compute erosion rate as a function of impact angle.

        Parameters
        ----------
        velocity : float
            Particle impact velocity (m/s).
        mass : float
            Particle mass (kg).
        angles : NDArray or None
            Array of impact angles (degrees). Defaults to 0-90 deg.

        Returns
        -------
        dict
            Keys: 'angles' (NDArray), 'erosion_rates' (NDArray),
            'peak_angle' (float), 'peak_rate' (float).
        """
        if angles is None:
            angles = np.linspace(1.0, 90.0, 90, dtype=np.float64)

        rates = np.array(
            [self.finnie_erosion(mass=mass, velocity=velocity, angle=a)["erosion_rate"] for a in angles],
            dtype=np.float64,
        )

        peak_idx = int(np.argmax(rates))
        return {
            "angles": angles,
            "erosion_rates": rates,
            "peak_angle": float(angles[peak_idx]),
            "peak_rate": float(rates[peak_idx]),
        }

    # ------------------------------------------------------------------
    # Leading edge blade erosion
    # ------------------------------------------------------------------

    def blade_erosion(
        self,
        tip_speed: float = 80.0,
        chord: float = 0.3,
        particle_mass: float = 1e-6,
        particle_flux: float = 1e-3,
        exposure_time: float = 3600.0,
        rain_density: float = 1000.0,
        droplet_radius: float = 1e-3,
    ) -> dict[str, Any]:
        """Simulate leading edge erosion of a wind turbine blade.

        Models erosion from rain droplet impact at the blade leading
        edge. Uses a simplified velocity-weigthed Finnie model with
        droplet breakup considerations.

        Parameters
        ----------
        tip_speed : float
            Blade tip speed (m/s).
        chord : float
            Blade chord at the leading edge section (m).
        particle_mass : float
            Effective mass of impacting particle/droplet (kg).
        particle_flux : float
            Particle flux (kg/m^2/s).
        exposure_time : float
            Exposure time (seconds).
        rain_density : float
            Density of rain droplets (kg/m^3).
        droplet_radius : float
            Mean droplet radius (m).

        Returns
        -------
        dict
            Keys: 'total_erosion_depth' (m), 'max_erosion_depth' (m),
            'depth_distribution' (NDArray), 'position' (NDArray),
            'rain_erosion_rate' (m/s).
        """
        if tip_speed <= 0.0:
            raise ValueError("Tip speed must be positive.")
        if exposure_time <= 0.0:
            raise ValueError("Exposure time must be positive.")
        if chord <= 0.0:
            raise ValueError("Chord must be positive.")

        # Velocity relative to blade leading edge
        v_rel = tip_speed * 1.0

        # Impact angle varies along leading edge (clamp > 0 to avoid Finnie singularity)
        n_pos = 50
        s = np.linspace(0.0, chord, n_pos, dtype=np.float64)
        impact_angle = np.clip(90.0 * (1.0 - s / chord), 1.0, 90.0)

        # For each position, compute Finnie erosion
        erosion_depth = np.zeros(n_pos, dtype=np.float64)
        for i in range(n_pos):
            # Droplet mass based on radius
            droplet_mass = (4.0 / 3.0) * np.pi * droplet_radius**3 * float(rain_density)
            mass = max(droplet_mass, particle_mass)

            result = self.finnie_erosion(
                mass=mass,
                velocity=v_rel,
                angle=float(impact_angle[i]),
            )
            depth_per_hit = result["depth_per_particle"]

            # Number of impacts during exposure
            n_impacts = particle_flux * exposure_time / max(mass, 1e-30)
            erosion_depth[i] = depth_per_hit * n_impacts

        rain_rate = float(erosion_depth.max() / max(exposure_time, 1e-12))

        return {
            "total_erosion_depth": float(erosion_depth.sum()),
            "max_erosion_depth": float(erosion_depth.max()),
            "depth_distribution": erosion_depth,
            "position": s,
            "rain_erosion_rate": rain_rate,
        }

    # ------------------------------------------------------------------
    # Cumulative erosion and time to failure
    # ------------------------------------------------------------------

    def cumulative_erosion(
        self,
        mass: float,
        velocity: float,
        angle: float,
        n_particles: int,
    ) -> dict[str, float]:
        """Compute total erosion after N particle impacts.

        Parameters
        ----------
        mass : float
            Mass of a single particle (kg).
        velocity : float
            Impact velocity (m/s).
        angle : float
            Impact angle (degrees).
        n_particles : int
            Number of particle impacts.

        Returns
        -------
        dict
            Keys: 'total_volume' (m^3), 'total_mass_loss' (kg),
            'total_depth' (m), 'n_particles' (int).
        """
        if n_particles < 0:
            raise ValueError("Number of particles must be non-negative.")

        single = self.finnie_erosion(mass=mass, velocity=velocity, angle=angle)
        total_vol = single["volume_removed"] * n_particles
        total_mass = single["mass_loss"] * n_particles

        # Depth estimate (accumulated over impact area)
        particle_volume = mass / self.hardness * self.k  # rough approx area factor
        area_factor = max(abs(self.d31) if hasattr(self, 'd31') else 1e-6, 1e-12)

        return {
            "total_volume": float(total_vol),
            "total_mass_loss": float(total_mass),
            "total_depth": single["depth_per_particle"] * n_particles,
            "n_particles": n_particles,
        }

    def erosion_over_time(
        self,
        velocity: float,
        angle: float,
        mass_flux: float,
        total_time: float,
        n_steps: int = 100,
    ) -> dict[str, Any]:
        """Compute erosion depth as a function of exposure time.

        Parameters
        ----------
        velocity : float
            Particle velocity (m/s).
        angle : float
            Impact angle (degrees).
        mass_flux : float
            Particle mass flux (kg/m^2/s).
        total_time : float
            Total exposure time (s).
        n_steps : int
            Number of time steps.

        Returns
        -------
        dict
            Keys: 'time' (NDArray), 'depth' (NDArray),
            'instantaneous_rate' (NDArray).
        """
        if total_time <= 0.0:
            raise ValueError("Total time must be positive.")
        if n_steps < 2:
            raise ValueError("At least 2 time steps required.")

        t_eval = np.linspace(0.0, float(total_time), n_steps, dtype=np.float64)
        dt = t_eval[1] - t_eval[0]

        M, V = float(mass_flux) * dt, float(velocity)
        alpha = float(angle)

        single = self.finnie_erosion(mass=1e-6, velocity=V, angle=alpha)
        rate_per_kg = single["erosion_rate"] / 1e-6  # rate per kg of erodent

        # Depth rate = erosion_rate (kg/kg) * mass_flux (kg/m^2/s) / density (kg/m^3)
        depth_rate = rate_per_kg * float(mass_flux) / self.material_density
        depth = depth_rate * t_eval
        instantaneous_rate = np.full_like(t_eval, depth_rate)

        return {
            "time": t_eval,
            "depth": depth,
            "instantaneous_rate": instantaneous_rate,
        }

    def time_to_failure(
        self,
        current_depth: float = 0.0,
        critical_depth: float = 2e-3,
        erosion_rate: float = 1e-9,
    ) -> dict[str, float]:
        """Estimate time to reach critical erosion depth.

        Parameters
        ----------
        current_depth : float
            Current erosion depth (m).
        critical_depth : float
            Critical/maximum allowable erosion depth (m).
        erosion_rate : float
            Erosion rate (m/s).

        Returns
        -------
        dict
            Keys: 'remaining_depth' (m), 'time_to_failure' (s),
            'time_to_failure_hours' (hours), 'critical_depth' (m).
        """
        if current_depth < 0.0:
            raise ValueError("Current depth must be non-negative.")
        if critical_depth <= current_depth:
            return {
                "remaining_depth": 0.0,
                "time_to_failure": 0.0,
                "time_to_failure_hours": 0.0,
                "critical_depth": critical_depth,
            }
        if erosion_rate <= 0.0:
            raise ValueError("Erosion rate must be positive.")

        remaining = float(critical_depth) - float(current_depth)
        ttf = remaining / float(erosion_rate)

        return {
            "remaining_depth": remaining,
            "time_to_failure": ttf,
            "time_to_failure_hours": ttf / 3600.0,
            "critical_depth": critical_depth,
        }


# ------------------------------------------------------------------
# Usage example
# ------------------------------------------------------------------
if __name__ == "__main__":
    import doctest

    doctest.testmod()

    em = ErosionModel(material_density=2700.0, hardness=3e9, k=2.0)

    print("Finnie erosion (1 mg particle, 50 m/s, 30 deg)...")
    result = em.finnie_erosion(mass=1e-6, velocity=50.0, angle=30.0)
    print(f"  Erosion rate: {result['erosion_rate']:.3e} kg/kg")
    print(f"  Volume removed: {result['volume_removed']:.3e} m^3")

    print("Erosion vs impact angle (50 m/s)...")
    eva = em.erosion_vs_angle(velocity=50.0)
    print(f"  Peak angle: {eva['peak_angle']:.1f} deg")
    print(f"  Peak rate: {eva['peak_rate']:.3e} kg/kg")

    print("Wind turbine blade leading edge erosion...")
    blade = em.blade_erosion(tip_speed=80.0, chord=0.3, exposure_time=3600.0)
    print(f"  Max erosion depth: {blade['max_erosion_depth']:.3e} m")
    print(f"  Rain erosion rate: {blade['rain_erosion_rate']:.3e} m/s")

    print("Time to failure (current=0.5mm, critical=2mm)...")
    ttf = em.time_to_failure(
        current_depth=0.5e-3, critical_depth=2e-3, erosion_rate=1e-9
    )
    print(f"  Time to failure: {ttf['time_to_failure_hours']:.1f} hours")

    print("ErosionModel module OK.")
