#!/usr/bin/env bash
# agent-factory.sh
# Fábrica de Agentes — Deriva a composição do time a partir do domain map
#
# Lê o relevance_check.md (F2) e para cada domínio confirmado (✅ ou "Sim"),
# gera um agente especialista com proficiência herdada da engine.
#
# Uso: ./agent-factory.sh <domain-map> <project-dir>

set -euo pipefail

DOMAIN_MAP="${1:-}"
PROJECT_DIR="${2:-}"

if [ -z "$DOMAIN_MAP" ] || [ ! -f "$DOMAIN_MAP" ]; then
    echo "ERRO: domain map não encontrado"
    exit 1
fi

TEAM_DIR="$PROJECT_DIR/team"
COORD_DIR="$TEAM_DIR/coordinator"
CONTEXT_DIR="$PROJECT_DIR/context"
COMPOSITION_FILE="$COORD_DIR/team-composition.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Mapa Domínio → Agente ─────────────────────────────────────────────────
# Cada domínio confirmado gera um agente com proficiência padrão.
# A proficiência pode ser override posteriormente (task #12 do plano).

declare -A DOMAIN_AGENT_MAP
DOMAIN_AGENT_MAP["Mecânica"]="agent-mecanica"
DOMAIN_AGENT_MAP["Fluidos"]="agent-fluidos"
DOMAIN_AGENT_MAP["Termodinâmica"]="agent-termo"
DOMAIN_AGENT_MAP["Energia"]="agent-energia"
DOMAIN_AGENT_MAP["Eletricidade"]="agent-eletrica"
DOMAIN_AGENT_MAP["Materiais"]="agent-materiais"
DOMAIN_AGENT_MAP["Construção"]="agent-construcao"
DOMAIN_AGENT_MAP["Ambiente"]="agent-ambiente"
DOMAIN_AGENT_MAP["Normativo"]="agent-normativo"
DOMAIN_AGENT_MAP["Econômico"]="agent-economico"

declare -A DOMAIN_AGENT_EN
DOMAIN_AGENT_EN["Mecânica"]="mecanica"
DOMAIN_AGENT_EN["Fluidos"]="fluidos"
DOMAIN_AGENT_EN["Termodinâmica"]="termo"
DOMAIN_AGENT_EN["Energia"]="energia"
DOMAIN_AGENT_EN["Eletricidade"]="eletricidade"
DOMAIN_AGENT_EN["Materiais"]="materiais"
DOMAIN_AGENT_EN["Construção"]="construcao"
DOMAIN_AGENT_EN["Ambiente"]="ambiente"
DOMAIN_AGENT_EN["Normativo"]="normativo"
DOMAIN_AGENT_EN["Econômico"]="economico"

# Proficiência base por domínio (do KDI core_capabilities)
declare -A DOMAIN_PROFICIENCY
DOMAIN_PROFICIENCY["Mecânica"]=5
DOMAIN_PROFICIENCY["Fluidos"]=4
DOMAIN_PROFICIENCY["Termodinâmica"]=4
DOMAIN_PROFICIENCY["Energia"]=3
DOMAIN_PROFICIENCY["Eletricidade"]=4
DOMAIN_PROFICIENCY["Materiais"]=4
DOMAIN_PROFICIENCY["Construção"]=3
DOMAIN_PROFICIENCY["Ambiente"]=3
DOMAIN_PROFICIENCY["Normativo"]=4
DOMAIN_PROFICIENCY["Econômico"]=3

# ─── Processamento ─────────────────────────────────────────────────────────

echo -e "${CYAN}Fábrica de Agentes — Derivando time do domínio${NC}"
echo "Fonte: $DOMAIN_MAP"
echo ""

CONFIRMED_DOMAINS=()
AGENTS_CREATED=0

