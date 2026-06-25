# Contexto — Engenharia de Contexto do Projeto

Este diretório contém o **sistema nervoso** do time multi-agente: todo contexto capturado,
gerado e compartilhado durante o ciclo de vida do projeto.

## Estrutura

| Diretório | Descrição |
|-----------|-----------|
| `ontology.json` | Schema ontológico — classes, propriedades, relacionamentos |
| `index.json` | Índice de todos os contextos do projeto |
| `graph.json` | Grafo de conhecimento serializado + queries |
| `quality_gates.json` | Configuração dos 4 gates de qualidade |
| `materials/` | Contextos de material (propriedades, comportamento) |
| `loads/` | Condições de carregamento |
| `constraints/` | Restrições de projeto |
| `components/` | Componentes físicos |
| `methods/` | Métodos numéricos selecionados |
| `tools/` | Ferramentas computacionais |
| `decisions/` | Decisões de projeto registradas |
| `simulations/` | Simulações executadas |
| `publications/` | Artigos e relatórios |
| `meetings/` | Reuniões do time |
| `lineage/` | Rastreabilidade de cada contexto |

## Quality Gates

Todo contexto deve passar por 4 gates antes de ser publicado em `shared/`:

1. **GATE 1 — Schema Validation**: O contexto segue a ontologia?
2. **GATE 2 — Sanity Check**: É fisicamente plausível?
3. **GATE 3 — Freshness**: Ainda é válido (não expirou)?
4. **GATE 4 — Revisor Hostil**: Outro agente validou?

Ver `quality_gates.json` para detalhes e regras.

## Formato de um Contexto

```json
{
  "id": "CTX-MAT-0001",
  "class": "Material",
  "label": "Aço Estrutural ASTM A36",
  "properties": {
    "E": { "value": 200, "unit": "GPa", "source": "ASTM A36" },
    "sigma_y": { "value": 250, "unit": "MPa", "source": "ASTM A36" },
    "rho": { "value": 7.85, "unit": "g/cm³", "source": "data_sheet" },
    "nu": { "value": 0.3, "unit": "adimensional", "source": "data_sheet" }
  },
  "lineage": {
    "created_by": "agent-materiais",
    "version": "1.0.0",
    "created_at": "2026-06-09T10:00:00Z",
    "based_on": ["LOG-MATERIAIS-0001"],
    "freshness": 1.0,
    "quality_gate_status": {
      "schema": "PASS",
      "sanity": "PASS",
      "freshness": "PASS",
      "revisor": "PASS"
    }
  },
  "relationships": {
    "isUsedIn": ["CTX-COMP-0001"],
    "classifiedBy": ["CTX-NORM-0001"]
  }
}
```

## Fluxo

1. Agente cria contexto em seu diretório (`team/agent-*/`)
2. Submete ao coordenador via quality gates
3. Gate 1-4 validam sequencialmente
4. Se ALL_PASS → contexto publicado em `context/{class}/{id}.json`
5. Agentes subscriptores são notificados via shared/
6. Contexto indexado em `index.json` e `graph.json`
