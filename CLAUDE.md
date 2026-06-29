PRIMEIRAMENTE SAIBA QUE ESTA PRODUZINDO ORQUESTRAMENTO AGENTIC QUE PRODUZ LABORORATORIOS CIENTIFICO ATRAVENS DE WORKFLOW CONTFORME DOCUMENTO EM FORMA DE MKDOCS NO DIRETORIO @docs-nav/

A ESTRUTURA DE BASR DE ORQUESTRAVAO ESTA ABAIXO

```
├── knowledge
│		 ├── materials
│		 ├── wind-energy
│		 ├── llm.pdf
│		 ├── RESEARCH_DECISIONS.md
│		 └── T069_FINAL_AUDIT.md
├── modules
│		 ├── ai_assist_cad
│		 ├── cad-cae-platform
│		 ├── kdi-m3-bridge
│		 ├── MathematicalEngineeringDeepLearning
│		 ├── modules
│		 ├── physics-m3
│		 └── demo_integrada.py
├── scripts
│		 ├── agentic
│		 ├── compliance
│		 ├── audit_deps.py
│		 ├── generate_gitnexus_report.py
│		 ├── migrate_unify_db.py
│		 └── run_full_pipeline.py
├── workspace
│		 ├── spec-014-configmanager
│		 ├── template
│		 └── README.md
├── CLAUDE.md
├── CONVENTIONS.md
├── DOC1-KDI_MECH-ELECTRO-MATERIALS.md
├── DOC2-KAIZEN.md
├── INSTRUCTIONS.md
```

## CONTEXTO DE ORQUESTRACAO

ENTENDA:
1. ORQUESTRACAO GUIADA POR @docs-nav
2. DOC1 E DOC2 MENCIONADOS em @docs-nav
E USADOS DE BASE PARA KDI ESTAO EM @docs-nav
@DOC1-KDI_MECH-ELECTRO-MATERIALS.md E @DOC2-KAIZEN.md

## REGRAS DE GOVERNANCA

O LABORATORIO DEVE TEM FSM [STATE MACHINE] A COMECAR PELO NOME DO LAB EM STATE E ESTASO 
└─ NENHUM LAB PODE SER CRIADO SEM SER VIA DOKICITACAO DO USUARIO E SEM PASSAR POR FSM DE ORQUESTRACAO
└─ SO E SOMENTE SE CRIARA LABORATORIO ATRAVES DE DOC INPUT.md ➞ con5endo ibstrucoes inciciais a ser aprimentora e construida ➞ onde addim que projeto e criado INPUT.md eh movido pro projeto
└─ o PROJETO CRIAFO DO LAVORATORIO DEVE TER UM README.md COM O NOME DO LAB E O LINK PARA O DOC INPUT.md (INPUT.md pra .archives do laboratio)
└─ O LAVORSTORIO JA TEM TEMPLATE 
└─ SCRIOT COBSTA MODULOS UTEIS DE ORQUESTRACAO 
└─ o lab deve ser criado no local ./workspace/[NOME_DO_LAB] e deve conter

## GARANTA FSM GESTAO D3 VVV E FACT CHECK + ENTREGAVEIS CONFORME SOLICITADO PELO LAB

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **bioeolica-entrega** (6794 symbols, 10492 relationships, 133 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/bioeolica-entrega/context` | Codebase overview, check index freshness |
| `gitnexus://repo/bioeolica-entrega/clusters` | All functional areas |
| `gitnexus://repo/bioeolica-entrega/processes` | All execution flows |
| `gitnexus://repo/bioeolica-entrega/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
