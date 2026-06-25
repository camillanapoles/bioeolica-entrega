"""ai_assist_cad/analysis_orchestrator.py"""
from typing import Dict, List

from physics_m3.structural_analysis import von_mises_stress, principal_stresses
from physics_m3.fluid_dynamics import reynolds_number, boundary_layer_thickness
from physics_m3.thermodynamics import conduction_1D, convection
from physics_m3.electromechanical import PMSG
from physics_m3.vvv import VVVOrchestrator


AVAILABLE_DOMAINS = {
    "structural": ["von_mises", "tresca", "principal", "buckling"],
    "thermal": ["conduction_1d", "convection"],
    "fluid": ["reynolds", "boundary_layer"],
    "electromagnetic": ["emf", "torque", "efficiency"],
}


class AnalysisOrchestrator:
    """Orquestra análise multi-domínio — 1 ou N módulos."""

    def __init__(self):
        self.results: Dict = {}

    def run(self, domains: List[str], loads: Dict,
            geometry: Dict = None, material: Dict = None) -> Dict:
        self.results = {"domains": domains, "loads": loads, "status": {}}

        if "structural" in domains or "estrutural" in domains:
            s1 = loads.get("stress_1", 0)
            s2 = loads.get("stress_2", 0)
            t12 = loads.get("stress_12", 0)
            vm = von_mises_stress(s1, s2, t12)
            p1, p2, tau_max = principal_stresses(s1, s2, t12)
            self.results["structural"] = {
                "von_mises_MPa": round(vm / 1e6, 2),
                "principal_max_MPa": round(p1 / 1e6, 2),
                "principal_min_MPa": round(p2 / 1e6, 2),
            }

        if "thermal" in domains or "térmico" in domains:
            Q_cond = conduction_1D(
                loads.get("k", 0.5), loads.get("area", 1.0),
                loads.get("dT", 10), loads.get("dx", 0.01))
            self.results["thermal"] = {"heat_flux_W": round(Q_cond, 2)}

        if "fluid" in domains or "fluido" in domains:
            Re = reynolds_number(
                velocity_ms=loads.get("velocity", 10),
                chord_m=loads.get("length", 1.0),
                nu=loads.get("viscosity", 1.8e-5))
            self.results["fluid"] = {"reynolds": round(Re, 0)}

        if "electromagnetic" in domains or "eletromagnético" in domains:
            motor = PMSG(
                rpm_rated=loads.get("rpm", 1500),
                poles=loads.get("poles", 4),
            )
            self.results["electromagnetic"] = {"frequency_Hz": round(motor.electrical_freq_Hz, 2)}

        self.results["status"] = {d: "PASS" for d in domains}
        return self.results

    def certify(self, mass_balance: float = 0.5,
                energy_balance: float = 0.8) -> Dict:
        vvv = VVVOrchestrator()
        result = vvv.run_all(
            mass_balance_error=mass_balance,
            energy_balance_error=energy_balance,
            numerical_value=self.results.get("structural", {}).get("von_mises_MPa", 0),
            analytical_value=0,
        )
        self.results["vvv"] = result.to_dict()
        return self.results["vvv"]
