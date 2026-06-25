"""
Fatigue Analysis Module — S-N Curves, Rainflow Counting, Damage Accumulation
=============================================================================

Implements classical fatigue analysis methods commonly used in mechanical
design and structural integrity assessment:

  - S-N curves: Woehler (power law), Basquin
  - Rainflow cycle counting (simplified 3-point algorithm)
  - Palmgren-Miner linear damage accumulation
  - Haigh diagram (Goodman, Gerber, Soderberg mean stress corrections)
  - Variable amplitude loading analysis

References
----------
- Woehler, A. (1870). Über die Festigkeitsversuche mit Eisen und Stahl.
- Basquin, O. H. (1910). The exponential law of endurance tests.
- Palmgren, A. (1924). Die Lebensdauer von Kugellagern.
- Miner, M. A. (1945). Cumulative damage in fatigue.
- Goodman, J. (1899). Mechanics applied to engineering.
- Gerber, W. (1874). Bestimmung der zulässigen Spannungen in Eisenkonstruktionen.
- Soderberg, C. R. (1939). Factor of safety and working stress.
- ASTM E1049-85 (2017). Standard practices for cycle counting in fatigue analysis.

Classes
-------
FatigueAnalysis
    Main class for S-N based fatigue assessment.
"""

from __future__ import annotations

from typing import Callable, Literal, Optional

import numpy as np


# ---------------------------------------------------------------------------
#  S-N curve core functions
# ---------------------------------------------------------------------------

def _woehler_curve(
    N: np.ndarray,
    S_f: float,
    b: float,
    N_f: float = 1e6,
) -> np.ndarray:
    """Woehler (power law) S-N curve: S = S_f * (N / N_f)^b.

    Parameters
    ----------
    N : np.ndarray
        Number of cycles to failure.
    S_f : float
        Fatigue strength at N_f cycles (MPa).
    b : float
        Exponent (negative for typical metals, e.g. -0.1 to -0.15).
    N_f : float, optional
        Reference number of cycles (default 1e6).

    Returns
    -------
    S : np.ndarray
        Stress amplitude (MPa).
    """
    return S_f * (N / N_f) ** b


def _basquin_curve(
    N: np.ndarray,
    sigma_f: float,
    b: float,
) -> np.ndarray:
    """Basquin S-N curve: S = sigma_f * (2N)^b.

    Parameters
    ----------
    N : np.ndarray
        Number of cycles to failure.
    sigma_f : float
        Fatigue strength coefficient (MPa).
    b : float
        Fatigue strength exponent (typically -0.05 to -0.15).

    Returns
    -------
    S : np.ndarray
        Stress amplitude (MPa).
    """
    return sigma_f * (2.0 * N) ** b


# ---------------------------------------------------------------------------
#  Rainflow counting (simplified 3-point algorithm)
# ---------------------------------------------------------------------------

