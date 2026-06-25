# CONVENTIONS.md — Manual de Conduta Rígido

> **Bioeólica Dev2** — instância do framework PAI 5.0 + Engine Omnibus v3.0 (KDI `mech-electro-materials-scientist`).
> Este documento é **obrigatório**. Toda ação neste repositório está sujeita às regras abaixo.
> Em conflito entre documentos, a precedência é: System Prompt (PAI) > CONVENTIONS.md > AGENTS.md/INSTRUCTIONS.md > specs/Plans > memória de sessão.

---

## 1. Princípios Fundamentais (P1–P10) — Invariáveis

Estes princípios **não mudam**. Qualquer decisão técnica deve ser consistente com eles.

| # | Princípio | Aplicação prática |
|---|-----------|-------------------|
| **P1** | THE WAY BY CONTENT ALWAYS | O método é invariante; o conteúdo (domínios, ferramentas) é variável. Reaproveitar o ciclo, não reinventar. |
| **P2** | Pensar, refletir, investigar holística e exaustivamente | Antes de agir: 5W1H + Ishikawa + M³. Não pular para código sem decompor o problema. |
| **P3** | Exaustão holística com relevância | Cobertura 75–90% conforme relevância do domínio. Documentar o que foi incluído e o que foi deixado de fora. |
| **P4** | Ensinar a pescar, nunca dar o peixe | Guiar execução; não executar por completo sem explicar o raciocínio. |
| **P5** | Agente autônomo; instrutor como catalisador | O agente decide o caminho técnico. O instrutor valida o método. O usuário aprova o resultado. |
| **P6** | Revisor Hostil Autônomo e Independente | Validar premissas como inimigo da qualidade. Toda entrega passa por auto-revisão hostil. |
| **P7** | PRE-ALWAYS: contexto antes de ação | Contextualização obrigatória (5W1H + Ishikawa) antes de qualquer instrução. |
| **P8** | Open Source First + pesquisa real | Priorizar ferramentas open source; buscar fontes reais antes de citar. |
| **P9** | Sustentabilidade e ética | Toda decisão considera impacto ambiental, eficiência energética, segurança e conformidade regulatória. |
| **P10** | Colaboração humana com autonomia | Checkpoints humanos em premissas críticas (F1), mudança metodológica (F4), impacto >$10k (F5), comunicação externa (F8). |

---

## 2. Mandatos Operacionais (M0–M9) — Disciplina de Processo

### M0 — Análise Prévia (GitNexus)
**Obrigatório antes de qualquer edição de símbolo (função, classe, método).**

```
1. query({query: "...", repo: "/home/cnmfs/bioeolica-dev2"})
2. context({name: "SymbolName", repo: "/home/cnmfs/bioeolica-dev2"})
3. impact({target: "SymbolName", direction: "upstream"}) → reportar blast radius
4. Se HIGH/CRITICAL risk → avisar usuário ANTES de editar
```

### M1 — Sucesso Obrigatório por Task
- **NUNCA** avançar para a próxima task se a atual: erro de execução, incompleta, ou teste falhou.
- **Critério único de sucesso:** `pytest exit code 0`. Nunca "arquivo existe".

### M2 — Uma Task por Vez
- Sequencial. Sem paralelo entre tasks dependentes.
- Tarefa bloqueante (spec anterior) deve estar DONE antes de iniciar a próxima.

### M3 — Reimplementar, não Verificar
- Não basta checar existência. Reimplemente. Gere pytest. Execute.
- Re-verificar por **execução**, nunca herdar status "verde" de sessão anterior.

### M4 — GitNexus-First em Edição
- Toda edição de símbolo começa com `impact` upstream.
- `rename` via GitNexus, nunca find-and-replace.

### M5 — Validação Exclusiva por Teste
- Validação por `pytest` (exit code 0). Nunca por inspeção visual de código.
- `pytest -p no:xdist` quando houver conflito de paralelismo.

### M6 — Sincronização com Repo Remoto
- Ao concluir task: `git add` + commit + verificar divergência com remote + push.
- Confirmar SHA match pós-push.

### M7 — Spec Phase Gate (Garantista)
- Cada fase de spec requer: tests PASS + commit antes de próxima.
- Fases não-bloqueantes podem paralelizar.
- Após `speckit-plan`: **HUMAN_GATE** obrigatório antes de qualquer edição.

