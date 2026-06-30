# AGENTS.md — Projeto Bioeólica / AgriFam-ICT 2026

## Visão Geral do Projeto

Este projeto é um repositório de análise documental voltado à preparação de propostas para a **Chamada Pública MCTI/FINEP/FNDCT — Cadeias Socioprodutivas da Agricultura Familiar e Sistemas Agroalimentares Sustentáveis para ICTs 2026** (também conhecida como **AgriFam-ICT 2026**).

O objetivo principal é reunir, organizar e analisar minuciosamente todos os documentos do edital para subsidiar a construção de uma proposta de projeto científico-tecnológico. Não há código-fonte de aplicação neste repositório; o trabalho consiste em leitura crítica, indexação de informações e produção de documentação derivada a partir dos anexos oficiais.

## Estrutura de Diretórios

```
./
├── AGENTS.md                     # Este arquivo
├── edital/                       # Documentos oficiais da chamada pública (PDF e ODT)
│   ├── urls.txt                  # URLs de download dos documentos no site da FINEP
│   └── ...                       # 29 arquivos (editais, anexos, comunicados, apresentações)
├── metodologia/
│   ├── REGRAS_DE_GOVERNANCA.md  # Constituição do projeto: SSOT, hierarquia, padrões de citação
│   └── CHECKLISTS.md             # Checklists de qualidade e conformidade
├── extracao/
│   ├── 2026-06-06/               # Texto extraído dos PDFs retificados (data da extração)
│   │   ├── COM_RET.txt           # Comunicado de Rerratificação
│   │   ├── EDITAL_RET.txt        # Edital retificado
│   │   ├── ANEXO1_RET.txt ... ANEXO7_RET.txt
│   │   └── GUIA_FAP.txt          # Telas FAP e Número de Caracteres
│   └── latest -> 2026-06-06      # Link simbólico para a extração mais recente
├── analise/
│   ├── indice_tematico.md        # Índice mestre com mapa de temas e referências
│   ├── elegibilidade.md          # Regras de elegibilidade institucional
│   ├── linhas_tematicas.md       # Análise das 4 linhas e aderência do projeto Bioeólica
│   ├── orcamento.md              # Regras orçamentárias, limites e documentação
│   ├── cronograma.md             # Prazos, deadlines e alertas temporais
│   ├── checklist.md              # Checklist de conformidade pré-submissão
│   └── inconsistencias.md        # Pendências, riscos e itens a resolver
├── proposta/                     # Documentos da proposta em elaboração (futuro)
└── .venv/                        # Ambiente virtual Python 3.11 (criado com uv, vazio)
```

## Documentos em `edital/`

### Hierarquia e Status dos Documentos

A fonte de verdade única é a versão **retificada** do edital. Os documentos originais de 25/03/2026 estão presentes apenas para referência histórica e **não devem ser usados** como base para a construção da proposta, pois foram alterados pela rerratificação.

| Documento | Versão Válida | Observação |
|-----------|---------------|------------|
| Edital AgriFam-ICT 2026 Rerratificação | ✅ Sim | Documento-base vigente |
| Comunicado AgriFam-ICT 2026 Rerratificacao | ✅ Sim | Alterações pontuais ao edital |
| Anexo 1 — Minuta Padrão de Convênio | ✅ Sim | Modelo contratual |
| Anexo 2 — Detalhamento das Linhas Temáticas | ✅ Sim | Requisitos técnicos das 4 linhas |
| Anexo 3 — Exigências para Avaliação dos Itens de Orçamento | ✅ Sim | Regras orçamentárias |
| Anexo 4 — Projeto Resumido de Obras | ✅ Sim | Modelo para obras |
| Anexo 5 — Tabela Pagamento de Pessoal | ✅ Sim | Planilha de pessoal |
| Anexo 6 — Orientações para Despesas Relativas a Bolsas | ✅ Sim | Regras de bolsas |
| Anexo 7 — Checklist Preventivo | ✅ Sim | Verificação pré-submissão |
| 09_04_2026_Telas_FAP_e_Numero_de_Caracteres | ✅ Sim | Guia de preenchimento do sistema FAP |
| Editais e anexos de 25/03/2026 | ❌ Não | Versão original, superseded |

