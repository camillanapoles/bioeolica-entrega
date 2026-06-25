# -*- coding: utf-8 -*-
"""KDI Forwarder — reads config.json, dispatches M³ analyses."""
from __future__ import annotations
import os, sys, importlib.util as _ilu
from typing import Any

_THIS = os.path.dirname(os.path.abspath(__file__))
_WS = os.path.abspath(os.path.join(_THIS, ".."))
_PROJ = os.path.abspath(os.path.join(_WS, ".."))

for _p in [os.path.join(_WS, "src"), os.path.join(_PROJ, "cad-cae-platform"), os.path.join(_PROJ, "physics-m3")]:
    if _p not in sys.path: sys.path.insert(0, _p)

from kdi_m3.config_manager import ConfigManager

def _imp(rel, name):
    s = _ilu.spec_from_file_location(name, os.path.join(_PROJ, rel))
    m = _ilu.module_from_spec(s); sys.modules.setdefault(name, m); s.loader.exec_module(m); return m

class KDIForwarder:
    def __init__(self, config_path=""):
        self.cfg = ConfigManager.load(config_path or os.path.join(_WS, "config.json"))
        self._results: dict[str, Any] = {}

    def run_macro(self):
        kdi_macro = _imp("kdi-m3-bridge/modules/kdi_macro.py", "kdi_macro")
        cad_bridge = _imp("cad-cae-platform/modules/cad_bridge.py", "cad_bridge")
        env = kdi_macro.MacroEnvironment(
            altitude_m=self.cfg.get("environment.altitude_m", 100),
            wind_class=self.cfg.get("environment.wind_class", "II"),
            wind_speed_ref_ms=self.cfg.get("environment.wind_speed_ref_ms", 30),
            exposure=self.cfg.get("environment.exposure", "rural"),
        )
        g = self.cfg.section("geometry")
        model = cad_bridge.CadModel().box(g.get("length_mm", 100), g.get("width_mm", 20), g.get("height_mm", 20))
        ma = kdi_macro.MacroAnalysis(cad_model=model, env=env, structure_type=g.get("type", "box"))
        result = ma.run(); self._results["macro"] = result; return result

    def run_meso(self, fem_results=None):
        kdi_meso = _imp("kdi-m3-bridge/modules/kdi_meso.py", "kdi_meso")
        r = kdi_meso.MesoAnalysis().run(); self._results["meso"] = r; return r

    def run_micro(self):
        kdi_micro = _imp("kdi-m3-bridge/modules/kdi_micro.py", "kdi_micro")
        mat = self.cfg.section("material")
        r = kdi_micro.MicroAnalysis(
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
