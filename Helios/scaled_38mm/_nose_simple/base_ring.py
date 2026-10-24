"""The base ring: the one part that stays bolted to the airframe.

It does five jobs and nothing else:

    1. plugs into Mbody's socket           spigot, and the SHOULDER above it
    2. is FASTENED to it                   two radial screw pads inside the spigot
    3. carries the hinge pins              four lugs, two per hinge
    4. carries the bulkhead                an annular seat plus two screw lobes
    5. finishes the airframe's OD          full-diameter collar up to the split

PRINT ORIENTATION
-----------------
Upright, spigot DOWN, on the z = 0 face.  Every downward-facing surface on the
part is then either tiny or ramped at 45 deg or steeper:

    shoulder at z 26.2069     1.34 mm annular overhang, with a 0.3 mm lead-in
    seat underside            replaced by a 45 deg cone, so there is no underside
    lobe underside            same, a 45 deg cone
    lug underside             the fairing ramp, 70 deg from horizontal
    retention pads            no underside at all: they start at z = 0 and grow
                              straight off the bed, and their TOP is the 45 deg
                              cone, which needs nothing
    root posts                no underside either: they grow UP off the collar top
                              and their root flare narrows going up

So it needs no support anywhere, which matters because supports inside a 57 mm
bore are miserable to remove and this bore has to stay dimensionally honest.

AND THAT POSE IS WHY THE ALIGNMENT PINS LIVE HERE
-------------------------------------------------
The two Ø2.0 x 3.0 posts on the collar top are the assembly's only moulded-in
locating pins.  They are on this part rather than on the shells because a shell
prints on its SPLIT FACE: y = SEAM_SETBACK is its bed, so a boss aimed from one
half at the other would need material below the bed, and every way around that
either turns 1042 mm2 of seam face into an overhang or needs a 190 mm separate
spline.  A +z pillar here is free.  Each half drops onto its own post 4.3 deg of
opening before either seam dowel engages, so the halves land on the RING first and
then find each other -- which is the clamping fit the shells could not provide.

WHAT IS DELIBERATELY *NOT* CARRIED OVER FROM THE ORIGINAL CONE
--------------------------------------------------------------
The original `cone_fixed.stl` base has a SOLID 10.48 mm plug across the spigot
with a Ø4.58 tether hole through it.  Both are dropped: the plug would block the
servo bay and the shock cord, and the tether hole belongs to a different
recovery scheme.  The original also carries a 0.3276 x 24.90 mm annular void
wrapped around its spigot -- that is the mating socket's clearance left behind in
CAD, not a feature, and it is not printable as a void anyway.

THE AXIAL DATUM IS THE SHOULDER, NOT THE SPIGOT END
---------------------------------------------------
Mbody's socket is 27.5172 deep and the spigot is 26.2069 long, so the spigot
bottoms out 1.6513 mm AFTER the shoulder lands.  It never gets there: the
shoulder's flat land seats on Mbody's forward rim and that is what sets the
station of everything above.  This is why the shoulder gets a relief cut at its
concave corner -- a printed fillet there would hold the joint open by exactly the
amount that datum is supposed to control.

AND THE DATUM IS WHY THE SCREWS ARE A CLEARANCE FIT IN THE TUBE
---------------------------------------------------------------
The two retention screws are what stop the nose being pulled out or turned, but
they are NOT allowed to set its station -- the shoulder does that.  So the hole
in the airframe is Ø3.2 for an M2.5 screw, deliberately sloppy, and the pilot in
the spigot is the only thing that locates it.  Drilled the other way round -- a
tight hole in the tube and a loose one here -- a hole 0.5 mm too far from the rim
would lever the shoulder off its seat and hold the joint open by 0.5 mm, and
every measurement of the assembled rocket would still look right.
"""

from __future__ import annotations

import math

from build123d import Align, Box, Cone, Plane, Pos, Rot

import nose_build as B
import nose_params as P

LOBE_WEDGE_PAD = 2.0             # the azimuth-limiting box overhangs the lobe
                                 # radially by this much, so the REVOLVE decides
                                 # the inboard face and the underside, not the box
RETAIN_WEDGE_PAD = 2.0           # ditto for the retention pads
SHOULDER_RELIEF = 0.3            # 45 deg, at the CONCAVE corner
SPIGOT_LEAD_IN = 0.5             # 45 deg, on the aft outer edge, for insertion
TOP_CHAMFER = 0.4                # on the collar's top OD edge


