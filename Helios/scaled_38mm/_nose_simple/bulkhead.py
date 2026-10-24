"""The bulkhead: the mechanism module.

Everything that moves is bolted to this one plate, so the nose can be assembled
and tested on the bench as a unit and then dropped into the ring as a unit.  It
does five jobs:

    1. closes the chute cavity      a disc, so the canopy can never reach the
                                    servo, the horn, the arm or the springs
    2. carries the servo            four cradle fins and two flange pads
    3. takes the latch load         an annular THRUST PAD bearing DOWN on the
                                    arm's top face, opposite the hooks pushing UP
                                    on its underside, so the servo's shaft
                                    carries none of it
    4. passes the two latch hooks   two through-slots, deliberately oversized
                                    towards -y: see _tongue_slot
    5. passes the shock cord        one off-axis hole at azimuth 270

PRINT ORIENTATION
-----------------
Disc TOP face (z = Z_BULK_TOP) flat on the bed, so the part builds toward -z and
the fins grow straight up off the bed.  Two consequences worth being explicit
about, because both drove geometry above:

  * The disc's layers lie in the plane of the latch load.  The arm pushes the
    disc UP through the thrust pad and the screws hold it down at the rim; both
    are in-layer paths.  Printed on edge instead, every one of them would be
    peeling layers apart.  Note the slots' edges carry nothing -- the hooks pass
    THROUGH them without touching, at every angle from shut to fully open.

  * z DECREASES as the print rises.  A face whose normal points at +z faces the
    bed and is therefore an overhang.  There is exactly one on this part: each
    flange pad's mounting face at z = Z_FLANGE_FACE, a 13.8 mm bridge between the
    two fins.  It cannot be supported from above, because the servo's own flange
    plate occupies that space (z 36..38.5 over |x| <= 6.1) -- and it cannot be
    ramped in from the fins either, since the ramp would have to pass through the
    same plate.  A 13.8 mm bridge is routine; a 0.9 mm sliver of web squeezed
    past the flange to avoid it would not be.  Print it as a bridge and, if the
    servo rocks, take one pass off the pads with a file.

Everything else is either vertical (fins, pad sides, slot walls, bore walls) or
faces away from the bed (the disc's underside, the thrust pad's bearing face, the
fins' free ends).  No support anywhere.

THE ACCESS HOLES ARE NOT OPTIONAL
---------------------------------
The servo's flange screws run along +z at (0, -8.8) and (0, +19.2), and the disc
is solid directly above both of them.  Without a hole through it the screws
cannot be started, let alone driven, and the servo cannot be fitted at all --
which is not visible in any view of the assembled part.  Same for the horn's
factory screw on the axis.  Three holes, Ø4.2 / Ø4.2 / Ø5.0; they also vent the
chute cavity into the servo bay, which is a small bonus rather than the reason.
"""

from __future__ import annotations

import math

from build123d import Align, Box, Cone, Pos, Rot

import nose_build as B
import nose_params as P

CORD_CHAMFER = 0.6       # both faces of the cord hole -- it is a bearing surface


def _block(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    """An axis-aligned box given by its two opposite corners."""
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0,
                                 align=(Align.MIN, Align.MIN, Align.MIN))


def _disc():
    return B.cyl_along("z", (0, 0, P.Z_BULK_BOT), 2 * P.R_BULK, P.BULK_T)


def _thrust_pad():
    """The annulus the arm actually bears on, standing THRUST_PAD_DROP proud below.

    A small defined bearing radius rather than the whole disc underside: friction
    torque scales with radius, and the servo's whole margin comes from keeping
    that radius small.

    ITS FACE MUST NOT BE COPLANAR WITH THE HOOKS' LATCH FACES, and that is the
    opposite of what an earlier version of this docstring claimed.  The hooks bear
    UPWARD on the arm's UNDERSIDE at Z_ARM_BOT, out at r 20.5..23.1.  This pad
    therefore has to react DOWNWARD on the arm's TOP face, at Z_ARM_TOP, in near
    the shaft.  Two faces on the same side of the arm oppose nothing.  So the arm
    is in BENDING between the two, not compression, and the 8.4 mm of LATCH_ARM_T
    between them is what carries it.  The load itself is only 0.64 N total (this
    used to say 3.5, from the spring figure spring_check() has since refuted), so
    the arm is not that thick for the load -- it is that thick because the
    geometry puts the two reaction faces 8.4 mm apart and because the floor over
    the horn pocket has to be printable.  nose_params.self_check() asserts both
    the coplanarity that must hold (pad face to Z_ARM_TOP) and the one that must
    not (pad face to the latch face).
    """
    return B.revolve_rz([(P.THRUST_PAD_R0, P.Z_ARM_TOP),
                         (P.THRUST_PAD_R1, P.Z_ARM_TOP),
                         (P.THRUST_PAD_R1, P.Z_BULK_BOT),
                         (P.THRUST_PAD_R0, P.Z_BULK_BOT)])


