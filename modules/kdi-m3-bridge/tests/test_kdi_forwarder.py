import pytest, os
from modules.kdi_forwarder import KDIForwarder

@pytest.fixture
def kf():
    cfg = os.path.join(os.path.dirname(__file__), "..", "config.json")
    return KDIForwarder(cfg)

def test_init(kf):
    assert kf.cfg is not None

def test_run_macro(kf):
    r = kf.run_macro()
    assert "dimensions_mm" in r

def test_run_meso(kf):
    r = kf.run_meso()
    assert "Kt" in r

def test_run_micro(kf):
    r = kf.run_micro()
    assert "E1_GPa" in r

def test_run_all(kf):
    results = kf.run_all()
    assert "macro" in results
    assert "meso" in results

def test_report(kf):
    r = kf.report()
    assert "KDI-M³ REPORT" in r
