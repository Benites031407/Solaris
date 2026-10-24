"""Export the not-printed hardware meshes and the mechanism numbers the animation needs.

Run in the cadgen environment from this folder:
    uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.21 python export_parts.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from cadgen import build123d as bd  # noqa: E402

from lib import params as p  # noqa: E402
from lib.door_parts import (  # noqa: E402
    _x_cylinder, _zprism, cord_hole_xy, door_hinge, door_levels, door_spring_x, make_screw_dummies, nose_geom,
    servo_pose,
)

sv = servo_pose()
w2 = p.SERVO_BODY_W / 2
xb, xt = sv.x_bottom, sv.x_bottom + p.SERVO_BODY_H
ear = (p.SERVO_EAR_SPAN - p.SERVO_BODY_L) / 2
body = _zprism(xb, xt, -w2, w2, sv.z_body_lo, sv.z_body_hi)
body += _zprism(sv.x_seat, sv.x_seat + p.SERVO_EAR_T, -w2, w2, sv.z_body_lo - ear, sv.z_body_hi + ear)
x_horn0 = sv.x_horn - 0.9
body += _x_cylinder(w2 - 0.3, xt - 0.1, xt + 2.5, 0.0, sv.z_shaft)
body += _x_cylinder(2.4, xt + 2.4, x_horn0 + 0.1, 0.0, sv.z_shaft)
horn = _x_cylinder(3.5, x_horn0, x_horn0 + 1.8, 0.0, sv.z_shaft)
horn += _zprism(x_horn0, x_horn0 + 1.8, -2.25, 2.25, sv.z_shaft, sv.z_shaft + p.SERVO_ARM)
(HERE / "meshes").mkdir(exist_ok=True)
bd.export_stl(body, str(HERE / "meshes" / "servo_body.stl"), tolerance=0.02)
bd.export_stl(horn, str(HERE / "meshes" / "horn.stl"), tolerance=0.02)
bd.export_stl(bd.Compound(children=make_screw_dummies()), str(HERE / "meshes" / "screws.stl"), tolerance=0.02)

g = nose_geom()
hinge = door_hinge()
z_d0, z_f = door_levels()
x_bottom, _, x_tip = door_spring_x()
scene = {
    "R": p.BODY_OD / 2, "wall": p.NOSE_WALL, "rho": g.rho, "cr": g.cr, "cz": g.cz, "z_og": g.z_og, "apex": g.apex,
    "shoulder_len": p.SHOULDER_LEN, "z_d0": z_d0, "z_f": z_f, "c": p.NOSE_DOOR_CLEARANCE,
    "hinge_point": list(hinge.position), "hinge_dir": list(hinge.direction),
    "spring_y": p.NOSE_DOOR_SPRING_Y, "spring_z": z_d0 + p.NOSE_DOOR_SPRING_Z, "pocket_bottom_x": x_bottom,
    "pin_tip_x": x_tip, "spring_free": p.SPRING_FREE_LEN, "spring_od": p.SPRING_OD_MAX,
    "cord_hole": list(cord_hole_xy()), "cord_az": p.NOSE_DOOR_CORD_AZ, "ramp_angle": p.NOSE_DOOR_RAMP_ANGLE,
    "shaft_z": sv.z_shaft, "x_horn": sv.x_horn, "unlock_deg": p.SERVO_UNLOCK_ANGLE, "release_deg": 26.0,
    "joint_z": p.NOSE_DOOR_JOINT_Z, "eye_x": [-12.0, -4.0], "eye_half_y": 4.0,
}
(HERE / "scene.json").write_text(json.dumps(scene, indent=1), encoding="utf-8")
print(json.dumps(scene))
