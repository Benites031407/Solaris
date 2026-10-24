"""The latch arm: the only moving part in the whole nose.

A bar on the servo's output shaft.  Latched, both halves' hooks reach UNDER its
two ends and pull up on them, so it holds the halves shut against the springs;
swept 31 deg, its ends pass out from over the hooks and the springs do the rest.
That is the entire mechanism.

The direction is worth stating once, plainly, because getting it backwards is
what the previous version of this design did: the arm is OVER the hooks and the
hooks pull UP.  Every point of a half is inboard of its own hinge pin, so the
hooks RISE as the halves open -- a bar merely sitting on top of them would be
lifted clear by the very motion it is supposed to prevent.

WHY THE ENDS ARE ARCS AND NOT ROUND CAPS
----------------------------------------
The ends are arcs of ARM_CORNER_R centred on the ROTATION AXIS, not semicircular
caps on the bar's centreline.  Two things fall out of that and both matter:

  * The arm's furthest point is ARM_CORNER_R = 22.36 at every angle, so it clears
    the bulkhead seat's SEAT_R_IN bore of 26.90 by 4.54 mm through the whole sweep
    -- one number, not a sweep to check.  Round caps on the 21.74 half-length would
    reach 26.99 and FOUL the bore: they used to leave 0.9 mm at LATCH_ARM_W 8.0, and
    widening the bar for the servo horn spent all of it.  The arcs are now load-
    bearing for clearance and not merely tidier.
  * ARM_CORNER_R is a FROZEN literal and LATCH_ARM_R is derived from it, which is
    backwards from the names and deliberate -- see the note at LATCH_ARM_W in
    nose_params.  It is what let the bar go 8.0 -> 10.50 without moving one digit of
    the hook load path.
  * The swept volume equals the part.  An arc concentric with its own axis of
    rotation sweeps along itself, so nothing outside the static outline ever needs
    clearing.

Constructed as (bar of width LATCH_ARM_W) & (disc of ARM_CORNER_R), which is
exactly that shape and cannot drift from it.

HOW IT DRIVES, AND WHAT CARRIES WHAT
------------------------------------
    torque      the horn's lever, in a 7.6 mm slot across the arm's underside --
                7.6 for a MEASURED 7.2 mm lever, held to full width for all 36.8 mm
                end to end for a 36 mm DOUBLE arm, so the slot runs right through and
                takes both spurs.  The blade tapers to 4.1 at its tips and the slot
                does NOT follow it down: see HORN_SLOT_R.  Flank contact, so the
                driving torque never passes through a
                fastener.  Peak is 9.4 N.mm, re-latching, out of the MG90S's 216;
                releasing is 6.7.  (This used to say 35.7 N.mm, which was the
                release figure back when the springs were believed to be 30 N.mm
                each -- see nose_params.spring_check().)
    retention   the servo's own centre screw, clamping arm + horn + shaft as one
                stack.  Counterbored, because there is only 0.5 mm between the
                arm's top face and the bulkhead and a pan head is 1.5 mm tall.
    latch load  BENDING, and the shaft carries none of it.  Each hook's foot
                pushes UP on the UNDERSIDE at z = Z_ARM_BOT, out at r 20.5..22.14
                (the outboard bound is the ARC at the foot's far edge, not 23.1);
                the bulkhead's thrust pad reacts DOWN on the TOP face at
                z = Z_ARM_TOP, in at r 6.5..9.5.  Opposite faces, opposite
                directions, 8.4 mm apart.  So the arm works as a beam with its
                BOTTOM fibre in tension -- an UPWARD load on an outboard overhang
                puts the far fibre in tension, a diving board inverted; this block
                said TOP for a long while and had it backwards.  It changes no
                dimension, because the print pose lays the layer planes normal to z
                while the bending stress runs along x, so BOTH fibres are in-layer
                (40 MPa) and neither is a bond (11).
                Both ends are loaded at once and symmetrically, so the shaft sees
                no net axial force either way.  1.20 N total -- 2 x
                latch_force_per_half(), 0.598 each -- not the 3.5 this used to say
                nor the 0.64 that replaced it: the springs that fit the hinge
                pocket are far weaker than the first sizing assumed, so the
                thickness here is governed by printability and by the land under
                the hooks, not by the load at all.  nose_verify.py measures the
                x = 0 section off the exported mesh: 36.49 mm2 survives at
                S = 38.08 mm3, 59% of the 88.20 mm2 gross.  That used to read 10.69
                and 4.19 -- 84% gone -- because at LATCH_ARM_W 8.0 the hub recess
                broke clean out through both flanks and the section hung on the floor
                alone.  The wide bar keeps 1.385 mm of flank through x = 0, and a
                factor of 9 in S is most of what widening the bar bought.

MEASURE YOUR HORN FIRST.  HORN_POCKET_DEPTH (5.00, MEASURED) has to equal the hub's
height above the servo case or the centre screw clamps thin air.  The one number
still NOT measured is HORN_BLADE_T, the blade's thickness in z, assumed 1.6 -- and it
is the only load-governed dimension in the part, so if yours is over 2.3 mm say so
before printing.  A thicker blade is worse, not better; nose_params.horn_drive_stress()
explains why.  See the notes in nose_params.

PRINT ORIENTATION
-----------------
Flat, TOP face on the bed.  Building toward -z from there, so the horn pocket
opens upward and needs no support, and the layers lie in the plane of the driving
torque.

The pose is unchanged from when the load was thought to run the other way, but
the reason for it is not, so it is worth re-deriving rather than inherited.  The
two faces that matter are the top (thrust pad, r 6.5..9.5) and the bottom (the
hooks, r 20.5..22.14).  In this pose the top is the first layer on glass -- the
flattest thing an FDM printer makes -- and the bottom is the print's last layer,
a solid top surface.  Iron it if the slicer offers it.

There is no sink on it to worry about, which is what this used to warn of: the
horn pocket OPENS at that face rather than being spanned by it, so nothing is
bridged there at all.  What there is instead is a LAND, and that is the number to
watch.  The pocket's outermost corner is the far end of the LEVER SLOT at
r = hypot(18.4, 3.8) = 18.79 -- not the Ø7.73 hub recess, which is only r 3.87, and
not the r 15.18 this used to claim, which was the 30 mm slot from before the horn
was measured.  The hooks bear from r 20.50 inward-most, so between the pocket's
corner and the bearing patch there is 1.71 mm of full-thickness bar, and every
newton of hook thrust crosses it.  It was 1.93 at HORN_SLOT_W 2.5; widening the
slot to swallow the measured 7.2 mm blade spent 0.22 mm of it, which is the whole
reason HORN_SLOT_W is capped rather than merely clearance-fitted.  Under the hooks
themselves it is solid to the bed.  So both bearing faces come out flat for free and
neither needs a fixture --
but if that slot ever grows, 1.71 mm is what gets spent.

Flipping the arm to put the hooks' face on the glass instead would be a bad
trade: the horn pocket would then open at the bed and the Ø7.73 hub bore plus the
36.8 mm lever slot would have to be bridged over, in the one part whose fit on the
horn has no adjustment in it.
"""

