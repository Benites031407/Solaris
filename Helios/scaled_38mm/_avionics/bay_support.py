"""The avionics SUPPORT: the half of the old one-piece sled that stays in the rocket.

Head ring, shell, trough opening and screw bosses -- all exactly as bay_sled.py had
them -- plus the three features that make the bay serviceable:

    two RAILS          standing proud of the bore, forming a pocket the plate slides
                       down.  Full length for the lower one, stopping short of the
                       bosses for the upper one.
    the STOP           the pocket filled aft of s 205, so the plate cannot pass
                       through and shoot out the far end.  This is the one-way part.

The plate is bay_plate.py and it goes in from the FORWARD end, tail first, already
populated.  Nothing about the support's installation changed: it still seats its
D61.20 crown in the airframe's depth-stop bead and is still retained by two M3
self-tappers at s 201.5 -- the same two screws now also catch the plate, so the
split added no holes to the airframe.

WHY THE RAILS STAND PROUD INSTEAD OF BEING GROOVES IN THE WALL
--------------------------------------------------------------
Because the head is a COMPLETE ring with a bore of r 27.45 and the plate has to fit
through it.  A groove cut into the shell puts the plate's edges at r > 27.45, i.e.
wider than the hole they have to pass, and thins a 2.0 mm wall below WALL_MIN into
the bargain.  Rails standing inward invert both problems at once: the plate is
NARROWER than the bore (r 27.05, 0.40 mm of clearance all round) and the wall is
never touched.  This is the constraint that picked the architecture, and it is
checked in bay_params.self_check(), not just asserted here.

PRINT ORIENTATION: unchanged -- forward end DOWN, axis = build Z, no support
---------------------------------------------------------------------------
The rails are constant cross-section along z, so like the shell and the old deck
they have no downward-facing surface at all: their forward faces are on the bed.
The ONE new downward-facing surface the slide adds is the stop's forward face at
s 205, and it is deliberately kept inside the rails' radial band so that it lands on
the lower rail below it and the shell wall outboard of it -- no point of it is more
than 1.40 mm from one of the two.  Drawn across the full chord instead (which looks
stronger) it would bridge some 52 mm of open bore, against BRIDGE_MAX 6.0.

The bed face is now the head's annulus (574.5 mm2) plus four small rail-end arcs
rather than the annulus plus a 106 mm2 deck section -- less first-layer area than
before, which is worth knowing before the first print and is printed below.

Run:  python bay_support.py
Export: PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \\
            -o out/bay_support.step --stl bay_support.stl bay_support.py
"""

from __future__ import annotations

import math

import bay_build as B
import bay_params as P

TAIL_LEAD_IN = 0.5          # 45 deg on the tail's outer edge, the leading edge
                            # during insertion
BAND_OVER = 1.0             # how far the clipping cylinders of a rail overshoot it
                            # in z, so no cylinder end face is ever coplanar with
                            # the box face that is actually meant to bound it


def _band_arc(x0: float, x1: float, z0: float, z1: float, sign: float,
              r_i: float = P.R_RAIL_I, r_o: float = P.R_RAIL_O):
    """One rail arc: the x-slab x0..x1 intersected with the annulus r_i..r_o.

    A rail has to follow the bore, so it cannot be a box -- a box of the right
    thickness either cuts inside the arc at its corners or stands proud of it in the
    middle.  Intersecting an x-slab with an annulus gives the arc for free and, more
    usefully, gives its area in closed form as a difference of two slab_area() calls,
    which is what B.add insists on knowing in advance.

    The slab crosses the annulus in TWO places, at +y and -y, and they are separate
    solids.  Rather than hand a two-solid compound to a fuse, each is built on its
    own: `sign` picks which, and the y face that selects it is placed at half the
    arc's own minimum y, i.e. inside the annulus's HOLE, where it bounds nothing.
    """
    x_out = max(abs(x0), abs(x1))
    if x_out >= r_i:
        raise ValueError(
            f"a rail over x {x0}..{x1} reaches |x| {x_out} which is outside the "
            f"annulus's inner radius {r_i} -- the slab no longer crosses it in two "
            f"places and this construction does not describe the result")
    y_gap = math.sqrt(r_i ** 2 - x_out ** 2)      # the arcs are outboard of this
    y_lo, y_hi = 0.5 * y_gap, r_o + 1.0
    if sign < 0.0:
        y_lo, y_hi = -y_hi, -y_lo
    box = B.box_between(x0, x1, y_lo, y_hi, z0, z1)
    base = (0.0, 0.0, z0 - BAND_OVER)
    length = (z1 - z0) + 2 * BAND_OVER
    outer = B.cyl_along("z", base, 2 * r_o, length)
    inner = B.cyl_along("z", base, 2 * r_i, length)
    return B.one_solid((box & outer) - inner,
                       f"rail arc x {x0:.2f}..{x1:.2f} at y {'+' if sign > 0 else '-'}")


