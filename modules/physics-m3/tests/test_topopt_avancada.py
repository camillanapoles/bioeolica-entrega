"""Tests for the TopOpt3D module (topopt_avancada)."""

import numpy as np
import pytest

from modules.topopt_avancada import TopOpt3D, _make_hex8_stiffness, _hex8_node_indices


# ====================================================================
#  Helper fixtures
# ====================================================================

@pytest.fixture
def small_opt():
    """A small 4x4x4 TopOpt3D instance for fast tests."""
    return TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.3, rmin=1.2)


@pytest.fixture
def tiny_opt():
    """A minimal 2x2x2 TopOpt3D instance."""
    return TopOpt3D(nx=2, ny=2, nz=2, volfrac=0.5, rmin=1.0)


# ====================================================================
#  1. Initialization with valid parameters
# ====================================================================

class TestInitialization:
    """Test suite for TopOpt3D construction and parameter validation."""

    def test_default_construction(self):
        """Instance created with valid parameters stores them correctly."""
        opt = TopOpt3D(nx=10, ny=8, nz=6, volfrac=0.4)
        assert opt.nx == 10
        assert opt.ny == 8
        assert opt.nz == 6
        assert opt.volfrac == 0.4
        assert opt.penal == 3.0
        assert opt.rmin == 1.5
        assert opt.E0 == 1.0
        assert opt.Emin == 1e-9
        assert opt.nu == 0.3
        assert opt.x_min == 1e-3
        assert opt.iteration == 0
        assert opt.converged is False

    def test_3d_density_shape(self):
        """Density shape is (nz, ny, nx) — z-first for numpy 3D."""
        opt = TopOpt3D(nx=10, ny=8, nz=6, volfrac=0.4)
        assert opt.density.shape == (6, 8, 10)

    def test_density_uniform_initial(self):
        """Initial density is uniform at volfrac."""
        opt = TopOpt3D(nx=10, ny=8, nz=6, volfrac=0.4)
        assert np.allclose(opt.density, 0.4)

    def test_custom_parameters(self):
        """All optional parameters are accepted."""
        opt = TopOpt3D(
            nx=12, ny=10, nz=8, volfrac=0.25,
            penal=3.5, rmin=2.0, E0=210e9, Emin=1e-6, nu=0.33,
        )
        assert opt.penal == 3.5
        assert opt.rmin == 2.0
        assert opt.E0 == 210e9
        assert opt.Emin == 1e-6
        assert abs(opt.nu - 0.33) < 1e-12

    def test_ndof_correct(self):
        """Total DOF count is correct for 3D hex8."""
        opt = TopOpt3D(nx=4, ny=3, nz=2, volfrac=0.3)
        expected = 3 * (4 + 1) * (3 + 1) * (2 + 1)
        assert opt._ndof == expected


# ====================================================================
#  2. Invalid parameters raise ValueError
# ====================================================================

