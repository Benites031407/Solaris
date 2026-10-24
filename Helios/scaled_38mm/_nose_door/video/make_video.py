"""Animation: the Helios side-door nose deploying its parachute.

Rendered with PyVista (VTK, off-screen) from the real meshes: the assembled Helios
(../../rocket_assembled_boattail.stl, its cone removed), the exported nose housing and
door, and the servo/horn/screws written by export_parts.py. The mechanism follows the
CAD numbers in scene.json: hinge axis, spring stations, 60 deg arm, release at 26 deg,
cord hole over Mbody's anchor tunnel. The springs, shock cord and parachute are
generated here.

    uv run --no-project --with pyvista --with trimesh --with scipy --with networkx \
        --with pillow --with imageio --with imageio-ffmpeg python make_video.py
Options: --stills 3,9.3,12 (PNG frames only), --scale 0.5 (quick low-res), --fps 30.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pyvista as pv
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
NOSE = HERE.parent
AIR = NOSE.parent
S = json.loads((HERE / "scene.json").read_text(encoding="utf-8"))
FONTS = AIR / "brag-output" / "composition" / "assets" / "fonts"

DURATION = 28.0
ORANGE, AIRFRAME, DARK = "#D2603F", "#D8D3CB", "#3A3F47"
RED, WHITE, KEVLAR = "#C8102E", "#F2F2F2", "#E2B33C"


# --- small maths ------------------------------------------------------------------------


def clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def seg(t: float, t0: float, t1: float) -> float:
    return clamp01((t - t0) / (t1 - t0))


def smooth(x: float) -> float:
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def lerp(a, b, f):
    return np.asarray(a, float) * (1 - f) + np.asarray(b, float) * f


def trans(v) -> np.ndarray:
    m = np.eye(4)
    m[:3, 3] = v
    return m


def rot(axis, deg: float, point=(0.0, 0.0, 0.0)) -> np.ndarray:
    """Right-hand rotation about an axis through a point (4x4)."""
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    th = math.radians(deg)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    r = np.eye(3) + math.sin(th) * k + (1 - math.cos(th)) * k @ k
    m = np.eye(4)
    m[:3, :3] = r
    p = np.asarray(point, float)
    m[:3, 3] = p - r @ p
    return m


def apply(m: np.ndarray, pts: np.ndarray) -> np.ndarray:
    return pts @ m[:3, :3].T + m[:3, 3]


# --- procedural meshes --------------------------------------------------------------------


def tube_faces(n: int, sides: int) -> np.ndarray:
    faces = []
    for i in range(n - 1):
        for k in range(sides):
            a, b = i * sides + k, i * sides + (k + 1) % sides
            faces.append([4, a, b, b + sides, a + sides])
    return np.array(faces, dtype=np.int64).ravel()


def tube_points(path: np.ndarray, radius: float, sides: int) -> np.ndarray:
    """Circle swept along a polyline with parallel-transport frames (fixed topology)."""
    t = np.gradient(path, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    ref = np.array([0.0, 0.0, 1.0]) if abs(t[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    nrm = np.cross(t[0], ref)
    nrm /= np.linalg.norm(nrm)
    ang = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    out = np.empty((len(path) * sides, 3))
    for i, (p, ti) in enumerate(zip(path, t)):
        nrm = nrm - np.dot(nrm, ti) * ti
        nrm /= np.linalg.norm(nrm) + 1e-12
        b = np.cross(ti, nrm)
        out[i * sides:(i + 1) * sides] = p + radius * (np.outer(np.cos(ang), nrm) + np.outer(np.sin(ang), b))
    return out


def resample(ctrl: np.ndarray, n: int) -> np.ndarray:
    """Catmull-Rom through the control points, resampled to n points by arc length."""
    c = np.vstack([2 * ctrl[0] - ctrl[1], ctrl, 2 * ctrl[-1] - ctrl[-2]])
    dense = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for u in np.linspace(0, 1, 24, endpoint=False):
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    dense.append(ctrl[-1])
    dense = np.array(dense)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]
    q = np.linspace(0, s[-1], n)
    return np.c_[[np.interp(q, s, dense[:, k]) for k in range(3)]].T


SPRING_N, SPRING_SIDES, SPRING_TURNS = 260, 6, 10


def spring_path(length: float, y: float) -> np.ndarray:
    s = np.linspace(0, 1, SPRING_N)
    f = s - 0.6 * np.sin(2 * math.pi * s) / (2 * math.pi)  # closed, tighter end coils
    rm = (S["spring_od"] - 0.5) / 2
    ang = 2 * math.pi * SPRING_TURNS * s
    return np.c_[-S["c"] + length * f, y + rm * np.cos(ang), S["spring_z"] + rm * np.sin(ang)]


def z_floor(x: float, y: float) -> float:
    """Top of whatever the packed chute rests on: door floor, ramp, tie eye, tether lug."""
    zf, c = S["z_f"], S["c"]
    z = zf
    if x < -c:
        z = max(z, zf + math.tan(math.radians(S["ramp_angle"])) * (-c - x))
    if -13.0 < x < -3.0 and abs(y) < 5.5:
        z = max(z, zf + math.tan(math.radians(S["ramp_angle"])) * 11.8 + 7.0)
    if 0.5 < x < 7.0 and abs(y) < 3.8:
        z = max(z, zf + 6.0)
    return z + 0.8


def bundle_mesh() -> tuple[pv.PolyData, np.ndarray]:
    """The packed chute: a bag resting on the floor, ramp and eye; gore-striped."""
    cx, rb, z_cyl, cap = 3.0, 17.0, 127.0, 9.0
    nt, m_bot, j_side, k_cap = 72, 6, 14, 6
    th = np.linspace(0, 2 * math.pi, nt, endpoint=False)
    rows = []
    for m in range(1, m_bot + 1):
        r = rb * m / m_bot
        rows.append([(cx + r * math.cos(a), r * math.sin(a), z_floor(cx + r * math.cos(a), r * math.sin(a))) for a in th])
    edge = [p[2] for p in rows[-1]]
    for j in range(1, j_side + 1):
        rows.append([(cx + rb * math.cos(a), rb * math.sin(a), edge[i] + (z_cyl - edge[i]) * j / j_side) for i, a in enumerate(th)])
    for k in range(1, k_cap):
        al = math.pi / 2 * k / k_cap
        rows.append([(cx + rb * math.cos(al) * math.cos(a), rb * math.cos(al) * math.sin(a), z_cyl + cap * math.sin(al)) for a in th])
    pts = [(cx, 0.0, z_floor(cx, 0.0))] + [p for row in rows for p in row] + [(cx, 0.0, z_cyl + cap)]
    faces, gore = [], []
    nr = len(rows)
    for i in range(nt):
        faces.append([3, 0, 1 + (i + 1) % nt, 1 + i])
        gore.append((i * 8 // nt) % 2)
    for r_ in range(nr - 1):
        for i in range(nt):
            a, b = 1 + r_ * nt + i, 1 + r_ * nt + (i + 1) % nt
            faces.append([4, a, b, b + nt, a + nt])
            gore.append((i * 8 // nt) % 2)
    top = len(pts) - 1
    for i in range(nt):
        faces.append([3, 1 + (nr - 1) * nt + i, 1 + (nr - 1) * nt + (i + 1) % nt, top])
        gore.append((i * 8 // nt) % 2)
    mesh = pv.PolyData(np.array(pts), np.array([v for f in faces for v in f]))
    mesh.cell_data["gore"] = np.array(gore)
    return mesh, np.array([cx, -6.0, z_floor(cx, -6.0)])


GORES, CAN_V, CAN_T = 8, 22, 8 * 14
LINE_LEN, CAN_R, CAN_H = 580.0, 262.0, 230.0


def canopy_points(u: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    """Canopy surface and line end points in the group frame (confluence at the origin,
    axis +z). u: lines paid out (0..1); s: inflation (0 streamer .. 1 open)."""
    se = s if s > 1 else smooth(s)
    th = np.linspace(0, 2 * math.pi, CAN_T, endpoint=False)
    v = np.linspace(0.06, 1.0, CAN_V + 1)
    beta = 1.75 * v
    scallop = 1 - 0.07 * (1 - np.abs(np.sin(GORES * th / 2)) ** 0.6)
    r_open = CAN_R * np.outer(np.sin(beta), scallop)
    z_open = np.outer(CAN_H * np.cos(beta), np.ones_like(th))
    r_str = 0.07 * CAN_R * np.outer(np.sin(np.minimum(beta, 1.57)) ** 0.5, 1 + 0.25 * np.sin(5 * th))
    z_str = np.outer(1.6 * CAN_H * np.cos(beta * 0.9), np.ones_like(th))
    r = r_str * (1 - se) + r_open * se
    z = z_str * (1 - se) + z_open * se
    r_skirt = r[-1].max()
    z_attach = math.sqrt(max(LINE_LEN ** 2 - r_skirt ** 2, 1.0)) * u
    zz = z - z[-1].mean() + z_attach
    pts = np.stack([r * np.cos(th), r * np.sin(th), zz], axis=-1).reshape(-1, 3)
    seams = np.arange(0, CAN_T, CAN_T // GORES)
    ends = np.stack([r[-1, seams] * np.cos(th[seams]), r[-1, seams] * np.sin(th[seams]), zz[-1, seams]], axis=-1)
    return pts, ends


def canopy_mesh() -> pv.PolyData:
    pts, _ = canopy_points(1.0, 1.0)
    faces, gore = [], []
    for i in range(CAN_V):
        for k in range(CAN_T):
            a, b = i * CAN_T + k, i * CAN_T + (k + 1) % CAN_T
            faces.append([4, a, b, b + CAN_T, a + CAN_T])
            gore.append((k * GORES // CAN_T) % 2)
    mesh = pv.PolyData(pts, np.array([v for f in faces for v in f]))
    mesh.cell_data["gore"] = np.array(gore)
    return mesh


# --- the scene -------------------------------------------------------------------------------


def load(path: Path) -> pv.PolyData:
    return pv.read(str(path)).clean()


def rocket_without_cone() -> list[tuple[pv.PolyData, str]]:
    m = trimesh.load_mesh(AIR / "rocket_assembled_boattail.stl")
    out = []
    for b in m.split(only_watertight=False):
        if b.volume <= 0 or b.bounds[1][2] > 980.0:  # internal voids, and the old cone
            continue
        mbody = abs(b.bounds[1][2] - 760.0) < 0.05 and abs(b.bounds[0][2] - 497.93) < 0.05
        out.append((pv.wrap(b), "mbody" if mbody else "airframe"))
    return out


def anchor_azimuth() -> float:
    """Azimuth of Mbody's cord-anchor tunnel in the assembled rocket (58 mm below its rim)."""
    m = trimesh.load_mesh(AIR / "rocket_assembled_boattail.stl")
    sec = m.section(plane_origin=[0, 0, 760.0 - 58.0], plane_normal=[0, 0, 1])
    loops = [e for e in sec.discrete if 18 < np.hypot(e[:, 0], e[:, 1]).mean() < 31.0 and np.hypot(e[:, 0], e[:, 1]).max() < 31.2]
    e = loops[0]
    return math.degrees(math.atan2(e[:, 1].mean(), e[:, 0].mean()))


