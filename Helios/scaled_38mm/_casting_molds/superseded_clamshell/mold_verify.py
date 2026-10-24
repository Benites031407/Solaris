"""Checks on the mold STLs and on the pieces they make.

  0  mold_params.self_check()
  1  every STL body is watertight, sits on the bed, has the through-holes it should
     (Euler number), and the bodies on one plate don't overlap; the STLs match the CAD
  2  each mold's cavity (in build123d, exact) is the silicone piece it's meant to make;
     the sleeve mold closes, and a half turned end-for-end doesn't
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
# genus = through-holes: a half has the bolt holes; the guide has its bore and two windows
G_HALF, G_GUIDE = 2 * len(P.BOLT_Z), 3
EXPECT = {                              # file: (genus of each body, CAD it was made from)
    "base_mold.stl": ([0], [base_mold()]),
    "end_cap_mold.stl": ([0], [cap_mold()]),
    "sleeve_mold.stl": ([G_HALF, G_HALF, 0, G_GUIDE], S.print_layout()),
    "sleeve_mold_half.stl": ([G_HALF], [S.half_printed()]),
    "sleeve_mold_stand.stl": ([0], [S.stand_printed()]),
    "sleeve_mold_rod_guide.stl": ([G_GUIDE], [S.rod_guide_printed()]),
}
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
    v_cad = sum(c.volume for c in cad)
    check(abs(m.volume - v_cad) < 0.005 * v_cad,
          f"{name}: mesh {m.volume / 1000:.2f} cm3 = CAD {v_cad / 1000:.2f} cm3 (not stale)")
    ext = m.bounds[1] - m.bounds[0]
    print(f"      {name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, {m.volume / 1000:.1f} cm3 of plastic")


# ---- 2: cavity == piece (exact, build123d) ------------------------------------------------
def as_molded(piece, z_rim):
    """A piece as used -> where it sits in its upside-down mold."""
    return piece.rotate(Axis.X, 180.0).moved(Location((0.0, 0.0, z_rim)))


# the base mold holds the base upside down; the cap mold holds the cap the way it's used
for label, mold, placed, z_rim in (
    ("base", base_mold(), as_molded(base_piece(), P.ZB_RIM), P.ZB_RIM),
    ("cap", cap_mold(), cap_piece(P.ZC_FACE), P.ZC_RIM),
):
    envelope = tube(0.0, P.R_HEAD - 0.01, 0.0, z_rim)
    cavity = envelope.cut(mold)
    over = vol(mold.intersect(placed))
    diff = vol(cavity.cut(placed)) + vol(placed.cut(cavity))
    check(over < 1e-3 and diff < 1e-2 * vol(placed),
          f"{label} mold: cavity {vol(cavity) / 1000:.3f} cm3 = piece {vol(placed) / 1000:.3f} cm3 "
          f"(overlap {over:.3f}, mismatch {diff:.3f} mm3)")

c = S.closed()
halves = c["half_a"].fuse(c["half_b"])
rod = tube(0.0, P.D_ROD / 2.0, P.ZS_SEAT, P.ZS_SEAT + P.L_ROD_MIN)
sleeve_in_mold = as_molded(sleeve_piece(0.0), P.ZS_TOP)
check(vol(c["half_a"].intersect(c["half_b"])) < 1e-3, "sleeve mold: halves close without clashing (keys in sockets)")
flipped = as_molded(c["half_a"], P.ZS_TOP)             # half A turned end-for-end, in B's place
v_flip = vol(c["half_a"].intersect(flipped))
check(v_flip > 1.0, f"sleeve mold: a half turned end-for-end won't close ({v_flip:.1f} mm3 of cone on face)")
check(vol(halves.intersect(sleeve_in_mold)) < 1e-3, "sleeve mold: sleeve sits clear of both halves")
check(vol(halves.intersect(rod)) < 1e-3 and vol(c["rod_guide"].intersect(rod)) < 1e-3,
      "sleeve mold: rod clears the seat and the guide")
check(vol(c["stand"].intersect(halves)) < 1e-3 and vol(c["rod_guide"].intersect(halves)) < 1e-3,
      "sleeve mold: stand and guide slip over the closed halves")

# the cavity, from the numbers alone: sleeve OD + comp, the tip bevel's cone carried down to
# the rod seat, the seat; minus the rod
envelope = tube(0.0, P.R_SLEEVE_CAV + 0.5, P.ZS_SEAT, P.ZS_TOP)
cavity = envelope.cut(halves).cut(rod)
r_od = P.D_CORE / 2 + P.GROOVE_COMP / 2
r_seat = P.D_ROD / 2 + (P.GROOVE_COMP + P.FIT_ROD_SEAT) / 2
z_bevel = P.ZS_END + (P.D_CORE - P.D_ROD) / 2            # bevel meets the OD
intent = revolve_rz([(0.0, P.ZS_SEAT), (r_seat, P.ZS_SEAT), (r_seat, z_bevel - (r_od - r_seat)),
                     (r_od, z_bevel), (r_od, P.ZS_TOP), (0.0, P.ZS_TOP)]).cut(rod)
mismatch = vol(cavity.cut(intent)) + vol(intent.cut(cavity))
check(mismatch < 0.5, f"sleeve mold: cavity {vol(cavity):.1f} mm3 = the intended one {vol(intent):.1f} "
      f"(mismatch {mismatch:.3f} mm3)")
check(vol(sleeve_in_mold.cut(cavity)) < 1e-3, "sleeve mold: the whole sleeve fits in the cavity")
extra = vol(cavity.cut(sleeve_in_mold))
skin = math.pi * (r_seat ** 2 - (P.D_ROD / 2) ** 2) * (P.ZS_END - P.ZS_SEAT)
ring = math.pi * (r_od ** 2 - (P.D_CORE / 2) ** 2) * (P.ZS_TOP - z_bevel)
print(f"      cavity - sleeve = {extra:.1f} mm3: groove comp ring {ring:.1f}, seat skin {skin:.1f}, "
      f"bevel comp {extra - ring - skin:.1f}")

# ---- 3: slices of the STL meshes -----------------------------------------------------------


def loops(mesh, origin, normal):
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    return [] if sec is None else list(sec.discrete)


def ring_radii(mesh, z, center=(0.0, 0.0)):
    """(r_min, r_max) of every closed loop in the section at height z, about `center`."""
    out = []
    for lp in loops(mesh, [0, 0, z], [0, 0, 1]):
        d = np.hypot(lp[:, 0] - center[0], lp[:, 1] - center[1])
        out.append((round(d.min(), 3), round(d.max(), 3)))
    return sorted(out)


bm = meshes["base_mold.stl"]
cm = meshes["end_cap_mold.stl"]
print("base mold sections (r_min, r_max):")
for z in (P.ZB_MOUTH + 5, P.ZB_FACE + 3, P.ZB_RIM - 0.2, P.ZB_RIM + 0.5):
    print(f"      z {z:5.1f}: {ring_radii(bm, z)}")
r = ring_radii(bm, P.ZB_FACE + 3)
check(any(abs(a - P.R_GRIP_PIN) < 0.02 for a, b in r) and any(abs(b - P.R_CUP) < 0.02 for a, b in r),
      f"base mold: grip pin r {P.R_GRIP_PIN} and cup wall r {P.R_CUP} measured off the STL")
r = ring_radii(bm, P.ZB_MOUTH + 5)
check(any(abs(b - P.R_BOSS) < 0.02 for a, b in r), f"base mold: tube boss r {P.R_BOSS} (tube OD {P.D_TUBE})")

vents = []
for lp in loops(cm, [0, 0, P.ZC_FACE + 3], [0, 0, 1]):
    ctr = lp[:, :2].mean(axis=0)
    rr = np.hypot(*(lp[:, :2] - ctr).T)
    if abs(np.hypot(*ctr) - P.R_VENT) < 0.1 and abs(rr.mean() - P.R_VENT_PIN) < 0.03:
        vents.append(round(float(np.degrees(np.arctan2(ctr[1], ctr[0]))) % 360, 1))
check(len(vents) == P.N_VENT, f"cap mold: {len(vents)} vent pins d {P.D_VENT} at r {P.R_VENT} "
      f"(expect {P.N_VENT}), at {sorted(vents)} deg")
r = ring_radii(cm, P.ZC_FACE + 3)
check(any(abs(a - P.R_GRIP_PIN) < 0.02 for a, b in r), f"cap mold: grip pin r {P.R_GRIP_PIN}")

# sleeve mold halves, as printed: closed (x, y, z) -> print (x, ZS_TOP/2 - z, y + SM_T)
seat_mid = 0.5 * (P.ZS_FUNNEL + P.ZS_END + P.SLEEVE_TIP_CHAMFER)
STATIONS = ((P.ZS_END + 40.0, P.R_SLEEVE_CAV, "sleeve cavity"),
            (P.ZS_SEAT + 3.0, P.R_SEAT, "rod seat"),
            (seat_mid, P.R_SLEEVE_CAV - (P.ZS_END + P.SLEEVE_TIP_CHAMFER - seat_mid), "funnel"))
for name, xs in (("sleeve_mold.stl", (-(P.SM_W / 2 + 5.0), P.SM_W / 2 + 5.0)), ("sleeve_mold_half.stl", (0.0,))):
    for zc, want, what in STATIONS:
        for x0 in xs:
            pts = np.vstack(loops(meshes[name], [0, P.ZS_TOP / 2 - zc, 0], [0, 1, 0]))
            pts = pts[np.abs(pts[:, 2] - P.SM_T) > 0.05]             # drop the parting face (y = 0 closed)
            d = np.hypot(pts[:, 0] - x0, pts[:, 2] - P.SM_T)
            near = d[d < want + 1.0]
            check(len(near) > 0 and abs(near.max() - want) < 0.03 and abs(near.min() - want) < 0.03,
                  f"{name}: {what} r {near.min():.3f}..{near.max():.3f} at closed z {zc:.1f}, half at x {x0:+.0f} "
                  f"(design {want:.3f})")

gm = meshes["sleeve_mold_rod_guide.stl"]
for zp, want, what in ((P.GUIDE_PLATE / 2, P.R_GUIDE, "bore"),
                       (0.05, P.R_GUIDE + P.BORE_CHAMFER - 0.05, "bore mouth on the bed")):
    r = [a for a, b in ring_radii(gm, zp) if b < 10.0]
    check(len(r) == 1 and abs(r[0] - want) < 0.03, f"rod guide: {what} r {r} at print z {zp} (design {want:.3f})")

sm = meshes["sleeve_mold_stand.stl"]
for zp, grow, what in ((P.STAND_PLATE + P.BOX_SKIRT / 2, 0.0, "pocket"),
                       (P.STAND_PLATE + P.BOX_SKIRT - 0.2, P.MOUTH_LEADIN - 0.2, "pocket mouth")):
    inner = min(loops(sm, [0, 0, zp], [0, 0, 1]), key=lambda lp: np.ptp(lp[:, 0]))
    hx, hy = np.ptp(inner[:, 0]) / 2, np.ptp(inner[:, 1]) / 2
    check(abs(hx - P.BOX_X / 2 - grow) < 0.02 and abs(hy - P.BOX_Y / 2 - grow) < 0.02,
          f"stand: {what} {2 * hx:.2f} x {2 * hy:.2f} (design {P.BOX_X + 2 * grow:.2f} x {P.BOX_Y + 2 * grow:.2f}, "
          f"over a {P.SM_W:.0f} x {2 * P.SM_T:.0f} block)")

# ---- 4: overhangs as printed --------------------------------------------------------------
# 46 deg: the 45 deg features (pin flare, bed chamfers, bore chamfer) round either way in facets
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
