# ORÇAMENTO VERSIONADO — FINEP AgriFam-ICT 2026 (Linha 2)

> **Este é o orçamento RETIFICADO corrente (v2.0).** A versão vigente é sempre a de número mais alto.
> Registro de versionamento: `docs/projetos/log-versoes-orcamento.md`.
> Proposta-mãe: `docs/projetos/finep-agrifam-bioeolica-linha2.md`.
> **Data-base dos preços:** 06/2026 (pró-manual data >01/01/2026, item 11.2.4). Câmbio: câmbio da data de lançamento da Chamada (item 11.2.4); US$1 ≈ R$5,20; €1 ≈ R$5,70.
> **Rastreabilidade SSOT (P$1 — zero hardcoded):** parâmetros físico-científicos em `workspace/lab1-material-papel-mache-grafite/config/constants.json`.

---

## INSTRUÇÃO DE LEITURA

| Versão | Status | Valor | Descrição curta |
|---|---|---|---|
| **v2.0 (RETIFICADA — VIGENTE)** | ✅ Corrente | **R$7.000.000,00** | Ciclo completo de P&D: ensaios iterativos de material (5 ciclos), infra 2 ambientes (Lab1 materiais + Lab2 eletromec), PI nacional + internacional (PCT + fases nacionais + anuidades), HPC, viagens a congressos (COP-31/32 e análogos), quadro ampliado de pesquisadores. |
| v1.0 (original) | 🗄 superseded | R$4.500.000,00 | Primeira consolidação (R$4,5M) — subdimensionava iterações de ensaio, PI internacional, HPC e disseminação internacional. |

> **Por que retificar (mandato do time):** *"EM HIPÓTESE ALGUMA POUPAR DINHEIRO SE FOR PERMITIDO E TIVER DENTRO DO PROJETO"* — a faixa R$1M–R$7M (item 9) permite R$7M; suborçar iterações de P&D, PI internacional e disseminação causaria **valor inabilitado >30% = eliminação** (risco R4, item 11.2.2). A v2.0 aloca o máximo permitido com justificativa por item.

---

# v2.0 — RETIFICADA (VIGENTE)

## Resumo consolidado — R$7.000.000,00 / 36 meses

| Rubrica | Teto edital `[FONTE]` | Valor (R$) | % | Status |
|---|---|---:|---:|---|
| **Pessoal** (Anexo 5) | ≤30% `[6.5.5]` | 1.800.000,00 | 25,7% | ✅ |
| **Bolsas** (Anexo 6) | ≤30% `[6.5.7]` | 1.600.000,00 | 22,9% | ✅ |
| **Serviços de TP PJ** | livre `[6.5.2]` | 850.000,00 | 12,1% | ✅ |
| **Material de consumo** | livre `[6.5.1]` | 750.000,00 | 10,7% | ✅ |
| **Equipamento permanente** | `[6.6.1/6.6.2/2.1.24]` | 750.000,00 | 10,7% | ✅ |
| **Obras** (2 ambientes) | ≤10% e ≤R$392.952/amb `[6.6.3]` | 500.000,00 | 7,1% | ✅ |
| **Despesas operacionais** | =5% `[6.5.3]` | 350.000,00 | 5,0% | ✅ |
| **Diárias** | ≤5% `[6.5.6]` | 200.000,00 | 2,9% | ✅ |
| **Passagens** | ≤5% `[6.5.6]` | 200.000,00 | 2,9% | ✅ |
| **TOTAL** | — | **7.000.000,00** | 100% | ✅ faixa R$1M–R$7M |

**Conformidade (revisão hostil):** todas as rubricas dentro dos tetos. Operacional **exatamente 5%** (=5%, item 6.5.3). Valor total no teto superior da faixa, integralmente justificado por item → **valor inabilitado-alvo = 0%** (risco R4).

---

## R1. PESSOAL — R$1.800.000,00 (25,7%) — Anexo 5

> **Consideração do time (qtos profissionais):** quadro ampliado para cobrir 2 frentes (Materiais + Eletromecânica) por 36 meses. Manter ≤30% via complemento de mão de obra por **Bolsas** (sem encargos) e **Serviços TP PJ** (transferência pessoal→PJ).

