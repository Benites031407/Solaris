"""Dump the side-door nose's CAD numbers (../_nose_door) for the explainer figure."""
import json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_nose_door" / "src"))
from lib import params as p  # noqa: E402
from lib.door_parts import (  # noqa: E402
    DOOR_K, R_BODY, cord_hole_xy, door_hinge, door_joint_z, door_levels, door_spring_x, nose_geom, servo_pose,
)

g = nose_geom()
z_d0, z_f = door_levels()
sv = servo_pose()
hinge = door_hinge()
x_bottom, x_funnel, x_tip = door_spring_x()
zj = p.NOSE_DOOR_JOINT_Z
out = {k: getattr(p, k) for k in dir(p) if k.isupper()}
out.update({
    "R": R_BODY, "cr": g.cr, "cz": g.cz, "rho": g.rho, "z_og": g.z_og, "apex": g.apex, "r_sh": g.r_sh, "r_sh_in": g.r_sh_in,
    "z_d0": z_d0, "z_f": z_f, "door_k": DOOR_K,
    "hinge_point": list(hinge.position), "hinge_dir": list(hinge.direction),
    "pocket_bottom_x": x_bottom, "funnel_x": x_funnel, "pin_tip_x": x_tip,
    "servo": {"x_bottom": sv.x_bottom, "x_seat": sv.x_seat, "x_horn": sv.x_horn, "z_shaft": sv.z_shaft,
              "z_lo": sv.z_body_lo, "z_hi": sv.z_body_hi, "z_holes": list(sv.z_holes)},
    "cord_hole": list(cord_hole_xy()),
    "joint_outer": [g.r_offset(0.0, zj), door_joint_z(g.r_offset(0.0, zj))],
    "ogive": [[z, g.r_offset(0.0, z), g.r_offset(p.NOSE_WALL, z)] for z in [p.SHOULDER_LEN + i * 0.5 for i in range(int((g.apex - p.SHOULDER_LEN) / 0.5) + 1)] if z < g.apex - 0.05],
})
Path(__file__).with_name("nose.json").write_text(json.dumps(out, indent=0, default=float), encoding="utf-8")
print("nose.json", len(out), "keys; apex", round(g.apex, 3))
