"""Topology optimization module — OpenMDAO-based SIMP method."""

from .fem_component import SIMPFemComponent
from .compliance import ComplianceComponent
from .volume_constraint import VolumeConstraint
from .topopt_group import TopOptGroup
from .run_optimization import run_topopt

__all__ = [
    "SIMPFemComponent",
    "ComplianceComponent",
    "VolumeConstraint",
    "TopOptGroup",
    "run_topopt",
]
