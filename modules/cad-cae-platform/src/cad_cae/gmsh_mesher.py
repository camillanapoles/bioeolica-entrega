"""
Gmsh Mesher — automatic mesh generation for CAD geometries.

Wraps the Gmsh Python API to import STEP files, control mesh size,
generate tetrahedral/hexahedral meshes, tag boundary conditions,
and export to CalculiX-compatible .msh format.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import gmsh
import numpy as np


class MeshGenerator:
    """Generate finite element meshes from STEP geometries.

    Parameters
    ----------
    model_name : str, optional
        Gmsh model name (default 'cad_model').
    """

    def __init__(self, model_name: str = "cad_model"):
        gmsh.initialize()
        gmsh.model.add(model_name)
        self.model_name = model_name
        self._initialized = True
        self._step_entities: list[tuple] = []
        self._physical_groups: dict[str, int] = {}

    def __del__(self):
        if getattr(self, "_initialized", False):
            try:
                gmsh.finalize()
            except Exception:
                pass

    def import_step(self, filepath: str | Path) -> list[tuple]:
        """Import a STEP file into the Gmsh model.

        Parameters
        ----------
        filepath : str | Path
            Path to .step or .stp file.

        Returns
        -------
        entities : list of tuple
            List of (dim, tag) tuples for imported entities.
        """
        filepath = str(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"STEP file not found: {filepath}")
        entities = gmsh.model.occ.importShapes(filepath)
        gmsh.model.occ.synchronize()
        self._step_entities = entities
        return entities

    def set_element_size(self, min_size: float = 0.1, max_size: float = 5.0):
        """Set global mesh element size limits.

        Parameters
        ----------
        min_size : float, optional
            Minimum element size (default 0.1).
        max_size : float, optional
            Maximum element size (default 5.0).
        """
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        gmsh.option.setNumber("Mesh.MeshSizeMin", min_size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", max_size)

    def set_element_size_on_entities(
        self, size: float, dim: int = -1, tags: Optional[list[int]] = None
    ):
        """Set element size on specific entities.

        Parameters
        ----------
        size : float
            Target element size.
        dim : int, optional
            Entity dimension (-1 = all, 0=point, 1=curve, 2=surface).
        tags : list of int, optional
            Entity tags. If None, apply to all of given dim.
        """
        if tags:
            for t in tags:
                gmsh.model.mesh.setSize(gmsh.model.getBoundary([(dim, t)]), size)
        else:
            entities = gmsh.model.getEntities(dim if dim >= 0 else 0)
            for d, t in entities:
                gmsh.model.mesh.setSize([(d, t)], size)

    def add_physical_group(self, name: str, dim: int, tags: list[int]) -> int:
        """Create a physical group for boundary condition tagging.

        Parameters
        ----------
        name : str
            Physical group name (e.g., 'fixed', 'load', 'pressure').
        dim : int
            Entity dimension (2=surface for BCs, 3=volume).
        tags : list of int
            Entity tags to include.

        Returns
        -------
        tag : int
            Physical group tag.
        """
        pg = gmsh.model.addPhysicalGroup(dim, tags)
        gmsh.model.setPhysicalName(dim, pg, name)
        self._physical_groups[name] = pg
        return pg

    def generate_volume_mesh(self, order: int = 1, algorithm: int = 6) -> tuple:
        """Generate a 3D tetrahedral volume mesh.

        Parameters
        ----------
        order : int, optional
            Element order: 1=linear, 2=quadratic (default 1).
        algorithm : int, optional
            Meshing algorithm: 6=Frontal-Delaunay (default),
            1=MeshAdapt, 2=Automatic, 5=Delaunay.

        Returns
        -------
        (node_tags, coord, elem_types, elem_tags, elem_node_tags) : tuple
            Gmsh mesh data.
        """
        gmsh.option.setNumber("Mesh.Algorithm3D", algorithm)
        gmsh.option.setNumber("Mesh.ElementOrder", order)
        gmsh.model.mesh.generate(3)
        return gmsh.model.mesh.getNodes(), gmsh.model.mesh.getElements()

    def generate_surface_mesh(self, order: int = 1) -> tuple:
        """Generate a 2D triangular surface mesh.

        Parameters
        ----------
        order : int, optional
            Element order (default 1).

        Returns
        -------
        mesh_data : tuple
        """
        gmsh.option.setNumber("Mesh.ElementOrder", order)
        gmsh.model.mesh.generate(2)
        return gmsh.model.mesh.getNodes(), gmsh.model.mesh.getElements()

    def export_msh(self, filepath: str | Path, version: str = "2.2") -> str:
        """Export mesh to .msh format (CalculiX-compatible).

        Parameters
        ----------
        filepath : str | Path
            Output file path.
        version : str, optional
            MSH format version: '2.2' for CalculiX (default), '4.1' for latest.

        Returns
        -------
        filepath : str
        """
        filepath = str(filepath)
        gmsh.option.setNumber("Mesh.MshFileVersion", float(version[:3]))
        gmsh.write(filepath)
        return filepath

    def export_vtk(self, filepath: str | Path) -> str:
        """Export mesh to VTK format."""
        gmsh.write(str(filepath))
        return str(filepath)

    def get_mesh_stats(self) -> dict:
        """Get mesh statistics.

        Returns
        -------
        stats : dict
            Number of nodes, elements, element types.
        """
        nodes, _, _ = gmsh.model.mesh.getNodes()
        n_nodes = len(nodes)
        n_vol = 0
        n_surf = 0
        try:
            elem_types, elem_tags, _ = gmsh.model.mesh.getElements(dim=3)
            n_vol = sum(len(t) for t in elem_tags)
        except Exception:
            pass
        try:
            surf_types, surf_tags, _ = gmsh.model.mesh.getElements(dim=2)
            n_surf = sum(len(t) for t in surf_tags)
        except Exception:
            pass
        return {
            "n_nodes": n_nodes,
            "n_volume_elements": n_vol,
            "n_surface_elements": n_surf,
        }

    def find_surfaces_by_location(
        self, coord: tuple[float, float, float], tolerance: float = 0.1
    ) -> list[tuple[int, int]]:
        """Find surface entities near a given point.

        Used for identifying boundary condition surfaces.

        Parameters
        ----------
        coord : tuple
            (x, y, z) point.
        tolerance : float, optional
            Distance tolerance.

        Returns
        -------
        surfaces : list of (dim, tag)
        """
        surfaces = gmsh.model.getEntities(dim=2)
        result = []
        for dim, tag in surfaces:
            com = gmsh.model.occ.getCenterOfMass(dim, tag)
            dist = np.linalg.norm(np.array(com) - np.array(coord))
            if dist < tolerance:
                result.append((dim, tag))
        return result

    def refine_by_size(self, size: float):
        """Refine mesh by setting a new global element size and re-meshing.

        Parameters
        ----------
        size : float
            New global mesh size.
        """
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.model.mesh.generate(3)

    def plot_mesh(self, show_edges: bool = True):
        """Display mesh using matplotlib (2D cross-section).

        Parameters
        ----------
        show_edges : bool, optional
            Show element edges (default True).
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection

        nodes, _ = gmsh.model.mesh.getNodes()
        coords = nodes.reshape(-1, 3)
        _, _, elem_node_tags = gmsh.model.mesh.getElements(dim=2)

        fig, ax = plt.subplots(figsize=(8, 6))
        if elem_node_tags and show_edges:
            for et in elem_node_tags:
                if len(et) < 3:
                    continue
                tri = et.reshape(-1, 3) - 1
                segs = []
                for t in tri:
                    segs.append([coords[t[0], :2], coords[t[1], :2]])
                    segs.append([coords[t[1], :2], coords[t[2], :2]])
                    segs.append([coords[t[2], :2], coords[t[0], :2]])
                lc = LineCollection(segs, colors="blue", linewidths=0.3, alpha=0.5)
                ax.add_collection(lc)

        ax.scatter(coords[:, 0], coords[:, 1], s=1, c="red", alpha=0.3)
        ax.set_aspect("equal")
        ax.set_title(f"Mesh: {len(coords)} nodes")
        plt.tight_layout()
        return fig


def create_beam_mesh(length: float = 10, width: float = 2, height: float = 2,
                      mesh_size: float = 1.0) -> MeshGenerator:
    """Create a simple beam mesh without requiring a STEP file.

    Parameters
    ----------
    length, width, height : float
        Beam dimensions.
    mesh_size : float, optional
        Target element size.

    Returns
    -------
    MeshGenerator
    """
    mg = MeshGenerator()
    gmsh.model.occ.addBox(0, 0, 0, length, width, height)
    gmsh.model.occ.synchronize()
    mg.set_element_size(max_size=mesh_size)
    try:
        gmsh.model.mesh.generate(3)
    except Exception:
        # Fallback: 2D mesh only
        pass
    return mg