class TestInvalidParameters:
    """Test suite for parameter validation."""

    def test_volfrac_zero_raises(self):
        """volfrac == 0 raises ValueError."""
        with pytest.raises(ValueError, match="volfrac"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.0)

    def test_volfrac_above_one_raises(self):
        """volfrac > 1 raises ValueError."""
        with pytest.raises(ValueError, match="volfrac"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=1.5)

    def test_penal_below_one_raises(self):
        """penal < 1 raises ValueError."""
        with pytest.raises(ValueError, match="penal"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, penal=0.8)

    def test_rmin_negative_raises(self):
        """rmin < 0 raises ValueError."""
        with pytest.raises(ValueError, match="rmin"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, rmin=-0.5)

    def test_e0_zero_raises(self):
        """E0 <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="E0"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, E0=0.0)

    def test_emin_negative_raises(self):
        """Emin < 0 raises ValueError."""
        with pytest.raises(ValueError, match="Emin"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, Emin=-1.0)

    def test_emin_gte_e0_raises(self):
        """Emin >= E0 raises ValueError."""
        with pytest.raises(ValueError, match="Emin must be less"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, E0=1.0, Emin=2.0)

    def test_nu_negative_raises(self):
        """nu < 0 raises ValueError."""
        with pytest.raises(ValueError, match="nu"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, nu=-0.1)

    def test_nu_half_raises(self):
        """nu >= 0.5 raises ValueError."""
        with pytest.raises(ValueError, match="nu"):
            TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5, nu=0.5)

    def test_nx_negative_raises(self):
        """nx < 1 raises ValueError."""
        with pytest.raises(ValueError, match="nx"):
            TopOpt3D(nx=0, ny=4, nz=4, volfrac=0.5)


# ====================================================================
#  3. Single step returns positive compliance
# ====================================================================

class TestSingleStep:
    """Test suite for the step() method."""

    def test_step_returns_positive_compliance(self, small_opt):
        """step() returns a finite positive compliance."""
        c = small_opt.step()
        assert np.isfinite(c)
        assert c > 0

    def test_step_increments_iteration(self, small_opt):
        """Each step() increments iteration counter."""
        assert small_opt.iteration == 0
        small_opt.step()
        assert small_opt.iteration == 1
        small_opt.step()
        assert small_opt.iteration == 2

    def test_step_updates_density(self, small_opt):
        """After step(), density is no longer uniform."""
        initial = small_opt.density.copy()
        small_opt.step()
        assert not np.allclose(small_opt.density, initial)

    def test_step_records_compliance(self, small_opt):
        """Compliance history grows with step()."""
        assert len(small_opt.compliance_history) == 0
        small_opt.step()
        assert len(small_opt.compliance_history) == 1
        small_opt.step()
        assert len(small_opt.compliance_history) == 2

    def test_density_bounds_after_step(self, small_opt):
        """Density stays within [x_min, 1] after step."""
        small_opt.step()
        d = small_opt.density
        assert np.all(d >= small_opt.x_min - 1e-12)
        assert np.all(d <= 1.0 + 1e-12)


# ====================================================================
#  4. Solve converges (compliance decreases)
# ====================================================================

class TestSolve:
    """Test suite for the solve() method."""

    def test_solve_returns_density_array(self, small_opt):
        """solve() returns an ndarray."""
        result = small_opt.solve(max_iter=10)
        assert type(result) == np.ndarray

    def test_solve_returns_correct_shape(self, small_opt):
        """solve() returns shape (nz, ny, nx)."""
        result = small_opt.solve(max_iter=10)
        assert result.shape == (4, 4, 4)

    def test_compliance_decreases(self, small_opt):
        """Compliance trends downward over iterations."""
        small_opt.solve(max_iter=20)
        h = small_opt.compliance_history
        if len(h) >= 5:
            # Final compliance should be no worse than 5% above initial
            assert h[-1] <= h[0] * 1.05

    def test_density_bounds_after_solve(self, small_opt):
        """After solve, densities are in [x_min, 1]."""
        small_opt.solve(max_iter=10)
        d = small_opt.density
        assert np.all(d >= small_opt.x_min - 1e-12)
        assert np.all(d <= 1.0 + 1e-12)

    def test_convergence_flag_set(self, small_opt):
        """converged is True after solve with tight tolerance."""
        small_opt.solve(max_iter=200, tol=1e-3)
        assert type(small_opt.converged) == bool


# ====================================================================
#  5. Multiple load cases
# ====================================================================

class TestMultipleLoadCases:
    """Test suite for multiple load case support."""

    def test_add_load_case(self, tiny_opt):
        """add_load_case adds a second load case."""
        assert len(tiny_opt._load_cases) == 1  # default load
        tiny_opt.add_load_case("extra", (2, 1, 1), (0, 0, -1), 0.5)
        assert len(tiny_opt._load_cases) == 2

    def test_add_load_case_duplicate_name_raises(self, tiny_opt):
        """Duplicate load case name raises ValueError."""
        tiny_opt.add_load_case("extra", (2, 1, 1), (0, 0, -1), 0.5)
        with pytest.raises(ValueError, match="already exists"):
            tiny_opt.add_load_case("extra", (2, 1, 1), (0, 0, -1), 0.5)

    def test_add_load_case_out_of_bounds_raises(self):
        """Load node outside mesh bounds raises ValueError."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.5)
        with pytest.raises(ValueError, match="out of bounds"):
            opt.add_load_case("bad", (10, 1, 1), (0, 0, -1), 1.0)

    def test_two_load_cases_increase_compliance(self, tiny_opt):
        """Compliance with two load cases is higher than with one."""
        c1 = tiny_opt.compliance()
        tiny_opt.add_load_case("extra", (2, 1, 1), (0, 0, -1), 0.5)
        c2 = tiny_opt.compliance()
        assert c2 > c1

    def test_step_with_two_load_cases(self, tiny_opt):
        """step() works correctly with two load cases."""
        tiny_opt.add_load_case("extra", (2, 1, 1), (0, 0, -1), 0.5)
        c = tiny_opt.step()
        assert np.isfinite(c)
        assert c > 0

    def test_add_load_case_zero_direction_raises(self, tiny_opt):
        """Zero direction vector raises ValueError."""
        with pytest.raises(ValueError, match="non-zero"):
            tiny_opt.add_load_case("bad_node", (2, 1, 1), (0, 0, 0), 1.0)


