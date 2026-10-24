"""Mold for the silicone END CAP of one BATES segment.

One printed part, holding the cap the way it's used (skirt down).  The boss is the top of
the casting tube; its flat top forms the cap's underside = the grain's top face.  The centre pin makes the
13.8 hole that grips the 14.0 sleeve; five 4 mm pins make the vents the excess propellant
leaves by.  Pour to the rim: that surface is the cap's outside top.

Frame: z = 0 on the print bed, +Z up; the mold axis is Z.
"""

import mold_params as P
from mold_build import finish, one_solid, pin, revolve_rz, tube


def cup_mold(z_mouth, z_face, z_rim):
    """A cup mold: outer wall to the rim, tube boss r R_BOSS standing up to z_face with
    the socket's 1 mm lead-in at its foot.  Shared with the base mold."""
    return revolve_rz([
        (0.0, 0.0),
        (P.R_HEAD, 0.0),
        (P.R_HEAD, z_rim),
        (P.R_CUP, z_rim),                                # rim: pour surface
        (P.R_CUP, z_mouth),                              # cup wall outside
        (P.R_BOSS + P.MOUTH_CHAMFER, z_mouth),           # socket mouth, lead-in flare
        (P.R_BOSS, z_mouth + P.MOUTH_CHAMFER),
        (P.R_BOSS, z_face),                              # boss = casting tube, 12 deep
        (0.0, z_face),                                   # boss top = grain face
    ])


def cap_mold():
    body = cup_mold(P.ZC_MOUTH, P.ZC_FACE, P.ZC_RIM)
    pins = [tube(0.0, P.R_GRIP_PIN, P.ZC_FACE - 0.5, P.ZC_PIN_TOP)]
    pins += [pin(P.D_VENT, P.R_VENT, th, P.ZC_FACE - 0.5, P.ZC_PIN_TOP) for th in P.vent_thetas()]
    return one_solid(body.fuse(*pins))


def gen_step():
    return finish(cap_mold(), "end_cap_mold", (0.20, 0.75, 0.45))


if __name__ == "__main__":
    c = gen_step()
    print("cap mold", c.volume, c.bounding_box())
