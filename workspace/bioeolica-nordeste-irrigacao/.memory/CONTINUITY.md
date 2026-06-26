---
id: CONTINUITY-bioeolica-nordeste-irrigacao
type: protocol
mandate: continuous
created: 2026-06-25
autorecall: true
---

# CONTINUITY — Protocolo de Continuidade Compliance-Integrada

## 1. MANDATO CONTÍNUO: PRE-ALWAYS `/recap`

**A CADA NOVA AÇÃO neste lab, ANTES de agir, executar `/recap`:**

1. Ler `.memory/HARNESS.md` (identidade, workspace lock, FSM, mandatos).
2. Ler `.memory/CONTINUITY.md` (este — protocolo).
3. Ler `data/TASKS.md` (fila de continuidade / to-do pendente).
4. Confirmar em 1–2 linhas: estado FSM atual + próxima transição pretendida + workspace lock respeitado.
5. Só então agir.

> O `/recap` é o **gate de pré-ação**. Nenhuma ação (Write/Edit/Bash substantivo/Agent) ocorre sem o recap registrado no WAL. Honra Mandato D3 (gestão) + M5 (WAL).

## 2. WAL DUPLO (Pré + Pós — Pre-Always)

Toda ação não-trivial gera **dois** registros em `data/logs/`:

- **WAL-PRÉ (`wal_YYYYMMDD_NN_pre.md`):** registrada ANTES da ação. Campos 5W1H: What (ação pretendida), Why (mandato/pergunta), Who, When, Where (path dentro do workspace), How (passos + ferramentas). Inclui **eval gate esperado** (critério de sucesso).
- **WAL-PÓS (`wal_YYYYMMDD_NN_post.md`):** registrada APÓS. Campos: resultado real, evidência, VVV check (fontes/lacunas), PQMS delta, **handoff** (done/blocked/next).

Nomenclatura: `N` = sequencial do dia. Par pré+pós compartilha o mesmo `N`.

### Gate de avaliação (entre Pré e Pós)
- Toda nova afirmação: `[FATO]` com fonte datada **OU** `[LACUNA]` declarada (Mandato 1).
- Revisor hostil (quality gate D9): houve viés? número fabricado? escopo violado?
- Workspace lock: nenhum arquivo criado fora do path do lab.

## 3. CICLO PDCA CONTÍNUO

A FSM entra em loop PDCA após M9. Cada iteração = um "foco" derivado do M4 (Mandato 2: "deste doc utilizado em focos").

| Fase | Atividade | Artefato |
|------|-----------|----------|
| **P — Plan** | Novo foco/pergunta (dictação usuário OU fechamento de lacuna do M4). Define critério de sucesso. | `data/TASKS.md` + WAL-PRÉ |
| **D — Do** | Executar: coletar evidência (exa/gitnexus), FAN-OUT de agentes KDI sob contexto, editar artefatos **dentro** do workspace. | WAL-PRÉ → execução → WAL-PÓS |
| **C — Check** | VVV gate + fact-check + PQMS + revisor hostil. Eval pass/fail. | bloco Check no WAL-PÓS |
| **A — Act** | Consolidar no M4 (SSOT); atualizar síntese se relevante; handoff; decidir próximo foco. | update M4 + `data/TASKS.md` |

**Condição de parada:** só para por (a) usuário, (b) todas as lacunas do M4 fechadas com fonte, ou (c) bloqueio insuperável declarado.

## 4. WORKSPACE LOCK (regra de compliance)

- ✅ Permitido criar/editar: tudo sob `workspace/bioeolica-nordeste-irrigacao/**`.
- ⚠️ Fora do lab, só com aprovação explícita do usuário (ex.: atualizar `docs-nav/`, `CLAUDE.md`).
- ❌ Nunca: criar novo `workspace/<outro-lab>/` sem dictação via INPUT.md + FSM.

## 5. COMPLIANCE INTEGRADA AO PROJETO

- O lab **é** o projeto: `/home/cnmfs/bioeolica-entrega/workspace/bioeolica-nordeste-irrigacao`.
- Continuidade = manter o lab vivo via PDCA, não criar projetos paralelos.
- Toda sessão nova retoma pelo `/recap` → lê HARNESS + CONTINUITY + TASKS → continua do último handoff.

## 6. USO DE GITNEXUS + CCG NO CICLO

- **gitnexus:** na fase D, usar para queries de código/símbolo/impacto quando o foco tocar `./modules/` ou scripts do repositório raiz (expertise de domínio).
- **CCG:** na fase C (Check), `/ccg:verify-change`, `/ccg:verify-quality`, `/ccg:verify-security` como gates; `/ccg:commit` na fase A (Act) quando o usuário pedir commit.

## 7. CAPTURE DE TO-DO DE ATUAÇÃO

Toda tarefa pendente/futuro foco é registrada em `data/TASKS.md` (fila de continuidade). O `/recap` a lê primeiro.
