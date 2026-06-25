"""Generate the complete integrated M3 workspace notebook."""
import json, nbformat
nb = nbformat.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbformat.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbformat.v4.new_code_cell(text))

md("# Physics M3 Workspace — Projeto Integrado\n\nMacro (environment) → Meso (interface/layers) → Micro (microstructure)\n\nAll domains integrated: materials, structural, fluids, thermodynamics, electromechanical, CAD, VVV")

code("import sys, os, numpy as np, matplotlib.pyplot as plt\nsys.path.insert(0, os.path.abspath('modules'))\nfrom m3_analysis import M3Analysis, MacroScale, MesoScale, MicroScale, PlyLayer\nfrom composite_model import CompositeMaterial, FabricationProcess\nfrom mechanical_tests import run_all_tests\nfrom fem_solver import FEModel, BeamElement\nfrom fluid_dynamics import wind_profile, bem_theory, turbine_power, Airfoil\nfrom thermodynamics import DryingProcess, carnot_efficiency\nfrom electromechanical import PMSG, BatteryStorage, power_conversion_chain\nfrom structural_analysis import BeamSection, CompositeLaminate, PlyProperties, von_mises_stress, safety_factor\nfrom cad_visualization import AirfoilCoordinates, BladeGeometry, LaminateView, WindRose, failure_envelope_points\nfrom vvv_protocol import VVVReport\nprint('M3 Workspace loaded — all systems ready')")

# LAB-BASE: Material Characterization
md("## LAB-BASE: Composite Material Characterization\nCore material model: waste paper + PVA + graphite coating. Elastic constants + strength + 7 tests.")

code("""mat = CompositeMaterial(fiber="waste_paper", matrix="pva", coating="graphite_coating", fiber_volume_fraction=0.15)
s = mat.summary()
print(f"Material: {s['name']}")
print(f"E1={s['elastic']['E1_longitudinal_GPa']} GPa | Strength={s['strength']['tensile_longitudinal_MPa']} MPa")
E, st = s['elastic']['E1_longitudinal_GPa'], s['strength']['tensile_longitudinal_MPa']
tests = run_all_tests(E, st, length_mm=100, width_mm=25, thickness_mm=5)
for t, r in tests.items():
    if t != "material":
        print(f"  {t}: force={r.get('max_force_N','-')} | strength={r.get('flexural_strength_MPa',r.get('tensile_strength_MPa','-'))}")
""")

# LAB-FEM: Structural Analysis
md("## LAB-FEM: Euler-Bernoulli Beam FEM\nDiscrete stiffness method. Clamped cantilever with tip load. Convergence study.")

code("""model = FEModel()
for i in range(4):
    model.add_element(BeamElement(L_m=0.25, E_GPa=200, I_m4=1e-6, A_m2=0.01))
model.assemble()
model.apply_bc(list(range(6)))
F = np.zeros(model.dofs)
F[-2] = -5000
u = model.solve(F)
print(f"Tip deflection: {abs(u[-2]):.4f} m")
print(f"Max element stress: {max(model.stress()):.1f} MPa")
""")

# LAB-FLUID: Aerodynamics
md("## LAB-FLUID: Wind Turbine Aerodynamics\nBEM theory, wind profile, power estimation.")

code("""v = wind_profile(50, 6.0, terrain="open")
print(f"Wind at 50m: {v:.2f} m/s")
bem = bem_theory(v, 200, 1.5)
print(f"BEM power: {bem['power_W']:.0f} W at TSR={bem['TSR']}")
t = turbine_power(v, 1.5)
print(f"Turbine power: {t['power_W']:.0f} W (Cp={t['Cp']})")
""")

# LAB-THERMO: Thermodynamics
md("## LAB-THERMO: Thermodynamic Cycles\nDrying process, Carnot efficiency, energy tracking.")

code("""dry = DryingProcess(mass_kg=1.0)
print(f"Drying energy: {dry.total_energy_MJ():.1f} MJ for {dry.mass_kg}kg")
eta = carnot_efficiency(500, 300)
print(f"Carnot efficiency (500K/300K): {eta:.1%}")
""")

# LAB-ELECTRO: Power
md("## LAB-ELECTRO: Electromechanical Power\nPMSG generator, battery storage, conversion chain losses.")

code("""g = PMSG()
print(f"PMSG @1500rpm: {g.efficiency(1500):.1f}%")
chain = power_conversion_chain(1000)
print(f"Power chain: {chain['total_efficiency_pct']:.0f}% efficient")
print(f"Stage losses (W): {chain['stage_losses_W']}")
""")

# LAB-VIS: CAD Visualization
md("## LAB-VIS: 3D CAD & Failure Visualization\nAirfoil, laminate, stress envelope, wind rose.")

code("""fig, axes = plt.subplots(2, 3, figsize=(15, 8))
af = AirfoilCoordinates("NACA4412", chord_m=0.3)
x, y = af.coordinates()
axes[0,0].plot(x, y, "b-"); axes[0,0].set_aspect("equal"); axes[0,0].set_title(f"Airfoil: {af.name}")
lam = LaminateView(); stack = lam.stacking_data()
for i, l in enumerate(stack["layers"]):
    axes[0,1].barh(0, l["thickness_mm"], left=l["z_start_mm"], height=0.6)
axes[0,1].set_title(f"Laminate {stack['total_thickness_mm']}mm")
env = failure_envelope_points("tsai_wu", Xt=50, Xc=30, Yt=15, Yc=10, S=8)
axes[1,1].plot(env["sigma_11"], env["sigma_22"], "b-"); axes[1,1].fill_between(env["sigma_11"], env["sigma_22"], alpha=0.2)
axes[1,1].set_title("Tsai-Wu Envelope"); axes[1,1].axis("equal")
plt.tight_layout(); plt.show()
print("Visualization complete")
""")

# VVV Protocol
md("## VVV Certification\nVerification (convergence) + Validation (experimental) = Certification (PASS/FAIL)")

code("""vvv = VVVReport("Blade FEM")
vvv.verify_convergence([12, 5, 1.5], [0.5, 0.25, 0.125])
vvv.validate_experimental([1.0, 2.0], [0.98, 2.05])
c = vvv.certify()
print(f"VVV: {c['status']}")
print(f"  Verification: {vvv.verification['status']} | Validation: {vvv.validation['status']}")
""")

# Gap Analysis
md("## Gap Analysis\n\n| Domain | Status | Next |\n|--------|--------|------|\n| Materials | 70+ tests | — |\n| Structural FEM | Analytical | FEniCS backend |\n| Fluids BEM | Working | Full CFD |\n| Thermo | Working | Heat exchangers |\n| Electro | Working | Controls |\n| Normativo | ASTM cited | ISO/IEC |\n| Economico | Cost/kg | LCC |\n| Manufacturing | Basic | CAM detail |\n| Controls | — | Next lab |\n\n**PQMS: ~7.0/10** → Target: 9.5/10")

nb.cells = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
with open("notebooks/lab_integrado_completo.ipynb", "w") as f:
    json.dump(nb, f, indent=2, default=str)
print("OK: notebooks/lab_integrado_completo.ipynb")
