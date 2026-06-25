import pytest
from modules.m3_analysis import MacroScale, MesoScale, PlyLayer

def test_macro():
    m = MacroScale(altitude_m=100, wind_speed_ms=10)
    assert m.density_air() > 0

def test_macro_summary():
    m = MacroScale(altitude_m=100, wind_speed_ms=10)
    s = m.summary()
    assert type(s) == dict and len(s) > 0

def test_ply():
    p = PlyLayer("carbon", thickness_mm=1, fiber_orientation_deg=45)
    assert p.fiber_orientation_deg == 45

def test_meso_add():
    me = MesoScale()
    me.add_layer(PlyLayer("glass", 2, 90))
    assert len(me.layers) == 1
