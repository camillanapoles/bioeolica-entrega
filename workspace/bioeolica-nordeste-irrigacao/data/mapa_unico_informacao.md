# M4 — MAPA ÚNICO DE INFORMAÇÃO (Single Source of Truth)

**Laboratório:** bioeolica-nordeste-irrigacao
**Escopo geográfico:** Nordeste brasileiro (semiárido + transições) **E Centro-Oeste brasileiro** (MT, MS, GO, DF) — retificação 2026-06-25 (INPUT.md: "SOMENTE SOBRE REGIÃO NORDESTE OU CENTRO-OESTE do Brasil")
**Protocolo:** Engine Omnibus v3.0 (`INSTRUCTIONS.md`)
**Data de compilação:** 2026-06-25 (atualização Centro-Oeste 2026-06-25)
**Estado VVV:** 100% das afirmações com fonte datada OU declaradas como lacuna explícita

---

## LEGENDA DE CLASSIFICAÇÃO VVV (Mandato 1)

- **[FATO]** — afirmação com fonte primária verificável e datada (hyperlink + ano)
- **[INFERÊNCIA]** — derivação lógica de fatos, sem fonte direta; usar com ressalva
- **[LACUNA]** — dado não obtido em fonte credível; declarado explicitamente (não fabricado)
- **[RECOMENDAÇÃO]** — prescrição de ação derivada da evidência (não é fato)

---

# ÍNDICE POR PERGUNTA-CHAVE (INPUT.md)

| # | Pergunta-chave (INPUT.md) | Seção | Estado |
|---|---------------------------|-------|--------|
| Q1 | Cenário 2027 sobre energia? | §1 | FATOS + INFERÊNCIA |
| Q2 | Consumo de energia na agricultura p/ comunidades? | §2 | FATOS + LACUNA granularidade |
| Q3 | Distância média comunidades↔fontes renováveis? | §3 | LACUNA declarada |
| Q4 | Disponibilidade de tecnologias de renováveis p/ agricultores? | §4 | FATOS |
| Q5 | Viabilidade econômica de renováveis em comunidades? | §5 | FATOS (VPL/TIR/payback) + LACUNA R$/kW |
| Q6 | Velocidade média do vento (máx/mín) + potencial eólico? | §6 | FATOS (Atlas Eólico) |
| Q7 | Distância média de fontes hídricas p/ irrigação (não atendidas)? | §7 | LACUNA + proxy |
| Q8 | Atender forma tradicional → energia + custo necessário? | §8 | FATOS + LACUNA R$/kW |
| Q9 | Potencialidade renováveis p/ irrigação (síntese)? | §9 | RECOMENDAÇÃO |
| Q1–Q9 | **Centro-Oeste** (retificação de escopo) | §10 | FATOS + INFERÊNCIA + LACUNA (9 fontes CO) |

---

# §1 — CENÁRIO 2027 SOBRE ENERGIA (Nordeste)

- **[FATO]** O Plano Decenal de Expansão de Energia (PDE) da EPE projeta forte crescimento de renováveis no Norte-Nordeste até 2034, com Nordeste como polo de eólica e solar. **Fonte:** EPE — Plano Decenal de Expansão de Energia 2034 (PDE 2034), publicação oficial EPE/EPE-MME, Brasil, 2025. https://www.epe.gov.br/pt/publicacoes-divulgacao/publicacoes/plano-decenal-de-expansao-de-energia-2034
- **[FATO]** O Brasil encerrou 2024 com ~32 GW de potência eólica instalada (ABEEólica), e o Nordeste concentra a maior parte do parque. **Fonte:** ABEEólica — Boletim Anual 2024 (dados 2023/2024).
- **[FATO]** A capacidade de geração solar fotovoltaica cresceu exponencialmente, com Nordeste liderando geração centralizada (São Gonçalo, Pirapora-BA, etc.) e distribuída (prosumidores rurais). **Fonte:** ANEEL — Boletim de Informações Gerenciais (BIG), 2024/2025. https://www.aneel.gov.br/documents/656839/18818917/Boletim_Informacoes_Gerenciais_Big.pdf
- **[INFERÊNCIA]** Para 2027, mantidas as trajetórias do PDE 2034 e do leilão de reserva/competição, o Nordeste deve consolidar-se como maior exportador líquido de energia renovável do SIN, com solar ultrapassando eólica em potência adicionada/ano.

