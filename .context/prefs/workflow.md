# Development Workflow Rules — bioeolica-entrega

> Fluxo obrigatório. FSM de orquestração (F1–F9) conforme INSTRUCTIONS.md/CONVENTIONS.md.

## Full Flow (sem exceções)

### feat
1. Ler INSTRUCTIONS.md/INPUT.md/CONVENTIONS.md + spec relevante
2. `impact()` GitNexus no símbolo a editar
3. Implementar em `workspace/<lab>/`
4. TDD: teste primeiro
5. `pytest` verde + `ruff` limpo
6. `detect_changes()` antes de commit

### fix
1. Reproduzir (teste falhando)
2. Root cause
3. Corrigir
4. Verde + regressão

### refactor
1. Testes verdes antes
2. Passos pequenos e verificáveis
3. Comportamento externo inalterado

## Decision Logging (`.context/current/branches/<branch>/session.log`)
Registrar quando: escolha de alternativa, bug encontrado+corrigido, decisão de API/arquitetura, abordagem descartada.

Formato:
```
## <ISO-8601>
**Decision**: <o quê>
**Alternatives**: <excluídas>
**Reason**: <por quê>
**Risk**: <risco>
```

## VVV (Validação, Verificação, Validada)
Toda entrega passa pelos 3 gates antes de merge em `develop`/release `main`.
