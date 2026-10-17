"""Validate the saved STEP outputs: kernel soundness, key dimensions, and assembly fits.

Run from the project root after building the models:
    python checks/check_parts.py
Exits 1 if any check fails. All lengths in mm.
"""

from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd  # noqa: E402
from cadgen import read_scene, read_step  # noqa: E402
from cadgen.geometry import boundary_edges, closest_points, is_sound, overlap_volume, topology_errors  # noqa: E402

from lib import params as p  # noqa: E402

PARTS = ["nose_cone", "coupler", "fin_can", "fin", "retainer_male", "retainer_female", "fit_gauge"]
BUILD_HEIGHT = 250.0  # Creality K1C printable height (the K1 Max has 300 mm)
TOL = 0.02
failures: list[str] = []


def check(name: str, value: float, expected: float, tol: float = TOL) -> None:
    ok = abs(value - expected) <= tol
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: {value:.3f} (expected {expected:.3f} +/- {tol})")
    if not ok:
        failures.append(name)


def check_range(name: str, value: float, lo: float, hi: float) -> None:
    ok = lo <= value <= hi
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: {value:.3f} (allowed {lo:.3f} .. {hi:.3f})")
    if not ok:
        failures.append(name)


def _ray_hits(shape: bd.Shape, z: float, angle_deg: float) -> list[float]:
    """Radii where a radial ray from the axis at height z crosses the material boundary."""
    a = math.radians(angle_deg)
    ray = bd.Edge.make_line((0, 0, z), (80 * math.cos(a), 80 * math.sin(a), z))
    return sorted(math.hypot(*tuple(v)[:2]) for v in (shape & ray).vertices())


def outer_radius(shape: bd.Shape, z: float, angle_deg: float) -> float:
    """Farthest material from the axis along one radial direction at height z."""
    hits = _ray_hits(shape, z, angle_deg)
    return hits[-1] if hits else float("nan")


def bore_profile_radius(shape: bd.Shape, z: float, angle_deg: float = 270.0) -> float:
    """Radius where a radial ray at height z first enters material."""
    hits = _ray_hits(shape, z, angle_deg)
    return hits[0] if hits else float("nan")


print("== Part soundness and envelope")
shapes = {}
for name in PARTS:
    shape = read_step(ROOT / "STEP" / f"{name}.step")
    shapes[name] = shape
    solids = shape.solids()
    bb = shape.bounding_box()
    errs = topology_errors(shape)
    open_edges = [e for s in solids for sh in s.shells() for e in boundary_edges(sh)]
    vol = sum(s.volume for s in solids)
    print(f"{name}: solids={len(solids)} valid={shape.is_valid} sound={is_sound(shape)} "
          f"topology_errors={len(errs)} open_edges={len(open_edges)} volume={vol / 1000:.1f} cm3 "
          f"bbox=({bb.size.X:.2f}, {bb.size.Y:.2f}, {bb.size.Z:.2f}) zmin={bb.min.Z:.3f}")
    if len(solids) != 1 or not shape.is_valid or errs or open_edges or min(s.volume for s in solids) <= 0:
        failures.append(f"{name} soundness")
    if abs(bb.min.Z) > 1e-6:
        failures.append(f"{name} not on bed (zmin={bb.min.Z})")
    if bb.size.Z > BUILD_HEIGHT:
        failures.append(f"{name} taller than {BUILD_HEIGHT}")

R = p.BODY_OD / 2
r_stub = (p.BODY_ID - p.GLUE_FIT) / 2
r_bore = (p.MOTOR_TUBE_OD + p.MOTOR_TUBE_FIT) / 2

print("== Nose cone")
nose = shapes["nose_cone"]
bb = nose.bounding_box()
check_range("total height (fits the K1C 250 mm Z with margin)", bb.size.Z, 240.0, BUILD_HEIGHT - 2.0)
check("base radius", outer_radius(nose, p.NOSE_SHOULDER_LEN + 0.5, 0), R, 0.05)
check("shoulder radius (slip fit)", outer_radius(nose, 20, 0), (p.BODY_ID - p.SLIP_FIT) / 2)
check("shoulder wall inner radius", bore_profile_radius(nose, 20, 90), (p.BODY_ID - p.SLIP_FIT) / 2 - p.NOSE_WALL)
check("ogive wall inner radius at mid-length", bore_profile_radius(nose, 140, 90),
      outer_radius(nose, 140, 90) - p.NOSE_WALL, 0.15)

print("== Coupler")
cp = shapes["coupler"]
check("band radius (away from guides)", outer_radius(cp, p.COUPLER_STUB_LEN + 13, 0), R)
check("lower stub radius", outer_radius(cp, 15, 0), r_stub)
check("upper stub radius", outer_radius(cp, p.COUPLER_STUB_LEN * 2 + p.COUPLER_BAND_LEN - 15, 0), r_stub)
check("bore radius", bore_profile_radius(cp, 20, 0), r_stub - p.STUB_WALL)
bb = cp.bounding_box()
check("length", bb.size.Z, 2 * p.COUPLER_STUB_LEN + p.COUPLER_BAND_LEN)

