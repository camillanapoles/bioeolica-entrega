# GitOps — Laboratório Virtual Multi-Agente

> Fonte de verdade do fluxo GitOps + CI/CD. Alinhado a `CONVENTIONS.md` (M0–M9) e `INSTRUCTIONS.md`.

## Ramos (branches)
| Ramo | Papel | Proteção |
|------|-------|----------|
| `main` | Estável, releaseável, VVV PASS | obrigatório: CI verde + 1 review + status checks |
| `develop` | Integração contínua das features | CI verde |
| `feature/spec-XXX` | Uma feature por spec | squash merge em `develop` |
| `lab1/*`, `lab2/*` | Prefixo por laboratório | — |

## Fluxo padrão (spec-driven)
```
spec draft → specified  ─(HUMAN_GATE via Actions env "approval")─▶  planned
   → implemented → validated  ─(CI verde)─▶  merge develop
   → release main (tag, VVV PASS)
```

## Gates automáticos (GitHub Actions)
- `ci.yml` — pytest (M1/M5) + ruff. Em push/PR para main/develop.
- `spec-gate.yml` — valida `specs/*.yaml` (M7) + HUMAN_GATE via environment `approval`.
- `gitnexus-impact.yml` — `detect_changes` e impacto em PRs .py (M0/M4).
- `vvv-certify.yml` — certificação PASS/FAIL por lab (P$4).

## Regras de escrita (P$7)
- Scripts/módulos vivem **somente** sob `workspace/<lab>/`.
- Dados/variáveis em JSON provido por SQLite (P$0).
- Nada hardcoded (P$1).

## Provisionamento (gh)
```bash
gh repo create <org>/<repo> --private --source=. --remote=origin --push
gh api -X PUT repos/:owner/:repo/branches/main/protection ...   # ver scripts/gitops-bootstrap.sh
gh secret set ...    # tokens GitNexus/sonar se necessário
gh label create spec-lab1 ...
```

## Tags / Releases
- `v<lab>-<semver>` ex.: `v-lab1-material-0.1.0`.
- Toda release tem artifact VVV anexado.
