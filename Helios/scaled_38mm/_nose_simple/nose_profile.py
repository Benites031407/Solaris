"""Authoritative outer profile for the simple clamshell nose cone.

THE COMBINED PROFILE
--------------------
    z_root .. 52.4138   cylinder at r = 32.75861  (flush with the airframe OD)
    52.4138 .. 248.9655 the measured ogive, from `_clam/ogive_prof.npy`

52.4138 is design intent, not a fit: it is 40.000 mm x the 1.310345 scale factor
this rocket was scaled by, and it is measured to be the exact station where the
outer radius stops being constant.  Below it the cone is a PLAIN CYLINDER at the
airframe radius, slope 0.000 deg over 0.25 mm steps -- there is no base flare.

WHICH ARRAY IS THE TRUTH, AND WHY IT MATTERS
--------------------------------------------
Three profile arrays exist for this cone.  Two of them agree and one is wrong.

  `_clam/ogive_prof.npy`            (3, 787) rows (z, r_out, r_inner), 0.25 mm
                                    pitch, z 52.414..248.914.  r_out[0] is
                                    exactly 32.7586067 = the airframe radius and
                                    r_out is monotone non-increasing.  THE TRUTH,
                                    and what this module loads.
  `_nose_simple/outer_profile_debiased.npy`
                                    my independent ray-cast reconstruction.
                                    Agrees with the above: mean +0.0036 mm,
                                    range -0.021..+0.022.  Kept as a cross-check.
                                    (Sign: POSITIVE means the ray-cast array reads
                                    fatter.  This said -0.0036 and had it backwards,
                                    which is the one direction that matters here --
                                    the whole section is about an estimator biased
                                    OUTWARD.)
  `_clamshell/ogive_measured.npy`   FAT.  Do not use.  See below.

`ogive_measured.npy` was built from the MAX VERTEX RADIUS of each z SECTION of
`cone_fixed.stl`, and that estimator is biased OUTWARD on a taper:

    On a CYLINDER it is exact -- a z section crosses only the vertical edges, so
    every section point shares one radius.  Mbody sections span just 0.002 mm.

    On a TAPER it is not.  The mesh's vertices lie in rows at discrete z, and a
    section between two rows crosses the diagonal edges as well, so its points
    span [r(z_row_above), r(z_row_below)] -- a spread of slope x row_spacing,
    0.56 mm at z = 100.  Taking the MAX therefore reports the radius of the row
    BELOW z, not the radius AT z.

    Sampling AT a vertex row is exact again, which is why the two good arrays
    agree: one lands on the rows, the other ray-casts and never uses vertices.

Measured bias of the bad array: mean +0.347, peak +0.586 mm on the RADIUS at
z 63.5 (1.17 mm on diameter).  Two proofs it is the bad one, not the other two:

1. Its r(54) = 33.031 EXCEEDS the mesh's own global maximum vertex radius of
   32.7586.  No measurement of this mesh can return that.  It also rises with z
   at z = 60 and 63, and the true surface is monotone.
2. It puts the base 0.276 mm PROUD of the airframe, i.e. a forward-facing lip
   standing into the airflow.  The two good arrays put z=54 at 32.646, which is
   0.113 mm INSIDE the tube.  The "0.276 mm base flare" is the estimator, not a
   feature; a flush-clamp was already being designed around that phantom.

CONVENTIONS
-----------
* z from the BASE of the nose assembly, +z toward the tip, same origin as
  `cone_fixed.stl`: z = 0 is the aft face of the base ring's spigot, z = 248.9655
  is the apex.  Every z in this package is in that frame.
* r is the OUTER radius; walls are applied inward from it, and a WALL IS ONLY A
  WALL PERPENDICULAR TO THE SKIN -- see `wall_normal_to_radial`.
* Both ends of an extent are always named (`z_root` / `z_tip`), never a bare
  number.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# --- datums (mm), measured off the STLs and confirmed against the scale factor
R_AIRFRAME = 32.75860673904564   # airframe OUTER radius; tube OD 65.51721
Z_OGIVE = 52.4138        # ogive start = 40.000 x 1.310345; plain cylinder below
Z_TIP = 248.9655         # apex, in nose-base coords
SCALE = 1.310345         # = 65.51721 / 50, confirmed on 4 independent features

_HERE = Path(__file__).resolve().parent
# The authoritative table normally lives one directory up, in the working folder it
# was measured in.  A COPY inside this package is the fallback, so _nose_simple/ can
# be zipped and handed to someone on its own -- which is the point of it being a
# package and not a scratch directory.  Order matters and the sibling wins: a
# re-measurement upstream must be picked up, not silently shadowed by a stale local
# copy.  If neither exists, _primary() says so and names both places it looked,
# instead of letting numpy raise about a path the reader has no context for.
_PRIMARY_PATHS = (_HERE.parent / "_clam" / "ogive_prof.npy",
                  _HERE / "ogive_prof.npy")                # (3, N): z, r_out, r_in
_PRIMARY = next((q for q in _PRIMARY_PATHS if q.exists()), _PRIMARY_PATHS[0])
_XCHECK = _HERE / "outer_profile_debiased.npy"            # (N, 2): z, r_out
_BAD = _HERE.parent / "_clamshell" / "ogive_measured.npy"  # fat -- comparison only
# _BAD IS ALREADY GONE -- _clamshell/ was deleted at some point and nobody noticed,
# because nothing is BUILT from that array; it only ever fed the comparison below.  So
# `python nose_profile.py` had been dying on a FileNotFoundError with the numbers that
# justify this whole docstring in the traceback rather than in the report.
#
# These are those numbers, taken from the section above, which is the only surviving
# record of the measurement.  If the array ever comes back, bias_vs_raw() measures
# again and this constant stops being used -- and the self-check says which it did.
_BIAS_MEASURED = (0.3468, 0.5859, 63.5)


def _primary() -> np.ndarray:
    if not _PRIMARY.exists():
        raise FileNotFoundError(
            "the authoritative ogive table is missing; looked for\n  "
            + "\n  ".join(str(q) for q in _PRIMARY_PATHS)
            + "\nCopy _clam/ogive_prof.npy next to nose_profile.py to make this "
              "package self-contained.")
    a = np.load(_PRIMARY)
    if a.shape[0] != 3:
        raise ValueError(f"expected (3, N) (z, r_out, r_in) in {_PRIMARY}, got {a.shape}")
    return a


def raw_profile() -> np.ndarray:
    """The discredited max-vertex-radius array.  FOR COMPARISON ONLY -- it is fat."""
    return np.load(_BAD)


def inner_profile_measured() -> np.ndarray:
    """(z, r_inner) of the ORIGINAL cone's wall.  Not used for the new shells.

    The original wall is 1.30-1.39 mm measured NORMAL to the skin (nominally
    1.33).  The new shells use a deliberately thicker wall -- see nose_params.
    """
    a = _primary()
    return np.column_stack([a[0], a[2]])


def debiased_profile() -> np.ndarray:
    """The ogive as (z, r_outer) rows, apex closed at Z_TIP.  This is the authority."""
    a = _primary()
    z, ro = a[0], a[1]
    out = np.column_stack([z, ro])
    if out[-1, 0] < Z_TIP - 1e-9:          # table stops 0.05 mm short of the apex
        out = np.vstack([out, [[Z_TIP, 0.0]]])
    return out


def outer_profile(z_root: float = 0.0, dz: float = 0.25) -> np.ndarray:
    """Full outer profile (z, r) from `z_root` to the apex.

    Cylindrical at R_AIRFRAME below Z_OGIVE, the measured ogive above it.
    """
    d = debiased_profile()
    z_hi = np.unique(np.concatenate([np.arange(Z_OGIVE, Z_TIP, dz), [Z_TIP]]))
    r_hi = np.interp(z_hi, d[:, 0], d[:, 1])
    parts = [np.column_stack([z_hi, r_hi])]
    if z_root < Z_OGIVE:
        z_lo = np.arange(z_root, Z_OGIVE, dz)
        parts.insert(0, np.column_stack([z_lo, np.full_like(z_lo, R_AIRFRAME)]))
    prof = np.vstack(parts)
    return prof[prof[:, 0] >= z_root - 1e-9]


def r_outer(z):
    """Outer radius at z (scalar or array)."""
    d = debiased_profile()
    z = np.asarray(z, dtype=float)
    return np.where(z <= Z_OGIVE, R_AIRFRAME,
                    np.interp(z, d[:, 0], d[:, 1], left=R_AIRFRAME, right=0.0))


def slope_deg(z) -> float:
    """Local cone half-angle of the outer surface at z, degrees."""
    d = debiased_profile()
    dr = np.gradient(d[:, 1], d[:, 0])
    return float(np.degrees(np.arctan(-np.interp(z, d[:, 0], dr))))


def r_inner(z, wall_normal: float):
    """Inner radius for a wall of `wall_normal` measured PERPENDICULAR to the skin.

    A wall is only a wall perpendicular to the face it backs.  Offsetting the
    radius by the wall thickness gives a wall that is too THIN by cos(slope);
    the radial step must be wall / cos(slope).  At the base the slope is 4.06 deg
    so the difference is only 0.25 %, but the function keeps the intent explicit.
    """
    z = np.asarray(z, dtype=float)
    s = np.radians(np.array([slope_deg(float(zz)) for zz in np.atleast_1d(z)]))
    return r_outer(z) - wall_normal / np.cos(s).reshape(np.shape(z) or (1,))


def wall_normal_to_radial(wall_normal: float, z: float) -> float:
    """Radial step that yields `wall_normal` measured perpendicular to the skin."""
    import math
    return wall_normal / math.cos(math.radians(slope_deg(z)))


def bias_vs_raw():
    """(mean, peak, z_of_peak) of the bad array minus the truth, mm of radius.

    Falls back to _BIAS_MEASURED when the discredited array is not present.
    """
    if not _BAD.exists():
        return _BIAS_MEASURED
    raw, deb = raw_profile(), debiased_profile()
    z = raw[(raw[:, 0] >= deb[0, 0]) & (raw[:, 0] <= 244.0), 0]
    d = np.interp(z, raw[:, 0], raw[:, 1]) - np.interp(z, deb[:, 0], deb[:, 1])
    return float(d.mean()), float(d.max()), float(z[int(np.argmax(d))])


def xcheck_vs_primary():
    """(mean, min, max) of my independent ray-cast array minus the primary table."""
    c = np.load(_XCHECK)
    d = debiased_profile()
    m = (c[:, 0] >= d[0, 0]) & (c[:, 0] <= d[-2, 0])
    diff = c[m, 1] - np.interp(c[m, 0], d[:, 0], d[:, 1])
    return float(diff.mean()), float(diff.min()), float(diff.max())


def base_slope_deg() -> float:
    """Cone half-angle of the straight run just above Z_OGIVE, degrees."""
    d = debiased_profile()
    m = (d[:, 0] >= Z_OGIVE) & (d[:, 0] <= Z_OGIVE + 10.0)
    a = np.polyfit(d[m, 0], d[m, 1], 1)
    return float(np.degrees(np.arctan(-a[0])))


def cavity_volume(z_floor: float, wall: float, z_ceiling: float = Z_TIP) -> float:
    """Interior volume in cm3 between z_floor and z_ceiling for a normal wall."""
    prof = outer_profile(z_root=z_floor, dz=0.1)
    m = (prof[:, 0] >= z_floor) & (prof[:, 0] <= z_ceiling)
    z = prof[m, 0]
    r = np.maximum(np.asarray(r_inner(z, wall)).ravel(), 0.0)
    return float(np.trapezoid(np.pi * r ** 2, z) / 1000.0)


def self_check() -> list[str]:
    d = debiased_profile()
    out = []
    out.append(f"primary table          : {_PRIMARY.name}, {d.shape[0]} rows, "
               f"z {d[0,0]:.4f}..{d[-1,0]:.4f}")
    out.append(f"r at Z_OGIVE           : {float(r_outer(Z_OGIVE)):.5f} "
               f"(must equal R_AIRFRAME {R_AIRFRAME:.5f})")
    assert abs(float(r_outer(Z_OGIVE)) - R_AIRFRAME) < 1e-6
    mono = bool(np.all(np.diff(d[:, 1]) <= 1e-9))
    out.append(f"monotone non-increasing: {mono}   (no undercut, so a pin hinge "
               f"on the skin opens it with zero interference)")
    assert mono, "profile must not bulge"
    proud = bool(np.all(d[:, 1] <= R_AIRFRAME + 1e-9))
    out.append(f"never proud of airframe: {proud}")
    assert proud
    m, p, zp = bias_vs_raw()
    out.append(f"discredited array is   : mean {m:+.4f}, peak {p:+.4f} mm fat at z {zp:.0f}"
               + ("" if _BAD.exists() else "  (from _BIAS_MEASURED -- the array "
                                          "itself is not in this package)"))
    out.append(f"table loaded from      : {_PRIMARY}"
               + ("" if _PRIMARY == _PRIMARY_PATHS[0]
                  else "  (the in-package fallback copy)"))
    xm, xlo, xhi = xcheck_vs_primary()
    out.append(f"independent ray-cast   : mean {xm:+.4f}, range {xlo:+.4f}..{xhi:+.4f} mm "
               f"vs the primary table -- two methods agree")
    out.append(f"base half-angle        : {base_slope_deg():.4f} deg (measured 4.0639)")
    out.append(f"original wall (normal) : {(d[0,1] - inner_profile_measured()[0,1]) * 1.0:.4f} mm "
               f"radial at the root; the new shells use their own, thicker wall")
    return out


if __name__ == "__main__":
    for ln in self_check():
        print(ln)
    print()
    for zz in (0, 26.2069, 52.4138, 54, 56, 60, 80, 100, 150, 200, 240, 248.9655):
        print(f"  r_outer({zz:9.4f}) = {float(r_outer(zz)):8.4f}   slope "
              f"{slope_deg(zz):6.3f} deg")
    print()
    for zf in (52.4138, 54.0, 60.0):
        for w in (2.0, 2.5):
            print(f"  cavity above z={zf:8.4f}, {w} mm normal wall : "
                  f"{cavity_volume(zf, w):7.1f} cm3")
