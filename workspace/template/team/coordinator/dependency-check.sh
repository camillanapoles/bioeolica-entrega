#!/usr/bin/env bash
# dependency-check.sh
# Verificador de Dependências — Detecta interconexões M³×M³ entre agentes
#
# Uso: ./dependency-check.sh <comando> <args...>
#
# Comandos:
#   check <project-dir>             Verifica dependências entre agentes ativos
#   matrix <project-dir>            Mostra matriz de interconexão
#   strong <project-dir>            Lista apenas interconexões fortes
#   path <agent-a> <agent-b> <dir>  Mostra caminho de dependência entre agentes

set -euo pipefail

COMMAND="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Matrix de Interconexão M³×M³ ─────────────────────────────────────────
# Fonte: INSTRUCTIONS.md - m3_interconnection_matrix
# Pares (domínio_A ↔ domínio_B) com tipo de acoplamento por escala

declare -A INTERCONNECTION_MATRIX

# Formato: key = "dominio_A:dominio_B:escala", value = "tipo:descrição"
# Tipos: forte, fraco, serial, nenhum

# mecânica × fluidos
INTERCONNECTION_MATRIX["mecanica:fluidos:macro"]="forte:Cargas estruturais afetam escoamento; escoamento afeta cargas"
INTERCONNECTION_MATRIX["mecanica:fluidos:meso"]="forte:Interfaces fluido-estrutura (juntas, selos, palhetas)"
INTERCONNECTION_MATRIX["mecanica:fluidos:micro"]="fraco:Turbulência local afeta tensões superficiais"

# mecânica × termo
INTERCONNECTION_MATRIX["mecanica:termo:macro"]="forte:Cargas geram calor; temperatura altera rigidez"
INTERCONNECTION_MATRIX["mecanica:termo:meso"]="fraco:Expansão térmica diferencial em juntas"
INTERCONNECTION_MATRIX["mecanica:termo:micro"]="fraco:Tensões residuais térmicas em grãos"

# mecânica × eletricidade
INTERCONNECTION_MATRIX["mecanica:eletricidade:macro"]="fraco:Demanda estrutural define potência nominal"
INTERCONNECTION_MATRIX["mecanica:eletricidade:meso"]="forte:Acoplamento eletromecânico torque×corrente"
INTERCONNECTION_MATRIX["mecanica:eletricidade:micro"]="nenhum:Escalas separadas"

# mecânica × materiais
INTERCONNECTION_MATRIX["mecanica:materiais:macro"]="forte:Seleção de material por requisitos mecânicos"
INTERCONNECTION_MATRIX["mecanica:materiais:meso"]="forte:Propriedades em juntas e soldas"
INTERCONNECTION_MATRIX["mecanica:materiais:micro"]="forte:Microestrutura determina resistência"

# mecânica × construcao
INTERCONNECTION_MATRIX["mecanica:construcao:macro"]="forte:Processo de fabricação impõe restrições"
INTERCONNECTION_MATRIX["mecanica:construcao:meso"]="forte:Tensões residuais pós-soldagem/usinagem"
INTERCONNECTION_MATRIX["mecanica:construcao:micro"]="forte:Parâmetros de usinagem alteram microestrutura"

# fluidos × termo
INTERCONNECTION_MATRIX["fluidos:termo:macro"]="forte:Convecção domina transferência de calor"
INTERCONNECTION_MATRIX["fluidos:termo:meso"]="forte:Trocadores de calor, aletas, camisas"
INTERCONNECTION_MATRIX["fluidos:termo:micro"]="fraco:Camada limite térmica local"

# fluidos × energia
INTERCONNECTION_MATRIX["fluidos:energia:macro"]="forte:Escoamento é meio primário de conversão"
INTERCONNECTION_MATRIX["fluidos:energia:meso"]="fraco:Perdas de carga afetam eficiência"
INTERCONNECTION_MATRIX["fluidos:energia:micro"]="nenhum:Escalas separadas"

# termo × energia
INTERCONNECTION_MATRIX["termo:energia:macro"]="forte:Ciclo termodinâmico define eficiência"
INTERCONNECTION_MATRIX["termo:energia:meso"]="fraco:Trocadores individuais afetam ciclo"
INTERCONNECTION_MATRIX["termo:energia:micro"]="nenhum:Escalas separadas"

# eletricidade × energia
INTERCONNECTION_MATRIX["eletricidade:energia:macro"]="forte:Conversão eletromecânica define eficiência"
INTERCONNECTION_MATRIX["eletricidade:energia:meso"]="forte:Perdas no motor/gerador"
INTERCONNECTION_MATRIX["eletricidade:energia:micro"]="fraco:Microestrutura magnética afeta perdas"

# materiais × construcao
INTERCONNECTION_MATRIX["materiais:construcao:macro"]="forte:Material define processo de fabricação"
INTERCONNECTION_MATRIX["materiais:construcao:meso"]="forte:Processo altera propriedades do material"
INTERCONNECTION_MATRIX["materiais:construcao:micro"]="forte:Microestrutura determina resposta ao processo"

