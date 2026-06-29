import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "physics-m3", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cad-cae-platform", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kdi_m3.kdi_forwarder import KDIForwarder

_CAD_OK = False
try:
    from cad_cae.cad_bridge import _CADQUERY_AVAILABLE
    _CAD_OK = _CADQUERY_AVAILABLE
except ImportError:
    pass

@pytest.fixture
def kf():
    cfg = os.path.join(os.path.dirname(__file__), "..", "config.json")
    return KDIForwarder(cfg)

def test_init(kf):
    assert kf.cfg is not None

@pytest.mark.skipif(not _CAD_OK, reason="CadQuery not installed")
def test_run_macro(kf):
    r = kf.run_macro()
    assert "dimensions_mm" in r

def test_run_meso(kf):
    r = kf.run_meso()
    assert "Kt" in r

def test_run_micro(kf):
    r = kf.run_micro()
    assert "E1_GPa" in r

@pytest.mark.skipif(not _CAD_OK, reason="CadQuery not installed")
def test_run_all(kf):
    results = kf.run_all()
    assert "macro" in results
    assert "meso" in results

@pytest.mark.skipif(not _CAD_OK, reason="CadQuery not installed")
def test_report(kf):
    r = kf.report()
    assert "KDI-M³ REPORT" in r
