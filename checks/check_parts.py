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
from lib.rocket_parts import LOCK_ANGLE, fin_housing_radii  # noqa: E402

PARTS = ["nose_cone_hook", "nose_cone_open", "coupler", "fin_can", "fin", "fin_lock_ring", "retainer_male", "retainer_female", "fit_gauge"]
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
h_floor, h_ceiling, h_top = fin_housing_radii()

r_sh = (p.BODY_ID - p.SLIP_FIT) / 2
r_pilot = p.NOSE_HOOK_PILOT / 2


def axial_hits(shape: bd.Shape, x: float = 0.0, y: float = 0.0) -> list[float]:
    """Z values where a vertical probe at (x, y), z = -1..40, crosses the material boundary."""
    return sorted(tuple(v)[2] for v in (shape & bd.Edge.make_line((x, y, -1), (x, y, 40))).vertices())


for variant in ("nose_cone_hook", "nose_cone_open"):
    print(f"== Nose cone ({variant})")
    nose = shapes[variant]
    bb = nose.bounding_box()
    check_range("total height (fits the K1C 250 mm Z with margin)", bb.size.Z, 240.0, BUILD_HEIGHT - 2.0)
    check("base radius", outer_radius(nose, p.NOSE_SHOULDER_LEN + 0.5, 0), R, 0.05)
    check("shoulder radius (slip fit)", outer_radius(nose, 20, 0), r_sh)
    check("ogive wall inner radius at mid-length", bore_profile_radius(nose, 140, 90),
          outer_radius(nose, 140, 90) - p.NOSE_WALL, 0.15)
    if variant == "nose_cone_hook":
        for ang in (0, 90, 180, 270):  # between the gussets (they sit at 45 deg + k*90)
            hits = _ray_hits(nose, 12.0, ang)
            expect = [r_pilot, p.NOSE_HOOK_BOSS_D / 2, r_sh - p.NOSE_WALL, r_sh]
            ok = len(hits) == 4 and all(abs(a - b) <= TOL for a, b in zip(hits, expect))
            check_range(f"hook boss + shoulder wall section at {ang} deg (z=12): {[round(h, 3) for h in hits]}", float(ok), 1, 1)
        bulk = _ray_hits(nose, p.NOSE_BULKHEAD_THICKNESS / 2, 90)
        check_range("bulkhead solid from pilot hole to shoulder skin", float(len(bulk) == 2 and abs(bulk[0] - r_pilot) <= TOL
                    and abs(bulk[1] - r_sh) <= TOL), 1, 1)
        axis = axial_hits(nose)
        print(f"  axial probe hits (z): {[round(z, 3) for z in axis]}")
        check("pilot hole depth to drill-point tip", axis[0] if axis else float("nan"), p.NOSE_HOOK_DEPTH + r_pilot)
        check("boss top", axis[1] if len(axis) > 1 else float("nan"), p.NOSE_HOOK_DEPTH + r_pilot + p.NOSE_HOOK_BOSS_CAP)
    else:
        bar = _ray_hits(nose, 5.0, 90)  # across the bar (it spans the base along X); starts inside it at r = 0
        expect = [0.0, p.NOSE_BAR_WIDTH / 2, r_sh - p.NOSE_WALL, r_sh]
        ok = len(bar) == 4 and all(abs(a - b) <= TOL for a, b in zip(bar, expect))
        check_range(f"bar + shoulder wall section (z=5): {[round(h, 3) for h in bar]}", float(ok), 1, 1)
        axis = axial_hits(nose)
        print(f"  axial probe hits (z): {[round(z, 3) for z in axis]}")
        check("bar ridge height", axis[-1] if axis else float("nan"), p.NOSE_BAR_HEIGHT)
        beside = axial_hits(nose, 0.0, p.NOSE_BAR_WIDTH / 2 + 6.0)
        check_range("base open beside the bar (probe crossings)", float(len(beside)), 0, 0)

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
check("body radius (270 deg, clear of housings/guides)", outer_radius(fc, 60, 270), R)
check("stub radius (between detent grooves)", outer_radius(fc, p.FIN_CAN_LEN + 13, 30), r_stub)
check("stub detent groove bottom", outer_radius(fc, p.FIN_CAN_LEN + 13, 0), r_stub - p.DETENT_DEPTH)
check("motor bore radius", bore_profile_radius(fc, 50), r_bore)
z_stop = p.MOTOR_LEN - (p.MALE_BAND_LEN + p.MALE_THREAD_LEN)
check("bore just below engine stop", bore_profile_radius(fc, z_stop - 0.3), r_bore)
check_range("stop radius just above engine stop (< motor radius)", bore_profile_radius(fc, z_stop + 0.3),
            0.0, p.MOTOR_DIA / 2 - 0.5)