# construcao × normativo
INTERCONNECTION_MATRIX["construcao:normativo:macro"]="serial:Normas de processo (ASME IX, AWS D1.1)"
INTERCONNECTION_MATRIX["construcao:normativo:meso"]="serial:Qualificação de procedimento (PQR/WPQ)"
INTERCONNECTION_MATRIX["construcao:normativo:micro"]="nenhum:Escalas separadas"

# construcao × economico
INTERCONNECTION_MATRIX["construcao:economico:macro"]="forte:Custo de fabricação 30-70% do total"
INTERCONNECTION_MATRIX["construcao:economico:meso"]="fraco:Custo por etapa de fabricação"
INTERCONNECTION_MATRIX["construcao:economico:micro"]="fraco:Custo de material, scrap, retrabalho"

# ─── Helpers ───────────────────────────────────────────────────────────────

get_active_agents() {
    local project_dir="$1"
    local team_dir="$project_dir/team"
    local agents=()

    for agent_dir in "$team_dir"/agent-*/; do
        if [ -d "$agent_dir" ]; then
            agents+=("$(basename "$agent_dir")")
        fi
    done
    echo "${agents[@]}"
}

domain_from_agent() {
    local agent="$1"
    case "$agent" in
        agent-mecanica) echo "mecanica" ;;
        agent-fluidos) echo "fluidos" ;;
        agent-termo) echo "termo" ;;
        agent-energia) echo "energia" ;;
        agent-eletrica) echo "eletricidade" ;;
        agent-materiais) echo "materiais" ;;
        agent-construcao) echo "construcao" ;;
        agent-ambiente) echo "ambiente" ;;
        agent-normativo) echo "normativo" ;;
        agent-economico) echo "economico" ;;
        *) echo "unknown" ;;
    esac
}

# ─── Commands ──────────────────────────────────────────────────────────────

do_check() {
    local project_dir="$1"
    echo -e "${CYAN}Verificando dependências entre agentes...${NC}"
    echo ""

    local agents
    agents=$(get_active_agents "$project_dir")
    if [ -z "$agents" ]; then
        echo -e "${YELLOW}Nenhum agente ativo encontrado. Execute 'derive-team' primeiro.${NC}"
        return
    fi

    echo -e "${YELLOW}Agentes ativos:${NC}"
    for a in $agents; do
        echo "  - $a (domínio: $(domain_from_agent "$a"))"
    done
    echo ""

    local has_strong=false

    for agent_a in $agents; do
        local domain_a
        domain_a=$(domain_from_agent "$agent_a")
        [ "$domain_a" = "unknown" ] && continue

        for agent_b in $agents; do
            [ "$agent_a" = "$agent_b" ] && continue

            local domain_b
            domain_b=$(domain_from_agent "$agent_b")
            [ "$domain_b" = "unknown" ] && continue

            # Verifica interconexão por escala
            for escala in macro meso micro; do
                local key1="$domain_a:$domain_b:$escala"
                local key2="$domain_b:$domain_a:$escala"
                local val="${INTERCONNECTION_MATRIX[$key1]:-${INTERCONNECTION_MATRIX[$key2]:-}}"

                if [ -n "$val" ]; then
                    local tipo="${val%%:*}"
                    local desc="${val#*:}"

                    local cor="$GREEN"
                    [ "$tipo" = "forte" ] && cor="$RED"
                    [ "$tipo" = "serial" ] && cor="$YELLOW"

                    echo -e "  $agent_a ↔ $agent_b (${CYAN}$escala${NC}): ${cor}$tipo${NC} — $desc"
                    [ "$tipo" = "forte" ] && has_strong=true
                fi
            done
        done
    done

    echo ""
    if $has_strong; then
        echo -e "${RED}⚠ Interconexões FORTES detectadas. Reunião de sincronização necessária.${NC}"
        echo "  Use: coordinator.sh schedule para convocar reunião entre os agentes acoplados."
    else
        echo -e "${GREEN}✓ Nenhuma interconexão forte detectada. Agentes podem trabalhar em paralelo.${NC}"
    fi
}

