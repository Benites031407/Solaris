"""The seam dowel: Ø3.0 x 6.5, four off.  BUY IT IF YOU CAN; print it if you cannot.

WHY THIS FILE EXISTS AT ALL
---------------------------
The four seam locators are loose rods, not moulded pins, and that is forced by the
print pose: a half prints on its SPLIT FACE, so y = SEAM_SETBACK is its bed and a boss
growing from one half toward the other would need material below the bed.  Only
recesses are printable on a seam face.  So both faces get sockets and something goes
between them.  (The ONE moulded pin in this design is on the base ring -- see the POST_*
block in nose_params.py -- because the ring prints upright and its collar top can grow
a +z pillar for free.)

The something should be steel: Ø3.0 h9 dowel pin, a 3 mm drill blank, silver steel, or
3 mm brass rod out of the same bag the mandrel came from.  It is stiffer than anything
printed, it is round, and it costs nothing.  This file is the fallback for a builder who
has sockets and no rod, and it exists because ONE NUMBER SAYS IT IS LEGAL:

    DOWEL_BORE       3.30                 the socket
    DOWEL_D          3.00 nominal         0.15 mm of slack per side
    largest that still WITHDRAWS  3.2492  computed by dowel_withdrawal() over both
                                          sockets and the whole 100 deg of opening

so a printed pin has 0.2492 mm of diameter to be wrong in and still let the half open.
That is 1.2 LAYER_H of diameter -- 0.125 mm a side -- and about 8x the 0.03 mm a tuned
ABS printer holds on a 3 mm peg, which is why printing these is a fallback and not a
compromise.  At the old DOWEL_LEN of 8.0 the same sweep allowed only Ø3.1328, i.e.
0.133 mm; shortening the rod to 6.5 is what bought the extra 0.116 mm, and it is the
reason this file could be written.

WHAT THE LENGTH IS DOING
------------------------
6.5 mm, and every one of the three numbers below is a consequence, not a choice:

    2.00 mm proud of half A's seam face, so the rod is visible and can be pushed out
    1.70 mm of engagement in half B, once the 0.30 mm total seam gap is paid for
    2.80 mm of clearance to half B's socket floor, so the rod NEVER bottoms

The last one is the one that matters.  A rod that bottoms in both sockets sets the seam
gap itself, fighting the latch for control of the joint; one that floats lets the two
faces close on each other and only stops them SLIDING.  That is the whole job.

PRINT IT
--------
Standing on end, all four at once, no support -- it is a cylinder on the bed.  On end
rather than lying down for two reasons: lying down, a Ø3.0 cylinder is elephant-footed
on the first layer and out of round for the rest of it, and the layer lines then run
along the pin so the shear plane at the seam IS a layer bond (11 MPa) instead of
crossing them (40 MPa).  Standing up, the seam load is in-layer shear.

0.3 x 45 deg on both ends, which is what makes it findable: the chamfer is bigger than
the 0.15 mm of radial slack, so a skewed rod is steered in rather than caught on the
socket's edge.  Sand the first layer flat before use -- an elephant foot on the end that
goes in is the one defect the chamfer cannot fix.

Run:  python seam_pin.py
Export: python ~/.claude/skills/cad/scripts/step -o out/seam_pin.step \
            --stl seam_pin.stl seam_pin.py
"""

from __future__ import annotations

import math

import nose_build as B
import nose_params as P

CHAMFER = 0.3            # > the 0.15 mm of radial slack, so it steers instead of catching
QTY = 4                  # two sockets per seam meridian, two meridians


