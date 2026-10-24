"""Validate the saved STEP outputs of the Helios side-door nose: kernel soundness,
airframe-interface dimensions, and the door mechanism (latch, springs, swing, fly-off).

Run from _nose_door after building the models:
    python checks/check_door.py
Exits 1 if any check fails. All lengths in mm.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import build123d as bd  # noqa: E402
from cadgen import read_scene, read_step  # noqa: E402
from cadgen.geometry import boundary_edges, closest_points, is_sound, overlap_volume, topology_errors  # noqa: E402

from lib import params as p  # noqa: E402
from lib.door_parts import (  # noqa: E402
    R_BODY, cord_hole_xy, door_hinge, door_levels, keeper_lift, make_servo_dummy, nose_geom, servo_mount, servo_pose,
)

PARTS = ["helios_nose_door_housing", "helios_nose_door", "helios_nose_servo_keeper"]
BUILD_HEIGHT = 300.0  # Creality K1 Max (the K1C has 250)
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


def axial_hits(shape: bd.Shape, x: float, y: float, z0: float = -1.0, z1: float = 300.0) -> list[float]:
    """Z values where a vertical probe at (x, y) crosses the material boundary."""
    return sorted(tuple(v)[2] for v in (shape & bd.Edge.make_line((x, y, z0), (x, y, z1))).vertices())


def moved(shape, v):
    return shape.moved(bd.Location(tuple(v)))


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

housing = shapes["helios_nose_door_housing"].solids()[0]
g = nose_geom()
z_d0, z_f = door_levels()

print("== Airframe interface (cone.stl / Mbody.stl numbers)")
hh = housing.bounding_box().size.Z
check_range("housing height (cone.stl's sharp tip is 248.97; K1 Max 300, K1C 250)", hh, 240.0, 249.0)
for ang in (60.0, 240.0):  # away from the screw pads
    hits = _ray_hits(housing, 13.0, ang)
    check(f"shoulder outer radius at {ang:.0f} deg (Mbody bore r {p.MBODY_BORE_R})", hits[-1], p.SHOULDER_R)
    check(f"shoulder wall at {ang:.0f} deg", hits[-1] - hits[-2], p.NOSE_WALL)
check_range("radial clearance in Mbody's socket", p.MBODY_BORE_R - p.SHOULDER_R, 0.10, 0.25)
face = axial_hits(housing, -(p.MBODY_BORE_R + p.SEAT_R_OUT) / 2, 0.0, -1.0, 60.0)  # on the flat seat
check("shoulder face lands on Mbody's rim at z (bay: nose_z = 26.2069 - s)", face[0] if face else float("nan"), p.SHOULDER_LEN)
check("skirt radius = airframe OD / 2", _ray_hits(housing, 45.0, 180.0)[-1], R_BODY)
r150 = g.r_offset(0.0, 150.0)
check("ogive radius at z 150 (cone.stl: 21.37 at 149.3, 19.63 at 159.3)", _ray_hits(housing, 150.0, 180.0)[-1], r150)
check_range("cone.stl's measured r(150) vs this ogive", r150, 20.90, 21.45)
for az in p.RETAIN_AZ:
    hits = _ray_hits(housing, p.RETAIN_Z, az)
    print(f"  pilot ray at {az:.0f} deg, z {p.RETAIN_Z}: {[round(h, 3) for h in hits]}")
    ok = len(hits) == 2 and abs(hits[0] - p.RETAIN_PAD_R_IN) <= TOL and abs(hits[1] - p.RETAIN_PILOT_R0) <= TOL
    check_range(f"screw pad face r {p.RETAIN_PAD_R_IN} and blind pilot from r {p.RETAIN_PILOT_R0} to the OD at {az:.0f} deg",
                float(ok), 1, 1)
check_range("M2.5 x 8 stops short of the pilot floor (mm): tube 1.47 + pilot depth - 8",
            1.47 + p.SHOULDER_R - p.RETAIN_PILOT_R0 - 8.0, 0.3, 1.5)
check("retention station below Mbody's rim (clamshell: 13.2069)", p.SHOULDER_LEN - p.RETAIN_Z, 13.2069, 0.001)

# Shock cord: a Ø4 cord rising from the shoulder's open base under the cord hole, up
# through it and 10 mm into the compartment, must not touch the housing.
xc, yc = cord_hole_xy()
a = math.radians(p.NOSE_DOOR_CORD_AZ)
r0 = 24.0
start = bd.Vector(r0 * math.cos(a), r0 * math.sin(a), -1.0)
end = bd.Vector(xc, yc, z_f + 25.0)
cord = bd.Solid.make_cylinder(2.0, (end - start).length, bd.Plane(origin=start, z_dir=end - start))
check_range("Ø4 shock cord from the shoulder base up through the cord hole clears the housing (mm3)",
            overlap_volume(cord, housing), 0.0, 0.01)

print("== Side-door mechanism (housing + door + servo envelope + springs)")
dscene = read_scene(str(ROOT / "STEP" / "helios_nose_door_assembly.step"))
dl = {occ.label: dscene.resolve(occ.ref).shape().solids()[0] for occ in dscene.leaves()}
print("  leaves:", sorted(dl))
housing_d, door_d, servo_l = dl["helios_nose_door_housing"], dl["helios_nose_door"], dl["servo_mg90s_not_printed"]
keeper_d = dl["helios_nose_servo_keeper"]
springs = [dl["spring_not_printed:1"], dl["spring_not_printed:2"]]
screws = [dl["m2_5x8_not_printed:1"], dl["m2_5x8_not_printed:2"]]
servo_open = make_servo_dummy(-p.SERVO_UNLOCK_ANGLE).solids()[0]
for (la, sa), (lb, sb) in (
    (("housing", housing_d), ("door", door_d)), (("housing", housing_d), ("servo latched", servo_l)),
    (("door", door_d), ("servo latched", servo_l)), (("housing", housing_d), ("servo released", servo_open)),
    (("door", door_d), ("servo released", servo_open)), (("housing", housing_d), ("screw 1", screws[0])),
    (("housing", housing_d), ("screw 2", screws[1])), (("servo latched", servo_l), ("screw 1", screws[0])),
    (("housing", housing_d), ("keeper", keeper_d)), (("keeper", keeper_d), ("servo latched", servo_l)),
    (("keeper", keeper_d), ("servo released", servo_open)), (("keeper", keeper_d), ("door", door_d)),
):
    check_range(f"no interference {la} / {lb} (mm3)", overlap_volume(sa, sb), 0.0, 0.01)
check_range("servo stays inside the nose: above the avionics bay's face at z -1.1",
            servo_open.bounding_box().min.Z, 0.0, 300.0)
check_range("door seated on the band (contact, mm)", closest_points(door_d, housing_d).distance, 0.0, 1e-3)
for i, sp in enumerate(springs, 1):
    check_range(f"compressed spring {i} clear of the door pocket and the pin (mm3)",
                overlap_volume(sp, door_d) + overlap_volume(sp, housing_d), 0.0, 0.05)
    check_range(f"spring {i} bears on the split face (mm)", closest_points(sp, housing_d).distance, 0.0, 1e-3)
    check_range(f"spring {i} seats on the pocket's funnel (gap to it, mm)", closest_points(sp, door_d).distance, 0.0, 0.5)

print("== Servo mount (MG90S as measured, slid in from the shoulder base, keeper under it)")
sv, mt = servo_pose(), servo_mount()
check_range("servo ears bear on the mount plate (mm)", closest_points(servo_l, housing_d).distance, 0.0, 1e-3)
check("horn arm mid-plane on the latch groove's centre line (x)", sv.x_arm, p.NOSE_DOOR_GROOVE_R, 1e-6)
blocked = [d / 2 for d in range(1, 93) if overlap_volume(make_servo_dummy(0.0, d / 2).solids()[0], housing_d) > 0.01]
check_range("servo with its horn on (arm up) slides up from below the shoulder base without touching the housing: "
            "blocked steps of 0.5 mm", float(len(blocked)), 0.0, 0.0)
check_range("  ...starting fully below the shoulder base (top of the dropped servo, z)",
            make_servo_dummy(0.0, 46.0).bounding_box().max.Z, -60.0, 0.0)
check_range("servo up 0.5 mm hits the slot roof (mm3)", overlap_volume(moved(servo_l, (0, 0, 0.5)), housing_d), 0.5, 1e9)
check_range("servo down 0.5 mm hits the keeper (mm3)", overlap_volume(moved(servo_l, (0, 0, -0.5)), keeper_d), 0.5, 1e9)
check_range("gap servo to keeper (mm)", closest_points(servo_l, keeper_d).distance, 0.05, 0.2)
check_range("servo pulled 0.5 mm toward the door: its ears hit the mount plate (mm3)",
            overlap_volume(moved(servo_l, (0.5, 0, 0)), housing_d), 0.5, 1e9)
check_range("servo pushed 0.5 mm back: its ears hit the channel's back wall (mm3)",
            overlap_volume(moved(servo_l, (-0.5, 0, 0)), housing_d), 0.5, 1e9)
check_range("servo shifted 0.5 mm sideways hits the slot (mm3)", overlap_volume(moved(servo_l, (0, 0.5, 0)), housing_d), 0.5, 1e9)
check_range("keeper tabs screwed up against their pockets' roofs (mm)", closest_points(keeper_d, housing_d).distance, 0.0, 1e-3)
check_range("keeper's lowest face above the shoulder base (bay face is 1.1 below it)", keeper_d.bounding_box().min.Z, 0.0, 1.0)
seat = keeper_lift() + p.KEEPER_HEAD_DEPTH
check_range("M2 x 8 keeper screw stops short of its pilot's floor (mm)", mt.z_tab + p.KEEPER_PILOT_DEPTH - (seat + 8.0), 0.3, 1.5)
check_range("keeper screw goes 4+ mm into the housing (mm)", seat + 8.0 - mt.z_tab, 4.0, 20.0)
for sign, side in ((-1, "toward the case's far end"), (1, "toward its near end")):
    swing = [a for a in range(0, 61, 5)
             if overlap_volume(make_servo_dummy(sign * float(a)).solids()[0], door_d) > 0.01
             or overlap_volume(make_servo_dummy(sign * float(a)).solids()[0], housing_d) > 0.01
             or overlap_volume(make_servo_dummy(sign * float(a)).solids()[0], keeper_d) > 0.01]
    check_range(f"arm swings 0 -> 60 deg {side} with the door shut, touching nothing: blocked angles", float(len(swing)), 0.0, 0.0)
tip_z = sv.z_shaft + p.SERVO_ARM * math.cos(math.radians(p.SERVO_UNLOCK_ANGLE))
check_range("released arm tip below the door's floor (mm)", z_d0 - tip_z, 2.0, 20.0)
check_range("latched arm tip below the groove roof (mm)", z_d0 + p.NOSE_DOOR_GROOVE_H - (sv.z_shaft + p.SERVO_ARM), 2.0, 5.0)
check_range("latched arm tip into the groove (mm)", sv.z_shaft + p.SERVO_ARM - z_d0, 3.0, 5.0)

check_range("latched: door pushed 1.5 mm outward hits the servo arm (mm3)",
            overlap_volume(moved(door_d, (1.5, 0, 0)), servo_l), 0.5, 1e9)
check_range("released: door pushed 3 mm outward clears the servo arm (mm3)",
            overlap_volume(moved(door_d, (3.0, 0, 0)), servo_open), 0.0, 0.01)
check_range("top: door pushed 1 mm outward is held by the tab inside the tip (mm3)",
            overlap_volume(moved(door_d, (1.0, 0, 0)), housing_d), 0.5, 1e9)
check_range("door lifted 1.2 mm hits the tip / pins (mm3)",
            overlap_volume(moved(door_d, (0, 0, 1.2)), housing_d), 0.5, 1e9)
check_range("door shifted 1 mm sideways hits the spring pins (mm3)",
            overlap_volume(moved(door_d, (0, 1.0, 0)), housing_d), 0.5, 1e9)

# Opening: once the arm drops, the springs kick the door's bottom out and it swings
# about its top outer edge until its tab drops out of the tip; from then on it can
# leave in a straight line. A contact hinge may lift it a little: within the joint gap.
hinge = door_hinge()
probe = bd.Vertex(hinge.position.X, 0, z_d0)
assert probe.rotate(hinge, 5.0).center().X > hinge.position.X


def free_path(turned) -> bool:
    return all(overlap_volume(moved(turned, (dx, 0, 0)), housing_d) <= 0.05 for dx in (1.0, 3.0, 6.0, 10.0, 15.0, 20.0, 30.0))


worst_lift, release = 0.0, None
for ang in range(2, 62, 3):
    turned = door_d.rotate(hinge, float(ang))
    lift = next((i * 0.1 for i in range(0, 16)
                 if overlap_volume(moved(turned, (0, 0, i * 0.1)), housing_d) <= 0.05
                 and overlap_volume(moved(turned, (0, 0, i * 0.1)), servo_open) <= 0.05), float("inf"))
    worst_lift = max(worst_lift, lift)
    if lift == float("inf"):
        print(f"  swing blocked at {ang} deg")
        break
    if free_path(turned):
        release = ang
        break
print(f"  door swings clear (max lift {worst_lift:.1f} mm) and leaves once swung {release} deg")
check_range("swing until release needs no lift: the door's bottom never touches the band (mm)", worst_lift, 0.0, 0.0)
rub = max(overlap_volume(door_d.rotate(hinge, a / 2), housing_d) for a in range(1, 41))
check_range("swinging 0.5..20 deg about the hinge, the door touches the housing nowhere (mm3)", rub, 0.0, 0.01)
check_range("fly-off: tab drops out of the tip after a swing of (deg)", float(release or 1e9), 0.0, 45.0)

cavity = g.outer - g.shell
room = (cavity & (bd.Pos(0, 0, z_f) * bd.Box(80, 80, 300, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))))
room = room - housing_d - door_d
print(f"  parachute compartment above the floors: {room.volume / 1000:.0f} cm3")
print(f"  servo case x {sv.x_bottom:.1f}..{sv.x_bottom + p.SERVO_CASE_H:.1f}, y {sv.y_near:.1f}..{sv.y_far:.1f}, "
      f"z {sv.z_lo:.2f}..{sv.z_hi:.2f}; ears x {sv.x_ear:.1f}..{sv.x_mount:.1f}; arm plane x {sv.x_arm:.1f}, shaft z {sv.z_shaft:.2f}")

print()
if failures:
    print("FAILED:", failures)
    raise SystemExit(1)
print("ALL CHECKS PASSED")
