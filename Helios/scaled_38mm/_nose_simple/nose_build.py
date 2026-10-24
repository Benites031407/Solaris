"""Shared build123d constructions for the simple clamshell nose.

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
    extrude(that_face, amount=+a)              ->  sweeps into +X
    revolve(Plane.XZ face, Axis.Z, 360)        ->  volume matches the analytic
                                                   annulus to 0.01 mm3

The helpers below wrap those so no caller has to remember the sign.
"""

from __future__ import annotations

import math

import numpy as np
from build123d import (Align, Axis, Box, Cylinder, Plane, Polyline, Pos, Rot,
                       extrude, make_face, revolve)

import nose_params as P
import nose_profile as prof

BIG = 400.0          # bigger than the whole nose, for keep-out and cutting solids


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


def cyl_along(axis: str, base, d: float, length: float):
    """A cylinder of diameter `d` starting at `base` and running `length` along +axis."""
    dirs = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
    xdirs = {"x": (0, 1, 0), "y": (0, 0, 1), "z": (1, 0, 0)}
    pl = Plane(origin=tuple(base), x_dir=xdirs[axis], z_dir=dirs[axis])
    return pl * Cylinder(radius=d / 2, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))


def radial_hole(d: float, theta_deg: float, z: float, r0: float, r1: float):
    """A cylinder boring radially outward through a wall, at azimuth theta."""
    t = math.radians(theta_deg)
    base = (r0 * math.cos(t), r0 * math.sin(t), z)
    pl = Plane(origin=base, x_dir=(0, 0, 1), z_dir=(math.cos(t), math.sin(t), 0))
    return pl * Cylinder(radius=d / 2, height=(r1 - r0),
                         align=(Align.CENTER, Align.CENTER, Align.MIN))


def wedge(theta_deg: float, half_chord: float, r_in: float, r_out: float,
          z0: float, z1: float):
    """A radial block centred on azimuth `theta`, `half_chord`*2 wide, for local bosses."""
    b = Box(r_out - r_in, 2 * half_chord, z1 - z0,
            align=(Align.MIN, Align.CENTER, Align.MIN))
    return Rot(0, 0, theta_deg) * Pos(r_in, 0, z0) * b


def keepout_below_y(y_plane: float, target):
    """Everything with y < y_plane -- the cutter that makes a half out of a whole.

    An explicit cutting box, deliberately not `split(bisect_by=..., keep=...)`:
    Keep.TOP on Plane.XZ returns the -Y half in this version, which is exactly
    backwards from the name, and a silently mirrored part is the worst kind of bug
    here because the two halves are supposed to be interchangeable.

    The cutter is sized FROM `target`, not from a generous-looking constant.  A
    fixed 400 mm box centred on the origin looks like it covers everything and
    silently leaves the last 49 mm of a 249 mm nose uncut -- and the volume
    removed is still most of the part, so a plain "did the boolean bite" check
    sails straight past it.
    """
    lo, hi = bbox(target)
    pad = 10.0
    sx = 2 * max(abs(lo[0]), abs(hi[0])) + pad
    sz = (hi[2] - lo[2]) + 2 * pad
    depth = (y_plane - lo[1]) + pad
    return Pos(0, y_plane, (lo[2] + hi[2]) / 2) * Box(
        sx, depth, sz, align=(Align.CENTER, Align.MAX, Align.CENTER))


# ----------------------------------------------------------------- the ogive

