"""THE PAIR: bay_support.py + bay_plate.py, and every check that needs both.

This file replaces bay_sled.py, which built the bay as one printed part.  A copy of
that generator is kept at _scratch/_bay_sled_one_piece.py for reference only -- it no
longer runs, because M_SLED now means "what the two parts weigh together" and the old
one-piece solid does not weigh that.

Each of the two modules already proves what it can prove alone.  bay_support.py checks
its pocket against an IDEALISED plate -- POCKET_X_BOT..POCKET_X_TOP out to the bore --
and that is the right test for the chord, but the real plate is not a chord: it has two
BMP ribs standing 3 mm above the deck and two lugs standing 9 mm above it, reaching to
x +3.0, and none of those are inside the pocket's x-band.  bay_plate.py checks itself
against the two boss sectors and the shock-cord duct, which are the features it can
describe in closed form, and nothing else.

What is left over is exactly what this file is for:

    THE SLIDE          the support intersected with the plate's SWEPT ENVELOPE -- ribs,
                       lugs and all -- over the whole travel.  One number, and it has
                       to be zero.
    THE STOP           the plate pushed PAST home, which must interfere.  The other
                       half of "one way".
    CAPTURE            the plate lifted out of the pocket in x, either way, which must
                       also interfere.  Slidable is not the same as retained.
    THE SCREW PATH     a 2.3 mm probe on the M3's axis, from where its tip lands out to
                       the airframe, which must be clear THROUGH BOTH PARTS AT ONCE.
                       This is the one check that can catch a plate whose lug pilots
                       are drawn at the wrong station -- the failure S_LUG_PILOT
                       exists to prevent, tested on the solid rather than on the
                       arithmetic that produced it.
    THE LOADS          boost onto the stop, landing into the two lugs, and the lug root
                       in INTERLAYER tension, which is the direction the flat print
                       pose makes weakest and the direction landing loads it in.

WHY THE PLATE IS DRAWN 0.5 mm SHORT OF HOME
-------------------------------------------
bay_plate.py draws the plate at s 27.31..204.5 and the stop's face is at 205.0, so the
part as drawn is SLIDE_GAP_Z forward of where it ends up.  Everything below therefore
tests `Pos(0, 0, SEAT) * plate` for the installed state, and the fact that the lug
pilots then line up with the bosses' is not a coincidence -- S_LUG_PILOT is defined by
subtracting the same 0.5 mm.

Run:  python bay_assembly.py
Export (for VIEWING -- do not print this, print the two parts):
      PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \\
          -o out/bay_assembly.step bay_assembly.py
"""

from __future__ import annotations

import math

from build123d import Compound, Pos

import bay_build as B
import bay_params as P
import bay_plate as PL
import bay_support as SUP
from bay_support import vol

SEAT = P.SLIDE_GAP_Z        # drawn -> home: how far aft the plate travels to seat
PROBE = 0.10                # how far past a clearance a capture probe pushes, so the
                            # interference it proves is unambiguous rather than a
                            # coincident-face zero
OVERRUN = 1.0               # how far past home the stop test drives the plate, chosen
                            # so the interference divides out to an AREA: the section
                            # the stop presents to the plate's aft face
SCREW_PROBE_D = P.LUG_PILOT_D - 0.2        # 2.3, concentric in a 2.5 pilot

# The two g-loads behind F_BOOST_N and F_LANDING_N.  They live in comments in
# bay_params and nowhere else, so they are restated here and the two forces are
# recomputed from the MEASURED masses below -- a mass that moves and a force that
# does not is the whole failure mode this catches.
G_BOOST = 15.0
G_LANDING = 40.0
G0 = 9.81 / 1000.0          # N per gram per g

# Everything the two M3s actually have to hold on landing: the PLATE and what rides on
# it.  The support does not move -- it is screwed to the airframe -- so its 41.2 g is
# not in this sum.  F_LANDING_N is the whole assembly's 49.15 N and is used anyway,
# because a conservative number that is already committed beats a tighter one that has
# to be kept in step.
M_MOVING = P.M_PLATE + P.M_ESP32 + P.M_BMP + P.M_WIRING + P.M_BATT_WORST
M_ALL = P.M_SLED + P.M_ESP32 + P.M_BMP + P.M_WIRING + P.M_BATT_WORST

# ABS across the layer lines, which is what the lug root sees.  Bulk ABS goes about
# 40 MPa in tension; a well-bonded ABS layer interface goes 50-60% of that, and this is
# the low end of it.  Every other stress in this bay is in-plane and compares against
# bay_support's 10 MPa; this one gets its own number because the flat print pose puts
# the lug's layers PERPENDICULAR to the load.
ABS_INTERLAYER_MPA = 20.0


def _parts():
    """The support, the plate AS DRAWN, and the plate WHERE IT ENDS UP.

    The drawn one is handed back too so the probes below can move it themselves: the
    plate takes some seconds to build and it gets displaced four different ways here,
    which is four rebuilds if each probe calls gen_step() for itself.
    """
    sup = SUP.gen_step()
    drawn = PL.gen_step()
    return sup, drawn, Pos(0.0, 0.0, SEAT) * drawn


