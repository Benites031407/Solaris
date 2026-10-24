"""Mold for the silicone END CAP of one BATES segment.

One printed part: a shallow cup with a pin in the middle.  The cap is a plain disc, as
wide as the tube, with a 13.8 hole that grips the 14.0 sleeve.  The mold holds it the way
it's used: the cup floor makes the cap's underside = the grain's top face.  Pour to the
rim: that surface is the cap's top.  The pin stands 1 mm proud of the rim so the hole
comes out open.

Frame: z = 0 on the print bed, +Z up; the mold axis is Z.
"""

import mold_params as P
from mold_build import finish, revolve_rz


def cap_mold():
    return revolve_rz([
        (0.0, 0.0),
        (P.R_CAP_HEAD, 0.0),
        (P.R_CAP_HEAD, P.ZC_RIM),
        (P.R_CAP_CAV, P.ZC_RIM),                         # rim: pour surface
        (P.R_CAP_CAV, P.ZC_FACE),                        # the cap's edge
        (P.R_GRIP_PIN, P.ZC_FACE),                       # floor = the cap's underside
        (P.R_GRIP_PIN, P.ZC_PIN_TOP),                    # pin = the core hole
        (0.0, P.ZC_PIN_TOP),
    ])


def gen_step():
    return finish(cap_mold(), "end_cap_mold", (0.20, 0.75, 0.45))


if __name__ == "__main__":
    c = gen_step()
    print("cap mold", c.volume, c.bounding_box())
