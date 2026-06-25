# Registro de Decisões do Projeto

| Decisão | Contexto | Alternativa | Decisão | Responsável | Data | Status |
|---------|----------|-------------|---------|-------------|------|--------|
| D014-P0 | HUMAN_GATE caveats applied to research.md + contracts | Original Option C had local ConfigManager fallback; original research rejected module-level ConfigManager instance; original sample had cfg.get() inside stiffness_matrix() | Apply 3 caveats: (1) shim re-export only, no local fallback; (2) module-level `_CFG_DEFAULTS = ConfigManager.from_defaults()` is OK; (3) cache resolved values in __init__/__post_init__, not hot path | Engineer (Marcus Webb) | 2026-06-18 | APPROVED |
| - | - | - | - | - | - | - |
