"""The whole nose, assembled, for looking at rather than printing.

Two configurations come out of the same source:

    nose_assembly.py       LATCHED and closed   -- how it flies
    nose_assembly_open.py  RELEASED and open    -- how it deploys

Nothing here re-describes the geometry.  Every part is imported from its own
generator and placed by the two joints the mechanism actually has:

    hinge_pY / hinge_mY   RevoluteJoint on the base ring, one per hinge, on the
                          pin axis at (0, +-Y_PIN, Z_PIN).  Drives `open_deg`.
    latch_shaft           RevoluteJoint on the bulkhead, on the servo output
                          axis.  Drives the LATCH_SWEEP release.

and one static mate:

    bulkhead_seat         RigidJoint pair, the ring's seat face at SEAT_Z1 to the
                          bulkhead's underside at Z_BULK_BOT.

That last one is not decoration.  The bulkhead's own generator puts its underside
at Z_BULK_BOT and the ring's puts the seat at SEAT_Z1; connecting them means the
seat POSITIONS the bulkhead, and the assertion below then catches the day those
two constants stop agreeing.  A raw transform would have quietly kept building.

WHY THE JOINT PLACEMENTS ARE STILL CHECKED AGAINST HAND MATHS
-------------------------------------------------------------
`RevoluteJoint.connect_to` composes `axis.location * Rz(angle) *
rigid.relative_location.inverse()`, so the ANGLE IS MEASURED ABOUT THE AXIS
DIRECTION YOU GAVE IT and the moving part picks up the axis frame's orientation.
Get the axis direction backwards and you get a perfectly clean assembly opening
the wrong way; get the RigidJoint's orientation wrong and the part arrives rotated
90 deg with no complaint at all.  So each hinge axis points along -sign*X (which
makes a POSITIVE angle open outward, matching nose_params.rotate_open), and every
placement is asserted vertex-for-vertex against `hinge_m()`, plain numpy built
straight from the datum.  Both were wrong once; that is why the check is here.

WHAT IS IN HERE THAT YOU DO NOT PRINT
-------------------------------------
The servo, the two hinge pins and the four seam dowels are reference bodies,
labelled `_REF_`.  A viewer showing only printed parts shows an empty cavity and
four disconnected lumps -- you cannot see that the MG90S goes in the cradle, that
its hub lands in the arm's pocket, or which way the pins run.  Do not send them to
a slicer.  The printed set is exactly the four part files.
"""

from __future__ import annotations

import math

import numpy as np
from build123d import (Align, Axis, Box, Compound, Cylinder, Location, Plane,
                       Polyline, Pos, RevoluteJoint, RigidJoint, Rot, extrude,
                       make_face)

import base_ring
import bulkhead
import half_shell
import latch_arm
import nose_build as B
import nose_params as P

OPEN_MAX = 110.0          # the largest angle nose_verify.py clears the halves at
# The horn's four numbers used to be LOCAL literals here -- 8.0 / 4.7 / 4.4 / 9.0, the
# nominal single-arm MG90S horn -- while nose_params carried the MEASURED double-arm
# ones.  So the reference servo in every assembly and every render was drawn with a
# 9 mm single blade while latch_arm.py was cutting a 36.8 mm slot for a 36 mm double
# one, and the picture agreed with itself and with nothing else.  There is one source
# of truth for this and it is nose_params.HORN_*.
FLANGE_T = 2.5
FLANGE_EAR = 2.2          # how far the ears reach past their screw holes


# --------------------------------------------------------------------------
# datums
# --------------------------------------------------------------------------

def hinge_axis(sign: int) -> Axis:
    """The pin axis of one hinge, pointed so a POSITIVE angle opens that half.

    nose_params.rotate_open maps dz -> +y for the +Y half, i.e. a rotation about
    +X by MINUS theta.  Rotating by +theta about -X is the same motion, and it
    keeps every joint angle in this file positive and inside angular_range.
    """
    return Axis((0.0, sign * P.Y_PIN, P.Z_PIN), (-sign * 1.0, 0.0, 0.0))


SHAFT_AXIS = Axis((0.0, 0.0, P.Z_ARM_BOT), (0.0, 0.0, 1.0))


def hinge_m(deg: float, sign: int) -> np.ndarray:
    """The same rotation as `hinge_axis(sign)` at `deg`, as a bare 4x4.

    Independent of build123d, and of the joint machinery, on purpose: it is what
    the joints get checked against.
    """
    a = np.radians(-sign * deg)                    # about +X, per rotate_open
    c, s = np.cos(a), np.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2] = c, -s
    m[2, 1], m[2, 2] = s, c
    p = np.array([0.0, sign * P.Y_PIN, P.Z_PIN])
    m[:3, 3] = p - m[:3, :3] @ p
    return m


