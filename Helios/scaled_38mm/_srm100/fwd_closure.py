"""Forward closure: 6061-T651 plug, radially bolted, solid (no pocket, no port).

Frame: z = 0 on the flange's bearing face = the case's FORWARD end face.  The plug
runs toward -Z (into the case, PLUG_L deep), the flange toward +Z.  The assembly
places it at motor z = CASE_L with no rotation, so its bolt holes sit at the same
azimuths as the case's.

Half-section, inboard face to forward face:
  * inboard face, 30 deg x 1.0 nose chamfer so the plug finds the bore
  * seal land 91.94 0/-0.02 with two AS568-237 piston grooves, 86.33 0/-0.04 dia,
    4.80 +0.08/0 wide, R0.4 bottom corners (Parker Chart 4-2).  Groove bottoms
    Ra 0.8, walls Ra 1.6.
  * R0.5 under the flange, clear of the case's 20 deg bore lead-in
  * flange 100 OD x 6: butts the case end, locates the plug axially on assembly.
    The pressure load goes through the eighteen bolts, never through the flange.
  * solid, 44 mm from the inboard face to the forward face: no lightening pocket
    and no port (a simply supported plate needs 12.4 at MEOP, FoS 2).  The forward
    face is one flat surface to the axis, the thrust face for a horizontal
    static-test load cell, broken only by the two puller holes at r 37.5.  The
    motor is fired without a chamber transducer, and the proof fills and bleeds
    through the proof dummy at the aft end.
  * 18 x M6 radial tapped holes on the bolt row (drawn at the 5.0 tap drill),
    bolt 0 keyed 0.8 deg off the even pattern; engagement 12 mm = 2 d in aluminium
  * groove top edges R0.1 (0.08 - 0.13)
  * 2 x M6 axial puller holes in the forward face, 10 deep, between bolts: take the
    radial screws out, then draw the plug out on two screws through a bridge,
    against the O-ring drag
"""

import math

import srm_params as P
from srm_build import arc, axial_drill, finish, one_solid, radial_drill, revolve_rz

R_LAND = P.PLUG_OD / 2.0
R_GROOVE = P.ORING_GROOVE_D / 2.0
R_FL = P.FLANGE_OD / 2.0
Z_IN = -P.PLUG_L
Z_TOP = P.FLANGE_T
NOSE_Z = P.PLUG_NOSE_CHAMFER / math.tan(math.radians(30.0))
GR = P.GROOVE_R_BOTTOM
BRK = 0.5          # 45 deg edge breaks
UNDER = 0.5        # radius under the flange
ET = P.GROOVE_EDGE_R       # groove top edges


def groove(zc):
    """A piston groove on the land, walked from its inboard wall (-z) to outboard."""
    z0, z1 = zc - P.GROOVE_W / 2.0, zc + P.GROOVE_W / 2.0
    s1, a1 = arc((R_GROOVE + GR, z0 + GR), GR, 270.0, 180.0)
    s2, a2 = arc((R_GROOVE + GR, z1 - GR), GR, 180.0, 90.0)
    e1, b1 = arc((R_LAND - ET, z0 - ET), ET, 0.0, 90.0)
    e2, b2 = arc((R_LAND - ET, z1 + ET), ET, 270.0, 360.0)
    return [e1, b1, s1, a1, s2, a2, e2, b2]


def section():
    su, au = arc((R_LAND + UNDER, -UNDER), UNDER, 180.0, 90.0)
    grooves = []
    for zc in sorted((-P.GROOVE_2_Z, -P.GROOVE_1_Z)):
        grooves += groove(zc)
    return [
        (0.0, Z_IN),
        (R_LAND - P.PLUG_NOSE_CHAMFER, Z_IN),
        (R_LAND, Z_IN + NOSE_Z),
        *grooves,
        su, au,
        (R_FL - BRK, 0.0), (R_FL, BRK),
        (R_FL, Z_TOP - BRK), (R_FL - BRK, Z_TOP),
        (0.0, Z_TOP),                    # forward face, flat to the axis: the thrust face
    ]


def gen_step():
    body = revolve_rz(section())
    z_bolt = -P.BOLT_EDGE
    depth = (P.BOLT_L_FWD - P.CASE_WALL - P.PLUG_CLEAR) + P.THREAD_OVER + P.DRILL_OVER
    for th in P.bolt_thetas():
        body = body - radial_drill(P.BOLT_TAP_DRILL, R_LAND + 0.5, depth + 0.5, th, z_bolt)
    for th in P.puller_thetas():
        t = math.radians(th)
        body = body - axial_drill(P.PULLER_TAP_DRILL, P.PULLER_R * math.cos(t),
                                  P.PULLER_R * math.sin(t), Z_TOP + 0.5, P.PULLER_DEPTH + 0.5)
    return finish(one_solid(body), "fwd_closure_6061t651", (0.80, 0.82, 0.86))
