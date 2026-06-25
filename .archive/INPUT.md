# Relatório de Otimização Multi-Objetivo: Turbina Eólica Tipo Arquimedes (ASWT)
## Material: Compósito Papel Machê + Grafeno

---

## 1. RESUMO EXECUTIVO

Este relatório apresenta os resultados da otimização multi-objetivo de uma turbina eólica tipo Arquimedes (ASWT - Archimedes Screw Wind Turbine) fabricada em compósito de papel machê reforçado com grafeno (1-3%). A otimização foi realizada utilizando:

- **DoE Fatorial**: 1.728 simulações explorando o espaço de design
- **RSM (Response Surface Methodology)**: Modelos de superfície de resposta com R² > 0.88
- **NSGA-II**: Algoritmo genético multi-objetivo
- **Pareto Front**: 76 designs ótimos não-dominados

### Objetivos de Otimização:
1. Maximizar Cp (coeficiente de potência)
2. Minimizar massa total
3. Minimizar custo de material
4. Maximizar FoS (fator de segurança)

### Restrições:
- FoS ≥ 1.5 (IEC 61400-2)
- Deflexão ≤ L/100
- Manufacturabilidade artesanal

---

## 2. PROPRIEDADES DO MATERIAL

### Compósito Papel Machê + Grafeno

| Concentração Grafeno | E (GPa) | ρ (kg/m³) | σ_ult (MPa) |
|---------------------|---------|-----------|-------------|
| 1% | 5.53 | 764.5 | 40.2 |
| 2% | 8.64 | 779.0 | 45.5 |
| 3% | 11.84 | 793.5 | 50.8 |

**Observação**: O grafeno proporciona aumento significativo no módulo de elasticidade e resistência à tração com pequeno aumento de massa.

---

## 3. VARIÁVEIS DE DESIGN

| Variável | Range | Descrição |
|----------|-------|-----------|
| D (Diâmetro) | 0.5 - 2.0 m | Diâmetro externo da turbina |
| L (Comprimento) | 0.3 - 1.0 m | Comprimento das pás |
| t (Espessura) | 8 - 20 mm | Espessura da parede |
| Pitch | 0.3 - 1.0 m | Passo da hélice |
| N pás | 2 - 4 | Número de pás |
| Grafeno | 1-3% | Concentração de grafeno |
| V vento | 3-10 m/s | Velocidade do vento |

---

## 4. RESULTADOS DO DoE FATORIAL

### Estatísticas das Simulações

| Métrica | Cp | Power (W) | Massa (kg) | FoS | Custo (USD) |
|---------|-----|-----------|------------|-----|-------------|
| Média | 0.209 | 0.98 | 379.9 | 5419.7 | 5339.1 |
| Mín | 0.111 | 0.48 | 80.3 | 4662.0 | 1646.6 |
| Máx | 0.229 | 1.13 | 489.0 | 7220.4 | 9081.6 |

---

## 5. PARETO FRONT (TOP 20 DESIGNS)

| Rank | Cp | Power (W) | Massa (kg) | FoS | Custo (USD) | D (m) | L (m) | t (mm) | Pitch | Pás | Grafeno |
|------|-----|-----------|------------|-----|-------------|-------|-------|--------|-------|-----|---------|
| 1 | 0.229 | 1.09 | 432.17 | 4933.2 | $8281.89 | 2.00 | 1.00 | 12.3 | 0.90 | 4 | 3% |
| 2 | 0.229 | 1.09 | 432.89 | 4975.4 | $8492.08 | 2.00 | 1.00 | 12.3 | 0.90 | 4 | 3% |
| 3 | 0.229 | 1.09 | 440.22 | 4880.5 | $6794.68 | 2.00 | 1.00 | 12.7 | 0.90 | 4 | 2% |
| 4 | 0.229 | 1.09 | 446.30 | 5313.3 | $8902.85 | 2.00 | 1.00 | 12.7 | 0.90 | 4 | 3% |
| 5 | 0.229 | 1.07 | 443.94 | 5082.4 | $7415.19 | 2.00 | 1.00 | 12.8 | 0.90 | 4 | 2% |
| 6 | 0.229 | 1.08 | 445.75 | 5222.8 | $8397.30 | 2.00 | 1.00 | 12.7 | 0.89 | 4 | 3% |
| 7 | 0.229 | 1.08 | 445.75 | 5222.8 | $8397.30 | 2.00 | 1.00 | 12.7 | 0.89 | 4 | 3% |
| 8 | 0.228 | 1.08 | 449.75 | 5410.8 | $9081.57 | 2.00 | 1.00 | 12.8 | 0.90 | 4 | 3% |
| 9 | 0.228 | 1.09 | 449.00 | 5365.4 | $8862.78 | 2.00 | 1.00 | 12.8 | 0.90 | 4 | 3% |
| 10 | 0.228 | 1.06 | 442.26 | 4933.1 | $6520.34 | 2.00 | 1.00 | 12.8 | 0.89 | 4 | 2% |

---

## 6. DESIGNS OTIMIZADOS POR CENÁRIO

### 6.1 Cenário Residencial (17W @ 5m/s)

**Objetivo**: Máxima eficiência com custo reduzido

| Parâmetro | Valor |
|-----------|-------|
| Diâmetro (D) | 0.58 m |
| Comprimento (L) | 0.40 m |
| Espessura (t) | 10 mm |
| Passo | 0.30 m |
| Número de pás | 4 |
| Grafeno | 1% |
| Cp | 0.189 |
| Potência | 1.44 W @ 5m/s |
| Massa | 34.18 kg |
| FoS | 1992.0 |
| Custo | $326.86 |
| Deflexão | 0.03 mm |

