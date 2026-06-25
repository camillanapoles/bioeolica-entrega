"""
mesh.py — Gmsh meshing bridge from STEP to MSH.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def mesh_step(step_path: str, msh_path: str, mesh_size: float = 5.0) -> str:
    """
    Generate MSH mesh from STEP file using Gmsh.

    Parameters
    ----------
    step_path : str
        Path to input STEP file.
    msh_path : str
        Path to output MSH file.
    mesh_size : float
        Target mesh element size.

    Returns
    -------
    str
        Path to generated MSH file.
    """
    path = Path(msh_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Generate Gmsh .geo script
    geo_content = f"""
SetFactory("OpenCASCADE");
Merge "{step_path}";
Mesh.CharacteristicLengthMax = {mesh_size};
Mesh.CharacteristicLengthMin = {mesh_size / 5};
Mesh 3;
Save "{path}";
"""
    geo_path = path.with_suffix(".geo")
    geo_path.write_text(geo_content)

    # Run Gmsh
    result = subprocess.run(
        ["gmsh", str(geo_path), "-3", "-o", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Gmsh warning/error: {result.stderr[:200]}", file=sys.stderr)

    return str(path)
