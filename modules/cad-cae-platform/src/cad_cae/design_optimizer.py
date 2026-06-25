"""Design Optimization — DOE, Pareto, sensitivity analysis."""

from __future__ import annotations

from itertools import product
from typing import Any, Callable

import numpy as np


class DesignSpace:
    """Defines parameter ranges for design optimization.

    Parameters
    ----------
    params : dict
        {name: (min, max)} — parameter bounds.
    """

    def __init__(self, params: dict[str, tuple[float, float]]):
        self.params = params
        self.names = list(params.keys())
        self._ranges = params

    def sample(self, n_levels: int = 3) -> dict[str, np.ndarray]:
        """Create a grid of parameter values at n_levels per parameter.

        Returns {name: array of values} for full factorial DOE.
        """
        return {n: np.linspace(lo, hi, n_levels) for n, (lo, hi) in self._ranges.items()}


class DesignOptimizer:
    """Parametric design optimization with DOE and Pareto analysis.

    Parameters
    ----------
    design_space : DesignSpace
        Parameter ranges.
    objectives : list of str
        Objective names for Pareto frontier.
    """

    def __init__(self, design_space: DesignSpace, objectives: list[str]):
        self.design_space = design_space
        self.objectives = objectives
        self._results: list[dict] = []

    def run_doe(self, evaluate_fn: Callable, n_levels: int = 3) -> list[dict]:
        """Run full factorial design of experiments.

        Parameters
        ----------
        evaluate_fn : callable
            Function(params_dict) -> dict of {objective: value}.
        n_levels : int, optional
            Levels per parameter (default 3).

        Returns
        -------
        results : list of dict
            Each entry has 'params', 'objectives', and any extra keys.
        """
        samples = self.design_space.sample(n_levels)
        grids = [samples[n] for n in self.design_space.names]
        self._results = []

        for combo in product(*grids):
            param_dict = dict(zip(self.design_space.names, combo))
            obj_vals = evaluate_fn(param_dict)
            self._results.append({"params": param_dict, "objectives": obj_vals})

        return self._results

    def pareto_frontier(self, maximize: tuple[bool, ...] | None = None) -> list[dict]:
        """Extract Pareto-optimal designs from DOE results.

        Parameters
        ----------
        maximize : tuple of bool, optional
            True = maximize objective, False = minimize. Default all minimize.

        Returns
        -------
        pareto : list of dict
            Pareto-optimal designs.
        """
        if not self._results:
            return []

        nobj = len(self.objectives)
        maximize = maximize or (False,) * nobj

        pareto = []
        for i, r1 in enumerate(self._results):
            o1 = [r1["objectives"][o] for o in self.objectives]
            dominated = False
            for j, r2 in enumerate(self._results):
                if i == j:
                    continue
                o2 = [r2["objectives"][o] for o in self.objectives]
                better = False
                worse_or_equal = True
                for k in range(nobj):
                    if maximize[k]:
                        if o2[k] > o1[k]:
                            better = True
                        elif o2[k] < o1[k]:
                            worse_or_equal = False
                    else:
                        if o2[k] < o1[k]:
                            better = True
                        elif o2[k] > o1[k]:
                            worse_or_equal = False
                if better and worse_or_equal:
                    dominated = True
                    break
            if not dominated:
                pareto.append(r1)

        return pareto

    def sensitivity(self, evaluate_fn: Callable, delta: float = 0.05) -> dict:
        """Local sensitivity analysis by perturbing each parameter.

        Parameters
        ----------
        evaluate_fn : callable
            Function(params_dict) -> dict of {objective: value}.
        delta : float, optional
            Relative perturbation (default 0.05 = 5%).

        Returns
        -------
        sensitivity : dict
            {objective: {param: sensitivity_index}}
        """
        if not self._results:
            return {}

        # Use the first result as baseline
        baseline_idx = 0
        baseline = self._results[baseline_idx]["objectives"]
        baseline_params = self._results[baseline_idx]["params"]

        sensitivity = {obj: {} for obj in self.objectives}
        for pname in self.design_space.names:
            pval = baseline_params[pname]
            perturbed = dict(baseline_params)
            dval = max(abs(pval) * delta, 0.001)
            perturbed[pname] = pval + dval
            new_result = evaluate_fn(perturbed)

            for obj in self.objectives:
                if abs(baseline[obj]) > 1e-12:
                    sens = abs(new_result[obj] - baseline[obj]) / abs(baseline[obj]) / delta
                else:
                    sens = abs(new_result[obj]) / delta
                sensitivity[obj][pname] = round(sens, 4)

        return sensitivity

    def optimize(self, evaluate_fn: Callable | None = None,
                 objectives: dict[str, str] | None = None) -> dict[str, Any]:
        """Find best design by weighted sum of normalized objectives.

        Parameters
        ----------
        evaluate_fn : callable, optional
            If provided, runs DOE first.
        objectives : dict, optional
            {name: 'min' or 'max'} — direction for each objective.

        Returns
        -------
        best : dict
            Best design parameters and objective values.
        """
        if evaluate_fn:
            self.run_doe(evaluate_fn, n_levels=5)

        if not self._results:
            return {"params": {}, "objectives": {}}

        objectives = objectives or {o: "min" for o in self.objectives}

        # Normalize and score
        scores = []
        for r in self._results:
            vals = [r["objectives"][o] for o in self.objectives]
            scores.append(vals)

        scores = np.array(scores)
        mins = scores.min(axis=0)
        maxs = scores.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1

        normalized = (scores - mins) / ranges
        for i, o in enumerate(self.objectives):
            if objectives.get(o, "min") == "max":
                normalized[:, i] = 1 - normalized[:, i]

        totals = normalized.sum(axis=1)
        best_idx = int(totals.argmin())

        return {
            "params": self._results[best_idx]["params"],
            "objectives": self._results[best_idx]["objectives"],
            "total_score": float(totals[best_idx]),
            "n_designs": len(self._results),
        }

    def plot_pareto(self, x_obj: str = "", y_obj: str = ""):
        """Plot Pareto frontier (requires matplotlib).

        Parameters
        ----------
        x_obj, y_obj : str
            Objective names for axes.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if not self._results:
            fig, ax = plt.subplots()
            ax.set_title("No results yet")
            return fig

        pareto = self.pareto_frontier()
        x_obj = x_obj or self.objectives[0]
        y_obj = y_obj or self.objectives[1] if len(self.objectives) > 1 else x_obj

        fig, ax = plt.subplots(figsize=(8, 6))
        for r in self._results:
            x = r["objectives"].get(x_obj, 0)
            y = r["objectives"].get(y_obj, 0)
            ax.scatter(x, y, c="blue", alpha=0.4, s=30)

        for r in pareto:
            x = r["objectives"].get(x_obj, 0)
            y = r["objectives"].get(y_obj, 0)
            ax.scatter(x, y, c="red", s=60, marker="*", zorder=5)

        ax.set_xlabel(x_obj)
        ax.set_ylabel(y_obj)
        ax.set_title(f"Pareto Frontier ({len(pareto)}/{len(self._results)} optimal)")
        ax.legend(["All designs", "Pareto-optimal"])
        plt.tight_layout()
        return fig
