"""One BATES propellant segment, APCP 70/16/14, cast into its kraft tube.

Frame: motor axis = Z, z = 0 at the segment's AFT face, forward is +Z.
The assembly uses this one STEP four times (srm_assembly.placements()).

Both ends and the core burn; the outside is inhibited by the casting tube it is cast
into (casting_tube.py), which is why GRAIN_OD is exactly that tube's ID.
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(P.GRAIN_CORE / 2.0, P.GRAIN_OD / 2.0, 0.0, P.GRAIN_L)
    return finish(shape, "grain_bates", (0.60, 0.60, 0.58))
