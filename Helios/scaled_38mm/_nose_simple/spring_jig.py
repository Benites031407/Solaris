"""The printed jig that makes the four torsion springs -- one plate, two stations.

WHY THIS FILE EXISTS
--------------------
The springs are the only part of this nose that is neither printed nor bought off a
shelf, and that was the one open objection to the design.  The answer is not a
catalogue part -- nose_params.py's "WHY THIS IS WOUND AND NOT BOUGHT" block gives the
three reasons no stock torsion spring fits, and correcting the 2 pi in TORSION_RATE
did not change any of them:

    1. the coil must clear a Ø2.0 pin AND stay inside POCKET_FREE_R, which boxes
       D_mean into 3.10..4.30 mm -- the very fine end of any stock range;
    2. TORSION_GAP is 5.5 mm, so n*d < 5.5 -- a stock Ø0.5 spring with the usual
       15..20 coils is three times too long;
    3. the killer -- stock torsion springs have STRAIGHT TANGENTIAL legs, and bending
       one to reach an axial seat at TORSION_LEG_R shifts its tail by
       arccos((D_mean/2)/TORSION_LEG_R).  The two legs leave the coil in opposite
       helical senses, so the two shifts ADD to about 100 deg of free-angle error,
       which no stock free-angle tolerance absorbs.

So the answer to "generally available" is at the level of MATERIAL AND TOOLING, not of
finished part, and everything it needs is already in the drawer:

    wire      Ø0.50 mm ASTM A228 music wire.  This is a plain steel guitar string:
              .020 in = 0.508 mm, inside the acceptance box.  One 1 m string makes six
              springs and four are needed.
    mandrel   a Ø3.0 mm dowel pin, drill blank, silver-steel rod or plain drill shank.
    gauge pin the same Ø2.0 stock as the hinge pin itself.
    tools     side cutters and one pair of pliers.
    jig       this part, printed once, no supports.

AND THE ACCEPTANCE BOX IS THE POINT
-----------------------------------
Nothing here is made to a tolerance, because the box is enormous:

    n        7.472, 8.472, 9.472 or 10.472 coils -- a three-coil window
    D_mean   3.20 .. 4.30 mm -- 1.1 mm wide
    the one real inequality:   n * D_mean <= 34      (strictly 38.61; 34 keeps 14% back)

A Ø3.0 mandrel gives D_mean = 3.50 as-wound and 3.68..4.03 after the 5..15% springback
music wire takes at this index, so the mandrel cannot miss the box -- 0..24% all lands
inside it, and at 24% the coil's unwound far edge reaches POCKET_FREE_R, which station
G's Ø6.90 ring physically refuses.  The coil count you do not even choose: see step 5.

THE ONE THING THAT IS NOT OBVIOUS, AND IT SET TORSION_COILS
-----------------------------------------------------------
The two legs leave OPPOSITE ENDS of the coil, so the angle between them IS the total
wrap.  A free included angle F therefore forces

    n mod 1 = F / 360 = 170 / 360 = 0.4722

and the legal coil counts are 7.472, 8.472, 9.472, ... and nothing else.  TORSION_COILS
read a round 8 until this file had to answer "wind how many turns?"; a round 8 is not a
spring you can build with legs 170 deg apart, and treating it as one overstated the
torque by 5.5%.  spring_check()'s assertion 10 now refuses a coil count that is not
leg-legal.

The happy consequence is that the fractional part costs nothing to hit: you do not
count it, you CUT it.  Wind long, then leave the coil at whatever azimuth the gauge
says, and the fraction comes out right by construction while the integer lands wherever
it lands -- inside a three-coil window.

THE TWO STATIONS
----------------
    W  WINDER, at x -15.  A Ø3.05 socket 10 mm deep for the mandrel rod, and one
       Ø0.9 x 3.0 anchor hole at r 2.8 in the boss top face.  The anchor is the SAME
       Ø0.9 x 3.0 at the SAME r 2.8 as the seats in the knuckle and the lug, so a leg
       that will not enter the jig will not enter the part either.  No 170 deg gauge
       here: the leg angle cannot be gauged on the mandrel, because coming off it the
       coil grows in diameter and, with the wire length fixed, n = L/(pi D) falls -- a
       10% growth in D moves the far leg by most of a turn.  Angle is gauged at G, off
       the mandrel, relaxed.

    G  GAUGE, at x +16.  This is the hinge pocket in miniature and it is the whole
       acceptance test:
           Ø2.10 bore              takes the actual Ø2.0 hinge-pin stock
           Ø0.9 x 3.0 at r 2.8     one seat, at az 90
           Ø6.90 ring, 5.5 tall    = 2 * POCKET_FREE_R and = TORSION_GAP, so it is at
                                     once the far-edge NO-GO and a direct read on body
                                     length: a coil that stands proud of the ring is
                                     longer than the gap it has to live in
           1.10 slot at az 260     = 90 + 170, the free-angle gauge.  Parallel-sided,
                                     r 4.75..11.0, so a wire pivoting at the coil's
                                     surface is held to +-1.9 deg -- tighter than the
                                     +-4.09 deg of slop the Ø0.9 seat allows anyway
           1.2 notch at az 90      relief for the first radial arm, and it lets you see
                                     the tail going into its hole

    plus a BEND FENCE, a 3.0 mm step across the plate's -y edge.  Lay the wire on top,
    bend the overhang down its vertical face, trim flush with the plate: the tail is
    TORSION_SEAT_DEPTH exactly, without measuring anything.

HOW TO MAKE ONE (four needed, all identical, all one hand)
----------------------------------------------------------
    1. Cut 150 mm of Ø0.50 music wire (110 mm ends up in the spring; the rest is grip).
    2. Bend tail A: 3.0 mm at 90 deg, on the bend fence.
    3. Tail A into station W's anchor hole; the arm lies flat on the boss face.
    4. Wind NINE turns of hard tension onto the Ø3.0 rod, pushing each turn down onto
       the last so the coil closes.  Deliberately long -- step 5 throws the excess away.
    5. Off the rod, over to station G: tail A into the seat hole, coil over the Ø2.0
       pin, inside the ring.  Now find where the coil's last turn crosses the az 260
       slot, bend the wire radially out THERE into the slot, and trim it at r 3.4.
       That bend is what sets the free angle, and it is why the coil count never had to
       be counted -- but it is NOT true that any crossing will do.  Coming off the rod
       the coil grows and, the wire length being fixed, the count falls: nine wound
       relaxes to 7.8..8.6 turns, so the crossing the wire naturally reaches is 7.472 or
       8.472, and both of those work.  If you have enough spare wire to push it round to
       9.472, DON'T -- take the crossing one turn earlier.  9.472 x 3.85 = 36.5 breaks
       n * D_mean <= 34 and the spring stops clearing bench gravity.
    6. Bend tail B: 3.0 mm, the OPPOSITE way to tail A, so the two tails point apart --
       they go into two seats that FACE each other across TORSION_GAP.  Fence, trim.
    7. ACCEPT it, back in station G, unloaded:  tail A bottomed and its arm flat;
       arm B free in the slot with no persuasion (that is the free angle);  coil not
       standing proud of the ring (that is body < TORSION_GAP);  coil loose inside the
       ring at every position you push it to (that is the far edge vs POCKET_FREE_R).
       Then callipers: D_mean over the coil, and count the turns.  The one number that
       has to be checked is n * D_mean <= 34 -- it is the whole acceptance test, because
       torque goes as 1/(n D) and 34 is 1.14x of what bench gravity needs.
    8. If it came out FAT (D_mean over 4.0) and n came out 8.472, unwrap it to 7.472 --
       one crossing earlier.  Torque goes as 1/n, so that is a flat 8.472/7.472 = 1.13x
       on the margin: 1.13x -> 1.28x at D_mean 4.03, or 1.09x -> 1.23x at 4.20.
       Two identical-looking springs, both legal, is fine: the halves are sprung in
       pairs and a 10% mismatch between the two on one half is invisible.

All four springs are the same hand and the same part.  Two of the four are deflected in
the UNWINDING sense in service -- the restoring torque is set by the free ANGLE, not by
the hand -- which is why spring_check() repeats the radial clearance on the grown
diameter, and why the ring here has to pass the unwound far edge and not just the wound
one.

PRINT IT
--------
Plate flat on the bed, everything grows +z, no overhang anywhere except the 1.1 mm
bridge over the az 90 notch in the ring, which needs nothing.  PLA or PETG for
preference -- a jig wants stiffness and dimensional stability, not ABS's heat
resistance, and ABS's 0.6% shrink lands the Ø3.05 socket at about Ø3.03.  Either way
clear the two sockets with the rods themselves before use.  The mandrel post is NOT
printed and that is deliberate: winding Ø0.5 music wire takes about 20 N of tension,
which on a Ø2.7 plastic post 12 mm tall works out near 60 MPa of bending stress -- it
would snap.  The plate only locates a steel rod.

Run:  python spring_jig.py
Export: python ~/.claude/skills/cad/scripts/step -o out/spring_jig.step \
            --stl spring_jig.stl spring_jig.py
"""

