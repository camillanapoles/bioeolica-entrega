# Laboratório: `bioeolica-nordeste-irrigacao`

> **STATE (FSM):** `bioeolica-nordeste-irrigacao`
> **KDI:** `mech-electro-materials-scientist` — Engine Omnibus v3.0 (Socrático Holístico)
> **Escopo:** **Nordeste brasileiro E Centro-Oeste brasileiro** (retificação 2026-06-25 — conforme INPUT.md: "SOMENTE SOBRE REGIÃO NORDESTE OU CENTRO-OESTE do Brasil")
> **Data (ISO 8601):** 2026-06-25
> **PQMS-alvo:** 9,5/10
> **Idioma:** Pt-br

---

## Instrução original (INPUT)

Doc de entrada do laboratório: [`./.memory/INPUT.md`](./.memory/INPUT.md)

Resumo da demanda: análise científica de **sustentabilidade agrícola no Nordeste E Centro-Oeste brasileiros**, com foco em irrigação eficiente, culturas resistentes à seca, manejo do solo, conservação da biodiversidade, políticas públicas, participação comunitária e mudanças climáticas. Nove perguntas-chave (Q1–Q9) sobre **energia renovável para irrigação** em comunidades agrícolas.

---

## Princípios de governança (Engine Omnibus v3.0)

- **Mandato 1 (VVV 100% prova):** toda afirmação com fonte verificável datada; não fabricar números; onde não houver fonte, **declarar lacuna**.
- **Mandato 2 (Mapa Único — SSOT):** TODA a evidência coletada está consolidada em **único documento categorizado** → [`data/mapa_unico_informacao.md`](./data/mapa_unico_informacao.md). Toda síntese/derivada CONSUME deste doc.
- **Mandato 5 (Log 5W1H):** rastreabilidade total de ações.
- **Mandato 8 (Segurança/Ética):** falha energética = risco de vida (S1); ética no acesso do pequeno produtor.
- **Mandato 9 (Comunicação CRSLR):** Contexto → Resultados → Síntese → Limitações → Recomendação.

---

## FSM de orquestração

```
STATE: bioeolica-nordeste-irrigacao
INIT  → INPUT.md lido e escopo confirmado (Nordeste E Centro-Oeste brasileiros) [retificação 2026-06-25]
M1    → Open Source First + fontes verificadas (EPE, ANEEL, ANA, ABEEólica, CRESESB, BNB, ASA, Codevasf, EMBRAPA, CNA/UNIFEI, UFMT, UnB, IF Goiano)
M4    → Mapa Único gravado (SSOT) ✓
M8    → Segurança/ética classificada (S1/S2) ✓
M9    → Comunicação CRSLR (síntese) ✓
```

---

## Estrutura de diretórios

```
bioeolica-nordeste-irrigacao/
├── README.md                          # este arquivo (entrypoint do lab)
├── .memory/INPUT.md                   # instrução original (movida para o lab)
├── data/
│   └── mapa_unico_informacao.md       # M4 — Single Source of Truth (Q1–Q9, 16 fontes)
├── context/                           # contexto adicional (5W1H, Ishikawa)
├── data/{knowledge,logs,vvv}/         # RAG, WAL, relatórios VVV
└── publications/
    └── sintese-research-ops.md        # síntese (consome M4) — formato research-ops
```

---

## Entregáveis

| Artefato | Status | Mandato |
|----------|--------|---------|
| `data/mapa_unico_informacao.md` (M4/SSOT) | ✅ GRAVADO | M2/M4 |
| `publications/sintese-research-ops.md` | ✅ ENTREGUE | M9 |
| `README.md` (este) | ✅ ENTREGUE | Governança CLAUDE.md |

---

## Fontes primárias (todas VERIFIED — ver M4 §RAG)

EPE PDE 2034 / Anuário Estatístico / BEN · ANEEL BIG / Luz para Todos · ABEEólica · CRESESB/CEPEL Atlas Eólico · ONS · ANA Atlas Irrigação · BCB Manual de Crédito Rural · BNB FNE Sol · ABSOLAR · EMBRAPA · ASA Brasil (P1MC/P1+2) · Codevasf · Ministério da Integração (PISF) · **Centro-Oeste:** CNA/UNIFEI/FUPAI (déficit energético MT/CO 2025) · UFMT Nativa (pivôs MT 2024/Lei 12.717/2024) · EMBRAPA (pivôs Brasil 2024) · UnB (FV pivô GO) · UFV Eng. Agrícola (FV GO) · IF Goiano (FV sudoeste GO 2025) · Revista Foco (eólica CO 2023) · ABSOLAR (GHI Cerrado / FCO).

---

## Classificação VVV (legenda)

`[FATO]` fonte verificada datada · `[INFERÊNCIA]` derivada racionalmente · `[LACUNA]` sem fonte, declarada · `[RECOMENDAÇÃO]` ação proposta.
