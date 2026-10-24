"""ONE half of the clamshell nose.  Print this file TWICE.

The second copy is not a mirror -- it is the SAME part rotated 180 deg about Z.
That matters: a mirrored part would need its own STL, its own slicer profile and
its own place in the bin, and someone would eventually print two of the same
hand.  Every feature here was placed so the 180 deg image lands correctly:

    shell body    half annulus y>0 becomes y<0
    hinge boss    centred on x = 0, so it maps onto itself
    latch hook    sits at +x, so its image sits at -x -- the two hooks stand
                  side by side in the split plane and can never collide, and
                  each one reaches under the SAME latch arm from its own side
    seam sockets  at MIRRORED x, equal z, so A's +x socket meets B's image of
                  its own -x socket.  Sockets on BOTH faces with loose dowels,
                  never a moulded pin: printing flat on the split face makes
                  y the build direction, so a pin sticking past y = 0 would
                  stick into the bed.  Only recesses are printable on a seam.
    root socket   ONE, at (POST_X, POST_Y), so its image lands at the opposite
                  corner and each half meets its OWN post on the base ring --
                  the assembly's only moulded-in pin, and it is on the ring
                  because of the bed argument above.  At -x, opposite the hook,
                  which is where the hook's weld is.
    vents         45/135 deg, no mating requirement

PRINT ORIENTATION -- this is load-bearing, not a suggestion
----------------------------------------------------------
Lay the half on its SPLIT FACE, y = 0 flat on the bed.  Layers then run ALONG
the rocket axis, so the hinge and latch loads are carried in-layer (~40 MPa for
ABS) instead of across the layer bond (~11 MPa).  Printed nose-up instead, every
one of those loads would be peeling layers apart.

The whole part measures 212.3 x 65.4 x 39.0 mm in that pose -- longer than the
bare shell because the latch hook hangs 16.3 mm below the root, and 39.0 rather
than 32.8 tall because the hinge fairing stands proud of the OD.

WHAT IT ASKS OF THE PRINTER, WHICH IS NOT "NOTHING"
--------------------------------------------------
It needs no support, and three of the four things that could have needed some do
not: the seam cut is a single plane at y = SEAM_SETBACK, so the entire flat face
lands on the bed with nothing floating above it; each successive layer of the
OUTER skin is narrower than the one below, so no part of it ever hangs out over
air; and the hinge boss grows in the +y build direction.

The ROOT POST SOCKET is a fifth thing that looks like it should need support and
does not: it is bored along +z, which in this pose is a BED direction, so it has no
downward-facing floor at all -- just a 2.70 mm slot in plan view whose largest
single-layer step is 0.3386 mm, 81 % of a bead.  Compare the dowel sockets, which
are bored along the build direction and each roof 8.55 mm2 of bridged floor.

The fourth is the CAVITY ROOF, and it does overhang -- an earlier version of this
docstring said "the skin never overhangs at all" and stopped there, which is true
of the skin and silent about the void behind it.  The cavity is the skin's
complement: it NARROWS as the print rises, so the material closes inward over air.
On the root section (cavity radius 30.754) it passes 45 deg at build height
21.75 mm, so the top 9.01 mm of every cross-section is shallower than that, with
the per-layer inward step growing 0.20 -> 0.32 -> 0.57 -> 0.89 -> 1.31 mm (48% ->
311% of a 0.42 mm bead) and closing on a 7.00 mm BRIDGE at the crown, under
2.01 mm of solid wall.

None of that needs support -- a 7 mm bridge in an enclosed ABS printer is routine,
and it is roofed by four more solid layers -- but it is where this part will look
worst inside, and it is worth knowing before blaming the model.  If the crown sags
enough to matter, the fix is slicer-side: raise the bridging flow, and cool the
bridge layer only.  Do not add support in there; the chute has to come out.

The hook's foot is the one place worth checking on the first print.  In this pose
its overhang is horizontal -- the foot reaches inboard in X, which is a bed
direction, not a build direction -- so it is a bridge of at most 2.57 mm under a
9.0 mm tall web, printed in-layer.  That bridges without support.  Printed
nose-up it would instead be an unsupported ledge in the build direction, on the
one face in this part that has to be flat and has to carry load; that is the
second reason the pose is not a suggestion.
"""

