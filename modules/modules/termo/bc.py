"""
Thermal boundary conditions — Dirichlet, Neumann, Robin types.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThermalBC:
    """Thermal boundary condition specification."""

    type: str  # "temperature" | "flux" | "convection"
    value: float
    node_ids: list[int] = field(default_factory=list)
    ref_temp: float = 300.0  # reference temperature for convection (K)

    def __post_init__(self):
        valid = {"temperature", "flux", "convection"}
        if self.type not in valid:
            raise ValueError(f"Invalid BC type '{self.type}'. Valid: {valid}")
        if self.type == "convection" and self.ref_temp is None:
            raise ValueError("Convection BC requires ref_temp")


def parse_bc_string(bc_str: str) -> dict[int, float]:
    """Parse 'node_id:value,node_id:value' format into dict."""
    result: dict[int, float] = {}
    for part in bc_str.split(","):
        part = part.strip()
        if ":" in part:
            node_id, val = part.split(":", 1)
            result[int(node_id.strip())] = float(val.strip())
    return result
