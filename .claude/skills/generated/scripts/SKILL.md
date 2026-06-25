---
name: scripts
description: "Skill for the Scripts area of Lab-builder. 12 symbols across 2 files."
---

# Scripts

12 symbols | 2 files | Cohesion: 100%

## When to Use

- Working with code in `scripts/`
- Understanding how parse_args, sha256, detect_databases work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `scripts/migrate_unify_db.py` | parse_args, sha256, detect_databases, get_table_info, do_migration (+2) |
| `scripts/audit_deps.py` | parse_args, extract_imports, check_deps, freeze_deps, main |

## Entry Points

Start here when exploring this area:

- **`parse_args`** (Function) — `scripts/migrate_unify_db.py:31`
- **`sha256`** (Function) — `scripts/migrate_unify_db.py:59`
- **`detect_databases`** (Function) — `scripts/migrate_unify_db.py:63`
- **`get_table_info`** (Function) — `scripts/migrate_unify_db.py:71`
- **`do_migration`** (Function) — `scripts/migrate_unify_db.py:82`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `parse_args` | Function | `scripts/migrate_unify_db.py` | 31 |
| `sha256` | Function | `scripts/migrate_unify_db.py` | 59 |
| `detect_databases` | Function | `scripts/migrate_unify_db.py` | 63 |
| `get_table_info` | Function | `scripts/migrate_unify_db.py` | 71 |
| `do_migration` | Function | `scripts/migrate_unify_db.py` | 82 |
| `do_restore` | Function | `scripts/migrate_unify_db.py` | 188 |
| `main` | Function | `scripts/migrate_unify_db.py` | 199 |
| `parse_args` | Function | `scripts/audit_deps.py` | 17 |
| `extract_imports` | Function | `scripts/audit_deps.py` | 49 |
| `check_deps` | Function | `scripts/audit_deps.py` | 76 |
| `freeze_deps` | Function | `scripts/audit_deps.py` | 119 |
| `main` | Function | `scripts/audit_deps.py` | 128 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Detect_databases` | intra_community | 3 |
| `Main → Get_table_info` | intra_community | 3 |
| `Main → Sha256` | intra_community | 3 |

## How to Explore

1. `context({name: "parse_args"})` — see callers and callees
2. `query({search_query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
4. `explain({target: "<file or symbol>"})` — persisted taint findings (source→sink data flows), when indexed with `--pdg`
