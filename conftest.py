"""Pytest config raiz — garante que workspace/ esteja importável e SQLite use :memory: por default."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
for cand in [ROOT / "workspace"]:
    p = str(cand)
    if p not in sys.path:
        sys.path.insert(0, p)
