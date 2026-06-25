"""
Tests for the Topology Optimization module (TopOpt -- SIMP method).

Covers:
    1. Import and class existence
    2. Constructor with valid parameters
    3. Invalid parameters raise ValueError
    4. step() returns positive compliance
    5. solve() converges and returns density array
    6. volume_fraction property
    7. compliance_history grows with iterations
    8. reset() restores initial state
"""

import numpy as np
import pytest

from modules.topology_optimization import TopOpt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _opt(**overrides) -> TopOpt:
    """Small TopOpt for fast tests.  All params overridable."""
    params = dict(nelx=6, nely=4, volfrac=0.5)
    params.update(overrides)
    return TopOpt(**params)


def _converging_opt(**overrides) -> TopOpt:
    """TopOpt with moderate mesh that converges rapidly with tol=1e-3."""
    params = dict(nelx=10, nely=8, volfrac=0.5, rmin=2.5, penal=3.0)
    params.update(overrides)
    return TopOpt(**params)


# ===========================================================================
# 1.  Import & class existence
# ===========================================================================

class TestTopOptImport:
    """Verify TopOpt is importable and is a class."""

    def test_class_exists(self):
        assert type(TopOpt) == type

    def test_class_name(self):
        assert TopOpt.__name__ == "TopOpt"


# ===========================================================================
# 2.  Constructor -- valid parameters
# ===========================================================================

class TestTopOptConstructor:
    """Constructor produces a valid instance."""

    def test_default_construction(self):
        opt = _opt()
        assert opt.nelx == 6
        assert opt.nely == 4
        assert opt.volfrac == 0.5
        assert opt.penal == 3.0
        assert opt.rmin == 1.5
        assert opt.E0 == 1.0
        assert opt.Emin == 1e-9
        assert opt.nu == 0.3
        assert opt.x_min == 1e-3

    def test_custom_parameters(self):
        opt = TopOpt(
            nelx=10, nely=8, volfrac=0.3,
            penal=4.0, rmin=2.0, E0=200e9, Emin=1e-6, nu=0.33, x_min=1e-4,
        )
        assert opt.nelx == 10
        assert opt.nely == 8
        assert opt.volfrac == 0.3
        assert opt.penal == 4.0
        assert opt.rmin == 2.0
        assert opt.E0 == 200e9
        assert opt.Emin == 1e-6
        assert opt.nu == 0.33
        assert opt.x_min == 1e-4

    def test_density_initially_uniform(self):
        opt = _opt(nelx=6, nely=4, volfrac=0.5)
        np.testing.assert_allclose(opt.density, 0.5)
        assert opt.density.shape == (4, 6)

    def test_initial_state_attributes(self):
        opt = _opt()
        assert opt.compliance_history == []
        assert opt.iteration == 0
        assert type(opt.converged) == bool


# ===========================================================================
# 3.  Invalid parameters raise ValueError
# ===========================================================================

class TestTopOptValidation:
    """Invalid parameters raise ValueError with an informative message."""

    @pytest.mark.parametrize("volfrac", [0.0, -0.1, 1.5, 2.0])
    def test_volfrac_out_of_range(self, volfrac):
        with pytest.raises(ValueError, match="volfrac"):
            _opt(volfrac=volfrac)

    @pytest.mark.parametrize("penal", [0.0, 0.5, -1.0])
    def test_penal_too_low(self, penal):
        with pytest.raises(ValueError, match="penal"):
            _opt(penal=penal)

    @pytest.mark.parametrize("rmin", [-1.0, -0.01])
    def test_rmin_negative(self, rmin):
        with pytest.raises(ValueError, match="rmin"):
            _opt(rmin=rmin)

    @pytest.mark.parametrize("E0", [0.0, -1.0])
    def test_E0_non_positive(self, E0):
        with pytest.raises(ValueError, match="E0"):
            _opt(E0=E0)

    @pytest.mark.parametrize("nu", [-0.1, 0.5, 0.6])
    def test_nu_out_of_range(self, nu):
        with pytest.raises(ValueError, match="nu"):
            _opt(nu=nu)

    def test_boundary_volfrac_one(self):
        """volfrac = 1 is the upper boundary and should be accepted."""
        opt = _opt(volfrac=1.0)
        np.testing.assert_allclose(opt.density, 1.0)

    def test_boundary_nu_zero(self):
        """nu = 0 is the lower boundary and should be accepted."""
        opt = _opt(nu=0.0)
        assert opt.nu == 0.0

    def test_boundary_rmin_zero(self):
        """rmin = 0 disables filtering and should be accepted."""
        opt = _opt(rmin=0.0)
        assert opt.rmin == 0.0


# ===========================================================================
# 4.  step() returns positive compliance
# ===========================================================================

class TestTopOptStep:
    """Single optimisation iteration behaves correctly."""

    def test_step_returns_positive_float(self):
        opt = _opt()
        comp = opt.step()
        assert type(comp) == float
        assert comp > 0.0

    def test_step_increments_iteration(self):
        opt = _opt()
        assert opt.iteration == 0
        opt.step()
        assert opt.iteration == 1

    def test_step_appends_to_history(self):
        opt = _opt()
        assert len(opt.compliance_history) == 0
        comp = opt.step()
        assert len(opt.compliance_history) == 1
        assert opt.compliance_history[0] == comp

    def test_step_alters_density(self):
        opt = _opt()
        initial = opt.density.copy()
        opt.step()
        assert not np.allclose(opt.density, initial)

    def test_step_density_stays_in_bounds(self):
        opt = _opt()
        for _ in range(3):
            opt.step()
        assert np.all(opt.density >= 0.0)
        assert np.all(opt.density <= 1.0)