from __future__ import annotations

import math

from build123d import Align, Box, Pos, Rot

import nose_build as B
import nose_params as P


def _blank():
    """The bar, ends trimmed to an arc concentric with the rotation axis."""
    bar = Pos(0, 0, P.Z_ARM_BOT) * Box(
        2 * P.ARM_CORNER_R + 2.0, P.LATCH_ARM_W, P.LATCH_ARM_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    disc = B.cyl_along("z", (0, 0, P.Z_ARM_BOT - 1.0), 2 * P.ARM_CORNER_R,
                       P.LATCH_ARM_T + 2.0)
    return bar & disc


def _horn_pocket():
    """Hub recess plus the lever slot, one uniform depth, open downward.

    Uniform depth rather than a stepped hub-then-slot pocket: the lever's height
    within the hub varies between horns, and a full-depth slot fits any of them.
    It also accepts a 2-arm horn, which is why the slot runs both ways.
    """
    z0 = P.Z_ARM_BOT - 0.01
    h = P.HORN_POCKET_DEPTH + 0.01
    hub = B.cyl_along("z", (0, 0, z0), P.HORN_POCKET_D, h)
    slot = Pos(-P.HORN_SLOT_R, -P.HORN_SLOT_W / 2, z0) * Box(
        2 * P.HORN_SLOT_R, P.HORN_SLOT_W, h, align=(Align.MIN, Align.MIN, Align.MIN))
    return hub + slot


def gen_step():
    s = _blank()

    t = s - _horn_pocket()
    B.assert_cut(s, t, 250.0, "horn pocket")
    s = t

    # --- the shaft screw: clearance through the floor, counterbored from the top
    floor = P.LATCH_ARM_T - P.HORN_POCKET_DEPTH
    t = s - B.cyl_along("z", (0, 0, P.Z_ARM_TOP - floor - 0.01),
                        P.ARM_SHAFT_CLEAR, floor + 0.02)
    B.assert_cut(s, t, 0.8 * math.pi * (P.ARM_SHAFT_CLEAR / 2) ** 2 * floor,
                 "shaft screw clearance")
    s = t
    t = s - B.cyl_along("z", (0, 0, P.Z_ARM_TOP - P.ARM_CB_DEPTH),
                        P.ARM_CB_D, P.ARM_CB_DEPTH + 0.01)
    B.assert_cut(s, t, 0.6 * math.pi * ((P.ARM_CB_D / 2) ** 2
                                        - (P.ARM_SHAFT_CLEAR / 2) ** 2) * P.ARM_CB_DEPTH,
                 "shaft screw counterbore")
    s = t

    s.label = "latch_arm"
    return s


if __name__ == "__main__":
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"latch_arm   vol {s.volume/1000:8.2f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    # The arc ends, not round caps: max radius must be ARM_CORNER_R exactly.
    # Measured over the VERTICES, not the bounding box -- the bbox corner
    # (22.361, 5.250) is at r 22.969 and is not a point of the solid at all.  It said
    # (23.345, 4.000) at r 23.685, and that WAS this arm's bbox corner once: back when
    # LATCH_ARM_R was 23.0 the arc radius was hypot(23.0, 4.0) = 23.3452 and the bar
    # was 8.0 wide.  Pulling LATCH_ARM_R in to 22.0 with the hook, and then widening
    # the bar to 10.50 for the horn, moved it twice without moving this comment.  On
    # this shape the radius is either constant along the arcs or extremal at a
    # vertex, so the vertices settle it.
    r_max = max(math.hypot(v.X, v.Y) for v in s.vertices())
    assert abs(r_max - P.ARM_CORNER_R) < 0.02, \
        f"arm reaches r={r_max:.3f}, expected {P.ARM_CORNER_R:.3f}"
    assert abs(hi[0] - P.ARM_CORNER_R) < 1e-6, (
        f"the bbox reaches x {hi[0]:.4f}, not ARM_CORNER_R {P.ARM_CORNER_R:.4f} -- "
        f"the arc is not what governs the outboard edge")
    assert abs(hi[1] - P.LATCH_ARM_W / 2) < 1e-6, (
        f"the bbox reaches y {hi[1]:.4f}, not LATCH_ARM_W/2 {P.LATCH_ARM_W/2:.4f}")
    assert r_max < P.SEAT_R_IN - 1.0, (
        f"r_max {r_max:.3f} leaves only {P.SEAT_R_IN - r_max:.3f} mm to the seat "
        f"bore {P.SEAT_R_IN}; wanted at least 1.0 so the arm cannot rub the "
        f"bulkhead's own bore at any angle of the sweep")

    # --- the land under the hooks.  The pocket's outermost corner against the
    # bearing patch's innermost radius: the one dimension standing between the
    # lever slot and an arm that folds along its own pocket.
    r_slot = math.hypot(P.HORN_SLOT_R, P.HORN_SLOT_W / 2)
    r_bear = math.hypot(P.HOOK_X_IN, P.TONGUE_Y0)
    print(f"  the lever slot's far corner is r {r_slot:.2f} and the hooks bear from "
          f"r {r_bear:.2f}, so {r_bear - r_slot:.2f} mm of full-thickness land "
          f"carries the thrust off the hooks and into the bar")
    assert r_bear - r_slot > 1.5, (
        f"only {r_bear - r_slot:.2f} mm of land between the lever slot's corner "
        f"(r {r_slot:.2f}) and the hooks' bearing patch (r {r_bear:.2f}) -- the arm "
        f"would hinge along its own pocket instead of carrying the latch load")
    print(f"  max radius {r_max:.3f} = ARM_CORNER_R, so it clears the seat bore "
          f"{P.SEAT_R_IN} by {P.SEAT_R_IN - r_max:.2f} mm at EVERY angle")

    # it must reach OVER the hook's foot far enough to be worth latching.  The
    # governing y is the FAR edge of the foot, TONGUE_Y1: the arm's arc bulges
    # inboard as |y| grows, so the overlap is narrowest at the foot's far edge,
    # not at the split plane.  Evaluating it at LATCH_ARM_W/2 = 5.25 would be
    # reporting a number the hook never sees.
    x_near = math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y0 ** 2)
    x_far = math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y1 ** 2)
    print(f"  reaches x {x_near:.2f} at the foot's near edge (y {P.TONGUE_Y0}) and "
          f"{x_far:.2f} at its far edge (y {P.TONGUE_Y1}), so it sits over the foot "
          f"across x {P.HOOK_X_IN}..{x_far:.2f} = {x_far - P.HOOK_X_IN:.2f} mm at "
          f"worst.  Both bounds come from the ARC of ARM_CORNER_R, not from "
          f"LATCH_ARM_R: _blank()'s bar is cut 2*ARM_CORNER_R + 2 long precisely so "
          f"the arc governs the outboard edge everywhere.")
    # DO NOT quote the footprint as the bearing area.  The foot's top is a ramp, so
    # on a fresh print the arm lands on the flat land alone -- 1.8 mm2, not 4.9.
    y_land = P.TONGUE_Y0 + P.RAMP_LAND
    a_land = (math.sqrt(P.ARM_CORNER_R ** 2 - y_land ** 2) - P.HOOK_X_IN) * P.RAMP_LAND
    a_full = (x_far - P.HOOK_X_IN) * (P.TONGUE_Y1 - P.TONGUE_Y0)
    f = P.latch_force_per_half()
    print(f"  it bears on the FLAT land only, y {P.TONGUE_Y0}..{y_land} = "
          f"{a_land:.2f} mm2 at {f / a_land:.3f} MPa; the whole {a_full:.2f} mm2 "
          f"footprint ({f / a_full:.3f} MPa) comes in only once the ramp beds in")
    assert x_far > P.HOOK_X_IN + 1.5, (
        f"the arm only overlaps the foot by {x_far - P.HOOK_X_IN:.2f} mm -- not "
        f"enough ledge to trust against print tolerance")
    assert P.TONGUE_Y1 < P.LATCH_ARM_W / 2, (
        f"the foot reaches y {P.TONGUE_Y1} but the arm is only "
        f"{P.LATCH_ARM_W / 2} wide either side of the split plane -- part of the "
        f"foot would hang out past the arm's edge with nothing above it")

    floor = P.LATCH_ARM_T - P.HORN_POCKET_DEPTH
    print(f"  {floor:.2f} mm of floor over the horn pocket, of which "
          f"{floor - P.ARM_CB_DEPTH:.2f} mm under the screw head")
    assert floor - P.ARM_CB_DEPTH > 1.0, "too little material under the screw head"
    # the head must not stand proud into the 0.5 mm gap under the bulkhead
    assert P.ARM_CB_DEPTH >= 1.5, "counterbore must swallow a pan head"
    print(f"  counterbore {P.ARM_CB_D} x {P.ARM_CB_DEPTH} keeps the screw head "
          f"below the top face, which clears the bulkhead by "
          f"{P.Z_BULK_BOT - P.Z_ARM_TOP:.1f} mm")

    # --- the two walls the pocket leaves, and the only load-governed stress here.
    # Reported together because they are the same wall seen two ways: it has to be
    # thick enough to PRINT (WALL_MIN, a slicer rule) and thick enough to CARRY (the
    # flank root against a stalled servo, an anisotropy rule).  At LATCH_ARM_W 8.0
    # the 7.6 slot the measured blade needs would have left 0.200 mm and failed both.
    w_slot = (P.LATCH_ARM_W - P.HORN_SLOT_W) / 2
    w_hub = (P.LATCH_ARM_W - P.HORN_POCKET_D) / 2
    hd = P.horn_drive_stress()
    print(f"  the pocket leaves {w_hub:.4f} mm either side of the Ø{P.HORN_POCKET_D} "
          f"hub recess and {w_slot:.4f} mm either side of the {P.HORN_SLOT_W} slot, "
          f"against WALL_MIN {P.WALL_MIN} -- the hub is the governing wall")
    assert min(w_slot, w_hub) >= P.WALL_MIN - 1e-9, (
        f"the pocket leaves a {min(w_slot, w_hub):.4f} mm wall, under WALL_MIN "
        f"{P.WALL_MIN}")
    print(f"  that flank sees {hd['resultant']:.2f} MPa at its root with the servo "
          f"STALLED at {hd['torque']:.0f} N.mm -- {hd['fos']:.2f}x on "
          f"{P.SIGMA_ABS_LAYER} MPa interlaminar, which is what the root plane is in "
          f"this print pose.  Assumes HORN_BLADE_T {P.HORN_BLADE_T} mm, STILL "
          f"UNMEASURED, and a thicker blade is worse")
