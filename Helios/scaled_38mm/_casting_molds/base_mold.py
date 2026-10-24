"""Mold for the silicone BASE of one BATES segment.

One printed part: a cup holding the base upside down.  The boss on its floor makes the
socket the tube's bottom end sits in, and the boss's flat top makes the shoulder = the
grain's bottom face.  The pin on the boss makes the blind pocket the core's end plugs into
(13.8: it grips the 14.0 sleeve).  Pour to the rim: that surface is the base's underside,
the face it stands on.

Frame: z = 0 on the print bed, +Z up; the mold axis is Z.
"""

import mold_params as P
from mold_build import finish, revolve_rz


def base_mold():
    return revolve_rz([
        (0.0, 0.0),
        (P.R_BASE_HEAD, 0.0),
        (P.R_BASE_HEAD, P.ZB_RIM),
        (P.R_BASE_CAV, P.ZB_RIM),                        # rim: pour surface
        (P.R_BASE_CAV, P.FLOOR),                         # the base's outside
        (P.R_BOSS + P.MOUTH_CHAMFER, P.FLOOR),           # socket mouth, lead-in flare
        (P.R_BOSS, P.FLOOR + P.MOUTH_CHAMFER),
        (P.R_BOSS, P.ZB_SHOULDER),                       # boss = the tube's bottom end
        (P.R_GRIP_PIN, P.ZB_SHOULDER),                   # boss top = shoulder = grain face
        (P.R_GRIP_PIN, P.ZB_POCKET),                     # pin = core pocket
        (0.0, P.ZB_POCKET),
    ])


def gen_step():
    return finish(base_mold(), "base_mold", (0.20, 0.55, 0.85))


if __name__ == "__main__":
    b = gen_step()
    print("base mold", b.volume, b.bounding_box())