def _band_area(x0: float, x1: float, r_i: float, r_o: float) -> float:
    """Cross-section area of ONE arc of the band -- half the two-sided total."""
    return 0.5 * (B.slab_area(r_o, x0, x1) - B.slab_area(r_i, x0, x1))


def _body():
    """Head and shell: one revolve, and that is all it is now.

    bay_sled.py's version added the deck here as a chord plate.  The deck has become
    a separate part, so what is left is the profile that was always the interesting
    bit -- radius only ever DECREASES going aft (30.60 -> 29.45), so the crown
    overhangs nothing and its forward face is the bed.
    """
    pts = [
        (P.R_SHELL_I, P.S_HEAD_FWD),
        (P.R_CROWN, P.S_HEAD_FWD),                    # the pilot land, r 30.60...
        (P.R_CROWN, P.S_CROWN),                       # ...to the crown circle
        (P.R_SHELL_O, P.S_HEAD_AFT),                  # 34.4 deg away from the flank
        (P.R_SHELL_O, P.S_TAIL - TAIL_LEAD_IN),
        (P.R_SHELL_O - TAIL_LEAD_IN, P.S_TAIL),
        (P.R_SHELL_I, P.S_TAIL),
    ]
    return B.one_solid(B.revolve_rz(pts), "head + shell revolve")


def _open_the_trough(s):
    """Cut everything with x > X_OPEN, aft of the head.  This is what makes it a C."""
    cutter = B.box_between(P.X_OPEN, B.BIG, -B.BIG, B.BIG, P.S_HEAD_AFT, B.BIG)
    # Predicted exactly, and the band is TIGHT where bay_sled's had to be loose: with
    # the deck gone there is nothing but shell in x > X_OPEN, so the only error left
    # is the sliver the tail lead-in trims off the top of the cut region -- 10.6 mm3
    # of 29000, i.e. 0.04%.
    area = (B.slab_area(P.R_SHELL_O, P.X_OPEN, P.R_SHELL_O)
            - B.slab_area(P.R_SHELL_I, P.X_OPEN, P.R_SHELL_I))
    want = area * (P.S_TAIL - P.S_HEAD_AFT)
    return B.cut(s, cutter, 0.995 * want, 1.001 * want, "trough opening")


