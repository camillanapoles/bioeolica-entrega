"""
FEM component for topology optimization using SIMP (Solid Isotropic Material with Penalization).

Uses an analytical stiffness matrix for a 2D plane-stress rectangular domain,
discretized with bilinear quadrilateral (Q4) elements. The density field
parameterizes the element-wise Young's modulus via SIMP penalization.

References:
    Sigmund, O. (2001). "A 99 line topology optimization code written in Matlab."
    Structural and Multidisciplinary Optimization, 21(2), 120-127.
    Andreassen, E. et al. (2011). "Efficient topology optimization in MATLAB
    using 88 lines of code." Structural and Multidisciplinary Optimization, 43(1), 1-16.
"""

from __future__ import annotations

import numpy as np
import openmdao.api as om


def _element_stiffness(E: float, nu: float) -> np.ndarray:
    """
    Return the 8×8 element stiffness matrix for a bilinear Q4 plane-stress element
    on a unit square domain, computed via 2×2 Gaussian quadrature.

    Shape functions (η,ξ ∈ [-1,1]):
        N1 = 0.25*(1-ξ)*(1-η),  N2 = 0.25*(1+ξ)*(1-η)
        N3 = 0.25*(1+ξ)*(1+η),  N4 = 0.25*(1-ξ)*(1+η)

    DOF ordering: [u1, v1, u2, v2, u3, v3, u4, v4]
    """
    # 2×2 Gauss points
    gauss_pts = [-1.0 / np.sqrt(3), 1.0 / np.sqrt(3)]
    weights = [1.0, 1.0]

    # Constitutive matrix D (plane stress)
    D = E / (1 - nu**2) * np.array([
        [1.0, nu, 0.0],
        [nu, 1.0, 0.0],
        [0.0, 0.0, (1.0 - nu) / 2.0],
    ])

    KE = np.zeros((8, 8))

    # Shape function derivatives w.r.t. (ξ, η):
    # dNi/dξ = ±0.25*(1±η),  dNi/dη = ±0.25*(1±ξ)
    # For each node i, (sign_xi_i, sign_eta_i):
    # Node 1: (-, -), Node 2: (+, -), Node 3: (+, +), Node 4: (-, +)
    signs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for xi in gauss_pts:
        for eta in gauss_pts:
            # Jacobian for unit square: |J| = 0.25 (for element of size 1×1 in physical space
            # mapped from [-1,1]×[-1,1] in parent space)
            detJ = 0.25

            # B matrix: 3 rows × 8 columns
            B = np.zeros((3, 8))
            for i, (sx, sy) in enumerate(signs):
                # dNi/dξ = sx * 0.25 * (1 + sy*eta)
                # dNi/dη = sy * 0.25 * (1 + sx*xi)
                dN_dxi = sx * 0.25 * (1.0 + sy * eta)
                dN_deta = sy * 0.25 * (1.0 + sx * xi)

                # For unit square: inv(J) = [[2,0],[0,2]] since J = [[0.5,0],[0,0.5]]
                # dNi/dx = 2 * dN_dxi,  dNi/dy = 2 * dN_deta
                dN_dx = 2.0 * dN_dxi
                dN_dy = 2.0 * dN_deta

                # B matrix columns for node i (DOFs 2i, 2i+1)
                B[0, 2*i] = dN_dx      # ε_xx = du/dx
                B[1, 2*i+1] = dN_dy     # ε_yy = dv/dy
                B[2, 2*i] = dN_dy      # γ_xy = du/dy + dv/dx
                B[2, 2*i+1] = dN_dx

            KE += B.T @ D @ B * detJ

    return KE


def _node_ids(nelx: int, nely: int) -> np.ndarray:
    """Return (nelx*nely, 4) array of global node indices per element."""
    nodenrs = np.arange(0, (1 + nelx) * (1 + nely)).reshape(1 + nely, 1 + nelx)
    elem_nodes = np.zeros((nely, nelx, 4), dtype=np.int32)
    for ey in range(nely):
        for ex in range(nelx):
            n0 = nodenrs[ey, ex]
            elem_nodes[ey, ex] = [n0, n0 + 1, n0 + nelx + 2, n0 + nelx + 1]
    return elem_nodes.reshape(-1, 4)