def rz_m(deg: float) -> np.ndarray:
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 1] = c, -s
    m[1, 0], m[1, 1] = s, c
    return m


def _verts(shape) -> np.ndarray:
    return np.array([tuple(v) for v in shape.vertices()])


def _apply(m: np.ndarray, v: np.ndarray) -> np.ndarray:
    return (v @ m[:3, :3].T) + m[:3, 3]


def _pointset_err(a: np.ndarray, b: np.ndarray) -> float:
    """Two-sided nearest-neighbour distance between two vertex clouds.

    NOT a sorted element-wise diff.  Sorting vertices lexicographically looks
    equivalent and is not: build123d substitutes a 360 deg rotation for a
    requested 0 deg, which leaves ~1e-15 of noise in x, and that is enough to
    swap two vertices that share an x and a y.  The sorted diff then reports the
    5.2 mm gap between those two vertices as a placement error, on an assembly
    whose bounding box is identical to the millimetre.  Matching points to their
    nearest neighbour cannot be fooled that way.
    """
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    return float(max(d.min(axis=1).max(), d.min(axis=0).max()))


def _assert_placed(shape, raw_verts: np.ndarray, m: np.ndarray, what: str) -> None:
    got = _verts(shape)
    want = _apply(m, raw_verts)
    assert len(got) == len(want), \
        f"{what}: {len(got)} vertices placed, {len(want)} expected"
    err = _pointset_err(got, want)
    assert err < 1e-6, f"{what}: joint placement is {err:.2e} mm off the datum maths"


# --------------------------------------------------------------------------
# reference bodies -- not printed
# --------------------------------------------------------------------------

def _servo():
    """MG90S envelope: case, flange plate with both ears, hub and lever.

    Built from SERVO_BODY_Y rather than from a half-length either side of the
    shaft.  The case is not symmetric about the shaft -- it runs -6.2..+16.6 --
    and drawing it symmetric is the mistake that makes a cradle look right in a
    picture and refuse the servo on the bench.
    """
    hw = P.SERVO_W / 2
    y0, y1 = P.SERVO_BODY_Y
    case = Pos(-hw, y0, P.Z_SERVO_BOT) * Box(
        P.SERVO_W, y1 - y0, P.SERVO_H, align=(Align.MIN,) * 3)
    ya = P.SERVO_HOLE_Y[0] - FLANGE_EAR
    yb = P.SERVO_HOLE_Y[1] + FLANGE_EAR
    flange = Pos(-hw, ya, P.Z_FLANGE_FACE) * Box(
        P.SERVO_W, yb - ya, FLANGE_T, align=(Align.MIN,) * 3)
    hub = B.cyl_along("z", (0, 0, P.Z_SERVO_TOP), P.HORN_HUB_D, P.HORN_HUB_H)
    # DOUBLE-arm, so the blade spans -HORN_LEVER_R..+HORN_LEVER_R = 36 mm tip to tip.
    # Drawn as one bar through the hub rather than two spurs off it, because that is
    # what the slot in latch_arm.py is: a single 36.8 mm through-slot.
    #
    # AND IT IS NOT A RECTANGLE.  It was, for as long as HORN_LEVER_W was a single
    # invented number; the MEASURED blade is 7.2 wide across its middle 22.5 mm and
    # tapers to 4.1 at the tips, so the reference solid is the hexagonal envelope
    # nose_params.horn_lever_w() describes.  Drawing it as a 4.6 mm bar is what let
    # the arm's slot be sized to something no horn has ever been, and having the
    # reference solid agree with the pocket by construction is precisely the circular
    # reasoning this whole block of parameters exists to break -- so the outline is
    # built from the horn_lever_w() envelope, which is measurement, and the pocket is
    # built from HORN_SLOT_*, which is design, and self_check() walks one against the
    # other.  They are allowed to disagree; that is the point.
    zb = P.Z_SERVO_TOP + P.HORN_HUB_H - P.HORN_BLADE_T
    hw_mid = P.horn_lever_w(0.0) / 2
    hw_tip = P.horn_lever_w(P.HORN_LEVER_R) / 2
    outline = [(-P.HORN_LEVER_R, hw_tip), (-P.HORN_LEVER_W_FULL, hw_mid),
               (P.HORN_LEVER_W_FULL, hw_mid), (P.HORN_LEVER_R, hw_tip),
               (P.HORN_LEVER_R, -hw_tip), (P.HORN_LEVER_W_FULL, -hw_mid),
               (-P.HORN_LEVER_W_FULL, -hw_mid), (-P.HORN_LEVER_R, -hw_tip)]
    blade = Pos(0, 0, zb) * extrude(
        make_face(Polyline(*[(x, y, 0.0) for x, y in outline], close=True)),
        P.HORN_BLADE_T)
    s = case + flange + hub + blade
    s.label = "_REF_MG90S_servo"
    return s


