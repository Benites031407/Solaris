"""The airframe stack, recovered and then CHECKED against the assembled mesh.

`rocket_assembly.py` is gone -- only `__pycache__/rocket_assembly.cpython-311.pyc`
survives.  Its constants and its `build` order are still readable in the bytecode,
so the stack here is not invented:

    datum      z = 0 is the TAIL AFT FACE, +z forward
    order      Tail, Lower_Body, conection, Mbody, cone
    joints     4, each losing SPIGOT = 26.207 mm of the naive sum
    rot180x    "180 deg about X (z -> -z, y -> -y) then translate +dz:
                z_asm = dz - z_stl."  -- so a part occupies [dz - L, dz].

Recovering an order and a spigot length is not the same as knowing it is right,
and a video built on a wrong stack would look every bit as convincing as the
latch that was wrong for a long time while every picture of it looked fine.
So `verify()` re-derives nothing from this file: it measures the OUTER RADIUS
PROFILE of the placed parts and of `rocket_assembled_boattail.stl` at the same
stations and reports the disagreement.

Radius is measured from real cross sections, never from max vertex radius --
max-vertex-radius over-reads a taper (it picks the corner of a facet that spans
the station) and would invent a flare that is not in the geometry.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]          # .../scaled_38mm

SPIGOT = 26.207
BODY_LEN = 262.069
SLEEVE_LEN = 52.414
CONE_LEN = 248.966

# aft -> forward, with the STL that supplies each section.
ORDER = [
    ("Tail",       "Tail_hollow.stl"),
    ("Lower_Body", "Lower_Body.stl"),
    ("conection",  "conection.stl"),
    ("Mbody",      "Mbody.stl"),
    ("cone",       "cone.stl"),
]

ASSEMBLED = "rocket_assembled_boattail.stl"


def load(name: str) -> trimesh.Trimesh:
    m = trimesh.load(ROOT / name, force="mesh")
    m.apply_translation((0, 0, -m.bounds[0, 2]))     # local z starts at 0
    return m


def rot180x(dz: float) -> np.ndarray:
    """z_asm = dz - z_stl, y_asm = -y_stl.  The bytecode's own docstring."""
    T = trimesh.transformations.rotation_matrix(math.pi, (1, 0, 0))
    T[2, 3] = dz
    return T


def shift(dz: float) -> np.ndarray:
    T = np.eye(4)
    T[2, 3] = dz
    return T


def stations() -> list[tuple[str, str, float, float, float]]:
    """(name, stl, length, z_aft, z_fwd) for each section, aft face at z=0."""
    out = []
    z = 0.0
    for name, stl in ORDER:
        L = load(stl).bounds[1, 2]
        out.append((name, stl, L, z, z + L))
        z += L - SPIGOT                              # next part overlaps by a spigot
    return out


# Which sections are flipped is NOT global: cone.stl already carries its apex at
# high local z (the nose README fixes "apex at z = 248.9655"), while the bytecode
# labels Mbody "(flipped)".  So the orientation of every section is SOLVED against
# the assembled mesh by `solve_flips()` and cached here, never assumed.
FLIP = {"Tail": False, "Lower_Body": False, "conection": False,
        "Mbody": True, "cone": False}


def placed(flip: dict[str, bool] | None = None
           ) -> list[tuple[str, trimesh.Trimesh, np.ndarray]]:
    """Each section, its mesh, and the 4x4 that puts it in the assembly."""
    flip = FLIP if flip is None else flip
    out = []
    for name, stl, L, z_aft, z_fwd in stations():
        m = load(stl)
        T = rot180x(z_fwd) if flip[name] else shift(z_aft)
        out.append((name, m, T))
    return out


def _union_profile(flips: dict[str, bool], zs: np.ndarray) -> np.ndarray:
    """Outer radius of the whole placed stack at each station in `zs`."""
    parts = []
    for name, m, T in placed(flips):
        mm = m.copy()
        mm.apply_transform(T)
        parts.append(mm)
    built = trimesh.util.concatenate(parts)
    return np.array([section_radius(built, z) or np.nan for z in zs])


