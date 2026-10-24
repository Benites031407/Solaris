"""Checks on the mold STLs and on the pieces they make.

  0  mold_params.self_check()
  1  every STL body is watertight, sits on the bed, has the through-holes it should
     (Euler number), and the bodies on one plate don't overlap; the STLs match the CAD
     (volume and bounds);
     the plate of sleeve-mold parts holds the same four bodies as the one-part STLs
  2  each mold's cavity (in build123d, exact) is the silicone piece it's meant to make,
     plus only the printing allowance; the sleeve mold's parts and the rod don't clash
  3  sizes measured off the STL meshes by slicing: the numbers that matter for the fit
  4  overhangs on the STLs as printed: nothing steeper than 45 deg that isn't on the bed
Run from this folder:  python mold_verify.py
"""

import math

import numpy as np
import trimesh
from build123d import Axis, Location

import mold_params as P
import sleeve_mold as S
from base_mold import base_mold
from end_cap_mold import cap_mold
from mold_build import revolve_rz, tube
from silicone_pieces import base_piece, cap_piece, sleeve_piece

FAIL = []


def check(cond, text):
    print(("ok    " if cond else "FAIL  ") + text)
    if not cond:
        FAIL.append(text)


def vol(shape):
    return sum(s.volume for s in shape.solids()) if shape is not None else 0.0


# ---- 0: parameters -------------------------------------------------------------------------
check(P.self_check(), "mold_params.self_check()")

# ---- 1: meshes -----------------------------------------------------------------------------
# genus = through-holes: the outer cylinder has its bore; the guide its bore and two windows
PART_GENUS = {"sleeve_mold_foot": 0, "sleeve_mold_outer_cylinder": 1, "sleeve_mold_top_guide": 3,
              "sleeve_mold_inner_cylinder": 0}
EXPECT = {                              # file: (genus of each body, CAD it was made from)
    "base_mold.stl": ([0], [base_mold()]),
    "end_cap_mold.stl": ([0], [cap_mold()]),
    "sleeve_mold.stl": (list(PART_GENUS.values()), S.print_layout()),
}
for name, make, _, _ in S.PARTS:
    EXPECT[name + ".stl"] = ([PART_GENUS[name]], [make()])

meshes = {}
for name, (genus, cad) in EXPECT.items():
    m = trimesh.load(name, force="mesh")
    bodies = m.split(only_watertight=False)
    meshes[name] = m
    check(len(bodies) == len(genus), f"{name}: {len(bodies)} bodies (expect {len(genus)})")
    check(all(b.is_watertight and b.is_winding_consistent for b in bodies), f"{name}: all bodies watertight")
    zmin = [b.bounds[0][2] for b in bodies]
    check(all(abs(z) < 1e-4 for z in zmin), f"{name}: every body sits on z = 0 (min z {min(zmin):.4f}..{max(zmin):.4f})")
    got = sorted(1 - b.euler_number // 2 for b in bodies)
    check(got == sorted(genus), f"{name}: through-holes per body {got} (expect {sorted(genus)})")
    boxes = [b.bounds for b in bodies]
    clash = [(i, j) for i in range(len(boxes)) for j in range(i + 1, len(boxes))
             if all(boxes[i][0][k] < boxes[j][1][k] and boxes[j][0][k] < boxes[i][1][k] for k in (0, 1))]
    check(not clash, f"{name}: bodies' footprints don't overlap")
    # faceting costs ~0.04 %; a one-parameter edit left unregenerated moves it >= ~0.25 %
    v_cad = sum(c.volume for c in cad)
    check(abs(m.volume - v_cad) < 0.0015 * v_cad,
          f"{name}: mesh {m.volume / 1000:.3f} cm3 = CAD {v_cad / 1000:.3f} cm3 (not stale)")
    bbs = [c.bounding_box() for c in cad]
    bb_cad = np.array([[min(b.min.X for b in bbs), min(b.min.Y for b in bbs), min(b.min.Z for b in bbs)],
                       [max(b.max.X for b in bbs), max(b.max.Y for b in bbs), max(b.max.Z for b in bbs)]])
    d_bb = float(np.abs(m.bounds - bb_cad).max())
    check(d_bb < 0.06, f"{name}: mesh bounds = CAD bounds within {d_bb:.3f} mm (not stale)")
    ext = m.bounds[1] - m.bounds[0]
    print(f"      {name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, {m.volume / 1000:.1f} cm3 of plastic")

plate = meshes["sleeve_mold.stl"].split(only_watertight=False)
for name, _, _, _ in S.PARTS:
    one = meshes[name + ".stl"]
    ext = one.bounds[1] - one.bounds[0]
    same = [b for b in plate if abs(b.volume - one.volume) < 1e-3 * one.volume
            and np.allclose(b.bounds[1] - b.bounds[0], ext, atol=0.01)]
    check(len(same) == 1, f"sleeve_mold.stl holds {name} ({one.volume / 1000:.2f} cm3, "
          f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f})")