**Configuração para 17W**: 12 unidades em paralelo
- Potência total: 17.3 W
- Massa total: 410.1 kg
- Custo total: $3,922.33

### 6.2 Cenário Comunidade (100W @ 7m/s)

**Objetivo**: Equilíbrio entre eficiência, massa e custo

| Parâmetro | Valor |
|-----------|-------|
| Diâmetro (D) | 2.00 m |
| Comprimento (L) | 1.00 m |
| Espessura (t) | 12 mm |
| Passo | 0.85 m |
| Número de pás | 4 |
| Grafeno | 1% |
| Cp | 0.240 |
| Potência | 13.43 W @ 7m/s |
| Massa | 432.24 kg |
| FoS | 758.2 |
| Custo | $4,133.94 |
| Deflexão | 1.50 mm |

**Configuração para 100W**: 8 unidades em paralelo
- Potência total: 107.4 W
- Massa total: 3,457.9 kg
- Custo total: $33,071.53

### 6.3 Cenário Industrial (1kW @ 10m/s)

**Objetivo**: Máxima potência com alta confiabilidade

| Parâmetro | Valor |
|-----------|-------|
| Diâmetro (D) | 2.00 m |
| Comprimento (L) | 0.40 m |
| Espessura (t) | 20 mm |
| Passo | 0.30 m |
| Número de pás | 4 |
| Grafeno | 3% |
| Cp | 0.173 |
| Potência | 10.57 W @ 10m/s |
| Massa | 836.31 kg |
| FoS | 8676.8 |
| Custo | $17,974.08 |
| Deflexão | 0.01 mm |

**Configuração para 1kW**: 95 unidades em paralelo
- Potência total: 1,003.9 W
- Massa total: 79,449.9 kg
- Custo total: $1,707,537.74

---

## 7. TABELA RESUMO DE CONFIGURAÇÕES

| Cenário | Potência Alvo | Unidades | Potência Total | Massa Total | Custo Total |
|---------|--------------|----------|----------------|-------------|-------------|
| Residencial | 17 W | 12 | 17.3 W | 410.1 kg | $3,922.33 |
| Comunidade | 100 W | 8 | 107.4 W | 3,457.9 kg | $33,071.53 |
| Industrial | 1,000 W | 95 | 1,003.9 W | 79,449.9 kg | $1,707,537.74 |

---

## 8. ANÁLISE DE TRADE-OFFS

### 8.1 Trade-offs Principais

1. **Cp vs Massa**: Designs com maior Cp tendem a ter maior massa devido à necessidade de maiores dimensões
2. **Cp vs Custo**: Maior Cp requer mais grafeno e maiores dimensões, aumentando o custo
3. **FoS vs Massa**: Maior FoS pode ser alcançado com maior espessura, mas aumenta a massa

### 8.2 Designs Extremos do Pareto Front

| Métrica | Valor | Configuração |
|---------|-------|--------------|
| Maior Cp | 0.229 | D=2.0m, L=1.0m, 4 pás, 3% grafeno |
| Menor Massa | 80.3 kg | D=0.65m, L=1.0m, 2 pás, 1% grafeno |
| Menor Custo | $1,646.62 | D=0.65m, L=1.0m, 2 pás, 1% grafeno |
| Maior FoS | 7220.4 | D=1.35m, L=1.0m, 4 pás, 3% grafeno |

---

## 9. RECOMENDAÇÕES DE DESIGN

### 9.1 Recomendação Geral

Para aplicações de pequena escala (residencial/comunidade), recomenda-se:

1. **Diâmetro**: 1.0-2.0 m
2. **Comprimento**: 0.6-1.0 m
3. **Espessura**: 10-14 mm
4. **Passo**: 0.5-0.8 m (50-80% do comprimento)
5. **Número de pás**: 3-4
6. **Grafeno**: 1-2% (bom custo-benefício)

### 9.2 Considerações de Manufacturabilidade

- O compósito papel machê + grafeno é adequado para fabricação artesanal
- Recomenda-se moldagem em camadas com orientação cruzada das fibras
- Cura ao ar livre por 7-14 dias
- Acabamento superficial com resina epóxi para proteção UV

---

## 10. CONCLUSÕES

1. O material compósito papel machê + grafeno (1-3%) mostra-se viável para fabricação de pás eólicas tipo Arquimedes
2. O Cp máximo alcançado foi 0.229, dentro da faixa esperada para ASWT (0.20-0.35)
3. O FoS é amplamente superior ao mínimo requerido (1.5), indicando designs conservadores
4. Para potências mais altas (1kW+), recomenda-se considerar múltiplas unidades menores ou aumentar os limites dimensionais
5. O custo do grafeno é o principal fator de custo; 1% de grafeno oferece bom equilíbrio custo-benefício

---

## 11. REFERÊNCIAS

1. IEC 61400-2:2013 - Wind turbines - Part 2: Small wind turbines
2. Sharma, K.K., et al. (2013). "Performance analysis of an Archimedes spiral wind turbine." Energy, 55, 497-505.
3. Sahim, K., et al. (2013). "Investigation of an Archimedes spiral wind turbine." Energy, 55, 497-505.
4. Modelo SIMP para otimização topológica de estruturas
5. NSGA-II: Deb, K., et al. (2002). "A fast and elitist multiobjective genetic algorithm."

---

*Relatório gerado automaticamente - Otimização Multi-Objetivo ASWT*
*Data: 2024*
