# Workspace Computacional — Laboratório Virtual Multi-Agente

Cada projeto de engenharia neste repositório segue uma estrutura padronizada de workspace,
permitindo que múltiplos agentes especialistas trabalhem em paralelo sem interferência,
compartilhando dados de forma controlada e registrando decisões, reuniões e validações.

## Estrutura

```
workspace/{projeto}/
├── context/               # Engenharia de Contexto (sistema nervoso do time)
│   ├── ontology.json      # Schema ontológico: classes, propriedades, relacionamentos
│   ├── index.json         # Índice de todos os contextos do projeto
│   ├── graph.json         # Grafo de conhecimento serializado + queries
│   ├── quality_gates.json # 4 gates de qualidade (schema+sanity+freshness+revisor)
│   ├── materials/         # Propriedades de materiais
│   ├── loads/             # Condições de carregamento
│   ├── constraints/       # Restrições de projeto
│   ├── components/        # Componentes físicos
│   ├── methods/           # Métodos numéricos selecionados
│   ├── tools/             # Ferramentas computacionais
│   ├── decisions/         # Decisões de projeto
│   ├── simulations/       # Simulações executadas
│   ├── publications/      # Artigos e relatórios
│   ├── meetings/          # Reuniões do time
│   └── lineage/           # Rastreabilidade de contextos
├── domains/                # F2: Mapeamento de Domínios
├── domains/                # F2: Mapeamento de Domínios
│   ├── relevance_check.md  # Relevance check dos domínios aplicáveis
│   ├── m3_matrix.md        # Matriz M³ por domínio
│   └── domain_map.json     # Mapa completo de domínios + cobertura
├── team/                   # Agentes Especialistas (1 dir por domínio)
│   ├── coordinator/        # Coordenador: alocação, agenda, atas
│   │   ├── allocation.md   # Alocação de tarefas por agente
│   │   ├── agenda.md       # Reuniões agendadas
│   │   └── atas/           # Atas de reuniões realizadas
│   ├── agent-materiais/    # Ambiente isolado do agente
│   ├── agent-mecanica/     # Ambiente isolado do agente
│   ├── agent-fluidos/      # Ambiente isolado do agente
│   └── ...                 # Conforme domínios relevantes
├── shared/                 # Dados compartilhados entre agentes
│   ├── materials/          # Banco de dados de materiais
│   ├── geometry/           # Modelos geométricos (CAD, malhas)
│   ├── loads/              # Condições de carga e contorno
│   └── results/            # Resultados consolidados
├── meetings/               # Dinâmica de reuniões e decisões
│   ├── decision_log.md     # Registro de decisões do projeto
│   ├── deadlocks.md        # Conflitos e resoluções
│   └── ata/                # Atas de reuniões
├── publications/           # Artigos científicos em produção
│   ├── drafts/             # Rascunhos de papers
│   ├── figures/            # Figuras e gráficos
│   └── submissions/        # Submissões e revisões
└── vvv/                    # Validação, Verificação e Certificação
    ├── verification/       # Relatórios de verificação numérica
    ├── validation/         # Relatórios de validação experimental
    └── certification/      # Certificações PASS/FAIL
```

## Uso

### Criar um novo projeto

```bash
./scripts/criar-workspace.sh nome-do-projeto
```

Isso instancia o template em `workspace/nome-do-projeto/` com diretórios e arquivos
de placeholder prontos para uso.

### Convenções

- **Agentes escrevem apenas em seu diretório** (`team/agent-*/`) — nunca no diretório de outro agente
- **Dados compartilhados** vão em `shared/` com arquivos versionados via Git LFS
- **Cada reunião** gera uma ata em `meetings/ata/` com decisões e action items
- **Toda análise** gera um relatório VVV em `vvv/` antes de ser considerada válida
- **Logs WAL** seguem o formato JSON Schema definido na engine (ver `INSTRUCTIONS.md`)

### Versionamento

- Arquivos pequenos (< 1MB): Git standard
- Malhas, resultados de simulação (> 1MB): Git LFS
- Dados grandes (bases de material, resultados brutos): DVC
