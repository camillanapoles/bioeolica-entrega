# Síntese — Energia Renovável para Irrigação no Nordeste e Centro-Oeste

> **Laboratório:** `bioeolica-nordeste-irrigacao`
> **Protocolo:** Engine Omnibus v3.0 (`mech-electro-materials-scientist`)
> **Fonte única (SSOT):** [`../data/mapa_unico_informacao.md`](../data/mapa_unico_informacao.md) (M4 — Mandato 2)
> **Data (ISO 8601):** 2026-06-25 (retificação Centro-Oeste 2026-06-25)
> **PQMS-alvo:** 9,5/10
> **Idioma:** Pt-br
> **Escopo:** **Nordeste brasileiro E Centro-Oeste brasileiro** (MT, MS, GO, DF) — conforme INPUT.md: "SOMENTE SOBRE REGIÃO NORDESTE OU CENTRO-OESTE do Brasil"

---

## WAL 5W1H (M5)

| W/H | Conteúdo |
|-----|----------|
| **What** | Síntese research-ops das 9 perguntas (Q1–Q9) sobre energia renovável para irrigação no **Nordeste E Centro-Oeste** brasileiros |
| **Why** | Atender Mandato 9 (Comunicação CRSLR) consumindo o M4 como Single Source of Truth |
| **Who** | Agente `mech-electro-materials-scientist` (Engine v3.0) |
| **When** | 2026-06-25 |
| **Where** | `publications/sintese-research-ops.md` ← consome `data/mapa_unico_informacao.md` |
| **How** | Formato research-ops (QUESTION TYPE / EVIDENCE / INFERENCE / RECOMMENDATION) + M³ + M8 + M9 |

**Legenda VVV:** `[FATO]` = fonte verificada datada · `[INFERÊNCIA]` = derivada racionalmente · `[LACUNA]` = sem fonte, declarada · `[RECOMENDAÇÃO]` = ação proposta.

---

## M³ — Cenário (Macro / Meso / Micro)

- **MACRO (ambiente externo):** Semiárido nordestino (~1,1 milhão de km²; ~28 milhões de pessoas) **+ Cerrado do Centro-Oeste** (MT/MS/GO, polo do agronegócio de grãos em larga escala, ~40.000 pivôs centrais); matriz elétrica nacional predominantemente renovável (~87%, EPE); programas federais Luz para Todos, FNE Sol, RenovAgro, PISF, **FCO (Fundo Constitucional do Centro-Oeste)**, Lei MT 12.717/2024.
- **MESO (interfaces):** Comunidades rurais ↔ fontes renováveis (SFV, eólico, diesel); irrigação ↔ recursos hídricos (cisternas, açudes, poços, PISF, rios do Cerrado); crédito (FNE Sol, Pronaf Eco, Moderagro, FCO, Proirriga) ↔ agricultor; assistência técnica (Embrapa/ASA/Codevasf/Emater).
- **MICRO (componentes):** Bomba solar submersa, painel SFV, cisterna de placas, gotejamento, gerador diesel (back-up), bateria/bombeamento direto. No CO: SFV utility-scale acoplada a pivô central (centenas de kWp) + inversores string + crédito de excedente na entressafra.

---

## Q1 — Cenário 2027: energia

**QUESTION TYPE:** Prospectivo / regulatório.

**EVIDENCE (consome M4 §1):**
- `[FATO]` PDE 2034 (EPE, 2024) projeta expansão de renováveis; meta de universalização energética mantida pelo MME. Luz para Todos já atendeu milhões, mas comunidades rurais isoladas ainda dependem de solução descentralizada.
- `[FATO]` Leilões de energia de reserva e contratações de SFV (ANEEL) crescem; Resolução Normativa 1.000/2021 simplifica acesso de mini/microgeração.

**INFERENCE:** Em 2027, o Nordeste consolida liderança em eólico + solar, porém o "último quilômetro" rural isolado seguirá exigindo **geração distribuída (SFV + bombeamento solar)** — a rede não chega de forma economicamente viável a todas as comunidades.

**RECOMMENDATION:** Priorizar SFV de pequeno porte (0,5–5 kWp) com bombeamento direto (sem bateria) para irrigação; manter back-up diesel/diesel-híbrido apenas onde há risco S1 (perda de safra/segurança alimentar).

