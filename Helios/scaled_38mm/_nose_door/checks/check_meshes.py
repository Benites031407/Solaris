"""Mesh checks for the Helios side-door nose, on the exported STL / 3MF files:

1. every mesh is watertight with consistent winding (no open or non-manifold edges);
2. the housing fits the real airframe: ../Mbody.stl is placed in the nose frame
   (station s -> nose z = 26.2069 - s, its cord anchor turned under the cord hole)
   and the shoulder, rim, bead and anchor are measured against it;
3. the outer shape matches ../cone.stl.

Needs trimesh (not in the cadgen environment), e.g.:
    uv run --no-project --with trimesh --with scipy --with shapely --with networkx --with rtree python checks/check_meshes.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lib import params as p  # noqa: E402  (plain constants, no CAD kernel)

AIRFRAME = ROOT.parent
failures: list[str] = []


def check_range(name: str, value: float, lo: float, hi: float) -> None:
    ok = lo <= value <= hi
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: {value:.3f} (allowed {lo:.3f} .. {hi:.3f})")
    if not ok:
        failures.append(name)


def edge_stats(m: trimesh.Trimesh) -> tuple[int, int]:
    _, counts = np.unique(m.edges_sorted, axis=0, return_counts=True)
    return int((counts == 1).sum()), int((counts > 2).sum())


print("== Exported meshes")
for name in ("helios_nose_door_housing", "helios_nose_door", "helios_nose_servo_keeper"):
    for path in (ROOT / "STL" / f"{name}.stl", ROOT / "3MF" / f"{name}.3mf"):
        loaded = trimesh.load(path)
        meshes = list(loaded.geometry.values()) if hasattr(loaded, "geometry") else [loaded]
        for m in meshes:
            m.merge_vertices()
            open_e, nonman = edge_stats(m)
            print(f"  {path.name}: bodies={len(meshes)} tris={len(m.faces)} open={open_e} non-manifold={nonman} "
                  f"watertight={m.is_watertight} winding={m.is_winding_consistent} volume={m.volume / 1000:.2f} cm3")
            if len(meshes) != 1 or open_e or nonman or not m.is_watertight or not m.is_winding_consistent:
                failures.append(f"{path.name} mesh")


def radii(m: trimesh.Trimesh, z: float) -> list[tuple[float, float, float]]:
    """(mean, min, max) radius of every section loop at height z, sorted by mean."""
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return []
    out = []
    for e in s.discrete:
        r = np.hypot(e[:, 0], e[:, 1])
        out.append((float(r.mean()), float(r.min()), float(r.max())))
    return sorted(out)


housing = trimesh.load_mesh(ROOT / "STL" / "helios_nose_door_housing.stl")

print("== Fit in the real airframe (../Mbody.stl)")
mbody = trimesh.load_mesh(AIRFRAME / "Mbody.stl")
# Mbody runs s = 0 (forward rim) aft along +z. Turn it end for end about X (keeps
# azimuth 0 = its cord anchor on +X), lift the rim to the shoulder face, then turn
# the anchor under the nose's cord hole.
flip = trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])
lift = trimesh.transformations.translation_matrix([0, 0, p.SHOULDER_LEN])
turn = trimesh.transformations.rotation_matrix(math.radians(p.NOSE_DOOR_CORD_AZ), [0, 0, 1])
mbody.apply_transform(turn @ lift @ flip)

worst = 1e9
for z in np.arange(1.0, p.SHOULDER_LEN - 0.5, 1.0):
    bore = min(lo for _, lo, _ in radii(mbody, z))
    sh = max(hi for _, _, hi in radii(housing, z))
    worst = min(worst, bore - sh)
check_range("shoulder in Mbody's socket: least radial gap over z 1..25.7 (mm)", worst, 0.05, 0.25)
rim = mbody.bounds[1][2]
check_range("Mbody's rim height = shoulder face (mm from nose z 0)", rim - p.SHOULDER_LEN, -0.01, 0.01)
skirt = max(hi for *_, hi in radii(housing, p.SHOULDER_LEN + 1.5))  # above the 45 deg step
tube = max(hi for *_, hi in radii(mbody, p.SHOULDER_LEN - 0.5))
check_range("nose skirt flush with the airframe OD at the joint (mm, + = nose proud)", skirt - tube, -0.06, 0.06)
# The bead (depth stop in Mbody's bore) starts just below the shoulder's base.
bead_top = max(z for z in np.arange(-6.0, 0.0, 0.05) if min(lo for _, lo, _ in radii(mbody, z)) < 31.0)
check_range("shoulder base above Mbody's bead (mm)", 0.0 - bead_top, 0.3, 3.0)
# Cord anchor tunnel: the closed loop in Mbody's section at s 58.
z_anchor = p.SHOULDER_LEN - 58.0
sec = mbody.section(plane_origin=[0, 0, z_anchor], plane_normal=[0, 0, 1])
loops = [e for e in sec.discrete if np.hypot(e[:, 0], e[:, 1]).max() < 31.2]
assert len(loops) == 1, "expected one tunnel loop"
cx, cy = loops[0][:, 0].mean(), loops[0][:, 1].mean()
az = math.degrees(math.atan2(cy, cx)) % 360
print(f"  anchor tunnel centre at nose z {z_anchor:.1f}: r {math.hypot(cx, cy):.2f}, azimuth {az:.1f} deg")
check_range("anchor tunnel azimuth = cord hole azimuth (deg)", az, p.NOSE_DOOR_CORD_AZ - 1.0, p.NOSE_DOOR_CORD_AZ + 1.0)

print("== Outer shape vs ../cone.stl")
cone = trimesh.load_mesh(AIRFRAME / "cone.stl")
dev = []
for z in np.arange(p.SHOULDER_LEN + 1.0, 236.0, 2.0):  # the first sample is just above the step
    dev.append((max(hi for *_, hi in radii(housing, z)) - max(hi for *_, hi in radii(cone, z)), z))  # outer surface
lo, hi = min(dev), max(dev)
print(f"  radius difference over z {p.SHOULDER_LEN + 1:.0f}..235: {lo[0]:+.3f} at z {lo[1]:.0f} .. {hi[0]:+.3f} at z {hi[1]:.0f}")
check_range("worst outer-radius difference from cone.stl below the tip (mm)", max(abs(lo[0]), abs(hi[0])), 0.0, 0.2)
print(f"  height: this nose {housing.bounds[1][2]:.2f}, cone.stl {cone.bounds[1][2]:.2f} (blunted tip)")
print(f"  volume: housing + door {housing.volume / 1000:.1f} + "
      f"{trimesh.load_mesh(ROOT / 'STL' / 'helios_nose_door.stl').volume / 1000:.1f} cm3, cone.stl {cone.volume / 1000:.1f} cm3")

print()
if failures:
    print("FAILED:", failures)
    raise SystemExit(1)
print("ALL MESH CHECKS PASSED")
