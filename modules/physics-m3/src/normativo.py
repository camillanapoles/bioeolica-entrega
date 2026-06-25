#!/usr/bin/env python3
"""
Standards Compliance Checker — Normative Engineering for Wind Energy Composites.

Validates materials and structural designs against international standards:
  - ISO 61400-1 (wind turbine design — general)
  - IEC 61400-2 (small wind turbines)
  - ASTM D790 (flexural properties of unreinforced/ reinforced plastics)
  - ASTM D3039 (tensile properties of polymer matrix composites)
  - ASTM D3410 (compressive properties of polymer matrix composites)
  - ABNT NBR 6123 (wind loads for buildings)

Functions and a StandardsCheck class to evaluate pass/fail against each
standard's acceptance criteria.

Usage:
    from normativo import StandardsCheck, check_astm_d790, check_iec_61400

    checker = StandardsCheck(
        material="paper_mache_pva",
        E_modulus_GPa=2.5, tensile_MPa=30, flexural_MPa=25,
        density_kgm3=850, thickness_mm=5,
    )

    # Check flexure against ASTM D790
    flex = checker.check_astm_d790(
        span_mm=80, width_mm=25, max_strain=0.05
    )

    # Check wind turbine against IEC 61400-2
    iec = checker.check_iec_61400(
        rotor_diameter_m=2.5, rated_power_W=500,
        wind_zone_avg_ms=6.0, safety_class="II"
    )

    # Check Brazilian wind loads
    nbr = checker.check_nbr_6123(
        height_m=10, terrain_category="B", basic_velocity_ms=35
    )

    print(checker.summary())
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  MATERIAL ACCEPTANCE DATABASE
# ═══════════════════════════════════════════════════════════════

# Typical minimum acceptable values per standard for composites
STANDARD_LIMITS = {
    "astm_d790": {
        "min_flexural_modulus_GPa": 1.0,
        "min_flexural_strength_MPa": 10.0,
        "span_to_thickness_ratio": 16,
        "max_strain_at_break": 0.05,
    },
    "astm_d3039": {
        "min_tensile_modulus_GPa": 1.0,
        "min_tensile_strength_MPa": 10.0,
        "max_elongation_pct_std": 1.5,
        "min_specimen_width_mm": 10.0,
    },
    "astm_d3410": {
        "min_compressive_modulus_GPa": 1.0,
        "min_compressive_strength_MPa": 8.0,
        "max_gage_length_mm": 30.0,
    },
    "iec_61400_2": {
        "min_rotor_diameter_m": 0.5,
        "max_rotor_diameter_m": 16.0,
        "min_tower_height_m": 3.0,
        "min_blade_tip_clearance_mm": 50.0,
        "max_annual_avg_wind_ms_class_I": 10.0,
        "max_annual_avg_wind_ms_class_II": 8.5,
        "max_annual_avg_wind_ms_class_III": 7.5,
        "reference_wind_speed_class_I_ms": 50.0,
        "reference_wind_speed_class_II_ms": 42.5,
        "reference_wind_speed_class_III_ms": 37.5,
        "safety_factor_ultimate": 1.35,
        "safety_factor_fatigue": 1.25,
    },
    "iso_61400_1": {
        "min_tower_height_m": 20.0,
        "safety_class_normal": 1.0,
        "safety_class_high": 1.35,
        "max_deflection_at_tip_pct": 1.0,
    },
    "nbr_6123": {
        "min_height_m": 5.0,
        "max_height_m": 100.0,
        "gust_factor_range": (1.5, 2.5),
        "min_dynamic_pressure_Pa": 200.0,
    },
}


# ═══════════════════════════════════════════════════════════════
#  STANDALONE CHECK FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def check_astm_d790(
    flexural_modulus_GPa: float,
    flexural_strength_MPa: float,
    span_mm: float,
    thickness_mm: float,
    width_mm: float,
    max_strain: float = 0.05,
) -> Dict:
    """Check flexural properties against ASTM D790 criteria.

    Evaluates 3-point bending configuration: span-to-thickness ratio,
    flexural modulus, flexural strength, and maximum strain.

    Args:
        flexural_modulus_GPa: Elastic modulus in flexure (GPa)
        flexural_strength_MPa: Maximum flexural stress (MPa)
        span_mm: Support span length (mm)
        thickness_mm: Specimen thickness (mm)
        width_mm: Specimen width (mm)
        max_strain: Maximum strain at outer fibre at break

    Returns:
        Dict with pass/fail for each criterion and overall status.
    """
    limits = STANDARD_LIMITS["astm_d790"]
    span_ratio = span_mm / thickness_mm if thickness_mm > 0 else 0.0

    checks = {
        "span_to_thickness_ratio": {
            "value": round(span_ratio, 1),
            "required": f">= {limits['span_to_thickness_ratio']}",
            "passed": span_ratio >= limits["span_to_thickness_ratio"],
        },
        "flexural_modulus": {
            "value": flexural_modulus_GPa,
            "required": f">= {limits['min_flexural_modulus_GPa']} GPa",
            "passed": flexural_modulus_GPa >= limits["min_flexural_modulus_GPa"],
        },
        "flexural_strength": {
            "value": flexural_strength_MPa,
            "required": f">= {limits['min_flexural_strength_MPa']} MPa",
            "passed": flexural_strength_MPa >= limits["min_flexural_strength_MPa"],
        },
        "max_strain": {
            "value": round(max_strain, 4),
            "required": f"<= {limits['max_strain_at_break']}",
            "passed": max_strain <= limits["max_strain_at_break"],
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "ASTM D790 — Flexural Properties",
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def check_astm_d3039(
    tensile_modulus_GPa: float,
    tensile_strength_MPa: float,
    elongation_pct: float,
    width_mm: float,
    thickness_mm: float,
) -> Dict:
    """Check tensile properties against ASTM D3039 criteria.

    Args:
        tensile_modulus_GPa: Tensile modulus (GPa)
        tensile_strength_MPa: Ultimate tensile strength (MPa)
        elongation_pct: Elongation at break (%)
        width_mm: Specimen width (mm)
        thickness_mm: Specimen thickness (mm)

    Returns:
        Dict with pass/fail per criterion.
    """
    limits = STANDARD_LIMITS["astm_d3039"]
    cross_section = width_mm * thickness_mm

    checks = {
        "tensile_modulus": {
            "value": tensile_modulus_GPa,
            "required": f">= {limits['min_tensile_modulus_GPa']} GPa",
            "passed": tensile_modulus_GPa >= limits["min_tensile_modulus_GPa"],
        },
        "tensile_strength": {
            "value": tensile_strength_MPa,
            "required": f">= {limits['min_tensile_strength_MPa']} MPa",
            "passed": tensile_strength_MPa >= limits["min_tensile_strength_MPa"],
        },
        "elongation": {
            "value": elongation_pct,
            "required": f"<= {limits['max_elongation_pct_std']}%",
            "passed": elongation_pct <= limits["max_elongation_pct_std"],
        },
        "specimen_width": {
            "value": width_mm,
            "required": f">= {limits['min_specimen_width_mm']} mm",
            "passed": width_mm >= limits["min_specimen_width_mm"],
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "ASTM D3039 — Tensile Properties",
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def check_astm_d3410(
    compressive_modulus_GPa: float,
    compressive_strength_MPa: float,
    gage_length_mm: float,
) -> Dict:
    """Check compressive properties against ASTM D3410 criteria.

    Args:
        compressive_modulus_GPa: Compressive modulus (GPa)
        compressive_strength_MPa: Ultimate compressive strength (MPa)
        gage_length_mm: Gage length for compression test (mm)

    Returns:
        Dict with pass/fail per criterion.
    """
    limits = STANDARD_LIMITS["astm_d3410"]

    checks = {
        "compressive_modulus": {
            "value": compressive_modulus_GPa,
            "required": f">= {limits['min_compressive_modulus_GPa']} GPa",
            "passed": compressive_modulus_GPa >= limits["min_compressive_modulus_GPa"],
        },
        "compressive_strength": {
            "value": compressive_strength_MPa,
            "required": f">= {limits['min_compressive_strength_MPa']} MPa",
            "passed": compressive_strength_MPa >= limits["min_compressive_strength_MPa"],
        },
        "gage_length": {
            "value": gage_length_mm,
            "required": f"<= {limits['max_gage_length_mm']} mm",
            "passed": gage_length_mm <= limits["max_gage_length_mm"],
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "ASTM D3410 — Compressive Properties",
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def check_iec_61400(
    rotor_diameter_m: float,
    rated_power_W: float,
    annual_avg_wind_ms: float,
    safety_class: str = "III",
    blade_tip_clearance_mm: float = 60.0,
    tower_height_m: float = 5.0,
) -> Dict:
    """Check small wind turbine design against IEC 61400-2.

    Validates rotor dimensions, wind class compatibility, safety factors,
    and geometric constraints per the IEC 61400-2 standard for small
    wind turbines (rotor area < 200 m^2).

    Args:
        rotor_diameter_m: Rotor diameter (m)
        rated_power_W: Rated electrical power (W)
        annual_avg_wind_ms: Annual average wind speed (m/s)
        safety_class: Wind class ('I', 'II', or 'III')
        blade_tip_clearance_mm: Blade tip to tower clearance (mm)
        tower_height_m: Tower height (m)

    Returns:
        Dict with pass/fail per criterion.
    """
    limits = STANDARD_LIMITS["iec_61400_2"]
    class_upper = safety_class.upper()

    if class_upper not in ("I", "II", "III"):
        return {
            "standard": "IEC 61400-2",
            "overall": "FAIL",
            "error": f"Unknown safety class '{safety_class}'. Use I, II, or III.",
        }

    max_wind_key = f"max_annual_avg_wind_ms_class_{class_upper}"
    max_wind = limits.get(max_wind_key, 7.5)
    ref_wind = limits.get(
        f"reference_wind_speed_class_{class_upper}_ms", 37.5
    )

    rotor_area = np.pi * (rotor_diameter_m / 2) ** 2

    checks = {
        "rotor_diameter": {
            "value": rotor_diameter_m,
            "required": f"{limits['min_rotor_diameter_m']}–{limits['max_rotor_diameter_m']} m",
            "passed": limits["min_rotor_diameter_m"] <= rotor_diameter_m <= limits["max_rotor_diameter_m"],
        },
        "wind_class_compatibility": {
            "value": annual_avg_wind_ms,
            "required": f"<= {max_wind} m/s for class {class_upper}",
            "passed": annual_avg_wind_ms <= max_wind,
        },
        "reference_wind_speed": {
            "value": ref_wind,
            "required": f"class {class_upper} design reference",
            "passed": True,
        },
        "tower_height": {
            "value": tower_height_m,
            "required": f">= {limits['min_tower_height_m']} m",
            "passed": tower_height_m >= limits["min_tower_height_m"],
        },
        "blade_tip_clearance": {
            "value": blade_tip_clearance_mm,
            "required": f">= {limits['min_blade_tip_clearance_mm']} mm",
            "passed": blade_tip_clearance_mm >= limits["min_blade_tip_clearance_mm"],
        },
        "power_density": {
            "value": round(rated_power_W / rotor_area, 1),
            "required": "power density within typical range",
            "passed": rotor_area > 0.5,
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "IEC 61400-2 — Small Wind Turbines",
        "class": class_upper,
        "reference_wind_speed_ms": ref_wind,
        "rotor_area_m2": round(rotor_area, 2),
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def check_iso_61400(
    tower_height_m: float,
    max_blade_deflection_m: float,
    blade_length_m: float,
    safety_class: str = "normal",
    annual_avg_wind_ms: float = 8.5,
) -> Dict:
    """Check wind turbine design against ISO 61400-1 general requirements.

    Args:
        tower_height_m: Hub height (m)
        max_blade_deflection_m: Maximum blade tip deflection (m)
        blade_length_m: Blade length (m)
        safety_class: 'normal' or 'high'
        annual_avg_wind_ms: Annual average wind speed (m/s)

    Returns:
        Dict with pass/fail per criterion.
    """
    limits = STANDARD_LIMITS["iso_61400_1"]
    deflection_pct = (
        (max_blade_deflection_m / blade_length_m) * 100
        if blade_length_m > 0 else 0.0
    )
    sf = limits["safety_class_high"] if safety_class == "high" else limits["safety_class_normal"]

    checks = {
        "tower_height": {
            "value": tower_height_m,
            "required": f">= {limits['min_tower_height_m']} m",
            "passed": tower_height_m >= limits["min_tower_height_m"],
        },
        "tip_deflection": {
            "value": f"{round(deflection_pct, 2)}%",
            "required": f"<= {limits['max_deflection_at_tip_pct']}%",
            "passed": deflection_pct <= limits["max_deflection_at_tip_pct"],
        },
        "safety_factor": {
            "value": sf,
            "required": f"1.00 (normal) or 1.35 (high)",
            "passed": sf >= 1.0,
        },
        "wind_regime": {
            "value": annual_avg_wind_ms,
            "required": "IEC class compatible",
            "passed": annual_avg_wind_ms <= 10.0,
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "ISO 61400-1 — Wind Turbine Design",
        "safety_class": safety_class,
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def check_nbr_6123(
    height_m: float,
    terrain_category: str,
    basic_velocity_ms: float,
    gust_factor: float = 2.0,
    dynamic_pressure_Pa: Optional[float] = None,
) -> Dict:
    """Check wind loads against ABNT NBR 6123.

    Evaluates wind load parameters for Brazilian construction standards:
    terrain category, gust factor, basic wind velocity, and dynamic
    pressure on structures.

    Args:
        height_m: Building/structure height (m)
        terrain_category: Terrain category ('A' through 'E')
        basic_velocity_ms: Basic wind velocity V0 (m/s)
        gust_factor: Gust factor S2 (typically 1.5–2.5)
        dynamic_pressure_Pa: Dynamic pressure q (Pa). If None, computed.

    Returns:
        Dict with pass/fail per criterion.
    """
    limits = STANDARD_LIMITS["nbr_6123"]

    terrain_roughness = {
        "A": 0.005,   # Open sea, flat coastal plain
        "B": 0.05,    # Open terrain, few obstacles
        "C": 0.30,    # Suburban, scattered obstacles
        "D": 0.70,    # Urban, many obstacles
        "E": 1.00,    # Dense urban, forest
    }

    category_upper = terrain_category.upper()
    if category_upper not in terrain_roughness:
        return {
            "standard": "ABNT NBR 6123",
            "overall": "FAIL",
            "error": f"Unknown terrain '{terrain_category}'. Use A–E.",
        }

    S1 = 1.0  # Topography factor (flat terrain)
    S3 = 1.0  # Usage factor (standard group)

    # Characteristic wind speed Vk = V0 * S1 * S2 * S3
    S2 = gust_factor
    Vk = basic_velocity_ms * S1 * S2 * S3

    if dynamic_pressure_Pa is None:
        dynamic_pressure_Pa = 0.613 * Vk ** 2

    checks = {
        "height": {
            "value": height_m,
            "required": f"{limits['min_height_m']}–{limits['max_height_m']} m",
            "passed": limits["min_height_m"] <= height_m <= limits["max_height_m"],
        },
        "gust_factor": {
            "value": gust_factor,
            "required": f"{limits['gust_factor_range']}",
            "passed": limits["gust_factor_range"][0] <= gust_factor <= limits["gust_factor_range"][1],
        },
        "basic_velocity": {
            "value": basic_velocity_ms,
            "required": ">= 25 m/s (Brazilian standard min)",
            "passed": basic_velocity_ms >= 25.0,
        },
        "dynamic_pressure": {
            "value": round(dynamic_pressure_Pa, 1),
            "required": f">= {limits['min_dynamic_pressure_Pa']} Pa",
            "passed": dynamic_pressure_Pa >= limits["min_dynamic_pressure_Pa"],
        },
        "characteristic_wind": {
            "value": round(Vk, 2),
            "required": "computed from V0 * S1 * S2 * S3",
            "passed": Vk > 0,
        },
    }

    all_passed = all(c["passed"] for c in checks.values())

    return {
        "standard": "ABNT NBR 6123 — Wind Loads",
        "terrain": category_upper,
        "Vk_ms": round(Vk, 2),
        "dynamic_pressure_Pa": round(dynamic_pressure_Pa, 1),
        "overall": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


# ═══════════════════════════════════════════════════════════════
#  STANDARDSCHECK CLASS
# ═══════════════════════════════════════════════════════════════

@dataclass
class StandardsCheck:
    """Composite material standards compliance checker.

    Stores material properties and runs standard-specific checks.
    Accumulates results for consolidated summary.

    Args:
        material: Material name
        E_modulus_GPa: Elastic modulus (GPa)
        tensile_MPa: Tensile strength (MPa)
        flexural_MPa: Flexural strength (MPa)
        compressive_MPa: Compressive strength (MPa)
        density_kgm3: Density (kg/m^3)
        thickness_mm: Default thickness (mm)
    """
    material: str
    E_modulus_GPa: float = 1.0
    tensile_MPa: float = 10.0
    flexural_MPa: float = 10.0
    compressive_MPa: float = 8.0
    density_kgm3: float = 1000.0
    thickness_mm: float = 5.0
    _results: List[Dict] = field(default_factory=list)

    def check_astm_d790(
        self,
        span_mm: float = 80.0,
        width_mm: float = 25.0,
        max_strain: float = 0.05,
    ) -> Dict:
        """Run ASTM D790 flexure check with stored material properties.

        Args:
            span_mm: Support span length (mm)
            width_mm: Specimen width (mm)
            max_strain: Maximum strain at break

        Returns:
            Dict with check results, appended to internal results list.
        """
        result = check_astm_d790(
            flexural_modulus_GPa=self.E_modulus_GPa,
            flexural_strength_MPa=self.flexural_MPa,
            span_mm=span_mm,
            thickness_mm=self.thickness_mm,
            width_mm=width_mm,
            max_strain=max_strain,
        )
        self._results.append(result)
        return result

    def check_astm_d3039(
        self,
        width_mm: float = 25.0,
        elongation_pct: float = 1.5,
    ) -> Dict:
        """Run ASTM D3039 tensile check with stored material properties.

        Args:
            width_mm: Specimen width (mm)
            elongation_pct: Elongation at break (%)

        Returns:
            Dict with check results.
        """
        result = check_astm_d3039(
            tensile_modulus_GPa=self.E_modulus_GPa,
            tensile_strength_MPa=self.tensile_MPa,
            elongation_pct=elongation_pct,
            width_mm=width_mm,
            thickness_mm=self.thickness_mm,
        )
        self._results.append(result)
        return result

    def check_astm_d3410(
        self,
        gage_length_mm: float = 25.0,
    ) -> Dict:
        """Run ASTM D3410 compression check with stored material properties.

        Args:
            gage_length_mm: Compression gage length (mm)

        Returns:
            Dict with check results.
        """
        result = check_astm_d3410(
            compressive_modulus_GPa=self.E_modulus_GPa,
            compressive_strength_MPa=self.compressive_MPa,
            gage_length_mm=gage_length_mm,
        )
        self._results.append(result)
        return result

    def check_iec_61400(
        self,
        rotor_diameter_m: float = 2.5,
        rated_power_W: float = 500.0,
        wind_zone_avg_ms: float = 6.0,
        safety_class: str = "III",
        tower_height_m: float = 5.0,
    ) -> Dict:
        """Run IEC 61400-2 small wind turbine check.

        Args:
            rotor_diameter_m: Rotor diameter (m)
            rated_power_W: Rated electrical power (W)
            wind_zone_avg_ms: Annual average wind speed (m/s)
            safety_class: Wind class I/II/III
            tower_height_m: Tower height (m)

        Returns:
            Dict with check results.
        """
        result = check_iec_61400(
            rotor_diameter_m=rotor_diameter_m,
            rated_power_W=rated_power_W,
            annual_avg_wind_ms=wind_zone_avg_ms,
            safety_class=safety_class,
            tower_height_m=tower_height_m,
        )
        self._results.append(result)
        return result

    def check_iso_61400(
        self,
        tower_height_m: float = 30.0,
        blade_length_m: float = 10.0,
        max_deflection_m: float = 0.05,
        safety_class: str = "normal",
    ) -> Dict:
        """Run ISO 61400-1 wind turbine design check.

        Args:
            tower_height_m: Hub height (m)
            blade_length_m: Blade length (m)
            max_deflection_m: Maximum tip deflection (m)
            safety_class: 'normal' or 'high'

        Returns:
            Dict with check results.
        """
        result = check_iso_61400(
            tower_height_m=tower_height_m,
            max_blade_deflection_m=max_deflection_m,
            blade_length_m=blade_length_m,
            safety_class=safety_class,
        )
        self._results.append(result)
        return result

    def check_nbr_6123(
        self,
        height_m: float = 10.0,
        terrain_category: str = "B",
        basic_velocity_ms: float = 35.0,
        gust_factor: float = 2.0,
    ) -> Dict:
        """Run ABNT NBR 6123 wind load check.

        Args:
            height_m: Structure height (m)
            terrain_category: Terrain category A–E
            basic_velocity_ms: Basic wind velocity (m/s)
            gust_factor: Gust factor S2

        Returns:
            Dict with check results.
        """
        result = check_nbr_6123(
            height_m=height_m,
            terrain_category=terrain_category,
            basic_velocity_ms=basic_velocity_ms,
            gust_factor=gust_factor,
        )
        self._results.append(result)
        return result

    def summary(self) -> Dict:
        """Consolidated summary of all checks performed.

        Returns:
            Dict with overall compliance status and per-standard results.
        """
        passed = sum(1 for r in self._results if r.get("overall") == "PASS")
        failed = sum(1 for r in self._results if r.get("overall") == "FAIL")
        total = len(self._results)

        return {
            "material": self.material,
            "checks_performed": total,
            "passed": passed,
            "failed": failed,
            "compliance_score_pct": round((passed / total) * 100, 1) if total > 0 else 0.0,
            "overall": "PASS" if failed == 0 else "PARTIAL" if passed > 0 else "FAIL",
            "results": self._results,
        }


def run_all_checks(
    E_modulus_GPa: float = 2.5,
    tensile_MPa: float = 30.0,
    flexural_MPa: float = 25.0,
    compressive_MPa: float = 15.0,
    density_kgm3: float = 850.0,
    thickness_mm: float = 5.0,
    material: str = "generic_composite",
) -> Dict:
    """Run all standard checks on a single material in one call.

    Convenience function that creates a StandardsCheck, runs every
    available check with default parameters, and returns the summary.

    Args:
        E_modulus_GPa: Elastic modulus (GPa)
        tensile_MPa: Tensile strength (MPa)
        flexural_MPa: Flexural strength (MPa)
        compressive_MPa: Compressive strength (MPa)
        density_kgm3: Density (kg/m^3)
        thickness_mm: Specimen thickness (mm)
        material: Material name

    Returns:
        Consolidated summary dict.
    """
    sc = StandardsCheck(
        material=material,
        E_modulus_GPa=E_modulus_GPa,
        tensile_MPa=tensile_MPa,
        flexural_MPa=flexural_MPa,
        compressive_MPa=compressive_MPa,
        density_kgm3=density_kgm3,
        thickness_mm=thickness_mm,
    )
    sc.check_astm_d790()
    sc.check_astm_d3039()
    sc.check_astm_d3410()
    sc.check_iec_61400()
    sc.check_iso_61400()
    sc.check_nbr_6123()
    return sc.summary()
