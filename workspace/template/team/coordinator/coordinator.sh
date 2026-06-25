#!/usr/bin/env bash
# coordinator.sh
# Agente Coordenador — Orquestração Multi-Agente
# Gerencia: derivação do time, alocação de tarefas, dependências,
#           reuniões, deadlocks, e publicação de contexto.
#
# Uso: ./coordinator.sh <comando> <args...>
#
# Comandos:
#   init <project-dir>          Inicializa coordenação para o projeto
#   derive-team <domain-map>    Deriva composição do time dos domínios
#   allocate <task> <agent>     Aloca tarefa para agente
#   schedule <meeting-file>     Agenda/convoca reunião
#   status                      Status do time e tarefas
#   deadlocks                   Lista deadlocks ativos
#   resolve <deadlock-id>       Resolve deadlock
#   publish <context-file>      Publica contexto (gatilho quality gates)
#   report                      Gera relatório de status do projeto

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd 2>/dev/null || echo "")"
CONTEXT_DIR="$PROJECT_DIR/context"
DOMAINS_DIR="$PROJECT_DIR/domains"
MEETINGS_DIR="$PROJECT_DIR/meetings"
SHARED_DIR="$PROJECT_DIR/shared"
TEAM_DIR="$PROJECT_DIR/team"
PROPAGATION_SCRIPT="$CONTEXT_DIR/propagation-proto.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Help ──────────────────────────────────────────────────────────────────

