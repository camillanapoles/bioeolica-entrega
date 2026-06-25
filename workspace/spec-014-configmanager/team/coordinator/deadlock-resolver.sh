#!/usr/bin/env bash
# deadlock-resolver.sh
# Resolvedor de Deadlocks — Detecta, analisa e resolve impasses entre agentes
#
# Uso: ./deadlock-resolver.sh <comando> <args...>
#
# Comandos:
#   list <project-dir>                Lista deadlocks ativos
#   detect <project-dir>              Detecta deadlocks automaticamente
#   resolve <deadlock-id> <dir>       Resolve deadlock (interativo)
#   resolve-auto <deadlock-id> <dir>  Resolve deadlock por regra automática

set -euo pipefail

COMMAND="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Tipos de Deadlock ─────────────────────────────────────────────────────

declare -A DEADLOCK_RULES
DEADLOCK_RULES["recurso:contexto"]="Regra 1: Prioridade por proficiência. O agente com maior proficiência no domínio do contexto mantém o lock. O outro agende revisão assíncrona."
DEADLOCK_RULES["recurso:ferramenta"]="Regra 2: Alternância temporal. Alocar janelas de uso de 2h. Se necessário simultâneo, provisionar segunda instância."
DEADLOCK_RULES["dependencia:resultado"]="Regra 3: Pipeline forçado. Agente A deve publicar resultado parcial (PENDING) para B iniciar. B trabalha com placeholder e atualiza quando A concluir."
DEADLOCK_RULES["dependencia:decisao"]="Regra 4: Voto do coordenador. Coordenador ouve ambos, decide com voto de desempate. Registrar em ata com justificativa."
DEADLOCK_RULES["contradicao:dado"]="Regra 5: Matriz de prioridade. (1) peer-reviewed, (2) norma, (3) data sheet, (4) estimativa. Se mesma prioridade, convocar reunião."
DEADLOCK_RULES["contradicao:metodo"]="Regra 6: Benchmark cego. Ambos executam método em problema padrão. Quem acertar benchmark vence. Registrar resultado."
DEADLOCK_RULES["default"]="Regra geral: Convocar reunião entre agentes + coordenador. Coordenador media e decide. Máximo 30 min de discussão."

# ─── Commands ──────────────────────────────────────────────────────────────

do_list() {
    local project_dir="${1:-}"
    local deadlock_file="$project_dir/meetings/deadlocks.md"

    echo -e "${CYAN}Deadlocks registrados:${NC}"
    echo ""

    if [ ! -f "$deadlock_file" ]; then
        echo "  Nenhum deadlock registrado."
        return
    fi

    local has_active=false
    while IFS='|' read -r _ id data agentes desc tipo status resolucao; do
        id=$(echo "$id" | xargs)
        status=$(echo "$status" | xargs)
        [ -z "$id" ] && continue
        [[ "$id" =~ ^-+$ ]] && continue
        [[ "$id" =~ ^ID$ ]] && continue

        if echo "$status" | grep -qiE '(ABERTO|PENDENTE)' 2>/dev/null; then
            has_active=true
            echo -e "  ${RED}✗${NC} ${CYAN}$id${NC} | $tipo | $agentes"
            echo "    Descrição: $desc"
            echo "    Status: $status"
            echo ""
        fi
    done < "$deadlock_file"

    if ! $has_active; then
        echo "  Nenhum deadlock ativo."
    fi
}

