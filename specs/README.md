# Specs (GitOps spec management)

Cada spec é um YAML versionado. Workflow `spec-gate.yml` valida schema + emite HUMAN_GATE (M7).

## Schema obrigatório
```yaml
id: lab1-material/001-tracao          # único
title: Ensaio de tração do compósito
lab: lab1-material                      # lab1-material | lab2-gerador
status: draft                           # draft|specified|planned|implemented|validated|to-validate
owner: agent-materiais                  # agente responsável
modules:                                # módulos que este spec toca
  - workspace/lab1-material-papel-mache-grafite/ensaios/tracao.py
acceptance:                             # critérios mensuráveis (TDD)
  - "Calcular módulo de Young via regra de misturas com erro < 5% vs referência"
  - "pytest exit code 0 em tests/test_tracao.py"
references:                             # fontes (VVV)
  - "ASTM D638 (tensile properties of plastics)"
notes: ""
```

## Status FSM (M7 Spec Phase Gate)
`draft → specified →(HUMAN_GATE)→ planned →(HUMAN_GATE)→ implemented → validated → to-validate`
JAMAIS marcar `validated` com pendências.
