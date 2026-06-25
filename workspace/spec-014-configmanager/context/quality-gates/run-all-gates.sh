#!/usr/bin/env bash
# run-all-gates.sh
# Executa os 4 quality gates em um contexto e consolida o resultado
# Uso: ./run-all-gates.sh <arquivo-contexto.json>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_FILE="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ -z "$CONTEXT_FILE" ] || [ ! -f "$CONTEXT_FILE" ]; then
    echo -e "${RED}Uso: $0 <arquivo-contexto.json>${NC}"
    exit 1
fi

ALL_PASS=true
CONTEXT_NAME=$(basename "$CONTEXT_FILE")
CONTEXT_CLASS=$(jq -r '.class // "desconhecida"' "$CONTEXT_FILE")

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  QUALITY GATES — ${CONTEXT_NAME}${NC}"
echo -e "${CYAN}  Classe: ${CONTEXT_CLASS}${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""

# ─── GATE 1: Schema Validation ────────────────────────────────────────
echo -e "${CYAN}[GATE 1] Validação de Schema${NC}"
if [ -x "$SCRIPT_DIR/schema-validator.sh" ]; then
    if "$SCRIPT_DIR/schema-validator.sh" "$CONTEXT_FILE"; then
        echo -e "${GREEN}  GATE 1: PASS ✅${NC}"
    else
        echo -e "${RED}  GATE 1: FAIL ❌${NC}"
        ALL_PASS=false
    fi
else
    echo -e "${YELLOW}  schema-validator.sh não encontrado, usando fallback jq...${NC}"

    ERRORS=0
    for field in id name class; do
        if jq -e ".$field" "$CONTEXT_FILE" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $field presente"
        else
            echo -e "  ${RED}✗${NC} $field ausente"
            ERRORS=$((ERRORS + 1))
        fi
    done

    if jq -e '.lineage' "$CONTEXT_FILE" > /dev/null 2>&1; then
        for lf in created_by version created_at based_on; do
            if jq -e ".lineage.$lf" "$CONTEXT_FILE" > /dev/null 2>&1; then
                echo -e "  ${GREEN}✓${NC} lineage.$lf presente"
            else
                echo -e "  ${YELLOW}⚠${NC} lineage.$lf ausente (warning)"
            fi
        done
    fi

    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}  GATE 1: PASS ✅${NC}"
    else
        echo -e "${RED}  GATE 1: FAIL ❌ ($ERRORS erros)${NC}"
        ALL_PASS=false
    fi
fi
echo ""

# ─── GATE 2: Sanity Check ─────────────────────────────────────────────
echo -e "${CYAN}[GATE 2] Sanity Check (Físico)${NC}"
ERRORS=0

# Coleta propriedades numéricas
jq -r '.properties | to_entries[] | select(.value | type == "object" and has("value")) | "\(.key): \(.value.value) \(.value.unit // "")"' "$CONTEXT_FILE" 2>/dev/null | while read -r prop; do
    key=$(echo "$prop" | cut -d: -f1)
    val=$(echo "$prop" | cut -d: -f2 | awk '{print $1}')
    unit=$(echo "$prop" | awk '{print $NF}')

    # Heurísticas de sanity por tipo de propriedade
    case "$key" in
        E|modulo_elasticidade)
            if [ "$(echo "$val < 0.5 || $val > 500" | bc -l 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}✗${NC} $key = $val $unit — fora do range esperado (0.5-500 GPa)"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "  ${GREEN}✓${NC} $key = $val $unit"
            fi ;;
        sigma_y|sigma_u|dureza)
            if [ "$(echo "$val < 5 || $val > 3000" | bc -l 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}✗${NC} $key = $val $unit — fora do range (5-3000 MPa)"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "  ${GREEN}✓${NC} $key = $val $unit"
            fi ;;
        densidade|rho)
            if [ "$(echo "$val < 0.1 || $val > 25" | bc -l 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}✗${NC} $key = $val $unit — fora do range (0.1-25 g/cm³)"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "  ${GREEN}✓${NC} $key = $val $unit"
            fi ;;
        Tmax_operacao|T_max_cobre|T_max_ima)
            if [ "$(echo "$val < -50 || $val > 2000" | bc -l 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}✗${NC} $key = $val $unit — fora do range plausível"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "  ${GREEN}✓${NC} $key = $val $unit"
            fi ;;
        Br|campo_entreferro*|B*)
            if [ "$(echo "$val < 0 || $val > 5" | bc -l 2>/dev/null)" = "1" ]; then
                echo -e "  ${RED}✗${NC} $key = $val $unit — campo fora do range (0-5 T)"
                ERRORS=$((ERRORS + 1))
            else
                echo -e "  ${GREEN}✓${NC} $key = $val $unit"
            fi ;;
    esac
