import numpy as np; import pytest
from modules.fem_solver import BeamElement, FEModel
def test_beam_defaults():
    assert BeamElement().E_GPa == 10.0
def test_beam_stiffness_12x12():
    e = BeamElement(E_GPa=200, L_m=1.0, I_m4=1e-4, A_m2=0.01)
    assert e.stiffness_matrix().shape == (12, 12)
def test_beam_mass_12x12():
    e = BeamElement(E_GPa=200, L_m=1.0, I_m4=1e-4, A_m2=0.01)
    assert e.mass_matrix().shape == (12, 12)
def test_femodel():
    e = BeamElement(E_GPa=200, L_m=1.0, I_m4=1e-4, A_m2=0.01)
    fem = FEModel(elements=[e], nodes=[0.0,1.0], dofs=12)
    fem.assemble()
    assert fem.K_global is not None
