"""Spec 014 Phase 2 - ConfigManager wiring for Tier 2 modules.

Verifies cfg override + Caveat 3 caching for:
  - m3_analysis.PlyLayer (nu, rho)
  - mkdelagen.MaterialSpec (nu, rho)
  - peridynamics.PeridynamicsModel (rho)
  - structural_analysis.BeamSection (rho)
  - fatigue.FatigueAnalysis (Sy)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import pytest
from m3_analysis import PlyLayer, _DEFAULT_NU
from mkdelagen import MaterialSpec
from peridynamics import PeridynamicsModel
from structural_analysis import BeamSection
from fatigue import FatigueAnalysis


class FakeCfg:
    def __init__(self, **vals):
        self._vals = vals
    def get(self, key, default=None):
        return self._vals.get(key, default)


def test_plylayer_cfg_override():
    cfg = FakeCfg(**{"material.nu": 0.25, "material.rho_kgm3": 1800.0})
    p_default = PlyLayer(material="CFRP", thickness_mm=1.0)
    p_cfg = PlyLayer(material="CFRP", thickness_mm=1.0, cfg=cfg)
    assert p_default._nu == 0.3
    assert p_cfg._nu == 0.25
    assert p_cfg._rho_resolved == 1800.0


def test_materialspec_cfg_override():
    cfg = FakeCfg(**{"material.nu": 0.27, "material.rho_kgm3": 1600.0})
    m_default = MaterialSpec()
    m_cfg = MaterialSpec(cfg=cfg)
    assert m_default._nu == 0.3
    assert m_cfg._nu == 0.27
    assert m_cfg._rho_resolved == 1600.0


def test_peridynamics_cfg_override():
    cfg = FakeCfg(**{"material.rho_kgm3": 2200.0})
    pd_default = PeridynamicsModel()
    pd_cfg = PeridynamicsModel(cfg=cfg)
    assert pd_default._rho_resolved == 1200.0
    assert pd_cfg._rho_resolved == 2200.0


def test_beamsection_cfg_override():
    cfg = FakeCfg(**{"material.rho_kgm3": 1900.0})
    bs_default = BeamSection()
    bs_cfg = BeamSection(cfg=cfg)
    assert bs_default._rho_resolved == 1200.0
    assert bs_cfg._rho_resolved == 1900.0


def test_fatigue_cfg_override():
    cfg = FakeCfg(**{"material.yield_strength_MPa": 350.0})
    m_default = FatigueAnalysis()
    m_cfg = FatigueAnalysis(cfg=cfg)
    assert m_default._sy_resolved == 250.0
    assert m_cfg._sy_resolved == 350.0


def test_plylayer_backward_compat():
    p = PlyLayer(material="CFRP", thickness_mm=1.0)
    assert p._nu == _DEFAULT_NU == 0.3


def test_caveat3_no_hot_path_lookup_plylayer():
    cfg = FakeCfg(**{"material.nu": 0.25})
    p = PlyLayer(material="CFRP", thickness_mm=1.0, cfg=cfg)
    cached = p._nu
    cfg._vals["material.nu"] = 0.40
    assert p._nu == cached == 0.25, "PlyLayer re-read cfg (Caveat 3 violation)"
