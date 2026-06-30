#!/usr/bin/env python3
"""Environment-mandatory hygiene gate.

Mandato: todo ambiente de desenvolvimento/deploy deve ser reproduzível via CI/CD.
Este script é a camada assertiva (data-driven) que garante que o repositório
permaneça limpo e que nenhum estado local/runtime vaze para o git.

Falha (exit != 0) se detectar:
  1. Artefatos de build trackeados (.pyc/.pyo/.bak/__pycache__/.old.modules)
  2. Estado local de runtime trackeado (.ccg/tasks/, .ssot_check.py, dumps ANALISE_*)
  3. Diretórios de backup deprecated (.old.modules/)
  4. Binários grandes que não são entregáveis declarados (>10MB sem estar em allowlist)

Uso:
  python scripts/check_env_mandatory.py            # human report, exit code
  python scripts/check_env_mandatory.py --json     # machine report para CI

Decisões baseadas em `git ls-files` (determinísticas) — nunca em achismo.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Padrões que NUNCA devem estar trackeados (regeneráveis ou runtime-local).
FORBIDDEN_TRACKED = [
    "*.pyc",
    "*.pyo",
    "*.bak",
    "*__pycache__*",
    "**/.old.modules/**",
    "*.old.modules/**",
    ".ccg/tasks/**",
    ".ssot_check.py",
    "docs/ANALISE_*.md",
    "docs/ANALISE_*.json",
    "docs/wiki/.pending/**",
]

# Entregáveis binários legítimos (não são ruído mesmo sendo grandes).
BINARY_ALLOWLIST = {
    "edital/",          # SSOT das regras FINEP — fonte de verdade
    "docs/paper/",      # paper científico (figuras + PDF)
    "docs/projetos/",   # propostas FINEP versionadas
}

LARGE_FILE_THRESHOLD_MB = 10.0


def git_ls(patterns: list[str]) -> list[str]:
    """Lista arquivos trackeados que casam com os padrões (pathspec do git)."""
    if not patterns:
        return []
    try:
        out = subprocess.run(
            ["git", "ls-files", "--", *patterns],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [p for p in out.stdout.splitlines() if p]


def large_tracked_files(threshold_mb: float) -> list[tuple[str, float]]:
    """Arquivos trackeados acima do limite, EXCETO allowlist de entregáveis."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return []
    files = [f for f in out.stdout.split("\0") if f]
    big = []
    for f in files:
        if any(f.startswith(prefix) for prefix in BINARY_ALLOWLIST):
            continue
        try:
            size = (Path.cwd() / f).stat().st_size
        except OSError:
            continue
        mb = size / (1024 * 1024)
        if mb > threshold_mb:
            big.append((f, round(mb, 2)))
    return big


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="saída JSON para CI")
    ap.add_argument("--large-threshold-mb", type=float, default=LARGE_FILE_THRESHOLD_MB)
    args = ap.parse_args()

    forbidden = git_ls(FORBIDDEN_TRACKED)
    large = large_tracked_files(args.large_threshold_mb)

    violations = {
        "forbidden_tracked": forbidden,
        "large_non_deliverable": [{"file": f, "mb": mb} for f, mb in large],
    }
    passed = not forbidden and not large

    if args.json:
        print(json.dumps({
            "passed": passed,
            "violations": violations,
        }, indent=2, ensure_ascii=False))
    else:
        if forbidden:
            print("❌ Artefatos/state proibidos trackeados no git:")
            for p in forbidden:
                print(f"   - {p}")
        if large:
            print(f"❌ Binários > {args.large_threshold_mb}MB fora da allowlist de entregáveis:")
            for f, mb in large:
                print(f"   - {f} ({mb} MB)")
        if passed:
            print("✅ Ambiente conforme: sem ruído trackeado, sem binários não-entregáveis.")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
