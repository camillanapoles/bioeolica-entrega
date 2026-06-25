#!/usr/bin/env python3
"""
Kinematic Machine Design — Mecanismos, Juntas, Análise Cinemática.

Para design de máquinas mecânicas com:
  - Mecanismos 4 barras (posição, velocidade, aceleração)
  - Juntas: rotacional, prismática, fixa, universal
  - Cadeia cinemática: graus de liberdade, mobilidade (critério de Gruebler)
  - Análise de posição via Newton-Raphson
  - Renderização 3D do mecanismo em movimento
  - Simulação de condições reais de trabalho (carga, velocidade, torque)

Uso:
    from kinematic_machine import (
        Mechanism4Bar, Joint, Link, KinematicChain,
        render_mechanism_3d, animate_mechanism
    )
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation


# ═══════════════════════════════════════════════════════════════
#  POINTS & VECTORS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Ponto3D:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def distance(self, other: 'Ponto3D') -> float:
        return float(np.linalg.norm(self.to_array() - other.to_array()))


# ═══════════════════════════════════════════════════════════════
#  JOINTS & LINKS
# ═══════════════════════════════════════════════════════════════

class JointType:
    ROTATIONAL = "rotational"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    UNIVERSAL = "universal"
    SPHERICAL = "spherical"


@dataclass
class Joint:
    """Kinematic joint connecting two links."""
    name: str
    joint_type: str = JointType.ROTATIONAL
    position: Ponto3D = field(default_factory=Ponto3D)
    axis: np.ndarray = field(default_factory=lambda: np.array([0, 0, 1]))
    angle_deg: float = 0.0  # Current angle (rotational)
    displacement_m: float = 0.0  # Current displacement (prismatic)
    torque_Nm: float = 0.0
    dof: int = 1  # Degrees of freedom removed

    def transform(self) -> np.ndarray:
        """Transformation matrix for this joint."""
        theta = np.radians(self.angle_deg)
        c, s = np.cos(theta), np.sin(theta)
        return np.array([
            [c, -s, 0, self.position.x],
            [s, c, 0, self.position.y],
            [0, 0, 1, self.position.z],
            [0, 0, 0, 1],
        ])


@dataclass
class Link:
    """Rigid link connecting two joints."""
    name: str
    length_m: float = 0.0
    mass_kg: float = 0.0
    joint_i: str = ""  # Starting joint
    joint_j: str = ""  # Ending joint
    color: str = "blue"

    def moment_of_inertia(self) -> float:
        """Moment of inertia about center (thin rod)."""
        if self.mass_kg <= 0 or self.length_m <= 0:
            return 0
        return self.mass_kg * self.length_m**2 / 12


# ═══════════════════════════════════════════════════════════════
#  MECHANISM 4-BAR LINKAGE
# ═══════════════════════════════════════════════════════════════

class Mechanism4Bar:
    """Four-bar linkage kinematic analysis.

    Ground (link 0) → Crank (link 1) → Coupler (link 2) → Rocker (link 3) → Ground
    """

    def __init__(self, L1: float = 1.0, L2: float = 3.0,
                 L3: float = 2.0, L4: float = 2.5):
        self.L = [0, L1, L2, L3, L4]  # L0=ground, L1=crank, L2=coupler, L3=rocker, L4=ground
        self.theta = [0.0, 0.0, 0.0, 0.0]  # Angles of links 1-3 relative to ground
        self.omega = [0.0, 0.0, 0.0]  # Angular velocities
        self.alpha = [0.0, 0.0, 0.0]  # Angular accelerations

    def grashof(self) -> Dict:
        """Grashof criterion for 4-bar mechanism."""
        l = sorted([self.L[1], self.L[2], self.L[3], self.L[4]])
        s, l_max = l[0], l[-1]
        pq = l[1] + l[2]
        grashof = (s + l_max) < pq
        return {
            "shortest": s, "longest": l_max,
            "sum_shortest_longest": s + l_max,
            "sum_other_two": pq,
            "is_grashof": grashof,
            "type": "crank-rocker" if grashof else "double-rocker",
        }

    def solve_position(self, theta2_deg: float, tol: float = 1e-6,
                       max_iter: int = 100) -> Dict:
        """Solve position of 4-bar using Newton-Raphson with multi-start."""
        L1, L2, L3, L4 = self.L[1], self.L[2], self.L[3], self.L[4]
        theta2 = np.radians(theta2_deg)

        initial_guesses = [
            np.array([np.pi/2, np.pi/2]), np.array([np.pi/4, np.pi/4]),
            np.array([np.pi, np.pi/2]), np.array([0.5, 0.5]),
        ]

        for x0 in initial_guesses:
            x = x0.copy()
            converged = False
            try:
                for _ in range(max_iter):
                    t3, t4 = x[0], x[1]
                    f = np.array([
                        L2*np.cos(theta2) + L3*np.cos(t3) - L4*np.cos(t4) - L1,
                        L2*np.sin(theta2) + L3*np.sin(t3) - L4*np.sin(t4),
                    ])
                    if np.linalg.norm(f) < tol:
                        converged = True
                        break
                    J = np.array([
                        [-L3*np.sin(t3), L4*np.sin(t4)],
                        [L3*np.cos(t3), -L4*np.cos(t4)],
                    ])
                    x = x - np.linalg.solve(J, f)
                if converged:
                    break
            except np.linalg.LinAlgError:
                continue

        if not converged:
            return {"theta2_deg": round(np.degrees(theta2), 2),
                    "theta3_deg": 0.0, "theta4_deg": 0.0, "error": "no_convergence"}

        t3, t4 = x[0], x[1]
        self.theta = [0, theta2, t3, t4]
        return {
            "theta2_deg": round(np.degrees(theta2), 2),
            "theta3_deg": round(np.degrees(t3) % 360, 2),
            "theta4_deg": round(np.degrees(t4) % 360, 2),
        }

    def solve_velocity(self, omega2: float = 1.0) -> Dict:
        """Solve angular velocities given crank input omega2 (rad/s)."""
        L2, L3, L4 = self.L[2], self.L[3], self.L[4]
        t2, t3, t4 = self.theta[1], self.theta[2], self.theta[3]
        A = np.array([
            [-L3 * np.sin(t3), L4 * np.sin(t4)],
            [L3 * np.cos(t3), -L4 * np.cos(t4)],
        ])
        B = np.array([L2 * np.sin(t2), -L2 * np.cos(t2)]) * omega2
        omegas = np.linalg.solve(A, B)
        self.omega = [0, omega2, omegas[0], omegas[1]]
        return {
            "omega2_rads": round(omega2, 3),
            "omega3_rads": round(float(omegas[0]), 3),
            "omega4_rads": round(float(omegas[1]), 3),
        }

    def joint_positions(self) -> Dict[str, np.ndarray]:
        """Calculate joint positions for current angles."""
        L1, L2, L3, L4 = self.L[1], self.L[2], self.L[3], self.L[4]
        t2, t3, t4 = self.theta[1], self.theta[2], self.theta[3]
        O = np.array([0.0, 0.0])
        A = np.array([L1, 0.0])
        B = np.array([L1 + L4 * np.cos(t4), L4 * np.sin(t4)])
        C = np.array([L2 * np.cos(t2), L2 * np.sin(t2)])
        return {"O": O, "A": A, "B": B, "C": C}

    def coupler_curve(self, n_points: int = 72) -> Tuple[np.ndarray, np.ndarray]:
        """Generate coupler point curve over full crank rotation."""
        x_pts, y_pts = [], []
        for i in range(n_points):
            theta2 = 360 * i / n_points
            try:
                self.solve_position(theta2)
                joints = self.joint_positions()
                # Midpoint of coupler (between C and B)
                x_pts.append((joints["C"][0] + joints["B"][0]) / 2)
                y_pts.append((joints["C"][1] + joints["B"][1]) / 2)
            except (np.linalg.LinAlgError, ValueError):
                continue
        return np.array(x_pts), np.array(y_pts)


# ═══════════════════════════════════════════════════════════════
#  KINEMATIC CHAIN — General
# ═══════════════════════════════════════════════════════════════

@dataclass
class KinematicChain:
    """General kinematic chain with arbitrary joints and links."""
    joints: Dict[str, Joint] = field(default_factory=dict)
    links: Dict[str, Link] = field(default_factory=dict)

    def add_joint(self, joint: Joint):
        self.joints[joint.name] = joint

    def add_link(self, link: Link):
        self.links[link.name] = link

    def dof(self) -> int:
        """Gruebler's criterion: DOF = 3(n-1) - 2j1 - j2."""
        n = len(self.links) + 1  # +1 for ground
        j1 = sum(1 for j in self.joints.values() if j.dof == 1)
        j2 = sum(1 for j in self.joints.values() if j.dof == 2)
        dof = 3 * (n - 1) - 2 * j1 - j2
        return max(0, dof)


