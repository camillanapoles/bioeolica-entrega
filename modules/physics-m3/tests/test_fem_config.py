"""Spec 014 Phase 1 - ConfigManager wiring tests for fem_solver.BeamElement.

Verifies:
  1. cfg=None backward compat (uses _DEFAULT_NU = 0.3)
  2. cfg with nu=0.25 produces different G than default
  3. cfg.get() is NOT called inside stiffness_matrix (caveat 3 - cached)
  4. rho override works through cfg
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import numpy as np
import pytest
from fem_solver import BeamElement, _DEFAULT_NU


class FakeCfg:
    """Minimal cfg stand-in mimicking ConfigManager.get(key, default)."""
    def __init__(self, **vals):
        self._vals = vals
    def get(self, key, default=None):
        return self._vals.get(key, default)


def test_backward_compat_no_cfg():
    """BeamElement with cfg=None uses _DEFAULT_NU = 0.3."""
    elem = BeamElement()
    assert elem._nu == _DEFAULT_NU
    assert elem._nu == 0.3
    k = elem.stiffness_matrix()
    assert k.shape == (12, 12)
    # Torsion block at DOF 3,3 should be non-zero for default nu
    assert k[3, 3] > 0


def test_cfg_overrides_nu():
    """cfg with nu=0.25 produces different G (and different k[3,3])."""
    cfg = FakeCfg(**{"material.nu": 0.25})
    elem_default = BeamElement()
    elem_override = BeamElement(cfg=cfg)
    assert elem_default._nu == 0.3
    assert elem_override._nu == 0.25
    # Torsion stiffness G*J/L differs because G differs
    k_def = elem_default.stiffness_matrix()
    k_ovr = elem_override.stiffness_matrix()
    assert k_def[3, 3] != k_ovr[3, 3], "nu override did not change torsion stiffness"
    # Expected ratio: G_ovr / G_def = (1+0.3)/(1+0.25) = 1.04
    ratio = k_ovr[3, 3] / k_def[3, 3]
    assert abs(ratio - 1.3 / 1.25) < 1e-9, f"unexpected stiffness ratio {ratio}"


def test_cfg_overrides_rho():
    """cfg with rho_kgm3=2000 doubles the mass matrix entries."""
    cfg = FakeCfg(**{"material.rho_kgm3": 2400.0})
    elem_default = BeamElement(rho_kgm3=1200.0)
    elem_override = BeamElement(rho_kgm3=1200.0, cfg=cfg)
    assert elem_override._rho_resolved == 2400.0
    m_def = elem_default.mass_matrix()
    m_ovr = elem_override.mass_matrix()
    assert abs(m_ovr[0, 0] / m_def[0, 0] - 2.0) < 1e-9


def test_no_cfg_lookup_in_hot_path():
    """Caveat 3: resolve() / cfg.get() not called inside stiffness_matrix.

    Mutate cfg to return a different nu AFTER construction; the cached
    _nu must remain unchanged. This proves the value is cached, not
    re-read on every stiffness_matrix call.
    """
    cfg = FakeCfg(**{"material.nu": 0.25})
    elem = BeamElement(cfg=cfg)
    cached_nu = elem._nu
    # Now mutate cfg - if stiffness_matrix re-reads, nu would change
    cfg._vals["material.nu"] = 0.40
    k_before = elem.stiffness_matrix().copy()
    cfg._vals["material.nu"] = 0.10
    k_after = elem.stiffness_matrix()
    # Cached nu must NOT have changed
    assert elem._nu == cached_nu == 0.25
    # Stiffness must NOT have changed (proves no re-read)
    assert np.allclose(k_before, k_after), "stiffness_matrix re-read cfg (Caveat 3 violation)"


def test_explicit_nu_default_isolated():
    """Independent BeamElement instances don't share cfg state."""
    a = BeamElement(cfg=FakeCfg(**{"material.nu": 0.20}))
    b = BeamElement()
    assert a._nu == 0.20
    assert b._nu == 0.3
    assert a._nu != b._nu
