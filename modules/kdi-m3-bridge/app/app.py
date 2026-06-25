"""KDI-M³ Dashboard — AI-assisted CAD/CAE with interactive config control."""

import importlib.util as _ilu
import sys, os, json

_THIS = os.path.dirname(os.path.abspath(__file__))
_WS = os.path.abspath(os.path.join(_THIS, ".."))
_PROJ = os.path.abspath(os.path.join(_WS, ".."))


def _import_by_path(rel_path: str, mod_name: str):
    full = os.path.join(_PROJ, rel_path)
    spec = _ilu.spec_from_file_location(mod_name, full)
    mod = _ilu.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_kf_mod = _import_by_path("kdi-m3-bridge/modules/kdi_forwarder.py", "kdi_forwarder")
_macro_mod = _import_by_path("kdi-m3-bridge/modules/kdi_macro.py", "kdi_macro")
_meso_mod = _import_by_path("kdi-m3-bridge/modules/kdi_meso.py", "kdi_meso")
_micro_mod = _import_by_path("kdi-m3-bridge/modules/kdi_micro.py", "kdi_micro")
_cad_mod = _import_by_path("cad-cae-platform/modules/cad_bridge.py", "cad_bridge")

import streamlit as st

st.set_page_config(page_title="KDI-M³ AI CAD/CAE", layout="wide")
st.title("KDI-M³ CAD/CAE — AI-Assisted Design")
st.caption("Macro → Meso → Micro | config.json-driven | NVIDIA CUDA accelerated")

cfg_path = os.path.join(_WS, "config.json")

cfg_tab, macro_tab, meso_tab, micro_tab, rpt_tab = st.tabs(["📋 Config", "🌍 Macro", "🔧 Meso", "🔬 Micro", "📊 Report"])

with cfg_tab:
    st.header("Configuration Editor")
    with open(cfg_path) as f:
        cfg_data = json.load(f)
    new_cfg = st.text_area("config.json", json.dumps(cfg_data, indent=2), height=400)
    if st.button("Save Config"):
        with open(cfg_path, "w") as f:
            json.dump(json.loads(new_cfg), f, indent=2)
        st.success("Saved!")
    st.subheader("Material")
    col = st.columns(3)
    with col[0]: fiber = st.selectbox("Fiber", ["waste_paper", "glass", "carbon"], index=0)
    with col[1]: matrix = st.selectbox("Matrix", ["pva", "epoxy", "polyester"], index=0)
    with col[2]: coating = st.selectbox("Coating", ["graphite_coating", "none"], index=0)
    Vf = st.slider("Fiber Volume Fraction", 0.05, 0.60, 0.15)
    if st.button("Preview Material"):
        micro = _micro_mod.MicroAnalysis(fiber=fiber, matrix=matrix, coating=coating, V_f=Vf).run()
        st.json(micro)

with macro_tab:
    st.header("Macro-Scale")
    kf = _kf_mod.KDIForwarder(cfg_path)
    if st.button("Run Macro"):
        with st.spinner("..."):
            r = kf.run_macro()
        st.json(r)
        env = r.get("environment", {})
        c1, c2 = st.columns(2)
        c1.metric("Volume", f"{r.get('volume_mm3',0):.0f} mm³")
        c2.metric("Wind", f"{env.get('wind_pressure_kPa',0):.2f} kPa")

with meso_tab:
    st.header("Meso-Scale")
    col = st.columns(3)
    nom = col[0].number_input("Nominal Stress (MPa)", 10, 500, 100)
    yield_v = col[1].number_input("Yield (MPa)", 100, 1000, 250)
    hole = col[2].number_input("Hole/Width Ratio", 0.05, 0.5, 0.1)
    if st.button("Run Meso"):
        ma = _meso_mod.MesoAnalysis({"nominal_stress_MPa": nom, "yield_strength_MPa": yield_v,
                                     "hole_diameter_mm": hole * 50, "plate_width_mm": 50})
        r = ma.run()
        st.metric("Kt (Stress Concentration)", r["Kt"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak Stress", f'{r["peak_stress_MPa"]} MPa')
        c2.metric("von Mises", f'{r["von_mises_MPa"]} MPa')
        c3.metric("Safety Factor", f'{r["safety_factor"]}')

with micro_tab:
    st.header("Micro-Scale")
    kf = _kf_mod.KDIForwarder(cfg_path)
    if st.button("Run Micro"):
        with st.spinner("..."):
            r = kf.run_micro()
        st.json(r)
        c1, c2, c3 = st.columns(3)
        c1.metric("E1 (GPa)", r.get("E1_GPa", 0))
        c2.metric("E2 (GPa)", r.get("E2_GPa", 0))
        c3.metric("Density", r.get("density_g_cm3", 0))

with rpt_tab:
    st.header("Full M³ Report")
    kf = _kf_mod.KDIForwarder(cfg_path)
    if st.button("Run All"):
        with st.spinner("Macro + Meso + Micro..."):
            r = kf.run_all()
        st.json(r)