print("== Fin can")
fc = shapes["fin_can"]
check("body radius (270 deg, clear of slots/guides)", outer_radius(fc, 60, 270), R)
check("stub radius", outer_radius(fc, p.FIN_CAN_LEN + 13, 270), r_stub)
check("motor bore radius", bore_profile_radius(fc, 50), r_bore)
z_stop = p.MOTOR_LEN - (p.MALE_BAND_LEN + p.MALE_THREAD_LEN)
check("bore just below engine stop", bore_profile_radius(fc, z_stop - 0.3), r_bore)
check_range("stop radius just above engine stop (< motor radius)", bore_profile_radius(fc, z_stop + 0.3),
            0.0, p.MOTOR_DIA / 2 - 0.5)
check("ejection passage radius", bore_profile_radius(fc, z_stop + 3.5), p.ENGINE_BLOCK_BORE / 2)
# Slot geometry at mid-height along the first fin's radial plane (y = 0 is the slot centre).
hits = _ray_hits(fc, 60, p.FIN_ANGLE0)
print(f"  slot ray hits along the first fin plane at z=60: {[round(h, 3) for h in hits]}")
ch_in = p.FIN_FLANGE_INNER_R - p.SLOT_CLEARANCE
check_range("slot channel starts at", hits[1] if len(hits) > 1 else float("nan"), ch_in - 0.01, ch_in + 0.01)

print("== Fin")
fn = shapes["fin"]
bb = fn.bounding_box()
check("root length", bb.size.Z, p.FIN_ROOT_LEN)
check("span incl. rail", bb.max.X - bb.min.X, p.FIN_LE_TIP[0] + (R - p.FIN_FLANGE_INNER_R))
check("rail flange width", bb.size.Y, p.FIN_FLANGE_WIDTH)

print("== Retainers")
male = shapes["retainer_male"]
check("male band radius", outer_radius(male, 3, 0), p.MALE_BAND_OD / 2)
check_range("male thread crest radius", max(outer_radius(male, z, a) for z in (9, 12, 15) for a in range(0, 360, 15)),
            p.MALE_THREAD_MAJOR / 2 - 0.05, p.MALE_THREAD_MAJOR / 2 + 0.01)
check("male bore radius", bore_profile_radius(male, 10), r_bore)
fem = shapes["retainer_female"]
check("cap outer radius", outer_radius(fem, 8, 360 / p.CAP_FLUTES / 2), p.CAP_OD / 2, 0.05)
check("cap nozzle hole radius", bore_profile_radius(fem, 1.2), p.CAP_HOLE / 2)

print("== Assembly fits and interference")
scene = read_scene(str(ROOT / "STEP" / "scorpio_assembly.step"))
leaves = {occ.label: scene.resolve(occ.ref).shape().solids()[0] for occ in scene.leaves()}
print("  leaves:", sorted(leaves))
boxes = {label: solid.bounding_box(optimal=False) for label, solid in leaves.items()}


def _boxes_touch(la: str, lb: str) -> bool:
    a, b = boxes[la], boxes[lb]
    return all(tuple(a.min)[i] <= tuple(b.max)[i] and tuple(b.min)[i] <= tuple(a.max)[i] for i in range(3))


tested = 0
for (la, a), (lb, b) in combinations(sorted(leaves.items()), 2):
    if not _boxes_touch(la, lb):
        continue
    v = overlap_volume(a, b)
    tested += 1
    if v > 0.01:
        print(f"  [FAIL] overlap {la} / {lb}: {v:.3f} mm3")
        failures.append(f"overlap {la}/{lb}")
print(f"  pairwise overlap checked on {tested} pairs (limit 0.01 mm3)")


def gap(la: str, lb: str, lo: float, hi: float, what: str) -> None:
    d = closest_points(leaves[la], leaves[lb]).distance
    check_range(f"{what} ({la} / {lb})", d, lo, hi)


gap("fin:1", "fin_can", 0.15, 0.25, "fin rail to slot clearance")
# Flank clearance is measured mid-engagement only: at the open end the cap
# deliberately seats against the male band chamfer.
engage = bd.Pos(0, 0, -17.0) * bd.Box(60, 60, 8.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
d = closest_points(leaves["retainer_male"] & engage, leaves["retainer_female"] & engage).distance
check_range("thread flank clearance, mid-engagement (retainer_male / retainer_female)", d, 0.20, 0.30)
gap("retainer_male", "retainer_female", 0.03, 0.30, "cap seat to male band (cap screwed home)")
gap("retainer_male", "fin_can", 0.0, 1e-3, "male band seated on fin can")
gap("motor_tube_not_printed", "fin_can", 0.0, 1e-3, "motor tube seated on engine stop")
gap("coupler", "lower_tube_not_printed", 0.0, 1e-3, "coupler band on lower tube")
gap("nose_cone", "upper_tube_not_printed", 0.0, 1e-3, "nose base on upper tube")
total = bd.Compound(children=list(leaves.values())).bounding_box()
check_range("assembled length (Estes: 1054 mm / 41.5 in)", total.size.Z, 1030.0, 1080.0)

print()
if failures:
    print("FAILED:", failures)
    raise SystemExit(1)
print("ALL CHECKS PASSED")
