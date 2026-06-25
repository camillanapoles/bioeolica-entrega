#!/usr/bin/env python3
"""
Agent Context Engine — KDI Socratic Context Validation.

Implements the 8 KDI context prompts as runtime validation checks
for the MECH-ELECTRO-MATERIALS-SCIENTIST agent workflow:
  - Context layers: domain, complexity, constraints, standards, data,
    optimization, time/cost, sustainability
  - Auto-instruction via Socratic questioning
  - Complexity assessment with quantitative scoring

Usage:
    from context_engine import ContextEngine, assess_complexity

    engine = ContextEngine(problem="Optimize blade for 3kW wind turbine")
    engine.add_domain("mecanica")
    engine.add_domain("fluidos")
    engine.add_domain("materiais")

    engine.set_constraint("max_mass_kg=15")
    engine.set_constraint("min_lifetime_years=20")

    report = engine.validate_context()
    prompts = engine.generate_prompts()
    complexity = engine.assess_complexity()

    for p in prompts:
        print(f"[{p['domain']}] {p['question']}")
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
#  KDI SOCRATIC PROMPTS — The 8 Context Questions
# ═══════════════════════════════════════════════════════════════

SOCRATIC_PROMPTS = {
    "dominant_physics": {
        "question": "Qual e o fenomeno fisico dominante neste problema?",
        "english": "What is the dominant physical phenomenon in this problem?",
        "prompt": "Identify the governing physical phenomenon — mechanical, fluid, thermal, electromagnetic, or coupled.",
        "validation_type": "domain_identification",
    },
    "governing_equations": {
        "question": "Quais equacoes governam este comportamento?",
        "english": "Which equations govern this behavior?",
        "prompt": "State the governing equations: Navier-Stokes, Euler-Bernoulli, Maxwell, heat equation, constitutive laws.",
        "validation_type": "mathematical_formulation",
    },
    "valid_simplifications": {
        "question": "Quais simplificacoes sao validas aqui?",
        "english": "Which simplifications are valid here?",
        "prompt": "Justify each simplification: steady-state? 2D? isotropic? linear elastic? incompressible? small displacements?",
        "validation_type": "assumption_check",
    },
    "computational_analysis": {
        "question": "Como analisar computacionalmente todas interacoes e realizar calculos precisos que sustentam o resultado experimentalmente?",
        "english": "How to computationally analyze all interactions and perform precise calculations that support the experimental result?",
        "prompt": "Define the computational workflow: mesh type, solver, boundary conditions, coupling method, convergence criteria.",
        "validation_type": "method_selection",
    },
    "uncertainties_limitations": {
        "question": "Quais sao as incertezas e limitacoes desta analise?",
        "english": "What are the uncertainties and limitations of this analysis?",
        "prompt": "Quantify uncertainties: model form, parameter, numerical, experimental. State limitations explicitly.",
        "validation_type": "uncertainty_quantification",
    },
    "sensitivity_to_change": {
        "question": "O que mudaria se a condicao X fosse diferente?",
        "english": "What would change if condition X were different?",
        "prompt": "Perform what-if analysis: change geometry, material, load, boundary condition — quantify sensitivity.",
        "validation_type": "sensitivity_analysis",
    },
    "validation_method": {
        "question": "Como validar como revisor hostil autonomo?",
        "english": "How to validate as an autonomous hostile reviewer?",
        "prompt": "Design falsification tests: what evidence would prove this analysis wrong? Benchmarks, cross-checks, experiments.",
        "validation_type": "falsification",
    },
    "numerical_method": {
        "question": "Qual metodo numerico e mais adequado: FEM, MPM, SPH, DEM, ou hibrido?",
        "english": "Which numerical method is most suitable: FEM, MPM, SPH, DEM, or hybrid?",
        "prompt": "Select numerical method based on deformation regime, material continuity, fluid presence, fracture risk.",
        "validation_type": "method_selection",
    },
}

# Domain-specific context prompts
DOMAIN_PROMPTS = {
    "mecanica": [
        "What are the critical load paths and stress concentrations?",
        "Is buckling a risk at this slenderness ratio?",
        "What is the fatigue life under cyclic loading?",
        "Are contact stresses within allowable limits?",
    ],
    "fluidos": [
        "Is the flow laminar or turbulent (Reynolds number)?",
        "Are compressibility effects significant (Mach number)?",
        "Is cavitation a risk in low-pressure regions?",
        "What is the boundary layer behavior?",
    ],
    "termo": [
        "What is the maximum operating temperature?",
        "Are thermal gradients causing differential expansion?",
        "Is natural or forced convection dominant?",
        "What is the heat flux at critical interfaces?",
    ],
    "energia": [
        "What is the overall energy conversion efficiency?",
        "Where are the largest energy losses?",
        "What is the specific energy/power density?",
        "Is there potential for energy recovery?",
    ],
    "eletricidade": [
        "What are the voltage and current ratings?",
        "Are electromagnetic interference levels acceptable?",
        "What is the thermal management requirement?",
        "What is the power quality impact?",
    ],
    "materiais": [
        "What are the critical material properties?",
        "Is there risk of environmental degradation?",
        "Are the materials compatible in contact?",
        "What is the cost vs. performance trade-off?",
    ],
    "construcao": [
        "What manufacturing processes are feasible?",
        "What tolerances are required?",
        "What is the estimated production cost?",
        "Are there quality control checkpoints?",
    ],
    "ambiente": [
        "What is the operating temperature range?",
        "Is corrosion protection required?",
        "What is the expected service life?",
        "Are there sustainability requirements?",
    ],
    "normativo": [
        "Which standards apply (ISO, ASTM, ABNT)?",
        "Are there certification requirements?",
        "What safety factors are mandated?",
        "What documentation is required for compliance?",
    ],
    "economico": [
        "What is the target cost per unit?",
        "What is the expected production volume?",
        "What is the payback period requirement?",
        "What financing structure is assumed?",
    ],
}


# ═══════════════════════════════════════════════════════════════
#  COMPLEXITY ASSESSMENT
# ═══════════════════════════════════════════════════════════════

def assess_complexity(
    n_domains: int = 1,
    coupling_strength: str = "weak",
    nonlinearity: str = "linear",
    uncertainty_level: str = "low",
    scale_count: int = 1,
) -> Dict:
    """Assess problem complexity from engineering parameters.

    Computes a complexity score (0–100) based on domain coupling,
    nonlinearity, uncertainty, and multi-scale nature.

    Args:
        n_domains: Number of engineering domains involved (1–10)
        coupling_strength: Coupling between domains:
                          'none', 'weak', 'moderate', 'strong'
        nonlinearity: Material/geometric behavior:
                     'linear', 'mild', 'moderate', 'severe'
        uncertainty_level: Data/knowledge uncertainty:
                          'low', 'medium', 'high'
        scale_count: Number of scales (M³: 1–3)

    Returns:
        Dict with complexity score, level, and breakdown.
    """
    coupling_scores = {
        "none": 0, "weak": 5, "moderate": 15, "strong": 30,
    }
    nonlinearity_scores = {
        "linear": 0, "mild": 10, "moderate": 20, "severe": 35,
    }
    uncertainty_scores = {
        "low": 0, "medium": 15, "high": 30,
    }

    domain_score = min(n_domains * 3, 20)
    coupling_val = coupling_scores.get(coupling_strength, 5)
    nonlinear_val = nonlinearity_scores.get(nonlinearity, 0)
    uncertainty_val = uncertainty_scores.get(uncertainty_level, 15)
    scale_val = (scale_count - 1) * 10

    total = min(domain_score + coupling_val + nonlinear_val + uncertainty_val + scale_val, 100)

    if total <= 25:
        level = "low"
    elif total <= 50:
        level = "moderate"
    elif total <= 75:
        level = "high"
    else:
        level = "very_high"

    return {
        "complexity_score": total,
        "complexity_level": level,
        "breakdown": {
            "domain_complexity": domain_score,
            "coupling_complexity": coupling_val,
            "nonlinearity_complexity": nonlinear_val,
            "uncertainty_complexity": uncertainty_val,
            "scale_complexity": scale_val,
        },
        "recommended_effort": (
            "E1" if total <= 20 else
            "E2" if total <= 40 else
            "E3" if total <= 60 else
            "E4" if total <= 80 else
            "E5"
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  CONTEXT ENGINE CLASS
# ═══════════════════════════════════════════════════════════════

@dataclass
class ContextEngine:
    """KDI Socratic Context Engine for engineering analysis.

    Validates problem context, generates Socratic prompts,
    assesses complexity, and provides auto-instruction guidance
    based on the MECH-ELECTRO-MATERIALS-SCIENTIST methodology.

    Args:
        problem: Problem statement text.
        domains: List of engineering domains involved.
        constraints: Dict of design/analysis constraints.
        standards: List of applicable standards.
        data_available: Dict of available data sources.
        optimization_target: Optimization objective, if any.
    """
    problem: str = ""
    domains: List[str] = field(default_factory=list)
    constraints: Dict = field(default_factory=dict)
    standards: List[str] = field(default_factory=list)
    data_available: Dict = field(default_factory=dict)
    optimization_target: str = ""

    def add_domain(self, domain: str) -> None:
        """Add an engineering domain to the analysis context.

        Args:
            domain: Domain name from the 10 KDI domains
                   (mecanica, fluidos, termo, energia,
                    eletricidade, materiais, construcao,
                    ambiente, normativo, economico)
        """
        if domain not in self.domains:
            self.domains.append(domain)

    def set_constraint(self, key: str, value: str) -> None:
        """Set a design or analysis constraint.

        Args:
            key: Constraint name (e.g. 'max_mass_kg')
            value: Constraint value (e.g. '15')
        """
        self.constraints[key] = value

    def set_data(self, key: str, description: str) -> None:
        """Register an available data source.

        Args:
            key: Data source name
            description: Description of data contents/format
        """
        self.data_available[key] = description

    def validate_context(self) -> Dict:
        """Validate the current problem context against KDI requirements.

        Checks that all required context layers are populated:
        problem statement, domains, constraints, standards, data,
        and optimization target.

        Returns:
            Dict with validation status per layer and overall readiness.
        """
        layers = {
            "problem_statement": {
                "present": len(self.problem.strip()) > 0,
                "status": "ok" if len(self.problem.strip()) > 0 else "missing",
            },
            "domains": {
                "present": len(self.domains) > 0,
                "count": len(self.domains),
                "status": "ok" if len(self.domains) > 0 else "missing",
            },
            "constraints": {
                "present": len(self.constraints) > 0,
                "count": len(self.constraints),
                "status": "ok" if len(self.constraints) > 0 else "missing",
            },
            "standards": {
                "present": len(self.standards) > 0,
                "count": len(self.standards),
                "status": "ok" if len(self.standards) > 0 else "missing",
            },
            "data": {
                "present": len(self.data_available) > 0,
                "count": len(self.data_available),
                "status": "ok" if len(self.data_available) > 0 else "missing",
            },
        }

        present_count = sum(1 for l in layers.values() if l["present"])
        total_layers = len(layers)

        return {
            "readiness_pct": round((present_count / total_layers) * 100, 1),
            "readiness": (
                "ready" if present_count == total_layers else
                "partial" if present_count >= 3 else
                "insufficient"
            ),
            "layers": layers,
            "optimization_target": self.optimization_target if self.optimization_target else "not_specified",
            "recommendation": (
                "Proceed with analysis." if present_count == total_layers
                else "Complete missing context layers before analysis."
            ),
        }

    def generate_prompts(
        self,
        language: str = "en",
        include_socratic: bool = True,
        include_domain: bool = True,
    ) -> List[Dict]:
        """Generate Socratic and domain-specific prompts for current context.

        Produces a list of validation questions based on the current
        problem domains and KDI methodology.

        Args:
            language: 'en' for English prompts, 'pt' for Portuguese
            include_socratic: Include 8 KDI Socratic prompts
            include_domain: Include domain-specific prompts

        Returns:
            List of prompt dicts with domain, question, and type.
        """
        prompts: List[Dict] = []

        if include_socratic:
            for key, data in SOCRATIC_PROMPTS.items():
                question = data["question"] if language == "pt" else data["english"]
                prompts.append({
                    "domain": "socratic",
                    "key": key,
                    "question": question,
                    "prompt": data["prompt"],
                    "type": data["validation_type"],
                })

        if include_domain:
            for domain in self.domains:
                domain_lower = domain.lower()
                if domain_lower in DOMAIN_PROMPTS:
                    for i, question in enumerate(DOMAIN_PROMPTS[domain_lower]):
                        prompts.append({
                            "domain": domain_lower,
                            "key": f"{domain_lower}_prompt_{i+1}",
                            "question": question,
                            "type": "domain_specific",
                        })

        return prompts

    def assess_complexity(self) -> Dict:
        """Assess problem complexity from current context.

        Uses the number of domains, coupling presence, nonlinearity
        from constraints, heuristic uncertainty from data availability,
        and scale information from domains.

        Returns:
            Complexity assessment dict.
        """
        n_domains = len(self.domains)

        # Estimate coupling from domain co-occurrence
        coupled_pairs = [
            {"mecanica", "fluidos"},
            {"mecanica", "termo"},
            {"fluidos", "termo"},
            {"mecanica", "eletricidade"},
            {"eletricidade", "energia"},
            {"materiais", "construcao"},
        ]
        domain_set = set(self.domains)
        n_couplings = sum(
            1 for pair in coupled_pairs if pair.issubset(domain_set)
        )
        coupling_strength = (
            "strong" if n_couplings >= 3 else
            "moderate" if n_couplings >= 1 else
            "weak"
        )

        # Heuristic for nonlinearity
        constraint_text = str(self.constraints).lower()
        has_nonlinear = any(
            word in constraint_text
            for word in ["plastic", "large", "nonlinear", "non-linear", "contact", "fracture"]
        )
        nonlinearity = "moderate" if has_nonlinear else "linear"

        # Heuristic for uncertainty
        has_data = len(self.data_available) > 0
        uncertainty = "low" if has_data and n_domains <= 3 else "medium"

        # Scale heuristic: more domains -> more likely multi-scale
        scale_count = min(n_domains, 3)
        has_micro = any(
            d in domain_set for d in ["materiais"]
        )
        if has_micro:
            scale_count = max(scale_count, 2)

        return assess_complexity(
            n_domains=n_domains,
            coupling_strength=coupling_strength,
            nonlinearity=nonlinearity,
            uncertainty_level=uncertainty,
            scale_count=scale_count,
        )

    def auto_instruct(self, language: str = "en") -> Dict:
        """Generate full auto-instruction guidance for the problem.

        Combines context validation, Socratic prompts, domain
        prompts, and complexity assessment into a single
        structured output for agent guidance.

        Args:
            language: 'en' or 'pt'

        Returns:
            Dict with context, prompts, complexity, and recommended
            next steps.
        """
        context = self.validate_context()
        prompts = self.generate_prompts(language=language)
        complexity = self.assess_complexity()

        return {
            "problem": self.problem,
            "context_validation": context,
            "complexity": complexity,
            "socratic_prompts_generated": len([p for p in prompts if p["domain"] == "socratic"]),
            "domain_prompts_generated": len([p for p in prompts if p["domain"] != "socratic"]),
            "total_prompts": len(prompts),
            "all_prompts": prompts,
            "recommended_effort": complexity["recommended_effort"],
            "next_steps": (
                "1. Review context validation gaps.\n"
                "2. Answer each Socratic question.\n"
                "3. Assign numerical methods per domain.\n"
                "4. Run VVV protocol on results."
            ),
        }