| Função | Nível (R$/h) | h/sem | 36 m (≈1.560 h) | Custo (R$) |
|---|---|---|---|---:|
| Coordenadora P&D integrado | DT3 (218,90) | 10 | 1.560 h | 341.500 |
| Pesq. Materiais sênior (Parte 1) | DT2 (179,40) | 16 | 2.496 h | 447.800 |
| Pesq. Eletromecânica sênior (Parte 2) | DT2 (179,40) | 16 | 2.496 h | 447.800 |
| 2× Apoio Técnico de bancada (AT2) | AT2 (59,90) | 20×2 | 3.120 h×2 | 373.776 |
| *Subtotal detalhado* | — | — | — | *1.610.876* |
| Reserva de banco de horas / reajuste | — | — | — | *189.124* |
| **TOTAL PESSOAL** | — | — | — | **1.800.000** |

*(Somatório ≤30% confirmado. Detalhamento mensal na escrita fina da Plataforma FINEP.)*

## R2. BOLSAS — R$1.600.000,00 (22,9%) — Anexo 6 / Portaria CNPq 2262/2025

> **Consideração do time (pesquisadores):** bolsas escalam mão de obra intensiva de bancada/campo sem encargos — núcleo da P&D de 3 anos.

| Bolsa | Categoria | Valor mensal | Período | Custo (R$) |
|---|---|---|---|---:|
| 2× Doutorado (material + campo) | SET D | 3.250 | 36 m ×2 | 234.000 |
| 3× Mestrado (bancada mecânica/eletrotéc) | SET F | 2.200 | 36 m ×3 | 237.600 |
| 3× Desenvolv. industrial (protótipo) | DTI B | 3.900 | 24 m ×3 | 280.800 |
| 1× Especialista eólica/PMG | EXP A | 5.200 | 18 m | 93.600 |
| 4× Iniciação científica | SET H | 1.560 | 36 m ×4 | 224.640 |
| 1× Pós-doc júnior | SET E | 2.600 | 24 m | 62.400 |
| 2× DTI apoio (simulação/dados) | DTI C | 1.430 | 24 m ×2 | 68.640 |
| *Subtotal* | — | — | — | *1.201.680* |
| Reserva (renewal/cobertura de vagas) | — | — | — | *398.320* |
| **TOTAL BOLSAS** | — | — | — | **1.600.000** |

## R3. SERVIÇOS DE TP PJ — R$850.000,00 (livre, item 6.5.2)

> **Considerações do time incorporadas:**
> (a) **Ensaios iterativos de P&D** — desenvolvimento de material novo NÃO é ensaio único; são ~5 ciclos de formulação→ensaio→reformulação até obter o produto-alvo. Cada ciclo re-executa tração/flexão/Izod/fadiga + caracterização microestrutural.
> (b) **PI nacional + INTERNACIONAL** — depósito INPI + pedido PCT + entrada em fases nacionais (US/EU/CN) + honorários de procurador + **anuidades/tempo de licença** durante o projeto.
> (c) **HPC** — computação de alto rendimento sob demanda (cloud) para FEM/CFD.
> (d) Logística de campo realocada para esta rubrica (sem teto) para respeitar o 5% de Diárias.

| Bloco | Norma/justif. | Ciclos/qty | Valor (R$) |
|---|---|---|---:|
| Ensaios mecânicos iterativos (D638/D790/D256/D7774 + fluência E139/Norton 1.000 h) | specs 001–005 | 5 ciclos × ~50 CP | 180.000 |
| Microestrutura iterativa (MEV+EDS, TGA E1131, DSC D3418, FTIR E1252) | spec 003 | 5 ciclos | 90.000 |
| END iterativo (ultrassom phased-array ISO 16811 + termografia E2582) | spec 004 | 4 ciclos | 55.000 |
| Envelhecimento longo (UV G154, umidade D2247, salt-spray B117, ciclagem D6944) | spec 006 | 3 ciclos | 95.000 |
| **PI nacional + internacional** (INPI + PCT + fases US/EU/CN + procurador + anuidades) | §PI | ciclo completo | **220.000** |
| Ensaios Parte 2 (túnel de vento + banco de carga + concretagem + bobinagem PMG) | Parte 2 | 6 unid. | 95.000 |
| HPC/cloud computing (FEM CalculiX/CFD OpenFOAM sob demanda) | ambas | 36 m | 45.000 |
| Logística de campo (hospedagem/fretes/capacitação terceirizada) — *realocada de Diárias* | Parte 2 | M12–M30 | 70.000 |
| **TOTAL TP PJ** | — | — | **850.000** |

