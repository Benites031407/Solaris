"""Geometry helpers for the casting molds.  No numbers live here.

Every mold and silicone piece is a body of revolution with a few features punched in,
so the toolkit is a half-section in the (r, z) plane spun about Z.  Same conventions
as _srm100/srm_build.py.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from build123d import Axis, Color, Compound, Edge, Face, Location, Solid, Vector, Wire, revolve


def _v(rz: Sequence[float]) -> Vector:
    # the half-section lives in the XZ plane: x is radius, z is the mold axis
    return Vector(float(rz[0]), 0.0, float(rz[1]))


def rz_face(path: Iterable) -> Face:
    """A closed half-section: items are (r, z) points (straight line to them) or
    ("arc", (r_mid, z_mid), (r_end, z_end)).  Closed back to the first point."""
    edges: list[Edge] = []
    first = cur = None
    for item in path:
        if isinstance(item[0], str):
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
    if math.dist(cur, first) > 1e-9:
        edges.append(Edge.make_line(_v(cur), _v(first)))
    return Face(Wire(edges))


def revolve_rz(path: Iterable, seam_deg: float = 0.0) -> Solid:
    """Spin a closed half-section a full turn about Z.  seam_deg turns the revolve seam
    off any radial feature (the STEP round trip can lose a feature cut on the seam)."""
    part = revolve(rz_face(path), Axis.Z, 360.0)
    solids = part.solids()
    if len(solids) != 1:
        raise RuntimeError(f"revolve produced {len(solids)} solids, expected 1")
    s = solids[0]
    return s.rotate(Axis.Z, seam_deg) if seam_deg else s


def tube(r_in: float, r_out: float, z0: float, z1: float) -> Solid:
    lo, hi = min(z0, z1), max(z0, z1)
    return revolve_rz([(r_in, lo), (r_out, lo), (r_out, hi), (r_in, hi)])


def one_solid(shape) -> Solid:
    solids = shape.solids()
    if len(solids) != 1:
        raise RuntimeError(f"expected one solid, got {len(solids)}")
    return solids[0]


def finish(shape, label: str, rgb=(0.8, 0.8, 0.8)):
    shape = one_solid(shape.clean()) if not isinstance(shape, Compound) else shape
    shape.label = label
    shape.color = Color(*rgb)
    return shape


def flip_z(shape, z_top: float):
    """Turn a part upside down about its own axis so z_top lands on z = 0."""
    return shape.rotate(Axis.X, 180.0).moved(Location((0.0, 0.0, z_top)))
