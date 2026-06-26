"""Conftest Lab2: Lab1 core reutilizável + path próprio."""
import sys
from pathlib import Path

LAB1 = Path(__file__).resolve().parents[1] / "lab1-material-papel-mache-grafite"
p = str(LAB1)
if p not in sys.path:
    sys.path.insert(0, p)
p2 = str(Path(__file__).parent)
if p2 not in sys.path:
    sys.path.insert(0, p2)
