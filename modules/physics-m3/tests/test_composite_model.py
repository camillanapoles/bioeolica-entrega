import pytest
from modules.composite_model import CompositeMaterial

def test_init():
    c = CompositeMaterial()
    assert c.Vf == 0.15

def test_e1_positive():
    ec = CompositeMaterial().elastic_constants()
    assert ec["E1_longitudinal_GPa"] > 0

def test_e2_positive():
    ec = CompositeMaterial().elastic_constants()
    assert ec["E2_transverse_GPa"] > 0
