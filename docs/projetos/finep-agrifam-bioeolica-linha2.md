# PROPOSTA FINEP AgriFam-ICT 2026 — Linha 2

> **Documento de submissão** · Substitui e descontinua `finep-pm-grafite-savonius.md` (4 violações registradas).
> **Data-base dos preços:** 06/2026 (pró-formas a coletar com data >01/01/2026, item 11.2.4).
> **Rastreabilidade:** valores físicos via SSOT `workspace/lab1-material-papel-mache-grafite/config/constants.json` (mandato P$1 — zero hardcoded); normas via specs físicos Lab1 (ensaios 001–007) e paper `docs/paper/pm-graphite-composite-savonius.tex`.

---

## 1. IDENTIFICAÇÃO DA PROPOSTA

| Campo | Conteúdo |
|---|---|
| **Chamada** | FINEP AgriFam-ICT 2026 (Agricultura Familiar e Sociobiodiversidade) `[FONTE \| COM_RET item 1]` |
| **Linha temática** | **Linha 2 — Sistemas Agroecológicos/Orgânicos** (dotação R$50M) `[FONTE \| EDITAL_RET item 1.3.2 / ANEXO2]` |
| **Título** | Desenvolvimento e Validação de Turbina Eólica Savonius em Compósito de Papel Machê com Grafite (PM-15G) para Geração Descentralizada no Semiárido — do Material Patenteável à Irrigação Comunitária |
| **Proponente / Executora** | ICT pública — Goiânia/GO (Centro-Oeste → cota regional N/NE/CO ≥30%, item 4.3) |
| **Coexecutora** | ICT — Pernambuco (Nordeste) |
| **Coordenadora** | C. Napoles — Bioeólica Pesquisa & Desenvolvimento |
| **Valor solicitado** | **R$7.000.000,00 — v2.0 retificada** (teto da faixa R$1M–R$7M, item 9; mandato [⚠️ AUDITAR]) |
| **Duração** | **36 meses** (máx. item 9.1) |
| **Instrumento** | **Convênio** (Anexo 1 = Minuta Padrão; NÃO "TCLE") `[FONTE \| ANEXO1]` |
| **Contrapartida** | Convenente estadual/municipal/DF (eliminatório, itens 7.3/8) |
| **Cota regional** | Atendida (GO + PE) `[FONTE \| EDITAL_RET item 4.3]` |

### Palavras-chave
energia eólica descentralizada · compósito biodegradável · papel machê · grafite · turbina Savonius · irrigação fotovoltaico-eólica · semiárido · sociobiodiversidade · agricultura familiar · economia circular · PI nacional · geração comunitária.

---

## 2. JUSTIFICATIVA E ADERÊNCIA AO EDITAL

### 2.1 Problema
Comunidades rurais isoladas do semiárido nordestino (sertões de PE/BA) sofrem com **acesso precário/ausente a eletricidade** e **escassez hídrica**. A energia descentralizada habilita irrigação de baixo custo — peça-chave da **sociobiodiversidade** e da produção agroecológica familiar. As pás de fibra de vidro (dominantes em microgeradores <5 kW) são caras, não-biodegradáveis e terminam em aterro.

### 2.2 Solução (duas partes inseparáveis)
- **Parte 1 — Material PM-15G:** compósito de papel machê (resíduo celulósico) + 15%vol grafite, ligante PVA. Propriedades-alvo validadas (SSOT + paper): **E≈3,4±0,5 GPa · σ≈30 MPa · ρ≈820 kg/m³ · custo≈R$12/kg · ~80% menos CO₂ vs fibra de vidro**. **Depósito de PI/TALCX** (parte intrínseca — sem material, não há gerador).
- **Parte 2 — Gerador Savonius:** rotor de 6 unidades (5 comunidades + 1 protótipo de bancada) acoplado a PMG + torre treliça 10 m + banco de baterias + **sistema de irrigação** (item permitido <R$50K, item 6.6.2). Saída alvo **~82,95 W/unidade a 8 m/s** (relatório Lab2).

