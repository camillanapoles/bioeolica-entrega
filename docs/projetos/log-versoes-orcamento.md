# LOG DE REGISTRO DE VERSÕES — Orçamento FINEP AgriFam-ICT 2026

> Registro canônico de versionamento do orçamento da proposta **Bioeólica (PM-15G + Savonius)** — Linha 2.
> Doc de orçamento: `docs/projetos/orcamento-versionado-finep-agrifam.md`.
> Proposta-mãe: `docs/projetos/finep-agrifam-bioeolica-linha2.md`.
> **Regra de leitura:** a versão vigente é sempre a de número mais alto marcada ✅ Corrente.

| Versão | Data | Valor | Status | Resumo do "o quê / por quê / quando" |
|---|---|---|---|---|
| **v2.0** | 2026-06-29 | **R$7.000.000,00** | ✅ **Corrente (retificada)** | **O quê:** retificação para o teto da faixa, incorporando 9 considerações do time Lab1+Lab2 não cobertas na v1.0.  + risco R4 (valor inabilitado >30% = eliminação); a v1.0 subdimensionava o ciclo completo de P&D. **Quando:** pré-submissão (proposta 03/07/2026 17h). |
| v1.0 | 2026-06-28 | R$4.500.000,00 | 🗄 Superseded | Primeira consolidação de 9 rubricas respeitando tetos, porém sem custo de iterações de ensaio, sem PI internacional, sem HPC, sem disseminação em congressos. |

---

## v2.0 (RETIFICADA) — detalhamento da mudança (diff vs v1.0)

### Rubricas — variação de valor (v1.0 → v2.0)

| Rubrica | v1.0 (R$) | v2.0 (R$) | Δ (R$) | Driver da mudança |
|---|---:|---:|---:|---|
| Pessoal | 1.200.000 | 1.800.000 | +600.000 | Quadro ampliado (Coord. + 2 Pesq. DT2 + 2 AT2) p/ cobrir Lab1+Lab2 por 36 m. |
| Bolsas | 1.050.000 | 1.600.000 | +550.000 | +pesquisadores (2 Dr + 3 M + 4 IC + DTI/EXP) — mão de obra sem encargos. |
| Serviços TP PJ | 510.000 | 850.000 | +340.000 | Ensaios iterativos (5 ciclos) + **PI internacional** (PCT+fases+procurador+anuidades) + HPC cloud + logística campo. |
| Material consumo | 450.000 | 750.000 | +300.000 | Insumos 5 ciclos (2.000 kg), ~1.500 corpos-de-prova, robustez 36 m. |
| Equip permanente | 450.000 | 750.000 | +300.000 | +**servidor HPC** + bancada PMG (ambos ≥R$50K) + casa vegetação. |
| Obras | 240.000 | 500.000 | +260.000 | 1→**2 ambientes** (Lab Materiais + Lab Eletromec) p/ encaixar 2 times. |
| Desp operac | 225.000 | 350.000 | +125.000 | =5% exato sobre R$7M (item 6.5.3). |
| Diárias | 225.000 | 200.000 | −25.000 | Logística campo realocada p/ TP PJ (sem teto); congressos internac. alocados. |
| Passagens | 150.000 | 200.000 | +50.000 | +viagens internac. (COP-31/32 e análogos). |
| **TOTAL** | **4.500.000** | **7.000.000** | **+2.500.000** | — |

### 9 considerações do time incorporadas (mandato do usuário)

1. **Custos durante 36 meses** — reservas de robustez por rubrica (reposição, inflação, quebras).
2. **Ensaios iterativos de P&D** — material novo exige ~5 ciclos formulação→ensaio→reformulação até o produto-alvo (especificações físicas 002–007). Cada ciclo re-executa D638/D790/D256/D7774/E139 + MEV/TGA/DSC/FTIR + END + envelhecimento.
3. **Infraestrutura/área para 2 times** — 2 ambientes: **Lab Materiais** (Lab1) e **Lab Eletromecânico** (Lab2: mecânicos + eletotécnicos), ≤R$392.952/ambiente.
4. **Robustez ao levantamento de custos** — valor inabilitado-alvo = 0%; cada item justificado com base normativa `[FONTE | item]`.
5. **PI nacional + INTERNACIONAL** — INPI + PCT + fases nacionais (US/EU/CN) + procurador + **anuidades/tempo de licença** (R$220.000 em TP PJ).
6. **Tempo de licença [valor]** — anuidades de manutenção durante 36 m contabilizadas (R$22.000).
7. **Computadores de alto rendimento** — servidor/workstation HPC (R$90.000, ≥R$50K) + cloud FEM/CFD sob demanda (R$45.000).
8. **Ciclo completo de desenvolvimento até PI internacional** — ensaios iterativos → PI BR → PCT → fases nacionais, todos custeados.
9. **Viagens a congressos (COP-31/32 e análogos)** — 2 deslocamentos internacionais (Passagens R$80K + Diárias R$80K); inscrições via TP PJ.
*(+ consideração: qtos profissionais pesquisadores — quadro ampliado em Pessoal+Bolsas, ver R1/R2.)*

### Conformidade preservada (revisão hostil)
- Pessoal 25,7% (≤30%) ✅ · Bolsas 22,9% (≤30%) ✅ · Operacional 5,0% (=5%) ✅ · Diárias 2,9% (≤5%) ✅ · Passagens 2,9% (≤5%) ✅ · Obras 7,1% e R$200K<R$392.952/amb (≤10%) ✅.
- Equip ≥R$50K livre; <R$50K só lista permitida; gerador = item composto único `[2.1.24]`.
- Valor total R$7M = teto superior da faixa `[item 9]`, integralmente justificado por item → valor inabilitado-alvo 0% `[11.2.2]`.

---

## v1.0 (SUPERSEDED) — histórico

- **O quê:** consolidação inicial em R$4.500.000,00 com 9 rubricas já respeitando tetos do edital.
- **Por quê superseded:** subdimensionava (a) iterações de ensaio de material, (b) PI internacional, (c) HPC, (d) 2 ambientes laboratoriais, (e) disseminação internacional (COP-31/32). Manter R$4,5M deixaria **valor inabilitado >30%** (risco R4) ao detalhar o ciclo real de P&D.
- **Decisão:** retificar para v2.0 (R$7M) — ⚠️ Avaliar risco de super orçado.

---

## Política de versionamento
- Nova versão (minor v2.x) só se houver **readequação de rubrica** ou atualização de pró-manual (item 11.2.4).
- Toda alteração registrada aqui com: versão, data ISO, valor, status, o quê/por quê/quando.
- A versão vigente espelha-se na proposta-mãe (`finep-agrifam-bioeolica-linha2.md`, §1 e §6) e neste log.