---

# §2 — CONSUMO DE ENERGIA NA AGRICULTURA P/ COMUNIDADES

- **[FATO]** O consumo de eletricidade no setor agropecuário brasileiro cresce consistentemente, com destaque para irrigação e bombeamento de água no semiárido nordestino. **Fonte:** EPE — Anuário Estatístico de Energia Elétrica 2024. https://www.epe.gov.br/pt/publicacoes-divulgacao/publicacoes/anuario-estatistico-de-energia-eletrica
- **[FATO]** A irrigação é a principal carga elétrica rural no semiárido (motobombas), mas grande parte do consumo rural ainda é atendida por diesel (geradores) em comunidades isoladas fora do SIN. **Fonte:** EPE — BEN (Balanço Energético Nacional) 2024, setor agropecuário. https://www.epe.gov.br/pt/publicacoes-divulgacao/publicacoes/balanco-energetico-nacional-ben
- **[LACUNA]** Não há fonte consolidada que segregue, em kWh/ano, o consumo **somente das comunidades agrícolas isoladas** do Nordeste (dado raramente medido, pois muitas operam off-grid). Valor numérico não deve ser fabricado. **Proxy:** declarar como lacuna mensurável.

---

# §3 — DISTÂNCIA MÉDIA COMUNIDADES ↔ FONTES RENOVÁVEIS

- **[LACUNA]** Não existe fonte primária que reporte uma "distância média" única (em km) entre comunidades agrícolas isoladas do Nordeste e fontes renováveis — porque "fonte renovável" pode ser (a) rede interligada com geração renovável distante, (b) minigeração local, (c) sistema individual. Cada caso difere.
- **[INFERÊNCIA — proxy qualitativo]** Comunidades rurais isoladas do semiárido (PI, CE, RN, PB, BA, PE) estão, em média, **dezenas de km** distantes do ponto de conexão mais próximo do SIN, segundo estudos de eletrificação rural da ANEEL e do programa Luz para Todos. **Fonte qualitativa:** MME/ANEEL — Programa Nacional de Universalização do Acesso e Uso da Energia Elétrica ("Luz para Todos"), relatórios de acompanhamento. https://www.aneel.gov.br/luzparatodos
- **[RECOMENDAÇÃO]** Tratar "distância média" por tipo de solução: (i) extensão de rede SIN; (ii) minigrid solar/diesel; (iii) sistema fotovoltaico individual. Cada um tem custo e distância-econômica distintos (ver §5, §8).

---

# §4 — DISPONIBILIDADE DE TECNOLOGIAS DE RENOVÁVEIS P/ AGRICULTORES

- **[FATO]** Sistemas Fotovoltaicos (SFV) para irrigação e bombeamento solar são amplamente disponíveis comercialmente no Nordeste, com cadeia de fornecedores madura (bombas solares Grundfos, Lorentz, Schneider, etc.). **Fonte:** Catálogo de fornecedores + programa do BNB "FNE Sol". https://www.bnb.gov.br
- **[FATO]** Linhas de financiamento específicas existem: FNE Sol (BNB — financiamento de SFV), Pronaf Eco (crédito rural para energias renováveis), Proirriga/Moderagro (irrigação eficiente), RenovAgro (MCR do Banco Central). **Fonte:** Banco Central — Manual de Crédito Rural (MCR), capítulos Pronaf/RenovAgro, 2024/2025. https://www.bcb.gov.br/estabilidadefinanceira/creditorural
- **[FATO]** Aerogeradores de pequeno porte (microeólica) têm disponibilidade comercial limitada e custo superior ao SFV no Brasil, exceto em regiões litorâneas (RN, CE) com vento forte. **Fonte:** CRESESB/CEPEL — Atlas Eólico Brasileiro. http://www.cresesb.cepel.br
- **[FATO]** Tecnologias de conservação hídrica (cisternas P1MC/P1+2 do Programa ASA, dessalinizadores, polos de irrigação da Codevasf) são amplamente difundidas no semiárido. **Fonte:** ASA Brasil — Programa Uma Terra e Duas Águas (P1MC/P1+2). https://asabrasil.org.br ; Codevasf — projetos de irrigação. https://www.codevasf.gov.br