if [ $# -lt 1 ]; then
    echo -e "${CYAN}Agente Coordenador — Orquestração Multi-Agente${NC}"
    echo ""
    echo "Comandos:"
    echo "  init <project-dir>          Inicializa coordenação"
    echo "  derive-team <domain-map>    Deriva time dos domínios"
    echo "  allocate <task> <agent>     Aloca tarefa"
    echo "  schedule <meeting-file>     Agenda reunião"
    echo "  status                      Status do projeto"
    echo "  deadlocks                   Lista deadlocks"
    echo "  resolve <deadlock-id>       Resolve deadlock"
    echo "  publish <context-file>      Publica contexto"
    echo "  report                      Relatório de status"
    exit 0
fi

COMMAND="$1"
shift

# ─── Core Functions ────────────────────────────────────────────────────────

log_event() {
    local event_type="$1"
    local details="$2"
    local timestamp
    timestamp=$(date -Iseconds)
    local log_file="$PROJECT_DIR/context/.events.log"
    echo "[$timestamp] COORD | $event_type | $details" >> "$log_file"
}

check_project() {
    if [ ! -d "$CONTEXT_DIR" ]; then
        echo -e "${RED}ERRO: diretório de contexto não encontrado. Execute 'init' primeiro.${NC}"
        exit 1
    fi
}

# ─── init ──────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "init" ]; then
    PROJECT_DIR="${1:-}"
    if [ -z "$PROJECT_DIR" ] || [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}ERRO: informe um diretório de projeto válido.${NC}"
        exit 1
    fi

    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    CONTEXT_DIR="$PROJECT_DIR/context"
    DOMAINS_DIR="$PROJECT_DIR/domains"
    MEETINGS_DIR="$PROJECT_DIR/meetings"
    SHARED_DIR="$PROJECT_DIR/shared"
    PROPAGATION_SCRIPT="$CONTEXT_DIR/propagation-proto.sh"

    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  COORDENADOR — Inicializando: $(basename "$PROJECT_DIR")${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"

    # Garante estrutura de diretórios
    mkdir -p "$PROJECT_DIR/team/coordinator/atas"
    mkdir -p "$PROJECT_DIR/team/coordinator/tasks"
    mkdir -p "$CONTEXT_DIR/.locks"
    mkdir -p "$SHARED_DIR"

    # Inicializa arquivos de estado do coordenador
    if [ ! -f "$PROJECT_DIR/team/coordinator/team-composition.md" ]; then
        cat > "$PROJECT_DIR/team/coordinator/team-composition.md" <<- EOF
# Composição do Time — $(basename "$PROJECT_DIR")

## Domínios Confirmados

| Domínio | Agente | Proficiência | Status |
|---------|--------|--------------|--------|

## Tarefas Alocadas

| ID | Tarefa | Responsável | Prazo | Depende de | Status |
|----|--------|-------------|-------|------------|--------|

## Reuniões

| # | Data | Pauta | Participantes | Status |
|---|------|-------|--------------|--------|
EOF
    fi

    if [ ! -f "$PROJECT_DIR/team/coordinator/agenda.md" ]; then
        cat > "$PROJECT_DIR/team/coordinator/agenda.md" <<- EOF
# Agenda do Coordenador — $(basename "$PROJECT_DIR")

## Próximas Reuniões

| Data | Pauta | Convocados | Tipo |
|------|-------|-----------|------|

## Reuniões Pendentes

- Nenhuma
EOF
    fi

    if [ ! -f "$PROJECT_DIR/meetings/decision_log.md" ]; then
        cat > "$PROJECT_DIR/meetings/decision_log.md" <<- EOF
# Registro de Decisões — $(basename "$PROJECT_DIR")

| # | Data | Decisão | Contexto | Responsável | Aprovado por |
|---|------|---------|----------|-------------|--------------|
EOF
    fi

    if [ ! -f "$PROJECT_DIR/meetings/deadlocks.md" ]; then
        cat > "$PROJECT_DIR/meetings/deadlocks.md" <<- EOF
# Deadlocks — $(basename "$PROJECT_DIR")

| ID | Data | Agentes | Descrição | Tipo | Status | Resolução |
|----|------|---------|-----------|------|--------|-----------|
EOF
    fi

    # Inicializa subscription do coordenador no protocolo de propagação
    if [ -f "$PROPAGATION_SCRIPT" ]; then
        bash "$PROPAGATION_SCRIPT" subscribe "coordinator" "*" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ Coordenação inicializada para $(basename "$PROJECT_DIR")${NC}"
    echo -e "${YELLOW}  Próximo passo: execute 'derive-team' com o domain-map preenchido${NC}"
    log_event "INIT" "coordenador inicializado para $(basename "$PROJECT_DIR")"
    exit 0
fi

# ─── derive-team ───────────────────────────────────────────────────────────

if [ "$COMMAND" = "derive-team" ]; then
    check_project
    DOMAIN_MAP="${1:-$DOMAINS_DIR/relevance_check.md}"
    if [ ! -f "$DOMAIN_MAP" ]; then
        echo -e "${RED}ERRO: domain map não encontrado: $DOMAIN_MAP${NC}"
        exit 1
    fi

    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  DERIVANDO TIME DOS DOMÍNIOS${NC}"
    echo -e "${CYAN}  Fonte: $DOMAIN_MAP${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"

    bash "$SCRIPT_DIR/agent-factory.sh" "$DOMAIN_MAP" "$PROJECT_DIR"
    log_event "DERIVE_TEAM" "time derivado de $(basename "$DOMAIN_MAP")"
    exit 0
fi

# ─── allocate ──────────────────────────────────────────────────────────────

if [ "$COMMAND" = "allocate" ]; then
    check_project
    TASK_DESC="${1:-}"
    AGENT="${2:-}"
    if [ -z "$TASK_DESC" ] || [ -z "$AGENT" ]; then
        echo -e "${RED}ERRO: use: coordinator.sh allocate \"<descrição>\" <agente>${NC}"
        exit 1
    fi

    bash "$SCRIPT_DIR/task-board.sh" allocate "$TASK_DESC" "$AGENT" "$PROJECT_DIR"
    log_event "ALLOCATE" "tarefa \"$TASK_DESC\" → $AGENT"
    exit 0
fi

# ─── schedule ──────────────────────────────────────────────────────────────

if [ "$COMMAND" = "schedule" ]; then
    check_project
    MEETING_FILE="${1:-}"
    if [ -z "$MEETING_FILE" ]; then
        echo -e "${YELLOW}Iniciando reunião interativa...${NC}"
        bash "$SCRIPT_DIR/meeting-convener.sh" interactive "$PROJECT_DIR"
    else
        bash "$SCRIPT_DIR/meeting-convener.sh" schedule "$MEETING_FILE" "$PROJECT_DIR"
    fi
    log_event "SCHEDULE" "reunião agendada: $MEETING_FILE"
    exit 0
fi

# ─── status ────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "status" ]; then
    check_project
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  STATUS DO PROJETO: $(basename "$PROJECT_DIR")${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo ""

    # Time
    echo -e "${YELLOW}Time:${NC}"
    if [ -f "$PROJECT_DIR/team/coordinator/team-composition.md" ]; then
        grep -E '^\|' "$PROJECT_DIR/team/coordinator/team-composition.md" | head -20
    else
        echo "  Nenhum time configurado."
    fi
    echo ""

    # Agentes registrados
    echo -e "${YELLOW}Agentes no workspace:${NC}"
    for agent_dir in "$TEAM_DIR"/agent-*/; do
        if [ -d "$agent_dir" ]; then
            agent_name=$(basename "$agent_dir")
            task_count=$(find "$agent_dir" -name "*.md" -o -name "*.json" 2>/dev/null | wc -l)
            echo -e "  ${GREEN}✓${NC} $agent_name ($task_count arquivos)"
        fi
    done
    if ! ls "$TEAM_DIR"/agent-*/ 1>/dev/null 2>&1; then
        echo "  Nenhum agente registrado. Execute 'derive-team' primeiro."
    fi
    echo ""

    # Tarefas
    echo -e "${YELLOW}Tarefas:${NC}"
    if ls "$PROJECT_DIR/team/coordinator/tasks/"*.json 1>/dev/null 2>&1; then
        bash "$SCRIPT_DIR/task-board.sh" summary "$PROJECT_DIR"
    else
        echo "  Nenhuma tarefa alocada."
    fi
    echo ""

    # Deadlocks
    echo -e "${YELLOW}Deadlocks:${NC}"
    if [ -f "$PROJECT_DIR/meetings/deadlocks.md" ]; then
        grep -E '^\|.*(ABERTO|PENDENTE)' "$PROJECT_DIR/meetings/deadlocks.md" 2>/dev/null || echo "  Nenhum deadlock ativo."
    fi
    echo ""

    # Últimos eventos
    echo -e "${YELLOW}Últimos eventos:${NC}"
    if [ -f "$CONTEXT_DIR/.events.log" ]; then
        grep "COORD" "$CONTEXT_DIR/.events.log" 2>/dev/null | tail -5 || echo "  Nenhum evento registrado."
    else
        echo "  Nenhum evento registrado."
    fi

    exit 0
fi

# ─── deadlocks ─────────────────────────────────────────────────────────────

if [ "$COMMAND" = "deadlocks" ]; then
    check_project
    bash "$SCRIPT_DIR/deadlock-resolver.sh" list "$PROJECT_DIR"
    exit 0
fi

if [ "$COMMAND" = "resolve" ]; then
    check_project
    DEADLOCK_ID="${1:-}"
    if [ -z "$DEADLOCK_ID" ]; then
        echo -e "${RED}ERRO: informe o ID do deadlock.${NC}"
        exit 1
    fi
    bash "$SCRIPT_DIR/deadlock-resolver.sh" resolve "$DEADLOCK_ID" "$PROJECT_DIR"
    log_event "RESOLVE_DEADLOCK" "deadlock $DEADLOCK_ID resolvido"
    exit 0
fi

# ─── publish ───────────────────────────────────────────────────────────────

if [ "$COMMAND" = "publish" ]; then
    check_project
    CONTEXT_FILE="${1:-}"
    if [ -z "$CONTEXT_FILE" ] || [ ! -f "$CONTEXT_FILE" ]; then
        echo -e "${RED}ERRO: informe um arquivo de contexto válido.${NC}"
        exit 1
    fi

    if [ -f "$PROPAGATION_SCRIPT" ]; then
        bash "$PROPAGATION_SCRIPT" publish "$CONTEXT_FILE"
        log_event "PUBLISH" "contexto $CONTEXT_FILE publicado via quality gates"
    else
        echo -e "${YELLOW}Aviso: propagation-proto.sh não encontrado. Publicando diretamente.${NC}"
        # Fallback: copia para shared/
        context_id=$(jq -r '.id // "unknown"' "$CONTEXT_FILE" 2>/dev/null || echo "unknown")
        cp "$CONTEXT_FILE" "$SHARED_DIR/$context_id.json"
        echo -e "${GREEN}✓ Contexto copiado para shared/$context_id.json${NC}"
        log_event "PUBLISH_FALLBACK" "contexto $context_id copiado para shared/"
    fi
    exit 0
fi

# ─── report ────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "report" ]; then
    check_project
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  RELATÓRIO DO COORDENADOR${NC}"
    echo -e "${CYAN}  Projeto: $(basename "$PROJECT_DIR")${NC}"
    echo -e "${CYAN}  Timestamp: $(date -Iseconds)${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
    echo ""

    # Contexto raiz
    if [ -f "$CONTEXT_DIR/problem_statement.md" ]; then
        problem_title=$(head -1 "$CONTEXT_DIR/problem_statement.md" 2>/dev/null | sed 's/^# //' || echo "Não definido")
        echo -e "${YELLOW}Problema:${NC} $problem_title"
    fi

    # Time
    if [ -f "$PROJECT_DIR/team/coordinator/team-composition.md" ]; then
        echo ""
        echo -e "${YELLOW}Time (da composição):${NC}"
        grep -E '^\|.*\|.*\|' "$PROJECT_DIR/team/coordinator/team-composition.md" | grep -v 'Domínio\|-----\|Tarefa\|Título' | while IFS= read -r line; do
            echo "  $line"
        done
    fi

    # Domínios
    if [ -f "$DOMAINS_DIR/relevance_check.md" ]; then
        echo ""
        echo -e "${YELLOW}Cobertura de Domínios:${NC}"
        total=$(grep -cE '^\|' "$DOMAINS_DIR/relevance_check.md" 2>/dev/null || echo 0)
        confirmed=$(grep -c '✅\|Sim\|sim' "$DOMAINS_DIR/relevance_check.md" 2>/dev/null || echo 0)
        total=$((total - 2))  # remove header + separator
        if [ "$total" -gt 0 ]; then
            pct=$((confirmed * 100 / total))
            echo -e "  $confirmed de $total domínios confirmados ($pct%)"
        fi
    fi

    # Contextos publicados
    echo ""
    echo -e "${YELLOW}Contextos publicados:${NC}"
    ctx_count=$(find "$PROJECT_DIR/context" -name "*.json" -not -name "*.events.log" -not -name ".subscriptions.json" -not -name "5w1h.json" 2>/dev/null | wc -l)
    echo "  $ctx_count contextos no índice"

    # Reuniões
    echo ""
    echo -e "${YELLOW}Reuniões realizadas:${NC}"
    meeting_count=$(find "$MEETINGS_DIR/ata" -name "*.md" 2>/dev/null | wc -l)
    echo "  $meeting_count atas registradas"

    # Deadlocks ativos
    echo ""
    echo -e "${YELLOW}Deadlocks ativos:${NC}"
    if [ -f "$PROJECT_DIR/meetings/deadlocks.md" ]; then
        grep -cE '^\|.*(ABERTO|PENDENTE)' "$PROJECT_DIR/meetings/deadlocks.md" 2>/dev/null || echo "  0"
    fi

    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────${NC}"
    echo -e "${CYAN}  Fim do relatório${NC}"

    exit 0
fi

# ─── Comando desconhecido ──────────────────────────────────────────────────

echo -e "${RED}Comando desconhecido: $COMMAND${NC}"
echo "Comandos: init, derive-team, allocate, schedule, status, deadlocks, resolve, publish, report"
exit 1
