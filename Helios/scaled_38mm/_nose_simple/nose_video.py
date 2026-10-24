"""Renders the mechanism working, as video.  Nothing here defines geometry.

Every solid comes from an already-exported STL in ./out, placed by the SAME maths
the assembly uses -- `nose_assembly.hinge_m` and `nose_assembly.rz_m` are imported,
not reimplemented -- so a video that shows the mechanism working is evidence about
the real parts and not about a second, hand-written model that happens to look
similar.  That distinction matters: the whole reason this file exists is that a
latch was wrong for a long time while every picture of it looked fine.

WHY THERE IS A RASTERISER IN HERE
---------------------------------
The `render` skill's snapshot CLI draws stills, and its GIF mode animates
`.step.js` sidecar PARAMETERS -- neither one animates two coupled rigid-body DOFs
(servo sweep, then hinge opening) with a section plane that has to stay put while
the parts move through it.  Rather than re-describe the geometry as a JS STEP
module just to get it to move, this file rasterises the meshes directly:

    z-buffer, flat shading, backface culling, 2x supersampling, and an edge pass
    that darkens pixels where the part id or the depth jumps.

That edge pass is doing more work than it looks like.  Flat-shaded ABS-coloured
parts inside a bore read as one grey blob; outlines are what make it legible as
an assembly of separate pieces.

THE THREE SHOTS
---------------
    overview   exterior, slow orbit.  What the rocket does.
    section    cut at y = Y_CUT, looking at the cut face.  The hook's foot and
               the bar are COPLANAR in this plane and stacked in z, so this is the
               one view where you can see the engagement itself.
    cutaway    ring and bulkhead cut away, half B hidden, arm and half A whole.
               The same event in 3D, so the sweep reads as a rotation.

Half B is hidden in `cutaway` on purpose and the frame says so.  Showing both
halves means the near one hides the mechanism, which is how the original drawing
managed to look convincing.

USAGE
-----
    python nose_video.py --shot section
    python nose_video.py --shot all --fps 30
    python nose_video.py --shot section --shell out/_before_half_shell.stl \
                         --tag before --caption-set before
"""

from __future__ import annotations

import argparse
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon

import nose_assembly as A
import nose_params as P

# --------------------------------------------------------------------------
# the timeline, in seconds.  One clock drives both DOFs and the camera.
# --------------------------------------------------------------------------

T_HOLD_SHUT = 1.3          # sit there latched, so the still frame is readable
T_SWEEP = 1.1              # servo drives the bar out from under the hooks
T_DWELL = 0.25             # nothing moves; the springs have not won yet
T_OPEN = 1.9               # springs push the halves apart
T_HOLD_OPEN = 1.5
T_TOTAL = T_HOLD_SHUT + T_SWEEP + T_DWELL + T_OPEN + T_HOLD_OPEN

Y_CUT = (P.TONGUE_Y0 + P.TONGUE_Y1) / 2      # 1.65: straight through the hook

BG = np.array([0.086, 0.098, 0.118])         # near-black, so ABS greys separate