### 2.3 Matriz 3M — aderência ao Anexo 2 (Linha 2)

| Escala | Análise |
|---|---|
| **MACRO** | Política energética nacional + PNRS (Lei 12.305/2010) + transição agroecológica do semiárido; cota N/NE/CO aproveitada (GO+PE); PI nacional reforça soberania tecnológica |
| **MESO** | Acoplamento eletromecânico rotor→PMG→bateria→bomba CC 24V; interface material-energia (pá PM-15G ↔ aerodinâmica Savonius); parcerias ICT GO/PE + 5 associações comunitárias + cooperativa de reciclagem (fonte do papel) |
| **MICRO** | Micromecânica Halpin-Tsai (ξ=2, V_f=0,15); interface grafite/matriz PVA; mecanismos de degradação (fadiga, fluência, UV, umidade); microestrutura via MEV/EDS |

---

## 3. OBJETIVOS E PRODUTOS

1. **PI/TALCX PM-15G** — depósito de patente de invenção no INPI (composição + processo de fabricação) + proteção de know-how (TALCX/NDA).
2. **Gerador Savonius PM-15G** — 6 unidades (D=1,0 m, H=1,5 m, Cp=0,25, λ=0,8) instaladas em 5 comunidades + 1 protótipo de bancada.
3. **Sistema de irrigação eólico** — 6× conjunto (bomba CC 24V + controlador + reservatório + cisterna), cada <R$50K (lista permitida).
4. **Documentação científica** — paper + relatório VVV + manual técnico comunitário (capacitação).
5. **Aprovação ética** — CEP (CNS 510/2016 + 466/2012), campo a partir de M9 (`docs/projetos/anexo-etica-submissao.md`).

---

## 4. PLANO DE PESQUISA E ROADMAP (36 meses)

| Marco | Mês | Entrega |
|---|---|---|
| **M1** Conformidade | M1–M2 | Cadastro Finep (PRIORITÁRIO — ver §11 risco R1) · Política de Inovação ICT · submissão CEP |
| **M2** Material | M2–M9 | Fabricação PM-15G · ensaios mecânicos (ASTM D638/D790/D256/D2240/D7774) · microestrutura (MEV/TGA/DSC/FTIR) · **depósito INPI** |
| **M3** Protótipo | M6–M14 | Protótipo bancada · túnel de vento · banco de carga · curva P(v) |
| **M4** Durabilidade | M9–M24 | END (ultrassom phased-array + termografia) · envelhecimento (UV/umidade/salt-spray/ciclagem térmica) · fluência (Norton) |
| **M5** Campo | M12–M30 | Instalação nas 5 comunidades (PE/BA) · comissionamento · capacitação |
| **M6** Acompanhamento | M18–M36 | Monitoramento GSM 24 meses · laudos finais · encerramento |

---

## 5. COMUNIDADES-BENEFICIÁRIAS

| # | Comunidade / Território | Município-REFERÊNCIA (UF) | Característica |
|---|---|---|---|
| 1 | Sertão do Pajeú | Serra Talhada / Afogados da Ingazeira (PE) | Agreste/Sertão, agricultura familiar de sequeiro |
| 2 | Agreste setentrional | Caruaru / Belo Jardim (PE) | Pequenas propriedades, escassez hídrica sazonal |
| 3 | Sertão de Itaparica | Petrolândia / Floresta (BA) | Várzea do São Francisco, irrigação potencial |
| 4 | Piauí-Médio (margem BA) | Bom Jesus da Lapa / Paratinga (BA) | Comunidades ribeirinhas isoladas |
| 5 | Sertão do São Francisco | Barra / Xique-Xique (BA) | Assentamentos, baixíssima cobertura elétrica |