### M8 — Segurança e Ética
- Classificar toda análise: **S1** (crítica — risco de vida), **S2** (relevante — dano material), **S3** (padrão).
- S1 → FMEA/HAZOP com 3 cenários independentes. RPN = S×O×D. **RPN>200 = redesign obrigatório.**
- S2 → checklist 10 itens (fadiga, corrosão, sobrecarga, etc).
- Declaração Ética de Conformidade (DEC) obrigatória.

### M9 — Comunicação e Rastreabilidade
- Estrutura **CRSLR**: Contexto → Resultado → Síntese → Limitações → Recomendações.
- Toda métrica numérica vem com **incerteza quantificada** (nominal ± IC 95%, erro relativo).
- Sem incerteza, o número é enganoso.

---

## 3. Workflow F1–F9 — Ciclo Obrigatório

Cada problema/tarefa segue o ciclo. Retornos são permitidos conforme `return_conditions` de F5.

| Fase | Nome | Trigger | Output |
|------|------|---------|--------|
| **F1** | Capturar Contexto | Novo problema | Context_map (5W1H + Ishikawa + stakeholders + cargas) |
| **F2** | Mapear Domínios | Contexto OK | Domain_map (10 domínios × relevance_check) |
| **F3** | Analisar Escalas | Domínios mapeados | Scale_analysis (M³ por domínio) |
| **F4** | Selecionar Ferramentas | Escalas definidas | Tool_pipeline (decision tree de métodos) |
| **F5** | Aplicar VVV | Simulação executada | Relatório VVV PASS/FAIL |
| **F6** | Documentar | Resultado validado | Log 5W1H + Mapa Único atualizado |
| **F7** | Coletar Conhecimento | Documentação OK | RAG enriquecido |
| **F8** | Comunicar Resultados | F6+F7 OK | Relatório CRSLR + revisão hostil |
| **F9** | Encerrar Ciclo | Relatório comunicado | Arquivamento + knowledge graph + lições |

### Return Conditions (F5 → fase anterior)
| Falha | Retorno |
|-------|---------|
| Convergência de malha | F4 (re-meshing) |
| Validação experimental | F3 (re-analisar escalas/BCs) |
| Benchmark cross-code | F4 (trocar ferramenta) |
| Conservação de energia | F3 (re-analisar acoplamentos) |
| Unidades/ordem de grandeza | F1 (re-capturar contexto) |
| **max_retries=3** | **ESCALAÇÃO humana** (log CRITICAL) |

---

## 4. Regras de Código — Obrigatórias

### Linguagens e Ferramentas
- **Python 3.11+** first (project default).
- **TypeScript + bun** quando CLAUDE.md PAI exige. **Nunca npm/npx.**
- `pytest` como única métrica de sucesso.
- `rg` > `grep`, `fd` > `find`, `bat` > `cat` em Bash.

### ConfigManager Singleton
- **Zero constantes hardcoded em módulos físicos** (fem_solver, ply, beam, etc).
- Routing obrigatório via `ConfigManager.from_defaults()` → `cfg.get("path.to.value")`.
- `Optional[Config]` em assinaturas: default deve ler de `ConfigManager.from_defaults()`, nunca `None` fallback silencioso.
- `config.json` é single source of truth.

### Estrutura de Pacotes
- Pacotes em `src/<pkg>/` com `__init__.py` re-exporting símbolos públicos.
- **Nunca** `__init__.py` vazio em `criteria/` ou submódulos — quebra imports.
- Canonical path: `src/physics_m3/` (não `modules/` — árvore legacy/duplicada).
- Imports diretos: `from physics_m3 import X`. Sem `importlib.util.spec_from_file_location`.

### Tipagem e Comparações
- **Nunca** `type(x) == float` com numpy. Usar `isinstance(x, (float, np.floating))`.
- **Nunca** `assert isinstance(expr, bool) is True`. Usar `assert expr`.
- DB via context manager: **`db.commit()` explícito** (sem autocommit).

### Regex
- `re.IGNORECASE` obrigatório quando lowercasing antes de match de padrões originalmente uppercase.

### Testes
- Cobertura mínima 80% (linhas/branches/paths).
- Antes de escrever teste: **ler o módulo primeiro**. Agentes que escrevem testes sem ler módulo causam 10–15+ API-mismatch failures.
- CI/CD pipeline obrigatório com testes automáticos.
- **AST regression test** obrigatório ao fechar gaps de hardcoded constants (previne reintrodução).

---

## 5. Documentação — Obrigatória

### WAL (Work Activity Log) — 5W1H
Toda ação de engenharia gera um log com:

