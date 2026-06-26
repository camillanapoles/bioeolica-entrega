# Mapa do Fluxo Canônico — INSTRUCTIONS.md (Engine Omnibus v3.0 + KDI)

> Fontes: `INSTRUCTIONS.md` (v3.0, F1-F9), `DOC1-KDI_MECH-ELECTRO-MATERIALS.md`
> (THE-WAY-BY-CONTENT, FASE 1-7), `DOC2-KAIZEN.md` (8 partes, M1-M7, F1-F7).

## Princípio fundamental
**"THE WAY BY CONTENT ALWAYS"** — o método é o produto; o conteúdo é variável.
Caminho invariante: filosofia → KDI → métodos → domínios → mandatos → fluxo → métricas → WAL.

## 8 partes da engine (DOC2 L111-160)
1. Filosofia (P1-P10)
2. KDI (identidade mech-electro-materials-scientist)
3. Métodos numéricos (FEM/MPM/SPH/DEM/Peridynamics/PINNs/híbridos)
4. Domínios (10 + M³ cada)
5. Mandatos M1-M9
6. Fluxo F1-F9
7. Métricas PQMS D1-D13
8. WAL (rastreabilidade)

## Mandatos M1-M9
| M | Nome | Trigger |
|---|---|---|
| M1 | Open Source First | Selecionar ferramenta |
| M2 | Seleção & Integração | Domínios acoplados |
| M3 | VVV | Resultado disponível |
| M4 | Mapa Único SSOT | Início de projeto |
| M5 | Log 5W1H | Cada ação |
| M6 | RAG Knowledge | Necessidade de conhecimento |
| M7 | Foco Pertinente (75-90%) | Análise complexa |
| M8 | Segurança & Ética (S1/S2/S3) | Risco humano/ambiental |
| M9 | Comunicação CRSLR | Resultado a comunicar |

## Fluxo F1-F9 — SEQUÊNCIA OBRIGATÓRIA
| F | Nome | Artefato de saída |
|---|---|---|
| F1 | CAPTURAR CONTEXTO | context_map (5W1H + Ishikawa + stakeholders + cargas) |
| F2 | MAPEAR DOMÍNIOS | domain_map (10 + relevance_check + M³ + % cobertura) |
| F3 | ANALISAR ESCALAS | scale_analysis (Macro/Meso/Micro por domínio) |
| F4 | SELECIONAR FERRAMENTAS | tool_pipeline (decision tree + ≥3 open source + versões) |
| F5 | APLICAR VVV | vvv_report (verificação+validação+validada+return_conditions) |
| F6 | DOCUMENTAR | Log 5W1H + Mapa Único + versionamento |
| F7 | COLETAR CONHECIMENTO | rag (fontes + quality_score + validation_status) |
| F8 | COMUNICAR RESULTADOS | Relatório CRSLR + revisão hostil ata + IC95% |
| F9 | ENCERRAR CICLO | Relatório encerramento + PQMS D1-D13 + archive |

### F5 — return_conditions
- falha_convergencia_malha → F4 (re-mesh)
- falha_validação_experimental → F3 (re-analisar)
- falha_benchmark_crosscode → F4 (trocar ferramenta)
- falha_unidades_ordem_grandeza → F1 (re-capturar)
- max_retries: 3 → ESCALAÇÃO

## PQMS D1-D13 (target 9.5/10)
D1 Completude 12% · D2 Profundidade 12% · D3 Rigor VVV 15% · D4 Rastreabilidade 8% ·
D5 Conhecimento 10% · D6 Integração 8% · D7 Qualidade Numérica 15% · D8 Impacto 5% ·
D9 Viés 5% · D10 Ensino 5% · D11 Velocidade 5% · D12 Satisfação 3% · D13 Inovação 2%.
