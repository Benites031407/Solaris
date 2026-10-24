"""Clean footage of the Canarinho going together, for the /brag cut.

Nothing here defines geometry.  Every solid is an already-exported STL, placed by
`stack.py`, whose placement is CHECKED against `rocket_assembled_boattail.stl`
(244 stations, max radius disagreement 0.0001 mm) rather than asserted.

WHY THERE IS A RASTERISER IN HERE
---------------------------------
`_nose_simple/nose_video.py` already owns exactly the rasteriser this needs, and
importing it would have been the right thing to do.  It cannot be imported in
this tree: it pulls in `nose_params`, which loads `_clam/ogive_prof.npy`, and
`_clam/` is not present.  So the z-buffer below is deliberately the same
technique as that file's -- flat shading, backface culling, supersampling, and an
edge pass that darkens pixels where the part id or the depth jumps -- with the
same BG, lights and ambient, so this footage and the existing `nose_*.mp4` clips
cut together as one film.  The edge pass is what stops ABS-grey parts inside a
bore reading as a single grey blob.

The frames carry NO captions or telemetry.  Type is the cut's job, not the
renderer's.

    python shots.py --shot stack      exploded -> assembled, aft to forward
    python shots.py --shot bay        the avionics sled sliding into Mbody
    python shots.py --shot hero       the finished rocket, slow orbit
    python shots.py --shot all
"""

from __future__ import annotations

import argparse
import math
import os
import time
from pathlib import Path

import numpy as np
import trimesh

import stack as S

OUT = Path(__file__).resolve().parent / "clips"

# --- look, matched to nose_video.py so the clips intercut -------------------
BG = np.array([0.086, 0.098, 0.118])
LIGHTS = ((np.array([-0.45, -0.72, 0.53]), 0.72),
          (np.array([0.66, 0.30, 0.69]), 0.42),
          (np.array([0.10, 0.55, -0.83]), 0.16))
AMBIENT = 0.26

ABS_GREY = (0.62, 0.65, 0.70)
ABS_WARM = (0.70, 0.66, 0.60)          # alternate sections, so joints read
SLED = (0.55, 0.72, 0.85)              # the avionics sled, cool blue
SECTION_COLOURS = {
    "Tail":       (0.58, 0.61, 0.66),
    "Lower_Body": (0.66, 0.69, 0.74),
    "conection":  (0.78, 0.72, 0.58),   # the sleeve, warm: it is the joint
    "Mbody":      (0.66, 0.69, 0.74),
    "cone":       (0.72, 0.75, 0.80),
}


def ease(x: float) -> float:
    """Smootherstep.  Slow out of rest, slow into the seat."""
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


# --------------------------------------------------------------------------
# camera
# --------------------------------------------------------------------------

class Cam:
    def __init__(self, eye, target, fov_deg, up=(0, 0, 1), roll=0.0):
        self.eye = np.asarray(eye, float)
        self.target = np.asarray(target, float)
        self.fov = float(fov_deg)
        f = self.target - self.eye
        f /= np.linalg.norm(f)
        up = np.asarray(up, float)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            up = c * up + s * np.cross(f, up)
        r = np.cross(f, up)
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        V = np.eye(4)
        V[0, :3], V[1, :3], V[2, :3] = r, u, -f
        V[:3, 3] = -V[:3, :3] @ self.eye
        self.V = V

    def project(self, pts, W, H):
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


def lying_cam(az, el, dist, target, fov, roll=0.0):
    """A camera that lays the rocket ACROSS the frame, nose to the right.

    A 983 mm rocket stood upright in a 16:9 frame is a thin stripe with two
    thirds of the frame empty.  Choosing `up` perpendicular to the rocket axis
    puts the axis along screen x instead, so the subject uses the long side of
    the frame.  `roll` then tips it off-horizontal, which is what stops it
    looking like a parts diagram.
    """
    eye = orbit(az, el, dist, target)
    f = np.asarray(target, float) - eye
    f /= np.linalg.norm(f)
    up = np.cross((0.0, 0.0, 1.0), f)          # -> screen x runs along +z
    n = np.linalg.norm(up)
    up = np.array([0.0, 0.0, 1.0]) if n < 1e-9 else up / n
    return Cam(eye, target, fov, up=up, roll=roll)