def _body():
    """Spigot, shoulder, collar and bore as one revolve.  No seat yet."""
    z_sh = P.Z_SHOULDER
    pts = [
        (P.RING_BORE, 0.0),
        (P.R_SPIGOT - SPIGOT_LEAD_IN, 0.0),
        (P.R_SPIGOT, SPIGOT_LEAD_IN),
        (P.R_SPIGOT, z_sh - SHOULDER_RELIEF),
        (P.R_SPIGOT + SHOULDER_RELIEF, z_sh),
        (P.R_AIRFRAME, z_sh),
        (P.R_AIRFRAME, P.Z_RING_TOP - TOP_CHAMFER),
        (P.R_AIRFRAME - TOP_CHAMFER, P.Z_RING_TOP),
        (P.RING_BORE, P.Z_RING_TOP),
    ]
    return B.revolve_rz(pts)


def _seat():
    """The annular ledge the bulkhead lands on, with a 45 deg cone under it.

    A plain inward flange would present a 2.22 mm downward-facing annulus to an
    upright print.  The cone costs nothing and removes the overhang entirely.
    """
    ramp = P.RING_BORE - P.SEAT_R_IN
    pts = [(P.SEAT_R_IN, P.SEAT_Z1),
           (P.RING_BORE, P.SEAT_Z1),
           (P.RING_BORE, P.SEAT_Z0 - ramp),
           (P.SEAT_R_IN, P.SEAT_Z0)]
    return B.revolve_rz(pts)


def _lobe(theta_deg: float):
    """One screw lobe: a local inward thickening, azimuth-limited.

    Built as a full revolve intersected with a box, rather than as a prism, so
    its inboard face is a true cylinder and its underside a true cone -- the
    printability argument then holds at every azimuth across the lobe, not just
    on its centreline.
    """
    ramp = P.RING_BORE - P.LOBE_R_IN
    ring = B.revolve_rz([(P.LOBE_R_IN, P.SEAT_Z1),
                         (P.RING_BORE, P.SEAT_Z1),
                         (P.RING_BORE, P.LOBE_Z0 - ramp),
                         (P.LOBE_R_IN, P.LOBE_Z0)])
    return ring & B.wedge(theta_deg, P.LOBE_HALF_CHORD,
                          P.LOBE_R_IN - LOBE_WEDGE_PAD, P.RING_BORE + LOBE_WEDGE_PAD,
                          P.LOBE_Z0 - ramp - 1.0, P.SEAT_Z1 + 1.0)


def _retain_pad(theta_deg: float):
    """Internal thickening that gives one retention screw something to thread into.

    The spigot wall is 2.400 mm.  An M2.5 self-tapper wants five or six times that
    in ABS, and there is nowhere outboard to put it -- outboard is the airframe's
    own wall -- so the material goes INBOARD, into the one part of the servo bay
    that is empty at every azimuth: r < 28.72, z < 21, away from +-Y.

    Built as a revolve intersected with a chord box, the same construction as the
    screw lobes, so the inboard face is a true cylinder and the 45 deg top a true
    cone at every azimuth across the pad rather than only on its centreline.

    It starts at z = 0, flush with the spigot's aft face.  That is not laziness: in
    the ring's upright print pose the pad then grows straight off the bed and has no
    downward-facing face anywhere, and the only sloped face it does have -- the top
    cone -- faces up.  The cone also means the shock cord dropping past it meets a
    45 deg ramp instead of a square ledge.
    """
    ramp = P.RING_BORE - P.RETAIN_PAD_R_IN
    ring = B.revolve_rz([(P.RETAIN_PAD_R_IN, 0.0),
                         (P.RING_BORE, 0.0),
                         (P.RING_BORE, P.RETAIN_PAD_Z_TOP),
                         (P.RETAIN_PAD_R_IN, P.RETAIN_PAD_Z_TOP - ramp)])
    return ring & B.wedge(theta_deg, P.RETAIN_HALF_CHORD,
                          P.RETAIN_PAD_R_IN - RETAIN_WEDGE_PAD,
                          P.RING_BORE + RETAIN_WEDGE_PAD,
                          -1.0, P.RETAIN_PAD_Z_TOP + 1.0)


