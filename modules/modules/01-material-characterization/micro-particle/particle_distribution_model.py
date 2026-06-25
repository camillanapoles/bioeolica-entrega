"""
Micro-scale particle distribution model for graphite particles in the
coating layer and penetrating into the paper mache substrate.

Models the graphite particles embedded in the coating layer during
blasting (4.0 bar, 150mm standoff, ~100 um mean particle size). The
model addresses:

  1. Lognormal size distribution of flake graphite particles
  2. Random spatial distribution in a representative volume element (RVE)
  3. Stress concentration around stiff particles in a softer matrix
     (Eshelby inclusion theory / modified Goodier model)
  4. Effective properties of the particle-reinforced composite via
     Mori-Tanaka homogenization
  5. Penetration depth distribution into the porous paper mache substrate

References
----------
- Eshelby, J.D. (1957). "The determination of the elastic field of an
  ellipsoidal inclusion, and related problems." Proceedings of the Royal
  Society A, 241(1226), 376-396.
- Mori, T. & Tanaka, K. (1973). "Average stress in matrix and average
  elastic energy of materials with misfitting inclusions." Acta
  Metallurgica, 21(5), 571-574.
- Goodier, J.N. (1933). "Concentration of stress around spherical and
  cylindrical inclusions and flaws." Journal of Applied Mechanics, 55,
  39-44.
- Budiansky, B. (1965). "On the elastic moduli of some heterogeneous
  materials." Journal of the Mechanics and Physics of Solids, 13(4),
  223-227.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================================
#  CONSTANTS
# ============================================================================

UM_TO_M: float = 1e-6
M_TO_UM: float = 1e6
MPA_TO_PA: float = 1e6
PA_TO_MPA: float = 1e-6


# ============================================================================
#  PARTICLE DISTRIBUTION DATA CLASS
# ============================================================================

@dataclass
class ParticleDistribution:
    """
    Describes the statistical distribution of graphite particles in the
    coating layer.

    Parameters
    ----------
    particle_size_um : float
        Mean particle diameter in um. Flake graphite for industrial blasting
        typically ranges 50-150 um. (Default: 100.0)
    particle_size_std_um : float
        Standard deviation of particle diameter in um. A lognormal
        distribution is assumed (natural for milling processes).
        (Default: 20.0)
    volume_fraction : float
        Volume fraction of graphite particles in the coating layer.
        Typical values for blasting: 0.30-0.50. (Default: 0.35)
    penetration_depth_um : float
        Mean penetration depth of particles into the paper mache substrate
        during blasting (um). Typical: 50-150 um. (Default: 80.0)
    particle_aspect_ratio : float
        Aspect ratio (diameter / thickness) of flake graphite particles.
        Flake graphite is platelike, typically 5:1 to 10:1.
        (Default: 5.0)
    grade : str
        Graphite grade description. (Default: 'flake_industrial')
    particle_modulus_MPa : float
        Young's modulus of graphite particles (MPa). Graphite flakes are
        highly anisotropic; this is the in-plane modulus.
        (Default: 15000.0)
    particle_poisson : float
        Poisson ratio of graphite particles. (Default: 0.20)
    """
    particle_size_um: float = 100.0
    particle_size_std_um: float = 20.0
    volume_fraction: float = 0.35
    penetration_depth_um: float = 80.0
    particle_aspect_ratio: float = 5.0
    grade: str = "flake_industrial"
    particle_modulus_MPa: float = 15000.0
    particle_poisson: float = 0.20

    # --- Computed post-init ---

    rve_size_um: float = field(init=False)
    """Edge length of the representative volume element (um). Computed from
    the expected particle count, volume fraction, and mean particle volume
    to ensure the RVE is large enough to contain the target number of
    particles at the specified volume fraction."""

    n_expected_particles: int = field(init=False, default=1000)
    """Target number of particles for statistical representation. This is
    used to compute the RVE size and can be overridden to control the
    resolution of the particle field."""

    def __post_init__(self) -> None:
        if self.particle_size_um <= 0.0:
            raise ValueError(
                f"Particle size must be positive. Got {self.particle_size_um}."
            )
        if self.particle_size_std_um <= 0.0:
            raise ValueError(
                f"Particle size std dev must be positive. "
                f"Got {self.particle_size_std_um}."
            )
        if not (0.0 < self.volume_fraction < 1.0):
            raise ValueError(
                f"Volume fraction must be in (0, 1). Got {self.volume_fraction}."
            )
        if self.particle_aspect_ratio < 1.0:
            raise ValueError(
                f"Aspect ratio must be >= 1. Got {self.particle_aspect_ratio}."
            )

        # Compute RVE size from the target number of particles, volume
        # fraction, and mean particle volume. This ensures the RVE is
        # large enough for statistical representativity.
        r_mean = self.particle_size_um / 2.0
        single_volume = (4.0 / 3.0) * math.pi * r_mean**3
        total_volume = self.n_expected_particles * single_volume
        rve_volume = total_volume / self.volume_fraction
        self.rve_size_um = max(200.0, rve_volume ** (1.0 / 3.0))

    def __repr__(self) -> str:
        return (
            f"ParticleDistribution("
            f"d={self.particle_size_um}um, "
            f"Vf={self.volume_fraction:.2f}, "
            f"AR={self.particle_aspect_ratio:.1f}, "
            f"grade='{self.grade}')"
        )


# ============================================================================
#  PARTICLE FIELD GENERATION
# ============================================================================

def generate_particle_field(
    n_particles: int,
    distribution: ParticleDistribution,
    seed: Optional[int] = None,
) -> List[Dict]:
    """
    Generate a random particle field within a representative volume element
    (RVE) of size (L x L x L), where L = distribution.rve_size_um.

    Particles are:
      - Sized from a lognormal distribution with the given mean and std dev
      - Positioned randomly with uniform spatial distribution
      - Oriented randomly (isotropic orientation of platelike particles)
      - Non-overlapping (hard-sphere rejection sampling)

    Parameters
    ----------
    n_particles : int
        Number of particles to generate.
    distribution : ParticleDistribution
        Statistical distribution parameters.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    list of dict
        Each dict represents one particle with keys:
          x, y, z            : Center position in um (float)
          radius_um          : Equivalent spherical radius in um (float)
          radius_eq_um       : Same as radius_um (for the inclusion model)
          aspect_ratio       : Diameter / thickness (float)
          theta, phi         : Orientation angles in radians (float)
          actual_Vf          : Actual volume fraction of the generated field (float)
    """
    if n_particles < 1:
        raise ValueError(
            f"Number of particles must be >= 1. Got {n_particles}."
        )

    if seed is not None:
        random.seed(seed)

    L = distribution.rve_size_um
    mu = distribution.particle_size_um
    sigma = distribution.particle_size_std_um

    # The lognormal distribution is parameterized by mu_log and sigma_log,
    # which relate to the desired mean and standard deviation:
    #   mu_log    = ln( mu^2 / sqrt(mu^2 + sigma^2) )
    #   sigma_log = sqrt( ln(1 + sigma^2 / mu^2) )
    mu_sq = mu * mu
    sigma_sq = sigma * sigma
    mu_log = math.log(mu_sq / math.sqrt(mu_sq + sigma_sq))
    sigma_log = math.sqrt(math.log(1.0 + sigma_sq / mu_sq))

    AR = distribution.particle_aspect_ratio

    particles: List[Dict] = []
    max_attempts = n_particles * 50  # Hard limit to prevent infinite loop
    attempts = 0
    placed = 0

    while placed < n_particles and attempts < max_attempts:
        attempts += 1

        # Sample size from lognormal (reject particles < 5 um as dust)
        radius_um = random.lognormvariate(mu_log, sigma_log) / 2.0
        if radius_um < 2.5 or radius_um > L / 4.0:
            continue

        # Random position (uniform in RVE)
        x = random.uniform(radius_um, L - radius_um)
        y = random.uniform(radius_um, L - radius_um)
        z = random.uniform(radius_um, L - radius_um)

        # Random orientation (isotropic on the sphere)
        theta = math.acos(2.0 * random.random() - 1.0)  # polar angle
        phi = random.uniform(0.0, 2.0 * math.pi)        # azimuthal angle

        # Check overlap with existing particles (hard-sphere rejection)
        overlap = False
        for p in particles:
            dx = x - p["x"]
            dy = y - p["y"]
            dz = z - p["z"]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            min_dist = 1.15 * (radius_um + p["radius_um"])  # 15% clearance
            if dist < min_dist:
                overlap = True
                break

        if not overlap:
            particles.append({
                "x": x,
                "y": y,
                "z": z,
                "radius_um": radius_um,
                "radius_eq_um": radius_um,
                "aspect_ratio": AR,
                "theta": theta,
                "phi": phi,
            })
            placed += 1

    if placed < n_particles:
        print(
            f"Warning: Only placed {placed}/{n_particles} particles "
            f"(max attempts exceeded). RVE may have reached packing limit."
        )

    # Compute actual volume fraction
    total_particle_volume = sum(
        (4.0 / 3.0) * math.pi * p["radius_um"]**3 for p in particles
    )
    rve_volume = L**3
    actual_Vf = total_particle_volume / rve_volume

    # Annotate the first particle (or a placeholder) with the Vf info
    if particles:
        particles[0]["actual_Vf"] = actual_Vf

    return particles


# ============================================================================
#  STRESS CONCENTRATION (ESHELBY / GOODIER MODEL)
# ============================================================================

def _goodier_stress_concentration(
    particle_modulus_MPa: float,
    matrix_modulus_MPa: float,
    particle_poisson: float,
    matrix_poisson: float,
) -> float:
    """
    Compute the stress concentration factor at the interface between a
    spherical inclusion and an infinite matrix under remote uniaxial tension.

    Based on Goodier (1933) and improved by Eshelby (1957):
        K_t = 1 + (E_p - E_m) / (E_p + E_m) * f(nu_p, nu_m)

    For a spherical inclusion stiffer than the matrix (E_p > E_m), the
    maximum stress concentration occurs at the particle-matrix interface
    at the equator (theta = 90 deg from the loading direction).

    The closed-form expression is:
        K_t_max = 1 + (beta * (1 - 2*nu_m) + gamma) / (1 + beta * (1 + nu_m) / 2)

    where beta and gamma are functions of the modulus ratio and Poisson
    ratios (see Goodier 1933, eq. 38-45).

    Parameters
    ----------
    particle_modulus_MPa : float
        Young's modulus of the particle (MPa).
    matrix_modulus_MPa : float
        Young's modulus of the matrix (MPa).
    particle_poisson : float
        Poisson ratio of the particle.
    matrix_poisson : float
        Poisson ratio of the matrix.

    Returns
    -------
    Kt : float
        Maximum stress concentration factor at the particle-matrix
        interface (dimensionless). Values > 1 indicate stress elevation.
    """
    alpha = particle_modulus_MPa / matrix_modulus_MPa
    nu_m = matrix_poisson
    nu_p = particle_poisson

    # Goodier's solution for a spherical inclusion:
    # The peak hoop stress at the interface (equator) is:
    #   sigma_theta_max = 1 + K * (alpha - 1) / (alpha * A + B)
    #
    # where A, B, K are functions of Poisson ratios.
    # For simplicity and numerical robustness, we use the closed-form
    # expression from the Eshelby solution for a spherical inclusion.
    #
    # The stress concentration factor at the particle-matrix interface
    # for the max principal stress is:
    #   Kt = 1 + (alpha - 1) / (alpha + (3 - 2*nu_m) / (1 + nu_m))

    denom_alpha = alpha + (3.0 - 2.0 * nu_m) / (1.0 + nu_m)
    Kt = 1.0 + (alpha - 1.0) / denom_alpha

    # Cap at physically reasonable values (Kt > ~5 is rare for spherical
    # particles in composites; higher values suggest very extreme mismatch)
    return min(Kt, 5.0)


def estimate_local_stress_concentration(
    particle_field: List[Dict],
    applied_stress_MPa: float,
    matrix_modulus_MPa: float = 4500.0,
    matrix_poisson: float = 0.30,
    particle_modulus_MPa: float = 15000.0,
    particle_poisson: float = 0.20,
) -> Dict:
    """
    Estimate local stress concentrations around particles in the matrix
    using the Goodier/Eshelby model for spherical inclusions.

    For each particle, the local stress field is the superposition of:
      1. The remote applied stress
      2. The stress perturbation caused by the stiff particle
         (Eshelby inclusion theory)

    The perturbation is maximum at the particle-matrix interface where
    stress must be continuous across the boundary.

    Parameters
    ----------
    particle_field : list of dict
        Particle positions and sizes from generate_particle_field().
    applied_stress_MPa : float
        Remote applied tensile stress (MPa).
    matrix_modulus_MPa : float
        Young's modulus of the matrix (MPa). (Default: 4500.0)
    matrix_poisson : float
        Poisson ratio of the matrix. (Default: 0.30)
    particle_modulus_MPa : float
        Young's modulus of the particles (MPa). (Default: 15000.0)
    particle_poisson : float
        Poisson ratio of the particles. (Default: 0.20)

    Returns
    -------
    dict with keys:
        max_local_stress_MPa    : Maximum local stress at any particle
                                  interface (MPa)
        mean_local_stress_MPa   : Mean of the peak stresses across all
                                  particles (MPa)
        stress_concentration_Kt : Maximum stress concentration factor
                                  (dimensionless)
        histogram               : List of (Kt_bin, count) pairs for the
                                  distribution of SCF across particles
        n_particles_analyzed    : Number of particles in the field
    """
    if applied_stress_MPa <= 0.0:
        raise ValueError(
            f"Applied stress must be positive. Got {applied_stress_MPa} MPa."
        )
    if not particle_field:
        raise ValueError("Particle field is empty. Generate particles first.")

    # Compute the stress concentration factor for this material pair
    Kt = _goodier_stress_concentration(
        particle_modulus_MPa=particle_modulus_MPa,
        matrix_modulus_MPa=matrix_modulus_MPa,
        particle_poisson=particle_poisson,
        matrix_poisson=matrix_poisson,
    )

    # For each particle, the local peak stress at the interface depends
    # on the particle size and the Kt factor:
    #   sigma_local = applied_stress * Kt * f(size)
    # where f(size) is a small correction for particle size relative to
    # the RVE. For particles much smaller than the RVE (which is the
    # case here), f(size) ~ 1.0 (infinite matrix approximation).
    #
    # The actual stress field also depends on inter-particle spacing.
    # Closely spaced particles interact and can produce higher local
    # stresses. Here we apply a nearest-neighbor interaction correction:
    #   f_interaction = 1 + exp(-d_nn / d_mean)
    # where d_nn is the nearest-neighbor distance and d_mean is the mean
    # particle diameter.

    particle_stresses = []
    for i, p in enumerate(particle_field):
        # Nearest-neighbor distance
        r = p["radius_um"]
        nn_dist = float("inf")
        for j, q in enumerate(particle_field):
            if i == j:
                continue
            dx = p["x"] - q["x"]
            dy = p["y"] - q["y"]
            dz = p["z"] - q["z"]
            d = math.sqrt(dx * dx + dy * dy + dz * dz) - r - q["radius_um"]
            if d < nn_dist:
                nn_dist = max(d, 0.0)

        # Interaction factor for closely spaced particles
        d_mean = 2.0 * r
        f_interaction = 1.0 + math.exp(-nn_dist / d_mean) if d_mean > 0 else 1.0

        # Local peak stress at this particle's interface
        local_stress = applied_stress_MPa * Kt * f_interaction
        particle_stresses.append({
            "particle_index": i,
            "local_stress_MPa": local_stress,
            "Kt_effective": Kt * f_interaction,
            "nn_dist_um": nn_dist,
        })

    # Summary statistics
    all_stresses = [s["local_stress_MPa"] for s in particle_stresses]
    all_Kt = [s["Kt_effective"] for s in particle_stresses]
    max_stress = max(all_stresses)
    mean_stress = sum(all_stresses) / len(all_stresses)

    # Histogram of SCF values (10 bins)
    min_Kt = min(all_Kt)
    max_Kt = max(all_Kt)
    n_bins = 10
    bin_width = (max_Kt - min_Kt) / n_bins if max_Kt > min_Kt else 0.1
    histogram = []
    for b in range(n_bins):
        low = min_Kt + b * bin_width
        high = low + bin_width
        count = sum(1 for k in all_Kt if low <= k < high)
        if count > 0:
            histogram.append((round(low + bin_width / 2, 3), count))

    return {
        "max_local_stress_MPa": round(max_stress, 3),
        "mean_local_stress_MPa": round(mean_stress, 3),
        "stress_concentration_Kt": round(Kt, 4),
        "histogram": histogram,
        "n_particles_analyzed": len(particle_field),
    }


# ============================================================================
#  EFFECTIVE PROPERTIES (MORI-TANAKA HOMOGENIZATION)
# ============================================================================

def compute_effective_properties(
    particle_field: List[Dict],
    matrix_modulus_MPa: float,
    particle_modulus_MPa: float,
    matrix_poisson: float = 0.30,
    particle_poisson: float = 0.20,
) -> Dict:
    """
    Compute the effective elastic properties of the particle-reinforced
    composite using the Mori-Tanaka homogenization scheme.

    The Mori-Tanaka method (1973) estimates the average stress in the
    matrix of a composite containing many inclusions. It accounts for
    inclusion interactions in an approximate way, giving accurate results
    for moderate volume fractions (Vf < 0.4).

    The effective bulk modulus K_eff and shear modulus G_eff are given by
    (Benveniste 1987 formulation of Mori-Tanaka):
        K_eff = K_m + Vf * (K_p - K_m) * K_m / [K_m + (1 - Vf) * alpha * (K_p - K_m)]
        G_eff = G_m + Vf * (G_p - G_m) * G_m / [G_m + (1 - Vf) * beta * (G_p - G_m)]

    which can be rewritten as:
        K_eff / K_m = 1 + Vf * (K_p - K_m) / [K_m + (1 - Vf) * alpha * (K_p - K_m)]
        G_eff / G_m = 1 + Vf * (G_p - G_m) / [G_m + (1 - Vf) * beta * (G_p - G_m)]

    where alpha and beta are Eshelby's tensor components for spherical
    inclusions (Eshelby 1957). This formulation ensures that K_eff > K_m
    when K_p > K_m (stiff inclusions stiffen the composite) and K_eff = K_m
    when Vf = 0 (dilute limit).

    Parameters
    ----------
    particle_field : list of dict
        Particle positions and sizes. Used to compute the actual volume
        fraction from the generated field.
    matrix_modulus_MPa : float
        Young's modulus of the matrix (MPa).
    particle_modulus_MPa : float
        Young's modulus of the particles (MPa).
    matrix_poisson : float
        Poisson ratio of the matrix. (Default: 0.30)
    particle_poisson : float
        Poisson ratio of the particles. (Default: 0.20)

    Returns
    -------
    dict with keys:
        effective_modulus_MPa   : Effective Young's modulus (MPa)
        effective_poisson       : Effective Poisson ratio
        anisotropy_factor       : Ratio of Hashin-Shtrikman bounds
                                  (1.0 = isotropic; >1 = anisotropic)
        volume_fraction_actual  : Actual Vf from the particle field
        matrix_modulus_MPa      : Input matrix modulus (MPa)
        particle_modulus_MPa    : Input particle modulus (MPa)
    """
    # --- Compute actual volume fraction from particle field ---
    total_particle_volume = sum(
        (4.0 / 3.0) * math.pi * p["radius_um"]**3 for p in particle_field
    )

    # Estimate RVE size from max coordinate and max radius
    max_coord = 0.0
    for p in particle_field:
        half_span = max(p["x"], p["y"], p["z"]) + p["radius_um"]
        if half_span > max_coord:
            max_coord = half_span

    rve_size_um = 2.0 * max_coord  # symmetric RVE
    rve_volume = rve_size_um**3
    Vf = total_particle_volume / rve_volume if rve_volume > 0 else 0.0
    Vf = min(Vf, 0.6)  # Cap at maximum random packing

    # --- Matrix elastic constants ---
    K_m = matrix_modulus_MPa / (3.0 * (1.0 - 2.0 * matrix_poisson))
    G_m = matrix_modulus_MPa / (2.0 * (1.0 + matrix_poisson))

    # --- Particle elastic constants ---
    K_p = particle_modulus_MPa / (3.0 * (1.0 - 2.0 * particle_poisson))
    G_p = particle_modulus_MPa / (2.0 * (1.0 + particle_poisson))

    # --- Eshelby tensor components (spherical inclusion) ---
    # For a spherical inclusion in an isotropic matrix (Eshelby 1957):
    #   alpha = (1 + nu_m) / (3 * (1 - nu_m))
    #   beta  = (4 - 5 * nu_m) / (15 * (1 - nu_m))
    nu_m = matrix_poisson
    alpha = (1.0 + nu_m) / (3.0 * (1.0 - nu_m))
    beta = (4.0 - 5.0 * nu_m) / (15.0 * (1.0 - nu_m))

    # --- Mori-Tanaka effective moduli ---
    # The correct formula (Benveniste 1987, following Mori & Tanaka 1973):
    #   K_eff = K_m + Vf * (K_p - K_m) * K_m / [K_m + (1-Vf) * alpha * (K_p - K_m)]
    #   G_eff = G_m + Vf * (G_p - G_m) * G_m / [G_m + (1-Vf) * beta  * (G_p - G_m)]
    #
    # This can be rewritten as:
    #   K_eff / K_m = 1 + Vf * (K_p - K_m) / [K_m + (1-Vf) * alpha * (K_p - K_m)]
    # which ensures K_eff > K_m when K_p > K_m (stiff inclusions), and
    # K_eff = K_m when Vf = 0 (no inclusions), validating the limit checks.

    # Effective bulk modulus
    K_eff_den = K_m + (1.0 - Vf) * alpha * (K_p - K_m)
    if abs(K_eff_den) < 1e-15:
        K_eff = float("inf")
    else:
        K_eff = K_m * (1.0 + Vf * (K_p - K_m) / K_eff_den)

    # Effective shear modulus
    G_eff_den = G_m + (1.0 - Vf) * beta * (G_p - G_m)
    if abs(G_eff_den) < 1e-15:
        G_eff = float("inf")
    else:
        G_eff = G_m * (1.0 + Vf * (G_p - G_m) / G_eff_den)

    # --- Effective Young's modulus and Poisson ratio ---
    E_eff = 9.0 * K_eff * G_eff / (3.0 * K_eff + G_eff) if (K_eff > 0 and G_eff > 0) else 0.0
    nu_eff = (3.0 * K_eff - 2.0 * G_eff) / (2.0 * (3.0 * K_eff + G_eff)) if (K_eff > 0 and G_eff > 0) else 0.0

    # --- Anisotropy factor ---
    # Ratio of upper to lower Hashin-Shtrikman bounds as a measure of
    # potential anisotropy. For randomly oriented spherical particles,
    # the composite is isotropic and this factor approaches 1.0.
    # For aligned platelike particles, it can be significantly > 1.
    #
    # The bounds are:
    #   K_upper = K_m + Vf / (1/(K_p - K_m) + 3*(1-Vf)/(3*K_m + 4*G_m))
    #   K_lower = K_p + (1-Vf) / (1/(K_m - K_p) + 3*Vf/(3*K_p + 4*G_p))
    denom_upper = 1.0 / (K_p - K_m) + 3.0 * (1.0 - Vf) / (3.0 * K_m + 4.0 * G_m)
    K_HS_upper = K_m + Vf / denom_upper if abs(denom_upper) > 1e-15 else K_m

    denom_lower = 1.0 / (K_m - K_p) + 3.0 * Vf / (3.0 * K_p + 4.0 * G_p)
    K_HS_lower = K_p + (1.0 - Vf) / denom_lower if abs(denom_lower) > 1e-15 else K_p

    if abs(K_HS_lower) > 1e-15:
        anisotropy_factor = K_HS_upper / K_HS_lower
    else:
        anisotropy_factor = 1.0

    return {
        "effective_modulus_MPa": round(E_eff, 1),
        "effective_poisson": round(nu_eff, 4),
        "anisotropy_factor": round(anisotropy_factor, 4),
        "volume_fraction_actual": round(Vf, 4),
        "matrix_modulus_MPa": matrix_modulus_MPa,
        "particle_modulus_MPa": particle_modulus_MPa,
    }


# ============================================================================
#  PENETRATION PROFILE
# ============================================================================

def penetration_profile(
    blasting_pressure_bar: float,
    standoff_mm: float,
    substrate_porosity: float,
    particle_size_um: float = 100.0,
    n_layers: int = 20,
) -> Dict:
    """
    Model the penetration depth distribution of graphite particles into
    the porous paper mache substrate during blasting.

    The model treats the substrate as a porous medium and particles as
    projectiles that embed at depths determined by:

      1. Kinetic energy at impact (function of pressure and standoff)
      2. Substrate porosity (higher porosity -> deeper penetration)
      3. Particle size (larger particles carry more momentum)

    The depth profile follows an approximately exponential decay:
        C(z) = C_0 * exp(-z / lambda)

    where:
        C(z)   = particle concentration at depth z
        C_0    = surface concentration
        lambda = characteristic penetration depth

    Parameters
    ----------
    blasting_pressure_bar : float
        Blasting pressure (bar).
    standoff_mm : float
        Standoff distance (mm).
    substrate_porosity : float
        Porosity of the paper mache substrate (0.0 to 1.0).
        Paper mache typically 0.3-0.6.
    particle_size_um : float
        Mean particle size (um). (Default: 100.0)
    n_layers : int
        Number of depth layers in the profile. (Default: 20)

    Returns
    -------
    dict with keys:
        mean_depth_um           : Mean penetration depth (um)
        characteristic_depth_um : Characteristic decay length lambda (um)
        max_depth_um            : Maximum penetration depth (um)
        depth_profile           : List of (depth_um, concentration) pairs
        surface_concentration   : Relative concentration at z=0
        penetration_efficiency  : Fraction of incident particles that embed
    """
    if blasting_pressure_bar <= 0.0:
        raise ValueError(
            f"Blasting pressure must be positive. Got {blasting_pressure_bar} bar."
        )
    if standoff_mm <= 0.0:
        raise ValueError(
            f"Standoff must be positive. Got {standoff_mm} mm."
        )
    if not (0.0 <= substrate_porosity <= 1.0):
        raise ValueError(
            f"Substrate porosity must be in [0, 1]. Got {substrate_porosity}."
        )
    if n_layers < 2:
        raise ValueError(
            f"Number of layers must be >= 2. Got {n_layers}."
        )

    # --- Characteristic decay length lambda ---
    # The decay length depends on:
    #   - Porosity: more pores -> deeper penetration
    #   - Particle size: larger particles -> deeper penetration
    #     (but also higher chance of bridging pores)
    #   - Pressure: higher pressure -> deeper initial embedment
    #
    # Empirical model:
    #   lambda = lambda_0 * f_porosity * f_pressure * f_standoff
    #
    # where:
    #   lambda_0     = 30 um (baseline decay length for this system)
    #   f_porosity   = 1 + 2 * porosity
    #   f_pressure   = (p / p_ref)^0.5   (KE ~ p, depth ~ sqrt(KE) ~ sqrt(p))
    #   f_standoff   = max(0.5, 1 - (s - s_opt)^2 / s_crit^2)

    lambda_0 = 30.0  # um (baseline)
    p_ref = 2.0      # bar (reference pressure)
    s_opt = 150.0    # mm (optimal standoff)
    s_crit = 200.0   # mm

    f_porosity = 1.0 + 2.0 * substrate_porosity
    f_pressure = math.sqrt(blasting_pressure_bar / p_ref) if blasting_pressure_bar > 0 else 0.5
    f_standoff = max(0.3, 1.0 - ((standoff_mm - s_opt) / s_crit) ** 2)

    lambda_char = lambda_0 * f_porosity * f_pressure * f_standoff

    # --- Maximum depth ---
    # Set at 5 * lambda (where C(z) < 1% of surface concentration)
    max_depth_um = 5.0 * lambda_char

    # --- Mean depth ---
    # For exponential decay C(z) ~ exp(-z/lambda), the mean depth is lambda.
    mean_depth_um = lambda_char

    # --- Penetration efficiency ---
    # Fraction of incident particles that actually embed (vs. bouncing off
    # or eroding the surface). High pressure + high porosity = more embedment.
    # Low standoff = particles may erode rather than embed.
    efficiency_base = 0.4  # baseline
    efficiency = efficiency_base + 0.3 * substrate_porosity + 0.15 * math.sqrt(
        blasting_pressure_bar / p_ref
    ) - 0.1 * max(0.0, 1.0 - standoff_mm / 100.0)
    efficiency = max(0.1, min(efficiency, 0.95))

    # --- Depth profile ---
    depth_step = max_depth_um / n_layers
    depth_profile = []
    for layer in range(n_layers + 1):
        z = layer * depth_step
        concentration = math.exp(-z / lambda_char) if lambda_char > 0 else 0.0
        depth_profile.append((round(z, 1), round(concentration, 4)))

    return {
        "mean_depth_um": round(mean_depth_um, 1),
        "characteristic_depth_um": round(lambda_char, 1),
        "max_depth_um": round(max_depth_um, 1),
        "depth_profile": depth_profile,
        "surface_concentration": 1.0,
        "penetration_efficiency": round(efficiency, 3),
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

    # 1. Create the particle distribution with default parameters
    dist = ParticleDistribution()

    # 2. Generate 1000 particles
    print("Generating 1000 particles (seed=42 for reproducibility)...")
    particles = generate_particle_field(
        n_particles=1000,
        distribution=dist,
        seed=42,
    )
    print(f"  Placed: {len(particles)} particles")

    # Compute actual Vf from generated field
    total_vol = sum(
        (4.0 / 3.0) * math.pi * p["radius_um"]**3 for p in particles
    )
    L = dist.rve_size_um
    actual_Vf = total_vol / (L**3)

    # 3. Compute effective properties
    effective = compute_effective_properties(
        particles,
        matrix_modulus_MPa=4500.0,   # paper mache
        particle_modulus_MPa=15000.0, # graphite flake
    )

    # 4. Estimate stress concentration for 12.5 MPa applied stress
    sc_result = estimate_local_stress_concentration(
        particles,
        applied_stress_MPa=12.5,
    )

    # 5. Compute penetration profile for 4.0 bar blasting
    penetration = penetration_profile(
        blasting_pressure_bar=4.0,
        standoff_mm=150.0,
        substrate_porosity=0.45,  # typical paper mache
    )

    # --- PRINT REPORT ---

    print(_format_header("GRAPHITE PARTICLE DISTRIBUTION ANALYSIS"))
    print(f"  Module:      micro-particle / particle_distribution_model.py")
    print(f"  System:      Graphite flakes in paper mache coating")
    print()

    # Particle distribution parameters
    print(_format_header("1. PARTICLE DISTRIBUTION PARAMETERS"))
    print(f"  Grade:                       {dist.grade}")
    print(f"  Mean particle size:          {dist.particle_size_um:.1f} um")
    print(f"  Std dev (lognormal):         {dist.particle_size_std_um:.1f} um")
    print(f"  Target volume fraction:      {dist.volume_fraction:.2f}")
    print(f"  Actual volume fraction:      {actual_Vf:.4f} ({len(particles)} particles)")
    print(f"  Aspect ratio (diam/thick):   {dist.particle_aspect_ratio:.1f}")
    print(f"  RVE size:                    {dist.rve_size_um:.0f} um")
    print()

    # Size statistics
    radii = [p["radius_um"] for p in particles]
    min_r = min(radii)
    max_r = max(radii)
    mean_r = sum(radii) / len(radii) if radii else 0.0
    print(f"  Particle radius range:       {min_r:.1f} - {max_r:.1f} um")
    print(f"  Mean radius:                 {mean_r:.2f} um (equiv. diameter: {2*mean_r:.2f} um)")
    print()

    # Effective properties
    print(_format_header("2. EFFECTIVE PROPERTIES (Mori-Tanaka Homogenization)"))
    print(f"  Matrix modulus (E_m):        {effective['matrix_modulus_MPa']:.0f} MPa")
    print(f"  Particle modulus (E_p):      {effective['particle_modulus_MPa']:.0f} MPa")
    print(f"  Volume fraction (actual):    {effective['volume_fraction_actual']:.4f}")
    print(f"  Effective modulus (E_eff):   {effective['effective_modulus_MPa']:.1f} MPa")
    print(f"  Effective Poisson ratio:     {effective['effective_poisson']:.4f}")
    print(f"  Anisotropy factor:           {effective['anisotropy_factor']:.4f}")
    print(f"  Reference: Eshelby (1957), Mori & Tanaka (1973)")
    print()

    # Stress concentration
    print(_format_header("3. LOCAL STRESS CONCENTRATION (Goodier/Eshelby)"))
    print(f"  Applied stress:              12.5 MPa")
    print(f"  Max SCF (Kt):                {sc_result['stress_concentration_Kt']:.4f}")
    print(f"  Max local stress:            {sc_result['max_local_stress_MPa']:.3f} MPa")
    print(f"  Mean local stress:           {sc_result['mean_local_stress_MPa']:.3f} MPa")
    print(f"  Particles analyzed:          {sc_result['n_particles_analyzed']}")
    print(f"  SCF histogram (Kt):")
    for bin_center, count in sc_result["histogram"]:
        bar = "#" * max(1, count // 5)
        print(f"    Kt ~ {bin_center:.3f}: {count:4d} particles  {bar}")
    print()

    # Penetration profile
    print(_format_header("4. PENETRATION PROFILE (Blasting into Porous Paper Mache)"))
    print(f"  Blasting pressure:           4.0 bar")
    print(f"  Standoff:                    150 mm")
    print(f"  Substrate porosity:          0.45")
    print(f"  Mean penetration depth:      {penetration['mean_depth_um']:.1f} um")
    print(f"  Characteristic depth (lambda): {penetration['characteristic_depth_um']:.1f} um")
    print(f"  Max penetration depth:       {penetration['max_depth_um']:.1f} um")
    print(f"  Penetration efficiency:      {penetration['penetration_efficiency']:.3f}")
    print(f"  Depth profile (z, C/C_0):")
    for z, conc in penetration["depth_profile"]:
        bar = "#" * max(1, int(conc * 80))
        print(f"    {z:6.1f} um  {conc:.4f}  {bar}")
    print()

    # Conclusion
    print(_format_header("5. CONCLUSION"))
    print(f"  The micro-scale analysis of the graphite particle coating")
    print(f"  indicates:")
    print(f"    - Effective modulus: {effective['effective_modulus_MPa']:.0f} MPa")
    print(f"      (stiffening from {effective['matrix_modulus_MPa']:.0f} MPa base)")
    print(f"    - Max local stress concentration at particle interfaces:")
    print(f"      {sc_result['max_local_stress_MPa']:.1f} MPa (Kt = {sc_result['stress_concentration_Kt']:.3f})")
    print(f"    - Particles penetrate {penetration['mean_depth_um']:.0f} um on average")
    print(f"      into the paper mache substrate")
    print(f"  These results feed into the meso-scale interface model and")
    print(f"  the FEM structural analysis at the macro scale.")
    print()


if __name__ == "__main__":
    _run_analysis()