# ═══════════════════════════════════════════════════════════════
#  3D RENDERER
# ═══════════════════════════════════════════════════════════════

def render_mechanism_3d(mech: Mechanism4Bar, title: str = "Mecanismo 4 Barras",
                        show_coupler: bool = True) -> plt.Figure:
    """Render 4-bar mechanism in 3D."""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    joints = mech.joint_positions()

    # Links
    ax.plot([0, joints["A"][0]], [0, joints["A"][1]], [0, 0], 'k-', linewidth=3, label="Ground")
    ax.plot([0, joints["C"][0]], [0, joints["C"][1]], [0, 0], 'b-', linewidth=3, label="Crank")
    ax.plot([joints["C"][0], joints["B"][0]], [joints["C"][1], joints["B"][1]], [0, 0],
            'r-', linewidth=3, label="Coupler")
    ax.plot([joints["A"][0], joints["B"][0]], [joints["A"][1], joints["B"][1]], [0, 0],
            'g-', linewidth=3, label="Rocker")

    # Joints
    for name, pos in joints.items():
        ax.scatter(*pos, 0, s=100, c='k', marker='o')
        ax.text(pos[0], pos[1], 0.1, name, fontsize=12)

    # Coupler curve
    if show_coupler:
        try:
            cx, cy = mech.coupler_curve()
            ax.plot(cx, cy, [0]*len(cx), 'm--', alpha=0.5, linewidth=1, label="Curva do Acoplador")
        except Exception:
            pass

    ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
    ax.set_title(title); ax.legend()
    return fig


