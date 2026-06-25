"""Tests for thermodynamics.py — Thermodynamics & Energy Systems Module."""
import numpy as np
import pytest
from modules.thermodynamics import (
    DryingProcess, conduction_1D, convection, radiation,
    overall_heat_transfer, carnot_efficiency,
    rankine_cycle_efficiency, heat_pump_COP, exergy,
)


class TestConduction1D:
    def test_import(self):
        assert conduction_1D is not None

    def test_basic_conduction(self):
        Q = conduction_1D(k_WmK=50, A_m2=0.1, dT_K=100, dx_m=1.0)
        assert Q == pytest.approx(50 * 0.1 * 100 / 1.0)
        assert Q > 0

    def test_zero_thickness(self):
        with pytest.raises(ZeroDivisionError):
            conduction_1D(k_WmK=50, A_m2=0.1, dT_K=100, dx_m=0)

    def test_negative_dT(self):
        Q = conduction_1D(k_WmK=50, A_m2=0.1, dT_K=-50, dx_m=1.0)
        assert Q < 0


class TestConvection:
    def test_basic(self):
        Q = convection(h_Wm2K=10, A_m2=2.0, dT_K=30)
        assert Q == pytest.approx(10 * 2.0 * 30)
        assert Q > 0


class TestRadiation:
    def test_basic_radiation(self):
        Q = radiation(epsilon=0.9, A_m2=1.0, T1_K=500, T2_K=300)
        assert Q > 0

    def test_reverse_direction(self):
        Q = radiation(epsilon=0.9, A_m2=1.0, T1_K=300, T2_K=500)
        assert Q < 0


class TestOverallHeatTransfer:
    def test_basic(self):
        Q = overall_heat_transfer(U_Wm2K=500, A_m2=2.0, dT_lm=40)
        assert Q == pytest.approx(500 * 2.0 * 40)
        assert Q > 0


class TestDryingProcess:
    def test_default_instantiation(self):
        dp = DryingProcess()
        assert dp.mass_kg == 1.0
        assert dp.drying_temp_C == 60

    def test_energy_to_heat_positive(self):
        dp = DryingProcess(mass_kg=2.0, water_content_pct=50)
        E = dp.energy_to_heat_J()
        assert E > 0

    def test_energy_to_evaporate_positive(self):
        dp = DryingProcess(mass_kg=2.0, water_content_pct=50)
        E = dp.energy_to_evaporate_J()
        assert E > 0

    def test_total_energy_mj(self):
        dp = DryingProcess(mass_kg=2.0, water_content_pct=50)
        total = dp.total_energy_MJ()
        assert total > 0
        assert total < 1000  # sanity check

    def test_evaporation_dominates(self):
        dp = DryingProcess(mass_kg=1.0, water_content_pct=60)
        heat = dp.energy_to_heat_J()
        evap = dp.energy_to_evaporate_J()
        assert evap > heat  # latent heat >> sensible heat


class TestCarnotEfficiency:
    def test_carnot(self):
        eta = carnot_efficiency(T_hot_K=500, T_cold_K=300)
        assert eta == pytest.approx(1 - 300 / 500)
        assert 0 < eta < 1

    def test_zero_hot(self):
        assert carnot_efficiency(T_hot_K=0, T_cold_K=300) == 0

    def test_ideal_cycle(self):
        eta = carnot_efficiency(T_hot_K=1000, T_cold_K=300)
        assert eta > 0.5


class TestRankineCycle:
    def test_basic(self):
        res = rankine_cycle_efficiency(p_high_MPa=5, p_low_MPa=0.01)
        assert type(res) == dict and len(res) > 0
        assert res["rankine_efficiency_pct"] > 0
        assert res["carnot_efficiency_pct"] > 0

    def test_superheat_increases_efficiency(self):
        base = rankine_cycle_efficiency(p_high_MPa=5, p_low_MPa=0.01)
        sh = rankine_cycle_efficiency(p_high_MPa=5, p_low_MPa=0.01, T_superheat_K=100)
        assert sh["rankine_efficiency_pct"] >= base["rankine_efficiency_pct"]


class TestHeatPumpCOP:
    def test_cop_heating_greater_than_one(self):
        res = heat_pump_COP(T_hot_K=320, T_cold_K=280)
        assert res["COP_heating"] > 1.0

    def test_cop_cooling(self):
        res = heat_pump_COP(T_hot_K=320, T_cold_K=280)
        assert res["COP_cooling"] > 0

    def test_equal_temps(self):
        res = heat_pump_COP(T_hot_K=300, T_cold_K=300)
        assert res["COP_heating"] == float('inf')
        assert res["COP_cooling"] == float('inf')

    def test_cold_above_hot(self):
        res = heat_pump_COP(T_hot_K=280, T_cold_K=320)
        assert res["COP_heating"] == float('inf')


class TestExergy:
    def test_basic(self):
        res = exergy(Q_J=1000, T_source_K=500, T_dead_K=300)
        assert res["exergy_J"] > 0
        assert res["anergy_J"] > 0
        assert 0 < res["exergy_fraction_pct"] < 100

    def test_conservation(self):
        res = exergy(Q_J=1000, T_source_K=500, T_dead_K=300)
        total = res["exergy_J"] + res["anergy_J"]
        assert total == pytest.approx(1000, rel=1e-3)
