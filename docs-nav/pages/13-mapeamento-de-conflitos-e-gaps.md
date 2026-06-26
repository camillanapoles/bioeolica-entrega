# Mapeamento de Conflitos e Gaps

_Origem: `INSTRUCTIONS.md` linhas 530-546 - Parte I - Conexao Omnibus v3.0 (Engine + KDI Integrado)_

## 🎯 MAPEAMENTO DE CONFLITOS E GAPS

| Aspecto | Doc 1 (Engine v3.0) | Doc 2 (KDI v2.0) | Gap / Conflito |
|---------|---------------------|------------------|----------------|
| **Versão** | v3.0 (omnibus-unified) | v1.0 → v2.0 (omnibus) | Doc 2 precisa upgrade para v3.0 |
| **Métodos Numéricos** | MPM, SPH, DEM, Peridynamics integrados | FEM, FVM, FDM, BEM, IGA, SPH, DEM, ROM, PINNs | Doc 1 tem MPM que Doc 2 não tinha |
| **Metodologia M³** | Macro-Meso-Micro em todos os 10 domínios | Macro-Meso-Micro como função Python | ✅ Alinhado |
| **Ferramentas** | Open source first (CalculiX, OpenFOAM, etc.) | Mistura com comerciais (ANSYS, ABAQUS) | Doc 2 precisa purgar comerciais |
| **Mandatos** | 7 mandatos como processos executáveis (M1-M7) | 7 mandatos como checklist (M1-M7) | Doc 1 tem processos, Doc 2 tem checklist |
| **Fluxo** | 7 fases (F1-F7) com triggers/inputs/outputs | 7 fases como funções Python | ✅ Alinhado, Doc 1 mais estruturado |
| **Métricas** | 10 dimensões (D1-D10) com métricas mensuráveis | 10 dimensões como tabela | ✅ Alinhado |
| **WAL** | Protocolo completo com patches cirúrgicos | Log 5W1H estruturado | Doc 1 tem patches, Doc 2 tem estrutura básica |
| **Auto-instrução** | Implícita na filosofia | "THE WAY BY CONTENT" explícito | Doc 2 tem auto-instrução mais detalhada |
| **KDI Identity** | "Revisor Hostil Autônomo Investigador" | "Engenheiro Cientista Multidisciplinar" | Doc 1 tem identidade mais forte |

---
