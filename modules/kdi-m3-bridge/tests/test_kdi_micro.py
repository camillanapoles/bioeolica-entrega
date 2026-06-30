import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kdi_m3.kdi_micro import MicroAnalysis

def test_defaults():
    ma = MicroAnalysis()
    r = ma.run()
    assert "E1_GPa" in r
    assert r["E1_GPa"] > 0

def test_material_name():
    ma = MicroAnalysis(fiber="waste_paper", matrix="pva", coating="graphite_coating")
    r = ma.run()
    assert "waste_paper" in r["material"]

def test_from_config():
    cfg = {"fiber": "waste_paper", "matrix": "pva", "V_f": 0.20}
    ma = MicroAnalysis().from_config(cfg)
    r = ma.run()
    assert r["V_f"] == 0.20

def test_vf_affects_e1():
    ma1 = MicroAnalysis(V_f=0.30)
    ma2 = MicroAnalysis(V_f=0.60)
    r1 = ma1.run()
    r2 = ma2.run()
    assert r2["E1_GPa"] >= r1["E1_GPa"] * 0.5
