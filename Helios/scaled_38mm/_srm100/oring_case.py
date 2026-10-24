"""AS568-237 O-ring, FKM 90A, as installed in a closure's piston gland.  4 per motor.

Frame: ring axis = Z, z = 0 on the ring's mid-plane, drawn at its INSTALLED
radius -- the assembly only slides it along Z to each groove.

Drawn squeezed: the section spans groove bottom to bore (less 0.01 mm each side so
the solids do not share faces) and keeps the free 3.53 mm circle's area, so it
comes out 2.82 tall x 4.42 wide in a 4.80 groove.  srm_verify.py reads the squeeze
back off this geometry.
"""

import srm_params as P
from srm_build import finish, squeezed_oring

GAP = 0.01


def gen_step():
    r_in = P.ORING_GROOVE_D / 2.0 + GAP
    r_out = P.CASE_ID / 2.0 - GAP
    return finish(squeezed_oring(r_in, r_out, P.ORING_CS), "oring_as568_237_fkm90",
                  (0.10, 0.10, 0.11))
