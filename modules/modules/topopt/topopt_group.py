"""
TopOptGroup — assembles the OpenMDAO group for topology optimization.

Pipeline: density_field → SIMPFemComponent → displacements + compliance
                                        → ComplianceComponent → compliance_value
          density_field → VolumeConstraint → volume_fraction

Driver: SLSQP (SciPyOptimizer) with fallback to COBYLA.
"""

import openmdao.api as om
from .fem_component import SIMPFemComponent
from .compliance import ComplianceComponent
from .volume_constraint import VolumeConstraint


class TopOptGroup(om.Group):
    """
    OpenMDAO Group for topology optimization.

    Parameters
    ----------
    nelx : int
        Number of elements in x-direction (default 80).
    nely : int
        Number of elements in y-direction (default 40).
    vol_frac : float
        Target volume fraction (default 0.3).
    penal : float
        SIMP penalization power (default 3.0).
    E0 : float
        Base Young's modulus in Pa (default 1.0e9). Can be thermally degraded.
    """

    def __init__(self, nelx: int = 80, nely: int = 40,
                 vol_frac: float = 0.3, penal: float = 3.0, E0: float = 1.0e9, **kwargs):
        super().__init__(**kwargs)
        self.nelx = nelx
        self.nely = nely
        self.vol_frac = vol_frac
        self.penal = penal
        self.E0 = E0

    def setup(self):
        # FEM solver — promotes density_field, load_vector, displacements to group
        self.add_subsystem(
            "fea",
            SIMPFemComponent(nelx=self.nelx, nely=self.nely, penal=self.penal, E0=self.E0),
            promotes=["density_field", "load_vector", "displacements"],
        )
        # Compliance objective — connect displacements from fea via promoted name
        self.add_subsystem(
            "objective",
            ComplianceComponent(),
            promotes=[("compliance_value", "compliance")],
        )
        self.connect("displacements", "objective.displacements")
        self.connect("load_vector", "objective.load_vector")
        # Volume constraint — shares density_field via promotion
        self.add_subsystem(
            "constraint",
            VolumeConstraint(vol_frac=self.vol_frac),
            promotes=["density_field"],
        )

        self.set_input_defaults("load_vector", None)
