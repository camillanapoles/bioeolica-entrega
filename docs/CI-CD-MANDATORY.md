# CI/CD-Mandatory: todo ambiente reproduzível via Actions

> **Mandato:** nenhum ambiente de desenvolvimento/deploy é "manual". Todo
> estado reproduz-se via CI/CD GitHub Actions. O repositório permanece limpo:
> nada de build artifacts, runtime state local, ou binários não-entregáveis no
> tracking. O `remote` funciona como **backup / SSOT** de toda informação
> relevante.

## O gate: `scripts/check_env_mandatory.py`

Camada assertiva **data-driven** (baseada em `git ls-files`, determinística).
Falha (exit 1) se detectar:

| Categoria | Padrões |
|---|---|
| Build artifacts | `*.pyc`, `*.pyo`, `*.bak`, `*__pycache__*` |
| Estado runtime local | `.ccg/tasks/**`, `.ssot_check.py`, `docs/ANALISE_*.md`, `docs/ANALISE_*.json`, `docs/wiki/.pending/**` |
| Backups deprecated | `**/.old.modules/**` |
| Binários não-entregáveis | `>10MB` fora da allowlist `{edital/, docs/paper/, docs/projetos/}` |

Uso local:

```bash
python scripts/check_env_mandatory.py            # relatório humano
python scripts/check_env_mandatory.py --json     # relatório máquina (CI)
```

## Workflow: `.github/workflows/env-mandatory.yml`

Roda em **todas as branches** (`main`, `develop`, `feat/**`, `fix/**`,
`chore/**`), em PRs, e auditoria semanal via `schedule`. Também cobre o
`workflow_dispatch`.

**Persistência entre execuções:**
- `actions/cache@v4` guarda snapshot do tracking (`tracked-files.txt` + SHA256)
  — auditoria comparativa entre runs.
- `actions/upload-artifact@v4` publica `env-mandatory.json` + snapshot
  (retenção 30 dias).
- Em regressão (somente `schedule`/`main`), abre issue automática com os
  violadores para rastreabilidade.

## Branch protection (required checks)

Para tornar o gate **mandatório**, configure no GitHub (Settings → Branches →
main):

```bash
gh api repos/:owner/:repo/branches/main/protection -X PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]="Env-Mandatory / gate" \
  -f required_status_checks[contexts][]="CI / test (3.11, root)" \
  -f required_status_checks[contexts][]="CI / test (3.11, lab1)" \
  -f required_status_checks[contexts][]="CI / test (3.11, lab2)" \
  -f enforce_admins=true \
  -f required_pull_request_reviews[required_approving_review_count]=1
```

> Substitua `:owner/:repo` pelo slug correto. Ajuste o número de revisores ao
> contexto do projeto.

## Alinhamento com `audit-edital.yml`

Dois gates independentes e complementares:

| Workflow | Domínio | Quando falha |
|---|---|---|
| `env-mandatory` | **Higiene de repo** | Estado local/binário não-entregável trackeado |
| `audit-edital` | **Conformidade FINEP** | Orçamento fora das regras AgriFam-ICT 2026 |

Ambos devem estar verde antes de merge em `main`.

## Corpus de consulta externo

`modules/MathematicalEngineeringDeepLearning/` (130MB, 177 arquivos,
zero importers — fonte: auditoria GitNexus + grep) é um **repositório
distinto** trazido sem git, destinado apenas a **consulta de soluções
computacionais** pelos agentes. Ele **não é trackeado** neste repo
(ver `.gitignore`) e permanece no disco apenas como fonte local.

Externalização pendente como **git submodule** ou link externo:

```bash
# Quando o repo distinto estiver publicado:
git submodule add <url-do-repo-distinto> modules/MathematicalEngineeringDeepLearning
```

Até lá, agentes o consultam em disco; nada do seu conteúdo entra no SSOT
deste repo.
