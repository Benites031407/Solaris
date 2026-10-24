"""Geometry helpers shared by every part generator.  No numbers live here.

Everything in this motor is a body of revolution with a few radial features punched
through it, so the whole toolkit is four things:

  rz_face / revolve_rz   draw a half-section in the (r, z) plane and spin it about Z.
                         The half-section is the drawing a machinist would get, so
                         every profile in the part files reads like one.
  radial_*               cylinders and drills whose axis points straight out from the
                         motor axis at azimuth theta and station z.  Bolt holes,
                         tapped holes, puller holes.
  radial_trsf            the 4x4 that places a part whose local +Z is "outward" at
                         (theta, r, z).  Used by the assembly for every bolt.
  location               the same 4x4 turned back into a build123d Location, so the
                         verifier places parts with exactly the numbers the
                         assembly ships, not a re-derivation of them.

TRANSFORM CONVENTION
--------------------
text-to-cad reads an instance's "transform" as 16 floats, ROW-MAJOR, and passes the
first 12 straight into gp_Trsf.SetValues(): translation lives at indices 3, 7, 11.
radial_trsf() builds exactly that and nothing else in this project writes one by hand.

For a radial part the local frame is
    local +Z -> u  = (cos t, sin t, 0)       outward
    local +X -> ez = (0, 0, 1)               forward, along the motor axis
    local +Y -> u x ez = (sin t, -cos t, 0)  so that X x Y = Z (right-handed)
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from build123d import (
    Axis,
    Color,
    Edge,
    Face,
    Location,
    Plane,
    Solid,
    Vector,
    Wire,
    revolve,
)
from OCP.gp import gp_Trsf


# -----------------------------------------------------------------------------
# half-sections
# -----------------------------------------------------------------------------
def _v(rz: Sequence[float]) -> Vector:
    # the half-section lives in the XZ plane: x is radius, z is the motor axis
    return Vector(float(rz[0]), 0.0, float(rz[1]))


def arc_point(center: Sequence[float], radius: float, deg: float) -> tuple[float, float]:
    """A point on a circle in the (r, z) plane; 0 deg = +r, 90 deg = +z."""
    a = math.radians(deg)
    return (center[0] + radius * math.cos(a), center[1] + radius * math.sin(a))


def arc(center: Sequence[float], radius: float, deg0: float, deg1: float):
    """A circular arc as an rz_face() move, from deg0 to deg1 about center.

    Returns (start, move); the caller must already be AT start -- rz_face() checks.
    """
    start = arc_point(center, radius, deg0)
    mid = arc_point(center, radius, 0.5 * (deg0 + deg1))
    end = arc_point(center, radius, deg1)
    return start, ("arc", mid, end)


def rz_face(path: Iterable) -> Face:
    """A closed half-section.

    `path` items are either an (r, z) point -- a straight line to it -- or
    ("arc", (r_mid, z_mid), (r_end, z_end)) -- a three-point arc to r_end, z_end.
    The path is closed back to its first point with a line if it does not end there.
    """
    edges: list[Edge] = []
    first = cur = None
    for item in path:
        if isinstance(item[0], str):
            if item[0] != "arc":
                raise ValueError(f"unknown move {item[0]!r}")
            _, mid, end = item
            edges.append(Edge.make_three_point_arc(_v(cur), _v(mid), _v(end)))
            cur = tuple(map(float, end))
            continue
        pt = (float(item[0]), float(item[1]))
        if cur is None:
            first = cur = pt
            continue
        if math.dist(pt, cur) < 1e-9:
            continue
        edges.append(Edge.make_line(_v(cur), _v(pt)))
        cur = pt
    if cur is None or first is None:
        raise ValueError("empty path")
    if math.dist(cur, first) > 1e-9:
        edges.append(Edge.make_line(_v(cur), _v(first)))
    return Face(Wire(edges))


def revolve_rz(path: Iterable) -> Solid:
    """Spin a closed half-section a full turn about the motor axis."""
    part = revolve(rz_face(path), Axis.Z, 360.0)
    solids = part.solids()
    if len(solids) != 1:
        raise RuntimeError(f"revolve produced {len(solids)} solids, expected 1")
    return solids[0]


def tube(r_in: float, r_out: float, z0: float, z1: float) -> Solid:
    """A plain annulus r_in..r_out over z0..z1 (r_in may be 0 for a rod)."""
    lo, hi = min(z0, z1), max(z0, z1)
    return revolve_rz([(r_in, lo), (r_out, lo), (r_out, hi), (r_in, hi)])


# -----------------------------------------------------------------------------
# radial features
# -----------------------------------------------------------------------------
def radial_unit(theta_deg: float) -> Vector:
    t = math.radians(theta_deg)
    return Vector(math.cos(t), math.sin(t), 0.0)


def _radial_plane(theta_deg: float, r: float, z: float, inward: bool) -> Plane:
    u = radial_unit(theta_deg)
    origin = Vector(u.X * r, u.Y * r, z)
    return Plane(origin=origin, x_dir=(0, 0, 1), z_dir=(-u if inward else u))


def radial_cylinder(dia: float, r0: float, r1: float, theta_deg: float, z: float) -> Solid:
    """A cylinder on the radial line at (theta, z), spanning radius r0 .. r1."""
    lo, hi = min(r0, r1), max(r0, r1)
    return Solid.make_cylinder(dia / 2.0, hi - lo, _radial_plane(theta_deg, lo, z, False))


def radial_drill(dia: float, r_entry: float, depth: float, theta_deg: float, z: float,
                 point_deg: float = 118.0) -> Solid:
    """A blind drilled hole going INWARD from r_entry, `depth` to the full diameter,
    with a drill-point cone beyond it (118 deg twist drill by default)."""
    plane = _radial_plane(theta_deg, r_entry, z, inward=True)
    body = Solid.make_cylinder(dia / 2.0, depth, plane)
    tip_h = (dia / 2.0) / math.tan(math.radians(point_deg / 2.0))
    tip_plane = plane.offset(depth)
    tip = Solid.make_cone(dia / 2.0, 0.0, tip_h, tip_plane)
    return body.fuse(tip).clean().solids()[0]


def radial_countersink(d_hole: float, r_surface: float, size: float, theta_deg: float,
                       z: float, outward: bool) -> Solid:
    """A size x 45 deg break on a radial hole's edge where it meets the cylinder
    r_surface.  outward=True breaks the edge on the OUTSIDE of that surface (a hole
    entering from r > r_surface), False on the inside (a bore-side edge)."""
    # A true 45 deg cone, based `size` off the surface on the air side so it cuts
    # the mouth at d/2 + size and meets the hole wall exactly `size` into the part.
    r_base = d_hole / 2.0 + 2.0 * size
    if outward:
        plane = _radial_plane(theta_deg, r_surface + size, z, inward=True)
    else:
        plane = _radial_plane(theta_deg, r_surface - size, z, inward=False)
    return Solid.make_cone(r_base, 0.0, r_base, plane)


def axial_drill(dia: float, x: float, y: float, z_entry: float, depth: float,
                point_deg: float = 118.0, toward: float = -1.0) -> Solid:
    """A blind hole drilled from z_entry at (x, y) in the direction `toward` (-1 = -Z,
    +1 = +Z), `depth` to full diameter, with a drill-point cone beyond."""
    plane = Plane(origin=(x, y, z_entry), x_dir=(1, 0, 0), z_dir=(0, 0, math.copysign(1.0, toward)))
    body = Solid.make_cylinder(dia / 2.0, depth, plane)
    tip_h = (dia / 2.0) / math.tan(math.radians(point_deg / 2.0))
    tip = Solid.make_cone(dia / 2.0, 0.0, tip_h, plane.offset(depth))
    return body.fuse(tip).clean().solids()[0]


def radial_trsf(theta_deg: float, r: float, z: float) -> list[float]:
    """Row-major 4x4 placing a part's local origin at (theta, r, z) with its local +Z
    pointing radially outward.  See the module docstring for the full frame."""
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return [
        0.0, s, c, r * c,
        0.0, -c, s, r * s,
        1.0, 0.0, 0.0, z,
        0.0, 0.0, 0.0, 1.0,
    ]


def axial_trsf(z: float, rot_deg: float = 0.0) -> list[float]:
    """Row-major 4x4: rotate about Z by rot_deg, then translate along Z."""
    t = math.radians(rot_deg)
    c, s = math.cos(t), math.sin(t)
    return [
        c, -s, 0.0, 0.0,
        s, c, 0.0, 0.0,
        0.0, 0.0, 1.0, z,
        0.0, 0.0, 0.0, 1.0,
    ]


def location(t: Sequence[float]) -> Location:
    """The inverse of the helpers above: a 16-float row-major transform as a Location,
    built the same way text-to-cad's assembly exporter builds it."""
    if len(t) != 16:
        raise ValueError("transform must have 16 values")
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in t[:12]])
    return Location(tr)