def _retain_pilot(theta_deg: float):
    """One blind screw pilot, plus the 45 deg mouth that lets a hand drill find it.

    The mouth is the whole reason this is not just a cylinder.  The matching hole
    in the airframe gets drilled by hand off a tape measure, and a Ø2.1 pilot 1.6
    mm behind a 1.5 mm tube wall is invisible from outside.  Countersinking its
    mouth to Ø4.1 turns a +-0.2 mm job into a +-1.0 mm one, at the cost of 1.0 mm
    of thread out of 6.9 -- and the cone is also what makes the screw self-centre
    instead of starting crooked and splitting the pad.

    Blind, not through: 1.00 mm of floor stays inboard of it, so no screw tip can
    ever appear in the bay where the servo wire and the shock cord run.
    """
    hole = B.radial_hole(P.RETAIN_PILOT, theta_deg, P.Z_RETAIN,
                         P.RETAIN_PILOT_R0, P.R_SPIGOT + 1.0)
    t = math.radians(theta_deg)
    r0 = P.R_SPIGOT - P.RETAIN_MOUTH_CS
    pl = Plane(origin=(r0 * math.cos(t), r0 * math.sin(t), P.Z_RETAIN),
               x_dir=(0, 0, 1), z_dir=(math.cos(t), math.sin(t), 0))
    cs = pl * Cone(bottom_radius=P.RETAIN_PILOT / 2,
                   top_radius=P.RETAIN_PILOT / 2 + P.RETAIN_MOUTH_CS + 1.0,
                   height=P.RETAIN_MOUTH_CS + 1.0,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    return hole + cs


def _lug_pair(theta_deg: float):
    """The two lugs of one hinge, at |x| LUG_X_IN..LUG_X_OUT, rotated to `theta`."""
    prof = P.lug_profile()
    a = B.prism_yz(prof, P.LUG_X_IN, P.LUG_X_OUT)
    b = B.prism_yz(prof, -P.LUG_X_OUT, -P.LUG_X_IN)
    return Rot(0, 0, theta_deg - 90.0) * (a + b)


def _post(sgn: int):
    """One root alignment post: Ø POST_D x POST_H standing up off the collar top.

    THIS IS THE ONLY MOULDED-IN LOCATING PIN IN THE WHOLE NOSE, and the reason is
    print pose, not preference.  The half shells print on their split faces, so
    y = SEAM_SETBACK is their bed and a boss growing from one half toward the other
    would need material under the bed.  This ring prints upright, spigot down, so a
    +z pillar on its top face is free -- it is the one surface in the assembly that
    can grow a pin.  See the POST_* block in nose_params.py.

    Two of them, at (+POST_X, +POST_Y) and (-POST_X, -POST_Y): one under each half,
    both on the seam meridian, and each the 180 deg image of the other, so half B --
    which IS half A rotated about z -- finds an identical post in an identical place.

    The shank starts 1.0 mm INSIDE the collar so the union has volume to fuse, and
    carries a 45 deg flare at its root.  The flare narrows going up, so it is an
    inward taper and still needs no support.
    """
    shaft = B.cyl_along("z", (sgn * P.POST_X, sgn * P.POST_Y, P.Z_RING_TOP - 1.0),
                        P.POST_D, P.POST_H + 1.0)
    fillet = Pos(sgn * P.POST_X, sgn * P.POST_Y, P.Z_RING_TOP) * Cone(
        bottom_radius=P.POST_D / 2 + P.POST_FILLET, top_radius=P.POST_D / 2,
        height=P.POST_FILLET, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return shaft + fillet


def gen_step():
    s = _body()

    # --- lugs, then the bore.  In that order, so the lugs' inboard faces are cut
    # to the bore instead of guessing where it is.
    for th in (90.0, 270.0):
        t = s + _lug_pair(th)
        B.assert_add(s, t, 900.0, f"hinge lugs at {th} deg")
        s = t

    # --- root posts, ALSO before the bore, and for exactly the same reason: the
    # SHANK stands on the top land with 0.0693 mm to spare (29.79 - 1.0 = 28.79 vs
    # RING_BORE 28.7207), but the 0.3 mm flare around it reaches r 28.49 and so hangs
    # a 1.479 x 0.2307 mm sliver over the bore.  Adding first lets the bore cut trim
    # it, instead of leaving a lip inside a hole that has to stay honest.
    for sgn in (+1, -1):
        t = s + _post(sgn)
        B.assert_add(s, t, 7.0, f"root post sgn={sgn:+d}")
        s = t

    bore = B.cyl_along("z", (0, 0, -1.0), 2 * P.RING_BORE, P.Z_RING_TOP + 2.0)
    t = s - bore
    B.assert_cut(s, t, 400.0, "bore, trimming the lugs to it")
    s = t

    # --- airframe retention: pads AFTER the bore, or the bore would eat them.
    # 1123 mm3 each as built.  Note that is well under the 100.70 mm2 of r-z
    # section times the 11 mm chord: the chord box and the r >= RETAIN_PAD_R_IN
    # cylinder cut each other, so the pad is only 11 mm wide at its outboard face
    # and tapers to nothing at its inboard one.
    for th in P.RETAIN_THETA:
        t = s + _retain_pad(th)
        B.assert_add(s, t, 700.0, f"retention pad at {th} deg")
        s = t
    for th in P.RETAIN_THETA:
        t = s - _retain_pilot(th)
        # Ø2.1 x 6.92 of pilot = 24.0 mm3, plus ~4.3 mm3 of countersink outside it
        B.assert_cut(s, t, 0.8 * (math.pi * (P.RETAIN_PILOT / 2) ** 2
                                  * (P.R_SPIGOT - P.RETAIN_PILOT_R0)),
                     f"retention pilot at {th} deg")
        s = t

    # --- pin bores, one straight through each hinge
    for th in (90.0, 270.0):
        cut = Rot(0, 0, th - 90.0) * B.cyl_along(
            "x", (-P.LUG_X_OUT - 1.0, P.Y_PIN, P.Z_PIN),
            P.PIN_BORE_LUG, 2 * (P.LUG_X_OUT + 1.0))
        t = s - cut
        # two lugs, 4.5 mm each, of a Ø2.1 hole
        B.assert_cut(s, t, 0.8 * math.pi * (P.PIN_BORE_LUG / 2) ** 2 * 2 * P.LUG_W,
                     f"pin bore at {th} deg")
        s = t

    # --- torsion-spring leg seats, one blind hole in each lug's INNER face, facing
    # the knuckle across the pocket.  The matching seat is in the knuckle end face;
    # between them they set the spring's free angle, which has to be the fully-open
    # one.  See nose_params.spring_check().  Note the azimuth is 250 deg and NOT the
    # knuckle's 180: at r = 2.8 the lug is air at 180 because that falls inboard of
    # LUG_Y_IN.  _scratch/_seat_probe.py is the mesh proof, and it is the reason this
    # is a separate constant instead of one shared number.
    y_seat, z_seat = P.torsion_seat_yz(P.TORSION_SEAT_AZ_LUG)
    for th in (90.0, 270.0):
        for sign in (+1, -1):
            # 0.5 mm of overshoot into the pocket, so the mouth is a clean break
            x0 = (P.LUG_X_IN - 0.5 if sign > 0
                  else -P.LUG_X_IN - P.TORSION_SEAT_DEPTH)
            seat = Rot(0, 0, th - 90.0) * B.cyl_along(
                "x", (x0, y_seat, z_seat), P.TORSION_SEAT_D,
                P.TORSION_SEAT_DEPTH + 0.5)
            t = s - seat
            B.assert_cut(s, t, 0.8 * math.pi * (P.TORSION_SEAT_D / 2) ** 2
                         * P.TORSION_SEAT_DEPTH,
                         f"spring leg seat at {th} deg x_sign={sign}")
            s = t

    # --- bulkhead seat and the two screw lobes
    t = s + _seat()
    B.assert_add(s, t, 600.0, "bulkhead seat")
    s = t
    for th in P.LOBE_THETA:
        t = s + _lobe(th)
        B.assert_add(s, t, 250.0, f"screw lobe at {th} deg")
        s = t
    for th in P.LOBE_THETA:
        a = math.radians(th)
        base = (P.R_BULK_SCREW * math.cos(a), P.R_BULK_SCREW * math.sin(a),
                P.SEAT_Z1 - P.BULK_SCREW_DEPTH)
        t = s - B.cyl_along("z", base, P.M2_5_PILOT, P.BULK_SCREW_DEPTH + 0.01)
        B.assert_cut(s, t, 0.8 * math.pi * (P.M2_5_PILOT / 2) ** 2 * P.BULK_SCREW_DEPTH,
                     f"screw pilot at {th} deg")
        s = t

    s.label = "base_ring"
    return s


if __name__ == "__main__":
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"base_ring   vol {s.volume/1000:8.2f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    # The lobes must clear the servo cradle they sit beside.  Sampled over the
    # lobe's whole footprint, not just its four corners: the lobe is a box
    # INTERSECTED with an annulus, and because the box is padded outward by
    # LOBE_WEDGE_PAD the binding inboard boundary is the r = LOBE_R_IN CYLINDER,
    # which bulges inboard of any chord drawn between corners.  Corners alone
    # report 2.31 mm of clearance; the arc's true closest approach is 1.72.
    r_in = P.LOBE_R_IN - LOBE_WEDGE_PAD
    r_out, hc = P.RING_BORE + LOBE_WEDGE_PAD, P.LOBE_HALF_CHORD
    worst, n = 1e9, 240
    for th in P.LOBE_THETA:
        a = math.radians(th)
        for i in range(n + 1):
            u = r_in + (r_out - r_in) * i / n
            for j in range(n + 1):
                sv = -hc + 2 * hc * j / n
                r = math.hypot(u, sv)
                if not (P.LOBE_R_IN - 1e-9 <= r <= P.RING_BORE + 1e-9):
                    continue          # outside the annulus the box is cut against
                x = u * math.cos(a) - sv * math.sin(a)
                worst = min(worst, abs(x) - (P.FIN_X_IN + P.FIN_T))
    assert worst > 1.0, f"a screw lobe comes within {worst:.2f} mm of a cradle fin"
    print(f"  lobe footprint clears the cradle fins by {worst:.2f} mm in x "
          f"(sampled over the arc, not just the corners)")

    # Same treatment for the retention pads, which are the same construction and
    # therefore have the same trap: the binding boundary is the r = RETAIN_PAD_R_IN
    # CYLINDER, and it bulges inboard of any chord between corners.  Sampled here
    # as well as asserted analytically in nose_params, because these two ways of
    # getting the number wrong are independent.
    r_in = P.RETAIN_PAD_R_IN - RETAIN_WEDGE_PAD
    r_out, hc = P.RING_BORE + RETAIN_WEDGE_PAD, P.RETAIN_HALF_CHORD
    worst, n = 1e9, 240
    for th in P.RETAIN_THETA:
        a = math.radians(th)
        for i in range(n + 1):
            u = r_in + (r_out - r_in) * i / n
            for j in range(n + 1):
                sv = -hc + 2 * hc * j / n
                r = math.hypot(u, sv)
                if not (P.RETAIN_PAD_R_IN - 1e-9 <= r <= P.RING_BORE + 1e-9):
                    continue
                x = u * math.cos(a) - sv * math.sin(a)
                worst = min(worst, abs(x) - (P.FIN_X_IN + P.FIN_T))
    assert worst > 1.0, f"a retention pad comes within {worst:.2f} mm of a cradle fin"
    assert P.RETAIN_PAD_Z_TOP < P.Z_ARM_BOT - 5.0, \
        "a retention pad reaches into the latch arm's z band"
    print(f"  retention pads clear the cradle fins by {worst:.2f} mm in x, and stop "
          f"{P.Z_ARM_BOT - P.RETAIN_PAD_Z_TOP:.1f} mm below the latch arm")
    print(f"  retention screws: 2 x M2.5 x {P.RETAIN_SCREW_LEN:.0f} radial at "
          f"{P.RETAIN_THETA[0]:.0f}/{P.RETAIN_THETA[1]:.0f} deg, z {P.Z_RETAIN} = "
          f"{P.Z_RETAIN_BELOW_RIM:.2f} mm below Mbody's forward rim; pilot "
          f"{P.R_SPIGOT - P.RETAIN_PILOT_R0:.2f} deep behind a "
          f"{P.RETAIN_MOUTH_CS} mm 45 deg mouth, {P.RETAIN_PILOT_R0 - P.RETAIN_PAD_R_IN:.2f} "
          f"mm of floor left")
    print(f"  shoulder land r {P.R_SPIGOT + SHOULDER_RELIEF:.4f}..{P.R_AIRFRAME:.4f} "
          f"= {P.R_AIRFRAME - P.R_SPIGOT - SHOULDER_RELIEF:.3f} mm wide, at z "
          f"{P.Z_SHOULDER:.4f}")