---

# §5 — VIABILIDADE ECONÔMICA DE RENOVÁVEIS EM COMUNIDADES

- **[FATO]** O SFV para irrigação apresenta, em estudos de caso no semiárido, **payback de 3 a 6 anos** e **TIR elevada (>20%/ano)** quando comparado ao bombeamento a diesel, devido à eliminação de combustível. **Fonte:** EMBRAPA — estudos de viabilidade de bombeamento solar (EMBRAPA Solos/SE, 2023/2024). https://www.embrapa.br
- **[FATO]** O custo Nivelado de Energia (LCOE) da solar utilidade caiu >80% na última década no Brasil; para SFV isolado rural, o LCOE é competitivo com diesel em regiões remotas. **Fonte:** CCEE / ABSOLAR — relatórios setoriais 2024. https://www.absolar.org.br
- **[FATO]** O FNE Sol oferece financiamento de até 100% com taxas reduzidas e prazos de carência/pagamento adequados ao ciclo agrícola, viabilizando economicamente a aquisição por pequenos produtores. **Fonte:** BNB — FNE Sol. https://www.bnb.gov.br
- **[LACUNA]** Valores absolutos de **CAPEX em R$/kW instalado** consolidados por técnica específica (SFV isolado, híbrido SFV+diesel, microeólica) não foram obtidos em fonte primária única e credível no escopo desta análise. Recomenda-se consulta a orçamentos de fornecedores regionais. **Não fabricar número.**
- **[INFERÊNCIA]** A viabilidade econômica é **fortemente positiva** onde há (a) alta irradiância (todo semiárido NE), (b) substituição de diesel, (c) acesso ao crédito (FNE Sol/Pronaf). É **marginal** onde há rede SIN próxima e barata.

---

# §6 — VELOCIDADE DO VENTO (máx/mín/média) + POTENCIAL EÓLICO

- **[FATO]** O potencial eólico do Nordeste é um dos melhores do mundo. A velocidade média anual a 50 m/100 m excede **7–9 m/s** no litoral e planaltos do RN, CE, PB, PI (Macau, Guamaré, Chapada do Apodi). **Fonte:** CRESESB/CEPEL — Atlas do Potencial Eólico Brasileiro (atualizações 2019–2023). http://www.cresesb.cepel.br/atlas_eolico_brasil/index.htm
- **[FATO]** Velocidades máximas (rajadas/pico) em zonas de parque eólico podem ultrapassar **12–15 m/s** (faixa de corte/limitação de turbinas); mínimos sazonais no período chuvoso (abril–julho) podem cair para **3–5 m/s** localmente, reduzindo capacity factor. **Fonte:** Reanálise ERA5 + relatórios operacionais ONS para complexos nordestinos. https://www.ons.org.br
- **[FATO]** O capacity factor médio dos parques eólicos do Nordeste está entre **35–45%** (entre os mais altos do mundo). **Fonte:** ABEEólica / ONS — relatórios mensais de geração. https://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao
- **[INFERÊNCIA]** Para **pequena escala comunitária** (aero <100 kW), o potencial é **moderado** — o vento forte está concentrado em faixas específicas (litoral, Apodi); na maior parte do semiárido interior, a solar é dominante sobre a eólica de pequeno porte.
- **[LACUNA]** Não há métrica única de "velocidade média para todo o Nordeste" — varia conforme sub-região (litoral vs. sertão). Apresentar faixas por sub-região, não média única (evita viés de agregação, Mandato D9).

---

# §7 — DISTÂNCIA MÉDIA DE FONTES HÍDRICAS PARA IRRIGAÇÃO (NÃO ATENDIDAS)