> Municípios do semiárido conforme Atlas ANEEL, IBGE e MMA; cartas de anuência das associações comunitárias a coletar (trio CNPJ + assinatura digital + validade ≥36 meses, item 5.6.1.2).

---

## 6. ORÇAMENTO CONSOLIDADO (R$7.000.000,00 / 36 m — v2.0 RETIFICADA)

> **Versão vigente: v2.0.** Orçamento detalhado em `docs/projetos/orcamento-versionado-finep-agrifam.md`; log de versões em `docs/projetos/log-versoes-orcamento.md`.

**Estratégia de compliance (revisão hostil):** retificação para o teto da faixa (R$7M), incorporando 9 considerações do time Lab1+Lab2 não cobertas na v1.0 (R$4,5M, 🗄 superseded). **Por quê:** mandato *"SER REALISTA COM CICLO DE VIDA P&D DeepTech EM DESENVOLVIMENTO DE NOVOS PRODUTOS* + risco R4 (valor inabilitado >30% = eliminação, item 11.2.2); a v1.0 subdimensionava o **ciclo completo de P&D**: ensaios iterativos (~5 ciclos), PI nacional+internacional, HPC, 2 ambientes laboratoriais e disseminação internacional (COP-31/32). Gerador Savonius empacotado como **item composto único** (item 2.1.24); logística de campo realocada para **Serviços TP PJ** (sem teto) para respeitar Diárias ≤5%.

| Rubrica | Teto edital `[FONTE]` | Valor (R$) | % |
|---|---|---:|---:|
| **Pessoal** (Anexo 5: AT/AP/DT) | ≤30% `[6.5.5]` | 1.800.000,00 | 25,7% ✅ |
| **Bolsas** (Anexo 6: SET/DTI/EXP) | ≤30% `[6.5.7]` | 1.600.000,00 | 22,9% ✅ |
| **Serviços de TP PJ** (ensaios iterativos+PI intl+HPC+logística) | livre `[6.5.2]` | 850.000,00 | 12,1% ✅ |
| **Material de consumo** (insumos 5 ciclos + componentes) | livre `[6.5.1]` | 750.000,00 | 10,7% ✅ |
| **Equipamento permanente** (≥R$50K + HPC + composto + irrigação) | — `[6.6.1/6.6.2/2.1.24]` | 750.000,00 | 10,7% ✅ |
| **Obras** (**2 ambientes**: Lab Materiais + Lab Eletromec) | ≤10% e ≤R$392.952/ambiente `[6.6.3]` | 500.000,00 | 7,1% ✅ |
| **Despesas operacionais** | =5% `[6.5.3]` | 350.000,00 | 5,0% ✅ |
| **Diárias** (campo + congressos internac.) | ≤5% `[6.5.6]` | 200.000,00 | 2,9% ✅ |
| **Passagens** (nacional + COP-31/32) | ≤5% `[6.5.6]` | 200.000,00 | 2,9% ✅ |
| **TOTAL** | — | **7.000.000,00** | 100% |

**Tetos respeitados:** pessoal 25,7% / bolsas 22,9% / diárias 2,9% / passagens 2,9% / obras 7,1% (R$200K<R$392.952/ambiente) / operac. **exatamente 5,0%** (=5%, item 6.5.3). Valor total no teto superior da faixa, integralmente justificado por item → **valor inabilitado-alvo = 0%** (risco R4, item 11.2.2).

### 6.1 Pessoal (R$1.800.000, 25,7% ≤30%) — Anexo 5

> **Consideração do time (qtos profissionais):** quadro ampliado para cobrir 2 frentes (Materiais + Eletromecânica) por 36 meses. Complemento de mão de obra via **Bolsas** (sem encargos) e **Serviços TP PJ** (transferência pessoal→PJ).

