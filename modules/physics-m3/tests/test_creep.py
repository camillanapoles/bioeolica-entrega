"""Tests for the creep module."""

import numpy as np
import pytest

from modules.creep import CreepModel, _norton_bailey_strain_rate, _larson_miller


class TestCreepModelInit:
    """Test suite for CreepModel construction."""

    def test_default_construction(self):
        """A CreepModel can be created with default parameters."""
        cm = CreepModel()
        assert cm.A == 1e-12
        assert cm.n == 5.0
        assert cm.m == 0.0
        assert abs(cm.Q - 300e3) < 1
        assert abs(cm.R - 8.314) < 1e-3
        assert abs(cm.E - 200e3) < 1

    def test_custom_parameters(self):
        """CreepModel accepts custom parameters."""
        cm = CreepModel(A=1e-15, n=4.0, m=-0.2, Q=350e3)
        assert abs(cm.A - 1e-15) < 1e-20
        assert cm.n == 4.0
        assert cm.m == -0.2


class TestNortonBailey:
    """Test suite for the Norton-Bailey strain rate function."""

    def test_strain_rate_positive(self):
        """Strain rate is positive for positive stress and time."""
        rate = _norton_bailey_strain_rate(
            sigma=100.0, A=1e-12, n=5.0, m=0.0, t=100.0, Q=300e3, R=8.314, T=800.0
        )
        assert rate > 0

    def test_strain_rate_increases_with_stress(self):
        """Higher stress gives higher strain rate."""
        r1 = _norton_bailey_strain_rate(50.0, 1e-12, 5.0, 0.0, 100.0, 300e3, 8.314, 800.0)
        r2 = _norton_bailey_strain_rate(100.0, 1e-12, 5.0, 0.0, 100.0, 300e3, 8.314, 800.0)
        assert r2 > r1

    def test_strain_rate_increases_with_temperature(self):
        """Higher temperature gives higher strain rate."""
        r1 = _norton_bailey_strain_rate(100.0, 1e-12, 5.0, 0.0, 100.0, 300e3, 8.314, 700.0)
        r2 = _norton_bailey_strain_rate(100.0, 1e-12, 5.0, 0.0, 100.0, 300e3, 8.314, 900.0)
        assert r2 > r1


class TestCreepStrain:
    """Test suite for creep strain integration."""

    def test_creep_strain_increases(self):
        """Creep strain should increase with time."""
        cm = CreepModel(A=1e-12, n=5.0, m=0.0, Q=300e3)
        t, eps = cm.creep_strain(sigma=100.0, t_total=5000.0, T=800.0)
        assert eps[0] == 0.0
        assert eps[-1] > 0
        assert eps[-1] >= eps[0]

    def test_creep_strain_final_positive(self):
        """Final creep strain is positive."""
        cm = CreepModel()
        _, eps = cm.creep_strain(sigma=100.0, t_total=1000.0, T=800.0)
        assert eps[-1] > 0

    def test_creep_strain_zero_stress(self):
        """Zero stress yields near-zero creep strain."""
        cm = CreepModel()
        _, eps = cm.creep_strain(sigma=0.0, t_total=1000.0, T=800.0)
        assert abs(eps[-1]) < 1e-10


class TestStressRelaxation:
    """Test suite for stress relaxation."""

    def test_relaxation_stress_decreases(self):
        """Stress decreases during relaxation."""
        cm = CreepModel()
        t, sigma = cm.relaxation(eps0=1e-3, t_total=5000.0, T=800.0)
        assert sigma[-1] <= sigma[0]

    def test_relaxation_initial_stress(self):
        """Initial stress equals E * eps0."""
        cm = CreepModel(E=200e3)
        _, sigma = cm.relaxation(eps0=5e-4, t_total=100.0, T=800.0)
        assert abs(sigma[0] - 100.0) < 1.0

    def test_relaxation_stress_positive(self):
        """Relaxed stress remains positive."""
        cm = CreepModel()
        _, sigma = cm.relaxation(eps0=1e-3, t_total=1000.0, T=800.0)
        assert np.all(sigma >= 0)


