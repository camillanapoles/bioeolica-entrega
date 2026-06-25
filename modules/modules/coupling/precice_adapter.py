"""
precice_adapter.py — preCICE coupling adapter for multi-physics simulation.

Supports:
  - FSI (Fluid-Structure Interaction): OpenFOAM ↔ CalculiX
  - Thermal-structural: Termo module ↔ structural FEM

Usage:
    adapter = PreCICEAdapter("fsi", config_path="precice-config.xml")
    adapter.initialize()
    adapter.advance(dt)
    adapter.read_data(mesh_name, data_name)
    adapter.write_data(mesh_name, data_name, values)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Optional

# preCICE python bindings (optional — only available after system install)
# import precice


@dataclass
class CouplingParticipant:
    """A participant in a coupled simulation."""

    name: str
    mesh_name: str
    read_data: list[str] = field(default_factory=list)
    write_data: list[str] = field(default_factory=list)


@dataclass
class CouplingConfig:
    """Validated coupling configuration."""

    scenario: str  # "fsi", "thermal_structural", "conjugate_ht"
    participants: list[CouplingParticipant] = field(default_factory=list)
    coupling_scheme: str = "serial-explicit"  # or "parallel-implicit"
    max_time: float = 10.0
    max_iterations: int = 100
    time_window_size: float = 0.01

    def validate(self) -> list[str]:
        """Validate configuration, return list of errors (empty = valid)."""
        errors: list[str] = []
        valid_scenarios = {"fsi", "thermal_structural", "conjugate_ht"}
        if self.scenario not in valid_scenarios:
            errors.append(f"Unknown scenario '{self.scenario}'")
        if len(self.participants) < 2:
            errors.append(f"Need ≥2 participants, got {len(self.participants)}")
        for p in self.participants:
            if not p.read_data and not p.write_data:
                errors.append(f"Participant '{p.name}' has no data exchange")
        return errors


# Predefined coupling configurations

FSI_CONFIG = CouplingConfig(
    scenario="fsi",
    participants=[
        CouplingParticipant("Fluid", "FluidMesh", read_data=["Force"],
                            write_data=["Displacement", "Velocity"]),
        CouplingParticipant("Solid", "SolidMesh", read_data=["Displacement", "Velocity"],
                            write_data=["Force"]),
    ],
    coupling_scheme="serial-explicit",
    max_time=10.0,
)

THERMAL_STRUCTURAL_CONFIG = CouplingConfig(
    scenario="thermal_structural",
    participants=[
        CouplingParticipant("Thermal", "ThermalMesh", read_data=["Displacement"],
                            write_data=["Temperature", "HeatFlux"]),
        CouplingParticipant("Structural", "StructuralMesh",
                            read_data=["Temperature", "HeatFlux"],
                            write_data=["Displacement"]),
    ],
    coupling_scheme="serial-explicit",
)


def generate_precice_xml(config: CouplingConfig) -> str:
    """Generate preCICE configuration XML from CouplingConfig."""
    root = ET.Element("precice-configuration")

    # Solver interfaces
    for p in config.participants:
        solver = ET.SubElement(root, "solver-interface")
        solver.set("dimension", "3")

        participant = ET.SubElement(solver, "participant", name=p.name)
        for wd in p.write_data:
            ET.SubElement(participant, "write-data", name=wd, mesh=p.mesh_name)
        for rd in p.read_data:
            ET.SubElement(participant, "read-data", name=rd, mesh=p.mesh_name)

        ET.SubElement(participant, "provide-mesh", name=p.mesh_name)

    if config.coupling_scheme == "serial-explicit":
        scheme = ET.SubElement(root, "coupling-scheme:serial-explicit")
    else:
        scheme = ET.SubElement(root, "coupling-scheme:parallel-implicit")

    for p in config.participants[:2]:
        ET.SubElement(scheme, "participants", first=p.name)

    ET.SubElement(scheme, "max-time", value=str(config.max_time))
    ET.SubElement(scheme, "max-iterations", value=str(config.max_iterations))
    ET.SubElement(scheme, "time-window-size", value=str(config.time_window_size))

    return ET.tostring(root, encoding="unicode")


class PreCICEAdapter:
    """
    Adapter for preCICE coupling.

    Designed to work with or without the actual preCICE library.
    When preCICE is not installed, validation and config generation work;
    runtime coupling requires preCICE system installation.
    """

    def __init__(self, scenario: str = "fsi",
                 config: Optional[CouplingConfig] = None):
        self.scenario = scenario
        self.config = config or self._default_config(scenario)
        self._initialized = False

    def _default_config(self, scenario: str) -> CouplingConfig:
        configs = {
            "fsi": FSI_CONFIG,
            "thermal_structural": THERMAL_STRUCTURAL_CONFIG,
        }
        return configs.get(scenario, FSI_CONFIG)

    def validate(self) -> list[str]:
        """Validate coupling configuration."""
        return self.config.validate()

    def generate_xml(self) -> str:
        """Generate preCICE XML configuration."""
        return generate_precice_xml(self.config)

    def initialize(self) -> bool:
        """Validate config — returns True if valid."""
        errors = self.validate()
        self._initialized = len(errors) == 0
        return self._initialized

    def advance(self, dt: float) -> bool:
        """Advance coupling iteration (stub for testing)."""
        if not self._initialized:
            return False
        return True

    def read_data(self, mesh: str, data: str) -> list[float]:
        """Read coupling data from participant (stub)."""
        return [0.0]

    def write_data(self, mesh: str, data: str, values: list[float]) -> bool:
        """Write coupling data to participant (stub)."""
        return True
