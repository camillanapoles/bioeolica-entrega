"""Pytest config raiz — garante workspace/lab1 e workspace/lab2 importáveis."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
for lab in [
    ROOT / "workspace" / "lab1-material-papel-mache-grafite",
    ROOT / "workspace" / "lab2-gerador-eolico-savonius",
]:
    p = str(lab)
    if p not in sys.path:
        sys.path.insert(0, p)
