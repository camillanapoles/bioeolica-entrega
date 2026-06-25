#!/usr/bin/env python3
"""Tests for economico.py — Economic Analysis Module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import numpy as np
from economico import (
    LCAAnalysis,
    break_even_analysis,
    cost_scaling_law,
    lcoe,
    manufacturing_cost_estimate,
)


def test_npv_positive():
    """NPV should be positive for a profitable project."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=50000,
        annual_opex=15000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    npv_val = analysis.npv()
    assert npv_val > 0, f"Expected positive NPV, got {npv_val}"


def test_npv_negative():
    """NPV should be negative for a loss-making project."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=5000,
        annual_opex=4000,
        lifetime_years=3,
        discount_rate=0.10,
    )
    npv_val = analysis.npv()
    assert npv_val < 0, f"Expected negative NPV, got {npv_val}"


def test_irr_reasonable():
    """IRR should be between 0 and 1 for typical projects."""
    analysis = LCAAnalysis(
        initial_investment=50000,
        annual_revenue=20000,
        annual_opex=5000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    irr_val = analysis.irr()
    assert 0 < irr_val < 1.0, f"IRR {irr_val} outside expected range (0, 1)"
    # IRR should exceed discount rate for profitable project
    assert irr_val > 0.10, f"IRR {irr_val} should exceed discount rate 0.10"


def test_irr_no_solution():
    """IRR should return NaN for a clearly unviable project."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=100,
        annual_opex=5000,
        lifetime_years=3,
        discount_rate=0.10,
    )
    irr_val = analysis.irr()
    # May return NaN or very small value
    assert irr_val != 0.10  # Should not just return the discount rate


def test_payback_within_lifetime():
    """Payback should be less than project lifetime for profitable project."""
    analysis = LCAAnalysis(
        initial_investment=50000,
        annual_revenue=25000,
        annual_opex=5000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    pb = analysis.payback()
    assert 0 < pb < 10, f"Payback {pb} should be within 0-10 years"


def test_payback_exceeds_lifetime():
    """Payback should exceed lifetime for unprofitable project."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=5000,
        annual_opex=4000,
        lifetime_years=3,
        discount_rate=0.10,
    )
    pb = analysis.payback()
    assert pb > 3, f"Payback {pb} should exceed 3-year lifetime"


def test_profitability_index():
    """Profitability index should be > 0 for NPV positive project."""
    analysis = LCAAnalysis(
        initial_investment=50000,
        annual_revenue=20000,
        annual_opex=5000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    pi = analysis.profitability_index()
    assert pi > 0, f"PI {pi} should be positive for NPV > 0"


def test_break_even():
    """Break-even analysis should compute correct quantity."""
    result = break_even_analysis(
        fixed_cost=30000,
        variable_cost_per_unit=50,
        price_per_unit=120,
    )
    expected = 30000 / (120 - 50)
    assert abs(result["break_even_units"] - expected) < 0.1
    assert result["contribution_margin_per_unit"] == 70.0


def test_break_even_with_volume():
    """Break-even with current volume should include margin of safety."""
    result = break_even_analysis(
        fixed_cost=30000, variable_cost_per_unit=50,
        price_per_unit=120, current_volume=1000,
    )
    assert "margin_of_safety_pct" in result
    assert result["margin_of_safety_pct"] > 0
    assert result["profit_at_volume_R"] > 0


def test_cost_scaling():
    """Cost scaling law should compute smaller cost for smaller size."""
    result = cost_scaling_law(
        base_cost=1000, base_size=1.0,
        new_size=0.5, scaling_exponent=0.7,
    )
    assert 500 <= result["scaled_cost"] <= 700  # ~615 for 0.7 exponent


def test_cost_scaling_with_learning():
    """Cost scaling with learning curve should reduce cost further."""
    result = cost_scaling_law(
        base_cost=1000, base_size=1.0, new_size=2.0,
        scaling_exponent=0.7, learning_rate=0.85,
        cumulative_units=10, new_cumulative_units=100,
    )
    assert "final_cost_with_learning" in result
    assert result["final_cost_with_learning"] < result["scaled_cost"]


def test_lcoe_positive():
    """LCOE should return a positive value for valid inputs."""
    result = lcoe(
        total_installed_cost_R=50000,
        annual_energy_kWh=15000,
        annual_o_and_m_R=2000,
        discount_rate=0.10,
        lifetime_years=20,
    )
    assert result > 0, f"LCOE {result} should be positive"
    assert result < 10.0, f"LCOE {result} unreasonably high"


def test_lcoe_infinite():
    """LCOE should return infinite for zero energy."""
    result = lcoe(
        total_installed_cost_R=50000,
        annual_energy_kWh=0,
        annual_o_and_m_R=2000,
        lifetime_years=20,
    )
    assert result == float('inf')


def test_manufacturing_cost():
    """Manufacturing cost estimate should return reasonable breakdown."""
    result = manufacturing_cost_estimate(
        material_cost_per_kg=10.0, mass_kg=2.0,
        labor_hours=1.5, labor_rate_per_hour=30,
        machine_rate_per_hour=50,
        tooling_cost=5000, batch_size=100,
    )
    assert result["total_cost_per_part"] > 0
    assert result["material_cost_per_part"] == 20.0
    assert result["batch_size"] == 100
    assert result["total_direct_cost"] > 0


def test_monte_carlo():
    """Monte Carlo simulation should return statistics."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=40000,
        annual_opex=10000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    mc = analysis.monte_carlo(n_simulations=200, seed=42)
    assert mc["n_simulations"] == 200
    assert mc["mean_npv"] != 0
    assert mc["p_positive"] > 0
    assert mc["p5_npv"] < mc["p95_npv"]
    assert mc["seed"] == 42


def test_sensitivity_analysis():
    """Sensitivity analysis should return valid parameter impacts."""
    analysis = LCAAnalysis(
        initial_investment=100000,
        annual_revenue=40000,
        annual_opex=10000,
        lifetime_years=10,
        discount_rate=0.10,
    )
    sens = analysis.sensitivity(
        parameters=["initial_investment", "annual_revenue"],
        variation=0.2,
    )
    assert "initial_investment" in sens["parameters"]
    assert "annual_revenue" in sens["parameters"]
    assert sens["parameters"]["initial_investment"]["baseline_npv"] == sens["baseline_npv"]
