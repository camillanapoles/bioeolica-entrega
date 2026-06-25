"""
Compliance component — computes compliance objective from displacements and load.

Simple dot product: compliance = f^T * u.
"""

import numpy as np
import openmdao.api as om


class ComplianceComponent(om.ExplicitComponent):
    """
    Compute compliance = f^T * u.

    Inputs:
        displacements : (ndof,) nodal displacements
        load_vector   : (ndof,) nodal forces
    Outputs:
        compliance_value : scalar compliance
    """

    def setup(self):
        self.add_input("displacements", shape_by_conn=True, tags=["topopt"])
        self.add_input("load_vector", shape_by_conn=True, tags=["topopt"])
        self.add_output("compliance_value", shape=(1,), tags=["topopt"])
        self.declare_partials("*", "*", method="fd", form="central", step=1e-6)

    def compute(self, inputs, outputs):
        u = inputs["displacements"]
        f = inputs["load_vector"]
        outputs["compliance_value"] = np.dot(f, u)
