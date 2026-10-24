"""Paper-phenolic case liner: the thermal barrier between the grains and the case.

Frame: z = 0 at the liner's AFT end (it sits on the nozzle insulator).
Length is the cavity between the nozzle insulator and the forward insulator LESS
LINER_FLOAT (0.5): it bears on the nozzle insulator and floats at the forward end,
so it never carries the closure load and never holds the take-up ring open.
Cut to length at assembly against the measured CAVITY (not the grain stack), and
check the forward gap with a feeler: >= 0.3 mm.
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(P.LINER_ID / 2.0, P.LINER_OD / 2.0, 0.0, P.LINER_L)
    return finish(shape, "liner", (0.55, 0.33, 0.15))
