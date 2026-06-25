"""
pipeline.py — CLI orchestrator for CAD generation pipeline.

Usage:
    python -m src.cad.pipeline --params params.json --output model.step
    python -m src.cad.pipeline --params params.json --output model.step --mesh
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parametric import ParametricModel, parse_parameters
from .export import export_step


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CAD Pipeline — generate STEP models from engineering parameters."
    )
    parser.add_argument("--params", required=True, help="Path to parameters JSON")
    parser.add_argument("--output", required=True, help="Path to output STEP file")
    parser.add_argument("--mesh", action="store_true", help="Also generate MSH mesh")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    model = parse_parameters(args.params)
    print(f"Generating CAD for: {model.name} ({model.model_id})")

    step_path = export_step(model, args.output)
    print(f"STEP saved: {step_path}")

    if args.mesh:
        from .mesh import mesh_step
        msh_path = args.output.replace(".step", ".msh").replace(".stp", ".msh")
        mesh_step(step_path, msh_path)
        print(f"MSH saved: {msh_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
