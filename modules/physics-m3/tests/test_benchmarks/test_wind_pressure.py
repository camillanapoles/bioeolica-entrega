"""
Benchmark: Wind Pressure Coefficients — NBR 6123 (ABNT 1988)
Domain: Fluidos / Engenharia do Vento

Reference: ABNT NBR 6123:1988 — Forças Devidas ao Vento em Edificações
  q = 0.613 × Vk² (dynamic pressure, Pa)
  Cp_external: pressure coefficients per geometry type

Tolerance: < 10% for standard geometries (rectangular, cylindrical)
"""
import numpy as np
import pytest


def dynamic_pressure(Vk: float) -> float:
    """Dynamic wind pressure per NBR 6123 Section 4.2: q = 0.613 × Vk²."""
    return 0.613 * Vk ** 2


def cp_rectangular_windward() -> float:
    """Cp external for windward face of rectangular building."""
    return 0.8  # NBR 6123 Table 4


def cp_rectangular_leeward(h_by_b: float) -> float:
    """Cp external for leeward face — depends on h/b ratio."""
    if h_by_b <= 0.5:
        return -0.4
    elif h_by_b <= 1.0:
        return -0.5
    else:
        return -0.6


def cp_rectangular_sidewall() -> float:
    """Cp external for sidewall (suction)."""
    return -0.7  # NBR 6123 Table 4


def cp_cylindrical(reynolds: float) -> float:
    """Cp external for cylindrical sections — varies with Re."""
    if reynolds < 2e5:
        return -0.8  # Subcritical: Cp_min ~ -0.8
    elif reynolds < 5e5:
        return -0.7  # Transition
    else:
        return -0.5  # Supercritical: Cp_min ~ -0.5


@pytest.mark.parametrize("Vk, expected_q", [
    (30, 0.613 * 900),   # 30 m/s → 551.7 Pa
    (40, 0.613 * 1600),  # 40 m/s → 980.8 Pa
    (50, 0.613 * 2500),  # 50 m/s → 1532.5 Pa
])
def test_dynamic_pressure(Vk, expected_q):
    """Verify dynamic pressure formula: q = 0.613 × Vk² (NBR 6123 §4.2)."""
    result = dynamic_pressure(Vk)
    assert abs(result - expected_q) < 0.1, f"q({Vk})={result}, expected={expected_q}"


def test_cp_rectangular_windward():
    """Windward face Cp = +0.8 per NBR 6123 Table 4."""
    assert abs(cp_rectangular_windward() - 0.8) < 0.01


@pytest.mark.parametrize("h_by_b, expected", [
    (0.3, -0.4),
    (0.5, -0.4),
    (0.75, -0.5),
    (1.0, -0.5),
    (2.0, -0.6),
])
def test_cp_rectangular_leeward(h_by_b, expected):
    """Leeward Cp depends on h/b ratio per NBR 6123 Table 4."""
    result = cp_rectangular_leeward(h_by_b)
    assert abs(result - expected) < 0.01, \
        f"h/b={h_by_b}: Cp={result}, expected={expected}"


def test_cp_sidewall():
    """Sidewall suction Cp = -0.7 per NBR 6123."""
    assert abs(cp_rectangular_sidewall() - (-0.7)) < 0.01


def test_wind_force_calculation():
    """Calculate total wind force: F = q × Cp × A (NBR 6123 §4.3)."""
    Vk = 45.0       # m/s
    A = 10.0 * 5.0  # m² (wall area)
    q = dynamic_pressure(Vk)
    Cp = cp_rectangular_windward()

    F = q * Cp * A  # N

    # Sanity: force should be positive (windward), order of kN
    assert F > 0, "Windward force must be positive"
    assert 10000 < F < 100000, f"Force {F:.0f} N outside expected range (10-100 kN) for 45 m/s wind on 50m²"


def test_cylindrical_cp_reynolds_dependence():
    """Cylindrical Cp varies with Reynolds number regime."""
    re_low = 1e5   # Subcritical
    re_high = 1e6  # Supercritical

    cp_low = cp_cylindrical(re_low)
    cp_high = cp_cylindrical(re_high)

    assert cp_low == -0.8, f"Subcritical Re: Cp={cp_low}, expected -0.8"
    assert cp_high == -0.5, f"Supercritical Re: Cp={cp_high}, expected -0.5"


def test_nbr6123_coherence():
    """Verify NBR 6123 Cp values are physically coherent."""
    # |Cp_windward| + |Cp_leeward| = total pressure coefficient
    cp_w = abs(cp_rectangular_windward())
    cp_l = abs(cp_rectangular_leeward(1.0))
    cp_total = cp_w + cp_l

    # For h/b=1: 0.8 + 0.5 = 1.3 — reasonable for rectangular building
    assert 1.0 < cp_total < 2.0, f"Total Cp={cp_total} outside expected range"
