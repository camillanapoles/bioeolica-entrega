#!/usr/bin/env python3
"""Generate computational figures for the PM-Graphite composite Savonius paper.

P$1 (ZERO HARDCODED): all physical/model constants are loaded from the project
SSOT (workspace/lab1-material-papel-mache-grafite/config/constants.json) — never
redeclared as literals here. Change a parameter by editing the JSON, not this file.
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "workspace" / "lab1-material-papel-mache-grafite" / "config" / "constants.json"
OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)


def _dig(obj, dotted):
    """Resolve a dotted SSOT path (e.g. 'modules.physics_m3.blade_design.Cp_max')."""
    cur = obj
    for part in dotted.split("."):
        cur = cur[part]
    return cur


with open(SSOT_PATH, encoding="utf-8") as _f:
    _SSOT = json.load(_f)

# ---- Constants from SSOT (Mandate P$1) ----
# Map: paper symbol -> SSOT dotted path in constants.json.
_SSOT_PATHS = {
    "rho_air":      "modules.blade_design.rho_air",
    "Cp_max":       "modules.blade_design.Cp_max",
    "lam_opt":      "modules.blade_design.lambda_opt",
    "sig_Cp":       "modules.blade_design.sigma_Cp",
    "D":            "modules.blade_design.rotor_D",
    "H":            "modules.blade_design.rotor_H",
    "K_e":          "modules.blade_design.Ke",
    "R_int":        "modules.blade_design.R_int",
    "P_loss_const": "modules.blade_design.P_loss_const",
    "E_m":          "modules.composite_model.E_matrix",
    "E_f":          "modules.composite_model.E_filler",
    "V_f":          "modules.composite_model.V_f",
    "xi":           "modules.composite_model.xi",
}
_g = {k: _dig(_SSOT, v) for k, v in _SSOT_PATHS.items()}
rho_air      = float(_g["rho_air"])
Cp_max       = float(_g["Cp_max"])
lam_opt      = float(_g["lam_opt"])
sig_Cp       = float(_g["sig_Cp"])
D            = float(_g["D"])
H            = float(_g["H"])
As = D * H
K_e          = float(_g["K_e"])
R_int        = float(_g["R_int"])
P_loss_const = float(_g["P_loss_const"])
E_m          = float(_g["E_m"])
E_f          = float(_g["E_f"])
V_f          = float(_g["V_f"])
xi           = float(_g["xi"])

# Monte-Carlo / aging simulation parameters (from SSOT sim.envelhecimento + paper config).
_AGING = _SSOT["sim"]["envelhecimento"]
np.random.seed(int(_AGING["seed"]))
_PAPER = _SSOT["paper"]  # P$1: figure-specific params (MC resolution, CVs, targets, LCA/cost figs)
n_mc = int(_PAPER["mc"]["n_amostras"])
CV_E = float(_PAPER["mc"]["CV_E"])
CV_Vf = float(_PAPER["mc"]["CV_Vf"])
E_target_GPa = float(_PAPER["targets"]["E_GPa"])
P_target_kW = float(_PAPER["targets"]["P_kw"])
v_design = float(_PAPER["targets"]["v_design"])
phi_critico = float(_PAPER["aging_fig"]["phi_critico"])

def halpin_tsai(Em, Ef, Vf, xi_val):
    # P$1: xi_val vem da SSOT (composite_model.xi) — sem default hardcoded.
    eta_val = ((Ef/Em) - 1) / ((Ef/Em) + xi_val)
    return Em * (1 + xi_val*eta_val*Vf) / (1 - eta_val*Vf)

# ========================
# FIGURE 1: Monte Carlo histogram
# ========================
Em_s = np.random.normal(E_m, CV_E*E_m, n_mc)
Ef_s = np.random.normal(E_f, CV_E*E_f, n_mc)
Vf_s = np.random.normal(V_f, CV_Vf*V_f, n_mc)
Ec_s = halpin_tsai(Em_s, Ef_s, Vf_s, xi)
Ec_mean = Ec_s.mean()
p_above_3 = (Ec_s > E_target_GPa*1e9).mean()

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(Ec_s/1e9, bins=60, density=True, alpha=0.75,
        color='steelblue', edgecolor='white', linewidth=0.5)
ax.axvline(E_target_GPa, color='crimson', ls='--', lw=2,
           label=f'$E={E_target_GPa:g}$ GPa (target)')
ax.axvline(Ec_mean/1e9, color='navy', ls='-', lw=2,
           label=f'Mean = {Ec_mean/1e9:.2f} GPa')
ax.set_xlabel("Young's modulus $E_c$ [GPa]", fontsize=12)
ax.set_ylabel("Probability density", fontsize=12)
ax.set_title(f"Monte Carlo ($n=10^4$): $p(E_c\\geq{E_target_GPa:g})$ = {p_above_3:.0%}", fontsize=11)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig1_mc_histogram.png", dpi=300)
print("fig1 ✓")
plt.close(fig)

# ========================
# FIGURE 2: Power curves
# ========================
def P_elec(v, lam_op=lam_opt):
    Cp_op = Cp_max * np.exp(-(lam_op-lam_opt)**2/(2*sig_Cp**2))
    P_mech = 0.5 * rho_air * As * v**3 * Cp_op
    tau = P_mech / (lam_op*v/(D/2)) if v>0 else 0
    omega = lam_op * v / (D/2)
    return max(0, tau*omega - R_int*(tau/K_e)**2 - P_loss_const)

vs = np.linspace(2, 14, 200)
Pw = 0.5*rho_air*As*vs**3
Pe = np.array([P_elec(v) for v in vs])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
lam = np.linspace(0.1, 2.0, 200)
Cp = Cp_max * np.exp(-(lam-lam_opt)**2/(2*sig_Cp**2))
ax1.plot(lam, Cp, 'b-', lw=2)
ax1.axvline(lam_opt, color='gray', ls=':', alpha=0.5)
ax1.axhline(Cp_max, color='gray', ls=':', alpha=0.5)
ax1.set_xlabel("Tip-speed ratio $\\lambda$", fontsize=11)
ax1.set_ylabel("$C_p$", fontsize=11)
ax1.set_title("Savonius aerodynamic model", fontsize=11)
ax1.grid(alpha=0.3)

ax2.plot(vs, Pw/1000, 'k-', lw=2, label='Wind power')
ax2.plot(vs, Pe/1000, 'b-', lw=2.5, label='Electrical output')
ax2.axhline(P_target_kW, color='crimson', ls='--', lw=1.5,
            label=f'{P_target_kW*1000:.0f} W target')
ax2.axvline(v_design, color='gray', ls=':', alpha=0.5)
ax2.set_xlabel("Wind speed [m/s]", fontsize=11)
ax2.set_ylabel("Power [kW]", fontsize=11)
ax2.legend(fontsize=9)
ax2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig2_power_curves.png", dpi=300)
print("fig2 ✓")
plt.close(fig)

# ========================
# FIGURE 3: Aging/lifetime
# ========================
n_aging = int(_AGING["n_amostras"])
sigma_ln_delta = float(_AGING["sigma_ruido"])
delta_0 = float(_AGING["taxa_base_degrad"])
deltas = np.random.lognormal(mean=np.log(delta_0), sigma=sigma_ln_delta, size=n_aging)
Nf = (1-phi_critico) / deltas

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(Nf/1e8, bins=50, density=True, alpha=0.75,
        color='forestgreen', edgecolor='white', linewidth=0.5)
ax.axvline(np.median(Nf)/1e8, color='darkgreen', lw=2.5, ls='--',
           label=f'Median: {np.median(Nf)/1e8:.1f}$\\times$10⁸')
ax.set_xlabel("Lifetime $N_f$ [$\\times 10^8$ cycles]", fontsize=12)
ax.set_ylabel("Probability density", fontsize=12)
ax.set_title("Aging simulation ($n=10^3$): "
             f"P5={np.percentile(Nf,5)/1e8:.1f}  P95={np.percentile(Nf,95)/1e8:.1f}",
             fontsize=11)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig3_aging_lifetime.png", dpi=300)
print("fig3 ✓")
plt.close(fig)

# ========================
# FIGURE 4: LCA comparison
# ========================
stages = _PAPER["lca_fig"]["stages"]
comp = np.array(_PAPER["lca_fig"]["pm15g"], dtype=float)
fg   = np.array(_PAPER["lca_fig"]["fiberglass"], dtype=float)
x = np.arange(len(stages))
width = 0.35

fig, ax = plt.subplots(figsize=(7, 4))
b1 = ax.bar(x-width/2, comp, width, label='PM-15G', color='steelblue', edgecolor='white')
b2 = ax.bar(x+width/2, fg, width, label='E-glass', color='crimson', edgecolor='white')
for b in b1:
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5, f'{b.get_height():.1f}',
            ha='center', va='bottom', fontsize=8)
for b in b2:
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5, f'{b.get_height():.1f}',
            ha='center', va='bottom', fontsize=8)
ax.set_ylabel("kg CO$_2$e per blade", fontsize=11)
ax.set_title(f"LCA: {sum(comp):.1f} vs {sum(fg):.1f} kg CO$_2$e "
             f"({100*(1-sum(comp)/sum(fg)):.1f}% reduction)", fontsize=10)
ax.set_xticks(x)
ax.set_xticklabels(stages, fontsize=9)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig4_lca_comparison.png", dpi=300)
print("fig4 ✓")
plt.close(fig)

# ========================
# FIGURE 5: Cost breakdown
# ========================
cost_labels = _PAPER["cost_fig"]["labels"]
cost_values = _PAPER["cost_fig"]["values"]
colors_pie = ['#2ecc71', '#3498db', '#95a5a6', '#f39c12']

fig, ax = plt.subplots(figsize=(5, 4))
wedges, texts, autotexts = ax.pie(
    cost_values, labels=cost_labels, autopct='%1.1f%%',
    colors=colors_pie, startangle=90, pctdistance=0.75,
    wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
for t in autotexts: t.set_fontsize(9)
ax.set_title(f"PM-15G cost: R$ {sum(cost_values):.2f}/kg", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig5_cost_breakdown.png", dpi=300)
print("fig5 ✓")
plt.close(fig)

# ========================
# FIGURE 6: Sensitivity tornado
# ========================
# P$1: cada parâmetro perturbado em ±20% (mantendo os outros) — xi fixo da SSOT.
base = halpin_tsai(E_m, E_f, V_f, xi) / 1e9
sens = {}
for label, sel in [('$E_m$ (matrix)', 'Em'), ('$E_f$ (filler)', 'Ef'), ('$V_f$ (vol.frac.)', 'Vf')]:
    def _perturbed(factor, sel=sel):
        e_m = E_m * factor if sel == 'Em' else E_m
        e_f = E_f * factor if sel == 'Ef' else E_f
        v_f = V_f * factor if sel == 'Vf' else V_f
        return halpin_tsai(e_m, e_f, v_f, xi) / 1e9
    sens[label] = (_perturbed(0.8) - base, _perturbed(1.2) - base)

fig, ax = plt.subplots(figsize=(7, 3))
y_pos = range(len(sens))
for i, (label, (lo, hi)) in enumerate(sens.items()):
    ax.barh(i, hi-lo, left=base+lo, height=0.5, color='steelblue', edgecolor='white')
    ax.text(base+lo-0.1, i, f'{base+lo:.2f}', ha='right', va='center', fontsize=8, color='white')
    ax.text(base+hi+0.1, i, f'{base+hi:.2f}', ha='left', va='center', fontsize=8)
ax.axvline(base, color='crimson', ls='--', lw=1.5, label=f'Base: {base:.2f} GPa')
ax.set_yticks(list(y_pos))
ax.set_yticklabels(sens.keys(), fontsize=10)
ax.set_xlabel("$E_c$ [GPa]", fontsize=11)
ax.set_title("Sensitivity: ±20% input variation", fontsize=11)
ax.legend(fontsize=9)
ax.grid(axis='x', alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "fig6_sensitivity.png", dpi=300)
print("fig6 ✓")
plt.close(fig)

print(f"\nDone — {len(list(OUT.glob('*.png')))} figures in {OUT}")
