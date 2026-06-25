#!/usr/bin/env bash
# meeting-convener.sh
# Convocador de Reuniões — Agenda, registra atas e gerencia action items
#
# Uso: ./meeting-convener.sh <comando> <args...>
#
# Comandos:
#   schedule <meeting-json> <project-dir>  Agenda reunião a partir de JSON
#   interactive <project-dir>              Modo interativo
#   ata <meeting-id> <project-dir>         Gera template de ata
#   list <project-dir>                     Lista reuniões agendadas

set -euo pipefail

COMMAND="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

schedule() {
    local meeting_json="${1:-}"
    local project_dir="${2:-}"

    if [ -z "$meeting_json" ] || [ ! -f "$meeting_json" ]; then
        echo -e "${RED}ERRO: arquivo JSON da reunião não encontrado${NC}"
        exit 1
    fi

    local meetings_dir="$project_dir/meetings"
    local atas_dir="$meetings_dir/ata"
    mkdir -p "$atas_dir"

    local meeting_id pauta participantes data
    meeting_id=$(jq -r '.id // empty' "$meeting_json" 2>/dev/null)
    if [ -z "$meeting_id" ]; then
        local num
        num=$(find "$atas_dir" -name "ata-*.md" 2>/dev/null | wc -l)
        num=$((num + 1))
        meeting_id=$(printf "MTG-%04d" "$num")
    fi

    pauta=$(jq -r '.pauta // "Reunião de sincronização"' "$meeting_json" 2>/dev/null)
    participantes=$(jq -r '.participantes // [] | join(", ")' "$meeting_json" 2>/dev/null)
    data=$(jq -r '.data // empty' "$meeting_json" 2>/dev/null)
    [ -z "$data" ] && data=$(date -Iseconds)

    # Cria ata
    local ata_file="$atas_dir/ata-$meeting_id.md"
    cat > "$ata_file" <<- EOF
# Ata — $meeting_id

**Data:** $data
**Pauta:** $pauta
**Convocada por:** Coordenador
**Participantes:** $participantes

## Pauta

$pauta

## Discussão

<!-- Resumo da discussão -->

## Decisões

| # | Decisão | Responsável | Prazo |
|---|---------|-------------|-------|

## Action Items

| # | Tarefa | Responsável | Prazo | Status |
|---|--------|-------------|-------|--------|

## Próximos Passos

<!-- Próximos passos acordados -->

## Deadlocks (se houver)

<!-- Pontos de impasse não resolvidos -->
EOF

    echo -e "${GREEN}✓${NC} Reunião ${CYAN}$meeting_id${NC} registrada"
    echo "  Pauta: $pauta"
    echo "  Ata: $ata_file"

    # Registra no agenda.md
    local agenda_file="$project_dir/team/coordinator/agenda.md"
    if [ -f "$agenda_file" ]; then
        echo "| $data | $pauta | $participantes | AGENDADA |" >> "$agenda_file"
    fi

    # Gera evento de contexto
    local context_dir="$project_dir/context"
    if [ -f "$context_dir/.events.log" ]; then
        echo "[$(date -Iseconds)] MEETING | CREATED | $meeting_id | pauta=$pauta | participantes=$participantes" >> "$context_dir/.events.log"
    fi
}

interactive() {
    local project_dir="${1:-}"

    echo -e "${CYAN}═══ CONVOCAÇÃO DE REUNIÃO INTERATIVA ═══${NC}"
    echo ""

    # Detecta agentes ativos
    echo -e "${YELLOW}Agentes disponíveis:${NC}"
    local agents=()
    for agent_dir in "$project_dir"/team/agent-*/; do
        if [ -d "$agent_dir" ]; then
            local name
            name=$(basename "$agent_dir")
            agents+=("$name")
            echo "  [${#agents[@]}] $name"
        fi
    done

    if [ ${#agents[@]} -eq 0 ]; then
        echo -e "  ${YELLOW}Nenhum agente encontrado. Execute 'derive-team' primeiro.${NC}"
        return
    fi

    echo ""
    read -r -p "Pauta da reunião: " pauta
    echo ""

    echo "Selecione participantes (números separados por espaço):"
    local selected_indices
    read -r -p "> " selected_indices

    local participants=()
    for idx in $selected_indices; do
        if [ "$idx" -ge 1 ] && [ "$idx" -le "${#agents[@]}" ]; then
            participants+=("${agents[$((idx - 1))]}")
        fi
    done

    if [ ${#participants[@]} -eq 0 ]; then
        echo -e "${RED}Nenhum participante válido selecionado.${NC}"
        return
    fi

    # Cria JSON da reunião
    local temp_file
    temp_file=$(mktemp)
    cat > "$temp_file" <<- EOF
{
  "pauta": "$pauta",
  "participantes": [$(printf '"%s",' "${participants[@]}" | sed 's/,$//')],
  "data": "$(date -Iseconds)"
}
EOF

    schedule "$temp_file" "$project_dir"
    rm -f "$temp_file"
}

do_ata() {
    local meeting_id="${1:-}"
    local project_dir="${2:-}"
    local ata_file="$project_dir/meetings/ata/ata-$meeting_id.md"

    if [ -f "$ata_file" ]; then
        echo -e "${CYAN}Ata: $meeting_id${NC}"
        echo ""
        cat "$ata_file"
    else
        echo -e "${YELLOW}Ata não encontrada para $meeting_id${NC}"
        echo "Procurando..."

        # Busca por ID parcial
        for f in "$project_dir"/meetings/ata/*.md; do
            if [ -f "$f" ] && grep -q "$meeting_id" "$f" 2>/dev/null; then
                echo -e "${GREEN}Encontrado: $f${NC}"
                echo ""
                cat "$f"
                return
            fi
        done

        echo -e "${RED}Ata não encontrada.${NC}"
    fi
}

do_list() {
    local project_dir="${1:-}"
    echo -e "${CYAN}Reuniões registradas:${NC}"
    echo ""

    local ata_dir="$project_dir/meetings/ata"
    if [ ! -d "$ata_dir" ]; then
        echo "  Nenhuma reunião registrada."
        return
    fi

    for f in "$ata_dir"/*.md; do
        if [ -f "$f" ]; then
            local id pauta data
            id=$(basename "$f" .md | sed 's/ata-//')
            pauta=$(grep -m1 '^\*\*Pauta:\*\*' "$f" 2>/dev/null | sed 's/\*\*Pauta:\*\* //' || echo "—")
            data=$(grep -m1 '^\*\*Data:\*\*' "$f" 2>/dev/null | sed 's/\*\*Data:\*\* //' || echo "—")
            echo -e "  ${CYAN}$id${NC} | $data | $pauta"
        fi
    done
}

# ─── Dispatch ──────────────────────────────────────────────────────────────

case "$COMMAND" in
    schedule)
        schedule "${2:-}" "${3:-}"
        ;;
    interactive)
        interactive "${2:-}"
        ;;
    ata)
        do_ata "${2:-}" "${3:-}"
        ;;
    list)
        do_list "${2:-}"
        ;;
    *)
        echo "Uso: meeting-convener.sh <schedule|interactive|ata|list> <args>"
        echo "  schedule <json> <project-dir>  — Agenda do JSON"
        echo "  interactive <project-dir>       — Modo interativo"
        echo "  ata <id> <project-dir>          — Mostra ata"
        echo "  list <project-dir>              — Lista reuniões"
        exit 1
        ;;
esac
