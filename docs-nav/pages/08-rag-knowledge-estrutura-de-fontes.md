# RAG Knowledge - Estrutura de Fontes

_Origem: `INSTRUCTIONS.md` linhas 389-409 - Parte 0 - KDI & Fundamentos_

## 🔍 RAG KNOWLEDGE — ESTRUTURA DE FONTES

```json
{
  "knowledge_entry": {
    "source_type": "book | article | standard | thesis | repo | manual",
    "title": "Título completo",
    "authors": ["Lista de autores"],
    "year": 2026,
    "doi": "DOI ou URL",
    "file_path": "/data/knowledge/sources/[id].pdf",
    "rag_index": "Embedding index no vector DB",
    "applicability": ["Domínios onde se aplica"],
    "quality_score": "Nota de qualidade 0-10",
    "validation_status": "VERIFIED | PENDING | DISPUTED"
  }
}
```

---
