# Relatorio CRSLR - Lab2 Gerador Eolico Savonius

**Fase:** F8 (Lab2)
**Data:** 2026-06-26
**Heranca:** Estreitamente acoplado a Lab1 (material da pa). Ver Lab1 para contexto material.

## CONTEXTO
Gerador Savonius D=1.0m H=1.5m, pa em compasito PM+15%grafite (Lab1), PMG Ke=2.0 R=1.5ohm.

## RESULTADOS (validados em runtime)
| Vento | P_disponivel | P_turbina | P_saida_eletrica |
|-------|-------------|-----------|------------------|
| 3 m/s | 24.81 W | 6.20 W | ~3 W |
| 5 m/s | 114.84 W | 28.71 W | ~22 W |
| **8 m/s** | **470.40 W** | **117.60 W** | **82.95 W** ✓ |
| 10 m/s | 918.75 W | 229.69 W | ~180 W |

@8m/s: omega=12.80 rad/s (122 RPM), torque=9.19 Nm. Atende alvo >=80W.

## SINTESE
Cp=0.25 conservador (vs limite Betz 0.593). Eficiencia total ~17% (multiplicacao Cp*eta_mec*eta_PMG*eta_reg). Savonius nao compete com HAWT em eficiencia, mas ganha em simplicidade/baixo custo/manutencao para comunidades.

## LIMITACOES
L1: Cp(λ) gaussiano, nao CFD. L2: sem tunel de vento. L3: PMG modelo lumped, nao FEM magnetico.

## RECOMENDACOES
1. Validar Cp em tunel de vento ou campo.
2. Substituir por CFD OpenFOAM.
3. Otimizar N espiras PMG (DOE).

## REVISAO HOSTIL
Cp_max=0.25 conservador - bom. P_saida=82.95W dentro de alvo mas sem margem - risco se Cp real <0.25. Mitigacao: tsr=0.8 bem caracterizado para Savonius. Aprovado condicional.
