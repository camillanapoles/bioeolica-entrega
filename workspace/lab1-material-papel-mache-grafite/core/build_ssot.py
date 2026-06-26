"""core/build_ssot.py — gera mapa unico de informacao a partir do SQLite dos labs.

Workflow arrastavel: roda em qualquer ambiente (local, CI). Sem hardcoded.
Uso: python -m core.build_ssot --lab1 <db> --lab2 <db> --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_THIS = Path(__file__).resolve().parent
_LAB2 = _THIS.parents[0].parent / "lab2-gerador-eolico-savonius"
for p in (str(_THIS.parents[0]), str(_LAB2)):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.db import Database  # noqa: E402


def build_ssot(lab1_db_path: str, lab2_db_path: str, out_path: Path) -> dict:
    out = {"_meta": {"doc": "SSOT gerado por build_ssot.py", "labs": ["lab1", "lab2"]}}
    for label, db_path in [("lab1", lab1_db_path), ("lab2", lab2_db_path)]:
        if db_path == ":memory:" or not Path(db_path).exists():
            out[label] = {"status": "vazio", "path": db_path}
            continue
        db = Database(db_path)
        out[label] = {
            "materials": [dict(r) for r in db.connection.execute("SELECT * FROM materials")],
            "results": [dict(r) for r in db.connection.execute("SELECT * FROM results")],
            "simulacoes": [dict(r) for r in db.connection.execute("SELECT * FROM simulacoes")],
        }
        db.close()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera SSOT consolidado dos labs.")
    ap.add_argument("--lab1", default=":memory:")
    ap.add_argument("--lab2", default=":memory:")
    ap.add_argument("--out", default="data/json/ssot_consolidado.json")
    args = ap.parse_args()
    p = Path(args.out)
    build_ssot(args.lab1, args.lab2, p)
    print(f"SSOT -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
