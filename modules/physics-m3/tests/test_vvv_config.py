"""Test VVVReinforced reading thresholds from ConfigManager."""

import numpy as np
from physics_m3.vvv_reinforced import VVVReinforced
from kdi_m3.config_manager import ConfigManager


def test_vvv_with_config():
    """Override threshold via cfg and verify certification changes."""
    cfg = ConfigManager({
        "vvv": {
            "rmse_threshold": 0.5,
            "r2_threshold": 0.0,
            "max_error_threshold": 1.0,
            "relative_error_threshold": 50.0,
        }
    })
    vvv = VVVReinforced(cfg=cfg)
    sim = np.array([1.0, 2.0, 3.0])
    exp = np.array([1.5, 2.0, 2.5])
    res = vvv.validate("test_case", sim, exp)
    assert res.certified is True  # now all criteria are loose enough


def test_vvv_without_config():
    """Without cfg, use hardcoded defaults."""
    vvv = VVVReinforced()
    sim = np.array([1.0, 2.0, 3.0])
    exp = np.array([10.0, 20.0, 30.0])
    res = vvv.validate("no_cfg", sim, exp)
    assert res.certified is False