PHI = anchor_azimuth() - S["cord_az"]       # turn the nose so its cord hole sits over the anchor
NOSE_TO_ASM = trans((0, 0, 760.0 - S["shoulder_len"])) @ rot((0, 0, 1), PHI)
HINGE_P, HINGE_D = np.array(S["hinge_point"]), np.array(S["hinge_dir"])

# timeline (s)
T_ARM = (9.2, 9.8)
T_SWING = (10.8, 12.0)          # slow motion: the real kick takes a few tens of ms
T_BAG = (13.8, 15.4)
T_LINES = (15.4, 16.7)
T_INFL = (16.7, 18.2)
SWING_W = 26.0 * (0.35 + 1.3) / (T_SWING[1] - T_SWING[0])  # deg/s at release

CAPTIONS = [
    (7.2, 9.1, "01", "LOCKED", "The servo arm stands in a groove under the door. Two springs push the door outward."),
    (9.1, 10.8, "02", "APOGEE: OPEN","The ESP32 turns the servo 60\u00b0 and the arm drops out of the groove."),
    (10.8, 12.4, "03", "KICK", "The springs throw the door's bottom out; it swings about its top tab.   (slow motion)"),
    (12.4, 14.0, "04", "DOOR AWAY", "At 26\u00b0 the tab clears the tip and the door flies off."),
    (14.0, 16.2, "05", "CHUTE OUT", "The packed chute slides off the 50\u00b0 ramp and out of the opening."),
    (16.4, 21.0, "06", "CANOPY", "The 30 in canopy opens. The Kevlar shock cord is anchored in the airframe, not the nose."),
]

