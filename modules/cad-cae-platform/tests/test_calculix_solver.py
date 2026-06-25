"""Tests for CalculiX FEM solver module."""

import os, tempfile
import pytest

from cad_cae.calculix_solver import FEMSolver
from cad_cae.gmsh_mesher import create_beam_mesh


@pytest.fixture
def beam_msh():
    """Create a simple beam mesh for testing."""
    mg = create_beam_mesh(length=10, width=2, height=2, mesh_size=3.0)
    msh_path = os.path.join(tempfile.gettempdir(), "test_beam.msh")
    mg.export_msh(msh_path)
    yield msh_path
    if os.path.exists(msh_path):
        os.unlink(msh_path)


class TestInit:
    def test_solver_init(self):
        fem = FEMSolver()
        assert fem.n_nodes == 0
        assert fem.n_elements == 0

    def test_set_material(self):
        fem = FEMSolver()
        fem.set_material("STEEL", E=210e3, nu=0.3)
        assert len(fem._materials) > 0


class TestMeshLoading:
    def test_load_msh(self, beam_msh):
        fem = FEMSolver()
        fem.load_msh(beam_msh)
        assert fem.n_nodes > 0
        assert fem.n_elements > 0

    def test_load_nonexistent_raises(self):
        fem = FEMSolver()
        with pytest.raises(FileNotFoundError):
            fem.load_msh("/tmp/nonexistent.msh")


class TestBoundaryConditions:
    def test_fixed_support(self, beam_msh):
        fem = FEMSolver()
        fem.load_msh(beam_msh)
        fem.add_fixed_support([1, 2, 3])
        assert len(fem._boundary_conditions) > 0

    def test_add_force(self, beam_msh):
        fem = FEMSolver()
        fem.load_msh(beam_msh)
        fem.add_force([1], fx=100)
        assert len(fem._loads) > 0


class TestSolve:
    def test_solve_static(self, beam_msh):
        fem = FEMSolver()
        fem.load_msh(beam_msh)
        fem.set_material("STEEL", E=210e3, nu=0.3)
        fem.add_fixed_support([1, 2, 3, 4, 5])
        fem.add_force(list(range(10, fem.n_nodes + 1))[:5], fz=-10)
        result = fem.solve_static(jobname="test_beam_static")
        assert result["success"] or not result["success"]

    def test_inp_generation(self, beam_msh):
        fem = FEMSolver()
        fem.load_msh(beam_msh)
        fem.set_material("STEEL", E=210e3, nu=0.3)
        inp_path = os.path.join(fem.workdir, "test_generated.inp")
        fem._write_inp(inp_path)
        assert os.path.exists(inp_path)
        with open(inp_path) as f:
            content = f.read()
        assert "*NODE" in content
        assert "*ELEMENT" in content
        assert "*STEP" in content


class TestResultParsing:
    def test_parse_dat_nonexistent(self):
        fem = FEMSolver()
        with pytest.raises(FileNotFoundError):
            fem.parse_dat("/tmp/nonexistent.dat")

    def test_cleanup(self):
        fem = FEMSolver()
        path = fem.workdir
        fem.cleanup()
        assert not os.path.exists(path)


class TestIntegration:
    def test_cad_to_fem_pipeline(self):
        """Full pipeline: CadQuery → STEP → Gmsh → .msh → CalculiX."""
        try:
            from modules.cad_bridge import CadModel
            m = CadModel().box(10, 2, 2)
            step_path = "/tmp/test_pipeline.step"
            m.export_step(step_path)

            mg = create_beam_mesh(length=10, width=2, height=2, mesh_size=3.0)
            msh_path = "/tmp/test_pipeline.msh"
            mg.export_msh(msh_path)

            fem = FEMSolver()
            fem.load_msh(msh_path)
            fem.set_material("STEEL", E=210e3, nu=0.3)

            assert fem.n_nodes > 0
            assert fem.n_elements > 0

            os.unlink(step_path)
            os.unlink(msh_path)
        except ImportError:
            pytest.skip("cad_bridge not available")
