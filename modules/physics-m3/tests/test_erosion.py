import numpy as np
import pytest
from modules.erosion import ErosionModel


@pytest.fixture
def erosion_model():
    return ErosionModel(material_density=2700, hardness=3e9)


def test_init_stores_properties(erosion_model):
    assert erosion_model.material_density == 2700.0
    assert erosion_model.hardness == 3e9


def test_finnie_erosion_returns_positive_volume(erosion_model):
    r = erosion_model.finnie_erosion(mass=1e-6, velocity=50, angle=30)
    assert 'volume_removed' in r
    assert 'mass_loss' in r
    assert 'erosion_rate' in r
    assert 'depth_per_particle' in r
    assert r['volume_removed'] > 0
    assert r['mass_loss'] > 0
    assert r['erosion_rate'] >= 0


def test_finnie_erosion_increases_with_velocity(erosion_model):
    r1 = erosion_model.finnie_erosion(mass=1e-6, velocity=25, angle=30)
    r2 = erosion_model.finnie_erosion(mass=1e-6, velocity=50, angle=30)
    # Erosion ∝ V² per Finnie: doubling velocity → ~4x erosion
    ratio = r2['volume_removed'] / r1['volume_removed']
    assert 3.0 < ratio < 5.0, f"V² scaling violated: ratio={ratio:.2f}"


def test_finnie_angle_dependence(erosion_model):
    """Erosion at 20° (ductile peak) should exceed erosion at 90°."""
    r_oblique = erosion_model.finnie_erosion(mass=1e-6, velocity=50, angle=20)
    r_normal = erosion_model.finnie_erosion(mass=1e-6, velocity=50, angle=90)
    assert r_oblique['volume_removed'] > r_normal['volume_removed'], \
        "Oblique impact should erode more than normal for ductile materials"


def test_blade_erosion_returns_reasonable_values(erosion_model):
    r = erosion_model.blade_erosion(tip_speed=80, chord=0.3)
    assert 'max_erosion_depth' in r
    assert 'total_erosion_depth' in r
    assert 'rain_erosion_rate' in r
    max_depth_mm = r.get('max_erosion_depth', 0) * 1000  # m → mm
    assert 0.001 < max_depth_mm < 1000.0, f"Max erosion depth {max_depth_mm:.4f} mm outside expected range"


def test_cumulative_erosion_scales_with_particle_count(erosion_model):
    r1 = erosion_model.cumulative_erosion(mass=1e-6, velocity=50, angle=30, n_particles=10)
    r2 = erosion_model.cumulative_erosion(mass=1e-6, velocity=50, angle=30, n_particles=100)
    # 10x particles → ~10x volume
    ratio = r2['total_volume'] / r1['total_volume']
    assert 8.0 < ratio < 12.0, f"Particle count scaling violated: ratio={ratio:.2f}"


def test_invalid_input_raises(erosion_model):
    with pytest.raises(ValueError):
        erosion_model.finnie_erosion(mass=-1e-6, velocity=50, angle=30)
    with pytest.raises(ValueError):
        erosion_model.finnie_erosion(mass=1e-6, velocity=0, angle=30)
    with pytest.raises(ValueError):
        erosion_model.finnie_erosion(mass=1e-6, velocity=50, angle=0)
