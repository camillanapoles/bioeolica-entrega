"""
CalculiX Solver — FEM on arbitrary meshes via CalculiX ccx CLI.

Writes CalculiX .inp input files from mesh + material + BC definitions,
runs the ccx solver, and parses .dat / .frd result files.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class FEMSolver:
    """Finite Element solver using CalculiX ccx.

    Parameters
    ----------
    workdir : str, optional
        Working directory for input/output files (default temp dir).
    """

    def __init__(self, workdir: Optional[str] = None):
        self.workdir = workdir or tempfile.mkdtemp(prefix="calculix_")
        self._nodes: list[tuple[int, float, float, float]] = []
        self._elements: list[tuple[int, int, list[int]]] = []
        self._materials: list[str] = []
        self._boundary_conditions: list[str] = []
        self._loads: list[str] = []
        self._steps: list[str] = []
        self._jobname = "calculix_job"

    # ---- Mesh Input ----
    def load_msh(self, msh_path: str) -> None:
        """Load nodes and elements from a .msh file (Gmsh format 2.2).

        Parameters
        ----------
        msh_path : str
            Path to .msh file.
        """
        self._nodes = []
        self._elements = []
        with open(msh_path) as f:
            lines = f.readlines()

        mode = None
        elem_id = 1
        for line in lines:
            line = line.strip()
            if line.startswith("$Nodes"):
                mode = "nodes"
                continue
            if line.startswith("$EndNodes"):
                mode = None
                continue
            if line.startswith("$Elements"):
                mode = "elements"
                continue
            if line.startswith("$EndElements"):
                mode = None
                continue

            if mode == "nodes":
                # Format: node_id x y z
                parts = line.split()
                if len(parts) >= 4 and parts[0].isdigit():
                    nid = int(parts[0])
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    self._nodes.append((nid, x, y, z))

            elif mode == "elements":
                # Gmsh format: id type tag-count tags... node-list
                parts = line.split()
                if len(parts) < 4 or not parts[0].isdigit():
                    continue
                etype = int(parts[1])
                n_tags = int(parts[2])
                node_start = 3 + n_tags
                node_ids = [int(p) for p in parts[node_start:]]
                # Map Gmsh element type to CalculiX type
                c3d_types = {4: 1, 5: 2, 6: 4, 7: 5, 8: 7, 9: 8,
                              10: 9, 11: 10, 12: 11, 15: 20, 16: 21}
                if etype in c3d_types:
                    self._elements.append((elem_id, c3d_types[etype], node_ids))
                    elem_id += 1

    def set_material(self, name: str, E: float, nu: float, rho: float = 0.0):
        """Set isotropic material properties.

        Parameters
        ----------
        name : str
            Material name.
        E : float
            Young's modulus.
        nu : float
            Poisson's ratio.
        rho : float, optional
            Density (for modal/dynamic).
        """
        self._materials = [f"*MATERIAL,NAME={name}",
                           f"*ELASTIC\n{E},{nu}"]
        if rho > 0:
            self._materials.append(f"*DENSITY\n{rho}")
        self._current_material = name

    def add_fixed_support(self, node_set: str | list[int]):
        """Add fixed (encastre) boundary condition.

        Parameters
        ----------
        node_set : str or list of int
            Node set name or list of node IDs.
        """
        if isinstance(node_set, list):
            nodes_str = ",".join(str(n) for n in node_set)
            self._boundary_conditions.append(f"*BOUNDARY\n{nodes_str},1,6,0")
        else:
            self._boundary_conditions.append(f"*BOUNDARY\n{node_set},1,6,0")

    def add_force(self, node_set: str | list[int], fx: float = 0, fy: float = 0, fz: float = 0):
        """Add concentrated force.

        Parameters
        ----------
        node_set : str or list of int
            Node set name or list of node IDs.
        fx, fy, fz : float
            Force components.
        """
        if isinstance(node_set, list):
            nodes_str = ",".join(str(n) for n in node_set)
            self._loads.append(f"*CLOAD\n{nodes_str},1,{fx}\n{nodes_str},2,{fy}\n{nodes_str},3,{fz}")
        else:
            self._loads.append(f"*CLOAD\n{node_set},1,{fx}\n{node_set},2,{fy}\n{node_set},3,{fz}")

    def add_pressure(self, element_set: str, value: float):
        """Add pressure load on element faces.

        Parameters
        ----------
        element_set : str
            Element set name.
        value : float
            Pressure value (positive = compression).
        """
        self._loads.append(f"*DLOAD\n{element_set},P,{value}")

    # ---- Input file generation ----
    def _write_inp(self, filepath: str) -> str:
        """Write the complete .inp input file.

        Parameters
        ----------
        filepath : str
            Output .inp file path.

        Returns
        -------
        filepath : str
        """
        with open(filepath, "w") as f:
            f.write("*HEADING\nPhysics M³ CalculiX Solver\n")

            # Nodes
            f.write("*NODE\n")
            for nid, x, y, z in self._nodes:
                f.write(f"{nid},{x},{y},{z}\n")

            # Elements
            if self._elements:
                f.write("*ELEMENT,TYPE=C3D4\n")
                for eid, etype, nodes in self._elements:
                    if etype == 1:  # C3D4 tetra
                        f.write(f"{eid},{nodes[0]},{nodes[1]},{nodes[2]},{nodes[3]}\n")

            # Node set for all nodes
            if self._nodes:
                f.write("*NSET,NSET=ALL\n")
                f.write(",".join(str(n[0]) for n in self._nodes[:20]))
                if len(self._nodes) > 20:
                    f.write(",\n")
                    for i in range(20, len(self._nodes), 20):
                        chunk = self._nodes[i:i+20]
                        f.write(",".join(str(n[0]) for n in chunk))
                        f.write("\n")

            # Material
            for line in self._materials:
                f.write(line + "\n")

            # Solid section
            if self._elements:
                mat_name = self._current_material if hasattr(self, '_current_material') else 'MATERIAL'
                f.write(f"*SOLID SECTION,ELSET=ALL,MATERIAL={mat_name}\n")

            # Boundary conditions
            for bc in self._boundary_conditions:
                f.write(bc + "\n")

            # Loads
            for load in self._loads:
                f.write(load + "\n")

            # Step
            f.write("*STEP,NAME=STATIC\n*STATIC\n")

            # Output
            f.write("*NODE FILE\nU\n")
            f.write("*EL FILE\nS\nE\n")
            f.write("*END STEP\n")

        return filepath

    # ---- Solve ----
    def solve_static(self, jobname: str = "calculix_job") -> dict:
        """Run a static CalculiX analysis.

        Parameters
        ----------
        jobname : str, optional
            Job name for input/output files.

        Returns
        -------
        results : dict
            Parsed results with keys: 'success', 'message', 'dat_file', 'frd_file'.
        """
        self._jobname = jobname
        inp_path = os.path.join(self.workdir, f"{jobname}.inp")

        self._write_inp(inp_path)

        # Run ccx
        result = subprocess.run(
            ["ccx", jobname],
            cwd=self.workdir,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse output
        success = result.returncode == 0
        dat_path = os.path.join(self.workdir, f"{jobname}.dat")
        frd_path = os.path.join(self.workdir, f"{jobname}.frd")

        return {
            "success": success,
            "message": result.stdout[-500:] if result.stdout else result.stderr[-500:],
            "stdout": result.stdout,
            "stderr": result.stderr,
            "dat_file": dat_path if os.path.exists(dat_path) else None,
            "frd_file": frd_path if os.path.exists(frd_path) else None,
        }

    # ---- Result Parsing ----
    def parse_dat(self, dat_path: str) -> dict:
        """Parse a .dat file for displacement and stress results.

        Parameters
        ----------
        dat_path : str
            Path to .dat file.

        Returns
        -------
        results : dict
            Parsed results: 'max_displacement', 'max_stress_mises', 'displacements', 'stresses'.
        """
        max_disp = 0.0
        max_stress = 0.0
        reading_displacements = False
        reading_stresses = False
        displacements = {}
        stresses = {}

        with open(dat_path) as f:
            for line in f:
                if "displacement" in line.lower() or "node" in line.lower() and "value" in line.lower():
                    reading_displacements = True
                    reading_stresses = False
                if "stress" in line.lower() and "mises" in line.lower():
                    reading_displacements = False
                    reading_stresses = True
                if "-------" in line:
                    continue

                parts = line.split()
                if reading_displacements and len(parts) >= 5:
                    try:
                        nid = int(parts[0])
                        vals = [float(x) for x in parts[1:4]]
                        displacements[nid] = vals
                        max_disp = max(max_disp, max(abs(v) for v in vals))
                    except ValueError:
                        pass

                if reading_stresses and len(parts) >= 6:
                    try:
                        eid = int(parts[0])
                        vm = float(parts[-1])
                        stresses[eid] = vm
                        max_stress = max(max_stress, vm)
                    except ValueError:
                        pass

        return {
            "max_displacement": max_disp,
            "max_stress_mises": max_stress,
            "nodal_displacements": displacements,
            "element_stresses": stresses,
        }

    @property
    def n_nodes(self) -> int:
        return len(self._nodes)

    @property
    def n_elements(self) -> int:
        return len(self._elements)

    def cleanup(self):
        """Remove temporary working directory."""
        import shutil
        if os.path.exists(self.workdir) and "/tmp/" in self.workdir:
            shutil.rmtree(self.workdir)
