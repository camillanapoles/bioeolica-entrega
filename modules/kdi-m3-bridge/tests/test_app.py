"""Tests for KDI-M³ Dashboard app."""

import ast
import os
import sys

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")


def test_syntax():
    with open(APP_PATH, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    assert isinstance(tree, ast.Module)


def test_has_tabs():
    with open(APP_PATH, encoding="utf-8") as f:
        content = f.read()
    for tab in ["Config", "Macro", "Meso", "Micro", "Report"]:
        assert tab in content


def test_imports_resolve():
    _THIS = os.path.dirname(os.path.abspath(__file__))
    _PROJ = os.path.abspath(os.path.join(_THIS, "..", ".."))
    _BRIDGE = os.path.join(_PROJ, "kdi-m3-bridge", "src")
    _CAE = os.path.join(_PROJ, "cad-cae-platform", "src")
    for _p in [_BRIDGE, _CAE]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
    try:
        from kdi_m3.kdi_forwarder import KDIForwarder
        from cad_cae.cad_bridge import CadModel
        ok = True
    except Exception:
        ok = False
    assert ok


def test_config_section():
    with open(APP_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "Material" in content or "Fiber" in content or "fiber" in content
