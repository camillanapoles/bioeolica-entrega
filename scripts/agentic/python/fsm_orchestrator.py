#!/usr/bin/env python3
"""
FSM Orchestrator — Agente de Ciclo de Produção.

Fluxo obrigatório:
  SPECIFY → HUMAN_GATE → MAD → HUMAN_GATE → TASKS → EXECUTE → SELF_HEALING → DONE

Uso:
    python fsm_orchestrator.py specify   # Inicia SPECIFY
    python fsm_orchestrator.py plan      # Inicia MAD/plan
    python fsm_orchestrator.py execute   # Inicia EXECUTE
    python fsm_orchestrator.py status    # Mostra estado atual
"""
import json, os, sys
from datetime import datetime, timezone

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state.json")


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"phase": "NONE", "human_approved": {}, "tasks": [], "errors": []}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_specify():
    state = load_state()
    state["phase"] = "SPECIFY"
    state["started_at"] = datetime.now(timezone.utc).isoformat()
    print("SPECIFY >> Phase: SPECIFY")
    print("SPECIFY >> Gerando especificação...")
    save_state(state)
    print("SPECIFY >> Pronto para approval humana. Execute: fsm_orchestrator.py approve <y/n>")


def run_plan():
    state = load_state()
    if not state.get("human_approved", {}).get("specify", False):
        print("PLAN >> ERRO: SPECIFY não aprovado. Execute 'fsm_orchestrator.py approve specify y' primeiro")
        sys.exit(1)
    state["phase"] = "MAD"
    print("PLAN >> Phase: MAD (Modelo-Arquitetura-Design)")
    save_state(state)
    print("PLAN >> Design concluído. Pronto para approval.")


def run_execute():
    state = load_state()
    if not state.get("human_approved", {}).get("plan", False):
        print("EXECUTE >> ERRO: MAD/PLAN não aprovado")
        sys.exit(1)
    state["phase"] = "EXECUTE"
    print("EXECUTE >> Executando...")
    save_state(state)
    print("EXECUTE >> Concluído. Verificando TASKS.")


def run_approve(target: str):
    state = load_state()
    state.setdefault("human_approved", {})
    state["human_approved"][target] = True
    save_state(state)
    print(f"APPROVE >> {target} aprovado.")


def run_status():
    state = load_state()
    print(f"Status: {state.get('phase', 'NONE')}")
    for k, v in state.get("human_approved", {}).items():
        print(f"  {k}: {'✅' if v else '❌'}")
    print(f"  Tasks: {len(state.get('tasks', []))}")
    print(f"  Errors: {len(state.get('errors', []))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fsm_orchestrator.py <specify|plan|execute|status|approve> [args]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "specify":
        run_specify()
    elif command == "plan":
        run_plan()
    elif command == "execute":
        run_execute()
    elif command == "approve" and len(sys.argv) >= 3:
        run_approve(sys.argv[2])
    elif command == "status":
        run_status()
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)
