"""The avionics PLATE: the half of the old one-piece sled that comes out.

Everything that touches a component -- the deck itself, the BMP280's ribs, the
ESP32's pin slots, ten cable-tie slots, four vents and three static ports -- plus the
two screw lugs that retain it.  It slides into bay_support.py from the forward end,
tail first, ALREADY POPULATED, and that is the whole point of the split: the
electronics get built up on a 52 x 177 mm plate lying on the bench with both hands
free, and only then does the assembly go down a 38 mm tube.

Nothing here reaches past r 27.05, which is 0.40 mm inside the head ring's 27.45 mm
bore.  It has to: the head is a complete ring and the plate goes through the hole.

PRINT ORIENTATION: FLAT, deck's underside on the bed, x = build Z
-----------------------------------------------------------------
This is the freedom the split bought, and it is worth more than it sounds.  In the
one-piece sled every feature on the deck had to be printable with the part standing
on end and the axis vertical, which is what forced the BMP ribs to rise off the deck
on 45 deg ramps, what ruled out mounting posts entirely, and what put a 3.6 mm bridge
over the aft end of each pin slot.  Lying flat, ALL of that goes away:

    ribs, lugs          vertical extrusions off the bed's plane.  No ramp needed.
    pin slots, tie
    slots               vertical through-slots.  No bridge anywhere.
    vents, ports        bored along x, which IS the build axis now -- so they are
                        vertical through-holes with no bridge at all, where in the
                        old pose they were horizontal bores with 2.5-5.0 mm ones.
    the curved edge     the only overhang left.  The chord's half-width grows from
                        25.84 mm at the deck's underside to 26.38 at its top face, so
                        the edge leans out 17.2 deg from vertical at worst -- 72.8 deg
                        from horizontal, against OVERHANG_DEG's 44.
    the lug pilots      the one bridge: a 2.5 mm hole bored along y, so 2.5 mm of
                        unsupported crown, against BRIDGE_MAX's 6.0.

The ramps are kept on the ribs anyway.  They cost 3.4 mm3 of ABS, they do no harm
lying flat, and they are what makes the rib's root a fillet instead of a stress
riser at the one place a tie strap pulls a rib sideways.

WHAT THE FLAT POSE COSTS: a 9157 mm2 first layer of ABS, 177 mm long.  That will
want to lift at the corners, and no amount of brim makes a 177 mm ABS plate come off
the bed dead flat.  SLIDE_CLR_X is sized for exactly that -- 0.30 mm per face is
about bow, not about shrink, which the slicer already compensates.

RETENTION, AND WHY IT IS TWO SCREWS AND NOT FRICTION
----------------------------------------------------
Aft, the plate seats on the support's stop and that carries boost (F_BOOST_N, 18.13 N
aft).  Landing is the bigger case at 48.35 N and it pushes FORWARD -- straight back
out of the mouth the plate came in through -- so there has to be a positive forward
stop as well.  It is the support's own two M3 self-tappers, lengthened to M3 x 16:
each crosses the airframe, the boss, 1.0 mm of air, and then takes 5.26 mm of thread
in a lug standing 9 mm off the plate's top face.  No new holes in the airframe, one
screw length in the assembly, and the load is a screw in shear rather than anything
printed in tension.

The lug's pilots are drawn SLIDE_GAP_Z forward of the bosses' -- see S_LUG_PILOT.
Seated, the plate has moved that far aft and the two line up.

Run:  python bay_plate.py
Export: PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \\
            -o out/bay_plate.step --stl bay_plate.stl bay_plate.py
"""

from __future__ import annotations

import math

import bay_build as B
import bay_params as P

SLOT_OVERSHOOT = 1.0        # how far a deck cutter reaches past each deck face, so
                            # the boolean is clean.  Bounded on BOTH sides by
                            # assert_cut_band, because this overshoot is exactly
                            # what would quietly eat a rib -- or now a lug -- if a y
                            # ever moved.
CLIP_OVER = 1.0             # z overshoot on the clipping cylinder, so its end faces
                            # are never coplanar with the ones meant to bound the
                            # plate