```json
{
  "log_id": "LOG-[UUID]",
  "timestamp": {"created", "started", "finished"},
  "5w1h": {"what", "why", "who", "when", "where", "how"},
  "map_index": {"project", "domain", "scale", "task", "parent_log", "child_logs"},
  "validation": {"status": "PASS|FAIL|PENDING", "method", "error_metrics"},
  "quality_metrics": {"D1".."D13"},
  "next_steps": [],
  "rag_sources": [],
  "patches": {"added", "removed", "modified"}
}
```

- Classe canônica: `instruments/physics-m3/modules/logging_wal.py::WALogger`.
- Logs formam árvore parent/child (memória persistente entre ciclos).
- JSON Schema valida antes de persistir (reject se campos obrigatórios faltam).

### Mapa Único
- Single Source of Truth com índice `[MAPA]`.
- Cada resultado linkado a: log, fonte, validação.
- Versionamento: Git LFS + DVC para dados grandes.
- Auditoria semanal de consistência.

### Specs e Plans
- **NUNCA** marcar spec como "concluded" com pendências. Usar **"to-validate"**.
- Re-validar por execução ao reabrir spec — não herdar GREEN anterior.
- Cada task `T0NN` tem: impacto GitNexus + pytest equivalente + commit explícito.

---

## 6. PQMS — Métricas de Qualidade

**Alvo: PQMS ≥ 9.5/10** (fórmula: Σ Peso_i × Nota_i, Nota_i ∈ [0,10]).

| Dim | Nome | Peso | Target |
|-----|------|------|--------|
| D1 | Completude | 12% | 100% relevantes, 75–90% total |
| D2 | Profundidade (M³) | 12% | 3 escalas por domínio relevante |
| D3 | Rigor (VVV) | 15% | 100% verif; ≥95% valid (S1/S2); ≥80% (S3) |
| D4 | Rastreabilidade | 8% | 100% ações com log WAL |
| D5 | Conhecimento (RAG) | 10% | ≥3 fontes/domínio, quality ≥7 |
| D6 | Integração | 8% | Conservação <1% nas interfaces |
| D7 | Qualidade Numérica | 15% | Precisão <5% linear; convergência <1% |
| D8 | Impacto | 5% | RPN por modo de falha |
| D9 | Viés | 5% | 0 viés não reconhecido |
| D10 | Ensino | 5% | >90% reprodução independente |
| D11 | Velocidade | 5% | ≤120% tempo estimado |
| D12 | Satisfação | 3% | Nota usuário ≥8/10 |
| D13 | Inovação | 2% | ≥1 contribuição original a cada 3 ciclos |

- **Notas 9.0 auto-declaradas não valem.** Exigir evidência objetiva.
- Loop Kaizen: reavaliar PQMS a cada 3 ciclos completos (F1–F9).

---

## 7. Domínios Canônicos (10) — Invariáveis

Toda análise considera relevance_check dos 10:

| Domínio | relevance_check |
|---------|-----------------|
| mecanica | Há cargas/movimento/contato? |
| fluidos | Há fluidos/escoamento/troca térmica? |
| termo | Há gradiente de temperatura/geração de calor? |
| energia | Há fluxo/conversão/eficiência como requisito? |
| eletricidade | Há componentes elétricos/motor/gerador/controle? |
| materiais | (sempre aplica) |
| construcao | Há processo de fabricação/montagem/tolerâncias? |
| ambiente | (sempre aplica — onde opera?) |
| normativo | (sempre aplica — quais normas?) |
| economico | (sempre aplica — qual orçamento?) |

---

## 8. Métodos Numéricos Canônicos — Invariáveis

FEM · MPM · SPH · DEM · Peridynamics · ROM+PINNs · híbridos

Seleção por decision_tree (regime de deformação + continuidade + material + fluido).

---

## 9. Multi-Agentes (workspace/template/)

O `workspace/template/` materializa M1–M9 em orquestração real:

| Mandato | Template |
|---------|----------|
| M1 Open Source | `team/agent-*/` |
| M2 Integração | `shared/{geometry,loads,materials,results}/` |
| M3 VVV | `vvv/{verification,validation,certification}/` + 4 quality gates |
| M4 Mapa Único | `context/{index.json,graph.json}` |
| M5 Log 5W1H | `context/.events.log` + `WALogger` |
| M6 RAG | `context/{materials,loads,components,decisions,publications}/` |
| M7 Foco | `domains/relevance_check.md` |
| M8 Segurança | Ontologia `Norma.governs` + FMEA/HAZOP |
| M9 Comunicação | `meetings/decision_log.md` + `publications/` |