from __future__ import annotations

import math

from build123d import Align, Box, Pos, Rot

import nose_build as B
import nose_params as P

# --- the plate
PLATE_L = 62.0
PLATE_W = 26.0
PLATE_T = 4.0

# --- station centres
X_WIND = -15.0
X_GAUGE = 16.0

# --- both stations sit on a boss, so the socket can be 10 mm deep in a 4 mm plate and
# hold its rod square.  10.0 is 3.3 diameters of the mandrel, which is what squareness
# needs; a 4 mm plate alone would be 1.3 and the rod would lean.
BOSS_H = 8.0
Z_FACE = PLATE_T + BOSS_H              # 12.0, the face both springs seat on
SOCKET_DEPTH = 10.0                    # leaves 2.0 mm of plate under both sockets

MANDREL_D = 3.0                        # dowel pin / drill blank / drill shank
MANDREL_BORE = MANDREL_D + 0.05
WIND_BOSS_D = 10.0

GAUGE_BORE = P.PIN_BORE_LUG            # 2.10, deliberately the part's own pin fit
GAUGE_BOSS_D = 11.0

# --- the ring at station G IS the pocket: 2 * POCKET_FREE_R across, TORSION_GAP tall
RING_R_IN = P.POCKET_FREE_R
RING_T = 1.3
RING_H = P.TORSION_GAP