# camera keys: t, azimuth from the door side (deg), elevation (deg), distance, target z (assembly mm),
# sideways shift (fraction of the half-width; + puts the subject right of centre, clear of the captions)
CAM_KEYS = [
    (0.0, 150, 6, 3150, 470, 0.0), (4.0, 100, 8, 3050, 470, 0.0), (7.0, 38, 20, 340, 790, 0.22),
    (10.6, 32, 17, 350, 792, 0.22), (12.0, 60, 12, 580, 832, 0.22), (13.6, 88, 9, 760, 850, 0.18),
    (15.0, 70, 7, 900, 880, 0.15), (16.4, 62, 5, 2600, 1300, 0.08), (19.6, 60, 4, 4750, 1180, 0.22),
    (DURATION, 118, 5, 4650, 1150, 0.22),
]
FOV, ASPECT = 30.0, 16 / 9


def camera_at(t: float):
    for (t0, *a), (t1, *b) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if t <= t1:
            f = smooth(seg(t, t0, t1))
            break
    az, el, dist, tz, shift = lerp(a, b, f)
    az = math.radians(az + PHI)
    el = math.radians(el)
    target = np.array([0.0, 0.0, tz])
    eye = target + dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    fwd = (target - eye) / dist
    right = np.cross(fwd, (0, 0, 1))
    right /= np.linalg.norm(right)
    off = -shift * dist * math.tan(math.radians(FOV / 2)) * ASPECT * right
    return eye + off, target + off