from __future__ import annotations

import math

import numpy as np
from build123d import Align, Box, Cone, Plane, Pos, Rot

import nose_build as B
import nose_params as P
import nose_profile as prof


def _hinge_boss():
    """Knuckle block at the +Y hinge, from the profile the sweep check ran on.

    The profile lives in nose_params.knuckle_profile() rather than here, because
    the swept-clearance check has to be run against the very polygon that gets
    built -- a second copy would drift and the check would be verifying nothing.
    Its outboard face is flush with the ring lug's, so the lug/knuckle/lug stack
    reads as one continuous fairing rather than three unrelated lumps.
    """
    return B.prism_yz(P.knuckle_profile(), -P.KNUCKLE_W / 2, P.KNUCKLE_W / 2)


def _tongue():
    """The latch HOOK and the gusset that ties it into the shell wall.

    One polygon, because the hook and the gusset are the same load path: the
    spring moment arrives at the wall, runs down the gusset's diagonal, down the
    web, and leaves through the FOOT'S TOP FACE upward into the latch arm's
    underside.  Splitting it into two solids would put a boolean seam right where
    the bending moment peaks.

    THE SHAPE IS A J AND THE DIRECTION IS THE ENTIRE POINT.  Every point of a
    half is inboard of its own hinge pin, so dz/dtheta = Y_PIN - |y| > 0: the
    tongue RISES as the half opens.  A blade resting ON TOP of the arm therefore
    lifts straight off it -- which is exactly what the previous version of this
    function built, and the reason it could not hold anything shut.  So the
    tongue drops past the arm on the inboard side (the web, at WEB_X_IN, which
    clears the arm's swept corner radius), turns outboard under it, and its FOOT
    catches the arm's underside at Z_LATCH_FACE.  Opening now drives the foot
    INTO the arm.

    The polygon and the foot's lead-in ramp both live in nose_params
    (tongue_profile / ramp_profile) rather than here, because the swept slot,
    seat and release checks have to run against the very polygon that gets built.
    A second copy would drift and those checks would be verifying nothing.
    """
    return B.prism_xz(P.tongue_profile(), P.TONGUE_Y0, P.TONGUE_Y1)


def _foot_ramp():
    """What turns the foot's top face from a flat into a lead-in ramp.

    Subtracted, not modelled into the J: the ramp falls in Y and the J is a
    profile in XZ, so it is a second prism at right angles to the first.  It
    reaches from x TONGUE_X0 - 1.0 (past the foot's inboard face, so the cut
    breaks out cleanly rather than leaving a sliver) to WEB_X_IN, which is where
    the web is -- outboard of that the ramp would eat into the web's root.
    """
    return B.prism_yz(P.ramp_profile(), P.TONGUE_X0 - 1.0, P.WEB_X_IN)


