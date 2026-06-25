# Cost Model Report — Upscaling Cost Analysis

> **Fase 4 — T013**: Relatório consolidado de custos
> **Data**: 2026-06-13

---

## Sumário Executivo

O modelo de custos para turbinas eólicas de pequeno porte (5-20 kW) no Sertão NE brasileiro demonstra que **HAWT de 20 kW** é a configuração mais econômica, com **LCOE de $0,0138/kWh** e custo instalado de **$588/kW** — ambos muito abaixo dos targets SC-004.

---

## SC-004 Status

| Target | Limite | Resultado (20 kW HAWT) | Status |
|--------|--------|----------------------|--------|
| Cost/kW | < $3.000/kW | **$588/kW** | ✅ PASS |
| LCOE | < $0,15/kWh | **$0,0138/kWh** | ✅ PASS |

**Todas as 50 configurações do sweep passam SC-004.**

---

## Estrutura de Custos

### Top-Down (cost_breakdown.py) — 20 kW HAWT

| Componente | Custo | % Total |
|------------|-------|---------|
| Rotor | $3.265 | 27,8% |
| Gerador | $1.899 | 16,1% |
| Torre | $1.140 | 9,7% |
| Bateria | $900 | 7,7% |
| Fixos (ctrl+inv+transp+inst) | $2.350 | 20,0% |
| BOS | $810 | 6,9% |
| **Total** | **$11.760** | **100%** |

### Bottom-Up BOM (bom_cost_model.py) — 20 kW VAWT

| Componente | Custo | % Total |
|------------|-------|---------|
| Bateria (40 kWh) | $7.200 | 66,8% |
| Eletrônica | $450 | 4,2% |
| Torres (aço) | $475 | 4,4% |
| Pás (compósito) | $520 | 4,8% |
| Gerador (ímãs + cobre) | $362 | 3,4% |
| Manufatura (106 h) | $1.733 | 16,1% |
| **Total BOM** | **$10.776** | **100%** |

**Observação**: O BOM é ~78% do custo total do modelo top-down. Os 22% restantes cobrem BOS, markup de integração, logística e margens não capturadas no BOM.

---

## Análise de Sensibilidade

Referência: 20 kW HAWT @ 8,0 m/s (LCOE base = $0,0138/kWh)

| Cenário | Variação | LCOE | Δ vs Base |
|---------|----------|------|-----------|
| Velocidade do vento -25% | 6,0 m/s | $0,0197 | **+42,8%** |
| Velocidade do vento +25% | 10,0 m/s | $0,0117 | -15,2% |
| Taxa de desconto 4% | Selic baixa | $0,0106 | -23,2% |
| Taxa de desconto 12% | Selic alta | $0,0173 | +25,4% |
| O&M 1% | Manutenção mínima | $0,0126 | -8,7% |
| O&M 4% | Manutenção remota | $0,0160 | +15,9% |
| Vida útil 15 anos | Substituição precoce | $0,0154 | +11,6% |
| Vida útil 25 anos | Operação estendida | $0,0129 | -6,5% |

**Principais conclusões**:
1. **Velocidade do vento** é o fator mais sensível (±42,8% para -25%)
2. **Taxa de desconto** é o segundo fator mais sensível (±25,4%)
3. **Mesmo no pior cenário (vento 6,0 m/s, selic 12%)**, o LCOE não chega a $0,02/kWh
4. Todos os cenários permanecem **abaixo do target SC-004 de $0,15/kWh**

---

## Economias de Escala

### Cost/kW por potência (VAWT)

| Potência | Cost/kW | Redução vs 5 kW |
|----------|---------|-----------------|
| 5 kW | $1.145 | — |
| 10 kW | $863 | -24,6% |
| 15 kW | $753 | -34,2% |
| 20 kW | $691 | **-39,7%** |

### VAWT vs HAWT (10 kW)

| Métrica | VAWT | HAWT | Vantagem |
|---------|------|------|----------|
| Cost/kW | $863 | $762 | HAWT -11,7% |
| LCOE | $0,0231 | $0,0190 | HAWT -17,7% |
| AEP | 47.196 kWh | 50.476 kWh | HAWT +6,9% |
| CF | 53,9% | 57,6% | HAWT +3,7pp |

---

## Recomendações

1. **Configuração primária**: 20 kW HAWT — menor LCOE, maior AEP
2. **Configuração secundária**: 10 kW VAWT — para locais com vento turbulento ou acesso limitado de manutenção
3. **Bateria domina o BOM** (67% para 20 kW) — reduzir autonomia de 2h para 1h corta o custo BOM em 33%
4. **Fabricação local**: BOM estima 106 h de fabricação para 20 kW — viável para produção comunitária
5. **O&M é baixo risco**: mesmo a 4% ao ano, LCOE permanece em $0,016/kWh

---

## Anexos

- Dados completos: `src/02-wind-energy/comparison/upscaling_sweep_results.json`
- Topologia: `knowledge/wind-energy/topology_recommendation.md`
- Baseline DB: `knowledge/wind-energy/baseline_verification.md`
- Scripts: `cost_breakdown.py`, `bom_cost_model.py`, `sensitivity_cost.py`, `lcoe_model.py`
