#!/usr/bin/env python3
"""Tests for P2: FEM solver, Method Selector, Uncertainty Quantification."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from fem_solver import FEModel, BeamElement, mesh1D
from method_selector import select_method, ProblemCharacteristics
from uncertainty import MonteCarloSampler, UncertainValue, confidence_interval
import numpy as np


class TestFEM:
    def test_beam_stiffness(self):
        e = BeamElement(E_GPa=10, L_m=1.0, I_m4=1e-6)
        K = e.stiffness_matrix()
        assert K.shape == (12, 12)
        assert K[0, 0] > 0
        # Symmetry check
        assert np.allclose(K, K.T)

    def test_assemble(self):
        model = FEModel()
        model.add_element(BeamElement(L_m=1.0))
        model.add_element(BeamElement(L_m=1.0))
        model.assemble()
        assert model.K_global is not None
        assert model.K_global.shape[0] >= 12

    def test_solve_cantilever(self):
        """Single element cantilever beam with tip load."""
        model = FEModel()
        model.add_element(BeamElement(L_m=1.0, E_GPa=200, I_m4=1e-6))
        model.assemble()
        # Clamp node 0 (DOF 0-5)
        bc = list(range(6))
        model.apply_bc(bc)
        F = np.zeros(model.dofs)
        F[1] = -1000  # y-force at tip (node 1, DOF 1)
        u = model.solve(F)
        assert u is not None
        assert len(u) == model.dofs
        # Tip displacement should be downward (negative y)
        assert u[1] < 0

    def test_mesh1d(self):
        nodes = mesh1D(1.0, 10)
        assert len(nodes) == 11
        assert nodes[0] == 0
        assert nodes[-1] == 1.0


class TestMethodSelector:
    def test_fem_small(self):
        p = ProblemCharacteristics(deformation_regime="small", continuity=True)
        r = select_method(p)
        assert "FEM" in r.primary

    def test_mpm_large(self):
        p = ProblemCharacteristics(deformation_regime="large", continuity=True)
        r = select_method(p)
        assert "MPM" in r.primary

    def test_peridynamics_fracture(self):
        p = ProblemCharacteristics(deformation_regime="large", has_fracture=True)
        r = select_method(p)
        assert "Peridynamics" in r.primary

    def test_dem_granular(self):
        p = ProblemCharacteristics(deformation_regime="extreme", is_granular=True)
        r = select_method(p)
        assert "DEM" in r.primary or "MPM" in r.primary

    def test_sph_fluid_large(self):
        p = ProblemCharacteristics(deformation_regime="large", is_fluid=True)
        r = select_method(p)
        assert "SPH" in r.primary


class TestUncertainty:
    def test_mc_run(self):
        mc = MonteCarloSampler(n_samples=100)
        result = mc.run(
            lambda E: E * 2,
            distributions={"E": ("normal", 10, 1)},
        )
        assert result.n_samples > 0
        assert 15 < result.nominal < 25

    def test_ci(self):
        lo, hi, std = confidence_interval(np.array([1, 2, 3, 4, 5]))
        assert lo < hi
        assert std > 0

    def test_sensitivity(self):
        def my_func(a, b):
            return a * b
        mc = MonteCarloSampler()
        sens = mc.sensitivity({"a": 10, "b": 5}, my_func)
        assert "sensitivities" in sens
        assert sens["most_sensitive"] is not None
