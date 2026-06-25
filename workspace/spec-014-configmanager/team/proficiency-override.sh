#!/usr/bin/env bash
# proficiency-override.sh
# Sistema de Herança com Proficiency Override — cada agente herda a engine
# KDI/Omnibus v3.0 com override de proficiência por especialidade.
#
# Uso: ./proficiency-override.sh init <agent-id> <domain>
#       ./proficiency-override.sh list
#       ./proficiency-override.sh show <agent-id>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAM_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENT_TEMPLATE="$TEAM_DIR/agent-template"
PROFICIENCY_DB="$TEAM_DIR/proficiency-db.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Base de Proficiência — Domínios × Níveis ─────────────────────────────
# Cada entrada define o perfil de proficiência (1-5) de um agente em cada
# capability da engine KDI/Omnibus v3.0.
#
# Níveis: 1_awareness, 2_operational, 3_proficient, 4_advanced, 5_expert

PROFICIENCY_DEFAULTS='{
  "agent-materiais": {
    "domain": "Engenharia de Materiais",
    "overrides": {
      "materials_science": 5,
      "structural_analysis": 3,
      "computational_analysis": 4,
      "fluid_dynamics": 2,
      "energy_systems": 2,
      "manufacturing_production": 3
    }
  },
  "agent-mecanica": {
    "domain": "Engenharia Mecânica",
    "overrides": {
      "structural_analysis": 5,
      "computational_analysis": 5,
      "fluid_dynamics": 3,
      "materials_science": 3,
      "energy_systems": 3,
      "manufacturing_production": 4
    }
  },
  "agent-fluidos": {
    "domain": "Mecânica dos Fluidos",
    "overrides": {
      "fluid_dynamics": 5,
      "computational_analysis": 4,
      "structural_analysis": 2,
      "materials_science": 2,
      "energy_systems": 4,
      "manufacturing_production": 2
    }
  },
  "agent-termo": {
    "domain": "Termodinâmica",
    "overrides": {
      "energy_systems": 5,
      "computational_analysis": 3,
      "fluid_dynamics": 4,
      "materials_science": 3,
      "structural_analysis": 2,
      "manufacturing_production": 2
    }
  },
  "agent-eletricidade": {
    "domain": "Engenharia Eletrotécnica",
    "overrides": {
      "computational_analysis": 4,
      "energy_systems": 4,
      "materials_science": 2,
      "structural_analysis": 2,
      "fluid_dynamics": 1,
      "manufacturing_production": 3
    }
  },
  "agent-energia": {
    "domain": "Sistemas Energéticos",
    "overrides": {
      "energy_systems": 5,
      "fluid_dynamics": 3,
      "computational_analysis": 3,
      "materials_science": 2,
      "structural_analysis": 2,
      "manufacturing_production": 2
    }
  },
  "agent-construcao": {
    "domain": "Métodos de Construção",
    "overrides": {
      "manufacturing_production": 5,
      "structural_analysis": 4,
      "computational_analysis": 3,
      "materials_science": 3,
      "fluid_dynamics": 2,
      "energy_systems": 2
    }
  },
  "agent-ambiente": {
    "domain": "Engenharia Ambiental",
    "overrides": {
      "materials_science": 3,
      "fluid_dynamics": 3,
      "energy_systems": 3,
      "computational_analysis": 2,
      "structural_analysis": 2,
      "manufacturing_production": 2
    }
  },
  "agent-normativo": {
    "domain": "Engenharia Normativa",
    "overrides": {
      "materials_science": 3,
      "structural_analysis": 3,
      "energy_systems": 2,
      "computational_analysis": 2,
      "fluid_dynamics": 2,
      "manufacturing_production": 3
    }
  },
  "agent-economico": {
    "domain": "Engenharia Econômica",
    "overrides": {
      "energy_systems": 3,
      "manufacturing_production": 3,
      "structural_analysis": 2,
      "materials_science": 2,
      "computational_analysis": 2,
      "fluid_dynamics": 1
    }
  }
}'

# ─── Help ──────────────────────────────────────────────────────────────────

