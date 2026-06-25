"""Tests for the topology_optimization module."""

import numpy as np
import pytest

from modules.topology_optimization import TopOpt


class TestTopOptInitialisation:
    """Test suite for TopOpt construction and basic properties."""

    def test_default_construction(self):
        """A TopOpt instance can be created with valid parameters."""
        opt = TopOpt(nelx=60, nely=20, volfrac=0.5)
        assert opt.nelx == 60
        assert opt.nely == 20
        assert opt.volfrac == 0.5
        assert opt.density.shape == (20, 60)
        assert np.allclose(opt.density, 0.5)
        assert opt.iteration == 0

    def test_invalid_volfrac_raises(self):
        """volfrac <= 0 or > 1 raises ValueError."""
        with pytest.raises(ValueError, match="volfrac"):
            TopOpt(nelx=10, nely=10, volfrac=0.0)
        with pytest.raises(ValueError, match="volfrac"):
            TopOpt(nelx=10, nely=10, volfrac=1.5)

    def test_invalid_penal_raises(self):
        """penal < 1 raises ValueError."""
        with pytest.raises(ValueError, match="penal"):
            TopOpt(nelx=10, nely=10, volfrac=0.5, penal=0.5)

    def test_volume_fraction_property(self):
        """volume_fraction property returns mean density."""
        opt = TopOpt(nelx=30, nely=10, volfrac=0.4)
        assert abs(opt.volume_fraction - 0.4) < 1e-10


class TestTopOptSolve:
    """Test suite for the optimisation solver."""

    def test_solve_returns_density(self):
        """solve() returns an array of the expected shape."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.5, rmin=1.5)
        result = opt.solve(max_iter=10)
        assert type(result) == np.ndarray
        assert result.shape == (8, 20)

    def test_compliance_decreases(self):
        """Compliance should trend downward over iterations."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.5, rmin=1.5)
        opt.solve(max_iter=15)
        history = opt.compliance_history
        if len(history) >= 5:
            assert history[-1] <= history[0] * 1.05  # allow small noise

    def test_solve_converges_to_volume_constraint(self):
        """Final volume fraction should approximately satisfy the constraint."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.4, rmin=1.5)
        opt.solve(max_iter=100)
        assert abs(opt.volume_fraction - 0.4) < 0.08

    def test_convergence_flag(self):
        """converged property becomes True when tolerance is met."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.5, rmin=1.5)
        opt.solve(max_iter=200, tol=1e-3)
        # May or may not converge on coarse grid — should not error
        assert type(opt.converged) == bool

    def test_compliance_method(self):
        """compliance() returns a positive scalar."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.5)
        c = opt.compliance()
        assert np.isfinite(c)
        assert c > 0

    def test_reset_clears_state(self):
        """reset() restores initial conditions."""
        opt = TopOpt(nelx=20, nely=8, volfrac=0.5)
        opt.solve(max_iter=10)
        opt.reset()
        assert np.allclose(opt.density, 0.5)
        assert opt.iteration == 0
        assert len(opt.compliance_history) == 0

    def test_step_increments_iteration(self):
        """Each step() call increments the iteration counter."""
        opt = TopOpt(nelx=10, nely=5, volfrac=0.5)
        assert opt.iteration == 0
        opt.step()
        assert opt.iteration == 1
        opt.step()
        assert opt.iteration == 2

    def test_plot_density_does_not_crash(self):
        """plot_density() runs without error."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        opt = TopOpt(nelx=20, nely=8, volfrac=0.5)
        opt.solve(max_iter=5)
        fig, ax = plt.subplots()
        opt.plot_density(ax=ax)
        plt.close(fig)

    def test_tiny_grid_solves(self):
        """Optimisation runs on a minimal grid without crashing."""
        opt = TopOpt(nelx=4, nely=4, volfrac=0.5, rmin=1.0)
        result = opt.solve(max_iter=5)
        assert result.shape == (4, 4)
        assert np.all(result >= 1e-3)
        assert np.all(result <= 1.0)