# -----------------------------------------------------------------------------
# finishing
# -----------------------------------------------------------------------------
def finish(shape, label: str, rgb: Sequence[float]):
    """Label and colour a part the way text-to-cad writes them into the STEP."""
    shape.label = label
    shape.color = Color(*rgb)
    return shape


def one_solid(shape) -> Solid:
    """Collapse a boolean result to its single solid, or fail loudly."""
    solids = shape.solids()
    if len(solids) != 1:
        raise RuntimeError(f"expected exactly 1 solid, got {len(solids)}")
    return solids[0]


# -----------------------------------------------------------------------------
# seals
# -----------------------------------------------------------------------------
def squeezed_oring(r_in: float, r_out: float, cs: float, z: float = 0.0) -> Solid:
    """An O-ring as installed in a radial gland: its section squashed from a cs circle
    to an ellipse that spans r_in..r_out radially and keeps the free section's area
    (elastomer is incompressible), so its axial width is cs^2 / (r_out - r_in)."""
    from build123d import Ellipse, Pos

    h = r_out - r_in
    w = cs * cs / h
    section = Plane.XZ * Pos((r_in + r_out) / 2.0, z) * Ellipse(h / 2.0, w / 2.0)
    part = revolve(section, Axis.Z, 360.0)
    return one_solid(part)


