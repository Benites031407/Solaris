"""Nozzle holder: the aft closure.  304 stainless -- PAPER: steel, not aluminium,
behind the graphite.  (Tripoli USC 10-10.4 allows a ferrous rear closure.)

Frame: the MOTOR frame (z = 0 on the case's aft end face, +Z forward); identity
placement.  Its forward face is Z_HOLDER_FACE = PLUG_L inside the case.

Half-section, walked from the bore mouth aft, then back up the outside:
  * insert bore 63.58 +0.025/0, Ra 0.8, opening at the forward face with a
    20 deg x 1.8 lead-in so the graphite enters square
  * ONE AS568-230 rod-gland groove in the bore, 69.14 +0.05/0 x 4.80, R0.4
    corners, cut inside the flange (z = -3): 13 mm aft of the throat, where the
    graphite is 17 mm thick and the steel 15 mm
  * R0.8 root fillet at the seat (stress relief at the lip's bending root); the
    insert's 20 deg lead-in clears it by >= 0.2 mm (0.31)
  * retaining lip, 6 thick: the insert's aft face bears on it from r 27.0 out; its
    bore opens at 20 deg, wider than the 15 deg plume
  * aft body 71.6 OD (4 mm wall) around the divergent, R2 into the flange
  * flange 100 OD x 6 butting the case's aft end; R0.5 under it, clear of the
    case's 20 deg bore lead-in
  * seal land 91.94 0/-0.02 with the same two AS568-237 piston grooves as the
    forward closure, 30 deg x 1.0 nose chamfer
  * 18 x M6 radial tapped holes on the bolt row (drawn at the 5.0 tap drill),
    bolt 0 keyed 0.8 deg off the even pattern; 6 mm of thread in the steel,
    2.7 mm of wall left under each drill point
  * 2 x M6 axial puller threads in the flange's aft face, 10 deep, between bolts:
    the holder is drawn out with a bridge and two screws, never levered or knocked
  * groove top edges R0.1 (0.08 - 0.13), all grooves
"""

import math

import srm_params as P
from srm_build import arc, axial_drill, finish, one_solid, radial_drill, revolve_rz

S = P.nozzle_stations()
R_LAND = P.PLUG_OD / 2.0
R_GROOVE = P.ORING_GROOVE_D / 2.0
R_FL = P.FLANGE_OD / 2.0
R_BORE = P.INSERT_BORE_D / 2.0
R_IGROOVE = P.INSERT_GROOVE_D / 2.0
R_BODY = R_BORE + P.HOLDER_AFT_WALL
R_LIP = S["r_exit"] + P.HOLDER_LIP_STEP
Z_FACE = P.Z_HOLDER_FACE
Z_SEAT = S["z_exit"]
Z_AFT = Z_SEAT - P.HOLDER_LIP_T
Z_FL = -P.FLANGE_T
R_LIP_AFT = R_LIP + P.HOLDER_LIP_T * math.tan(math.radians(P.HOLDER_LIP_BORE_DEG))
NOSE_Z = P.PLUG_NOSE_CHAMFER / math.tan(math.radians(30.0))
LEAD_R = P.HOLDER_BORE_LEAD_IN * math.tan(math.radians(20.0))
GR = P.GROOVE_R_BOTTOM
BRK = 0.5          # 45 deg edge breaks
UNDER = 0.5        # radius under the flange
BODY_R = 2.0       # root radius, aft body -> flange
SEAT_R = P.HOLDER_SEAT_R    # bore -> seat root fillet
ET = P.GROOVE_EDGE_R       # groove top edges


def case_groove(zc):
    """A piston groove on the land, walked in +z: aft wall, bottom, forward wall."""
    z0, z1 = zc - P.GROOVE_W / 2.0, zc + P.GROOVE_W / 2.0
    s1, a1 = arc((R_GROOVE + GR, z0 + GR), GR, 270.0, 180.0)
    s2, a2 = arc((R_GROOVE + GR, z1 - GR), GR, 180.0, 90.0)
    e1, b1 = arc((R_LAND - ET, z0 - ET), ET, 0.0, 90.0)
    e2, b2 = arc((R_LAND - ET, z1 + ET), ET, 270.0, 360.0)
    return [e1, b1, s1, a1, s2, a2, e2, b2]


def insert_groove(zc):
    """The rod groove in the bore, walked in -z: forward wall, bottom, aft wall."""
    z0, z1 = zc - P.INSERT_GROOVE_W / 2.0, zc + P.INSERT_GROOVE_W / 2.0
    s1, a1 = arc((R_IGROOVE - GR, z1 - GR), GR, 90.0, 0.0)
    s2, a2 = arc((R_IGROOVE - GR, z0 + GR), GR, 0.0, -90.0)
    e1, b1 = arc((R_BORE + ET, z1 + ET), ET, 180.0, 270.0)
    e2, b2 = arc((R_BORE + ET, z0 - ET), ET, 90.0, 180.0)
    return [e1, b1, s1, a1, s2, a2, e2, b2]


def section():
    ss, a_seat = arc((R_BORE - SEAT_R, Z_SEAT + SEAT_R), SEAT_R, 0.0, -90.0)
    sb, a_body = arc((R_BODY + BODY_R, Z_FL - BODY_R), BODY_R, 180.0, 90.0)
    su, a_under = arc((R_LAND + UNDER, UNDER), UNDER, 270.0, 180.0)
    grooves = []
    for zc in sorted((P.GROOVE_1_Z, P.GROOVE_2_Z)):
        grooves += case_groove(zc)
    return [
        (R_BORE + LEAD_R, Z_FACE),                       # bore mouth, forward face
        (R_BORE, Z_FACE - P.HOLDER_BORE_LEAD_IN),
        *insert_groove(P.INSERT_GROOVE_Z),
        ss, a_seat,                                      # bore -> seat
        (R_LIP, Z_SEAT),                                 # seat face under the graphite
        (R_LIP_AFT, Z_AFT),                              # lip bore, 20 deg
        (R_BODY - BRK, Z_AFT), (R_BODY, Z_AFT + BRK),    # aft face
        sb, a_body,                                      # aft body -> flange root
        (R_FL - BRK, Z_FL), (R_FL, Z_FL + BRK),          # flange
        (R_FL, -BRK), (R_FL - BRK, 0.0),
        su, a_under,                                     # bearing face -> land
        *grooves,
        (R_LAND, Z_FACE - NOSE_Z), (R_LAND - P.PLUG_NOSE_CHAMFER, Z_FACE),
    ]


def gen_step():
    body = revolve_rz(section())
    depth = (P.BOLT_L_AFT - P.CASE_WALL - P.PLUG_CLEAR) + P.THREAD_OVER + P.DRILL_OVER
    for th in P.bolt_thetas():
        body = body - radial_drill(P.BOLT_TAP_DRILL, R_LAND + 0.5, depth + 0.5, th, P.bolt_z_aft())
    for th in P.puller_thetas():
        t = math.radians(th)
        body = body - axial_drill(P.PULLER_TAP_DRILL, P.HOLDER_PULLER_R * math.cos(t),
                                  P.HOLDER_PULLER_R * math.sin(t), Z_FL - 0.5,
                                  P.HOLDER_PULLER_DEPTH + 0.5, toward=+1.0)
    return finish(one_solid(body), "nozzle_holder_304ss", (0.55, 0.56, 0.58))
