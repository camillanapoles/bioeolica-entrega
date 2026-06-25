"""
Topology Optimization Module — SIMP Method
============================================

Implements the Solid Isotropic Material with Penalization (SIMP) method for
topology optimization, targeting minimum compliance subject to a volume
constraint. Based on the classic 88-line and 99-line MATLAB codes by
Sigmund (2001) and Andreassen et al. (2011).

References
----------
- Sigmund, O. (2001). A 99 line topology optimization code written in MATLAB.
  Structural and Multidisciplinary Optimization, 21(2), 120-127.
- Andreassen, E., et al. (2011). Efficient topology optimization in MATLAB
  using 88 lines of code. Structural and Multidisciplinary Optimization, 43(1), 1-16.
- Bendsøe, M. P., & Sigmund, O. (2003). Topology Optimization: Theory, Methods,
  and Applications. Springer.

Classes
-------
TopOpt
    Main class for SIMP-based topology optimization.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.sparse import coo_matrix


def _create_element_stiffness(E: float = 1.0, nu: float = 0.3) -> np.ndarray:
    """Create the 8x8 element stiffness matrix for a 4-node quadrilateral.

    Parameters
    ----------
    E : float
        Young's modulus (default 1.0).
    nu : float
        Poisson ratio (default 0.3).

    Returns
    -------
    ke : np.ndarray, shape (8, 8)
        Element stiffness matrix.
    """
    k = np.array([
        1 / 2 - nu / 6, 1 / 8 + nu / 8, -1 / 4 - nu / 12, -1 / 8 + 3 * nu / 8,
        -1 / 4 + nu / 12, -1 / 8 - nu / 8, nu / 6, 1 / 8 - 3 * nu / 8,
    ])
    KE = np.zeros((8, 8))
    for i in range(8):
        KE[i, 0] = k[i]
        KE[i, 1] = k[(i + 1) % 8]
        KE[i, 2] = k[(i + 2) % 8]
        KE[i, 3] = k[(i + 3) % 8]
        KE[i, 4] = k[(i + 4) % 8]
        KE[i, 5] = k[(i + 5) % 8]
        KE[i, 6] = k[(i + 6) % 8]
        KE[i, 7] = k[(i + 7) % 8]
    return (E / (1 - nu ** 2)) * KE


def _node_indices(ely: int, elx: int, nelx: int, nely: int) -> np.ndarray:
    """Return the global node indices for element (ely, elx).

    Parameters
    ----------
    ely : int
        Element row index (0-based, from top).
    elx : int
        Element column index (0-based, from left).
    nelx : int
        Number of elements in x-direction.
    nely : int
        Number of elements in y-direction.

    Returns
    -------
    nids : np.ndarray, shape (4,)
        Global node numbers (one per corner).
    """
    n1 = (nely + 1) * elx + ely
    n2 = (nely + 1) * (elx + 1) + ely
    n3 = (nely + 1) * (elx + 1) + ely + 1
    n4 = (nely + 1) * elx + ely + 1
    return np.array([n1, n2, n3, n4])


def _edof_from_nids(nids: np.ndarray) -> np.ndarray:
    """Convert four node numbers to the 8 DOF indices of a quad element.

    Parameters
    ----------
    nids : np.ndarray, shape (4,)
        Node numbers (4 corners).

    Returns
    -------
    edof : np.ndarray, shape (8,)
        Global DOF indices (2 per node).
    """
    return np.array([
        2 * nids[0], 2 * nids[0] + 1,
        2 * nids[1], 2 * nids[1] + 1,
        2 * nids[2], 2 * nids[2] + 1,
        2 * nids[3], 2 * nids[3] + 1,
    ])


class TopOpt:
    """Topology optimization using the SIMP method.

    Solves the minimum compliance problem:

        minimize   c(x) = f^T u(x)
        subject to V(x) / V0 <= volfrac
                 0 < x_min <= x_i <= 1

    where x is the density vector, u are displacements, f is the load vector,
    V(x) is the material volume, V0 is the design domain volume, and volfrac
    is the allowable volume fraction.

    Parameters
    ----------
    nelx : int
        Number of elements in x-direction (horizontal).
    nely : int
        Number of elements in y-direction (vertical).
    volfrac : float
        Volume fraction constraint (0 < volfrac <= 1).
    penal : float, optional
        SIMP penalisation power (default 3.0).
    rmin : float, optional
        Filter radius in element units (default 1.5).
    E0 : float, optional
        Young's modulus of solid material (default 1.0).
    Emin : float, optional
        Young's modulus of void material (default 1e-9).
    nu : float, optional
        Poisson ratio (default 0.3).
    x_min : float, optional
        Minimum density to avoid singularity (default 1e-3).

    Attributes
    ----------
    density : np.ndarray, shape (nely, nelx)
        Current density field.
    compliance_history : list[float]
        Compliance values per iteration.
    iteration : int
        Current iteration number.
    """

    def __init__(
        self,
        nelx: int,
        nely: int,
        volfrac: float,
        penal: float = 3.0,
        rmin: float = 1.5,
        E0: float = 1.0,
        Emin: float = 1e-9,
        nu: float = 0.3,
        x_min: float = 1e-3,
    ) -> None:
        if volfrac <= 0 or volfrac > 1:
            raise ValueError("volfrac must be in (0, 1]")
        if penal < 1.0:
            raise ValueError("penal must be >= 1.0")
        if rmin < 0:
            raise ValueError("rmin must be >= 0")
        if E0 <= 0:
            raise ValueError("E0 must be positive")
        if not (0 <= nu < 0.5):
            raise ValueError("nu must be in [0, 0.5)")
        self.nelx = nelx
        self.nely = nely
        self.volfrac = volfrac
        self.penal = penal
        self.rmin = rmin
        self.E0 = E0
        self.Emin = Emin
        self.nu = nu
        self.x_min = x_min

        # Initialise density to uniform volfrac
        self.density = volfrac * np.ones((nely, nelx), dtype=np.float64)
        self.compliance_history: list[float] = []
        self.iteration = 0
        self._ke = _create_element_stiffness(E0, nu)
        self._ndof = 2 * (nelx + 1) * (nely + 1)
        self._converged = False

    def _build_global_stiffness(self, x: np.ndarray) -> coo_matrix:
        """Assemble the global stiffness matrix in sparse COO format.

        Parameters
        ----------
        x : np.ndarray, shape (nely, nelx)
            Density field.

        Returns
        -------
        K : coo_matrix
            Global stiffness matrix.
        """
        nely, nelx = self.nely, self.nelx
        ndof = self._ndof
        ke = self._ke
        # Pre-allocate for 64 entries per element
        n_entries = 64 * nelx * nely
        i_vec = np.zeros(n_entries, dtype=np.int32)
        j_vec = np.zeros(n_entries, dtype=np.int32)
        s_vec = np.zeros(n_entries, dtype=np.float64)
        idx = 0
        for elx in range(nelx):
            for ely in range(nely):
                nids = _node_indices(ely, elx, nelx, nely)
                edof = _edof_from_nids(nids)
                # SIMP penalisation
                E_e = self.Emin + x[ely, elx] ** self.penal * (self.E0 - self.Emin)
                k_e = E_e * ke
                for a in range(8):
                    for b in range(8):
                        i_vec[idx] = edof[a]
                        j_vec[idx] = edof[b]
                        s_vec[idx] = k_e[a, b]
                        idx += 1
        return coo_matrix(
            (s_vec, (i_vec, j_vec)),
            shape=(ndof, ndof),
            dtype=np.float64,
        )

    def _apply_boundary_conditions(
        self,
        K: coo_matrix,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Apply fixed DOFs and build reduced system.

        Uses a fixed boundary: left edge fixed (all DOFs = 0).
        Load: unit point load downward at centre of right edge.

        Returns
        -------
        K_red : np.ndarray, shape (n_free, n_free)
            Reduced stiffness matrix (dense for direct solve).
        f_red : np.ndarray, shape (n_free,)
            Reduced force vector.
        free_dofs : np.ndarray
            Indices of free DOFs.
        """
        nelx, nely = self.nelx, self.nely
        ndof = self._ndof
        # Fixed DOFs — left edge (x = 0)
        fixed = np.arange(0, 2 * (nely + 1), dtype=np.int32)
        all_dofs = np.arange(ndof, dtype=np.int32)
        free = np.setdiff1d(all_dofs, fixed)

        # Force vector — point load downward at centre of right edge
        f = np.zeros(ndof, dtype=np.float64)
        load_node = (nely + 1) * nelx + nely // 2
        f[2 * load_node + 1] = -1.0

        # Reduce system
        K_dense = K.toarray()
        K_red = K_dense[np.ix_(free, free)]
        f_red = f[free]
        return K_red, f_red, free

    def _filter_sensitivities(
        self, x: np.ndarray, dc: np.ndarray
    ) -> np.ndarray:
        """Apply mesh-independency filter to sensitivity field.

        Parameters
        ----------
        x : np.ndarray, shape (nely, nelx)
            Density field.
        dc : np.ndarray, shape (nely, nelx)
            Unfiltered sensitivities.

        Returns
        -------
        dcf : np.ndarray, shape (nely, nelx)
            Filtered sensitivities.
        """
        if self.rmin <= 0:
            return dc
        nelx, nely = self.nelx, self.nely
        rmin = self.rmin
        dcf = np.zeros_like(dc)
        for i in range(nelx):
            for j in range(nely):
                total = 0.0
                # Neighbourhood bounds
                i_min = max(0, i - int(np.ceil(rmin)))
                i_max = min(nelx, i + int(np.ceil(rmin)) + 1)
                j_min = max(0, j - int(np.ceil(rmin)))
                j_max = min(nely, j + int(np.ceil(rmin)) + 1)
                for k in range(i_min, i_max):
                    for l in range(j_min, j_max):
                        r = np.sqrt((i - k) ** 2 + (j - l) ** 2)
                        if r <= rmin:
                            w = rmin - r
                            dcf[j, i] += w * x[l, k] * dc[l, k]
                            total += w * x[l, k]
                if total > 0:
                    dcf[j, i] /= total
                else:
                    dcf[j, i] = dc[j, i]
        return dcf

    @staticmethod
    def _optimality_criteria_update(
        x: np.ndarray,
        dc: np.ndarray,
        volfrac: float,
        penal: float,
        x_min: float,
        move: float = 0.2,
    ) -> tuple[np.ndarray, float]:
        """Perform Optimality Criteria (OC) update.

        Classic OC update from Sigmund (2001):

            x_new = max(x_min, max(x - move, x * sqrt(-dc / (lam * dv))))
            x_new = min(1.0, min(x + move, x_new))

        where lam is found by bisection to satisfy the volume constraint.

        Parameters
        ----------
        x : np.ndarray
            Current densities.
        dc : np.ndarray
            Sensitivity of compliance (negative values expected).
        volfrac : float
            Target volume fraction.
        penal : float
            Penalisation power.
        x_min : float
            Minimum density.
        move : float, optional
            OC move limit (default 0.2).

        Returns
        -------
        x_new : np.ndarray
            Updated densities.
        lam : float
            Lagrange multiplier (lower bound).
        """
        # Sensitivity of objective is -dc (dc is negative, so -dc is positive)
        # Sensitivity of volume constraint dV/dxe = 1
        dv = 1.0

        # Bisection on Lagrange multiplier lam
        l1 = 0.0
        l2 = 1e9
        x_new = np.empty_like(x)
        for _ in range(100):
            lam = 0.5 * (l1 + l2)
            # B = -dc / (lam * dv); clip to ensure non-negative before sqrt
            B = np.clip(-dc / (lam * dv + 1e-12), a_min=1e-12, a_max=None)
            # Classic OC update: two-step bound projection
            x_new = x * np.sqrt(B)
            x_new = np.maximum(x - move, np.maximum(x_min, x_new))
            x_new = np.minimum(x + move, np.minimum(1.0, x_new))
            # Bisection: sum(x_new) > volfrac * n => lam too small => raise lower bound
            if np.sum(x_new) - volfrac * x.size > 0:
                l1 = lam
            else:
                l2 = lam
            if abs(np.sum(x_new) - volfrac * x.size) / x.size < 1e-6:
                break
        return x_new, lam

    def step(self) -> float:
        """Perform one optimisation iteration.

        Returns
        -------
        comp : float
            Compliance value at current iteration.
        """
        x = self.density
        # Assemble and solve
        K = self._build_global_stiffness(x)
        K_red, f_red, free = self._apply_boundary_conditions(K)
        u_red = np.linalg.solve(K_red, f_red)

        u_full = np.zeros(self._ndof, dtype=np.float64)
        u_full[free] = u_red

        # Compliance
        comp = float(np.dot(f_red, u_red))

        # Sensitivity
        dc = np.zeros((self.nely, self.nelx), dtype=np.float64)
        ke = self._ke
        for elx in range(self.nelx):
            for ely in range(self.nely):
                nids = _node_indices(ely, elx, self.nelx, self.nely)
                edof = _edof_from_nids(nids)
                u_e = u_full[edof]
                E_e = self.Emin + x[ely, elx] ** self.penal * (self.E0 - self.Emin)
                dE_dx = self.penal * x[ely, elx] ** (self.penal - 1) * (self.E0 - self.Emin)
                # d(c)/d(x) = -u_e^T (dK_e/dx) u_e
                dc[ely, elx] = -dE_dx * np.dot(u_e, ke @ u_e) / (E_e + 1e-12)

        # Filter
        dc = self._filter_sensitivities(x, dc)

        # OC update
        self.density, _ = self._optimality_criteria_update(
            x, dc, self.volfrac, self.penal, self.x_min
        )

        self.compliance_history.append(comp)
        self.iteration += 1
        return comp

    def solve(
        self,
        max_iter: int = 200,
        tol: float = 1e-4,
        verbose: bool = False,
    ) -> np.ndarray:
        """Run full topology optimisation to convergence.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations (default 200).
        tol : float, optional
            Relative convergence tolerance on compliance change
            (default 1e-4).
        verbose : bool, optional
            If True, print iteration info (default False).

        Returns
        -------
        density : np.ndarray, shape (nely, nelx)
            Optimised density distribution.
        """
        for it in range(max_iter):
            comp = self.step()
            if verbose:
                print(
                    f"Iteration {self.iteration:3d}: Compliance = {comp:.6e}, "
                    f"Change = {self._relative_change():.6e}"
                )
            if self._relative_change() < tol and it > 1:
                self._converged = True
                if verbose:
                    print(f"Converged after {self.iteration} iterations.")
                break
        return self.density

    def _relative_change(self) -> float:
        """Return relative change in compliance over last 5 iterations."""
        if len(self.compliance_history) < 3:
            return 1.0
        prev = self.compliance_history[-2]
        curr = self.compliance_history[-1]
        return abs((curr - prev) / (prev + 1e-12))

    def compliance(self, x: Optional[np.ndarray] = None) -> float:
        """Compute compliance for a given density distribution.

        Parameters
        ----------
        x : np.ndarray, optional
            Density field. If None, uses current density.

        Returns
        -------
        comp : float
            Compliance value.
        """
        if x is not None:
            prev = self.density
            self.density = x
        K = self._build_global_stiffness(self.density)
        K_red, f_red, free = self._apply_boundary_conditions(K)
        u_red = np.linalg.solve(K_red, f_red)
        comp = float(np.dot(f_red, u_red))
        if x is not None:
            self.density = prev
        return comp

    def plot_density(
        self,
        ax=None,
        cmap: str = "gray_r",
        show_colorbar: bool = True,
    ) -> None:
        """Plot the current density distribution.

        Uses matplotlib. If no axes is provided, creates a new figure.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to plot on.
        cmap : str, optional
            Colormap name (default 'gray_r').
        show_colorbar : bool, optional
            Whether to display a colour bar (default True).
        """
        import matplotlib.pyplot as plt

        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(8, 4))
        im = ax.imshow(self.density, cmap=cmap, interpolation="none")
        ax.set_xlabel("x (elements)")
        ax.set_ylabel("y (elements)")
        ax.set_title(f"Topology (iter={self.iteration}, volfrac={self.volfrac})")
        if show_colorbar:
            plt.colorbar(im, ax=ax)

    @property
    def volume_fraction(self) -> float:
        """Current volume fraction of the design."""
        return float(np.mean(self.density))

    @property
    def converged(self) -> bool:
        """Whether the solver has converged."""
        return self._converged

    def reset(self) -> None:
        """Reset to initial uniform density state."""
        self.density = self.volfrac * np.ones((self.nely, self.nelx), dtype=np.float64)
        self.compliance_history = []
        self.iteration = 0
        self._converged = False


# ---------------------------------------------------------------------------
#  Usage example (run as script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # MBB beam: 60 x 20 elements
    opt = TopOpt(nelx=60, nely=20, volfrac=0.5, penal=3.0, rmin=1.5)
    print("Solving topology optimisation (60x20, volfrac=0.5)...")
    x_opt = opt.solve(max_iter=100, verbose=True)
    print(f"Final compliance: {opt.compliance():.6f}")
    print(f"Volume fraction:  {opt.volume_fraction:.4f}")
    print(f"Converged:        {opt.converged}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    opt.plot_density(ax=axes[0])
    axes[1].plot(opt.compliance_history)
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("Compliance")
    axes[1].set_title("Convergence history")
    axes[1].grid(True)
    plt.tight_layout()
    plt.show()