def _rainflow_3point(
    history: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Simplified 3-point rainflow cycle counting (ASTM E1049).

    Extracts cycles from a stress history as (range, mean) pairs.

    Parameters
    ----------
    history : np.ndarray, shape (n,)
        Sequence of turning points (peaks and valleys).

    Returns
    -------
    ranges : np.ndarray
        Cycle ranges (max - min).
    means : np.ndarray
        Cycle means ((max + min) / 2).
    """
    # Extract peaks and valleys
    if len(history) < 3:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    # Keep only turning points
    extrema = [history[0]]
    for i in range(1, len(history) - 1):
        prev, curr, nxt = history[i - 1], history[i], history[i + 1]
        if (curr > prev and curr >= nxt) or (curr < prev and curr <= nxt):
            extrema.append(curr)
    extrema.append(history[-1])
    pts = np.array(extrema, dtype=np.float64)

    ranges: list[float] = []
    means: list[float] = []
    i = 0
    while i < len(pts) - 2:
        X = abs(pts[i + 1] - pts[i])
        Y = abs(pts[i + 2] - pts[i + 1])
        if X >= Y:
            # Count a cycle
            rng = Y
            mn = 0.5 * (pts[i + 1] + pts[i + 2])
            ranges.append(rng)
            means.append(mn)
            pts = np.delete(pts, [i + 1, i + 2])
            i = max(0, i - 1)
        else:
            i += 1

    # Remaining points form a half-cycle (residue)
    for j in range(len(pts) - 1):
        ranges.append(abs(pts[j + 1] - pts[j]))
        means.append(0.5 * (pts[j + 1] + pts[j]))

    return np.array(ranges, dtype=np.float64), np.array(means, dtype=np.float64)


# ---------------------------------------------------------------------------
#  Mean stress corrections
# ---------------------------------------------------------------------------

def _goodman_correction(
    Sa: np.ndarray,
    Sm: np.ndarray,
    Su: float,
) -> np.ndarray:
    """Goodman mean stress correction: Sa_corr = Sa / (1 - Sm / Su).

    Parameters
    ----------
    Sa : np.ndarray
        Stress amplitude (MPa).
    Sm : np.ndarray
        Mean stress (MPa).
    Su : float
        Ultimate tensile strength (MPa).

    Returns
    -------
    Sa_eq : np.ndarray
        Equivalent fully-reversed stress amplitude (MPa).
    """
    return Sa / (1.0 - Sm / Su + 1e-12)


def _gerber_correction(
    Sa: np.ndarray,
    Sm: np.ndarray,
    Su: float,
) -> np.ndarray:
    """Gerber mean stress correction: Sa_corr = Sa / (1 - (Sm / Su)^2).

    Parameters
    ----------
    Sa : np.ndarray
        Stress amplitude (MPa).
    Sm : np.ndarray
        Mean stress (MPa).
    Su : float
        Ultimate tensile strength (MPa).

    Returns
    -------
    Sa_eq : np.ndarray
        Equivalent fully-reversed stress amplitude (MPa).
    """
    return Sa / (1.0 - (Sm / Su) ** 2 + 1e-12)


def _soderberg_correction(
    Sa: np.ndarray,
    Sm: np.ndarray,
    Sy: float,
) -> np.ndarray:
    """Soderberg mean stress correction: Sa_corr = Sa / (1 - Sm / Sy).

    Uses yield strength (most conservative).

    Parameters
    ----------
    Sa : np.ndarray
        Stress amplitude (MPa).
    Sm : np.ndarray
        Mean stress (MPa).
    Sy : float
        Yield strength (MPa).

    Returns
    -------
    Sa_eq : np.ndarray
        Equivalent fully-reversed stress amplitude (MPa).
    """
    return Sa / (1.0 - Sm / Sy + 1e-12)


# ---------------------------------------------------------------------------
#  Main class
# ---------------------------------------------------------------------------

class FatigueAnalysis:
    """Fatigue analysis using S-N curves and linear damage accumulation.

    Parameters
    ----------
    sn_type : str
        Type of S-N curve: 'woehler' or 'basquin'.
    S_f : float, optional
        Fatigue strength coefficient for Woehler (MPa, default 200.0).
        For Basquin, this is sigma_f'.
    b : float, optional
        Exponent (default -0.1 for Woehler, -0.085 for Basquin).
    N_ref : float, optional
        Reference cycles for Woehler curve (default 1e6).
    Su : float, optional
        Ultimate tensile strength (MPa, default 400.0).
    Sy : float, optional
        Yield strength (MPa, default 250.0).

    Attributes
    ----------
    sn_type : str
        S-N curve type.
    """

    def __init__(
        self,
        sn_type: Literal["woehler", "basquin"] = "woehler",
        S_f: float = 200.0,
        b: float = -0.1,
        N_ref: float = 1e6,
        Su: float = 400.0,
        Sy: float = 250.0,
    ) -> None:
        self.sn_type = sn_type
        self.S_f = S_f
        self.b = b
        self.N_ref = N_ref
        self.Su = Su
        self.Sy = Sy
        self._sn_func: Callable = (
            _woehler_curve if sn_type == "woehler" else _basquin_curve
        )

    # -- S-N curve -----------------------------------------------------------

    def sn_curve(
        self,
        N: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Evaluate the S-N curve at given cycle counts.

        Parameters
        ----------
        N : np.ndarray, optional
            Cycles to failure. If None, returns a default curve from
            1 to 1e7 cycles.

        Returns
        -------
        S : np.ndarray
            Stress amplitude (MPa).
        """
        if N is None:
            N = np.logspace(0, 7, 200)
        if self.sn_type == "woehler":
            return _woehler_curve(N, self.S_f, self.b, self.N_ref)
        else:
            return _basquin_curve(N, self.S_f, self.b)

    def cycles_to_failure(self, Sa: float) -> float:
        """Compute cycles to failure for a given stress amplitude.

        Parameters
        ----------
        Sa : float
            Stress amplitude (MPa).

        Returns
        -------
        Nf : float
            Number of cycles to failure.
        """
        if self.sn_type == "woehler":
            return float(self.N_ref * (Sa / self.S_f) ** (1.0 / self.b))
        else:
            return float(0.5 * (Sa / self.S_f) ** (1.0 / self.b))

    # -- Rainflow ------------------------------------------------------------

    def rainflow_count(
        self,
        history: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Perform rainflow cycle counting on a stress history.

        Parameters
        ----------
        history : np.ndarray, shape (n,)
            Stress history (time series of peaks and valleys).

        Returns
        -------
        ranges : np.ndarray
            Cycle ranges (MPa).
        means : np.ndarray
            Cycle means (MPa).
        counts : np.ndarray
            Cycle count per bin (ones for full cycles, 0.5 for half-cycles).
            For the simplified algorithm, all detected events
            are counted as 1.0.
        """
        ranges, means = _rainflow_3point(history)
        counts = np.ones_like(ranges)
        return ranges, means, counts

    # -- Damage accumulation -------------------------------------------------

    def damage_accumulation(
        self,
        ranges: np.ndarray,
        counts: Optional[np.ndarray] = None,
        means: Optional[np.ndarray] = None,
        correction: Literal["goodman", "gerber", "soderberg", "none"] = "none",
    ) -> float:
        """Palmgren-Miner linear damage accumulation.

        Parameters
        ----------
        ranges : np.ndarray
            Stress ranges (MPa).
        counts : np.ndarray, optional
            Cycle counts per range (default ones).
        means : np.ndarray, optional
            Mean stresses (MPa, default zeros).
        correction : str, optional
            Mean stress correction type (default 'none').

        Returns
        -------
        D : float
            Total accumulated damage (D >= 1 indicates failure).
        """
        n = len(ranges)
        if counts is None:
            counts = np.ones(n)
        if means is None:
            means = np.zeros(n)

        D = 0.0
        for rng, cnt, mn in zip(ranges, counts, means):
            Sa = 0.5 * rng
            if correction == "goodman":
                Sa_eq = _goodman_correction(np.array([Sa]), np.array([mn]), self.Su)[0]
            elif correction == "gerber":
                Sa_eq = _gerber_correction(np.array([Sa]), np.array([mn]), self.Su)[0]
            elif correction == "soderberg":
                Sa_eq = _soderberg_correction(np.array([Sa]), np.array([mn]), self.Sy)[0]
            else:
                Sa_eq = Sa

            Nf = self.cycles_to_failure(Sa_eq)
            D += cnt / Nf

        return float(D)

    def fatigue_life(
        self,
        history: np.ndarray,
        correction: Literal["goodman", "gerber", "soderberg", "none"] = "none",
    ) -> tuple[float, float, float]:
        """Compute fatigue life for a variable amplitude stress history.

        Parameters
        ----------
        history : np.ndarray
            Stress history (time series).
        correction : str, optional
            Mean stress correction type.

        Returns
        -------
        D : float
            Damage per block.
        life_repeats : float
            Number of repeats of the block until failure (1/D).
        life_cycles : float
            Equivalent constant-amplitude life in cycles.
        """
        ranges, means, counts = self.rainflow_count(history)
        D = self.damage_accumulation(ranges, counts, means, correction)
        life_repeats = 1.0 / D if D > 0 else np.inf
        life_cycles = float(life_repeats * np.sum(counts))
        return D, life_repeats, life_cycles

    # -- Haigh diagram -------------------------------------------------------

    def haigh_diagram(
        self,
        Sa_range: Optional[np.ndarray] = None,
        Sm_range: Optional[np.ndarray] = None,
        N_target: float = 1e6,
        methods: Optional[list[str]] = None,
    ) -> dict[str, np.ndarray]:
        """Build a Haigh diagram (constant-life diagram).

        Parameters
        ----------
        Sa_range : np.ndarray, optional
            Stress amplitude values (MPa). If None, uses 100 points
            from 0 to S_f.
        Sm_range : np.ndarray, optional
            Mean stress values (MPa). If None, uses 100 points
            from 0 to Su.
        N_target : float, optional
            Target fatigue life (cycles, default 1e6).
        methods : list of str, optional
            Mean stress correction models to include.
            Default is ['goodman', 'gerber', 'soderberg'].

        Returns
        -------
        diagram : dict
            Keys are method names, values are Sa arrays at each Sm.
            Also contains 'Sm' key with the mean stress grid.
        """
        if Sa_range is None:
            # S from S-N curve at N_target
            S_at_N = self.sn_curve(np.array([N_target]))[0]
            Sa_range = np.linspace(0, S_at_N * 1.1, 100)
        if Sm_range is None:
            Sm_range = np.linspace(0, self.Su, 100)
        if methods is None:
            methods = ["goodman", "gerber", "soderberg"]

        diagram: dict[str, np.ndarray] = {"Sm": Sm_range}
        for method in methods:
            dia: list[float] = []
            for sm in Sm_range:
                if sm == 0:
                    dia.append(self.sn_curve(np.array([N_target]))[0])
                else:
                    # Back-calculate Sa such that corrected Sa_eq gives N_target
                    Sa_eq_target = self.sn_curve(np.array([N_target]))[0]
                    if method == "goodman":
                        Sa = Sa_eq_target * (1.0 - sm / self.Su)
                    elif method == "gerber":
                        ratio = sm / self.Su
                        Sa = Sa_eq_target * (1.0 - ratio ** 2)
                    elif method == "soderberg":
                        Sa = Sa_eq_target * (1.0 - sm / self.Sy)
                    else:
                        Sa = Sa_eq_target
                    dia.append(max(0.0, Sa))
            diagram[method] = np.array(dia)

        return diagram

    def plot_haigh(
        self,
        N_target: float = 1e6,
        methods: Optional[list[str]] = None,
        ax=None,
    ) -> None:
        """Plot the Haigh diagram.

        Parameters
        ----------
        N_target : float, optional
            Target fatigue life (default 1e6).
        methods : list of str, optional
            Correction models to plot.
        ax : matplotlib.axes.Axes, optional
            Axes to plot on.
        """
        import matplotlib.pyplot as plt

        if methods is None:
            methods = ["goodman", "gerber", "soderberg"]
        diagram = self.haigh_diagram(N_target=N_target, methods=methods)
        colors = {"goodman": "#e74c3c", "gerber": "#2ecc71", "soderberg": "#3498db"}

        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(7, 5))
        for method in methods:
            ax.plot(
                diagram["Sm"], diagram[method],
                label=method.capitalize(), color=colors.get(method, "gray"), lw=2,
            )
        ax.axhline(0, color="gray", lw=0.5)
        ax.axvline(0, color="gray", lw=0.5)
        ax.set_xlabel("Mean stress Sm (MPa)")
        ax.set_ylabel("Stress amplitude Sa (MPa)")
        ax.set_title(f"Haigh diagram (N = {N_target:.0e} cycles)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # -- Convenience factory methods -----------------------------------------

    @classmethod
    def from_material(
        cls,
        material: str,
    ) -> "FatigueAnalysis":
        """Create a FatigueAnalysis from a predefined material name.

        Parameters
        ----------
        material : str
            One of 'steel_4340', 'aluminium_7075', 'steel_mild'.

        Returns
        -------
        fa : FatigueAnalysis
        """
        materials = {
            "steel_4340": {"sn_type": "basquin", "S_f": 950.0, "b": -0.08, "Su": 1240.0, "Sy": 1080.0},
            "aluminium_7075": {"sn_type": "basquin", "S_f": 500.0, "b": -0.12, "Su": 570.0, "Sy": 500.0},
            "steel_mild": {"sn_type": "woehler", "S_f": 250.0, "b": -0.12, "Su": 400.0, "Sy": 250.0},
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

    # Steel S-N curve
    fa = FatigueAnalysis(sn_type="woehler", S_f=200.0, b=-0.1, Su=400.0, Sy=250.0)

    # S-N curve
    N = np.logspace(3, 7, 100)
    S = fa.sn_curve(N)
    print(f"At N=1e5 cycles, S = {fa.sn_curve(np.array([1e5]))[0]:.2f} MPa")
    print(f"At S=150 MPa, Nf = {fa.cycles_to_failure(150.0):.1f} cycles")

    # Variable amplitude loading
    np.random.seed(42)
    t = np.linspace(0, 10, 200)
    history = 100.0 * np.sin(2 * np.pi * 1.0 * t) + 30.0 * np.sin(2 * np.pi * 3.5 * t)

    D, repeats, cycles = fa.fatigue_life(history, correction="goodman")
    print(f"\nFatigue life estimate:")
    print(f"  Damage per block:  {D:.4e}")
    print(f"  Repeats to fail:   {repeats:.1f}")
    print(f"  Total cycles:      {cycles:.1f}")

    # Haigh diagram
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.loglog(N, S)
    ax1.set_xlabel("Cycles to failure N")
    ax1.set_ylabel("Stress amplitude S (MPa)")
    ax1.set_title("S-N curve (Woehler)")
    ax1.grid(True, which="both", alpha=0.3)
    fa.plot_haigh(ax=ax2)
    plt.tight_layout()
    plt.show()
