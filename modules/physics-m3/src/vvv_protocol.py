#!/usr/bin/env python3
"""
VVV Protocol — Verificação, Validação, Certificação.

Conforme INSTRUCTIONS.md KDI mandate M3/F5:
  1. VERIFICAÇÃO: convergência de malha, estabilidade temporal, conservação
  2. VALIDAÇÃO: benchmark experimental, solução analítica, cross-code
  3. CERTIFICAÇÃO: fonte confiável, erro quantificado, reprodutibilidade

Uso:
    from vvv_protocol import VVVReport, VerificationStudy, ValidationCrossCode

    vvv = VVVReport(study="Blade FEM Convergence")
    vvv.verify_convergence(errors=[8.1, 3.2, 1.1], h_values=[0.5, 0.25, 0.125])
    vvv.validate_experimental(simulation=[1.0, 2.0], experimental=[0.95, 2.1])
    result = vvv.certify()
    print(result.status)  # PASS or FAIL
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timezone
import json


@dataclass
class VVVReport:
    """Verification, Validation, and Certification report."""
    study_name: str = ""
    created_at: str = ""
    verification: Dict = field(default_factory=dict)
    validation: Dict = field(default_factory=dict)
    certification: Dict = field(default_factory=dict)
    status: str = "PENDING"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def verify_convergence(self, errors: List[float],
                           h_values: List[float],
                           tolerance: float = 5.0) -> Dict:
        """Mesh convergence study: error should decrease with h-refinement."""
        if len(errors) < 2:
            result = {"status": "INCONCLUSIVE", "reason": "Need at least 2 meshes"}
        else:
            rate = self._convergence_rate(errors, h_values)
            decreasing = all(errors[i] > errors[i+1] for i in range(len(errors)-1))
            converged = errors[-1] < tolerance

            result = {
                "status": "PASS" if (decreasing and converged) else "FAIL",
                "errors_pct": errors,
                "h_values": h_values,
                "convergence_rate": round(rate, 2),
                "monotonic": decreasing,
                "final_error": round(errors[-1], 2),
                "tolerance": tolerance,
                "converged": converged,
            }

        self.verification = result
        return result

    def validate_experimental(self, simulation: List[float],
                              experimental: List[float],
                              max_error_pct: float = 10.0) -> Dict:
        """Compare simulation vs experimental data."""
        if len(simulation) != len(experimental):
            return {"status": "FAIL", "reason": "Mismatched array lengths"}

        errors = []
        for s, e in zip(simulation, experimental):
            if e != 0:
                errors.append(abs(s - e) / abs(e) * 100)

        if not errors:
            return {"status": "INCONCLUSIVE", "reason": "No valid comparison points"}

        max_err = max(errors)
        mean_err = np.mean(errors)
        r_squared = self._r_squared(simulation, experimental)

        result = {
            "status": "PASS" if max_err < max_error_pct else "FAIL",
            "max_error_pct": round(max_err, 2),
            "mean_error_pct": round(float(mean_err), 2),
            "r_squared": round(r_squared, 4),
            "n_points": len(simulation),
            "tolerance_pct": max_error_pct,
        }
        self.validation = result
        return result

    def validate_analytical(self, numerical: float,
                            analytical: float,
                            tolerance_pct: float = 5.0) -> Dict:
        """Compare numerical result with analytical solution."""
        if analytical == 0:
            return {"status": "INCONCLUSIVE", "reason": "Analytical solution is 0"}
        error_pct = abs(numerical - analytical) / abs(analytical) * 100
        result = {
            "status": "PASS" if error_pct < tolerance_pct else "FAIL",
            "numerical": numerical,
            "analytical": analytical,
            "error_pct": round(error_pct, 2),
            "tolerance_pct": tolerance_pct,
        }
        self.validation = result
        return result

    def certify(self) -> Dict:
        """Certify based on verification + validation results."""
        v_pass = self.verification.get("status") == "PASS"
        v_method = self.verification.get("method", "convergence")
        val_pass = self.validation.get("status") == "PASS" if self.validation else False

        # Certification requires BOTH
        # But allow single pillar if other is N/A
        has_verification = bool(self.verification)
        has_validation = bool(self.validation)

        if has_verification and has_validation:
            passed = v_pass and val_pass
        elif has_verification:
            passed = v_pass
        elif has_validation:
            passed = val_pass
        else:
            passed = False

        self.status = "PASS" if passed else "FAIL"
        self.certification = {
            "status": self.status,
            "verification_passed": v_pass if has_verification else "N/A",
            "validation_passed": val_pass if has_validation else "N/A",
            "certified_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.certification

    def _convergence_rate(self, errors: List[float], h_values: List[float]) -> float:
        """Estimate p from error ∝ h^p."""
        if len(errors) < 3 or len(h_values) < 3:
            return 0.0
        p = np.log(errors[1] / errors[0]) / np.log(h_values[1] / h_values[0])
        return float(p)

    def _r_squared(self, y_true: List[float], y_pred: List[float]) -> float:
        """Coefficient of determination."""
        y = np.array(y_true)
        p = np.array(y_pred)
        ss_res = np.sum((y - p) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


@dataclass
class CrossValidation:
    """Cross-validation between numerical methods."""
    results_a: List[float] = field(default_factory=list)
    results_b: List[float] = field(default_factory=list)
    method_a: str = ""
    method_b: str = ""

    def compare(self, tolerance_pct: float = 5.0) -> Dict:
        errors = []
        for a, b in zip(self.results_a, self.results_b):
            if abs(a) > 0:
                errors.append(abs(a - b) / abs(a) * 100)

        if not errors:
            return {"status": "FAIL", "reason": "No valid comparison"}
        max_err = max(errors)
        return {
            "status": "PASS" if max_err < tolerance_pct else "FAIL",
            "max_error_pct": round(max_err, 2),
            "n_points": len(errors),
            "tolerance_pct": tolerance_pct,
        }


# Pre-defined VVV checklists
COMPOSITE_VVV_CHECKLIST = {
    "step_1_verification": [
        "Convergência de malha (3 níveis: grosseira/média/fina)",
        "Estabilidade temporal (redução de Δt até estabilização)",
        "Conservação de energia (< 1% desbalanço)",
        "Consistência de unidades (SI)",
    ],
    "step_2_validation": [
        "Benchmark experimental (dados de ensaio de flexão/tração)",
        "Solução analítica (Euler-Bernoulli para casos limite)",
        "Cross-code (comparar com solver alternativo)",
        "Propagação de incerteza quantificada",
    ],
    "step_3_certification": [
        "Fonte confiável (peer-reviewed DOI ou norma)",
        "Comparação justa (mesmas BCs, materiais, cargas)",
        "Erro quantificado (nominal ± IC 95%)",
        "Reprodutível (seed fixa, versões documentadas)",
    ],
}