check("ejection passage radius", bore_profile_radius(fc, z_stop + 3.5), p.ENGINE_BLOCK_BORE / 2)
# Fin housing: along the fin plane (y = 0) the channel and neck are open to the outside.
hits = _ray_hits(fc, 60, p.FIN_ANGLE0)
print(f"  housing ray hits along the first fin plane at z=60: {[round(h, 3) for h in hits]}")
check("housing channel floor (rails ride above the 25.4 mm tube)", hits[1] if len(hits) == 2 else float("nan"), h_floor)
lip = _ray_hits(fc, 60, p.FIN_ANGLE0 + math.degrees(math.atan2(2.7, h_ceiling)))
print(f"  ray through a housing lip at z=60: {[round(h, 3) for h in lip]}")
check_range("housing lip over the rail flange (4 boundary crossings)", len(lip), 4, 4)
aft = _ray_hits(fc, p.FIN_HOUSING_AFT_STOP / 2, p.FIN_ANGLE0)
check_range("housing closed at the aft end (solid out to the top)", aft[-1] if len(aft) == 2 else float("nan"),
            h_top, h_top + 0.5)

print("== Fin")
fn = shapes["fin"]
bb = fn.bounding_box()
check("root length", bb.size.Z, p.FIN_ROOT_LEN)
check("span incl. rail", bb.max.X - bb.min.X, p.FIN_LE_TIP[0] + (h_top - h_floor - p.SLOT_CLEARANCE))
check("rail flange width", bb.size.Y, p.FIN_FLANGE_WIDTH)

print("== Fin lock ring")
ring = shapes["fin_lock_ring"]
r_ring = r_stub + p.LOCK_RING_CLEARANCE
check("thickness", ring.bounding_box().size.Z, p.LOCK_RING_THICKNESS)
check("bore radius (clear of fingers and notches)", bore_profile_radius(ring, 2.5, 30), r_ring)
check("outer radius (= housing top)", outer_radius(ring, 1.0, 30), h_top)
notch = _ray_hits(ring, 1.0, 0)
check("notch floor (inner band only)", notch[-1] if len(notch) == 2 else float("nan"), p.LOCK_RING_NOTCH_R)
check("detent nub tip", bore_profile_radius(ring, 2.5, LOCK_ANGLE), r_ring - p.DETENT_DEPTH)

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


gap("fin:1", "fin_can", 0.15, 0.25, "fin rail to housing clearance")
gap("fin:1", "fin_lock_ring", 0.15, 0.25, "fin forward end to locked ring")
gap("fin_lock_ring", "fin_can", 0.0, 1e-3, "lock ring seated on the fin can")
gap("lower_tube_not_printed", "fin_lock_ring", 0.0, 1e-3, "lower tube end on the lock ring")

print("== Fin lock function (fin:1, moved rigidly)")
fin1, can, ring_locked = leaves["fin:1"], leaves["fin_can"], leaves["fin_lock_ring"]
ring_open = ring_locked.rotate(bd.Axis.Z, -LOCK_ANGLE)
radial = bd.Vector(math.cos(math.radians(p.FIN_ANGLE0)), math.sin(math.radians(p.FIN_ANGLE0)), 0)


def moved(shape, v):
    return shape.moved(bd.Location(tuple(v)))


check_range("locked: 1 mm forward hits the ring (mm3)", overlap_volume(moved(fin1, (0, 0, 1.0)), ring_locked), 0.5, 1e9)
check_range("aft: 0.5 mm back hits the housing stop (mm3)", overlap_volume(moved(fin1, (0, 0, -0.5)), can), 0.5, 1e9)
check_range("outward: 0.5 mm radial pull hits the housing lips (mm3)", overlap_volume(moved(fin1, radial * 0.5), can), 0.5, 1e9)
out = moved(fin1, (0, 0, 20.0))
check_range("open: 20 mm forward clears the ring notch (mm3)", overlap_volume(out, ring_open), 0.0, 0.01)
check_range("open: 20 mm forward clears the fin can (mm3)", overlap_volume(out, can), 0.0, 0.01)
check_range("open: 20 mm forward rides over the body tube (mm3)", overlap_volume(out, leaves["lower_tube_not_printed"]), 0.0, 0.01)
check_range("open ring clears the fin can (detents in grooves) (mm3)", overlap_volume(ring_open, can), 0.0, 0.01)
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
