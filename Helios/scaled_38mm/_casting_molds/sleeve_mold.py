"""Mold for the silicone SLEEVE: a plain Ø14 tube around the Ø10 aluminium core rod.

An inner cylinder inside a bigger cylinder, standing on end.  Four printed parts, laid
out on the bed as they print (sleeve_mold.stl), and also one STL per part:
  outer cylinder  its Ø14 bore forms the sleeve's OD.  Open at both ends, and the same
                  either way up.
  foot            a wide flange with a collar the outer cylinder's bottom end pushes into.
                  Its floor forms the sleeve's bottom end; the seat in the middle of it
                  takes the inner cylinder's foot.
  top guide       a skirt over the outer cylinder's top end and a plate 5 mm above the pour
                  surface, with a hub that holds the inner cylinder on the axis.  Through
                  the windows either side of the hub you watch the level and top it up.
  inner cylinder  the aluminium rod itself: the sleeve cures straight onto it and comes out
                  of the mold already on it.  Or the printed Ø10 pin, which the seat and the
                  guide fit the same way -- but at normal infill it's lighter than the
                  silicone it stands in and floats up out of the seat: print it solid and
                  tape its top down to the guide.

Filled by displacement: the silicone goes into the open bore (foot and outer cylinder
only), then the guide goes on and the rod is pushed down through it into the seat, which
brings the level up to the top face.  Poured past a rod already in, the 2 mm annulus
traps air.  The sleeve's bottom end forms on the foot floor; its top end is the pour
surface, flush with the outer cylinder's top face.

Frame (assembled): z = 0 on the table, axis = Z.
"""

import mold_params as P
from build123d import Compound, Location, Plane, Solid
from mold_build import finish, flip_z, one_solid, revolve_rz, tube


def outer_cylinder():
    ch = P.SM_END_CH
    return revolve_rz([
        (P.R_BORE, P.ZS_END),
        (P.R_SM - ch, P.ZS_END),
        (P.R_SM, P.ZS_END + ch),
        (P.R_SM, P.ZS_TOP - ch),
        (P.R_SM - ch, P.ZS_TOP),
        (P.R_BORE, P.ZS_TOP),
    ])


def foot():
    ml, sl = P.MOUTH_LEADIN, P.SEAT_LEADIN
    return revolve_rz([
        (0.0, 0.0),
        (P.FOOT_D / 2.0, 0.0),
        (P.FOOT_D / 2.0, P.FOOT_FLOOR),
        (P.R_SKIRT_OUT, P.FOOT_FLOOR),
        (P.R_SKIRT_OUT, P.ZF_COLLAR),
        (P.R_SKIRT_IN + ml, P.ZF_COLLAR),                # collar mouth lead-in
        (P.R_SKIRT_IN, P.ZF_COLLAR - ml),
        (P.R_SKIRT_IN, P.FOOT_FLOOR),
        (P.R_SEAT + sl, P.FOOT_FLOOR),                   # floor = the sleeve's bottom end
        (P.R_SEAT, P.FOOT_FLOOR - sl),                   # seat lead-in
        (P.R_SEAT, P.ZS_SEAT),
        (0.0, P.ZS_SEAT),
    ])