def _pins():
    out = []
    for sign in (+1, -1):
        p = B.cyl_along("x", (-P.PIN_LEN / 2, sign * P.Y_PIN, P.Z_PIN),
                        P.D_PIN, P.PIN_LEN)
        p.label = f"_REF_hinge_pin_{'pY' if sign > 0 else 'mY'}"
        out.append(p)
    return out


def _retain_screws():
    """The two airframe retention screws, drawn where they actually end up.

    Modelled at the M2.5 MAJOR diameter, not at the Ø2.1 pilot, so each one visibly
    interferes with the spigot wall by 0.2 mm of radius.  That interference is the
    thread: a self-tapper is supposed to displace material.  Drawing the shank at
    the pilot diameter instead would look tidy and would hide the one thing worth
    seeing here, which is how much thread is actually in the pad.

    The head is drawn with its underside ON R_AIRFRAME because that is where it
    sits, and the airframe is not part of this scene, so there is a visible 1.6379
    mm gap under it.  That gap is NOT all tube wall, which is what this docstring
    used to say: it is 1.4741 mm of tube wall plus the 0.1638 mm of radial
    clearance in the socket, and the second term is the one worth seeing, because
    it is the slop these two screws exist to take out.  The tip stops 0.56 mm short
    of the pilot floor; that gap is why this is an M2.5 x 8 and not an x 10.
    """
    out = []
    for th in P.RETAIN_THETA:
        a = math.radians(th)
        d = (math.cos(a), math.sin(a), 0.0)
        r_tip = P.R_AIRFRAME - P.RETAIN_SCREW_LEN
        pl = Plane(origin=(r_tip * d[0], r_tip * d[1], P.Z_RETAIN),
                   x_dir=(0, 0, 1), z_dir=d)
        shank = pl * Cylinder(radius=1.25, height=P.RETAIN_SCREW_LEN,
                              align=(Align.CENTER, Align.CENTER, Align.MIN))
        head = pl * Pos(0, 0, P.RETAIN_SCREW_LEN) * Cylinder(
            radius=2.5, height=1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
        s = shank + head
        s.label = f"_REF_retain_screw_M2.5x8_th{th:.0f}"
        out.append(s)
    return out


def _dowels(open_deg: float = 0.0):
    """The four seam dowels, GLUED INTO HALF A and therefore riding with it.

    Which half they are glued into is not a detail, and drawing them centred on
    the split plane -- as this used to, with a 10 mm rod bottoming in neither
    socket -- hid the fact that they could not withdraw.  A dowel has to come out
    of half B while both halves rotate away from each other, and the sideways skew
    it has to survive grows with the SQUARE of how far it reaches into B while the
    withdrawal only grows linearly.  Centred, they jammed 2.8 deg into the
    opening.  See nose_params.dowel_withdrawal(), which now sweeps it.

    So: bottomed in half A's socket, DOWEL_LEN long, and shown in the open pose as
    well as the closed one, carried by half A's own hinge placement.  In the open
    assembly they should stand proud of A's seam face with clear air around them,
    and if a future edit makes one intersect half B it will be visible instead of
    hidden behind an `if open_deg == 0.0`.
    """
    import nose_profile as prof
    out = []
    y_hi = P.SEAM_SETBACK + P.DOWEL_DEPTH          # bottomed in half A
    y_lo = y_hi - P.DOWEL_LEN
    # half A's placement, spelled with the same primitives as everything else here
    # and then checked against hinge_m() -- a rotation about an axis parallel to X
    # through (0, Y_PIN, Z_PIN), by -open_deg, per hinge_axis()'s note.
    place = (Pos(0, P.Y_PIN, P.Z_PIN) * Rot(-open_deg, 0, 0)
             * Pos(0, -P.Y_PIN, -P.Z_PIN))
    for z0 in P.DOWEL_Z:
        x_soc = float(prof.r_outer(z0)) - P.DOWEL_INSET
        for sign in (+1, -1):
            rest = B.cyl_along("y", (sign * x_soc, y_lo, z0), P.DOWEL_D, P.DOWEL_LEN)
            raw = _verts(rest)
            d = place * rest
            d.label = f"_REF_dowel_z{z0:.0f}_x{'p' if sign > 0 else 'm'}"
            _assert_placed(d, raw, hinge_m(open_deg, +1), f"dowel {d.label}")
            out.append(d)
    return out


# --------------------------------------------------------------------------

def build(open_deg: float = 0.0, released: bool = False) -> Compound:
    assert 0.0 <= open_deg <= OPEN_MAX, f"open_deg must be 0..{OPEN_MAX}"

    ring = base_ring.gen_step()
    ring.label = "base_ring"
    bulk = bulkhead.gen_step()
    bulk.label = "bulkhead"
    arm = latch_arm.gen_step()
    arm.label = "latch_arm_" + ("released" if released else "latched")
    shell_a = half_shell.gen_step()
    shell_a.label = "half_shell_A"
    shell_b = Rot(0, 0, 180.0) * half_shell.gen_step()
    shell_b.label = "half_shell_B_same_part_rotated_180"

    raw = {s.label: _verts(s) for s in (ring, bulk, arm, shell_a, shell_b)}

    # --- static mate: the ring's seat face carries the bulkhead ---------------
    RigidJoint("bulkhead_seat", to_part=ring,
               joint_location=Location((0, 0, P.SEAT_Z1)))
    RigidJoint("seat_face", to_part=bulk,
               joint_location=Location((0, 0, P.Z_BULK_BOT)))
    ring.joints["bulkhead_seat"].connect_to(bulk.joints["seat_face"])
    _assert_placed(bulk, raw["bulkhead"], np.eye(4),
                   "bulkhead on the ring seat")   # SEAT_Z1 must equal Z_BULK_BOT

    # --- the latch: arm on the servo output axis, which the bulkhead holds ----
    RevoluteJoint("latch_shaft", to_part=bulk, axis=SHAFT_AXIS,
                  angular_range=(0.0, P.LATCH_SWEEP))
    RigidJoint("horn_hub", to_part=arm, joint_location=SHAFT_AXIS.location)
    sweep = P.LATCH_SWEEP if released else 0.0
    bulk.joints["latch_shaft"].connect_to(arm.joints["horn_hub"], angle=sweep)
    _assert_placed(arm, raw[arm.label], rz_m(sweep), "latch arm on its shaft")

    # --- the hinges ----------------------------------------------------------
    for sign, shell in ((+1, shell_a), (-1, shell_b)):
        tag = "pY" if sign > 0 else "mY"
        RevoluteJoint(f"hinge_{tag}", to_part=ring, axis=hinge_axis(sign),
                      angular_range=(0.0, OPEN_MAX))
        RigidJoint(f"pin_{tag}", to_part=shell,
                   joint_location=hinge_axis(sign).location)
        ring.joints[f"hinge_{tag}"].connect_to(shell.joints[f"pin_{tag}"],
                                              angle=open_deg)
        _assert_placed(shell, raw[shell.label], hinge_m(open_deg, sign),
                       f"half shell on hinge {tag}")

    kids = [ring, bulk, arm, shell_a, shell_b, _servo(), *_pins(),
            *_retain_screws(), *_dowels(open_deg)]

    asm = Compound(children=kids)
    asm.label = "nose_open" if open_deg else "nose_closed"
    return asm


def gen_step():
    return build(0.0, released=False)


def report(asm: Compound) -> None:
    lo, hi = B.bbox(asm)
    printed = [c for c in asm.children if not c.label.startswith("_REF_")]
    vol = sum(c.volume for c in printed)
    print(f"{asm.label:11s} {len(asm.children)} bodies "
          f"({len(printed)} printed, {len(asm.children) - len(printed)} reference)")
    print(f"  printed volume {vol / 1000:7.2f} cm3 = "
          f"{vol / 1000 * P.ABS_DENSITY:6.1f} g ABS")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}"
          f"   z {lo[2]:8.3f}..{hi[2]:8.3f}")
    for c in asm.children:
        clo, chi = B.bbox(c)
        print(f"    {c.label:38s} {c.volume / 1000:7.2f} cm3   "
              f"z {clo[2]:8.3f}..{chi[2]:8.3f}")


if __name__ == "__main__":
    for deg, rel in ((0.0, False), (100.0, True)):
        report(build(deg, rel))