---

## Q2 — Consumo de energia na agricultura para comunidades

**QUESTION TYPE:** Quantitativo / setorial.

**EVIDENCE (consome M4 §2):**
- `[FATO]` BEN (EPE, 2024): agropecuária consome parcela pequena do total (~2–3% da matriz), porém localmente o bombeamento para irrigação é o vetor dominante.
- `[LACUNA]` Não há número único publicado de kWh/ano por comunidade isolada — varia por área irrigada, método (gotejamento x aspersão), profundidade do poço e cabeçalho (altura manométrica).

**INFERENCE:** O consumo é fortemente correlacionado à altura manométrica e à área irrigada. SFV dimensionado para 1–3 ha em gotejamento tipicamente demanda 1–3 kWp por ha (ordem de grandeza, problem-dependent).

**RECOMMENDATION:** Adotar dimensionamento por caso via software open source (PVsyst trial / System Advisor Model — SAM do NREL) calibrado com dados locais de irradiância (Atlas solarimétrico do NE) e profundidade do poço.

---

## Q3 — Distância média comunidades ↔ fontes renováveis

**QUESTION TYPE:** Geoespacial / infraestrutura.

**EVIDENCE (consome M4 §3):**
- `[FATO]` Luz para Todos e programas estaduais de eletrificação rural reduzem o déficit, mas o semiárido ainda possui comunidades a dezenas de km da rede.
- `[LACUNA]` Não há distância média única publicada; depende do estado (CE, RN, PB, PE, BA, PI, etc.) e do tipo de comunidade (quilombola, indígena, assentamento).

**INFERENCE:** Acima de ~5–10 km da rede, o SFV descentralizado geralmente supera economicamente a extensão de linha (custos de posteação, manutenção, perdas técnicas).

**RECOMMENDATION:** Adotar regra de decisão: se distância à rede > ~8 km e demanda < ~50 kWh/dia → SFV isolado; caso contrário, avaliar extensão de rede ou sistema híbrido.

---

## Q4 — Disponibilidade de tecnologias renováveis

**QUESTION TYPE:** Oferta / maturidade tecnológica.

**EVIDENCE (consome M4 §4):**
- `[FATO]` ABSOLAR: mercado brasileiro de SFV crescente; cadeia de fornecedores madura (bombas solares submersas, controladores MPPT, gotejamento).
- `[FATO]` ABEEólica: eólico utility-scale maduro no litoral NE e no complexo Chapada do Apodi (RN/CE); eólico de pequeno porte é menos difundido.

**INFERENCE:** A **disponibilidade tecnológica para SFV+bombeamento é alta e madura** no NE; eólico é maduro apenas em escala utility (parques) ou em sítios específicos de bom vento (litoral, Apodi).

**RECOMMENDATION:** SFV é a tecnologia padrão; eólico de pequeno porte apenas onde o Atlas CRESESB indicar velocidade média anual > ~6 m/s a 50 m (litoral, planaltos elevados).

---

## Q5 — Viabilidade econômica (renováveis em comunidades agrícolas)

**QUESTION TYPE:** Econômico / LCOE / VPL.

**EVIDENCE (consome M4 §5):**
- `[FATO]` LCOE solar fotovoltaica no Brasil é competitivo (entre as menores do mundo segundo IRENA/BNEF); SFV residencial e comercial tem payback cada vez menor.
- `[FATO]` BNB FNE Sol: linha de crédito para SFV e sistemas híbridos no Nordeste semiárido; Pronaf Eco e Moderagro financiam irrigação e energias renováveis.
- `[LACUNA]` CAPEX exato R$/kWW instalado varia por fornecedor e escala; não há número único confiável sem cotação.

**INFERENCE:** SFV+bombeamento é viável quando combinado com (a) crédito subsidiado (FNE Sol), (b) ATER (assistência técnica) e (c) infraestrutura hídrica pré-existente (cisterna/poço). Payback tipicamente **3–6 anos** (ordem de grandeza, depende de tarifa evitada/diesel evitado e produção incrementada).

**RECOMMENDATION:** Estruturar projeto como trio "tecnologia + crédito + ATER"; dimensionar para maximizar Fator de Capacidade solar (~18–22% NE) e usar diesel apenas como back-up.

