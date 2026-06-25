"""Tests for CrystalLattice module."""

import numpy as np
import pytest

from modules.crystal_lattice import CrystalLattice


class TestInit:
    def test_bcc_default(self):
        cl = CrystalLattice("bcc")
        assert cl.name == "Body-Centered Cubic"
        assert cl.atoms_per_cell == 2

    def test_fcc(self):
        cl = CrystalLattice("fcc")
        assert cl.name == "Face-Centered Cubic"
        assert cl.atoms_per_cell == 4

    def test_sc(self):
        cl = CrystalLattice("sc")
        assert cl.atoms_per_cell == 1

    def test_hcp(self):
        cl = CrystalLattice("hcp")
        assert cl.atoms_per_cell == 2

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            CrystalLattice("unknown")

    def test_custom_a(self):
        cl = CrystalLattice("bcc", a=0.286)
        assert cl.a == 0.286


class TestUnitCell:
    def test_sc_atoms(self):
        cl = CrystalLattice("sc")
        a = cl.unit_cell_atoms()
        assert a.shape == (1, 3)

    def test_bcc_atoms(self):
        cl = CrystalLattice("bcc")
        a = cl.unit_cell_atoms()
        assert a.shape == (2, 3)
        assert np.allclose(a[1], [0.5, 0.5, 0.5])

    def test_fcc_atoms(self):
        cl = CrystalLattice("fcc")
        a = cl.unit_cell_atoms()
        assert a.shape == (4, 3)

    def test_hcp_atoms(self):
        cl = CrystalLattice("hcp")
        a = cl.unit_cell_atoms()
        assert a.shape == (2, 3)


class TestSupercell:
    def test_2x2x2(self):
        cl = CrystalLattice("bcc")
        sc = cl.supercell(2, 2, 2)
        assert sc.shape == (16, 3)  # 2 atoms/cell * 8 cells

    def test_1x1x1(self):
        cl = CrystalLattice("fcc")
        sc = cl.supercell(1, 1, 1)
        assert sc.shape == (4, 3)


class TestMiller:
    def test_100_plane(self):
        cl = CrystalLattice("bcc")
        X, Y, Z = cl.miller_plane(1, 0, 0)
        assert X.shape == (20, 20)

    def test_110_spacing(self):
        cl = CrystalLattice("bcc", a=0.286)
        d = cl.interplanar_spacing(1, 1, 0)
        assert d > 0
        assert np.isclose(d, 0.286 / np.sqrt(2), rtol=0.01)

    def test_invalid_miller(self):
        cl = CrystalLattice("sc")
        with pytest.raises(ValueError):
            cl.miller_plane(0, 0, 0)


class TestPacking:
    def test_packing_bcc(self):
        cl = CrystalLattice("bcc")
        assert np.isclose(cl.packing_fraction(), 0.680, rtol=0.01)

    def test_packing_fcc(self):
        cl = CrystalLattice("fcc")
        assert np.isclose(cl.packing_fraction(), 0.740, rtol=0.01)

    def test_coordination_bcc(self):
        cl = CrystalLattice("bcc")
        assert cl.coordination_number() == 8

    def test_coordination_fcc(self):
        cl = CrystalLattice("fcc")
        assert cl.coordination_number() == 12


class TestVectors:
    def test_primitive_bcc(self):
        cl = CrystalLattice("bcc")
        pv = cl.primitive_vectors()
        assert pv.shape == (3, 3)

    def test_reciprocal_volume(self):
        cl = CrystalLattice("bcc")
        rv = cl.reciprocal_vectors()
        assert rv.shape == (3, 3)

    def test_density(self):
        cl = CrystalLattice("bcc", a=0.286)
        d = cl.density_g_cm3(atomic_mass=55.845)
        assert 7.0 < d < 8.0  # Fe BCC ~7.87 g/cm³
