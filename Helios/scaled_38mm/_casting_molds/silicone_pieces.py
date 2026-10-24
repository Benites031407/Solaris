"""The three silicone pieces the molds make, as used (z = 0 on the table, +Z up).

Reference geometry only -- nothing here is printed.  Nominal sizes: the molds carry
HOLE_COMP on their printed holes so the silicone comes out at these numbers.

  base    Ø41.8 x 15.  A 34.7 socket 6 deep that grips the 34.8 tube (1 mm lead-in), its
          floor the shoulder the tube stands on = the grain's bottom face; a 13.8 pocket
          6 deep in the middle of it for the core's end; 3 mm of floor under that.
  sleeve  r 5.0..7.0 x 87, square ends.  As molded it also carries a thin skin round the
          rod below its bottom end (the seat's clearance) -- trimmed off, not modelled.
  cap     Ø34.8 x 6 disc, 13.8 hole.
"""

import mold_params as P
from build123d import Compound, Location
from mold_build import finish, revolve_rz, tube

Z_POCKET = P.BASE_FLOOR                         # pocket floor = the core's bottom end, as used
Z_GRAIN0 = P.BASE_FLOOR + P.POCKET_DEPTH        # shoulder = grain bottom face = tube bottom end


def base_piece():
    ch = P.MOUTH_CHAMFER
    return revolve_rz([
        (0.0, 0.0),
        (P.D_BASE / 2.0, 0.0),
        (P.D_BASE / 2.0, P.H_BASE),
        (P.R_BOSS + ch, P.H_BASE),                  # socket mouth
        (P.R_BOSS, P.H_BASE - ch),
        (P.R_BOSS, Z_GRAIN0),                       # shoulder
        (P.R_GRIP_PIN, Z_GRAIN0),                   # pocket, sharp edge on the grain side
        (P.R_GRIP_PIN, Z_POCKET),
        (0.0, Z_POCKET),
    ])


def sleeve_piece(z0=0.0):
    return tube(P.D_ROD / 2.0, P.D_CORE / 2.0, z0, z0 + P.L_SLEEVE)


def cap_piece(z_face=0.0):
    """Cap with its underside (on the grain's top face) at z_face."""
    return tube(P.R_GRIP_PIN, P.D_CAP / 2.0, z_face, z_face + P.CAP_T)


def gen_step():
    step = P.D_BASE + 10.0
    base = finish(base_piece(), "silicone_base", (0.85, 0.30, 0.30))
    sleeve = finish(sleeve_piece().moved(Location((step, 0.0, 0.0))), "silicone_sleeve", (0.85, 0.30, 0.30))
    cap = finish(cap_piece().moved(Location((2.0 * step, 0.0, 0.0))), "silicone_cap", (0.85, 0.30, 0.30))
    return Compound(children=[base, sleeve, cap], label="silicone_pieces")


if __name__ == "__main__":
    b, s, c = base_piece(), sleeve_piece(), cap_piece()
    print(f"silicone base {b.volume / 1000:.2f} cm3, sleeve {s.volume / 1000:.2f} cm3, "
          f"cap {c.volume / 1000:.2f} cm3")
