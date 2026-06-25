"""
src/thermo/fluid_properties.py — Wrapper for CoolProp.
Provides a unified interface for fluid property retrieval (M4 Single Source of Truth).
"""

try:
    from CoolProp.CoolProp import PropsSI
    _COOLPROP_AVAILABLE = True
except ImportError:
    _COOLPROP_AVAILABLE = False

class FluidProperties:
    """
    Retrieves thermodynamic properties using CoolProp.
    """
    def __init__(self, fluid_name: str = "air"):
        if not _COOLPROP_AVAILABLE:
            raise ImportError("CoolProp is not installed. Please install with 'pip install coolprop'.")
        self.fluid_name = fluid_name

    def get_density(self, T_K: float, P_Pa: float) -> float:
        """Returns density [kg/m^3] given Temperature [K] and Pressure [Pa]."""
        return PropsSI('D', 'T', T_K, 'P', P_Pa, self.fluid_name)

    def get_viscosity(self, T_K: float, P_Pa: float) -> float:
        """Returns dynamic viscosity [Pa*s] given Temperature [K] and Pressure [Pa]."""
        return PropsSI('V', 'T', T_K, 'P', P_Pa, self.fluid_name)

    def get_heat_capacity(self, T_K: float, P_Pa: float) -> float:
        """Returns specific heat capacity cp [J/kg/K] given Temperature [K] and Pressure [Pa]."""
        return PropsSI('C', 'T', T_K, 'P', P_Pa, self.fluid_name)
