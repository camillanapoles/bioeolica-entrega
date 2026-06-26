# Assumptions — Turbine Upscaling Analysis

> **Fase 6 — T018**: Documentação de premissas
> **Data**: 2026-06-13

---

## 1. Recurso Eólico

| Premissa | Valor | Fonte | Impacto |
|----------|-------|-------|---------|
| Weibull shape k | 2,0 | Sertão NE (INMET/SONDA) | Moderado — variacao sazonal |
| Weibull scale c @ 10m | 6,5 m/s | Sertão NE | Alto — define AEP base |
| Shear exponent alpha | 0,20 | Terreno aberto semiárido | Alto — define vento no hub |
| Densidade do ar | 1,105 kg/m³ | 40°C, 500m | Moderado ±1% por 5°C |
| Vento médio @ 30m | 7,5 m/s | Calculado da lei de potência | Alto — validação de campo necessária |

**Limitação**: Dados de vento baseados em séries históricas regionais. Cada local específico requer medição in-situ.

---

## 2. Aerodinâmica

| Premissa | Valor | Fonte |
|----------|-------|-------|
| Cp máximo VAWT | 0,35 | Paraschivoiu, Tjiu et al. (2015) |
| Cp máximo HAWT | 0,45 | Betz limit × 0,76 |
| TSR ótimo VAWT | 2,5 | Darrieus H-rotor |
| TSR ótimo HAWT | 7,0 | Small wind padrão |
| Cut-in | 3,0 m/s | Pequenas turbinas típico |
| Cut-out | 25,0 m/s | IEC 61400-2 |

**Limitação**: Curvas Cp(λ) são genéricas da literatura. Cada design específico requer simulação CFD ou túnel de vento.

---

## 3. Custos

| Premissa | Valor | Fonte |
|----------|-------|-------|
| Scaling exponent | 0,70-0,90 | Power-law por componente |
| Taxa de câmbio | 5,0 BRL/USD | Mercado 2025-2026 |
| Mão de obra | $12,50/h | Técnico especializado NE |
| Aço estrutural | $2,50/kg | Mercado Brasil |
| Compósito (fibra de vidro) | $8,00/kg | Resina epóxi + fibra |
| Cobre | $12,00/kg | Mercado internacional |
| Ímãs NdFeB | $60,00/kg | Neodímio permanente |
| Bateria LiFePO4 | $180/kWh | Armazenamento estacionário |

**Limitação**: Custos de materiais variam ±20% com mercado. Custos de logística para áreas remotas do NE podem adicionar 10-30%.

---

## 4. Financeiras

| Premissa | Valor | Justificativa |
|----------|-------|---------------|
| Taxa de desconto | 8% | SELIC (14,25%) + risco projeto |
| Vida útil | 20 anos | Pequenas turbinas típico |
| O&M anual | 2% do investimento | Remoto, acesso limitado |
| Depreciação anual | 0,5%/ano | Degradação de desempenho |

**Limitação**: Taxa de desconto é altamente sensível a condições de financiamento rural (PRONAF, programas governamentais podem reduzir para 4-6%).

---

## 5. Armazenamento

| Premissa | Valor | Fonte |
|----------|-------|-------|
| Autonomia | 2 dias | Off-grid típico |
| DoD (LiFePO4) | 80% | Ciclo de vida 3000+ |
| Eficiência | 90% | Inversor + bateria |
| Tensão DC | 48 V | Off-grid padrão |
| Demanda diária | 40 kWh/dia | ~10 famílias rurais |

**Limitação**: Demanda varia por perfil de consumo comunitário. 40 kWh/dia é estimativa para assentamento típico do NE semiárido.

---

## 6. Estruturais

| Premissa | Valor | Fonte |
|----------|-------|-------|
| Massa torre | 30 + 8 × P (VAWT) ou 40 + 12 × P (HAWT) | Estimativa paramétrica |
| Massa pás | 5 + 3 × P (VAWT) ou 4 + 4 × P (HAWT) | Compósito |
| Massa gerador | 8 + 2,5 × P | PMSG radial |
| Massa ímãs | 8% do gerador | NdFeB |
| Massa cobre | 12% do gerador | Enrolamento |

**Limitação**: Massas paramétricas baseadas em literatura de turbinas <50 kW. Design estrutural detalhado requer análise FEM.

---

## 7. Metodológicas

| Premissa | Escopo |
|----------|--------|
| Modelo de top-down | custos de componentes escalam com power-law |
| Modelo de bottom-up | BOM itemizado + manufatura + montagem |
| AEP via integração Weibull × Cp | Precisão ~5-10% vs. dados reais |
| LCOE via NPV | CAPEX + OPEX descontado + depreciação |

**Validações pendentes**:
- [ ] Comparação com dados de campo de turbinas instaladas no NE
- [ ] Validação CFD das curvas Cp(λ)
- [ ] Calibração de massas paramétricas com FEM estrutural
- [ ] Sensibilidade a perfil de demanda real (não estimado)

---

## 8. Regulatórias

| Norma | Aplicação |
|-------|-----------|
| IEC 61400-2 | Pequenas turbinas eólicas |
| ISO 2533 | Atmosfera padrão (air density) |
| ABNT NBR | Normas brasileiras de instalação |
| PROINFRA | Programa de incentivo (se aplicável) |

---

*Este documento deve ser revisado quando novos dados de campo, normas ou condições de mercado forem disponíveis.*