# --------------------------------------------------------------------------
# rasteriser
# --------------------------------------------------------------------------

def tris(bodies, section=None):
    """World-space triangles, per-triangle colour, per-triangle body id."""
    V, C, I = [], [], []
    for i, (name, mesh, T, colour) in enumerate(bodies):
        m = mesh.copy()
        m.apply_transform(T)
        if section is not None:
            origin, normal, only = section
            if only is None or name in only:
                keep = m.slice_plane(origin, normal, cap=True)
                if keep is None or len(keep.faces) == 0:
                    continue
                m = keep
        V.append(m.triangles)
        C.append(np.tile(colour, (len(m.faces), 1)))
        I.append(np.full(len(m.faces), i + 1, dtype=np.int32))
    return np.concatenate(V), np.concatenate(C), np.concatenate(I)


def raster(verts, cols, ids, cam, W, H):
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
    live &= (np.einsum("ij,ij->i", n, cen - cam.eye) < 0.0)      # backface cull

    shade = np.full(len(verts), AMBIENT, dtype=np.float32)
    for d, w in LIGHTS:
        d = d / np.linalg.norm(d)
        shade += w * np.clip(n @ d, 0.0, None)
    rgb = np.clip(cols * shade[:, None], 0.0, 1.0).astype(np.float32)

    px, py, dep = cam.project(verts.reshape(-1, 3), W, H)
    px, py, dep = px.reshape(-1, 3), py.reshape(-1, 3), dep.reshape(-1, 3)
    live &= (dep > 1.0).all(axis=1)
    live &= (px.max(1) >= 0) & (px.min(1) < W) & (py.max(1) >= 0) & (py.min(1) < H)

    idx = np.nonzero(live)[0]
    order = np.argsort(-dep[idx].min(axis=1))
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
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        w0 = ((bx - ax) * (gy - ay) - (gx - ax) * (by - ay)) / area
        w1 = ((gx - ax) * (cy - ay) - (cx - ax) * (gy - ay)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
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
    finite = np.isfinite(zb)
    d = np.where(finite, zb, zb[finite].max() if finite.any() else 1.0)
    edge = np.zeros(d.shape, bool)
    for sh in ((0, 1), (1, 0)):
        edge |= (np.roll(ib, sh, axis=(0, 1)) != ib)
        rel = np.abs(np.roll(d, sh, axis=(0, 1)) - d) / np.maximum(d, 1e-6)
        edge |= rel > 0.0035
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = False
    out = img.copy()
    out[edge] *= (1.0 - strength)
    return out


# --------------------------------------------------------------------------
# shots
# --------------------------------------------------------------------------

TOTAL_Z = None          # filled from stack.stations()


def _sections():
    """(name, mesh, T_final, colour) for the five airframe sections."""
    out = []
    for name, mesh, T in S.placed():
        out.append((name, mesh, T, SECTION_COLOURS[name]))
    return out


def shot_stack(t: float, dur: float, secs):
    """Exploded -> assembled, seating aft to forward.

    Each section gets its own window, so there are four distinct joint arrivals
    to cut and to put a sound on, instead of one mushy convergence.
    """
    u = t / dur
    bodies = []
    n = len(secs)
    for i, (name, mesh, T, colour) in enumerate(secs):
        start = 0.06 + i * 0.15
        local = ease((u - start) / 0.28)      # last section seats by u = 0.94
        # Exploded, but only just: the sections are already spread over 983 mm of
        # axis, so a big axial fan puts the end ones outside the frame and the
        # shot stops being about one rocket.  A small axial gap plus an
        # alternating lift off the axis separates them and stays compact.
        axial = (i - (n - 1) / 2.0) * 88.0
        lateral = (86.0 if i % 2 else -86.0)
        k = 1.0 - local
        E = np.eye(4)
        E[2, 3] = axial * k
        E[1, 3] = lateral * k
        if k > 1e-6:                       # a little drift while it is loose
            R = trimesh.transformations.rotation_matrix(
                math.radians(9.0 * k) * (1 if i % 2 else -1), (0, 1, 0),
                point=(T @ np.array([0, 0, 0, 1.0]))[:3])
            E = E @ R
        bodies.append((name, mesh, E @ T, colour))

    # camera: wide on the whole stack, easing in as it closes up
    tgt = np.array([0.0, 0.0, TOTAL_Z * 0.5])
    a = ease(u)
    cam = lying_cam(az=34.0 + 26.0 * u, el=7.0 + 4.0 * a,
                    dist=1760.0 - 430.0 * a, target=tgt,
                    fov=31.0, roll=math.radians(-9.0 + 3.0 * a))
    return bodies, cam, None


def shot_bay(t: float, dur: float):
    """The ESP32 sled sliding forward into Mbody and seating on the bead.

    Mbody is cut at y = 0 so the bore and the sled inside it are both visible;
    the sled is left whole.  It enters from FORWARD, which is the only way it
    goes in -- the crown is larger than the bead's throat, so it can only be
    withdrawn forwards once the nose is off.
    """
    u = t / dur
    mbody = S.load("Mbody.stl")
    T_m = S.rot180x(S.stations()[3][4])            # Mbody, flipped, in place
    sled = trimesh.load(S.ROOT / "_avionics" / "out" / "bay_sled.stl",
                        force="mesh")

    # bay_sled.stl is already in station coordinates (s aft of the forward rim),
    # the same frame Mbody uses once flipped: s -> z_asm = MBODY_FWD - s.
    fwd = S.stations()[3][4]
    T_s = S.rot180x(fwd)
    travel = (1.0 - ease(min(u / 0.72, 1.0))) * 230.0     # slides aft into place
    E = np.eye(4)
    E[2, 3] = travel
    bodies = [("Mbody", mbody, T_m, SECTION_COLOURS["Mbody"]),
              ("bay_sled", sled, E @ T_s, SLED)]

    tgt = np.array([0.0, 0.0, fwd - 118.0 + 20.0 * ease(u)])
    cam = lying_cam(az=-64.0 + 16.0 * u, el=15.0 - 4.0 * ease(u),
                    dist=560.0 - 40.0 * ease(u), target=tgt,
                    fov=25.0, roll=math.radians(-6.0))
    return bodies, cam, ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), {"Mbody"})