# --- the leg features, all three numbers taken straight from the printed seats
ANCHOR_D = P.TORSION_SEAT_D            # 0.9
ANCHOR_DEPTH = P.TORSION_SEAT_DEPTH    # 3.0
ANCHOR_R = P.TORSION_LEG_R             # 2.8
AZ_ANCHOR = 90.0                       # +y.  Arbitrary, but it fixes the hand together
                                       # with AZ_GAUGE being +F from it (counter-
                                       # clockwise seen from +z = a right-hand coil).

# --- the free-angle gauge
SLOT_W = 1.10                          # a 0.50 wire in a 1.10 slot has 0.30 of play
                                       # either side; over the lever from the coil's
                                       # surface to r 11.0 that is +-1.9 deg
CH_WALL_T = 1.4
CH_R1 = 11.0
CH_TOP_Z = Z_FACE + P.TORSION_GAP + 1.0
NOTCH_H = 1.2                          # arm relief through the ring at AZ_ANCHOR

# --- the bend fence
FENCE_H = P.TORSION_SEAT_DEPTH         # so a tail bent over it and trimmed flush with
                                       # the plate is TORSION_SEAT_DEPTH long
FENCE_X = 8.0                          # half-length.  NOT wider: the az 260 channel
                                       # reaches (14.1, -10.8), which is inside the
                                       # fence's y band, and both live at z 4..7 -- at
                                       # x +-16 the channel walls grow straight up
                                       # through the fence and interrupt the very edge
                                       # you bend against.  16 mm of clean fence is
                                       # plenty for a 0.5 mm wire.  (Caught by drawing
                                       # the plan view, not by a boolean: the union is
                                       # legal geometry, just a useless fence.)
