"""Mold for the silicone BASE of one BATES segment.

One printed part: the base upside down.  The boss is the bottom of the casting tube; its
flat top forms the base floor = the grain's bottom face.  The centre pin makes the 13.8
hole that grips the 14.0 sleeve, and flares 45 deg at the rim so the hole gets a 1 mm
lead-in on the underside only (the grain side of the hole stays sharp).  Pour to the rim:
that surface is the base's underside, the face it stands on.

Frame: z = 0 on the print bed, +Z up; the mold axis is Z.
"""

import mold_params as P
from end_cap_mold import cup_mold
from mold_build import finish, one_solid, revolve_rz


def base_mold():
    body = cup_mold(P.ZB_MOUTH, P.ZB_FACE, P.ZB_RIM)
    r_flare = P.R_GRIP_PIN + P.BASE_LEADIN
    grip_pin = revolve_rz([
        (0.0, P.ZB_FACE - 0.5),
        (P.R_GRIP_PIN, P.ZB_FACE - 0.5),
        (P.R_GRIP_PIN, P.ZB_RIM - P.BASE_LEADIN),
        (r_flare, P.ZB_RIM),                            # lead-in, formed at the pour surface
        (r_flare, P.ZB_PIN_TOP),
        (0.0, P.ZB_PIN_TOP),
    ])
    return one_solid(body.fuse(grip_pin))


def gen_step():
    return finish(base_mold(), "base_mold", (0.20, 0.55, 0.85))


if __name__ == "__main__":
    b = gen_step()
    print("base mold", b.volume, b.bounding_box())
