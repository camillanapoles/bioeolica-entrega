# Knowledge Base Index — Composite Wind Energy

> **SPEC1 Phase 8 — T068**: Documentation of research decisions, modeling assumptions, and validation certificates.
> **Date**: 2026-06-14
> **Principle**: UNTRUSTED — all sources independently verified.

---

## Purpose

This index centralizes the knowledge base entries produced across phases. Each section below points to the authoritative file in its subdirectory. Research decisions, modeling assumptions, and validation certificates live alongside their source data, not in a monolithic document, so they can evolve independently as the project advances.

---

## Research Decisions

Decisions trace the rationale behind material choices, topology selection, and computational methods.

| Decision | Authoritative Source | Phase | Summary |
|----------|----------------------|-------|---------|
| Turbine topology (VAWT vs HAWT) | `wind-energy/topology_recommendation.md` | Phase 4 / US1 | HAWT selected over VAWT for capacity factor, manufacturability, cost |
| Composite material formulation | `materials/README.md` | Phase 1 / SC-001 | Paper mache + PVA binder + graphite coating pathway |
| Cost model | `wind-energy/cost_model_report.md` | Phase 5 / US2 | BOM-based, BOM allocations documented, LCOE $0.0176/kWh |

---

## Modeling Assumptions

Assumptions underpin every computational model. Each carries a documented impact rating and source.

| Assumption Class | Authoritative Source | Key Entries |
|------------------|----------------------|-------------|
| Wind resource | `wind-energy/assumptions.md` §1 | Weibull k=2.0, c=6.5 m/s, alpha=0.20, 7.5 m/s @ 30m |
| Aerodynamics | `wind-energy/assumptions.md` §2 | Cp HAWT=0.45, Cp VAWT=0.35, TSR optima |
| Structural | `wind-energy/assumptions.md` (blades) | NACA 0018 baseline, 3.5m blade, 11 stations |
| Material | `materials/README.md` | ASTM D638/D790/D695/D2240 testing standards, cellulose fiber reinforcement |
| Cost | `wind-energy/cost_model_report.md` | Per-kW and per-kWh cost factors, BOM breakdown |

Every assumption has a `Limitation` note indicating where field measurement or experimental validation is required.

---

## Validation Certificates

Validation follows the VVV framework: Verification (numerical) → Validation (experimental/benchmark) → Certification (PASS/FAIL with uncertainty).

| Certificate | Authoritative Source | Status | Method |
|-------------|----------------------|--------|--------|
| Database integrity | `wind-energy/baseline_verification.md` | ✅ PASS | FK violation count = 0, 15 tables, 14 views |
| Migration tracking | `wind-energy/baseline_verification.md` | ⚠️ PARTIAL | 3 of 4 migrations applied; v4 pending |
| SC-001 Material characterization | `v_material_characterization` view | ✅ PASS | +31% flexural strength vs baseline |
| SC-003 Safety factors | `v_safety_factor_check` view | ✅ PASS | All factors within design envelope |
| SC-004 Economic targets | `v_economic_targets` view | ✅ PASS | LCOE $0.0176/kWh, cost $691/kW |
| SC-005 Energy sizing | `v_energy_sizing` view | ✅ PASS | 2.0 day autonomy, 56.7% capacity factor |
| SC-007 Provenance audit | `v_provenance_audit` view | ✅ PASS | Full specimen→test_result chain restored (T009 fix) |
| SC-008 PQMS | `v_pqms_summary` view | ❌ FAIL | Weighted PQMS below 9.5 on some objects |
| SC-010 Environmental | `validation_references` table | ✅ PASS | 71 refs, all source quality ≥ 8/10, avg 9.0/10 |

---

## Coverage of T068 Spec Requirements

| Requirement | Status | Location |
|-------------|--------|----------|
| Document all research decisions | ✅ COMPLETE | This file + 4 decision docs |
| Document modeling assumptions | ✅ COMPLETE | `wind-energy/assumptions.md` + `materials/README.md` |
| Document validation certificates | ✅ COMPLETE | This file + `baseline_verification.md` |
| Store under `knowledge/` | ✅ COMPLETE | All sources under `knowledge/` |

---

## Knowledge Maintenance

This index must be regenerated whenever:
1. A new research decision is logged (add row to Research Decisions table)
2. A modeling assumption changes (update Assumptions doc, update this index)
3. A SC status changes from PASS↔FAIL (update Validation Certificates table)

The `v_success_criteria_status` view is the live source of truth for SC PASS/FAIL — this index should mirror it whenever refreshed.
