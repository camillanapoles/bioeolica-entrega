"""Physics M³ CAD/CAE Platform — Streamlit UI."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

st.set_page_config(page_title="Physics M³ CAD/CAE", layout="wide")
st.title("Physics M³ — CAD/CAE Platform")
st.caption("Design → Mesh → FEM → Results pipeline")

tabs = st.tabs(["Design", "Mesh", "FEM", "Results", "About"])

with tabs[0]:
    st.header("Parametric Design")
    col = st.columns(3)
    with col[0]: length = st.number_input("Length (mm)", 10, 500, 100)
    with col[1]: width = st.number_input("Width (mm)", 5, 200, 20)
    with col[2]: height = st.number_input("Height (mm)", 5, 200, 20)
    if st.button("Generate Model"):
        from modules.cad_bridge import CadModel
        m = CadModel().box(length, width, height)
        st.metric("Volume", f"{m.volume:.0f} mm³")
        st.metric("Mass", f"{m.mass*1000:.1f} g")
        bb = m.bounding_box()
        st.json(bb)

with tabs[1]:
    st.header("Mesh Generation")
    size = st.slider("Element Size", 0.5, 10.0, 3.0)
    if st.button("Generate Mesh"):
        from modules.gmsh_mesher import create_beam_mesh
        mg = create_beam_mesh(length, width, height, mesh_size=size)
        stats = mg.get_mesh_stats()
        st.metric("Nodes", stats["n_nodes"])
        st.metric("Elements", stats["n_volume_elements"])

with tabs[2]:
    st.header("FEM Solver")
    E = st.number_input("Young's Modulus (GPa)", 1, 500, 210)
    nu = st.slider("Poisson's Ratio", 0.1, 0.49, 0.3)
    fx = st.number_input("Force X (N)", -1000, 1000, 0)
    fy = st.number_input("Force Y (N)", -1000, 1000, 0)
    fz = st.number_input("Force Z (N)", -1000, 1000, -100)
    if st.button("Solve"):
        from modules.gmsh_mesher import create_beam_mesh
        from modules.calculix_solver import FEMSolver
        mg = create_beam_mesh(length, width, height, mesh_size=size)
        msh = "/tmp/cae_mesh.msh"
        mg.export_msh(msh)
        fem = FEMSolver()
        fem.load_msh(msh)
        fem.set_material("STEEL", E=E*1e3, nu=nu)
        fem.add_force(list(range(fem.n_nodes-5, fem.n_nodes+1)), fx=fx, fy=fy, fz=fz)
        result = fem.solve_static(jobname="cae_solve")
        st.metric("Solver Status", "OK" if result["success"] else "FAIL")

with tabs[3]:
    st.header("Results")
    st.info("Run a simulation in the FEM tab first.")

with tabs[4]:
    st.header("About")
    st.markdown("""
    **Physics M³ CAD/CAE Platform** — Cycles C1-C3

    - C1: CadQuery parametric modeling
    - C2: Gmsh tetrahedral meshing
    - C3: CalculiX FEM solver
    """)
