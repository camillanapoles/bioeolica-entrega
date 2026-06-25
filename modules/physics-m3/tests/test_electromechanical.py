"""Tests for electromechanical.py — Generators, Motors & Power Conversion."""
import numpy as np
import pytest
from modules.electromechanical import (
    PMSG, DCMachine, BatteryStorage,
    rectifier_efficiency, inverter_efficiency,
    transformer_efficiency, power_conversion_chain,
)


class TestPMSG:
    """PMSG: Permanent Magnet Synchronous Generator."""

    def test_import(self):
        assert PMSG is not None

    def test_default_instantiation(self):
        gen = PMSG()
        assert gen.power_rated_W == 3000.0
        assert gen.voltage_V == 48.0
        assert gen.poles == 8

    def test_electrical_freq(self):
        gen = PMSG()
        f = gen.electrical_freq_Hz
        assert f == pytest.approx(400 * 8 / 120)

    def test_emf_at_rated(self):
        gen = PMSG()
        emf = gen.emf_V(400)
        assert emf > 0

    def test_emf_increases_with_rpm(self):
        gen = PMSG()
        low = gen.emf_V(200)
        high = gen.emf_V(400)
        assert high > low

    def test_emf_zero_at_zero_rpm(self):
        gen = PMSG()
        assert gen.emf_V(0) == pytest.approx(0.0, abs=1e-6)

    def test_torque_max_positive(self):
        gen = PMSG()
        assert gen.torque_max_Nm() > 0

    def test_efficiency_at_rated(self):
        gen = PMSG()
        eta = gen.efficiency(3000)
        assert 80 <= eta <= 100  # percentage

    def test_efficiency_zero_output(self):
        gen = PMSG()
        assert gen.efficiency(0) == 0

    def test_summary_returns_dict(self):
        gen = PMSG()
        s = gen.summary()
        assert type(s) == dict
        assert s["type"] == "PMSG"
        assert s["power_rated_W"] == 3000
        assert s["efficiency_at_rated_pct"] > 80


class TestDCMachine:
    def test_default_instantiation(self):
        dc = DCMachine()
        assert dc.voltage_V == 24.0
        assert dc.K_T_Nm_A == 0.1

    def test_torque(self):
        dc = DCMachine(current_A=5)
        t = dc.torque_Nm()
        assert t == pytest.approx(0.1 * 5)

    def test_speed_rads(self):
        dc = DCMachine(voltage_V=24, current_A=5)
        w = dc.speed_rads()
        assert w > 0

    def test_speed_rpm(self):
        dc = DCMachine(voltage_V=24, current_A=5)
        rpm = dc.speed_rpm()
        assert rpm > 0

    def test_power_dict(self):
        dc = DCMachine(voltage_V=24, current_A=5)
        pw = dc.power_W()
        assert type(pw) == dict
        for key in ("electrical_W", "mechanical_W", "efficiency_pct",
                    "torque_Nm", "speed_rpm"):
            assert key in pw
        assert pw["electrical_W"] == pytest.approx(24 * 5)
        assert 80 <= pw["efficiency_pct"] <= 100

    def test_zero_current(self):
        dc = DCMachine(voltage_V=24, current_A=0)
        pw = dc.power_W()
        assert pw["efficiency_pct"] == 0


class TestRectifierEfficiency:
    def test_three_phase(self):
        eff = rectifier_efficiency(AC_power_W=1000)
        assert eff == 0.97

    def test_single_phase(self):
        eff = rectifier_efficiency(AC_power_W=1000, topology="single")
        assert eff == 0.95


class TestInverterEfficiency:
    def test_between_95_98(self):
        eff = inverter_efficiency(DC_power_W=1000)
        assert 0.95 <= eff <= 0.98

    def test_increases_with_power(self):
        low = inverter_efficiency(100)
        high = inverter_efficiency(10000)
        assert high >= low


class TestTransformerEfficiency:
    def test_full_load(self):
        eff = transformer_efficiency(S_rated_VA=1000, load_pct=100)
        assert 0 < eff < 1

    def test_no_load(self):
        eff = transformer_efficiency(S_rated_VA=1000, load_pct=0)
        assert eff == 0  # P_out = 0


class TestPowerConversionChain:
    def test_returns_dict(self):
        res = power_conversion_chain(DC_power_W=1000)
        assert type(res) == dict
        for key in ("inverter_efficiency_pct", "transformer_efficiency_pct",
                    "total_efficiency_pct", "loss_W"):
            assert key in res
        assert 0 < res["total_efficiency_pct"] < 100
        assert res["loss_W"] > 0

    def test_total_less_than_individual(self):
        res = power_conversion_chain(1000)
        assert res["total_efficiency_pct"] < res["inverter_efficiency_pct"]


class TestBatteryStorage:
    def test_default_instantiation(self):
        b = BatteryStorage()
        assert b.capacity_Wh == 2000.0
        assert b.chemistry == "LiFePO4"

    def test_capacity_ah(self):
        b = BatteryStorage(capacity_Wh=2000, voltage_nominal_V=48)
        assert b.capacity_Ah == pytest.approx(2000 / 48)

    def test_energy_available(self):
        b = BatteryStorage(capacity_Wh=2000)
        avail = b.energy_available_Wh(depth_of_discharge_pct=80)
        assert avail == pytest.approx(2000 * 0.80)

    def test_charge_time_positive(self):
        b = BatteryStorage(capacity_Wh=2000, soc_pct=50)
        t = b.charge_time_h(power_W=500, efficiency=0.95)
        assert t > 0

    def test_charge_time_zero_power(self):
        b = BatteryStorage()
        with pytest.raises(ZeroDivisionError):
            b.charge_time_h(power_W=0)

    def test_summary_dict(self):
        b = BatteryStorage()
        s = b.summary()
        assert type(s) == dict
        assert s["type"] == "LiFePO4"
        assert s["capacity_Wh"] == 2000.0