def _body():
    """The deck: a chord plate, clipped to R_PLATE so it can slide down the bore.

    R_PLATE, not the bore itself.  The old deck was clipped 0.5 mm OUTSIDE the bore,
    deliberately buried in the shell wall so the fuse had volumetric overlap.  This
    one is a separate part that has to move, so the sign flips: 0.40 mm INSIDE, and
    it must never touch.  Confusing FUSE_MERGE with SLIDE_CLR_R here would give a
    plate 1.8 mm too wide to enter the head ring at all.
    """
    r = P.R_PLATE
    plate = B.box_between(P.DECK_X_BOT, P.DECK_X_TOP, -r - 1.0, r + 1.0,
                          P.S_PLATE_FWD, P.S_PLATE_AFT)
    plate = plate & B.cyl_along("z", (0.0, 0.0, P.S_PLATE_FWD - CLIP_OVER),
                                2 * r, P.PLATE_L + 2 * CLIP_OVER)
    plate = B.one_solid(plate, "plate chord")
    want = B.slab_area(r, P.DECK_X_BOT, P.DECK_X_TOP) * P.PLATE_L
    got = plate.volume
    if abs(got - want) > 0.002 * want:
        raise AssertionError(
            f"plate chord: {got:.1f} mm3 against a closed-form {want:.1f} -- the "
            f"clip cylinder and the box do not bound what they were meant to")
    return plate


def _ribs(s):
    """The BMP280's two location ribs, each with a 45 deg ramp off the deck.

    The rib's foot is sunk RIB_EMBED into the deck rather than laid on top of it.
    Not cosmetic: a rib whose bottom face is exactly coplanar with the deck's top
    face touches the body on a face and overlaps it nowhere, and OCCT fuses that
    badly.  Drawn flush, this union came out 1478.665 mm3 SMALLER than the body it
    was added to -- it silently deleted most of a screw boss 20 mm away.  Half a
    millimetre of overlap makes it a well-posed boolean instead of a coincident-face
    special case, and assert_add is what turned a wrong solid into an error message.
    """
    h, t_rib, emb = P.RIB_H_BMP, P.RIB_T, P.FUSE_MERGE
    z0, z1 = P.S_RIB_BMP_0, P.S_RIB_BMP_1
    prof = [(P.DECK_X_TOP - emb, z0),                 # foot, INSIDE the deck
            (P.DECK_X_TOP + h, z0 + h + emb),         # still 45 deg: same rise, run
            (P.DECK_X_TOP + h, z1),
            (P.DECK_X_TOP - emb, z1)]
    # New material is only the part above the deck's top face: the trapezoid
    # truncated at x = DECK_X_TOP.  With u = x - (DECK_X_TOP - emb) that is
    # integral from emb to h+emb of (z1 - z0 - u) du.
    a, b = emb, h + emb
    want = ((z1 - z0) * (b - a) - (b * b - a * a) / 2.0) * t_rib
    for sign in (-1.0, 1.0):
        y_c = sign * P.RIB_Y_BMP
        s = B.add(s, B.prism_xz(prof, y_c - t_rib / 2, y_c + t_rib / 2),
                  0.99 * want, f"BMP rib at y {y_c:+.2f}")
    return s


def _lugs(s):
    """The two screw lugs, and the only features on this part that rise above x = 0.

    A plain BOX, not a sector clipped to a radius.  That makes its volume exact and
    its worst case a single point rather than a surface -- and the worst point is not
    where it looks: the lug's top-outboard CORNER is at r 22.20, but its outboard FACE
    keeps running as x falls and leaves the boss's 18 deg sector at r 22.27.  See the
    check in bay_params.self_check(), which had this wrong and read the corner.

    Sunk FUSE_MERGE into the plate, same rule as the ribs.
    """
    want = (P.LUG_X_TOP - P.DECK_X_TOP) * P.LUG_DEPTH * (P.S_LUG_1 - P.S_LUG_0)
    for sign in (1.0, -1.0):
        y0, y1 = P.LUG_Y_O - P.LUG_DEPTH, P.LUG_Y_O
        if sign < 0.0:
            y0, y1 = -y1, -y0
        s = B.add(s, B.box_between(P.LUG_X_BOT, P.LUG_X_TOP, y0, y1,
                                   P.S_LUG_0, P.S_LUG_1),
                  0.99 * want, f"screw lug at y {sign * P.LUG_Y_O:+.1f}")
    # The pilot goes THROUGH the lug, from FUSE_MERGE inside its inboard face to
    # 1.0 mm outboard of its outer one -- volumetric overlap at both ends, the same
    # rule the boss's pilot obeys and for the same reason.  Through, not blind, so a
    # screw that is driven a little far stops where its length says instead of
    # bottoming out and splitting the lug; the tip still lands 0.745 mm short of the
    # inboard face, and there is nothing behind it but air (s 197.5 is aft of the
    # battery bay's 193.2).
    want = math.pi * (P.LUG_PILOT_D / 2) ** 2 * P.LUG_DEPTH
    for th in P.SCREW_THETA:
        s = B.cut(s, B.radial_hole(P.LUG_PILOT_D, th, P.S_LUG_PILOT,
                                   P.LUG_Y_O - P.LUG_DEPTH - P.FUSE_MERGE,
                                   P.LUG_Y_O + 1.0),
                  0.92 * want, 1.08 * want, f"lug pilot at {th:.0f} deg")
    return s