def gen_step():
    s = B.cyl_along("z", (0.0, 0.0, 0.0), P.DOWEL_D, P.DOWEL_LEN)
    plain = math.pi * (P.DOWEL_D / 2) ** 2 * P.DOWEL_LEN
    assert abs(s.volume - plain) < 1e-6, \
        f"the body came out {s.volume:.4f} mm3, not the {plain:.4f} a Ø{P.DOWEL_D} x " \
        f"{P.DOWEL_LEN} cylinder is"

    # Both ends, cut rather than modelled, so the two are guaranteed identical and the
    # body stays one number.
    #
    # THE CUTTER IS THE RING, NOT THE CONE, and that is the easy thing to get backwards
    # here.  A Cone() from r at the end face to r - CHAMFER inboard looks like the
    # chamfer, and subtracting it removes exactly the material a chamfer KEEPS -- the
    # frustum, 1.725 mm3 an end, leaving a tube with a countersunk hole in it.  What has
    # to go is the annulus OUTSIDE that taper: 0.3958 mm3 an end.  So the cutter is a
    # revolve of the removed quad, padded 0.5 mm outboard so the difference breaks out
    # cleanly instead of landing on the pin's own cylindrical face.
    r, c = P.DOWEL_D / 2, CHAMFER
    for z0, up in ((0.0, True), (P.DOWEL_LEN, False)):
        z_in = z0 + c if up else z0 - c        # where the taper meets full diameter
        cut = B.revolve_rz([(r - c, z0), (r + 0.5, z0), (r + 0.5, z_in), (r, z_in)])
        t = s - cut
        # a c-tall slab of the cylinder less the frustum inside it, which reduces to
        # pi c^2 (3r - c) / 3 = 0.3958 mm3
        B.assert_cut(s, t, 0.9 * math.pi * c ** 2 * (3 * r - c) / 3,
                     f"end chamfer at z {z0}")
        s = t

    s.label = "seam_pin"
    return s


if __name__ == "__main__":
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"seam_pin    vol {s.volume/1000:8.4f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.2f} g ABS each, x{QTY} = "
          f"{QTY*s.volume/1000*P.ABS_DENSITY:.2f} g")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    plain = math.pi * (P.DOWEL_D / 2) ** 2 * P.DOWEL_LEN
    assert abs(hi[2] - lo[2] - P.DOWEL_LEN) < 1e-9, "the pin is not DOWEL_LEN long"
    assert abs(hi[0] - lo[0] - P.DOWEL_D) < 1e-9, "the pin is not DOWEL_D across"
    assert s.volume < plain, "the chamfers removed nothing"
    print(f"  Ø{P.DOWEL_D} x {P.DOWEL_LEN} with {CHAMFER} x 45 deg both ends: "
          f"{plain:.2f} mm3 of cylinder less {plain - s.volume:.2f} of chamfer")

    # --- THE CHECK THAT MAKES THIS PART LEGAL.  Re-derived from the sweep, not copied:
    # the largest ACTUAL diameter that still withdraws from both sockets over the whole
    # opening, given the 0.15 mm of nominal slack the fit already spends.
    avail = (P.DOWEL_BORE - P.DOWEL_D) / 2
    worst = max(avail + P.dowel_withdrawal(z0)[0] for z0 in P.DOWEL_Z)
    d_max = P.DOWEL_BORE - 2 * worst
    assert d_max >= P.DOWEL_D + 0.20, (
        f"a printed pin has only {d_max - P.DOWEL_D:.4f} mm of oversize before the "
        f"halves stop opening -- buy rod instead")
    print(f"  the sweep allows up to Ø{d_max:.4f} before a half stops opening, so a "
          f"printed pin may be {d_max - P.DOWEL_D:.4f} mm fat -- about "
          f"{(d_max - P.DOWEL_D)/P.LAYER_H:.1f} layers of diameter, or "
          f"{(d_max - P.DOWEL_D)/0.03:.0f}x what a tuned printer misses by")
    assert CHAMFER > avail, (
        f"the {CHAMFER} mm chamfer is smaller than the {avail:.2f} mm of radial slack, "
        f"so a skewed pin catches the socket edge instead of being steered in")

    # --- and the three length consequences, so the docstring cannot drift from the file
    proud = P.DOWEL_LEN - P.DOWEL_DEPTH
    engaged = proud - 2 * P.SEAM_SETBACK
    floor = P.DOWEL_DEPTH - engaged
    print(f"  bottomed in half A: {proud:.2f} mm proud, {engaged:.2f} engaged in B "
          f"after the {2*P.SEAM_SETBACK:.2f} mm seam gap, {floor:.2f} mm off B's socket "
          f"floor -- so it locates the seam in shear and never sets its gap")
    assert floor > 1.0, "the pin can bottom in both sockets and set the seam gap itself"
    print(f"  print {QTY} standing on end; layer lines then CROSS the seam's shear "
          f"plane ({P.SIGMA_ABS:.0f} MPa in-layer) instead of lying in it "
          f"({P.SIGMA_ABS_LAYER:.0f} MPa)")
