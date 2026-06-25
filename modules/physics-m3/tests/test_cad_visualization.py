import matplotlib; matplotlib.use("Agg")
import numpy as np; import pytest
from modules.cad_visualization import (
    AirfoilCoordinates, BladeGeometry, StressField, HeatMap3D,
    M3Visualizer, FailureEnvelope, WindRose, LaminateView,
    stress_color_map, geometry_to_stl,
)

def test_airfoil(): a=AirfoilCoordinates(); c=a.coordinates(); assert len(c)==2
def test_blade(): b=BladeGeometry(); assert b.length_m==1.5
def test_color(): assert type(stress_color_map(100,250)) == str
def test_stress():
    n=np.array([[0,0,0],[0,0.1,0],[0.1,0.1,0],[0.1,0,0],[0.2,0,0],[0.2,0.1,0]], dtype=float)
    s=np.ones(6); sf=StressField(nodes=n, stress_values=s); assert sf is not None
def test_heatmap(): x=y=z=v=np.array([[0,1],[0,1]], dtype=float); assert HeatMap3D(x=x,y=y,z=z,values=v)
def test_viz(): assert M3Visualizer() is not None
def test_fe(): assert FailureEnvelope() is not None
def test_wr(): assert WindRose() is not None
def test_lam(): assert LaminateView() is not None
def test_stl():
    v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float)
    f=np.array([[0,1,2],[0,1,3]], dtype=int)
    assert geometry_to_stl(v,f) is not None
