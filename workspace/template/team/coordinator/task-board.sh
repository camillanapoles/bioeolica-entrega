#!/usr/bin/env bash
# task-board.sh
# Quadro de Tarefas — Alocação, rastreamento e relatório de tarefas
#
# Uso: ./task-board.sh <comando> <args...>
#
# Comandos:
#   allocate <desc> <agent> <project-dir>   Aloca nova tarefa
#   update <task-id> <status> <project-dir>  Atualiza status da tarefa
#   list <project-dir>                       Lista tarefas ativas
#   summary <project-dir>                    Resumo estatístico

set -euo pipefail

COMMAND="${1:-}"
shift 2>/dev/null || true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

allocate() {
    local desc="$1"
    local agent="$2"
    local project_dir="$3"
    local tasks_dir="$project_dir/team/coordinator/tasks"
    local task_id

    mkdir -p "$tasks_dir"

    # Gera ID sequencial
    local next_num
    next_num=1
    for f in "$tasks_dir"/TASK-*.json; do
        if [ -f "$f" ]; then
            local num
            num=$(basename "$f" .json | sed 's/TASK-//')
            if [ "$num" -ge "$next_num" ]; then
                next_num=$((num + 1))
            fi
        fi
    done
    task_id=$(printf "TASK-%04d" "$next_num")

    local now
    now=$(date -Iseconds)

    cat > "$tasks_dir/$task_id.json" <<- EOF
{
  "id": "$task_id",
  "description": "$desc",
  "agent": "$agent",
  "status": "ALOCADA",
  "created_at": "$now",
  "updated_at": "$now",
  "depends_on": [],
  "blocked_by": [],
  "contexts_published": [],
  "completed_at": null
}
EOF

    echo -e "${GREEN}✓${NC} Tarefa ${CYAN}$task_id${NC} alocada para $agent"
    echo "  Descrição: $desc"

    # Atualiza team-composition.md
    local comp_file="$project_dir/team/coordinator/team-composition.md"
    if [ -f "$comp_file" ]; then
        # Adiciona linha na tabela de tarefas
        local task_line="| $task_id | $desc | $agent | - | - | ALOCADA |"
        # Procura pelo marcador de tarefas e insere
        if grep -q '## Tarefas Alocadas' "$comp_file"; then
            # Insere depois da última linha da tabela
            sed -i "/^## Tarefas Alocadas/,/^## /{ /^## /a\\
$task_line
            }" "$comp_file" 2>/dev/null || true
        fi
    fi
}

update() {
    local task_id="$1"
    local new_status="$2"
    local project_dir="$3"
    local task_file="$project_dir/team/coordinator/tasks/$task_id.json"

    if [ ! -f "$task_file" ]; then
        echo -e "${RED}ERRO: tarefa $task_id não encontrada${NC}"
        exit 1
    fi

    # Valida status
    case "$new_status" in
        ALOCADA|EM_ANDAMENTO|AGUARDANDO|BLOQUEADA|CONCLUIDA|CANCELADA) ;;
        *)
            echo -e "${RED}ERRO: status inválido: $new_status${NC}"
            echo "Válidos: ALOCADA, EM_ANDAMENTO, AGUARDANDO, BLOQUEADA, CONCLUIDA, CANCELADA"
            exit 1
            ;;
    esac

    local now
    now=$(date -Iseconds)
    local completed_json=""

    if [ "$new_status" = "CONCLUIDA" ]; then
        completed_json=", \"completed_at\": \"$now\""
    fi

    # Usa jq para atualizar se disponível, senão sed
    if command -v jq &>/dev/null; then
        jq --arg status "$new_status" --arg now "$now" \
            ".status = \$status | .updated_at = \$now" \
            "$task_file" > "${task_file}.tmp" && mv "${task_file}.tmp" "$task_file"
    else
        echo -e "${YELLOW}Aviso: jq não encontrado. Atualizando manualmente.${NC}"
        sed -i "s/\"status\": \".*\"/\"status\": \"$new_status\"/" "$task_file"
        sed -i "s/\"updated_at\": \".*\"/\"updated_at\": \"$now\"/" "$task_file"
    fi

    echo -e "${GREEN}✓${NC} Tarefa $task_id atualizada: $new_status"
}

list() {
    local project_dir="$1"
    local tasks_dir="$project_dir/team/coordinator/tasks"

    if [ ! -d "$tasks_dir" ]; then
        echo "Nenhuma tarefa encontrada."
        return
    fi

    echo -e "${CYAN}Tarefas:${NC}"
    printf "  %-12s %-30s %-18s %-12s\n" "ID" "Descrição" "Agente" "Status"
    printf "  %-12s %-30s %-18s %-12s\n" "---" "---------" "------" "------"

    for f in "$tasks_dir"/TASK-*.json; do
        if [ -f "$f" ]; then
            local id desc agent status
            id=$(jq -r '.id // "unknown"' "$f" 2>/dev/null)
            desc=$(jq -r '.description // ""' "$f" 2>/dev/null | cut -c1-28)
            agent=$(jq -r '.agent // ""' "$f" 2>/dev/null)
            status=$(jq -r '.status // ""' "$f" 2>/dev/null)

            local color="$GREEN"
            [ "$status" = "BLOQUEADA" ] && color="$RED"
            [ "$status" = "ALOCADA" ] && color="$YELLOW"

            printf "  ${color}%-12s${NC} %-30s %-18s ${color}%-12s${NC}\n" "$id" "$desc" "$agent" "$status"
        fi
    done
}

summary() {
    local project_dir="$1"
    local tasks_dir="$project_dir/team/coordinator/tasks"
    local total=0
    local alocadas=0
    local em_andamento=0
    local bloqueadas=0
    local concluidas=0
    local canceladas=0

    if [ ! -d "$tasks_dir" ]; then
        echo "  0 tarefas."
        return
    fi

    for f in "$tasks_dir"/TASK-*.json; do
        if [ -f "$f" ]; then
            local status
            status=$(jq -r '.status // ""' "$f" 2>/dev/null)
            total=$((total + 1))
            case "$status" in
                ALOCADA) alocadas=$((alocadas + 1)) ;;
                EM_ANDAMENTO) em_andamento=$((em_andamento + 1)) ;;
                BLOQUEADA) bloqueadas=$((bloqueadas + 1)) ;;
                CONCLUIDA) concluidas=$((concluidas + 1)) ;;
                CANCELADA) canceladas=$((canceladas + 1)) ;;
            esac
        fi
    done

    echo "  Total: $total | ${GREEN}✓${NC} $concluidas concluídas | ${YELLOW}→${NC} $em_andamento ativas | ${YELLOW}◷${NC} $alocadas pendentes | ${RED}✗${NC} $bloqueadas bloqueadas | — $canceladas canceladas"
}

# ─── Dispatch ──────────────────────────────────────────────────────────────

case "$COMMAND" in
    allocate)
        allocate "${1:-}" "${2:-}" "${3:-}"
        ;;
    update)
        update "${1:-}" "${2:-}" "${3:-}"
        ;;
    list)
        list "${1:-}"
        ;;
    summary)
        summary "${1:-}"
        ;;
    *)
        echo "Uso: task-board.sh <allocate|update|list|summary> <args>"
        exit 1
        ;;
esac
