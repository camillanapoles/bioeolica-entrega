#!/usr/bin/env python3
"""
SU2 cross-validation configuration for VAWT H-rotor Darrieus.

Validates OpenFOAM SRF results against SU2 sliding mesh for
selected operating points (TSR=2.0, 3.0 at V=6,8 m/s).

Uses SU2's incompressible Navier-Stokes solver with k-omega SST
turublence model. Rotor motion handled via mesh motion (sliding mesh).

Reference: NACA 0018, 3 blades, R=1.75m, c=0.12-0.35m
"""

# SU2 configuration (exported as .cfg for SU2 v8.x)
SU2_CFG_TEMPLATE = """
%--------------------------------------------------------------------------%
% SU2 configuration for VAWT H-rotor cross-validation
% NACA 0018, TSR={tsr}, V_inf={v_inf} m/s
%--------------------------------------------------------------------------%

% Solver
SOLVER= INC_RANS
KIND_TURB_MODEL= SST

% Compressibility
INC_DENSITY_INIT= 1.105
INC_VELOCITY_INIT= ({v_inf}, 0, 0)

% Mesh (sliding mesh: rotor + stator)
MESH_FILENAME= vawt_su2.su2
MESH_FORMAT= SU2

% Sliding mesh
MARKER_ZONE_INTERFACE= ( stator/rotor_interface, rotor/stator_interface )
MARKER_ZONE_INTERFACE_KIND= sliding_interface
MARKER_ZONE_INTERFACE_MOTION= ( rotating, rotor, (0, 0, 1), (0, 0, 0), {omega_rads} )

% Boundary conditions
MARKER_HEATFLUX= ( blade, 0.0 )
MARKER_FARFIELD= ( inlet, outlet, top, bottom )
MARKER_SYM= ( symmetry_xy, symmetry_xz )

% Reference values
REF_ORIGIN_MOMENT_X= 0.0
REF_ORIGIN_MOMENT_Y= 0.0
REF_ORIGIN_MOMENT_Z= 0.0
REF_LENGTH= 1.75
REF_AREA= 9.62

% Numerical methods
CONV_NUM_METHOD_FLOW= JST
CONV_NUM_METHOD_TURB= SCALAR_UPWIND
MUSCL_FLOW= YES
SLOPE_LIMITER_FLOW= VENKATAKRISHNAN

% Linear solver
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= LU_SGS
LINEAR_SOLVER_ERROR= 1E-6

% Time discretization (unsteady)
TIME_DOMAIN= YES
TIME_MARCHING= DUAL_TIME_STEPPING-2ND_ORDER
UNST_TIMESTEP= {dt}
MAX_TIME= {n_rev:d}
INNER_ITER= 10
TIME_ITER= {n_time_iter:d}

% Convergence
CONV_FIELD= RMS_DENSITY
CONV_STARTITER= 10
CONV_CAUCHY_ELEMS= 100
CONV_CAUCHY_EPS= 1E-6

% Output
SCREEN_OUTPUT= (INNER_ITER, WALL_TIME, RMS_DENSITY, RMS_ENERGY, LIFT, DRAG, MOMENT)
HISTORY_OUTPUT= (ITER, RMS_RES, LIFT, DRAG, MOMENT)
OUTPUT_FILES= (RESTART, PARAVIEW)
TABULAR_FORMAT= CSV
"""


def generate_su2_configs(output_dir="vawt_su2_case"):
    """Generate SU2 .cfg files for each operating point."""
    import os

    v_inf_values = [6.0, 8.0]
    tsr_values = [2.0, 3.0]
    R = 1.75  # rotor radius m

    os.makedirs(output_dir, exist_ok=True)

    for v_inf in v_inf_values:
        for tsr in tsr_values:
            omega = 2.0 * tsr * v_inf / R
            rpm = omega * 60 / (2 * 3.14159)
            dt = 1.0 / (omega * 360)  # 1 deg per timestep
            n_rev = 10  # 10 revolutions
            n_time_iter = int(360 * n_rev)

            cfg = SU2_CFG_TEMPLATE.format(
                tsr=tsr,
                v_inf=v_inf,
                omega_rads=omega,
                dt=dt,
                n_rev=n_rev,
                n_time_iter=n_time_iter,
            )

            filename = f"vawt_TSR{tsr:.1f}_V{v_inf:.0f}.cfg"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                f.write(cfg)

            print(f"  SU2 config: {filename} → TSR={tsr} V={v_inf}m/s omega={omega:.2f}rad/s RPM={rpm:.1f}")


if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_su2_configs(out)
    print(f"\nSU2 configs written to {out}/")
    print("Run: SU2 > SU2_CFD vawt_TSR3.0_V8.cfg 2>&1")