def door_pose(t: float, door_com: np.ndarray) -> np.ndarray:
    """Door transform in the nose frame (applied after lifting it onto the band)."""
    if t <= T_SWING[0]:
        return np.eye(4)
    x = seg(t, *T_SWING)
    ang = 26.0 * (0.35 * x + 0.65 * x * x)
    swing = rot(HINGE_D, ang, HINGE_P)
    if t <= T_SWING[1]:
        return swing
    dt = t - T_SWING[1]
    c0 = apply(swing, door_com[None])[0]
    w = math.radians(SWING_W) * HINGE_D / np.linalg.norm(HINGE_D)
    v = np.cross(w, c0 - HINGE_P)                          # CG velocity at release (mm/s)
    drift = v * dt + np.array([260.0, 0.0, -60.0]) * dt * dt
    spin = rot(HINGE_D, SWING_W * dt, c0) @ rot((0, 0, 1), 35.0 * dt, c0)
    return trans(drift) @ spin @ swing


def spring_len(t: float, door_m: np.ndarray, y: float) -> float:
    closed = S["pocket_bottom_x"] + S["c"]
    if t > T_SWING[1]:
        return S["spring_free"]
    p = np.array([S["pocket_bottom_x"], y, S["spring_z"]])
    dx = apply(door_m, p[None])[0][0] - p[0]
    return float(np.clip(closed + dx, closed, S["spring_free"]))


def chute_state(t: float):
    """Bundle transform, canopy group transform, payout u, inflation s (nose frame)."""
    x = smooth(seg(t, *T_BAG))
    bag = trans((88.0 * x, 0.0, 16.0 * x)) @ rot((0, 1, 0), 22.0 * x, (20.0, 0.0, 60.0))
    q0, q1, qf = np.array([100.0, 0.0, 105.0]), np.array([200.0, 0.0, 430.0]), np.array([42.0, 0.0, 700.0])
    if t < T_LINES[1]:
        f = smooth(seg(t, *T_LINES))
        q, tilt, u, s = lerp(q0, q1, f), 62.0 - 37.0 * f, 0.06 + 0.94 * f, 0.0
    else:
        f = smooth(seg(t, *T_INFL))
        q, tilt, u = lerp(q1, qf, f), 25.0 * (1 - f), 1.0
        g = seg(t, *T_INFL)
        s = g * (1 + 0.08 * math.sin(math.pi * g)) if g < 1 else 1 + 0.012 * math.sin(2 * math.pi * (t - T_INFL[1]) / 1.6)
    group = trans(q) @ rot((0, 1, 0), tilt)
    return bag, group, u, s


