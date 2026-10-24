"""Mold for the silicone SLEEVE: a Ø14 tube cast straight onto the aluminium core rod.

A clamshell that stands on end.  Four printed parts, laid out on the bed as they print
(sleeve_mold.stl), and also one STL per part (sleeve_mold_half.stl is printed twice):
  2 x half    identical; each is the other turned 180 deg about the mold axis.  A
              half-round sleeve cavity, the rod seat at the bottom, two registration
              cones + two sockets, and three rows of M3 holes.  The bolts are required:
              they hold the seam shut.  The keys are staggered along the length, so a half
              turned end-for-end won't close.  Printed parting face up.
  stand       plate with a pocket that holds the closed mold's bottom end: keeps it
              upright, locates the halves there, catches drips.
  rod guide   sits on the top face and holds the top of the rod on the axis.  Its hub
              stays 6 mm above the pour surface; through the windows either side of it
              you watch the level.  Printed plate-down.

The sleeve's two ends: the bottom one is molded, with a 45 deg bevel across the whole
wall -- in use that end goes UP, into the cap.  The bevel's cone carries on down into the
rod seat as a funnel, so the rod's tip finds the seat.  The top end is the pour surface,
flush with the top face.

Frame (closed mold): z = 0 on the stand, axis = Z, parting plane y = 0, half A at y <= 0.
"""

import mold_params as P
from build123d import Axis, Compound, Location, Plane, Solid
from mold_build import finish, flip_z, one_solid, revolve_rz, tube


def _box(x0, x1, y0, y1, z0, z1):
    return Solid.make_box(x1 - x0, y1 - y0, z1 - z0, Plane(origin=(x0, y0, z0)))


def _cone_y(x, z, y0, r0, y1, r1):
    """A truncated cone on a line parallel to Y, radius r0 at y0 and r1 at y1."""
    d = 1.0 if y1 > y0 else -1.0
    return Solid.make_cone(r0, r1, abs(y1 - y0), Plane(origin=(x, y0, z), z_dir=(0, d, 0)))


def _edges_at(shape, test, n=4):
    edges = [e for e in shape.edges() if test(e.center())]
    if len(edges) != n:
        raise RuntimeError(f"picked {len(edges)} edges to chamfer, expected {n}")
    return edges


def _rect_mouth(shape, z, hx, hy):
    """The four edges of a rectangular opening hx x hy (half sizes) at height z."""
    return _edges_at(shape, lambda c: abs(c.Z - z) < 1e-6 and
                     (abs(abs(c.X) - hx) < 1e-6 or abs(abs(c.Y) - hy) < 1e-6) and
                     abs(c.X) <= hx + 1e-6 and abs(c.Y) <= hy + 1e-6)


def half_a():
    body = _box(-P.SM_W / 2, P.SM_W / 2, -P.SM_T, 0.0, 0.0, P.ZS_TOP)
    bed = _edges_at(body, lambda c: abs(c.Y + P.SM_T) < 1e-6)        # the back face prints on the bed
    body = body.chamfer(P.BED_CHAMFER, None, bed)
    ch = P.SLEEVE_TIP_CHAMFER
    cavity = revolve_rz([
        (0.0, P.ZS_SEAT),
        (P.R_SEAT, P.ZS_SEAT),                             # rod seat: centres the rod's foot
        (P.R_SEAT, P.ZS_FUNNEL),                           # funnel = the tip bevel, carried on
        (P.R_SLEEVE_CAV, P.ZS_END + ch),                   # sleeve's molded tip: 45 deg, full wall
        (P.R_SLEEVE_CAV, P.ZS_TOP + 1.0),                  # open at the top face
        (0.0, P.ZS_TOP + 1.0),
    ])
    slope = (P.KEY_D0 - P.KEY_D1) / 2.0 / P.KEY_H          # cone radius lost per mm of height
    r0 = P.KEY_D0 / 2.0
    rs = (P.KEY_D0 + P.FIT_KEY) / 2.0
    cuts = [cavity]
    pins = []
    for (xp, xs), z in zip(((P.KEY_X, -P.KEY_X), (-P.KEY_X, P.KEY_X)), P.KEY_Z):   # cone at xp, socket at xs
        pins.append(_cone_y(xp, z, -0.5, r0 + 0.5 * slope, P.KEY_H, P.KEY_D1 / 2.0))
        depth = P.KEY_H + 0.5
        cuts.append(_cone_y(xs, z, 0.5, rs + 0.5 * slope, -depth, rs - depth * slope))
    for x in (-P.KEY_X, P.KEY_X):
        for z in P.BOLT_Z:
            cuts.append(Solid.make_cylinder(P.D_BOLT / 2.0, P.SM_T + 2.0,
                                            Plane(origin=(x, 1.0, z), z_dir=(0, -1, 0))))
    body = one_solid(body.fuse(*pins))
    return one_solid(body.cut(*cuts))


def half_b():
    return half_a().rotate(Axis.Z, 180.0)