### R3.1 Detalhamento PI nacional + internacional (R$220.000)
| Item | Valor (R$) | Base |
|---|---:|---|
| Depósito patente INPI (BR) + busca de anterioridades | 8.000 | INPI tabelas 2026 |
| Pedido PCT (international application) | 30.000 | WIPO PCT-RO/101 (~US$5.800) |
| Fases nacionais (US/USPTO, EU/EPO, China/CNIPA) — tradução + taxas | 120.000 | ~3× US$7.700 |
| Honorários procurador de PI (BR + exterior) | 40.000 | Tabela ABPI |
| Anuidades/tempo de licença (manutenção durante 36 m) | 22.000 | INPI anuidades + PCT |
| **Subtotal PI** | **220.000** | |

## R4. MATERIAL DE CONSUMO — R$750.000,00 (livre, item 6.5.1)

| Bloco | Conteúdo | Valor (R$) |
|---|---|---:|
| Insumos PM-15G (papel reciclado, PVA, grafite mesh 325, água deionizada, desmoldante, EPI) — 2.000 kg compósito (5 ciclos) | Parte 1 | 42.000 |
| Bancada Parte 1 (balança, misturador planetário, triturador, moldes ASTM, durômetro Shore D, pistola coating) | Parte 1 | 52.000 |
| Bancada Parte 2 (banco baterias 150 Ah ×30 + eletrônica NR-10 + instrumentação Arduino/GSM ×6 + cabeamento) | Parte 2 | 74.000 |
| Ferramental + reposição de moldes (5 ciclos) | ambas | 38.000 |
| Reagentes + corpos-de-prova 36 m (~1.500 CP acumulado) | Parte 1 | 85.000 |
| Mantimentos de campo + capacitação comunitária (5 comunidades) | Parte 2 | 120.000 |
| Reserva de robustez 36 m (reposição, inflação, quebras) | ambas | 339.000 |
| **TOTAL CONSUMO** | — | **750.000** |

## R5. EQUIPAMENTO PERMANENTE — R$750.000,00

> **Regra 6.6.1/6.6.2/2.1.24:** item ≥R$50K é livre (6.6.1); item <R$50K **só** da lista permitida (6.6.2); sistema composto = **item único + PDF único + justificativa** (2.1.24).

| Item | Rubrica | Origem | Valor (R$) |
|---|---|---|---:|
| Prensa hidráulica moldagem 50 t (P≥0,5 MPa) | ≥R$50K `[6.6.1]` | Parte 1 | 95.000 |
| Estufa secagem/cura 500 L | ≥R$50K `[6.6.1]` | Parte 1 | 62.000 |
| Máquina universal de ensaios 50 kN (EMU) | ≥R$50K `[6.6.1]` | Parte 1+2 | 130.000 |
| **Servidor/workstation HPC** (FEM/CFD — ≥R$50K) | ≥R$50K `[6.6.1]` | ambas | **90.000** |
| Bancada de testes PMG/eletrônica (≥R$50K) | ≥R$50K `[6.6.1]` | Parte 2 | 100.000 |
| **Gerador Savonius ×6 (sistema composto: rotor PM-15G + PMG + torre + eletrônica)** | **item único `[2.1.24]`** | Parte 2 | 75.000 |
| 6× sistema de irrigação (cada <R$50K: bomba CC 24V + controlador + cisterna) | lista `[6.6.2]` | Parte 2 | 100.000 |
| Nobreak + chiller + AC + casa de vegetação (<R$50K) | lista `[6.6.2]` | Parte 1 | 98.000 |
| **TOTAL EQUIP** | — | — | **750.000** |

> **Risco R12 (2.1.24):** o gerador Savonius é **1 item + 1 PDF + justificativa**. Listar rotor/PMG/torre separadamente = eliminação.

## R6. OBRAS — R$500.000,00 (7,1% ≤10%; ≤R$392.952/ambiente, Dec. 12.807/2025)

