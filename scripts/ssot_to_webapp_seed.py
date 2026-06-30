#!/usr/bin/env python3
"""SSOT → webapp seed bridge (Mandato B.0 / "mesma DB").

Reads the project Single Source of Truth
(`workspace/lab1-material-papel-mache-grafite/config/constants.json`) and emits
a derived, webapp-consumable manifest at `webapp/_seed_from_ssot.json`.

This is the **CI/CD backbone of the "same DB" mandate**: editing a constant in
constants.json propagates to the webapp catalog + hard-cost unit references
*without any manual edit of seed.js*. Run by `.github/workflows/sync-ssot.yml`
on every change to the SSOT; the workflow auto-commits the regenerated file.

Exit codes:
  0 — seed regenerated (changed or identical)
  2 — constants.json missing or invalid JSON (fails the CI gate)

Usage:
  python3 scripts/ssot_to_webapp_seed.py [--root REPO_ROOT] [--check]
  --check : regenerate in-memory, report whether the on-disk file would change,
            do NOT write. Exit 3 if it would change (useful as a CI gate).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SSOT_REL = "workspace/lab1-material-papel-mache-grafite/config/constants.json"
OUT_REL = "webapp/_seed_from_ssot.json"


def _dig(obj, dotted):
    """Resolve a dotted path (e.g. 'modules.blade_design.Cp_max')."""
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"SSOT path not found: {dotted} (failed at '{part}')")
        cur = cur[part]
    return cur


def load_ssot(ssot_path: Path) -> dict:
    """Load + validate the SSOT. Raises on invalid JSON."""
    if not ssot_path.exists():
        raise FileNotFoundError(f"SSOT not found: {ssot_path}")
    with open(ssot_path, encoding="utf-8") as f:
        return json.load(f)  # raises json.JSONDecodeError → CI gate fails


def build_seed(ssot: dict) -> dict:
    """Derive the webapp manifest (catalog + hard costs + paper params) from SSOT."""
    material_db = _dig(ssot, "modules.physics_m3.composite.material_db")
    composite_model = ssot["modules"]["composite_model"]
    blade = ssot["modules"]["blade_design"]
    lca = ssot["modules"]["lca"]
    econ = ssot["economico"]
    lab2_orc = ssot["lab2"]["orcamento"]
    aging = ssot["sim"]["envelhecimento"]

    # ---- Catalog: every material in material_db typed for the webapp ----
    catalog = []
    for key, m in material_db.items():
        if not isinstance(m, dict) or "type" not in m:
            continue
        catalog.append({
            "id": key,
            "tipo": m["type"],
            "E_GPa": m.get("E_GPa"),
            "tensile_MPa": m.get("tensile_MPa"),
            "density_kgm3": m.get("density_kgm3"),
            "cost_brl_kg": m.get("cost_per_kg"),
            "descricao": m.get("description", ""),
            "ssot_path": f"modules.physics_m3.composite.material_db.{key}",
        })

    # ---- Hard costs: unit costs referenced by the orcamento engine ----
    hard_costs = {
        "processo_brl_kg":   econ["custo_processo_brl_kg"],
        "taxa_desconto":     econ["taxa_desconto"],
        "baseline_pa_brl":   econ["custo_baseline_pa_brl"],
        "biodegradabilidade": econ["biodegradabilidade"],
        "lab2_composito_brl_kg":  lab2_orc["custo_kg_composito"],
        "lab2_fibra_brl_kg":      lab2_orc["custo_kg_fibra"],
        "lab2_pmg_brl":           lab2_orc["custo_pmg_brl"],
        "lab2_estrutura_brl":     lab2_orc["custo_estrutura_brl"],
        "lab2_densidade_fibra":   lab2_orc["densidade_fibra_vidro"],
    }

    # ---- Paper/engineering parameters (provenance: webapp knows these come from SSOT) ----
    paper_params = {
        "rho_air":      blade["rho_air"],
        "Cp_max":       blade["Cp_max"],
        "lambda_opt":   blade["lambda_opt"],
        "sigma_Cp":     blade["sigma_Cp"],
        "rotor_D_m":    blade["rotor_D"],
        "rotor_H_m":    blade["rotor_H"],
        "Ke":           blade["Ke"],
        "R_int_ohm":    blade["R_int"],
        "P_loss_const_W": blade["P_loss_const"],
        "E_matrix_Pa":  composite_model["E_matrix"],
        "E_filler_Pa":  composite_model["E_filler"],
        "V_f":          composite_model["V_f"],
        "xi":           composite_model["xi"],
        "blade_mass_kg":     lca["BLADE_MASS_KG"],
        "paper_mass_kg":     lca["PAPER_MASS_PER_BLADE_KG"],
        "pva_mass_kg":       lca["PVA_MASS_PER_BLADE_KG"],
        "graphite_mass_kg":  lca["GRAPHITE_MASS_PER_BLADE_KG"],
    }

    aging_params = {
        "taxa_base_degrad": aging["taxa_base_degrad"],
        "sigma_ruido":      aging["sigma_ruido"],
        "n_amostras":       aging["n_amostras"],
        "ciclos_max":       aging["ciclos_max"],
        "seed":             aging["seed"],
    }

    # ---- Projeto FINEP: meta + cronograma (M1–M6) + roadmap de implementação ----
    # P$1: a página webapp (aba Cronograma + aba Roadmap) lê ESTES dados, não literais JS.
    projeto = ssot.get("projeto", {})
    projeto_out = {
        "meta": projeto.get("meta", {}),
        "cronograma": projeto.get("cronograma", {"duracao_meses": 36, "marcos": []}),
        "roadmap": projeto.get("roadmap", {"fases": []}),
    }

    return {
        "_meta": {
            "doc": "Manifest derivado da SSOT (constants.json) pelo CI/CD sync-ssot.yml. "
                   "Não editar à mão — regenerado a cada mudança da SSOT (Mandato B.0 / 'mesma DB').",
            "gerado_por": "scripts/ssot_to_webapp_seed.py",
            "ssot_source": SSOT_REL,
        },
        "catalogo": catalog,
        "hard_costs": hard_costs,
        "paper_params": paper_params,
        "aging_params": aging_params,
        "projeto": projeto_out,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SSOT → webapp seed bridge")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="repo root")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 3 if on-disk file differs from regenerated")
    args = ap.parse_args(argv)

    root = Path(args.root)
    ssot_path = root / SSOT_REL
    out_path = root / OUT_REL

    try:
        ssot = load_ssot(ssot_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ SSOT inválido/ausente: {e}", file=sys.stderr)
        return 2

    seed = build_seed(ssot)
    rendered = json.dumps(seed, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        if existing != rendered:
            print(f"⚠️  {OUT_REL} está DESATUALIZADO em relação à SSOT — rode o sync.", file=sys.stderr)
            return 3
        print(f"✓ {OUT_REL} sincronizado com a SSOT.")
        return 0

    changed = (not out_path.exists()) or out_path.read_text(encoding="utf-8") != rendered
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")

    n_cat = len(seed["catalogo"])
    if changed:
        print(f"✓ {OUT_REL} regenerado ({n_cat} materiais no catálogo).")
    else:
        print(f"✓ {OUT_REL} sem mudanças ({n_cat} materiais).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