def _dowel_pad(z0: float, x_sign: int):
    """Local thickening at the seam so a dowel socket has material around it.

    The socket's axis is the seam normal (y), but the wall it goes into is only
    2.005 mm thick measured radially -- which at the seam means measured along x.
    A Ø3.2 socket centred DOWEL_INSET inboard of the skin therefore sits mostly in
    thin air, and needs a rib to live in.  Sized to the socket and no more: 1.2 mm
    of material inboard of the bore, 1.5 mm behind its bottom.

    In the print pose this is a prism extruded along the build direction, so its
    four sides are vertical walls -- but "every face is vertical", which this used
    to claim, is not right and the two exceptions are worth naming.  The outboard
    side is trimmed by the shell envelope rather than standing at x_hi, so it comes
    out as a patch of the ogive surface; that one is harmless, because the ogive's
    normal there tilts AWAY from the bed.  The socket is the real one: a blind
    Ø DOWEL_BORE hole bored straight up the build direction, so its floor is a
    downward-facing disc printed over air at y = SEAM_SETBACK + DOWEL_DEPTH.  A
    3.3 mm circular bridge, which needs no support but is why the pad carries
    1.5 mm of material behind the bore rather than 0.6.

    It doubles as a seam stiffener, which is the other reason the dowels are here.
    """
    r_out = float(prof.r_outer(z0))
    r_soc = r_out - P.DOWEL_INSET
    x_lo, x_hi = r_soc - (P.DOWEL_BORE / 2 + 1.2), r_out + 1.0
    pts = [(x_sign * x_lo, z0 - P.DOWEL_PAD_LEN / 2),
           (x_sign * x_hi, z0 - P.DOWEL_PAD_LEN / 2),
           (x_sign * x_hi, z0 + P.DOWEL_PAD_LEN / 2),
           (x_sign * x_lo, z0 + P.DOWEL_PAD_LEN / 2)]
    if x_sign < 0:
        pts = pts[::-1]
    pad = B.prism_xz(pts, P.SEAM_SETBACK, P.SEAM_SETBACK + P.DOWEL_DEPTH + 1.5)
    return pad, x_sign * r_soc


def _root_post_pad():
    """Local thickening at the root so the ring's post has a socket to enter.

    ONE of these, not a mirrored pair, and that is the whole trick: the socket sits
    at (POST_X, POST_Y), on the seam meridian, and half B is half A turned 180 deg
    about z, so B's socket lands at (-POST_X, -POST_Y).  Two halves, two sockets, two
    posts, and each half only ever meets its own.  Mirroring this to both signs of x
    would put a second socket where the OTHER half's post is not, and cost skin.

    AND IT SITS AT -x, WHICH IS THE MERIDIAN THE LATCH HOOK IS NOT ON.  That is not
    tidiness: with the full-depth gusset, the hook's weld to the shell IS the plane
    x = +30.7536 over y 0.15..3.15, and a Ø2.70 socket there would take 0.6795 mm out
    of that 3.0 mm weld at its most-stressed fibre -- 17 % of S, and the servo-jam
    margin falls from 1.22x to 1.02x.  The other meridian is bare skin: nearest dowel
    pad 62.1 mm further up, vents on the 45/135 deg meridians, knuckle out at y 35.76.

    The socket's axis is +z, which in this part's print pose lies IN the bed plane --
    so unlike the dowel sockets there is no downward-facing floor disc at all, and
    the largest single-layer step around the bore is 0.3386 mm against a 0.42 mm
    bead.  It is a strictly easier print than the dowel sockets it sits next to.

    Sized like _dowel_pad: 1.2 mm of material inboard of the bore, WALL_MIN above and
    below it in y, and 6.0 mm of length in z, which puts 2.0 mm of rib past the end of
    a 4.0 mm bore.  Its inboard face lands at r 27.068, 7.0 mm outside the chute bag,
    so it costs the parachute nothing.
    """
    r_out = float(prof.r_outer(P.Z_SHELL_ROOT))
    x_sign = 1 if P.POST_X >= 0 else -1
    x_lo = abs(P.POST_X) - (P.POST_BORE / 2 + 1.2)
    pts = [(x_sign * x_lo, P.Z_SHELL_ROOT),
           (x_sign * (r_out + 1.0), P.Z_SHELL_ROOT),
           (x_sign * (r_out + 1.0), P.Z_SHELL_ROOT + P.POST_PAD_LEN),
           (x_sign * x_lo, P.Z_SHELL_ROOT + P.POST_PAD_LEN)]
    if x_sign < 0:
        pts = pts[::-1]
    return B.prism_xz(pts, P.SEAM_SETBACK, P.POST_PAD_Y)


