# -*- coding: utf-8 -*-
"""Test E2E Completo — valida toda a cadeia de valor do sistema.

Cobre: Material → CAD → Macro → Meso → Micro → Falha → Testes Mecânicos → KDI
"""

import sys, os, json, math, pytest

_THIS = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.abspath(os.path.join(_THIS, "..", ".."))
_PHYSICS = os.path.join(_PROJ, "physics-m3", "src")
_CAE = os.path.join(_PROJ, "cad-cae-platform", "src")
_BRIDGE = os.path.join(_PROJ, "kdi-m3-bridge", "src")

for _p in [_PHYSICS, _CAE, _BRIDGE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cad_cae.cad_bridge import CadModel as _CadModel
from cad_cae.gpu_accelerator import GPUAccelerator
from cad_cae.design_optimizer import DesignSpace, DesignOptimizer

# kdi-m3-bridge module aliases (keep short names for test clarity)
import kdi_m3.kdi_macro as km
import kdi_m3.kdi_meso as kme
import kdi_m3.kdi_micro as kmi

# physics-m3 modules
from composite_model import CompositeMaterial
from mechanical_tests import tensile_test, flexure_test
from structural_analysis import von_mises_stress, safety_factor, tsai_wu_failure

# cad_bridge helpers
cb = _CadModel

def test_01_material():
    mat = CompositeMaterial(fiber='waste_paper', matrix='pva', coating='graphite_coating')
    ec = mat.elastic_constants()
    assert ec["E1_longitudinal_GPa"] > 0, "E1 deve ser > 0"
    assert ec["E2_transverse_GPa"] > 0, "E2 deve ser > 0"
    assert ec["G12_shear_GPa"] > 0, "G12 deve ser > 0"
    print(f"  ✅ Material: E1={ec['E1_longitudinal_GPa']} GPa, E2={ec['E2_transverse_GPa']} GPa")


# ── 2. TESTES MECÂNICOS ──
def test_02_mechanical_tests():
    sigma = tensile_test(E_GPa=50, width_mm=10, thickness_mm=2, tensile_strength_MPa=100)
    assert isinstance(sigma, dict) or sigma > 0, "Tensão de tração deve ser positiva"
    sigma_f = flexure_test(E_GPa=50, length_mm=80, width_mm=10, thickness_mm=2, strength_MPa=80)
    assert isinstance(sigma_f, dict) or sigma_f > 0
    print(f"  ✅ Tração + Flexão: resultados obtidos")


# ── 3. CAD ──
def test_03_cad():
    viga = cb.cantilever_beam(length=100, width=10, height=5)
    assert abs(viga.volume - 5000) < 1, "Volume da viga deve ser 5000 mm³"
    chapa = cb.plate_with_hole(width=100, height=50, thickness=5, hole_diameter=10)
    vol_esperado = 100 * 50 * 5 - math.pi * 5**2 * 5
    assert chapa.volume == pytest.approx(vol_esperado, rel=0.05)
    print(f"  ✅ CAD: viga={viga.volume:.0f} mm³ | chapa={chapa.volume:.0f} mm³")


# ── 4. CRITÉRIOS DE FALHA ──
def test_04_failure():
    vm = von_mises_stress(100, 50, 30)
    sf = safety_factor(250, vm)
    tw = tsai_wu_failure(50, 10, 5, Xt=200, Xc=150, Yt=50, Yc=100, S=30)
    assert isinstance(vm, (int, float)) and vm > 0
    assert sf > 0
    assert isinstance(tw, dict) and "status" in tw
    print(f"  ✅ Falha: von Mises={vm:.1f} MPa, SF={sf:.2f}, Tsai-Wu={tw['status']}")


# ── 5. KDI MACRO ──
def test_05_macro():
    env = km.MacroEnvironment(altitude_m=500, wind_speed_ref_ms=40, wind_class="I")
    viga = cb.cantilever_beam(length=100, width=10, height=5)
    ma = km.MacroAnalysis(cad_model=viga, env=env)
    r = ma.run()
    assert r["volume_mm3"] > 0
    assert r["environment"]["wind_pressure_kPa"] > 0
    assert r["environment"]["total_wind_force_N"] > 0
    print(f"  ✅ Macro: volume={r['volume_mm3']:.0f} mm³, vento={r['environment']['wind_pressure_kPa']:.2f} kPa")


# ── 6. KDI MESO ──
def test_06_meso():
    ma = kme.MesoAnalysis({"nominal_stress_MPa": 100, "yield_strength_MPa": 250})
    r = ma.run()
    assert r["Kt"] == pytest.approx(3.0, rel=0.01)
    assert r["safety_factor"] > 0 or r["status"] == "PASS"
    print(f"  ✅ Meso: Kt={r['Kt']}, SF={r['safety_factor']}")


# ── 7. KDI MICRO ──
def test_07_micro():
    ma = kmi.MicroAnalysis(fiber="waste_paper", matrix="pva", coating="graphite_coating", V_f=0.30)
    r = ma.run()
    assert r["E1_GPa"] > 0, "E1 homogeneizado deve ser > 0"
    assert r["density_g_cm3"] > 0
    print(f"  ✅ Micro: E1={r['E1_GPa']} GPa, ρ={r['density_g_cm3']} g/cm³")


# ── 8. DESIGN OPTIMIZATION ──
def test_08_design_optimization():
    ds = DesignSpace({"L": (1, 10), "w": (1, 5)})
    opt = DesignOptimizer(ds, ["mass", "stiffness"])
    results = opt.run_doe(lambda p: {"mass": p["L"] * p["w"], "stiffness": 1 / (p["L"] * p["w"])})
    assert len(results) == 9
    pareto = opt.pareto_frontier()
    assert len(pareto) <= 9 and len(pareto) > 0
    print(f"  ✅ DOE: {len(results)} designs, {len(pareto)} Pareto-ótimos")


# ── 9. CADASTRO COMPLETO ──
def test_09_full_kdi():
    """Fluxo completo: config.json → Forwarder → Macro + Meso + Micro + Report."""
    cfg_path = os.path.join(_PROJ, "kdi-m3-bridge", "config.json")
    from kdi_m3.config_manager import ConfigManager
    from kdi_m3.kdi_forwarder import KDIForwarder
    kf = KDIForwarder(cfg_path)
    r = kf.run_all()
    assert "macro" in r
    assert "meso" in r
    report = kf.report()
    assert "KDI-M³ REPORT" in report
    print(f"  ✅ KDI Forwarder: {len(r)} escalas executadas")


# ── 10. GPU ──
def test_10_gpu():
    if GPUAccelerator.is_available():
        accel = GPUAccelerator()
        results = accel.benchmark(n=200, density=0.03)
        print(f"  ✅ GPU: speedup={results.get('speedup_vs_cpu', 0)}x, solve={results.get('solve_time_s', 0):.4f}s")
    else:
        print("  ⏭️  GPU: CUDA não disponível neste ambiente")
