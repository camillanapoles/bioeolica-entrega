# -*- coding: utf-8 -*-
"""KDI Forwarder — reads config.json, dispatches M³ analyses."""
from __future__ import annotations
import os, sys
from typing import Any

_THIS = os.path.dirname(os.path.abspath(__file__))
_WS = os.path.abspath(os.path.join(_THIS, ".."))
_PROJ = os.path.abspath(os.path.join(_WS, ".."))

for _p in [_WS]:
    if _p not in sys.path: sys.path.insert(0, _p)

# cad-cae-platform for CadModel
sys.path.insert(0, os.path.join(_PROJ, "modules", "cad-cae-platform", "src"))

from kdi_m3.config_manager import ConfigManager
from kdi_m3.kdi_macro import MacroEnvironment, MacroAnalysis
from kdi_m3.kdi_meso import MesoAnalysis
from kdi_m3.kdi_micro import MicroAnalysis
from cad_cae.cad_bridge import CadModel

class KDIForwarder:
    def __init__(self, config_path=""):
        self.cfg = ConfigManager.load(config_path or os.path.join(_WS, "config.json"))
        self._results: dict[str, Any] = {}

    def run_macro(self):
        env = MacroEnvironment(
            altitude_m=self.cfg.get("environment.altitude_m", 100),
            wind_class=self.cfg.get("environment.wind_class", "II"),
            wind_speed_ref_ms=self.cfg.get("environment.wind_speed_ref_ms", 30),
            exposure=self.cfg.get("environment.exposure", "rural"),
        )
        g = self.cfg.section("geometry")
        model = CadModel().box(g.get("length_mm", 100), g.get("width_mm", 20), g.get("height_mm", 20))
        ma = MacroAnalysis(cad_model=model, env=env, structure_type=g.get("type", "box"))
        result = ma.run(); self._results["macro"] = result; return result

    def run_meso(self, fem_results=None):
        r = MesoAnalysis().run(); self._results["meso"] = r; return r

    def run_micro(self):
        mat = self.cfg.section("material")
        r = MicroAnalysis(
            fiber=mat.get("fiber", "waste_paper"), matrix=mat.get("matrix", "pva"),
            coating=mat.get("coating", "graphite_coating"), V_f=mat.get("V_f", 0.15)
        ).run()
        self._results["micro"] = r; return r

    def run_all(self):
        kdi = self.cfg.section("kdi"); results = {}
        if kdi.get("macro", {}).get("enabled", True): results["macro"] = self.run_macro()
        if kdi.get("meso", {}).get("enabled", True): results["meso"] = self.run_meso(results.get("macro", {}))
        if kdi.get("micro", {}).get("enabled", False): results["micro"] = self.run_micro()
        self._results = results; return results

    def report(self):
        if not self._results: self.run_all()
        lines = ["=" * 60, f"KDI-M³ REPORT — {self.cfg.get('project.name', 'default')}", "=" * 60, ""]
        for scale, result in self._results.items():
            lines.append(f"[{scale.upper()}]")
            if isinstance(result, dict):
                for k, v in list(result.items())[:6]:
                    if not isinstance(v, (dict, list)): lines.append(f"  {k}: {v}")
            lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    @property
    def results(self):
        return self._results if self._results else self.run_all()
