> ⛔ **DESCONTINUADO — NÃO USAR PARA SUBMISSÃO** (2026-06-29)
>
> Este documento foi **substituído** por [`finep-agrifam-bioeolica-linha2.md`](./finep-agrifam-bioeolica-linha2.md)
> (orçamento versionado v2.0 retificada, R$ 7.000.000 / 36 meses) e está retido apenas como registro histórico.
> Contém **4 violações eliminatórias** às regras do edital FINEP **AgriFam-ICT 2026** (não ao edital aqui citado):
>
> | # | Violação | Valor neste doc | Regra do edital AgriFam-ICT 2026 |
> |---|----------|-----------------|----------------------------------|
> | 1 | **Valor abaixo do piso** | R$ 847.200,00 | Faixa mínima **R$ 1.000.000,00** (§1.4) |
> | 2 | **Edital incorreto** | "FINEP — Energias Renováveis para Comunidades Isoladas (MCTI/FINEP 2025)" | Chamada correta: **FINEP AgriFam-ICT 2026** |
> | 3 | **Duração divergente** | 24 meses (M1–M24) | **36 meses** (item 9.1) |
> | 4 | **Bolsas acima do teto** | 42,5 % do total | **≤ 30 %** (item 6.5.7) |
> | 5 | **Diárias + Passagens acima do teto** | 8,0 % (somado) | **≤ 5 % cada** (item 6.5.6) |
>
> O orçamento válido/canônico vive em `finep-agrifam-bioeolica-linha2.md` +
> `orcamento-versionado-finep-agrifam.md` (webapp: `webapp/seed.js`, SSOT: `workspace/lab1-.../config/constants.json`).

---

# PROJETO FINEP — Turbina Eólica Savonius em Compósito PM-Grafite para Comunidades Isoladas do Semiárido Nordestino

## 1. IDENTIFICAÇÃO DO PROJETO

| Campo | Valor |
|-------|-------|
| **Título** | Desenvolvimento e Validação de Turbina Eólica Savonius em Compósito de Papel Machê com Grafite para Geração Descentralizada no Semiárido Nordestino |
| **Sigla** | SAVONIUS-PM-15G |
| **Área** | Geração de Energia Renovável / Materiais Compósitos Sustentáveis |
| **Duração** | 24 meses (M1–M24) |
| **Valor solicitado** | R\$ 847.200,00 |
| **Instituição proponente** | Bioeólica Pesquisa & Desenvolvimento |
| **Coordenador** | C. Napoles |
| **Edital** | FINEP — Energias Renováveis para Comunidades Isoladas (Chamada Pública MCTI/FINEP 2025) |

---

## 2. RESUMO EXECUTIVO

O projeto propõe o desenvolvimento, fabricação e validação em campo de uma turbina eólica Savonius de eixo vertical (1,0 m diâmetro × 1,5 m altura, 83 W elétricos a 8 m/s) cujas pás são fabricadas em compósito biodegradável de papel machê reforçado com 15% vol. de grafite (PM-15G). O material, com E = 3,4 GPa, σ_r = 30 MPa e ρ = 820 kg/m³, é 60–70% mais barato que fibra de vidro e integralmente compostável ao fim da vida útil. O projeto abrange desde a caracterização mecânica experimental do compósito até a implantação de três unidades piloto em comunidades rurais do semiárido baiano, com monitoramento remoto de desempenho por 12 meses.

**Objetivo geral:** Demonstrar a viabilidade técnica, econômica e socioambiental de turbinas eólicas de baixíssimo custo para eletrificação de comunidades isoladas, utilizando materiais reciclados e processos produtivos de baixa emissão de carbono.

---

## 3. JUSTIFICATIVA

### 3.1 Contexto Energético do Semiárido Nordestino

A região semiárida do Nordeste brasileiro abriga aproximadamente 27 milhões de habitantes, dos quais 1,5 milhão ainda não têm acesso à energia elétrica confiável (IBGE, 2023). Embora a região possua o melhor potencial eólico do país (velocidades médias anuais de 5–7 m/s a 10 m de altura), a geração descentralizada de pequeno porte permanece incipiente. As principais barreiras são:

1. **Custo das turbinas comerciais:** Um aerogerador de 1 kW instalado custa entre R\$ 15.000 e R\$ 25.000, inviável para comunidades com renda per capita abaixo de R\$ 500/mês.
2. **Manutenção especializada:** Turbinas convencionais requerem técnicos treinados e peças de reposição não disponíveis localmente.
3. **Descarte de pás:** As pás de fibra de vidro têm vida útil de 15–20 anos e não são recicláveis, gerando resíduo de difícil destinação.