def gen_step():
    """Both parts, seated, as a two-solid compound.  For viewing only.

    Deliberately NOT a fuse: they do not touch, and a fuse of two disjoint solids is
    a compound with a misleading name.  There is nothing to print here -- print
    bay_support.py and bay_plate.py, in their own poses.
    """
    sup, _, plate = _parts()
    sup.label, plate.label = "bay_support", "bay_plate"
    return Compound(label="bay_assembly", children=[sup, plate])


def screw_probe(th: float):
    """The M3's swept path at azimuth th, from its tip out to the airframe's OD.

    Concentric in both pilots and 0.1 mm smaller all round, so a probe that hits
    something means real interference and not a face it happens to share.  It starts
    at r = R_OD - SCREW_L, which is where the tip lands, and ends at the shell's OD
    rather than the tube's: outboard of that is airframe, not this assembly.
    """
    return B.radial_hole(SCREW_PROBE_D, th, P.S_SCREW,
                         P.R_OD - P.SCREW_L, P.R_SHELL_O)


if __name__ == "__main__":
    P.self_check()
    print()
    sup, drawn, plate = _parts()
    m_sup = sup.volume * P.ABS_RHO
    m_pl = plate.volume * P.ABS_RHO
    print(f"bay_assembly  support {m_sup:5.1f} g + plate {m_pl:5.1f} g "
          f"= {m_sup + m_pl:5.1f} g ABS")
    lo, hi = B.bbox(Compound(children=[sup, plate]))
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")
    assert abs((m_sup + m_pl) - P.M_SLED) < 1.0, (
        f"bay_params.M_SLED says {P.M_SLED:.1f} g and the pair weighs "
        f"{m_sup + m_pl:.1f} g")

    print()
    print("  THE SLIDE -- the support against the plate's swept envelope")
    # The envelope is every station the plate's material can occupy on the way in, and
    # it is EXACT rather than a bound: see bay_plate.swept_envelope().  This is the
    # check that covers the ribs and the lugs, which the pocket's x-band does not.
    home = vol(sup & PL.swept_envelope(P.S_HEAD_FWD, P.S_STOP))
    print(f"    s {P.S_HEAD_FWD:.2f}..{P.S_STOP:.1f}: {home:.3f} mm3 of the support "
          f"in the plate's path")
    assert home < 1e-6, (
        f"{home:.3f} mm3 of the support stands in the plate's swept path -- the plate "
        f"jams before it is home.  bay_support's pocket_keepout() covers only the "
        f"chord's x-band, so this is most likely a RIB or a LUG against a boss")

    # Seated, which is a subset of the above and so needs no separate boolean: the
    # seated plate spans s 27.81..205.0, inside the envelope's 27.31..205.0.  Stated
    # rather than tested, because testing it again would only prove the same thing
    # more slowly.

    print()
    print("  THE STOP -- driven past home, it must not go")
    v = vol(sup & (Pos(0.0, 0.0, SEAT + OVERRUN) * drawn))
    print(f"    {OVERRUN:.1f} mm past home: {v:.2f} mm3 = {v/OVERRUN:.2f} mm2 of "
          f"section the stop presents to the plate's aft face")
    assert v / OVERRUN > 3.0, (
        f"the stop presents only {v/OVERRUN:.2f} mm2 to the plate -- it would slide "
        f"past and out of the tube's aft end, 209 mm down a 38 mm tube")
    print(f"    boost puts {P.F_BOOST_N:.2f} N on it: "
          f"{P.F_BOOST_N/(v/OVERRUN):.2f} MPa")
    assert P.F_BOOST_N / (v / OVERRUN) < 10.0, \
        f"the plate bears {P.F_BOOST_N/(v/OVERRUN):.1f} MPa on the stop"

    print()
    print("  CAPTURE -- lifted out of the pocket in x, it must not come")
    for sign, rail in ((1.0, "upper"), (-1.0, "lower")):
        dx = sign * (P.SLIDE_CLR_X + PROBE)
        v = vol(sup & (Pos(dx, 0.0, SEAT) * drawn))
        print(f"    x {dx:+.2f} mm: {v:.2f} mm3 into the {rail} rail")
        assert v > 1e-3, (
            f"the plate moved {dx:+.2f} mm in x -- past its {P.SLIDE_CLR_X:.2f} mm of "
            f"clearance -- and hit nothing.  The {rail} rail does not capture it, so "
            f"it is a plate resting in a channel and not a plate in a pocket")
    print(f"    (forward of s {P.S_RAIL_U_1:.0f} only, where the upper rail runs.  Aft "
          f"of it the two M3s hold the plate down, which is why they are there)")

    print()
    print("  THE SCREW PATH -- clear through BOTH parts at once")
    both = sup + plate
    for th in P.SCREW_THETA:
        v = vol(both & screw_probe(th))
        print(f"    theta {th:.0f}: {v:.3f} mm3 of material on a "
              f"{SCREW_PROBE_D:.1f} mm probe over r {P.R_OD - P.SCREW_L:.3f}.."
              f"{P.R_SHELL_O:.2f}")
        assert v < 1e-6, (
            f"{v:.3f} mm3 blocks the M3 at theta {th:.0f} -- the screw cannot be "
            f"driven home.  If the support's pilot is clear, the plate's lug pilot is "
            f"at the wrong station: it is drawn at s {P.S_LUG_PILOT:.1f} and has to "
            f"arrive at s {P.S_SCREW:.1f} after {SEAT:.1f} mm of seating")

    print()
    print("  THE LOADS")
    print(f"    flying mass {M_ALL:.2f} g = pair {P.M_SLED:.1f} + ESP32 "
          f"{P.M_ESP32:.1f} + BMP {P.M_BMP:.1f} + wiring {P.M_WIRING:.1f} + battery "
          f"{P.M_BATT_WORST:.1f}")
    f_boost, f_land = G_BOOST * M_ALL * G0, G_LANDING * M_ALL * G0
    print(f"    {G_BOOST:.0f} g boost {f_boost:.2f} N against F_BOOST_N "
          f"{P.F_BOOST_N:.2f};  {G_LANDING:.0f} g landing {f_land:.2f} N against "
          f"F_LANDING_N {P.F_LANDING_N:.2f}")
    assert abs(f_boost - P.F_BOOST_N) < 0.05 and abs(f_land - P.F_LANDING_N) < 0.05, (
        f"the committed forces no longer follow from the measured masses: "
        f"{f_boost:.2f}/{f_land:.2f} N against {P.F_BOOST_N}/{P.F_LANDING_N} -- a "
        f"part changed weight and F_BOOST_N/F_LANDING_N did not follow")
    print(f"    only {M_MOVING:.2f} g of that actually pulls on the screws (the "
          f"support is bolted to the airframe), i.e. "
          f"{G_LANDING * M_MOVING * G0:.2f} N -- F_LANDING_N is used below anyway")

    # Each lug is a cantilever standing off the plate: root at the deck's top face,
    # load at the screw's axis on the centreline.  In the FLAT print pose its layers
    # are planes of constant x -- perpendicular to the beam's own axis -- so this
    # bending stress is carried entirely across layer interfaces.  It is the one
    # number on this part that is not compared against bulk ABS.
    f_screw = P.F_LANDING_N / len(P.SCREW_THETA)
    arm = 0.0 - P.DECK_X_TOP                    # pilot axis is on x = 0
    lug_l = P.S_LUG_1 - P.S_LUG_0
    w_sec = P.LUG_DEPTH * lug_l ** 2 / 6.0      # bending about y, stress varies with z
    sigma = f_screw * arm / w_sec
    print(f"    lug root: {f_screw:.2f} N at {arm:.1f} mm on a "
          f"{P.LUG_DEPTH:.1f} x {lug_l:.1f} mm section, W {w_sec:.1f} mm3 -> "
          f"{sigma:.2f} MPa INTERLAYER")
    assert sigma < 0.4 * ABS_INTERLAYER_MPA, (
        f"the lug root sees {sigma:.1f} MPa across its layer lines against ABS's "
        f"~{ABS_INTERLAYER_MPA:.0f} -- lengthen the lug in z (it goes as the SQUARE "
        f"of {lug_l:.1f} mm) or drop LUG_X_TOP to shorten the {arm:.1f} mm arm")

    # Pullout: shear on the cylinder at the thread's major diameter, over the length
    # of thread the screw actually forms in the lug.
    thread = P.LUG_Y_O - (P.R_OD - P.SCREW_L)
    a_thread = math.pi * 3.0 * thread
    print(f"    thread pullout: {thread:.2f} mm of M3 in the lug, "
          f"{a_thread:.1f} mm2 of shear cylinder -> {f_screw/a_thread:.2f} MPa")
    assert f_screw / a_thread < 5.0, (
        f"{f_screw/a_thread:.1f} MPa on the lug's thread -- SCREW_L does not reach "
        f"far enough into it")

    print()
    print("  ASSEMBLY ORDER")
    print("    1.  print bay_support.py forward-end DOWN and bay_plate.py FLAT")
    print(f"    2.  populate the plate on the bench: BMP between the ribs at s "
          f"{P.S_RIB_BMP_0:.0f}, ESP32 over the pin slots, battery aft")
    print(f"    3.  seat the support in the airframe, crown into the bead at s "
          f"{P.S_CROWN:.2f}")
    print(f"    4.  slide the plate in from the FORWARD end, tail first, until it "
          f"stops on the plug at s {P.S_STOP:.1f} ({P.PLATE_L + SEAT:.1f} mm of "
          f"travel)")
    print(f"    5.  two M3 x {P.SCREW_L:.0f} through the airframe at s "
          f"{P.S_SCREW:.1f}, theta {P.SCREW_THETA[0]:.0f} and "
          f"{P.SCREW_THETA[1]:.0f} -- they catch the bosses AND the lugs")
    print("    to service it, back out the two screws and the plate draws straight "
          "out the way it went in")