do_detect() {
    local project_dir="${1:-}"
    echo -e "${CYAN}Verificando deadlocks potenciais...${NC}"
    echo ""

    local tasks_dir="$project_dir/team/coordinator/tasks"
    local found=false

    # 1. Detecta tarefas bloqueadas
    if [ -d "$tasks_dir" ]; then
        for f in "$tasks_dir"/TASK-*.json; do
            if [ -f "$f" ]; then
                local status agent desc
                status=$(jq -r '.status // ""' "$f" 2>/dev/null)
                agent=$(jq -r '.agent // ""' "$f" 2>/dev/null)
                desc=$(jq -r '.description // ""' "$f" 2>/dev/null)

                if [ "$status" = "BLOQUEADA" ]; then
                    echo -e "  ${RED}⚠ TAREFA BLOQUEADA${NC} — $agent: $desc"
                    found=true
                fi
            fi
        done
    fi

    # 2. Detecta contexto locks ativos por muito tempo
    local locks_dir="$project_dir/context/.locks"
    if [ -d "$locks_dir" ]; then
        for lock_file in "$locks_dir"/*.lock; do
            if [ -f "$lock_file" ]; then
                local context_id
                context_id=$(basename "$lock_file" .lock)
                local locker
                locker=$(cat "$lock_file")
                local age
                age=$(($(date +%s) - $(stat -c %Y "$lock_file" 2>/dev/null || echo 0)))

                if [ "$age" -gt 3600 ]; then  # > 1 hora
                    echo -e "  ${YELLOW}⚠ LOCK PROLONGADO${NC} — $context_id por $locker ($((age / 60)) min)"
                    found=true
                fi
            fi
        done
    fi

    # 3. Detecta dependências não resolvidas entre tarefas
    if [ -d "$tasks_dir" ]; then
        for f in "$tasks_dir"/TASK-*.json; do
            local depends
            depends=$(jq -r '.depends_on[] // empty' "$f" 2>/dev/null)
            for dep in $depends; do
                local dep_file="$tasks_dir/$dep.json"
                if [ -f "$dep_file" ]; then
                    local dep_status
                    dep_status=$(jq -r '.status // ""' "$dep_file" 2>/dev/null)
                    local task_id
                    task_id=$(jq -r '.id // ""' "$f" 2>/dev/null)
                    if [ "$dep_status" != "CONCLUIDA" ] && [ "$dep_status" != "CANCELADA" ]; then
                        echo -e "  ${YELLOW}⚠ DEPENDÊNCIA PENDENTE${NC} — $task_id aguarda $dep ($dep_status)"
                        found=true
                    fi
                fi
            done
        done
    fi

    if ! $found; then
        echo -e "${GREEN}✓ Nenhum deadlock potencial detectado.${NC}"
    fi
}

do_resolve() {
    local deadlock_id="${1:-}"
    local project_dir="${2:-}"
    local deadlock_file="$project_dir/meetings/deadlocks.md"

    if [ ! -f "$deadlock_file" ]; then
        echo -e "${RED}Nenhum deadlock registrado.${NC}"
        return
    fi

    # Encontra o deadlock
    local linha=""
    while IFS= read -r line; do
        if echo "$line" | grep -q "$deadlock_id"; then
            linha="$line"
            break
        fi
    done < "$deadlock_file"

    if [ -z "$linha" ]; then
        echo -e "${RED}Deadlock $deadlock_id não encontrado.${NC}"
        return
    fi

    echo -e "${CYAN}═══ RESOLVENDO DEADLOCK: $deadlock_id ═══${NC}"
    echo ""
    echo "Registrado: $linha"
    echo ""

    # Extrai tipo do deadlock
    local tipo
    tipo=$(echo "$linha" | awk -F'|' '{print $6}' | xargs)
    local agentes
    agentes=$(echo "$linha" | awk -F'|' '{print $4}' | xargs)

    echo -e "${YELLOW}Tipo:${NC} $tipo"
    echo -e "${YELLOW}Agentes envolvidos:${NC} $agentes"
    echo ""

    # Sugere regra de resolução
    echo -e "${CYAN}Regra aplicável:${NC}"
    local rule="${DEADLOCK_RULES[$tipo]:-${DEADLOCK_RULES["default"]}}"
    echo "  $rule"
    echo ""

    # Opções de resolução
    echo "Opções de resolução:"
    echo "  1) Aplicar regra automática"
    echo "  2) Convocar reunião entre agentes + coordenador"
    echo "  3) Registrar como resolvido manualmente"
    echo ""
    read -r -p "Selecione (1-3): " option

    case "$option" in
        1)
            do_resolve_auto "$deadlock_id" "$project_dir"
            ;;
        2)
            echo ""
            echo -e "${YELLOW}Convocando reunião...${NC}"
            local meetings_dir="$project_dir/meetings"
            local atas_dir="$meetings_dir/ata"
            mkdir -p "$atas_dir"

            local meeting_num
            meeting_num=$(find "$atas_dir" -name "*.md" 2>/dev/null | wc -l)
            meeting_num=$((meeting_num + 1))
            local meeting_id
            meeting_id=$(printf "MTG-%04d" "$meeting_num")

            cat > "$atas_dir/ata-$meeting_id.md" <<- EOF
# Ata — $meeting_id (Deadlock Resolution)

**Data:** $(date -Iseconds)
**Motivo:** Resolução de deadlock $deadlock_id
**Agentes:** $agentes
**Tipo:** $tipo

## Regra Aplicada

$rule

## Decisão

<!-- Preencher após reunião -->

## Resolução

- Deadlock $deadlock_id: [RESOLVIDO / PENDENTE]
- Data: $(date -Iseconds)
EOF
            echo -e "${GREEN}✓ Ata criada: $atas_dir/ata-$meeting_id.md${NC}"
            echo "  Convide os agentes para revisar e preencher."
            ;;
        3)
            read -r -p "Descreva a resolução: " resolucao
            echo ""
            echo -e "${YELLOW}Registrando resolução manual...${NC}"

            # Atualiza deadlock file
            local now
            now=$(date -Iseconds)
            local temp_file
            temp_file=$(mktemp)
            sed "s/| $deadlock_id |.*ABERTO.*/| $deadlock_id | $now | $agentes | $resolucao | $tipo | RESOLVIDO | $resolucao |/" "$deadlock_file" > "$temp_file" && mv "$temp_file" "$deadlock_file"

            echo -e "${GREEN}✓ Deadlock $deadlock_id marcado como RESOLVIDO.${NC}"

            # Log no events
            local events_file="$project_dir/context/.events.log"
            echo "[$now] DEADLOCK | RESOLVED | $deadlock_id | resolução=$resolucao" >> "$events_file"
            ;;
        *)
            echo -e "${RED}Opção inválida.${NC}"
            ;;
    esac
}