> **Consideração do time (infra/área p/ encaixar Lab1 + Lab2):** adaptação de **2 ambientes laboratoriais** dedicados — um de **Materiais** (Lab1) e um **Eletromecânico** (Lab2: mecânicos + eletotécnicos), além do sistema de efluentes e fundações de campo.

| Item | Rubrica | Valor (R$) |
|---|---|---:|
| **Ambiente 1 — Lab Materiais** (piso químico, elétrica 220 V, exaustão, NR-8/23, NBR 14725) | Obra `[6.6.3]` | 200.000 |
| **Ambiente 2 — Lab Eletromecânico** (piso técnico, bancada mecânica + eletrotécnica, NR-10/18) | Obra `[6.6.3]` | 200.000 |
| Sistema de tratamento de efluentes (caixa separadora + filtração PVA, CONAMA 430/2011) | Obra `[6.6.3]` | 50.000 |
| Fundações das 6 unidades (concreto, fixação torre treliça 10 m) | Obra `[6.6.3]` | 50.000 |
| **TOTAL OBRAS** | — | **500.000** |

> Verificação de teto: 2 ambientes × R$200.000 ≤ R$392.952/ambiente? — **R$200.000 < R$392.952 ✅**. Proformas de obra com defasagem máx. 6 meses (risco R6); responsáveis CREA/CAU.

## R7. DIÁRIAS / PASSAGENS / OPERACIONAL — R$750.000,00

> **Consideração do time (viagens a comunidades + congressos COP-31/32):** diárias e passagens respeitam 5% cada; **inscrições e organização de congressos** vão para TP PJ/operacional. Congressos internacionais de disseminação (COP-31 2026, COP-32 2027 e análogos: EWEA/WindEnergy, ICCM biomateriais) — 2 deslocamentos internacionais + campo nacional.

| Rubrica | Teto | Composição | Valor (R$) |
|---|---|---|---:|
| Diárias | ≤5% `[6.5.6]` | Campo 5 comunidades (M12–M30) R$120K + internac. congressos (2×) R$80K | 200.000 |
| Passagens | ≤5% `[6.5.6]` | Nacionais PE/BA/GO + congressos BR R$120K + internac. (COP-31/32) R$80K | 200.000 |
| Despesas operacionais | =5% `[6.5.3]` | Energia, materiais de escritório, comunicação, seguros, software | 350.000 |
| **TOTAL** | — | — | **750.000** |

> **COP-31/32:** participações condicionadas ao calendário oficial (COP-30 Belém 11/2025; COP-31 2026; COP-32 2027). Inscrições/eventos via TP PJ (sem teto); aéreo+diária via Passagens/Diárias (≤5%).

---

## VERIFICAÇÃO DE CONFORMIDADE v2.0 (revisão hostil)

| Verificação | Teto | Resultado |
|---|---|---|
| Valor total na faixa R$1M–R$7M | `[item 9]` | ✅ R$7.000.000 (teto superior) |
| Pessoal ≤30% | `[6.5.5]` | ✅ 25,7% |
| Bolsas ≤30% | `[6.5.7]` | ✅ 22,9% |
| Operacional =5% | `[6.5.3]` | ✅ 5,0% |
| Diárias ≤5% | `[6.5.6]` | ✅ 2,9% |
| Passagens ≤5% | `[6.5.6]` | ✅ 2,9% |
| Obras ≤10% e ≤R$392.952/ambiente | `[6.6.3]` | ✅ 7,1% / R$200K<amb |
| Equip ≥R$50K livre / <R$50K só lista | `[6.6.1/6.6.2]` | ✅ |
| Gerador = item composto único | `[2.1.24]` | ✅ |
| Sistema irrigação permitido | `[6.6.2]` | ✅ |
| Valor inabilitado-alvo | `[11.2.2]` | ✅ 0% (justificado por item) |
| Similar nacional comprovado | `[11.2.3]` | ⏳ pró-manual |
| Pró-manual data >01/01/2026 | `[11.2.4]` | ⏳ coletar |

---

*Orçamento versionado conforme mandato do time Lab1+Lab2. Próxima versão (v2.1) only se houver readequação de rubricas; alterações registradas em `log-versoes-orcamento.md`.*
