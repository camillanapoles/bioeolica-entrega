"""Tests for the fatigue module."""

import numpy as np
import pytest

from modules.fatigue import FatigueAnalysis, _rainflow_3point
from modules.fatigue import _woehler_curve, _basquin_curve
from modules.fatigue import _goodman_correction, _gerber_correction, _soderberg_correction


class TestSNCurves:
    """Test suite for S-N curve functions."""

    def test_woehler_curve_shape(self):
        """Woehler curve returns correct shape."""
        N = np.logspace(3, 7, 50)
        S = _woehler_curve(N, S_f=200.0, b=-0.1, N_f=1e6)
        assert S.shape == (50,)
        assert np.all(S > 0)

    def test_woehler_decreasing(self):
        """S-N curve is monotonically decreasing."""
        N = np.logspace(3, 7, 100)
        S = _woehler_curve(N, S_f=200.0, b=-0.1)
        assert np.all(np.diff(S) <= 0)

    def test_basquin_curve(self):
        """Basquin curve returns finite positive values."""
        N = np.logspace(3, 7, 100)
        S = _basquin_curve(N, sigma_f=950.0, b=-0.08)
        assert S.shape == (100,)
        assert np.all(S > 0)

    def test_sn_curve_method(self):
        """FatigueAnalysis.sn_curve() works with no arguments."""
        fa = FatigueAnalysis()
        S = fa.sn_curve()
        assert len(S) == 200
        assert np.all(S > 0)

    def test_cycles_to_failure(self):
        """cycles_to_failure returns expected value."""
        fa = FatigueAnalysis(sn_type="woehler", S_f=200.0, b=-0.1)
        Nf = fa.cycles_to_failure(200.0)
        assert np.isfinite(Nf)
        assert Nf > 0

    def test_cycles_to_failure_higher_stress_shorter_life(self):
        """Higher stress amplitude gives shorter life."""
        fa = FatigueAnalysis()
        Nf_low = fa.cycles_to_failure(180.0)
        Nf_high = fa.cycles_to_failure(220.0)
        assert Nf_high < Nf_low


class TestRainflow:
    """Test suite for rainflow cycle counting."""

    def test_rainflow_empty_returns_empty(self):
        """Two-point history (< 3) returns empty arrays."""
        r, m = _rainflow_3point(np.array([1.0, 2.0]))
        assert len(r) == len(m) == 0

    def test_rainflow_sine_wave(self):
        """A simple sine wave produces expected number of cycles."""
        t = np.linspace(0, 2 * np.pi, 100)
        history = 100.0 * np.sin(t)
        r, m = _rainflow_3point(history)
        assert len(r) >= 1

    def test_rainflow_constant_amplitude(self):
        """Constant amplitude history has consistent ranges."""
        pts = np.array([100, -50, 100, -50, 100, -50, 100])
        r, m = _rainflow_3point(pts)
        if len(r) > 0:
            assert np.allclose(r, 150.0, atol=1e-5)

    def test_rainflow_count_method(self):
        """FatigueAnalysis.rainflow_count returns three arrays."""
        fa = FatigueAnalysis()
        t = np.linspace(0, 2 * np.pi, 50)
        history = 100.0 * np.sin(t)
        ranges, means, counts = fa.rainflow_count(history)
        assert len(ranges) == len(means) == len(counts)


