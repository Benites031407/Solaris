"""M6 x 16 ISO 7380-1 button head cap screw, class 10.9 -- the FORWARD closure's bolts.

Local frame: head bearing face at z = 0, head toward +Z, shank toward -Z.
The assembly places 18 of these with local +Z pointing radially outward and the
bearing face on the case OD (srm_build.radial_trsf).
16 = 4.0 case wall + 12.0 engaged in the 6061 plug (2 d, the aluminium rule).
"""

import srm_params as P
from srm_build import button_head_screw, finish


def gen_step():
    shape = button_head_screw(P.BOLT_D, P.BOLT_L_FWD, P.BOLT_HEAD_DK, P.BOLT_HEAD_K,
                              P.BOLT_HEAD_S, P.BOLT_HEAD_T)
    return finish(shape, "bolt_iso7380_m6x16", (0.12, 0.12, 0.14))
