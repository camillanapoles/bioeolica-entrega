#!/usr/bin/env python3
"""
CAD & Visualization Module — 3D Geometry, FEM Mesh, Stress Visualization, M3 Layers.

Critical module providing 3D visualization of:
  - 3D Heat maps on FEM mesh surfaces showing stress distribution
  - M3 layers visualization (Macro/Meso/Micro stacked 3D plots)
  - FEM mesh overlay with color-mapped nodal results
  - Boundary layer visualization (gradient from surface to free stream)
  - Database integration via MapaUnico (M4) and WALogger (M5)

Dependencies: numpy, matplotlib, mpl_toolkits.mplot3d only (no external deps).

Usage:
    from cad_visualization import (
        BladeGeometry, StressField, FailureEnvelope, LaminateView,
        WindRose, HeatMap3D, M3Visualizer, BoundaryLayerView,
        stress_color_map, beam_stress_diagram, geometry_to_stl,
        AirfoilCoordinates
    )
"""

import numpy as np
import os
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Callable, Any

# Conditional matplotlib imports — support headless mode
import matplotlib
matplotlib.use('Agg')  # Default headless; interactive set by caller
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — activates 3D projection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

PLOTS_DIR = "data/plots"
DEFAULT_COLORMAP = "jet"
STRESS_COLORMAP = "RdYlGn_r"  # red=critical, green=safe


def _ensure_plots_dir() -> str:
    """Create plots directory if it does not exist."""
    os.makedirs(PLOTS_DIR, exist_ok=True)
    return PLOTS_DIR