### 3.2 Oportunidade Tecnológica

O compósito PM-15G oferece uma alternativa radicalmente diferente: matéria-prima local (papel reciclado, cola branca PVA), processo produtivo de baixa temperatura (secagem a 60 °C, sem fornos industriais) e descarte por compostagem doméstica. Para a turbina Savonius, cujo baixo λ (~0,8) gera tensões nas pás de apenas 5–8 MPa em operação normal, as propriedades mecânicas do PM-15G são suficientes.

---

## 4. OBJETIVOS

### 4.1 Objetivo Geral

Validar experimentalmente o compósito PM-15G como material estrutural para pás de turbina Savonius e demonstrar a operação de três unidades piloto em comunidades do semiárido baiano.

### 4.2 Objetivos Específicos

| # | Objetivo | Métrica de Sucesso |
|---|----------|-------------------|
| OE1 | Caracterizar mecanicamente o compósito PM-15G (tração, flexão, impacto, dureza, fadiga) | ≥80% das propriedades dentro do intervalo predito pelo modelo Halpin-Tsai |
| OE2 | Otimizar o processo de fabricação (moagem, mistura, moldagem, secagem, pintura condutiva) | Ciclo de produção ≤ 48 h por pá; taxa de refugo < 15% |
| OE3 | Projetar e fabricar 3 turbinas Savonius completas (rotor + PMG + torre) | Potência elétrica ≥ 80 W a 8 m/s |
| OE4 | Instalar e monitorar 3 unidades piloto em comunidades rurais | Disponibilidade operacional ≥ 85% em 12 meses |
| OE5 | Avaliar aceitação social, capacitação local e modelo de negócio | ≥70% de satisfação dos usuários |

---

## 5. METODOLOGIA

### 5.1 Macroetapas e Cronograma

| Mês | 1-3 | 4-6 | 7-9 | 10-12 | 13-15 | 16-18 | 19-21 | 22-24 |
|-----|-----|-----|------|-------|-------|-------|-------|-------|
| WP1 Caracterização | === | === | | | | | | |
| WP2 Processo | | === | === | | | | | |
| WP3 Projeto+Fabricação | | | === | === | === | | | |
| WP4 Instalação | | | | === | === | | | |
| WP5 Monitoramento | | | | | === | === | === | |
| WP6 Análise | | | | | | === | === | === |
| WP7 Disseminação | | | | | | === | === | === |

#### WP1 — Caracterização do Compósito (M1–M6, R\$ 156.000)

- Ensaio de tração (ASTM D638): 30 corpos de prova, 5 lotes
- Ensaio de flexão 3 pontos (ASTM D790): 30 corpos
- Impacto Izod (ASTM D256): 20 corpos
- Dureza Shore D (ASTM D2240)
- Fadiga flexional (ASTM D7774): curva S-N, R = 0,1, 10 Hz
- Microscopia eletrônica de varredura (MEV) de fratura
- Termogravimetria (TGA) e calorimetria diferencial (DSC)
- Ensaios de envelhecimento acelerado: UV (1000 h), umidade (95% UR, 500 h), ciclagem térmica (−5 a 60 °C, 200 ciclos)

#### WP2 — Otimização do Processo (M3–M8, R\$ 128.000)

- Parametrização: granulometria do grafite, tempo de moagem, razão fibra/cola, pressão de moldagem, temperatura e tempo de secagem
- Método de superfície de resposta (RSM) com DOE fatorial fracionário 2^(5−1)
- Validação: resistência à tração como variável resposta
- Pintura condutiva: grafite + PVA spray vs. pincel, espessura 0,3–0,8 mm

#### WP3 — Projeto e Fabricação das Turbinas (M5–M14, R\$ 264.000)

- Projeto estrutural detalhado (SolidWorks / CalculiX FEM)
- Fabricação de moldes de silicone para as pás
- Geração PMG: ímãs de ferrita, enrolamento cobre 18 AWG
- Torre treliçada em aço galvanizado (10 m)
- Controlador de carga PWM 12 V / 30 A
- 3 turbinas completas (1 reserva + 2 instalação)

#### WP4 — Instalação em Campo (M9–M16, R\$ 112.000)