---

## Q6 — Velocidade do vento (máx/mín) + potencial eólico

**QUESTION TYPE:** Recurso natural / Atlas eólico.

**EVIDENCE (consome M4 §6):**
- `[FATO]` CRESESB/CEPEL Atlas Eólico: Nordeste tem os melhores ventos do Brasil. Litoral do CE/RN/RP e Chapada do Apodi com médias anuais elevadas a 50–100 m (classe de vento favorável a utility-scale, capacity factor > 40% em bons sítios).
- `[FATO]` Ventos máximos: ocorrem em litoral e planaltos; mínimos em vales e baixadas interioranas.
- `[LACUNA]` Não existe velocidade média única — varia drasticamente por micro-região, altitude e rugosidade do terreno; requer consulta ao Atlas por coordenada.

**INFERENCE:** Eólico de grande escala é altamente viável em faixas específicas (litoral, Apodi); para **pequeno porte/comunidades isoladas**, eólico é **complementar**, não primário — SFV domina pela previsibilidade e maturidade de pequena escala.

**RECOMMENDATION:** Consultar Atlas CRESESB por coordenada; se média anual a 50 m > ~6 m/s → considerar eólico híbrido (eólico+SFV+diesel); senão, SFV puro.

---

## Q7 — Distância hídrica (comunidades não atendidas)

**QUESTION TYPE:** Recurso hídrico / infraestrutura.

**EVIDENCE (consome M4 §7):**
- `[FATO]` ASA Brasil (P1MC — Programa Um Milhão de Cisternas; P1+2 — Segunda Água) constrói cisternas de placas para consumo e produção.
- `[FATO]` Codevasf e Ministério da Integração (PISF — transposição do São Francisco) ampliam oferta hídrica no semiárido.
- `[LACUNA]` Distância média hídrica exata (km) por comunidade não é consolidada em fonte única.

**INFERENCE:** A solução para "distância hídrica" é híbrida: **cisternas (captação in situ) + poços + adução (PISF/Codevasf) + irrigação localizada**. Energia renovável entra para bombear e distribuir — não para criar a fonte.

**RECOMMENDATION:** Combinar ASA (cisternas) + Codevasf/PISF (a dução) + SFV (bombeamento) + gotejamento (eficiência hídrica).

---

## Q8 — Forma tradicional de energia + custo necessário

**QUESTION TYPE:** Comparativo / diesel-referência.

**EVIDENCE (consome M4 §8):**
- `[FATO]` Forma tradicional predominante em comunidades isoladas sem rede: **gerador diesel**.
- `[LACUNA]` Custo total (CAPEX diesel + OPEX combustível) por kWh útil não é único; depende do logística do óleo diesel (distância a postos), horas de operação e potência do grupo gerador.

**INFERENCE:** Diesel tem CAPEX baixo mas OPEX alto e crescente (combustível + frete para zonas remotas); SFV inverte o perfil (CAPEX maior, OPEX baixo). Em horizonte > 5 anos, SFV geralmente supera diesel em VPL.

**RECOMMENDATION:** Substituir gerador diesel por SFV+bombeamento; manter diesel apenas como back-up S1 (falha → perda de safra).

---

## Q9 — Síntese: potencialidade de renováveis para irrigação

**QUESTION TYPE:** Síntese holística / M9 CRSLR.

**EVIDENCE (consome M4 §9):**
- `[FATO]` Recurso solar abundante no NE (irradiância entre as maiores do Brasil).
- `[FATO]` Recurso eólico de classe mundial em faixas específicas (litoral, Apodi).
- `[FATO]` Crédito (FNE Sol, Pronaf Eco, Moderagro) + ATER (Embrapa) + infra hídrica (ASA, Codevasf, PISF) disponíveis.
- `[FATO]` Tecnologias maduras e fornecedores nacionais (ABSOLAR/ABEEólica).

**INFERENCE (síntese):** A combinação **SFV + bombeamento + cisterna + gotejamento** é a solução preferencial para irrigação no semiárido nordestino; eólico complementa em sítios de bom vento; diesel permanece como back-up S1. A barreira não é tecnológica nem de recurso — é de **crédito acessível + ATER + infraestrutura hídrica prévia**.