def cord_ctrl(t: float, attach: np.ndarray) -> np.ndarray:
    a = math.radians(S["cord_az"])
    hx, hy = S["cord_hole"]
    base = [
        (26.4 * math.cos(a), 26.4 * math.sin(a), -31.8),   # Mbody's anchor tunnel
        (25.0 * math.cos(a), 25.0 * math.sin(a), -12.0),
        (22.0 * math.cos(a), 22.0 * math.sin(a), 25.0),
        (hx, hy, 50.0), (hx, hy, 63.0),                       # up through the ramp's cord hole
    ]
    if t < T_BAG[0]:
        return np.array(base + [tuple(attach)])
    corner = (0.6, -14.0, S["z_f"] + 2.6)                     # over the plate/ramp corner
    if t < T_LINES[0] + 0.4:
        return np.array(base + [corner, tuple(attach)])
    exit_ = (38.0, -8.0, 62.0)
    return np.array(base + [corner, exit_, tuple(attach)])


def shell_opacity(t: float) -> float:
    return 1.0 - 0.8 * smooth(seg(t, 6.0, 7.5)) + 0.8 * smooth(seg(t, 15.6, 16.8))


def sway(t: float) -> np.ndarray:
    a = 2.2 * smooth(seg(t, T_INFL[1], T_INFL[1] + 2.0)) * math.sin(2 * math.pi * (t - T_INFL[1]) / 3.4)
    pivot = apply(NOSE_TO_ASM, np.array([[42.0, 0.0, 1500.0]]))[0]
    return rot((math.cos(math.radians(PHI + 90)), math.sin(math.radians(PHI + 90)), 0), a, pivot)


# --- captions ------------------------------------------------------------------------------------


class Overlay:
    def __init__(self, w: int, h: int):
        k = h / 1080
        self.w, self.h, self.k = w, h, k
        self.f_title = ImageFont.truetype(str(FONTS / "Oswald-Variable.ttf"), int(46 * k))
        self.f_big = ImageFont.truetype(str(FONTS / "Oswald-Variable.ttf"), int(120 * k))
        self.f_num = ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), int(30 * k))
        self.f_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", int(30 * k))
        self.f_small = ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), int(26 * k))

    def draw(self, img: np.ndarray, t: float) -> np.ndarray:
        im = Image.fromarray(img).convert("RGBA")
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        k = self.k
        for t0, t1, num, title, body in CAPTIONS:
            a = min(seg(t, t0, t0 + 0.3), 1 - seg(t, t1 - 0.3, t1))
            if a <= 0:
                continue
            x0, y1 = int(70 * k), self.h - int(70 * k)
            tw = d.textlength(body, font=self.f_body)
            box = (x0 - int(28 * k), y1 - int(132 * k), x0 + int(max(tw, 520 * k)) + int(28 * k), y1 + int(18 * k))
            d.rounded_rectangle(box, radius=int(10 * k), fill=(12, 16, 24, int(175 * a)))
            d.text((x0, y1 - int(118 * k)), num, font=self.f_num, fill=(226, 120, 80, int(255 * a)))
            d.text((x0 + int(62 * k), y1 - int(128 * k)), title, font=self.f_title, fill=(255, 255, 255, int(255 * a)))
            d.text((x0, y1 - int(46 * k)), body, font=self.f_body, fill=(222, 228, 236, int(255 * a)))
        a = min(seg(t, 0.3, 0.9), 1 - seg(t, 3.4, 4.0))
        if a > 0:
            self._centre(d, "HELIOS", self.f_big, int(self.h * 0.36), a)
            self._centre(d, "side-door parachute deployment", self.f_title, int(self.h * 0.36 + 150 * k), a)
        a = min(seg(t, 22.0, 22.8), 1.0)
        if a > 0:
            x0, y0 = int(0.07 * self.w), int(0.34 * self.h)
            d.text((x0, y0), "HELIOS SIDE-DOOR NOSE", font=self.f_title, fill=(255, 255, 255, int(255 * a)))
            for i, line in enumerate(("MG90S servo latch", "2 ejection springs", "254 cm\u00b3 chute bay",
                                      "cord anchored in the airframe", "45 checks pass")):
                col = (226, 120, 80) if i == 4 else (222, 228, 236)
                d.text((x0, y0 + int((78 + 44 * i) * k)), line, font=self.f_small, fill=(*col, int(255 * a)))
        out = Image.alpha_composite(im, layer).convert("RGB")
        fade = 1 - seg(t, DURATION - 0.7, DURATION)
        arr = np.asarray(out)
        return (arr * fade).astype(np.uint8) if fade < 1 else arr

    def _centre(self, d, text, font, y, a):
        w = d.textlength(text, font=font)
        d.text(((self.w - w) / 2, y), text, font=font, fill=(255, 255, 255, int(255 * a)))