- Seleção de 3 comunidades (critérios: velocidade média ≥ 5 m/s, sem rede elétrica, 10–30 famílias)
- Preparação de bases e fundações
- Instalação eletromecânica e comissionamento
- Baterias estacionárias 150 Ah / 12 V (2 por unidade)
- Treinamento de moradores para operação e manutenção básica

#### WP5 — Monitoramento Remoto (M10–M21, R\$ 72.000)

- Sensores: tensão, corrente, rotação, temperatura, velocidade do vento — datalogger Arduino + SD
- Transmissão: GSM/GPRS com cartão M2M
- Indicadores mensais: energia gerada (kWh), disponibilidade (%), falhas
- Visitas técnicas trimestrais para inspeção visual das pás

#### WP6 — Análise e Publicação (M16–M24, R\$ 68.000)

- Análise comparativa: PM-15G vs. predições computacionais
- Atualização do modelo Halpin-Tsai com dados experimentais
- Artigo para periódico indexado (Journal of Cleaner Production ou Renewable Energy)
- Relatório FINEP completo

#### WP7 — Disseminação (M18–M24, R\$ 47.200)

- Cartilha técnica para comunidades (linguagem acessível)
- Oficina de capacitação para multiplicadores
- Vídeo documentário do projeto (10 min)
- Dados abertos: repositório GitHub com CAD, firmware, schematics

---

## 6. ORÇAMENTO

### 6.1 Resumo Financeiro

| Rubrica | Valor (R\$) | % |
|---------|------------|---|
| 1. Recursos Humanos (bolsas) | 360.000 | 42,5 |
| 2. Material de Consumo | 164.000 | 19,4 |
| 3. Equipamentos Permanentes | 148.000 | 17,5 |
| 4. Serviços de Terceiros | 95.200 | 11,2 |
| 5. Passagens e Diárias | 68.000 | 8,0 |
| 6. Disseminação | 12.000 | 1,4 |
| **Total** | **847.200** | **100** |

### 6.2 RH — Bolsas (R\$ 360.000)

| Função | Dedicação | Meses | Valor/mês | Total |
|--------|-----------|-------|-----------|-------|
| Coordenador (Doutor) | 20 h/sem | 24 | R\$ 4.000 | R\$ 96.000 |
| Eng. Materiais (Mestre) | 40 h/sem | 18 | R\$ 4.500 | R\$ 81.000 |
| Técnico Fabricação | 40 h/sem | 14 | R\$ 2.500 | R\$ 35.000 |
| Assistente de Campo | 40 h/sem | 12 | R\$ 2.000 | R\$ 24.000 |
| Bolsista IC (Graduação) | 20 h/sem | 20 | R\$ 1.200 | R\$ 24.000 |
| Bolsista AT | 40 h/sem | 24 | R\$ 3.500 | R\$ 84.000 |
| Jornalismo Científico | 20 h/sem | 8 | R\$ 2.000 | R\$ 16.000 |

### 6.3 Equipamentos Permanentes (R\$ 148.000)

| Item | Qtd. | Unit. | Total |
|------|------|-------|-------|
| Máquina universal de ensaios (5 kN) | 1 | R\$ 85.000 | R\$ 85.000 |
| Estufa de secação (200 L, 200 °C) | 1 | R\$ 8.000 | R\$ 8.000 |
| Microscópio digital USB (200×) | 1 | R\$ 2.500 | R\$ 2.500 |
| Multímetro digital de precisão | 2 | R\$ 1.800 | R\$ 3.600 |
| Torno mecânico bancada | 1 | R\$ 12.000 | R\$ 12.000 |
| Furadeira de bancada | 1 | R\$ 2.500 | R\$ 2.500 |
| Serra fita metais | 1 | R\$ 4.500 | R\$ 4.500 |
| Balança de precisão (0,01 g) | 1 | R\$ 3.200 | R\$ 3.200 |
| Notebook rugged | 2 | R\$ 8.000 | R\$ 16.000 |
| Osciloscópio portátil | 1 | R\$ 5.700 | R\$ 5.700 |
| Câmera fotográfica | 1 | R\$ 5.000 | R\$ 5.000 |

---

## 7. EQUIPE

| Nome | Função | Vínculo | CH |
|------|--------|---------|-----|
| C. Napoles | Coordenador | Bioeólica | 20 h |
| [a selecionar] | Eng. Materiais | Bolsa | 40 h |
| [a selecionar] | Técnico Fabricação | Bolsa | 40 h |
| [a selecionar] | Assistente de Campo | Bolsa | 40 h |
| [a selecionar] | Bolsista IC | Graduação | 20 h |
| [a selecionar] | Bolsista AT | Técnico | 40 h |
| [a selecionar] | Jornalismo Científico | Graduação | 20 h |

