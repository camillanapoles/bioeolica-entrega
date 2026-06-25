"""VVVCertificate — 6 critérios binários + métricas quantificadas.

Conforme data-model.md e INSTRUCTIONS.md M3:
  - 6 binary criteria
  - metrics dict with quantified error/convergence/conservation
  - overall_status: PASS/FAIL
  - return_phase suggestion if FAIL
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


class VVVCriterion:
    """Single VVV criterion result."""

    def __init__(self, name: str, passed: bool,
                 metric_value: float = 0.0,
                 tolerance: float = 0.0,
                 details: Optional[str] = None):
        self.name = name
        self.passed = passed
        self.metric_value = metric_value
        self.tolerance = tolerance
        self.details = details or ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "metric_value": self.metric_value,
            "tolerance": self.tolerance,
            "details": self.details,
        }


class VVVResult:
    """Container for VVV certification result."""

    def __init__(self, simulation_id: str, domain: str, scale: str,
                 criteria: List[VVVCriterion],
                 metrics: Dict[str, float],
                 overall_status: str,
                 return_phase: Optional[str] = None,
                 return_reason: Optional[str] = None):
        self.simulation_id = simulation_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.domain = domain
        self.scale = scale
        self.criteria = criteria
        self.metrics = metrics
        self.overall_status = overall_status
        self.return_phase = return_phase
        self.return_reason = return_reason

    def to_dict(self) -> Dict:
        return {
            "simulation_id": self.simulation_id,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "scale": self.scale,
            "criteria": {c.name: c.passed for c in self.criteria},
            "metrics": self.metrics,
            "overall_status": self.overall_status,
            "return_phase": self.return_phase,
            "return_reason": self.return_reason,
        }


class VVVCertificate:
    """Certificate aggregating 6 VVV criteria."""

    CRITERION_NAMES = [
        "mesh_convergence",
        "temporal_stability",
        "conservation",
        "benchmark_correlation",
        "cross_code",
        "units_consistency",
    ]

    # Return phase mapping per failed criterion
    RETURN_PHASE_MAP = {
        "mesh_convergence": "F5→F4",
        "temporal_stability": "F5→F4",
        "conservation": "F5→F3",
        "benchmark_correlation": "F5→F3",
        "cross_code": "F5→F4",
        "units_consistency": "F5→F1",
    }

    def __init__(self, domain: str = "general", scale: str = "meso"):
        self.simulation_id = str(uuid.uuid4())[:8]
        self.domain = domain
        self.scale = scale
        self.criteria: Dict[str, VVVCriterion] = {}

    def add_criterion(self, criterion: VVVCriterion) -> None:
        self.criteria[criterion.name] = criterion

    def evaluate(self) -> VVVResult:
        failures = [n for n, c in self.criteria.items() if not c.passed]
        all_pass = len(failures) == 0

        metrics = {}
        for name, crit in self.criteria.items():
            metrics[f"{name}_value"] = crit.metric_value

        return_phase = None
        return_reason = None
        if not all_pass and failures:
            # Use the first failing criterion for return guidance
            first_fail = failures[0]
            return_phase = self.RETURN_PHASE_MAP.get(first_fail, "F5→F3")
            fail_details = [f"{n}: {self.criteria[n].details}" for n in failures if self.criteria[n].details]
            return_reason = f"Failed criteria: {', '.join(failures)}. " + "; ".join(fail_details)

        return VVVResult(
            simulation_id=self.simulation_id,
            domain=self.domain,
            scale=self.scale,
            criteria=list(self.criteria.values()),
            metrics=metrics,
            overall_status="PASS" if all_pass else "FAIL",
            return_phase=return_phase,
            return_reason=return_reason,
        )
