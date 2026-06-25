"""
piezoelectric.py — Piezoelectric Material Modeling Module
==========================================================

Constitutive equations (e-form and d-form), d31, d33, d15 coupling
modes, actuator force/displacement vs voltage, sensor voltage output
from strain, and energy harvesting power vs load resistance.

Classes
-------
PiezoMaterial : Piezoelectric material property and device modeling.

Dependencies
------------
numpy, scipy (optimize, integrate)

Usage Example
-------------
>>> import numpy as np
>>> from modules.piezoelectric import PiezoMaterial
>>> mat = PiezoMaterial(d31=-190e-12, d33=390e-12, eps33=1500*8.854e-12)
>>> F = mat.actuator_force(voltage=100.0, width=0.01, length=0.05)
>>> V = mat.sensor_voltage(strain_x=1e-4, thickness=0.5e-3)
>>> P = mat.harvested_power(voltage=10.0, frequency=100.0, load=1e3)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import integrate, optimize


class PiezoMaterial:
    """Piezoelectric material with constitutive equations and device models.

    Supports both the e-form (stress-charge) and d-form (strain-charge)
    constitutive relations. Provides methods for actuator, sensor, and
    energy harvesting calculations.

    Parameters
    ----------
    d31 : float
        Transverse piezoelectric charge coefficient (C/N or m/V).
    d33 : float
        Longitudinal piezoelectric coefficient (C/N or m/V).
    d15 : float
        Shear piezoelectric coefficient (C/N or m/V).
    eps33 : float
        Permittivity in the poling direction (F/m).
    eps11 : float
        Permittivity perpendicular to poling (F/m); defaults to eps33.
    sE11 : float
        Elastic compliance at constant E (Pa^-1); default 1.5e-11.
    sE33 : float
        Elastic compliance at constant E, longitudinal; default 1.8e-11.
    sE55 : float
        Shear elastic compliance; default 4.5e-11.
    density : float
        Material density (kg/m^3); default 7700 (PZT-5A).
    mechanical_q : float
        Mechanical quality factor; default 75.
    """

    def __init__(
        self,
        d31: float = -190e-12,
        d33: float = 390e-12,
        d15: float = 590e-12,
        eps33: float = 1500.0 * 8.854e-12,
        eps11: float | None = None,
        sE11: float = 1.5e-11,
        sE33: float = 1.8e-11,
        sE55: float = 4.5e-11,
        density: float = 7700.0,
        mechanical_q: float = 75.0,
    ) -> None:
        self.d31 = float(d31)
        self.d33 = float(d33)
        self.d15 = float(d15)
        self.eps33 = float(eps33)
        self.eps11 = float(eps11) if eps11 is not None else float(eps33)
        self.sE11 = float(sE11)
        self.sE33 = float(sE33)
        self.sE55 = float(sE55)
        self.density = float(density)
        self.mechanical_q = float(mechanical_q)

        # Derived: elastic moduli (C = S^-1)
        self.cE11 = 1.0 / sE11
        self.cE33 = 1.0 / sE33
        self.cE55 = 1.0 / sE55

    # ------------------------------------------------------------------
    # Constitutive equations
    # ------------------------------------------------------------------

    def eform_stress(
        self,
        strain: NDArray[np.float64],
        electric_field: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Stress from e-form: sigma = C^E * strain - e^T * E.

        Parameters
        ----------
        strain : NDArray (3,)
            Mechanical strain components [e11, e33, e13].
        electric_field : NDArray (3,)
            Electric field components [E1, E3, E2].

        Returns
        -------
        NDArray (3,)
            Stress components [sigma11, sigma33, sigma13].
        """
        # e = d * C (piezoelectric stress coefficients)
        e31 = self.d31 * self.cE11 + self.d31 * self.cE11 * 0.3  # approx
        e33 = self.d33 * self.cE33
        e15 = self.d15 * self.cE55

        e11, e33_s, e13 = strain
        E1, E3, _ = electric_field

        sig11 = self.cE11 * e11 - e31 * E3
        sig33 = self.cE33 * e33_s - e33 * E3
        sig13 = self.cE55 * 2.0 * e13 - e15 * E1

        return np.array([sig11, sig33, sig13], dtype=np.float64)

    def dform_strain(
        self,
        stress: NDArray[np.float64],
        electric_field: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Strain from d-form: strain = S^E * sigma + d^T * E.

        Parameters
        ----------
        stress : NDArray (3,)
            Stress components [sigma11, sigma33, sigma13].
        electric_field : NDArray (3,)
            Electric field components [E1, E3, E2].

        Returns
        -------
        NDArray (3,)
            Strain components [e11, e33, e13].
        """
        sig11, sig33, sig13 = stress
        E1, E3, _ = electric_field

        e11 = self.sE11 * sig11 + self.d31 * E3
        e33_s = self.sE33 * sig33 + self.d33 * E3
        e13 = self.sE55 * sig13 + self.d15 * E1

        return np.array([e11, e33_s, e13], dtype=np.float64)

    # ------------------------------------------------------------------
    # Actuator
    # ------------------------------------------------------------------

    def actuator_strain(self, voltage: float, thickness: float) -> dict[str, float]:
        """Free strain of a piezoelectric actuator.

        For a thin plate with poling in the 3-direction and electric
        field applied across thickness, the in-plane strain is:
            e11 = d31 * V / t

        Parameters
        ----------
        voltage : float
            Applied voltage (V).
        thickness : float
            Layer thickness (m).

        Returns
        -------
        dict
            Keys: 'strain_11', 'strain_33', 'strain_13'.
        """
        if thickness <= 0.0:
            raise ValueError("Thickness must be positive.")
        E3 = float(voltage) / float(thickness)
        stress = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        e_field = np.array([0.0, E3, 0.0], dtype=np.float64)
        strain = self.dform_strain(stress, e_field)
        return {
            "strain_11": float(strain[0]),
            "strain_33": float(strain[1]),
            "strain_13": float(strain[2]),
        }

    def actuator_force(
        self,
        voltage: float,
        width: float,
        length: float,
        thickness: float = 0.5e-3,
        blocked: bool = True,
    ) -> dict[str, float]:
        """Actuator force and displacement vs applied voltage.

        For a piezoelectric stack or bimorph actuator.

        Parameters
        ----------
        voltage : float
            Applied voltage (V).
        width : float
            Actuator width (m).
        length : float
            Actuator length (m).
        thickness : float
            Layer thickness (m).
        blocked : bool
            If True, return blocked force (zero displacement).
            If False, return free displacement (zero load).

        Returns
        -------
        dict
            Keys: 'force', 'displacement', 'strain', 'blocked_force',
            'free_displacement'.
        """
        if thickness <= 0.0 or width <= 0.0 or length <= 0.0:
            raise ValueError("Dimensions must be positive.")

        E3 = float(voltage) / float(thickness)
        free_strain = self.d31 * E3
        cross_area = width * thickness

        # Blocked force (full constraint)
        blocked_force_val = -self.cE11 * free_strain * cross_area  # N
        # Free displacement (no load)
        free_disp = free_strain * length  # m

        result = {
            "strain": float(free_strain),
            "blocked_force": float(blocked_force_val),
            "free_displacement": float(free_disp),
        }

        if blocked:
            result["force"] = float(blocked_force_val)
            result["displacement"] = 0.0
        else:
            result["force"] = 0.0
            result["displacement"] = float(free_disp)

        return result

    # ------------------------------------------------------------------
    # Sensor
    # ------------------------------------------------------------------

    def sensor_voltage(
        self,
        strain_x: float = 0.0,
        strain_z: float = 0.0,
        stress_x: float | None = None,
        thickness: float = 0.5e-3,
    ) -> float:
        """Sensor voltage output under mechanical strain.

        Calculates the open-circuit voltage from the direct piezoelectric
        effect using the d31 (transverse) or d33 (longitudinal) mode.

        Parameters
        ----------
        strain_x : float
            In-plane strain (d31 mode).
        strain_z : float
            Out-of-plane strain (d33 mode).
        stress_x : float or None
            If provided, computes strain = stress_x / cE11 instead.
        thickness : float
            Layer thickness (m).

        Returns
        -------
        float
            Open-circuit sensor voltage (V).
        """
        if thickness <= 0.0:
            raise ValueError("Thickness must be positive.")

        if stress_x is not None:
            strain_effective = float(stress_x) / self.cE11
        else:
            # Combine d31 and d33 contributions
            strain_effective = abs(float(strain_x)) + abs(float(strain_z)) * (self.d33 / max(abs(self.d31), 1e-30))

        # Open-circuit voltage: V = (d31 / eps33) * strain * thickness
        V = (abs(self.d31) / self.eps33) * strain_effective * thickness
        return float(V)

    # ------------------------------------------------------------------
    # Energy harvesting
    # ------------------------------------------------------------------

    def harvested_power(
        self,
        voltage: float,
        frequency: float,
        load_resistance: float,
        capacitance: float | None = None,
    ) -> dict[str, float]:
        """Energy harvesting power vs load resistance.

        Models a resistive load connected to a piezoelectric element
        driven at a given frequency. Uses the standard AC power model:
            P = V^2 * R_load / (R_load^2 + (1/(2*pi*f*C))^2)

        Parameters
        ----------
        voltage : float
            Open-circuit voltage amplitude (V).
        frequency : float
            Excitation frequency (Hz).
        load_resistance : float
            Load resistance (ohms).
        capacitance : float or None
            Electrical capacitance of the piezo element (F).
            If None, calculated from eps33 and geometry.

        Returns
        -------
        dict
            Keys: 'power' (W), 'voltage_across_load' (V),
            'current' (A), 'efficiency' (fraction).
        """
        if frequency <= 0.0:
            raise ValueError("Frequency must be positive.")
        if load_resistance <= 0.0:
            raise ValueError("Load resistance must be positive.")

        omega = 2.0 * np.pi * float(frequency)

        if capacitance is None or capacitance <= 0.0:
            # Typical capacitance for a small piezo patch
            capacitance = self.eps33 * 1e-4 / 0.5e-3  # A=1cm^2, t=0.5mm

        C = float(capacitance)
        R = float(load_resistance)

        # Impedance of capacitor
        Zc = 1.0 / (1j * omega * C)

        # Voltage across load (voltage divider)
        V_load = float(voltage) * R / abs(R + Zc)

        # Power
        power = V_load**2 / R

        # Current
        current = V_load / R

        # Efficiency (simplified: fraction of max available power)
        # Max power when R_load = |Z_c| = 1/(omega*C)
        R_opt = 1.0 / (omega * C)
        efficiency = (2.0 * R / R_opt) / (1.0 + (R / R_opt) ** 2)

        return {
            "power": power,
            "voltage_across_load": V_load,
            "current": current,
            "efficiency": efficiency,
            "optimal_load": R_opt,
        }

    def optimal_load_resistance(
        self, frequency: float, capacitance: float | None = None
    ) -> float:
        """Calculate optimal load resistance for maximum power transfer.

        Parameters
        ----------
        frequency : float
            Excitation frequency (Hz).
        capacitance : float or None
            Piezo capacitance (F). Estimated from eps33 if None.

        Returns
        -------
        float
            Optimal load resistance (ohms).
        """
        if frequency <= 0.0:
            raise ValueError("Frequency must be positive.")
        omega = 2.0 * np.pi * float(frequency)
        if capacitance is None or capacitance <= 0.0:
            capacitance = self.eps33 * 1e-4 / 0.5e-3
        return 1.0 / (omega * float(capacitance))


# ------------------------------------------------------------------
# Usage example
# ------------------------------------------------------------------
if __name__ == "__main__":
    import doctest

    doctest.testmod()

    mat = PiezoMaterial()

    print("Constitutive equations (d-form with zero stress)...")
    strain = mat.dform_strain(np.zeros(3), np.array([0.0, 1e5, 0.0]))
    print(f"  Strain from E3=1e5 V/m: e11={strain[0]:.3e}, e33={strain[1]:.3e}")

    print("Actuator analysis (100 V, blocked)...")
    act = mat.actuator_force(voltage=100.0, width=0.01, length=0.05, thickness=0.5e-3)
    print(f"  Blocked force: {act['blocked_force']:.4f} N")
    print(f"  Free displacement: {act['free_displacement']:.3e} m")

    print("Sensor analysis (strain_x = 100 microstrain)...")
    V = mat.sensor_voltage(strain_x=1e-4, thickness=0.5e-3)
    print(f"  Sensor voltage: {V:.6f} V")

    print("Energy harvesting (50 V, 100 Hz, 10 kOhm)...")
    hp = mat.harvested_power(voltage=10.0, frequency=100.0, load_resistance=1e3)
    print(f"  Power: {hp['power']:.6f} W")
    print(f"  Optimal load: {hp['optimal_load']:.0f} Ohm")

    print("PiezoMaterial module OK.")