# --- the nose, from the hinge recovered in nose.py -------------------------

# The release is SEQUENCED, and the order is the whole point: the bar has to be
# out from under the hooks before the springs can win.  Fractions of `dur`.
# The sweep is deliberately short: from outside, the bar is inside the shell and
# nothing visible moves during it, so a long sweep is just a still frame.  It is
# kept because the dwell after it -- bar clear, springs not yet winning -- is the
# beat that makes the release land.
NOSE_HOLD = 0.10          # latched, so the closed shape reads first
NOSE_SWEEP = 0.10         # servo drives the bar 30 deg
NOSE_DWELL = 0.04         # bar is clear, springs have not moved yet
NOSE_OPEN = 0.50          # halves swing to 100 deg
# remainder: hold open

_NOSE_CACHE = None


def _nose_motions():
    global _NOSE_CACHE
    if _NOSE_CACHE is None:
        import nose as N
        _NOSE_CACHE = N.recover()
    return _NOSE_CACHE


def shot_nose(t: float, dur: float):
    """The clamshell opening: bar sweeps, then both halves swing to 100 deg."""
    u = t / dur
    f_arm = ease((u - NOSE_HOLD) / NOSE_SWEEP)
    f_open = ease((u - (NOSE_HOLD + NOSE_SWEEP + NOSE_DWELL)) / NOSE_OPEN)

    bodies = []
    for i, m in enumerate(_nose_motions()):
        # the bar turns about z; the halves and what rides on them, about x
        f = f_arm if (m.moves and abs(m.axis[2]) > 0.9) else f_open
        big = len(m.mesh.faces) > 5000
        colour = (0.70, 0.73, 0.78) if big else (0.60, 0.63, 0.69)
        if m.moves and abs(m.axis[2]) > 0.9:
            colour = (0.85, 0.62, 0.38)          # the bar, so the sweep is visible
        bodies.append((f"n{i}", m.mesh, m.at(f), colour))

    o = f_open
    # Framing is set by the CLOSED shape, not the open one: the closed nose spans
    # z 0..248.97 (the README's apex), so at fov 30 the target needs 160 mm of
    # half-height to clear the tip -- dist 600, not 470, or the apex is cut off at
    # the top edge.  Then the camera pulls back and drops its target as the halves
    # swing, because held at the closed framing they leave the frame at 100 deg.
    tgt = np.array([0.0, 0.0, 126.0 - 55.0 * o])
    cam = Cam(orbit(24.0 + 34.0 * u, 11.0 + 6.0 * o,
                    600.0 + 150.0 * o, tgt),
              tgt, 30.0)
    return bodies, cam, None