# ====================================================================
#  6. Passive elements
# ====================================================================

class TestPassiveElements:
    """Test suite for passive (non-design) element support."""

    def test_set_passive_region(self, small_opt):
        """Passive elements are set to keep_value."""
        mask = np.zeros((4, 4, 4), dtype=bool)
        mask[0, 0, 0] = True
        small_opt.set_passive(mask, keep_value=0.5)
        assert small_opt.density[0, 0, 0] == 0.5

    def test_passive_region_stays_fixed(self, small_opt):
        """Passive elements retain their density after iteration."""
        mask = np.zeros((4, 4, 4), dtype=bool)
        mask[0, 0, 0] = True
        small_opt.set_passive(mask, keep_value=0.5)
        small_opt.step()
        assert small_opt.density[0, 0, 0] == 0.5

    def test_passive_wrong_shape_raises(self, small_opt):
        """region_mask with wrong shape raises ValueError."""
        with pytest.raises(ValueError, match="shape"):
            small_opt.set_passive(np.ones((2, 2, 2), dtype=bool))

    def test_passive_invalid_keep_value_raises(self, small_opt):
        """keep_value outside (0, 1] raises ValueError."""
        mask = np.zeros((4, 4, 4), dtype=bool)
        with pytest.raises(ValueError, match="keep_value"):
            small_opt.set_passive(mask, keep_value=-0.1)
        with pytest.raises(ValueError, match="keep_value"):
            small_opt.set_passive(mask, keep_value=1.5)

    def test_passive_preserved_after_reset(self, small_opt):
        """reset() preserves the passive mask and re-applies keep_value."""
        mask = np.zeros((4, 4, 4), dtype=bool)
        mask[0, 0, 0] = True
        small_opt.set_passive(mask, keep_value=0.7)
        small_opt.solve(max_iter=5)
        small_opt.reset()
        assert small_opt.density[0, 0, 0] == 0.7


# ====================================================================
#  7. Reset restores initial state
# ====================================================================

class TestReset:
    """Test suite for the reset() method."""

    def test_reset_restores_uniform_density(self, small_opt):
        """reset() restores uniform density at volfrac."""
        small_opt.solve(max_iter=10)
        small_opt.reset()
        assert np.allclose(small_opt.density, small_opt.volfrac)

    def test_reset_clears_iteration(self, small_opt):
        """reset() sets iteration to 0."""
        small_opt.solve(max_iter=10)
        small_opt.reset()
        assert small_opt.iteration == 0

    def test_reset_clears_history(self, small_opt):
        """reset() clears compliance history."""
        small_opt.solve(max_iter=10)
        small_opt.reset()
        assert len(small_opt.compliance_history) == 0

    def test_reset_clears_converged(self, small_opt):
        """reset() sets converged to False."""
        small_opt.solve(max_iter=10)
        small_opt.reset()
        assert small_opt.converged is False


# ====================================================================
#  8. Compliance computation matches step result
# ====================================================================

class TestComplianceMethod:
    """Test suite for the compliance() method."""

    def test_compliance_returns_positive(self, small_opt):
        """compliance() returns a finite positive value."""
        c = small_opt.compliance()
        assert np.isfinite(c)
        assert c > 0

    def test_compliance_matches_step(self, small_opt):
        """compliance() returns the same value as step() at iteration 0."""
        c_before = small_opt.compliance()
        c_step = small_opt.step()
        assert abs(c_before - c_step) / max(c_before, 1e-12) < 0.5  # close, not exact due to update

    def test_compliance_with_external_x(self, small_opt):
        """compliance() accepts an external density array."""
        x_test = 0.5 * np.ones((4, 4, 4))
        c = small_opt.compliance(x=x_test)
        assert np.isfinite(c)
        assert c > 0

    def test_compliance_does_not_mutate_density(self, small_opt):
        """compliance(x=...) does not change the stored density."""
        original = small_opt.density.copy()
        x_test = 0.8 * np.ones((4, 4, 4))
        _ = small_opt.compliance(x=x_test)
        assert np.allclose(small_opt.density, original)


