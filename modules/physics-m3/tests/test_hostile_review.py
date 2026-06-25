#!/usr/bin/env python3
"""
Hostile Review Tests — P6: Revisor Hostil Autônomo.

Testa comportamento sob condições adversas:
  - Inputs inválidos (negativos, zero, extremos)
  - Condições de contorno (edge cases)
  - Cross-validation entre métodos
  - Estabilidade numérica
  - Assert que falhas são explicitamente tratadas
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import numpy as np
import pytest

from fem_solver import BeamElement
from composite_model import CompositeMaterial
from mechanical_tests import flexure_test, tensile_test, buckling_test
from m3_analysis import M3Analysis, PlyLayer
from fluid_dynamics import wind_profile, bem_theory, reynolds_number
from vvv_protocol import VVVReport, CrossValidation


# ═══════════════════════════════════════════════════════════════
#  EDGE CASE TESTS — Entradas inválidas
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_beam_zero_length(self):
        """Beam with zero length should produce finite stiffness matrix."""
        e = BeamElement(E_GPa=10, L_m=0)
        K = e.stiffness_matrix()
        assert not np.any(np.isnan(K))
        assert not np.any(np.isinf(K))

    def test_composite_zero_vf(self):
        """Zero fiber volume fraction = pure matrix behavior."""
        mat = CompositeMaterial(fiber_volume_fraction=0)
        s = mat.summary()
        assert s["elastic"]["E1_longitudinal_GPa"] > 0

    def test_composite_high_vv(self):
        """High void fraction degrades strength."""
        mat = CompositeMaterial(void_fraction=0.2)
        s = mat.summary()
        assert s["strength"]["tensile_longitudinal_MPa"] > 0

    def test_wind_zero_height(self):
        """Wind at zero height should be >= 0."""
        v = wind_profile(0, 5.0)
        assert v >= 0

    def test_bem_zero_wind(self):
        """BEM with zero wind should produce zero power."""
        r = bem_theory(v_wind_ms=0, rpm=0, R_m=1.5)
        assert r["power_W"] == 0

    def test_buckling_zero_length(self):
        """Buckling with zero length should handle gracefully."""
        try:
            r = buckling_test(E_GPa=10, length_mm=0, width_mm=10, thickness_mm=2)
            assert r["critical_load_N"] == float('inf') or r["critical_load_N"] > 1e10
        except (ValueError, ZeroDivisionError):
            pass

    def test_reynolds_zero(self):
        """Re=0 at zero velocity."""
        Re = reynolds_number(0, 0.3)
        assert Re == 0

    def test_tensile_no_strength(self):
        """Tensile with zero strength."""
        r = tensile_test(E_GPa=10, width_mm=10, thickness_mm=2, tensile_strength_MPa=0)
        assert r["max_force_N"] == 0


# ═══════════════════════════════════════════════════════════════
#  CROSS-VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestCrossValidation:
    def test_analytical_vs_numerical(self):
        """Euler-Bernoulli beam: analytical vs numerical tip deflection.

        Analytical: delta = PL³/(3EI) (cantilever, end load)
        Numerical: FEM with single beam element
        """
        L, P, E = 1.0, 1000.0, 200e9
        I = 1e-6
        delta_analytical = P * L**3 / (3 * E * I)

        from fem_solver import FEModel
        model = FEModel()
        model.add_element(BeamElement(L_m=L, E_GPa=E/1e9, I_m4=I, A_m2=0.01))
        model.assemble()
        model.apply_bc(list(range(6)))
        forces = np.zeros(model.dofs)
        # Node 0 DOF 0-5 (clamped), Node 1 DOF 6-11 (tip)
        # y-displacement at tip = DOF 7
        forces[7] = -P
        u = model.solve(forces)
        delta_numerical = abs(u[7])

        error = abs(delta_numerical - delta_analytical) / delta_analytical * 100
        # Single beam element gives exact solution for tip-loaded cantilever
        assert error < 1.0, f"FEM vs analytical error: {error:.2f}%"

    def test_vvv_cross_code_path(self):
        """VVV protocol cross-validation path."""
        cv = CrossValidation(
            results_a=[1.0, 2.0, 3.0],
            results_b=[1.02, 2.05, 2.95],
            method_a="CalculiX", method_b="Code_Aster",
        )
        r = cv.compare(tolerance_pct=5.0)
        assert r["status"] == "PASS"


# ═══════════════════════════════════════════════════════════════
#  VVV PROTOCOL TESTS
# ═══════════════════════════════════════════════════════════════

class TestVVV:
    def test_convergence_pass(self):
        vvv = VVVReport("Mesh Study")
        r = vvv.verify_convergence([12.0, 5.0, 1.5], [0.5, 0.25, 0.125])
        assert r["status"] == "PASS"

    def test_convergence_fail(self):
        vvv = VVVReport("Non-converging")
        r = vvv.verify_convergence([1.0, 3.0, 5.0], [0.5, 0.25, 0.125])
        assert r["status"] == "FAIL"

    def test_validation_pass(self):
        vvv = VVVReport("Exp Validation")
        r = vvv.validate_experimental([1.0, 2.0], [0.98, 2.05])
        assert r["status"] == "PASS"

    def test_certification_both_pass(self):
        vvv = VVVReport("Full Cert")
        vvv.verify_convergence([10, 4, 1.2], [0.5, 0.25, 0.125])
        vvv.validate_experimental([1.0, 2.0], [0.97, 2.08])
        c = vvv.certify()
        assert c["status"] == "PASS"

    def test_certification_one_fails(self):
        vvv = VVVReport("Failed Cert")
        vvv.verify_convergence([10, 4, 1.2], [0.5, 0.25, 0.125])
        vvv.validate_experimental([1.0, 2.0], [5.0, 8.0])  # big error
        c = vvv.certify()
        assert c["status"] == "FAIL"

    def test_r_squared_perfect(self):
        vvv = VVVReport("R²")
        r = vvv.validate_experimental([1, 2, 3], [1, 2, 3])
        assert r["r_squared"] == 1.0


# ═══════════════════════════════════════════════════════════════
#  REPRODUCIBILITY TESTS
# ═══════════════════════════════════════════════════════════════

class TestReproducibility:
    def test_material_seeded(self):
        """Composite material should give same results on re-run."""
        mat1 = CompositeMaterial(fiber="waste_paper", matrix="pva", fiber_volume_fraction=0.15)
        mat2 = CompositeMaterial(fiber="waste_paper", matrix="pva", fiber_volume_fraction=0.15)
        assert mat1.elastic_constants() == mat2.elastic_constants()

    def test_bem_deterministic(self):
        """BEM with same inputs = same outputs."""
        r1 = bem_theory(6, 200, 1.5)
        r2 = bem_theory(6, 200, 1.5)
        assert r1["power_W"] == r2["power_W"]

    def test_fem_reproducible(self):
        """FEM solver seeded gives consistent results."""
        from fem_solver import FEModel
        def solve_once():
            m = FEModel()
            m.add_element(BeamElement(L_m=1.0, E_GPa=200, I_m4=1e-6))
            m.assemble()
            m.apply_bc(list(range(6)))
            F = np.zeros(m.dofs)
            F[1] = -100
            return m.solve(F)[1]
        assert solve_once() == solve_once()
