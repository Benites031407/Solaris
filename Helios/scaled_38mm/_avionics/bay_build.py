"""Shared build123d constructions for the avionics bay.

Deliberately a SIBLING of `_nose_simple/nose_build.py` rather than an import of
it.  The primitives are the same handful and the plane-orientation probes below
are copied from there verbatim, but `_avionics/` has to stand on its own: a
cross-directory `sys.path` hack that works when you run one script from one cwd
and breaks from another is not worth saving forty lines.

PLANE ORIENTATIONS ARE MEASURED, NOT ASSUMED
--------------------------------------------
build123d's stock planes do not all face the way the name suggests, and guessing
wrong produces a solid in the right place with the wrong handedness -- which then
looks correct in a bounding box and wrong in a boolean.  Probed in this
installation (build123d 0.10.0):

    Plane.XZ * make_face(Polyline((u,v)...))   ->  point lands at (u, 0, v)
    extrude(that_face, amount=+a)              ->  sweeps into -Y  (normal is -Y!)
    Plane(origin=(x0,0,0), x_dir=(0,1,0), z_dir=(1,0,0)) * face with (y,z) points
                                               ->  lands at (x0, y, z)
    revolve(Plane.XZ face, Axis.Z, 360)        ->  volume matches the analytic
                                                   annulus to 0.01 mm3

COORDINATE FRAME FOR THIS BAY
-----------------------------
z = STATION s, in mm AFT of the body tube's forward rim, growing aft.  So +z
points TOWARDS THE TAIL here, which is the opposite of the nose's frame; the two
relate by nose_z = 26.2069 - s and that conversion lives in bay_params.NOSE_Z().
The reason to flip rather than inherit is that every dimension the bay is bounded
by came off Mbody.stl, whose own z already runs this way -- carrying the nose's
sign convention across would mean negating a measured table, which is exactly the
kind of silent mirror that `assert_half` exists to catch in the nose.

Azimuth theta is measured in the TUBE's frame: 0 = +x, 90 = +y, matching the
cord tunnel's measured centreline at theta = 0 and the nose's two retention
screws at theta = 0 and 180.
"""

from __future__ import annotations

import math

from build123d import (Align, Axis, Box, Cylinder, Plane, Polyline, Pos, Rot,
                       extrude, make_face, revolve)

BIG = 400.0          # bigger than the whole bay, for keep-out and cutting solids


# ------------------------------------------------------------------- primitives

def revolve_rz(pts_rz):
    """Revolve a closed polygon given as (r, z) pairs 360 deg about Z."""
    pts = [(float(r), float(z)) for r, z in pts_rz]
    if min(r for r, _ in pts) < -1e-9:
        raise ValueError("a revolved profile cannot cross the axis")
    return revolve(Plane.XZ * make_face(Polyline(*pts, close=True)), Axis.Z, 360)


def prism_yz(pts_yz, x0: float, x1: float):
    """Extrude a closed polygon given as (y, z) pairs along X from x0 to x1."""
    if x1 <= x0:
        raise ValueError(f"x1 must exceed x0, got {x0}..{x1}")
    pl = Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    pts = [(float(y), float(z)) for y, z in pts_yz]
    return extrude(pl * make_face(Polyline(*pts, close=True)), amount=(x1 - x0))


def prism_xz(pts_xz, y0: float, y1: float):
    """Extrude a closed polygon given as (x, z) pairs along Y from y0 to y1.

    Plane.XZ's normal is -Y, so the raw extrude lands at y in [-(y1-y0), 0] and
    has to be shifted up by y1.  That off-by-a-sign is the whole reason this
    wrapper exists.
    """
    if y1 <= y0:
        raise ValueError(f"y1 must exceed y0, got {y0}..{y1}")
    pts = [(float(x), float(z)) for x, z in pts_xz]
    s = extrude(Plane.XZ * make_face(Polyline(*pts, close=True)), amount=(y1 - y0))
    return Pos(0, y1, 0) * s


def box_between(x0, x1, y0, y1, z0, z1):
    """An axis-aligned box given by its two opposite corners."""
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        raise ValueError(f"degenerate box {x0}..{x1}, {y0}..{y1}, {z0}..{z1}")
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0,
                                 align=(Align.MIN, Align.MIN, Align.MIN))


def cyl_along(axis: str, base, d: float, length: float):
    """A cylinder of diameter `d` starting at `base` and running `length` along +axis."""
    dirs = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
    xdirs = {"x": (0, 1, 0), "y": (0, 0, 1), "z": (1, 0, 0)}
    pl = Plane(origin=tuple(base), x_dir=xdirs[axis], z_dir=dirs[axis])
    return pl * Cylinder(radius=d / 2, height=length,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))