do_resolve_auto() {
    local deadlock_id="${1:-}"
    local project_dir="${2:-}"
    local deadlock_file="$project_dir/meetings/deadlocks.md"

    echo -e "${CYAN}Aplicando regra automática para $deadlock_id...${NC}"
    echo ""

    # Lê o deadlock atual
    local linha
    linha=$(grep "$deadlock_id" "$deadlock_file" 2>/dev/null || echo "")
    if [ -z "$linha" ]; then
        echo -e "${RED}Deadlock não encontrado.${NC}"
        return
    fi

    local tipo
    tipo=$(echo "$linha" | awk -F'|' '{print $6}' | xargs)

    local rule="${DEADLOCK_RULES[$tipo]:-${DEADLOCK_RULES["default"]}}"
    local auto_resolution=""

    case "$tipo" in
        "recurso:contexto")
            auto_resolution="Aplicado Regra 1: agente com maior proficiência mantém lock. Outro agenda revisão assíncrona."
            ;;
        "recurso:ferramenta")
            auto_resolution="Aplicado Regra 2: janelas de uso alternadas de 2h. Segunda instância provisionada se necessário."
            ;;
        "dependencia:resultado")
            auto_resolution="Aplicado Regra 3: resultado parcial publicado como PENDING. Placeholder para dependente."
            ;;
        "dependencia:decisao")
            auto_resolution="Aplicado Regra 4: coordenador decide com voto de desempate. Registrado em ata."
            ;;
        "contradicao:dado")
            auto_resolution="Aplicado Regra 5: matriz de prioridade (peer-reviewed > norma > data sheet > estimativa). Fonte de maior prioridade prevalece."
            ;;
        "contradicao:metodo")
            auto_resolution="Aplicado Regra 6: benchmark cego executado. Método com maior acurácia no problema padrão prevalece."
            ;;
        *)
            auto_resolution="Aplicado Regra geral: reunião convocada entre agentes e coordenador. Coordenador decide."
            ;;
    esac

    echo -e "${GREEN}$auto_resolution${NC}"
    echo ""

    # Atualiza deadlock file
    local now
    now=$(date -Iseconds)
    local temp_file
    temp_file=$(mktemp)
    sed "s/| $deadlock_id |.*ABERTO.*/| $deadlock_id | $now | - | - | $tipo | RESOLVIDO | $auto_resolution |/" "$deadlock_file" > "$temp_file" && mv "$temp_file" "$deadlock_file"

    # Registra no events
    local events_file="$project_dir/context/.events.log"
    echo "[$now] DEADLOCK | AUTO_RESOLVED | $deadlock_id | $auto_resolution" >> "$events_file"

    echo -e "${GREEN}✓ Deadlock $deadlock_id resolvido automaticamente.${NC}"
}

do_register() {
    local project_dir="${1:-}"
    local desc="${2:-}"
    local agentes="${3:-}"
    local tipo="${4:-dependencia:resultado}"

    local deadlock_file="$project_dir/meetings/deadlocks.md"
    local now
    now=$(date -Iseconds)

    # Gera ID
    local num
    num=$(grep -cE '^\|' "$deadlock_file" 2>/dev/null || echo 0)
    num=$((num - 2))  # header + separator
    [ "$num" -lt 0 ] && num=0
    num=$((num + 1))
    local dl_id
    dl_id=$(printf "DL-%04d" "$num")

    echo "| $dl_id | $now | $agentes | $desc | $tipo | ABERTO | |" >> "$deadlock_file"

    echo -e "${RED}✗${NC} Deadlock ${CYAN}$dl_id${NC} registrado: $desc"
    echo "  Agentes: $agentes | Tipo: $tipo"
    echo "  Use: coordinator.sh resolve $dl_id"
}

# ─── Dispatch ──────────────────────────────────────────────────────────────

case "$COMMAND" in
    list)
        do_list "${2:-}"
        ;;
    detect)
        do_detect "${2:-}"
        ;;
    resolve)
        do_resolve "${2:-}" "${3:-}"
        ;;
    resolve-auto)
        do_resolve_auto "${2:-}" "${3:-}"
        ;;
    register)
        do_register "${2:-}" "${3:-}" "${4:-}" "${5:-}"
        ;;
    *)
        echo "Uso: deadlock-resolver.sh <list|detect|resolve|resolve-auto|register> <args>"
        echo "  list <project-dir>              — Lista deadlocks"
        echo "  detect <project-dir>            — Detecta deadlocks"
        echo "  resolve <id> <dir>              — Resolve interativo"
        echo "  resolve-auto <id> <dir>         — Resolve automático"
        echo "  register <dir> <desc> <ags>     — Registra deadlock"
        exit 1
        ;;
esac
