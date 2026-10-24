"""Scratch: build the ENLARGED reaction tower for the measured 57 x 80 cell.

Not a source change. Monkeypatches stand_params BEFORE importing reaction_tower
so reaction_tower's module-level derived constants recompute, then re-runs the
same gen_step() body against the new numbers.

Two candidate bores:
  A  bore 57.6  cell straight into the cup, liner deleted   (57.0 + 0.6 clear)
  B  bore 62.0  liner retained at min 2.0 mm wall
     57.0 + LC_LINER_CLEAR 0.3 + 2*2.0 wall + LC_LINER_FIT 0.3 = 61.6 -> 62.0
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, SRC)

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    Rot,
    extrude,
    mirror,
)

import stand_params as P
from stand_common import OVER, flange_ear, rail_channel, saddle, side_slot_bolt, vbolt


def build_tower(bore, cup_wall, cup_depth, floor_t, stud_bore, stud_depth,
                wedge_deg, side_bolt_xs, cap_over_bore=6.0, roof_top=28.0,
                ear_t=10.0):
    """Rebuild reaction_tower.gen_step() with explicit enlarged parameters."""
    AXIS_Z = P.AXIS_Z
    CUP_OD = bore + 2 * cup_wall
    PLATE_T = P.plate_t_for_width(CUP_OD)
    HALF_W = CUP_OD / 2
    BORE_R = bore / 2
    BORE_END = cup_depth
    FLOOR_X1 = BORE_END + floor_t
    FLOOR_TOP = AXIS_Z + BORE_R + cap_over_bore
    rise = FLOOR_TOP - roof_top
    WEDGE_RUN = rise / math.tan(math.radians(wedge_deg))
    SADDLE_LEN = FLOOR_X1 + WEDGE_RUN

    EAR_Y_IN = HALF_W
    EAR_Y_OUT = HALF_W + 9.0
    EAR_X0, EAR_LEN, GUSSET_T = 8.0, 29.0, 6.0
    EAR_BOLT_X = EAR_X0 + EAR_LEN / 2
    EAR_BOLT_Y = (EAR_Y_IN + EAR_Y_OUT) / 2
    CABLE_W, CABLE_D = 12.0, 6.0

    part = saddle(length=SADDLE_LEN, plate_t=PLATE_T, roof_top=roof_top,
                  side_bolt_xs=side_bolt_xs)
    part += Pos(0, 0, roof_top) * Box(BORE_END, CUP_OD, AXIS_Z - roof_top,
                                     align=(Align.MIN, Align.CENTER, Align.MIN))
    part += Pos(BORE_END, 0, roof_top) * Box(floor_t, CUP_OD, FLOOR_TOP - roof_top,
                                            align=(Align.MIN, Align.CENTER, Align.MIN))
    wedge = [(FLOOR_X1, roof_top), (SADDLE_LEN, roof_top), (FLOOR_X1, FLOOR_TOP)]
    part += extrude(Plane.XZ * Polygon(*wedge, align=None), amount=HALF_W, both=True)
    part += flange_ear(EAR_X0, EAR_LEN, EAR_Y_IN, EAR_Y_OUT, AXIS_Z, ear_t)

    z_low = AXIS_Z - ear_t
    z_toe = z_low - (EAR_Y_OUT - EAR_Y_IN)
    gp = [(EAR_Y_IN, z_toe), (EAR_Y_OUT, z_low), (EAR_Y_IN, z_low)]
    one = extrude(Plane.YZ * Polygon(*gp, align=None), amount=GUSSET_T)
    pair = Pos(EAR_X0, 0, 0) * one + Pos(EAR_X0 + EAR_LEN - GUSSET_T, 0, 0) * one
    part += pair + mirror(pair, about=Plane.XZ)

    part -= Pos(-OVER, 0, AXIS_Z) * Rot(0, 90, 0) * Cylinder(
        BORE_R, BORE_END + OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part -= Pos(BORE_END, 0, AXIS_Z) * Rot(0, 90, 0) * Cylinder(
        stud_bore / 2, stud_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part -= Pos(-OVER, 0, AXIS_Z - BORE_R) * Box(
        BORE_END + OVER, CABLE_W, CABLE_D, align=(Align.MIN, Align.CENTER, Align.MAX))
    for y in (EAR_BOLT_Y, -EAR_BOLT_Y):
        part -= vbolt(EAR_BOLT_X, y, AXIS_Z - ear_t, AXIS_Z, P.M5_CLEAR)

    part.label = "reaction_tower_enlarged"
    facts = dict(bore=bore, CUP_OD=CUP_OD, PLATE_T=PLATE_T, HALF_W=HALF_W,
                 BORE_R=BORE_R, BORE_END=BORE_END, floor_t=floor_t,
                 FLOOR_X1=FLOOR_X1, FLOOR_TOP=FLOOR_TOP, WEDGE_RUN=WEDGE_RUN,
                 SADDLE_LEN=SADDLE_LEN, stud_bore=stud_bore,
                 side_bolt_xs=side_bolt_xs, roof_top=roof_top)
    return part, facts


def bed_area(part):
    """First-layer footprint: area of faces lying in the z = 0 plane."""
    zmin = part.bounding_box().min.Z
    tot = 0.0
    for f in part.faces().filter_by(Plane.XY):
        c = f.center()
        if abs(c.Z - zmin) < 1e-6:
            tot += f.area
    return tot


def butt_joint(tower, foot, saddle_len, eps=0.5):
    """Bearing area and centroid of the tower/foot butt joint, by intersection."""
    overlap = tower & (Pos(saddle_len - eps, 0, 0) * foot)
    if overlap is None:
        return 0.0, None
    if isinstance(overlap, (list, tuple)) or hasattr(overlap, "__iter__"):
        solids = list(overlap)
        vol = sum(s.volume for s in solids)
        if vol < 1e-9:
            return 0.0, None
        cz = sum(s.volume * s.center().Z for s in solids) / vol
        cy = sum(s.volume * s.center().Y for s in solids) / vol
        from build123d import Vector
        return vol / eps, Vector(0, cy, cz)
    if overlap.volume < 1e-9:
        return 0.0, None
    return overlap.volume / eps, overlap.center()
