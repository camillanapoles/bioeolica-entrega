# Perfil de Agente — Template
#
# Este diretório é o template base para agentes especialistas.
# O coordenador copia este template quando convoca um novo agente.
#
# Estrutura:
#   INSTRUCTIONS.md   — Engine herdada + override de proficiência
#   proficiency.json   — Perfil de proficiência do agente
#   tasks.md           — Tarefas alocadas pelo coordenador
#   agenda.md          — Reuniões e compromissos
#
# Regras:
#   1. Escreva apenas neste diretório
#   2. Publique contextos via propagation-proto.sh
#   3. Sincronize via shared/
#   4. Documente no WAL
#   5. Submeta a quality gates antes de publicar
