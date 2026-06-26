# Baseline Verification — 2026-06-13

> **Fase 2 — T005**: Verificação formal do estado do banco de dados
> **Princípio**: UNTRUSTED — todos os dados verificados independentemente

---

## Resumo

| Métrica | Valor |
|---------|-------|
| Database | `data/bioeolica.db` |
| Tamanho | 1.5 MB |
| Integridade | ✅ PASS |
| Tabelas | 15 |
| Views | 14 |
| FK violations | 0 |
| Migrations aplicadas | 3 de 4 esperados |

---

## Schema

### Migrations

| Versão | Descrição | Status |
|--------|-----------|--------|
| v1 | Core schema: objects, provenance, quality_scores | ✅ APPLIED |
| v2 | schema-validation.sql | ✅ APPLIED |
| v3 | pqms-interface.sql | ✅ APPLIED |
| v4 | **AUSENTE** (esperado por database.py) | ❌ MISSING |

**Observação**: `database.py` espera migration v4, mas o DB tem apenas v1-v3. A v4 nunca foi aplicada — possível causa do SC-004/SC-005 incompleto.

### Tabelas (15)

| Tabela | Registros | Notas |
|--------|-----------|-------|
| `objects` | 284 | Registry universal |
| `quality_scores` | 3835 | Scores PQMS individuais |
| `validation_references` | 49 | Referências normativas |
| `computational_models` | 48 | Modelos FEM/CFD |
| `provenance` | 53 | Edges do DAG |
| `simulation_results` | 34 | Resultados de simulação |
| `test_results` | 10 | Resultados experimentais |
| `community_profiles` | 2 | Perfis de comunidade |
| `material_specimens` | 4 | Corpos de prova |
| `wind_turbine_systems` | 2 | Sistemas eólicos cadastrados |
| `blade_designs` | 1 | Design de pá |
| `energy_systems` | **0** | ❌ Vazio (causa SC-004 FAIL) |
| `microstructure_images` | 0 | Não utilizado |
| `pqms_dimension_weights` | 13 | Pesos D1-D13 |
| `schema_migrations` | 3 | Controle de versão |

### Views (14)

| View | Propósito |
|------|-----------|
| `v_economic_targets` | SC-004 — alvos econômicos |
| `v_energy_sizing` | SC-005 — dimensionamento energético |
| `v_material_characterization` | Propriedades de materiais |
| `v_methodology_validation` | Validação de metodologia |
| `v_pqms_aggregate` | PQMS agregado por objeto |
| `v_pqms_breakdown` | Detalhamento por dimensão |
| `v_pqms_pending` | Objetos pendentes de PQMS |
| `v_pqms_summary` | Sumário PQMS |
| `v_provenance_audit` | Auditoria de proveniência |
| `v_provenance_coverage` | Cobertura do DAG |
| `v_provenance_cycles` | Detecção de ciclos |
| `v_provenance_orphans` | Referências órfãs |
| `v_safety_factor_check` | SC-003 — fatores de segurança |
| `v_success_criteria_status` | Status consolidado dos SC |

---

## Objetos no Registry (284)

### Por tipo

| Tipo | Quantidade | Com PQMS | Média PQMS |
|------|-----------|----------|-----------|
| `computational_model` | 48 | 48 | ~8.5 |
| `specimen` | 48 | 0 | N/A |
| `validation_reference` | 49 | ~39 | ~9.0 |
| `community_profile` | 7 | 2 | 9.5 |
| `wind_turbine_system` | 2 | 1 | 9.18 |
| `blade_design` | 1 | 1 | 9.19 |
| `simulation_result` | 34 | ~34 | ~8.5 |
| `test_result` | 10 | ~10 | ~8.5 |
| `energy_system` | **0** | 0 | N/A |
| `microstructure_image` | 0 | 0 | N/A |

### Objetos críticos

- `191c0b4f...` — blade_design, PENDING, score=9.19
- `fbcab5ce...` — wind_turbine_system, PENDING, score=None
- `300de9bf...` — wind_turbine_system, PENDING, score=9.18
- `a92ffcb6...` — community_profile, PASS, score=9.5

---

## Proveniência (DAG)

| Métrica | Valor | Status |
|---------|-------|--------|
| Total de edges | 53 | — |
| Ciclos | 0 | ✅ PASS |
| Órfãos | 0 | ✅ PASS |
| Objetos com upstream | ~20 | — |
| Objetos com downstream | ~20 | — |

---

## Gaps Identificados

| Gap | Impacto | Prioridade |
|-----|---------|------------|
| `energy_systems` vazia (0 registros) | SC-004 FAIL — sem alvo econômico | 🔴 CRÍTICA |
| `community_profiles` sem demanda energética | SC-005 FAIL — sizing sem baseline | 🔴 CRÍTICA |
| Migration v4 ausente | Schema incompleto | 🟡 MÉDIA |
| 48 `specimens` sem PQMS | SC-008 parcial | 🟡 MÉDIA |
| `microstructure_images` vazia | US4 não executado | 🟢 BAIXA |

---

## Artefatos da Fase 2

| Tarefa | Arquivo | Status |
|--------|---------|--------|
| T003 | `src/common/db_helper.py` | ✅ CRIADO |
| T004 | `src/common/wind_utils.py` | ✅ CRIADO |
| T005 | Este relatório | ✅ VERIFICADO |

---

*Relatório gerado automaticamente em 2026-06-13. Estado salvo como baseline para comparação futura.*
