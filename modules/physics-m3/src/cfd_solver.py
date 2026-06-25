"""
cfd_solver.py — Computational Fluid Dynamics Solver Module
============================================================

Finite difference method (1D/2D) for incompressible Navier-Stokes,
lid-driven cavity benchmark, heat transfer coupling (energy equation),
and boundary layer resolution.

Classes
-------
CFDSolver : Core solver for incompressible flow and energy transport.

Dependencies
------------
numpy, scipy (sparse linear algebra)

Usage Example
-------------
>>> import numpy as np
>>> from modules.cfd_solver import CFDSolver
>>> x, y = CFDSolver.create_mesh(nx=32, ny=32, Lx=1.0, Ly=1.0)
>>> solver = CFDSolver(x, y, Re=100.0, Pr=0.71)
>>> u, v, p = solver.solve_navier_stokes(max_iter=500, tol=1e-6)
>>> T = solver.solve_energy(u, v)
>>> u_cavity, v_cavity, p_cavity = solver.lid_driven_cavity(Re=400)
>>> delta, u_bl = solver.boundary_layer(Re_x=1e5, x=1.0)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from scipy import sparse
from scipy.sparse.linalg import spsolve


class CFDSolver:
    """Finite difference solver for 2D incompressible Navier-Stokes.

    Uses a projection method on a staggered (MAC) grid with upwind
    advection. Pressure Poisson is solved with a sparse direct solver.

    Parameters
    ----------
    x : NDArray
        1D array of x-coordinates (cell centers).
    y : NDArray
        1D array of y-coordinates (cell centers).
    Re : float
        Reynolds number (default 100.0).
    Pr : float
        Prandtl number for energy equation (default 0.71).
    dt : float
        Time step size (default 0.001).
    rho : float
        Fluid density (default 1.0).
    """

    def __init__(
        self,
        x: NDArray[np.float64],
        y: NDArray[np.float64],
        Re: float = 100.0,
        Pr: float = 0.71,
        dt: float = 0.001,
        rho: float = 1.0,
    ) -> None:
        if len(x) < 2 or len(y) < 2:
            raise ValueError("Grid must have at least 2 points in each direction.")

        self.x = np.asarray(x, dtype=np.float64)
        self.y = np.asarray(y, dtype=np.float64)
        self.dx = self.x[1] - self.x[0]
        self.dy = self.y[1] - self.y[0]
        self.nx = len(self.x)
        self.ny = len(self.y)
        self.Re = float(Re)
        self.Pr = float(Pr)
        self.dt = float(dt)
        self.rho = float(rho)
        self.nu = 1.0 / self.Re
        self.alpha = self.nu / self.Pr

    @staticmethod
    def create_mesh(
        nx: int = 32, ny: int = 32, Lx: float = 1.0, Ly: float = 1.0
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Create a uniform Cartesian mesh.

        Parameters
        ----------
        nx, ny : int
            Number of cells in each direction.
        Lx, Ly : float
            Domain lengths.

        Returns
        -------
        tuple of NDArray
            (x, y) coordinate arrays at cell centers.
        """
        return (
            np.linspace(0.0, Lx, nx, dtype=np.float64),
            np.linspace(0.0, Ly, ny, dtype=np.float64),
        )

    # ------------------------------------------------------------------
    # Pressure Laplacian
    # ------------------------------------------------------------------

    def _build_laplacian(
        self, nx: int, ny: int
    ) -> sparse.csr_matrix:
        """Build the 5-point Laplacian for the pressure Poisson equation.

        Parameters
        ----------
        nx, ny : int
            Grid dimensions.

        Returns
        -------
        sparse.csr_matrix
            Laplacian operator.
        """
        N = nx * ny
        dx2_inv = 1.0 / self.dx**2
        dy2_inv = 1.0 / self.dy**2

        diag = np.full(N, -2.0 * dx2_inv - 2.0 * dy2_inv, dtype=np.float64)
        off_x = np.full(N - 1, dx2_inv, dtype=np.float64)
        off_y = np.full(N - nx, dy2_inv, dtype=np.float64)

        for i in range(1, nx):
            off_x[i * ny - 1] = 0.0

        return sparse.diags(
            [off_y, off_x, diag, off_x, off_y],
            [-nx, -1, 0, 1, nx],
            format="csr",
            dtype=np.float64,
        )

    # ------------------------------------------------------------------
    # Navier-Stokes solver (loop-based, staggered MAC grid)
    # ------------------------------------------------------------------

    def solve_navier_stokes(
        self,
        max_iter: int = 1000,
        tol: float = 1e-6,
        u_init: NDArray[np.float64] | None = None,
        v_init: NDArray[np.float64] | None = None,
        lid_velocity: float = 0.0,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Solve the 2D incompressible Navier-Stokes equations.

        Projection method (Chorin) on a staggered grid. Upwind for
        advection, central for diffusion.

        Parameters
        ----------
        max_iter : int
            Maximum time steps.
        tol : float
            Convergence tolerance on L2 velocity change.
        u_init, v_init : NDArray or None
            Initial velocity (zero if None).
        lid_velocity : float
            Top-wall tangential velocity (0 = no-slip everywhere).

        Returns
        -------
        tuple of NDArray
            (u, v, p).
        """
        nx, ny = self.nx, self.ny
        dx, dy = self.dx, self.dy
        dt = self.dt
        nu = self.nu

        # Staggered grid arrays
        # u: (nx+1) x (ny+2)  -- u at x_{i+1/2}, y_j
        # v: (nx+2) x (ny+2)  -- v at x_i, y_{j+1/2}
        # p: nx x ny           -- cell centers
        if u_init is not None:
            u = u_init.copy().astype(np.float64)
        else:
            u = np.zeros((nx + 1, ny + 2), dtype=np.float64)
        if v_init is not None:
            v = v_init.copy().astype(np.float64)
        else:
            v = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        p = np.zeros((nx, ny), dtype=np.float64)

        A = self._build_laplacian(nx, ny)

        for it in range(max_iter):
            u_old = u.copy()
            v_old = v.copy()

            # CFL-based time step
            u_max = max(float(np.max(np.abs(u))), 0.01)
            v_max = max(float(np.max(np.abs(v))), 0.01)
            cfl = min(dx / u_max, dy / v_max) * 0.5
            diff = 0.5 / (nu * (1.0 / dx**2 + 1.0 / dy**2) + 1e-30)
            local_dt = min(dt, cfl, diff)

            # --- u-momentum predictor ---
            # Loop over u-interior: i=1..nx-1, j=1..ny
            ut = np.zeros_like(u)
            for i in range(1, nx):
                for j in range(1, ny + 1):
                    # Diffusion (central)
                    visc = nu * (
                        (u[i + 1, j] - 2.0 * u[i, j] + u[i - 1, j]) / dx**2
                        + (u[i, j + 1] - 2.0 * u[i, j] + u[i, j - 1]) / dy**2
                    )

                    # x-advection (upwind)
                    ue = 0.5 * (u[i, j] + u[i + 1, j])
                    uw = 0.5 * (u[i, j] + u[i - 1, j])
                    flux_e = ue * (u[i, j] if ue > 0 else u[i + 1, j])
                    flux_w = uw * (u[i - 1, j] if uw > 0 else u[i, j])
                    adv_x = -(flux_e - flux_w) / dx

                    # y-advection (upwind, using v interpolated to u-cell corners)
                    # v at north-east and south-east corners of u-cell
                    vne = 0.5 * (v[i, j] + v[i + 1, j])
                    vnw = 0.5 * (v[i - 1, j] + v[i, j])
                    v_at_n = 0.5 * (vne + vnw)

                    vse = 0.5 * (v[i, j + 1] + v[i + 1, j + 1])
                    vsw = 0.5 * (v[i - 1, j + 1] + v[i, j + 1])
                    v_at_s = 0.5 * (vse + vsw)

                    flux_n = v_at_n * (u[i, j] if v_at_n > 0 else u[i, j + 1])
                    flux_s = v_at_s * (u[i, j - 1] if v_at_s > 0 else u[i, j])
                    adv_y = -(flux_n - flux_s) / dy

                    ut[i, j] = u[i, j] + local_dt * (adv_x + adv_y + visc)

            # --- v-momentum predictor ---
            # Loop over v-interior: i=1..nx, j=1..ny
            vt = np.zeros_like(v)
            for i in range(1, nx + 1):
                for j in range(1, ny + 1):
                    visc = nu * (
                        (v[i + 1, j] - 2.0 * v[i, j] + v[i - 1, j]) / dx**2
                        + (v[i, j + 1] - 2.0 * v[i, j] + v[i, j - 1]) / dy**2
                    )

                    # x-advection (upwind, using u interpolated to v-cell corners)
                    une = 0.5 * (u[i, j] + u[i, j + 1])
                    unw = 0.5 * (u[i - 1, j] + u[i - 1, j + 1])
                    use = 0.5 * (u[i, j - 1] + u[i, j])
                    usw = 0.5 * (u[i - 1, j - 1] + u[i - 1, j])
                    u_at_e = 0.5 * (une + use)
                    u_at_w = 0.5 * (unw + usw)

                    flux_e = u_at_e * (v[i, j] if u_at_e > 0 else v[i + 1, j])
                    flux_w = u_at_w * (v[i - 1, j] if u_at_w > 0 else v[i, j])
                    adv_x = -(flux_e - flux_w) / dx

                    # y-advection (upwind)
                    vn = 0.5 * (v[i, j] + v[i, j + 1])
                    vs = 0.5 * (v[i, j] + v[i, j - 1])
                    flux_n = vn * (v[i, j] if vn > 0 else v[i, j + 1])
                    flux_s = vs * (v[i, j - 1] if vs > 0 else v[i, j])
                    adv_y = -(flux_n - flux_s) / dy

                    vt[i, j] = v[i, j] + local_dt * (adv_x + adv_y + visc)

            # --- Pressure Poisson ---
            rhs = np.zeros(nx * ny, dtype=np.float64)
            for i in range(nx):
                for j in range(ny):
                    div = (
                        (ut[i + 1, j + 1] - ut[i, j + 1]) / dx
                        + (vt[i + 1, j + 1] - vt[i + 1, j]) / dy
                    )
                    rhs[j * nx + i] = div / local_dt

            p_flat = spsolve(A, rhs)
            p = p_flat.reshape((ny, nx), order="F").T

            # --- Projection ---
            for i in range(1, nx):
                for j in range(1, ny + 1):
                    u[i, j] = ut[i, j] - local_dt / dx * (p[i, j - 1] - p[i - 1, j - 1])
            for i in range(1, nx + 1):
                for j in range(1, ny):
                    v[i, j] = vt[i, j] - local_dt / dy * (p[i - 1, j] - p[i - 1, j - 1])

            # --- Boundary conditions ---
            u[0, :] = 0.0
            u[nx, :] = 0.0
            u[:, 0] = 0.0
            if lid_velocity != 0.0:
                u[:, ny + 1] = lid_velocity
                u[0, ny + 1] = 0.0
                u[nx, ny + 1] = 0.0
            else:
                u[:, ny + 1] = 0.0

            v[0, :] = 0.0
            v[nx + 1, :] = 0.0
            v[:, 0] = 0.0
            v[:, ny + 1] = 0.0

            # --- Convergence ---
            du = np.linalg.norm(u - u_old) / max(1.0, np.linalg.norm(u_old))
            dv = np.linalg.norm(v - v_old) / max(1.0, np.linalg.norm(v_old))
            if max(du, dv) < tol and it > 50:
                break

        return u, v, p

    # ------------------------------------------------------------------
    # Lid-driven cavity
    # ------------------------------------------------------------------

    def lid_driven_cavity(
        self,
        Re: float = 100.0,
        nx: int | None = None,
        ny: int | None = None,
        max_iter: int = 2000,
        tol: float = 1e-6,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Benchmark lid-driven cavity flow.

        Parameters
        ----------
        Re : float
            Reynolds number.
        nx, ny : int or None
            Grid resolution.
        max_iter, tol : int, float
            Solver parameters.

        Returns
        -------
        tuple of NDArray
            (u, v, p).
        """
        orig_Re = self.Re
        orig_nx, orig_ny = self.nx, self.ny
        self.Re = float(Re)
        self.nu = 1.0 / self.Re
        if nx is not None:
            self.nx = nx
        if ny is not None:
            self.ny = ny
        try:
            return self.solve_navier_stokes(max_iter=max_iter, tol=tol, lid_velocity=1.0)
        finally:
            self.Re = orig_Re
            self.nu = 1.0 / self.Re
            self.nx = orig_nx
            self.ny = orig_ny

    # ------------------------------------------------------------------
    # Energy equation
    # ------------------------------------------------------------------

    def solve_energy(
        self,
        u: NDArray[np.float64],
        v: NDArray[np.float64],
        T_wall: float = 1.0,
        max_iter: int = 5000,
        tol: float = 1e-6,
    ) -> NDArray[np.float64]:
        """Solve advection-diffusion energy equation.

        Parameters
        ----------
        u, v : NDArray
            Velocity field (staggered).
        T_wall : float
            Top wall temperature (Dirichlet).
        max_iter, tol : int, float
            Solver parameters.

        Returns
        -------
        NDArray
            Temperature field (nx x ny).
        """
        nx, ny = self.nx, self.ny
        dx, dy = self.dx, self.dy
        alpha = self.alpha

        T = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        T[:, -1] = float(T_wall)

        for it in range(max_iter):
            T_old = T.copy()
            for i in range(1, nx + 1):
                for j in range(1, ny + 1):
                    u_cc = 0.5 * (u[i - 1, j] + u[i, j])
                    v_cc = 0.5 * (v[i, j - 1] + v[i, j])

                    if u_cc > 0:
                        fx_e = u[i, j] * T[i, j]
                        fx_w = u[i - 1, j] * T[i - 1, j]
                    else:
                        fx_e = u[i, j] * T[i + 1, j]
                        fx_w = u[i - 1, j] * T[i, j]

                    if v_cc > 0:
                        fy_n = v[i, j] * T[i, j]
                        fy_s = v[i, j - 1] * T[i, j - 1]
                    else:
                        fy_n = v[i, j] * T[i, j + 1]
                        fy_s = v[i, j - 1] * T[i, j]

                    adv = -(fx_e - fx_w) / dx - (fy_n - fy_s) / dy
                    diff = alpha * (
                        (T[i + 1, j] - 2.0 * T[i, j] + T[i - 1, j]) / dx**2
                        + (T[i, j + 1] - 2.0 * T[i, j] + T[i, j - 1]) / dy**2
                    )
                    T[i, j] += self.dt * (adv + diff)

            # Adiabatic sides
            T[0, :] = T[1, :]
            T[-1, :] = T[-2, :]
            T[:, 0] = T[:, 1]

            change = np.linalg.norm(T - T_old) / max(1.0, np.linalg.norm(T_old))
            if change < tol:
                break

        return T[1:-1, 1:-1]

    # ------------------------------------------------------------------
    # Boundary layer
    # ------------------------------------------------------------------

    @staticmethod
    def boundary_layer(
        self=None,
        Re_x: float = 1e5,
        x: float = 1.0,
        n_points: int = 100,
    ) -> tuple[float, NDArray[np.float64]]:
        """Compute 1D boundary layer profile via Blasius similarity.

        Call signature: solver.boundary_layer(Re_x=..., x=..., n_points=...)

        Parameters
        ----------
        Re_x : float
            Reynolds number based on streamwise position.
        x : float
            Streamwise position.
        n_points : int
            Number of wall-normal points.

        Returns
        -------
        tuple of (float, NDArray)
            (delta_99, u_profile).
        """
        def blasius_ode(
            eta: float, yv: tuple[float, float, float]
        ) -> tuple[float, float, float]:
            f, fp, fpp = yv
            return (fp, fpp, -0.5 * f * fpp)

        sol = solve_ivp(
            blasius_ode,
            (0.0, 10.0),
            (0.0, 0.0, 0.33206),
            max_step=0.01,
            rtol=1e-8,
            atol=1e-10,
        )
        eta_vals = sol.t
        fp_vals = sol.y[1]

        idx = np.searchsorted(fp_vals, 0.99)
        eta_99 = eta_vals[idx] if idx < len(eta_vals) else 5.0
        delta = eta_99 * float(x) / np.sqrt(float(Re_x))

        eta_eval = np.linspace(0.0, 10.0, n_points)
        u_profile = np.interp(eta_eval, eta_vals, fp_vals)
        return delta, u_profile


# ------------------------------------------------------------------
# Usage example
# ------------------------------------------------------------------
if __name__ == "__main__":
    import doctest
    doctest.testmod()

    nx, ny = 32, 32
    x, y = CFDSolver.create_mesh(nx, ny, Lx=1.0, Ly=1.0)
    solver = CFDSolver(x, y, Re=100.0, Pr=0.71, dt=0.001)

    print("Solving Navier-Stokes (lid-driven cavity, Re=100)...")
    u, v, p = solver.lid_driven_cavity(Re=100.0, max_iter=200, tol=1e-4)
    print(f"  u range: [{u.min():.4f}, {u.max():.4f}]")
    print(f"  v range: [{v.min():.4f}, {v.max():.4f}]")

    print("Solving energy equation...")
    T = solver.solve_energy(u, v, T_wall=1.0, max_iter=200, tol=1e-4)
    print(f"  T range: [{T.min():.4f}, {T.max():.4f}]")

    print("Boundary layer...")
    delta, up = solver.boundary_layer(Re_x=1e5, x=1.0)
    print(f"  delta_99 = {delta:.6f}")
    print("CFDSolver module OK.")