FENCE_Y0 = -PLATE_W / 2                # its back is the plate's -y edge
FENCE_Y1 = -8.5                        # its face; y -8.5..+13 is clear plate to cut on


def free_angle() -> float:
    """The free included leg angle, from the two seat azimuths at full opening."""
    az_k, az_l = P.torsion_leg_azimuths(P.TORSION_TRAVEL)
    return az_l - az_k


AZ_GAUGE = AZ_ANCHOR + free_angle()     # 260.0


# --------------------------------------------------------------------- primitives

def _radial_box(x0: float, az: float, r0: float, r1: float,
                w: float, z0: float, z1: float):
    """A `w`-wide box lying on the ray at azimuth `az`, spanning r0..r1 and z0..z1."""
    b = Box(r1 - r0, w, z1 - z0, align=(Align.MIN, Align.CENTER, Align.MIN))
    return Pos(x0, 0, 0) * Rot(0, 0, az) * Pos(r0, 0, z0) * b


def _plate():
    return Pos(0, 0, 0) * Box(PLATE_L, PLATE_W, PLATE_T,
                              align=(Align.CENTER, Align.CENTER, Align.MIN))


def _boss(x0: float, d: float):
    return B.cyl_along("z", (x0, 0, PLATE_T), d, BOSS_H)


def _ring():
    """Ø6.90 x 5.5 collar on station G -- the far-edge NO-GO and the body-length read."""
    return Pos(X_GAUGE, 0, 0) * B.revolve_rz([
        (RING_R_IN, Z_FACE), (RING_R_IN + RING_T, Z_FACE),
        (RING_R_IN + RING_T, Z_FACE + RING_H), (RING_R_IN, Z_FACE + RING_H)])


def _channel(x0: float, r0: float):
    """Two parallel walls forming the SLOT_W free-angle gauge at AZ_GAUGE."""
    solid = _radial_box(x0, AZ_GAUGE, r0, CH_R1, SLOT_W + 2 * CH_WALL_T,
                        PLATE_T, CH_TOP_Z)
    slot = _radial_box(x0, AZ_GAUGE, r0 - 1.0, CH_R1 + 1.0, SLOT_W,
                       PLATE_T - 0.01, CH_TOP_Z + 0.01)
    return solid, slot


def _fence():
    return Pos(0, (FENCE_Y0 + FENCE_Y1) / 2, PLATE_T) * Box(
        2 * FENCE_X, FENCE_Y1 - FENCE_Y0, FENCE_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN))