**RECOMMENDATION (M9):**
1. **Padrão SFV** (0,5–5 kWp) + bomba solar submersa + gotejamento para 1–3 ha.
2. **Crédito** via FNE Sol/Pronaf Eco/Moderagro (BNB).
3. **ATER** via Embrapa/ASA/Codevasf.
4. **Infra hídrica** via cisternas (ASA) + adução (PISF/Codevasf).
5. **Back-up S1** diesel/híbrido apenas onde perda de safra = risco de vida/segurança alimentar.
6. **Eólico** (híbrido) apenas onde Atlas CRESESB > ~6 m/s a 50 m.

---

## Centro-Oeste — Aplicação das Q1–Q9 (retificação de escopo, consome M4 §10)

> O Centro-Oeste compartilha as 9 perguntas, mas com **drivers estruturais distintos** do NE: agronegócio de larga escala (pivôs 100+ ha), rede SIN presente (gargalo = ENS/tensão, não distância), e vento modesto (solar domina).

**QUESTION TYPE:** Síntese regional comparativa.

**EVIDENCE (consome M4 §10):**
- `[FATO]` CO tem a **2ª maior projeção de déficit elétrico para irrigação do Brasil (~1,4 GW até 2040)**; MT exige expansão de rede de 4,59% a.a. até 2040 (CNA/UNIFEI, 10/06/2025).
- `[FATO]` MT saltou de 250,9 ha (1985) → **208.000 ha / 1.724 pivôs (2024)**, projeção >280.000 ha até 2030 (UFMT/Nativa; Lei MT 12.717/2024). MS >60% de variação (pecuária→agricultura); GO e MT >10% a.a. (EMBRAPA 2024).
- `[FATO]` SFV em pivô central GO: **TIR 33,85%, B/C 1,24, payback 7,4 anos** (UFV); VPL R$ 14,4 mi (UnB/Daga 2023); viabilidade confirmada no sudoeste goiano (IF Goiano 2025).
- `[FATO]` Cerrado: GHI **5,2–6,0 kWh/m²/dia** (Sorriso MT, Rio Verde GO, Dourados MS, Barreiras BA); dimensão real: pivô 40.000 kWh/mês → SFV 330 kWp, ~R$ 1,6 mi, payback 7,7 anos, FCO 5–7% a.a. até 12 anos.
- `[FATO]` Eólica CO é modesta; melhores densidades em Sonora/Bataguaçu/Campo Grande (MS), Luziânia/Itumbiara (GO), Campo Verde/Tangará da Serra (MT), pico jul–nov (Revista Foco 2023).
- `[LACUNA]` Consumo (kWh/ano) **somente de comunidades familiares isoladas do CO** não consolidado — evidência CO é majoritariamente grande escala.

**INFERENCE:** No CO, ao contrário do NE, **a FV é viável mas nem sempre ótima** quando há rede SIN próxima e barata (UFV: payback rede 4,7 a < FV 7,4 a). A FV CO vence onde: (a) tarifa horo-sazonal pune o pico, (b) ENS elevado nos polos irrigados, (c) expansão de carga exige reforço de rede caro (PRODIST), (d) propriedade remota, ou (e) crédito de excedente na entressafra é bem aproveitado. Diesel é irrelevante no CO (rede presente). Eólica de pequeno porte é nicho (MS/sul MT).

**RECOMMENDATION (CO):**
1. **SFV acoplada ao pivô central** (centenas de kWp) + gestão ativa de tarifa horo-sazonal + crédito de excedente na entressafra.
2. **FCO + Pronaf Eco + Proirriga** como crédito preferencial (5–7% a.a.).
3. **Eficiência hídrica** (gotejamento onde viável) — irrigação = 67% do consumo hídrico nacional (ANA), principal risco socioambiental do Cerrado.
4. **Eólica** apenas em nichos identificados (MS, sul MT).
5. **Segmentar** perfil produtivo: soluções de grande escala (agronegócio) ≠ soluções para pequena comunidade familiar CO (honra Mandato D9).

---

## M8 — Segurança e Ética

