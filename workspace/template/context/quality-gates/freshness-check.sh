#!/usr/bin/env bash
# freshness-check.sh
# GATE 3 — Freshness Check: verifica se o contexto ainda é válido temporalmente
# Uso: ./freshness-check.sh <arquivo-contexto.json>
#
# Política de Freshness:
#   - < 12 meses: PASS (score 0.95)
#   - 12-24 meses: WARNING (marcar para revalidação)
#   - > 24 meses: FAIL (exigir revalidação antes de publicar)
#   - Se freshness_score explícito no JSON, usar esse no lugar

set -euo pipefail

CONTEXT_FILE="${1:-}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

RECENT_MONTHS=12
EXPIRY_MONTHS=24

# ─── Validação ─────────────────────────────────────────────────────────────

if [ -z "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: informe o arquivo de contexto.${NC}"
    echo "Uso: ./freshness-check.sh <arquivo-contexto.json>"
    exit 1
fi

if [ ! -f "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
    exit 1
fi

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GATE 3 — FRESHNESS CHECK${NC}"
echo -e "${CYAN}  Arquivo: $CONTEXT_FILE${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Obtém data de criação ────────────────────────────────────────────────

CREATED_AT=$(jq -r '.lineage.created_at // .created_at // empty' "$CONTEXT_FILE" 2>/dev/null)
FRESHNESS_SCORE=$(jq -r '.lineage.freshness_score // .freshness_score // empty' "$CONTEXT_FILE" 2>/dev/null)

# Se freshness_score explícito existe, usa ele
if [ -n "$FRESHNESS_SCORE" ] && [ "$FRESHNESS_SCORE" != "null" ]; then
    echo -e "${YELLOW}Freshness score explícito encontrado: $FRESHNESS_SCORE${NC}"
    if [ "$(echo "$FRESHNESS_SCORE < 0.3" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${RED}✗ FAIL — freshness_score=$FRESHNESS_SCORE abaixo de 0.3${NC}"
        echo -e "  ${YELLOW}  Ação: revalidar contexto antes de publicar${NC}"
        exit 1
    elif [ "$(echo "$FRESHNESS_SCORE < 0.6" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${YELLOW}⚠ WARNING — freshness_score=$FRESHNESS_SCORE abaixo de 0.6${NC}"
        echo -e "  ${YELLOW}  Ação: marcar para revalidação opcional${NC}"
        exit 0
    else
        echo -e "  ${GREEN}✓ PASS — freshness_score=$FRESHNESS_SCORE adequado${NC}"
        exit 0
    fi
fi

# ─── Se não tem freshness_score, calcula pela data ─────────────────────────

if [ -z "$CREATED_AT" ] || [ "$CREATED_AT" = "null" ]; then
    echo -e "${YELLOW}⚠ Sem data de criação. Usando data do arquivo...${NC}"
    CREATED_AT=$(stat -c '%Y' "$CONTEXT_FILE" 2>/dev/null)
    CREATED_AT=$(date -d "@$CREATED_AT" +%Y-%m-%d 2>/dev/null || echo "")
fi

if [ -z "$CREATED_AT" ]; then
    echo -e "${RED}✗ FAIL — não foi possível determinar a data de criação${NC}"
    echo -e "${YELLOW}  Ação: adicionar lineage.created_at ou created_at ao JSON${NC}"
    exit 1
fi

echo -e "${YELLOW}Data de criação: $CREATED_AT${NC}"

# ─── Calcula idade em meses ───────────────────────────────────────────────

CREATED_EPOCH=$(date -d "$CREATED_AT" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(date +%s)
AGE_SECONDS=$((NOW_EPOCH - CREATED_EPOCH))
AGE_MONTHS=$((AGE_SECONDS / 2592000))  # ~30 dias por mês

echo -e "${YELLOW}Idade: $AGE_MONTHS meses${NC}"

# ─── Aplica política de freshness ─────────────────────────────────────────

echo ""
if [ $AGE_MONTHS -lt $RECENT_MONTHS ]; then
    FRESHNESS=$(echo "scale=2; 1.0 - ($AGE_MONTHS / $RECENT_MONTHS) * 0.05" | bc -l 2>/dev/null || echo "0.95")
    echo -e "${GREEN}✓ PASS — contexto atualizado ($AGE_MONTHS meses < $RECENT_MONTHS meses)${NC}"
    echo -e "  Freshness score: ~$FRESHNESS"
    exit 0
elif [ $AGE_MONTHS -lt $EXPIRY_MONTHS ]; then
    FRESHNESS=$(echo "scale=2; 0.95 - (($AGE_MONTHS - $RECENT_MONTHS) / ($EXPIRY_MONTHS - $RECENT_MONTHS)) * 0.65" | bc -l 2>/dev/null || echo "0.30")
    echo -e "${YELLOW}⚠ WARNING — contexto envelhecendo ($AGE_MONTHS meses)${NC}"
    echo -e "  Freshness score: ~$FRESHNESS"
    echo -e "  Ação: marcar para revalidação"
    exit 0
else
    FRESHNESS=$(echo "scale=2; 0.30 - (($AGE_MONTHS - $EXPIRY_MONTHS) / $EXPIRY_MONTHS) * 0.30" | bc -l 2>/dev/null || echo "0.10")
    echo -e "${RED}✗ FAIL — contexto expirado ($AGE_MONTHS meses > $EXPIRY_MONTHS meses)${NC}"
    echo -e "  Freshness score: ~$FRESHNESS (máximo 0.30)"
    echo -e "  Ação: revalidar contexto antes de publicar"
    exit 1
fi