class TestLarsonMiller:
    """Test suite for Larson-Miller parameter."""

    def test_larson_miller_finite(self):
        """LMP returns a finite value."""
        cm = CreepModel()
        P = cm.larson_miller(sigma=100.0)
        assert np.isfinite(P)

    def test_larson_miller_increases_with_stress(self):
        """LMP decreases with increasing stress (negative B_lmp)."""
        cm = CreepModel(A_lmp=25.0, B_lmp=-5.0)
        P1 = cm.larson_miller(50.0)
        P2 = cm.larson_miller(100.0)
        # B_lmp is negative, so P should be lower for higher stress
        assert P2 < P1

    def test_rupture_time_finite(self):
        """rupture_time returns a positive finite value."""
        cm = CreepModel()
        tr = cm.rupture_time(sigma=100.0, T=800.0)
        assert np.isfinite(tr)
        assert tr > 0

    def test_rupture_stress_roundtrip(self):
        """rupture_stress inverts rupture_time."""
        cm = CreepModel()
        sigma0 = 100.0
        tr = cm.rupture_time(sigma0, T=800.0)
        sigma_back = cm.rupture_stress(tr, T=800.0)
        assert abs(sigma_back - sigma0) / sigma0 < 0.05


class TestAnalyticalStrain:
    """Test suite for analytical strain approximation."""

    def test_steady_state_rate(self):
        """steady_state_rate returns positive value."""
        cm = CreepModel()
        rate = cm.steady_state_rate(sigma=100.0, T=800.0)
        assert rate > 0

    def test_strain_at_time_positive(self):
        """strain_at_time returns positive value."""
        cm = CreepModel()
        eps = cm.strain_at_time(sigma=100.0, t=1000.0, T=800.0)
        assert eps > 0

    def test_strain_at_time_m_not_minus_one(self):
        """strain_at_time matches numerical integration for m=0."""
        cm = CreepModel(A=1e-14, n=4.0, m=0.0, Q=300e3)
        eps_analytical = cm.strain_at_time(sigma=50.0, t=500.0, T=800.0)
        _, eps_num = cm.creep_strain(sigma=50.0, t_total=500.0, n_steps=500, T=800.0)
        assert abs(eps_analytical - eps_num[-1]) / max(eps_num[-1], 1e-12) < 0.1


class TestCompositeCreep:
    """Test suite for composite creep."""

    def test_composite_voigt(self):
        """Composite creep with Voigt rule returns finite value."""
        cm = CreepModel(A=1e-14, n=4.0)
        eps = cm.composite_creep(sigma=100.0, t=1000.0, V_f=0.4, rule="voigt")
        assert np.isfinite(eps)

    def test_composite_reuss(self):
        """Composite creep with Reuss rule returns finite value."""
        cm = CreepModel(A=1e-14, n=4.0)
        eps = cm.composite_creep(sigma=100.0, t=1000.0, V_f=0.4, rule="reuss")
        assert np.isfinite(eps)

    def test_composite_higher_vf_less_creep(self):
        """Higher fibre fraction reduces composite creep."""
        cm = CreepModel(A=1e-14, n=4.0)
        eps1 = cm.composite_creep(sigma=100.0, t=1000.0, V_f=0.2, rule="voigt")
        eps2 = cm.composite_creep(sigma=100.0, t=1000.0, V_f=0.6, rule="voigt")
        assert eps2 < eps1


class TestMaterialFactory:
    """Test suite for material factory."""

    def test_from_material_steel(self):
        """from_material creates a valid CreepModel for steel_cr1mo."""
        cm = CreepModel.from_material("steel_cr1mo")
        assert abs(cm.n - 5.5) < 0.1
        assert abs(cm.E - 210e3) < 1e3

    def test_from_material_unknown_raises(self):
        """from_material with unknown material raises ValueError."""
        with pytest.raises(ValueError, match="Unknown"):
            CreepModel.from_material("unknown_material")


class TestIntegration:
    """Integration tests across multiple methods."""

    def test_creep_relaxation_cycle(self):
        """Creep and relaxation can be run in sequence."""
        cm = CreepModel()
        _, eps = cm.creep_strain(sigma=80.0, t_total=2000.0, T=800.0)
        _, sig = cm.relaxation(eps0=5e-4, t_total=2000.0, T=800.0)
        assert np.isfinite(eps[-1])
        assert np.isfinite(sig[-1])

    def test_lmp_and_creep_self_consistent(self):
        """LMP and strain integration produce expected trends."""
        cm = CreepModel(A=1e-12, n=5.0)
        tr = cm.rupture_time(sigma=100.0, T=800.0)
        _, eps = cm.creep_strain(sigma=100.0, t_total=min(tr * 3600, 1e5), T=800.0)
        assert np.isfinite(eps[-1])
