#!/usr/bin/env bash
# schema-validator.sh
# GATE 1 — Schema Validation: verifica se contexto segue a ontologia
# Uso: ./schema-validator.sh <arquivo-contexto.json>
#
# Valida:
#   1. Campos obrigatórios preenchidos
#   2. Tipos corretos (number, string, array, object)
#   3. Enums válidos
#   4. Relationships válidas (não referencia nó inexistente)
#
# Depende de: ajv (npm install -g ajv-cli) ou jq + validação manual

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONTOLOGY="$SCRIPT_DIR/../ontology.json"
CONTEXT_FILE="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Validação ─────────────────────────────────────────────────────────────

if [ -z "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: informe o arquivo de contexto.${NC}"
    echo "Uso: ./schema-validator.sh <arquivo-contexto.json>"
    exit 1
fi

if [ ! -f "$CONTEXT_FILE" ]; then
    echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
    exit 1
fi

echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  GATE 1 — VALIDAÇÃO DE SCHEMA${NC}"
echo -e "${CYAN}  Arquivo: $CONTEXT_FILE${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Verifica se ajv está disponível ──────────────────────────────────────

if command -v ajv &> /dev/null; then
    echo -e "${YELLOW}Usando ajv para validação JSON Schema...${NC}"
    if ajv validate -s "$ONTOLOGY" -d "$CONTEXT_FILE" --strict 2>&1; then
        echo -e "${GREEN}✓ SCHEMA PASS — contexto válido conforme ontologia${NC}"
        exit 0
    else
        echo -e "${RED}✗ SCHEMA FAIL — contexto não conforme${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}ajv não encontrado. Usando validação básica com jq...${NC}"
fi

# ─── Validação básica com jq (fallback) ────────────────────────────────────

ERRORS=0

# 1. Verifica se é JSON válido
if ! jq empty "$CONTEXT_FILE" 2>/dev/null; then
    echo -e "${RED}✗ JSON inválido${NC}"
    exit 1
fi

# 2. Verifica campos obrigatórios comuns
echo -e "${YELLOW}Verificando campos obrigatórios...${NC}"

for field in id name; do
    if jq -e ".$field" "$CONTEXT_FILE" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $field presente"
    else
        echo -e "  ${RED}✗${NC} $field ausente"
        ERRORS=$((ERRORS + 1))
    fi
done

# 3. Verifica lineage se presente
if jq -e '.lineage' "$CONTEXT_FILE" > /dev/null 2>&1; then
    echo -e "${YELLOW}Verificando lineage...${NC}"
    for lfield in created_by version created_at; do
        if jq -e ".lineage.$lfield" "$CONTEXT_FILE" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} lineage.$lfield presente"
        else
            echo -e "  ${RED}✗${NC} lineage.$lfield ausente"
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

# 4. Verifica relationships se presentes
if jq -e '.relationships' "$CONTEXT_FILE" > /dev/null 2>&1; then
    echo -e "${YELLOW}Verificando relationships...${NC}"
    # Verifica se targets de relationships são não-nulos (suporta array de strings e objeto com .target)
    jq -r '.relationships | to_entries[] | .key as $k | (.value | if type == "array" then (. // [] | join(", ")) else (.target // "none") end) | "\($k): \(.)"' "$CONTEXT_FILE" 2>/dev/null | while read -r rel; do
        if echo "$rel" | grep -qE "(none|\[\])$"; then
            echo -e "  ${YELLOW}⚠${NC} $rel — target ausente (warning)"
        else
            echo -e "  ${GREEN}✓${NC} $rel"
        fi
    done
fi

# ─── Resultado ─────────────────────────────────────────────────────────────

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  SCHEMA PASS — contexto válido${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  SCHEMA FAIL — $ERRORS erro(s) encontrado(s)${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    exit 1
fi