def top_guide():
    ml = P.MOUTH_LEADIN
    g = revolve_rz([
        (P.R_SKIRT_IN + ml, P.ZG_SKIRT),                 # skirt mouth lead-in
        (P.R_SKIRT_OUT, P.ZG_SKIRT),
        (P.R_SKIRT_OUT, P.ZG_PLATE1),
        (0.0, P.ZG_PLATE1),
        (0.0, P.ZG_PLATE0),                              # plate
        (P.R_CHAMBER, P.ZG_PLATE0),
        (P.R_CHAMBER, P.ZS_TOP),                         # chamber over the pour surface
        (P.R_SKIRT_IN, P.ZS_TOP),                        # ledge: sits on the top face
        (P.R_SKIRT_IN, P.ZG_SKIRT + ml),
    ])
    hw, rw = P.GUIDE_BAR_W / 2.0, P.R_CHAMBER + 1.0
    disc = tube(0.0, P.R_CHAMBER, P.ZG_PLATE0 - 0.5, P.ZG_PLATE1 + 1.0)
    hub = tube(0.0, P.R_GUIDE_HUB, P.ZG_PLATE0 - 1.0, P.ZG_PLATE1 + 2.0)
    for y0, y1 in ((hw, rw), (-rw, -hw)):                # windows either side of the bars
        box = Solid.make_box(2 * rw, y1 - y0, P.GUIDE_PLATE + 3.0,
                             Plane(origin=(-rw, y0, P.ZG_PLATE0 - 1.0)))
        g = g.cut(disc.intersect(box).cut(hub))
    c, rg = P.BORE_CHAMFER, P.R_GUIDE
    bore = revolve_rz([                                  # chamfered both ends
        (0.0, P.ZG_PLATE0 - 1.0), (rg + c + 1.0, P.ZG_PLATE0 - 1.0), (rg, P.ZG_PLATE0 + c),
        (rg, P.ZG_PLATE1 - c), (rg + c + 1.0, P.ZG_PLATE1 + 1.0), (0.0, P.ZG_PLATE1 + 1.0),
    ])
    return one_solid(g.cut(bore))


def inner_cylinder():
    """The printed pin, seated: it stands in for the rod, same diameter, same length."""
    r, z0, z1 = P.D_ROD / 2.0, P.ZS_SEAT, P.ZS_SEAT + P.L_ROD_MIN
    t, b = P.PIN_TIP_CH, P.PIN_TOP_CH
    return revolve_rz([(0.0, z0), (r - t, z0), (r, z0 + t), (r, z1 - b), (r - b, z1), (0.0, z1)])


def assembled():
    """The mold as it stands for pouring (reference, not printed like this)."""
    return {"foot": foot(), "outer_cylinder": outer_cylinder(), "top_guide": top_guide(),
            "inner_cylinder": inner_cylinder()}


# ---- as printed: each part on z = 0, centred on x = y = 0 --------------------------------
def outer_printed():
    return outer_cylinder().moved(Location((0.0, 0.0, -P.ZS_END)))


def foot_printed():
    return foot()


def guide_printed():
    return flip_z(top_guide(), P.ZG_PLATE1)                      # plate on the bed


def inner_printed():
    return flip_z(inner_cylinder(), P.ZS_SEAT + P.L_ROD_MIN)     # tip up


PARTS = (  # (name, as printed, footprint radius, colour)
    ("sleeve_mold_foot", foot_printed, P.FOOT_D / 2.0, (0.55, 0.55, 0.60)),
    ("sleeve_mold_outer_cylinder", outer_printed, P.R_SM, (0.20, 0.55, 0.85)),
    ("sleeve_mold_top_guide", guide_printed, P.R_SKIRT_OUT, (0.95, 0.60, 0.15)),
    ("sleeve_mold_inner_cylinder", inner_printed, P.D_ROD / 2.0, (0.70, 0.72, 0.75)),
)
GAP = 8.0


def print_layout():
    out, x = [], 0.0
    for i, (name, make, r, rgb) in enumerate(PARTS):
        x += (r if i else 0.0)
        out.append(finish(make().moved(Location((x, 0.0, 0.0))), name, rgb))
        x += r + GAP
    return out


def gen_step():
    return Compound(children=print_layout(), label="sleeve_mold")


if __name__ == "__main__":
    for s in print_layout():
        bb = s.bounding_box()
        print(f"{s.label:28s} {s.volume / 1000:7.2f} cm3  x {bb.min.X:7.2f}..{bb.max.X:7.2f}  "
              f"y {bb.min.Y:7.2f}..{bb.max.Y:7.2f}  z {bb.min.Z:6.2f}..{bb.max.Z:6.2f}")
    a = assembled()
    names = list(a)
    for i, m in enumerate(names):
        for n in names[i + 1:]:
            x = a[m].intersect(a[n])
            v = sum(s.volume for s in x.solids()) if x else 0.0
            print(f"{m} x {n}: {v:.4f} mm3")
