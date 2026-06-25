#!/usr/bin/env python3
"""
Método Seletor — Decision Tree per KDI Numerical Methods (INSTRUCTIONS.md).

Implementa a árvore de decisão binária: regime de deformação → continuidade → fratura.
Seleciona automaticamente: FEM, MPM, SPH, DEM, Peridynamics, ou híbrido.

Uso:
    from method_selector import select_method, MethodRecommendation

    rec = select_method(
        deformation_regime="large",
        has_fracture=True,
        is_fluid=False,
        is_granular=False,
    )
    print(rec.primary)  # "MPM" or "Peridynamics"
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class MethodRecommendation:
    """Recommended numerical method and alternatives."""
    primary: str
    alternatives: List[str]
    rationale: str
    tools_open_source: List[str]
    coupling_tool: str = ""


@dataclass
class ProblemCharacteristics:
    """Characteristics that determine numerical method selection."""
    deformation_regime: str = "small"  # small, moderate, large, extreme
    has_fracture: bool = False
    has_fragmentation: bool = False
    is_fluid: bool = False
    is_granular: bool = False
    has_fsi: bool = False
    needs_coupling: bool = False
    is_multiscale: bool = False
    continuity: bool = True  # material is continuous (vs discrete)


# Decision tree implementation
def select_method(characteristics: ProblemCharacteristics) -> MethodRecommendation:
    """
    KDI decision tree for numerical method selection.

    Root: deformation regime
    """
    regime = characteristics.deformation_regime
    has_fracture = characteristics.has_fracture
    has_fragmentation = characteristics.has_fragmentation
    is_fluid = characteristics.is_fluid
    is_granular = characteristics.is_granular
    has_fsi = characteristics.has_fsi
    is_multiscale = characteristics.is_multiscale
    continuous = characteristics.continuity

    # Small deformation (FEM territory)
    if regime == "small" and continuous and not has_fracture:
        if is_fluid:
            return MethodRecommendation(
                primary="FVM (OpenFOAM)",
                alternatives=["FEM-ALE", "SPH"],
                rationale="Small deformation fluid: FVM is standard.",
                tools_open_source=["OpenFOAM", "SU2"],
            )
        return MethodRecommendation(
            primary="FEM",
            alternatives=["FVM"],
            rationale="Small deformation, no fracture: FEM is efficient and validated.",
            tools_open_source=["CalculiX", "Code_Aster", "FEniCS", "MOOSE"],
        )

    # Moderate to large deformation
    if regime in ("moderate", "large") and continuous:
        if has_fracture and not is_granular:
            return MethodRecommendation(
                primary="Peridynamics",
                alternatives=["MPM", "FEM-XFEM"],
                rationale="Fracture initiation: Peridynamics captures natural crack growth.",
                tools_open_source=["Peridigm", "PDLAMMPS", "PeriPy"],
            )
        if has_fragmentation:
            return MethodRecommendation(
                primary="Peridynamics → DEM",
                alternatives=["MPM", "SPH"],
                rationale="Fragmentation: Peridynamics inits cracks, DEM handles post-fracture.",
                tools_open_source=["Peridigm", "LIGGGHTS", "YADE"],
                coupling_tool="Peridigm + LIGGGHTS coupling",
            )
        if has_fsi:
            return MethodRecommendation(
                primary="SPH-MPM",
                alternatives=["FEM-ALE", "MPM"],
                rationale="FSI with large deformation: SPH handles fluid, MPM handles solid.",
                tools_open_source=["DualSPHysics", "CB-Geo MPM", "preCICE"],
                coupling_tool="preCICE",
            )
        if is_fluid:
            return MethodRecommendation(
                primary="SPH",
                alternatives=["FVM", "MPM"],
                rationale="Large deformation fluid with free surface: SPH is natural.",
                tools_open_source=["DualSPHysics", "SPHinXsys", "OpenFOAM"],
            )
        if is_granular:
            return MethodRecommendation(
                primary="DEM",
                alternatives=["MPM-DEM", "MPM"],
                rationale="Granular material: DEM models particle interactions.",
                tools_open_source=["YADE", "LIGGGHTS", "CFDEM"],
                coupling_tool="CFDEM (DEM-CFD coupling)",
            )
        return MethodRecommendation(
            primary="MPM",
            alternatives=["SPH", "FEM non-linear"],
            rationale="Large deformation, continuous: MPM avoids mesh distortion.",
            tools_open_source=["CB-Geo MPM", "Uintah MPM", "NairnMPM"],
        )

    # Extreme deformation and non-continuous
    if regime == "extreme" or not continuous:
        if is_granular:
            return MethodRecommendation(
                primary="DEM", alternatives=["MPM-DEM"],
                rationale="Extreme deformation granular: DEM is the standard.",
                tools_open_source=["YADE", "LIGGGHTS"],
            )
        return MethodRecommendation(
            primary="MPM",
            alternatives=["SPH", "Peridynamics"],
            rationale="Extreme deformation with material flow: MPM handles topology change.",
            tools_open_source=["CB-Geo MPM", "Uintah MPM"],
        )

    # Multi-scale
    if is_multiscale:
        return MethodRecommendation(
            primary="ROM + PINNs",
            alternatives=["FE²", "Multi-scale MPM"],
            rationale="Multi-scale: ROM reduces DOFs, PINNs replace sub-models.",
            tools_open_source=["pyROM", "DeepXDE", "FEniCS + DeepXDE coupling"],
        )

    # Fallback
    return MethodRecommendation(
        primary="FEM",
        alternatives=["MPM", "SPH"],
        rationale="Default: FEM for standard structural analysis.",
        tools_open_source=["CalculiX", "FEniCS", "Code_Aster"],
    )


def recommend_for_composite_laminate() -> MethodRecommendation:
    """Specific recommendation for composite laminate analysis."""
    return MethodRecommendation(
        primary="CLT + FEM (multi-scale)",
        alternatives=["FE²", "ROM"],
        rationale="Composite laminate: CLT at meso-scale, FEM at macro-scale.",
        tools_open_source=["CalculiX (composite)", "FEniCS + custom CLT"],
    )


def recommend_for_wind_turbine_blade() -> MethodRecommendation:
    """Specific recommendation for wind turbine blade analysis."""
    return MethodRecommendation(
        primary="FEM + BEM (coupled)",
        alternatives=["FSI (preCICE)", "MPM for leading-edge erosion"],
        rationale="Blade: FEM for structure, BEM for aerodynamics, preCICE for coupling.",
        tools_open_source=["CalculiX", "OpenFOAM", "preCICE"],
        coupling_tool="preCICE",
    )
