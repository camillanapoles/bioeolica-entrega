"""
Creep Analysis Module — Power Law, Arrhenius Temperature, LMP, Stress Relaxation
=================================================================================

Implements classical creep analysis methods for high-temperature materials:

  - Norton-Bailey power law creep (steady-state and primary)
  - Arrhenius temperature dependence (thermal activation)
  - Larson-Miller parameter (LMP) for life prediction
  - Creep strain vs time integration (Runge-Kutta)
  - Stress relaxation (constant strain)
  - Composite creep (rule of mixtures, Reuss, Voigt)

References
----------
- Norton, F. H. (1929). The creep of steel at high temperatures.
- Bailey, R. W. (1935). The utilisation of creep test data in engineering design.
- Arrhenius, S. (1889). Uber die Reaktionsgeschwindigkeit bei der Inversion
  von Rohrzucker durch Sauren.
- Larson, F. R., & Miller, J. (1952). A time-temperature relationship for
  rupture and creep stresses.
- ASTM E139-11 (2018). Standard test methods for conducting creep,
  creep-rupture, and stress-rupture tests of metallic materials.

Classes
-------
CreepModel
    Main class for creep strain, relaxation, and life prediction.
"""

from __future__ import annotations

from typing import Callable, Literal, Optional

import numpy as np
from scipy.integrate import solve_ivp

# P$1: rotear constantes pelo schema unificado
import sys
from pathlib import Path
_CORE = Path(__file__).resolve()
while not (_CORE / "workspace").exists() and _CORE.parent != _CORE:
    _CORE = _CORE.parent
_CORE = _CORE / "workspace" / "lab1-material-papel-mache-grafite"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from core.constants import get

# ---------------------------------------------------------------------------
#  Norton-Bailey creep strain rate
# ---------------------------------------------------------------------------

def _norton_bailey_strain_rate(
    sigma: float,
    A: float,
    n: float,
    m: float,
    t: float,
    Q: float,
    R: float,
    T: float,
) -> float:
    """Norton-Bailey creep strain rate with Arrhenius temperature dependence.

    eps_dot = A * sigma^n * t^m * exp(-Q / (R * T))

    Parameters
    ----------
    sigma : float
        Applied stress (MPa).
    A : float
        Norton coefficient (MPa^{-n} s^{-(m+1)}).
    n : float
        Stress exponent.
    m : float
        Time exponent (m < 0 for primary creep, m = 0 for steady-state).
    t : float
        Current time (s).
    Q : float
        Activation energy (J/mol).
    R : float
        Universal gas constant (J/(mol K)).
    T : float
        Absolute temperature (K).

    Returns
    -------
    eps_dot : float
        Creep strain rate (1/s).
    """
    if t <= 0:
        t = 1e-12
    arrhenius = np.exp(-Q / (R * T))
    return A * (sigma ** n) * (t ** m) * arrhenius


# ---------------------------------------------------------------------------
#  Larson-Miller parameter
# ---------------------------------------------------------------------------

def _larson_miller(
    sigma: float,
    C_lmp: float,
    A_lmp: float,
    B_lmp: float,
) -> float:
    """Larson-Miller parameter: P = T * (log10(t_r) + C).

    Uses a linear fit: P(sigma) = A_lmp + B_lmp * log10(sigma).

    Parameters
    ----------
    sigma : float
        Applied stress (MPa).
    C_lmp : float
        Larson-Miller constant (typical ~20 for steels).
    A_lmp : float
        Intercept of LMP vs log(sigma) fit.
    B_lmp : float
        Slope of LMP vs log(sigma) fit.

    Returns
    -------
    P : float
        Larson-Miller parameter.
    """
    return A_lmp + B_lmp * np.log10(sigma)


# ---------------------------------------------------------------------------
#  Composite creep models
# ---------------------------------------------------------------------------

def _voigt_strain(
    sigma: float,
    t: float,
    E_f: float,
    E_m: float,
    V_f: float,
    creep_func_f: Callable,
    creep_func_m: Callable,
) -> float:
    """Voigt (isostrain) composite creep: equal strain in both phases.

    Parameters
    ----------
    sigma : float
        Applied stress (MPa).
    t : float
        Time (s).
    E_f : float
        Fibre Young's modulus (MPa).
    E_m : float
        Matrix Young's modulus (MPa).
    V_f : float
        Fibre volume fraction.
    creep_func_f : Callable
        Fibre creep function (sigma, t) -> strain.
    creep_func_m : Callable
        Matrix creep function (sigma, t) -> strain.

    Returns
    -------
    eps_total : float
        Total creep strain.
    """
    V_m = 1.0 - V_f
    # Equal strain assumption: eps_f = eps_m = eps_total
    # Stress partition: sigma = V_f * sigma_f + V_m * sigma_m
    # Iterative solution is required; simplified:
    # Approximate: fibre carries more stress
    E_eff = V_f * E_f + V_m * E_m
    sigma_f = sigma * E_f / E_eff
    sigma_m = sigma * E_m / E_eff
    eps_f = creep_func_f(sigma_f, t)
    eps_m = creep_func_m(sigma_m, t)
    return V_f * eps_f + V_m * eps_m