def _deck_slot(y_c: float, w_y: float, z0: float, z1: float):
    """A rectangular void through the deck, oversized in x on both faces."""
    return B.box_between(P.DECK_X_BOT - SLOT_OVERSHOOT,
                         P.DECK_X_TOP + SLOT_OVERSHOOT,
                         y_c - w_y / 2, y_c + w_y / 2, z0, z1)


def _pin_slots(s):
    """Two slots so the ESP32's header pins hang through instead of being crushed."""
    want = P.PIN_SLOT_W * P.DECK_T * (P.S_PIN_SLOT_1 - P.S_PIN_SLOT_0)
    for sign in (-1.0, 1.0):
        y_c = sign * P.PIN_SLOT_Y
        s = B.cut(s, _deck_slot(y_c, P.PIN_SLOT_W,
                                P.S_PIN_SLOT_0, P.S_PIN_SLOT_1),
                  0.98 * want, 1.02 * want, f"ESP32 pin slot at y {y_c:+.2f}")
    return s


def _tie_slots(s):
    """Cable-tie slot pairs: one pair for the BMP280, two each for the ESP32 and
    the battery.  The battery has nothing else -- which is the whole point, since
    it is the one item whose dimensions are not yet known."""
    want = P.STRAP_SLOT_Y * P.DECK_T * P.STRAP_SLOT_Z
    groups = ([(z, P.STRAP_Y_BMP, "BMP280") for z in P.STRAP_STATIONS_BMP]
              + [(z, P.STRAP_Y_MAIN, "ESP32") for z in P.STRAP_STATIONS_ESP32]
              + [(z, P.STRAP_Y_MAIN, "battery") for z in P.STRAP_STATIONS_BATT])
    for z, y, lbl in groups:
        for sign in (-1.0, 1.0):
            y_c = sign * y
            s = B.cut(s, _deck_slot(y_c, P.STRAP_SLOT_Y,
                                    z - P.STRAP_SLOT_Z / 2,
                                    z + P.STRAP_SLOT_Z / 2),
                      0.97 * want, 1.03 * want,
                      f"{lbl} tie slot at s {z:.1f}, y {y_c:+.1f}")
    return s


def _holes(s):
    """Static ports and deck vents.  In the flat pose these are the only features
    bored along the BUILD axis, so unlike every other hole in this bay they have no
    bridge over them at all."""
    depth = P.DECK_T + 2 * SLOT_OVERSHOOT
    x0 = P.DECK_X_BOT - SLOT_OVERSHOOT

    for z in P.BMP_PORT_STATIONS:
        want = math.pi * (P.BMP_PORT_D / 2) ** 2 * P.DECK_T
        s = B.cut(s, B.cyl_along("x", (x0, 0.0, z), P.BMP_PORT_D, depth),
                  0.94 * want, 1.06 * want, f"BMP static port at s {z:.1f}")

    for z in P.VENT_STATIONS:
        for sign in (-1.0, 1.0):
            y_c = sign * P.VENT_Y
            want = math.pi * (P.VENT_D / 2) ** 2 * P.DECK_T
            s = B.cut(s, B.cyl_along("x", (x0, y_c, z), P.VENT_D, depth),
                      0.94 * want, 1.06 * want,
                      f"vent at s {z:.1f}, y {y_c:+.1f}")
    return s


def gen_step():
    s = _body()
    s = _ribs(s)
    s = _lugs(s)
    s = _pin_slots(s)
    s = _tie_slots(s)
    s = _holes(s)
    s.label = "bay_plate"
    return s


