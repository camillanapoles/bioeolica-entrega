#!/usr/bin/env bash
# sanity-check.sh
# GATE 2 — Sanity Check: verifica se o contexto é fisicamente plausível
# Uso: ./sanity-check.sh <arquivo-contexto.json>
#
# Verifica ranges físicos para propriedades de materiais e cargas:
#   - Módulo de elasticidade (E) dentro de limites conhecidos
#   - Tensão de escoamento (sigma_y) dentro de limites conhecidos
#   - Densidade (rho) dentro de limites conhecidos
#   - Coeficiente de Poisson (nu) entre 0 e 0.5
#   - Cargas com magnitude positiva

set -euo pipefail

CONTEXT_FILE="${1:-}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Tabela de ranges físicos ──────────────────────────────────────────────
# Fonte: ASM Handbook, CES EduPack, MatWeb, literatura de engenharia
# Format: "class": [min_GPa, max_GPa]

declare -A E_RANGES
E_RANGES[Metal]="10 400"         # Chumbo 10GPa - Tungstênio 400GPa
E_RANGES[Polimero]="0.1 10"      # Borracha 0.1GPa - Nylon 10GPa
E_RANGES[Ceramica]="50 600"      # Concreto 50GPa - Diamante 600GPa
E_RANGES[Composito]="5 150"      # Madeira 5GPa - CFRP 150GPa
E_RANGES[Semicondutor]="50 200"  # Silício 130GPa
E_RANGES[Biomaterial]="0.1 30"   # Osso 10-30GPa
E_RANGES[Nanomaterial]="0.1 1000" # Nanotubos podem chegar a 1000GPa
E_RANGES[Liga]="10 400"          # Similar a metais
E_RANGES[Outro]="0.1 500"

declare -A SIGMAY_RANGES
SIGMAY_RANGES[Metal]="5 2000"         # Al puro 5MPa - Aços especiais 2000MPa
SIGMAY_RANGES[Polimero]="1 200"       # PEBD 1MPa - Poliimida 200MPa
SIGMAY_RANGES[Ceramica]="50 5000"     # Cerâmicas avançadas até 5GPa
SIGMAY_RANGES[Composito]="10 1000"    # Madeira 10MPa - CFRP 1000MPa
SIGMAY_RANGES[Semicondutor]="100 500"
SIGMAY_RANGES[Biomaterial]="1 300"
SIGMAY_RANGES[Nanomaterial]="10 5000"
SIGMAY_RANGES[Liga]="50 2000"
SIGMAY_RANGES[Outro]="1 1000"

declare -A RHO_RANGES
RHO_RANGES[Metal]="1500 22000"        # Mg 1740 - W 19300 kg/m3
RHO_RANGES[Polimero]="900 2200"       # PP 900 - PTFE 2200 kg/m3
RHO_RANGES[Ceramica]="1500 10000"     # SiO2 2650 - ZrO2 6000 kg/m3
RHO_RANGES[Composito]="100 2500"      # PVC foam 100 - GFRP 2500 kg/m3
RHO_RANGES[Semicondutor]="2000 6000"
RHO_RANGES[Biomaterial]="1000 3000"
RHO_RANGES[Nanomaterial]="500 5000"
RHO_RANGES[Liga]="1500 22000"
RHO_RANGES[Outro]="100 25000"

# ─── Validação ─────────────────────────────────────────────────────────────

