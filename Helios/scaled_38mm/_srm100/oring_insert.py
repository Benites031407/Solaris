"""AS568-230 O-ring, FKM 90A, sealing the graphite insert in the holder bore.  1 per motor.

Frame: ring axis = Z, z = 0 on the ring's mid-plane, drawn at its INSTALLED
radius (ID on the 63.50 insert, OD in the holder's 69.14 groove).

Rod (female) gland: the groove is cut in the steel, the ring's ID seals on the
graphite.  It is the hottest seal in the motor -- graphite conducts -- and is a
consumable: replace after every firing.  Section drawn squeezed, area-conserving,
exactly like oring_case.py.
"""

import srm_params as P
from srm_build import finish, squeezed_oring

GAP = 0.01


def gen_step():
    r_in = P.INSERT_OD / 2.0 + GAP
    r_out = P.INSERT_GROOVE_D / 2.0 - GAP
    return finish(squeezed_oring(r_in, r_out, P.INSERT_ORING_CS), "oring_as568_230_fkm90",
                  (0.20, 0.08, 0.06))
