"""Phenolic washer over the steel nozzle holder's inboard face.

Frame: z = 0 at its aft face (on the holder and the graphite's forward face).
Its bore continues the graphite's convergent cone: CONV_ENTRY_D at the aft face,
opening at CONV_HALF_DEG toward the chamber, so there is no step for the flow to
trip on where the phenolic meets the graphite.
"""

import math

import srm_params as P
from srm_build import finish, revolve_rz

R_AFT = P.CONV_ENTRY_D / 2.0
R_FWD = R_AFT + P.NOZ_INSUL_T * math.tan(math.radians(P.CONV_HALF_DEG))
R_OUT = P.NOZ_INSUL_OD / 2.0


def gen_step():
    shape = revolve_rz([(R_AFT, 0.0), (R_OUT, 0.0), (R_OUT, P.NOZ_INSUL_T), (R_FWD, P.NOZ_INSUL_T)])
    return finish(shape, "nozzle_insulator", (0.50, 0.30, 0.12))