def decimate(z, r, tol: float = 0.008):
    """Douglas-Peucker the (z, r) polyline to `tol` mm of chord error.

    The measured table is 787 rows at 0.25 mm pitch.  Revolving that many faces
    and then booleaning against them is slow and numerically noisy for no gain:
    the ogive's curvature is gentle enough that 0.008 mm of chord error -- a
    twentieth of a layer height, well inside the printer's own resolution --
    needs far fewer points.
    """
    z = np.asarray(z, float)
    r = np.asarray(r, float)
    keep = np.zeros(len(z), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(z) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        dz, dr = z[j] - z[i], r[j] - r[i]
        n = math.hypot(dz, dr)
        d = np.abs((z[i + 1:j] - z[i]) * dr - (r[i + 1:j] - r[i]) * dz) / n
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack += [(i, m), (m, j)]
    return z[keep], r[keep]


def ogive_tables(wall: float = None, tol: float = 0.008):
    """Decimated (z, r_outer) and (z, r_inner) tables for the printed shell.

    r_inner is the TRUE normal offset expressed radially: a wall is only a wall
    perpendicular to the face it backs, so the radial step is wall/cos(slope),
    not wall.  Near the apex 1/cos blows up, so the inner surface is truncated
    where it would close on itself and the tip is left solid.
    """
    if wall is None:
        wall = P.WALL
    d = prof.debiased_profile()
    z, ro = d[:, 0], d[:, 1]
    m = z >= P.Z_SHELL_ROOT - 1e-6
    z, ro = z[m], ro[m]
    z = np.concatenate([[P.Z_SHELL_ROOT], z[1:]])
    ro = np.concatenate([[P.R_AIRFRAME], ro[1:]])

    slope = np.arctan(-np.gradient(ro, z))
    ri = ro - wall / np.cos(np.clip(slope, 0.0, math.radians(88.0)))

    zo, rr_o = decimate(z, ro, tol)
    ok = ri > 0.4
    last = int(np.max(np.nonzero(ok)[0]))
    zi, rr_i = decimate(z[:last + 1], ri[:last + 1], tol)
    return (np.column_stack([zo, rr_o]), np.column_stack([zi, rr_i]))


def shell_outer(wall: float = None, tol: float = 0.008):
    """The full solid ogive from the root plane to the apex (both halves, no cavity)."""
    o, _ = ogive_tables(wall, tol)
    pts = [(0.0, P.Z_SHELL_ROOT)] + [(r, z) for z, r in o]
    if pts[-1][0] > 1e-9:
        pts.append((0.0, P.Z_TIP))
    return revolve_rz(pts)


def shell_cavity(wall: float = None, tol: float = 0.008):
    """The void inside the shell, extended below the root so the base is open."""
    _, i = ogive_tables(wall, tol)
    z_bot = P.Z_SHELL_ROOT - 4.0
    pts = [(0.0, z_bot), (i[0, 1], z_bot)] + [(r, z) for z, r in i] + [(0.0, i[-1, 0])]
    return revolve_rz(pts)


def shell_envelope(wall: float = None, tol: float = 0.008):
    """Outer skin PLUS the ring's bore below the root.

    Everything added to a half-shell gets intersected with this, which makes it
    impossible for a boss, gusset or pad to poke out through the skin or to grow
    outside the ring bore below the root plane, no matter how the numbers drift.
    Cheaper than re-deriving a clearance by hand every time a feature moves.
    """
    bore = revolve_rz([(0.0, 0.0), (P.RING_BORE, 0.0),
                       (P.RING_BORE, P.Z_SHELL_ROOT), (0.0, P.Z_SHELL_ROOT)])
    return shell_outer(wall, tol) + bore


def chamfer_ring_cutter(r_nom: float, z_face: float, size: float, outward_up: bool):
    """A revolved cutter that puts a 45 deg chamfer on a circular edge.

    `outward_up=True` chamfers the edge where an OUTER cylinder meets the face
    ABOVE it (material lies above `z_face`); False for the face below.
    """
    if outward_up:
        pts = [(r_nom - size, z_face), (r_nom + 2.0, z_face),
               (r_nom + 2.0, z_face + size + 2.0)]
    else:
        pts = [(r_nom - size, z_face), (r_nom + 2.0, z_face),
               (r_nom + 2.0, z_face - size - 2.0)]
    return revolve_rz(pts)


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


def assert_add(before, after, min_mm3: float, label: str):
    added = after.volume - before.volume
    if added < min_mm3:
        raise AssertionError(
            f"{label}: union added {added:.3f} mm3, expected >= {min_mm3:.3f} -- "
            f"the feature landed inside existing material, or nowhere")
    return added


def assert_half(s, y_plane: float, label: str):
    """A half must live entirely on one side of the seam.  Never trust Keep.TOP."""
    lo, hi = bbox(s)
    if lo[1] < y_plane - 1e-6:
        raise AssertionError(f"{label}: reaches y={lo[1]:.4f}, past the seam plane "
                             f"y={y_plane:.4f} -- the wrong half was kept")
