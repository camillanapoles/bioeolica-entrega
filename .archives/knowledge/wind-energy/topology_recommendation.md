# Topology Recommendation — Upscaling Analysis

> **Fase 3 — T010**: Relatório técnico baseado no sweep multi-config
> **Data**: 2026-06-13
> **Fonte**: `upscaling_sweep_results.json` (50 configurações)

---

## Sumário Executivo

HAWT supera VAWT em todas as métricas para o Sertão NE brasileiro. A melhor configuração entre 5-20 kW é **20 kW HAWT a 8,0 m/s**, com LCOE de **$0.0138/kWh** e custo instalado de **$588/kW** — ambos muito abaixo dos targets SC-004 ($0,15/kWh e $3.000/kW).

---

## Resultados do Sweep

### VAWT (25 configurações)

| Métrica | Mínimo | Máximo |
|---------|--------|--------|
| Cost/kW | $691 | $1.145 |
| LCOE | $0.0176/kWh | $0.0377/kWh |
| AEP | 19.168 kWh/yr | 99.340 kWh/yr |
| Capacity Factor | 43,7% | 56,7% |

### HAWT (25 configurações)

| Métrica | Mínimo | Máximo |
|---------|--------|--------|
| Cost/kW | $588 | $1.048 |
| LCOE | $0.0138/kWh | $0.0352/kWh |
| AEP | 18.790 kWh/yr | 107.652 kWh/yr |
| Capacity Factor | 42,9% | 61,5% |

---

## Melhores por Topologia

| Topologia | Rating | Vento | Cost/kW | LCOE | AEP |
|-----------|--------|-------|---------|------|-----|
| VAWT | 20 kW | 8,0 m/s | $691 | $0,0176/kWh | 99.340 kWh/yr |
| **HAWT** | **20 kW** | **8,0 m/s** | **$588** | **$0,0138/kWh** | **107.652 kWh/yr** |

**Diferencial HAWT**: 20% menor cost/kW, 22% menor LCOE, 8% maior AEP.

---

## Análise Comparativa

### Economias de Escala

```
Custo/kW × Potência Nominal:
  5 kW  VAWT: $1.145/kW   HAWT: $1.048/kW
 10 kW  VAWT:  $863/kW    HAWT:  $762/kW
 20 kW  VAWT:  $691/kW    HAWT:  $588/kW

Redução de 5→20 kW: VAWT -40%, HAWT -44%
```

Ambas as topologias mostram fortes economias de escala. HAWT mantém vantagem consistente de ~15% no custo/kW em todas as potências.

### LCOE vs Velocidade do Vento

```
LCOE ($/kWh) @ 10 kW:
  Vento   VAWT    HAWT   Diferença
  6,0    0,0284  0,0256  -10%
  7,0    0,0245  0,0206  -16%
  8,0    0,0219  0,0179  -18%

Target SC-004 (< $0,15/kWh): ✅ TODAS AS CONFIGS PASSAM
```

### SC-004 Cost/kW

Todas as 50 configurações passam SC-004 cost (< $3.000/kW). A melhor é 20 kW HAWT a $588/kW — **5,1× abaixo do limite**.

### SC-005c Capacity Factor

Todas as 50 configurações passam SC-005c (CF >= 20%). A pior é 5 kW HAWT @ 6,0 m/s com CF=42,9% — ainda **2,1× acima do limite**.

---

## Recomendação Final

### Configuração Recomendada

| Parâmetro | Valor |
|-----------|-------|
| **Topologia** | **HAWT** |
| **Potência** | **20 kW** |
| **Velocidade de projeto** | **8,0 m/s** |
| **Custo instalado** | **$11.760** |
| **Cost/kW** | **$588** |
| **LCOE** | **$0,0138/kWh** |
| **AEP** | **107.652 kWh/yr** |
| **Capacity Factor** | **61,5%** |
| **Rotor estimado** | **19,6 m diâmetro** |

### Justificativa

1. **HAWT supera VAWT em todas as métricas** para o regime de vento do Sertão (shear α=0,20, Weibull k=2,0)
2. **Economias de escala expressivas**: 20 kW tem cost/kW 44% menor que 5 kW
3. **SC-004 folgado**: LCOE é 10,9× menor que o limite, cost/kW é 5,1× menor
4. **SC-005c folgado**: CF é 3,1× maior que o limite mínimo

### Trade-offs

| Aspecto | HAWT | VAWT |
|---------|------|------|
| Torre mais alta | ✅ Maior captura energética | ❌ Não necessário |
| Manutenção (caixa de engrenagens) | ❌ Acesso no topo da torre | ✅ Gerador no nível do solo |
| Ruído | ❌ Ponta de pá em alta rotação | ✅ Menor TSR, mais silencioso |
| Impacto visual | ❌ Estrutura mais visível | ✅ Menor perfil |
| Custo de fabricação (DIY/comunidade) | ⚠️ Pás mais longas, requer precisão | ✅ Geometria mais simples |

Para contexto de **fabricação comunitária no semiárido NE brasileiro**, a simplicidade construtiva do VAWT pode compensar parcialmente a diferença de LCOE. Recomenda-se:
- Protótipo **10 kW HAWT** (torre treliçada, fabricação local) como configuração inicial
- VAWT permanece como alternativa para locais com vento turbulento ou acesso limitado para manutenção em torre

---

## Anexos

- Dados completos: `src/02-wind-energy/comparison/upscaling_sweep_results.json`
- Baseline DB: `knowledge/wind-energy/baseline_verification.md`
- Fase 2: `src/common/wind_utils.py`, `src/common/db_helper.py`
- US1 scripts: `cost_breakdown.py`, `aep_model.py`, `lcoe_model.py`
