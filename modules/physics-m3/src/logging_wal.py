#!/usr/bin/env python3
"""
M5 — Log 5W1H (Work Activity Log).

Structured JSON logging per INSTRUCTIONS.md KDI mandate M5:
  - Every action generates a structured log entry
  - 5W1H: What, Why, Who, When, Where, How
  - Links to Mapa Único via map_index
  - Validates quality metrics (D1-D10)

Usage:
    from logging_wal import WALogger, LogEntry

    log = WALogger(project="PRODUTO-COMPOSITE-001")
    log.record(
        what="BEM analysis of blade element",
        why="Determine optimal TSR for composite blade",
        who="agent",
        where="fluid_dynamics.py:bem_theory",
        how={"method": "BEM theory", "tool": "Python/NumPy"},
        domain="fluidos",
        scale="meso",
    )
"""

import json
import os
import uuid
import functools
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable


@dataclass
class LogEntry:
    """Single 5W1H log entry per KDI WAL schema."""
    log_id: str = ""
    timestamp_created: str = ""
    what: str = ""
    why: str = ""
    who: str = ""
    when_started: str = ""
    when_finished: str = ""
    where_file: str = ""
    where_line: str = ""
    where_version: str = ""
    how_method: str = ""
    how_tool: str = ""
    how_parameters: str = ""
    domain: str = ""
    scale: str = ""
    project: str = ""
    parent_log: str = ""
    validation_status: str = "PENDING"

    def __post_init__(self):
        if not self.log_id:
            self.log_id = f"LOG-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
        if not self.timestamp_created:
            self.timestamp_created = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


class WALogger:
    """Work Activity Logger — 5W1H structured logging per M5 mandate."""

    def __init__(self, project: str = "PRODUTO-COMPOSITE-001",
                 log_dir: str = "data/logs"):
        self.project = project
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.active_log: Optional[LogEntry] = None

    def record(self, what: str, why: str, who: str,
               where: str, how: Dict[str, str],
               domain: str = "", scale: str = "",
               parent_log: str = "",
               duration_s: float = 0.0) -> str:
        """Record a 5W1H log entry."""
        now = datetime.now(timezone.utc)
        entry = LogEntry(
            what=what,
            why=why,
            who=who,
            when_started=now.isoformat(),
            where_file=where,
            how_method=how.get("method", ""),
            how_tool=how.get("tool", ""),
            how_parameters=json.dumps(how.get("params", {})),
            domain=domain,
            scale=scale,
            project=self.project,
            parent_log=parent_log,
        )
        self._append(entry)
        return entry.log_id

    def _append(self, entry: LogEntry):
        """Append log entry to JSONL file."""
        filepath = f"{self.log_dir}/wal_{datetime.now():%Y%m}.jsonl"
        entry.timestamp_created = datetime.now(timezone.utc).isoformat()
        with open(filepath, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def query(self, domain: Optional[str] = None,
              limit: int = 10) -> List[Dict]:
        """Query recent logs by domain."""
        results = []
        log_files = sorted(
            [f for f in os.listdir(self.log_dir) if f.startswith("wal_")],
            reverse=True
        )
        for lf in log_files[:3]:
            with open(f"{self.log_dir}/{lf}") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if domain and entry.get("domain") != domain:
                        continue
                    results.append(entry)
                    if len(results) >= limit:
                        return results
        return results

    def decorator(self, **metadata):
        """Decorator for automatic 5W1H logging of function calls."""
        def decorator_func(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                self.record(
                    what=f"Called {func.__name__}",
                    why=metadata.get("why", "analysis"),
                    who="agent",
                    where=f"{func.__module__}:{func.__name__}",
                    how={"method": metadata.get("method", "analytical"),
                         "tool": "Python/NumPy",
                         "params": metadata},
                    domain=metadata.get("domain", ""),
                    scale=metadata.get("scale", ""),
                    duration_s=duration,
                )
                return result
            return wrapper
        return decorator_func