# ---- 2: cavity == piece (exact, build123d) ------------------------------------------------
def upside_down(piece, z_rim):
    """A piece as used -> where it sits in a mold that holds it upside down."""
    return piece.rotate(Axis.X, 180.0).moved(Location((0.0, 0.0, z_rim)))


# the base mold holds the base upside down; the cap mold holds the cap the way it's used.
# The cavities' outer walls are printed holes, so they're HOLE_COMP bigger than the piece.
for label, mold, placed, r_head, z_rim, r_cav, r_nom, h in (
    ("base", base_mold(), upside_down(base_piece(), P.ZB_RIM), P.R_BASE_HEAD, P.ZB_RIM,
     P.R_BASE_CAV, P.D_BASE / 2, P.H_BASE),
    ("cap", cap_mold(), cap_piece(P.ZC_FACE), P.R_CAP_HEAD, P.ZC_RIM, P.R_CAP_CAV, P.D_CAP / 2, P.CAP_T),
):
    cavity = tube(0.0, r_head - 0.01, 0.0, z_rim).cut(mold)
    over = vol(mold.intersect(placed))
    outside = vol(placed.cut(cavity))
    extra = vol(cavity.cut(placed))
    comp = math.pi * (r_cav ** 2 - r_nom ** 2) * h
    check(over < 1e-3 and outside < 1e-3 and abs(extra - comp) < 0.01 * comp,
          f"{label} mold: cavity {vol(cavity) / 1000:.3f} cm3 = piece {vol(placed) / 1000:.3f} cm3 + "
          f"{extra:.1f} mm3 of hole allowance (expect {comp:.1f}; overlap {over:.4f}, piece outside {outside:.4f})")

a = S.assembled()
names = list(a)
for i, m in enumerate(names):
    for n in names[i + 1:]:
        check(vol(a[m].intersect(a[n])) < 1e-3, f"sleeve mold: {m} and {n} don't clash")
rod = tube(0.0, P.D_ROD / 2.0, P.ZS_SEAT, P.ZS_SEAT + P.L_ROD_MIN)
for m in ("foot", "outer_cylinder", "top_guide"):
    check(vol(a[m].intersect(rod)) < 1e-3, f"sleeve mold: a plain Ø{P.D_ROD:.0f} rod, seated, clears the {m}")
check(vol(a["inner_cylinder"].cut(rod)) < 1e-3, "sleeve mold: the printed inner cylinder is inside the rod's envelope")

# the cavity, from the numbers alone: bore = sleeve OD + comp from the foot floor to the
# top face; the seat (with its lead-in) below; minus the rod
walls = a["foot"].fuse(a["outer_cylinder"])
cavity = tube(0.0, P.R_BORE + 0.5, P.ZS_SEAT, P.ZS_TOP).cut(walls).cut(rod)
sl = P.SEAT_LEADIN
intent = revolve_rz([(0.0, P.ZS_SEAT), (P.R_SEAT, P.ZS_SEAT), (P.R_SEAT, P.ZS_END - sl), (P.R_SEAT + sl, P.ZS_END),
                     (P.R_BORE, P.ZS_END), (P.R_BORE, P.ZS_TOP), (0.0, P.ZS_TOP)]).cut(rod)
mismatch = vol(cavity.cut(intent)) + vol(intent.cut(cavity))
check(mismatch < 0.5, f"sleeve mold: cavity {vol(cavity):.1f} mm3 = the intended one {vol(intent):.1f} "
      f"(mismatch {mismatch:.3f} mm3)")
sleeve_in_mold = sleeve_piece(P.ZS_END)
check(vol(sleeve_in_mold.cut(cavity)) < 1e-3, "sleeve mold: the whole sleeve fits in the cavity")
extra = vol(cavity.cut(sleeve_in_mold))
ring = math.pi * (P.R_BORE ** 2 - (P.D_CORE / 2) ** 2) * P.L_SLEEVE
print(f"      cavity - sleeve = {extra:.1f} mm3: bore allowance {ring:.1f}, seat skin {extra - ring:.1f}")
# displacement fill: poured into the empty mold it fills the seat first, then the bore
seat = tube(0.0, P.R_BORE + 0.5, P.ZS_SEAT, P.ZS_END).cut(walls)
h_fill = (vol(cavity) - vol(seat)) / (math.pi * P.R_BORE ** 2)
print(f"      silicone to fill it: {vol(cavity) / 1000:.2f} ml.  Poured before the rod goes in, it fills the "
      f"{vol(seat):.0f} mm3 seat and stands {h_fill:.2f} mm above the foot floor, {P.L_SLEEVE - h_fill:.2f} "
      f"below the top face; the rod then brings it up to the top face")

# ---- 3: slices of the STL meshes -----------------------------------------------------------


def loops(mesh, z):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    return [] if sec is None else list(sec.discrete)


