"""Verification of the EXPORTED artifacts in out/, not of the build scripts.

Everything up to now was checked in CAD, against the same numbers that built the
geometry.  That catches arithmetic mistakes but it cannot catch an export that
lost a feature, a boolean that left a sliver shell behind, or two parts that
occupy the same millimetre of space.  So this module reads the STL files back and
asks questions whose answers were decided elsewhere:

    1. is each mesh a closed, positive-volume, single body
    2. does each part fit the bed IN ITS PRINT POSE (not its assembly pose)
    3. does the exported ogive still agree with nose_profile
    4. for every feature: probe the azimuth/coordinate it is supposed to be at
       AND one it is supposed to MISS.  A hole that was never cut passes the
       first probe's negation only; it takes both to pin a feature down.
    5. do any two parts interpenetrate in the assembled position
    6. does the mechanism actually HOLD -- with the arm latched, does opening the
       half by a fraction of a degree drive the hook's foot INTO the arm
    7. and does it actually RELEASE -- with the arm swept LATCH_SWEEP, is the
       whole 0..110 deg travel clear of it

(6) and (7) are a pair and neither is optional.  An earlier version of this file
had only the release half of it, plus a check that the tongue and the arm touched
when latched, and both passed on a mechanism that could not hold the nose shut at
all: the contact was on the wrong side of the arm, so opening lifted the tongue
off it instead of driving it in.  Contact is not resistance.  Ask for the
collision.

On (5): the ring/bulkhead/arm stack is designed to TOUCH on three coincident
faces (seat, thrust pad, blade), so a surface-to-surface distance would read zero
and prove nothing.  The test used instead samples one part's surface, steps
`BITE` INTO that part along its own normal, and asks whether those strictly
interior points are inside the other part.  Coincident faces then read clean and
real overlap reads as a hit count with a depth.

On (4): the mesh surface of a curved face lies INSIDE the nominal radius by one
chord sagitta, so a probe placed analytically at exactly r = R falls outside the
solid over most of each facet.  Probes on curved boundaries are offset inward.
Probes on planar boundaries -- which is most of this mechanism -- need no offset,
and are deliberately placed away from edges so that faceting cannot reach them.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import trimesh

import nose_checks as C
import nose_params as P
import nose_profile as prof

OUT = Path(__file__).parent / "out"
BITE = 0.05          # how far inside a part its surface samples are pushed
N_SAMP = 12000       # surface samples per interference direction
N_GAP = 8000         # surface samples per closest-approach measurement
CHUNK = 900          # points per containment call -- see inside()
CHUNK_GAP = 500      # points per proximity call -- smaller, see gap()

FAILS: list[str] = []
NOTES: list[str] = []


# --------------------------------------------------------------------- helpers

def check(cond: bool, ok_msg: str, bad_msg: str) -> bool:
    """Record a pass or a failure without aborting -- one run, all the news."""
    if cond:
        NOTES.append(f"  ok   {ok_msg}")
    else:
        FAILS.append(bad_msg)
        NOTES.append(f"  FAIL {bad_msg}")
    return cond


def inside(mesh: trimesh.Trimesh, pts) -> np.ndarray:
    """Point-in-mesh, in chunks.

    trimesh's pure-Python ray intersector (there is no embree here) builds a
    ray x triangle candidate array, so 12000 points against the 22842-triangle
    ogive asks numpy for 168 MiB in one go and raises.  Chunking costs nothing
    and keeps the peak flat regardless of part size or sample count.
    """
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    if len(pts) <= CHUNK:
        return mesh.contains(pts)
    return np.concatenate([mesh.contains(pts[i:i + CHUNK])
                           for i in range(0, len(pts), CHUNK)])


def expect_points(mesh, label: str, cases) -> None:
    """cases: [(point, want_solid, why), ...].  One containment call for all."""
    pts = [c[0] for c in cases]
    got = inside(mesh, pts)
    for (p, want, why), g in zip(cases, got):
        state = "SOLID" if g else "void"
        wanted = "SOLID" if want else "void"
        check(bool(g) == want,
              f"{label}: {why} -- {state} at ({p[0]:8.3f},{p[1]:8.3f},{p[2]:8.3f})",
              f"{label}: {why} -- wanted {wanted}, got {state} at "
              f"({p[0]:.3f},{p[1]:.3f},{p[2]:.3f})")


def outer_r_by_ray(mesh, theta_deg: float, z: float,
                   r_solid: float, r_void: float, tol: float = 2e-4) -> float:
    """Radius of the outer surface, found by bisection along a radial ray.

    Ray casting rather than max-vertex-radius of a z section: on a tapered
    surface the section's vertices sit at the facet corners of a DIFFERENT z, so
    the section over-reads.  A ray at one (theta, z) has no such bias.
    """
    lo, hi = r_solid, r_void
    assert inside(mesh, [C.cyl(lo, theta_deg, z)])[0], f"r={lo} not solid"
    assert not inside(mesh, [C.cyl(hi, theta_deg, z)])[0], f"r={hi} not void"
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if inside(mesh, [C.cyl(mid, theta_deg, z)])[0]:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def interference(a: trimesh.Trimesh, b: trimesh.Trimesh,
                 n: int = N_SAMP) -> tuple[int, float]:
    """(hits, max depth) for points strictly inside A that are also inside B."""
    pts, fid = trimesh.sample.sample_surface(a, n)
    pts = np.asarray(pts) - a.face_normals[fid] * BITE
    hit = inside(b, pts)
    if not hit.any():
        return 0, 0.0
    # chunked as in gap(): this branch only runs when something is already wrong,
    # and a MemoryError here would throw away the depth that says HOW wrong
    bad = pts[hit]
    deep = max(float(np.max(trimesh.proximity.signed_distance(b, bad[i:i + CHUNK_GAP])))
               for i in range(0, len(bad), CHUNK_GAP))
    return int(hit.sum()), deep


def assert_disjoint(a, b, label: str) -> None:
    """Both directions: A poking into B and B poking into A."""
    ha, da = interference(a, b)
    hb, db = interference(b, a)
    check(ha == 0 and hb == 0,
          f"{label}: no interpenetration ({N_SAMP} samples each way, "
          f"coincident faces tolerated by a {BITE} mm bite)",
          f"{label}: INTERPENETRATES -- {ha} interior points of the first inside "
          f"the second (max depth {da:.3f} mm), {hb} the other way "
          f"(max depth {db:.3f} mm)")


def gap(a: trimesh.Trimesh, b: trimesh.Trimesh, n: int = N_GAP) -> float:
    """Closest surface-to-surface approach, sampled on B and measured to A.

    on_surface returns (closest_points, distance, triangle_id) IN THAT ORDER.
    Taking the first return value as the distance yields a min over raw x/y/z
    coordinates, which is negative for anything straddling the origin and looks
    exactly like a collision.  It is not one.

    Chunked for the same reason inside() is, and it bites harder here: trimesh's
    closest_point builds several point x candidate-triangle arrays at once, so
    8000 samples against a 22842-triangle half shell asked numpy for 173 MiB in
    one block and raised.  The result is a min over independent points, so
    chunking changes nothing about the answer.
    """
    pts, _ = trimesh.sample.sample_surface(b, n)
    pts = np.asarray(pts)
    best = np.inf
    for i in range(0, len(pts), CHUNK_GAP):
        _, d, _ = a.nearest.on_surface(pts[i:i + CHUNK_GAP])
        best = min(best, float(np.min(d)))
    return best


def rx(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0])


def rz(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1])


def hinge_open(deg: float) -> np.ndarray:
    """The half shell's opening rotation: about the pin axis, x-parallel.

    nose_params.rotate_open maps dz -> +y, which is a rotation about +x by
    MINUS theta.  Reproduced here through the same helper's sign convention so
    the mesh sweep and the analytic sweep cannot disagree.
    """
    m = trimesh.transformations.rotation_matrix(
        math.radians(-deg), [1, 0, 0], [0.0, P.Y_PIN, P.Z_PIN])
    y, z = P.rotate_open(P.Y_PIN, P.Z_PIN + 10.0, deg)
    q = m @ np.array([0.0, P.Y_PIN, P.Z_PIN + 10.0, 1.0])
    assert abs(q[1] - y) < 1e-9 and abs(q[2] - z) < 1e-9, "sweep sign mismatch"
    return m


def moved(mesh: trimesh.Trimesh, m: np.ndarray) -> trimesh.Trimesh:
    out = mesh.copy()
    out.apply_transform(m)
    return out


# ------------------------------------------------------------------- per part

def basics(mesh, name: str, print_pose: np.ndarray, cad_vol_cm3: float) -> None:
    C.assert_watertight(mesh, name)
    C.assert_single_body(mesh, name)
    NOTES.append(f"  ok   {name}: watertight, 1 body, "
                 f"vol {mesh.volume/1000:.2f} cm3, "
                 f"mass {C.mass_g(mesh):.1f} g ABS")
    check(abs(mesh.volume / 1000 - cad_vol_cm3) < 0.06 * max(1.0, cad_vol_cm3),
          f"{name}: mesh volume agrees with the CAD solid "
          f"({mesh.volume/1000:.2f} vs {cad_vol_cm3:.2f} cm3)",
          f"{name}: mesh volume {mesh.volume/1000:.2f} cm3 disagrees with the CAD "
          f"solid's {cad_vol_cm3:.2f} cm3 by more than tessellation can explain")
    e = moved(mesh, print_pose).extents
    check(all(e[i] <= P.BED[i] for i in range(3)),
          f"{name}: print pose {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm fits the "
          f"{P.BED[0]:.0f} mm bed",
          f"{name}: print pose {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm does NOT "
          f"fit the bed {P.BED}")


def verify_base_ring(m) -> None:
    n = "base_ring"
    r_sp, r_bore, r_af = P.R_SPIGOT, P.RING_BORE, P.R_AIRFRAME
    sag = C.chord_sagitta(r_af, m)

    th_a, th_b = P.RETAIN_THETA
    z_r = P.Z_RETAIN

    expect_points(m, n, [
        # --- the spigot really is a reduced diameter, not just a chamfer.
        # Scanned at 45 deg, NOT at 0 as it used to be: azimuth 0 is now the
        # retention pilot's own axis, and a radial scan along a hole reads the
        # hole, then reports it as a missing wall.
        (C.cyl(20.0, 45.0, 13.0), False, "spigot: bore is open at r=20"),
        (C.cyl(0.5 * (r_bore + r_sp), 45.0, 13.0), True,
         "spigot: wall at mid-thickness"),
        (C.cyl(r_af - 0.3, 45.0, 13.0), False,
         "spigot: nothing out at the airframe OD below the shoulder"),
        # --- airframe retention, part 1: the pads.  r = 26 is the discriminator --
        # at this height that radius is open bore at every other azimuth, so SOLID
        # there can only be pad.
        (C.cyl(26.0, th_a, 6.0), True, "retention pad at 0: solid at r=26, in the bore"),
        (C.cyl(26.0, th_b, 6.0), True, "retention pad at 180: solid at r=26"),
        (C.cyl(26.0, 90.0, 6.0), False, "no pad at 90: bore is open at r=26"),
        (C.cyl(26.0, 270.0, 6.0), False, "no pad at 270: bore is open at r=26"),
        ((0.0, P.Y_CORD_HOLE, 6.0), False,
         "and the shock cord's drop at azimuth 270 is clear of both pads"),
        # the chord limit, from both sides -- this is what makes it a PAD and not a
        # ring, and a ring would swallow the bay
        (C.cyl(26.0, 9.0, 6.0), True, "pad at 0: still there 4.07 mm along the chord"),
        (C.cyl(26.0, 15.0, 6.0), False,
         "pad at 0: gone by 6.73 mm along the chord, so it is chord-limited"),
        # the corner where the r=23.20 cylinder meets the chord plane.  x = 23.0
        # here is INBOARD of that radius: this is the bulge RETAIN_X_MIN measures.
        ((23.0, 5.0, 6.0), True, "pad at 0: material at |x| 23.0 where y = 5.0"),
        ((23.0, 6.5, 6.0), False, "pad at 0: none at y = 6.5, past the chord"),
        # z extent: full thickness to 15.479, then a 45 deg cone, and it starts on
        # the bed at z = 0
        (C.cyl(26.0, th_a, 0.5), True, "pad at 0: starts at z=0, prints off the bed"),
        (C.cyl(24.0, th_a, 10.0), True, "pad at 0: full thickness in to r=24"),
        (C.cyl(24.0, th_a, 18.0), False,
         "pad at 0: by z=18 the 45 deg top cone has pulled the inboard face back "
         "out past r=24"),
        (C.cyl(26.5, th_a, 18.0), True,
         "pad at 0: but still solid at r=26.5 there -- a cone, not a step"),
        (C.cyl(26.0, th_a, 22.0), False, "pad at 0: nothing above RETAIN_PAD_Z_TOP"),
        # --- part 2: the pilots.  r = 30 is in the spigot WALL, solid at every
        # other azimuth, so a void there is the hole and can be nothing else.
        (C.cyl(30.0, th_a, z_r), False, "retention pilot at 0: bored"),
        (C.cyl(30.0, th_b, z_r), False, "retention pilot at 180: bored"),
        (C.cyl(30.0, 90.0, z_r), True, "no pilot at 90: the spigot wall is whole"),
        (C.cyl(30.0, th_a, z_r + 1.6), True,
         "pilot at 0 is only 2.10 wide: 1.6 mm off its axis the wall is back"),
        # BLIND, with a floor.  The one that matters: a screw tip must never appear
        # in the bay where the servo wire and the shock cord run.
        (C.cyl(23.7, th_a, z_r), True, "pilot at 0: the 1.00 mm floor is SOLID"),
        (C.cyl(23.7, th_b, z_r), True, "pilot at 180: same floor"),
        (C.cyl(24.5, th_a, z_r + 1.55), True,
         "pilot at 0: material above its top edge too, so it has not broken out "
         "through the pad's 45 deg cone"),
        # and ringed tangentially, which is what stops a self-tapper splitting it
        ((24.5, 1.6, z_r), True, "pilot at 0: pad material 1.6 mm to one side"),
        ((-24.5, -1.6, z_r), True, "pilot at 180: same, mirrored"),
        # --- part 3: the countersunk mouth, which is what makes a hole drilled by
        # hand in the airframe findable.  Proved as a FLARE, one probe each side.
        (C.cyl(29.5, th_a, z_r + 1.4), True,
         "mouth at 0: inboard of the countersink the hole is still 2.10 wide"),
        (C.cyl(30.9, th_a, z_r + 1.4), False,
         "mouth at 0: by r=30.9 it has opened to 3.66 -- the cone is real"),
        # --- above the shoulder the OD is full
        (C.cyl(r_af - 2.5 * sag, 0.0, 35.0), True, "collar: solid at the OD"),
        (C.cyl(r_af + 0.5, 0.0, 35.0), False, "collar: void outboard of the OD"),
        (C.cyl(20.0, 0.0, 35.0), False, "collar: bore still open at r=20"),
        # --- the bulkhead seat, and the 45 deg cone under it.  Both cone probes are
        # written as offsets from SEAT_R_IN and SEAT_Z0, not as literals: SEAT_R_IN
        # moved 26.5 -> 26.9 to keep the deepened hook slots off this land, and a
        # literal 28.3/43.0 pair silently landed 0.1 mm the wrong side of the cone
        # afterwards.  A probe that has to be re-derived by hand every time a datum
        # moves is a probe that will eventually be adjusted to pass.
        (C.cyl(P.SEAT_R_IN + 0.6, 0.0, 46.0), True,
         "seat: land is solid just inboard of the bore"),
        (C.cyl(P.SEAT_R_IN - 1.9, 0.0, 46.0), False,
         "seat: bore inboard of the land is open"),
        (C.cyl(P.SEAT_R_IN + 1.5, 0.0, P.SEAT_Z0 - 1.0), True,
         "seat: the 45 deg cone is present 1.0 mm below SEAT_Z0 at +1.5 mm of radius"),
        (C.cyl(P.SEAT_R_IN + 0.5, 0.0, P.SEAT_Z0 - 1.0), False,
         "seat: and absent at the same z only 1.0 mm further in -- so it is a 45 deg "
         "ramp and not a step, which is what makes it printable"),
        (C.cyl(P.SEAT_R_IN + 0.6, 0.0, 50.0), False,
         "seat: does NOT continue above SEAT_Z1"),
        # --- screw lobes: at their azimuth and at one they must miss
        (C.cyl(23.0, P.LOBE_THETA[0], 45.0), True, "lobe at 135: solid at r=23"),
        (C.cyl(23.0, P.LOBE_THETA[1], 45.0), True, "lobe at 315: solid at r=23"),
        (C.cyl(23.0, 45.0, 45.0), False, "no lobe at 45: r=23 is open"),
        (C.cyl(23.0, 225.0, 45.0), False, "no lobe at 225: r=23 is open"),
        (C.cyl(20.5, P.LOBE_THETA[0], 45.0), False,
         "lobe at 135 stops at LOBE_R_IN, r=20.5 is open"),
        # --- the two screw pilots, and their floors
        (C.cyl(P.R_BULK_SCREW, P.LOBE_THETA[0], 45.0), False, "pilot at 135 is bored"),
        (C.cyl(P.R_BULK_SCREW, P.LOBE_THETA[1], 45.0), False, "pilot at 315 is bored"),
        (C.cyl(P.R_BULK_SCREW, P.LOBE_THETA[0], 40.5), True,
         "pilot at 135 bottoms out above z=40.5, as designed"),
        # --- hinge lugs at +Y: the pin bore, the meat, and the gap between them.
        # All these probes sit at y >= 33, hence r >= 35.4, i.e. OUTBOARD of the
        # collar OD -- so a SOLID answer can only be lug and nothing else.
        ((12.75, P.Y_PIN, P.Z_PIN), False, "+Y lug: pin bore is open on the axis"),
        ((12.75, P.Y_PIN, P.Z_PIN + 1.8), True, "+Y lug: meat above the pin bore"),
        ((0.0, P.Y_PIN, P.Z_PIN + 1.8), False,
         "+Y hinge: nothing at x=0 -- that gap is where the shell's knuckle goes"),
        ((12.75, 34.5, 50.0), True, "+Y lug: solid mid-height, outboard of the OD"),
        ((12.75, 33.0, 45.0), True, "+Y lug: solid below the inboard cutback"),
        ((12.75, 33.0, 55.0), False,
         "+Y lug: cut back to Z_RING_TOP inboard of y=33.5, so the shell can seat"),
        ((12.75, 34.5, 39.0), False, "+Y lug: below the 70 deg fairing ramp"),
        # --- and the same hinge mirrored to -Y
        ((-12.75, -P.Y_PIN, P.Z_PIN), False, "-Y lug: pin bore is open"),
        ((-12.75, -P.Y_PIN, P.Z_PIN + 1.8), True, "-Y lug: meat above the bore"),
        ((12.75, 0.0, P.Z_PIN + 1.8), False, "no lug at theta=0"),
        # --- THE TWO ROOT POSTS: the only moulded-in pin anywhere in this assembly,
        # and it lives here rather than on a half because the ring prints upright and
        # a +z pillar on its collar top costs nothing, while a half prints ON its
        # split face and a pin there would need material under the bed.
        #
        # TWO, on OPPOSITE diagonals -- (POST_X, POST_Y) and its 180 deg image -- so
        # each half meets its own and only its own.  The wrong-diagonal probe is the
        # one that matters: a post at (-POST_X, +POST_Y) would be the one place both
        # halves reach, and then neither would go on.  Every point here sits at
        # r ~ 29.8 ABOVE Z_RING_TOP, where the collar has ended and the lugs are
        # 30 mm away in y, so SOLID can only be post.
        ((P.POST_X, P.POST_Y, P.Z_RING_TOP + P.POST_H - 0.4), True,
         "root post A: solid 0.4 mm below its tip"),
        ((-P.POST_X, -P.POST_Y, P.Z_RING_TOP + P.POST_H - 0.4), True,
         "root post B: and so is its 180 deg image, which is half B's"),
        ((-P.POST_X, P.POST_Y, P.Z_RING_TOP + P.POST_H - 0.4), False,
         "root posts: nothing on the other diagonal -- there are TWO, not four, "
         "and that is what keeps each half meeting only its own"),
        ((P.POST_X, P.POST_Y, P.Z_RING_TOP + P.POST_H + 0.5), False,
         "root post A: and it stops at POST_H, 0.5 mm below this"),
        ((P.POST_X, P.POST_Y + P.POST_D / 2 + 0.5, P.Z_RING_TOP + P.POST_H - 0.4),
         False,
         "root post A: Ø2.0 and no fatter -- the rest of the Ø2.7 socket is the "
         "0.35 mm of radial slack the half needs to find it while still skewed"),
    ])

    # --- torsion-spring leg seats: four blind Ø0.9 x 3.0 holes, one in each lug's
    # INNER face, looking across the pocket at the matching seat in the knuckle.
    # Probed the way the dowel sockets are, because "there is a hole" is not the claim.
    # The claims are: it is bored, it is BLIND (a leg driven in cannot come out the
    # back of the lug), it is Ø0.9 and not wider, and the wall between it and the pin
    # bore is really there.  Every point sits at |y| ~ 34.8 with |x| >= 10.5, so it is
    # outboard of the collar OD and a SOLID answer can only be lug material.
    y_seat, z_seat = P.torsion_seat_yz(P.TORSION_SEAT_AZ_LUG)
    x_mid = P.LUG_X_IN + P.TORSION_SEAT_DEPTH / 2
    x_past = P.LUG_X_IN + P.TORSION_SEAT_DEPTH + 0.3
    r_wall = (P.PIN_BORE_LUG / 2 + P.TORSION_LEG_R - P.TORSION_SEAT_D / 2) / 2
    y_wall, z_wall = P.torsion_seat_yz(P.TORSION_SEAT_AZ_LUG, r_wall)
    seat_cases = []
    for sx in (+1, -1):
        for sy, th in ((+1, 90.0), (-1, 270.0)):
            tag = f"{th:.0f} deg x{'+' if sx > 0 else '-'}"
            seat_cases += [
                ((sx * x_mid, sy * y_seat, z_seat), False,
                 f"spring seat {tag}: bored into the lug's inner face"),
                ((sx * x_past, sy * y_seat, z_seat), True,
                 f"spring seat {tag}: blind, with "
                 f"{P.LUG_W - P.TORSION_SEAT_DEPTH:.1f} mm of lug behind its floor"),
                ((sx * x_mid, sy * y_seat,
                  z_seat + P.TORSION_SEAT_D / 2 - 0.25), False,
                 f"spring seat {tag}: still open just inside r = TORSION_SEAT_D/2"),
                ((sx * x_mid, sy * y_seat,
                  z_seat + P.TORSION_SEAT_D / 2 + 0.25), True,
                 f"spring seat {tag}: solid just outside it, so it is "
                 f"Ø{P.TORSION_SEAT_D} and not wider"),
                # the one that matters structurally: the seat runs alongside the pin
                # bore and must not have broken into it
                ((sx * x_mid, sy * y_wall, z_wall), True,
                 f"spring seat {tag}: the wall to the pin bore is solid midway "
                 f"between them"),
            ]
    expect_points(m, n, seat_cases)

    # and the depth walked down the seat's OWN axis, because a seat that came out
    # shallow passes every probe above while giving the leg less than the
    # TORSION_SEAT_DEPTH of engagement spring_check() spends.
    for sx in (+1, -1):
        for sy, th in ((+1, 90.0), (-1, 270.0)):
            # NOT a hard-coded 4.0.  The scan has to reach past the seat floor to find
            # it, so its length must follow TORSION_SEAT_DEPTH: at depth 2.0 the 4.0
            # left 2.0 mm of headroom, at 3.0 it leaves 1.0, and at 3.95 it would stop
            # short of the floor and silently report "never reaches material".
            xs = np.arange(P.LUG_X_IN + 0.05,
                           P.LUG_X_IN + P.TORSION_SEAT_DEPTH + 1.5, 0.05)
            ins = inside(m, [(sx * float(x), sy * y_seat, z_seat) for x in xs])
            if not ins.any():
                check(False, "", f"{n}: spring seat at {th:.0f} deg x_sign={sx:+d} "
                                 f"never reaches material -- it runs out the back")
                continue
            d = float(xs[int(np.argmax(ins))]) - P.LUG_X_IN
            check(abs(d - P.TORSION_SEAT_DEPTH) < 0.1,
                  f"{n}: spring seat at {th:.0f} deg x_sign={sx:+d} is {d:.2f} mm "
                  f"deep, so the leg has the {P.TORSION_SEAT_DEPTH} mm of travel "
                  f"spring_check() spends on axial float",
                  f"{n}: spring seat at {th:.0f} deg x_sign={sx:+d} measures "
                  f"{d:.2f} mm deep, expected {P.TORSION_SEAT_DEPTH}")

    # the lug bore and the knuckle bore have to be the SAME line, or the pin binds
    for sgn, th in ((+1, 90.0), (-1, 270.0)):
        y = sgn * P.Y_PIN
        zs = np.linspace(P.Z_PIN - 0.7, P.Z_PIN + 0.7, 15)
        ins = inside(m, [(sgn * 12.75, y, float(z)) for z in zs])
        check(not ins.any(),
              f"{n}: pin bore at {th:.0f} deg is clear over +-0.7 mm of its axis",
              f"{n}: pin bore at {th:.0f} deg is obstructed at "
              f"{[round(float(z),2) for z, i in zip(zs, ins) if i]}")

    # --- the pilot walked down its OWN axis, not just sampled at two radii.  The
    # claim is not "there is a hole" but "the hole runs 6.92 mm and then stops",
    # and only a walk can see the stop.  Two scans per screw: the bore, then the
    # floor behind it.
    for th in P.RETAIN_THETA:
        rs = np.linspace(P.RETAIN_PILOT_R0 + 0.55, P.R_SPIGOT - 0.4, 25)
        ins = inside(m, [C.cyl(float(r), th, z_r) for r in rs])
        check(not ins.any(),
              f"{n}: retention pilot at {th:.0f} deg is clear over its whole "
              f"{P.R_SPIGOT - P.RETAIN_PILOT_R0:.2f} mm depth (25 stations)",
              f"{n}: retention pilot at {th:.0f} deg is obstructed at r="
              f"{[round(float(r), 2) for r, i in zip(rs, ins) if i]}")
        # 0.15 off each face, not 0.45 off the inboard one: a probe that close to a
        # mesh facet is still safely inside, and the wider walk covers 0.70 of the
        # 1.00 mm floor instead of 0.40.  The span is reported rather than rounded up
        # to "the whole floor", because it is not the whole floor.
        rs = np.linspace(P.RETAIN_PAD_R_IN + 0.15, P.RETAIN_PILOT_R0 - 0.15, 8)
        ins = inside(m, [C.cyl(float(r), th, z_r) for r in rs])
        check(ins.all(),
              f"{n}: and the floor behind it is unbroken over r "
              f"{rs[0]:.2f}..{rs[-1]:.2f}, {rs[-1] - rs[0]:.2f} mm of its "
              f"{P.RETAIN_PILOT_R0 - P.RETAIN_PAD_R_IN:.2f} mm thickness (8 "
              f"stations) -- the pilot cannot reach the servo bay",
              f"{n}: retention pilot at {th:.0f} deg has broken through its floor "
              f"at r={[round(float(r), 2) for r, i in zip(rs, ins) if not i]}")

    r = outer_r_by_ray(m, 0.0, 35.0, 30.0, 34.0)
    check(abs(r - r_af) < 0.02,
          f"{n}: collar OD measured by ray {r:.4f} vs R_AIRFRAME {r_af:.4f}",
          f"{n}: collar OD measured {r:.4f}, expected {r_af:.4f}")
    # 45 deg, for the same reason the probes above moved: at azimuth 0 this ray
    # would start inside the retention pilot and bisect on the wrong surface.
    r = outer_r_by_ray(m, 45.0, 13.0, 30.0, 32.0)
    check(abs(r - r_sp) < 0.02,
          f"{n}: spigot OD measured by ray {r:.4f} vs R_SPIGOT {r_sp:.4f} "
          f"-- {P.R_MBODY_BORE - r:.4f} mm radial clearance in Mbody's socket",
          f"{n}: spigot OD measured {r:.4f}, expected {r_sp:.4f}")


def verify_bulkhead(m) -> None:
    n = "bulkhead"
    zc = 0.5 * (P.Z_BULK_BOT + P.Z_BULK_TOP)     # mid-plate, away from both faces
    g32 = P.fin_notch_half_at(P.Z_FLANGE_FACE)   # 6.3326, was 4.615
    xf = P.FIN_X_IN + 0.5 * P.FIN_T              # mid-fin

    cases = [
        # --- the disc, and that it stops where it should
        ((0.0, 25.0, zc), True, "disc: solid at r=25"),
        ((0.0, 25.0, 46.0), False, "disc: nothing below Z_BULK_BOT at r=25"),
        ((0.0, 25.0, 51.0), False, "disc: nothing above Z_BULK_TOP"),
        # --- the thrust pad: an annulus, not a boss and not the whole underside
        ((8.0, 0.0, 47.2), True, "thrust pad: solid at r=8, below the disc"),
        ((12.0, 0.0, 47.2), False, "thrust pad: void outboard at r=12"),
        ((4.0, 0.0, 47.2), False, "thrust pad: void inboard at r=4"),
        # --- the cradle fins, and the notch V that opens for the arm
        ((xf, 0.0, 25.0), True, "fin +x: solid below the notch apex at y=0"),
        ((xf, 0.0, 30.0), False, "fin +x: notch apex has removed y=0 at z=30"),
        # These three, and the mirrored pair below, are written off fin_notch_half()
        # rather than as y literals.  The literals were 12.0 (fwd, wanted solid) and
        # 5.0 (mirrored, wanted solid), and both were INSIDE the notch by the time
        # LATCH_ARM_W reached 10.50: fin_notch_half() reads the bar's width and the
        # sweep, so it went 10.5150 -> 12.2326 and the V at the flange face went
        # 4.615 -> 6.3326.  A literal that was outboard of the old V is not outboard
        # of this one, and a probe that says "outboard of the notch" has to mean it.
        ((xf, P.fin_notch_half() + 0.6, 40.0), True,
         "fin +x: full height outboard of the notch, fwd side"),
        ((xf, -(P.fin_notch_half() + 0.6), 40.0), True,
         "fin +x: and outboard of it on the AFT side, where only FIN_Y0 - g = 2.77 mm "
         "of fin is left -- the strip a further widening would spend first"),
        ((xf, 5.0, 40.0), False, "fin +x: notched away in the arm's band"),
        ((xf, g32 + 0.6, P.Z_FLANGE_FACE), True,
         "fin +x: V has closed to +-6.33 by the flange face, so the pad has a root"),
        ((xf, g32 - 0.6, P.Z_FLANGE_FACE), False,
         "fin +x: still open just inboard of that, as the V requires"),
        ((-xf, g32 + 0.6, P.Z_FLANGE_FACE), True, "fin -x: same V, mirrored"),
        ((-xf, 5.0, 40.0), False, "fin -x: same notch, mirrored"),
        ((0.0, 0.0, 25.0), False, "between the fins: open for the servo body"),
        ((xf, P.FIN_Y1 + 1.0, 30.0), False, "fin +x: ends at FIN_Y1"),
        ((xf, P.FIN_Y0 - 1.0, 30.0), False, "fin +x: ends at FIN_Y0"),
        ((xf, 20.0, 15.0), False, "fin +x: nothing below FIN_Z_BOT"),
        # --- the flange pads and their pilots
        ((3.0, -9.0, 30.0), True, "aft pad: solid"),
        ((0.0, P.SERVO_HOLE_Y[0], 30.0), False, "aft pad: M2 pilot is bored"),
        ((3.0, 20.0, 30.0), True, "fwd pad: solid"),
        ((0.0, P.SERVO_HOLE_Y[1], 30.0), False, "fwd pad: M2 pilot is bored"),
        ((3.0, 5.0, 30.0), False, "between the pads: clear for the servo body"),
        ((3.0, -9.0, 26.0), False, "aft pad: nothing below PAD_T"),
        ((3.0, -9.0, 33.0), False, "aft pad: nothing above the flange face"),
        # --- the two hook slots, at 0 and 180.  The y probes are the ones that
        # matter and they are deliberately lopsided: the slot has to run 4.75 mm
        # PAST the split plane on the -y side, because the hook's foot swings
        # across the axis to y -4.25 while still level with this plate.  A slot
        # sized to the hook at rest is a hard stop at about 9 deg of opening.
        ((23.0, 1.0, zc), False, "hook slot A: open where the hook sits at rest"),
        ((23.0, -3.0, zc), False,
         "hook slot A: STILL open 3 mm the wrong side of the split plane -- this is "
         "the swing clearance, and it is the whole reason the nose can open"),
        ((23.0, -5.5, zc), True, "hook slot A: closed again by y=-5.5, past SLOT_Y0"),
        ((23.0, 5.0, zc), True, "hook slot A: disc intact outboard in y, past SLOT_Y1"),
        ((-23.0, -1.0, zc), False, "hook slot B: open, at the 180 deg image"),
        ((-23.0, 3.0, zc), False, "hook slot B: its swing clearance, mirrored"),
        ((-23.0, 5.5, zc), True, "hook slot B: closed again on its far side"),
        ((23.0, 1.0, 46.0), False, "hook slot A: it is a THROUGH slot"),
        ((18.0, 1.0, zc), True, "hook slot A: inboard of the slot the disc is whole"),
        ((27.5, 1.0, zc), True,
         "hook slot A: outboard of it the rim is continuous, so the seat land is "
         "unbroken even with the slot deepened"),
        # --- shock cord, with a chamfer proof
        ((0.0, P.Y_CORD_HOLE, zc), False, "cord hole: open"),
        ((0.0, P.Y_CORD_HOLE, 46.0), False, "cord hole: goes through"),
        ((0.0, P.Y_CORD_HOLE - 6.0, zc), True, "cord hole: disc intact beside it"),
        ((4.3, P.Y_CORD_HOLE, zc), True, "cord hole: straight bore is only 8 wide"),
        ((4.3, P.Y_CORD_HOLE, P.Z_BULK_TOP - 0.15), False,
         "cord hole: top chamfer has opened past r=4.3 near the face"),
        ((4.3, P.Y_CORD_HOLE, P.Z_BULK_BOT + 0.15), False,
         "cord hole: bottom chamfer likewise -- both faces relieved"),
        # --- the ring screws, at their azimuth and at one they must miss
        (C.cyl(P.R_BULK_SCREW, P.LOBE_THETA[0], zc), False, "ring screw at 135: bored"),
        (C.cyl(P.R_BULK_SCREW, P.LOBE_THETA[1], zc), False, "ring screw at 315: bored"),
        (C.cyl(P.R_BULK_SCREW, 45.0, zc), True, "no ring screw at 45"),
        # --- the three access holes.  Without these the servo cannot be fitted.
        ((0.0, P.SERVO_HOLE_Y[0], zc), False, "aft flange screw access: open"),
        ((0.0, P.SERVO_HOLE_Y[1], zc), False, "fwd flange screw access: open"),
        ((0.0, 0.0, zc), False, "horn screw access: open on the axis"),
        ((0.0, -5.5, zc), True, "disc intact between the aft access and the horn one"),
        ((0.0, 3.5, zc), True, "disc intact between the horn access and the fwd one"),
    ]
    expect_points(m, n, cases)

    # every access hole must line up with the fastener it exists for
    for y, d in ((P.SERVO_HOLE_Y[0], P.SERVO_ACCESS_D),
                 (P.SERVO_HOLE_Y[1], P.SERVO_ACCESS_D),
                 (0.0, P.HORN_ACCESS_D)):
        zs = np.linspace(P.Z_BULK_BOT + 0.1, P.Z_BULK_TOP - 0.1, 9)
        ins = inside(m, [(0.0, y, float(z)) for z in zs])
        check(not ins.any(),
              f"{n}: access hole at y={y:+.1f} is clear right through the plate",
              f"{n}: access hole at y={y:+.1f} is blocked at z="
              f"{[round(float(z),2) for z, i in zip(zs, ins) if i]}")

    # the pad's mounting face must have fin under BOTH its ends, or it prints in air
    for y0, y1 in P.flange_pads():
        for y in (y0 + 0.3, y1 - 0.3):
            got = inside(m, [(xf, y, P.Z_FLANGE_FACE - P.PAD_T - 0.5)])[0]
            check(bool(got),
                  f"{n}: fin carries the pad at y={y:+.1f} below its own underside",
                  f"{n}: pad end at y={y:+.1f} has no fin under it -- it would "
                  f"print in mid-air")

    # --- DOES A REAL MG90S FIT?  Every check so far has been about the bulkhead's
    # own geometry.  This one is about the object it has to hold: a grid through
    # the servo's whole envelope, every point of which must be empty.  The body is
    # NOT symmetric about the shaft -- it runs y -6.2..+16.6, so the flange
    # centreline sits at +5.2 -- and getting that wrong is the single easiest way
    # to print a cradle the servo will not go into.
    hw = P.SERVO_W / 2                       # 6.1
    y_b0, y_b1 = P.SERVO_BODY_Y              # -6.2 .. +16.6
    ear = 2.2                                # ears reach past each flange hole
    boxes = [("body", -hw, hw, y_b0, y_b1, P.Z_SERVO_BOT, P.Z_SERVO_TOP),
             ("aft flange ear", -hw, hw, P.SERVO_HOLE_Y[0] - ear, y_b0,
              P.Z_FLANGE_FACE, P.Z_FLANGE_FACE + 2.5),
             ("fwd flange ear", -hw, hw, y_b1, P.SERVO_HOLE_Y[1] + ear,
              P.Z_FLANGE_FACE, P.Z_FLANGE_FACE + 2.5)]
    for what, x0, x1, y0, y1, z0, z1 in boxes:
        pts = [(float(x), float(y), float(z))
               for x in np.linspace(x0 + 0.05, x1 - 0.05, 7)
               for y in np.linspace(y0 + 0.05, y1 - 0.05, 21)
               for z in np.linspace(z0 + 0.05, z1 - 0.05, 9)]
        ins = inside(m, pts)
        check(not ins.any(),
              f"{n}: the MG90S {what} envelope "
              f"({x1-x0:.1f} x {y1-y0:.1f} x {z1-z0:.1f} mm at y {y0:+.1f}.."
              f"{y1:+.1f}) is clear -- {len(pts)} points, none in material",
              f"{n}: the MG90S {what} envelope is fouled at "
              f"{int(ins.sum())} of {len(pts)} points -- the servo will not fit")

    # and the two flange pilots must actually lie on the pads' faces
    for y in P.SERVO_HOLE_Y:
        ring = [(0.85 + 0.4) * np.array([math.cos(t), math.sin(t), 0.0])
                + np.array([0.0, y, P.Z_FLANGE_FACE - 0.2]) for t in
                np.linspace(0.0, 2 * math.pi, 17)[:-1]]
        ins = inside(m, [tuple(p) for p in ring])
        check(ins.all(),
              f"{n}: the flange pilot at y={y:+.1f} is ringed by material all the "
              f"way round, so the screw pulls on a face and not on an edge",
              f"{n}: the flange pilot at y={y:+.1f} is unsupported over "
              f"{16 - int(ins.sum())} of 16 directions")


def verify_latch_arm(m) -> None:
    n = "latch_arm"
    floor = P.LATCH_ARM_T - P.HORN_POCKET_DEPTH          # 3.40
    z_pocket = P.Z_ARM_BOT + 0.5 * P.HORN_POCKET_DEPTH   # inside the pocket
    # between the pocket's ceiling and the counterbore's floor: the one z band
    # where the only thing missing is the Ø2.7 shaft clearance
    z_floor = P.Z_ARM_TOP - P.ARM_CB_DEPTH - 0.5 * (floor - P.ARM_CB_DEPTH)

    expect_points(m, n, [
        # --- the bar
        ((20.0, 0.0, 42.0), True, "bar: full thickness outboard of the horn slot"),
        ((20.0, 0.0, 39.0), True, "bar: solid right down to Z_ARM_BOT out there"),
        # PARAMETRIC, both of them.  These two were literals -- y 5.0 and "r=22.0"
        # -- sized to LATCH_ARM_W 8.0, and y 5.0 is INSIDE the 10.50 bar, so widening
        # it for the servo horn turned a passing probe into a false one.  A probe that
        # has to be edited every time the part changes is a probe that will one day be
        # edited to agree with the part.
        ((0.0, P.LATCH_ARM_W / 2 + 0.5, 42.0), False,
         f"bar: nothing past LATCH_ARM_W/2 = {P.LATCH_ARM_W / 2:.2f}"),
        ((P.ARM_CORNER_R + 1.6, 0.0, 42.0), False,
         f"bar: ends at the arc, r={P.ARM_CORNER_R:.2f}"),
        ((20.0, 0.0, 47.5), False, "bar: nothing above Z_ARM_TOP"),
        ((20.0, 0.0, 38.2), False, "bar: nothing below Z_ARM_BOT"),
        # --- the horn pocket: hub + slot, one depth, open downward only
        ((0.0, 0.0, z_pocket), False, "horn pocket: hub is open"),
        ((10.0, 0.0, z_pocket), False, "horn pocket: slot is open at x=10"),
        ((-10.0, 0.0, z_pocket), False, "horn pocket: and at x=-10, for a 2-arm horn"),
        # the slot is 36.8 mm end to end for a 36 mm double-arm horn, so it stops at
        # HORN_SLOT_R 18.4 and leaves 3.96 mm of land out to the arc at 22.36.  Probed as
        # a PAIR, because the single old probe at x 16 read solid only because the slot
        # used to stop at 15 -- one point cannot tell "the slot ends here" from "the
        # slot never started".
        ((19.5, 0.0, z_pocket), True,
         "horn pocket: the slot ends by x=19.5, leaving land out to the arc"),
        ((17.5, 0.0, z_pocket), False,
         "horn pocket: and is still open at x=17.5, so it really is 36.8 mm long"),
        # y 3.0 was OUTSIDE the old 5.0 slot and is INSIDE the 7.6 one, so this is
        # the second probe the wider blade invalidated.  Probed as a pair now: open in
        # the middle of the slot, solid just outside it, which is what pins the width.
        ((10.0, P.HORN_SLOT_W / 2 - 0.4, z_pocket), False,
         f"horn pocket: still open 0.4 mm inside the slot's {P.HORN_SLOT_W} width"),
        ((10.0, P.HORN_SLOT_W / 2 + 0.3, z_pocket), True,
         f"horn pocket: and solid 0.3 mm outside it -- the slot really is only "
         f"{P.HORN_SLOT_W} wide, which is what leaves the "
         f"{(P.LATCH_ARM_W - P.HORN_SLOT_W) / 2:.3f} mm flanks that drive the arm"),
        ((10.0, 0.0, z_floor), True,
         f"horn pocket: {floor:.2f} mm of floor over the slot"),
        # --- THE GOVERNING WALL, and it is not the slot's flank.  The Ø7.73 hub
        # recess is wider than the 7.6 slot, so the thinnest wall in the whole part is
        # at x = 0: (LATCH_ARM_W - HORN_POCKET_D)/2 = 1.385 mm against WALL_MIN 1.26.
        # Probed either side of it, because a wall is only evidence if the void next
        # to it is evidence too.
        ((0.0, P.HORN_POCKET_D / 2 + 0.4, z_pocket), True,
         f"wall: solid 0.4 mm outboard of the Ø{P.HORN_POCKET_D} hub recess -- this "
         f"{(P.LATCH_ARM_W - P.HORN_POCKET_D) / 2:.3f} mm wall is the thinnest thing "
         f"in the arm and it is why LATCH_ARM_W had to reach {P.LATCH_ARM_W}"),
        ((0.0, P.HORN_POCKET_D / 2 - 0.4, z_pocket), False,
         "wall: and open 0.4 mm inboard, so it really is the recess next door"),
        # --- AND THE ONE THE USER ASKED FOR.  The blade is 7.2 mm wide for 22.5 mm of
        # its length, so the slot has to be open at y = 3.5 all the way out to
        # |x| = 11.25 -- not just near the hub, which is what a slot sized on the
        # blade's 4.1 mm TIP would have given.  Probed at both ends of that span and
        # on both sides of the axis, because it is a DOUBLE-arm horn and a slot that
        # is open one way and blocked the other fits nothing.
        ((P.HORN_LEVER_W_FULL, P.HORN_LEVER_W / 2 - 0.1, z_pocket), False,
         f"blade envelope: the slot is open at y {P.HORN_LEVER_W / 2 - 0.1:.2f} out at "
         f"x {P.HORN_LEVER_W_FULL}, so the blade's full-width section clears"),
        ((-P.HORN_LEVER_W_FULL, -(P.HORN_LEVER_W / 2 - 0.1), z_pocket), False,
         "blade envelope: and the same on the other spur"),
        # --- the shaft screw: clearance, then counterbore, then nothing proud
        ((0.0, 0.0, z_floor), False, "shaft screw: clearance bored through the floor"),
        ((2.0, 0.0, z_floor), True, "shaft screw: clearance is only 2.7 wide"),
        ((2.0, 0.0, P.Z_ARM_TOP - 0.5), False, "counterbore: open at r=2.0 near the top"),
        ((3.0, 0.0, P.Z_ARM_TOP - 0.5), True, "counterbore: only 5.0 wide"),
        ((2.0, 0.0, P.Z_ARM_TOP - P.ARM_CB_DEPTH - 0.4), True,
         "counterbore: stops at 1.6 deep, leaving material for the head to pull on"),
        # --- THE LAND UNDER THE HOOKS.  The lever slot's outermost corner sits at
        # r 18.79 and the hooks bear from r 20.50 inward-most, so 1.71 mm of
        # full-thickness bar stands between the pocket and the bearing patch and
        # every newton of hook thrust crosses it.  It was 1.93 mm with the old 5.0
        # slot: widening the slot 2.6 mm for the measured blade spent 0.22 mm of the
        # land, which is why HORN_SLOT_R stayed at 18.4 instead of going out to 18.8.
        # Probed at BOTH ends of the land,
        # because one point cannot tell "the land is there" from "the slot stopped
        # somewhere else entirely".
        ((P.HORN_SLOT_R + 0.3, P.HORN_SLOT_W / 2 - 0.5, z_pocket), True,
         "land: solid 0.3 mm outboard of the slot's end, at its widest y"),
        ((P.HOOK_X_IN - 0.3, P.TONGUE_Y0 + 0.1, z_pocket), True,
         "land: and still solid 0.3 mm inboard of the foot's inboard corner, so "
         "the 1.71 mm of land is unbroken across the whole thrust path"),
        ((P.HORN_SLOT_R - 0.3, P.HORN_SLOT_W / 2 - 0.5, z_pocket), False,
         "land: and it really is the slot next door -- open 0.3 mm the other side "
         "of HORN_SLOT_R"),
        # --- and it reaches OVER the hook's foot.  Probed at the UNDERSIDE, which
        # is the latch face: that is the face the foot bears up on.
        ((P.HOOK_X_IN + 0.5, 1.5, P.Z_ARM_BOT + 0.3), True,
         "latched: solid directly above the foot's inboard end, at the latch face"),
        ((P.HOOK_X_IN + 0.5, 1.5, P.Z_ARM_BOT - 0.3), False,
         "and nothing below it -- the foot occupies that, which is the point"),
    ])

    r = max(math.hypot(*v[:2]) for v in m.vertices)
    check(abs(r - P.ARM_CORNER_R) < 0.05,
          f"{n}: furthest point of the exported mesh r={r:.3f} = ARM_CORNER_R, "
          f"so it clears the seat bore {P.SEAT_R_IN} by {P.SEAT_R_IN - r:.2f} mm at "
          f"every angle of the sweep",
          f"{n}: furthest point r={r:.3f}, expected ARM_CORNER_R "
          f"{P.ARM_CORNER_R:.3f}")

    # the arm must SWEEP within its own outline: rotating it must not grow its
    # radius.  That is the whole point of the concentric arc ends.
    for a in (10.0, 20.0, P.LATCH_SWEEP):
        rr = max(math.hypot(*v[:2]) for v in moved(m, rz(a)).vertices)
        check(abs(rr - r) < 1e-6,
              f"{n}: at {a:.0f} deg of sweep the furthest point is still {rr:.3f}",
              f"{n}: at {a:.0f} deg of sweep the radius grew to {rr:.3f}")

    # --- THE SECTION THE WHOLE LATCH MOMENT PASSES THROUGH.
    #
    # x = 0 is where the hub recess, the lever slot and the Ø2.7 shaft clearance all
    # overlap, so it is the arm's thinnest station -- and it is also the station
    # carrying the most moment, because both hooks push up at r ~ 21 and the shaft
    # reacts down at the middle: M(0) = F * 21, one hook's worth from each side in
    # the same sense.  So the weakest section and the worst-loaded section are the
    # same section, which is the only reason it is worth measuring.
    #
    # Measured off the MESH on a 0.025 mm grid rather than derived.  Three cuts
    # interact there and the closed form for their union is not worth trusting -- and
    # the point of this harness is to ask the exported part, not the model.
    ys = np.linspace(-P.LATCH_ARM_W / 2, P.LATCH_ARM_W / 2, 321)
    zs = np.linspace(P.Z_ARM_BOT, P.Z_ARM_TOP, 337)
    da = float((ys[1] - ys[0]) * (zs[1] - zs[0]))
    grid = np.array([(0.0, float(y), float(z)) for y in ys for z in zs])
    sect = grid[inside(m, grid)]
    area = len(sect) * da
    z_bar = float(sect[:, 2].mean())
    i_yy = float(((sect[:, 2] - z_bar) ** 2).sum()) * da
    c_max = float(max(sect[:, 2].max() - z_bar, z_bar - sect[:, 2].min()))
    s_yy = i_yy / c_max
    # bending about y, fibres along x -- which in this part's print pose is IN-layer
    # at both fibres, so the allowable is SIGMA_ABS and not the bond's 11 MPa.
    f = P.latch_force_per_half()
    arm_m = f * math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y1 ** 2)
    sigma = arm_m / s_yy
    # Thresholds raised 10.0/4.0 -> 30.0/30.0 with LATCH_ARM_W 10.50.  The old pair
    # was sized to an 8.0 bar whose Ø8.2 hub recess broke clean out of it, leaving the
    # section hanging on 10.69 mm2; the wider bar keeps 1.385 mm flanks through x = 0
    # and the section is 36.49 mm2 at S = 38.08 mm3.  Leaving the thresholds where they
    # were would mean this check could no longer fail for any reason worth catching --
    # including a revert to the 8.0 bar the measured horn does not fit.
    check(area > 30.0 and s_yy > 30.0,
          f"{n}: at x=0, {area:.2f} mm2 of the {P.LATCH_ARM_W * P.LATCH_ARM_T:.1f} "
          f"gross survives the pocket and the bore "
          f"({100 * (1 - area / (P.LATCH_ARM_W * P.LATCH_ARM_T)):.0f}% gone), with "
          f"S={s_yy:.2f} mm3 about the bending axis.  One hook's {f:.3f} N at "
          f"r {math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y1 ** 2):.2f} is "
          f"{arm_m:.2f} N.mm, so {sigma:.2f} MPa -- {P.SIGMA_ABS / sigma:.0f}x "
          f"inside in-layer ABS, which is the allowable because both fibres run "
          f"along x",
          f"{n}: the x=0 section is down to A={area:.2f} mm2, S={s_yy:.2f} mm3 "
          f"(wanted A>30.0, S>30.0) -- the pocket has eaten the arm")

    # RELEASE: with the arm swept, is the foot's footprint empty?
    #
    # Sampled just ABOVE the arm's underside now, not just below its top face.
    # The latch face is Z_ARM_BOT and it faces UP -- so what has to be full when
    # latched and empty when released is the material immediately above the foot,
    # and a probe 0.3 mm under the TOP face answers a question about the thrust
    # pad instead.  It happens to give the same answer on a solid bar, which is
    # exactly why it was worth nothing as evidence.
    #
    # Two footprints, deliberately:
    #   the ENGAGED LEDGE, x HOOK_X_IN..x_reach, which the arm must cover in full
    #   the WHOLE FOOT,   x HOOK_X_IN..TONGUE_X1, which it only partly covers
    # because the foot runs 2.4 mm further outboard than the arm's arc reaches.
    # That outboard strip is not wasted -- it is the web's root -- but reporting
    # coverage over it would understate the latch.
    x_reach = math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y1 ** 2)      # 22.14
    z_probe = P.Z_ARM_BOT + 0.3
    for a in (0.0, P.LATCH_SWEEP):
        arm = moved(m, rz(a))
        for what, x0, x1, want_latched in (
                ("engaged ledge", P.HOOK_X_IN + 0.1, x_reach - 0.1, 1.0),
                ("whole foot", P.HOOK_X_IN, P.TONGUE_X1, 0.30)):
            pts = [(float(x), float(y), z_probe)
                   for x in np.linspace(x0, x1, 11)
                   for y in np.linspace(P.TONGUE_Y0 + 0.05, P.TONGUE_Y1 - 0.05, 7)]
            pts += [(-x, -y, z) for (x, y, z) in pts]                # hook B
            frac = float(inside(arm, pts).mean())
            if a == 0.0:
                check(frac >= want_latched - 1e-9,
                      f"{n}: latched, the arm sits over {100*frac:.0f}% of both "
                      f"hooks' {what} (x {x0:.2f}..{x1:.2f}) -- wanted "
                      f"{100*want_latched:.0f}%",
                      f"{n}: latched, the arm sits over only {100*frac:.0f}% of the "
                      f"{what} (x {x0:.2f}..{x1:.2f}), wanted "
                      f"{100*want_latched:.0f}%; it would not hold")
            else:
                check(frac == 0.0,
                      f"{n}: swept {a:.0f} deg, the arm sits over 0% of either "
                      f"hook's {what} -- the halves are free",
                      f"{n}: swept {a:.0f} deg, the arm still sits over "
                      f"{100*frac:.0f}% of a hook's {what}; it would NOT release")


def verify_half_shell(m) -> None:
    n = "half_shell"

    # --- it is a HALF: the whole y<0 side must be empty
    bad = []
    for z in (60.0, 100.0, 150.0, 200.0, 240.0):
        r = float(prof.r_outer(z))
        for th in (200.0, 250.0, 270.0, 300.0, 340.0):
            if inside(m, [C.cyl(r - 1.0, th, z)])[0]:
                bad.append((th, z))
    check(not bad, f"{n}: nothing at all on the y<0 side (25 probes)",
          f"{n}: material found below the split plane at {bad}")

    # --- skin and wall, measured by ray at four stations
    for z in (70.0, 110.0, 160.0, 210.0):
        r_nom = float(prof.r_outer(z))
        r = outer_r_by_ray(m, 90.0, z, r_nom - 1.0, r_nom + 1.5)
        check(abs(r - r_nom) < 0.03,
              f"{n}: OD at z={z:.0f} measured {r:.4f} vs nose_profile {r_nom:.4f}",
              f"{n}: OD at z={z:.0f} measured {r:.4f}, profile says {r_nom:.4f}")
        t = C.wall_thickness(m, 90.0, z, r_nom - 0.1, r_nom - 6.0, step=0.02)
        t_nom = float(prof.wall_normal_to_radial(P.WALL, z))
        check(abs(t - t_nom) < 0.10,
              f"{n}: radial wall at z={z:.0f} is {t:.3f} mm, and {t_nom:.3f} is "
              f"what {P.WALL} mm normal becomes at this {prof.slope_deg(z):.2f} deg "
              f"slope",
              f"{n}: radial wall at z={z:.0f} is {t:.3f} mm, expected {t_nom:.3f}")

    r_root = float(prof.r_outer(P.Z_SHELL_ROOT + 0.8))
    r_v = float(prof.r_outer(P.Z_VENT))
    cases = [
        # --- the cavity is open all the way down
        (C.cyl(15.0, 90.0, 100.0), False, "cavity: open on the axis side at z=100"),
        (C.cyl(15.0, 90.0, P.Z_SHELL_ROOT + 1.0), False, "cavity: open at the root"),
        (C.cyl(3.0, 90.0, 240.0), False, "cavity: still open near the tip"),
        # --- vents, at their azimuth and at one they must miss
        (C.cyl(r_v - 1.0, P.VENT_THETA[0], P.Z_VENT), False, "vent at 45: bored"),
        (C.cyl(r_v - 1.0, P.VENT_THETA[1], P.Z_VENT), False, "vent at 135: bored"),
        (C.cyl(r_v - 1.0, 90.0, P.Z_VENT), True, "no vent at 90: skin intact"),
        (C.cyl(r_v - 1.0, P.VENT_THETA[0], P.Z_VENT + 4.0), True,
         "vent at 45: skin intact 4 mm above it, so it is a hole not a slot"),
        # --- the hinge knuckle and its pin bore
        ((0.0, P.KNUCKLE_WEB_Y + 1.0, 55.0), True, "knuckle: solid at x=0"),
        ((0.0, P.Y_PIN, P.Z_PIN), False, "knuckle: pin bore is open"),
        ((0.0, P.Y_PIN, P.Z_PIN + 1.6), True, "knuckle: meat above the pin bore"),
        ((P.KNUCKLE_W / 2 + 1.0, 33.0, 55.0), False,
         "knuckle: only KNUCKLE_W wide, so the ring's lugs at |x|>=10.5 have room"),
        ((0.0, P.LUG_Y_OUT + 0.5, 55.0), False, "knuckle: ends at the lug's OD line"),
        # --- the latch HOOK.  This is the feature the whole mechanism turns on, so
        # it gets probed as a SHAPE: solid where the J is, void in the notch the
        # arm has to occupy, and void below the foot.  Nothing here would have
        # passed on the plain blade this replaced, and nothing that follows would
        # have failed on it -- which is why the probes are worth spelling out.
        ((23.0, 1.5, 50.0), True, "hook A: solid below the shell root"),
        ((23.0, 5.0, 50.0), False, "hook A: only TONGUE_Y0..Y1 thick"),
        ((-23.0, 1.5, 50.0), False,
         "no hook at -x: the 180 deg image puts the second one there instead"),
        ((22.0, 1.5, 42.0), False,
         "THE NOTCH: void at x=22, z=42 -- this is the pocket the latch arm lies "
         "in, and its ceiling and floor are what grip the arm"),
        ((22.0, 1.5, P.Z_STEP + 0.5), True,
         "the notch's CEILING: solid again just above Z_STEP, 0.6 mm over the arm"),
        ((22.0, 1.5, P.Z_LATCH_FACE - 0.5), True,
         "the notch's FLOOR: the foot, solid just under the latch face -- this is "
         "the material the arm cannot rise through"),
        ((22.0, 1.5, P.Z_HOOK_BOT - 0.5), False, "and nothing below Z_HOOK_BOT"),
        ((P.HOOK_X_IN - 1.0, 1.5, P.Z_LATCH_FACE - 0.5), False,
         "the foot stops at HOOK_X_IN inboard, so it clears the horn and the hub"),
        ((25.0, 1.5, 42.0), True,
         "the WEB: solid between WEB_X_IN and TONGUE_X1 -- 2.43 mm of wall carrying "
         "the whole latch load down past the arm"),
        ((P.TONGUE_X1 + 0.6, 1.5, 42.0), False, "the web stops at TONGUE_X1 outboard"),
        (((P.WEB_X_IN + P.ARM_CORNER_R) / 2, 1.5, 42.0), False,
         "and the arm's swept corner radius passes through that void, inboard of "
         "the web, with WEB_CLEAR to spare"),
        # the RAMP, proved as a pair: the same z is solid in the bearing land and
        # void out at the far edge of the foot.  One probe cannot tell a ramp from
        # a flat; two at different y can, and a flat foot is a jam.
        ((22.0, P.TONGUE_Y0 + 0.35, P.Z_LATCH_FACE - 0.15), True,
         "foot ramp: the bearing LAND is at full height near the split plane"),
        ((22.0, P.TONGUE_Y1 - 0.15, P.Z_LATCH_FACE - 0.15), False,
         "foot ramp: and has fallen away by the foot's far edge -- so the arm has "
         "somewhere to enter and cams the halves shut as it advances"),
        ((24.0, 1.5, P.Z_TONGUE_TOP - 1.0), True, "gusset: ties the hook to the wall"),
        # --- THE GUSSET IS THE FIX, so it gets measured and not just touched.  It runs
        # the full Z_SHELL_ROOT..GUSSET_Z_TOP = 9.586 mm in z at the wall, against the
        # 0.6 mm spur it replaces, and that depth cubed is the whole of the 5.1x in S.
        # Three stations up the depth, then two bounds -- a probe that only says "solid
        # somewhere in there" cannot tell 9.586 mm from 0.6.
        # x 27, not out at TONGUE_X_WALL: r there is 30.84, INSIDE the skin, so a
        # solid answer would be the shell wall answering for the gusset.  27 is 3.7 mm
        # inboard of r_in and can only be gusset.
        ((27.0, 1.5, P.Z_SHELL_ROOT + 0.3), True,
         "gusset: full depth at the root -- this is the extreme fibre of the weld"),
        ((27.0, 1.5, (P.Z_SHELL_ROOT + P.GUSSET_Z_TOP) / 2), True,
         "gusset: and solid at mid-depth"),
        ((27.0, 1.5, P.GUSSET_Z_TOP - 0.3), True,
         "gusset: and right up under GUSSET_Z_TOP, so it really is 9.59 mm deep"),
        ((27.0, 1.5, P.GUSSET_Z_TOP + 0.6), False,
         "gusset: but nothing above it -- the diagonal has ended, not run on"),
        ((P.TONGUE_X_WALL + 2.0, 1.5, P.Z_SHELL_ROOT + 2.0), False,
         "gusset: and nothing outboard of the wall it welds to"),
        # --- the step chamfer, which is what keeps the web's inboard corner off the
        # arm's swept radius.  A pair again: the corner is cut, the material below is
        # not.  A missing chamfer is a zero-length OCC edge, which builds silently.
        ((P.WEB_X_IN - 0.2, 1.5, P.Z_STEP - 0.2), True,
         "step chamfer: 0.2 below Z_STEP the web's inboard face has been pulled "
         "inboard of WEB_X_IN -- a square corner would leave this void"),
        ((P.WEB_X_IN - 0.2, 1.5, P.Z_STEP - P.STEP_CHAM - 0.5), False,
         "step chamfer: and it is only STEP_CHAM deep -- the face is back at "
         "WEB_X_IN below that, which is what keeps it off the arm's swept radius"),
        # --- the ROOT POST SOCKET.  One, on the -x meridian, because +x is the hook's
        # weld: a bore there would have taken 0.68 of the weld's 3.0 mm at the root,
        # 17 % of S.  So the socket is probed AND its absence at +x is probed, at the
        # pad roof -- the only y where the two meridians differ for a reason that is
        # about the socket rather than about the tongue's own y band.
        ((P.POST_X, P.POST_Y, P.Z_SHELL_ROOT + 1.0), False,
         "root post socket: bored along +z from the root face"),
        ((P.POST_X, P.POST_Y, P.Z_SHELL_ROOT + P.POST_BORE_DEPTH + 0.5), True,
         "root post socket: blind at POST_BORE_DEPTH, so the post cannot punch through"),
        ((P.POST_X, P.POST_PAD_Y - 0.4, P.Z_SHELL_ROOT + 2.0), True,
         "root post pad: roofs the socket"),
        ((-P.POST_X, P.POST_PAD_Y - 0.4, P.Z_SHELL_ROOT + 2.0), False,
         "root post pad: and there is exactly ONE of them -- none at the mirror, "
         "where the hook's weld is"),
        # --- seam dowel sockets, on BOTH seam faces at mirrored x
        ((0.0, 1.0, 110.0), False, "seam: the cavity is between the pads"),
    ]
    for z0 in P.DOWEL_Z:
        r_out = float(prof.r_outer(z0))
        x_soc = r_out - P.DOWEL_INSET
        for s in (+1, -1):
            tag = f"z={z0:.0f} x{'+' if s > 0 else '-'}"
            y_mid = P.SEAM_SETBACK + P.DOWEL_DEPTH / 2
            cases += [
                ((s * x_soc, y_mid, z0), False,
                 f"dowel socket {tag}: bored"),
                ((s * x_soc, P.SEAM_SETBACK + P.DOWEL_DEPTH + 0.5, z0), True,
                 f"dowel socket {tag}: backed by material, not a through hole"),
                # RADIUS, as a pair.  dowel_withdrawal() computes its whole margin
                # against r_bore = DOWEL_BORE/2; if the built bore were bigger the
                # sweep would be reporting a clearance the part does not have, and
                # if it were smaller the depth scan above would still pass.
                ((s * x_soc, y_mid, z0 + P.DOWEL_BORE / 2 - 0.25), False,
                 f"dowel socket {tag}: still open just inside r = DOWEL_BORE/2"),
                ((s * x_soc, y_mid, z0 + P.DOWEL_BORE / 2 + 0.25), True,
                 f"dowel socket {tag}: solid just outside it, so the bore is "
                 f"{P.DOWEL_BORE} and not wider"),
            ]
    # --- torsion-spring leg seats, one blind Ø0.9 x 3.0 hole in each knuckle end
    # face.  Same four claims as the dowel sockets -- bored, blind, Ø0.9 and not
    # wider -- plus the one that is specific to this feature: the seat runs
    # alongside the pin bore with 1.20 mm between them, and if the cut had broken
    # through into the bore the leg would foul the pin and assert_cut would still
    # have passed, because breaking through removes MORE material, not less.
    y_seat, z_seat = P.torsion_seat_yz(P.TORSION_SEAT_AZ_KNUCKLE)
    x_mid = P.KNUCKLE_W / 2 - P.TORSION_SEAT_DEPTH / 2
    x_past = P.KNUCKLE_W / 2 - P.TORSION_SEAT_DEPTH - 0.3
    r_wall = (P.PIN_BORE_KNUCKLE / 2 + P.TORSION_LEG_R - P.TORSION_SEAT_D / 2) / 2
    y_wall, z_wall = P.torsion_seat_yz(P.TORSION_SEAT_AZ_KNUCKLE, r_wall)
    for s in (+1, -1):
        tag = f"x{'+' if s > 0 else '-'}"
        cases += [
            ((s * x_mid, y_seat, z_seat), False,
             f"spring seat {tag}: bored into the knuckle end face"),
            ((s * x_past, y_seat, z_seat), True,
             f"spring seat {tag}: blind -- solid again past its floor, so the two "
             f"seats in one knuckle do not meet in the middle"),
            ((s * x_mid, y_seat, z_seat + P.TORSION_SEAT_D / 2 - 0.25), False,
             f"spring seat {tag}: still open just inside r = TORSION_SEAT_D/2"),
            ((s * x_mid, y_seat, z_seat + P.TORSION_SEAT_D / 2 + 0.25), True,
             f"spring seat {tag}: solid just outside it, so it is "
             f"Ø{P.TORSION_SEAT_D} and not wider"),
            ((s * x_mid, y_wall, z_wall), True,
             f"spring seat {tag}: the wall to the pin bore is solid midway between "
             f"them, so the leg cannot foul the pin"),
        ]

    expect_points(m, n, cases)

    # ...and their depth down their own axis, for the same reason the dowel sockets
    # get one below: spring_check() spends TORSION_SEAT_DEPTH twice over, once on
    # the leg's engagement and once on the coil's axial float, so a seat that came
    # out shallow silently eats the margin that makes the spring self-locating.
    for s in (+1, -1):
        xs = np.arange(P.KNUCKLE_W / 2 - 0.05, 0.0, -0.05)
        ins = inside(m, [(s * float(x), y_seat, z_seat) for x in xs])
        if not ins.any():
            check(False, "", f"{n}: spring seat x_sign={s:+d} never reaches material "
                             f"-- it runs clean through the knuckle")
        else:
            d = P.KNUCKLE_W / 2 - float(xs[int(np.argmax(ins))])
            check(abs(d - P.TORSION_SEAT_DEPTH) < 0.1,
                  f"{n}: spring seat x_sign={s:+d} is {d:.2f} mm deep, matching the "
                  f"{P.TORSION_SEAT_DEPTH} mm of bent leg spring_check() assumes",
                  f"{n}: spring seat x_sign={s:+d} measures {d:.2f} mm deep, "
                  f"expected {P.TORSION_SEAT_DEPTH}")

    # Socket depth measured down its own axis.  A socket that came out shallow
    # still passes the probes above; only the scan pins the number, and the whole
    # dowel scheme is stated in terms of it: the rod is DOWEL_LEN long and glued
    # BOTTOMED in one half, so this depth sets both how much sticks out and how
    # much room the far half has to swallow it without ever bottoming.
    # 2 x SEAM_SETBACK, not one: the setback is per half, so with the nose shut the
    # two seam faces stand 0.30 mm apart and the rod spends that crossing the gap.
    reach = P.DOWEL_LEN - P.DOWEL_DEPTH - 2 * P.SEAM_SETBACK   # engagement in half B
    for z0 in P.DOWEL_Z:
        x_soc = float(prof.r_outer(z0)) - P.DOWEL_INSET
        for s in (+1, -1):
            ys = np.arange(P.SEAM_SETBACK + 0.05, P.SEAM_SETBACK + 9.0, 0.05)
            ins = inside(m, [(s * x_soc, float(y), z0) for y in ys])
            if not ins.any():
                check(False, "", f"{n}: dowel socket z={z0:.0f} x_sign={s:+d} "
                                 f"never reaches material -- it is a through hole")
                continue
            d = float(ys[int(np.argmax(ins))]) - P.SEAM_SETBACK
            check(abs(d - P.DOWEL_DEPTH) < 0.15,
                  f"{n}: dowel socket z={z0:.0f} x_sign={s:+d} is {d:.2f} mm deep "
                  f"(DOWEL_DEPTH {P.DOWEL_DEPTH}), so a {P.DOWEL_D} x "
                  f"{P.DOWEL_LEN:.1f} mm rod bottomed in half A engages half B by "
                  f"{reach:.2f} mm and still stops {d - reach:.2f} mm off its floor",
                  f"{n}: dowel socket z={z0:.0f} x_sign={s:+d} measures {d:.2f} mm "
                  f"deep, expected {P.DOWEL_DEPTH}")

    lo, hi = m.bounds
    check(lo[1] >= P.SEAM_SETBACK - 1e-6,
          f"{n}: lowest y is {lo[1]:.4f} = SEAM_SETBACK, so the two halves have "
          f"{2*P.SEAM_SETBACK:.2f} mm of total seam gap and cannot fight",
          f"{n}: lowest y is {lo[1]:.4f}, which crosses SEAM_SETBACK "
          f"{P.SEAM_SETBACK}")
    # 1e-4, not 1e-6: an STL stores float32, and 36.1 is not representable in it
    # (36.099998474...), so an exact datum reads 1.5e-6 off.  The old datum, 47.0,
    # happened to be exact and hid that.  1e-4 is still 65x the float32 quantum
    # here, so it cannot hide a real 0.05 mm feature loss.
    # hi[2] used to be tested against Z_TIP, which is VACUOUS: Z_TIP is the design
    # apex of the full ogive and the seam cut always lands TIP_DEFICIT (0.5766 mm)
    # below it, so "hi < Z_TIP" was true no matter what the part did.  Z_SHELL_TOP is
    # the apex a half actually has, so this now measures the tip instead of assuming it.
    # --- THE APEX, which is what the user asked about.  It is not a flat: at
    # z = Z_SHELL_TOP the ogive's radius is 0.150004 mm, i.e. SEAM_SETBACK to four
    # decimals, so the seam plane is TANGENT to the section circle there and the half
    # comes to a POINT.  The missing height is arithmetic, not a modelling choice --
    # TIP_DEFICIT = SEAM_SETBACK / tan(TIP_HALF_ANGLE) = 0.5766 -- and it is smaller
    # than what the slicer takes off anyway (the first layer costs 1.3454 mm, 2.33x
    # this).  Probed on the seam face, just off it, because that is the meridian the
    # truncation acts on.
    y_ap = P.SEAM_SETBACK + 0.05
    expect_points(m, "half_shell", [
        ((0.0, y_ap, P.Z_SHELL_TOP - 1.0), True,
         "apex: solid 1.0 mm down from the top, where the cone is r 0.41"),
        ((0.0, y_ap, P.Z_SHELL_TOP + 0.1), False,
         "apex: and nothing above Z_SHELL_TOP -- it ends in a point, not a flat"),
        ((0.0, y_ap, P.Z_TIP - 0.1), False,
         f"apex: the last {P.TIP_DEFICIT:.4f} mm up to the true Z_TIP is missing, "
         f"and that is SEAM_SETBACK / tan(TIP_HALF_ANGLE) exactly"),
    ])

    check(abs(lo[2] - P.Z_HOOK_BOT) < 1e-4 and abs(hi[2] - P.Z_SHELL_TOP) < 1e-3,
          f"{n}: spans z {lo[2]:.3f}..{hi[2]:.3f} -- down to Z_HOOK_BOT exactly, so "
          f"the foot is the lowest thing on the part, and up to Z_SHELL_TOP exactly, "
          f"which is {P.TIP_DEFICIT:.4f} mm short of the design apex because the seam "
          f"cut takes SEAM_SETBACK off a cone of half-angle {P.TIP_HALF_ANGLE:.2f} deg",
          f"{n}: spans z {lo[2]:.3f}..{hi[2]:.3f}, expected Z_HOOK_BOT "
          f"{P.Z_HOOK_BOT} .. Z_SHELL_TOP {P.Z_SHELL_TOP:.4f}")


# ----------------------------------------------------------------- assembly

def verify_seam_pin(m) -> None:
    """The fallback dowel: Ø3.0 x 6.5, chamfered BOTH ends, and no fatter than the
    sweep allows.

    Small enough that basics()'s 6 % volume tolerance floors at 1.0 cm3 and cannot
    say anything about a 0.045 cm3 part -- so the volume is re-checked here against
    the closed form, tightly.  The chamfers are the reason this part is verified at
    all: seam_pin.py's cutter is the ANNULUS outside the taper, and the mistake it
    warns about (subtracting the frustum instead) yields a tube with a countersunk
    hole, which is watertight, one body, the right bbox, and useless.  A point just
    inside the taper at each end separates the two.
    """
    n = "seam_pin"
    r, c, L = P.DOWEL_D / 2, 0.3, P.DOWEL_LEN     # CHAMFER is local to seam_pin.py
    r_ch = r - c + 0.05                           # the taper's radius 0.05 up from an end

    expect_points(m, n, [
        ((0.0, 0.0, L / 2), True, "pin: solid on the axis at mid-length"),
        ((r - 0.1, 0.0, L / 2), True, "pin: full Ø3.0 at mid-length"),
        ((r + 0.1, 0.0, L / 2), False, "pin: and nothing outboard of Ø3.0"),
        ((0.0, 0.0, -0.1), False, "pin: nothing below z=0"),
        ((0.0, 0.0, L + 0.1), False, "pin: nothing above DOWEL_LEN"),
        ((r_ch - 0.1, 0.0, 0.05), True,
         "chamfer at z=0: inside the taper is solid"),
        ((r_ch + 0.1, 0.0, 0.05), False,
         "chamfer at z=0: outside it is gone -- the cutter took the annulus, not "
         "the frustum"),
        ((r_ch - 0.1, 0.0, L - 0.05), True,
         "chamfer at z=DOWEL_LEN: inside the taper is solid"),
        ((r_ch + 0.1, 0.0, L - 0.05), False,
         "chamfer at z=DOWEL_LEN: and gone outside it too, so BOTH ends are broken "
         "and the pin is symmetric end for end"),
    ])

    plain = math.pi * r ** 2 * L
    v_ch = 2 * math.pi * c ** 2 * (3 * r - c) / 3
    want = plain - v_ch
    # 1.5 % covers the tessellated cylinder's inscribed-polygon deficit
    # (~2/3 . perimeter . 0.03 . L = 1.2 mm3 of the 45.2) with room to spare.
    check(abs(m.volume - want) < 0.015 * want,
          f"{n}: {m.volume:.2f} mm3 is the {plain:.2f} of cylinder less the "
          f"{v_ch:.2f} of chamfer, to {abs(m.volume - want)/want*100:.1f} %",
          f"{n}: {m.volume:.2f} mm3, not the {want:.2f} a Ø{P.DOWEL_D} x {L} with "
          f"{c} x 45 deg on both ends is")

    # --- THE CHECK THAT MAKES THE PRINTED PIN LEGAL, taken off the mesh rather than
    # trusted from seam_pin.py: the largest radius that survived tessellation and
    # export has to clear the withdrawal sweep, not just the nominal bore.
    r_max = float(np.linalg.norm(m.vertices[:, :2], axis=1).max())
    worst = max((P.DOWEL_BORE - P.DOWEL_D) / 2 + P.dowel_withdrawal(z0)[0]
                for z0 in P.DOWEL_Z)
    r_legal = P.DOWEL_BORE / 2 - worst
    check(r_max <= r_legal,
          f"{n}: widest point r {r_max:.4f} against the r {r_legal:.4f} the "
          f"withdrawal sweep allows -- {2*(r_legal - r_max):.4f} mm of diameter "
          f"spare for the printer to be wrong by",
          f"{n}: r {r_max:.4f} exceeds the r {r_legal:.4f} the sweep allows, so a "
          f"half cannot open with this pin in it -- use Ø3 rod")


def verify_assembly(ring, shell, bulk, arm) -> None:
    shell_b = moved(shell, rz(180.0))            # the second half, same STL

    assert_disjoint(ring, bulk, "ring vs bulkhead")
    assert_disjoint(ring, arm, "ring vs latch arm (latched)")
    assert_disjoint(bulk, arm, "bulkhead vs latch arm (latched)")
    assert_disjoint(ring, shell, "ring vs half A")
    assert_disjoint(shell, shell_b, "half A vs half B")
    assert_disjoint(bulk, shell, "bulkhead vs half A")
    assert_disjoint(bulk, shell_b, "bulkhead vs half B")
    assert_disjoint(arm, shell_b, "latch arm vs half B (latched)")

    # The arm SHOULD touch hook A when latched -- that is the latch.  Two facts
    # together say "contact": zero overlap, and zero gap over the whole patch.
    # Either alone is ambiguous, since a part that misses entirely also has zero
    # overlap.
    #
    # The plane is Z_ARM_BOT, the arm's UNDERSIDE, and the patch is the bearing
    # LAND only -- y TONGUE_Y0..+RAMP_LAND.  Outboard of the land the foot's top
    # deliberately falls away on the lead-in ramp, so a grid over the full y band
    # would measure the ramp's drop and call it a gap.
    #
    # The gap is measured on a DETERMINISTIC grid, not by surface sampling.  The
    # contact patch is about 8 mm2 out of the shell's ~30000, so random samples
    # land in it two or three times at n=8000 and the reported minimum is then
    # luck rather than geometry -- it read 0.060 mm that way, which is a near
    # miss, not a gap.  A grid over the patch also proves the foot lands FLAT
    # instead of on one corner.
    h, d = interference(arm, shell)
    x_reach = math.sqrt(P.ARM_CORNER_R ** 2 - P.TONGUE_Y1 ** 2)   # 22.14
    y_land1 = P.TONGUE_Y0 + P.RAMP_LAND
    grid = np.array([[x, y, P.Z_ARM_BOT + 1e-4]
                     for x in np.linspace(P.HOOK_X_IN + 0.2, x_reach - 0.2, 9)
                     for y in np.linspace(P.TONGUE_Y0 + 0.1, y_land1 - 0.1, 5)])
    _, dd, _ = shell.nearest.on_surface(grid)
    worst_contact = float(np.max(dd))
    check(h == 0 and worst_contact < 0.01,
          f"latch arm vs half A (latched): 0 overlapping samples, and across the "
          f"whole {P.HOOK_X_IN}..{x_reach:.1f} x {P.TONGUE_Y0}..{y_land1} bearing "
          f"land the foot's top is never more than {worst_contact*1000:.1f} um off "
          f"the arm's UNDERSIDE -- it bears flat up on it, which is the latch",
          f"latch arm vs half A (latched): {h} overlapping samples "
          f"({d:.3f} mm deep); worst gap over the bearing land "
          f"{worst_contact:.4f} mm -- wanted flat contact")

    # --- DOES IT ACTUALLY RESIST?  THIS IS THE CHECK THIS PROJECT DID NOT HAVE.
    #
    # Everything above establishes that the arm and the hook touch.  Touching is
    # not latching.  The previous design touched perfectly and held nothing,
    # because the contact was on the wrong side of the arm: every point of a half
    # is inboard of its own hinge pin, so dz/dtheta = Y_PIN - |y| > 0 and the
    # tongue RISES as the half opens.  A blade resting on top of the arm simply
    # lifts off it.  236 assertions all passed.
    #
    # So: open the half a little with the arm LATCHED and demand a COLLISION.
    # Points taken strictly inside the arm just above its underside; once the
    # half has rotated far enough for the land to rise past them, they must be
    # inside the shell.  If the mechanism is backwards this fails at every angle,
    # and nothing else here does.
    ledge = np.array([[x, y, P.Z_ARM_BOT + 0.05]
                      for x in np.linspace(P.HOOK_X_IN + 0.2, x_reach - 0.2, 9)
                      for y in np.linspace(P.TONGUE_Y0 + 0.1, y_land1 - 0.1, 5)])
    for a in (0.25, 0.5, 1.0, 2.0):
        opened = moved(shell, hinge_open(a))
        got = inside(opened, ledge)
        rise = (P.Y_PIN - P.TONGUE_Y0) * math.radians(a)
        check(got.all(),
              f"RESISTANCE at {a:.2f} deg: the foot has risen {rise:.3f} mm and now "
              f"occupies all {len(ledge)} points inside the arm -- the half CANNOT "
              f"open without breaking the arm, which is what a latch is",
              f"RESISTANCE at {a:.2f} deg: the foot only reaches "
              f"{int(got.sum())} of {len(ledge)} points inside the arm -- the half "
              f"is free to open with the latch engaged, so this is NOT a latch")

    # --- and the converse: RELEASED, the same motion must be unobstructed over the
    # entire travel.  Both halves, both hooks, the arm swept out of the way.
    free = moved(arm, rz(P.LATCH_SWEEP))
    for a in (0.0, 2.0, 10.0, 30.0, 110.0):
        for tag, sh, mat in (("A", shell, hinge_open(a)),
                             ("B", shell_b, trimesh.transformations.rotation_matrix(
                                 math.radians(a), [1, 0, 0], [0.0, -P.Y_PIN, P.Z_PIN]))):
            assert_disjoint(free, moved(sh, mat),
                            f"RELEASED arm vs half {tag} opened {a:.1f} deg")

    # --- the sweep.  This is the check the analytic capsule test stands in for.
    #
    # Measured against the bulkhead SLICED below the thrust pad rather than the
    # whole part.  The arm's top face is deliberately coincident with that pad, so
    # a whole-part closest approach reads 0.000 at every angle and hides the
    # number actually wanted: the LATERAL gap to the cradle fins.  The slice is
    # left uncapped so the cut introduces no surface of its own to measure to.
    cradle = bulk.slice_plane([0.0, 0.0, P.Z_ARM_TOP - 1.0], [0.0, 0.0, -1.0])
    worst = (1e9, None)
    for a in np.linspace(0.0, P.LATCH_SWEEP, 7):
        swept = moved(arm, rz(float(a)))
        assert_disjoint(swept, bulk, f"latch arm at {a:.1f} deg vs bulkhead")
        g = gap(cradle, swept)
        if g < worst[0]:
            worst = (g, float(a))
    check(worst[0] > 0.3,
          f"latch arm through its whole {P.LATCH_SWEEP:.0f} deg sweep: closest "
          f"approach to the CRADLE {worst[0]:.3f} mm, at {worst[1]:.1f} deg "
          f"(measured on the meshes; bulkhead.py's capsule maths said 0.607)",
          f"latch arm comes within {worst[0]:.3f} mm of the cradle at "
          f"{worst[1]:.1f} deg of sweep")

    # --- opening.  The halves must clear the ring AND each other all the way.
    worst_r, worst_o = (1e9, None), (1e9, None)
    for a in (5.0, 15.0, 30.0, 60.0, 90.0, 110.0):
        oa = moved(shell, hinge_open(a))
        ob = moved(shell_b, trimesh.transformations.rotation_matrix(
            math.radians(a), [1, 0, 0], [0.0, -P.Y_PIN, P.Z_PIN]))
        assert_disjoint(oa, ring, f"half A opened {a:.0f} deg vs ring")
        assert_disjoint(oa, ob, f"half A vs half B, both opened {a:.0f} deg")
        assert_disjoint(oa, bulk, f"half A opened {a:.0f} deg vs bulkhead")
        g = gap(ring, oa)
        if g < worst_r[0]:
            worst_r = (g, a)
        g = gap(ob, oa)
        if g < worst_o[0]:
            worst_o = (g, a)
    # Sampled, so these are UPPER bounds on the true minima and they move a little
    # run to run.  The statement that matters is the assert_disjoint above, which
    # is about overlap and does not depend on where the samples fell.
    NOTES.append(f"  ok   opening sweep (sampled upper bounds): half-to-ring "
                 f"closest approach <= {worst_r[0]:.3f} mm at {worst_r[1]:.0f} deg; "
                 f"half-to-half <= {worst_o[0]:.3f} mm at {worst_o[1]:.0f} deg -- "
                 f"both positive, and no overlap at any angle")

    # --- THE DOWELS HAVE TO GET OUT, and the sweep above cannot see it.
    # Every angle sampled above starts at 5 deg.  A dowel that binds does it in the
    # first two degrees and is long clear by five, so that sample set is blind to
    # exactly this failure -- and it was: the 10 mm rod this design used to carry
    # jammed 0.03 mm at 1.85 deg and passed every check in this file.  So: the four
    # rods as actually glued (bottomed in half A, riding with half A), against half
    # B, stepped finely through the angles where the seam is still nearly shut.
    #
    # This is the mesh counterpart of nose_params.dowel_withdrawal().  Keep both:
    # the analytic one is exact and cheap but models the socket as an ideal
    # cylinder, and this one uses the socket the part actually has.
    y_hi = P.SEAM_SETBACK + P.DOWEL_DEPTH              # bottomed in half A
    rods = []
    for z0 in P.DOWEL_Z:
        x_soc = float(prof.r_outer(z0)) - P.DOWEL_INSET
        for s in (+1, -1):
            t = trimesh.transformations.concatenate_matrices(
                trimesh.transformations.translation_matrix(
                    [s * x_soc, y_hi - P.DOWEL_LEN / 2, z0]),
                rx(-90.0))
            rods.append(trimesh.creation.cylinder(
                radius=P.DOWEL_D / 2, height=P.DOWEL_LEN, sections=48, transform=t))
    dowels = trimesh.util.concatenate(rods)

    fine = [round(0.25 * i, 2) for i in range(1, 25)]   # 0.25 .. 6.00 deg
    # third slot starts at 0.0, not None: check()'s messages are f-strings and both
    # get built before the condition is looked at, so a None here formats-errors out
    # of a PASSING check.
    worst_d = (0, 0.0, 0.0)
    for a in fine + [10.0, 30.0, 90.0]:
        od = moved(dowels, hinge_open(a))
        ob = moved(shell_b, trimesh.transformations.rotation_matrix(
            math.radians(a), [1, 0, 0], [0.0, -P.Y_PIN, P.Z_PIN]))
        # one-way on purpose: at 27 angles the reverse direction would resample a
        # 22842-triangle shell each time for no new information.  Overlap is
        # symmetric, and the rod is the small body -- its surface is where a bind
        # of a few hundredths shows up.
        h, d = interference(od, ob, n=6000)
        if h > worst_d[0] or (h == worst_d[0] and d > worst_d[1]):
            worst_d = (h, d, a)
    check(worst_d[0] == 0,
          f"seam dowels withdraw: the four rods stay clear of half B at every one "
          f"of the {len(fine) + 3} angles from 0.25 to 90 deg, the first 6 deg "
          f"stepped at 0.25 -- which is where a dowel binds if it is going to",
          f"seam dowels BIND: {worst_d[0]} interior points of a rod are inside "
          f"half B at {worst_d[2]:.2f} deg of opening, {worst_d[1]:.3f} mm deep")

    # --- AND THE ROOT POST HAS TO GET OUT, for the same reason the dowels do:
    # it binds inside the first degree or not at all, and the coarse 5-deg sweep
    # above cannot see that.  Withdrawal here is easier than for a dowel -- the post
    # is 3.0 long against the dowel's 1.7 mm of engagement, but it sits at |y| 3.2,
    # only 3.05 mm off the seam, so the skew it has to survive is small.
    #
    # The posts are taken by SLICING THE RING rather than re-modelling them, so the
    # fillet at their root is the real one and this cannot drift from base_ring.py.
    # Above Z_RING_TOP and inside |y| < 20 is exactly the two posts: the collar has
    # ended and the hinge lugs are all at |y| > 33.
    #
    # Both posts go in together, which makes this two checks in one: half A's own
    # post must WITHDRAW, and half B's post -- sitting at y -4.5..-1.9, on the far
    # side of the seam -- must never touch half A at any angle, including shut.
    posts = ring.slice_plane([[0.0, 0.0, P.Z_RING_TOP + 1e-4],
                              [0.0, 20.0, 0.0], [0.0, -20.0, 0.0]],
                             [[0.0, 0.0, 1.0], [0.0, -1.0, 0.0], [0.0, 1.0, 0.0]],
                             cap=True)
    check(abs(posts.volume - 19.42) < 0.5,
          f"root posts: the slice above the collar top is {posts.volume:.2f} mm3, "
          f"which is the two Ø{P.POST_D} x {P.POST_H} pillars "
          f"({2 * math.pi * (P.POST_D / 2) ** 2 * P.POST_H:.2f}) plus their root "
          f"fillets and nothing else",
          f"root posts: the slice above the collar top came out {posts.volume:.2f} "
          f"mm3, not the ~19.42 the two posts and their fillets are -- something "
          f"else is up there, or a post is missing")
    worst_p = (0, 0.0, 0.0)
    for a in fine + [10.0, 30.0, 90.0]:
        oa = moved(shell, hinge_open(a))
        h, d = interference(posts, oa, n=6000)
        if h > worst_p[0] or (h == worst_p[0] and d > worst_p[1]):
            worst_p = (h, d, a)
    check(worst_p[0] == 0,
          f"root post withdraws: both posts stay clear of half A at every one of "
          f"the {len(fine) + 3} angles from 0.25 to 90 deg -- so A's own post comes "
          f"out of its socket, and B's post (y -4.5..-1.9, the wrong side of the "
          f"seam) never touches A at all, shut or open",
          f"root post BINDS: {worst_p[0]} interior points of a post are inside "
          f"half A at {worst_p[2]:.2f} deg of opening, {worst_p[1]:.3f} mm deep")

    # --- the mouth the chute has to come out of, once open
    oa = moved(shell, hinge_open(100.0))
    ob = moved(shell_b, trimesh.transformations.rotation_matrix(
        math.radians(100.0), [1, 0, 0], [0.0, -P.Y_PIN, P.Z_PIN]))
    zs = np.linspace(P.Z_BULK_TOP + 2.0, P.Z_BULK_TOP + 40.0, 25)
    blocked = [float(z) for z in zs
               if inside(oa, [(0.0, 0.0, float(z))])[0]
               or inside(ob, [(0.0, 0.0, float(z))])[0]]
    check(not blocked,
          "opened 100 deg: the axis is clear from the bulkhead face for 40 mm, so "
          "the pack has a straight way out",
          f"opened 100 deg: the halves still block the axis at z={blocked}")

    # --- assembled OD: nothing may stand proud except the hinge fairing, which
    # does, and by how much is a number the user needs.
    stack = trimesh.util.concatenate([ring, shell, shell_b])
    lo, hi = stack.bounds
    NOTES.append(f"  ok   assembled bbox x {lo[0]:.3f}..{hi[0]:.3f}  "
                 f"y {lo[1]:.3f}..{hi[1]:.3f}  z {lo[2]:.3f}..{hi[2]:.3f}")
    proud = max(hi[1], -lo[1]) - P.R_AIRFRAME
    NOTES.append(f"  ok   hinge fairing stands {proud:.2f} mm proud of the "
                 f"{2*P.R_AIRFRAME:.2f} mm OD at +-Y; x stays within "
                 f"{max(hi[0], -lo[0]) - P.R_AIRFRAME:+.3f} mm of it, so rail "
                 f"guides belong at +-X")


# --------------------------------------------------------------------- driver

def main() -> int:
    meshes = {}
    for name in ("base_ring", "half_shell", "bulkhead", "latch_arm", "seam_pin"):
        p = OUT / f"{name}.stl"
        if not p.exists():
            print(f"missing {p}")
            return 2
        meshes[name] = C.load(p)

    C.report([], "EXPORTED MESH VERIFICATION -- _nose_simple/out/*.stl")
    # CAD volumes, cm3, straight off `python <part>.py`.  Kept here as literals on
    # purpose -- importing the part scripts to ask them would make this check
    # tautological, and the point of it is to catch a tessellation or export fault
    # by comparing the mesh against a number that came from the SOLID.  So they have
    # to be re-read by hand when a part changes; half_shell's said 24.48 for a while
    # after the spring seats went in, which is a 0.09 cm3 lie the 6% tolerance was
    # wide enough to hide.
    # base_ring lost 0.0025 cm3 and half_shell 0.0013 when TORSION_SEAT_DEPTH went
    # 2.0 -> 3.0: that is exactly 4 x and 2 x pi*0.45^2*1.0 = 0.636 mm3 of extra blind
    # hole, which is the arithmetic that says the depth change reached the seats and
    # nothing else.  Both are far inside the 6% tolerance below, so this is bookkeeping
    # rather than a check -- but a literal nobody updates is a literal nobody trusts.
    # base_ring +0.0194 (the two root posts), half_shell +0.1713 (the full-depth
    # gusset and the root post pad, less the socket), latch_arm -0.4546 (the 36.8 mm
    # horn slot and the 5.70 mm pocket, which take out far more than LATCH_ARM_R 22.0
    # puts back).  bulkhead untouched.
    #
    # THEN the servo horn was measured and the arm had to swallow a 7.2 mm blade:
    # latch_arm 1.8213 -> 2.4664, +0.6451, which is LATCH_ARM_W 8.0 -> 10.50 adding
    # 1.0452 of bar less the 0.4001 the 7.6 mm slot and the deeper counterbore floor
    # take back out.  bulkhead 10.2255 -> 9.9204, -0.3051, all of it the fin notch
    # widening 10.5150 -> 12.2326 as fin_notch_half() reads the wider bar and the
    # 31 deg sweep.  base_ring -0.0186 and half_shell -0.0274 are NOT geometry: neither
    # part reads any parameter that changed (half_shell reads WEB_X_IN, which the
    # ARM_CORNER_R freeze holds at 23.07 precisely so this stays true), and 0.05% and
    # 0.11% on two heavily curved parts is tessellation from the re-export.
    #
    # AND THAT PARAGRAPH IS WHERE THIS CHECK QUIETLY BROKE.  Those two deltas were not
    # re-read off the solid, they were copied from the MESH column of the comparison
    # this very loop prints -- and so were the other three.  All five literals were
    # low by exactly the tessellation deficit a faceted hull of a convex curved solid
    # has to show: 38.9810/24.5367/9.9204/2.4664/0.0451 against CAD
    # 38.9996/24.5641/9.9229/2.4671/0.0452, i.e. -0.048%, -0.112%, -0.026%, -0.030%,
    # -0.2%.  Comparing the mesh against a number taken FROM the mesh is the
    # tautology the preamble above forbids, and it makes a genuine tessellation or
    # export fault invisible -- the one fault this check exists to catch.  Restored to
    # the solid: `python <part>.py` prints 2 dp, so take them from
    # `gen_step().volume/1000` at 4.  The 6% tolerance never noticed, which is the
    # point: nothing failed, and the check had still stopped working.
    for name, pose, cad in (("base_ring", np.eye(4), 38.9996),
                            ("half_shell", rx(90.0), 24.5641),
                            ("bulkhead", rx(180.0), 9.9229),
                            ("latch_arm", rx(180.0), 2.4671),
                            # standing on end IS its print pose, so no rotation --
                            # and see verify_seam_pin for the volume check that
                            # actually bites at this size
                            ("seam_pin", np.eye(4), 0.0452)):
        basics(meshes[name], name, pose, cad)

    print("\n-- part features (each probed where it is AND where it is not)")
    verify_base_ring(meshes["base_ring"])
    verify_bulkhead(meshes["bulkhead"])
    verify_latch_arm(meshes["latch_arm"])
    verify_half_shell(meshes["half_shell"])
    verify_seam_pin(meshes["seam_pin"])

    print("-- assembly, sweep and release")
    verify_assembly(meshes["base_ring"], meshes["half_shell"],
                    meshes["bulkhead"], meshes["latch_arm"])

    for line in NOTES:
        print(line)
    print("=" * 72)
    if FAILS:
        print(f"{len(FAILS)} FAILURES:")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print(f"all {len(NOTES)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
