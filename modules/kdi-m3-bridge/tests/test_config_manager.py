"""Tests for ConfigManager module."""

import json, sys, tempfile, os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kdi_m3.config_manager import ConfigManager, create_default_config


class TestInit:
    def test_load_default(self):
        cfg = ConfigManager.from_defaults()
        assert cfg.get("environment.altitude_m") == 100

    def test_load_nonexistent_uses_defaults(self):
        """Loading a nonexistent path returns module defaults (graceful fallback)."""
        cfg = ConfigManager.load("/tmp/nonexistent_config_xyz_123456789.json")
        assert cfg is not None
        assert cfg.get("material.E_GPa", 0) == 210

    def test_create_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            create_default_config(f.name)
            cfg = ConfigManager.load(f.name)
        os.unlink(f.name)
        assert cfg.get("material.E_GPa") == 210

    def test_from_dict(self):
        data = {"environment": {"altitude_m": 500}}
        cfg = ConfigManager(data)
        assert cfg.get("environment.altitude_m") == 500


class TestGetSet:
    def test_get_dot_path(self):
        cfg = ConfigManager.from_defaults()
        assert cfg.get("material.E_GPa") == 210

    def test_get_nested(self):
        cfg = ConfigManager.from_defaults()
        assert cfg.get("solver.force_N.z") == -100

    def test_get_default(self):
        cfg = ConfigManager.from_defaults()
        assert cfg.get("nonexistent.key", 42) == 42

    def test_set_and_get(self):
        cfg = ConfigManager({})
        cfg.set("environment.altitude_m", 500)
        assert cfg.get("environment.altitude_m") == 500

    def test_set_deep(self):
        cfg = ConfigManager({})
        cfg.set("a.b.c.d", "deep")
        assert cfg.get("a.b.c.d") == "deep"

    def test_set_overwrites(self):
        cfg = ConfigManager.from_defaults()
        cfg.set("environment.altitude_m", 999)
        assert cfg.get("environment.altitude_m") == 999


class TestSection:
    def test_section_keys(self):
        cfg = ConfigManager.from_defaults()
        sec = cfg.section("environment")
        assert "altitude_m" in sec
        assert "wind_class" in sec

    def test_section_missing(self):
        cfg = ConfigManager({})
        assert cfg.section("nonexistent") == {}


class TestSave:
    def test_save_roundtrip(self):
        cfg = ConfigManager.from_defaults()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cfg.save(f.name)
            cfg2 = ConfigManager.load(f.name)
        os.unlink(f.name)
        assert cfg2.get("environment.altitude_m") == 100


class TestValidate:
    def test_valid_default(self):
        cfg = ConfigManager.from_defaults()
        assert cfg.validate() == []

    def test_invalid_returns_errors(self):
        cfg = ConfigManager({})
        errors = cfg.validate()
        assert len(errors) > 0

    def test_copy(self):
        cfg = ConfigManager.from_defaults()
        cfg2 = cfg.copy()
        cfg2.set("environment.altitude_m", 500)
        assert cfg.get("environment.altitude_m") == 100
        assert cfg2.get("environment.altitude_m") == 500