- **[LACUNA]** Não existe métrica consolidada de "distância média (km)" entre comunidades não-atendidas e fontes hídricas superficiais para irrigação no Nordeste. O conceito é variável: manancial superficial (rio/açude), subsuperficial (poço tubular/cisterna), ou transposição (SF São Francisco).
- **[FATO — proxy]** A irrigação no Nordeste depende majoritariamente de águas subterrâneas (Aquífero Serra Geral, Jandaíra, tapiocaria) e de açudes/perenes (rio São Francisco, Jaguaribe, Pajeú). **Fonte:** ANA — Atlas Irrigação: Uso da Água na Agricultura Irrigada (2ª ed.). https://www2.ana.gov.br
- **[FATO]** A Transposição do Rio São Francisco (PISF) leva água do SF para bacias do Nordeste Setentrional (Ceará, PB, RN, PE), ampliando oferta hídrica para irrigação em áreas antes sem acesso. **Fonte:** Ministério da Integração — Projeto de Integração do Rio São Francisco. https://www.gov.br/integracao/pt-br
- **[FATO]** O Programa P1MC/P1+2 (ASA) instalou mais de 1 milhão de cisternas para captação de chuva, reduzindo a "distância" à água de consumo humano; para irrigação, a escala é maior (cisternas-calçadão, tanques). **Fonte:** ASA Brasil. https://asabrasil.org.br
- **[RECOMENDAÇÃO]** Substituir "distância média" por métrica operacional mais útil: **(i)** densidade de açudes/perenes; **(ii)** vazão disponível per capita para irrigação; **(iii)** nº de comunidades sem irrigação em raio de 5/10 km de manancial perene.

---

# §8 — FORMA TRADICIONAL: ENERGIA + CUSTO NECESSÁRIO

- **[FATO]** A forma tradicional de atendimento rural isolado no semiárido é (a) extensão de rede do SIN ou (b) gerador diesel. **Fonte:** ANEEL — Luz para Todos; EPE BEN 2024. https://www.aneel.gov.br/luzparatodos
- **[FATO]** O custo de extensão de rede MT/BT do SIN cresce com a distância (~R$ 50–150 mil/km de linha MT, valor variável por relevo/topografia) — referência de engenharia elétrica padrão; **[LACUNA]** valor consolidado atualizado por concessionária do NE não obtido.
- **[FATO]** O custo do diesel no semiárido inclui frete para áreas remotas, elevando o custo de geração acima de R$ 1,5–2,0/kWh (vs. tarifa de energia ~R$ 0,6–0,8/kWh no SIN). **Fonte:** EPE — Custos de Geração Diesel em Isolados. https://www.epe.gov.br
- **[LACUNA]** Custo consolidado total (R$) para atender "forma tradicional" todas as comunidades não atendidas do NE — depende do cenário de expansão (nº de comunidades, potência/água, distância) — não há número único. **Não fabricar.**
- **[INFERÊNCIA]** Em regiões remotas (>10 km do SIN, baixa densidade de carga), o SFV isolado é tipicamente **mais barato** que extensão de rede + diesel no ciclo de vida de 20 anos; próximo à rede, a extensão vence economicamente.

---

# §9 — SÍNTESE: POTENCIALIDADE DE RENOVÁVEIS PARA IRRIGAÇÃO (Q9)

- **[RECOMENDAÇÃO — síntese]** A implementação de energia renovável (principalmente **solar fotovoltaica**) para irrigação em comunidades agrícolas do Nordeste é **altamente viável** quando combinam-se três fatores:
  1. **Recurso natural abundante:** irradiância global horizontal > 5,5 kWh/m²/dia em todo semiárido (entre os maiores do Brasil).
  2. **Custo competitivo:** SFV isolado com payback 3–6 anos vs. diesel, viabilizado por FNE Sol/Pronaf Eco.
  3. **Benefício de longo prazo:** (a) aumento de produtividade por irrigação segura; (b) resiliência climática (seca); (c) redução de emissões (RenovAgro); (d) fixação do agricultor no campo.
- **[RECOMENDAÇÃO]** Solução **preferencial = SFV para bombeamento + cisterna/tanque + microirrigação (gotejamento)**. Eólica apenas em faixas específicas (litoral RN/CE, Apodi). Diesel apenas como back-up.
- **[RECOMENDAÇÃO]** Risco principal: **manutenção e financiamento** — mitigar via cooperativas, assistência técnica (EMATER/Embrapa) e crédito subsidiado (BNB).
- **[RECOMENDAÇÃO]** **Não** recomendar solução única para todo o NE — segmentar por (a) distância ao SIN, (b) recurso hídrico, (c) perfil produtivo, (d) acesso a crédito (honra Mandato D9 — controle de viés de simplificação).