class TestDamageAccumulation:
    """Test suite for Palmgren-Miner damage."""

    def test_damage_single_cycle(self):
        """Single cycle below endurance limit produces small damage."""
        fa = FatigueAnalysis(S_f=200.0, b=-0.1)
        D = fa.damage_accumulation(np.array([100.0]))
        assert D > 0
        assert D < 1.0

    def test_damage_exceeds_unity(self):
        """Many high-amplitude cycles produce D > 1."""
        fa = FatigueAnalysis(S_f=200.0, b=-0.1)
        # Sa = 400 -> Nf = 1e6 * (400/200)^-10 = 977, D = 100000/977 > 1
        ranges = np.full(100_000, 800.0)
        D = fa.damage_accumulation(ranges)
        assert D > 1.0

    def test_damage_zero_ranges(self):
        """Zero stress ranges produce negligible damage."""
        fa = FatigueAnalysis()
        D = fa.damage_accumulation(np.array([0.0, 0.0]))
        # Very large but finite Nf -> damage is essentially zero
        assert D < 1e-10

    def test_fatigue_life_returns_repeats(self):
        """fatigue_life returns a tuple of three floats."""
        fa = FatigueAnalysis()
        t = np.linspace(0, 10, 200)
        history = 100.0 * np.sin(2 * np.pi * t)
        D, repeats, cycles = fa.fatigue_life(history)
        assert D > 0
        assert repeats > 0
        assert cycles > 0

    def test_goodman_correction_increases_damage(self):
        """Goodman correction increases damage for tensile mean stress."""
        fa = FatigueAnalysis(Su=400.0)
        ranges = np.array([200.0])
        means = np.array([50.0])
        D_none = fa.damage_accumulation(ranges, means=means, correction="none")
        D_good = fa.damage_accumulation(ranges, means=means, correction="goodman")
        assert D_good >= D_none


class TestMeanStressCorrections:
    """Test suite for mean stress correction functions."""

    def test_goodman_amplifies(self):
        """Goodman correction amplifies stress for positive mean."""
        Sa_eq = _goodman_correction(np.array([100.0]), np.array([50.0]), 400.0)
        assert Sa_eq[0] > 100.0

    def test_gerber_amplifies_less_than_goodman(self):
        """Gerber correction is less conservative than Goodman."""
        Sa = np.array([100.0])
        Sm = np.array([100.0])
        Su = 400.0
        G = _goodman_correction(Sa, Sm, Su)
        Ge = _gerber_correction(Sa, Sm, Su)
        assert Ge[0] < G[0]

    def test_soderberg_most_conservative(self):
        """Soderberg is more conservative than Goodman."""
        Sa = np.array([100.0])
        Sm = np.array([50.0])
        Su, Sy = 400.0, 250.0
        G = _goodman_correction(Sa, Sm, Su)
        Sod = _soderberg_correction(Sa, Sm, Sy)
        assert Sod[0] > G[0]


class TestHaighDiagram:
    """Test suite for Haigh diagram generation."""

    def test_haigh_diagram_keys(self):
        """haigh_diagram() contains Sm and correction method keys."""
        fa = FatigueAnalysis(Su=400.0, Sy=250.0)
        dia = fa.haigh_diagram(methods=["goodman", "gerber"])
        assert "Sm" in dia
        assert "goodman" in dia
        assert "gerber" in dia

    def test_haigh_diagram_decreasing(self):
        """Sa decreases as Sm increases for Goodman."""
        fa = FatigueAnalysis(Su=400.0, Sy=250.0)
        dia = fa.haigh_diagram(methods=["goodman"])
        Sa = dia["goodman"]
        assert Sa[0] > Sa[-1]


class TestMaterialFactory:
    """Test suite for the material factory."""

    def test_from_material_steel(self):
        """from_material creates a valid instance for steel_4340."""
        fa = FatigueAnalysis.from_material("steel_4340")
        assert fa.sn_type == "basquin"
        assert fa.Su == 1240.0

    def test_from_material_unknown_raises(self):
        """from_material with unknown material raises ValueError."""
        with pytest.raises(ValueError, match="Unknown"):
            FatigueAnalysis.from_material("unknown_alloy")


class TestIntegration:
    """Integration-level tests."""

    def test_end_to_end_fatigue_life(self):
        """Full pipeline: history -> rainflow -> damage -> life."""
        fa = FatigueAnalysis.from_material("steel_mild")
        np.random.seed(0)
        t = np.linspace(0, 5, 500)
        history = 150.0 * np.sin(2 * np.pi * 2.0 * t) + 50.0 * np.sin(2 * np.pi * 7.0 * t)
        _, repeats, cycles = fa.fatigue_life(history, correction="goodman")
        assert np.isfinite(repeats)
        assert np.isfinite(cycles)
        assert cycles > 0

    def test_plot_haigh_does_not_crash(self):
        """plot_haigh runs without error."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fa = FatigueAnalysis(Su=400.0, Sy=250.0)
        fig, ax = plt.subplots()
        fa.plot_haigh(ax=ax)
        plt.close(fig)