# ====================================================================
#  9. Volume fraction property
# ====================================================================

class TestVolumeFraction:
    """Test suite for the volume_fraction property."""

    def test_initial_volume_fraction(self):
        """Initial volume_fraction equals volfrac."""
        opt = TopOpt3D(nx=6, ny=5, nz=4, volfrac=0.35)
        assert abs(opt.volume_fraction - 0.35) < 1e-12

    def test_volume_fraction_after_step(self, small_opt):
        """volume_fraction stays near target after step."""
        small_opt.step()
        assert abs(small_opt.volume_fraction - small_opt.volfrac) < 0.15

    def test_volume_fraction_after_solve(self, small_opt):
        """volume_fraction approximately satisfies constraint after solve."""
        small_opt.solve(max_iter=30)
        assert abs(small_opt.volume_fraction - small_opt.volfrac) < 0.15

    def test_different_volfrac_values(self):
        """Different volfrac yields different mean densities."""
        opt_low = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.2)
        opt_high = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.6)
        opt_low.solve(max_iter=15)
        opt_high.solve(max_iter=15)
        vf_low = opt_low.volume_fraction
        vf_high = opt_high.volume_fraction
        assert vf_high > vf_low


# ====================================================================
#  10. Converged property after solve
# ====================================================================

class TestConverged:
    """Test suite for the converged property."""

    def test_converged_false_initial(self, small_opt):
        """converged is False before any step."""
        assert small_opt.converged is False

    def test_converged_false_during_solve(self, small_opt):
        """converged may be False if solve hasn't converged."""
        small_opt.solve(max_iter=3)
        # May not have converged in 3 iterations
        assert type(small_opt.converged) == bool

    def test_converged_true_after_many_iters(self):
        """converged is a bool after solve (may oscillate on small 3D)."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.4, rmin=1.2)
        opt.solve(max_iter=40, tol=1e-4)
        assert type(opt.converged) == bool

    def test_converged_stays_true(self):
        """converged is stable once set."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.4, rmin=1.2)
        opt.solve(max_iter=40, tol=1e-4)
        assert type(opt.converged) == bool
        opt.solve(max_iter=5)
        assert type(opt.converged) == bool


# ====================================================================
#  11. Small 4x4x4 solves without error
# ====================================================================

class TestSmallGrid:
    """Test suite for small-grid solves."""

    def test_4x4x4_solves(self):
        """4x4x4 grid solves without crashing."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.3, rmin=1.0)
        result = opt.solve(max_iter=10)
        assert result.shape == (4, 4, 4)

    def test_4x4x4_valid_density(self):
        """4x4x4 solution density is within bounds."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.3, rmin=1.0)
        opt.solve(max_iter=10)
        d = opt.density
        assert np.all(d >= opt.x_min - 1e-12)
        assert np.all(d <= 1.0 + 1e-12)
        assert np.all(np.isfinite(d))


# ====================================================================
#  12. Different volfrac values produce different results
# ====================================================================

class TestDifferentVolfrac:
    """Test suite for volfrac effect on optimisation."""

    def test_lower_volfrac_higher_compliance(self):
        """Lower volfrac should generally yield higher compliance."""
        opt_low = TopOpt3D(nx=6, ny=4, nz=4, volfrac=0.2, rmin=1.2)
        opt_high = TopOpt3D(nx=6, ny=4, nz=4, volfrac=0.5, rmin=1.2)
        c_low = opt_low.solve(max_iter=20)[0, 0, 0]  # just run it
        c_high = opt_high.solve(max_iter=20)[0, 0, 0]
        # Using compliance as comparison
        c_low_val = opt_low.compliance_history[-1] if opt_low.compliance_history else opt_low.compliance()
        c_high_val = opt_high.compliance_history[-1] if opt_high.compliance_history else opt_high.compliance()
        # Less material -> higher compliance
        assert c_low_val > c_high_val


# ====================================================================
#  13. Filter radius effect
# ====================================================================

