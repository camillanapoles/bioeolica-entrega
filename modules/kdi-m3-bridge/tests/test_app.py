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
    import importlib.util
    _PROJ = "/home/cnmfs/bioeolica-dev2/workspaces"
    ok = True
    for rel, name in [
        ("kdi-m3-bridge/modules/kdi_forwarder.py", "kdi_forwarder"),
        ("cad-cae-platform/modules/cad_bridge.py", "cad_bridge"),
    ]:
        try:
            spec = importlib.util.spec_from_file_location(name, os.path.join(_PROJ, rel))
            m = importlib.util.module_from_spec(spec)
            sys.modules[name] = m
            spec.loader.exec_module(m)
        except Exception:
            ok = False
    assert ok


def test_config_section():
    with open(APP_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "Material" in content or "Fiber" in content or "fiber" in content