def _bosses(s):
    """The two screw bosses, at tube theta 90 and 270.  Unchanged from bay_sled.py.

    The boss stops at r = R_SHELL_I + FUSE_MERGE, INSIDE the wall, rather than
    running out to the shell's OD.  Drawn out to the OD it shares a cylindrical face
    with the shell over 20 mm of length, and that union produced a solid that
    measured correctly, passed its volume check, survived two further operations and
    was then deleted by a rib -- see bay_build.one_solid().  Ending inside the wall
    also means the boss never re-fills the sliver of shell the trough's opening cut
    away between x = 4.0 and the sector's own x = 4.61, so the opening stays a clean
    plane for its whole length.  The screw does not care: at theta 90 the material
    along its axis is continuous from r 23.0 to the OD either way.

    The aft end deliberately OVERSHOOTS past S_TAIL and is trimmed off afterwards by
    one planar cut, so the boss and the shell never present coplanar end faces to a
    fuse either.
    """
    over = 1.0
    pts = [
        (P.R_BOSS_I, P.S_BOSS_0),                     # full depth from here aft
        (P.R_SHELL_I + P.FUSE_MERGE, P.S_BOSS_RAMP),  # the ramp's foot, in the wall
        (P.R_SHELL_I + P.FUSE_MERGE, P.S_TAIL + over),
        (P.R_BOSS_I, P.S_TAIL + over),
    ]
    frac = 2.0 * P.BOSS_HALF_ANG / 360.0
    ring = math.pi * ((P.R_SHELL_I + P.FUSE_MERGE) ** 2 - P.R_BOSS_I ** 2) * frac
    for th in P.SCREW_THETA:
        s = B.add(s, B.sector_rz(th, P.BOSS_HALF_ANG, pts),
                  0.9 * ring * (P.S_TAIL + over - P.S_BOSS_0),
                  f"screw boss at {th:.0f} deg")
    trim = B.box_between(-B.BIG, B.BIG, -B.BIG, B.BIG, P.S_TAIL, B.BIG)
    want = 2.0 * ring * over
    return B.cut(s, trim, 0.98 * want, 1.02 * want, "trim the boss overshoot")


def _rails(s):
    """The pocket: a lower rail under the plate and an upper rail over it.

    The lower one runs the whole length, because it is what the plate rests on and
    because it is also the stop's floor at the aft end.  The upper one has to stop at
    s 188: its top face is at x -3.70 and the bosses' x-band is |x| <= 4.372, so run
    aft it would fuse into both bosses -- harmless metal that destroys the closed-form
    volume prediction in _bosses() and puts rail material on the exact ray
    bay_verify.py uses to prove a boss is a local sector and not a ring.  The 16.5 mm
    of upper capture that costs is the 16.5 mm where the two retention screws are.
    """
    for x0, x1, z1, lbl in (
            (P.RAIL_L_X_BOT, P.POCKET_X_BOT, P.S_TAIL, "lower"),
            (P.POCKET_X_TOP, P.RAIL_U_X_TOP, P.S_RAIL_U_1, "upper")):
        # New material is only the part INSIDE the bore: from r 26.05 out to 27.45 is
        # air the rail fills, and from 27.45 to 27.95 is the shell it is buried in.
        want = _band_area(x0, x1, P.R_RAIL_I, P.R_SHELL_I) * (z1 - P.S_RAIL_0)
        for sign in (1.0, -1.0):
            s = B.add(s, _band_arc(x0, x1, P.S_RAIL_0, z1, sign),
                      0.99 * want,
                      f"{lbl} rail at y {'+' if sign > 0 else '-'}, "
                      f"x {x0:.2f}..{x1:.2f}, s {P.S_RAIL_0:.2f}..{z1:.1f}")
    return s


def _stop(s):
    """THE HARD STOP: the pocket filled from s 205 to the tail.

    Only over the rails' radial band, and only from POCKET_X_BOT - FUSE_MERGE up, so
    that it overlaps the lower rail volumetrically instead of sitting on its top face
    -- the same rule every other fused feature here obeys, and the one that turned a
    plausible volume into a shattered solid the last time it was broken.

    It is what makes this a one-way slide.  The plate goes in from the forward end
    and is stopped here; it cannot continue and drop out of the aft end, which is
    209 mm down a 38 mm tube and unreachable.  Forward retention is the two M3s
    through the bosses into the plate's lugs -- see bay_plate.py.
    """
    x0, x1 = P.POCKET_X_BOT - P.FUSE_MERGE, P.POCKET_X_TOP
    # The strip x0..POCKET_X_BOT is already the lower rail, so the material this adds
    # is only what fills the pocket proper, r 26.05..27.45.
    want = (_band_area(P.POCKET_X_BOT, P.POCKET_X_TOP, P.R_RAIL_I, P.R_SHELL_I)
            * (P.S_TAIL - P.S_STOP))
    for sign in (1.0, -1.0):
        s = B.add(s, _band_arc(x0, x1, P.S_STOP, P.S_TAIL, sign), 0.9 * want,
                  f"aft stop at y {'+' if sign > 0 else '-'}, "
                  f"s {P.S_STOP:.1f}..{P.S_TAIL:.1f}")
    return s


