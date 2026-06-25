"""Schema validation for CRSLR input JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AnalysisResult:
    """Validated input for CRSLR report generation."""

    analysis_id: str
    title: str
    date: str = ""
    domain: str = ""
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)
    vvv_status: str = "PENDING"
    uncertainty_interval: str = "95%"
    references: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


VALID_SECTIONS = {"context", "results", "synthesis", "limitations", "recommendations"}
VALID_VVV = {"PASS", "FAIL", "PENDING"}


def load_and_validate(path: str) -> AnalysisResult:
    """Load JSON from path and validate against schema."""
    with open(path) as f:
        raw = json.load(f)

    errors: list[str] = []

    if "analysis_id" not in raw:
        errors.append("analysis_id is required")

    if "sections" not in raw or not isinstance(raw["sections"], dict):
        errors.append("sections must be a non-empty dict")
    else:
        for key in raw["sections"]:
            if key not in VALID_SECTIONS:
                errors.append(f"Unknown section: '{key}' (valid: {', '.join(sorted(VALID_SECTIONS))})")

    if "vvv_status" in raw and raw["vvv_status"] not in VALID_VVV:
        errors.append(f"vvv_status must be one of {VALID_VVV}, got '{raw.get('vvv_status')}'")

    if errors:
        raise ValueError(f"Validation failed:\n  " + "\n  ".join(errors))

    return AnalysisResult(**raw)


def make_sample() -> AnalysisResult:
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        analysis_id="ANL-001",
        title="Topology Optimization — Cantilever Beam",
        date="2026-06-17T12:00:00Z",
        domain="Structural",
        sections={
            "context": {
                "content": "Cantilever beam 80×40 mesh, unit load at tip, SIMP penalization 3.0.",
                "priority": 1,
            },
            "results": {
                "content": "Compliance converged to 42.3 N·mm. Volume fraction 0.301.",
                "priority": 2,
                "metrics": {
                    "compliance": {"value": 42.3, "uncertainty": 2.1},
                    "volume_fraction": {"value": 0.301, "uncertainty": 0.005},
                    "iterations": {"value": 47, "uncertainty": 0},
                },
            },
            "synthesis": {
                "content": "Optimal topology transfers load through two primary load paths. Design is 30% lighter than baseline.",
                "priority": 3,
            },
            "limitations": {
                "content": "Linear elastic only. No manufacturing constraints applied. Mesh convergence at 50k elements not verified.",
                "priority": 4,
            },
            "recommendations": {
                "content": "1. Validate with finer mesh (50k elements)\n2. Add overhang constraint for AM\n3. Consider thermal loads in next iteration",
                "priority": 5,
            },
        },
        vvv_status="PASS",
        uncertainty_interval="95%",
        references=["Sigmund 2001", "Andreassen 2011"],
    )