def _plot_filename(plot_type: str) -> str:
    """Generate auto-named plot filename: data/plots/{type}_{timestamp}.png."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:22]
    fname = f"{plot_type}_{ts}.png"
    return os.path.join(PLOTS_DIR, fname)


def _maybe_register(mapa, entry_id: str, domain: str, name: str,
                    data: dict, tags: Optional[List[str]] = None,
                    source: str = "") -> Optional[str]:
    """Register plot metadata in MapaUnico if mapa is provided."""
    if mapa is not None:
        return mapa.register(
            domain=domain,
            name=name,
            data=data,
            data_type="plot",
            source=source,
            tags=tags or [],
            parent_id=entry_id,
        )
    return None


def _maybe_log(log, what: str, why: str, where: str,
               how: dict, domain: str = "", scale: str = "",
               parent_log: str = "", **kw) -> Optional[str]:
    """Log action in WALogger if log is provided."""
    if log is not None:
        return log.record(
            what=what, why=why, who="cad_visualization",
            where=where, how=how,
            domain=domain, scale=scale,
            parent_log=parent_log,
            **kw,
        )
    return None


def _set_interactive(interactive: bool = False):
    """Switch between headless (Agg) and interactive (QtAgg/TkAgg) backends."""
    if interactive:
        try:
            import matplotlib.pyplot as _plt
            _plt.switch_backend('TkAgg')
        except Exception:
            pass  # fallback to Agg if interactive backend unavailable


# ═══════════════════════════════════════════════════════════════
#  GEOMETRY PRIMITIVES
# ═══════════════════════════════════════════════════════════════

@dataclass
class AirfoilCoordinates:
    """Generate NACA-style airfoil coordinates."""
    name: str = "NACA0012"
    chord_m: float = 0.3
    n_points: int = 100

    def _naca_thickness(self, x: np.ndarray) -> np.ndarray:
        """NACA 4-digit thickness distribution."""
        t = float(self.name[-2:]) / 100
        return 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x -
                        0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)

    def coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (x, y) coordinates of airfoil."""
        beta = np.linspace(0, np.pi, self.n_points // 2)
        x_u = 0.5 * (1 - np.cos(beta))
        y_t = self._naca_thickness(x_u)
        x = np.concatenate([x_u[::-1], x_u]) * self.chord_m
        y = np.concatenate([y_t[::-1], -y_t]) * self.chord_m
        return x, y


@dataclass
class BladeGeometry:
    """Simplified wind turbine blade geometry for visualization."""
    length_m: float = 1.5
    root_chord_m: float = 0.3
    tip_chord_m: float = 0.1
    root_thickness_pct: float = 0.20
    twist_deg: float = 10.0
    airfoil_name: str = "NACA4412"
    n_sections: int = 10

    def section_chord(self, r: float) -> float:
        """Chord at radial position r."""
        r_norm = r / self.length_m
        return self.root_chord_m - (self.root_chord_m - self.tip_chord_m) * r_norm

    def section_twist(self, r: float) -> float:
        """Twist angle at radial position r."""
        r_norm = r / self.length_m
        return self.twist_deg * (1 - r_norm)

    def section_thickness(self, r: float) -> float:
        """Thickness at radial position r."""
        r_norm = r / self.length_m
        return self.root_thickness_pct * (1 - 0.5 * r_norm)

    def blade_sections(self) -> List[Dict]:
        """Generate blade cross-sections for 3D visualization."""
        sections = []
        for i in range(self.n_sections):
            r = i * self.length_m / (self.n_sections - 1)
            c = self.section_chord(r)
            sections.append({
                "r_m": round(r, 3),
                "chord_m": round(c, 3),
                "twist_deg": round(self.section_twist(r), 1),
                "thickness_pct": round(self.section_thickness(r), 3),
            })
        return sections

    def surface_points(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate blade surface point cloud for 3D plotting."""
        af = AirfoilCoordinates(self.airfoil_name, chord_m=1.0)
        x_af, y_af = af.coordinates()

        X, Y, Z = [], [], []
        for i in range(self.n_sections):
            r = i * self.length_m / (self.n_sections - 1)
            c = self.section_chord(r)
            twist = np.radians(self.section_twist(r))
            thick = self.section_thickness(r)

            x_sec = x_af * c
            y_sec = y_af * c * thick * 5
            # Apply twist
            x_r = x_sec * np.cos(twist) - y_sec * np.sin(twist)
            y_r = x_sec * np.sin(twist) + y_sec * np.cos(twist)

            X.extend(x_r)
            Y.extend(y_r + r)
            Z.extend([r] * len(x_r))

        return np.array(X), np.array(Y), np.array(Z)

    def plot_heatmap_overlay(self, nodal_stress: Optional[np.ndarray] = None,
                             title: str = "Blade Stress Distribution",
                             save: bool = True,
                             interactive: bool = False,
                             mapa: Optional[Any] = None,
                             log: Optional[Any] = None,
                             entry_id: Optional[str] = None) -> str:
        """Plot 3D blade surface with heat-map colored stress overlay.

        Parameters
        ----------
        nodal_stress : array, optional
            Stress values per surface point. If None, generates synthetic data.
        title : str
            Plot title.
        save : bool
            Save plot to PNG.
        interactive : bool
            Show interactive plot window.
        mapa : MapaUnico, optional
            Register plot data in Mapa Unico.
        log : WALogger, optional
            Log rendering action.
        entry_id : str, optional
            Parent entry ID for mapa/log linking.

        Returns
        -------
        str
            Path to saved PNG, or empty string if not saved.
        """
        _set_interactive(interactive)
        X, Y, Z = self.surface_points()

        if nodal_stress is None:
            r_vals = np.array([p[2] for p in zip(X, Y, Z)])
            nodal_stress = 100 * (1 - np.abs(r_vals - r_vals.mean()) / r_vals.max())
            nodal_stress += 20 * np.random.randn(len(nodal_stress))
            nodal_stress = np.clip(nodal_stress, 0, 100)

        fig = plt.figure(figsize=(12, 7))
        ax = fig.add_subplot(111, projection='3d')

        norm = Normalize(vmin=nodal_stress.min(), vmax=nodal_stress.max())
        colors = plt.get_cmap(STRESS_COLORMAP)(norm(nodal_stress))

        scatter = ax.scatter(X, Y, Z, c=nodal_stress, cmap=STRESS_COLORMAP,
                             s=15, alpha=0.8)

        cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.1)
        cbar.set_label("Stress (MPa)", fontsize=11)

        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.view_init(elev=25, azim=-60)

        result = ""
        if save:
            result = _plot_filename("blade_heatmap")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "mecanica", f"blade_heatmap_{title[:20]}",
                            {"file": result, "n_points": len(X),
                             "stress_range": [float(nodal_stress.min()),
                                              float(nodal_stress.max())]},
                            tags=["heatmap", "blade", "stress"],
                            source="cad_visualization.BladeGeometry.plot_heatmap_overlay")
            _maybe_log(log, "Rendered blade 3D heatmap overlay",
                       "Visualize stress distribution on blade surface",
                       "cad_visualization.py:BladeGeometry.plot_heatmap_overlay",
                       {"method": "3D scatter heatmap", "tool": "matplotlib"},
                       domain="mecanica", scale="macro",
                       parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  STRESS VISUALIZATION
# ═══════════════════════════════════════════════════════════════

def stress_color_map(stress_MPa: float, yield_MPa: float) -> str:
    """Traffic-light color for stress level."""
    ratio = abs(stress_MPa) / yield_MPa
    if ratio < 0.3:
        return "green"
    elif ratio < 0.6:
        return "yellow"
    elif ratio < 0.9:
        return "orange"
    else:
        return "red"


def beam_stress_diagram(L_m: float, forces_N: List[float],
                        positions: List[float]) -> Dict:
    """Generate shear and moment diagram data points."""
    x = np.linspace(0, L_m, 100)
    V = np.zeros_like(x)
    M = np.zeros_like(x)
    for f, pos in zip(forces_N, positions):
        idx = np.searchsorted(x, pos)
        V[idx:] += f
        M[idx:] += f * (x[idx:] - pos)
    return {
        "x_m": x.tolist(),
        "shear_N": V.tolist(),
        "moment_Nm": M.tolist(),
    }


class StressField:
    """3D stress heat map on arbitrary mesh data.

    Renders a 3D scatter/trisurf plot where each point/node is colored
    by its stress value (red=critical, green=safe).
    """

    def __init__(self, nodes: np.ndarray, stress_values: np.ndarray,
                 elements: Optional[np.ndarray] = None):
        """Initialize with nodal coordinates and stress values.

        Parameters
        ----------
        nodes : (N, 3) array
            Node coordinates (x, y, z).
        stress_values : (N,) array
            Stress value per node (e.g., von Mises).
        elements : (M, 3|4) array, optional
            Element connectivity for triangle/tetra mesh overlay.
        """
        self.nodes = np.asarray(nodes)
        self.stress = np.asarray(stress_values)
        self.elements = np.asarray(elements) if elements is not None else None

        if self.nodes.ndim != 2 or self.nodes.shape[1] != 3:
            raise ValueError(f"nodes must be (N,3), got {self.nodes.shape}")
        if self.stress.ndim != 1 or len(self.stress) != len(self.nodes):
            raise ValueError(
                f"stress must be 1-D with length N={len(self.nodes)}, "
                f"got shape {self.stress.shape}"
            )

    def plot(self, title: str = "3D Stress Field",
             colormap: str = STRESS_COLORMAP,
             show_mesh: bool = True,
             opacity: float = 0.85,
             save: bool = True,
             interactive: bool = False,
             mapa: Optional[Any] = None,
             log: Optional[Any] = None,
             entry_id: Optional[str] = None) -> str:
        """Render the 3D stress heat map.

        Parameters
        ----------
        title : str
            Plot title.
        colormap : str
            Matplotlib colormap name.
        show_mesh : bool
            Draw element edges if connectivity available.
        opacity : float
            Face alpha for mesh surfaces.
        save, interactive, mapa, log, entry_id : see plot_heatmap_overlay.

        Returns
        -------
        str
            Path to saved PNG.
        """
        _set_interactive(interactive)
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')

        norm = Normalize(vmin=self.stress.min(), vmax=self.stress.max())
        cmap_obj = plt.get_cmap(colormap)

        # Draw mesh faces if connectivity available
        if self.elements is not None and show_mesh:
            polygons = []
            for elem in self.elements:
                verts = self.nodes[elem]
                polygons.append(verts)

            # Color each face by average nodal stress
            face_colors = []
            for elem in self.elements:
                avg_s = self.stress[elem].mean()
                face_colors.append(cmap_obj(norm(avg_s)))

            mesh = Poly3DCollection(polygons, alpha=opacity,
                                    facecolors=face_colors,
                                    edgecolors='k', linewidths=0.3)
            ax.add_collection3d(mesh)

        # Scatter overlay on nodes
        scatter = ax.scatter(self.nodes[:, 0], self.nodes[:, 1], self.nodes[:, 2],
                             c=self.stress, cmap=colormap, s=20,
                             alpha=0.6, norm=norm)

        cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.1)
        cbar.set_label("von Mises Stress (MPa)", fontsize=11)

        # Set limits
        margin = 0.05
        for i, lbl in enumerate(['X', 'Y', 'Z']):
            lo, hi = self.nodes[:, i].min(), self.nodes[:, i].max()
            rng = hi - lo if hi > lo else 1.0
            getattr(ax, f'set_{lbl.lower()}lim')(lo - margin * rng, hi + margin * rng)

        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.view_init(elev=30, azim=-45)

        result = ""
        if save:
            result = _plot_filename("stress_field_3d")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "mecanica",
                            f"stress_field_{title[:20]}",
                            {"file": result, "n_nodes": len(self.nodes),
                             "n_elements": len(self.elements) if self.elements is not None else 0,
                             "stress_range": [float(self.stress.min()),
                                              float(self.stress.max())]},
                            tags=["stress", "fem", "3d"],
                            source="cad_visualization.StressField.plot")
            _maybe_log(log, "Rendered 3D stress field heat map",
                       "Visualize FEM stress distribution on mesh",
                       "cad_visualization.py:StressField.plot",
                       {"method": "3D Poly3DCollection + scatter heatmap",
                        "tool": "matplotlib",
                        "params": {"colormap": colormap, "show_mesh": show_mesh}},
                       domain="mecanica", scale="micro",
                       parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  HEAT MAP 3D — Generic 3D heat map on point cloud / mesh
# ═══════════════════════════════════════════════════════════════

class HeatMap3D:
    """Generic 3D heat map on point cloud or structured mesh.

    Renders scalar field values on 3D coordinates using color mapping.
    Supports both scatter (point cloud) and surface (structured grid) modes.
    """

    def __init__(self, x: np.ndarray, y: np.ndarray, z: np.ndarray,
                 values: np.ndarray,
                 x_label: str = "X", y_label: str = "Y", z_label: str = "Z",
                 value_label: str = "Value"):
        """Initialize with 3D coordinates and scalar values.

        Parameters
        ----------
        x, y, z : 1-D arrays
            Coordinate arrays (same length for scatter, or 2-D for structured surface).
        values : 1-D array
            Scalar field values matching coordinates.
        """
        self.x = np.asarray(x)
        self.y = np.asarray(y)
        self.z = np.asarray(z)
        self.values = np.asarray(values)
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label
        self.value_label = value_label

        is_2d = self.x.ndim == 2
        flat_len = self.x.size
        if is_2d:
            self._mode = "structured"
        else:
            self._mode = "scatter"

        if self.values.shape != self.x.shape:
            self.values = np.asarray(values).ravel().reshape(self.x.shape)

    def plot_scatter(self, title: str = "3D Heat Map (Scatter)",
                     colormap: str = DEFAULT_COLORMAP,
                     point_size: int = 30,
                     save: bool = True, interactive: bool = False,
                     mapa: Optional[Any] = None,
                     log: Optional[Any] = None,
                     entry_id: Optional[str] = None) -> str:
        """Render as 3D scatter plot colored by value."""
        _set_interactive(interactive)
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        xf = self.x.ravel() if self.x.ndim == 2 else self.x
        yf = self.y.ravel() if self.y.ndim == 2 else self.y
        zf = self.z.ravel() if self.z.ndim == 2 else self.z
        vf = self.values.ravel()

        sc = ax.scatter(xf, yf, zf, c=vf, cmap=colormap, s=point_size, alpha=0.8)

        cbar = fig.colorbar(sc, ax=ax, shrink=0.6)
        cbar.set_label(self.value_label, fontsize=11)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_zlabel(self.z_label)
        ax.set_title(title, fontsize=13, fontweight='bold')

        result = ""
        if save:
            result = _plot_filename("heatmap3d_scatter")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "geral",
                            f"heatmap3d_scatter_{title[:20]}",
                            {"file": result, "n_points": len(xf),
                             "value_range": [float(vf.min()), float(vf.max())]},
                            tags=["heatmap", "3d", "scatter"],
                            source="cad_visualization.HeatMap3D.plot_scatter")
            _maybe_log(log, "Rendered 3D scatter heat map",
                       "Visualize scalar field on point cloud",
                       "cad_visualization.py:HeatMap3D.plot_scatter",
                       {"method": "3D scatter colormap", "tool": "matplotlib"},
                       domain="geral", parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)
        return result

    def plot_surface(self, title: str = "3D Heat Map (Surface)",
                     colormap: str = DEFAULT_COLORMAP,
                     rstride: int = 1, cstride: int = 1,
                     save: bool = True, interactive: bool = False,
                     mapa: Optional[Any] = None,
                     log: Optional[Any] = None,
                     entry_id: Optional[str] = None) -> str:
        """Render as 3D surface plot colored by value (structured grid only)."""
        _set_interactive(interactive)
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        if self._mode != "structured":
            # Fallback: triangulate scatter
            return self.plot_scatter(title=title, colormap=colormap,
                                     save=save, interactive=interactive,
                                     mapa=mapa, log=log, entry_id=entry_id)

        surf = ax.plot_surface(self.x, self.y, self.z,
                               facecolors=plt.get_cmap(colormap)(
                                   Normalize()(self.values)),
                               rstride=rstride, cstride=cstride,
                               alpha=0.9, antialiased=True)

        mappable = cm.ScalarMappable(Normalize(self.values.min(),
                                                self.values.max()),
                                     cmap=colormap)
        mappable.set_array(self.values)
        cbar = fig.colorbar(mappable, ax=ax, shrink=0.6)
        cbar.set_label(self.value_label, fontsize=11)

        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_zlabel(self.z_label)
        ax.set_title(title, fontsize=13, fontweight='bold')

        result = ""
        if save:
            result = _plot_filename("heatmap3d_surface")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "geral",
                            f"heatmap3d_surface_{title[:20]}",
                            {"file": result,
                             "grid_shape": list(self.x.shape),
                             "value_range": [float(self.values.min()),
                                             float(self.values.max())]},
                            tags=["heatmap", "3d", "surface"],
                            source="cad_visualization.HeatMap3D.plot_surface")
            _maybe_log(log, "Rendered 3D surface heat map",
                       "Visualize scalar field on structured grid",
                       "cad_visualization.py:HeatMap3D.plot_surface",
                       {"method": "3D plot_surface colormap", "tool": "matplotlib"},
                       domain="geral", parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)
        return result

    def plot(self, title: str = "3D Heat Map",
             mode: str = "auto", **kwargs) -> str:
        """Auto-select scatter or surface based on data dimensionality."""
        if mode == "scatter" or (mode == "auto" and self._mode == "scatter"):
            return self.plot_scatter(title=title, **kwargs)
        return self.plot_surface(title=title, **kwargs)


# ═══════════════════════════════════════════════════════════════
#  M3 VISUALIZER — 3-panel 3D plot for Macro/Meso/Micro
# ═══════════════════════════════════════════════════════════════

class M3Visualizer:
    """Three-panel 3D visualization of Macro/Meso/Micro scales.

    Panel 1 (Macro): Environment box — bounding box with external conditions.
    Panel 2 (Meso): Interface layers — shell/surface between domains.
    Panel 3 (Micro): Fiber/matrix distribution — detailed internal structure.
    """

    def __init__(self, macro_data: Optional[Dict] = None,
                 meso_data: Optional[Dict] = None,
                 micro_data: Optional[Dict] = None):
        """Initialize with optional data for each scale.

        Parameters
        ----------
        macro_data : dict
            'bounds': [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
            'title': str
            'load_arrows': list of {'origin': [x,y,z], 'direction': [dx,dy,dz], 'magnitude': float}
        meso_data : dict
            'layers': list of {'z_level': float, 'thickness': float, 'name': str, 'color': str}
            'title': str
        micro_data : dict
            'fibers': (N,3) array of fiber endpoints or positions
            'matrix_points': (M,3) array of matrix fill points
            'title': str
        """
        self.macro_data = macro_data or self._default_macro()
        self.meso_data = meso_data or self._default_meso()
        self.micro_data = micro_data or self._default_micro()

    @staticmethod
    def _default_macro() -> Dict:
        return {
            "title": "Macro: Environment & External Loads",
            "bounds": [[-2, 2], [-2, 2], [-2, 2]],
            "load_arrows": [
                {"origin": [0, 0, 2], "direction": [0, 0, -1],
                 "magnitude": 1.0, "label": "Wind Load"},
            ],
        }

    @staticmethod
    def _default_meso() -> Dict:
        return {
            "title": "Meso: Interface Layers",
            "layers": [
                {"z_level": -0.8, "thickness": 0.3, "name": "Gel Coat",
                 "color": "#4A90D9"},
                {"z_level": -0.3, "thickness": 0.6, "name": "Composite Laminate",
                 "color": "#50C878"},
                {"z_level": 0.5, "thickness": 0.3, "name": "Core Material",
                 "color": "#D4A017"},
                {"z_level": 1.0, "thickness": 0.2, "name": "Inner Liner",
                 "color": "#8B4513"},
            ],
        }

    @staticmethod
    def _default_micro() -> Dict:
        np.random.seed(42)
        n_fibers = 60
        fibers = np.random.rand(n_fibers, 3) * 2 - 1
        n_matrix = 200
        matrix = np.random.randn(n_matrix, 3) * 0.5
        return {
            "title": "Micro: Fiber/Matrix Distribution",
            "fibers": fibers,
            "matrix_points": matrix,
        }

    def _plot_macro(self, ax) -> None:
        """Render macro scale: environment bounding box + load arrows."""
        bounds = self.macro_data.get("bounds", [[-2, 2], [-2, 2], [-2, 2]])
        xl, yl, zl = bounds

        # Draw bounding box
        corners = np.array([
            [xl[0], yl[0], zl[0]], [xl[1], yl[0], zl[0]],
            [xl[1], yl[1], zl[0]], [xl[0], yl[1], zl[0]],
            [xl[0], yl[0], zl[1]], [xl[1], yl[0], zl[1]],
            [xl[1], yl[1], zl[1]], [xl[0], yl[1], zl[1]],
        ])
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7],
        ]
        for i, j in edges:
            ax.plot3D(*zip(corners[i], corners[j]), 'b-', alpha=0.4, linewidth=0.8)

        # Semi-transparent faces
        faces = [
            [corners[0], corners[1], corners[5], corners[4]],
            [corners[2], corners[3], corners[7], corners[6]],
            [corners[0], corners[3], corners[7], corners[4]],
            [corners[1], corners[2], corners[6], corners[5]],
            [corners[0], corners[1], corners[2], corners[3]],
            [corners[4], corners[5], corners[6], corners[7]],
        ]
        for face_verts in faces:
            poly = Poly3DCollection([face_verts], alpha=0.05, facecolor='cyan',
                                    edgecolor='none')
            ax.add_collection3d(poly)

        # Load arrows
        for arrow in self.macro_data.get("load_arrows", []):
            o = arrow["origin"]
            d = arrow["direction"]
            mag = arrow.get("magnitude", 1.0)
            lbl = arrow.get("label", "")
            scale = max(xl[1] - xl[0], yl[1] - yl[0], zl[1] - zl[0]) * 0.15
            ax.quiver(o[0], o[1], o[2],
                      d[0] * mag, d[1] * mag, d[2] * mag,
                      color='red', alpha=0.8, arrow_length_ratio=0.2,
                      length=scale)
            if lbl:
                ax.text(o[0], o[1], o[2] + 0.2, lbl, fontsize=9, color='red')

        ax.set_xlim(xl)
        ax.set_ylim(yl)
        ax.set_zlim(zl)
        ax.set_title(self.macro_data.get("title", "Macro"), fontsize=12,
                     fontweight='bold', pad=10)

    def _plot_meso(self, ax) -> None:
        """Render meso scale: stacked interface layers."""
        layers = self.meso_data.get("layers", [])
        bounds = [-1.2, 1.2]

        for layer in layers:
            z_center = layer["z_level"]
            half_t = layer["thickness"] / 2
            z_bottom = z_center - half_t
            z_top = z_center + half_t
            color = layer.get("color", "#AAAAAA")
            name = layer.get("name", "")

            # Draw rectangular slab
            verts = np.array([
                [bounds[0], bounds[0], z_bottom],
                [bounds[1], bounds[0], z_bottom],
                [bounds[1], bounds[1], z_bottom],
                [bounds[0], bounds[1], z_bottom],
                [bounds[0], bounds[0], z_top],
                [bounds[1], bounds[0], z_top],
                [bounds[1], bounds[1], z_top],
                [bounds[0], bounds[1], z_top],
            ])

            # Top and bottom faces
            for idx_set in [[0, 1, 2, 3], [4, 5, 6, 7]]:
                face = Poly3DCollection([verts[idx_set]], alpha=0.6,
                                        facecolor=color, edgecolor='k',
                                        linewidths=0.5)
                ax.add_collection3d(face)

            # Side faces
            side_idxs = [[0, 1, 5, 4], [1, 2, 6, 5],
                         [2, 3, 7, 6], [3, 0, 4, 7]]
            for idx_set in side_idxs:
                face = Poly3DCollection([verts[idx_set]], alpha=0.3,
                                        facecolor=color, edgecolor='k',
                                        linewidths=0.3)
                ax.add_collection3d(face)

            # Label
            ax.text(bounds[1] + 0.1, 0, z_center, name,
                    fontsize=8, color='black', va='center')

        # Interface dashed lines between layers
        z_levels = sorted(set(
            l["z_level"] - l["thickness"] / 2 for l in layers
        ) | set(
            l["z_level"] + l["thickness"] / 2 for l in layers
        ))
        for z in z_levels:
            ax.plot3D([bounds[0], bounds[1]], [0, 0], [z, z],
                      'k--', alpha=0.3, linewidth=0.5)

        ax.set_xlim(bounds[0] - 0.3, bounds[1] + 0.5)
        ax.set_ylim(bounds)
        all_z = [l["z_level"] for l in layers]
        if all_z:
            ax.set_zlim(min(all_z) - 0.5, max(all_z) + 0.5)
        ax.set_title(self.meso_data.get("title", "Meso"), fontsize=12,
                     fontweight='bold', pad=10)

    def _plot_micro(self, ax) -> None:
        """Render micro scale: fiber/matrix distribution."""
        fibers = self.micro_data.get("fibers")
        matrix = self.micro_data.get("matrix_points")

        if fibers is not None:
            fibers = np.asarray(fibers)
            ax.scatter(fibers[:, 0], fibers[:, 1], fibers[:, 2],
                       c='#DAA520', s=30, alpha=0.8, label='Fibers',
                       edgecolors='#8B6914', linewidths=0.5)

        if matrix is not None:
            matrix = np.asarray(matrix)
            ax.scatter(matrix[:, 0], matrix[:, 1], matrix[:, 2],
                       c='#87CEEB', s=8, alpha=0.4, label='Matrix')

        # Set limits
        all_pts = []
        if fibers is not None:
            all_pts.append(fibers)
        if matrix is not None:
            all_pts.append(matrix)
        if all_pts:
            combined = np.vstack(all_pts)
            for i, lbl in enumerate(['X', 'Y', 'Z']):
                lo, hi = combined[:, i].min(), combined[:, i].max()
                margin = 0.2 * (hi - lo) if hi > lo else 1.0
                getattr(ax, f'set_{lbl.lower()}lim')(lo - margin, hi + margin)

        ax.legend(fontsize=8, loc='upper right')
        ax.set_title(self.micro_data.get("title", "Micro"), fontsize=12,
                     fontweight='bold', pad=10)

    def plot(self, title: str = "M3 Scale Analysis",
             save: bool = True, interactive: bool = False,
             mapa: Optional[Any] = None,
             log: Optional[Any] = None,
             entry_id: Optional[str] = None) -> str:
        """Render 3-panel 3D plot with Macro/Meso/Micro scales.

        Returns
        -------
        str
            Path to saved PNG.
        """
        _set_interactive(interactive)
        fig = plt.figure(figsize=(18, 6))

        # Panel 1 — Macro
        ax1 = fig.add_subplot(131, projection='3d')
        self._plot_macro(ax1)

        # Panel 2 — Meso
        ax2 = fig.add_subplot(132, projection='3d')
        self._plot_meso(ax2)

        # Panel 3 — Micro
        ax3 = fig.add_subplot(133, projection='3d')
        self._plot_micro(ax3)

        fig.suptitle(title, fontsize=15, fontweight='bold', y=1.02)

        plt.tight_layout()

        result = ""
        if save:
            result = _plot_filename("m3_visualization")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "geral",
                            f"m3_viz_{title[:20]}",
                            {"file": result,
                             "macro_bounds": self.macro_data.get("bounds"),
                             "n_meso_layers": len(
                                 self.meso_data.get("layers", [])),
                             "micro_has_fibers": str(
                                 self.micro_data.get("fibers") is not None)},
                            tags=["m3", "macro", "meso", "micro",
                                  "multi-scale"],
                            source="cad_visualization.M3Visualizer.plot")
            _maybe_log(log, "Rendered M3 multi-scale visualization",
                       "Visualize Macro/Meso/Micro analysis scales",
                       "cad_visualization.py:M3Visualizer.plot",
                       {"method": "3-panel 3D plot", "tool": "matplotlib"},
                       domain="geral", scale="macro,meso,micro",
                       parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  FAILURE ENVELOPE
# ═══════════════════════════════════════════════════════════════

def failure_envelope_points(criterion: str = "tsai_wu",
                            Xt: float = 50, Xc: float = 30,
                            Yt: float = 15, Yc: float = 10,
                            S: float = 8, n: int = 50) -> Dict:
    """Generate failure envelope contour points for plotting.

    Returns x/y coordinates of sigma_11/sigma_22 at FI=1.
    """
    angles = np.linspace(0, 2 * np.pi, n)
    s11, s22 = [], []

    for theta in angles:
        # Radial search for failure boundary
        for r in np.linspace(0, max(Xt, Xc, Yt, Yc) * 1.5, 200):
            sx = r * np.cos(theta)
            sy = r * np.sin(theta)
            if criterion == "tsai_wu":
                from structural_analysis import tsai_wu_failure
                result = tsai_wu_failure(sx, sy, 0, Xt, Xc, Yt, Yc, S)
            else:
                from structural_analysis import max_stress_failure
                result = max_stress_failure(sx, sy, 0, Xt, Xc, Yt, Yc, S)

            if result["failure_index"] >= 0.95:
                s11.append(sx)
                s22.append(sy)
                break

    return {"sigma_11": s11, "sigma_22": s22, "criterion": criterion}


class FailureEnvelope:
    """Failure envelope 2D/3D plotting for composite materials."""

    @staticmethod
    def plot(criterion: str = "tsai_wu",
             Xt: float = 50, Xc: float = 30,
             Yt: float = 15, Yc: float = 10,
             S: float = 8,
             title: str = "Failure Envelope",
             save: bool = True, interactive: bool = False,
             mapa: Optional[Any] = None,
             log: Optional[Any] = None,
             entry_id: Optional[str] = None) -> str:
        """Plot 2D failure envelope for composite lamina.

        Returns path to saved PNG.
        """
        _set_interactive(interactive)
        data = failure_envelope_points(criterion, Xt, Xc, Yt, Yc, S)

        fig, ax = plt.subplots(figsize=(8, 7))
        ax.fill(data["sigma_11"], data["sigma_22"], alpha=0.3,
                color='skyblue', label=f'Safe region ({criterion})')
        ax.plot(data["sigma_11"], data["sigma_22"], 'b-', linewidth=1.5)

        ax.axhline(0, color='gray', linewidth=0.5)
        ax.axvline(0, color='gray', linewidth=0.5)
        ax.set_xlabel(r"$\sigma_{11}$ (MPa)")
        ax.set_ylabel(r"$\sigma_{22}$ (MPa)")
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        result = ""
        if save:
            result = _plot_filename("failure_envelope")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "materiais",
                            f"failure_envelope_{criterion}",
                            {"file": result, "criterion": criterion,
                             "Xt": Xt, "Xc": Xc, "Yt": Yt, "Yc": Yc, "S": S},
                            tags=["failure", "envelope", criterion],
                            source="cad_visualization.FailureEnvelope.plot")
            _maybe_log(log, "Generated failure envelope plot",
                       "Visualize composite failure envelope",
                       "cad_visualization.py:FailureEnvelope.plot",
                       {"method": "2D fill + contour", "tool": "matplotlib",
                        "params": {"criterion": criterion}},
                       domain="materiais", parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  WIND ROSE
# ═══════════════════════════════════════════════════════════════

@dataclass
class WindRose:
    """Wind rose data generator."""
    directions: List[str] = None
    frequencies_pct: List[float] = None
    avg_speeds_ms: List[float] = None

    def __post_init__(self):
        if self.directions is None:
            self.directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        if self.frequencies_pct is None:
            self.frequencies_pct = [8, 6, 12, 15, 20, 18, 14, 7]
        if self.avg_speeds_ms is None:
            self.avg_speeds_ms = [4, 3.5, 5, 6, 7, 6.5, 5.5, 4.5]

    def polar_data(self) -> Dict:
        """Return data formatted for polar plot."""
        theta = np.radians(np.linspace(0, 360, len(self.directions),
                                       endpoint=False))
        return {
            "theta": theta.tolist(),
            "frequencies": self.frequencies_pct,
            "speeds": self.avg_speeds_ms,
            "directions": self.directions,
        }

    def plot(self, title: str = "Wind Rose",
             save: bool = True, interactive: bool = False,
             mapa: Optional[Any] = None,
             log: Optional[Any] = None,
             entry_id: Optional[str] = None) -> str:
        """Render wind rose polar plot.

        Returns path to saved PNG.
        """
        _set_interactive(interactive)
        data = self.polar_data()
        theta = np.array(data["theta"]) + np.pi / 8

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

        speeds = np.array(data.get("avg_speeds_ms", data.get("speeds", [5]*len(data["frequencies"]))))
        bars = ax.bar(theta, data["frequencies"],
                      width=np.pi / 4, alpha=0.7,
                      color=plt.cm.viridis(speeds / max(speeds)),
                      edgecolor='k', linewidth=0.5)

        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_xticks(theta)
        ax.set_xticklabels(data["directions"], fontsize=9)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=20)

        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=max(speeds)))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.7, pad=0.1,
                            label="Avg Wind Speed (m/s)")

        result = ""
        if save:
            result = _plot_filename("wind_rose")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "ambiente",
                            f"wind_rose_{title[:15]}",
                            {"file": result, "directions": data["directions"],
                             "frequencies": data["frequencies"]},
                            tags=["wind", "rose", "environment"],
                            source="cad_visualization.WindRose.plot")
            _maybe_log(log, "Generated wind rose plot",
                       "Visualize wind frequency and speed distribution",
                       "cad_visualization.py:WindRose.plot",
                       {"method": "polar bar chart", "tool": "matplotlib"},
                       domain="ambiente", parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  LAMINATE 3D VIEW (upgraded with 3D depth)
# ═══════════════════════════════════════════════════════════════

@dataclass
class LaminateView:
    """Laminate stacking sequence visualization with 3D depth."""
    layers: List[Dict] = None

    def __post_init__(self):
        if self.layers is None:
            self.layers = [
                {"material": "graphite", "thickness_mm": 0.5, "angle": 0},
                {"material": "paper_mache", "thickness_mm": 4.0, "angle": 45},
                {"material": "paper_mache", "thickness_mm": 4.0, "angle": -45},
                {"material": "graphite", "thickness_mm": 0.5, "angle": 0},
            ]

    def stacking_data(self) -> Dict:
        """Generate layer positions for stacked bar visualization."""
        z = 0
        data = []
        for l in self.layers:
            data.append({
                "material": l["material"],
                "z_start_mm": round(z, 2),
                "z_end_mm": round(z + l["thickness_mm"], 2),
                "thickness_mm": l["thickness_mm"],
                "angle_deg": l["angle"],
            })
            z += l["thickness_mm"]
        return {
            "total_thickness_mm": round(z, 2),
            "n_layers": len(self.layers),
            "layers": data,
        }

    def get_material_color(self, material: str) -> str:
        """Return a representative color for a material type."""
        palette = {
            "graphite": "#555555",
            "carbon": "#333333",
            "fiberglass": "#87CEEB",
            "paper_mache": "#D2B48C",
            "foam": "#FFD700",
            "gelcoat": "#4A90D9",
            "resin": "#D4A017",
            "core": "#8B4513",
        }
        for key, color in palette.items():
            if key in material.lower():
                return color
        return "#AAAAAA"

    def plot_3d(self, title: str = "Laminate Stacking Sequence (3D)",
                show_angles: bool = True, depth: float = 2.0,
                save: bool = True, interactive: bool = False,
                mapa: Optional[Any] = None,
                log: Optional[Any] = None,
                entry_id: Optional[str] = None) -> str:
        """Render laminate in 3D with depth, showing layers and fiber angles.

        Parameters
        ----------
        title : str
            Plot title.
        show_angles : bool
            Draw fiber orientation indicators on each layer.
        depth : float
            Visual depth/extent of each layer.
        save, interactive, mapa, log, entry_id : see other plot methods.

        Returns
        -------
        str
            Path to saved PNG.
        """
        _set_interactive(interactive)
        stack = self.stacking_data()

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        half_depth = depth / 2
        width = 3.0
        half_width = width / 2

        for layer in stack["layers"]:
            z0 = layer["z_start_mm"]
            z1 = layer["z_end_mm"]
            mat = layer["material"]
            angle = layer["angle_deg"]
            color = self.get_material_color(mat)

            # Layer faces
            verts_bottom = [
                [-half_width, -half_depth, z0],
                [half_width, -half_depth, z0],
                [half_width, half_depth, z0],
                [-half_width, half_depth, z0],
            ]
            verts_top = [
                [-half_width, -half_depth, z1],
                [half_width, -half_depth, z1],
                [half_width, half_depth, z1],
                [-half_width, half_depth, z1],
            ]

            # Top face
            top_poly = Poly3DCollection([verts_top], alpha=0.7,
                                        facecolor=color, edgecolor='k',
                                        linewidths=0.8)
            ax.add_collection3d(top_poly)

            # Side faces
            for idx1, idx2 in [(0, 1), (1, 2), (2, 3), (3, 0)]:
                side_verts = [
                    verts_bottom[idx1], verts_bottom[idx2],
                    verts_top[idx2], verts_top[idx1],
                ]
                side = Poly3DCollection([side_verts], alpha=0.4,
                                        facecolor=color, edgecolor='k',
                                        linewidths=0.3)
                ax.add_collection3d(side)

            # Fiber angle indicator
            if show_angles:
                rad = np.radians(angle)
                r_len = half_width * 0.6
                mid_z = (z0 + z1) / 2
                dx = r_len * np.cos(rad)
                dy = r_len * np.sin(rad)
                ax.plot([-dx, dx], [-dy, dy], [mid_z, mid_z],
                        'r-', linewidth=2.5, alpha=0.9)
                # Angle label
                ax.text(0, half_depth + 0.2, mid_z,
                        f"{angle}°", fontsize=8, ha='center', va='center')

        # Labels on right side
        for layer in stack["layers"]:
            mid_z = (layer["z_start_mm"] + layer["z_end_mm"]) / 2
            ax.text(half_width + 0.3, 0, mid_z,
                    f"{layer['material']}\n{layer['thickness_mm']}mm",
                    fontsize=7, va='center')

        ax.set_xlabel("Width (mm)")
        ax.set_ylabel("Depth (mm)")
        ax.set_zlabel("Thickness (mm)")
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.view_init(elev=25, azim=-45)

        total_t = stack["total_thickness_mm"]
        ax.set_xlim(-half_width - 0.5, half_width + 1.5)
        ax.set_ylim(-half_depth - 0.5, half_depth + 0.5)
        ax.set_zlim(-0.5, total_t + 0.5)

        result = ""
        if save:
            result = _plot_filename("laminate_3d")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "materiais",
                            f"laminate_3d_{title[:20]}",
                            {"file": result, "n_layers": stack["n_layers"],
                             "total_thickness": total_t,
                             "layer_materials": [l["material"]
                                                  for l in stack["layers"]]},
                            tags=["laminate", "composite", "3d"],
                            source="cad_visualization.LaminateView.plot_3d")
            _maybe_log(log, "Rendered 3D laminate stacking sequence",
                       "Visualize composite layup with fiber orientations",
                       "cad_visualization.py:LaminateView.plot_3d",
                       {"method": "3D Poly3DCollection layers", "tool": "matplotlib",
                        "params": {"show_angles": show_angles, "depth": depth}},
                       domain="materiais", scale="meso",
                       parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  BOUNDARY LAYER VIEW
# ═══════════════════════════════════════════════════════════════

class BoundaryLayerView:
    """3D boundary layer visualization — gradient from surface to free stream.

    Shows velocity/temperature profile development along a surface with
    color mapping from wall to free stream.
    """

    def __init__(self, surface_points: Optional[np.ndarray] = None,
                 profile_data: Optional[Dict] = None):
        """Initialize boundary layer visualization data.

        Parameters
        ----------
        surface_points : (N, 3) array, optional
            Points on the solid surface.
        profile_data : dict, optional
            'x': 1-D array of streamwise positions
            'y': 1-D array of wall-normal positions
            'velocity': 2-D array (nx, ny) velocity magnitude
            'delta_99': array of boundary layer thickness at each x
            'title': str
        """
        self.surface_points = surface_points
        if profile_data is None:
            self.profile_data = self._default_profile()
        else:
            self.profile_data = profile_data

    @staticmethod
    def _default_profile() -> Dict:
        """Generate a synthetic turbulent boundary layer profile."""
        nx, ny = 30, 25
        x = np.linspace(0, 2.0, nx)
        y = np.linspace(0, 0.5, ny)
        U_inf = 10.0
        delta_99 = 0.02 * x**0.8 + 0.01

        velocity = np.zeros((nx, ny))
        for i in range(nx):
            delta = delta_99[i]
            for j in range(ny):
                eta = y[j] / delta if delta > 0 else 10
                if eta <= 1:
                    # 1/7th power law
                    velocity[i, j] = U_inf * eta**(1/7)
                else:
                    velocity[i, j] = U_inf

        return {
            "x": x, "y": y, "velocity": velocity,
            "delta_99": delta_99,
            "U_inf": U_inf,
            "title": "Turbulent Boundary Layer Profile",
            "x_label": "Streamwise (m)",
            "y_label": "Wall-normal (m)",
            "value_label": "Velocity (m/s)",
        }

    def plot(self, title: Optional[str] = None,
             colormap: str = "plasma",
             show_delta: bool = True,
             save: bool = True, interactive: bool = False,
             mapa: Optional[Any] = None,
             log: Optional[Any] = None,
             entry_id: Optional[str] = None) -> str:
        """Render 3D boundary layer visualization.

        Shows a surface plot of velocity profile developing along
        the streamwise direction, with boundary layer thickness overlay.

        Parameters
        ----------
        title : str, optional
            Override default title.
        colormap : str
            Colormap for velocity field.
        show_delta : bool
            Overlay boundary layer thickness line.
        save, interactive, mapa, log, entry_id : see other plot methods.

        Returns
        -------
        str
            Path to saved PNG.
        """
        _set_interactive(interactive)
        pd = self.profile_data
        X, Y = np.meshgrid(pd["x"], pd["y"], indexing='ij')
        V = pd["velocity"]

        title_str = title or pd.get("title", "Boundary Layer")
        x_lbl = pd.get("x_label", "Streamwise (m)")
        y_lbl = pd.get("y_label", "Wall-normal (m)")
        v_lbl = pd.get("value_label", "Velocity (m/s)")

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        norm = Normalize(vmin=V.min(), vmax=V.max())
        surf = ax.plot_surface(X, V, Y, facecolors=plt.get_cmap(colormap)(norm(V)),
                               rstride=1, cstride=1, alpha=0.85,
                               linewidth=0, antialiased=True)

        # Free-stream plane
        U_inf = pd.get("U_inf", V.max())
        ax.plot_surface(X, np.full_like(X, U_inf), Y,
                        color='gray', alpha=0.15, linewidth=0)

        # Boundary layer thickness overlay
        if show_delta and "delta_99" in pd:
            delta = pd["delta_99"]
            ax.plot(pd["x"], [U_inf + 0.5] * len(pd["x"]), delta,
                    'r--', linewidth=2, alpha=0.8, label=r'$\delta_{99}$')
            # Fill between surface and delta
            for i in range(len(pd["x"])):
                y_line = np.linspace(0, delta[i], 20)
                v_line = np.interp(y_line / delta[i] if delta[i] > 0 else 0,
                                   np.linspace(0, 1, 10),
                                   U_inf * np.linspace(0, 1, 10)**(1/7))
                ax.plot([pd["x"][i]] * len(y_line), v_line, y_line,
                        'gray', alpha=0.15, linewidth=0.5)

        mappable = cm.ScalarMappable(norm, cmap=colormap)
        mappable.set_array(V)
        cbar = fig.colorbar(mappable, ax=ax, shrink=0.6, pad=0.1)
        cbar.set_label(v_lbl, fontsize=11)

        ax.set_xlabel(x_lbl)
        ax.set_ylabel(v_lbl)
        ax.set_zlabel(y_lbl)
        ax.set_title(title_str, fontsize=13, fontweight='bold')
        if show_delta and "delta_99" in pd:
            ax.legend(fontsize=9, loc='upper right')

        result = ""
        if save:
            result = _plot_filename("boundary_layer")
            plt.savefig(result, dpi=150, bbox_inches='tight')
            _maybe_register(mapa, entry_id, "fluidos",
                            f"boundary_layer_{title_str[:20]}",
                            {"file": result,
                             "nx": len(pd["x"]), "ny": len(pd["y"]),
                             "U_inf": U_inf,
                             "delta_max": float(pd["delta_99"].max())},
                            tags=["boundary_layer", "fluid", "profile"],
                            source="cad_visualization.BoundaryLayerView.plot")
            _maybe_log(log, "Rendered 3D boundary layer visualization",
                       "Visualize velocity profile from surface to free stream",
                       "cad_visualization.py:BoundaryLayerView.plot",
                       {"method": "3D surface plot with thickness overlay",
                        "tool": "matplotlib",
                        "params": {"colormap": colormap, "show_delta": show_delta}},
                       domain="fluidos", scale="micro",
                       parent_log=entry_id)

        if interactive:
            plt.show()
        else:
            plt.close(fig)

        return result


# ═══════════════════════════════════════════════════════════════
#  STL EXPORT
# ═══════════════════════════════════════════════════════════════

def geometry_to_stl(vertices: np.ndarray, faces: np.ndarray,
                    filename: str = "output.stl") -> str:
    """Export triangulated geometry to STL (ASCII) format."""
    _ensure_plots_dir()
    filepath = os.path.join(PLOTS_DIR, filename)
    with open(filepath, 'w') as f:
        f.write("solid exported\n")
        for face in faces:
            f.write("  facet normal 0 0 0\n")
            f.write("    outer loop\n")
            for vi in face:
                v = vertices[vi]
                f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid exported\n")
    return filepath