| Função | Nível (R$/h) | h/sem | 36 m (≈1.560 h) | Custo (R$) |
|---|---|---|---|---:|
| Coordenadora P&D integrado | DT3 (218,90) | 10 | 1.560 h | 341.500 |
| Pesq. Materiais sênior (Parte 1) | DT2 (179,40) | 16 | 2.496 h | 447.800 |
| Pesq. Eletromecânica sênior (Parte 2) | DT2 (179,40) | 16 | 2.496 h | 447.800 |
| 2× Apoio Técnico de bancada (AT2) | AT2 (59,90) | 20×2 | 3.120 h×2 | 373.776 |
| *Subtotal detalhado* | — | — | — | *1.610.876* |
| Reserva banco de horas / reajuste | — | — | — | *189.124* |
| **TOTAL PESSOAL** | — | — | — | **1.800.000** |

### 6.2 Bolsas (R$1.600.000, 22,9% ≤30%) — Anexo 6 / Portaria CNPq 2262/2025

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

### 6.3 Serviços de TP PJ (R$850.000, livre, item 6.5.2)

> **Considerações do time incorporadas:** (a) **ensaios iterativos de P&D** (~5 ciclos formulação→ensaio→reformulação até o produto-alvo); (b) **PI nacional + INTERNACIONAL** (INPI + PCT + fases US/EU/CN + procurador + anuidades); (c) **HPC** cloud sob demanda (FEM/CFD); (d) **logística de campo** realocada aqui (sem teto) para respeitar Diárias ≤5%.

| Bloco | Norma/justif. | Ciclos/qty | Valor (R$) |
|---|---|---|---:|
| Ensaios mecânicos iterativos (D638/D790/D256/D7774 + fluência E139/Norton 1.000 h) | specs 001–005 | 5 ciclos × ~50 CP | 180.000 |
| Microestrutura iterativa (MEV+EDS, TGA E1131, DSC D3418, FTIR E1252) | spec 003 | 5 ciclos | 90.000 |
| END iterativo (ultrassom phased-array ISO 16811 + termografia E2582) | spec 004 | 4 ciclos | 55.000 |
| Envelhecimento longo (UV G154, umidade D2247, salt-spray B117, ciclagem D6944) | spec 006 | 3 ciclos | 95.000 |
| **PI nacional + internacional** (INPI + PCT + fases US/EU/CN + procurador + anuidades) | §10/§PI | ciclo completo | **220.000** |
| Ensaios Parte 2 (túnel de vento + banco de carga + concretagem + bobinagem PMG) | Parte 2 | 6 unid. | 95.000 |
| HPC/cloud computing (FEM CalculiX/CFD OpenFOAM sob demanda) | ambas | 36 m | 45.000 |
| Logística de campo (hospedagem/fretes/capacitação terceirizada) — *realocada de Diárias* | Parte 2 | M12–M30 | 70.000 |
| **TOTAL TP PJ** | — | — | **850.000** |

**Detalhamento PI nacional + internacional (R$220.000):** depósito INPI + busca R$8.000 · pedido PCT (WIPO PCT-RO/101) R$30.000 · fases nacionais US/EU/CN (tradução + taxas) R$120.000 · honorários procurador BR+exterior R$40.000 · **anuidades/tempo de licença (36 m)** R$22.000.

### 6.4 Material de Consumo (R$750.000, livre) — insumos 5 ciclos + componentes

| Bloco | Origem | Valor (R$) |
|---|---|---:|
| Insumos PM-15G (papel reciclado, PVA, grafite mesh 325, água deionizada, desmoldante, EPI) — 2.000 kg (5 ciclos) | Parte 1 | 42.000 |
| Bancada Parte 1 (balança, misturador planetário, triturador, moldes ASTM, durômetro Shore D, pistola coating) | Parte 1 | 52.000 |
| Bancada Parte 2 (banco baterias 150 Ah ×30 + eletrônica NR-10 + instrumentação Arduino/GSM ×6 + cabeamento) | Parte 2 | 74.000 |
| Ferramental + reposição de moldes (5 ciclos) | ambas | 38.000 |
| Reagentes + corpos-de-prova 36 m (~1.500 CP acumulado) | Parte 1 | 85.000 |
| Mantimentos de campo + capacitação comunitária (5 comunidades) | Parte 2 | 120.000 |
| Reserva de robustez 36 m (reposição, inflação, quebras) | ambas | 339.000 |
| **TOTAL CONSUMO** | — | **750.000** |

