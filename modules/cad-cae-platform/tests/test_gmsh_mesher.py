"""Tests for Gmsh mesher module."""

import os, tempfile
import numpy as np
import pytest
from cad_cae.gmsh_mesher import MeshGenerator, create_beam_mesh

class TestBasic:
    def test_init(self):
        mg = MeshGenerator(); assert mg._initialized
        mg.__del__(); mg.__del__()

    def test_create_beam(self):
        mg = create_beam_mesh(10, 2, 2, mesh_size=2.0)
        stats = mg.get_mesh_stats()
        assert stats["n_nodes"] > 10

    def test_negative_size_raises(self):
        mg = MeshGenerator()
        with pytest.raises(ValueError):
            mg.set_element_size(max_size=-1)

class TestExport:
    def test_export_msh(self):
        mg = create_beam_mesh(10, 2, 2, mesh_size=2.0)
        with tempfile.NamedTemporaryFile(suffix=".msh", delete=False) as f:
            mg.export_msh(f.name)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 100

    def test_export_vtk(self):
        mg = create_beam_mesh(6, 2, 2, mesh_size=3.0)
        with tempfile.NamedTemporaryFile(suffix=".vtk", delete=False) as f:
            mg.export_vtk(f.name)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 100

class TestStep:
    def test_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            MeshGenerator().import_step("/tmp/nonexistent.step")

    def test_step_import(self):
        try:
            from modules.cad_bridge import CadModel
            m = CadModel().box(10, 10, 10)
            p = "/tmp/test_cad_step.step"; m.export_step(p)
            mg = MeshGenerator()
            e = mg.import_step(p)
            assert len(e) > 0
        except ImportError:
            pytest.skip("cad_bridge not available")
