---
id: TASKS-bioeolica-nordeste-irrigacao
type: task-queue
lab: bioeolica-nordeste-irrigacao
updated: 2026-06-25
---

# Fila de Continuidade (To-Do de Atuação) — PDCA

> Lida pelo `/recap` no início de cada ação. Cada item = um foco futuro derivado do M4.

## Estado FSM atual
`M9 ✅ → CICLO PDCA (P1 em espera de dictação)`

## BACKLOG (focos candidatos — derivados das lacunas do M4)

| ID | Foco | Fase | Status | Mandato | Origem |
|----|------|------|--------|---------|--------|
| T-001 | Fechar lacuna CAPEX R$/kW por técnica (SFV isolado, híbrido SFV+diesel, microeólica) com cotação regional NE | Plan | pendente | M1/VVV | M4 §5, §8 |
| T-002 | Detalhar subperfil "pequena comunidade familiar do Centro-Oeste" (evidência CO atual = grande escala) | Plan | pendente | D9 | M4 §10 Q2 |
| T-003 | Consolidar métrica operacional de "distância hídrica" (densidade de mananciais, vazão per capita) por sub-região NE+CO | Plan | pendente | M4 §7/§10 Q7 | M4 |
| T-004 | Mapa de calor de potencial eólico small-scale cruzado com CRESESB Atlas por coordenada (NE litoral/Apodi + CO nichos) | Plan | pendente | M4 §6 | M4 §6/§10 Q6 |
| T-005 | Análise comparativa tradicional vs renovável por perfil (familiar NE / grande escala CO) — matriz de decisão | Plan | pendente | M9 | M4 §8/§10 Q8 |

## EM ANDAMENTO
_(vazio — ciclo PDCA aguarda dictação de próximo foco pelo usuário)_

## CONCLUÍDO

| ID | Foco | Data | WAL |
|----|------|------|-----|
| T-000 | Retificação de escopo: inclusão Centro-Oeste (NE+CO) | 2026-06-25 | `data/logs/wal_20260625_retificacao_co.md` |

## PRÓXIMA AÇÃO (handoff)
- Aguardar dictação do usuário para o próximo foco (T-001…T-005), **OU**
- Se usuário autorizar loop autônomo: iniciar por **T-001** (lacuna de maior impacto — CAPEX R$/kW ainda aberta em ambas as regiões).
