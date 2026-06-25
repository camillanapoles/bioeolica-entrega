#!/usr/bin/env python3
"""Tests for kinematic_machine.py — Machine Design & 3D Rendering."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))
import numpy as np
from kinematic_machine import Mechanism4Bar, KinematicChain, Joint, Link, JointType, Ponto3D


def test_mechanism_create():
    m = Mechanism4Bar(L1=1, L2=3, L3=2, L4=2.5)
    assert len(m.L) == 5


def test_grashof():
    m = Mechanism4Bar(L1=1, L2=3, L3=2, L4=2.5)
    g = m.grashof()
    assert "is_grashof" in g


def test_solve_position():
    m = Mechanism4Bar()
    r = m.solve_position(45)
    assert abs(r["theta2_deg"] - 45) < 1
    assert 0 < r["theta3_deg"] < 360
    assert 0 < r["theta4_deg"] < 360


def test_solve_velocity():
    m = Mechanism4Bar()
    m.solve_position(45)
    r = m.solve_velocity(omega2=2.0)
    assert abs(r["omega2_rads"] - 2.0) < 0.01


def test_joint_positions():
    m = Mechanism4Bar()
    m.solve_position(30)
    j = m.joint_positions()
    for name in ["O", "A", "B", "C"]:
        assert name in j
        assert len(j[name]) == 2


def test_coupler_curve():
    m = Mechanism4Bar()
    x, y = m.coupler_curve(n_points=36)
    assert len(x) > 0
    assert len(y) > 0


def test_kinematic_chain():
    chain = KinematicChain()
    chain.add_joint(Joint("J1", joint_type=JointType.ROTATIONAL))
    assert "J1" in chain.joints


def test_chain_dof():
    chain = KinematicChain()
    chain.add_joint(Joint("J1", dof=1))
    chain.add_joint(Joint("J2", dof=1))
    chain.add_link(Link("L1", length_m=1.0))
    assert chain.dof() >= 0