def _reuss_strain(
    sigma: float,
    t: float,
    E_f: float,
    E_m: float,
    V_f: float,
    creep_func_f: Callable,
    creep_func_m: Callable,
) -> float:
    """Reuss (isostress) composite creep: equal stress in both phases.

    Parameters
    ----------
    sigma : float
        Applied stress (MPa).
    t : float
        Time (s).
    E_f : float
        Fibre Young's modulus (MPa).
    E_m : float
        Matrix Young's modulus (MPa).
    V_f : float
        Fibre volume fraction.
    creep_func_f : Callable
        Fibre creep function (sigma, t) -> strain.
    creep_func_m : Callable
        Matrix creep function (sigma, t) -> strain.

    Returns
    -------
    eps_total : float
        Total creep strain.
    """
    V_m = 1.0 - V_f
    eps_f = creep_func_f(sigma, t)
    eps_m = creep_func_m(sigma, t)
    return V_f * eps_f + V_m * eps_m


# ---------------------------------------------------------------------------
#  Main class
# ---------------------------------------------------------------------------

class CreepModel:
    """Creep material model with Norton-Bailey, Arrhenius, and LMP.

    Parameters
    ----------
    A : float
        Norton coefficient (MPa^{-n} s^{-(m+1)}).
    n : float
        Stress exponent.
    m : float, optional
        Time exponent (default 0.0 — steady-state creep).
    Q : float, optional
        Activation energy in J/mol (default 300e3).
    R : float, optional
        Gas constant in J/(mol K) (default 8.314).
    C_lmp : float, optional
        Larson-Miller constant (default 20).
    A_lmp : float, optional
        LMP intercept (default 25.0).
    B_lmp : float, optional
        LMP slope (default -5.0).
    E : float, optional
        Young's modulus for relaxation (MPa, default 200e3).

    Attributes
    ----------
    A, n, m, Q, R : float
        Constitutive parameters.
    C_lmp, A_lmp, B_lmp : float
        Larson-Miller parameters.
    E : float
        Young's modulus.
    """

    def __init__(
        self,
        A: float = 1e-12,
        n: float = 5.0,
        m: float = 0.0,
        Q: float = 300e3,
        R: float = 8.314,
        C_lmp: float = 20.0,
        A_lmp: float = 25.0,
        B_lmp: float = -5.0,
        E: float = 200e3,
    ) -> None:
        self.A = A
        self.n = n
        self.m = m
        self.Q = Q
        self.R = R
        self.C_lmp = C_lmp
        self.A_lmp = A_lmp
        self.B_lmp = B_lmp
        self.E = E

    # -- Creep strain --------------------------------------------------------

    def creep_strain(
        self,
        sigma: float,
        t_total: float,
        n_steps: int = 1000,
        T: float = 800.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute creep strain vs time by integrating Norton-Bailey.

        The ODE solved is:

            deps/dt = A * sigma^n * t^m * exp(-Q/(R*T))

        Parameters
        ----------
        sigma : float
            Applied stress (MPa).
        t_total : float
            Total time (s).
        n_steps : int, optional
            Number of time steps (default 1000).
        T : float, optional
            Temperature in K (default 800).

        Returns
        -------
        t : np.ndarray, shape (n_steps + 1,)
            Time points (s).
        eps : np.ndarray, shape (n_steps + 1,)
            Creep strain at each time point.
        """
        t_span = (0.0, t_total)
        t_eval = np.linspace(0.0, t_total, n_steps + 1)

        def ode(t: float, y: np.ndarray) -> np.ndarray:
            eps = y[0]
            rate = _norton_bailey_strain_rate(sigma, self.A, self.n, self.m, t, self.Q, self.R, T)
            return np.array([rate])

        sol = solve_ivp(ode, t_span, np.array([0.0]), t_eval=t_eval, method="RK45")
        return sol.t, sol.y[0]

    # -- Stress relaxation ---------------------------------------------------

    def relaxation(
        self,
        eps0: float,
        t_total: float,
        n_steps: int = 1000,
        T: float = 800.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute stress relaxation under constant strain.

        The ODE solved for stress sigma(t):

            d(sigma)/dt = -E * A * sigma^n * t^m * exp(-Q/(R*T))

        assuming elastic-creep decomposition: sigma = E * (eps0 - eps_c).

        Parameters
        ----------
        eps0 : float
            Constant total strain.
        t_total : float
            Total time (s).
        n_steps : int, optional
            Number of time steps (default 1000).
        T : float, optional
            Temperature in K (default 800).

        Returns
        -------
        t : np.ndarray, shape (n_steps + 1,)
            Time points (s).
        sigma : np.ndarray, shape (n_steps + 1,)
            Relaxed stress (MPa).
        """
        t_span = (0.0, t_total)
        t_eval = np.linspace(0.0, t_total, n_steps + 1)
        sigma0 = self.E * eps0

        def ode(t: float, y: np.ndarray) -> np.ndarray:
            sig = y[0]
            if sig <= 0:
                return np.array([0.0])
            rate_creep = _norton_bailey_strain_rate(sig, self.A, self.n, self.m, t, self.Q, self.R, T)
            d_sig = -self.E * rate_creep
            return np.array([d_sig])

        sol = solve_ivp(ode, t_span, np.array([sigma0]), t_eval=t_eval, method="RK45")
        return sol.t, sol.y[0]

    # -- Larson-Miller -------------------------------------------------------

    def larson_miller(
        self,
        sigma: float,
    ) -> float:
        """Compute the Larson-Miller parameter for a given stress.

        Uses the linear fit: P = A_lmp + B_lmp * log10(sigma).

        Parameters
        ----------
        sigma : float
            Applied stress (MPa).

        Returns
        -------
        P : float
            Larson-Miller parameter.
        """
        return _larson_miller(sigma, self.C_lmp, self.A_lmp, self.B_lmp)

    def rupture_time(
        self,
        sigma: float,
        T: float,
    ) -> float:
        """Compute creep rupture time from the Larson-Miller parameter.

        t_r = 10^(P/T - C_lmp)

        Parameters
        ----------
        sigma : float
            Applied stress (MPa).
        T : float
            Temperature (K).

        Returns
        -------
        t_r : float
            Rupture time (hours).
        """
        P = self.larson_miller(sigma)
        log_tr = P / T - self.C_lmp
        return 10.0 ** log_tr

    def rupture_stress(
        self,
        t_r: float,
        T: float,
    ) -> float:
        """Compute stress that causes rupture at given time and temperature.

        Inverts the LMP relation: given t_r and T, find sigma.

        Parameters
        ----------
        t_r : float
            Rupture time (hours).
        T : float
            Temperature (K).

        Returns
        -------
        sigma : float
            Rupture stress (MPa).
        """
        P = T * (np.log10(t_r) + self.C_lmp)
        log10_sigma = (P - self.A_lmp) / self.B_lmp
        return 10.0 ** log10_sigma

    # -- Composite creep -----------------------------------------------------

    def composite_creep(
        self,
        sigma: float,
        t: float,
        E_f: float = 400e3,
        E_m: float = 70e3,
        V_f: float = 0.5,
        rule: Literal["voigt", "reuss"] = "voigt",
        creep_func_f: Optional[Callable] = None,
        creep_func_m: Optional[Callable] = None,
    ) -> float:
        """Compute composite creep strain using Voigt or Reuss rule of mixtures.

        Parameters
        ----------
        sigma : float
            Applied stress (MPa).
        t : float
            Time (s).
        E_f : float, optional
            Fibre modulus (MPa, default 400e3).
        E_m : float, optional
            Matrix modulus (MPa, default 70e3).
        V_f : float, optional
            Fibre volume fraction (default 0.5).
        rule : str, optional
            'voigt' (isostrain) or 'reuss' (isostress).
        creep_func_f : Callable, optional
            Fibre creep function (sigma, t) -> strain. Default is
            elastic only (no creep).
        creep_func_m : Callable, optional
            Matrix creep function. Default uses Norton-Bailey of this model.

        Returns
        -------
        eps_total : float
            Total creep strain.
        """
        if creep_func_f is None:
            def elastic_f(s: float, _: float) -> float:
                return s / E_f
            creep_func_f = elastic_f

        if creep_func_m is None:
            def matrix_creep(s: float, tt: float) -> float:
                # Integrate creep rate for a single time point
                _, eps_hist = self.creep_strain(s, tt, n_steps=100, T=800.0)
                return s / E_m + eps_hist[-1]
            creep_func_m = matrix_creep

        if rule == "voigt":
            return _voigt_strain(sigma, t, E_f, E_m, V_f, creep_func_f, creep_func_m)
        else:
            return _reuss_strain(sigma, t, E_f, E_m, V_f, creep_func_f, creep_func_m)

    # -- Analytical approximations -------------------------------------------

    def steady_state_rate(self, sigma: float, T: float = 800.0) -> float:
        """Steady-state creep rate (Norton law, m=0).

        Parameters
        ----------
        sigma : float
            Stress (MPa).
        T : float, optional
            Temperature in K (default 800).

        Returns
        -------
        eps_dot : float
            Steady-state strain rate (1/s).
        """
        return _norton_bailey_strain_rate(sigma, self.A, self.n, 0.0, 1.0, self.Q, self.R, T)

    def strain_at_time(self, sigma: float, t: float, T: float = 800.0) -> float:
        """Analytical creep strain for m != -1.

        For m != -1, integrating Norton-Bailey analytically:

            eps = A * sigma^n * t^(m+1) / (m+1) * exp(-Q/(R*T))

        Parameters
        ----------
        sigma : float
            Stress (MPa).
        t : float
            Time (s).
        T : float, optional
            Temperature in K (default 800).

        Returns
        -------
        eps : float
            Creep strain.
        """
        if abs(self.m + 1.0) < 1e-12:
            return self.steady_state_rate(sigma, T) * t * np.log(t + 1e-12)
        arrhenius_factor = np.exp(-self.Q / (self.R * T))
        return (
            self.A * (sigma ** self.n) * (t ** (self.m + 1.0)) / (self.m + 1.0) * arrhenius_factor
        )

    # -- Material factory ----------------------------------------------------

    @classmethod
    def from_material(cls, material: str) -> "CreepModel":
        """Create a CreepModel from predefined material parameters.

        Parameters
        ----------
        material : str
            One of 'steel_cr1mo', 'aluminium_2024', 'inconel_718'.

        Returns
        -------
        cm : CreepModel
        """
        materials = {
            "steel_cr1mo": {
                "A": 5.7e-18, "n": 5.5, "m": 0.0, "Q": 380e3,
                "C_lmp": 20.0, "A_lmp": 28.0, "B_lmp": -6.0, "E": 210e3,
            },
            "aluminium_2024": {
                "A": 1.2e-10, "n": 3.5, "m": -0.3, "Q": 150e3,
                "C_lmp": 18.0, "A_lmp": 22.0, "B_lmp": -4.5, "E": 73e3,
            },
            "inconel_718": {
                "A": 2.1e-20, "n": 7.0, "m": 0.0, "Q": 420e3,
                "C_lmp": 22.0, "A_lmp": 30.0, "B_lmp": -5.5, "E": 200e3,
            },
        }
        if material not in materials:
            raise ValueError(
                f"Unknown material '{material}'. "
                f"Available: {list(materials.keys())}"
            )
        return cls(**materials[material])


# ---------------------------------------------------------------------------
#  Usage example (run as script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Creep model for Cr1Mo steel at 550 C
    cm = CreepModel(A=5.7e-18, n=5.5, m=0.0, Q=380e3, E=210e3)
    T = get("modules.physics_m3.creep.temp_ref_K")  # 550 C

    # Creep strain
    t, eps = cm.creep_strain(sigma=100.0, t_total=10000.0, T=T)
    print(f"Creep strain at 10,000 s: {eps[-1]:.6f}")
    print(f"Steady-state rate:        {cm.steady_state_rate(100.0, T):.3e} 1/s")

    # Stress relaxation
    t_rel, sig_rel = cm.relaxation(eps0=5e-4, t_total=5000.0, T=T)
    print(f"Stress after 5000 s:      {sig_rel[-1]:.2f} MPa")

    # Larson-Miller
    tr = cm.rupture_time(100.0, T)
    print(f"Rupture time at 100 MPa:  {tr:.1f} hours")
    sr = cm.rupture_stress(tr, T)
    print(f"Rupture stress (roundtrip): {sr:.1f} MPa")

    # Composite creep
    eps_comp = cm.composite_creep(sigma=100.0, t=10000.0, V_f=0.4, rule="voigt")
    print(f"Composite creep strain:   {eps_comp:.6f}")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    axes[0].plot(t, eps)
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Creep strain")
    axes[0].set_title("Creep curve")
    axes[0].grid(True)

    axes[1].plot(t_rel, sig_rel)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Stress (MPa)")
    axes[1].set_title("Stress relaxation")
    axes[1].grid(True)

    sigmas = np.logspace(1, 2.5, 50)
    lmp_vals = [cm.larson_miller(s) for s in sigmas]
    axes[2].plot(sigmas, lmp_vals)
    axes[2].set_xlabel("Stress (MPa)")
    axes[2].set_ylabel("LMP")
    axes[2].set_title("Larson-Miller")
    axes[2].set_xscale("log")
    axes[2].grid(True)

    plt.tight_layout()
    plt.show()
