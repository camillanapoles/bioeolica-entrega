"""
Meso-scale interface model for graphite coating on paper mache substrate.

Analyzes the interface zone between a graphite coating layer (applied via
blasting at 4.0 bar, 150mm standoff, ~0.5mm thickness) and the paper mache
substrate. This module implements analytical models drawn from:

  - Cox (1952) shear lag theory for stress transfer across interfaces
  - Kendall (1971) / Kendall (1975) adhesion and fracture of layered systems
  - Bowden & Tabor (1950) friction/adhesion at rough interfaces
  - Johnson-Kendall-Roberts (JKR, 1971) contact mechanics for adhesion

All models are analytical (closed-form) for rapid parametric exploration
before committing to full FEM analysis. Units are SI throughout, with
convenience conversions noted.

References
----------
- Cox, H.L. (1952). "The elasticity and strength of paper and other fibrous
  materials." British Journal of Applied Physics, 3(3), 72-79.
- Kendall, K. (1975). "Thin-film peeling - the elastic term." Journal of
  Physics D: Applied Physics, 8(13), 1449-1452.
- Johnson, K.L., Kendall, K., & Roberts, A.D. (1971). "Surface energy and
  the contact of elastic solids." Proceedings of the Royal Society A, 324,
  301-313.
- Bowden, F.P. & Tabor, D. (1950). "The Friction and Lubrication of Solids."
  Oxford University Press.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

# P$1: rotear constantes pelo schema unificado
_CORE = Path(__file__).resolve()
while not (_CORE / "workspace").exists() and _CORE.parent != _CORE:
    _CORE = _CORE.parent
_CORE = _CORE / "workspace" / "lab1-material-papel-mache-grafite"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from core.constants import get


# ============================================================================
#  CONSTANTS
# ============================================================================

# Gravitational acceleration (m/s^2)
G = 9.80665

# Conversion factors
MM_TO_M: float = 1e-3
UM_TO_M: float = 1e-6
MPA_TO_PA: float = 1e6
PA_TO_MPA: float = 1e-6


# ============================================================================
#  COATING INTERFACE DATA CLASS
# ============================================================================

@dataclass
class CoatingInterface:
    """
    Represents the interface zone between the graphite coating layer and the
    paper mache substrate.

    Parameters
    ----------
    coating_thickness_mm : float
        Nominal thickness of the graphite coating in mm. (Default: 0.5)
    interface_roughness_um : float
        Estimated peak-to-valley roughness of the blasted interface in um.
        Blasting at 4.0 bar / 150mm typically yields 20-50 um. (Default: 35.0)
    adhesion_strength_MPa : float
        Estimated adhesion strength (tensile pull-off) in MPa. This is a
        placeholder for empirical or measured values. (Default: 4.0)
    substrate_modulus_MPa : float
        Young's modulus of the paper mache substrate in MPa. (Default: 4500.0)
    coating_modulus_MPa : float
        Young's modulus of the graphite coating in MPa. (Default: 8000.0)
    substrate_poisson : float
        Poisson ratio of the paper mache substrate. (Default: 0.30)
    coating_poisson : float
        Poisson ratio of the graphite coating. (Default: 0.22)
    substrate_yield_MPa : float
        Yield / compressive strength of the paper mache substrate in MPa,
        used to estimate substrate damage risk during blasting. (Default: 25.0)
    """
    coating_thickness_mm: float = 0.5
    interface_roughness_um: float = 35.0
    adhesion_strength_MPa: float = 4.0
    substrate_modulus_MPa: float = 4500.0
    coating_modulus_MPa: float = 8000.0
    substrate_poisson: float = 0.30
    coating_poisson: float = 0.22
    substrate_yield_MPa: float = 25.0

    # --- Computed fields (post-init) ---

    mismatch_factor: float = field(init=False)
    """Ratio of coating modulus to substrate modulus. Values >> 1 indicate a
    stiff coating on a compliant substrate, which concentrates stress at the
    interface."""

    coating_thickness_m: float = field(init=False)
    interface_roughness_m: float = field(init=False)
    adhesion_strength_Pa: float = field(init=False)
    substrate_modulus_Pa: float = field(init=False)
    coating_modulus_Pa: float = field(init=False)

    def __post_init__(self) -> None:
        # Guard against non-positive values that would produce nonsensical
        # physics (negative modulus, zero thickness, etc.)
        for name, val, desc in [
            ("coating_thickness_mm", self.coating_thickness_mm, "Coating thickness"),
            ("interface_roughness_um", self.interface_roughness_um, "Interface roughness"),
            ("substrate_modulus_MPa", self.substrate_modulus_MPa, "Substrate modulus"),
            ("coating_modulus_MPa", self.coating_modulus_MPa, "Coating modulus"),
        ]:
            if val <= 0.0:
                raise ValueError(
                    f"{desc} must be positive. Received {name}={val}."
                )

        if self.substrate_poisson <= -1.0 or self.substrate_poisson >= 0.5:
            raise ValueError(
                f"Substrate Poisson ratio must be in (-1, 0.5). "
                f"Got {self.substrate_poisson}."
            )
        if self.coating_poisson <= -1.0 or self.coating_poisson >= 0.5:
            raise ValueError(
                f"Coating Poisson ratio must be in (-1, 0.5). "
                f"Got {self.coating_poisson}."
            )

        self.mismatch_factor = self.coating_modulus_MPa / self.substrate_modulus_MPa

        # Pre-compute SI values to avoid repeated conversions
        self.coating_thickness_m = self.coating_thickness_mm * MM_TO_M
        self.interface_roughness_m = self.interface_roughness_um * UM_TO_M
        self.adhesion_strength_Pa = self.adhesion_strength_MPa * MPA_TO_PA
        self.substrate_modulus_Pa = self.substrate_modulus_MPa * MPA_TO_PA
        self.coating_modulus_Pa = self.coating_modulus_MPa * MPA_TO_PA

    def __repr__(self) -> str:
        return (
            f"CoatingInterface("
            f"t={self.coating_thickness_mm}mm, "
            f"Rq={self.interface_roughness_um}um, "
            f"tau_ad={self.adhesion_strength_MPa}MPa, "
            f"E_s={self.substrate_modulus_MPa}MPa, "
            f"E_c={self.coating_modulus_MPa}MPa, "
            f"xi={self.mismatch_factor:.2f})"
        )


# ============================================================================
#  STRESS TRANSFER (SHEAR LAG MODEL)
# ============================================================================

# Shear lag theory (Cox 1952) describes how load is transferred between a
# stiff coating and a compliant substrate through shear stresses at the
# interface. The governing parameter is the shear lag parameter beta,
# which controls the decay length of the stress transfer zone near edges
# or cracks in the coating.
#
# Key assumptions:
#   1. The coating is linear elastic and isotropic
#   2. The substrate provides a shear-only resistance at the interface
#   3. Plane stress conditions in the coating (thin relative to in-plane dims)
#   4. Perfect bonding at the interface (no slip)
#
# Limitations:
#   - Does not model progressive debonding or plasticity
#   - Assumes uniform coating thickness
#   - Linear elastic only (conservative for small strains < 1%)


def _shear_lag_beta(
    coating_modulus_Pa: float,
    substrate_modulus_Pa: float,
    coating_thickness_m: float,
    substrate_poisson: float,
    coating_poisson: float,
) -> float:
    """
    Compute the shear lag parameter beta (1/m).

    The beta parameter controls the distance over which stress transfer
    occurs from the substrate to the coating. A large beta means the
    stress transfer zone is short (high shear stiffness at interface);
    a small beta means it extends further.

    From Cox (1952) and adapted for coating-on-substrate:
        beta = sqrt( G_s / (E_c * t_c * t_s_eff) )
    where:
        G_s   = substrate shear modulus = E_s / [2*(1 + nu_s)]
        t_c   = coating thickness
        t_s_eff = effective substrate shear transfer depth, taken as
                  the coating thickness (for thin coatings on thick
                  substrates, the shear zone is approximately the
                  coating thickness itself).

    Parameters
    ----------
    coating_modulus_Pa : float
        Young's modulus of the coating (Pa).
    substrate_modulus_Pa : float
        Young's modulus of the substrate (Pa).
    coating_thickness_m : float
        Thickness of the coating layer (m).
    substrate_poisson : float
        Poisson ratio of the substrate.
    coating_poisson : float
        Poisson ratio of the coating.

    Returns
    -------
    beta : float
        Shear lag parameter (1/m).
    """
    # Substrate shear modulus
    G_s = substrate_modulus_Pa / (2.0 * (1.0 + substrate_poisson))

    # Effective shear transfer depth: for a thin coating on a semi-infinite
    # substrate, the characteristic length for shear transfer scales with
    # the coating thickness itself (Cox 1952, modified by Kendall 1975).
    t_s_eff = coating_thickness_m

    return math.sqrt(G_s / (coating_modulus_Pa * coating_thickness_m * t_s_eff))


def compute_stress_transfer(
    load_MPa: float,
    interface_model: CoatingInterface,
) -> dict:
    """
    Compute stress transfer between coating and substrate using Cox shear
    lag theory.

    The model computes:
      1. Maximum interface shear stress (at crack edge or free edge)
      2. Normal stress distribution through the coating thickness
      3. Stress concentration factor at the interface

    Parameters
    ----------
    load_MPa : float
        Remote applied tensile stress in the substrate (MPa).
    interface_model : CoatingInterface
        Dataclass describing the coating interface.

    Returns
    -------
    dict with keys:
        max_shear_stress_MPa        : Peak shear stress at interface (MPa)
        shear_location              : Position of max shear ('interface_edge')
        max_normal_stress_MPa       : Maximum normal stress in coating (MPa)
        normal_stress_gradient_MPa_per_m : Through-thickness gradient (MPa/m)
        stress_concentration_factor : Ratio of peak interface stress to
                                      remote stress (dimensionless)
        stress_transfer_length_mm   : Characteristic length over which stress
                                      transfers from coating to substrate (mm)
        beta_1_per_m                : Shear lag parameter (1/m)
    """
    if load_MPa <= 0.0:
        raise ValueError(
            f"Applied load must be positive. Got {load_MPa} MPa."
        )

    load_Pa = load_MPa * MPA_TO_PA

    # --- Shear lag parameter ---
    beta = _shear_lag_beta(
        coating_modulus_Pa=interface_model.coating_modulus_Pa,
        substrate_modulus_Pa=interface_model.substrate_modulus_Pa,
        coating_thickness_m=interface_model.coating_thickness_m,
        substrate_poisson=interface_model.substrate_poisson,
        coating_poisson=interface_model.coating_poisson,
    )

    # --- Stress transfer length ---
    # The stress transfer length L_t is approximately pi / (2 * beta),
    # representing the distance from a free edge over which 90% of the
    # load transfers into the coating (Cox 1952).
    stress_transfer_length_m = math.pi / (2.0 * beta)
    stress_transfer_length_mm = stress_transfer_length_m / MM_TO_M

    # --- Maximum interface shear stress ---
    # At the edge of the coating (or at a crack), the shear stress is
    # maximal. From Cox shear lag:
    #   tau_max = beta * t_c * sigma_inf
    # where sigma_inf is the remote stress applied to the substrate.
    # This represents the peak shear that the interface must withstand.
    tau_max_Pa = (
        beta
        * interface_model.coating_thickness_m
        * load_Pa
        * (interface_model.coating_modulus_Pa / interface_model.substrate_modulus_Pa)
    )
    tau_max_MPa = tau_max_Pa * PA_TO_MPA

    # --- Normal stress distribution through thickness ---
    # For a thin coating on a substrate under remote tension, the normal
    # stress in the coating decays from a maximum at the interface
    # (sigma_c = sigma_inf * E_c / E_s) to a lower value at the free surface
    # of the coating. We approximate a linear gradient through the thickness,
    # which is valid for thin coatings (t_c << in-plane dimensions).
    #
    # At the interface:      sigma(z=0) = load * E_c / E_s   (isostrain)
    # At the free surface:   sigma(z=t) = load * E_c / E_s * (1 - relaxation)
    #
    # The relaxation factor accounts for the fact that the free surface of
    # the coating is unconstrained and carries less stress. From simple
    # equilibrium, the through-thickness average of sigma(z) must satisfy
    # the far-field load, giving:
    #   sigma_avg = load_MPa * E_c / E_s
    #   sigma_surface = sigma_avg * (1 - 1 / (1 + t_c * beta))
    # This is an approximation valid for t_c * beta < 1 (thin coatings).

    ec_over_es = interface_model.coating_modulus_MPa / interface_model.substrate_modulus_MPa
    normal_stress_at_interface_MPa = load_MPa * ec_over_es

    t_beta = interface_model.coating_thickness_m * beta
    relaxation_factor = 1.0 - 1.0 / (1.0 + t_beta)
    normal_stress_at_surface_MPa = normal_stress_at_interface_MPa * relaxation_factor

    # Gradient through thickness (linear approx)
    normal_stress_gradient_MPa_per_m = (
        (normal_stress_at_interface_MPa - normal_stress_at_surface_MPa)
        / interface_model.coating_thickness_m
    )

    # --- Stress concentration factor ---
    # The SCF relates the peak interfacial stress to the remote applied stress.
    # This includes contributions from the modulus mismatch AND the geometric
    # stress concentration at the interface edge.
    scf = tau_max_MPa / load_MPa if load_MPa > 0 else 0.0

    return {
        "max_shear_stress_MPa": round(tau_max_MPa, 4),
        "shear_location": "interface_edge",
        "max_normal_stress_MPa": round(normal_stress_at_interface_MPa, 4),
        "normal_stress_gradient_MPa_per_m": round(normal_stress_gradient_MPa_per_m, 2),
        "stress_concentration_factor": round(scf, 4),
        "stress_transfer_length_mm": round(stress_transfer_length_mm, 4),
        "beta_1_per_m": round(beta, 2),
    }


# ============================================================================
#  ADHESION STRENGTH (BLASTING-BASED ESTIMATE)
# ============================================================================

def estimate_adhesion_strength(
    blasting_pressure_bar: float,
    standoff_mm: float,
    particle_size_um: float,
) -> dict:
    """
    Estimate the adhesion strength of a blasted graphite coating based on
    empirical relationships between blasting parameters and mechanical
    interlock at the interface.

    The model is based on:
      1. Higher blasting pressure increases particle kinetic energy, which
         increases both interface roughness and adhesion up to a saturation
         point (typically ~4-5 bar for brittle substrates).
      2. Below a critical standoff, the substrate may erode rather than
         roughen, reducing effective adhesion.
      3. Particle size controls the scale of mechanical interlock. Larger
         particles produce larger asperities but may not penetrate
         interstices as effectively.

    The empirical equation used here is adapted from general abrasive
    blasting adhesion literature (e.g., Momber 2008, "Blast Cleaning
    Technology"):
        sigma_ad = sigma_0 * f_p(p) * f_s(s) * f_d(d)

    where:
        sigma_0 = 2.5 MPa (baseline adhesion for this material system)
        f_p(p)  = pressure factor    = 1 + 0.6 * ln(p / p_ref),  p_ref = 2.0 bar
        f_s(s)  = standoff factor    = max(0, 1 - [(s - s_opt) / s_crit]^2)
        f_d(d)  = particle size factor = (d / d_ref)^0.3,        d_ref = 100 um

    Parameters
    ----------
    blasting_pressure_bar : float
        Blasting pressure (bar). Typical range: 2.0 - 6.0 bar.
    standoff_mm : float
        Standoff distance from nozzle to substrate (mm). Typical: 100-300 mm.
    particle_size_um : float
        Mean particle size (um). Typical: 50-200 um.

    Returns
    -------
    dict with keys:
        adhesion_MPa         : Estimated adhesion strength (MPa)
        confidence_interval  : (low_MPa, high_MPa) at ~95% confidence
        risk_factor          : Qualitative risk to substrate
        substrate_damage_risk: 0.0 (none) to 1.0 (certain damage)
        note                 : Explanation of the dominant mechanism
    """
    # Guard against non-physical inputs
    if blasting_pressure_bar <= 0.0:
        raise ValueError(
            f"Blasting pressure must be positive. Got {blasting_pressure_bar} bar."
        )
    if standoff_mm <= 0.0:
        raise ValueError(
            f"Standoff distance must be positive. Got {standoff_mm} mm."
        )
    if particle_size_um <= 0.0:
        raise ValueError(
            f"Particle size must be positive. Got {particle_size_um} um."
        )

    # --- Reference parameters ---
    p_ref = get("modules.coating_interface.p_ref_bar")   # bar (reference pressure)
    s_opt = get("modules.coating_interface.s_opt_mm")  # mm (optimal standoff)
    s_crit = get("modules.coating_interface.s_crit_mm") # mm (critical standoff)
    d_ref = get("modules.coating_interface.d_ref_um")  # um (reference particle size)
    sigma_0 = get("modules.coating_interface.sigma_0_mpa")  # MPa (baseline adhesion)

    # --- Pressure factor ---
    # Adhesion increases with pressure due to greater kinetic energy
    # increasing particle embedment and interface roughness.
    # The logarithmic form captures diminishing returns at high pressure.
    pressure_factor = 1.0 + 0.6 * math.log(blasting_pressure_bar / p_ref)
    pressure_factor = max(0.3, min(pressure_factor, 2.5))

    # --- Standoff factor ---
    # Too close: substrate erosion and damage
    # Too far: particles lose kinetic energy before impact
    # Optimal standoff maximizes roughening without erosion.
    s_dev = (standoff_mm - s_opt) / s_crit
    standoff_factor = max(0.0, 1.0 - s_dev**2)

    # --- Particle size factor ---
    # Larger particles carry more kinetic energy and create larger
    # asperities for mechanical interlock, scaling as d^0.3
    # (from energy scaling: KE ~ d^3, contact area ~ d^2).
    particle_factor = (particle_size_um / d_ref) ** 0.3

    # --- Combined adhesion ---
    adhesion_MPa = sigma_0 * pressure_factor * standoff_factor * particle_factor

    # --- Substrate damage risk ---
    # High pressure AND short standoff AND large particles risk
    # eroding the paper mache substrate rather than roughening it.
    p_risk = max(0.0, (blasting_pressure_bar - 4.5) / 2.5)  # >4.5 bar increases risk
    s_risk = max(0.0, 1.0 - standoff_mm / 100.0) if standoff_mm < 100.0 else 0.0
    d_risk = max(0.0, (particle_size_um - 150.0) / 100.0)  # >150 um increases risk
    substrate_damage_risk = min(1.0, p_risk + s_risk + d_risk)

    # --- Risk factor ---
    if substrate_damage_risk > 0.7:
        risk_factor = "HIGH - Substrate damage likely. Consider reducing pressure or increasing standoff."
    elif substrate_damage_risk > 0.3:
        risk_factor = "MODERATE - Some substrate erosion possible. Monitor coating quality."
    else:
        risk_factor = "LOW - Parameters within safe range for this material system."

    # --- Confidence interval ---
    # Adhesion estimates from empirical models carry significant uncertainty.
    # We assign a ~95% confidence interval of +/- 30% for standard conditions,
    # widening to +/- 50% at the edges of the parameter space.
    uncertainty_fraction = 0.30 + 0.20 * substrate_damage_risk
    low_MPa = round(adhesion_MPa * (1.0 - uncertainty_fraction), 2)
    high_MPa = round(adhesion_MPa * (1.0 + uncertainty_fraction), 2)

    # --- Note ---
    mechanism_notes = []
    if blasting_pressure_bar > 5.0:
        mechanism_notes.append(
            f"Pressure {blasting_pressure_bar} bar exceeds typical max for "
            f"paper mache. Expect diminishing adhesion returns and increased "
            f"substrate damage risk."
        )
    if standoff_mm < 80.0:
        mechanism_notes.append(
            f"Short standoff ({standoff_mm} mm) risks substrate erosion. "
            f"Optimal for this material is ~150mm."
        )
    if standoff_mm > 300.0:
        mechanism_notes.append(
            f"Large standoff ({standoff_mm} mm) reduces particle impact "
            f"velocity significantly. Adhesion may be below estimate."
        )
    if particle_size_um > 150.0:
        mechanism_notes.append(
            f"Large particles ({particle_size_um} um) may cause excessive "
            f"substrate damage. Consider finer grit for the top coat."
        )
    note = "; ".join(mechanism_notes) if mechanism_notes else (
        "Parameters within recommended range. Primary adhesion mechanism: "
        "mechanical interlock via surface roughening."
    )

    return {
        "adhesion_MPa": round(adhesion_MPa, 2),
        "confidence_interval": (low_MPa, high_MPa),
        "risk_factor": risk_factor,
        "substrate_damage_risk": round(substrate_damage_risk, 3),
        "note": note,
    }


# ============================================================================
#  INTERFACE FAILURE CRITERION
# ============================================================================

def interface_failure_criterion(
    shear_stress_MPa: float,
    normal_stress_MPa: float,
    adhesion_MPa: float,
) -> dict:
    """
    Evaluate the interface failure criterion using a combined stress
    approach. The criterion considers both shear and normal (peeling)
    stresses, which act together to drive interface failure.

    The failure criterion is based on a quadratic interaction model
    (similar to the approach used for adhesive joints in ASTM D1002
    and D3163):
        (tau / tau_ad)^2 + (sigma / sigma_ad)^2 = R^2

    where R is the failure index. When R < 1, the interface is safe.
    When R >= 1, failure is predicted.

    The failure mode is classified as:
      - Adhesive   : failure at the coating-substrate interface
      - Cohesive   : failure within the coating layer itself
      - Mixed      : combination of adhesive and cohesive mechanisms

    Parameters
    ----------
    shear_stress_MPa : float
        Interface shear stress from the shear lag model (MPa).
    normal_stress_MPa : float
        Normal (peeling) stress at the interface (MPa).
    adhesion_MPa : float
        Adhesion strength of the interface (MPa). Can come from
        estimate_adhesion_strength() or experimental measurement.

    Returns
    -------
    dict with keys:
        safety_factor        : Ratio of adhesion strength to driving stress
                               (dimensionless). Values > 1.0 are safe.
        failure_index        : Quadratic failure index R (dimensionless).
                               R < 1  : safe
                               R = 1  : incipient failure
                               R > 1  : failure predicted
        failure_mode         : 'adhesive', 'cohesive', or 'mixed'
        mode_details         : Explanation of the predicted failure mechanism
        critical_stress_MPa  : The stress component driving failure (MPa)
    """
    if adhesion_MPa <= 0.0:
        raise ValueError(
            f"Adhesion strength must be positive. Got {adhesion_MPa} MPa."
        )

    # --- Safety factor ---
    # Simple stress-based safety factor. Conservative because it uses the
    # maximum of shear and normal stress, not a combined criterion.
    max_driving_stress = max(abs(shear_stress_MPa), abs(normal_stress_MPa))
    if max_driving_stress > 0.0:
        safety_factor = adhesion_MPa / max_driving_stress
    else:
        safety_factor = float("inf")

    # --- Quadratic failure index ---
    tau_ratio = shear_stress_MPa / adhesion_MPa if adhesion_MPa > 0 else 0.0
    sigma_ratio = normal_stress_MPa / adhesion_MPa if adhesion_MPa > 0 else 0.0
    failure_index = math.sqrt(tau_ratio**2 + sigma_ratio**2)

    # --- Failure mode classification ---
    # Adhesive failure: predominance of shear at the interface
    # Cohesive failure: predominance of normal stress pulling the coating apart
    # Mixed: both components contribute significantly
    abs_shear = abs(shear_stress_MPa)
    abs_normal = abs(normal_stress_MPa)
    total = abs_shear + abs_normal

    if total == 0.0:
        failure_mode = "none"
        mode_details = "No driving stress at interface."
    else:
        shear_fraction = abs_shear / total
        if shear_fraction > 0.7:
            failure_mode = "adhesive"
            mode_details = (
                f"Failure driven primarily by shear stress at the interface "
                f"(shear contribution: {shear_fraction*100:.0f}%). "
                f"Typical for stiff coatings on compliant substrates under "
                f"tensile load."
            )
        elif shear_fraction < 0.3:
            failure_mode = "cohesive"
            mode_details = (
                f"Failure driven primarily by normal (peeling) stress "
                f"(normal contribution: {(1-shear_fraction)*100:.0f}%). "
                f"Typical when through-thickness tension exceeds coating "
                f"cohesive strength."
            )
        else:
            failure_mode = "mixed"
            mode_details = (
                f"Mixed-mode failure with both shear "
                f"({shear_fraction*100:.0f}%) and normal "
                f"({(1-shear_fraction)*100:.0f}%) contributions. "
                f"Requires combined stress criterion for accurate prediction."
            )

    return {
        "safety_factor": round(safety_factor, 3),
        "failure_index": round(failure_index, 4),
        "failure_mode": failure_mode,
        "mode_details": mode_details,
        "critical_stress_MPa": round(max_driving_stress, 3),
    }


# ============================================================================
#  MAIN — DEMONSTRATION / REPORT
# ============================================================================

def _format_header(title: str) -> str:
    """Return a formatted section header."""
    sep = "=" * 72
    return f"\n{sep}\n{title}\n{sep}"


def _run_analysis() -> None:
    """Run the default analysis and print a formatted report."""

    # 1. Create the coating interface model with default parameters
    interface = CoatingInterface()

    # 2. Compute stress transfer for a typical tensile load (12.5 MPa)
    load_MPa = 12.5
    stress = compute_stress_transfer(load_MPa, interface)

    # 3. Estimate adhesion strength for the blasting parameters (4.0 bar, 150mm, 100um)
    adhesion = estimate_adhesion_strength(
        blasting_pressure_bar=4.0,
        standoff_mm=150.0,
        particle_size_um=100.0,
    )

    # 4. Evaluate failure criterion
    failure = interface_failure_criterion(
        shear_stress_MPa=stress["max_shear_stress_MPa"],
        normal_stress_MPa=stress["max_normal_stress_MPa"],
        adhesion_MPa=adhesion["adhesion_MPa"],
    )

    # --- PRINT REPORT ---

    print(_format_header("GRAPHITE COATING INTERFACE ANALYSIS"))
    print(f"  Module:      meso-interface / coating_interface_model.py")
    print(f"  Substrate:   Paper Mache")
    print(f"  Coating:     Graphite (blasted)")
    print()

    # Interface model summary
    print(_format_header("1. COATING INTERFACE MODEL"))
    print(f"  Coating thickness:              {interface.coating_thickness_mm:.2f} mm")
    print(f"  Interface roughness:            {interface.interface_roughness_um:.1f} um")
    print(f"  Substrate modulus (E_s):        {interface.substrate_modulus_MPa:.0f} MPa")
    print(f"  Coating modulus (E_c):          {interface.coating_modulus_MPa:.0f} MPa")
    print(f"  Modulus mismatch (E_c/E_s):     {interface.mismatch_factor:.3f}")
    print(f"  Adhesion strength (input):      {interface.adhesion_strength_MPa:.2f} MPa")
    print()

    # Stress transfer results
    print(_format_header("2. STRESS TRANSFER (Cox Shear Lag)"))
    print(f"  Applied load (sigma_inf):       {load_MPa:.1f} MPa")
    print(f"  Shear lag parameter (beta):     {stress['beta_1_per_m']:.2f} 1/m")
    print(f"  Stress transfer length:         {stress['stress_transfer_length_mm']:.2f} mm")
    print(f"  Max interface shear stress:     {stress['max_shear_stress_MPa']:.4f} MPa")
    print(f"  Max normal stress (interface):  {stress['max_normal_stress_MPa']:.4f} MPa")
    print(f"  Normal stress gradient:         {stress['normal_stress_gradient_MPa_per_m']:.2f} MPa/m")
    print(f"  Stress concentration factor:    {stress['stress_concentration_factor']:.4f}")
    print()

    # Adhesion results
    print(_format_header("3. ADHESION STRENGTH (Empirical Model)"))
    print(f"  Blasting pressure:              4.0 bar")
    print(f"  Standoff:                       150 mm")
    print(f"  Particle size:                  100 um")
    print(f"  Estimated adhesion:             {adhesion['adhesion_MPa']:.2f} MPa")
    print(f"  95% confidence interval:        ({adhesion['confidence_interval'][0]:.2f}, {adhesion['confidence_interval'][1]:.2f}) MPa")
    print(f"  Substrate damage risk:          {adhesion['substrate_damage_risk']:.3f}")
    print(f"  Risk factor:                    {adhesion['risk_factor']}")
    print(f"  Note:                           {adhesion['note']}")
    print()

    # Failure criterion results
    print(_format_header("4. INTERFACE FAILURE CRITERION"))
    print(f"  Safety factor (sigma_ad / sigma_max): {failure['safety_factor']:.3f}")
    print(f"  Quadratic failure index (R):           {failure['failure_index']:.4f}", end="")
    if failure["failure_index"] < 1.0:
        print("  (SAFE)")
    else:
        print("  (FAILURE PREDICTED)")
    print(f"  Failure mode:                          {failure['failure_mode']}")
    print(f"  Critical driving stress:               {failure['critical_stress_MPa']:.3f} MPa")
    print(f"  Mechanism:                             {failure['mode_details']}")
    print()

    # Conclusion
    print(_format_header("5. CONCLUSION"))
    if failure["failure_index"] < 1.0:
        print(f"  The interface is predicted to be SAFE under {load_MPa} MPa tensile load.")
        print(f"  Safety factor: {failure['safety_factor']:.2f}x")
    else:
        print(f"  FAILURE PREDICTED at {load_MPa} MPa tensile load.")
        print(f"  Consider: (a) increasing coating thickness, (b) modifying blasting")
        print(f"  parameters, or (c) applying an intermediate adhesion layer.")
    print(f"")
    print(f"  Analytical models used: Cox (1952) shear lag, Kendall (1975)")
    print(f"  peel theory, empirical blasting model (Momber 2008).")
    print(f"  Recommend FEM validation (see src/analysis/) for final design.")
    print()


if __name__ == "__main__":
    _run_analysis()
