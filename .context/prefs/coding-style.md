# Coding Style Guide — bioeolica-entrega

> Código neste repo. Alinhado a CONVENTIONS.md (M0–M9), INPUT.md, INSTRUCTIONS.md.

## General
- Funções curtas (<50 linhas), aninhamento ≤3.
- Nomes explícitos; sem variáveis de 1 letra exceto contadores de loop.
- Tratar erros explicitamente; nunca engolir silenciosamente.

## Python (pyproject: ruff, py311)
- Linha ≤100. Lint: E,F,I,B,UP,N.
- Sem hardcoded de constantes físico-científicas (P$1): tudo via config/JSON.
- Type hints em assinaturas públicas.

## Domínio (P$0/P$7)
- Todo dado/variável em JSON provido por SQLite + CRUD (P$0).
- Escrever SOMENTE em `workspace/<lab>/` (P$7).
- SSOT: `data/json/mapa_unico_informacao.json` espelha SQLite.

## Commits
- Conventional Commits, voz imperativa. Atômico (1 mudança lógica).
- Antes de commit: `detect_changes()` (GitNexus) + pytest verde.

## Testes
- Todo feat/fix com teste. Cobertura não pode cair.
- Fix: teste falhando PRIMEIRO, depois conserta.

## Segurança
- SQL sempre parametrizado (sem concatenação de string).
- Validar inputs nas fronteiras de confiança (loader, config).
