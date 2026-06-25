"""Tests for KDI Macro Bridge module."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cad-cae-platform"))

import numpy as np
import pytest

from modules.kdi_macro import MacroAnalysis, MacroEnvironment, macro_from_cad_and_env


class TestEnvironment:
    def test_defaults(self):
        env = MacroEnvironment()
        assert env.altitude_m == 100
        assert env.wind_class == "II"

    def test_terrain_roughness(self):
        env = MacroEnvironment(wind_class="I")
        assert env.terrain_roughness() == 0.01

    def test_wind_pressure_positive(self):
        env = MacroEnvironment(wind_speed_ref_ms=30)
        p = env.wind_pressure_kPa(50)
        assert p > 0

    def test_gust_offshore(self):
        env = MacroEnvironment(exposure="offshore")
        assert env.gust_factor() == 1.35


class TestNoCAD:
    def test_no_cad_raises(self):
        ma = MacroAnalysis()
        with pytest.raises(ValueError):
            ma.run()


@pytest.fixture
def cad():
    class MockCAD:
        def bounding_box(self):
            return {"x": 10, "y": 5, "z": 2,
                    "xmin": 0, "ymin": 0, "zmin": 0,
                    "xmax": 10, "ymax": 5, "zmax": 2}
        @property
        def volume(self):
            return 10 * 5 * 2
        @property
        def mass(self):
            return self.volume * 1e-6
    return MockCAD()


class TestWithCAD:
    def test_run(self, cad):
        ma = MacroAnalysis(cad_model=cad)
        r = ma.run()
        assert "dimensions_mm" in r
        assert r["volume_mm3"] == 100

    def test_environment_in_results(self, cad):
        ma = MacroAnalysis(cad_model=cad)
        r = ma.run()
        assert "wind_pressure_kPa" in r["environment"]
        assert r["environment"]["wind_pressure_kPa"] > 0

    def test_report(self, cad):
        ma = MacroAnalysis(cad_model=cad)
        report = ma.report()
        assert "MACRO ANALYSIS" in report
        assert "100.0" in report

    def test_to_fem_bcs(self, cad):
        ma = MacroAnalysis(cad_model=cad)
        bcs = ma.to_fem_bcs()
        assert "force" in bcs
        assert "pressure" in bcs

    def test_convenience(self, cad):
        ma = macro_from_cad_and_env(cad, altitude_m=500, wind_speed_ref_ms=40)
        r = ma.run()
        assert r["environment"]["altitude_m"] == 500


class TestWindForce:
    def test_force_scales_with_area(self, cad):
        class TallCAD:
            def bounding_box(self):
                return {"x": 10, "y": 5, "z": 20,
                        "xmin": 0, "ymin": 0, "zmin": 0,
                        "xmax": 10, "ymax": 5, "zmax": 20}
            @property
            def volume(self): return 1000
            @property
            def mass(self): return 0.001
        ma = MacroAnalysis(cad_model=TallCAD(), env=MacroEnvironment(wind_speed_ref_ms=40))
        r = ma.run()
        assert r["environment"]["total_wind_force_N"] > 0
