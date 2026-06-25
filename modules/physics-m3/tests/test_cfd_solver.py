import numpy as np; import pytest
from modules.cfd_solver import CFDSolver

def test_create_mesh():
    x, y = CFDSolver.create_mesh(nx=8, ny=8)
    assert len(x) == 8 and len(y) == 8

def test_solver_init():
    x, y = CFDSolver.create_mesh(nx=4, ny=4)
    s = CFDSolver(x, y, Re=100.0)
    assert s.Re == 100.0

def test_navier_stokes():
    x, y = CFDSolver.create_mesh(nx=4, ny=4)
    s = CFDSolver(x, y, Re=100.0)
    u, v, p = s.solve_navier_stokes(max_iter=10, tol=1e-2)
    assert all(a.size > 0 for a in (u, v, p))

def test_boundary_layer():
    x, y = CFDSolver.create_mesh(nx=4, ny=4)
    s = CFDSolver(x, y, Re=100.0)
    d, ubl = s.boundary_layer(Re_x=1e5, x=1.0)
    assert d > 0 and len(ubl) > 0
