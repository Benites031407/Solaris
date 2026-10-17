"""Barrowman stability estimate for the assembled replica (subsonic, zero angle of attack).

Run from the project root after building the assembly:
    python checks/stability.py
Masses of printed parts come from the saved STEP volumes and centroids with an
effective print density (walls + sparse infill); non-printed items use typical
values. It is an estimate: weigh your parts and confirm with OpenRocket before
flying. Exits 1 if the static margin is below 1.0 caliber.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cadgen import read_scene  # noqa: E402

from lib import params as p  # noqa: E402

ABS = 1.04e-3  # g/mm3
# Effective fill of each printed part at 3 walls + ~10 % gyroid (thin shells print ~solid).
FILL = {"nose_cone": 0.95, "coupler": 0.95, "fin_can": 0.45, "fin": 0.9,
        "retainer_male": 0.9, "retainer_female": 0.9}
TUBE_G_PER_MM = 0.035     # ~2 in heavy-wall kraft body tube
MOTOR_TUBE_G = 8.0
RECOVERY_G = 35.0         # 24 in parachute, shock cord, aramid leader, wadding
RECOVERY_Z = 600.0        # packed in the upper tube
MOTORS = {"E16-4": (74.8, 44.0), "F15-6": (101.8, 60.0)}  # total g, propellant g

scene = read_scene(str(ROOT / "STEP" / "scorpio_assembly.step"))
items = []  # (label, mass g, z of centroid)
for occ in scene.leaves():
    shape = scene.resolve(occ.ref).shape()
    label = occ.label
    z = shape.center().Z
    if label.startswith("fin:"):
        items.append((label, shape.volume * ABS * FILL["fin"], z))
    elif label in FILL:
        items.append((label, shape.volume * ABS * FILL[label], z))
    elif label == "motor_tube_not_printed":
        items.append((label, MOTOR_TUBE_G, z))
    elif label.endswith("tube_not_printed"):
        bb = shape.bounding_box()
        items.append((label, bb.size.Z * TUBE_G_PER_MM, z))
items.append(("recovery", RECOVERY_G, RECOVERY_Z))

bb_all = [scene.resolve(o.ref).shape().bounding_box() for o in scene.leaves()]
z_tip = max(b.max.Z for b in bb_all)
z_aft = min(b.min.Z for b in bb_all)
length = z_tip - z_aft


def x_from_tip(z: float) -> float:
    return z_tip - z


# --- Barrowman centre of pressure -------------------------------------------------
d = p.BODY_OD
R = d / 2
nose_len = z_tip - (p.FIN_CAN_LEN + p.LOWER_TUBE_LEN + p.COUPLER_BAND_LEN + p.UPPER_TUBE_LEN)
cn_nose, x_nose = 2.0, 0.466 * nose_len  # tangent ogive

# Fin planform -> equivalent trapezoid with the same root, span and area.
cx, cz = 158.8, 183.0  # LE arc centre fitted in params (s, z); radius below
r_le = math.dist((cx, cz), (0.0, p.FIN_ROOT_LEN))


def le_z(s: float) -> float:
    return cz - math.sqrt(r_le ** 2 - (s - cx) ** 2)


def te_z(s: float) -> float:  # trailing edge, then the slanted tip edge
    s_te, (s_tip, z_tip_le) = p.FIN_TE_TIP_SPAN, p.FIN_LE_TIP
    return 0.0 if s <= s_te else z_tip_le * (s - s_te) / (s_tip - s_te)


span = p.FIN_LE_TIP[0]
n = 2000
area = sum((le_z((i + 0.5) * span / n) - te_z((i + 0.5) * span / n)) * span / n for i in range(n))
cr = p.FIN_ROOT_LEN
ct = max(2 * area / span - cr, 0.0)
x_r = cr - p.FIN_LE_TIP[1]  # sweep of the leading edge at the tip, measured aft
l_m = math.hypot(span, x_r + ct / 2 - cr / 2)
cn_fins = (1 + R / (span + R)) * (4 * p.FIN_COUNT * (span / d) ** 2) / (1 + math.sqrt(1 + (2 * l_m / (cr + ct)) ** 2))
fin_root_le = x_from_tip(p.FIN_SLOT_TOP - 0.2)
x_fins = fin_root_le + x_r * (cr + 2 * ct) / (3 * (cr + ct)) + ((cr + ct) - cr * ct / (cr + ct)) / 6
x_cp = (cn_nose * x_nose + cn_fins * x_fins) / (cn_nose + cn_fins)

print(f"length {length:.0f} mm, nose {nose_len:.1f} mm, fin area {area:.0f} mm2 "
      f"(equivalent trapezoid Cr={cr:.1f} Ct={ct:.1f} span={span:.1f})")
print(f"CN_alpha: nose {cn_nose:.2f}, fins {cn_fins:.2f};  CP {x_cp:.0f} mm from the tip")
dry = sum(m for _, m, _ in items)
for label, m, z in sorted(items, key=lambda t: -t[2]):
    print(f"  {label:26s} {m:6.1f} g at {x_from_tip(z):6.0f} mm from tip")

ok = True
motor_z = -(p.MALE_BAND_LEN + p.MALE_THREAD_LEN) + p.MOTOR_LEN / 2
for name, (m_motor, m_prop) in MOTORS.items():
    for phase, mm in (("lift-off", m_motor), ("burnout", m_motor - m_prop)):
        total = dry + mm
        x_cg = (sum(m * x_from_tip(z) for _, m, z in items) + mm * x_from_tip(motor_z)) / total
        margin = (x_cp - x_cg) / d
        flag = "ok" if margin >= 1.0 else "LOW"
        ok &= margin >= 1.0
        print(f"[{flag}] {name} {phase:8s}: mass {total:5.0f} g, CG {x_cg:5.0f} mm, margin {margin:4.2f} cal")
print(f"empty (no motor) printed+tubes+recovery mass: {dry:.0f} g  (Estes lists 482 g)")
raise SystemExit(0 if ok else 1)