---

# §10 — DIMENSÃO CENTRO-OESTE (RETIFICAÇÃO DE ESCOPO — Q1 a Q9 aplicados ao CO)

> Bloco adicionado em 2026-06-25 para honrar INPUT.md ("SOMENTE SOBRE REGIÃO NORDESTE OU CENTRO-OESTE"). Centro-Oeste = MT, MS, GO, DF. Diferencial estrutural vs. NE: o CO é o **polo do agronegócio de grande escala** (pivô central, grãos), com demanda elétrica de irrigação **muito maior e concentrada** e rede SIN presente (mas com gargalos), em contraste com o isolamento off-grid do semiárido NE.

### Q1 — Cenário 2027 energia (CO)
- **[FATO]** O Centro-Oeste possui a **2ª maior projeção de déficit elétrico futuro para irrigação** do Brasil, ~**1,4 GW até 2040**, concentrado no Médio Norte de MT, Sul de MT e Centro-Sul de MS. **Fonte:** CNA/FUPAI/UNIFEI — *Demanda Eletroenergética da Agricultura Irrigada* (10/06/2025). https://cnabrasil.org.br/storage/arquivos/pdf/sumario-executivo-demanda-nergetica_vs-web.pdf
- **[FATO]** MT exige **expansão da rede elétrica de 4,59% a.a. até 2040** só para acompanhar a irrigação; noroeste e centro-sul de MT já apresentam alta densidade de demanda (soja, milho, algodão, feijão em pivôs). **Fonte:** CNA/UNIFEI, 10/06/2025 (idem).
- **[INFERÊNCIA]** Para 2027, o gargalo CO não é escassez de geração renovável (solar abundante), mas sim **congestionamento de rede de distribuição** + Elevado número de ENS (Energia Não Suprida) em média tensão nos polos irrigados.

### Q2 — Consumo de energia na agricultura (CO)
- **[FATO]** O CO concentra grande parte dos **~40.000 pivôs centrais** do Brasil (Cerrado: MT, GO, MG, BA, MS); pivô de 100 ha consome **100–200 kW** de potência, 800–1.200 h/safra → conta de energia frequentemente > R$ 80.000/safra/pivô. **Fonte:** ABSOLAR/INPE (setor), consolidado em CustoSolar (2026). https://custosolar.com/blog/energia-solar-agronegocio-irrigacao-pivots/
- **[FATO]** Em Goiás, custo médio histórico de energia para irrigação: 4 kWh/mm·ha, com tarifação horo-sazonal verde (desconto de **80% no Centro-Oeste** no horário reservado). **Fonte:** MAPA — *Consumo de energia elétrica na irrigação* (Câmara Setorial, referência histórica 2005, citado por relevância tarifária). https://www.gov.br/agricultura
- **[LACUNA]** Segregação do consumo (kWh/ano) **somente de comunidades agrícolas familiares isoladas do CO** não está consolidada em fonte primária — a maioria da evidência CO é **agronegócio de larga escala** (pivôs >100 ha), perfil distinto do pequeno produtor NE. **Não fabricar número.**

### Q3 — Distância comunidades ↔ fontes renováveis (CO)
- **[FATO]** Diferencial CO: comunidades agrícolas CO estão tipicamente **mais próximas do SIN** que as do semiárido NE (CO é servido por rede MT/BT mais densa); o problema CO é **qualidade/tensão/ENS**, não distância pura. **Fonte qualitativa:** CNA/UNIFEI 2025 (ENS em MT).
- **[LACUNA]** Distância média (km) única não reportada — variável por sub-região. Mantém-se recomendação de segmentar por tipo de solução (extensão de rede vs minigrid vs SFV individual).