do_matrix() {
    local project_dir="$1"
    echo -e "${CYAN}Matriz de Interconexão M³×M³${NC}"
    echo ""

    local agents
    agents=$(get_active_agents "$project_dir")
    if [ -z "$agents" ]; then
        echo -e "${YELLOW}Nenhum agente ativo.${NC}"
        return
    fi

    local domains=()
    for a in $agents; do
        local d
        d=$(domain_from_agent "$a")
        [ "$d" != "unknown" ] && domains+=("$d")
    done

    # Cabeçalho
    printf "%-14s" ""
    for d in "${domains[@]}"; do
        printf "%-12s" "$d"
    done
    echo ""

    for d1 in "${domains[@]}"; do
        printf "%-14s" "$d1"
        for d2 in "${domains[@]}"; do
            if [ "$d1" = "$d2" ]; then
                printf "%-12s" "—"
                continue
            fi
            # Checa qualquer escala com interconexão forte
            local tipo=""
            for e in macro meso micro; do
                local v="${INTERCONNECTION_MATRIX["$d1:$d2:$e"]:-${INTERCONNECTION_MATRIX["$d2:$d1:$e"]:-}}"
                if [ -n "$v" ]; then
                    local t="${v%%:*}"
                    if [ "$t" = "forte" ]; then
                        tipo="forte"
                        break
                    elif [ "$t" = "fraco" ] || [ "$t" = "serial" ]; then
                        tipo="$t"
                    fi
                fi
            done

            local cor="$GREEN"
            [ "$tipo" = "forte" ] && cor="$RED"
            [ "$tipo" = "serial" ] && cor="$YELLOW"
            [ -z "$tipo" ] && tipo="—" && cor="$NC"
            printf "${cor}%-12s${NC}" "$tipo"
        done
        echo ""
    done

    echo ""
    echo -e "Legenda: ${RED}forte${NC}=reunião necessária  ${GREEN}fraco${NC}=sequencial OK  ${YELLOW}serial${NC}=passagem de dados"
}

do_strong() {
    local project_dir="$1"
    echo -e "${YELLOW}Interconexões FORTES detectadas (requerem reunião):${NC}"
    echo ""

    local agents
    agents=$(get_active_agents "$project_dir")
    local found=false

    for agent_a in $agents; do
        local domain_a
        domain_a=$(domain_from_agent "$agent_a")
        [ "$domain_a" = "unknown" ] && continue

        for agent_b in $agents; do
            [ "$agent_a" = "$agent_b" ] && continue
            local domain_b
            domain_b=$(domain_from_agent "$agent_b")
            [ "$domain_b" = "unknown" ] && continue

            for escala in macro meso micro; do
                local key1="$domain_a:$domain_b:$escala"
                local key2="$domain_b:$domain_a:$escala"
                local val="${INTERCONNECTION_MATRIX[$key1]:-${INTERCONNECTION_MATRIX[$key2]:-}}"

                if [ -n "$val" ]; then
                    local tipo="${val%%:*}"
                    if [ "$tipo" = "forte" ]; then
                        local desc="${val#*:}"
                        echo -e "  ${RED}✗${NC} $agent_a ↔ $agent_b (${CYAN}$escala${NC})"
                        echo "    $desc"
                        found=true
                    fi
                fi
            done
        done
    done

    if ! $found; then
        echo "  (nenhuma)"
    fi
}

do_path() {
    local agent_a="$1"
    local agent_b="$2"
    local project_dir="$3"
    local domain_a
    local domain_b
    domain_a=$(domain_from_agent "$agent_a")
    domain_b=$(domain_from_agent "$agent_b")

    echo -e "${CYAN}Caminho de dependência: $agent_a → $agent_b${NC}"
    echo "  Domínios: $domain_a → $domain_b"
    echo ""

    # Caminho direto
    local direct_key="$domain_a:$domain_b"
    local found=false
    for e in macro meso micro; do
        local v="${INTERCONNECTION_MATRIX["$domain_a:$domain_b:$e"]:-}"
        if [ -n "$v" ]; then
            local tipo="${v%%:*}"
            local desc="${v#*:}"
            echo -e "  Caminho direto ($e): ${tipo} — $desc"
            found=true
        fi
    done

    if ! $found; then
        echo "  Nenhuma interconexão direta. Verificar caminho indireto via domínio intermediário."
        # Busca intermediário
        for mid in mecanica fluidos termo energia eletricidade materiais construcao ambiente normativo economico; do
            [ "$mid" = "$domain_a" ] && continue
            [ "$mid" = "$domain_b" ] && continue
            local a_mid_key="$domain_a:$mid"
            local mid_b_key="$mid:$domain_b"
            local a_mid_val="${INTERCONNECTION_MATRIX["$domain_a:$mid:macro"]:-}"
            local mid_b_val="${INTERCONNECTION_MATRIX["$mid:$domain_b:macro"]:-}"
            if [ -n "$a_mid_val" ] && [ -n "$mid_b_val" ]; then
                echo -e "  Caminho indireto via ${CYAN}$mid${NC}: $domain_a → $mid → $domain_b"
                break
            fi
        done
    fi
}

# ─── Dispatch ──────────────────────────────────────────────────────────────

case "$COMMAND" in
    check)
        do_check "${2:-}"
        ;;
    matrix)
        do_matrix "${2:-}"
        ;;
    strong)
        do_strong "${2:-}"
        ;;
    path)
        do_path "${2:-}" "${3:-}" "${4:-}"
        ;;
    *)
        echo "Uso: dependency-check.sh <check|matrix|strong|path> <args>"
        echo "  check <project-dir>         — Verifica dependências"
        echo "  matrix <project-dir>        — Mostra matriz completa"
        echo "  strong <project-dir>        — Lista apenas fortes"
        echo "  path <agent-a> <agent-b>    — Caminho entre agentes"
        exit 1
        ;;
esac
