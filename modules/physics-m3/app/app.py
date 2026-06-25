"""Physics M³ Workspace — Streamlit Dashboard.

Usage: streamlit run app/app.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.set_page_config(page_title="Physics M³ Workspace", layout="wide")
st.title("Physics M³ — Computational Mechanics Workspace")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Materials", "FEM", "TopOpt", "Crystal", "DT", "About"
])

with tab1:
    st.header("Composite Material Explorer")
    from modules.m3_analysis import CompositeLayer, CompositeLamina, CompositeLaminate
    col1, col2 = st.columns(2)
    with col1:
        vf = st.slider("Fiber Volume Fraction", 0.1, 0.7, 0.5)
        angle = st.slider("Fiber Angle (°)", 0, 90, 0)
    with col2:
        E_f = st.number_input("Fiber Modulus (GPa)", 70.0, 400.0, 235.0)
        E_m = st.number_input("Matrix Modulus (GPa)", 1.0, 10.0, 3.5)
    lamina = CompositeLamina(E_f=E_f*1e9, E_m=E_m*1e9, V_f=vf)
    st.metric("Longitudinal Modulus E₁", f"{lamina.E1/1e9:.1f} GPa")
    st.metric("Transverse Modulus E₂", f"{lamina.E2/1e9:.1f} GPa")

with tab2:
    st.header("FEM Solver")
    from modules.fem_solver import FEM
    nx, ny = st.columns(2)
    with nx: nelx = st.number_input("Elements X", 4, 40, 10)
    with ny: nely = st.number_input("Elements Y", 4, 40, 6)
    fem = FEM(nelx=nelx, nely=nely)
    fem.solve()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.tripcolor(fem.mesh_nodes[:, 0], fem.mesh_nodes[:, 1], fem.u)
    ax.set_title("Displacement Field")
    st.pyplot(fig); plt.close()

with tab3:
    st.header("Topology Optimization")
    from modules.topology_optimization import TopOpt
    col = st.columns(3)
    with col[0]: tvf = st.slider("Volume Fraction", 0.2, 0.8, 0.4, key="topvf")
    with col[1]: tpen = st.slider("Penalization", 1.0, 5.0, 3.0, key="toppen")
    with col[2]: tit = st.slider("Max Iterations", 10, 200, 40, key="topit")
    if st.button("Run TopOpt"):
        opt = TopOpt(nelx=20, nely=12, volfrac=tvf, penal=tpen)
        x = opt.solve(max_iter=tit, verbose=False)
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.imshow(x, cmap="gray_r", aspect="auto")
        ax.set_title(f"TopOpt Density (compl={opt.compliance_history[-1]:.2f})")
        st.pyplot(fig); plt.close()

with tab4:
    st.header("Crystal Lattice Explorer")
    from modules.crystal_lattice import CrystalLattice
    lt = st.selectbox("Lattice", ["bcc", "fcc", "sc", "hcp"])
    cl = CrystalLattice(lt, a=st.number_input("Lattice constant (nm)", 0.2, 0.5, 0.286))
    st.metric("Coordination Number", cl.coordination_number())
    st.metric("Packing Fraction", f"{cl.packing_fraction():.3f}")
    h, k, l = st.columns(3)
    with h: mh = st.number_input("h", 0, 5, 1)
    with k: mk = st.number_input("k", 0, 5, 1)
    with l: ml = st.number_input("l", 0, 5, 0)
    if mh + mk + ml > 0:
        d = cl.interplanar_spacing(mh, mk, ml)
        st.metric(f"d({mh}{mk}{ml}) spacing", f"{d:.4f} nm")

with tab5:
    st.header("Digital Twin — Predictive Maintenance")
    from modules.predictive_maintenance import RULEstimator, AnomalyDetector
    col = st.columns(2)
    with col[0]:
        st.subheader("RUL Estimation")
        rul = RULEstimator(failure_threshold=10.0, window=5)
        for t in range(10):
            rul.add_observation(0.8 ** (9 - t) * 10, float(t))
        result = rul.estimate(method="exponential")
        st.metric("RUL", f"{result.rul:.1f} units")
        st.metric("Degradation Rate", f"{result.degradation_rate:.4f}")
    with col[1]:
        st.subheader("Anomaly Detection")
        np.random.seed(42)
        ad = AnomalyDetector(threshold=2.5, window=10)
        for i in range(30):
            v = 15.0 if i in (15, 22) else np.random.normal(5, 1)
            ad.add(v)
        st.metric("Anomalies Detected", ad.n_detected)
        st.metric("Anomaly Rate", f"{ad.anomaly_rate:.1%}")

with tab6:
    st.header("About Physics M³ Workspace")
    st.markdown("""
    **33 modules** | **8+ test suites** | **0 failures**

    - Materials: M³ analysis, composite models, mechanical tests
    - FEM: Static, dynamic, thermal, fluid
    - Topology Optimization: 2D SIMP, 3D SIMP, multi-objective, manufacturing
    - Crystallography: BCC, FCC, SC, HCP lattices
    - Digital Twin: Kalman filter, RUL, anomaly detection
    - VVV: Verification, validation, certification pipeline
    - CI/CD: GitHub Actions matrix build + PyPI publish
    """)
