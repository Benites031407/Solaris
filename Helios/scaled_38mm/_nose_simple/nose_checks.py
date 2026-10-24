"""Geometric verification helpers for the simple clamshell nose.

WHY THIS MODULE EXISTS
----------------------
On this project, every cheap check -- watertightness, pairwise interference,
max-vertex radius, mass agreement between scripts -- has at some point passed on
a part with three unintended holes through its wall.  Those checks confirm parts
do not COLLIDE.  None of them confirms a feature is the SHAPE it was meant to be.

So this module provides the two checks that do catch that class of bug:

1. `assert_removed` -- a boolean that removes nothing is silent.  Assert the
   volume actually went down by a plausible amount, every time.
2. `radial_ray` / `probe` -- point-in-mesh probing of the EXPORTED mesh along a
   ray whose answer you can predict, at the azimuth a feature is supposed to be
   at AND at an azimuth it is supposed to miss.

FACETING RULE (do not skip this)
--------------------------------
A faceted cylinder's z section is the polygon INSCRIBED in the true circle, so
its edge midpoints sit at r*cos(pi/n) < r while its vertices sit at r.  Two
consequences:

* A probe placed analytically at exactly r = R falls OUTSIDE the mesh over most
  of each facet.  Always offset a probe by `chord_sagitta` * a safety factor in
  the direction that puts it clearly inside material, and say which way and why.
* `max` vertex radius of a section reports the TRUE radius; `min` vertex radius
  under-reports it by the sagitta.  Use the right one for the question asked.
"""

from __future__ import annotations

import math

import numpy as np
import trimesh


# --------------------------------------------------------------------------- io

def load(path) -> trimesh.Trimesh:
    m = trimesh.load(str(path), force="mesh")
    if not isinstance(m, trimesh.Trimesh):
        raise TypeError(f"{path} did not load as a single mesh: {type(m)}")
    return m


# ------------------------------------------------------------------ tessellation

def chord_sagitta(r: float, mesh: trimesh.Trimesh | None = None,
                  n_facets: int | None = None) -> float:
    """Height of the gap between the true circle at `r` and the mesh's chord.

    This is how far INSIDE the nominal radius the mesh surface can be.  Pass
    `n_facets` if known; otherwise it is estimated from the mesh's own angular
    resolution, falling back to a conservative 64.
    """
    if n_facets is None:
        n_facets = 64
        if mesh is not None:
            try:
                n_facets = max(24, min(360, estimate_facets(mesh)))
            except Exception:
                pass
    return r * (1.0 - math.cos(math.pi / n_facets))


def estimate_facets(mesh: trimesh.Trimesh, z: float | None = None) -> int:
    """Count distinct azimuths in one z section -- the surface's facet count."""
    if z is None:
        z = float(np.mean(mesh.bounds[:, 2]))
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        raise ValueError(f"no section at z={z}")
    v = np.asarray(sec.vertices)
    th = np.unique(np.round(np.degrees(np.arctan2(v[:, 1], v[:, 0])), 2))
    return int(len(th))


# ------------------------------------------------------------------- probing

def probe(mesh: trimesh.Trimesh, pts) -> np.ndarray:
    """Boolean 'is inside the solid' for each of `pts`.  Requires a closed mesh."""
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    if not mesh.is_watertight:
        raise ValueError("point-in-mesh probing needs a watertight mesh; "
                         "repair or report the leak instead of trusting this")
    return mesh.contains(pts)


def cyl(r: float, theta_deg: float, z: float) -> tuple[float, float, float]:
    t = math.radians(theta_deg)
    return (r * math.cos(t), r * math.sin(t), z)


def radial_ray(mesh: trimesh.Trimesh, theta_deg: float, z: float,
               r0: float, r1: float, step: float = 0.25):
    """Sample solid/void along a radial ray.  Returns (radii, inside_bools)."""
    rs = np.arange(r0, r1 + 1e-9, step)
    pts = np.array([cyl(float(r), theta_deg, z) for r in rs])
    return rs, probe(mesh, pts)


def spans(rs: np.ndarray, inside: np.ndarray) -> list[tuple[float, float, bool]]:
    """Compress a probe into [(r_start, r_end, is_solid), ...] runs."""
    out = []
    if len(rs) == 0:
        return out
    cur, start = bool(inside[0]), float(rs[0])
    for r, f in zip(rs[1:], inside[1:]):
        if bool(f) != cur:
            out.append((start, float(r), cur))
            cur, start = bool(f), float(r)
    out.append((start, float(rs[-1]), cur))
    return out


def describe_ray(mesh, theta_deg, z, r0, r1, step=0.25) -> str:
    rs, ins = radial_ray(mesh, theta_deg, z, r0, r1, step)
    parts = [f"r{a:.2f}-{b:.2f} {'SOLID' if s else 'void '}" for a, b, s in spans(rs, ins)]
    return f"theta={theta_deg:7.2f} z={z:8.3f} | " + " | ".join(parts)


