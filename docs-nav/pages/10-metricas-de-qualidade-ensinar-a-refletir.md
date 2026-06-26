# Metricas de Qualidade - Ensinar a Refletir

_Origem: `INSTRUCTIONS.md` linhas 448-491 - Parte 0 - KDI & Fundamentos_

## ⚠️ MÉTRICAS DE QUALIDADE — ENSINAR A REFLETIR

### Métricas de Qualidade da Análise:

| Métrica | Descrição | Peso |
|---------|-----------|------|
| **Precisão** | Erro relativo vs. referência experimental | 25% |
| **Convergência** | Estabilidade numérica, independência de malha | 20% |
| **Fidelidade** | Correspondência com fenômeno físico real | 20% |
| **Robustez** | Sensibilidade a parâmetros de entrada | 15% |
| **Eficiência** | Tempo computacional vs. precisão | 10% |
| **Reprodutibilidade** | Capacidade de reproduzir resultados | 10% |

### Impacto de Erro:

| Tipo de Erro | Custo | Mitigação |
|--------------|-------|-----------|
| **Erro de Modelagem** | Alto — resultados inválidos | VVV rigoroso, validação experimental |
| **Erro de Malha** | Médio — convergência falsa | Refinamento adaptativo, estudo de malha |
| **Erro de Material** | Alto — propriedades incorretas | Banco de dados validado, calibração |
| **Erro de Fronteira** | Médio — condições irreais | Análise de sensibilidade, benchmarking |
| **Erro de Integração** | Alto — acoplamento mal feito | VVV em cada interface |

### Peso de Retrabalho:

| Fase | Custo de Retrabalho | Prevenção |
|------|---------------------|-----------|
| Conceito | 1x | Análise holística inicial |
| Design | 3x | VVV contínua |
| Prototipagem | 10x | Simulação exaustiva |
| Teste | 30x | Validação computacional prévia |
| Produção | 100x+ | Qualidade desde o início |

### Custo Monetário de Viés:

| Viés | Custo Estimado | Prevenção |
|------|---------------|-----------|
| Viés de confirmação | 15-30% do projeto | Revisão por pares, validação independente |
| Viés de ferramenta | 10-20% | Benchmarking multi-ferramenta |
| Viés de simplificação | 20-50% | Análise de incerteza, modelos hierárquicos |
| Viés de dados | 25-40% | Single Source of Truth, versionamento |

---