def radii(mesh, z):
    """(r_min, r_max) about the Z axis of every closed loop in the section at height z."""
    out = []
    for lp in loops(mesh, z):
        d = np.hypot(lp[:, 0], lp[:, 1])
        out.append((round(float(d.min()), 3), round(float(d.max()), 3)))
    return sorted(out)


def has_circle(rr, want, tol=0.02):
    return any(abs(lo - want) < tol and abs(hi - want) < tol for lo, hi in rr)


SLICES = (  # (file, print z, [(radius, what)], [radius that must NOT be there])
    ("base_mold.stl", P.FLOOR + 3.0, [(P.R_BOSS, "socket boss (grips the tube)"), (P.R_BASE_CAV, "cup wall")], []),
    ("base_mold.stl", P.ZB_SHOULDER + 3.0, [(P.R_GRIP_PIN, "pocket pin"), (P.R_BASE_CAV, "cup wall")], []),
    ("base_mold.stl", P.ZB_POCKET + 1.5, [(P.R_BASE_CAV, "cup wall")], [P.R_GRIP_PIN]),   # pocket is blind
    ("end_cap_mold.stl", P.ZC_FACE + 3.0, [(P.R_GRIP_PIN, "hole pin"), (P.R_CAP_CAV, "cup wall")], []),
    ("end_cap_mold.stl", P.ZC_RIM + 0.5, [(P.R_GRIP_PIN, "hole pin, above the rim")], []),
    ("sleeve_mold_outer_cylinder.stl", P.L_SLEEVE / 2, [(P.R_BORE, "bore"), (P.R_SM, "OD")], []),
    ("sleeve_mold_outer_cylinder.stl", 0.3, [(P.R_BORE, "bore at the bed"), (P.R_SM - P.SM_END_CH + 0.3, "end chamfer")], []),
    ("sleeve_mold_foot.stl", P.ZS_SEAT + 1.0, [(P.R_SEAT, "seat"), (P.FOOT_D / 2, "flange")], []),
    ("sleeve_mold_foot.stl", P.FOOT_FLOOR - 0.3, [(P.R_SEAT + 0.3, "seat lead-in")], []),
    ("sleeve_mold_foot.stl", P.FOOT_FLOOR + 3.0, [(P.R_SKIRT_IN, "collar inside"), (P.R_SKIRT_OUT, "collar outside")], []),
    ("sleeve_mold_top_guide.stl", P.GUIDE_PLATE / 2, [(P.R_GUIDE, "bore"), (P.R_SKIRT_OUT, "plate edge")], []),
    ("sleeve_mold_top_guide.stl", P.GUIDE_PLATE + P.GUIDE_GAP / 2, [(P.R_CHAMBER, "chamber")], []),
    ("sleeve_mold_top_guide.stl", P.GUIDE_PLATE + P.GUIDE_GAP + P.SKIRT / 2, [(P.R_SKIRT_IN, "skirt inside")], []),
    ("sleeve_mold_inner_cylinder.stl", P.L_ROD_MIN / 2, [(P.D_ROD / 2, "pin")], []),
)
print("sections, (r_min, r_max) of each loop:")
for name, z, wants, nots in SLICES:
    rr = radii(meshes[name], z)
    for want, what in wants:
        check(has_circle(rr, want), f"{name}: {what} r {want:.3f} at print z {z:.1f}   {rr}")
    for r in nots:
        check(not has_circle(rr, r), f"{name}: nothing at r {r:.3f} at print z {z:.1f} (blind)")

# guide windows: two loops in the plate besides the bore and the edge, between hub and chamber
wins = [(lo, hi) for lo, hi in radii(meshes["sleeve_mold_top_guide.stl"], P.GUIDE_PLATE / 2)
        if not (abs(hi - lo) < 0.02)]
check(len(wins) == 2 and all(abs(lo - P.R_GUIDE_HUB) < 0.03 and abs(hi - P.R_CHAMBER) < 0.03 for lo, hi in wins),
      f"top guide: two windows r {P.R_GUIDE_HUB:.3f}..{P.R_CHAMBER:.3f} ({wins})")

# ---- 4: overhangs as printed --------------------------------------------------------------
# 46 deg: the 45 deg features (lead-ins, chamfers) round either way in facets
print("overhangs (downward faces steeper than 46 deg from vertical, off the bed):")
for name, m in meshes.items():
    for i, b in enumerate(m.split(only_watertight=False)):
        n = b.face_normals
        zc = b.triangles_center[:, 2]
        down = (n[:, 2] < -math.sin(math.radians(46.0))) & (zc > 0.05)   # n_z = -sin(angle off vertical)
        area = b.area_faces[down].sum()
        check(area < 1.0, f"{name}[{i}]: {area:.2f} mm2 needs support"
              + (f" at z {sorted(set(np.round(zc[down], 2)))[:6]}" if down.any() else ""))

print()
print("ALL CHECKS PASSED" if not FAIL else f"{len(FAIL)} FAILED: {FAIL}")