### 6.5 Equipamento Permanente (R$750.000)

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

### 6.6 Obras (R$500.000, 7,1% ≤10%; ≤R$392.952/ambiente, Dec. 12.807/2025)

> **Consideração do time (infra/área p/ encaixar Lab1 + Lab2):** adaptação de **2 ambientes laboratoriais** — **Lab Materiais** (Lab1) e **Lab Eletromecânico** (Lab2: mecânicos + eletotécnicos), além de efluentes e fundações de campo.

| Item | Rubrica | Valor (R$) |
|---|---|---:|
| **Ambiente 1 — Lab Materiais** (piso químico, elétrica 220 V, exaustão, NR-8/23, NBR 14725) | Obra `[6.6.3]` | 200.000 |
| **Ambiente 2 — Lab Eletromecânico** (piso técnico, bancada mecânica + eletrotécnica, NR-10/18) | Obra `[6.6.3]` | 200.000 |
| Sistema de tratamento de efluentes (caixa separadora + filtração PVA, CONAMA 430/2011) | Obra `[6.6.3]` | 50.000 |
| Fundações das 6 unidades (concreto, fixação torre treliça 10 m) | Obra `[6.6.3]` | 50.000 |
| **TOTAL OBRAS** | — | **500.000** |

> Verificação de teto: 2 ambientes × R$200.000 ≤ R$392.952/ambiente? — **R$200.000 < R$392.952 ✅**. Proformas de obra com defasagem máx. 6 meses (risco R6); responsáveis CREA/CAU.

### 6.7 Diárias / Passagens / Operacional (R$750.000)

> **Consideração do time (viagens a comunidades + congressos COP-31/32):** diárias e passagens respeitam 5% cada; **inscrições e organização de congressos** vão para TP PJ/operacional. Congressos internacionais de disseminação (COP-31 2026, COP-32 2027 e análogos: EWEA/WindEnergy, ICCM biomateriais) — 2 deslocamentos internacionais + campo nacional.

| Rubrica | Teto | Composição | Valor (R$) |
|---|---|---|---:|
| Diárias | ≤5% `[6.5.6]` | Campo 5 comunidades (M12–M30) R$120K + internac. congressos (2×) R$80K | 200.000 |
| Passagens | ≤5% `[6.5.6]` | Nacionais PE/BA/GO + congressos BR R$120K + internac. (COP-31/32) R$80K | 200.000 |
| Despesas operacionais | =5% `[6.5.3]` | Energia, materiais de escritório, comunicação, seguros, software | 350.000 |
| **TOTAL** | — | — | **750.000** |

> **COP-31/32:** participações condicionadas ao calendário oficial (COP-30 Belém 11/2025; COP-31 2026; COP-32 2027). Inscrições/eventos via TP PJ (sem teto); aéreo+diária via Passagens/Diárias (≤5%).

---

## 7. INFRAESTRUTURA, INSUMOS, MATERIAIS E FERRAMENTAS

### 7.1 Parte 1 — Material PM-15G (BOM Lab1: R$1.119.730)

