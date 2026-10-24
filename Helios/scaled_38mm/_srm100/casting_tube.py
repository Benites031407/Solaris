"""Spiral-wound kraft casting tube -- the grain is cast straight into it and stays in it.

Frame: same as grain.py (z = 0 at the segment's aft face).  Four instances.
Its bore IS the grain's outer surface, so it inhibits the grain OD; its OD slides
into the liner with 0.1 mm radial clearance.
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(P.TUBE_ID / 2.0, P.TUBE_OD / 2.0, 0.0, P.GRAIN_L)
    return finish(shape, "casting_tube", (0.76, 0.60, 0.42))
