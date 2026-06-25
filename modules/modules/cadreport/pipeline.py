"""
pipeline.py — CLI orchestrator for CAD+REPORT engineering package.

Usage:
    python -m src.cadreport.pipeline --params params.json --output-dir /tmp/package
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from src.cad.parametric import parse_parameters
from src.cad.export import export_step
from src.crslr.engine import render_report
from .metadata import build_crslr_input


class CadReportPipeline:
    """Orchestrator: parameters → CAD (STEP) → CRSLR (report) → package."""

    def __init__(self, params_path: str, output_dir: str,
                 format: str = "markdown", no_mesh: bool = False):
        self.params_path = params_path
        self.output_dir = Path(output_dir)
        self.format = format
        self.no_mesh = no_mesh
        self.model = parse_parameters(params_path)

    def run(self) -> dict[str, Any]:
        """Execute full pipeline. Returns package metadata dict."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate CAD
        step_path = str(self.output_dir / "model.step")
        export_step(self.model, step_path)

        # Step 2: Generate mesh (optional)
        msh_path: str | None = None
        mesh_info: dict | None = None
        if not self.no_mesh:
            from src.cad.mesh import mesh_step
            msh_path = str(self.output_dir / "model.msh")
            mesh_step(step_path, msh_path)
            mesh_info = {"elements": "auto", "mesh_size": 5.0}

        # Step 3: Generate CRSLR report
        crslr_input = build_crslr_input(self.model, step_path, msh_path, mesh_info)
        crslr_json_path = str(self.output_dir / "crslr_input.json")
        with open(crslr_json_path, "w") as f:
            json.dump(crslr_input, f, indent=2)

        report_path = str(self.output_dir / f"report.{'md' if self.format == 'markdown' else 'html'}")
        render_report(crslr_json_path, report_path, fmt=self.format)

        # Step 4: Generate checksums
        checksums: dict[str, str] = {}
        for fpath in self.output_dir.iterdir():
            if fpath.is_file() and not fpath.name.startswith("."):
                checksums[fpath.name] = hashlib.sha256(fpath.read_bytes()).hexdigest()
        (self.output_dir / "checksums.sha256").write_text(
            json.dumps(checksums, indent=2) + "\n"
        )

        # Step 5: Generate metadata JSON
        metadata = {
            "package_id": f"PKG-{self.model.model_id}",
            "model_id": self.model.model_id,
            "generated_at": crslr_input["date"],
            "step_checksum": checksums.get("model.step", ""),
            "mesh_checksum": checksums.get("model.msh", ""),
            "report_path": f"report.{'md' if self.format == 'markdown' else 'html'}",
            "parameters": self.model.to_dict(),
            "dependencies": ["crslr", "cad"],
        }
        (self.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CAD+REPORT Pipeline — generate engineering package."
    )
    parser.add_argument("--params", required=True, help="Parameters JSON path")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--no-mesh", action="store_true", help="Skip Gmsh meshing")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown",
                        help="Report format")
    return parser.parse_args(argv)


def run_pipeline(params_path: str, output_dir: str,
                 format: str = "markdown", no_mesh: bool = False) -> dict[str, Any]:
    """Convenience function: create pipeline and run."""
    p = CadReportPipeline(params_path, output_dir, format=format, no_mesh=no_mesh)
    return p.run()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metadata = run_pipeline(args.params, args.output_dir,
                            format=args.format, no_mesh=args.no_mesh)
    print(f"Package generated: {args.output_dir}")
    print(f"  Model: {metadata['model_id']}")
    print(f"  STEP checksum: {metadata['step_checksum'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
