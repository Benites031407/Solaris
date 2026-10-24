"""Nozzle insert: one piece of isomolded fine-grain graphite, throat 23.00 +0.05/0.
Grade ISO-63, TTK-4 or IG-43 class (rho >= 1.78, flexural >= 50 MPa); not extruded rod.

Frame: the MOTOR frame -- the flow path's stations are motor z values from
srm_params.nozzle_stations(), so this is placed with the identity.

Flow path, forward to aft (half-section, every junction tangent):
  52.0 entry at the holder face  ->  35 deg convergent  ->  R11.5 blend (1.0 rt)
  ->  4.0 cylindrical throat land, 23.00  ->  R5.75 blend (0.5 rt)
  ->  15 deg conical divergent  ->  52.0 exit, expansion 5.11
The exit edge is broken 0.2 x 45 deg: 52.0 is the nominal cone/face intersection;
the cone now ends 0.27 above the face at 51.85 (eps 5.08) and the break opens to
52.4 at the face.  The aft face inside the lip, r 26.2 .. 27.0, is the push face
for pressing the insert out forward (README: extraction).
Outside: 63.50 0/-0.05, Ra 0.8 -- the AS568-230 rod seal runs on it -- with a
20 deg x 3.0 lead-in on the aft edge, which goes into the holder first.  The aft
face bears on the holder's lip (r 27.0 .. 30.66); the forward face sits under the
phenolic nozzle insulator.

Graphite is brittle: all loads on it are compressive.  Chamber pressure pushes it
onto the lip (19 kN at MEOP, 29 MPa on the seat).  No threads, no press fit: the
0.08-0.155 mm diametral clearance is closed by the graphite's own growth early in
the burn, after which it bears on the steel at up to ~17 MPa -- radial compression,
the benign direction (srm_params.self_check).  Never wet it: a hydro proof uses the
304 proof dummy in its place.
Measure the throat after every firing.  Re-use while it is <= 23.9 mm and
uncracked; the post-burn value goes into THROAT_D for the next simulation.
"""

import math

import srm_params as P
from srm_build import arc, finish, revolve_rz

S = P.nozzle_stations()
R_OD = P.INSERT_OD / 2.0
LEAD_R = P.INSERT_LEAD_IN * math.tan(math.radians(20.0))
BRK = 0.5
XB = P.EXIT_BREAK
XB_H = XB / (1.0 - math.tan(math.radians(P.DIV_HALF_DEG)))   # where the break meets the cone


def section():
    s_up, a_up = arc(S["c_up"], P.R_THROAT_UP, 180.0 - P.CONV_HALF_DEG, 180.0)
    s_dn, a_dn = arc(S["c_dn"], P.R_THROAT_DN, 180.0, 180.0 + P.DIV_HALF_DEG)
    return [
        (S["r_entry"], S["z_fwd"]),
        s_up, a_up,                                    # convergent -> blend -> land
        (S["r_throat"], S["z_land_aft"]),
        a_dn,                                          # land -> blend
        (S["r_exit"] - XB_H * math.tan(math.radians(P.DIV_HALF_DEG)), S["z_exit"] + XB_H),   # divergent
        (S["r_exit"] + XB, S["z_exit"]),               # 45 deg exit break
        (R_OD - LEAD_R, S["z_exit"]),                  # aft (bearing) face
        (R_OD, S["z_exit"] + P.INSERT_LEAD_IN),
        (R_OD, S["z_fwd"] - BRK), (R_OD - BRK, S["z_fwd"]),
    ]


def gen_step():
    assert abs(section()[1][0] - S["r_up"]) < 1e-9
    return finish(revolve_rz(section()), "nozzle_insert_graphite", (0.16, 0.16, 0.17))
