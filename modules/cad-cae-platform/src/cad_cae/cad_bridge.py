"""CadQuery Bridge — parametric 3D modeling for engineering design.

Uses CadQuery (OpenCASCADE) for parametric solid modeling, STEP/STL export,
and integration with the Physics M³ analysis pipeline.
"""

from __future__ import annotations

from typing import Optional
import numpy as np

try:
    import cadquery as cq
    _CADQUERY_AVAILABLE = True
except ImportError:
    _CADQUERY_AVAILABLE = False
    cq = None  # type: ignore[assignment]


class CadModel:
    """Parametric 3D solid model built from CadQuery operations.

    Parameters
    ----------
    workplane : str, optional
        Initial workplane ('XY', 'YZ', 'XZ'). Default 'XY'.
    origin : tuple, optional
        Workplane origin offset (x, y, z). Default (0, 0, 0).
    """

    def __init__(self, workplane: str = "XY", origin: tuple = (0, 0, 0)):
        if not _CADQUERY_AVAILABLE:
            raise RuntimeError("CadQuery is required for 3D modeling. Install with: pip install cadquery")
        self.wp = cq.Workplane(workplane).workplane(offset=origin[2])
        if origin[:2] != (0, 0):
            self.wp = self.wp.center(origin[0], origin[1])
        self._compound: Optional[cq.Workplane] = None

    # --- Primitives ---

    def box(self, length: float, width: float, height: float, centered: bool = True) -> "CadModel":
        """Add a rectangular box.

        Parameters
        ----------
        length : float
            Size in X direction.
        width : float
            Size in Y direction.
        height : float
            Size in Z direction.
        centered : bool, optional
            Center the box on origin (default True).

        Returns
        -------
        CadModel
            Self for chaining.
        """
        self._compound = self.wp.box(length, width, height, centered=centered)
        return self

    def cylinder(self, radius: float, height: float, centered: bool = True) -> "CadModel":
        """Add a cylinder."""
        self._compound = self.wp.cylinder(height, radius, centered=centered)
        return self

    def sphere(self, radius: float) -> "CadModel":
        """Add a sphere."""
        self._compound = self.wp.sphere(radius)
        return self

    # --- 2D Sketches → 3D ---

    def extrude(self, points: list[tuple], height: float, closed: bool = True) -> "CadModel":
        """Create a polygon sketch and extrude it.

        Parameters
        ----------
        points : list of tuple
            2D polygon vertices as (x, y) pairs.
        height : float
            Extrusion distance (positive = up, negative = down).
        closed : bool, optional
            Close the polygon (default True).

        Returns
        -------
        CadModel
        """
        wp = self.wp
        for i, (x, y) in enumerate(points):
            if i == 0:
                wp = wp.moveTo(x, y)
            else:
                wp = wp.lineTo(x, y)
        if closed:
            wp = wp.close()
        self._compound = wp.extrude(height)
        return self

    def revolve(self, points: list[tuple], angle_deg: float = 360) -> "CadModel":
        """Create a profile and revolve it 360° around the Z axis.

        Parameters
        ----------
        points : list of tuple
            2D profile vertices as (x, y) pairs — profile should be in XZ plane.
        angle_deg : float, optional
            Revolution angle (default 360).

        Returns
        -------
        CadModel
        """
        wp = self.wp
        for i, (x, y) in enumerate(points):
            if i == 0:
                wp = wp.moveTo(x, y)
            else:
                wp = wp.lineTo(x, y)
        wp = wp.close()
        self._compound = wp.revolve(angle_deg, (0, 0, 0), (0, 0, 1))
        return self

    # --- Boolean Operations ---

    def union(self, other: "CadModel") -> "CadModel":
        """Boolean union with another model."""
        self._compound = self._compound.union(other._compound)
        return self

    def cut(self, other: "CadModel") -> "CadModel":
        """Boolean subtraction (cut other from self)."""
        self._compound = self._compound.cut(other._compound)
        return self

    def intersect(self, other: "CadModel") -> "CadModel":
        """Boolean intersection."""
        self._compound = self._compound.intersect(other._compound)
        return self

    # --- Edge Treatments ---

    def fillet(self, radius: float, edges: Optional[list] = None) -> "CadModel":
        """Apply fillet to edges.

        Parameters
        ----------
        radius : float
            Fillet radius.
        edges : list, optional
            Edges to fillet. If None, fillet all edges.

        Returns
        -------
        CadModel
        """
        obj = self._compound.val()
        if edges is None:
            edge_list = obj.Edges
        else:
            edge_list = edges
        self._compound = self._compound.edges(tag=id(edge_list)).fillet(radius)
        return self

    def chamfer(self, distance: float, edges: Optional[list] = None) -> "CadModel":
        """Apply chamfer to edges."""
        self._compound = self._compound.edges().chamfer(distance)
        return self

    # --- Export ---

    def export_step(self, filepath: str) -> str:
        """Export model to STEP format.

        Parameters
        ----------
        filepath : str
            Output file path (.step or .stp extension).

        Returns
        -------
        filepath : str
        """
        if self._compound is None:
            raise RuntimeError("No geometry to export. Build a model first.")
        cq.exporters.export(self._compound, filepath, exportType="STEP")
        return filepath

    def export_stl(self, filepath: str, tolerance: float = 0.1, angular_tolerance: float = 0.1) -> str:
        """Export model to STL format for meshing/3D printing.

        Parameters
        ----------
        filepath : str
            Output file path (.stl extension).
        tolerance : float, optional
            Linear deflection tolerance (default 0.1).
        angular_tolerance : float, optional
            Angular deflection tolerance (default 0.1).

        Returns
        -------
        filepath : str
        """
        if self._compound is None:
            raise RuntimeError("No geometry to export.")
        cq.exporters.export(self._compound, filepath,
                           exportType="STL", tolerance=tolerance,
                           angularTolerance=angular_tolerance)
        return filepath

    # --- Properties ---

    @property
    def volume(self) -> float:
        """Model volume in mm³."""
        if self._compound is None:
            return 0.0
        return self._compound.val().Volume()

    @property
    def mass(self) -> float:
        """Model mass in kg (assumes density=1 g/cm³)."""
        return self.volume * 1e-6  # mm³ → cm³ → g → kg at 1 g/cm³

    def bounding_box(self) -> dict:
        """Bounding box dimensions.

        Returns
        -------
        dict : {'x': float, 'y': float, 'z': float, 'xmin': float, ...}
        """
        if self._compound is None:
            return {"x": 0, "y": 0, "z": 0}
        bb = self._compound.val().BoundingBox()
        return {
            "xmin": bb.xmin, "ymin": bb.ymin, "zmin": bb.zmin,
            "xmax": bb.xmax, "ymax": bb.ymax, "zmax": bb.zmax,
            "x": bb.xmax - bb.xmin, "y": bb.ymax - bb.ymin, "z": bb.zmax - bb.zmin,
        }


