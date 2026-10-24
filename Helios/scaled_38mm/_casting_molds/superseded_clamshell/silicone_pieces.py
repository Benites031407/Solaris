"""The three silicone pieces the molds make, as used (z = 0 on the table, +Z up).

Reference geometry only -- nothing here is printed.  Nominal sizes: the molds carry
HOLE_COMP / GROOVE_COMP on their printed holes so the silicone comes out at these numbers.

  base    cup r 17.4..20.9 over the tube's bottom 12 mm, 8 mm floor, 13.8 grip hole with a
          1 mm lead-in on the underside.
  sleeve  r 5.0..7.0 x 88, a 45 deg bevel across the whole wall at its top (molded) end.
          As molded it also carries a thin skin down the rod from the bevel (the rod seat's
          clearance) -- trimmed off, not modelled.
  cap     5 mm disk + 12 mm skirt over the tube's top, 13.8 grip hole, 5 x 4 mm vents.
"""

import mold_params as P
from build123d import Compound, Location
from mold_build import finish, one_solid, pin, revolve_rz

Z_GRAIN0 = P.BASE_FLOOR                         # grain bottom face, as used


def base_piece():
    z_rim = P.BASE_FLOOR + P.SOCKET_DEPTH
    return revolve_rz([
        (P.R_GRIP_PIN + P.BASE_LEADIN, 0.0),
        (P.R_CUP, 0.0),
        (P.R_CUP, z_rim),
        (P.R_BOSS + P.MOUTH_CHAMFER, z_rim),
        (P.R_BOSS, z_rim - P.MOUTH_CHAMFER),
        (P.R_BOSS, P.BASE_FLOOR),                    # floor = grain bottom face
        (P.R_GRIP_PIN, P.BASE_FLOOR),                # sharp edge on the grain side
        (P.R_GRIP_PIN, P.BASE_LEADIN),
    ])


def sleeve_piece(z0=0.0):
    ch = P.SLEEVE_TIP_CHAMFER
    r_in, r_out, z1 = P.D_ROD / 2.0, P.D_CORE / 2.0, z0 + P.L_SLEEVE
    return revolve_rz([(r_in, z0), (r_out, z0), (r_out, z1 - ch), (r_out - ch, z1), (r_in, z1)])


def cap_piece(z_face=0.0):
    """Cap with its inner face (on the grain's top face) at z_face, skirt hanging down."""
    z_skirt = z_face - P.SOCKET_DEPTH
    z_top = z_face + P.CAP_TOP
    body = revolve_rz([
        (P.R_GRIP_PIN, z_face),
        (P.R_BOSS, z_face),
        (P.R_BOSS, z_skirt + P.MOUTH_CHAMFER),
        (P.R_BOSS + P.MOUTH_CHAMFER, z_skirt),
        (P.R_CUP, z_skirt),
        (P.R_CUP, z_top),
        (P.R_GRIP_PIN, z_top),
    ])
    vents = [pin(P.D_VENT, P.R_VENT, th, z_face - 1.0, z_top + 1.0) for th in P.vent_thetas()]
    return one_solid(body.cut(*vents))


def gen_step():
    step = 2.0 * P.R_CUP + 10.0
    base = finish(base_piece(), "silicone_base", (0.85, 0.30, 0.30))
    sleeve = finish(sleeve_piece().moved(Location((step, 0.0, 0.0))), "silicone_sleeve", (0.85, 0.30, 0.30))
    cap = cap_piece(P.SOCKET_DEPTH).moved(Location((2.0 * step, 0.0, 0.0)))
    cap = finish(cap, "silicone_cap", (0.85, 0.30, 0.30))
    return Compound(children=[base, sleeve, cap], label="silicone_pieces")


if __name__ == "__main__":
    b, s, c = base_piece(), sleeve_piece(), cap_piece()
    print(f"silicone base {b.volume / 1000:.2f} cm3, sleeve {s.volume / 1000:.2f} cm3, "
          f"cap {c.volume / 1000:.2f} cm3")