def solve_flips(verbose: bool = True) -> dict[str, bool]:
    """Pick each section's orientation by matching the assembled radius profile.

    Two passes, because one is not enough:

      1. Over each part's EXCLUSIVE span.  This settles the tapered sections
         (Tail, cone) outright.
      2. For any section a plain tube leaves INDETERMINATE -- both orientations
         score the same because the exclusive span is a constant-radius tube --
         search the remaining combinations against the UNION profile.  A tube's
         orientation only shows up at its joints, which is exactly the region
         pass 1 has to exclude (inside a joint the outer radius is the max of two
         parts, so it cannot attribute a radius to either one alone).
    """
    asm = trimesh.load(ROOT / ASSEMBLED, force="mesh")
    st = stations()
    settled, unknown = {}, []
    for i, (name, stl, L, z_aft, z_fwd) in enumerate(st):
        lo = z_aft + (SPIGOT + 1.0 if i > 0 else 2.0)
        hi = z_fwd - (SPIGOT + 1.0 if i < len(st) - 1 else 2.0)
        zs = np.linspace(lo, hi, 28)
        m = load(stl)
        scores = {}
        for fl in (False, True):
            mm = m.copy()
            mm.apply_transform(rot180x(z_fwd) if fl else shift(z_aft))
            ds = [abs(rb - ra) for z in zs
                  if (rb := section_radius(mm, z)) is not None
                  and (ra := section_radius(asm, z)) is not None]
            scores[fl] = float(np.mean(ds)) if ds else float("inf")
        gap = abs(scores[True] - scores[False])
        if gap < 1e-3:
            unknown.append(name)
            settled[name] = False
            if verbose:
                print(f"  {name:<12} both orientations score "
                      f"{scores[False]:.4f} -- INDETERMINATE on its own span")
        else:
            settled[name] = scores[True] < scores[False]
            if verbose:
                print(f"  {name:<12} flip=False err {scores[False]:8.4f}   "
                      f"flip=True err {scores[True]:8.4f}   -> "
                      f"{'FLIPPED' if settled[name] else 'as-is'}")

    if not unknown:
        return settled

    if verbose:
        print(f"  resolving {unknown} against the union profile "
              f"({2 ** len(unknown)} combinations):")
    total = st[-1][4]
    zs = np.arange(6.0, total - 6.0, 6.0)
    ra = np.array([section_radius(asm, z) or np.nan for z in zs])
    best, best_err = None, float("inf")
    for bits in range(2 ** len(unknown)):
        cand = dict(settled)
        for k, name in enumerate(unknown):
            cand[name] = bool(bits >> k & 1)
        rb = _union_profile(cand, zs)
        good = ~np.isnan(rb) & ~np.isnan(ra)
        err = float(np.abs(rb[good] - ra[good]).max())
        if verbose:
            flagged = ",".join(n for n in unknown if cand[n]) or "none"
            print(f"    flipped={flagged:<30} max |d| = {err:8.4f} mm")
        if err < best_err:
            best, best_err = cand, err
    if verbose:
        print(f"  best: {[n for n in unknown if best[n]] or 'none flipped'} "
              f"at max |d| = {best_err:.4f} mm")
    return best


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------

def section_radius(mesh: trimesh.Trimesh, z: float, r_max: float = 33.5) -> float | None:
    """Outer radius at station z, from a real cross section.

    Fins are excluded by the r_max window, the same way the recovered
    `outer_steps` did it.  Returns None when the plane misses the mesh.
    """
    try:
        sec = mesh.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
    except Exception:
        return None
    if sec is None or len(sec.vertices) == 0:
        return None
    r = np.hypot(sec.vertices[:, 0], sec.vertices[:, 1])
    r = r[r < r_max]
    return float(r.max()) if len(r) else None


def verify() -> bool:
    asm = trimesh.load(ROOT / ASSEMBLED, force="mesh")
    st = stations()
    total = st[-1][4]
    naive = sum(s[2] for s in st)

    print(f"{'part':<12}{'length':>10}{'z aft':>10}{'z fwd':>10}")
    for name, stl, L, a, f in st:
        print(f"{name:<12}{L:>10.3f}{a:>10.3f}{f:>10.3f}")
    print(f"\nnaive sum of parts      {naive:>10.3f}")
    print(f"joint loss (4 x {SPIGOT})  {4 * SPIGOT:>10.3f}")
    print(f"assembled length        {total:>10.3f}")
    print(f"{ASSEMBLED} spans  {asm.bounds[0,2]:.3f} .. {asm.bounds[1,2]:.3f}"
          f"  (length {asm.bounds[1,2]-asm.bounds[0,2]:.3f})")

    # The assembled file carries an aft cap and motor below z=0, so compare the
    # airframe only: its forward tip must be the cone's tip.
    tip_err = abs(asm.bounds[1, 2] - total)
    print(f"\nforward tip disagreement  {tip_err:.4f} mm")

    print("\nsolving each section's orientation against the assembled mesh:")
    flips = solve_flips()
    if flips != FLIP:
        print(f"  NOTE: solved {flips} differs from cached FLIP {FLIP}")

    # Radius profile: union the placed sections, then compare to the assembled
    # mesh station by station.
    parts = []
    for name, m, T in placed(flips):
        mm = m.copy()
        mm.apply_transform(T)
        parts.append(mm)
    built = trimesh.util.concatenate(parts)

    zs = np.arange(4.0, total - 4.0, 4.0)
    rows, bad = [], 0
    for z in zs:
        rb = section_radius(built, z)
        ra = section_radius(asm, z)
        if rb is None or ra is None:
            continue
        d = abs(rb - ra)
        rows.append((z, rb, ra, d))
        if d > 0.05:
            bad += 1
    ds = np.array([r[3] for r in rows])
    print(f"radius profile: {len(rows)} stations, "
          f"max |d| = {ds.max():.4f} mm, mean {ds.mean():.4f} mm, "
          f"{bad} station(s) over 0.05 mm")
    if bad:
        print("  worst stations:")
        for z, rb, ra, d in sorted(rows, key=lambda r: -r[3])[:8]:
            print(f"    z={z:8.2f}  built r={rb:7.3f}  assembled r={ra:7.3f}  d={d:.4f}")

    ok = tip_err < 0.01 and ds.max() < 0.05
    print("\nPLACEMENT", "VERIFIED" if ok else "DOES NOT MATCH")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