def _holes(s):
    """The two screw pilots.  The plate's own lug pilots are in bay_plate.py."""
    for th in P.SCREW_THETA:
        # Bored from FUSE_MERGE INSIDE the boss's inner face, not from the face
        # itself.  Started at exactly R_BOSS_I the cut lays a circular seam on the
        # very cylinder it begins on, and OCCT tessellated that into 8 non-manifold
        # faces at r 23.0: one valid solid, correct volume, and an STL that is not
        # watertight -- so every containment probe in bay_verify.py was formally
        # void.  Same coincident-face rule as one_solid()'s, applied to a CUT: the
        # cutter must overlap volumetrically at both ends, not stop on a face.
        #
        # The extra 0.5 mm is in the trough's own air: at theta 90 the pilot's axis
        # is the +y axis at x = 0, and the nearest material of this part inboard of
        # r 23.0 is the upper rail at |x| >= 3.70 -- which also ends 13 mm forward of
        # here.  So it removes nothing, and the band below still bounds the real
        # material: one diameter the whole way, a self-tapper's pilot, the thread
        # forming in the 6.45 mm behind the OD.
        want = (math.pi * (P.SCREW_PILOT_D / 2) ** 2
                * (P.R_SHELL_O - P.R_BOSS_I))
        s = B.cut(s, B.radial_hole(P.SCREW_PILOT_D, th, P.S_SCREW,
                                   P.R_BOSS_I - P.FUSE_MERGE, P.R_SHELL_O + 1.0),
                  0.92 * want, 1.08 * want, f"screw pilot at {th:.0f} deg")
    return s


def gen_step():
    s = _body()
    s = _open_the_trough(s)
    s = _bosses(s)
    s = _rails(s)
    s = _stop(s)
    s = _holes(s)
    s.label = "bay_support"
    return s


def pocket_keepout(z0: float, z1: float):
    """The volume the plate's chord section needs, over stations z0..z1.

    Out to the BORE, not to R_PLATE: within the pocket's x-band the support must be
    empty all the way to r 27.45, because the plate's 0.40 mm of radial clearance is
    clearance, not somewhere the support may put material.
    """
    box = B.box_between(P.POCKET_X_BOT, P.POCKET_X_TOP,
                        -P.R_SHELL_I - 1.0, P.R_SHELL_I + 1.0, z0, z1)
    return box & B.cyl_along("z", (0.0, 0.0, z0 - BAND_OVER), 2 * P.R_SHELL_I,
                             (z1 - z0) + 2 * BAND_OVER)


def vol(shape) -> float:
    """Volume of a boolean result that may be EMPTY or may be SEVERAL solids.

    Both are ordinary here and the first version of this function read them the same
    way -- as zero -- which is harmless for one and a catastrophe for the other.
    build123d hands back a bare ShapeList when an intersection comes out as more than
    one lump, and a ShapeList has no `.volume`; catching that AttributeError and
    returning 0.0 turns "the two parts collide in two places" into "they do not
    collide".  EVERY obstruction in this bay is a symmetric PAIR -- the rails, the
    bosses, the stop, the lugs all come in +y and -y -- so that is not a corner case,
    it is the normal case, and it made both `open_v` below and bay_plate.py's three
    sector checks unable to report the interference they exist to find.

    So: sum over the solids, which reads a single solid, a compound and a ShapeList
    alike, and gives 0.0 for a result that contains no solid at all (an empty
    boolean, or a face where two shapes merely touch -- which encloses no volume and
    is correctly not an interference).
    """
    if shape is None:
        return 0.0
    solids = getattr(shape, "solids", None)
    if solids is None:
        return 0.0
    return sum(float(s.volume) for s in solids())


