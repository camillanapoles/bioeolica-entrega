"""Tests for CadQuery Bridge module."""

import os
import tempfile

import numpy as np
import pytest

from cad_cae.cad_bridge import (
    CadModel,
    cantilever_beam,
    l_bracket,
    plate_with_hole,
    pressure_vessel,
)


class TestPrimitives:
    def test_box_creation(self):
        m = CadModel().box(10, 20, 30)
        assert m.volume == pytest.approx(10 * 20 * 30, rel=0.01)
        bb = m.bounding_box()
        assert bb["x"] == pytest.approx(10)
        assert bb["y"] == pytest.approx(20)
        assert bb["z"] == pytest.approx(30)

    def test_cylinder(self):
        m = CadModel().cylinder(radius=10, height=20)
        import math
        expected = math.pi * 10**2 * 20
        assert m.volume == pytest.approx(expected, rel=0.02)

    def test_sphere(self):
        m = CadModel().sphere(radius=10)
        expected = 4 / 3 * np.pi * 10**3
        assert m.volume == pytest.approx(expected, rel=0.02)

    def test_extrude_polygon(self):
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        m = CadModel().extrude(points, height=5)
        assert m.volume == pytest.approx(10 * 10 * 5, rel=0.05)

    def test_union(self):
        a = CadModel().box(10, 10, 10)
        b = CadModel().box(10, 10, 10).box(10, 10, 10)
        a.union(b)
        assert a.volume > 900

    def test_cut(self):
        plate = CadModel().box(20, 20, 2)
        hole = CadModel().cylinder(radius=5, height=4)
        plate.cut(hole)
        import math
        expected = 20 * 20 * 2 - math.pi * 5**2 * 2
        assert plate.volume == pytest.approx(expected, rel=0.05)


class TestExport:
    def test_export_step(self):
        m = CadModel().box(10, 10, 10)
        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
            m.export_step(f.name)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 100, f"STEP file too small: {size} bytes"

    def test_export_stl(self):
        m = CadModel().box(10, 10, 10)
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            m.export_stl(f.name)
            size = os.path.getsize(f.name)
        os.unlink(f.name)
        assert size > 100

    def test_export_no_geometry_raises(self):
        m = CadModel()
        with pytest.raises(RuntimeError):
            m.export_step("/tmp/nonexistent.step")


class TestBoundingBox:
    def test_box_bb(self):
        m = CadModel().box(10, 20, 30)
        bb = m.bounding_box()
        assert bb["x"] == 10
        assert bb["y"] == 20
        assert bb["z"] == 30

    def test_empty_bb(self):
        m = CadModel()
        bb = m.bounding_box()
        assert bb["x"] == 0


class TestMass:
    def test_box_mass(self):
        m = CadModel().box(10, 10, 10)  # 1000 mm³ = 1 cm³
        assert m.mass == pytest.approx(1e-3, rel=0.01)  # 1 g at 1 g/cm³ = 0.001 kg


class TestPreBuilt:
    def test_cantilever_beam(self):
        b = cantilever_beam(100, 10, 5)
        assert b.volume == pytest.approx(5000, rel=0.01)

    def test_plate_with_hole(self):
        import math
        p = plate_with_hole(100, 50, 5, hole_diameter=10)
        expected = 100 * 50 * 5 - math.pi * 5**2 * 5
        assert p.volume == pytest.approx(expected, rel=0.02)

    def test_pressure_vessel(self):
        v = pressure_vessel(length=200, radius=50, wall_thickness=5)
        import math
        outer = math.pi * 50**2 * (200 + 100)  # cylinder + 2 hemispheres
        inner = math.pi * 45**2 * (200 + 90)
        expected = (outer - inner) / 3  # rough estimate
        assert v.volume > 10000

    def test_l_bracket(self):
        b = l_bracket()
        assert b.volume > 1000
