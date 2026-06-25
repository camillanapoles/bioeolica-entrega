#!/usr/bin/env python3
"""
Generate a GitNexus-style analysis report.
Fallback when `gitnexus` CLI is not available.
"""

import subprocess
import sys
from pathlib import Path

REPORT_PATH = Path("gitnexus_report.txt")

def run_cmd(cmd: list[str], capture: bool = True) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout + result.stderr
    except FileNotFoundError:
        return f"Command not found: {cmd[0]}"

def generate():
    lines = []
    lines.append("# GitNexus Analysis Report — Bioeólica Dev (Simulated)")
    lines.append(f"# Generated: {__import__('datetime').datetime.now().isoformat()}")
    lines.append("")

    # Get git log
    git_log = run_cmd(["git", "log", "--oneline", "--decorate", "--graph", "--all"])
    lines.append("## Git Log")
    lines.append("```")
    lines.append(git_log)
    lines.append("```")
    lines.append("")

    # Get directory tree
    tree = run_cmd(["tree", "-L", "3", "--dirsfirst"])
    lines.append("## Project Tree")
    lines.append("```")
    lines.append(tree)
    lines.append("```")
    lines.append("")

    # Provide analysis placeholders
    lines.append("## Dependency Analysis")
    lines.append("(Manual analysis of source code required; see module comments.)")
    lines.append("")

    # Write report
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    generate()
