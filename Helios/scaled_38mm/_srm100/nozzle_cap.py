"""Nozzle cap / igniter retainer: LDPE, one per firing.

Frame: the MOTOR frame, identity placement, like the insert it sits in.

Commercial practice for an aft-ignited motor: the pyrogen igniter is pushed in
through the throat and up the core to the forward grain, its leads run back out
through this cap's centre hole, and the cap keeps moisture and debris out of the
chamber until ignition blows it out.  Its conical plug follows the graphite's
15 deg divergent with 0.05 mm radial clearance (a slip fit: it does not grip),
passes the holder's lip, and its flange sits on the holder's aft face, where a
strip of tape across flange and holder holds it.  The igniter goes in last, at the
stand, after the range is cleared (README: static-fire procedure); only then is the
cap fitted and taped.  A motor is never moved with an igniter in it.  The plug stays
clear of the graphite's 0.2 x 45 deg exit break.
"""

import math

import srm_params as P
from srm_build import finish, revolve_rz

S = P.nozzle_stations()
T15 = math.tan(math.radians(P.DIV_HALF_DEG))
CLEAR = 0.05
Z_EXIT = S["z_exit"]
Z_FWD = Z_EXIT + P.CAP_PLUG_L
Z_SEAT = Z_EXIT - P.HOLDER_LIP_T                 # the holder's aft face
Z_BACK = Z_SEAT - P.CAP_FLANGE_T
R_HOLE = P.CAP_LEAD_HOLE / 2.0
OFFSET = P.CAP_WALL / math.cos(math.radians(P.DIV_HALF_DEG))   # radial, for a normal wall


def r_out(z):
    return S["r_exit"] - (z - Z_EXIT) * T15 - CLEAR


def gen_step():
    r_in_exit = r_out(Z_EXIT) - OFFSET
    z_in_fwd = Z_FWD - P.CAP_WALL
    shape = revolve_rz([
        (R_HOLE, Z_FWD),
        (r_out(Z_FWD), Z_FWD),                   # closed forward end
        (r_out(Z_EXIT), Z_EXIT),                 # cone in the divergent
        (r_out(Z_EXIT), Z_SEAT),                 # through the lip
        (P.CAP_FLANGE_OD / 2.0, Z_SEAT),         # flange on the holder's aft face
        (P.CAP_FLANGE_OD / 2.0, Z_BACK),
        (r_in_exit, Z_BACK),
        (r_in_exit, Z_EXIT),
        (r_out(z_in_fwd) - OFFSET, z_in_fwd),
        (R_HOLE, z_in_fwd),
    ])
    return finish(shape, "nozzle_cap_ldpe", (0.93, 0.62, 0.10))
