"""
src/topopt/visualization.py — Plotting utilities for Topology Optimization.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def plot_density_field(density_field: np.ndarray, nelx: int, nely: int, output_path: str = None):
    """
    Plots the 2D density field resulting from topology optimization.
    
    Parameters
    ----------
    density_field : np.ndarray
        Array of shape (nelx * nely,) containing densities [0, 1].
    nelx : int
        Number of elements in x direction.
    nely : int
        Number of elements in y direction.
    output_path : str, optional
        If provided, saves the plot to this path. Otherwise, shows the plot.
    """
    # Reshape density to 2D grid (flip y for correct visual orientation)
    grid = density_field.reshape((nelx, nely)).T
    grid = np.flipud(grid)
    
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    
    # Custom colormap: black (void) to white (solid)
    cmap = LinearSegmentedColormap.from_list('topopt', ['black', 'white'], N=256)
    
    ax.imshow(grid, cmap=cmap, aspect='equal', interpolation='bilinear', vmin=0, vmax=1)
    
    ax.set_title(f'Topology Optimization Result ({nelx}x{nely})')
    ax.set_xlabel('X Elements')
    ax.set_ylabel('Y Elements')
    ax.axis('off')
    
    if output_path:
        plt.savefig(output_path, bbox_inches='tight', pad_inches=0.1)
        plt.close()
        print(f"✅ Density field plot saved to {output_path}")
    else:
        plt.show()