def animate_mechanism(mech: Mechanism4Bar, n_frames: int = 72) -> plt.Figure:
    """Animate 4-bar mechanism over one crank rotation.

    Returns figure. In Jupyter, use %matplotlib notebook to see animation.
    """
    from matplotlib.animation import FuncAnimation
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111)

    def update(frame):
        ax.clear()
        theta2 = 360 * frame / n_frames
        try:
            mech.solve_position(theta2)
        except Exception:
            return
        joints = mech.joint_positions()

        ax.plot([0, joints["A"][0]], [0, joints["A"][1]], 'k-', linewidth=3)
        ax.plot([0, joints["C"][0]], [0, joints["C"][1]], 'b-', linewidth=3)
        ax.plot([joints["C"][0], joints["B"][0]], [joints["C"][1], joints["B"][1]], 'r-', linewidth=3)
        ax.plot([joints["A"][0], joints["B"][0]], [joints["A"][1], joints["B"][1]], 'g-', linewidth=3)
        for name, pos in joints.items():
            ax.scatter(*pos, s=80, c='k', marker='o')
            ax.text(pos[0], pos[1] + 0.1, name, fontsize=10)
        ax.set_xlim(-4, 4); ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.set_title(f"Crank angle: {theta2:.0f}°")
        ax.grid(True)

    return FuncAnimation(fig, update, frames=n_frames, interval=50)
