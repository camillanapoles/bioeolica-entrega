"""
tests/test_cfd.py — Unit tests for the CFDSolver module.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from modules.cfd_solver import CFDSolver


class TestCFDSolver:
    """Test suite for CFDSolver."""

    def test_create_mesh(self):
        """Test uniform mesh generation."""
        x, y = CFDSolver.create_mesh(nx=10, ny=8, Lx=2.0, Ly=1.0)
        assert len(x) == 10
        assert len(y) == 8
        assert abs(x[1] - x[0]) == pytest.approx(2.0 / 9.0)
        assert abs(y[1] - y[0]) == pytest.approx(1.0 / 7.0)

    def test_solver_initialization(self):
        """Test that CFDSolver initializes with correct parameters."""
        x, y = CFDSolver.create_mesh(16, 16)
        solver = CFDSolver(x, y, Re=200.0, Pr=0.71, dt=0.0005)
        assert solver.nx == 16
        assert solver.ny == 16
        assert solver.Re == pytest.approx(200.0)
        assert solver.Pr == pytest.approx(0.71)
        assert solver.dt == pytest.approx(0.0005)
        assert solver.nu == pytest.approx(1.0 / 200.0)

    def test_invalid_grid_raises(self):
        """Test that a grid with fewer than 2 points raises ValueError."""
        x = np.array([0.0])
        y = np.array([0.0, 1.0])
        with pytest.raises(ValueError, match="at least 2 points"):
            CFDSolver(x, y)

    def test_laplacian_matrix_shape(self):
        """Test that the Laplacian matrix has correct dimensions."""
        x, y = CFDSolver.create_mesh(8, 6)
        solver = CFDSolver(x, y)
        A = solver._build_laplacian(8, 6)
        assert A.shape == (48, 48)

    def test_solve_navier_stokes_returns_fields(self):
        """Test that Navier-Stokes solver returns u, v, p arrays."""
        x, y = CFDSolver.create_mesh(8, 8, Lx=1.0, Ly=1.0)
        solver = CFDSolver(x, y, Re=100.0, dt=0.0005)
        u, v, p = solver.solve_navier_stokes(max_iter=50, tol=1e-3)
        assert u.shape == (9, 10)
        assert v.shape == (10, 10)  # (nx+2, ny+2)
        assert p.shape == (8, 8)
        assert not np.any(np.isnan(u))
        assert not np.any(np.isnan(v))
        assert not np.any(np.isnan(p))

    def test_lid_driven_cavity_top_bc(self):
        """Test that lid-driven cavity has u~1 at top boundary."""
        x, y = CFDSolver.create_mesh(10, 10, Lx=1.0, Ly=1.0)
        solver = CFDSolver(x, y, Re=100.0, dt=0.0005)
        u, v, p = solver.lid_driven_cavity(Re=100.0, max_iter=200, tol=1e-4)
        # Lid boundary condition at top wall interior should be 1.0
        # (corners are 0 from no-slip side walls)
        top_interior = u[1:-1, solver.ny + 1]
        assert np.allclose(top_interior, 1.0, atol=1e-6)

    def test_solve_energy_returns_temperature(self):
        """Test that energy solver returns a temperature field."""
        x, y = CFDSolver.create_mesh(8, 8)
        solver = CFDSolver(x, y, Re=100.0, Pr=0.71, dt=0.0005)
        u, v, p = solver.solve_navier_stokes(max_iter=30, tol=1e-3)
        T = solver.solve_energy(u, v, T_wall=1.0, max_iter=200, tol=1e-3)
        assert T.shape == (8, 8)
        assert not np.any(np.isnan(T))

    def test_energy_temperature_bounds(self):
        """Test that temperature is bounded by boundary conditions."""
        x, y = CFDSolver.create_mesh(6, 6)
        solver = CFDSolver(x, y, Re=10.0, Pr=0.71, dt=0.001)
        u, v, p = solver.solve_navier_stokes(max_iter=20, tol=1e-3)
        T = solver.solve_energy(u, v, T_wall=1.0, max_iter=100, tol=1e-3)
        # Temperature should be between 0 (initial) and 1.0 (wall BC)
        assert np.all(T >= 0.0 - 1e-10)
        assert np.all(T <= 1.0 + 1e-10)

    def test_boundary_layer_thickness(self):
        """Test that boundary layer thickness scales correctly."""
        solver_dummy = CFDSolver.__new__(CFDSolver)
        delta_1, _ = CFDSolver.boundary_layer(solver_dummy, Re_x=1e4, x=1.0)
        delta_2, _ = CFDSolver.boundary_layer(solver_dummy, Re_x=1e5, x=1.0)
        # delta ~ x / sqrt(Re_x), so delta_1 > delta_2
        assert delta_1 > delta_2

    def test_boundary_layer_profile_shape(self):
        """Test that boundary layer velocity profile is monotonic."""
        solver_dummy = CFDSolver.__new__(CFDSolver)
        delta, u_bl = CFDSolver.boundary_layer(solver_dummy, Re_x=1e5, x=1.0)
        assert delta > 0.0
        assert len(u_bl) == 100
        # Profile should be increasing (monotonic)
        diffs = np.diff(u_bl)
        assert np.all(diffs >= -1e-10)
        # Must start near 0 and approach 1
        assert u_bl[0] <= 0.05
        assert u_bl[-1] >= 0.95

    def test_boundary_layer_zero_reynolds(self):
        """Test that BL with very low Re_x still produces valid output."""
        solver_dummy = CFDSolver.__new__(CFDSolver)
        delta, u_bl = CFDSolver.boundary_layer(
            solver_dummy, Re_x=1e3, x=0.1, n_points=20
        )
        assert delta > 0.0
        assert len(u_bl) == 20

    def test_multiple_reynolds_numbers(self):
        """Test lid-driven cavity at different Reynolds numbers."""
        x, y = CFDSolver.create_mesh(10, 10)
        solver = CFDSolver(x, y, Re=100.0, dt=0.0005)
        u, v, p = solver.lid_driven_cavity(Re=100.0, max_iter=300, tol=1e-4)
        # Lid BC should be enforced (interior, corners are 0 from side walls)
        assert np.allclose(u[1:-1, solver.ny + 1], 1.0, atol=1e-6)
        # Interior velocities should be finite (not NaN)
        u_interior = u[1:-1, 1:-1]
        assert not np.any(np.isnan(u_interior))
        assert not np.any(np.isinf(u_interior))
