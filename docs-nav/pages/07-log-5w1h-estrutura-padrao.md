# Log 5W1H - Estrutura Padrao

_Origem: `INSTRUCTIONS.md` linhas 358-388 - Parte 0 - KDI & Fundamentos_

## 📝 LOG 5W1H — ESTRUTURA PADRÃO

Toda ação do agente deve gerar log com:

```json
{
  "log_id": "LOG-[UUID]",
  "timestamp": "2026-06-08T15:19:00Z",
  "task_id": "TASK-[UUID]",
  "5w1h": {
    "what": "Descrição exata da ação realizada",
    "why": "Justificativa técnica / objetivo",
    "who": "Agente / sub-agente responsável",
    "when": "Timestamp de início e fim",
    "where": "Arquivo, diretório, linha, versão",
    "how": "Método, ferramenta, parâmetros, versão da ferramenta"
  },
  "inputs": ["lista de arquivos/dados de entrada"],
  "outputs": ["lista de arquivos/dados de saída"],
  "validation": {
    "status": "PASS / FAIL / PENDING",
    "method": "Método de validação aplicado",
    "reference": "Referência normativa ou artigo"
  },
  "next_steps": ["ações subsequentes sugeridas"],
  "map_index": "Referência ao MAPA de informação única"
}
```

---