def radial_hole(d: float, theta_deg: float, z: float, r0: float, r1: float):
    """A cylinder boring radially outward through a wall, at azimuth theta."""
    if r1 <= r0:
        raise ValueError(f"r1 must exceed r0, got {r0}..{r1}")
    t = math.radians(theta_deg)
    base = (r0 * math.cos(t), r0 * math.sin(t), z)
    pl = Plane(origin=base, x_dir=(0, 0, 1), z_dir=(math.cos(t), math.sin(t), 0))
    return pl * Cylinder(radius=d / 2, height=(r1 - r0),
                         align=(Align.CENTER, Align.CENTER, Align.MIN))


def wedge(theta_deg: float, half_chord: float, r_in: float, r_out: float,
          z0: float, z1: float):
    """A radial block centred on azimuth `theta`, 2*half_chord wide, for local bosses."""
    b = Box(r_out - r_in, 2 * half_chord, z1 - z0,
            align=(Align.MIN, Align.CENTER, Align.MIN))
    return Rot(0, 0, theta_deg) * Pos(r_in, 0, z0) * b


def sector(theta_c: float, half_ang: float, r_in: float, r_out: float,
           z0: float, z1: float):
    """A true annular SECTOR: r_in..r_out, centred on theta_c, +/- half_ang.

    Not the same as wedge(), which is a straight-sided box and therefore cuts
    inside the arc at its corners.  For a keyway that has to clear a measured
    azimuth span this has to be the arc, or the keyway is narrower than asked for
    at exactly the radius that matters.

    Built as a PARTIAL REVOLVE rather than as a ring intersected with two
    half-space boxes.  The box version is what this used to be and it was wrong:
    a box aligned (MIN, CENTER) spans the 180 deg [phi-90, phi+90] about its own
    axis, so intersecting the boxes at theta_c-half_ang and theta_c+half_ang
    keeps [theta_c+half_ang-90, theta_c-half_ang+90] -- a span of
    180 - 2*half_ang, i.e. the wrong sector, which happens to look plausible and
    is exactly right at half_ang = 45.  It also needed a complement branch above
    89 deg that recursed forever at exactly 90.  A partial revolve has one code
    path and no orientation to get backwards.
    """
    if not 0.0 < half_ang <= 180.0:
        raise ValueError(f"half_ang must be in (0, 180], got {half_ang}")
    face = make_face(Polyline((r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1),
                              close=True))
    s = revolve(Plane.XZ * face, Axis.Z, 2.0 * half_ang)
    return Rot(0, 0, theta_c - half_ang) * s


def sector_rz(theta_c: float, half_ang: float, pts_rz):
    """A partial revolve of an arbitrary (r, z) profile: sector() generalised.

    sector() can only make a rectangle in (r, z), which is fine for a keyway but
    not for a boss that has to RAMP in from the shell so its underside prints
    without support.  Same partial-revolve construction, arbitrary profile.
    """
    if not 0.0 < half_ang <= 180.0:
        raise ValueError(f"half_ang must be in (0, 180], got {half_ang}")
    pts = [(float(r), float(z)) for r, z in pts_rz]
    if min(r for r, _ in pts) < -1e-9:
        raise ValueError("a revolved profile cannot cross the axis")
    s = revolve(Plane.XZ * make_face(Polyline(*pts, close=True)),
                Axis.Z, 2.0 * half_ang)
    return Rot(0, 0, theta_c - half_ang) * s


# --------------------------------------------------------------------- checks

def bbox(s):
    b = s.bounding_box()
    return (b.min.X, b.min.Y, b.min.Z), (b.max.X, b.max.Y, b.max.Z)


def assert_cut(before, after, min_mm3: float, label: str):
    """A boolean that removes nothing is silent.  Make it loud."""
    removed = before.volume - after.volume
    if removed < min_mm3:
        raise AssertionError(
            f"{label}: cut removed {removed:.3f} mm3, expected >= {min_mm3:.3f} -- "
            f"the cutter is missing the material it was aimed at")
    return removed


def assert_cut_band(before, after, lo_mm3: float, hi_mm3: float, label: str):
    """A cut whose removed volume must land in a BAND, not merely exceed a floor.

    assert_cut() only catches a cutter that missed.  It cannot catch one that hit
    something else as well, because eating extra material makes the number bigger
    and a floor test passes harder.  Every cutter here is deliberately oversized in
    one direction so the boolean is clean -- a slot cutter reaches 1 mm past the
    deck on both faces -- and that overshoot is exactly what would silently chew a
    rib if a y coordinate ever moved.  Where the expected volume is known in closed
    form, bound it on both sides.
    """
    removed = before.volume - after.volume
    if not lo_mm3 <= removed <= hi_mm3:
        raise AssertionError(
            f"{label}: cut removed {removed:.3f} mm3, expected "
            f"{lo_mm3:.3f}..{hi_mm3:.3f} -- "
            + ("the cutter missed its target"
               if removed < lo_mm3 else
               "the cutter also hit something it was not aimed at"))
    return removed