if __name__ == "__main__":
    P.self_check()
    print()
    s = gen_step()
    lo, hi = B.bbox(s)
    mass = s.volume * P.ABS_RHO
    print(f"bay_support vol {s.volume/1000:8.2f} cm3   mass {mass:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    # The head must reach past the bead throat; nothing else may.
    r_max = max(math.hypot(v.X, v.Y) for v in s.vertices())
    print(f"  max radius anywhere: {r_max:.4f} (the crown, r {P.R_CROWN:.2f})")
    assert abs(r_max - P.R_CROWN) < 1e-6, \
        f"something reaches r {r_max:.4f}, past the crown's {P.R_CROWN:.2f}"
    aft = s - B.box_between(-B.BIG, B.BIG, -B.BIG, B.BIG, -B.BIG, P.S_HEAD_AFT)
    r_aft = max(math.hypot(v.X, v.Y) for v in aft.vertices())
    print(f"  max radius aft of the head: {r_aft:.4f}, against the bead's "
          f"{P.R_BEAD_THROAT:.3f} ({P.R_BEAD_THROAT - r_aft:+.3f} mm)")
    assert r_aft < P.R_BEAD_THROAT, \
        f"the support reaches r {r_aft:.4f} aft of its head and cannot pass the bead"

    # THE SLIDE, PROVED ON THE SOLID RATHER THAN ON THE PARAMETERS.  Everything above
    # about rails and clearances is arithmetic in bay_params; these two lines are the
    # geometry itself answering the question.  The pocket must be EMPTY over the
    # plate's whole travel, and it must be BLOCKED aft of the stop -- one number each,
    # and they are the two halves of "it slides in, one way".
    open_v = vol(s & pocket_keepout(P.S_HEAD_FWD, P.S_STOP))
    print(f"  pocket, s {P.S_HEAD_FWD:.2f}..{P.S_STOP:.1f}: "
          f"{open_v:.3f} mm3 of obstruction")
    assert open_v < 1e-6, (
        f"the pocket is not clear: {open_v:.3f} mm3 of the support stands in the "
        f"plate's path forward of the stop, so the plate cannot go home")
    dz = P.S_TAIL - P.S_STOP
    stop_v = vol(s & pocket_keepout(P.S_STOP, P.S_TAIL))
    print(f"  stop, s {P.S_STOP:.1f}..{P.S_TAIL:.1f}: {stop_v:.1f} mm3 blocking the "
          f"pocket ({stop_v/dz:.2f} mm2 of section)")
    assert stop_v / dz > 5.0, (
        f"the stop blocks only {stop_v/dz:.2f} mm2 of the pocket's section -- the "
        f"plate would slide past it and out of the tube's aft end")

    # What the plate actually BEARS on is smaller than the section above: only the
    # part of the stop that the plate's own chord reaches, which is RAIL_ENGAGE deep.
    bear = (B.slab_area(P.R_PLATE, P.DECK_X_BOT, P.DECK_X_TOP)
            - B.slab_area(P.R_RAIL_I, P.DECK_X_BOT, P.DECK_X_TOP))
    print(f"  the plate's aft face bears on {bear:.2f} mm2 of it: "
          f"{P.F_BOOST_N/bear:.2f} MPa on boost")
    assert P.F_BOOST_N / bear < 10.0, (
        f"the plate bears {P.F_BOOST_N/bear:.1f} MPa on the stop, which is a "
        f"quarter of what ABS takes -- deepen RAIL_ENGAGE or lengthen the stop")

    # The first layer, which is what actually decides whether this stays on the bed.
    head_a = math.pi * (P.R_CROWN ** 2 - P.R_SHELL_I ** 2)
    rail_a = 2.0 * (_band_area(P.RAIL_L_X_BOT, P.POCKET_X_BOT,
                               P.R_RAIL_I, P.R_RAIL_O)
                    + _band_area(P.POCKET_X_TOP, P.RAIL_U_X_TOP,
                                 P.R_RAIL_I, P.R_RAIL_O))
    print(f"  first layer {head_a + rail_a:.1f} mm2 = head annulus {head_a:.1f} + "
          f"4 rail ends {rail_a:.1f}")

    assert abs(mass - P.M_SUPPORT) < 1.0, (
        f"bay_params.M_SUPPORT says {P.M_SUPPORT:.1f} g and the solid weighs "
        f"{mass:.1f} g")