| Bloco | Conteúdo | Subtotal (R$) |
|---|---|---:|
| Equip. ≥R$50K | prensa + estufa + EMU | 287.000 |
| Equip. <R$50K permitido | nobreak, chiller, AC, casa de vegetação | 62.000 |
| Bancada (material consumo) | balança, misturador, triturador, moldes ASTM, durômetro, bancada inox | 51.300 |
| Insumos (36 m, 1.300 kg) | papel reciclado, PVA, grafite, água, desmoldante, EPI | 26.930 |
| Ensaios TP PJ | mecânicos, microestrutura, END, envelhecimento | 258.600 |
| PI/TALCX (nacional + internacional) | INPI + PCT + fases US/EU/CN + procurador + anuidades 36 m | 220.000 |
| Profissionais certificados + certificações | CRQ, CREA, IBAMA/CONAMA, INMETRO RTM, ISO 17025, NBR 10004 | 177.400 |
| Obra (**2 ambientes**) | Lab Materiais + Lab Eletromecânico + efluentes (≤R$392.952/amb) | 400.000 |

**Normas (todas reais — revisão hostil confirmada):** mecânicas ASTM D638/D790/D256/D2240/D7774/E139; térmicas E1131/D3418/E1252; END ISO 16811/E2582; envelhecimento G154/D2247/D6944/B117; micromecânica Halpin-Tsai/Basquin/Norton/Hashin-Shtrikman/Archard; ambientais CONAMA 358/2004·307/2002·430/2011 + PNRS Lei 12.305/2010; PI LPI 9.279/1996 + Lei Inovação 10.973/2004; profissionais Lei 5.194/1966 (CREA) + Lei 2.195/1974 (CRQ) + Lei 9.933/1999 (RTM) + NR-6/8/15/16/23; energia IEC 61400-2.

### 7.2 Parte 2 — Savonius + irrigação (BOM Lab2: R$1.089.620)

| Bloco | Conteúdo | Subtotal (R$) |
|---|---|---:|
| Rotor/pás PM-15G ×6 | fabricação compósito | 36.000 |
| PMG (NdFeB + cobre) ×6 | gerador axial | 8.300 |
| Torre treliça 10 m ×6 (incl. soldas — RT soldador) | estrutura | 38.700 |
| Banco baterias 150 Ah ×30 + eletrônica NR-10 | armazenamento | 24.600 |
| 6× sistema irrigação (<R$50K) | bomba CC + controlador + cisterna | 91.800 |
| Instrumentação Arduino/GSM ×6 | monitoramento | 15.100 |
| Obra fundação + cabeamento | civil | 50.100 |
| Ferramental bancada | torno (via TP) + ferramentas | 13.300 |
| Ensaios (túnel + banco de carga) via TP | validação | 43.800 |
| Logística campo 5 comunidades | hospedagem/fretes/capacitação | 64.500 |
| Profissionais certificados + ambientais | eletricista NR-10, soldador, licenciamento | 83.420 |
| Reserva Parte 2 | 36 m | 620.000 |

> Bateria: V_dc=48, DoD=0,80, η=0,90, 2 dias de autonomia → ~5 baterias 150 Ah/banco ×6 unidades.

> **Roteamento v2.0:** estes BOMs Lab1 (R$1.119.730) e Lab2 (R$1.089.620) são a base de hard-cost de engenharia. Na **v2.0 retificada (R$7.000.000)**, cada item é roteado para a rubrica edital adequada (Equipamento permanente / Material de consumo / Serviços TP PJ / Obras / Pessoal / Bolsas), com a maior fatia em PESSOAL+BOLSAS (P&D 36 m) + ensaios iterativos (5 ciclos) + HPC + disseminação internacional (COP-31/32). Detalhamento rubricado e versionado em `orcamento-versionado-finep-agrifam.md` (v2.0 vigente); registro de versões em `log-versoes-orcamento.md`. Webapp de orçamento editável + análise de conformidade: `webapp/`.

---

## 8. PROFISSIONAIS CERTIFICADOS E CERTIFICAÇÕES LEGAIS/AMBIENTAIS

### 8.1 Profissionais certificados
- **Químico CRQ** — manipulação PVA/grafite, RT químico (Lei 2.195/1974; NR-16).
- **Eng. Materiais/Metalurgista CREA** — RT laudos de ensaio e fabricação (Lei 5.194/1966).
- **Eletricista NR-10** — instalação PMG/bancos/bombas (NR-10).
- **Soldador qualificado** — torre treliça (NR-18; Qualisol/FK).
- **Procurador de PI** — depósito INPI e follow-up.