---

## 8. RESULTADOS ESPERADOS

| # | Entregável | Prazo |
|---|------------|-------|
| D1 | Relatório de caracterização do compósito PM-15G | M6 |
| D2 | Otimização do processo + parâmetros RSM | M8 |
| D3 | Projeto executivo (CAD + FEM + schematics) | M10 |
| D4 | 3 turbinas fabricadas e testadas | M14 |
| D5 | Relatório de instalação e comissionamento | M16 |
| D6 | Série temporal de 12 meses de operação | M21 |
| D7 | Artigo submetido a periódico indexado | M22 |
| D8 | Cartilha técnica + vídeo + dados abertos | M24 |

### Indicadores de Sucesso

| Indicador | Meta |
|-----------|------|
| Potência elétrica | ≥ 80 W a 8 m/s |
| Custo por turbina | ≤ R\$ 2.500 |
| Disponibilidade | ≥ 85% |
| Redução de CO₂ vs. diesel | ≥ 80% |
| Satisfação dos usuários | ≥ 70% |
| Vida útil das pás | ≥ 3 anos |

---

## 9. SUSTENTABILIDADE E IMPACTO SOCIOAMBIENTAL

**Impacto ambiental:** Cada turbina evita a queima de ~720 L de diesel/ano (2,0 t CO₂e evitadas/ano). Pás compostáveis ao fim da vida. LCA: 21,6 kg CO₂e/pá compósito vs. 110,5 kg CO₂e/pá fibra de vidro (redução de 80%).

**Impacto social:** Produção local de pás como microatividade econômica. Três comunidades (15–20 famílias cada) com eletricidade 24 h para iluminação, refrigeração e bombeamento.

---

## 10. RISCOS E MITIGAÇÃO

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| Propriedades abaixo do previsto | Média | Alto | DOE otimiza parâmetros; grafite pode aumentar para 20% vol. |
| Ventos abaixo da média | Baixa | Médio | Seleção com série histórica ≥ 3 anos (SONDA) |
| Falha estrutural em vento extremo | Baixa | Alto | FS 1,3 aceito por limitação inerente Savonius (stall) |
| Roubo/vandalismo | Média | Alto | Torres em área comunitária vigiada |

---

## 11. CRONOGRAMA FÍSICO-FINANCEIRO (R\$ mil)

| Mês | 1-3 | 4-6 | 7-9 | 10-12 | 13-15 | 16-18 | 19-21 | 22-24 |
|-----|-----|-----|------|-------|-------|-------|-------|-------|
| Desembolso | 80 | 124 | 180 | 172 | 140 | 55 | 46 | 32 |

---

## 12. CONTRAPARTIDA

| Item | Valor (R\$) |
|------|-------------|
| Infraestrutura de laboratório (24 meses) | 36.000 |
| Equipamentos existentes | 28.000 |
| Horas equipe administrativa | 24.000 |
| Veículo para campo | 18.000 |
| **Total** | **106.000** |

---

## 13. REFERÊNCIAS

1. IEC 61400-2. Wind turbines — Part 2: Small wind turbines. IEC, 2013.
2. Akwa, J.V. et al. A review on the performance of Savonius wind turbines. *RSER*, v. 16, p. 3054–3064, 2012.
3. Halpin, J.C., Kardos, J.L. The Halpin-Tsai equations. *Polymer Eng. Sci.*, v. 16, p. 344–352, 1976.
4. Chung, D.D.L. *Functional Properties of Carbon Materials*. Elsevier, 2023.
5. Liu, Y. et al. LCA of wind turbine blade materials. *RSER*, v. 166, 112652, 2022.
6. Owen, A. et al. Small wind turbines for rural electrification. *RSER*, v. 104, p. 223–241, 2019.
7. Callister, W.D., Rethwisch, D.G. *Materials Science and Engineering*. 10th ed. Wiley, 2018.

---

## ANEXO I — CHECKLIST PARA SUBMISSÃO

- [ ] Currículo Lattes do coordenador
- [ ] Declaração de anuência institucional
- [ ] Comprovante de submissão ao CEP (Res. CNS 466/12)
- [ ] Cartas de anuência de 2 associações comunitárias
- [ ] Memorial de cálculo estrutural (FEM)
- [ ] 3 cotações dos equipamentos principais