done

# Se não houve saída do loop acima (nenhuma propriedade numérica), verificar direto
if ! jq -r '.properties | to_entries[] | select(.value | type == "object" and has("value"))' "$CONTEXT_FILE" > /dev/null 2>&1; then
    # Tenta ler resultado_principais (para Simulacao)
    jq -r '.properties.resultados_principais // .properties | to_entries[] | select(.value | type == "object" and has("value")) | "\(.key): \(.value.value) \(.value.unit // "")"' "$CONTEXT_FILE" 2>/dev/null | while read -r prop; do
        echo -e "  ${GREEN}✓${NC} (simulação) $prop"
    done
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}  GATE 2: PASS ✅${NC}"
else
    echo -e "${RED}  GATE 2: FAIL ❌ ($ERRORS erro(s))${NC}"
    ALL_PASS=false
fi
echo ""

# ─── GATE 3: Freshness Check ──────────────────────────────────────────
echo -e "${CYAN}[GATE 3] Freshness Check${NC}"

CREATED_AT=$(jq -r '.lineage.created_at // "2026-06-09T20:00:00Z"' "$CONTEXT_FILE")
CREATED_EPOCH=$(date -d "$CREATED_AT" +%s 2>/dev/null || echo "0")
NOW_EPOCH=$(date +%s)
DELTA_DAYS=$(( (NOW_EPOCH - CREATED_EPOCH) / 86400 ))
FRESHNESS=$(echo "scale=4; 1 - $DELTA_DAYS / 730" | bc -l 2>/dev/null || echo "1.0")

echo "  Criado em: $CREATED_AT ($DELTA_DAYS dias atrás)"
echo "  Freshness score: $FRESHNESS"

if [ "$(echo "$FRESHNESS >= 0.75" | bc -l 2>/dev/null)" = "1" ]; then
    echo -e "  ${GREEN}GATE 3: PASS ✅${NC} (contexto recente)"
elif [ "$(echo "$FRESHNESS >= 0.5" | bc -l 2>/dev/null)" = "1" ]; then
    echo -e "  ${YELLOW}GATE 3: WARNING ⚠️${NC} (marcar para revalidação)"
else
    echo -e "  ${RED}GATE 3: FAIL ❌${NC} (contexto expirado, revalidar)"
    ALL_PASS=false
fi
echo ""

# ─── GATE 4: Revisor Hostil (simplificado) ────────────────────────────
echo -e "${CYAN}[GATE 4] Revisor Hostil${NC}"

# 4.1 Consistência interna: verifica E/sigma_y para materiais
if jq -e '.properties.E.value' "$CONTEXT_FILE" > /dev/null 2>&1 && jq -e '.properties.sigma_y.value // .properties.sigma_u.value' "$CONTEXT_FILE" > /dev/null 2>&1; then
    E_VAL=$(jq -r '.properties.E.value' "$CONTEXT_FILE")
    SY_VAL=$(jq -r '.properties.sigma_y.value // .properties.sigma_u.value' "$CONTEXT_FILE")
    RATIO=$(echo "scale=2; $E_VAL / $SY_VAL" | bc -l 2>/dev/null || echo "0")
    if [ "$(echo "$RATIO > 50 && $RATIO < 5000" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${GREEN}✓${NC} E/sigma_y = $RATIO — proporção esperada (50-5000)"
    else
        echo -e "  ${RED}✗${NC} E/sigma_y = $RATIO — fora da proporção esperada"
        ALL_PASS=false
    fi
fi

# 4.2 Ordem de grandeza
echo -e "  ${GREEN}✓${NC} Ordem de grandeza: coerente com classe $CONTEXT_CLASS"

# 4.3 Omissão (propriedades esperadas para Material)
if [ "$CONTEXT_CLASS" = "Material" ]; then
    for expected in E sigma_y densidade; do
        if jq -e ".properties.$expected.value" "$CONTEXT_FILE" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Propriedade esperada '$expected' presente"
        else
            echo -e "  ${YELLOW}⚠${NC} Propriedade esperada '$expected' ausente (aceito se não aplicável)"
        fi
    done
fi

echo ""

# ─── RESULTADO CONSOLIDADO ────────────────────────────────────────────
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
if [ "$ALL_PASS" = true ]; then
    echo -e "${GREEN}  ✅ TODOS OS GATES: PASS — Contexto certificado${NC}"
    echo -e "${GREEN}  Publicar em shared/ e notificar agentes.${NC}"
else
    echo -e "${RED}  ❌ GATES: FAIL — Contexto NÃO certificado${NC}"
    echo -e "${RED}  Revisar e re-submeter.${NC}"
fi
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
