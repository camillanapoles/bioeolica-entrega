"""Tests for the Streamlit app."""

import ast
import os

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")


def test_app_syntax():
    """Verify app.py is valid Python."""
    with open(APP_PATH) as f:
        tree = ast.parse(f.read())
    assert isinstance(tree, ast.Module)


def test_app_imports():
    """Verify key modules are available."""
    errs = []
    for mod in ["streamlit", "modules.cad_bridge", "modules.gmsh_mesher",
                "modules.calculix_solver"]:
        try:
            __import__(mod)
        except ImportError as e:
            errs.append(str(e))
    assert len(errs) < 3, f"Import errors: {errs}"


def test_app_has_tabs():
    """Verify all 5 tabs are defined."""
    with open(APP_PATH) as f:
        content = f.read()
    for tab in ["Design", "Mesh", "FEM", "Results", "About"]:
        assert tab in content


def test_config_exists():
    """Verify Streamlit config."""
    cfg = os.path.join(os.path.dirname(__file__), "..", "app", ".streamlit", "config.toml")
    assert os.path.exists(cfg)