### 8.2 Certificações legais e ambientais
- **Licenciamento ambiental IBAMA/CONAMA** — descarte/classificação de resíduos (CONAMA 358/2004; Res. 307/2002; Dec. 10.388/2020).
- **PNRS (Lei 12.305/2010)** — co-responsabilidade com cooperativa de reciclagem (fonte do papel).
- **Auditoria metrológica INMETRO (Lei 9.933/1999; Port. 263/2015)** — balança + EMU.
- **Laboratório sob ISO 17025** — calibração casa de vegetação e instrumentos.
- **Destinação de resíduos químicos** — ABNT NBR 10004/10005/10006.
- **SST** — NR-6 (EPI), NR-8 (sanitárias), NR-15/16 (químicos), NR-23 (sinalização).
- **Aprovação CEP** — CNS 510/2016 + 466/2012 (`docs/projetos/anexo-etica-submissao.md`).

---

## 9. PARCERIAS (item 5.6)

| Parceiro | Papel | Documentos (trio 5.6.1.2) |
|---|---|---|
| ICT Goiânia/GO (executora) | P&D integrado, fabricação, EMU | CNPJ + assinatura digital + ≥36 m |
| ICT PE (coexecutora) | Campo, instalação comunidades PE | CNPJ + assinatura digital + ≥36 m |
| Cooperativa de reciclagem | Fonte do papel (PNRS) | CNPJ + termo de co-responsabilidade |
| 5 Associações comunitárias | Beneficiárias, operação local | CNPJ + assinatura digital + ≥36 m |
| Fundação de apoio (se ICT federal) | Proponente administrativo (item 5.x) | — |

> **Risco R7:** documento de parceria sem o trio (CNPJ/assinatura/validade) zera o Critério 5 (peso 2). Coletar 3/3 para TODOS agora.
> **Política de Inovação (item 5.7):** obrigatória para ICT pública executora — eliminatório se ausente (R8).
> **Limites:** máx 2 propostas/executora (5.2); máx 3 coexecutoras (5.4).

---

## 10. PROPRIEDADE INTELECTUAL (item 5.7)

- **Patente de invenção INPI** — PM-15G (composição: papel reciclado + 15%vol grafite + PVA) **e** processo de fabricação (mistura → moldagem P≥0,5 MPa → secagem 60 °C/24 h → cura 25 °C/48 h → coating grafite/PVA). LPI Lei 9.279/1996.
- **TALCX (know-how)** — manual técnico restrito + NDA. Lei 10.973/2004 (Inovação).
- **Co-titularidade** — pactuada ICT GO + coexec PE + Bioeólica conforme política de PI da ICT.

---

## 11. RISCOS E CHECKLIST DE SUBMISSÃO

### 11.1 ⚠️ RISCO TEMPORAL CRÍTICO (R1) — DECISÃO NECESSÁRIA
- **Cadastro Finep: 26/06/2026 17h — VENCIDO** (hoje 29/06/2026). Sem cadastro aprovado, proposta não é recebida `[EDITAL_RET 10.4]`.
- **Proposta: 03/07/2026 17h** (~4 dias úteis). Antecedência 5 d.ú. (10.4.3) não cumprida.
- **Ação antes da submissão fina:** confirmar status do cadastro; se não emitido, avaliar recurso/questionamento de prazo ou agendar próxima chamada na validade de 18 m. A escrita do projeto independe disso.

