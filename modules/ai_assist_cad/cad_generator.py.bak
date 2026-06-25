"""ai_assist_cad/cad_generator.py"""
import os
from typing import Dict, List, Optional

MACHINE_TEMPLATES = {
    "generator": {
        "stator": {"type": "cylinder", "default_diameter_mm": 400},
        "rotor": {"type": "cylinder", "default_diameter_mm": 310},
        "shaft": {"type": "cylinder", "default_diameter_mm": 80},
    },
    "turbine": {
        "blade": {"type": "airfoil", "default_chord_m": 0.3},
        "hub": {"type": "cylinder", "default_diameter_mm": 200},
        "tower": {"type": "cylinder", "default_diameter_mm": 300},
    },
    "compressor": {
        "casing": {"type": "cylinder", "default_diameter_mm": 250},
        "piston": {"type": "cylinder", "default_diameter_mm": 100},
        "shaft": {"type": "cylinder", "default_diameter_mm": 50},
    },
    "motor": {
        "stator": {"type": "cylinder", "default_diameter_mm": 350},
        "rotor": {"type": "cylinder", "default_diameter_mm": 280},
        "shaft": {"type": "cylinder", "default_diameter_mm": 70},
    },
}


class CADGenerator:
    """Gera geometria paramétrica baseada em templates de máquina."""

    def __init__(self, knowledge_engine=None):
        self.ke = knowledge_engine
        self.components: List[Dict] = []

    def generate(self, params: Dict) -> Dict:
        machine = params.get("machine_type", "generator")
        materials = params.get("materials", ["steel"])
        template = MACHINE_TEMPLATES.get(machine, MACHINE_TEMPLATES["generator"])
        self.components = []

        for comp_name, comp_def in template.items():
            component = {
                "name": comp_name,
                "type": comp_def["type"],
                "material": materials[0] if materials else "steel",
                "params": comp_def,
            }
            # Apply knowledge engine dimensioning if available
            if self.ke and machine == "generator" and comp_name == "shaft":
                torque = (params.get("power_kW", 1000) * 9550) / max(params.get("rpm", 1500), 1)
                shaft = self.ke.dimension_shaft(torque_Nm=torque)
                component["params"]["diameter_mm"] = shaft["diameter_mm"]
            self.components.append(component)

        return {
            "machine": machine,
            "components": self.components,
            "total_parts": len(self.components),
            "materials_used": materials,
        }

    def generate_step(self, output_dir: str = "/tmp/cad_output") -> List[str]:
        """Gera arquivos STEP simulados (placeholder — CadQuery real na Fase 2)."""
        os.makedirs(output_dir, exist_ok=True)
        exported = []
        for comp in self.components:
            path = os.path.join(output_dir, f"{comp['name']}.step")
            with open(path, "w") as f:
                f.write(f"STEP FILE: {comp['name']}\nTYPE: {comp['type']}\n")
            exported.append(path)
        return exported