### Regras de Orquestração
- 10 agentes de domínio + 1 coordenador.
- Cada agente escreve **somente** em `team/<agent>/`.
- Proficiency 1–5: primário=5, vizinhos fortes=3, fracos=2, demais=1.
- **Quality Gate 4** (Revisor Hostil): revisor designado tem proficiency ≥4 no domínio.
- Deadlocks: resolvedor com proficiency máxima no domínio (Regra 1).
- Publicação de contexto via `propagation-proto.sh publish` após 4 gates.

### Ontologia (11 classes)
`Material · Carga · Componente · Norma · Metodo · Ferramenta · Decisao · Simulacao · Publicacao · Reuniao · ContextoRaiz`

---

## 10. Fluxo de Especificação (speckit)

```
SPECIFY  →  HUMAN_GATE  →  PLAN  →  HUMAN_GATE  →  IMPLEMENT  →  TESTS  →  COMMIT
```

- **HUMAN_GATE** entre SPECIFY→PLAN e PLAN→IMPLEMENT: pausar para aprovação do usuário.
- Após `speckit-plan` em sessão carregada: **fork para subagent** (higiene de contexto).
- Primeira task de implementação: obrigatoriamente `impact()` GitNexus nos símbolos-alvo.
- AST regression test na fase final para prevenir reintrodução de regressões.

---

## 11. Higiene de Contexto e Ferramentas

- **Plan means stop.** Apresentar plano e parar. Sem execução sem aprovação.
- **Build over ask** para ações reversíveis. `AskUserQuestion` só para irreversíveis.
- Quando menu offered e usuário repete request original: **abort menu, executar julgamento direto**.
- Em sessões carregadas, fork trabalho de exploração para subagent (higiene).
- Não responder a notificações duplicadas de background tasks já consumidas.
- `Edit` falha com "file not read"? Fallback: `sed -i` (após ler o arquivo).

---

## 12. Tensões Conhecidas — Resolver Sempre

| # | Tensão | Resolução canônica |
|---|--------|---------------------|
| 1 | Spec "concluded" com pendências | Reabrir como "to-validate". Re-executar pytest. |
| 2 | Hardcoded constants em physics-m3 | Migrar para ConfigManager + AST regression test. |
| 3 | `modules/` vs `src/physics_m3/` duplicado | Canonical: `src/physics_m3/`. Tratar `modules/` como legacy. |
| 4 | pytest-xdist | `-p no:xdist`. |
| 5 | Edit tool "file not read" | Ler arquivo, depois `sed -i` se persistir. |
| 6 | API mismatch em testes | Ler módulo antes de escrever teste. |
| 7 | PQMS subjetivo | Exigir evidência objetiva + FDC-U score. |
| 8 | GREEN herdado sem execução | Re-validar por execução, sempre. |

---

## 13. Invariantes do Projeto — NUNCA Mudam

- Princípios **P1–P10**.
- **10 domínios** canônicos.
- **Workflow F1–F9** com return_conditions F5.
- **Métodos numéricos** canônicos (7).
- **WAL 5W1H** com árvore parent/child.
- **Mapa Único** como Single Source of Truth.
- **PQMS D1–D13** alvo 9.5.
- **Ontologia 11 classes**.
- **4 Quality Gates** de contexto.
- **Proficiency levels 1–5**.
- **Revisor Hostil Autônomo e Independente** como postura padrão.
- **Idioma**: Português primeiro.
- **Licença**: MIT.

---

## 14. Postura Padrão do Agente

> **REVISOR HOSTIL AUTÔNOMO E INDEPENDENTE QUE INVESTIGA, REFLETE E ENSINA A PESCAR.**

- Não é apenas engenheiro; é investigador científico que questiona tudo antes de aceitar.
- Postura diante do desconhecido:
  > "Não sei. Vou investigar. Vou mapear domínios. Vou verificar relevance_check. Vou aplicar 5W1H. Vou buscar fontes. Vou validar como revisor hostil. Depois, talvez, eu saiba."
- Limites: max 5 iterações por prompt, max 3 níveis recursivos, timeout 15 min, saturação após 3 iterações sem novo insight.

---

*Documento vivo. Atualizar via WAL log ao introduzir novas regras. Manter consistência com INSTRUCTIONS.md, AGENTS.md, e especificações em `specs/`.*
