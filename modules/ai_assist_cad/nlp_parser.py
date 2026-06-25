"""ai_assist_cad/nlp_parser.py"""
import re
from typing import Dict, Any, List

MACHINE_KEYWORDS = {
    "gerador": "generator", "motor": "motor", "turbina": "turbine",
    "compressor": "compressor", "bomba": "pump",
}
MATERIAL_KEYWORDS = {
    "aço": "steel", "alumínio": "aluminum", "cobre": "copper",
    "compósito": "composite", "papel": "paper", "grafite": "graphite",
    "resina": "resin", "cerâmica": "ceramic",
}
PROCESS_KEYWORDS = {
    "jateamento": "shot_blasting", "ultrassom": "ultrasound",
    "têmpera": "tempering", "oxidação": "oxidation",
    "soldagem": "welding", "laminação": "rolling",
}


def parse_project_parameters(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("No project description provided")

    result: Dict[str, Any] = {"materials": [], "processes": [], "layers": [],
                              "power_kW": None}
    text_lower = text.lower()

    for kw, val in MACHINE_KEYWORDS.items():
        if kw in text_lower:
            result["machine_type"] = val
            break
    result.setdefault("machine_type", "unknown")

    power_match = re.search(r'(\d+)\s*(?:MW|kw|kW|watt)', text_lower, re.IGNORECASE)
    if power_match:
        result["power_kW"] = float(power_match.group(1)) * (
            1000 if "MW" in power_match.group(0).upper() else 1
        )

    for kw, val in MATERIAL_KEYWORDS.items():
        if kw in text_lower:
            result["materials"].append(val)

    for kw, val in PROCESS_KEYWORDS.items():
        if kw in text_lower:
            result["processes"].append(val)

    layer_match = re.search(r'(\d+)\s*camadas?\s*(\d+)\s*mm', text_lower)
    if layer_match:
        result["layers"] = [{
            "material": result["materials"][-1] if result["materials"] else "unknown",
            "repetitions": int(layer_match.group(1)),
            "thickness_mm": float(layer_match.group(2)),
        }]

    return result