def stand():
    """Closed-mold frame: the mold's bottom face at z = 0 sits on the plate."""
    wx, wy = P.BOX_X / 2 + P.BOX_WALL, P.BOX_Y / 2 + P.BOX_WALL
    mx, my = wx + P.STAND_MARGIN, wy + P.STAND_MARGIN
    plate = _box(-mx, mx, -my, my, -P.STAND_PLATE, 0.0)
    rim = _box(-wx, wx, -wy, wy, -0.5, P.BOX_SKIRT)
    pocket = _box(-P.BOX_X / 2, P.BOX_X / 2, -P.BOX_Y / 2, P.BOX_Y / 2, 0.0, P.BOX_SKIRT + 1.0)
    st = one_solid(plate.fuse(rim).cut(pocket))
    return st.chamfer(P.MOUTH_LEADIN, None, _rect_mouth(st, P.BOX_SKIRT, P.BOX_X / 2, P.BOX_Y / 2))


def rod_guide():
    """Closed-mold frame, as it sits on the top face."""
    wx, wy = P.BOX_X / 2 + P.BOX_WALL, P.BOX_Y / 2 + P.BOX_WALL
    cx, cy = P.BOX_X / 2 - P.GUIDE_LEDGE, P.BOX_Y / 2 - P.GUIDE_LEDGE
    z_skirt = P.ZS_TOP - P.BOX_SKIRT
    g = _box(-wx, wx, -wy, wy, z_skirt, P.ZG_PLATE1)
    g = g.cut(_box(-P.BOX_X / 2, P.BOX_X / 2, -P.BOX_Y / 2, P.BOX_Y / 2, z_skirt - 1.0, P.ZS_TOP))  # skirt
    g = one_solid(g)
    g = g.chamfer(P.MOUTH_LEADIN, None, _rect_mouth(g, z_skirt, P.BOX_X / 2, P.BOX_Y / 2))
    g = g.cut(_box(-cx, cx, -cy, cy, P.ZS_TOP - 0.5, P.ZG_PLATE0))                               # chamber
    hw = P.GUIDE_BAR_W / 2.0
    for y0, y1 in ((hw, cy), (-cy, -hw)):                                          # windows
        g = g.cut(_box(-cx, cx, y0, y1, P.ZG_PLATE0 - 1.0, P.ZG_PLATE1 + 1.0))
    g = g.fuse(tube(0.0, P.R_GUIDE_HUB, P.ZG_HUB0, P.ZG_PLATE1))                   # hub
    c, rg = P.BORE_CHAMFER, P.R_GUIDE
    bore = revolve_rz([                                                            # chamfered both ends
        (0.0, P.ZG_HUB0 - 1.0), (rg + c + 1.0, P.ZG_HUB0 - 1.0), (rg, P.ZG_HUB0 + c),
        (rg, P.ZG_PLATE1 - c), (rg + c + 1.0, P.ZG_PLATE1 + 1.0), (0.0, P.ZG_PLATE1 + 1.0),
    ])
    return one_solid(g.cut(bore))


def closed():
    """The mold as it stands for pouring (reference, not printed like this)."""
    return {"half_a": half_a(), "half_b": half_b(), "stand": stand(), "rod_guide": rod_guide()}


def half_printed():
    """A half as it prints: on its back, parting face up, axis along Y, centred on x = 0."""
    return half_a().rotate(Axis.X, 90.0).moved(Location((0.0, P.ZS_TOP / 2.0, P.SM_T)))


def stand_printed():
    return stand().moved(Location((0.0, 0.0, P.STAND_PLATE)))


def rod_guide_printed():
    return flip_z(rod_guide(), P.ZG_PLATE1)


def print_layout():
    lying = half_printed()
    dx = P.SM_W / 2.0 + 5.0
    h1 = lying.moved(Location((-dx, 0.0, 0.0)))
    h2 = lying.moved(Location((dx, 0.0, 0.0)))
    st = stand_printed()
    sb = st.bounding_box()
    st = st.moved(Location((-P.SM_W - 5.0 - sb.min.X, P.ZS_TOP / 2.0 + 8.0 - sb.min.Y, 0.0)))
    gd = rod_guide_printed()
    gb, sb = gd.bounding_box(), st.bounding_box()
    gd = gd.moved(Location((sb.max.X + 8.0 - gb.min.X, sb.min.Y - gb.min.Y, 0.0)))
    return [
        finish(h1, "sleeve_mold_half_1", (0.20, 0.55, 0.85)),
        finish(h2, "sleeve_mold_half_2", (0.25, 0.60, 0.90)),
        finish(st, "sleeve_mold_stand", (0.55, 0.55, 0.60)),
        finish(gd, "sleeve_mold_rod_guide", (0.95, 0.60, 0.15)),
    ]


def gen_step():
    return Compound(children=print_layout(), label="sleeve_mold")


if __name__ == "__main__":
    for s in print_layout():
        bb = s.bounding_box()
        print(f"{s.label:24s} {s.volume / 1000:7.2f} cm3  x {bb.min.X:7.2f}..{bb.max.X:7.2f}  "
              f"y {bb.min.Y:7.2f}..{bb.max.Y:7.2f}  z {bb.min.Z:6.2f}..{bb.max.Z:6.2f}")
    c = closed()
    a, b = c["half_a"], c["half_b"]
    x = a.intersect(b)
    print("half_a x half_b overlap mm3:", sum(s.volume for s in x.solids()) if x else 0.0)
