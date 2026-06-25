"""
TopOpt3D — Advanced 3D Topology Optimization Module
=====================================================

Implements the Solid Isotropic Material with Penalization (SIMP) method for
three-dimensional topology optimization, targeting minimum compliance subject
to a volume constraint. Extends the classic 2D SIMP formulation (Sigmund 2001,
Andreassen et al. 2011) to 3D hexahedral (hex8) elements with 2x2x2 Gauss
quadrature, mesh-independency filtering, multiple load case superposition,
and passive element support.

Features
--------
- 3D hex8 element with 24 DOFs per element, full 6x6 constitutive matrix
- Multiple load cases with compliance superposition
- Passive elements (fixed-density regions, e.g. for non-design domains)
- Mesh-independency cone-filter in 3D
- Optimality Criteria (OC) update with bisection on Lagrange multiplier
- Convergence detection on compliance change
- 3D slice plotting along any axis

References
----------
- Sigmund, O. (2001). A 99 line topology optimization code written in MATLAB.
  Structural and Multidisciplinary Optimization, 21(2), 120-127.
- Andreassen, E., et al. (2011). Efficient topology optimization in MATLAB
  using 88 lines of code. SMO, 43(1), 1-16.
- Bendsøe, M. P., & Sigmund, O. (2003). Topology Optimization: Theory, Methods,
  and Applications. Springer.
- Liu, K., & Tovar, A. (2014). An efficient 3D topology optimization code
  written in MATLAB. SMO, 50(6), 1175-1196.

Classes
-------
TopOpt3D
    Main class for 3D SIMP-based topology optimization.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.sparse import coo_matrix


# ---------------------------------------------------------------------------
#  Hex8 element helpers
# ---------------------------------------------------------------------------

_GAUSS_PTS = np.array([
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1],
], dtype=np.float64) / np.sqrt(3)


def _hex8_shape_derivatives(xi: float, eta: float, zeta: float) -> np.ndarray:
    """Shape function derivatives for an 8-node hexahedral element.

    Returns array dN_dxi of shape (3, 8): row 0 = dN/dxi,
    row 1 = dN/deta, row 2 = dN/dzeta.
    """
    xi = np.float64(xi)
    eta = np.float64(eta)
    zeta = np.float64(zeta)
    sx = np.array([-1, 1, 1, -1, -1, 1, 1, -1], dtype=np.float64)
    sy = np.array([-1, -1, 1, 1, -1, -1, 1, 1], dtype=np.float64)
    sz = np.array([-1, -1, -1, -1, 1, 1, 1, 1], dtype=np.float64)
    dN = np.zeros((3, 8), dtype=np.float64)
    for i in range(8):
        dN[0, i] = 0.125 * sx[i] * (1 + sy[i] * eta) * (1 + sz[i] * zeta)
        dN[1, i] = 0.125 * sy[i] * (1 + sx[i] * xi)  * (1 + sz[i] * zeta)
        dN[2, i] = 0.125 * sz[i] * (1 + sx[i] * xi)  * (1 + sy[i] * eta)
    return dN


def _make_hex8_stiffness(E: float = 1.0, nu: float = 0.3) -> np.ndarray:
    """Compute the 24x24 element stiffness matrix for a hex8 element.

    Uses 2x2x2 Gauss quadrature over the bi-unit cube [-1,1]^3.

    Parameters
    ----------
    E : float
        Young's modulus.
    nu : float
        Poisson ratio.

    Returns
    -------
    ke : np.ndarray, shape (24, 24)
        Element stiffness matrix (full, not sparse).
    """
    c = E / ((1 + nu) * (1 - 2 * nu))
    D = c * np.array([
        [1 - nu, nu,     nu,     0, 0, 0],
        [nu,     1 - nu, nu,     0, 0, 0],
        [nu,     nu,     1 - nu, 0, 0, 0],
        [0,      0,      0,      (1 - 2 * nu) / 2, 0, 0],
        [0,      0,      0,      0, (1 - 2 * nu) / 2, 0],
        [0,      0,      0,      0, 0, (1 - 2 * nu) / 2],
    ], dtype=np.float64)

    ke = np.zeros((24, 24), dtype=np.float64)
    for gp in range(8):
        xi, eta, zeta = _GAUSS_PTS[gp]
        dN = _hex8_shape_derivatives(xi, eta, zeta)

        B = np.zeros((6, 24), dtype=np.float64)
        for n in range(8):
            col = 3 * n
            B[0, col]     = dN[0, n]
            B[1, col + 1] = dN[1, n]
            B[2, col + 2] = dN[2, n]
            B[3, col + 1] = dN[2, n]
            B[3, col + 2] = dN[1, n]
            B[4, col]     = dN[2, n]
            B[4, col + 2] = dN[0, n]
            B[5, col]     = dN[1, n]
            B[5, col + 1] = dN[0, n]

        ke += B.T @ D @ B

    return ke


# ---------------------------------------------------------------------------
#  3D node / DOF indexing
# ---------------------------------------------------------------------------

def _hex8_node_indices(
    elx: int, ely: int, elz: int,
    nx: int, ny: int, nz: int,
) -> np.ndarray:
    """Return the 8 global node indices for hex element (elx, ely, elz).

    Standard hex8 node ordering:
        0: (0,0,0), 1: (1,0,0), 2: (1,1,0), 3: (0,1,0)
        4: (0,0,1), 5: (1,0,1), 6: (1,1,1), 7: (0,1,1)

    Parameters
    ----------
    elx, ely, elz : int
        Element indices (0-based).
    nx, ny, nz : int
        Number of elements in each direction.

    Returns
    -------
    nids : np.ndarray, shape (8,)
        Global node indices.
    """
    nnz = nz + 1      # nodes in z-direction
    nny = ny + 1      # nodes in y-direction
    stride_y = nnz            # one step in y = skip one row of z-nodes
    stride_x = nnz * nny      # one step in x = skip one yz-plane

    # Bottom layer (z = elz)
    b0 = elx * stride_x + ely * stride_y + elz          # (elx,   ely,   elz)
    b1 = b0 + stride_x                                   # (elx+1, ely,   elz)
    b3 = b0 + stride_y                                   # (elx,   ely+1, elz)
    b2 = b3 + stride_x                                   # (elx+1, ely+1, elz)
    # Top layer (z = elz + 1)
    t0 = b0 + 1                                          # (elx,   ely,   elz+1)
    t1 = b1 + 1                                          # (elx+1, ely,   elz+1)
    t3 = b3 + 1                                          # (elx,   ely+1, elz+1)
    t2 = b2 + 1                                          # (elx+1, ely+1, elz+1)

    return np.array([b0, b1, b2, b3, t0, t1, t2, t3], dtype=np.int32)


def _hex8_edof(nids: np.ndarray) -> np.ndarray:
    """Convert 8 node numbers to the 24 DOF indices of a hex element.

    Each node has 3 DOFs (ux, uy, uz).

    Parameters
    ----------
    nids : np.ndarray, shape (8,)
        Node numbers.

    Returns
    -------
    edof : np.ndarray, shape (24,)
        Global DOF indices.
    """
    edof = np.empty(24, dtype=np.int32)
    for i in range(8):
        edof[3 * i]     = 3 * nids[i]
        edof[3 * i + 1] = 3 * nids[i] + 1
        edof[3 * i + 2] = 3 * nids[i] + 2
    return edof


# ---------------------------------------------------------------------------
#  Main class
# ---------------------------------------------------------------------------

class TopOpt3D:
    """3D topology optimization using the SIMP method.

    Solves the minimum compliance problem:

        minimize   c(x) = sum_k f_k^T u_k
        subject to V(x) / V0 <= volfrac
                  x_min <= x_i <= 1

    where x is the density vector, f_k / u_k are the load / displacement
    vectors for load case k, V(x) is the material volume, and V0 is the
    design domain volume.

    Parameters
    ----------
    nx : int
        Number of elements in x-direction.
    ny : int
        Number of elements in y-direction.
    nz : int
        Number of elements in z-direction.
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
    density : np.ndarray, shape (nz, ny, nx)
        Current density field (z-index first to match numpy 3D indexing).
    compliance_history : list[float]
        Compliance values per iteration.
    iteration : int
        Current iteration counter.
    """

    def __init__(
        self,
        nx: int,
        ny: int,
        nz: int,
        volfrac: float,
        penal: float = 3.0,
        rmin: float = 1.5,
        E0: float = 1.0,
        Emin: float = 1e-9,
        nu: float = 0.3,
        x_min: float = 1e-3,
    ) -> None:
        # --- validate parameters ---
        if nx < 1 or ny < 1 or nz < 1:
            raise ValueError("nx, ny, nz must be >= 1")
        if volfrac <= 0 or volfrac > 1:
            raise ValueError("volfrac must be in (0, 1]")
        if penal < 1.0:
            raise ValueError("penal must be >= 1.0")
        if rmin < 0:
            raise ValueError("rmin must be >= 0")
        if E0 <= 0:
            raise ValueError("E0 must be positive")
        if Emin < 0:
            raise ValueError("Emin must be non-negative")
        if Emin >= E0:
            raise ValueError("Emin must be less than E0")
        if not (0 <= nu < 0.5):
            raise ValueError("nu must be in [0, 0.5)")

        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.volfrac = volfrac
        self.penal = penal
        self.rmin = rmin
        self.E0 = E0
        self.Emin = Emin
        self.nu = nu
        self.x_min = x_min

        # Density field: shape (nz, ny, nx) to match numpy 3D conventions
        self.density = volfrac * np.ones((nz, ny, nx), dtype=np.float64)

        # Compliance history, iteration counter, convergence flag
        self.compliance_history: list[float] = []
        self.iteration = 0
        self._converged = False

        # Pre-compute element stiffness matrix (unit E)
        self._ke = _make_hex8_stiffness(1.0, nu)

        # Total DOFs
        self._ndof = 3 * (nx + 1) * (ny + 1) * (nz + 1)

        # Load cases
        self._load_cases: list[dict] = []

        # Passive elements
        self._passive_mask: Optional[np.ndarray] = None
        self._passive_keep_value: float = 1.0

        # Default single-point load
        self._add_default_load()

    # ------------------------------------------------------------------
    #  Load case management
    # ------------------------------------------------------------------

    def _add_default_load(self) -> None:
        """Add a default single-point load (clamped left face, point load
        on right face centre, downward in y)."""
        ndof = self._ndof
        f = np.zeros(ndof, dtype=np.float64)
        node_x = self.nx
        node_y = self.ny // 2
        node_z = self.nz // 2
        nid = (
            node_x * (self.ny + 1) * (self.nz + 1)
            + node_y * (self.nz + 1)
            + node_z
        )
        f[3 * nid + 1] = -1.0  # downward in y
        self._load_cases.append({"name": "default", "f": f})

    def add_load_case(
        self,
        name: str,
        load_node_ijk: tuple[int, int, int],
        direction: tuple[float, float, float],
        magnitude: float,
    ) -> None:
        """Add a point load case.

        Parameters
        ----------
        name : str
            Load case name (must be unique).
        load_node_ijk : tuple of int
            Node (i, j, k) grid indices where i in [0, nx], j in [0, ny],
            k in [0, nz].
        direction : tuple of float
            Load direction vector (dx, dy, dz).
        magnitude : float
            Load magnitude.
        """
        i, j, k = load_node_ijk
        if not (0 <= i <= self.nx and 0 <= j <= self.ny and 0 <= k <= self.nz):
            raise ValueError(
                f"Node ({i}, {j}, {k}) out of bounds "
                f"[0, {self.nx}] x [0, {self.ny}] x [0, {self.nz}]"
            )
        for lc in self._load_cases:
            if lc["name"] == name:
                raise ValueError(f"Load case '{name}' already exists")

        nid = (
            i * (self.ny + 1) * (self.nz + 1)
            + j * (self.nz + 1)
            + k
        )
        dx, dy, dz = direction
        norm = np.sqrt(dx * dx + dy * dy + dz * dz)
        if norm == 0:
            raise ValueError("Direction vector must be non-zero")
        dx, dy, dz = dx / norm, dy / norm, dz / norm

        ndof = self._ndof
        f = np.zeros(ndof, dtype=np.float64)
        f[3 * nid]     = magnitude * dx
        f[3 * nid + 1] = magnitude * dy
        f[3 * nid + 2] = magnitude * dz
        self._load_cases.append({"name": name, "f": f})

    # ------------------------------------------------------------------
    #  Passive elements
    # ------------------------------------------------------------------

    def set_passive(
        self,
        region_mask: np.ndarray,
        keep_value: float = 1.0,
    ) -> None:
        """Set a region of passive (non-design) elements.

        Passive elements maintain their density at ``keep_value`` throughout
        the optimisation and are excluded from the OC update.

        Parameters
        ----------
        region_mask : np.ndarray, shape (nz, ny, nx), dtype bool
            True where elements should be passive.
        keep_value : float, optional
            Density value assigned to passive elements (default 1.0).
        """
        if region_mask.shape != (self.nz, self.ny, self.nx):
            raise ValueError(
                f"region_mask shape {region_mask.shape} does not match "
                f"density shape {(self.nz, self.ny, self.nx)}"
            )
        if not 0 < keep_value <= 1:
            raise ValueError("keep_value must be in (0, 1]")
        self._passive_mask = region_mask.astype(bool)
        self._passive_keep_value = float(keep_value)
        self.density[self._passive_mask] = self._passive_keep_value

    # ------------------------------------------------------------------
    #  System assembly
    # ------------------------------------------------------------------

    def _build_global_stiffness(self, x: np.ndarray) -> coo_matrix:
        """Assemble the global stiffness matrix in sparse COO format.

        Parameters
        ----------
        x : np.ndarray, shape (nz, ny, nx)
            Density field.

        Returns
        -------
        K : coo_matrix
            Global stiffness matrix.
        """
        nx, ny, nz = self.nx, self.ny, self.nz
        ndof = self._ndof
        ke_base = self._ke

        n_entries = 24 * 24 * nx * ny * nz
        i_vec = np.zeros(n_entries, dtype=np.int32)
        j_vec = np.zeros(n_entries, dtype=np.int32)
        s_vec = np.zeros(n_entries, dtype=np.float64)
        idx = 0

        for elx in range(nx):
            for ely in range(ny):
                for elz in range(nz):
                    nids = _hex8_node_indices(elx, ely, elz, nx, ny, nz)
                    edof = _hex8_edof(nids)
                    E_e = self.Emin + x[elz, ely, elx] ** self.penal * (self.E0 - self.Emin)
                    k_e = E_e * ke_base
                    for a in range(24):
                        for b in range(24):
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
        load_case_idx: int = 0,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Apply fixed DOFs and build reduced system for a load case.

        Clamps the left face (x = 0) — all DOFs on that face are fixed.

        Parameters
        ----------
        K : coo_matrix
            Global stiffness matrix.
        load_case_idx : int
            Index of the load case to use.

        Returns
        -------
        K_red : np.ndarray, shape (n_free, n_free)
            Reduced stiffness matrix (dense for direct solve).
        f_red : np.ndarray, shape (n_free,)
            Reduced force vector.
        free_dofs : np.ndarray
            Indices of free DOFs.
        """
        ndof = self._ndof
        n_face = (self.ny + 1) * (self.nz + 1)
        fixed = np.arange(0, 3 * n_face, dtype=np.int32)
        all_dofs = np.arange(ndof, dtype=np.int32)
        free = np.setdiff1d(all_dofs, fixed)

        f = self._load_cases[load_case_idx]["f"].copy()

        K_dense = K.toarray()
        K_red = K_dense[np.ix_(free, free)]
        f_red = f[free]
        return K_red, f_red, free

    # ------------------------------------------------------------------
    #  Filter
    # ------------------------------------------------------------------

    def _filter_sensitivities(
        self, x: np.ndarray, dc: np.ndarray
    ) -> np.ndarray:
        """Apply 3D mesh-independency cone-filter.

        Parameters
        ----------
        x : np.ndarray, shape (nz, ny, nx)
            Density field.
        dc : np.ndarray, shape (nz, ny, nx)
            Unfiltered sensitivities.

        Returns
        -------
        dcf : np.ndarray, shape (nz, ny, nx)
            Filtered sensitivities.
        """
        if self.rmin <= 0:
            return dc
        nx, ny, nz = self.nx, self.ny, self.nz
        rmin = self.rmin
        dcf = np.zeros_like(dc)
        ceil_rmin = int(np.ceil(rmin))

        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    total = 0.0
                    i_min = max(0, i - ceil_rmin)
                    i_max = min(nx, i + ceil_rmin + 1)
                    j_min = max(0, j - ceil_rmin)
                    j_max = min(ny, j + ceil_rmin + 1)
                    k_min = max(0, k - ceil_rmin)
                    k_max = min(nz, k + ceil_rmin + 1)
                    for ii in range(i_min, i_max):
                        for jj in range(j_min, j_max):
                            for kk in range(k_min, k_max):
                                r = np.sqrt(
                                    (i - ii) ** 2
                                    + (j - jj) ** 2
                                    + (k - kk) ** 2
                                )
                                if r <= rmin:
                                    w = rmin - r
                                    dcf[k, j, i] += w * x[kk, jj, ii] * dc[kk, jj, ii]
                                    total += w * x[kk, jj, ii]
                    if total > 0:
                        dcf[k, j, i] /= total
                    else:
                        dcf[k, j, i] = dc[k, j, i]
        return dcf

    # ------------------------------------------------------------------
    #  OC update
    # ------------------------------------------------------------------

    @staticmethod
    def _optimality_criteria_update(
        x: np.ndarray,
        dc: np.ndarray,
        volfrac: float,
        penal: float,
        x_min: float,
        move: float = 0.2,
        passive_mask: Optional[np.ndarray] = None,
        passive_value: float = 1.0,
    ) -> tuple[np.ndarray, float]:
        """Perform Optimality Criteria (OC) update.

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
        passive_mask : np.ndarray or None
            Boolean mask of passive elements (True = fixed).
        passive_value : float
            Density to assign to passive elements.

        Returns
        -------
        x_new : np.ndarray
            Updated densities.
        lam : float
            Lagrange multiplier (lower bound).
        """
        dv = 1.0

        if passive_mask is not None:
            n_design = int(np.sum(~passive_mask))
        else:
            n_design = x.size

        l1 = 0.0
        l2 = 1e9
        x_new = np.empty_like(x)

        for _ in range(100):
            lam = 0.5 * (l1 + l2)
            B = np.clip(-dc / (lam * dv + 1e-12), a_min=1e-12, a_max=None)
            x_new = x * np.sqrt(B)
            x_new = np.maximum(x - move, np.maximum(x_min, x_new))
            x_new = np.minimum(x + move, np.minimum(1.0, x_new))

            if passive_mask is not None:
                x_new[passive_mask] = passive_value

            if passive_mask is not None:
                vol_design = np.sum(x_new[~passive_mask])
            else:
                vol_design = np.sum(x_new)
            target_vol = volfrac * n_design
            if vol_design - target_vol > 0:
                l1 = lam
            else:
                l2 = lam
            if abs(vol_design - target_vol) / max(n_design, 1) < 1e-6:
                break

        return x_new, lam

    # ------------------------------------------------------------------
    #  Single step
    # ------------------------------------------------------------------

    def step(self) -> float:
        """Perform one optimisation iteration.

        When multiple load cases exist, compliance = sum of all load case
        compliances, and sensitivities are summed across load cases.

        Returns
        -------
        comp : float
            Total compliance at this iteration.
        """
        x = self.density.copy()

        K = self._build_global_stiffness(x)
        total_comp = 0.0
        dc = np.zeros((self.nz, self.ny, self.nx), dtype=np.float64)
        ke_base = self._ke

        for lc_idx in range(len(self._load_cases)):
            K_red, f_red, free = self._apply_boundary_conditions(K, lc_idx)
            u_red = np.linalg.solve(K_red, f_red)
            u_full = np.zeros(self._ndof, dtype=np.float64)
            u_full[free] = u_red

            comp = float(np.dot(f_red, u_red))
            total_comp += comp

            for elx in range(self.nx):
                for ely in range(self.ny):
                    for elz in range(self.nz):
                        nids = _hex8_node_indices(elx, ely, elz, self.nx, self.ny, self.nz)
                        edof = _hex8_edof(nids)
                        u_e = u_full[edof]
                        E_e = self.Emin + x[elz, ely, elx] ** self.penal * (self.E0 - self.Emin)
                        dE_dx = self.penal * x[elz, ely, elx] ** (self.penal - 1) * (self.E0 - self.Emin)
                        dc[elz, ely, elx] -= dE_dx * np.dot(u_e, ke_base @ u_e) / (E_e + 1e-12)

        dc = self._filter_sensitivities(x, dc)

        self.density, _ = self._optimality_criteria_update(
            x, dc, self.volfrac, self.penal, self.x_min,
            passive_mask=self._passive_mask,
            passive_value=self._passive_keep_value,
        )

        self.compliance_history.append(total_comp)
        self.iteration += 1
        return total_comp

    # ------------------------------------------------------------------
    #  Solve loop
    # ------------------------------------------------------------------

    def solve(
        self,
        max_iter: int = 200,
        tol: float = 1e-4,
        verbose: bool = False,
    ) -> np.ndarray:
        """Run the full optimisation loop to convergence.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations (default 200).
        tol : float, optional
            Relative convergence tolerance on compliance change
            (default 1e-4).
        verbose : bool, optional
            Print iteration info when True (default False).

        Returns
        -------
        density : np.ndarray, shape (nz, ny, nx)
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
        """Relative change in compliance over the last iteration."""
        if len(self.compliance_history) < 3:
            return 1.0
        prev = self.compliance_history[-2]
        curr = self.compliance_history[-1]
        return float(abs((curr - prev) / (prev + 1e-12)))

    # ------------------------------------------------------------------
    #  Compliance evaluation
    # ------------------------------------------------------------------

    def compliance(self, x: Optional[np.ndarray] = None) -> float:
        """Compute the total compliance for a given density distribution.

        Parameters
        ----------
        x : np.ndarray, optional
            Density field of shape (nz, ny, nx).  If None, uses the current
            density.

        Returns
        -------
        comp : float
            Total compliance (sum over all load cases).
        """
        if x is not None:
            prev = self.density
            self.density = x
        else:
            prev = None

        K = self._build_global_stiffness(self.density)
        total = 0.0
        for lc_idx in range(len(self._load_cases)):
            K_red, f_red, free = self._apply_boundary_conditions(K, lc_idx)
            u_red = np.linalg.solve(K_red, f_red)
            total += float(np.dot(f_red, u_red))

        if prev is not None:
            self.density = prev
        return total

    # ------------------------------------------------------------------
    #  Properties
    # ------------------------------------------------------------------

    @property
    def volume_fraction(self) -> float:
        """Current volume fraction of the design."""
        return float(np.mean(self.density))

    @property
    def converged(self) -> bool:
        """Whether the solver has converged."""
        return self._converged

    # ------------------------------------------------------------------
    #  Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset to the initial uniform density state.

        Clears compliance history, iteration counter, and convergence flag.
        Passive element masks and load cases are preserved.
        """
        self.density = self.volfrac * np.ones((self.nz, self.ny, self.nx), dtype=np.float64)
        self.compliance_history = []
        self.iteration = 0
        self._converged = False
        if self._passive_mask is not None:
            self.density[self._passive_mask] = self._passive_keep_value

    # ------------------------------------------------------------------
    #  Plotting
    # ------------------------------------------------------------------

    def plot_slice(
        self,
        axis: str = "z",
        index: Optional[int] = None,
        ax=None,
        cmap: str = "gray_r",
        show_colorbar: bool = True,
    ) -> None:
        """Plot a 2D slice of the current density field.

        Parameters
        ----------
        axis : {'x', 'y', 'z'}
            Axis normal to the slice plane.
        index : int, optional
            Slice index.  Defaults to the mid-plane if None.
        ax : matplotlib.axes.Axes, optional
            Axes to plot on.  Creates a new figure if None.
        cmap : str, optional
            Matplotlib colormap name (default 'gray_r').
        show_colorbar : bool, optional
            Show colour bar (default True).
        """
        import matplotlib.pyplot as plt

        if axis == "x":
            idx = index if index is not None else self.nx // 2
            data = self.density[:, :, idx]
            xlabel, ylabel = "y", "z"
        elif axis == "y":
            idx = index if index is not None else self.ny // 2
            data = self.density[:, idx, :]
            xlabel, ylabel = "x", "z"
        elif axis == "z":
            idx = index if index is not None else self.nz // 2
            data = self.density[idx, :, :]
            xlabel, ylabel = "x", "y"
        else:
            raise ValueError(f"axis must be 'x', 'y', or 'z', got {axis!r}")

        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(8, 6))
        im = ax.imshow(data, cmap=cmap, interpolation="none", origin="lower")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(
            f"TopOpt3D slice ({axis}={idx}), "
            f"iter={self.iteration}, volfrac={self.volfrac:.3f}"
        )
        if show_colorbar:
            plt.colorbar(im, ax=ax)


# ---------------------------------------------------------------------------
#  Usage example
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    opt = TopOpt3D(nx=16, ny=8, nz=6, volfrac=0.3, penal=3.0, rmin=2.0)
    print("Solving 3D topology optimisation (16x8x6, volfrac=0.3)...")
    x_opt = opt.solve(max_iter=60, verbose=True)
    print(f"Final compliance: {opt.compliance():.6f}")
    print(f"Volume fraction:  {opt.volume_fraction:.4f}")
    print(f"Converged:        {opt.converged}")
    print(f"Density shape:    {x_opt.shape}")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    opt.plot_slice(axis="x", index=8, ax=axes[0])
    opt.plot_slice(axis="y", index=4, ax=axes[1])
    opt.plot_slice(axis="z", index=3, ax=axes[2])
    plt.tight_layout()
    plt.show()