# Lê o relevance_check.md e identifica domínios confirmados
while IFS='|' read -r _ domain applies rest; do
    domain=$(echo "$domain" | xargs)
    applies=$(echo "$applies" | xargs)

    # Pula cabeçalho e separador
    [[ "$domain" =~ ^-+$ ]] && continue
    [[ "$domain" =~ ^(Domínio|-----)$ ]] && continue
    [[ "$domain" =~ ^\s*$ ]] && continue
    [ -z "$domain" ] && continue

    # Verifica se é um domínio confirmado (✅, Sim, sim, Yes, yes, S, s, X, x)
    if echo "$applies" | grep -qiE '(✅|sim|yes|s|x)' 2>/dev/null; then
        CONFIRMED_DOMAINS+=("$domain")
        echo -e "  ${GREEN}✓${NC} $domain → CONFIRMADO"
    else
        echo -e "  ${YELLOW}—${NC} $domain → não aplica (ou não preenchido)"
    fi
done < "$DOMAIN_MAP"

echo ""
echo -e "${CYAN}────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}  Time derivado:${NC}"
echo ""

if [ ${#CONFIRMED_DOMAINS[@]} -eq 0 ]; then
    echo -e "${YELLOW}Nenhum domínio confirmado. Preencha o relevance_check.md primeiro.${NC}"
    echo ""
    echo "Formato esperado: | Domínio | Aplica? | Justificativa |"
    echo "Exemplo:          | Mecânica | ✅ Sim | Cargas estruturais na pá |"

    # Gera composição vazia
    cat > "$COMPOSITION_FILE" <<- EOF
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
    exit 0
fi

# Cria composição do time
{
    echo "# Composição do Time — $(basename "$PROJECT_DIR")"
    echo ""
    echo "## Domínios Confirmados"
    echo ""
    echo "| Domínio | Agente | Proficiência | Status |"
    echo "|---------|--------|--------------|--------|"
} > "$COMPOSITION_FILE"

for domain in "${CONFIRMED_DOMAINS[@]}"; do
    agent_name="${DOMAIN_AGENT_MAP[$domain]:-agent-$(echo "$domain" | tr '[:upper:]' '[:lower:]' | sed 's/ç/c/g; s/ã/a/g; s/ó/o/g; s/é/e/g')}"
    proficiency="${DOMAIN_PROFICIENCY[$domain]:-3}"
    agent_dir="$TEAM_DIR/$agent_name"

    # Cria diretório do agente se não existir
    if [ ! -d "$agent_dir" ]; then
        mkdir -p "$agent_dir"
        mkdir -p "$agent_dir/analises"
        mkdir -p "$agent_dir/contextos"
        mkdir -p "$agent_dir/logs"

        # Cria README do agente
        cat > "$agent_dir/README.md" <<- EOF
# $agent_name

**Domínio:** $domain
**Proficiência:** $proficiency (1-5)
**Criado por:** Coordenador em $(date -Iseconds)

## Responsabilidades

- Análises computacionais no domínio de $domain
- Publicação de contextos via quality gates
- Participação em reuniões quando convocado

## Diretórios

- \`analises/\` — Relatórios de análise
- \`contextos/\` — Contextos em produção (antes da publicação)
- \`logs/\` — Logs 5W1H das ações do agente
EOF
        echo -e "  ${GREEN}✓${NC} $domain → ${CYAN}$agent_name${NC} criado (proficiência $proficiency)"
    else
        echo -e "  ${GREEN}✓${NC} $domain → ${CYAN}$agent_name${NC} já existe (proficiência $proficiency)"
    fi

    AGENTS_CREATED=$((AGENTS_CREATED + 1))

    # Adiciona à composição
    echo "| $domain | $agent_name | $proficiency | ATIVO |" >> "$COMPOSITION_FILE"
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  $AGENTS_CREATED agentes criados/confirmados${NC}"
echo -e "${GREEN}  Composição salva em: $COMPOSITION_FILE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Próximo passo: Alocar tarefas com: coordinator.sh allocate \"<desc>\" <agente>${NC}"
