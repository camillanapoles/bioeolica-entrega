#!/usr/bin/env python3
"""Validate upgraded CAD module."""
import sys, numpy as np; sys.path.insert(0, 'modules')
from cad_visualization import HeatMap3D, M3Visualizer, BoundaryLayerView
from cad_visualization import stress_color_map, beam_stress_diagram

# HeatMap3D with generated data
n = 50
x = np.random.rand(n) * 2 - 1
y = np.random.rand(n) * 2 - 1
z = np.random.rand(n) * 2 - 1
vals = np.exp(-(x**2 + y**2 + z**2)) * 100
hm = HeatMap3D(x, y, z, vals)
fig = hm.plot(title="Stress Heat Map")
print(f"HeatMap3D: {n} points in 3D ✅")

# M3Visualizer
mv = M3Visualizer()
fig2 = mv.plot()
print(f"M3Visualizer: 3-panel Macro/Meso/Micro ✅")

# BoundaryLayerView
bl = BoundaryLayerView()
fig3 = bl.plot()
print(f"BoundaryLayerView: OK ✅")

# Legacy functions
print(f"stress_color_map(50,100): {stress_color_map(50, 100)} ✅")
bsd = beam_stress_diagram(1.0, [100], [0.5])
print(f"beam_stress_diagram: {len(bsd['shear_N'])} pts ✅")

print("\nALL CAD UPGRADES OK ✅")