def swept_envelope(z0: float, z1: float):
    """Every station this part's material can occupy, over z0..z1.

    EXACT, not a bounding approximation, and that is the point.  The plate is
    inserted tail first and already populated, so a feature at plate station z passes
    every support station forward of it: asking "does the plate fit where it ends up"
    answers the wrong question.  But every solid FAMILY on this part is a prism along
    z -- the chord, the ribs, the lugs -- and each cut only removes material.  So the
    union of those three families, extruded over any station range, is precisely the
    volume the plate sweeps through that range.  The support may not have material
    anywhere inside it.
    """
    r = P.R_PLATE
    box = B.box_between(P.DECK_X_BOT, P.DECK_X_TOP, -r - 1.0, r + 1.0, z0, z1)
    env = box & B.cyl_along("z", (0.0, 0.0, z0 - CLIP_OVER), 2 * r,
                            (z1 - z0) + 2 * CLIP_OVER)
    for sign in (-1.0, 1.0):
        y_c = sign * P.RIB_Y_BMP
        env = env + B.box_between(P.DECK_X_TOP - P.FUSE_MERGE,
                                  P.DECK_X_TOP + P.RIB_H_BMP,
                                  y_c - P.RIB_T / 2, y_c + P.RIB_T / 2, z0, z1)
        y0, y1 = P.LUG_Y_O - P.LUG_DEPTH, P.LUG_Y_O
        if sign < 0.0:
            y0, y1 = -y1, -y0
        env = env + B.box_between(P.LUG_X_BOT, P.LUG_X_TOP, y0, y1, z0, z1)
    return env


if __name__ == "__main__":
    P.self_check()
    print()
    s = gen_step()
    lo, hi = B.bbox(s)
    mass = s.volume * P.ABS_RHO
    print(f"bay_plate   vol {s.volume/1000:8.2f} cm3   mass {mass:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")

    # It goes through the head ring, or it does not go in at all.
    r_max = B.assert_inside_bore(s, P.R_PLATE, "the plate")
    print(f"  max radius anywhere: {r_max:.4f}, against the head ring's bore "
          f"{P.R_SHELL_I:.2f} ({P.R_SHELL_I - r_max:+.3f} mm)")
    assert abs(r_max - P.R_PLATE) < 1e-6, \
        f"the plate's widest point is r {r_max:.4f}, not its clip radius {P.R_PLATE}"

    # THE TWO SECTORS IT HAS TO PASS THROUGH, checked on the solid over EVERY station
    # rather than at the one where each feature ends up.  Both sectors are invariant
    # along z, so intersecting them with the plate's full extent IS the swept test.
    from bay_support import vol            # noqa: E402  (same-package helper)

    for th in P.SCREW_THETA:
        keep = B.sector(th, P.BOSS_HALF_ANG, P.R_BOSS_I - P.LUG_CLR, P.R_SHELL_O,
                        P.S_PLATE_FWD - 1.0, P.S_PLATE_AFT + 1.0)
        v = vol(s & keep)
        print(f"  boss sector at {th:.0f} deg, r >= {P.R_BOSS_I - P.LUG_CLR:.2f}: "
              f"{v:.3f} mm3 of plate in it")
        assert v < 1e-6, (
            f"{v:.3f} mm3 of the plate lies inside the boss at theta {th:.0f} plus "
            f"its {P.LUG_CLR:.2f} mm clearance -- it jams on the way in")

    duct = B.sector(P.DUCT_THETA, P.DUCT_HALF_ANG, P.R_DUCT_INNER, P.R_SHELL_O,
                    P.S_PLATE_FWD - 1.0, P.S_PLATE_AFT + 1.0)
    v = vol(s & duct)
    print(f"  duct sector at {P.DUCT_THETA:.0f} deg +/-{P.DUCT_HALF_ANG:.0f}, "
          f"r >= {P.R_DUCT_INNER:.2f}: {v:.3f} mm3 of plate in it")
    assert v < 1e-6, (
        f"{v:.3f} mm3 of the plate lies in the shock-cord duct's sector -- the lugs "
        f"reach x +{P.LUG_X_TOP:.1f} now, so this is no longer covered by the deck "
        f"being below the axis")

    # The flat pose's first layer, which is the number that decides whether a
    # 177 mm ABS plate stays on the bed.
    foot = 2.0 * math.sqrt(P.R_PLATE ** 2 - P.DECK_X_BOT ** 2) * P.PLATE_L
    print(f"  flat pose: {2*math.sqrt(P.R_PLATE**2 - P.DECK_X_BOT**2):.2f} x "
          f"{P.PLATE_L:.2f} mm, first layer {foot:.0f} mm2 before slots")
    assert max(2 * math.sqrt(P.R_PLATE ** 2 - P.DECK_X_BOT ** 2),
               P.PLATE_L) < P.BED, \
        f"the plate does not fit the {P.BED:.0f} mm bed lying flat"

    assert abs(mass - P.M_PLATE) < 1.0, (
        f"bay_params.M_PLATE says {P.M_PLATE:.1f} g and the solid weighs "
        f"{mass:.1f} g")
