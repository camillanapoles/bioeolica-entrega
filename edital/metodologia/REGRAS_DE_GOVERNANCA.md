# REGRAS DE GOVERNANÇA — Projeto Bioeólica / AgriFam-ICT 2026

> **Status:** Vigente desde a sessão inicial
> **Última atualização:** 2026-06-06
> **Responsável:** Agente de análise documental

---

## 1. PRINCÍPIO FUNDAMENTAL: FONTE ÚNICA DE VERDADE (SSOT)

| Camada | Localização | Regra |
|--------|-------------|-------|
| **Fonte Primária** | `./edital/` | APENAS LEITURA. Nunca editar, renomear ou mover. |
| **Extração Bruta** | `./extracao/` | Texto extraído 1:1 dos PDFs retificados. Versionado por data. |
| **Análise Derivada** | `./analise/` | Interpretações, resumos, índices. SEMPRE citar fonte exata. |
| **Proposta** | `./proposta/` | Documentos de submissão. Cada afirmação deve ter referência em `./analise/` |

**Regra de ouro:** Se uma informação não pode ser rastreada até `./edital/[documento retificado]`, ela é considerada **não confirmada**.

---

## 2. HIERARQUIA DOCUMENTAL VIGENTE

```
NÍVEL 1 (mais alto): Comunicado AgriFam-ICT 2026 Rerratificacao
NÍVEL 2: Edital AgriFam-ICT 2026 Rerratificação
NÍVEL 3: Anexos 1–7 (versão retificada)
NÍVEL 4: Telas FAP e Número de Caracteres
NÍVEL 5 (referência apenas): Documentos de 25/03/2026 (ORIGINAIS, SUPERSSEDED)
```

- Em caso de **conflito**, o documento de **nível mais alto** prevalece.
- Nunca usar documentos do NÍVEL 5 para decisões de proposta.

---

## 3. PADRÃO DE CITAÇÃO E TRAZABILIDADE

Toda informação extraída ou inferida DEVE ser registrada com:

```
[FONTE: <nome_curto_do_documento> | Página: <N> | Seção/Item: <X.Y>]
```

**Nomenclatura curta dos documentos (oficial):**

| Documento Completo | Nome Curto |
|--------------------|------------|
| `Edital AgriFam-ICT 2026 Rerratificação.pdf` | `EDITAL_RET` |
| `Comunicado AgriFam-ICT 2026 Rerratificacao.pdf` | `COM_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 1 - Minuta Padrão de Convênio.pdf` | `ANEXO1_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 2 -Detalhamento das Linhas Temáticas.pdf` | `ANEXO2_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 3 - Exigências para Avaliação dos Itens de Orçamento.pdf` | `ANEXO3_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 4 - Projeto Resumido de Obras.pdf` | `ANEXO4_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 5 - Tabela Pagamento de Pessoal.pdf` | `ANEXO5_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 6 - Orientações para Despesas Relativas a Bolsas.pdf` | `ANEXO6_RET` |
| `Edital AgriFam-ICT 2026 Rerratificação - Anexo 7 - Checklist Preventivo.pdf` | `ANEXO7_RET` |
| `09_04_2026_Telas_FAP_e_Numero_de_Caracteres.pdf` | `GUIA_FAP` |

**Exemplo de citação válida:**
```
O limite de propostas por ICT é de 3 (três). [FONTE: COM_RET | Página: 2 | Item: 3.1]
```

---

## 4. ESTRUTURA DE DIRETÓRIOS

```

├── edital/              # Fonte primária — SÓ LEITURA
├── extracao/
│   ├── YYYY-MM-DD/      # Texto extraído na data
│   └── latest -> link para última extração
├── analise/
│   ├── indice_tematico.md
│   ├── elegibilidade.md
│   ├── linhas_tematicas.md
│   ├── orcamento.md
│   ├── cronograma.md
│   └── inconsistencias.md
├── proposta/
│   └── (documentos de submissão)
├── metodologia/
│   ├── REGRAS_DE_GOVERNANCA.md   # Este arquivo
│   └── CHECKLISTS.md
└── AGENTS.md
```

---

## 5. REGRAS DE CONTINUIDADE ENTRE SESSÕES

1. **Sempre ler este arquivo antes de qualquer ação.**
2. **Sempre verificar se há novos documentos em `./edital/`** não mapeados.
3. **Sempre usar o `TODO` do agente** para manter estado de trabalho visível.
4. **Nunca assumir que uma informação de sessões anteriores está correta** sem revalidar na fonte.
5. **Data de extração:** ao extrair texto de PDF, registrar a data no diretório para saber se houve retrabalho.

---

## 6. CHECKLIST DE QUALIDADE (antes de qualquer entrega)

- [ ] Toda afirmação numérica (valores, datas, limites) tem citação de fonte?
- [ ] A fonte citada é da versão **retificada** (não da original de 25/03)?
- [ ] Houve validação cruzada entre edital e anexo correspondente?
- [ ] Há risco de interpretação ambígua? Se sim, foi sinalizado com `[INTERPRETAÇÃO]`?
- [ ] Informações sensíveis da proposta estão tratadas com sigilo adequado?

---

## 7. FERRAMENTAS E SKILLS AUTORIZADAS

| Tipo | Ferramenta | Uso |
|------|------------|-----|
| Extração de PDF | `pdftotext` | Extração 1:1 de texto para arquivo `.txt` |
| Extração estruturada | Python + `PyPDF2` / `pdfplumber` | Tabelas, metadados, paginação |
| Análise textual | Python + processamento de texto | Contagem de caracteres, busca, indexação |
| Busca e grep | `ripgrep` (via ferramenta Grep) | Localização rápida de termos |
| Organização | Markdown estruturado | Documentação e análise |

---

## 8. DEFINIÇÃO DE "PRONTO" (DONE)

Uma tarefa de análise documental só está **pronta** quando:
1. O texto foi extraído e verificado quanto a perda de conteúdo
2. As informações relevantes foram transcritas para `./analise/` com citações
3. Foi feita validação cruzada com o documento hierarquicamente superior
4. Não há flags de `[INCONSISTÊNCIA]` ou `[PENDENTE]` sem justificativa

---

*Este documento é a constituição do projeto. Qualquer alteração deve ser registrada aqui e propagada para AGENTS.md.*
