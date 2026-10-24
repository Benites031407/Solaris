"""M6 x 10 ISO 7380-1 button head cap screw, class 10.9 -- the NOZZLE holder's bolts.

Local frame: head bearing face at z = 0, head toward +Z, shank toward -Z.
10 = 4.0 case wall + 6.0 engaged in the 304 holder (1.0 d, the steel rule).
Shorter than the forward ones because the holder has only 14.2 mm of steel outside
the graphite; see srm_params.self_check() "aft tapped hole leaves ...".
Do not mix the two lengths up: an M6 x 16 here jams at the end of the tapped
thread with its head 3-4 mm proud of the case, and an M6 x 10 in the forward
closure engages only 1 d of aluminium.
"""

import srm_params as P
from srm_build import button_head_screw, finish


def gen_step():
    shape = button_head_screw(P.BOLT_D, P.BOLT_L_AFT, P.BOLT_HEAD_DK, P.BOLT_HEAD_K,
                              P.BOLT_HEAD_S, P.BOLT_HEAD_T)
    return finish(shape, "bolt_iso7380_m6x10", (0.12, 0.12, 0.14))