if [ $# -lt 1 ]; then
    echo -e "${CYAN}Proficiency Override System${NC}"
    echo -e "Herança da engine KDI/Omnibus v3.0 com override por especialidade"
    echo ""
    echo "Comandos:"
    echo "  init <agent-id> <domain>   Gera agente com perfil de proficiência"
    echo "  list                        Lista todos os perfis disponíveis"
    echo "  show <agent-id>            Mostra perfil de proficiência do agente"
    echo "  capabilities               Lista capabilities da engine base"
    exit 0
fi

COMMAND="$1"
shift

# ─── init ──────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "init" ]; then
    AGENT_ID="${1:-}"
    DOMAIN="${2:-}"

    if [ -z "$AGENT_ID" ]; then
        echo -e "${RED}ERRO: informe agent-id${NC}"
        exit 1
    fi

    AGENT_DIR="$TEAM_DIR/$AGENT_ID"
    mkdir -p "$AGENT_DIR"

    echo -e "${CYAN}Inicializando agente: $AGENT_ID${NC}"
    echo -e "${CYAN}Domínio: ${DOMAIN:-não especificado}${NC}"
    echo ""

    # Carrega perfil de proficiência do banco de dados
    PROFILE_FILE="$AGENT_DIR/proficiency.json"
    if echo "$PROFICIENCY_DEFAULTS" | jq -e ".$AGENT_ID" > /dev/null 2>&1; then
        echo "$PROFICIENCY_DEFAULTS" | jq ".$AGENT_ID" > "$PROFILE_FILE"
        echo -e "${GREEN}✓ Perfil carregado do banco de proficiência${NC}"
    else
        # Perfil genérico (nível 3 em tudo)
        cat > "$PROFILE_FILE" << JSONEOF
{
  "agent_id": "$AGENT_ID",
  "domain": "${DOMAIN:-general}",
  "overrides": {
    "computational_analysis": 3,
    "fluid_dynamics": 3,
    "materials_science": 3,
    "structural_analysis": 3,
    "energy_systems": 3,
    "manufacturing_production": 3
  },
  "note": "Perfil genérico — personalize as proficiências para a especialidade do agente"
}
JSONEOF
        echo -e "${YELLOW}⚠ Perfil genérico criado (proficiency 3 em todas capabilities)${NC}"
        echo -e "  Edite $PROFILE_FILE para personalizar${NC}"
    fi

    # Gera INSTRUCTIONS.md do agente (engine herdada + overrides)
    AGENT_INSTRUCTIONS="$AGENT_DIR/INSTRUCTIONS.md"
    cat > "$AGENT_INSTRUCTIONS" << MDEOF
# ${AGENT_ID} — Agente Especialista

## Herança

Este agente herda a engine **KDI/Omnibus v3.0** definida em \`INSTRUCTIONS.md\` (raiz do projeto).

## Especialidade

- **Domínio:** ${DOMAIN:-não especificado}
- **Proficiência:** $(echo "$PROFICIENCY_DEFAULTS" | jq -r ".[\"$AGENT_ID\"].overrides // {} | to_entries | sort_by(-.value) | .[:3] | .[] | \"\(.key)=\(.value | tostring)\"" 2>/dev/null | tr '\n' ', ' | sed 's/,$//' || "genérica (nível 3)")

## Autonomia por Atividade

| Atividade | Nível Mínimo | Autonomia |
|-----------|-------------|-----------|
| Análise simples | proficiency ≥ 2 | Autônomo — executa sem supervisão |
| Análise complexa | proficiency ≥ 3 | Autônomo — executa com checkpoint humano |
| Integração multifísica | proficiency ≥ 4 | Autônomo — lidera integração |
| Inovação/P&D | proficiency ≥ 5 | Autônomo total — cria novos métodos |
| Fora da especialidade | proficiency < 2 | Requer supervisão de agente com nível ≥ 3 |

## Regras de Atuação

1. **Escreva apenas em seu diretório** (\`team/${AGENT_ID}/\`)
2. **Publique contextos** via \`context/propagation-proto.sh publish\`
3. **Sincronize resultados** via \`shared/\`
4. **Participe de reuniões** convocadas pelo Coordenador
5. **Documente no WAL** — toda ação requer log 5W1H
6. **Submeta a quality gates** antes de publicar em shared/
7. **Consulte o Coordenador** para tarefas com interconexão forte
MDEOF

    # Gera .agenda.md local do agente
    cat > "$AGENT_DIR/agenda.md" << AGENDAEOF
# Agenda — ${AGENT_ID}

## Tarefas Atuais

*(a definir pelo Coordenador)*

## Reuniões Agendadas

*(nenhuma)*

## Dependências

- **Fornece contexto para:** *(mapear durante execução)*
- **Depende de contexto de:** *(mapear durante execução)*
AGENDAEOF

    echo -e "${GREEN}✓ Instruções do agente geradas: $AGENT_INSTRUCTIONS${NC}"
    echo -e "${GREEN}✓ Perfil de proficiência: $PROFILE_FILE${NC}"
    echo ""
    echo -e "${YELLOW}Perfil de proficiência:${NC}"
    echo "$PROFICIENCY_DEFAULTS" | jq -r ".[\"$AGENT_ID\"].overrides // {} | to_entries | sort_by(-.value) | .[] | \"  \(.key): \(.value | tostring) — \(.value | if . >= 5 then \"Expert\" elif . >= 4 then \"Advanced\" elif . >= 3 then \"Proficient\" elif . >= 2 then \"Operational\" else \"Awareness\" end)\"" 2>/dev/null || echo "  (genérico)"

    exit 0
fi

# ─── list ──────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "list" ]; then
    echo -e "${CYAN}Perfis de Proficiência Disponíveis:${NC}"
    echo ""

    echo "$PROFICIENCY_DEFAULTS" | jq -r '
        to_entries | sort_by(.key) | .[] |
        "  \(.key) (\(.value.domain)):" +
        ([.value.overrides | to_entries | sort_by(-.value) | .[0].key] | join(", "))
    '

    echo ""
    echo -e "Para criar um agente: ${CYAN}./proficiency-override.sh init <agent-id>${NC}"
    exit 0
fi

# ─── show ──────────────────────────────────────────────────────────────────

if [ "$COMMAND" = "show" ]; then
    AGENT_ID="${1:-}"
    if [ -z "$AGENT_ID" ]; then
        echo -e "${RED}ERRO: informe agent-id${NC}"
        exit 1
    fi

    echo -e "${CYAN}Perfil de Proficiência: $AGENT_ID${NC}"
    echo ""

    # Tenta do banco de dados primeiro
    if echo "$PROFICIENCY_DEFAULTS" | jq -e ".$AGENT_ID" > /dev/null 2>&1; then
        echo "$PROFICIENCY_DEFAULTS" | jq -r "
            .[\"$AGENT_ID\"].overrides | to_entries | sort_by(-.value) | .[] |
            \"  \(.key): \" +
            (if .value >= 5 then \"★★★★★ Expert\"
             elif .value >= 4 then \"★★★★☆ Advanced\"
             elif .value >= 3 then \"★★★☆☆ Proficient\"
             elif .value >= 2 then \"★★☆☆☆ Operational\"
             else \"★☆☆☆☆ Awareness\" end) +
            \" (nível \(.value | tostring))\"
        "
    elif [ -f "$TEAM_DIR/$AGENT_ID/proficiency.json" ]; then
        cat "$TEAM_DIR/$AGENT_ID/proficiency.json"
    else
        echo -e "${YELLOW}Perfil não encontrado para: $AGENT_ID${NC}"
        echo "Crie com: ./proficiency-override.sh init $AGENT_ID"
        exit 1
    fi

    exit 0
fi

# ─── capabilities ──────────────────────────────────────────────────────────

if [ "$COMMAND" = "capabilities" ]; then
    echo -e "${CYAN}Capabilities da Engine KDI/Omnibus v3.0:${NC}"
    echo ""
    echo "  computational_analysis   — Análise computacional (FEM, MPM, SPH, CFD, ...)"
    echo "  fluid_dynamics           — Mecânica dos fluidos e CFD"
    echo "  materials_science        — Ciência e engenharia de materiais"
    echo "  structural_analysis      — Análise estrutural e tensões"
    echo "  energy_systems           — Sistemas energéticos e termodinâmica"
    echo "  manufacturing_production — Processos de fabricação e manufatura"
    echo ""
    echo -e "Níveis: ${YELLOW}1${NC}=Awareness ${YELLOW}2${NC}=Operational ${YELLOW}3${NC}=Proficient ${YELLOW}4${NC}=Advanced ${YELLOW}5${NC}=Expert"
    exit 0
fi

# ─── Comando desconhecido ──────────────────────────────────────────────────

echo -e "${RED}Comando desconhecido: $COMMAND${NC}"
echo "Comandos válidos: init, list, show, capabilities"
exit 1
