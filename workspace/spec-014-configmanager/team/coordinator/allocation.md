# Alocação de Tarefas — {{PROJECT_NAME}}

**Gerado em:** Pendente — execute `coordinator.sh init`
**Agente:** Coordenador

## Agentes Convocados

*Nenhum — execute `coordinator.sh init` para derivar o time do contexto.*

## Regras de Alocação

1. **Domínio confirmado** (relevance_check = SIM) → gera um agente especialista
2. **Domínio rejeitado** (relevance_check = NÃO) → registra justificativa no domain_map
3. **Coordenador** sempre presente — gerencia dependências, detecta deadlocks, convoca reuniões
4. **Paralelismo mínimo** — 3 agentes trabalhando simultaneamente
5. **Sincronização** — agentes com interconexão forte sincronizam via reunião coordenada