def shot_hero(t: float, dur: float, secs):
    """The finished rocket, one slow orbit.  Nothing moves but the camera.

    Picks up exactly where `shot_stack` leaves off -- same target, same distance,
    az/el/roll continuing through -- so the outro can cut straight from the last
    joint seating without the rocket jumping to a new size or attitude.
    """
    u = t / dur
    tgt = np.array([0.0, 0.0, TOTAL_Z * 0.5])
    cam = lying_cam(az=60.0 + 34.0 * u, el=11.0 - 3.0 * ease(u),
                    dist=1330.0 - 60.0 * ease(u), target=tgt,
                    fov=31.0, roll=math.radians(-6.0 + 4.0 * u))
    return list(secs), cam, None


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def render(shot: str, W: int, H: int, fps: int, ss: int, dur: float):
    from PIL import Image
    global TOTAL_Z
    TOTAL_Z = S.stations()[-1][4]
    secs = _sections()

    n = int(round(dur * fps))
    frames = []
    t0 = time.time()
    for i in range(n):
        t = i / fps
        if shot == "stack":
            bodies, cam, sec = shot_stack(t, dur, secs)
        elif shot == "bay":
            bodies, cam, sec = shot_bay(t, dur)
        elif shot == "nose":
            bodies, cam, sec = shot_nose(t, dur)
        elif shot == "hero":
            bodies, cam, sec = shot_hero(t, dur, secs)
        else:
            raise SystemExit(f"unknown shot {shot}")
        v, c, ids = tris(bodies, sec)
        img, zb, ib = raster(v, c, ids, cam, W * ss, H * ss)
        img = outline(img, zb, ib)
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        if ss != 1:
            im = im.resize((W, H), Image.LANCZOS)
        frames.append(np.asarray(im))
        if (i + 1) % 5 == 0 or i + 1 == n:
            el = time.time() - t0
            print(f"  {shot}: {i+1}/{n}  {el:.0f}s elapsed, "
                  f"{el/(i+1):.2f}s/frame", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    write_mp4(frames, OUT / f"{shot}.mp4", fps)


def write_mp4(frames, path, fps):
    import imageio.v2 as iio
    # imageio already sets -pix_fmt yuv420p; passing it again only makes ffmpeg
    # warn about duplicate options.
    w = iio.get_writer(str(path), fps=fps, codec="libx264", quality=9,
                       macro_block_size=1, ffmpeg_params=["-preset", "slow"])
    for f in frames:
        w.append_data(f)
    w.close()
    print(f"wrote {path}  ({len(frames)} frames, {len(frames)/fps:.2f}s, "
          f"{os.path.getsize(path)/1e6:.2f} MB)")


DURATIONS = {"stack": 9.0, "bay": 4.5, "nose": 5.0, "hero": 4.0}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="all",
                    choices=["all", "stack", "bay", "nose", "hero"])
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--ss", type=int, default=2)
    ap.add_argument("--dur", type=float, default=None)
    ap.add_argument("--frames", type=int, default=None,
                    help="render only this many frames (bench/preview)")
    a = ap.parse_args()
    shots = (["stack", "bay", "nose", "hero"] if a.shot == "all" else [a.shot])
    for sh in shots:
        d = a.dur if a.dur else DURATIONS[sh]
        if a.frames:
            d = a.frames / a.fps
        render(sh, a.width, a.height, a.fps, a.ss, d)