def _build_index_map(nelx: int, nely: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Build sparse triplet indices (rows, cols) and ndof for the global stiffness matrix."""
    ndof = 2 * (nelx + 1) * (nely + 1)
    node_ids = _node_ids(nelx, nely)
    nelem = nelx * nely
    rows = np.zeros((nelem, 8), dtype=np.int32)
    cols = np.zeros((nelem, 8), dtype=np.int32)
    for i in range(4):
        rows[:, 2 * i] = 2 * node_ids[:, i]
        rows[:, 2 * i + 1] = 2 * node_ids[:, i] + 1
        cols[:, 2 * i] = 2 * node_ids[:, i]
        cols[:, 2 * i + 1] = 2 * node_ids[:, i] + 1
    return rows.ravel(), cols.ravel(), ndof


class SIMPFemComponent(om.ExplicitComponent):
    """
    OpenMDAO ExplicitComponent for 2D SIMP topology optimization FEM.

    Solves K(d) * u = f using a density-filtered SIMP penalization.
    Inputs:
        density_field : (nelx*nely,) array of element densities [0, 1]
        load_vector   : (ndof,) array of nodal forces
    Outputs:
        displacements : (ndof,) array of nodal displacements
        compliance    : scalar compliance = f^T * u
    """

    def __init__(self, nelx: int = 80, nely: int = 40, E0: float = 1.0,
                 Emin: float = 1e-9, penal: float = 3.0, nu: float = 0.3):
        super().__init__()
        self.nelx = nelx
        self.nely = nely
        self.E0 = E0
        self.Emin = Emin
        self.penal = penal
        self.nu = nu
        self.nelem = nelx * nely
        self._rows, self._cols, self.ndof = _build_index_map(nelx, nely)
        self._KE = _element_stiffness(E0, nu)

    def setup(self):
        self.add_input("density_field", shape=(self.nelem,),
                       units=None, tags=["topopt"])
        self.add_input("load_vector", shape=(self.ndof,),
                       units=None, tags=["topopt"])
        self.add_output("displacements", shape=(self.ndof,),
                        units=None, tags=["topopt"])
        self.add_output("compliance", shape=(1,),
                        units=None, tags=["topopt"])
        # Declare partials — we use fd for the complex topology coupling
        self.declare_partials("*", "*", method="fd", form="central", step=1e-6)

    def compute(self, inputs, outputs):
        x = np.clip(inputs["density_field"], self.Emin, 1.0)
        f = inputs["load_vector"]
        nelem = self.nelem
        ndof = self.ndof

        # SIMP penalization of element stiffness
        E_elem = self.Emin + (self.E0 - self.Emin) * (x ** self.penal)

        # Expand DOF indices: each element has 8 DOFs → 8×8 = 64 contributions
        rows_8 = self._rows.reshape(-1, 8)   # (nelem, 8)
        cols_8 = self._cols.reshape(-1, 8)   # (nelem, 8)
        # rows_64[e, i, j] = rows_8[e, i]  (row i repeated for j=0..7)
        r = np.repeat(rows_8[:, :, np.newaxis], 8, axis=2)
        # cols_64[e, i, j] = cols_8[e, j]  (col j repeated for i=0..7)
        c = np.repeat(cols_8[:, np.newaxis, :], 8, axis=1)

        KE_flat = self._KE.ravel()  # (64,)
        data = np.outer(E_elem, KE_flat).ravel()  # (nelem * 64,)

        K_coo = (data, (r.ravel(), c.ravel()))
        from scipy.sparse import coo_matrix
        K = coo_matrix(K_coo, shape=(ndof, ndof)).tocsc()

        # Solve K * u = f
        from scipy.sparse.linalg import spsolve
        # Fixed DOFs: bottom-left corner (x,y) + bottom-right corner (y)
        n_horiz = self.nelx + 1
        n_vert = self.nely + 1
        # Node indices: node = col + row * n_horiz
        # DOF index = 2 * node
        bottom_left_x = 0
        bottom_left_y = 1
        bottom_right_y = 2 * (n_horiz - 1) + 1
        fixed = np.array([bottom_left_x, bottom_left_y, bottom_right_y], dtype=np.int32)
        free = np.setdiff1d(np.arange(ndof), fixed, assume_unique=True)

        K_red = K[free, :][:, free]
        f_red = f[free]
        u_red = spsolve(K_red, f_red)

        u = np.zeros(ndof)
        u[free] = u_red

        outputs["displacements"] = u
        outputs["compliance"] = np.dot(f, u)
