"""core/build_ssot.py — gera SSOT consolidado a partir de N SQLite (workflow arrastável).

Uso:
  python -m core.build_ssot \
      --db lab1=path/to/lab1.db \
      --db lab2=path/to/lab2.db \
      --out data/json/ssot_consolidado.json

Sem nomes de laboratório hardcoded (P$1): os rótulos vêm da CLI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_THIS = Path(__file__).resolve().parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

from core.db import Database  # noqa: E402


def _dump_db(db_path: str) -> dict:
    if db_path == ":memory:" or not Path(db_path).exists():
        return {"status": "vazio", "path": db_path}
    db = Database(db_path)
    out = {
        "materials": [dict(r) for r in db.connection.execute("SELECT * FROM materials")],
        "results": [dict(r) for r in db.connection.execute("SELECT * FROM results")],
        "simulacoes": [dict(r) for r in db.connection.execute("SELECT * FROM simulacoes")],
    }
    db.close()
    return out


def build_ssot(dbs: dict[str, str], out_path: Path) -> dict:
    out = {"_meta": {"doc": "SSOT gerado por build_ssot.py", "labs": list(dbs)}}
    for label, db_path in dbs.items():
        out[label] = _dump_db(db_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return out


def _parse_kv(s: str) -> tuple[str, str]:
    if "=" not in s:
        raise SystemExit(f"--db exige formato label=caminho (recebido: {s})")
    k, v = s.split("=", 1)
    return k.strip(), v.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera SSOT consolidado dos labs.")
    ap.add_argument("--db", action="append", required=True,
                    help="label=caminho.db (repita para cada lab)")
    ap.add_argument("--out", default="data/json/ssot_consolidado.json")
    args = ap.parse_args()
    dbs = dict(_parse_kv(x) for x in args.db)
    p = Path(args.out)
    build_ssot(dbs, p)
    print(f"SSOT -> {p}  labs={list(dbs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