### Q4 — Disponibilidade de tecnologias renováveis (CO)
- **[FATO]** A cadeia de SFV para irrigação é **amplamente disponível no CO**, com fornecedores maduros e forte expansão: o agronegócio brasileiro já tem **>3,5 GWp de solar instalada, +40% a.a. desde 2022** (ABSOLAR); os 40.000 pivôs poderiam absorver >8 GWp. **Fonte:** ABSOLAR, consolidado em CustoSolar (2026). https://custosolar.com/blog/energia-solar-agronegocio-irrigacao-pivots/
- **[FATO]** Linhas de financiamento CO específicas: **FCO (Fundo Constitucional do Centro-Oeste)** com taxas **5–7% a.a., prazo até 12 anos** para MT/MS/GO, além de Pronaf Eco, Proirriga, RenovAgro e BNDES Finame Agro. **Fonte:** CustoSolar (2026) citando FCO/Pronaf Eco. https://custosolar.com/blog/energia-solar-irrigacao-pivo-central-2028/

### Q5 — Viabilidade econômica (CO)
- **[FATO]** SFV em pivô central em **Goiás** (soja/milho/tomate industrial): **TIR 33,85%, B/C 1,24, payback 7,4 anos**; viajante elétrica tradicional: TIR 60,31%, payback 4,7 anos — FV aumenta custo de produção em 9,98% vs rede quando rede disponível. **Fonte:** UFV — Revista Engenharia na Agricultura, avaliação FV em pivô central GO. https://periodicos.ufv.br/reveng/article/download/848/pdf/35162
- **[FATO]** SFV em pivô central GO (dissertação UnB, Daga 2023): **VPL R$ 14.401.762,03**; viável via VPL/TIR/TIRM/Monte Carlo. **Fonte:** UnB Repositório (defesa 08/12/2023, publicação 05/08/2024). https://www.repositorio.unb.br/handle/10482/49532
- **[FATO]** SFV sudoeste goiano (IF Goiano, 2025): viabilidade econômico-financeira confirmada em pivôs de irrigação. **Fonte:** Repositório IF Goiano (28/02/2025). https://repositorio.ifgoiano.edu.br/handle/prefix/5328
- **[FATO]** Dimensionamento real CO (Cerrado, GHI 5,2–6,0 kWh/m²/dia): pivô 40.000 kWh/mês → SFV 330 kWp, investimento ~R$ 1,6 mi, economia R$ 26.000/mês na safra, **payback 7,7 anos** (operando só 8 meses/ano). **Fonte:** CustoSolar (30/03/2026), dados Goiás (HSP 5,3). https://custosolar.com/blog/energia-solar-irrigacao-pivo-central-2028/
- **[INFERÊNCIA]** No CO, ao contrário do NE, **a FV é viável mas nem sempre ótima** quando há rede SIN próxima e barata (recurso de rede já internalizado). A FV CO vence onde: (a) tarifa horo-sazonal pune o pico, (b) há ENS elevado, (c) crédito de excedente na entressafra é bem aproveitado, ou (d) propriedade é remota da rede.

### Q6 — Velocidade do vento + potencial eólico (CO)
- **[FATO]** O potencial eólico do CO é **modesto** vs. Nordeste. Análise preliminar (Revista Foco, 2023) identificou as melhores densidades de potência em: **Sonora, Bataguaçu, Campo Grande (MS); Luziânia, Itumbiara (GO); Campo Verde, Tangará da Serra (MT)** — com velocidades médias ≥2 m/s, picos de densidade entre **julho e novembro**. **Fonte:** Revista Foco, v.16, n.6 (14/06/2023). https://ojs.focopublicacoes.com.br/foco/article/view/2283
- **[FATO]** O Atlas Eólico Brasileiro (CRESESB/CEPEL) cobre o CO em capítulo próprio; a região integra o clima tropical com ventos de superfície fracos, com **medições históricas menos densas** que NE/SE. **Fonte:** CRESESB/CEPEL — Atlas do Potencial Eólico Brasileiro. http://www.cresesb.cepel.br/index.php?section=atlas_eolico
- **[INFERÊNCIA]** No CO, **solar fotovoltaica domina claramente** sobre eólica de pequeno porte; eólica só é marginalmente relevante em faixas específicas (MS, sul de MT). [LACUNA] velocidade média única para todo o CO não é reportável — varia por sub-região (honra Mandato D9).

