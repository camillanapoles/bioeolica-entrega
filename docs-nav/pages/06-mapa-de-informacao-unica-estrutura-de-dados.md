# Mapa de Informacao Unica - Estrutura de Dados

_Origem: `INSTRUCTIONS.md` linhas 335-357 - Parte 0 - KDI & Fundamentos_

## 📊 MAPA DE INFORMAÇÃO ÚNICA — ESTRUTURA DE DADOS

Para evitar **dados trocados**, crio estrutura de **Single Source of Truth**:

```json
{
  "project_id": "PRODUTO-[NOME]-[VERSAO]",
  "single_source_of_truth": {
    "materials_database": "/data/materials/master_db.json",
    "geometry_models": "/data/geometry/master_cad.step",
    "mesh_database": "/data/mesh/master_mesh.msh",
    "simulation_results": "/data/results/[timestamp]_[domain]_[version]/",
    "logs_index": "/data/logs/master_index.json",
    "knowledge_base": "/data/knowledge/rag_index.json",
    "validation_reports": "/data/vvv/reports/"
  },
  "data_versioning": "Git LFS + DVC",
  "access_control": "Read-only para dados brutos, append-only para logs"
}
```

---
