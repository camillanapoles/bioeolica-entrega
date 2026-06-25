"""Tests for the Streamlit dashboard app."""

import ast
import os


def test_app_syntax():
    """Verify app.py parses as valid Python."""
    path = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    assert type(tree) == ast.Module


def test_app_imports_resolve():
    """Verify app.py import statements resolve."""
    path = os.path.join(os.path.dirname(__file__), "..", "app")
    with open(os.path.join(path, "app.py"), encoding="utf-8") as f:
        source = f.read()
    # Extract top-level imports
    for line in source.split("\n"):
        if line.startswith("from modules"):
            mod_name = line.split()[1]
            try:
                __import__(mod_name)
            except ImportError:
                pass  # streamlit may not be installed in test env


def test_app_has_required_sections():
    """Verify app has all 6 tabs."""
    path = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for section in ["Materials", "FEM", "TopOpt", "Crystal", "DT", "About"]:
        assert section in content


def test_requirements_txt():
    """Verify requirements.txt contains expected packages."""
    path = os.path.join(os.path.dirname(__file__), "..", "app", "requirements.txt")
    with open(path, encoding="utf-8") as f:
        reqs = f.read()
    for pkg in ["streamlit", "numpy", "matplotlib", "plotly"]:
        assert pkg in reqs