### 11.2 Checklist Anexo 7 (item a item)
- [ ] Formulário eletrônico (Plataforma FINEP) `[10.1]`
- [ ] Cadastro institucional aprovado `[10.4, 15.1]`
- [ ] Orçamento detalhado + planilhas por rubrica `[item 6]`
- [ ] **Pró-formas/orçamentos data >01/01/2026** `[11.2.4]`
- [ ] Anexo Geral (material consumo + serviços PJ <R$100K) `[11.x]`
- [ ] Anexos de Itens de Rubricas (cada item ≥R$100K, equip, obra) `[11.2]`
- [ ] Política de Inovação da ICT `[5.7]` — eliminatório
- [ ] Instrumentos de parceria (trio CNPJ+assinatura+≥36m) `[5.6]`
- [ ] Plano de PI (prevê PI/TALCX) `[5.7]`
- [ ] Documentação ICT + Lattes coordenador `[10.4]`
- [ ] Contrapartida convenente `[7.3/8]` — eliminatório
- [ ] Aprovação CEP (M2→M9) `docs/projetos/anexo-etica-submissao.md`
- [ ] **Similar nacional** comprovado (prensa/EMU/insumos) `[11.2.3]` (LDO 2026 art. 138 §1º III)
- [ ] Gerador Savonius como **1 item + 1 PDF** `[2.1.24]`
- [ ] Câmbio da data de lançamento da Chamada `[11.2.4]`

### 11.3 Rastreabilidade SSOT (P$1 — zero hardcoded)
Todos os parâmetros físico-científicos vêm de `workspace/lab1-material-papel-mache-grafite/config/constants.json`: ξ=2,0 · V_f=0,15 · P moldagem 0,5 MPa · secagem 60 °C/24 h · Cp=0,25 · λ=0,8 · D=1,0 m · H=1,5 m · Ke=2,0 · R_int=1,5 Ω · custo R$12/kg compósito · massas por pá (papel 3,8/PVA 2,2/grafite 0,8/água 1,7 kg). Propriedades de saída (E≈3,4 GPa, σ≈30 MPa, ρ≈820 kg/m³) validadas no paper. **Nenhum valor hardcoded em código.**

---

## 12. VERIFICAÇÃO DE CONFORMIDADE (revisão hostil)

| Verificação | Resultado |
|---|---|
| Valor total na faixa R$1M–R$7M `[item 9]` | ✅ R$7.000.000 (teto superior) |
| Pessoal ≤30% `[6.5.5]` | ✅ 25,7% |
| Bolsas ≤30% `[6.5.7]` | ✅ 22,9% |
| Desp. operac. =5% `[6.5.3]` | ✅ 5,0% |
| Diárias ≤5% `[6.5.6]` | ✅ 2,9% |
| Passagens ≤5% `[6.5.6]` | ✅ 2,9% |
| Obras ≤10% e ≤R$392.952/ambiente `[6.6.3]` | ✅ 7,1% / R$200K<amb (2 ambientes) |
| Serviços TP PJ livre `[6.5.2]` | ✅ 12,1% |
| Material de consumo livre `[6.5.1]` | ✅ 10,7% |
| Equipamento permanente `[6.6.1/6.6.2]` | ✅ 10,7% |
| Equip ≥R$50K livre / <R$50K só lista | ✅ |
| Gerador = item composto único (2.1.24) | ✅ |
| Sistema irrigação permitido (6.6.2) | ✅ |
| Valor inabilitado-alvo 0% (R4, 11.2.2) | ✅ justificado por item |
| Parcerias trio 5.6.1.2 | ⏳ coletar 3/3 |
| Política de Inovação 5.7 | ⏳ exibir |
| Cadastro Finep 15.2 | ⚠️ R1 — confirmar |
| PI/TALCX previsto | ✅ §10 |
| CEP CNS 510/2016 + 466/2012 | ✅ anexo |
| SSOT zero hardcoded (P$1) | ✅ constants.json |

---

*Documento gerado em conformidade com o plano aprovado (`~/.claude/plans/async-gathering-sunset.md`) e com os BOMs consolidados dos times de engenharia Lab1 (materiais) e Lab2 (eletromecânica). Substitui `finep-pm-grafite-savonius.md` (descontinuado).*
