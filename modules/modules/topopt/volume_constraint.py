"""
Volume constraint component — computes volume fraction from density field.

volume_fraction = (1/n) * sum(rho_i)
"""

import numpy as np
import openmdao.api as om


class VolumeConstraint(om.ExplicitComponent):
    """
    Compute volume fraction from density field.

    Inputs:
        density_field : (n_elem,) element densities in [0, 1]
    Outputs:
        volume_fraction : scalar volume fraction
    """

    def __init__(self, vol_frac: float = 0.3):
        super().__init__()
        self.target_vol_frac = vol_frac

    def setup(self):
        self.add_input("density_field", shape_by_conn=True, tags=["topopt"])
        self.add_output("volume_fraction", shape=(1,), tags=["topopt"])
        self.declare_partials("volume_fraction", "density_field",
                              method="fd", form="central", step=1e-6)

    def compute(self, inputs, outputs):
        x = inputs["density_field"]
        outputs["volume_fraction"] = np.mean(x)
