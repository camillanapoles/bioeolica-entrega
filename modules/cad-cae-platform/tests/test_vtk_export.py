"""Tests for VTK export module."""

import os
import tempfile

import numpy as np
import pytest

from cad_cae.vtk_export import write_vtu, write_vtp


class TestVTU:
    def test_write_beam_vtu(self):
        nodes = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],
                           [0,0,1],[1,0,1],[1,1,1],[0,1,1]], dtype=float)
        elems = [(8, [0,1,2,3,4,5,6,7])]  # hex8
        with tempfile.NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            write_vtu(f.name, nodes, elems)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 200

    def test_tet_mesh(self):
        nodes = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float)
        elems = [(4, [0,1,2,3])]
        with tempfile.NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            write_vtu(f.name, nodes, elems)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 200

    def test_with_displacement(self):
        nodes = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float)
        elems = [(4, [0,1,2,3])]
        disp = np.array([[0,0,0],[0.1,0,0],[0,0.1,0],[0,0,0.1]], dtype=float)
        with tempfile.NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            write_vtu(f.name, nodes, elems, point_data={"disp": disp})
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 300

    def test_with_stress(self):
        nodes = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float)
        elems = [(4, [0,1,2,3])]
        stress = np.array([10.0, 20.0, 30.0])
        with tempfile.NamedTemporaryFile(suffix=".vtu", delete=False) as f:
            write_vtu(f.name, nodes, elems, cell_data={"vm_stress": stress})
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 300


class TestVTP:
    def test_write_vtp(self):
        points = np.random.rand(50, 3)
        with tempfile.NamedTemporaryFile(suffix=".vtp", delete=False) as f:
            write_vtp(f.name, points)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 200

    def test_vtp_with_data(self):
        points = np.random.rand(20, 3)
        data = np.random.rand(20)
        with tempfile.NamedTemporaryFile(suffix=".vtp", delete=False) as f:
            write_vtp(f.name, points, point_data={"mode": data})
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 300
