"""
src/cad/assembly.py — Generates 3D CAD models (STEP) from topological data.
"""
from typing import List, Tuple

try:
    import cadquery as cq
    _CADQUERY_AVAILABLE = True
except ImportError:
    _CADQUERY_AVAILABLE = False

class TopologyToCAD:
    """
    Converts a list of 2D normalized solid boxes (x, y, dx, dy) into a 3D STEP file.
    """
    def __init__(self, physical_width_mm: float = 100.0, physical_height_mm: float = 50.0, extrude_depth_mm: float = 10.0):
        if not _CADQUERY_AVAILABLE:
            raise ImportError("CadQuery is not installed. Please install with 'pip install cadquery'.")
        self.width = physical_width_mm
        self.height = physical_height_mm
        self.depth = extrude_depth_mm

    def generate_step(self, solid_boxes: List[Tuple[float, float, float, float]], output_path: str = "topopt_part.step") -> str:
        """
        Extrudes the boxes into a single solid 3D model and saves as STEP.
        """
        # Create a base empty Workplane
        result = cq.Workplane("XY")

        for (x_norm, y_norm, dx_norm, dy_norm) in solid_boxes:
            # Convert normalized coordinates to physical mm
            x_phys = x_norm * self.width
            y_phys = y_norm * self.height
            dx_phys = dx_norm * self.width
            dy_phys = dy_norm * self.height
            
            # Draw rectangle at the correct center point
            center_x = x_phys + (dx_phys / 2.0)
            center_y = y_phys + (dy_phys / 2.0)
            
            box = cq.Workplane("XY").moveTo(center_x, center_y).rect(dx_phys, dy_phys).extrude(self.depth)
            
            # Union the box to the main result
            result = result.union(box)

        # Export to STEP
        cq.exporters.export(result, output_path)
        return output_path