def gen_step():
    s = _plate()

    # --- the two bosses and the fence
    for x0, d in ((X_WIND, WIND_BOSS_D), (X_GAUGE, GAUGE_BOSS_D)):
        t = s + _boss(x0, d)
        B.assert_add(s, t, 0.8 * math.pi * (d / 2) ** 2 * BOSS_H, f"boss at x {x0}")
        s = t
    t = s + _fence()
    B.assert_add(s, t, 0.8 * 2 * FENCE_X * (FENCE_Y1 - FENCE_Y0) * FENCE_H, "bend fence")
    s = t

    # --- the ring, then the free-angle channel walls (added before any hole is cut, so
    # every assert_add below is measured against solid material)
    t = s + _ring()
    B.assert_add(s, t, 0.8 * math.pi * ((RING_R_IN + RING_T) ** 2 - RING_R_IN ** 2)
                 * RING_H, "POCKET_FREE_R ring")
    s = t
    walls, slot = _channel(X_GAUGE, RING_R_IN + RING_T)
    t = s + walls
    B.assert_add(s, t, 0.5 * (CH_R1 - RING_R_IN - RING_T) * (SLOT_W + 2 * CH_WALL_T)
                 * (CH_TOP_Z - Z_FACE), "free-angle channel walls")
    s = t

    # --- the slot through both the walls and the ring: one cutter, so they cannot end
    # up at different azimuths
    t = s - slot
    B.assert_cut(s, t, 0.5 * (CH_R1 - RING_R_IN) * SLOT_W * (CH_TOP_Z - Z_FACE),
                 "free-angle slot")
    s = t

    # --- arm relief through the ring at the anchor azimuth
    t = s - _radial_box(X_GAUGE, AZ_ANCHOR, RING_R_IN - 0.5, RING_R_IN + RING_T + 0.5,
                        SLOT_W, Z_FACE - 0.01, Z_FACE + NOTCH_H)
    B.assert_cut(s, t, 0.5 * RING_T * SLOT_W * NOTCH_H, "arm relief notch")
    s = t

    # --- the two rod sockets
    for x0, bore, label in ((X_WIND, MANDREL_BORE, "mandrel socket"),
                            (X_GAUGE, GAUGE_BORE, "gauge pin socket")):
        t = s - B.cyl_along("z", (x0, 0, Z_FACE - SOCKET_DEPTH), bore,
                            SOCKET_DEPTH + 0.01)
        B.assert_cut(s, t, 0.8 * math.pi * (bore / 2) ** 2 * SOCKET_DEPTH, label)
        s = t

    # --- the two leg-seat anchors, identical to the seats in the knuckle and the lug
    a = math.radians(AZ_ANCHOR)
    for x0 in (X_WIND, X_GAUGE):
        base = (x0 + ANCHOR_R * math.cos(a), ANCHOR_R * math.sin(a),
                Z_FACE - ANCHOR_DEPTH)
        t = s - B.cyl_along("z", base, ANCHOR_D, ANCHOR_DEPTH + 0.01)
        B.assert_cut(s, t, 0.8 * math.pi * (ANCHOR_D / 2) ** 2 * ANCHOR_DEPTH,
                     f"anchor hole at x {x0}")
        s = t

    s.label = "spring_jig"
    return s


