import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kdi_m3.kdi_meso import MesoAnalysis

def test_defaults():
    ma = MesoAnalysis()
    r = ma.run()
    assert "Kt" in r
    assert "safety_factor" in r

def test_kt_infinite_plate():
    ma = MesoAnalysis({"hole_diameter_mm": 5, "plate_width_mm": 50})
    r = ma.run()
    assert r["Kt"] == pytest.approx(3.0, rel=0.01)

def test_safety_pass():
    ma = MesoAnalysis({"nominal_stress_MPa": 50, "yield_strength_MPa": 500})
    r = ma.run()
    assert r["status"] == "PASS"

def test_from_config():
    ma = MesoAnalysis().from_config({"hole_diameter_mm": 10, "plate_width_mm": 100})
    r = ma.run()
    assert r["Kt"] == pytest.approx(3.0, rel=0.01)
