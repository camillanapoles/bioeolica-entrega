import pytest
from modules.mkdelagen import MaterialSpec, LoadCase

def test_material_spec():
    m = MaterialSpec(name="steel", E_GPa=200, nu=0.3, rho_kgm3=7800)
    assert m.name == "steel"

def test_load_case():
    lc = LoadCase(name="test", tip_force_N=1000)
    assert lc.tip_force_N == 1000

def test_material_defaults():
    m = MaterialSpec()
    assert m.E_GPa == 10.0