def _fins():
    """The two cradle fins, each a wall with a V-bottomed notch for the arm.

    Profile from nose_params.fin_profile(), so the swept-clearance check runs on
    the polygon that is actually built.  In the print pose each is a vertical wall
    standing on the bed, and the notch's 45 deg V is the only sloped face on it.
    """
    return [B.prism_yz(P.fin_profile(), *sorted((sx * P.FIN_X_IN,
                                                sx * (P.FIN_X_IN + P.FIN_T))))
            for sx in (+1, -1)]


def _flange_pads():
    """The two shelves the servo's flange lands on, spanning fin to fin."""
    x_out = P.FIN_X_IN + P.FIN_T
    return [_block(-x_out, x_out, y0, y1, P.Z_FLANGE_FACE - P.PAD_T, P.Z_FLANGE_FACE)
            for y0, y1 in P.flange_pads()]


def _tongue_slot():
    """The through-slot for hook A, at +x.  Hook B's slot is this rotated 180 deg.

    Asymmetric in both axes, and neither asymmetry is cosmetic.

    In Y the slot runs SLOT_Y0 = -4.75 to SLOT_Y1 = +3.65, i.e. 4.9 mm past the
    split plane on the far side.  The hook's foot hangs 2.5 mm below its own web,
    so as the half swings open the foot sweeps ACROSS the axis -- it reaches
    y = -4.25 at 20.8 deg of opening, while it is still level with this plate.  A
    slot sized to the hook at rest (the -1.5 it used to be) is a hard stop at
    about 9 deg: the nose would crack open, jam, and stay jammed.

    In X the clearances differ because what is nearby differs: 0.5 mm inboard
    where there is nothing for 20 mm, and 0.25 mm outboard so the deepened slot's
    outer corner (r 26.18) stays clear of the ring's seat bore at SEAT_R_IN.
    """
    return _block(P.TONGUE_X0 - P.SLOT_CLEAR_X_IN, P.TONGUE_X1 + P.SLOT_CLEAR_X_OUT,
                  P.SLOT_Y0, P.SLOT_Y1, P.Z_BULK_BOT - 1.0, P.Z_BULK_TOP + 1.0)


def _thru(d: float, y: float, x: float = 0.0):
    """A hole straight through the disc at (x, y)."""
    return B.cyl_along("z", (x, y, P.Z_BULK_BOT - 1.0), d, P.BULK_T + 2.0)


