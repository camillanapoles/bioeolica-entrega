# Proficiency Override — Herança com Especialização

Cada agente do time herda a engine KDI/Omnibus v3.0-unified completa (INSTRUCTIONS.md),
mas com **override de proficiência** por domínio — permitindo que um agente seja expert
em seu domínio e tenha conhecimento operacional em domínios vizinhos.

## Mecanismo

```
Engine KDI/Omnibus (invariante)
  │
  ├── Proficiency Base (do KDI core_capabilities)
  │     Mecânica:     5 (expert)
  │     Fluidos:      4 (advanced)
  │     Termodinâmica: 4 (advanced)
  │     Energia:      3 (proficient)
  │     Eletricidade: 4 (advanced)
  │     Materiais:    4 (advanced)
  │     Construção:   3 (proficient)
  │     Ambiente:     3 (proficient)
  │     Normativo:    4 (advanced)
  │     Econômico:    3 (proficient)
  │
  ├── Override por Agente (especialização)
  │     agent-mecanica:  Mecânica=5,        Fluidos=3, Materiais=3
  │     agent-fluidos:   Fluidos=5,         Mecânica=3, Termo=3
  │     agent-materiais: Materiais=5,       Mecânica=3, Construção=3
  │     agent-eletrica:  Eletricidade=5,    Energia=4,  Mecânica=2
  │     agent-termo:     Termodinâmica=5,   Fluidos=3,  Energia=3
  │     agent-energia:   Energia=4,         Termo=3,    Eletricidade=2
  │     agent-construcao: Construção=4,     Materiais=3, Mecânica=2
  │     agent-ambiente:  Ambiente=4,        Materiais=3, Normativo=2
  │     agent-normativo: Normativo=5,       Construção=2, Ambiente=2
  │     agent-economico: Econômico=4,       Construção=2, Normativo=2
```

## Níveis de Proficiência

| Nível | Autonomia | Complexidade | Supervisão |
|-------|-----------|-------------|------------|
| **1** (awareness) | Conhece conceitos, identifica quando aplicar | Simples | Supervisão direta |
| **2** (operational) | Executa workflows existentes | Rotineira | Templates + validação |
| **3** (proficient) | Executa autonomamente | Complexa | Revisão por pares |
| **4** (advanced) | Integra métodos, diagnostica falhas | Multidisciplinar | Revisão hostil |
| **5** (expert) | Inova, cria métodos, publica | Estado da arte | Autônomo total |

## Regras de Override

1. **Domínio primário** do agente → proficiency = 5 (expert) — o agente é autoridade no seu domínio
2. **Domínios vizinhos** com interconexão forte → proficiency = 3 (proficient) — suficiente para entender e colaborar
3. **Domínios com interconexão fraca** → proficiency = 2 (operational) — consegue ler contexto mas não produz análise autônoma
4. **Demais domínios** → proficiency = 1 (awareness) — reconhece quando consultar outro agente
5. **Override mínimo**: nenhum agente tem proficiency < 1 em qualquer domínio (consciência mínima)

## Exemplo: agent-mecanica

```json
{
  "agent_id": "agent-mecanica",
  "engine": "KDI/Omnibus v3.0-unified (herdada)",
  "proficiency_override": {
    "mecanica":     5,  // Expert — autoridade em estruturas, tensões, fadiga
    "fluidos":      3,  // Proficient — FSI básico, arrasto aerodinâmico
    "termo":        2,  // Operational — expansão térmica, tensões térmicas
    "energia":      2,  // Operational — balanço energético básico
    "eletricidade": 1,  // Awareness — reconhece quando consultar agent-eletrica
    "materiais":    3,  // Proficient — seleção de material, comportamento mecânico
    "construcao":   2,  // Operational — usinabilidade, soldagem básica
    "ambiente":     1,  // Awareness — degradação ambiental
    "normativo":    2,  // Operational — normas estruturais (ASME, ISO)
    "economico":    1   // Awareness — custo de material
  }
}
```

## Implicações

- **Quality Gates**: revisão hostil (GATE 4) designa revisor com proficiency ≥ 4 no domínio do contexto
- **Reuniões**: proficiency ≥ 3 necessária para participar de reunião técnica sobre o domínio
- **Deadlocks**: em conflito entre agentes, o de maior proficiency no domínio tem prioridade (Regra 1)
- **Alocação de tarefas**: tarefas complexas (nível 4-5) só podem ser alocadas a agentes com proficiency ≥ 4