**Regra de ouro:** sempre consultar primeiro a rerratificação e seus anexos. Quando houver conflito, a rerratificação prevalece sobre o edital original.

### Formato dos Documentos

Cada documento está disponível em duas versões idênticas em conteúdo:
- **PDF**: melhor para leitura estruturada e extração de texto via `pdftotext`
- **ODT/ODP**: melhor para edição e extração de tabelas

### URLs Oficiais

O arquivo `edital/urls.txt` contém os 29 links de download direto do portal da FINEP (`finep.gov.br`). Esses links são a fonte primária caso seja necessário verificar a autenticidade ou baixar versões atualizadas.

## Tecnologia e Ferramentas

### Ambiente Python

- **Gerenciador de pacotes:** `uv` (versão 0.11.17)
- **Versão do Python:** 3.11.14 (CPython)
- **Ambiente virtual:** `.venv/` (include-system-site-packages = false)
- **Estado atual:** ambiente vazio, sem pacotes instalados

### Ativação do Ambiente

```bash
source .venv/bin/activate
```

### Ferramentas Disponíveis no Sistema

- `python3` (3.12.3 global)
- `pdftotext` (para extração de texto de PDFs)
- `uv` (para gerenciamento de pacotes Python)

## Convenções de Trabalho

### Análise Documental

1. **Fonte única de informação:** para evitar dados desatualizados, use apenas a versão retificada do edital e seus anexos.
2. **Atenção à hierarquia:** o edital estabelece regras gerais; os anexos detalham exigências específicas. Sempre correlacione ambos.
3. **Rerratificações e erratas:** o comunicado de rerratificação alterou itens cruciais (ex.: limite de propostas por ICT, definição de "entidade", regras de equipamentos de pequeno porte). Leia-o integralmente antes de qualquer outro documento.
4. **Memória indexada:** ao analisar os documentos, construa índices por tema (ex.: orçamento, linhas temáticas, cronograma, elegibilidade) para consulta rápida futura.
5. **Cada linha é relevante:** editais de fomento têm informações críticas em parágrafos aparentemente secundários. Analise o texto integralmente.

### Linhas Temáticas da Chamada

A chamada contempla 4 linhas temáticas:
1. **Bioinsumos**
2. **Sistemas de produção agroecológicos e orgânicos**
3. **Soluções digitais para a pequena propriedade rural**
4. **Aquicultura de espécies nativas**

Cada linha tem requisitos específicos detalhados no Anexo 2 (versão retificada).

## Limitações e Considerações

- **Sem código-fonte:** este não é um projeto de desenvolvimento de software. Não há testes automatizados, pipelines de CI/CD ou processo de deploy.
- **Sem dependências Python instaladas:** se for necessário usar bibliotecas (ex.: `PyPDF2`, `python-docx`, `pandas` para análise de tabelas), instale-as no `.venv` via `uv pip install <pacote>`.
- **Idioma:** todos os documentos oficiais e a produção derivada devem estar em **português brasileiro**.
- **Confidencialidade:** os documentos são públicos (edital de chamada pública), mas a proposta em elaboração pode conter informações sensíveis. Trate o conteúdo derivado com o nível de sigilo apropriado.

## Checklist para Novas Sessões

- [ ] Confirmar que está usando a versão retificada do edital e seus anexos
- [ ] Ler o Comunicado de Rerratificação antes dos demais documentos
- [ ] Verificar se há novos documentos em `edital/` não analisados
- [ ] Ao usar RAG ou memória indexada, indexar por tema e número de item do edital
- [ ] Registrar a fonte exata (documento, página, item) de qualquer informação extraída