def axial_ray(mesh: trimesh.Trimesh, r: float, theta_deg: float,
              z0: float, z1: float, step: float = 0.25):
    zs = np.arange(z0, z1 + 1e-9, step)
    pts = np.array([cyl(r, theta_deg, float(z)) for z in zs])
    return zs, probe(mesh, pts)


# ----------------------------------------------------------------- assertions

class CheckError(AssertionError):
    pass


def assert_removed(vol_before: float, vol_after: float, min_mm3: float,
                   label: str) -> float:
    """A subtraction that removes nothing is silent.  Make it loud."""
    removed = vol_before - vol_after
    if removed < min_mm3:
        raise CheckError(
            f"{label}: boolean removed {removed:.3f} mm3, expected >= {min_mm3:.3f}. "
            f"The cut is missing the material it was aimed at.")
    return removed


def assert_solid(mesh, theta_deg, z, r, label, mesh_for_facets=None):
    """Assert the point is INSIDE.  `r` is pulled inward by one sagitta."""
    off = chord_sagitta(r, mesh_for_facets or mesh)
    p = cyl(r - 2.0 * off, theta_deg, z)   # inward: toward the axis, into material
    if not probe(mesh, [p])[0]:
        raise CheckError(f"{label}: expected SOLID at theta={theta_deg} z={z} "
                         f"r={r} (probed r={r - 2*off:.4f}, offset inward by "
                         f"2 sagittae={2*off:.4f} because the mesh chord lies "
                         f"inside the nominal radius) -- found VOID")


def assert_void(mesh, theta_deg, z, r, label):
    if probe(mesh, [cyl(r, theta_deg, z)])[0]:
        raise CheckError(f"{label}: expected VOID at theta={theta_deg} z={z} "
                         f"r={r} -- found SOLID")


def assert_watertight(mesh, label):
    if not mesh.is_watertight:
        raise CheckError(f"{label}: mesh is not watertight "
                         f"({len(trimesh.repair.broken_faces(mesh))} broken faces)")
    if mesh.volume <= 0:
        raise CheckError(f"{label}: non-positive volume {mesh.volume:.3f} mm3 "
                         f"(inverted normals?)")


def assert_single_body(mesh, label, expect: int = 1):
    n = len(mesh.split(only_watertight=False))
    if n != expect:
        raise CheckError(f"{label}: mesh splits into {n} bodies, expected {expect}. "
                         f"A stray shell from a failed boolean reads as extra volume.")


# -------------------------------------------------------------- measurements

def section_radii(mesh: trimesh.Trimesh, z: float):
    """(r_out_max, r_in_min, n_loops) of one z section, from raw vertices.

    r_out uses MAX vertex radius (the true outer radius of an inscribed polygon);
    r_in uses MIN vertex radius.  Returns None if the section is empty.
    """
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    v = np.asarray(sec.vertices)
    rr = np.hypot(v[:, 0], v[:, 1])
    return float(rr.max()), float(rr.min()), len(sec.entities)


def wall_thickness(mesh, theta_deg, z, r_start, r_end, step=0.05) -> float:
    """Radial thickness of the first solid run met walking inward from r_start."""
    rs = np.arange(r_start, r_end - 1e-9, -abs(step))
    pts = np.array([cyl(float(r), theta_deg, z) for r in rs])
    ins = probe(mesh, pts)
    if not ins.any():
        return 0.0
    i0 = int(np.argmax(ins))
    j = i0
    while j < len(ins) and ins[j]:
        j += 1
    return float(abs(rs[i0] - rs[min(j, len(rs) - 1)]))


def bed_fit(mesh, bed=(300.0, 300.0, 300.0), label="part"):
    """Report the part's bbox against the build volume in its current pose."""
    e = mesh.extents
    ok = all(e[i] <= bed[i] for i in range(3))
    return ok, (f"{label}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm vs bed "
                f"{bed[0]:.0f} x {bed[1]:.0f} x {bed[2]:.0f} -- "
                f"{'FITS' if ok else 'DOES NOT FIT'}")


def mass_g(mesh, density_g_cm3: float = 1.04) -> float:
    """ABS mass.  stability.py carries ABS at 1.04 g/cm3."""
    return mesh.volume / 1000.0 * density_g_cm3


def min_clearance(a: trimesh.Trimesh, b: trimesh.Trimesh, samples: int = 60000) -> float:
    """Approx minimum surface-to-surface distance; negative-ish if interpenetrating.

    Samples `a`'s surface and measures to `b`.  Approximate by construction --
    use it to find WHERE things are tight, then confirm that spot exactly.
    """
    pts = a.sample(samples)
    d = trimesh.proximity.signed_distance(b, pts)
    return float(-d.max()) if d.max() > 0 else float(np.abs(d).min())


def report(lines, title):
    w = max(len(title) + 4, 72)
    print("=" * w)
    print(f"  {title}")
    print("=" * w)
    for ln in lines:
        print(ln)
