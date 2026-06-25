#!/usr/bin/env bash
# propagation-proto.sh
# Protocolo de Propagação de Contexto — eventos, locking, detecção de conflito
# Uso: ./propagation-proto.sh <comando> <args...>
#
# Comandos:
#   publish   <context-file>   Publica contexto (passa pelos 4 quality gates + checkout)
#   update    <context-file>   Atualiza contexto existente (version bump + lineage update)
#   lock      <context-id>     Faz checkout (write lock) de um contexto
#   unlock    <context-id>     Libera checkout
#   status    <context-id>     Verifica status de um contexto
#   conflicts                  Lista contextos com conflito (DISPUTED)
#   subscribe <agent-id>       Inscreve agente para notificações de mudança

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUALITY_GATES_DIR="$SCRIPT_DIR/quality-gates"
CONTEXT_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCKS_DIR="$CONTEXT_DIR/.locks"
EVENTS_LOG="$CONTEXT_DIR/.events.log"
SUBSCRIPTIONS_FILE="$CONTEXT_DIR/.subscriptions.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$LOCKS_DIR"

# ─── Help ──────────────────────────────────────────────────────────────────

if [ $# -lt 1 ]; then
    echo -e "${CYAN}Uso: ./propagation-proto.sh <comando> <args...>${NC}"
    echo ""
    echo "Comandos:"
    echo "  publish   <context-file>   Publica contexto (quality gates + checkout)"
    echo "  update    <context-file>   Atualiza contexto existente"
    echo "  lock      <context-id>     Faz checkout (write lock)"
    echo "  unlock    <context-id>     Libera checkout"
    echo "  status    <context-id>     Verifica status"
    echo "  conflicts                 Lista contextos DISPUTED"
    echo "  subscribe <agent-id>      Inscreve para notificações"
    echo "  events    [n]             Últimos n eventos (padrão: 10)"
    exit 0
fi

COMMAND="$1"
shift

# ─── Funções ───────────────────────────────────────────────────────────────

emit_event() {
    local event_type="$1"
    local context_id="$2"
    local agent="$3"
    local details="${4:-}"
    local timestamp
    timestamp=$(date -Iseconds)

    echo "[$timestamp] $event_type | context=$context_id | agent=$agent | $details" >> "$EVENTS_LOG"

    # Notifica agentes inscritos
    if [ -f "$SUBSCRIPTIONS_FILE" ]; then
        local subscribers
        subscribers=$(jq -r ".subscribers[] | select(.context_pattern == \"*\"
            or .context_pattern == \"$context_id\") | .agent_id" "$SUBSCRIPTIONS_FILE" 2>/dev/null)
        if [ -n "$subscribers" ]; then
            echo -e "  ${YELLOW}Notificando: $subscribers${NC}"
        fi
    fi
}

check_locks_dir() {
    mkdir -p "$LOCKS_DIR"
}

# ─── publish ───────────────────────────────────────────────────────────────

if [ "$COMMAND" = "publish" ]; then
    CONTEXT_FILE="${1:-}"
    if [ -z "$CONTEXT_FILE" ] || [ ! -f "$CONTEXT_FILE" ]; then
        echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
        exit 1
    fi

    CONTEXT_ID=$(jq -r '.id // empty' "$CONTEXT_FILE" 2>/dev/null || echo "unknown")
    AGENT=$(jq -r '.lineage.created_by // "unknown"' "$CONTEXT_FILE" 2>/dev/null || echo "unknown")

    echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}  PUBLICANDO CONTEXTO: $CONTEXT_ID${NC}"
    echo -e "${CYAN}  Agente: $AGENT${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────${NC}"
    echo ""

    # Verifica lock
    if [ -f "$LOCKS_DIR/$CONTEXT_ID.lock" ]; then
        local locker
        locker=$(cat "$LOCKS_DIR/$CONTEXT_ID.lock")
        if [ "$locker" != "$AGENT" ]; then
            echo -e "${RED}✗ Contexto locked por $locker — publish rejeitado${NC}"
            emit_event "PUBLISH_REJECTED_LOCKED" "$CONTEXT_ID" "$AGENT" "locked by $locker"
            exit 1
        fi
    fi

    # Cria lock automático
    echo "$AGENT" > "$LOCKS_DIR/$CONTEXT_ID.lock"
    echo -e "${YELLOW}  Lock adquirido para $CONTEXT_ID por $AGENT${NC}"

    # GATE 1: Schema Validation
    echo -e "${YELLOW}[GATE 1] Schema Validation...${NC}"
    if bash "$QUALITY_GATES_DIR/schema-validator.sh" "$CONTEXT_FILE"; then
        echo -e "${GREEN}  GATE 1 PASS${NC}"
    else
        echo -e "${RED}  GATE 1 FAIL — publish abortado${NC}"
        rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"
        emit_event "PUBLISH_FAILED_SCHEMA" "$CONTEXT_ID" "$AGENT" "schema validation failed"
        exit 1
    fi

    # GATE 2: Sanity Check
    echo ""
    echo -e "${YELLOW}[GATE 2] Sanity Check...${NC}"
    if bash "$QUALITY_GATES_DIR/sanity-check.sh" "$CONTEXT_FILE"; then
        echo -e "${GREEN}  GATE 2 PASS${NC}"
    else
        echo -e "${RED}  GATE 2 FAIL — publish abortado${NC}"
        rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"
        emit_event "PUBLISH_FAILED_SANITY" "$CONTEXT_ID" "$AGENT" "sanity check failed"
        exit 1
    fi

    # GATE 3: Freshness Check
    echo ""
    echo -e "${YELLOW}[GATE 3] Freshness Check...${NC}"
    if bash "$QUALITY_GATES_DIR/freshness-check.sh" "$CONTEXT_FILE"; then
        echo -e "${GREEN}  GATE 3 PASS${NC}"
    else
        echo -e "${RED}  GATE 3 FAIL — publish abortado${NC}"
        rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"
        emit_event "PUBLISH_FAILED_FRESHNESS" "$CONTEXT_ID" "$AGENT" "freshness check failed"
        exit 1
    fi

    # GATE 4: Revisor Hostil
    echo ""
    echo -e "${YELLOW}[GATE 4] Revisor Hostil...${NC}"
    if bash "$QUALITY_GATES_DIR/revisor-hostil.sh" "$CONTEXT_FILE"; then
        echo -e "${GREEN}  GATE 4 PASS${NC}"
    else
        echo -e "${RED}  GATE 4 FAIL — publish abortado${NC}"
        rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"
        emit_event "PUBLISH_FAILED_REVIEW" "$CONTEXT_ID" "$AGENT" "hostile review failed"
        exit 1
    fi

    # Copia para o diretório de contexto
    CONTEXT_CLASS=$(jq -r '.class // "unknown"' "$CONTEXT_FILE" 2>/dev/null | tr '[:upper:]' '[:lower:]')
    CLASS_DIR="$CONTEXT_DIR/${CONTEXT_CLASS}s"

    if echo "$CONTEXT_CLASS" | grep -qE '^(metal|polimero|ceramica|composito|semicondutor|biomaterial|nanomaterial|liga|outro)$'; then
        CLASS_DIR="$CONTEXT_DIR/materials"
    fi

    mkdir -p "$CLASS_DIR"
    cp "$CONTEXT_FILE" "$CLASS_DIR/$CONTEXT_ID.json"
    echo -e "${GREEN}  Contexto copiado para $CLASS_DIR/$CONTEXT_ID.json${NC}"

    # Libera lock
    rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"

    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  PUBLISH COMPLETO — $CONTEXT_ID publicado com sucesso${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"

    emit_event "PUBLISHED" "$CONTEXT_ID" "$AGENT" "all quality gates passed"
    exit 0
fi

# ─── update ────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "update" ]; then
    CONTEXT_FILE="${1:-}"
    if [ -z "$CONTEXT_FILE" ] || [ ! -f "$CONTEXT_FILE" ]; then
        echo -e "${RED}ERRO: arquivo não encontrado: $CONTEXT_FILE${NC}"
        exit 1
    fi

    CONTEXT_ID=$(jq -r '.id // empty' "$CONTEXT_FILE" 2>/dev/null || echo "unknown")
    AGENT=$(jq -r '.lineage.updated_by // .lineage.created_by // "unknown"' "$CONTEXT_FILE" 2>/dev/null || echo "unknown")
    CURRENT_VERSION=$(jq -r '.lineage.version // "0.0"' "$CONTEXT_FILE" 2>/dev/null || echo "0.0")

    echo -e "${CYAN}Atualizando contexto $CONTEXT_ID (versão $CURRENT_VERSION)${NC}"

    # Incrementa minor version
    MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
    MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
    NEW_MINOR=$((MINOR + 1))
    NEW_VERSION="$MAJOR.$NEW_MINOR"

    # Aplica version bump via jq
    jq --arg ver "$NEW_VERSION" --arg now "$(date -Iseconds)" \
        '.lineage.version = $ver | .lineage.updated_at = $now' \
        "$CONTEXT_FILE" > "${CONTEXT_FILE}.tmp" && mv "${CONTEXT_FILE}.tmp" "$CONTEXT_FILE"

    echo -e "${GREEN}✓ Versão atualizada: $CURRENT_VERSION → $NEW_VERSION${NC}"
    emit_event "UPDATED" "$CONTEXT_ID" "$AGENT" "version $CURRENT_VERSION -> $NEW_VERSION"
    exit 0
fi

# ─── lock / unlock ─────────────────────────────────────────────────────────

if [ "$COMMAND" = "lock" ]; then
    CONTEXT_ID="${1:-}"
    AGENT="${2:-unknown}"

    if [ -z "$CONTEXT_ID" ]; then
        echo -e "${RED}ERRO: informe context-id${NC}"
        exit 1
    fi

    if [ -f "$LOCKS_DIR/$CONTEXT_ID.lock" ]; then
        local locker
        locker=$(cat "$LOCKS_DIR/$CONTEXT_ID.lock")
        echo -e "${RED}✗ Contexto $CONTEXT_ID já locked por: $locker${NC}"
        exit 1
    fi

    echo "$AGENT" > "$LOCKS_DIR/$CONTEXT_ID.lock"
    echo -e "${GREEN}✓ Lock adquirido: $CONTEXT_ID → $AGENT${NC}"
    emit_event "LOCKED" "$CONTEXT_ID" "$AGENT" "write lock acquired"
    exit 0
fi

if [ "$COMMAND" = "unlock" ]; then
    CONTEXT_ID="${1:-}"
    AGENT="${2:-unknown}"

    if [ -z "$CONTEXT_ID" ]; then
        echo -e "${RED}ERRO: informe context-id${NC}"
        exit 1
    fi

    if [ ! -f "$LOCKS_DIR/$CONTEXT_ID.lock" ]; then
        echo -e "${YELLOW}⚠ Contexto $CONTEXT_ID não está locked${NC}"
        exit 0
    fi

    rm -f "$LOCKS_DIR/$CONTEXT_ID.lock"
    echo -e "${GREEN}✓ Lock liberado: $CONTEXT_ID${NC}"
    emit_event "UNLOCKED" "$CONTEXT_ID" "$AGENT" "write lock released"
    exit 0
fi

# ─── status ────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "status" ]; then
    CONTEXT_ID="${1:-}"
    if [ -z "$CONTEXT_ID" ]; then
        echo -e "${RED}ERRO: informe context-id${NC}"
        exit 1
    fi

    echo -e "${CYAN}Status do contexto: $CONTEXT_ID${NC}"
    echo ""

    # Lock status
    if [ -f "$LOCKS_DIR/$CONTEXT_ID.lock" ]; then
        local locker
        locker=$(cat "$LOCKS_DIR/$CONTEXT_ID.lock")
        echo -e "  Lock: ${RED}LOCKED${NC} por $locker"
    else
        echo -e "  Lock: ${GREEN}FREE${NC}"
    fi

    # Últimos eventos
    echo ""
    echo -e "${YELLOW}Últimos eventos:${NC}"
    grep "$CONTEXT_ID" "$EVENTS_LOG" 2>/dev/null | tail -5 || echo "  Nenhum evento registrado"

    exit 0
fi

# ─── conflicts ─────────────────────────────────────────────────────────────

if [ "$COMMAND" = "conflicts" ]; then
    echo -e "${YELLOW}Contextos com conflito (DISPUTED):${NC}"

    # Procura em todos os JSONs do diretório de contexto
    found=0
    while IFS= read -r -d '' json_file; do
        local status
        status=$(jq -r '.lineage.validation_status // empty' "$json_file" 2>/dev/null)
        if [ "$status" = "DISPUTED" ]; then
            local cid
            cid=$(jq -r '.id // "unknown"' "$json_file" 2>/dev/null)
            local agent
            agent=$(jq -r '.lineage.created_by // "unknown"' "$json_file" 2>/dev/null)
            echo -e "  ${RED}✗${NC} $cid (criado por: $agent, arquivo: $json_file)"
            found=$((found + 1))
        fi
    done < <(find "$CONTEXT_DIR" -name "*.json" -not -name "*.events.log" -not -name ".subscriptions.json" -print0 2>/dev/null)

    if [ $found -eq 0 ]; then
        echo -e "  ${GREEN}Nenhum contexto em conflito${NC}"
    fi

    exit 0
fi

# ─── subscribe ─────────────────────────────────────────────────────────────

if [ "$COMMAND" = "subscribe" ]; then
    AGENT_ID="${1:-}"
    CONTEXT_PATTERN="${2:-*}"

    if [ -z "$AGENT_ID" ]; then
        echo -e "${RED}ERRO: informe agent-id${NC}"
        exit 1
    fi

    mkdir -p "$(dirname "$SUBSCRIPTIONS_FILE")"

    if [ ! -f "$SUBSCRIPTIONS_FILE" ]; then
        echo '{"subscribers": []}' > "$SUBSCRIPTIONS_FILE"
    fi

    # Verifica se já está inscrito
    if jq -e ".subscribers[] | select(.agent_id == \"$AGENT_ID\" and .context_pattern == \"$CONTEXT_PATTERN\")" "$SUBSCRIPTIONS_FILE" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Agente $AGENT_ID já inscrito em '$CONTEXT_PATTERN'${NC}"
    else
        jq --arg agent "$AGENT_ID" --arg pattern "$CONTEXT_PATTERN" \
            '.subscribers += [{"agent_id": $agent, "context_pattern": $pattern, "subscribed_at": now|strftime("%Y-%m-%dT%H:%M:%S%z")}]' \
            "$SUBSCRIPTIONS_FILE" > "${SUBSCRIPTIONS_FILE}.tmp" && mv "${SUBSCRIPTIONS_FILE}.tmp" "$SUBSCRIPTIONS_FILE"
        echo -e "${GREEN}✓ Agente $AGENT_ID inscrito em '$CONTEXT_PATTERN'${NC}"
    fi

    exit 0
fi

# ─── events ────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "events" ]; then
    N="${1:-10}"
    if [ -f "$EVENTS_LOG" ]; then
        tail -n "$N" "$EVENTS_LOG"
    else
        echo "Nenhum evento registrado ainda."
    fi
    exit 0
fi

# ─── Comando desconhecido ──────────────────────────────────────────────────

echo -e "${RED}Comando desconhecido: $COMMAND${NC}"
echo "Comandos válidos: publish, update, lock, unlock, status, conflicts, subscribe, events"
exit 1