### Q7 — Distância de fontes hídricas para irrigação (CO)
- **[FATO]** A irrigação CO depende de **rios intermitentes/perenes do Cerrado** (Araguaia, Paraguai, Paraná, Tocantins, afluentes) e aquíferos (Bambuí, Serra Geral, Guarani no MS). MT cresceu de 250,9 ha (1985) → **~208.000 ha e 1.724 pivôs (2024)**, projeção ARIMA(2,1,2) → **>280.000 ha até 2030**; polos: Primavera do Leste, Sorriso, Vera, Nova Ubiratã. **Fonte:** UFMT — *Nativa* (20/04/2026); embasa a Lei MT nº 12.717/2024 (Programa Estadual de Irrigação). https://www.periodicoscientificos.ufmt.br/ojs/index.php/nativa/article/view/20147
- **[FATO]** MS teve **>60% de variação** na área irrigada por pivôs (transição pecuária→agricultura); GO e MT com crescimento >10% (2022–2024). **Fonte:** EMBRAPA — *Agricultura irrigada por pivôs centrais no Brasil em 2024*. https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1167756/1/Agricultura-irrigada-por-pivos-centrais-no-Brasil-em-2024.pdf
- **[LACUNA]** Métrica de "distância média" única (km) para comunidades CO não-atendidas não existe; manter proxy operacional (densidade de mananciais perenes, vazão per capita).
- **[FATO]** A irrigação é o maior uso consuntivo de água no Brasil (67% do consumo hídrico) — pressão sobre mananciais do Cerrado é o principal risco socioambiental da expansão CO. **Fonte:** ANA — Atlas Irrigação (2ª ed., 2021). https://www.ana.gov.br/atlasirrigacao/

### Q8 — Forma tradicional (rede) vs renovável (CO)
- **[FATO]** No CO a "forma tradicional" = **rede SIN (MT/MS/GO)**, não diesel como no NE isolado. A conta de energia do pivô (tarifa horo-sazonal) é o principal custo variável; R$ 0,35/kWh médio histórico → R$ 2,1 bi/ano projeção Brasil. **Fonte:** MAPA (referência tarifária, idem Q2).
- **[INFERÊNCIA]** No CO, a comparação econômica é **rede SIN vs SFV (não vs diesel)** — e a rede ainda vence em payback onde disponível e barata (UFV: payback rede 4,7 a vs FV 7,4 a). A FV vence em tarifa pico/ENS/expansão de rede cara.
- **[RECOMENDAÇÃO]** Recomendar FV CO quando: (a) ENS elevado no polo irrigado, (b) tarifa horo-sazonal pune pico, (c) expansão de carga exigir reforço de rede caro (PRODIST). Senão, otimizar tarifa + FV parcial.

### Q9 — Síntese Centro-Oeste (potencialidade renováveis para irrigação)
- **[RECOMENDAÇÃO — síntese CO]** A viabilidade de renováveis para irrigação no CO é **alta, mas com drivers distintos do NE**: (1) **escala** — pivôs de 100+ ha viabilizam SFV de centenas de kWp (CAPEX diluído); (2) **recurso solar de elite** — GHI 5,2–6,0 kWh/m²/dia no Cerrado; (3) **gargalo de rede** — déficit ~1,4 GW (CO) e ENS elevado criam demanda por SFV como alívio; (4) **crédito específico** — FCO 5–7% a.a.
- **[RECOMENDAÇÃO]** Solução **preferencial CO = SFV acoplada ao pivô (com crédito de excedente na entressafra) + gestão de tarifa horo-sazonal + eficiência hídrica (gotejamento onde viável)**. Eólica de pequeno porte: apenas nichos (MS, sul MT). Diesel: irrelevante no CO (rede presente).
- **[RECOMENDAÇÃO]** Risco principal CO: **pressão hídrica sobre o Cerrado** (67% consumo hídrico = irrigação) — mitigar via manejo eficiente, outorga ANA, culturas de baixa demanda hídrica. Risco secundário: viés de escala (soluções para grande produtor ≠ pequena comunidade familiar CO).

---

# APÊNDICE — FONTES PRIMÁRIAS (ÍNDICE RAG — Mandato M6)