# --- Pre-built engineering geometries ---

def cantilever_beam(length: float = 100, width: float = 10, height: float = 5) -> CadModel:
    """Create a cantilever beam for FEM validation."""
    return CadModel().box(length, width, height)

def l_bracket(base: float = 50, height: float = 50, thickness: float = 5, fillet_r: float = 5) -> CadModel:
    """Create an L-bracket."""
    m = CadModel()
    m.box(base, thickness, height)  # vertical leg
    m.box(thickness, thickness, height)  # joining
    vert = CadModel().box(thickness, base, thickness)  # horizontal leg
    m.union(vert)
    return m

def plate_with_hole(width: float = 100, height: float = 50, thickness: float = 5,
                     hole_diameter: float = 10) -> CadModel:
    """Create a plate with a central hole (Kirsch benchmark)."""
    m = CadModel().box(width, height, thickness)
    hole = CadModel().cylinder(radius=hole_diameter/2, height=thickness*2)
    m.cut(hole)
    return m

def pressure_vessel(length: float = 200, radius: float = 50, wall_thickness: float = 5) -> CadModel:
    """Create a cylindrical pressure vessel with hemispherical ends."""
    body = CadModel().cylinder(radius=radius, height=length)
    # Remove interior
    interior = CadModel().cylinder(radius=radius - wall_thickness, height=length)
    body.cut(interior)
    return body
