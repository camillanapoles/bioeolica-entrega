"""
Multi-Objective Topology Optimization Module
==============================================

Extends the SIMP-based topology optimization with weighted-sum multi-objective
optimization, combining compliance minimisation, mass minimisation, and cost
minimisation into a single scalar objective.

The scalarised subproblem solved at each iteration is:

    minimise    F(x) = w_c * f_c(x) + w_m * f_m(x) + w_s * f_s(x)
    subject to  V(x) / V0 <= volfrac
                0 < x_min <= x_i <= 1

where
    f_c(x) = compliance (f^T u)
    f_m(x) = mass fraction (mean density)
    f_s(x) = cost fraction (normalised material cost)
    w_c, w_m, w_s are user-supplied weights (normalised to sum 1.0).

The module also provides an approximate Pareto-front sampler that sweeps the
volume fraction constraint and records the individual objective values.

References
----------
- Sigmund, O. (2001). A 99 line topology optimization code written in MATLAB.
  Structural and Multidisciplinary Optimization, 21(2), 120-127.
- Andreassen, E., et al. (2011). Efficient topology optimization in MATLAB
  using 88 lines of code. Structural and Multidisciplinary Optimization,
  43(1), 1-16.
- Bendsøe, M. P., & Sigmund, O. (2003). Topology Optimization: Theory,
  Methods, and Applications. Springer.
- Min, S., et al. (2000). A multiobjective topology optimization using
  the weighted sum approach. KSME International Journal, 14(1), 49-56.

Classes
-------
TopOptMultiObj
    Multi-objective topology optimisation via weighted-sum SIMP.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from modules.topology_optimization import (
    TopOpt,
    _node_indices,
    _edof_from_nids,
)


class TopOptMultiObj(TopOpt):
    """Multi-objective topology optimisation via weighted-sum SIMP.

    Extends the classic SIMP compliance-minimisation problem with additional
    mass and cost objectives. The three objectives are combined through a
    normalised weighted sum:

        F = w_c * (f_c / f_c0) + w_m * f_m + w_s * f_s

    where f_c0 is the compliance of the initial uniform-density design, used
    to scale compliance to a similar magnitude as the other (unit-normalised)
    terms. The mass objective is the mean density (volume fraction) and the
    cost objective is the mean material cost.

    Parameters
    ----------
    nelx : int
        Number of elements in the x-direction (horizontal).
    nely : int
        Number of elements in the y-direction (vertical).
    volfrac : float
        Volume fraction constraint (0 < volfrac <= 1).
    penal : float, optional
        SIMP penalisation power (default 3.0).
    rmin : float, optional
        Filter radius in element units (default 1.5).
    weights : dict, optional
        Objective weights with keys ``'compliance'``, ``'mass'``, ``'cost'``.
        Values are normalised to sum to 1.0. If None, equal weights (1/3 each)
        are used (default None).
    material_cost : float, optional
        Cost per unit volume of solid material (default 1.0).
    void_cost : float, optional
        Cost per unit volume of void material (default 0.0).
    E0 : float, optional
        Young's modulus of solid material (default 1.0).
    Emin : float, optional
        Young's modulus of void material (default 1e-9).
    nu : float, optional
        Poisson ratio (default 0.3).
    x_min : float, optional
        Minimum density to avoid singular stiffness (default 1e-3).

    Attributes
    ----------
    density : np.ndarray, shape (nely, nelx)
        Current density field.
    weights : dict
        Normalised objective weights.
    compliance_history : list of float
        Compliance at each iteration.
    mass_history : list of float
        Mass fraction at each iteration.
    cost_history : list of float
        Cost fraction at each iteration.
    multiobj_history : list of float
        Scalarised multi-objective value at each iteration.
    iteration : int
        Current iteration number.

    Examples
    --------
    >>> opt = TopOptMultiObj(nelx=60, nely=20, volfrac=0.5,
    ...                      weights={'compliance': 0.5, 'mass': 0.3, 'cost': 0.2})
    >>> x_opt = opt.solve(max_iter=100)
    >>> opt.objective_breakdown()
    {'compliance': 42.3, 'mass': 0.45, 'cost': 0.45, 'multiobj': 0.85}
    """

    def __init__(
        self,
        nelx: int,
        nely: int,
        volfrac: float,
        penal: float = 3.0,
        rmin: float = 1.5,
        weights: Optional[dict[str, float]] = None,
        material_cost: float = 1.0,
        void_cost: float = 0.0,
        E0: float = 1.0,
        Emin: float = 1e-9,
        nu: float = 0.3,
        x_min: float = 1e-3,
    ) -> None:
        super().__init__(
            nelx=nelx,
            nely=nely,
            volfrac=volfrac,
            penal=penal,
            rmin=rmin,
            E0=E0,
            Emin=Emin,
            nu=nu,
            x_min=x_min,
        )

        # --- Normalise weights -------------------------------------------------
        if weights is None:
            weights = {"compliance": 1.0 / 3.0, "mass": 1.0 / 3.0, "cost": 1.0 / 3.0}
        required_keys = {"compliance", "mass", "cost"}
        if set(weights.keys()) != required_keys:
            raise ValueError(
                f"weights must contain exactly {required_keys}, got {set(weights.keys())}"
            )
        for k, v in weights.items():
            if v < 0:
                raise ValueError(f"Weight '{k}' is negative ({v}). All weights must be >= 0.")
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Sum of weights must be positive.")
        self.weights = {k: v / total for k, v in weights.items()}

        # Cost model parameters
        self.material_cost = float(material_cost)
        self.void_cost = float(void_cost)

        # Additional history arrays
        self.mass_history: list[float] = []
        self.cost_history: list[float] = []
        self.multiobj_history: list[float] = []

        # Compliance normalisation factor (computed on first step)
        self._f_c0: Optional[float] = None

    # ------------------------------------------------------------------
    # Objective and sensitivity helpers
    # ------------------------------------------------------------------

    def _compute_compliance(
        self, u_full: np.ndarray, f_full: np.ndarray
    ) -> float:
        """Compute compliance from displacement and force vectors.

        Parameters
        ----------
        u_full : np.ndarray, shape (ndof,)
            Displacement vector from the current FEM solve.
        f_full : np.ndarray, shape (ndof,)
            Global force vector.

        Returns
        -------
        comp : float
            Compliance :math:`f^T u`.
        """
        return float(np.dot(f_full, u_full))

    def _compute_mass_fraction(self, x: np.ndarray) -> float:
        """Compute mass fraction (mean density).

        Parameters
        ----------
        x : np.ndarray, shape (nely, nelx)
            Density field.

        Returns
        -------
        mass : float
            Mean density in [0, 1].
        """
        return float(np.mean(x))

    def _compute_cost_fraction(self, x: np.ndarray) -> float:
        """Compute normalised cost fraction.

        The cost per element is modelled as a linear interpolation between
        void and solid cost:

            cost_i = material_cost * x_i + void_cost * (1 - x_i)

        The cost fraction returned is the mean value normalised by the
        solid-material cost so that it lies in [0, 1].

        Parameters
        ----------
        x : np.ndarray, shape (nely, nelx)
            Density field.

        Returns
        -------
        cost : float
            Normalised mean cost in [0, 1].
        """
        cm = self.material_cost
        cv = self.void_cost
        # Per-element cost, normalised so solid=1, void=0
        cost_per_elem = (cm * x + cv * (1.0 - x)) / max(cv, cm, 1e-12)
        return float(np.mean(cost_per_elem))

    def _sensitivity_compliance(self, x: np.ndarray, u_full: np.ndarray) -> np.ndarray:
        """Return the sensitivity of compliance w.r.t. density.

        Uses the standard 88-line SIMP sensitivity (Andreassen et al. 2011)
        which includes the :math:`E_e` normalisation in the denominator.

        Parameters
        ----------
        x : np.ndarray, shape (nely, nelx)
            Density field.
        u_full : np.ndarray, shape (ndof,)
            Displacement vector from the current FEM solve.

        Returns
        -------
        dc : np.ndarray, shape (nely, nelx)
            Compliance sensitivity (negative values expected).
        """
        dc = np.zeros((self.nely, self.nelx), dtype=np.float64)
        ke = self._ke
        for elx in range(self.nelx):
            for ely in range(self.nely):
                nids = _node_indices(ely, elx, self.nelx, self.nely)
                edof = _edof_from_nids(nids)
                u_e = u_full[edof]
                E_e = self.Emin + x[ely, elx] ** self.penal * (self.E0 - self.Emin)
                dE_dx = self.penal * x[ely, elx] ** (self.penal - 1) * (
                    self.E0 - self.Emin
                )
                dc[ely, elx] = -dE_dx * np.dot(u_e, ke @ u_e) / (E_e + 1e-12)
        return dc

    def step(self) -> float:
        """Perform one multi-objective optimisation iteration.

        Returns
        -------
        F : float
            Scalarised multi-objective value at the new design point.
            Positive-definite; smaller values are better.
        """
        x = self.density

        # --- Single FEM assembly and solve (avoids duplicate work) --------
        K = self._build_global_stiffness(x)
        K_dense = K.toarray()
        ndof = self._ndof
        nely = self.nely
        nelx = self.nelx

        # Fixed DOFs — left edge (x = 0)
        fixed = np.arange(0, 2 * (nely + 1), dtype=np.int32)
        all_dofs = np.arange(ndof, dtype=np.int32)
        free = np.setdiff1d(all_dofs, fixed)

        # Force vector — point load downward at centre of right edge
        f_full = np.zeros(ndof, dtype=np.float64)
        load_node = (nely + 1) * nelx + nely // 2
        f_full[2 * load_node + 1] = -1.0

        # Solve reduced system
        K_red = K_dense[np.ix_(free, free)]
        f_red = f_full[free]
        u_red = np.linalg.solve(K_red, f_red)

        u_full = np.zeros(ndof, dtype=np.float64)
        u_full[free] = u_red

        # --- Individual objective values -----------------------------------
        f_c = self._compute_compliance(u_full, f_full)
        f_m = self._compute_mass_fraction(x)
        f_s = self._compute_cost_fraction(x)

        # Normalise compliance by its value at first iteration
        if self._f_c0 is None:
            self._f_c0 = f_c
        f_c_norm = f_c / self._f_c0 if self._f_c0 > 1e-12 else f_c

        # Scalarised objective
        w = self.weights
        F = w["compliance"] * f_c_norm + w["mass"] * f_m + w["cost"] * f_s

        # --- Sensitivity ---------------------------------------------------
        dc_c = self._sensitivity_compliance(x, u_full)

        # Sensitivity of mass fraction: df_m / dx_i = 1 / n_elements
        n_elems = float(x.size)
        dc_m = np.full_like(x, 1.0 / n_elems)

        # Sensitivity of cost fraction:
        #   cost_i = (cm * x_i + cv * (1 - x_i)) / max(cv, cm)
        #   d(cost_i)/dx_i = (cm - cv) / max(cv, cm, eps)
        cm = self.material_cost
        cv = self.void_cost
        cost_scale = max(cv, cm, 1e-12)
        dc_s = np.full_like(x, (cm - cv) / (n_elems * cost_scale))

        # Combined sensitivity (weighted sum, with compliance normalisation)
        dc_combined = (
            w["compliance"] * dc_c / (self._f_c0 + 1e-12)
            + w["mass"] * dc_m
            + w["cost"] * dc_s
        )

        # --- Filter sensitivities -----------------------------------------
        dc_filtered = self._filter_sensitivities(x, dc_combined)

        # --- OC update (volume constraint still applies) -------------------
        self.density, _ = self._optimality_criteria_update(
            self.density,
            dc_filtered,
            self.volfrac,
            self.penal,
            self.x_min,
        )

        # Store last FEM state for external queries
        self._u_full = u_full
        self._f_full = f_full
        self.compliance_history.append(f_c)
        self.mass_history.append(f_m)
        self.cost_history.append(f_s)
        self.multiobj_history.append(F)
        self.iteration += 1

        return F

    def solve(
        self,
        max_iter: int = 200,
        tol: float = 1e-4,
        verbose: bool = False,
    ) -> np.ndarray:
        """Run multi-objective topology optimisation to convergence.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations (default 200).
        tol : float, optional
            Relative convergence tolerance on the scalarised multi-objective
            value (default 1e-4).
        verbose : bool, optional
            If True, print iteration info (default False).

        Returns
        -------
        density : np.ndarray, shape (nely, nelx)
            Optimised density distribution.
        """
        for _ in range(max_iter):
            F = self.step()
            if verbose:
                bd = self.objective_breakdown()
                print(
                    f"Iteration {self.iteration:3d}: "
                    f"F = {F:.6e}, "
                    f"c = {bd['compliance']:.6e}, "
                    f"m = {bd['mass']:.4f}, "
                    f"s = {bd['cost']:.4f}, "
                    f"chg = {self._relative_change_multi():.6e}"
                )
            if self._relative_change_multi() < tol and self.iteration > 1:
                self._converged = True
                if verbose:
                    print(f"Converged after {self.iteration} iterations.")
                break
        return self.density

    def _relative_change_multi(self) -> float:
        """Relative change in the scalarised objective over the last 3 steps.

        Returns
        -------
        chg : float
            Relative change; returns 1.0 if fewer than 3 records exist.
        """
        if len(self.multiobj_history) < 3:
            return 1.0
        prev = self.multiobj_history[-2]
        curr = self.multiobj_history[-1]
        return float(abs((curr - prev) / (prev + 1e-12)))

    def objective_breakdown(self) -> Dict[str, float]:
        """Return the individual objective values at the current design.

        Returns
        -------
        breakdown : dict
            Keys ``'compliance'``, ``'mass'``, ``'cost'``, ``'multiobj'``.
            The ``'multiobj'`` entry is the scalarised value using the
            current (normalised) weights.
        """
        x = self.density
        u_full = getattr(self, "_u_full", None)
        f_full = getattr(self, "_f_full", None)
        if u_full is None or f_full is None:
            # Fallback — perform a fresh FEM solve
            K = self._build_global_stiffness(x)
            K_dense = K.toarray()
            ndof = self._ndof
            nely = self.nely
            nelx = self.nelx
            fixed = np.arange(0, 2 * (nely + 1), dtype=np.int32)
            all_dofs = np.arange(ndof, dtype=np.int32)
            free = np.setdiff1d(all_dofs, fixed)
            f_full = np.zeros(ndof, dtype=np.float64)
            load_node = (nely + 1) * nelx + nely // 2
            f_full[2 * load_node + 1] = -1.0
            K_red = K_dense[np.ix_(free, free)]
            f_red = f_full[free]
            u_red = np.linalg.solve(K_red, f_red)
            u_full = np.zeros(ndof, dtype=np.float64)
            u_full[free] = u_red
        f_c = self._compute_compliance(u_full, f_full)
        f_m = self._compute_mass_fraction(x)
        f_s = self._compute_cost_fraction(x)
        f_c0 = self._f_c0 if self._f_c0 is not None else f_c
        f_c_norm = f_c / f_c0 if f_c0 > 1e-12 else f_c
        w = self.weights
        F = w["compliance"] * f_c_norm + w["mass"] * f_m + w["cost"] * f_s
        return {"compliance": f_c, "mass": f_m, "cost": f_s, "multiobj": F}

    def pareto_frontier(
        self,
        samples: int = 10,
        volfrac_range: tuple[float, float] = (0.2, 0.8),
    ) -> List[Dict[str, Any]]:
        """Approximate the Pareto front by sweeping the volume fraction.

        For each volume fraction in the sampled range, a fresh
        ``TopOptMultiObj`` instance is created (with the same weights and
        material parameters) and converged. The individual objective values
        at convergence are recorded.

        Parameters
        ----------
        samples : int, optional
            Number of volume fraction samples (default 10).
        volfrac_range : tuple of float, optional
            (min_volfrac, max_volfrac) range to sweep (default (0.2, 0.8)).

        Returns
        -------
        frontier : list of dict
            Each dict contains ``'volfrac'``, ``'compliance'``, ``'mass'``,
            ``'cost'``, and ``'multiobj'``. Ordered by increasing volfrac.

        Notes
        -----
        This is an expensive operation: it runs ``samples`` independent
        optimisation cycles to completion. For problem sizes above roughly
        100x100 elements, consider reducing the number of samples or
        increasing the convergence tolerance.

        Examples
        --------
        >>> opt = TopOptMultiObj(60, 20, volfrac=0.5)
        >>> front = opt.pareto_frontier(samples=5, volfrac_range=(0.3, 0.7))
        >>> len(front)
        5
        """
        vf_min, vf_max = volfrac_range
        volfracs = np.linspace(vf_min, vf_max, samples)

        frontier: list[dict[str, Any]] = []
        w = self.weights
        penal = self.penal
        rmin = self.rmin
        E0 = self.E0
        Emin = self.Emin
        nu_val = self.nu
        x_min = self.x_min
        mat_cost = self.material_cost
        void_cost = self.void_cost

        for vf in volfracs:
            sub = TopOptMultiObj(
                nelx=self.nelx,
                nely=self.nely,
                volfrac=float(vf),
                penal=penal,
                rmin=rmin,
                weights=w,
                material_cost=mat_cost,
                void_cost=void_cost,
                E0=E0,
                Emin=Emin,
                nu=nu_val,
                x_min=x_min,
            )
            sub.solve(max_iter=40, tol=5e-3, verbose=False)
            bd = sub.objective_breakdown()
            frontier.append(
                {
                    "volfrac": float(vf),
                    "compliance": bd["compliance"],
                    "density": bd["mass"],
                    "cost": bd["cost"],
                    "multiobj": bd["multiobj"],
                }
            )

        return frontier

    def reset(self) -> None:
        """Reset to initial uniform-density state, clearing all histories."""
        super().reset()
        self.mass_history.clear()
        self.cost_history.clear()
        self.multiobj_history.clear()
        self._f_c0 = None

    def compliance(self, x: Optional[np.ndarray] = None) -> float:
        """Compute compliance (delegates to parent).

        Parameters
        ----------
        x : np.ndarray, optional
            Density field. If None, uses current density.

        Returns
        -------
        comp : float
            Compliance value.
        """
        return super().compliance(x)


# ---------------------------------------------------------------------------
#  Usage example (run as script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Equal-weight multi-objective optimisation of an MBB beam
    opt = TopOptMultiObj(
        nelx=60,
        nely=20,
        volfrac=0.5,
        penal=3.0,
        rmin=1.5,
        weights={"compliance": 1.0 / 3, "mass": 1.0 / 3, "cost": 1.0 / 3},
    )
    print("Solving multi-objective topology optimisation (60x20, volfrac=0.5)...")
    x_opt = opt.solve(max_iter=100, verbose=True)

    bd = opt.objective_breakdown()
    print()
    print("Final objective breakdown:")
    for k, v in bd.items():
        print(f"  {k}: {v:.6f}")
    print(f"  Volume fraction: {opt.volume_fraction:.4f}")
    print(f"  Converged:       {opt.converged}")

    # --- Plot -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    opt.plot_density(ax=axes[0, 0])
    axes[0, 0].set_title("Optimised topology (multi-objective)")

    axes[0, 1].plot(opt.compliance_history, label="Compliance")
    axes[0, 1].set_xlabel("Iteration")
    axes[0, 1].set_ylabel("Compliance")
    axes[0, 1].set_title("Compliance history")
    axes[0, 1].grid(True)
    axes[0, 1].legend()

    axes[1, 0].plot(opt.mass_history, label="Mass fraction", color="C2")
    axes[1, 0].plot(opt.cost_history, label="Cost fraction", color="C3")
    axes[1, 0].set_xlabel("Iteration")
    axes[1, 0].set_ylabel("Fraction")
    axes[1, 0].set_title("Mass and cost history")
    axes[1, 0].grid(True)
    axes[1, 0].legend()

    axes[1, 1].plot(opt.multiobj_history, label="Multi-objective F", color="C4")
    axes[1, 1].set_xlabel("Iteration")
    axes[1, 1].set_ylabel("F")
    axes[1, 1].set_title("Scalarised objective history")
    axes[1, 1].grid(True)
    axes[1, 1].legend()

    plt.tight_layout()
    plt.show()

    # --- Approximate Pareto front -----------------------------------------
    print("\nSampling approximate Pareto front...")
    front = opt.pareto_frontier(samples=8, volfrac_range=(0.25, 0.75))
    print(f"{'volfrac':>8s}  {'compliance':>12s}  {'density':>8s}  {'cost':>8s}")
    for pt in front:
        print(
            f"{pt['volfrac']:>8.3f}  {pt['compliance']:>12.4e}  "
            f"{pt['density']:>8.4f}  {pt['cost']:>8.4f}"
        )
