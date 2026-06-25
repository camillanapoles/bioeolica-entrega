#!/usr/bin/env python3
"""
scripts/audit_deps.py — Audit Python dependencies against actual imports.

Usage:
    python scripts/audit_deps.py --check   # report undeclared and unused deps
    python scripts/audit_deps.py --freeze  # output version-pinned requirements
"""

import argparse
import ast
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Python dependencies against actual imports."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report undeclared and unused dependencies.",
    )
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Output pip-freeze style list from current environment.",
    )
    return parser.parse_args(argv)


STDLIB_MODULES = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections", "copy",
    "csv", "datetime", "decimal", "enum", "functools", "glob", "hashlib",
    "html", "http", "importlib", "inspect", "io", "itertools", "json",
    "logging", "math", "multiprocessing", "operator", "os", "pathlib",
    "pickle", "pdb", "pprint", "queue", "random", "re", "secrets",
    "shutil", "signal", "sqlite3", "statistics", "string", "struct",
    "subprocess", "sys", "tempfile", "textwrap", "threading", "time",
    "traceback", "typing", "unittest", "uuid", "warnings", "weakref",
    "xml", "zipfile",
}

SKIP_DIRS = {"__pycache__", ".venv", "venv", ".git", "node_modules"}


def extract_imports(root: Path) -> dict[str, set[str]]:
    """Scan .py files and return {module_name: {source_files}}."""
    imports: dict[str, set[str]] = defaultdict(set)
    for pyfile in root.rglob("*.py"):
        rel = pyfile.relative_to(root)
        if any(part.startswith(".") or part in SKIP_DIRS for part in rel.parts):
            continue
        if ".venv" in str(rel) or "venv" in str(rel):
            continue
        try:
            tree = ast.parse(pyfile.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in STDLIB_MODULES:
                        imports[top].add(str(rel))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top not in STDLIB_MODULES:
                        imports[top].add(str(rel))
    return imports


def check_deps(imports: dict[str, set[str]]):
    """Check declared deps in pyproject.toml vs actual imports."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("pyproject.toml not found.")
        return

    content = pyproject.read_text()
    # Naive parse: extract [project.dependencies] lines
    declared: set[str] = set()
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[project.dependencies]"):
            in_deps = True
            continue
        if in_deps:
            if stripped.startswith("[") and not stripped.startswith("["):
                break
            if stripped and not stripped.startswith("#"):
                # extract package name before any version spec
                pkg = stripped.lstrip("- ").strip().split("[")[0].split(">")[0].split("<")[0].split("=")[0].split("~")[0].split("!=")[0].strip().strip(",").strip('"').strip("'")
                if pkg and not pkg.startswith("#"):
                    declared.add(pkg.lower())

    actual = set(imports.keys())
    missing = actual - declared
    unused = declared - actual

    print("=== Dependency Audit ===")
    print(f"Declared deps: {len(declared)}")
    print(f"Actual imports: {len(actual)}")
    if missing:
        print(f"\nMissing from pyproject.toml ({len(missing)}):")
        for m in sorted(missing):
            files = ", ".join(sorted(imports[m]))
            print(f"  {m} ← {files}")
    if unused:
        print(f"\nDeclared but not imported ({len(unused)}):")
        for u in sorted(unused):
            print(f"  {u}")


def freeze_deps():
    """Output pip freeze."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True, text=True, check=False,
    )
    print(result.stdout)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.freeze:
        freeze_deps()
        return 0
    root = Path(".").resolve()
    imports = extract_imports(root)
    if args.check:
        check_deps(imports)
    else:
        print(f"Scanned {len(imports)} unique external modules:")
        for mod, files in sorted(imports.items()):
            print(f"  {mod} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
