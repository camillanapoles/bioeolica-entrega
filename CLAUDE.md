PRIMEIRAMENTE SAIBA QUE ESTA PRODUZINDO ORQUESTRAMENTO AGENTIC QUE PRODUZ LABORORATORIOS CIENTIFICO ATRAVENS DE WORKFLOW CONTFORME DOCUMENTO @./INSTRUCTIONS.md


A ESTRUTURA DE BASR DE ORQUESTRAVAO ESTA ABAIXO

```
├── knowledge
│		 ├── materials
│		 ├── wind-energy
│		 ├── llm.pdf
│		 ├── RESEARCH_DECISIONS.md
│		 └── T069_FINAL_AUDIT.md
├── modules
│		 ├── ai_assist_cad
│		 ├── cad-cae-platform
│		 ├── kdi-m3-bridge
│		 ├── MathematicalEngineeringDeepLearning
│		 ├── modules
│		 ├── physics-m3
│		 └── demo_integrada.py
├── scripts
│		 ├── agentic
│		 ├── compliance
│		 ├── audit_deps.py
│		 ├── generate_gitnexus_report.py
│		 ├── migrate_unify_db.py
│		 └── run_full_pipeline.py
├── workspace
│		 ├── spec-014-configmanager
│		 ├── template
│		 └── README.md
├── CLAUDE.md
├── CONVENTIONS.md
├── DOC1-KDI_MECH-ELECTRO-MATERIALS.md
├── DOC2-KAIZEN.md
├── INSTRUCTIONS.md
```

## CONTEXTO DE ORQUESTRACAO

ENTENDA:
1. ORQUESTRACAO GUIADA POR @./INSTRUCTIONS.md
2. DOC1 E DOC2 MENCIONADOS em @INSTRUCTIONS
E USADOS DE BASE PARA KDI SAO @./DOC1-KDI_MECH-ELECTRO-MATERIALS.md E @./DOC2-KAIZEN.md

## REGRAS DE GOVERNANCA

O LABORATORIO DEVE TEM FSM [STATE MACHINE] A COMECAR PELO NOME DO LAB EM STATE E ESTASO 
└─ NENHUM LAB PODE SER CRIADO SEM SER VIA DOKICITACAO DO USUARIO E SEM PASSAR POR FSM DE ORQUESTRACAO
└─ SO E SOMENTE SE CRIARA LABORATORIO ATRAVES DE DOC @./INPUT.md ➞ con5endo ibstrucoes inciciais a ser aprimentora e construida ➞ onde addim que projeto e criado INPUT.md eh movido pro projeto
└─ o PROJETO CRIAFO DO LAVORATORIO DEVE TER UM README.md COM O NOME DO LAB E O LINK PARA O DOC @./INPUT.md (INPUT.md pra .memory do laboratio)
└─ O LAVORSTORIO JA TEM TEMPLATE 
└─ SCRIOT COBSTA MODULOS UTEIS DE ORQUESTRACAO 
└─ o lab deve ser criado no local ./workspace/[NOME_DO_LAB] e deve conter

## GARANTA FSM GESTAO D3 VVV E FACT CHECK + ENTREGAVEIS CONFORME SOLICITADO PELO LAB