# -----------------------------------------------------------------------------
# fasteners
# -----------------------------------------------------------------------------
def button_head_screw(d: float, length: float, dk: float, k: float, s: float, t: float,
                      edge_h: float = 0.6, tip_chamfer: float = 0.5) -> Solid:
    """ISO 7380-1-style button head cap screw.

    Local frame: axis = Z, head bearing face at z = 0, head toward +Z, shank toward
    -Z to z = -length.  The thread is drawn as its major-diameter cylinder (the
    tapped holes it goes into are drawn at tap-drill size, so the overlap between the
    two IS the thread engagement -- srm_verify.py measures it that way).

    The dome is one circular arc centred on the axis through the head's edge at
    (dk/2, edge_h) and its crown at (0, k); the hex socket is s across flats, t deep.
    """
    from build123d import Plane as _Plane, RegularPolygon, extrude

    rk = dk / 2.0
    # circle centred on the axis through (rk, edge_h) and (0, k)
    R = (rk * rk + (k - edge_h) ** 2) / (2.0 * (k - edge_h))
    zc = k - R
    a0 = math.degrees(math.atan2(edge_h - zc, rk))
    start, dome = arc((0.0, zc), R, a0, 90.0)
    rs = d / 2.0
    path = [
        (0.0, -length),
        (rs - tip_chamfer, -length),
        (rs, -length + tip_chamfer),
        (rs, 0.0),
        (rk, 0.0),
        start,
        dome,
    ]
    body = revolve_rz(path)
    hexa = _Plane.XY.offset(k - t) * RegularPolygon(radius=s / 2.0, side_count=6, major_radius=False)
    socket = extrude(hexa, amount=t + 1.0)
    return one_solid(body - socket)
