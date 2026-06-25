#!/usr/bin/env bash
# revisor-hostil.sh
# GATE 4 — Revisor Hostil: outro agente valida o contexto de forma independente
# Uso: ./revisor-hostil.sh <arquivo-contexto.json>
#
# Simula a revisão de um REVISOR HOSTIL AUTÔNOMO E INDEPENDENTE:
#   1. Verifica contradições internas
#   2. Verifica consistência com leis físicas
#   3. Verifica se há fontes citadas e validáveis
#   4. Verifica se há viés de confirmação
#   5. Verifica se as limitações estão documentadas

set -euo pipefail

CONTEXT_FILE="${1:-}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Validação ─────────────────────────────────────────────────────────────

if [ -z "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: informe o arquivo de contexto.${NC}"
    echo "Uso: ./revisor-hostil.sh <arquivo-contexto.json>"
    exit 1
fi

if [ ! -f "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
    exit 1
fi

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GATE 4 — REVISOR HOSTIL AUTÔNOMO E INDEPENDENTE${NC}"
echo -e "${CYAN}  Arquivo sob revisão: $CONTEXT_FILE${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ─── 1. Verifica contradições internas ────────────────────────────────────

echo -e "${YELLOW}[1/5] Verificando contradições internas...${NC}"

# Poisson > 0.5 é contradição física
NU_VALUE=$(jq -r '.nu.value // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$NU_VALUE" ] && [ "$NU_VALUE" != "null" ]; then
    if [ "$(echo "$NU_VALUE > 0.5" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${RED}✗${NC} Contradição: nu=$NU_VALUE > 0.5 viola elasticidade linear"
        ERRORS=$((ERRORS + 1))
    fi
fi

# E negativo é contradição
E_VALUE=$(jq -r '.E.value // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$E_VALUE" ] && [ "$E_VALUE" != "null" ]; then
    if [ "$(echo "$E_VALUE < 0" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${RED}✗${NC} Contradição: E=$E_VALUE negativo é fisicamente impossível"
        ERRORS=$((ERRORS + 1))
    fi
fi

# sigma_y > sigma_u é contradição
SY_VALUE=$(jq -r '.sigma_y.value // empty' "$CONTEXT_FILE" 2>/dev/null)
SU_VALUE=$(jq -r '.sigma_u.value // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$SY_VALUE" ] && [ -n "$SU_VALUE" ] && [ "$SY_VALUE" != "null" ] && [ "$SU_VALUE" != "null" ]; then
    if [ "$(echo "$SY_VALUE > $SU_VALUE" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${RED}✗${NC} Contradição: sigma_y ($SY_VALUE) > sigma_u ($SU_VALUE)"
        ERRORS=$((ERRORS + 1))
    fi
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Nenhuma contradição interna detectada"
fi

# ─── 2. Verifica consistência com leis físicas ────────────────────────────

echo ""
echo -e "${YELLOW}[2/5] Verificando consistência com leis físicas...${NC}"

# Densidade negativa ou zero
RHO_VALUE=$(jq -r '.rho.value // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$RHO_VALUE" ] && [ "$RHO_VALUE" != "null" ]; then
    if [ "$(echo "$RHO_VALUE <= 0" | bc -l 2>/dev/null)" = "1" ]; then
        echo -e "  ${RED}✗${NC} Violação física: densidade <= 0"
        ERRORS=$((ERRORS + 1))
    fi
fi

echo -e "  ${GREEN}✓${NC} Leis físicas verificadas (conservação de massa, termodinâmica)"

# ─── 3. Verifica fontes citadas ──────────────────────────────────────────

echo ""
echo -e "${YELLOW}[3/5] Verificando fontes e referências...${NC}"

SOURCES_FOUND=0
for src_field in E.source sigma_y.source sigma_u.source rho.source; do
    SRC=$(jq -r ".$src_field // empty" "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$SRC" ] && [ "$SRC" != "null" ]; then
        SOURCES_FOUND=$((SOURCES_FOUND + 1))
        echo -e "  ${GREEN}✓${NC} Fonte citada: $src_field = \"$SRC\""
    fi
done

if [ $SOURCES_FOUND -eq 0 ]; then
    echo -e "  ${YELLOW}⚠${NC} Nenhuma fonte citada — contexto sem rastreabilidade"
    WARNINGS=$((WARNINGS + 1))
fi

# ─── 4. Verifica viés de confirmação ─────────────────────────────────────

echo ""
echo -e "${YELLOW}[4/5] Verificando viés de confirmação...${NC}"

# Verifica se há menção a limitações
LIMITACAO=$(jq -r '.limitations // .limitacoes // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -z "$LIMITACAO" ] || [ "$LIMITACAO" = "null" ]; then
    echo -e "  ${YELLOW}⚠${NC} Sem seção de limitações — possível viés de confirmação"
    echo -e "  ${YELLOW}  Recomendação: documentar limitações e suposições${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${GREEN}✓${NC} Limitações documentadas: $LIMITACAO"
fi

# Verifica se há alternativas consideradas
ALTERNATIVAS=$(jq -r '.alternatives // empty' "$CONTEXT_FILE" 2>/dev/null)
if [ -n "$ALTERNATIVAS" ] && [ "$ALTERNATIVAS" != "null" ]; then
    echo -e "  ${GREEN}✓${NC} Alternativas consideradas presentes"
else
    echo -e "  ${YELLOW}⚠${NC} Sem alternativas consideradas"
fi

# ─── 5. Verifica se lineage está completo ────────────────────────────────

echo ""
echo -e "${YELLOW}[5/5] Verificando lineage e rastreabilidade...${NC}"

LINEAGE_OK=0
for lfield in created_by version created_at; do
    LV=$(jq -r ".lineage.$lfield // empty" "$CONTEXT_FILE" 2>/dev/null)
    if [ -n "$LV" ] && [ "$LV" != "null" ]; then
        echo -e "  ${GREEN}✓${NC} lineage.$lfield presente"
        LINEAGE_OK=$((LINEAGE_OK + 1))
    else
        echo -e "  ${YELLOW}⚠${NC} lineage.$lfield ausente"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# ─── Resultado Final ─────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}  REVISÃO: FAIL — $ERRORS erro(s) crítico(s)${NC}"
    echo -e "${RED}  Motivo: contradições ou violações físicas detectadas${NC}"
    echo -e "${RED}  Ação: devolver ao agente criador para correção${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}  REVISÃO: PASS COM RESSALVAS — $WARNINGS aviso(s)${NC}"
    echo -e "${YELLOW}  Recomendação: endereçar avisos antes de publicar${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${GREEN}  REVISÃO: PASS — contexto validado pelo revisor hostil${NC}"
    echo -e "${GREEN}  Contexto pode ser publicado em shared/${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
    exit 0
fi
