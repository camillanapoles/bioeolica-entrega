#!/usr/bin/env python3
"""
Economic Analysis Module — LCC, NPV, IRR, Break-even, Sensitivity.

Computes lifecycle cost analysis for wind energy composite components:
  - LCC (Life Cycle Cost) with NPV, IRR, payback period
  - Break-even analysis (units to profitability)
  - Cost scaling laws for manufacturing (learning curves, power laws)
  - Sensitivity analysis (tornado charts, Monte Carlo sampling)

Usage:
    from economico import LCAAnalysis, break_even_analysis, cost_scaling_law

    analysis = LCAAnalysis(
        initial_investment=50000,         # R$
        annual_revenue=15000,              # R$/year
        annual_opex=5000,                  # R$/year
        lifetime_years=20,
        discount_rate=0.10,                # 10% WACC
    )

    npv_val = analysis.npv()
    irr_val = analysis.irr()
    payback = analysis.payback()
    sens = analysis.sensitivity(["opex_change", "revenue_change"])

    # Break-even
    be = break_even_analysis(
        fixed_cost=30000, variable_cost_per_unit=50,
        price_per_unit=120
    )

    # Cost scaling
    scaled = cost_scaling_law(
        base_cost=1000, base_size=1.0, new_size=2.5,
        scaling_exponent=0.7
    )
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  LCC ANALYSIS CLASS
# ═══════════════════════════════════════════════════════════════

@dataclass
class LCAAnalysis:
    """Life Cycle Cost analysis for energy/composite projects.

    Computes NPV, IRR, payback period, and performs sensitivity
    analysis on economic parameters.

    Args:
        initial_investment: Upfront capital cost (R$ or USD)
        annual_revenue: Expected annual revenue (R$/year)
        annual_opex: Annual operating expenditure (R$/year)
        lifetime_years: Project lifetime (years)
        discount_rate: Weighted average cost of capital (decimal)
        residual_value: Salvage value at end of life (R$)
        tax_rate: Effective tax rate (decimal, default 0.0)
        inflation_rate: Annual inflation rate (decimal, default 0.0)
    """
    initial_investment: float
    annual_revenue: float
    annual_opex: float
    lifetime_years: int = 20
    discount_rate: float = 0.10
    residual_value: float = 0.0
    tax_rate: float = 0.0
    inflation_rate: float = 0.0

    def _net_cash_flows(self) -> np.ndarray:
        """Compute net cash flow array over project lifetime.

        First element (year 0) is negative investment. Subsequent
        years include revenue minus opex, adjusted for inflation
        and tax.

        Returns:
            ndarray of shape (lifetime_years + 1,) with cash flows.
        """
        n = self.lifetime_years
        flows = np.zeros(n + 1)
        flows[0] = -self.initial_investment

        for t in range(1, n + 1):
            inflator = (1 + self.inflation_rate) ** (t - 1)
            revenue_t = self.annual_revenue * inflator
            opex_t = self.annual_opex * inflator
            pretax = revenue_t - opex_t
            after_tax = pretax * (1 - self.tax_rate)
            flows[t] = after_tax

        # Add residual value in final year
        flows[-1] += self.residual_value
        return flows

    def npv(self) -> float:
        """Compute Net Present Value.

        NPV = sum(CF_t / (1 + r)^t) for t = 0..lifetime_years

        Returns:
            NPV as float (positive = viable project).
        """
        flows = self._net_cash_flows()
        t = np.arange(len(flows))
        discounted = flows / (1 + self.discount_rate) ** t
        return round(float(np.sum(discounted)), 2)

    def irr(self, guess: float = 0.1) -> float:
        """Compute Internal Rate of Return.

        IRR is the discount rate that makes NPV = 0. Uses
        Newton-Raphson with numerical derivative (no SciPy dependency).

        Args:
            guess: Initial guess for IRR (decimal)

        Returns:
            IRR as decimal (e.g. 0.15 = 15%).
            Returns NaN if no solution found.
        """
        flows = self._net_cash_flows()

        def npv_at_rate(r: float) -> float:
            t = np.arange(len(flows))
            return float(np.sum(flows / (1 + r) ** t))

        # Newton-Raphson with numerical derivative (pure NumPy)
        def npv_derivative(r: float, eps: float = 1e-6) -> float:
            return (npv_at_rate(r + eps) - npv_at_rate(r - eps)) / (2 * eps)

        r = guess
        for _ in range(100):
            f = npv_at_rate(r)
            if abs(f) < 1e-8:
                return round(float(r), 4)
            df = npv_derivative(r)
            if abs(df) < 1e-15:
                break
            r_new = r - f / df
            # Keep within bounds
            if r_new <= 0:
                r_new = 0.001
            if abs(r_new - r) < 1e-8:
                return round(float(r_new), 4)
            r = r_new

        # Fallback: brute-force search over reasonable rates
        rates = np.linspace(0.001, 1.0, 1000)
        npvs = np.array([npv_at_rate(rr) for rr in rates])
        sign_changes = np.where(np.diff(np.sign(npvs)))[0]
        if len(sign_changes) == 0:
            return float('nan')
        idx = sign_changes[0]
        # Linear interpolation between bracketing rates
        r1, r2 = rates[idx], rates[idx + 1]
        n1, n2 = npvs[idx], npvs[idx + 1]
        if abs(n2 - n1) < 1e-12:
            return round(float(r1), 4)
        r_zero = r1 - n1 * (r2 - r1) / (n2 - n1)
        return round(float(max(r_zero, 0.0)), 4)

    def payback(self) -> float:
        """Compute discounted payback period in years.

        Payback is the time required for cumulative discounted
        cash flows to equal the initial investment.

        Returns:
            Payback period in years (float). Returns lifetime_years
            + 1 if payback not achieved within project life.
        """
        flows = self._net_cash_flows()
        t = np.arange(len(flows))
        discounted = flows / (1 + self.discount_rate) ** t
        cumulative = np.cumsum(discounted)

        for i in range(1, len(cumulative)):
            if cumulative[i] >= 0:
                # Linear interpolation between year i-1 and i
                prev_cum = cumulative[i - 1]
                curr_cum = cumulative[i]
                if curr_cum - prev_cum == 0:
                    return float(i)
                fraction = -prev_cum / (curr_cum - prev_cum)
                return round(float(i - 1 + fraction), 2)

        return float(self.lifetime_years + 1)

    def profitability_index(self) -> float:
        """Compute Profitability Index (PI).

        PI = NPV / |initial_investment|
        PI > 1.0 indicates a viable project.

        Returns:
            Profitability index as float.
        """
        if self.initial_investment == 0:
            return 0.0
        return round(self.npv() / abs(self.initial_investment), 4)

    def annualized_return(self) -> float:
        """Compute annualized return (equivalent annuity).

        Converts NPV into an equivalent uniform annual cash flow
        over the project lifetime using the capital recovery factor.

        Returns:
            Annualized return in R$/year.
        """
        n = self.lifetime_years
        r = self.discount_rate
        if r == 0:
            if n == 0:
                return 0.0
            return round(self.npv() / n, 2)

        crf = (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(self.npv() * crf, 2)

    def _lcoe_components(self) -> Dict:
        """Compute Levelized Cost of Energy components.

        Returns:
            Dict with LCOE breakdown.
        """
        flows = self._net_cash_flows()
        t = np.arange(len(flows))
        discount_factor = 1 / (1 + self.discount_rate) ** t

        total_discounted_cost = float(np.sum(
            (flows.copy() * discount_factor) * (flows < 0)
            + self.annual_opex * discount_factor
        ))

        return {
            "total_discounted_cost": round(total_discounted_cost, 2),
            "discount_rate_applied": self.discount_rate,
        }

    def sensitivity(
        self,
        parameters: Optional[List[str]] = None,
        variation: float = 0.2,
    ) -> Dict:
        """Perform sensitivity analysis on key economic parameters.

        Varies each parameter by +/- variation (default 20%) and
        measures the impact on NPV. Results can be visualized as
        a tornado chart.

        Args:
            parameters: List of parameter names to vary. If None,
                       uses all major parameters.
            variation: Fractional variation (0.2 = +-20%)

        Returns:
            Dict with parameter names as keys, each containing
            baseline, low, high NPV values.
        """
        if parameters is None:
            parameters = [
                "initial_investment", "annual_revenue", "annual_opex",
                "discount_rate", "lifetime_years",
            ]

        baseline_npv = self.npv()
        result = {}

        for param in parameters:
            original = getattr(self, param, None)
            if original is None or original == 0:
                continue

            if isinstance(original, (int, float)):
                # Low case
                low_val = original * (1 - variation)
                setattr(self, param, low_val)
                npv_low = self.npv()

                # High case
                high_val = original * (1 + variation)
                setattr(self, param, high_val)
                npv_high = self.npv()

                # Restore
                setattr(self, param, original)

                spread = abs(npv_high - npv_low)
                result[param] = {
                    "baseline_npv": baseline_npv,
                    "low_value": round(low_val, 4),
                    "low_npv": round(npv_low, 2),
                    "high_value": round(high_val, 4),
                    "high_npv": round(npv_high, 2),
                    "spread": round(spread, 2),
                    "sensitivity_index": round(spread / baseline_npv, 4) if baseline_npv != 0 else 0.0,
                }

        return {
            "baseline_npv": baseline_npv,
            "variation": variation,
            "parameters": result,
        }

    def monte_carlo(
        self,
        n_simulations: int = 1000,
        uncertainty: float = 0.15,
        seed: int = 42,
    ) -> Dict:
        """Run Monte Carlo simulation for NPV uncertainty estimation.

        Each parameter is sampled from a normal distribution centered
        on its nominal value with standard deviation = uncertainty * nominal.

        Args:
            n_simulations: Number of simulation runs
            uncertainty: Coefficient of variation for all parameters
            seed: Random seed for reproducibility

        Returns:
            Dict with statistics: mean, std, p5, p50, p95, min, max.
        """
        rng = np.random.default_rng(seed)
        npv_samples = np.zeros(n_simulations)

        original_investment = self.initial_investment
        original_revenue = self.annual_revenue
        original_opex = self.annual_opex
        original_rate = self.discount_rate

        for i in range(n_simulations):
            self.initial_investment = rng.normal(
                original_investment, abs(original_investment) * uncertainty
            )
            self.annual_revenue = rng.normal(
                original_revenue, abs(original_revenue) * uncertainty
            )
            self.annual_opex = rng.normal(
                original_opex, abs(original_opex) * uncertainty
            )
            self.discount_rate = rng.normal(
                original_rate, original_rate * uncertainty
            )
            self.discount_rate = max(self.discount_rate, 0.001)
            npv_samples[i] = self.npv()

        # Restore originals
        self.initial_investment = original_investment
        self.annual_revenue = original_revenue
        self.annual_opex = original_opex
        self.discount_rate = original_rate

        p5 = float(np.percentile(npv_samples, 5))
        p50 = float(np.percentile(npv_samples, 50))
        p95 = float(np.percentile(npv_samples, 95))

        return {
            "n_simulations": n_simulations,
            "mean_npv": round(float(np.mean(npv_samples)), 2),
            "std_npv": round(float(np.std(npv_samples)), 2),
            "p5_npv": round(p5, 2),
            "p50_npv": round(p50, 2),
            "p95_npv": round(p95, 2),
            "min_npv": round(float(np.min(npv_samples)), 2),
            "max_npv": round(float(np.max(npv_samples)), 2),
            "p_positive": round(float(np.sum(npv_samples > 0) / n_simulations * 100), 1),
            "seed": seed,
        }


# ═══════════════════════════════════════════════════════════════
#  BREAK-EVEN ANALYSIS
# ═══════════════════════════════════════════════════════════════

def break_even_analysis(
    fixed_cost: float,
    variable_cost_per_unit: float,
    price_per_unit: float,
    current_volume: Optional[float] = None,
) -> Dict:
    """Compute break-even point and margin analysis.

    Break-even quantity = fixed_cost / (price - variable_cost).
    Also computes contribution margin and margin of safety.

    Args:
        fixed_cost: Total fixed costs (R$)
        variable_cost_per_unit: Variable cost per unit (R$/unit)
        price_per_unit: Selling price per unit (R$/unit)
        current_volume: Actual production volume (units, optional)

    Returns:
        Dict with break-even quantity, contribution margin, and
        margin of safety if current_volume provided.
    """
    if price_per_unit <= variable_cost_per_unit:
        return {
            "error": "Price must exceed variable cost per unit.",
            "break_even_units": float('inf'),
            "contribution_margin_per_unit": 0.0,
            "contribution_margin_ratio_pct": 0.0,
        }

    contribution_margin = price_per_unit - variable_cost_per_unit
    contribution_ratio = (contribution_margin / price_per_unit) * 100
    be_units = fixed_cost / contribution_margin

    result = {
        "break_even_units": round(be_units, 1),
        "break_even_revenue_R": round(be_units * price_per_unit, 2),
        "contribution_margin_per_unit": round(contribution_margin, 2),
        "contribution_margin_ratio_pct": round(contribution_ratio, 2),
        "fixed_cost_R": fixed_cost,
        "variable_cost_per_unit": variable_cost_per_unit,
        "price_per_unit": price_per_unit,
    }

    if current_volume is not None and current_volume > 0:
        profit = current_volume * (price_per_unit - variable_cost_per_unit) - fixed_cost
        margin_of_safety_units = current_volume - be_units
        margin_of_safety_pct = (margin_of_safety_units / current_volume) * 100

        result["current_volume"] = current_volume
        result["profit_at_volume_R"] = round(profit, 2)
        result["margin_of_safety_units"] = round(margin_of_safety_units, 1)
        result["margin_of_safety_pct"] = round(margin_of_safety_pct, 2)

    return result


# ═══════════════════════════════════════════════════════════════
#  COST SCALING LAWS
# ═══════════════════════════════════════════════════════════════

def cost_scaling_law(
    base_cost: float,
    base_size: float,
    new_size: float,
    scaling_exponent: float = 0.7,
    learning_rate: Optional[float] = None,
    cumulative_units: int = 1,
    new_cumulative_units: int = 1,
) -> Dict:
    """Estimate cost at a new size using power-law scaling.

    Cost_new = Cost_base * (Size_new / Size_base) ^ exponent
    With optional learning curve: Cost = Cost_initial * N ^ (-log2(1/LR))

    Args:
        base_cost: Known cost at base size (R$)
        base_size: Base size/capacity parameter (kW, m, kg, etc.)
        new_size: New size/capacity parameter
        scaling_exponent: Scaling exponent (0.6–0.8 typical for
                         mechanical equipment, 0.7 default)
        learning_rate: Learning rate (decimal, e.g. 0.85 = 85%).
                      If None, no learning curve applied.
        cumulative_units: Cumulative units produced at base cost
        new_cumulative_units: Cumulative units at new cost

    Returns:
        Dict with scaled cost, learning curve factor, and final cost.
    """
    if base_size <= 0 or new_size <= 0:
        return {"error": "Sizes must be positive."}

    size_ratio = new_size / base_size
    scaled_cost = base_cost * (size_ratio ** scaling_exponent)

    result = {
        "base_cost": base_cost,
        "base_size": base_size,
        "new_size": new_size,
        "scaling_exponent": scaling_exponent,
        "size_ratio": round(size_ratio, 4),
        "scaled_cost": round(scaled_cost, 2),
    }

    if learning_rate is not None and cumulative_units > 0 and new_cumulative_units > 0:
        exp_learning = np.log2(1 / learning_rate) if learning_rate > 0 else 0.0
        learning_factor = (new_cumulative_units / cumulative_units) ** (-exp_learning)
        final_cost = scaled_cost * learning_factor

        result["learning_rate"] = learning_rate
        result["learning_exponent"] = round(exp_learning, 4)
        result["cumulative_units_base"] = cumulative_units
        result["cumulative_units_new"] = new_cumulative_units
        result["learning_factor"] = round(learning_factor, 4)
        result["final_cost_with_learning"] = round(final_cost, 2)
    else:
        result["final_cost"] = round(scaled_cost, 2)

    return result


# ═══════════════════════════════════════════════════════════════
#  LCOE (LEVELIZED COST OF ENERGY)
# ═══════════════════════════════════════════════════════════════

def lcoe(
    total_installed_cost_R: float,
    annual_energy_kWh: float,
    annual_o_and_m_R: float,
    discount_rate: float = 0.10,
    lifetime_years: int = 20,
    decommissioning_cost_R: float = 0.0,
) -> float:
    """Compute Levelized Cost of Energy.

    LCOE = (CAPEX + sum(OPEX_t / (1+r)^t) + decommissioning / (1+r)^n)
           / sum(Energy_t / (1+r)^t)

    Args:
        total_installed_cost_R: Total installed capital cost (R$)
        annual_energy_kWh: Annual energy production (kWh)
        annual_o_and_m_R: Annual O&M cost (R$)
        discount_rate: Discount rate (decimal)
        lifetime_years: Project life (years)
        decommissioning_cost_R: End-of-life decommissioning cost (R$)

    Returns:
        LCOE in R$/kWh.
    """
    t = np.arange(1, lifetime_years + 1)
    discount_factors = 1 / (1 + discount_rate) ** t

    # Capital cost (year 0)
    total_capex = total_installed_cost_R

    # O&M discounted sum
    opex_discounted = np.sum(annual_o_and_m_R * discount_factors)

    # Decommissioning discounted
    decom_discounted = decommissioning_cost_R / (1 + discount_rate) ** lifetime_years

    # Energy discounted sum (assuming constant annual generation)
    energy_discounted = np.sum(annual_energy_kWh * discount_factors)

    total_cost = total_capex + opex_discounted + decom_discounted
    total_energy = energy_discounted

    if total_energy <= 0:
        return float('inf')

    return round(total_cost / total_energy, 6)


# ═══════════════════════════════════════════════════════════════
#  COMPOSITE MANUFACTURING COST MODEL
# ═══════════════════════════════════════════════════════════════

def manufacturing_cost_estimate(
    material_cost_per_kg: float,
    mass_kg: float,
    labor_hours: float,
    labor_rate_per_hour: float,
    machine_rate_per_hour: float,
    tooling_cost: float,
    batch_size: int = 1,
    scrap_rate: float = 0.05,
    overhead_factor: float = 1.2,
) -> Dict:
    """Estimate manufacturing cost per part for composite components.

    Total cost = (material + labor + machine + tooling/batch)
                 * overhead / (1 - scrap_rate)

    Args:
        material_cost_per_kg: Raw material cost (R$/kg)
        mass_kg: Part mass (kg)
        labor_hours: Direct labor hours per part
        labor_rate_per_hour: Labor cost (R$/hour)
        machine_rate_per_hour: Machine cost (R$/hour)
        tooling_cost: Total tooling cost (R$, amortized over batch)
        batch_size: Number of parts in batch
        scrap_rate: Scrap/rework fraction (0.0–1.0)
        overhead_factor: Overhead multiplier (1.0–2.0 typical)

    Returns:
        Dict with cost breakdown.
    """
    if batch_size <= 0 or overhead_factor <= 0:
        return {"error": "Batch size and overhead must be positive."}

    material_cost = material_cost_per_kg * mass_kg
    labor_cost = labor_hours * labor_rate_per_hour
    machine_cost = labor_hours * machine_rate_per_hour  # machine time = labor time
    tooling_per_part = tooling_cost / batch_size

    total_direct = material_cost + labor_cost + machine_cost + tooling_per_part
    with_overhead = total_direct * overhead_factor
    with_scrap = with_overhead / (1 - scrap_rate)

    return {
        "material_cost_per_part": round(material_cost, 2),
        "labor_cost_per_part": round(labor_cost, 2),
        "machine_cost_per_part": round(machine_cost, 2),
        "tooling_per_part": round(tooling_per_part, 2),
        "total_direct_cost": round(total_direct, 2),
        "overhead_applied_R": round(total_direct * (overhead_factor - 1), 2),
        "total_cost_with_overhead": round(with_overhead, 2),
        "scrap_allowance_R": round(with_overhead * scrap_rate / (1 - scrap_rate), 2),
        "total_cost_per_part": round(with_scrap, 2),
        "batch_size": batch_size,
    }