- **S1 (segurança crítica):** Falha energética na irrigação = perda de safra = risco de vida e segurança alimentar. Mitigação: redundância (SFV + diesel back-up + cisterna de reserva).
- **S2 (segurança relevante):** Acesso do pequeno produtor ao crédito e tecnologia — ética: evitar endividamento predatório; condicionar crédito a ATER.
- **DEC (Declaração ética de conformidade):** Recomendações respeitam acesso equitativo, transparência de limitações (lacunas declaradas) e conformidade com programas públicos vigentes.

---

## M9 — Comunicação CRSLR

- **Contexto:** Nordeste (semiárido, comunidades isoladas) **E Centro-Oeste** (Cerrado, agronegócio de larga escala + comunidades familiares), 9 perguntas sobre energia renovável para irrigação.
- **Resultados:** Q1–Q9 respondidos para **ambas as regiões**; SFV é padrão em ambas; eólico complementa em faixas específicas (NE litoral/Apodi; CO apenas nichos MS/sul MT); diesel back-up S1 (NE) / irrelevante (CO onde há rede).
- **Síntese:** NE = SFV pequeno porte + bombeamento + cisterna + gotejamento + FNE Sol + ATER + ASA/Codevasf/PISF. CO = SFV acoplada a pivô central + gestão de tarifa + crédito excedente + FCO + eficiência hídrica.
- **Limitações:** Lacunas declaradas (kWh/ano em comunidades isoladas, km médio renovável/hídrico, CAPEX R$/kW, média vento única) — ausência de número único confiável sem cotação/levantamento de campo; segregação "comunidade familiar CO" não consolidada.
- **Recomendação:** Segmentar por região (NE vs CO) e por caso (área, poço, vento, distância à rede, escala); SFV como padrão; combinar tecnologia + crédito + ATER + infra hídrica.

---

## Status PQMS

| Dimensão | Estado |
|----------|--------|
| D1 Completude | 9 perguntas (100% relevantes) × **2 regiões (NE + CO)** |
| D2 Profundidade | M³ aplicado (macro/meso/micro) com distinção NE vs CO |
| D3 Rigor | VVV aplicado; lacunas declaradas onde sem fonte |
| D4 Rastreabilidade | WAL 5W1H + **25 fontes no M4** (16 NE + 9 CO) |
| D5 Conhecimento | 25 fontes primárias (EPE, ANEEL, ANA, ABEEólica, CRESESB, BNB, ASA, Codevasf + CNA/UNIFEI, UFMT, EMBRAPA, UnB, UFV, IF Goiano, Revista Foco, ABSOLAR) |
| D7 Qualidade numérica | Ordem de grandeza com lacunas declaradas (sem fabricar) |
| D9 Viés | Revisor hostil: lacunas declaradas; segmentação NE vs CO explícita |
| **PQMS parcial** | **Alvo 9,5 — retificação CO eleva D1/D5; lacunas declaradas preservam integridade** |

---

## Conclusão

A potencialidade de implementar sistemas de energia renovável para irrigação é **alta e tecnicamente madura em ambas as regiões**, com soluções diferenciadas por contexto. **No Nordeste** (semiárido, comunidades isoladas), a solução preferencial é **SFV de pequeno porte + bombeamento + cisterna + gotejamento** (payback 3–6 anos, ordem de grandeza), viabilizada por tecnologia madura (ABSOLAR), crédito subsidiado (FNE Sol/BNB), ATER (Embrapa/ASA/Codevasf) e infra hídrica (P1MC/P1+2, PISF/Codevasf); eólico complementa em faixas específicas (litoral, Chapada do Apodi); diesel como back-up S1. **No Centro-Oeste** (Cerrado, agronegócio de larga escala + comunidades familiares), a solução preferencial é **SFV acoplada ao pivô central (centenas de kWp) + gestão de tarifa horo-sazonal + crédito de excedente na entressafra + eficiência hídrica**, com TIR ~33,85% e payback ~7,4–7,7 anos (UFV/UnB/CustoSolar), viabilizada por FCO (5–7% a.a.) e Pronaf Eco/Proirriga — onde a rede SIN é próxima e barata, a FV complementa (não substitui) e o driver é o gargalo de rede (déficit ~1,4 GW, ENS elevado); eólica é nicho (MS, sul MT). As lacunas declaradas exigem levantamento de campo ou cotação para fechamento numérico definitivo — não foram fabricadas (Mandato VVV).