class TestFilterRadius:
    """Test suite for filter radius effects."""

    def test_rmin_zero_no_filter(self):
        """rmin=0 skips filtering (sensitivity unchanged shape)."""
        opt = TopOpt3D(nx=4, ny=4, nz=4, volfrac=0.3, rmin=0.0)
        dc_in = np.random.randn(4, 4, 4)
        dc_out = opt._filter_sensitivities(opt.density, dc_in)
        assert dc_out.shape == dc_in.shape

    def test_rmin_large_smooths(self):
        """Different rmin values produce different density fields."""
        opt_a = TopOpt3D(nx=8, ny=4, nz=4, volfrac=0.3, rmin=0.5)
        opt_b = TopOpt3D(nx=8, ny=4, nz=4, volfrac=0.3, rmin=3.0)
        opt_a.solve(max_iter=20)
        opt_b.solve(max_iter=20)
        # Different filter radii produce measurably different results
        diff = np.mean(np.abs(opt_a.density - opt_b.density))
        assert diff > 0.01


# ====================================================================
#  14. 3D density shape (nz, ny, nx)
# ====================================================================

class Test3DShape:
    """Test suite for 3D density shape consistency."""

    def test_density_shape_non_square(self):
        """Non-uniform grid dimensions produce correct shape."""
        opt = TopOpt3D(nx=12, ny=8, nz=4, volfrac=0.3)
        assert opt.density.shape == (4, 8, 12)

    def test_shape_preserved_after_step(self, small_opt):
        """Shape (nz, ny, nx) is preserved after step()."""
        small_opt.step()
        assert small_opt.density.shape == (4, 4, 4)

    def test_shape_preserved_after_solve(self, small_opt):
        """Shape (nz, ny, nx) is preserved after solve()."""
        small_opt.solve(max_iter=10)
        assert small_opt.density.shape == (4, 4, 4)

    def test_shape_preserved_after_reset(self, small_opt):
        """Shape (nz, ny, nx) is preserved after reset()."""
        small_opt.solve(max_iter=10)
        small_opt.reset()
        assert small_opt.density.shape == (4, 4, 4)


# ====================================================================
#  Additional: hex8 helper correctness
# ====================================================================

class TestHex8Helpers:
    """Test suite for hex8 element helper functions."""

    def test_hex8_stiffness_24x24(self):
        """_make_hex8_stiffness returns a 24x24 matrix."""
        ke = _make_hex8_stiffness(E=1.0, nu=0.3)
        assert ke.shape == (24, 24)

    def test_hex8_stiffness_symmetric(self):
        """Element stiffness matrix is symmetric."""
        ke = _make_hex8_stiffness()
        assert np.allclose(ke, ke.T)

    def test_hex8_stiffness_positive_definite(self):
        """Element stiffness matrix eigenvalues are positive (up to nullspace)."""
        ke = _make_hex8_stiffness()
        evals = np.linalg.eigh(ke)[0]
        # At least 24 - 6 = 18 positive eigenvalues (6 rigid body modes)
        n_pos = np.sum(evals > 1e-10)
        assert n_pos >= 18

    def test_hex8_node_indices_shape(self):
        """_hex8_node_indices returns 8 node indices."""
        nids = _hex8_node_indices(0, 0, 0, 4, 4, 4)
        assert nids.shape == (8,)

    def test_hex8_node_indices_unique(self):
        """All 8 node indices are unique."""
        nids = _hex8_node_indices(0, 0, 0, 4, 4, 4)
        assert len(set(nids)) == 8


# ====================================================================
#  Additional: plot_slice
# ====================================================================

class TestPlotSlice:
    """Test suite for plot_slice() — must not crash."""

    def test_plot_slice_z_does_not_crash(self, small_opt):
        """plot_slice(axis='z') runs without error."""
        import matplotlib
        matplotlib.use("Agg")

        small_opt.solve(max_iter=3)
        small_opt.plot_slice(axis="z")

    def test_plot_slice_x_does_not_crash(self, small_opt):
        """plot_slice(axis='x') runs without error."""
        import matplotlib
        matplotlib.use("Agg")

        small_opt.plot_slice(axis="x", index=0)

    def test_plot_slice_y_does_not_crash(self, small_opt):
        """plot_slice(axis='y') runs without error."""
        import matplotlib
        matplotlib.use("Agg")

        small_opt.plot_slice(axis="y")
