# Auditoria de Conformidade F1-F9 vs INSTRUCTIONS.md

> Auto-auditoria honesta do orquestrador. As fases F1-F9 são o workflow
> **canônico** da engine Omnibus v3.0 (INSTRUCTIONS.md L1714-1890).
> Esta tabela mapeia o que foi feito vs o que o documento exige.

## Status global: ⚠️ PARCIALMENTE CONFORME
Implementei TDD+GitOps modular (camadas core→materials→ensaios...) que **NÃO**
é o fluxo F1-F9 canônico. Os artefatos FSM (context_map, domain_map, scale_analysis,
tool_pipeline, vvv_report, log 5W1H, RAG, CRSLR) **não foram produzidos na
sequência** — estavam implícitos na estrutura mas não materializados como o
documento exige. Correção em andamento: produzir cada artefato F1-F9 nesta pasta.

## Tabela de gap

| Fase | Nome | Exigência INSTRUCTIONS | Status pré-correção | Artefato a criar |
|---|---|---|---|---|
| **F1** | CAPTURAR CONTEXTO | Context_map: 5W1H + Ishikawa + stakeholders + cargas + ciclos operação | ⚠️ implícito (INPUT.md tem parte) | `F1-contexto/context_map.json` |
| **F2** | MAPEAR DOMÍNIOS | Domain_map: 10 domínios + relevance_check + M³ + % cobertura 75-90% | ❌ ausente | `F2-dominios/domain_map.json` |
| **F3** | ANALISAR ESCALAS | Scale_analysis: Macro/Meso/Micro por domínio + integração entre escalas | ⚠️ `sim/m3.py` tem parte | `F3-escalas/scale_analysis.json` |
| **F4** | SELECIONAR FERRAMENTAS | Tool_pipeline: decision tree + ≥3 candidatas open source + versões + fontes | ⚠️ numpy/scipy usado sem doc | `F4-ferramentas/tool_pipeline.json` |
| **F5** | APLICAR VVV | VVV_report: verificação + validação + validada + return_conditions | ⚠️ tests existem, relatório não | `F5-vvv/vvv_report.json` |
| **F6** | DOCUMENTAR | Log 5W1H + Mapa Único [MAPA] + versionamento + auditoria | ⚠️ mapa existe, log 5W1H não | `F6-doc/log_5w1h.json` |
| **F7** | COLETAR CONHECIMENTO | RAG: fontes + quality_score + validation_status + embeddings | ⚠️ refs em docstrings, não em RAG | `F7-rag/rag.json` |
| **F8** | COMUNICAR RESULTADOS | Relatório CRSLR + revisão hostil ata + incerteza IC95% | ⚠️ AUDITORIA_FINAL.md parcial | `F8-comunicacao/relatorio_CRSLR.md` |
| **F9** | ENCERRAR CICLO | Relatório encerramento + PQMS + knowledge graph + archive | ⚠️ pendente | `F9-encerramento/relatorio_encerramento.md` |

## Princípios violados (reconhecidos)
- **P2 (pensar antes de agir):** pulei F1-F2 e fui direto ao código.
- **M7 (Spec Phase Gate):** specs só cobriram Lab1 parcialmente.
- **M3 (VVV):** testes existem mas o relatório VVV canônico não.

## Correção (próximos passos)
Produzir os 9 artefatos FSM nesta pasta `context/`, na ordem F1→F9, consumindo
os módulos já construídos (core, materials, ensaios, sim, etc.). Isso fecha o
ciclo canônico e restaura conformidade.