def slab_area(r: float, x0: float, x1: float) -> float:
    """Area of the slab x0 <= x <= x1 inside a circle of radius r, in closed form.

    Used to predict the volume of every chord-shaped feature (the deck, and the
    material the trough's opening removes) so those predictions are analytic rather
    than "about right".  integral of 2*sqrt(r^2 - x^2) dx = x*sqrt(r^2-x^2)
    + r^2*asin(x/r).
    """
    def f(x):
        x = max(-r, min(r, x))
        return x * math.sqrt(max(0.0, r * r - x * x)) + r * r * math.asin(x / r)
    return f(min(x1, r)) - f(max(x0, -r))


def assert_add(before, after, min_mm3: float, label: str):
    added = after.volume - before.volume
    if added < min_mm3:
        raise AssertionError(
            f"{label}: union added {added:.3f} mm3, expected >= {min_mm3:.3f} -- "
            f"the feature landed inside existing material, or nowhere")
    return added


def one_solid(t, label: str):
    """Unwrap a boolean result and insist it is exactly ONE valid solid.

    THE CHECK THAT VOLUME CANNOT MAKE FOR YOU.  assert_add and assert_cut_band see
    only a scalar, and a boolean can go wrong in ways that leave the scalar looking
    fine: fusing a solid whose cylindrical face is EXACTLY coincident with an
    existing one (a boss whose OD equals the shell's OD, say) returns a plausible
    volume and a non-manifold result, and the damage only appears when some later,
    innocent boolean re-evaluates it and shatters the shape.  That is not
    hypothetical -- a screw boss here fused with the right volume, survived two more
    operations, and was then almost entirely deleted by a rib 20 mm away, leaving a
    23.6 mm3 orphan sliver.  Counting solids catches it at the operation that caused
    it instead of three features later.

    So: overlap features VOLUMETRICALLY, never face-to-face, and check topology
    after every boolean.
    """
    if isinstance(t, (list, tuple)) or type(t).__name__ == "ShapeList":
        vols = sorted((x.volume for x in t), reverse=True)
        raise AssertionError(
            f"{label}: the boolean returned {len(vols)} separate shapes "
            f"({', '.join(f'{v:.2f}' for v in vols[:5])} mm3) instead of one -- "
            f"the operands touch on a face somewhere instead of overlapping")
    n = len(t.solids())
    if n != 1:
        vols = sorted((x.volume for x in t.solids()), reverse=True)
        raise AssertionError(
            f"{label}: the result is {n} solids "
            f"({', '.join(f'{v:.2f}' for v in vols[:5])} mm3), not one -- "
            f"a feature has broken away or the shape has been shattered")
    # is_valid is a PROPERTY in build123d 0.10, not a method.  Called as t.is_valid()
    # it raises TypeError, and wrapped in a try/except that would have read as "this
    # build cannot check validity" -- so resolve it explicitly instead of guessing.
    valid = getattr(t, "is_valid", True)
    if callable(valid):
        valid = valid()
    if not valid:
        raise AssertionError(
            f"{label}: the result is one solid but not a VALID one -- it will "
            f"export and look right, and the next boolean will destroy it")
    return t


def add(s, feature, min_mm3: float, label: str):
    """Fuse, then check the volume added AND the topology.  Use this, not `+`."""
    t = one_solid(s + feature, label)
    assert_add(s, t, min_mm3, label)
    return t


def cut(s, cutter, lo_mm3: float, hi_mm3: float, label: str):
    """Subtract, then check the volume removed lands in a band AND the topology."""
    t = one_solid(s - cutter, label)
    assert_cut_band(s, t, lo_mm3, hi_mm3, label)
    return t


def assert_inside_bore(s, r_max: float, label: str):
    """Nothing may reach past the bore it has to slide down.

    Checked on the VERTICES rather than the bounding box: the bbox corner of a
    round part sits at r = sqrt(2)*R and is not a point of the solid at all, so a
    bbox test either fails a part that fits or, if loosened to compensate, passes
    one that does not.
    """
    r = max(math.hypot(v.X, v.Y) for v in s.vertices())
    if r > r_max + 1e-6:
        raise AssertionError(
            f"{label}: reaches r={r:.4f}, past the {r_max:.4f} it must pass -- "
            f"it will not go down the tube")
    return r