if [ -z "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: informe o arquivo de contexto.${NC}"
    echo "Uso: ./sanity-check.sh <arquivo-contexto.json>"
    exit 1
fi

if [ ! -f "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
    exit 1
fi

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GATE 2 — SANITY CHECK (Plausibilidade Física)${NC}"
echo -e "${CYAN}  Arquivo: $CONTEXT_FILE${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ─── Verifica material ─────────────────────────────────────────────────────

MATERIAL_CLASS=$(jq -r '.class // empty' "$CONTEXT_FILE" 2>/dev/null)

if [ -n "$MATERIAL_CLASS" ] && [ "$MATERIAL_CLASS" != "null" ]; then
    echo -e "${YELLOW}Verificando material (classe: $MATERIAL_CLASS)...${NC}"

    # E (GPa)
    E_VALUE=$(jq -r '.E.value // empty' "$CONTEXT_FILE" 2>/dev/null)
    E_UNIT=$(jq -r '.E.unit // "Pa"' "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$E_VALUE" ] && [ "$E_VALUE" != "null" ]; then
        E_GPA=$(echo "$E_VALUE" | awk '{
            if ($1 ~ /^[0-9]+([.][0-9]+)?$/) print $1
            else print 0
        }')
        # Converte para GPa se necessário
        if echo "$E_UNIT" | grep -qi "pa"; then
            E_GPA=$(echo "$E_GPA / 1e9" | bc -l 2>/dev/null || echo "$E_GPA")
        fi
        RANGE="${E_RANGES[$MATERIAL_CLASS]:-0.1 500}"
        MIN=$(echo "$RANGE" | cut -d' ' -f1)
        MAX=$(echo "$RANGE" | cut -d' ' -f2)
        if [ "$(echo "$E_GPA < $MIN" | bc -l 2>/dev/null)" = "1" ] || [ "$(echo "$E_GPA > $MAX" | bc -l 2>/dev/null)" = "1" ]; then
            echo -e "  ${RED}✗${NC} E=$E_GPA GPa fora do range [$MIN, $MAX] GPa para $MATERIAL_CLASS"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✓${NC} E=$E_GPA GPa dentro do range [$MIN, $MAX] GPa"
        fi
    fi

    # sigma_y (MPa)
    SY_VALUE=$(jq -r '.sigma_y.value // empty' "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$SY_VALUE" ] && [ "$SY_VALUE" != "null" ]; then
        RANGE="${SIGMAY_RANGES[$MATERIAL_CLASS]:-1 1000}"
        MIN=$(echo "$RANGE" | cut -d' ' -f1)
        MAX=$(echo "$RANGE" | cut -d' ' -f2)
        if [ "$(echo "$SY_VALUE < $MIN" | bc -l 2>/dev/null)" = "1" ] || [ "$(echo "$SY_VALUE > $MAX" | bc -l 2>/dev/null)" = "1" ]; then
            echo -e "  ${RED}✗${NC} sigma_y=$SY_VALUE MPa fora do range [$MIN, $MAX] MPa para $MATERIAL_CLASS"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✓${NC} sigma_y=$SY_VALUE MPa dentro do range [$MIN, $MAX] MPa"
        fi
    fi

    # rho (kg/m3)
    RHO_VALUE=$(jq -r '.rho.value // empty' "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$RHO_VALUE" ] && [ "$RHO_VALUE" != "null" ]; then
        RANGE="${RHO_RANGES[$MATERIAL_CLASS]:-100 25000}"
        MIN=$(echo "$RANGE" | cut -d' ' -f1)
        MAX=$(echo "$RANGE" | cut -d' ' -f2)
        if [ "$(echo "$RHO_VALUE < $MIN" | bc -l 2>/dev/null)" = "1" ] || [ "$(echo "$RHO_VALUE > $MAX" | bc -l 2>/dev/null)" = "1" ]; then
            echo -e "  ${RED}✗${NC} rho=$RHO_VALUE kg/m3 fora do range [$MIN, $MAX] kg/m3 para $MATERIAL_CLASS"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✓${NC} rho=$RHO_VALUE kg/m3 dentro do range [$MIN, $MAX] kg/m3"
        fi
    fi

    # nu (Poisson)
    NU_VALUE=$(jq -r '.nu.value // empty' "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$NU_VALUE" ] && [ "$NU_VALUE" != "null" ]; then
        if [ "$(echo "$NU_VALUE < 0" | bc -l 2>/dev/null)" = "1" ] || [ "$(echo "$NU_VALUE > 0.5" | bc -l 2>/dev/null)" = "1" ]; then
            echo -e "  ${RED}✗${NC} nu=$NU_VALUE fora do range [0, 0.5]"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✓${NC} nu=$NU_VALUE dentro do range [0, 0.5]"
        fi
    fi
fi

# ─── Verifica carga ────────────────────────────────────────────────────────

CARGA_TYPE=$(jq -r '.type // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$CARGA_TYPE" ] && [ "$CARGA_TYPE" != "null" ]; then
    echo -e "${YELLOW}Verificando carga (tipo: $CARGA_TYPE)...${NC}"

    MAG_VALUE=$(jq -r '.magnitude.value // empty' "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$MAG_VALUE" ] && [ "$MAG_VALUE" != "null" ]; then
        if [ "$(echo "$MAG_VALUE <= 0" | bc -l 2>/dev/null)" = "1" ]; then
            echo -e "  ${RED}✗${NC} magnitude=$MAG_VALUE deve ser positiva"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✓${NC} magnitude=$MAG_VALUE positiva"
        fi
    fi
fi

# ─── Verifica simulação ────────────────────────────────────────────────────

VVV_STATUS=$(jq -r '.vvv_status // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$VVV_STATUS" ] && [ "$VVV_STATUS" != "null" ]; then
    echo -e "${YELLOW}Verificando simulação...${NC}"
    case "$VVV_STATUS" in
        PASS|FAIL|PENDING)
            echo -e "  ${GREEN}✓${NC} vvv_status=$VVV_STATUS válido"
            ;;
        *)
            echo -e "  ${RED}✗${NC} vvv_status=$VVV_STATUS inválido (deve ser PASS/FAIL/PENDING)"
            ERRORS=$((ERRORS + 1))
            ;;
    esac
fi

# ─── Resultado ─────────────────────────────────────────────────────────────

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  SANITY PASS — todos os valores fisicamente plausíveis${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}  $WARNINGS aviso(s) — revisar recommendado${NC}"
    fi
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  SANITY FAIL — $ERRORS erro(s) de plausibilidade física${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    exit 1
fi
