"""Hydrostatic proof dummy: 304 stainless, stands in for the graphite insert.

Frame: the MOTOR frame, identity placement, exactly where the insert goes.

The proof has to load the case joints, the holder's lip and all five O-rings the way
a firing does, so the holder is proofed with this dummy in the insert's own gland and
never with the graphite (which must stay dry, and is scrap if it cracks at proof).
It copies the insert's outside: 63.50 0/-0.05, Ra 0.8, with the same 20 deg x 3.0
lead-in on the aft edge, and its aft face bears on the lip over the same r 27.0 ..
30.66 annulus.  Being closed, it puts 33 kN on the lip at 10.5 MPa, against the
insert's 19 kN at MEOP: the lip is proofed harder than it is fired.

  * cup bore 40 dia, open forward to the chamber, R2 floor corner; 15 mm closed end
  * 1/8-27 NPT fill / bleed port in the centre of the aft face (8.73 x 10, 90 deg csk 11),
    reached through the holder's lip bore, then a 6 mm passage into the cup.  It is the
    motor's only port (the forward closure has none): fill and bleed with the motor
    vertical, aft end up, where it is the cavity's highest point.
"""

import math

import srm_params as P
from srm_build import arc, finish, revolve_rz

S = P.nozzle_stations()
R_OD = P.INSERT_OD / 2.0
LEAD_R = P.INSERT_LEAD_IN * math.tan(math.radians(20.0))
R_CUP = P.PROOF_CUP_D / 2.0
R_PORT = P.PORT_TAP_DRILL / 2.0
R_CSK = P.PORT_CSK_D / 2.0
R_PASS = P.PROOF_PASSAGE_D / 2.0
Z0, Z1 = S["z_exit"], S["z_fwd"]
Z_FLOOR = Z0 + P.PROOF_BOTTOM_T
Z_PORT = Z0 + P.PORT_THREAD_DEPTH
TIP = (R_PORT - R_PASS) / math.tan(math.radians(59.0))    # 118 deg drill point
BRK = 0.5
CR = 2.0           # cup floor corner


def section():
    sc, ac = arc((R_CUP - CR, Z_FLOOR + CR), CR, 0.0, -90.0)
    return [
        (R_CSK, Z0),                                 # aft face, round the port's 90 deg countersink
        (R_OD - LEAD_R, Z0),                         # bears on the lip out to here
        (R_OD, Z0 + P.INSERT_LEAD_IN),               # 20 deg lead-in
        (R_OD, Z1 - BRK), (R_OD - BRK, Z1),          # forward face
        (R_CUP + BRK, Z1), (R_CUP, Z1 - BRK),
        sc, ac,                                      # cup wall -> floor
        (R_PASS, Z_FLOOR),
        (R_PASS, Z_PORT + TIP),                      # passage
        (R_PORT, Z_PORT),                            # port tap drill
        (R_PORT, Z0 + (R_CSK - R_PORT)),
    ]


def gen_step():
    return finish(revolve_rz(section()), "proof_dummy_304ss", (0.62, 0.52, 0.40))
