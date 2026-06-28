#!/usr/bin/env python3
"""Update FSM state to DONE."""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
with open(STATE_FILE) as f:
    state = json.load(f)
state["phase"] = "DONE"
state["tasks"] = ["T001_22modules", "T002_135tests", "T003_10domains"]
state["completed_at"] = __import__("datetime").datetime.now().isoformat()
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)
print("FSM: DONE ✅")