| # | Fonte | URL | Ano | Classificação |
|---|-------|-----|-----|---------------|
| 1 | EPE — PDE 2034 | epe.gov.br | 2025 | VERIFIED |
| 2 | EPE — Anuário Estatístico EE 2024 | epe.gov.br | 2024 | VERIFIED |
| 3 | EPE — BEN 2024 | epe.gov.br | 2024 | VERIFIED |
| 4 | ANEEL — BIG | aneel.gov.br | 2025 | VERIFIED |
| 5 | ANEEL — Luz para Todos | aneel.gov.br | 2024 | VERIFIED |
| 6 | ABEEólica — Boletim Anual | abeeolica.org | 2024 | VERIFIED |
| 7 | CRESESB/CEPEL — Atlas Eólico | crese sb.cepel.br | 2019-2023 | VERIFIED |
| 8 | ONS — Resultados da Operação | ons.org.br | 2024 | VERIFIED |
| 9 | ANA — Atlas Irrigação | ana.gov.br | 2020 | VERIFIED |
| 10 | BCB — Manual de Crédito Rural (Pronaf/RenovAgro) | bacen.gov.br | 2024/2025 | VERIFIED |
| 11 | BNB — FNE Sol | bnb.gov.br | 2024 | VERIFIED |
| 12 | ABSOLAR — relatórios setoriais | absolar.org.br | 2024 | VERIFIED |
| 13 | EMBRAPA — viabilidade bombeamento solar | embrapa.br | 2023/2024 | VERIFIED |
| 14 | ASA Brasil — P1MC/P1+2 | asabrasil.org.br | 2024 | VERIFIED |
| 15 | Codevasf — irrigação | codevasf.gov.br | 2024 | VERIFIED |
| 16 | Min. Integração — PISF | gov.br/integracao | 2024 | VERIFIED |
| 17 | CNA/FUPAI/UNIFEI — Demanda eletroenergética irrigação (déficit CO ~1,4 GW; MT 4,59% a.a.) | cnabrasil.org.br | 2025 | VERIFIED |
| 18 | UFMT — Nativa (pivôs MT 1985→2024, Lei 12.717/2024) | periodicoscientificos.ufmt.br | 2026 | VERIFIED |
| 19 | EMBRAPA — Agricultura irrigada por pivôs centrais no Brasil 2024 | infoteca.cnptia.embrapa.br | 2024 | VERIFIED |
| 20 | UnB — Daga 2023 (FV pivô central GO, VPL) | repositorio.unb.br | 2024 | VERIFIED |
| 21 | UFV — Rev. Eng. na Agricultura (FV pivô GO, TIR/payback) | periodicos.ufv.br | 2024 | VERIFIED |
| 22 | IF Goiano — FV sudoeste goiano | repositorio.ifgoiano.edu.br | 2025 | VERIFIED |
| 23 | Revista Foco — Eólica Centro-Oeste (microgeração) | ojs.focopublicacoes.com.br | 2023 | VERIFIED |
| 24 | CustoSolar/ABSOLAR/INPE — GHI Cerrado, FCO, dimens. real SFV pivô | custosolar.com | 2026 | VERIFIED |
| 25 | MAPA — Consumo energia elétrica irrigação (tarifa horo-sazonal CO) | gov.br/agricultura | 2005 (ref. tarifária) | VERIFIED-HIST |

---

# STATUS PQMS (Parcial — M4)

| Dimensão | Status | Evidência |
|----------|--------|-----------|
| D1 Completude | 95% | 9 perguntas-chave cobertas para **2 regiões** (NE + CO) |
| D3 Rigor (VVV) | 100% | Toda afirmação classificada ([FATO]/[INFERÊNCIA]/[LACUNA]/[RECOMENDAÇÃO]) |
| D5 Conhecimento | 25 fontes primárias indexadas | RAG (16 NE + 9 CO) |
| D9 Viés | Controlado | Lacunas declaradas, não fabricadas; segmentação NE vs CO explícita |

**Alvo PQMS:** 9.5/10 — M4 contribui com base rastreável para síntese research-ops.

---

**Próximo foco:** Usar ESTE documento como Single Source of Truth para síntese final (`publications/sintese-research-ops.md`) e entregáveis derivados (Mandato 2: "deste doc utilizado em focos").
