"""The clamshell nose opening, recovered from the two baked assemblies.

`nose_video.py` already animates this properly, from `nose_params` and
`nose_assembly.hinge_m`.  It cannot run in this tree: `nose_params` loads
`_clam/ogive_prof.npy` and `_clam/` is not present.  The existing
`out/nose_overview.mp4` is real footage of the same motion, but it is 1280x720
with captions and a telemetry box burnt in, so it can only be cropped to about
1048 px wide -- visibly soft next to native-1920 renders.

So the motion is recovered instead of re-derived.  `out/nose_closed.stl` and
`out/nose_open.stl` are the SAME assembly in two poses: both split into 14
components with identical vertex counts, face counts and volumes.  For each
component the rigid transform closed -> open is fitted with Kabsch, and a fit is
only accepted if its residual is at machine precision -- if the vertex ordering
did not correspond, the residual would be large and this module refuses to run
rather than animating a guess.

Each moving component's transform is then decomposed into a rotation of angle
theta about an axis through a point, so any intermediate pose is a rotation of
`f * theta` about that same axis.  That is exactly a hinge, which is what the
part is, and it is why the halves swing instead of sliding.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
NOSE_OUT = HERE.parents[1] / "_nose_simple" / "out"

FIT_TOL = 1e-4          # mm RMS; a real correspondence lands far below this


def _components(path: Path) -> list[trimesh.Trimesh]:
    m = trimesh.load(path, force="mesh")
    return m.split(only_watertight=False)


def _kabsch(P: np.ndarray, Q: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Rigid R,t with Q ~= P @ R.T + t, plus the RMS residual."""
    cp, cq = P.mean(0), Q.mean(0)
    H = (P - cp).T @ (Q - cq)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    t = cq - R @ cp
    res = np.sqrt(((P @ R.T + t - Q) ** 2).sum(axis=1).mean())
    return R, t, float(res)


def _axis_angle_point(R: np.ndarray, t: np.ndarray):
    """Decompose a rigid motion into (axis, angle, point-on-axis).

    For a pure hinge the motion has a fixed line; the point returned is the one
    on that line closest to the origin, found by least squares on (I-R)x = t.
    """
    ang = math.acos(min(max((np.trace(R) - 1.0) / 2.0, -1.0), 1.0))
    if ang < 1e-9:
        return np.array([0.0, 0.0, 1.0]), 0.0, np.zeros(3)
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    axis = w / np.linalg.norm(w)
    pt, *_ = np.linalg.lstsq(np.eye(3) - R, t, rcond=None)
    return axis, ang, pt


class Motion:
    """One component and the hinge that carries it from closed to open."""

    def __init__(self, mesh, R, t, res):
        self.mesh = mesh
        self.res = res
        self.axis, self.angle, self.point = _axis_angle_point(R, t)
        self.R, self.t = R, t
        # residual translation along the axis (a hinge has none to speak of)
        self.slide = float(self.axis @ (t - (np.eye(3) - R) @ self.point))

    @property
    def moves(self) -> bool:
        return self.angle > math.radians(0.5)

    def at(self, f: float) -> np.ndarray:
        """4x4 for fraction f of the opening (0 = closed, 1 = open)."""
        if not self.moves:
            return np.eye(4)
        return trimesh.transformations.rotation_matrix(
            self.angle * f, self.axis, point=self.point)


def recover(verbose: bool = False) -> list[Motion]:
    closed = _components(NOSE_OUT / "nose_closed.stl")
    opened = _components(NOSE_OUT / "nose_open.stl")
    if len(closed) != len(opened):
        raise SystemExit(f"component count differs: {len(closed)} vs {len(opened)}")

    used, out = set(), []
    for c in closed:
        best = None
        for j, o in enumerate(opened):
            if j in used or len(o.vertices) != len(c.vertices):
                continue
            R, t, res = _kabsch(c.vertices, o.vertices)
            if best is None or res < best[0]:
                best = (res, j, R, t)
        if best is None:
            raise SystemExit(f"no partner for a {len(c.vertices)}-vertex component")
        res, j, R, t = best
        if res > FIT_TOL:
            raise SystemExit(
                f"component pairing is not a rigid correspondence "
                f"(RMS {res:.6g} mm > {FIT_TOL}); vertex order does not match, "
                f"so the hinge cannot be recovered this way")
        used.add(j)
        out.append(Motion(c, R, t, res))
    if verbose:
        print(f"recovered {len(out)} components from the two nose poses")
        for m in sorted(out, key=lambda m: -len(m.mesh.faces)):
            if m.moves:
                print(f"  f={len(m.mesh.faces):6d}  rotates "
                      f"{math.degrees(m.angle):7.3f} deg about "
                      f"[{m.axis[0]:+.4f} {m.axis[1]:+.4f} {m.axis[2]:+.4f}] "
                      f"through (x={m.point[0]:.3f}, y={m.point[1]:.3f}, "
                      f"z={m.point[2]:.3f})   slide {m.slide:+.4f} mm   "
                      f"fit RMS {m.res:.2e}")
            else:
                print(f"  f={len(m.mesh.faces):6d}  static"
                      f"                    fit RMS {m.res:.2e}")
    return out


if __name__ == "__main__":
    ms = recover(verbose=True)
    mv = [m for m in ms if m.moves]
    print(f"\n{len(mv)} moving component(s), "
          f"{len(ms) - len(mv)} static")
    if mv:
        angs = sorted({round(math.degrees(m.angle), 3) for m in mv})
        print("distinct opening angles:", angs)
        print("max |slide| along axis: "
              f"{max(abs(m.slide) for m in mv):.4f} mm  (a hinge should be ~0)")