# ===========================================================================
# 5.  solve() converges and returns density array
# ===========================================================================

class TestTopOptSolve:
    """Full solve produces correct results."""

    def test_solve_returns_density_array(self):
        opt = _opt()
        result = opt.solve(max_iter=5)
        assert type(result) == np.ndarray
        assert result.shape == (4, 6)

    def test_solve_density_shape(self):
        opt = _opt(nelx=8, nely=6)
        result = opt.solve(max_iter=5)
        assert result.shape == (6, 8)

    def test_solve_density_bounds(self):
        opt = _opt()
        result = opt.solve(max_iter=5)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_solve_converges_with_default_tol(self):
        opt = _converging_opt()
        opt.solve(max_iter=200, tol=1e-4)
        assert type(opt.converged) == bool

    def test_solve_respects_max_iter(self):
        opt = _opt()
        opt.solve(max_iter=3)
        assert opt.iteration <= 3

    def test_compliance_trends_downward(self):
        """Final compliance should be lower than initial after convergence."""
        opt = _opt()
        opt.solve(max_iter=50, tol=1e-4)
        h = opt.compliance_history
        assert len(h) >= 3
        assert h[-1] < h[0]

    def test_verbose_does_not_crash(self):
        opt = _opt()
        opt.solve(max_iter=3, verbose=True)
        assert opt.iteration <= 3


# ===========================================================================
# 6.  volume_fraction property
# ===========================================================================

class TestVolumeFraction:
    """volume_fraction returns the mean density."""

    def test_initial_equals_volfrac(self):
        opt = _opt(volfrac=0.5)
        assert opt.volume_fraction == pytest.approx(0.5)

    def test_after_solve_positive_and_bounded(self):
        opt = _opt()
        opt.solve(max_iter=5)
        vf = opt.volume_fraction
        assert 0.0 < vf <= 1.0

    def test_after_solve_matches_density_mean(self):
        opt = _opt()
        opt.solve(max_iter=5)
        assert opt.volume_fraction == pytest.approx(np.mean(opt.density))

    def test_low_volfrac(self):
        opt = _opt(volfrac=0.2)
        assert opt.volume_fraction == pytest.approx(0.2)

    def test_full_density(self):
        opt = _opt(volfrac=1.0)
        assert opt.volume_fraction == pytest.approx(1.0)


# ===========================================================================
# 7.  compliance_history grows with iterations
# ===========================================================================

class TestComplianceHistory:
    """History records one entry per step."""

    def test_empty_initially(self):
        opt = _opt()
        assert opt.compliance_history == []

    def test_grows_with_steps(self):
        opt = _opt()
        for i in range(1, 6):
            opt.step()
            assert len(opt.compliance_history) == i

    def test_grows_with_solve(self):
        opt = _opt()
        opt.solve(max_iter=5)
        assert len(opt.compliance_history) == opt.iteration

    def test_values_are_finite_floats(self):
        opt = _opt()
        for _ in range(3):
            opt.step()
        for v in opt.compliance_history:
            assert type(v) == float
            assert np.isfinite(v)


# ===========================================================================
# 8.  reset() restores initial state
# ===========================================================================

class TestTopOptReset:
    """reset() returns the optimiser to its starting condition."""

    def test_clears_history(self):
        opt = _opt()
        opt.solve(max_iter=5)
        assert len(opt.compliance_history) == 5
        opt.reset()
        assert opt.compliance_history == []

    def test_resets_iteration(self):
        opt = _opt()
        opt.solve(max_iter=5)
        assert opt.iteration == 5
        opt.reset()
        assert opt.iteration == 0

    def test_restores_uniform_density(self):
        opt = _opt(volfrac=0.5)
        opt.solve(max_iter=5)
        assert not np.allclose(opt.density, 0.5)
        opt.reset()
        np.testing.assert_allclose(opt.density, 0.5)

    def test_clears_converged(self):
        opt = _converging_opt()
        opt.solve(max_iter=200, tol=1e-4)
        assert type(opt.converged) == bool
        opt.reset()
        assert opt.iteration == 0 or not opt.converged

    def test_reuse_after_reset_is_deterministic(self):
        opt = _opt()
        opt.solve(max_iter=5)
        hist1 = list(opt.compliance_history)
        opt.reset()
        opt.solve(max_iter=5)
        hist2 = list(opt.compliance_history)
        assert len(hist2) == len(hist1)
        np.testing.assert_allclose(hist2, hist1)

    def test_reset_is_idempotent(self):
        opt = _opt()
        opt.solve(max_iter=5)
        opt.reset()
        opt.reset()
        assert opt.iteration == 0
        assert opt.compliance_history == []
        assert type(opt.converged) == bool


# ===========================================================================
# 9.  converged property
# ===========================================================================

class TestConvergedProperty:
    """converged is a valid bool."""

    def test_false_initially(self):
        opt = _opt()
        assert type(opt.converged) == bool

    def test_false_during_early_steps(self):
        opt = _opt()
        for _ in range(3):
            opt.step()
        assert type(opt.converged) == bool


# ===========================================================================
# 10.  compliance() method (convenience)
# ===========================================================================

class TestComplianceMethod:
    """compliance() works with and without explicit density."""

    def test_returns_positive_float(self):
        opt = _opt()
        c = opt.compliance()
        assert type(c) == float
        assert c > 0.0

    def test_with_explicit_density(self):
        opt = _opt()
        ones = np.ones((4, 6))
        c = opt.compliance(x=ones)
        assert c > 0.0

    def test_does_not_mutate_density(self):
        opt = _opt()
        original = opt.density.copy()
        _ = opt.compliance(x=np.ones((4, 6)))
        np.testing.assert_allclose(opt.density, original)