def _smooth(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def state(t: float) -> tuple[float, float, str, str]:
    """(open_deg, sweep_deg, phase, subtitle) at time t.

    The servo finishes its sweep BEFORE the halves move, with T_DWELL of nothing
    in between.  That gap is not padding -- it is the claim being made: the bar
    has to be fully clear before the springs do anything, because if the two
    overlapped in time you could not tell from the picture whether the bar was
    released by the servo or shoved aside by the springs.
    """
    t0 = T_HOLD_SHUT
    t1 = t0 + T_SWEEP
    t2 = t1 + T_DWELL
    t3 = t2 + T_OPEN
    if t < t0:
        return 0.0, 0.0, "LATCHED", "the bar sits in the throat of both hooks"
    if t < t1:
        u = _smooth((t - t0) / T_SWEEP)
        return 0.0, P.LATCH_SWEEP * u, "SERVO SWEEPS", \
            f"{P.LATCH_SWEEP:.0f} deg is all it takes to clear the hooks"
    if t < t2:
        return 0.0, P.LATCH_SWEEP, "RELEASED", "nothing is holding the halves now"
    if t < t3:
        u = (t - t2) / T_OPEN
        return A.OPEN_MAX * (1.0 - (1.0 - u) ** 2.2), P.LATCH_SWEEP, \
            "SPRINGS OPEN IT", \
            f"two torsion springs, {P.TORSION_MOMENT_EACH:.1f} N-mm each"
    return A.OPEN_MAX, P.LATCH_SWEEP, "OPEN", "the 30 in chute leaves straight up"


CAPTIONS_BEFORE = {
    "LATCHED": ("NOT LATCHED", "the blade only RESTS on the bar"),
    "SERVO SWEEPS": ("SERVO SWEEPS", "too late -- the blade already left"),
    "RELEASED": ("RELEASED", "this never held anything shut"),
    "SPRINGS OPEN IT": ("IT WAS ALWAYS OPENING", "the blade lifts straight off the bar"),
    "OPEN": ("OPEN", "the springs never met any resistance"),
}


# --------------------------------------------------------------------------
# the scene: one entry per solid, with the transform it gets at time t
# --------------------------------------------------------------------------

class Body:
    def __init__(self, name, mesh, colour, xform, highlight=None, hl_colour=None):
        self.name = name
        self.mesh = mesh
        self.colour = np.asarray(colour, dtype=float)
        self.xform = xform                 # (open_deg, sweep_deg) -> 4x4
        self.highlight = highlight         # predicate on LOCAL centroids -> bool mask
        self.hl_colour = None if hl_colour is None else np.asarray(hl_colour, float)


def _servo_mesh():
    """MG90S envelope, from nose_params, mirroring nose_assembly._servo().

    Rebuilt with trimesh boxes instead of importing the build123d body because
    that body is a reference solid inside an assembly, not an exported STL.  The
    NUMBERS come from nose_params either way, including the asymmetric case: it
    runs SERVO_BODY_Y, not +-SERVO_W/2 about the shaft.
    """
    hw = P.SERVO_W / 2
    y0, y1 = P.SERVO_BODY_Y
    parts = [trimesh.creation.box(
        extents=(P.SERVO_W, y1 - y0, P.SERVO_H),
        transform=trimesh.transformations.translation_matrix(
            (0, (y0 + y1) / 2, P.Z_SERVO_BOT + P.SERVO_H / 2)))]
    ya = P.SERVO_HOLE_Y[0] - A.FLANGE_EAR
    yb = P.SERVO_HOLE_Y[1] + A.FLANGE_EAR
    parts.append(trimesh.creation.box(
        extents=(P.SERVO_W, yb - ya, A.FLANGE_T),
        transform=trimesh.transformations.translation_matrix(
            (0, (ya + yb) / 2, P.Z_FLANGE_FACE + A.FLANGE_T / 2))))
    parts.append(trimesh.creation.cylinder(
        radius=P.HORN_HUB_D / 2, height=P.HORN_HUB_H, sections=32,
        transform=trimesh.transformations.translation_matrix(
            (0, 0, P.Z_SERVO_TOP + P.HORN_HUB_H / 2))))
    # the DOUBLE-arm blade, 36 mm tip to tip -- the same envelope nose_assembly draws
    # and the same one latch_arm.py cuts its 36.8 mm slot for.  Extruded from the
    # MEASURED outline, not a box: 7.2 wide across the middle 22.5 mm, 4.1 at the
    # tips.  A box here would quietly disagree with the assembly's own reference horn.
    hw_mid, hw_tip = P.horn_lever_w(0.0) / 2, P.horn_lever_w(P.HORN_LEVER_R) / 2
    parts.append(trimesh.creation.extrude_polygon(
        Polygon([(-P.HORN_LEVER_R, hw_tip), (-P.HORN_LEVER_W_FULL, hw_mid),
                 (P.HORN_LEVER_W_FULL, hw_mid), (P.HORN_LEVER_R, hw_tip),
                 (P.HORN_LEVER_R, -hw_tip), (P.HORN_LEVER_W_FULL, -hw_mid),
                 (-P.HORN_LEVER_W_FULL, -hw_mid), (-P.HORN_LEVER_R, -hw_tip)]),
        P.HORN_BLADE_T,
        transform=trimesh.transformations.translation_matrix(
            (0, 0, P.Z_SERVO_TOP + P.HORN_HUB_H - P.HORN_BLADE_T))))
    return trimesh.util.concatenate(parts)


def _pin_mesh():
    out = []
    for sign in (+1, -1):
        m = trimesh.creation.cylinder(radius=P.D_PIN / 2, height=P.PIN_LEN,
                                      sections=20)
        m.apply_transform(trimesh.transformations.rotation_matrix(
            math.pi / 2, (0, 1, 0)))
        m.apply_translation((0, sign * P.Y_PIN, P.Z_PIN))
        out.append(m)
    return trimesh.util.concatenate(out)


def _hook_mask(c: np.ndarray) -> np.ndarray:
    """Triangles of a half shell that belong to the latch HOOK.

    Selected by LOCAL position, so it follows the part when the hinge moves it.
    The x window is deliberately wider than TONGUE_X0..X1 -- the hook's web and
    foot live outboard and inboard of the old flat blade -- and the z ceiling is
    the shell root, which is where the hook stops and the wall begins.
    """
    return ((np.abs(c[:, 0]) > 18.0) & (np.abs(c[:, 0]) < 27.5)
            & (c[:, 2] < P.Z_SHELL_ROOT + 0.5))


def scene(shell_path: str, arm_path: str, shot: str) -> list[Body]:
    ring = trimesh.load("out/base_ring.stl")
    bulk = trimesh.load("out/bulkhead.stl")
    arm = trimesh.load(arm_path)
    shell = trimesh.load(shell_path)

    rz180 = trimesh.transformations.rotation_matrix(math.pi, (0, 0, 1))

    bodies = [
        Body("base_ring", ring, (0.44, 0.47, 0.53), lambda o, s: np.eye(4)),
        Body("bulkhead", bulk, (0.62, 0.60, 0.55), lambda o, s: np.eye(4)),
        Body("servo", _servo_mesh(), (0.14, 0.15, 0.17), lambda o, s: np.eye(4)),
        Body("pins", _pin_mesh(), (0.70, 0.72, 0.76), lambda o, s: np.eye(4)),
        Body("latch_arm", arm, (0.95, 0.47, 0.13), lambda o, s: A.rz_m(s)),
        Body("half_A", shell, (0.58, 0.66, 0.76),
             lambda o, s: A.hinge_m(o, +1),
             highlight=_hook_mask, hl_colour=(0.92, 0.27, 0.24)),
    ]
    if shot != "cutaway":
        bodies.append(Body("half_B", shell, (0.46, 0.53, 0.62),
                           lambda o, s: A.hinge_m(o, -1) @ rz180,
                           highlight=_hook_mask, hl_colour=(0.78, 0.22, 0.20)))
    return bodies


# --------------------------------------------------------------------------
# camera
# --------------------------------------------------------------------------

class Cam:
    def __init__(self, eye, target, fov_deg, up=(0, 0, 1)):
        self.eye = np.asarray(eye, float)
        self.target = np.asarray(target, float)
        self.fov = float(fov_deg)
        f = np.asarray(target, float) - self.eye
        f /= np.linalg.norm(f)
        r = np.cross(f, np.asarray(up, float))
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        V = np.eye(4)
        V[0, :3], V[1, :3], V[2, :3] = r, u, -f
        V[:3, 3] = -V[:3, :3] @ self.eye
        self.V = V

    def project(self, pts: np.ndarray, W: int, H: int):
        """World points -> (px, py, depth).  depth is distance along the axis."""
        p = np.atleast_2d(np.asarray(pts, float))
        v = p @ self.V[:3, :3].T + self.V[:3, 3]
        d = -v[:, 2]
        f = 1.0 / math.tan(math.radians(self.fov) / 2.0)
        safe = np.where(np.abs(d) < 1e-6, 1e-6, d)
        px = ((v[:, 0] * f / (W / H)) / safe + 1.0) * 0.5 * W
        py = (1.0 - (v[:, 1] * f) / safe) * 0.5 * H
        return px, py, d


def orbit(az_deg, el_deg, dist, target):
    a, e = math.radians(az_deg), math.radians(el_deg)
    t = np.asarray(target, float)
    return t + dist * np.array([math.cos(e) * math.cos(a),
                                math.cos(e) * math.sin(a),
                                math.sin(e)])


def camera_for(shot: str, t: float, open_deg: float) -> Cam:
    """The camera for one shot at one instant.

    The section and cutaway cameras DOLLY OUT as the halves open.  Held still they
    would be a tight shot of an empty bore two seconds in, because the thing they
    were framing has left at 110 deg.
    """
    u = _smooth(min(max((t - (T_HOLD_SHUT + T_SWEEP + T_DWELL)) / T_OPEN, 0.0), 1.0))
    if shot == "overview":
        # at OPEN_MAX the halves have swung PAST horizontal -- a tip ends up at
        # y ~ 230, z ~ 22 -- so the envelope roughly triples.  Held at the closed
        # framing the halves would simply leave the frame.
        tgt = np.array([0.0, 0.0, 128.0]) + u * np.array([0.0, 0.0, -18.0])
        az = 28.0 + 46.0 * (t / T_TOTAL)
        return Cam(orbit(az, 13.0 + 5.0 * u, 470.0 + u * 510.0, tgt), tgt, 31.0)
    if shot == "section":
        tgt = np.array([0.0, 0.0, 42.0]) + u * np.array([0.0, 12.0, 20.0])
        az = -74.0 + 7.0 * (t / T_TOTAL)
        return Cam(orbit(az, 9.0 + 6.0 * u, 255.0 + u * 150.0, tgt), tgt,
                   13.0 + 2.0 * u)
    tgt = np.array([0.0, 0.0, 43.0]) + u * np.array([0.0, 14.0, 20.0])
    az = -46.0 + 20.0 * (t / T_TOTAL)
    return Cam(orbit(az, 21.0 - 3.0 * u, 245.0 + u * 160.0, tgt), tgt,
               16.0 + 2.0 * u)


SECTIONS = {                       # shot -> (origin, normal, which bodies)
    "overview": None,
    "section": ((0.0, Y_CUT, 0.0), (0.0, 1.0, 0.0), None),
    "cutaway": ((0.0, -5.0, 0.0), (0.0, 1.0, 0.0), {"base_ring", "bulkhead"}),
}


# --------------------------------------------------------------------------
# rasteriser
# --------------------------------------------------------------------------

LIGHTS = ((np.array([-0.45, -0.72, 0.53]), 0.72),
          (np.array([0.66, 0.30, 0.69]), 0.42),
          (np.array([0.10, 0.55, -0.83]), 0.16))
AMBIENT = 0.26


def _tris(bodies, open_deg, sweep_deg, section):
    """World-space triangles + per-triangle colour + per-triangle body id."""
    V, C, I = [], [], []
    for i, b in enumerate(bodies):
        m = b.mesh.copy()
        m.apply_transform(b.xform(open_deg, sweep_deg))
        col = np.tile(b.colour, (len(m.faces), 1))
        if b.highlight is not None:
            local = b.mesh.triangles.mean(axis=1)
            col[b.highlight(local)] = b.hl_colour
        if section is not None:
            origin, normal, only = section
            if only is None or b.name in only:
                keep = m.slice_plane(origin, normal, cap=True)
                if keep is None or len(keep.faces) == 0:
                    continue
                # slice_plane rebuilds the topology, so face colours cannot be
                # carried across.  Re-derive the highlight from world centroids
                # instead, mapped back through the body's own transform.
                col = np.tile(b.colour, (len(keep.faces), 1))
                if b.highlight is not None:
                    inv = np.linalg.inv(b.xform(open_deg, sweep_deg))
                    wc = keep.triangles.mean(axis=1)
                    lc = wc @ inv[:3, :3].T + inv[:3, 3]
                    col[b.highlight(lc)] = b.hl_colour
                m = keep
        V.append(m.triangles)
        C.append(col)
        I.append(np.full(len(m.faces), i + 1, dtype=np.int32))
    return np.concatenate(V), np.concatenate(C), np.concatenate(I)


def raster(verts, cols, ids, cam, W, H):
    """Flat-shaded z-buffer.  Returns (rgb HxWx3 float, depth HxW, id HxW)."""
    img = np.tile(BG, (H, W, 1)).astype(np.float32)
    zb = np.full((H, W), np.inf, dtype=np.float32)
    ib = np.zeros((H, W), dtype=np.int32)

    e0 = verts[:, 1] - verts[:, 0]
    e1 = verts[:, 2] - verts[:, 0]
    n = np.cross(e0, e1)
    ln = np.linalg.norm(n, axis=1)
    live = ln > 1e-12
    n = n / np.where(ln[:, None] == 0, 1.0, ln[:, None])

    cen = verts.mean(axis=1)
    view = cen - cam.eye
    live &= (np.einsum("ij,ij->i", n, view) < 0.0)          # backface cull

    shade = np.full(len(verts), AMBIENT, dtype=np.float32)
    for d, w in LIGHTS:
        d = d / np.linalg.norm(d)
        shade += w * np.clip(n @ d, 0.0, None)
    rgb = np.clip(cols * shade[:, None], 0.0, 1.0).astype(np.float32)

    flat = verts.reshape(-1, 3)
    px, py, dep = cam.project(flat, W, H)
    px = px.reshape(-1, 3)
    py = py.reshape(-1, 3)
    dep = dep.reshape(-1, 3)
    live &= (dep > 1.0).all(axis=1)
    live &= (px.max(1) >= 0) & (px.min(1) < W) & (py.max(1) >= 0) & (py.min(1) < H)

    idx = np.nonzero(live)[0]
    order = np.argsort(-dep[idx].min(axis=1))               # far to near: fewer writes
    invd = 1.0 / dep

    for k in idx[order]:
        x0 = max(int(np.floor(px[k].min())), 0)
        x1 = min(int(np.ceil(px[k].max())) + 1, W)
        y0 = max(int(np.floor(py[k].min())), 0)
        y1 = min(int(np.ceil(py[k].max())) + 1, H)
        if x1 <= x0 or y1 <= y0:
            continue
        ax, ay = px[k, 0], py[k, 0]
        bx, by = px[k, 1], py[k, 1]
        cx, cy = px[k, 2], py[k, 2]
        area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(area) < 1e-9:
            continue
        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        w0 = ((bx - ax) * (gy - ay) - (gx - ax) * (by - ay)) / area
        w1 = ((gx - ax) * (cy - ay) - (cx - ax) * (gy - ay)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        # 1/z is what varies linearly in screen space; interpolating z does not.
        iz = w2 * invd[k, 0] + w1 * invd[k, 1] + w0 * invd[k, 2]
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(iz > 0, 1.0 / iz, np.inf)
        sub = zb[y0:y1, x0:x1]
        win = inside & (z < sub)
        if not win.any():
            continue
        sub[win] = z[win]
        img[y0:y1, x0:x1][win] = rgb[k]
        ib[y0:y1, x0:x1][win] = ids[k]
    return img, zb, ib


def outline(img, zb, ib, strength=0.55):
    """Darken pixels where the body id changes or the depth gradient jumps.

    The depth term is normalised by the local depth so a 0.3 mm step reads the
    same at the tip of the cone as it does 400 mm from the camera.
    """
    d = np.where(np.isfinite(zb), zb, np.nanmax(zb[np.isfinite(zb)]) if
                 np.isfinite(zb).any() else 1.0)
    edge = np.zeros(d.shape, bool)
    for sh in ((0, 1), (1, 0)):
        a = np.roll(ib, sh, axis=(0, 1))
        edge |= (a != ib)
        rel = np.abs(np.roll(d, sh, axis=(0, 1)) - d) / np.maximum(d, 1e-6)
        edge |= rel > 0.0035
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = False
    out = img.copy()
    out[edge] *= (1.0 - strength)
    return out


# --------------------------------------------------------------------------
# overlay
# --------------------------------------------------------------------------

def _font(size, bold=True):
    for name in (("segoeuib.ttf", "segoeui.ttf") if bold else
                 ("segoeui.ttf", "segoeuib.ttf")) + ("consolab.ttf",):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
        except OSError:
            pass
    return ImageFont.load_default()


CALLOUTS = {                       # phase -> [(label, world anchor xyz)]
    "LATCHED": [
        ("LATCH ARM on the servo shaft", (13.0, 0.0, 43.0)),
        # getattr, because this file must still render the BEFORE clip from the
        # old geometry, which has no hook parameters at all.  The names are the
        # ones the fixed nose_params actually declares -- HOOK_X_IN and
        # Z_LATCH_FACE.  An earlier draft asked for Z_HOOK_TOP, which never
        # existed, so the default silently supplied the right number for the
        # wrong reason and would have gone on doing so if the value ever moved.
        ("HOOK pulls UP under the bar",
         (getattr(P, "HOOK_X_IN", 21.0) + 0.9, Y_CUT,
          getattr(P, "Z_LATCH_FACE", 38.6) - 1.2)),
        ("bulkhead THRUST PAD reacts DOWN", (8.2, 0.0, 47.2)),
        ("MG90S servo", (0.0, 4.0, 26.0)),
    ],
}
CALLOUTS_BEFORE = {
    "NOT LATCHED": [
        ("LATCH ARM -- ends here, r 23.35", (21.0, 0.0, 43.0)),
        ("BLADE only RESTS on top", (23.0, Y_CUT, 49.5)),
        ("MG90S servo", (0.0, 4.0, 26.0)),
    ],
}


def annotate(frame: Image.Image, shot, t, open_deg, sweep_deg, cam,
             captions=None):
    W, H = frame.size
    d = ImageDraw.Draw(frame, "RGBA")
    _, _, phase, sub = state(t)
    if captions:
        phase, sub = captions.get(phase, (phase, sub))

    f_title = _font(max(20, H // 22))
    f_sub = _font(max(14, H // 36), bold=False)
    f_hud = _font(max(13, H // 44), bold=False)
    f_call = _font(max(12, H // 52), bold=False)

    d.rectangle([0, 0, W, int(H * 0.145)], fill=(10, 12, 15, 205))
    d.text((int(W * 0.028), int(H * 0.022)), phase, font=f_title,
           fill=(255, 255, 255, 255))
    d.text((int(W * 0.028), int(H * 0.022) + f_title.size + 6), sub, font=f_sub,
           fill=(176, 190, 206, 255))

    shot_label = {"overview": "EXTERIOR", "section": f"SECTION  y = {Y_CUT:.2f} mm",
                  "cutaway": "CUTAWAY  ring + bulkhead removed, half B hidden"}[shot]
    tw = d.textlength(shot_label, font=f_hud)
    d.text((W - tw - int(W * 0.028), int(H * 0.032)), shot_label, font=f_hud,
           fill=(140, 152, 168, 255))

    hud = [f"servo   {sweep_deg:5.1f} deg  of {P.LATCH_SWEEP:.0f}",
           f"opening {open_deg:5.1f} deg  of {A.OPEN_MAX:.0f}",
           f"t = {t:4.2f} s"]
    y = H - int(H * 0.035) - len(hud) * (f_hud.size + 5)
    d.rectangle([int(W * 0.020), y - 9,
                 int(W * 0.020) + int(d.textlength(hud[1], font=f_hud)) + 24,
                 H - int(H * 0.024)], fill=(10, 12, 15, 165))
    for line in hud:
        d.text((int(W * 0.032), y), line, font=f_hud, fill=(206, 216, 228, 255))
        y += f_hud.size + 5

    table = CALLOUTS_BEFORE if captions else CALLOUTS
    for label, anchor in table.get(phase, []):
        if shot == "overview":
            break
        px, py, dep = cam.project(np.array([anchor]), W, H)
        if dep[0] <= 1.0 or not (0 < px[0] < W and 0 < py[0] < H):
            continue
        x, yy = float(px[0]), float(py[0])
        left = x < W * 0.5
        lx = x + (-1 if left else 1) * int(W * 0.055)
        ly = yy - int(H * 0.055)
        d.ellipse([x - 4, yy - 4, x + 4, yy + 4], outline=(240, 240, 240, 230),
                  width=2)
        tw = d.textlength(label, font=f_call)
        tx = lx - tw if left else lx
        # clamp INTO the frame, then redraw the leader to wherever the box ended
        # up.  Without this a callout on the far side of a wide shot walks off the
        # edge and the label is unreadable in exactly the frame that needed it.
        tx = min(max(tx, int(W * 0.012)), W - tw - int(W * 0.012))
        ly = min(max(ly, int(H * 0.18)), H - int(H * 0.10))
        anchor_x = tx + tw if (tx + tw) < x else tx
        d.line([x, yy, anchor_x, ly + 2], fill=(240, 240, 240, 220), width=2)
        d.rectangle([tx - 6, ly - f_call.size - 6, tx + tw + 6, ly + 5],
                    fill=(10, 12, 15, 195))
        d.text((tx, ly - f_call.size - 2), label, font=f_call,
               fill=(246, 248, 250, 255))
    return frame


def title_card(text, sub, W, H, hold_frames):
    im = Image.new("RGB", (W, H), tuple((BG * 255).astype(int)))
    d = ImageDraw.Draw(im)
    f1, f2 = _font(max(26, H // 15)), _font(max(15, H // 30), bold=False)
    tw = d.textlength(text, font=f1)
    d.text(((W - tw) / 2, H / 2 - f1.size), text, font=f1, fill=(255, 255, 255))
    tw = d.textlength(sub, font=f2)
    d.text(((W - tw) / 2, H / 2 + 10), sub, font=f2, fill=(150, 164, 180))
    return [np.asarray(im)] * hold_frames


# --------------------------------------------------------------------------

SHOT_TITLES = {
    "overview": ("HOW THE NOSE OPENS", "exterior view, one release cycle"),
    "section": ("HOW THE LATCH HOLDS",
                f"cut through the hook at y = {Y_CUT:.2f} mm"),
    "cutaway": ("THE SAME EVENT IN 3D", "ring and bulkhead cut away"),
}


def render_shot(shot, bodies, W, H, fps, ss, captions=None, title=True):
    frames = []
    if title:
        t1, t2 = SHOT_TITLES[shot]
        if captions:
            t1 = "BEFORE THE FIX -- " + t1
        frames += title_card(t1, t2, W, H, int(fps * 1.1))
    n = int(round(T_TOTAL * fps))
    for i in range(n):
        t = i / fps
        o, s, _, _ = state(t)
        cam = camera_for(shot, t, o)
        v, c, ids = _tris(bodies, o, s, SECTIONS[shot])
        img, zb, ib = raster(v, c, ids, cam, W * ss, H * ss)
        img = outline(img, zb, ib)
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        if ss != 1:
            im = im.resize((W, H), Image.LANCZOS)
        frames.append(np.asarray(annotate(im, shot, t, o, s, cam, captions)))
        if (i + 1) % 10 == 0 or i + 1 == n:
            print(f"  {shot}: {i + 1}/{n} frames", flush=True)
    return frames


def write_mp4(frames, path, fps):
    import imageio.v2 as iio
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", "")
    w = iio.get_writer(path, fps=fps, codec="libx264", quality=8,
                       macro_block_size=1,
                       ffmpeg_params=["-pix_fmt", "yuv420p", "-preset", "slow"])
    for f in frames:
        w.append_data(f)
    w.close()
    print(f"wrote {path}  ({len(frames)} frames, {len(frames)/fps:.1f} s, "
          f"{os.path.getsize(path)/1e6:.2f} MB)")


def write_gif(frames, path, fps, width=560):
    ims = []
    for f in frames:
        im = Image.fromarray(f)
        im = im.resize((width, round(width * im.height / im.width)), Image.LANCZOS)
        ims.append(im.convert("P", palette=Image.ADAPTIVE, colors=128))
    ims[0].save(path, save_all=True, append_images=ims[1:],
                duration=int(1000 / fps), loop=0, optimize=True)
    print(f"wrote {path}  ({os.path.getsize(path)/1e6:.2f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="section",
                    choices=["overview", "section", "cutaway", "all"])
    ap.add_argument("--shell", default="out/half_shell.stl")
    ap.add_argument("--arm", default="out/latch_arm.stl")
    ap.add_argument("--out", default="out")
    ap.add_argument("--tag", default="")
    ap.add_argument("--caption-set", default="", choices=["", "before"])
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--ss", type=int, default=2, help="supersampling factor")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--frame", type=float, default=None,
                    help="render ONE frame at this time, to a png, and stop")
    a = ap.parse_args()

    caps = CAPTIONS_BEFORE if a.caption_set == "before" else None
    shots = ["overview", "section", "cutaway"] if a.shot == "all" else [a.shot]
    tag = ("_" + a.tag) if a.tag else ""

    if a.frame is not None:
        shot = shots[0]
        o, s, _, _ = state(a.frame)
        cam = camera_for(shot, a.frame, o)
        v, c, ids = _tris(scene(a.shell, a.arm, shot), o, s, SECTIONS[shot])
        img, zb, ib = raster(v, c, ids, cam, a.width * a.ss, a.height * a.ss)
        im = Image.fromarray(
            (np.clip(outline(img, zb, ib), 0, 1) * 255).astype(np.uint8))
        if a.ss != 1:
            im = im.resize((a.width, a.height), Image.LANCZOS)
        p = f"{a.out}/_frame_{shot}{tag}_t{a.frame:.2f}.png"
        annotate(im, shot, a.frame, o, s, cam, caps).save(p)
        print("wrote", p, f"({len(v)} triangles)")
        return

    allf = []
    for shot in shots:
        fr = render_shot(shot, scene(a.shell, a.arm, shot), a.width, a.height,
                         a.fps, a.ss, caps)
        write_mp4(fr, f"{a.out}/nose_{shot}{tag}.mp4", a.fps)
        if a.gif:
            write_gif(fr, f"{a.out}/nose_{shot}{tag}.gif", a.fps)
        allf += fr
    if len(shots) > 1:
        write_mp4(allf, f"{a.out}/nose_mechanism{tag}.mp4", a.fps)


if __name__ == "__main__":
    main()