# --- main ------------------------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default="")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default=str(HERE / "helios_side_door_deploy.mp4"))
    args = ap.parse_args()
    w, h = int(1920 * args.scale) // 2 * 2, int(1080 * args.scale) // 2 * 2

    pl = pv.Plotter(off_screen=True, window_size=(w, h))
    pl.set_background("#121a26", top="#33465f")
    pl.enable_depth_peeling(number_of_peels=8)
    pl.enable_anti_aliasing("ssaa")
    pl.remove_all_lights()
    for pos, inten, col in (((1.0, 1.4, 1.2), 0.85, "#fff4e6"), ((-1.5, -0.3, 0.4), 0.35, "#cfe0ff"),
                            ((0.0, 0.2, -1.0), 0.45, "#ffffff")):
        lt = pv.Light(position=pos, focal_point=(0, 0, 0), intensity=inten, color=col, light_type="camera light")
        pl.add_light(lt)
    look = dict(smooth_shading=True, split_sharp_edges=True, feature_angle=35, specular=0.35, specular_power=24,
                ambient=0.18, diffuse=0.85)

    # rigid parts
    shells = []
    for mesh, kind in rocket_without_cone():
        act = pl.add_mesh(mesh, color=AIRFRAME, **look)
        if kind == "mbody":
            shells.append(act)
    rocket_acts = [a for a in pl.actors.values()]
    housing = pl.add_mesh(load(NOSE / "STL" / "helios_nose_door_housing.stl"), color=ORANGE, **look)
    door_mesh = load(NOSE / "STL" / "helios_nose_door.stl").translate((0, 0, S["z_d0"]))
    door = pl.add_mesh(door_mesh, color=ORANGE, **look)
    door_com = np.array(door_mesh.center_of_mass())
    shells += [housing, door]
    servo = pl.add_mesh(load(HERE / "meshes" / "servo_body.stl"), color="#2E4A7D", **look)
    horn = pl.add_mesh(load(HERE / "meshes" / "horn.stl"), color="#F5F5F5", **look)
    screws = pl.add_mesh(load(HERE / "meshes" / "screws.stl"), color="#C9A44C", **look)

    # deforming parts
    sp_faces = tube_faces(SPRING_N, SPRING_SIDES)
    springs = []
    for y in (-S["spring_y"], S["spring_y"]):
        m = pv.PolyData(tube_points(spring_path(11.4, y), 0.3, SPRING_SIDES), sp_faces)
        springs.append((m, y, pl.add_mesh(m, color="#C7CDD4", specular=0.9, specular_power=40, smooth_shading=True)))
    bag_mesh, bag_attach = bundle_mesh()
    bag = pl.add_mesh(bag_mesh, scalars="gore", cmap=[RED, WHITE], show_scalar_bar=False, smooth_shading=True,
                      ambient=0.25, diffuse=0.8, specular=0.1)
    cord_n, cord_sides = 220, 10
    cord_mesh = pv.PolyData(tube_points(resample(cord_ctrl(0, bag_attach), cord_n), 2.0, cord_sides),
                            tube_faces(cord_n, cord_sides))
    cord = pl.add_mesh(cord_mesh, color=KEVLAR, smooth_shading=True, specular=0.3, ambient=0.25)
    can_mesh = canopy_mesh()
    canopy = pl.add_mesh(can_mesh, scalars="gore", cmap=[RED, WHITE], show_scalar_bar=False, smooth_shading=True,
                         ambient=0.3, diffuse=0.75, specular=0.15)
    lines_mesh = pv.PolyData(np.zeros((2 * GORES, 3)), lines=np.array([[2, 2 * i, 2 * i + 1] for i in range(GORES)]).ravel())
    lines = pl.add_mesh(lines_mesh, color="#EDEDED", line_width=max(1.5, 2.2 * args.scale), render_lines_as_tubes=True)

    overlay = Overlay(w, h)

    def frame(t: float) -> np.ndarray:
        world = sway(t)
        nose = world @ NOSE_TO_ASM
        for act in rocket_acts:
            act.user_matrix = world
        for act in (housing, servo, screws, cord, canopy, lines):
            act.user_matrix = nose
        arm = -S["unlock_deg"] * smooth(seg(t, *T_ARM))
        horn.user_matrix = nose @ rot((1, 0, 0), arm, (0, 0, S["shaft_z"]))
        dm = door_pose(t, door_com)
        door.user_matrix = nose @ dm
        door.visibility = t < T_SWING[1] + 2.6
        op = shell_opacity(t)
        for act in shells:
            act.prop.opacity = op
        for m, y, act in springs:
            m.points = tube_points(spring_path(spring_len(t, dm, y), y), 0.3, SPRING_SIDES)
            act.user_matrix = nose
        bag_m, group, u, s = chute_state(t)
        shrink = 1 - 0.85 * smooth(seg(t, T_LINES[0], T_LINES[0] + 0.35))
        centre = apply(bag_m, np.array([[3.0, 0.0, 90.0]]))[0]
        bag.user_matrix = nose @ trans(centre) @ np.diag([shrink, shrink, shrink, 1.0]) @ trans(-centre) @ bag_m
        bag.visibility = t < T_LINES[0] + 0.35
        bag.prop.opacity = 1.0 - 0.5 * smooth(seg(t, 6.0, 7.5)) + 0.5 * smooth(seg(t, T_BAG[0], T_BAG[0] + 0.8))
        show_can = t >= T_LINES[0]
        canopy.visibility = lines.visibility = show_can
        if show_can:
            pts, ends = canopy_points(u, s)
            can_mesh.points = apply(group, pts)
            q = apply(group, np.zeros((1, 3)))[0]
            seg_pts = np.empty((2 * GORES, 3))
            seg_pts[0::2] = q
            seg_pts[1::2] = apply(group, ends)
            lines_mesh.points = seg_pts
            attach = q
        else:
            attach = apply(bag_m, bag_attach[None])[0]
        cord_mesh.points = tube_points(resample(cord_ctrl(t, attach), cord_n), 2.0, cord_sides)
        eye, target = camera_at(t)
        pl.camera.position, pl.camera.focal_point, pl.camera.up = eye, target, (0, 0, 1)
        pl.camera.view_angle = FOV
        pl.renderer.ResetCameraClippingRange()
        pl.render()
        return overlay.draw(pl.screenshot(return_img=True), t)

    if args.stills:
        for ts in args.stills.split(","):
            t = float(ts)
            Image.fromarray(frame(t)).save(HERE / f"still_{t:05.1f}.png")
            print("still", t)
        return
    n = int(DURATION * args.fps)
    writer = imageio.get_writer(args.out, fps=args.fps, codec="libx264", macro_block_size=1,
                                ffmpeg_params=["-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p"])
    t_start = time.time()
    for i in range(n):
        writer.append_data(frame(i / args.fps))
        if i % 30 == 0:
            el = time.time() - t_start
            print(f"frame {i}/{n}  {el:.0f}s elapsed, {el / (i + 1):.2f}s/frame", flush=True)
    writer.close()
    print("wrote", args.out)


if __name__ == "__main__":
    main()