if __name__ == "__main__":
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"spring_jig   vol {s.volume/1000:8.2f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.1f} g")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    # --- it must fit its own plate, and nothing may hang below it
    assert abs(lo[2]) < 1e-6 and abs(hi[2] - CH_TOP_Z) < 1e-6, \
        f"z runs {lo[2]}..{hi[2]}, expected 0..{CH_TOP_Z}"
    assert lo[0] > -PLATE_L / 2 - 1e-6 and hi[0] < PLATE_L / 2 + 1e-6, \
        "a feature hangs off the plate in x"
    assert lo[1] > -PLATE_W / 2 - 1e-6 and hi[1] < PLATE_W / 2 + 1e-6, \
        "a feature hangs off the plate in y"
    print(f"  everything grows +z off one {PLATE_L} x {PLATE_W} x {PLATE_T} plate, so it "
          f"prints face down with no support")

    # --- THE JIG IS ONLY HONEST IF ITS FEATURES ARE THE PART'S FEATURES.  Re-derived
    # here rather than copied, so an edit to any seat number breaks this and not a print.
    assert ANCHOR_D == P.TORSION_SEAT_D
    assert ANCHOR_DEPTH == P.TORSION_SEAT_DEPTH
    assert ANCHOR_R == P.TORSION_LEG_R
    assert FENCE_H == P.TORSION_SEAT_DEPTH
    assert RING_H == P.TORSION_GAP
    assert abs(RING_R_IN - P.POCKET_FREE_R) < 1e-9
    assert GAUGE_BORE == P.PIN_BORE_LUG
    print(f"  station G reproduces the pocket: Ø{2*RING_R_IN:.2f} x {RING_H} "
          f"(= 2 x POCKET_FREE_R x TORSION_GAP), Ø{GAUGE_BORE} pin bore, "
          f"Ø{ANCHOR_D} x {ANCHOR_DEPTH} seat at r {ANCHOR_R}")

    # --- the anchor has to be in the boss and not through the socket wall
    for x0, boss_d, bore, tag in ((X_WIND, WIND_BOSS_D, MANDREL_BORE, "W"),
                                  (X_GAUGE, GAUGE_BOSS_D, GAUGE_BORE, "G")):
        assert ANCHOR_R + ANCHOR_D / 2 < boss_d / 2 - 0.5, \
            f"station {tag}: the anchor hole runs off the edge of its boss"
        wall = ANCHOR_R - ANCHOR_D / 2 - bore / 2
        assert wall > 0.6, (f"station {tag}: only {wall:.2f} mm between the anchor hole "
                            f"and the Ø{bore} socket")
        print(f"  station {tag}: anchor at r {ANCHOR_R} leaves {wall:.2f} mm of wall to "
              f"its Ø{bore} socket and {boss_d/2 - ANCHOR_R - ANCHOR_D/2:.2f} mm to the "
              f"boss edge")
    assert SOCKET_DEPTH >= 3.0 * MANDREL_D, \
        "the mandrel socket is shallower than 3 diameters -- the rod will lean"
    assert PLATE_T + BOSS_H - SOCKET_DEPTH >= 1.5, "too little floor under the sockets"
    print(f"  sockets {SOCKET_DEPTH} deep = {SOCKET_DEPTH/MANDREL_D:.1f} mandrel "
          f"diameters, on {PLATE_T + BOSS_H - SOCKET_DEPTH:.1f} mm of floor")

    # --- THE FENCE MUST NOT MEET THE CHANNEL.  Both stand on the plate at z 4, so an
    # overlap in plan is an overlap in solid: the channel walls would grow up through
    # the fence and break the edge you bend the tail against.  A boolean union will not
    # complain about that, so it is checked here.
    ch_half = (SLOT_W + 2 * CH_WALL_T) / 2
    gx, gy = math.cos(math.radians(AZ_GAUGE)), math.sin(math.radians(AZ_GAUGE))
    corners = [(X_GAUGE + gx * r - gy * s * ch_half, gy * r + gx * s * ch_half)
               for r in (RING_R_IN + RING_T, CH_R1) for s in (-1, 1)]
    for cx, cy in corners:
        assert not (FENCE_Y0 - 0.2 <= cy <= FENCE_Y1 + 0.2
                    and -FENCE_X - 0.2 <= cx <= FENCE_X + 0.2), (
            f"the az {AZ_GAUGE:.0f} channel corner ({cx:.2f}, {cy:.2f}) lands inside "
            f"the bend fence (x +-{FENCE_X}, y {FENCE_Y0}..{FENCE_Y1}) -- they would "
            f"merge into each other at z {PLATE_T}..{PLATE_T + FENCE_H}")
        assert abs(cx) <= PLATE_L / 2 and abs(cy) <= PLATE_W / 2, \
            f"the channel corner ({cx:.2f}, {cy:.2f}) hangs off the plate"
    far = max(corners, key=lambda c: math.hypot(c[0] - X_GAUGE, c[1]))
    print(f"  channel reaches ({far[0]:.2f}, {far[1]:.2f}) -- clear of the fence "
          f"(x +-{FENCE_X}) and inside the plate, so the fence keeps {2*FENCE_X:.0f} mm "
          f"of unbroken edge")

    # --- the free-angle gauge must be TIGHTER than the slop the seat already allows,
    # or it is not gauging anything.  The wire pivots where it leaves the coil, at
    # r = D_mean/2, and must lie inside the slot all the way out to CH_R1, so the far
    # end is what binds.
    lever = CH_R1 - P.TORSION_COIL_D_MEAN / 2
    hold = math.degrees(math.atan(((SLOT_W - P.TORSION_WIRE_D) / 2) / lever))
    seat_slop = math.degrees(math.atan(((P.TORSION_SEAT_D - P.TORSION_WIRE_D) / 2)
                                       / P.TORSION_LEG_R))
    assert hold < seat_slop, (
        f"the az {AZ_GAUGE:.0f} slot holds the leg to only +-{hold:.2f} deg while the "
        f"Ø{P.TORSION_SEAT_D} seat itself allows +-{seat_slop:.2f} -- the jig would be "
        f"the loosest thing in the chain")
    assert abs(AZ_GAUGE - AZ_ANCHOR - free_angle()) < 1e-9
    print(f"  free angle {free_angle():.0f} deg = az {AZ_ANCHOR:.0f} to az "
          f"{AZ_GAUGE:.0f}; the Ø{SLOT_W} slot out to r {CH_R1} holds a leg to "
          f"+-{hold:.2f} deg against the seat's own +-{seat_slop:.2f}")

    # --- and the mandrel must land D_mean inside the box over the whole springback
    # range, which is the claim that makes this buildable without measuring anything
    aw = MANDREL_D + P.TORSION_WIRE_D
    n = P.TORSION_COILS
    print(f"  Ø{MANDREL_D} mandrel -> D_mean {aw:.2f} as-wound; after springback:")
    worst = None
    for sb in (0.00, 0.05, 0.10, 0.15, 0.20, 0.25):
        dm = aw * (1 + sb)
        k = P.TORSION_E * P.TORSION_WIRE_D ** 4 / (10.8 * dm * n) / 360.0
        half = 2 * k * P.TORSION_TRAVEL
        dm_un = dm * n / (n - P.TORSION_TRAVEL / 360.0)
        far_un = dm_un - P.D_PIN / 2
        ok = far_un <= P.POCKET_FREE_R and half > P.BENCH_MOMENT_WORST
        print(f"    {100*sb:5.0f} %  D_mean {dm:5.3f}  n*D {n*dm:5.2f}  "
              f"{half:6.2f} N.mm/half = {half/P.BENCH_MOMENT_WORST:5.3f}x bench  "
              f"far edge unwound {far_un:5.3f} of {P.POCKET_FREE_R}  "
              f"{'OK' if ok else 'REFUSED BY THE RING'}")
        if sb <= 0.15:
            worst = half if worst is None else min(worst, half)
    assert worst > P.BENCH_MOMENT_WORST, (
        f"somewhere in 0..15% springback the spring stops lifting a half: "
        f"{worst:.2f} vs {P.BENCH_MOMENT_WORST:.2f} N.mm")
    assert 3.20 <= P.TORSION_COIL_D_MEAN <= 4.30, \
        "the nominal D_mean is outside the box this jig is built around"
    print(f"    -> over the 5..15% music wire actually takes, the worst case is "
          f"{worst:.2f} N.mm per half = {worst/P.BENCH_MOMENT_WORST:.2f}x bench, and the "
          f"ring refuses anything past about 24%")

    # --- THE COIL COUNT IS NOT CHOSEN, IT IS CUT -- but the window is narrower than the
    # leg quantisation alone suggests, and getting that wrong is how you wind a spring
    # that gauges perfectly and still will not lift the half.  TORSION_GAP bounds the
    # count from above at 10.472, but n * D_mean <= 34 bites first.
    frac = free_angle() / 360.0
    assert abs((n % 1.0) - frac) < 0.01
    legal = [math.floor(n) + frac + k for k in (-1, 0, 1, 2)]
    fits = [c for c in legal
            if (c + P.TORSION_TRAVEL / 360.0) * P.TORSION_WIRE_D < P.TORSION_GAP
            and c * P.TORSION_COIL_D_MEAN <= 34.0]
    # TORSION_COILS is a rounded literal (8.472) and frac is exact (0.47222...), so this
    # compares within the rounding and not with ==
    assert any(abs(n - c) < 0.01 for c in fits), \
        f"the nominal {n} coils is not in the acceptable window {fits}"
    print(f"  coil count is quantised by the free angle: n mod 1 = {frac:.4f}, so the "
          f"legal counts are {', '.join(f'{c:.3f}' for c in legal)}")
    print(f"  of those only {', '.join(f'{c:.3f}' for c in fits)} are ACCEPTABLE at "
          f"D_mean {P.TORSION_COIL_D_MEAN}: body must stay inside TORSION_GAP "
          f"{P.TORSION_GAP} (that alone would allow all four) and n * D_mean must stay "
          f"under 34 (that is what rules out {', '.join(f'{c:.3f}' for c in legal if c not in fits)})")

    # --- so how many turns do you WIND?  Springback grows D and, with the wire length
    # fixed, drops the count: n_free = n_wound * D_wound / D_free.  Nine is chosen so
    # that the relaxed coil lands ON the acceptable window across the whole springback
    # range, and never above it -- winding to the count you want would land BELOW it.
    n_wind = 9
    lands = [n_wind * aw / (aw * (1 + sb)) for sb in (0.05, 0.10, 0.15)]
    print(f"  so WIND {n_wind}: over 5..15% springback that relaxes to "
          f"{min(lands):.2f}..{max(lands):.2f} turns, and the slot crossing you take is "
          f"{fits[0]:.3f} or {fits[-1]:.3f} -- both acceptable, which is the whole reason "
          f"nine and not eight")
    assert min(lands) > min(fits) - 0.5 and max(lands) < max(fits) + 0.5, (
        f"winding {n_wind} relaxes to {min(lands):.2f}..{max(lands):.2f} turns, which "
        f"does not bracket the acceptable window {fits} -- wind a different number")

    # --- what to buy
    wire = (2 * ANCHOR_DEPTH + 2 * (ANCHOR_R - P.TORSION_COIL_D_MEAN / 2)
            + math.pi * P.TORSION_COIL_D_MEAN * n)
    print(f"  wire: {wire:.1f} mm ends up in each spring ({2*ANCHOR_DEPTH:.1f} tails + "
          f"{2*(ANCHOR_R - P.TORSION_COIL_D_MEAN/2):.1f} arms + "
          f"{math.pi*P.TORSION_COIL_D_MEAN*n:.1f} of coil); cut 150 mm to have something "
          f"to pull on, so one 1000 mm guitar string makes {int(1000 // 150)} and four "
          f"are needed")

    # --- and the substitution table, because the wire is the one thing a builder may
    # have to swap.  T goes as d^4, so this is steep in both directions.
    print("  if you have other wire (same jig, same mandrel, same seats):")
    for d in (0.45, 0.50, 0.508, 0.56, 0.60, 0.63, 0.66, 0.71):
        dm = MANDREL_D + d
        dm = dm * 1.10
        k = P.TORSION_E * d ** 4 / (10.8 * dm * n) / 360.0
        half = 2 * k * P.TORSION_TRAVEL
        sig = 32 * (half / 2) / (math.pi * d ** 3)
        bw = (n + P.TORSION_TRAVEL / 360.0) * d
        why = []
        if bw >= P.TORSION_GAP:
            why.append(f"body {bw:.2f} > gap")
        if sig > P.TORSION_SIGMA_ALLOW:
            why.append(f"sigma {sig:.0f}")
        if d + 0.05 > P.TORSION_SEAT_D:
            why.append("too fat for the Ø0.9 seat")
        if half <= P.BENCH_MOMENT_WORST:
            why.append("under 1.0x bench")
        print(f"    Ø{d:5.3f}  D_mean {dm:5.2f}  {half:6.2f} N.mm/half = "
              f"{half/P.BENCH_MOMENT_WORST:5.2f}x bench, sigma {sig:4.0f}  "
              f"{'; '.join(why) if why else 'OK'}")