def gen_step():
    o, _ = B.ogive_tables()
    envelope = B.shell_envelope()

    # --- the shell itself, then the seam cut
    whole = B.shell_outer() - B.shell_cavity()
    half = whole - B.keepout_below_y(P.SEAM_SETBACK, whole)
    B.assert_cut(whole, half, 0.45 * whole.volume, "seam cut")
    B.assert_half(half, P.SEAM_SETBACK, "half shell")

    # --- hinge boss and pin bore
    s = half + _hinge_boss()
    # profile area ~34.7 mm2 x 10 mm wide = 347 mm3, less the ~35 mm3 that already
    # lies inside the wall between KNUCKLE_WEB_Y and the OD
    B.assert_add(half, s, 250.0, "hinge boss")
    bore = B.cyl_along("x", (-P.KNUCKLE_W / 2 - 1, P.Y_PIN, P.Z_PIN),
                       P.PIN_BORE_KNUCKLE, P.KNUCKLE_W + 2)
    t = s - bore
    B.assert_cut(s, t, 0.8 * math.pi * (P.PIN_BORE_KNUCKLE / 2) ** 2 * P.KNUCKLE_W,
                 "knuckle pin bore")
    s = t

    # --- torsion-spring leg seats, one blind hole in each knuckle end face.
    # Along x, because that is the only direction a seat can work here: the leg comes
    # off the coil INSIDE the pocket, so a groove in the face would sit under the leg
    # rather than around it, and a boss to bear on would be new printed material.  The
    # leg gets one 90 deg bend and drops in.  Sized, positioned and justified in
    # nose_params.spring_check(); _scratch/_seat_probe.py is the mesh proof that this
    # azimuth is solid (210..290 deg is not -- KNUCKLE_CHAMFER eats it).
    # Both holes overshoot their face by 0.5 mm into the pocket's air, so the mouth is
    # a clean break rather than a boolean that has to land exactly on a face.
    y_seat, z_seat = P.torsion_seat_yz(P.TORSION_SEAT_AZ_KNUCKLE)
    for sign in (+1, -1):
        x0 = (P.KNUCKLE_W / 2 - P.TORSION_SEAT_DEPTH if sign > 0
              else -P.KNUCKLE_W / 2 - 0.5)
        seat = B.cyl_along("x", (x0, y_seat, z_seat), P.TORSION_SEAT_D,
                           P.TORSION_SEAT_DEPTH + 0.5)
        t = s - seat
        B.assert_cut(s, t, 0.8 * math.pi * (P.TORSION_SEAT_D / 2) ** 2
                     * P.TORSION_SEAT_DEPTH, f"spring leg seat x_sign={sign}")
        s = t

    # --- latch hook: J profile, foot ramped, then clipped to the envelope so it
    #     cannot breach the skin
    tongue = _tongue()
    ramped = tongue - _foot_ramp()
    # 0.4 mm of drop over 2.0 mm of y across the 2.57 mm of exposed foot the ramp
    # cutter reaches (was 3.55 before LATCH_ARM_R pulled the web inboard) = 1.03 mm3.
    # Small, and the reason it gets its own assertion: a ramp that silently misses is
    # a flat foot, and a flat foot is a jam.
    B.assert_cut(tongue, ramped, 1.0, "foot lead-in ramp")
    tongue = ramped & envelope
    t = s + tongue
    # J profile 161.14 mm2 x 3.0 mm of y = 483.4 mm3, less the ramp and less the
    # sliver of the gusset's spur that is already inside the wall.  Was 126.58 /
    # 379.7 with the 0.6 mm gusset that snapped -- squaring the wall off full depth
    # IS the fix.  This said 152.19 / 456.6, which was right when it was written and
    # is the same staleness as the "# 24.05" that sat on WEB_X_IN: the remaining
    # +8.82 mm2 is not tongue that was added, it is POCKET that stopped being cut,
    # WEB_X_IN coming 24.05 -> 23.07 over 9.0 mm of pocket height when LATCH_ARM_R
    # went 23.0 -> 22.0 (the same move line 258's "was 3.55" records).  Measure it,
    # do not trust it: shapely on nose_params.tongue_profile() is the one source.
    B.assert_add(s, t, 420.0, "latch hook")
    s = t

    # --- seam dowel sockets: pads first, then bore, both at mirrored x
    for z0 in P.DOWEL_Z:
        for sign in (+1, -1):
            pad, x_soc = _dowel_pad(z0, sign)
            t = s + (pad & envelope)
            B.assert_add(s, t, 40.0, f"dowel pad z={z0} x_sign={sign}")
            s = t
            soc = B.cyl_along("y", (x_soc, P.SEAM_SETBACK - 0.01, z0),
                              P.DOWEL_BORE, P.DOWEL_DEPTH)
            t = s - soc
            B.assert_cut(s, t, 0.8 * math.pi * (P.DOWEL_BORE / 2) ** 2 * P.DOWEL_DEPTH,
                         f"dowel socket z={z0} x_sign={sign}")
            s = t

    # --- root post socket: the ONE place this assembly has a moulded-in pin, and it
    # belongs to the base ring, not to the other half.  Pad, bore, then break the
    # mouth -- the chamfer is what lets the half find the post while it is still
    # skewed, and it is capped at 0.3554 mm by the skin outboard of it.
    #
    # It is on the -x meridian, and this threshold is what caught that.  Placed at +x it
    # added only 51.6 mm3, because the full-depth gusset ALREADY fills that corner --
    # which is another way of saying the bore would have gone through the hook's weld
    # (0.6795 of its 3.0 mm, at z = Z_SHELL_ROOT, the extreme fibre: 17 % of S, and the
    # servo-jam margin back down to 1.02x).  At -x it is bare skin and adds 113.0 of the
    # 182.6 mm3 the clipped pad occupies.  _scratch/_post_probe.py is the mesh proof
    # that the pad is one-sided and that the +x weld is continuous across all 3.0 mm.
    t = s + (_root_post_pad() & envelope)
    B.assert_add(s, t, 95.0, "root post pad")
    s = t
    soc = B.cyl_along("z", (P.POST_X, P.POST_Y, P.Z_SHELL_ROOT - 0.01),
                      P.POST_BORE, P.POST_BORE_DEPTH + 0.01)
    t = s - soc
    B.assert_cut(s, t, 0.8 * math.pi * (P.POST_BORE / 2) ** 2 * P.POST_BORE_DEPTH,
                 "root post socket")
    s = t
    mouth = Pos(P.POST_X, P.POST_Y, P.Z_SHELL_ROOT - 1e-6) * Cone(
        bottom_radius=P.POST_BORE / 2 + P.POST_MOUTH_CHAMFER,
        top_radius=P.POST_BORE / 2, height=P.POST_MOUTH_CHAMFER,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    t = s - mouth
    B.assert_cut(s, t, 0.3, "root post socket mouth chamfer")
    s = t

    # --- vents
    r_v = float(prof.r_outer(P.Z_VENT))
    for th in P.VENT_THETA:
        t = s - B.radial_hole(P.VENT_D, th, P.Z_VENT, r_v - 6.0, r_v + 3.0)
        B.assert_cut(s, t, 0.5 * math.pi * (P.VENT_D / 2) ** 2 * P.WALL,
                     f"vent at {th} deg")
        s = t

    # --- root chamfer, so the butt joint cannot be held open by a print corner
    t = s - B.chamfer_ring_cutter(P.R_AIRFRAME, P.Z_SHELL_ROOT, P.ROOT_CHAMFER, True)
    B.assert_cut(s, t, 5.0, "root chamfer")
    s = t

    s.label = "half_shell"
    return s


if __name__ == "__main__":
    import nose_checks as C
    s = gen_step()
    lo, hi = B.bbox(s)
    print(f"half_shell  vol {s.volume/1000:8.2f} cm3   mass "
          f"{s.volume/1000*P.ABS_DENSITY:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")
    print(f"  print pose (on the split face): "
          f"{hi[2]-lo[2]:.1f} x {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} mm")