def _cord_chamfers():
    """45 deg lead-ins on both faces of the cord hole.

    The cord bears on whichever edge it is pulled over, and which one that is
    depends on how the airframe happens to be hanging at deployment -- so both
    get relieved.  0.6 mm each still leaves 1.3 mm of straight bore in a 2.5 mm
    plate.
    """
    r, c = P.D_CORD_HOLE / 2, CORD_CHAMFER
    top = Pos(0, P.Y_CORD_HOLE, P.Z_BULK_TOP - c) * Cone(
        bottom_radius=r, top_radius=r + c, height=c,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    bot = Pos(0, P.Y_CORD_HOLE, P.Z_BULK_BOT) * Cone(
        bottom_radius=r + c, top_radius=r, height=c,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return top, bot


def gen_step():
    s = _disc()

    t = s + _thrust_pad()
    B.assert_add(s, t, 60.0, "thrust pad")
    s = t

    for i, fin in enumerate(_fins()):
        t = s + fin
        B.assert_add(s, t, 1000.0, f"cradle fin {i}")
        s = t

    for i, pad in enumerate(_flange_pads()):
        t = s + pad
        B.assert_add(s, t, 300.0, f"flange pad {i}")
        s = t

    # --- flange pilots, straight through the pads
    for y in P.SERVO_HOLE_Y:
        t = s - B.cyl_along("z", (0, y, P.Z_FLANGE_FACE - P.PAD_T - 0.01),
                            P.M2_PILOT, P.PAD_T + 0.02)
        B.assert_cut(s, t, 0.8 * math.pi * (P.M2_PILOT / 2) ** 2 * P.PAD_T,
                     f"flange pilot at y={y:+.1f}")
        s = t

    # --- the two blade slots, A and its 180 deg image
    for th in (0.0, 180.0):
        t = s - (Rot(0, 0, th) * _tongue_slot())
        B.assert_cut(s, t, 60.0, f"blade slot at {th:.0f} deg")
        s = t

    # --- shock cord, chamfered both ways
    t = s - _thru(P.D_CORD_HOLE, P.Y_CORD_HOLE)
    B.assert_cut(s, t, 100.0, "shock cord hole")
    s = t
    for name, cut in zip(("top", "bottom"), _cord_chamfers()):
        t = s - cut
        B.assert_cut(s, t, 3.0, f"cord hole {name} chamfer")
        s = t

    # --- the two retaining screws, into the ring's lobes
    for th in P.LOBE_THETA:
        a = math.radians(th)
        t = s - _thru(P.M2_5_CLEAR, P.R_BULK_SCREW * math.sin(a),
                      P.R_BULK_SCREW * math.cos(a))
        B.assert_cut(s, t, 0.8 * math.pi * (P.M2_5_CLEAR / 2) ** 2 * P.BULK_T,
                     f"retaining screw at {th:.0f} deg")
        s = t

    # --- driver access: two over the flange screws, one over the horn screw
    for y in P.SERVO_HOLE_Y:
        t = s - _thru(P.SERVO_ACCESS_D, y)
        B.assert_cut(s, t, 0.8 * math.pi * (P.SERVO_ACCESS_D / 2) ** 2 * P.BULK_T,
                     f"flange screw access at y={y:+.1f}")
        s = t
    t = s - _thru(P.HORN_ACCESS_D, 0.0)
    B.assert_cut(s, t, 0.8 * math.pi * (P.HORN_ACCESS_D / 2) ** 2 * P.BULK_T,
                 "horn screw access")
    s = t

    s.label = "bulkhead"
    return s


# ------------------------------------------------------------------ standalone
def _seg_rect_gap(p0, p1, rect, n: int = 400) -> float:
    """Min distance from segment p0->p1 to an axis-aligned rect (x0,x1,y0,y1)."""
    x0, x1, y0, y1 = rect
    best = 1e9
    for i in range(n + 1):
        t = i / n
        px = p0[0] + (p1[0] - p0[0]) * t
        py = p0[1] + (p1[1] - p0[1]) * t
        dx = max(x0 - px, 0.0, px - x1)
        dy = max(y0 - py, 0.0, py - y1)
        best = min(best, math.hypot(dx, dy))
    return best


if __name__ == "__main__":
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"bulkhead    vol {s.volume/1000:8.2f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")
    print(f"  print pose (disc face down): {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x "
          f"{hi[2]-lo[2]:.1f} mm")

    # --- the reason the fins are split: the arm's capsule must miss all four of
    # them at every angle.  Exact for a slot: distance from its centreline to the
    # fin rectangle, against the half width.
    rects = []
    for sx in (+1, -1):
        xa, xb = sorted((sx * P.FIN_X_IN, sx * (P.FIN_X_IN + P.FIN_T)))
        for y0, y1 in P.fin_segments():
            rects.append((xa, xb, y0, y1))
    worst, worst_t = 1e9, None
    for k in range(0, 121):
        t = math.radians(P.LATCH_SWEEP * k / 120.0)
        c, sn = math.cos(t), math.sin(t)
        p0 = (-P.LATCH_ARM_R * c, -P.LATCH_ARM_R * sn)
        p1 = (P.LATCH_ARM_R * c, P.LATCH_ARM_R * sn)
        for r in rects:
            g = _seg_rect_gap(p0, p1, r) - P.LATCH_ARM_W / 2
            if g < worst:
                worst, worst_t = g, math.degrees(t)
    assert worst > 0.3, (f"the latch arm fouls a cradle fin by {-worst:.3f} mm at "
                         f"{worst_t:.1f} deg of sweep")
    print(f"  arm vs the four fins: closest approach {worst:.3f} mm, at "
          f"{worst_t:.1f} deg of sweep (checked over the whole {P.LATCH_SWEEP:.0f} deg)")

    # --- nothing on the cradle may touch the ring's seat or its screw lobes
    r_fin = max(math.hypot(x, y) for (x0, x1, y0, y1) in rects
                for x in (x0, x1) for y in (y0, y1))
    assert r_fin < P.SEAT_R_IN - 1.0, f"a fin reaches r={r_fin:.2f}, seat bore {P.SEAT_R_IN}"
    print(f"  cradle's furthest corner r {r_fin:.2f} vs the seat bore "
          f"{P.SEAT_R_IN} -- clear by {P.SEAT_R_IN - r_fin:.2f} mm")
    x_lo = P.TONGUE_X0 - P.SLOT_CLEAR_X_IN
    x_hi = P.TONGUE_X1 + P.SLOT_CLEAR_X_OUT
    r_corner = max(math.hypot(x_hi, y) for y in (P.SLOT_Y0, P.SLOT_Y1))
    assert r_corner < P.SEAT_R_IN - 0.5, (
        f"the hook slot's outer corner reaches r {r_corner:.2f} against a seat bore "
        f"of {P.SEAT_R_IN} -- it would break into the ring's seat land")
    print(f"  hook slots {x_lo:.2f}..{x_hi:.2f} in x, {P.SLOT_Y0:+.2f}.."
          f"{P.SLOT_Y1:+.2f} in y = {(x_hi-x_lo)*(P.SLOT_Y1-P.SLOT_Y0):.1f} mm2 each; "
          f"worst corner r {r_corner:.2f}, so they stop {P.SEAT_R_IN - r_corner:.2f} mm "
          f"short of the seat land at {P.SEAT_R_IN} and the rim stays continuous")
    print(f"  the slots run {-P.SLOT_Y0:.2f} mm past the split plane on the far side, "
          f"because the hook's foot swings across the axis to y -4.25 at 20.8 deg of "
          f"opening while it is still inside this plate's z band")
