"""Parametric factories for the Scorpio replica parts (build123d, millimetres).

Each factory returns one closed solid in its print orientation (see params.py).
Every downward-facing surface is either on the bed, a short bridge, or 45 deg or
steeper, so no part needs support material.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cadgen import build123d as bd
from cadgen import srgb

from lib import params as p

R_BODY = p.BODY_OD / 2
# T-shoulders lean by this slope (radial per tangential mm) so that no planar
# outline has four collinear vertices, which the mesh exporter mis-triangulates.
SHOULDER_SLOPE = 0.1


# --- small helpers ----------------------------------------------------------------


def _revolve_rz(points) -> bd.Part:
    """Revolve a closed (r, z) polygon drawn in the XZ half-plane about Z."""
    wire = bd.Wire.make_polygon([bd.Vector(r, 0, z) for r, z in points], close=True)
    return bd.revolve(bd.Face(wire), bd.Axis.Z)


def _zextrude(face: bd.Face, z0: float, z1: float) -> bd.Part:
    """Extrude an XY face from z0 to z1.

    T-shaped features are drawn as one outline and extruded once: a union of
    boxes leaves coplanar faces split by collinear vertices, which the mesh
    exporter turns into open (T-junction) edges.
    """
    return bd.Pos(0, 0, z0) * bd.extrude(face, amount=z1 - z0)


def _xy_polygon(points) -> bd.Face:
    return bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in points], close=True))


def _zprism(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> bd.Part:
    """Axis-aligned box from corner ranges."""
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )


def _chamfer_envelope(r0: float, z0: float, h: float, reach: float, bottom: bool, top: bool) -> bd.Part:
    """Region whose ends rise/fall at 45 deg outward from radius r0 (local +X is radial).

    Intersecting a radial feature with it gives self-supporting, streamlined ends.
    Callers pass r0 just inside the body skin, so the cut faces meet the body's
    cylinder instead of leaving slivers on the body's end planes.
    """
    lo, hi = r0 - 6.0, r0 + reach
    if bottom and top:
        assert 2 * reach < h, "feature too tall for its length"
    elif reach >= h:
        raise ValueError("feature too tall for its length")
    zb = (z0 - (r0 - lo), z0 + (hi - r0)) if bottom else (z0 - 50.0, z0 - 50.0)
    zt = (z0 + h + (r0 - lo), z0 + h - (hi - r0)) if top else (z0 + h + 50.0, z0 + h + 50.0)
    pts = [(lo, zb[0]), (hi, zb[1]), (hi, zt[1]), (lo, zt[0])]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, 0, z) for x, z in pts], close=True))
    return bd.extrude(face, amount=30.0, dir=(0, 1, 0), both=True)


def _finish(part: bd.Part, label: str, color: str = p.PRINT_COLOR) -> bd.Part:
    solids = part.solids()
    if len(solids) != 1:
        raise ValueError(f"{label}: expected one solid, got {len(solids)}")
    solid = solids[0]
    solid.label = label
    solid.color = srgb(color)
    return solid


# --- launch guides ------------------------------------------------------------------


def rail_guide_1010(z0: float, length: float, angle: float, chamfer_bottom: bool) -> bd.Part:
    """Printed 1010 rail guide: pad, neck that rides in the slot, and a T head."""
    face = R_BODY + p.RAIL_STANDOFF
    neck_top = face + p.RAIL_NECK_HEIGHT
    head_top = neck_top + p.RAIL_HEAD_THICKNESS
    pad, neck, head = p.RAIL_PAD_WIDTH / 2, p.RAIL_NECK_WIDTH / 2, p.RAIL_HEAD_WIDTH / 2
    pad_lean = SHOULDER_SLOPE * (pad - neck)
    head_lean = SHOULDER_SLOPE * (head - neck)
    x_in = R_BODY - 2.0
    outline = _xy_polygon([
        (x_in, -pad), (face - pad_lean, -pad), (face, -neck), (neck_top, -neck), (neck_top + head_lean, -head),
        (head_top, -head), (head_top, head), (neck_top + head_lean, head), (neck_top, neck), (face, neck),
        (face - pad_lean, pad), (x_in, pad),
    ])
    guide = _zextrude(outline, z0, z0 + length)
    r0 = R_BODY - 1.0
    guide = guide & _chamfer_envelope(r0, z0, length, head_top - r0 + 0.5, chamfer_bottom, True)
    return bd.Rot(0, 0, angle) * guide


def launch_lug(z0: float, length: float, angle: float, chamfer_bottom: bool) -> bd.Part:
    """Launch lug for a 1/4 in rod, faired to the body by a web."""
    bore_r = p.LUG_BORE / 2
    d = R_BODY + p.LUG_CLEARANCE + bore_r  # rod centre distance from the rocket axis
    ro = bore_r + p.LUG_WALL
    V = bd.Vector
    x0 = R_BODY - 2.0
    outer = bd.Wire([
        bd.Edge.make_line(V(x0, -ro, 0), V(d, -ro, 0)),
        bd.Edge.make_three_point_arc(V(d, -ro, 0), V(d + ro, 0, 0), V(d, ro, 0)),
        bd.Edge.make_line(V(d, ro, 0), V(x0, ro, 0)),
        bd.Edge.make_line(V(x0, ro, 0), V(x0, -ro, 0)),
    ])
    lug = _zextrude(bd.Face(outer), z0, z0 + length)
    r0 = R_BODY - 1.0
    lug = lug & _chamfer_envelope(r0, z0, length, d + ro - r0 + 0.5, chamfer_bottom, True)
    lug -= bd.Pos(d, 0, z0 - 1.0) * bd.Cylinder(
        bore_r, length + 2.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
    return bd.Rot(0, 0, angle) * lug


# --- threads (45 deg flanks: every downward flank is self-supporting) ----------------


THREAD_SINK = 0.05  # ridge root sinks this far into its wall: no vertex lies on the wall


def _thread_ridge(r_root: float, r_tip: float, w_tip: float, z_start: float, height: float) -> bd.Part:
    """Sweep one right-hand 45 deg-flank ridge rising from the wall at r_root to r_tip.

    The root vertices sit THREAD_SINK inside the wall, so the wall cylinder cuts
    the flanks cleanly instead of sharing an edge with them (a shared edge makes
    the union fail), and the profile stays shorter than one pitch.
    """
    sink = THREAD_SINK if r_tip > r_root else -THREAD_SINK
    r_anchor = r_root - sink
    half = w_tip / 2 + abs(r_tip - r_anchor)
    if 2 * half >= p.THREAD_PITCH:
        raise ValueError("thread ridge wider than its pitch")
    pts = [(r_anchor, -half), (r_tip, -w_tip / 2), (r_tip, w_tip / 2), (r_anchor, half)]
    profile = bd.Face(bd.Wire.make_polygon([bd.Vector(x, 0, z + z_start) for x, z in pts], close=True))
    helix = bd.Helix(pitch=p.THREAD_PITCH, height=height, radius=r_anchor).moved(bd.Location((0, 0, z_start)))
    return bd.sweep(profile, path=helix, is_frenet=True)


def male_thread_radii() -> tuple[float, float]:
    major = p.MALE_THREAD_MAJOR / 2
    return major, major - p.THREAD_DEPTH


def cap_engaged_angle() -> float:
    """Cap rotation (deg) that centres its ridge in the groove of the flipped male.

    Male ridge (after Rot(180, 0, 0)): z = P - MALE_BAND_LEN + P*phi/2pi.
    Cap ridge (after Pos(0, 0, cap_z) * Rot(0, 0, a)): z = CAP_LIP - P + cap_z + P*(phi - a)/2pi.
    The cap ridge must sit half a pitch from the male ridge.
    """
    pitch = p.THREAD_PITCH
    cap_z = -(p.MALE_BAND_LEN + p.CAP_LIP + p.CAP_THREAD_LEN)
    phase = (p.CAP_LIP + cap_z + p.MALE_BAND_LEN - 2.5 * pitch) / pitch
    return 360.0 * (phase - math.floor(phase))


# --- parts ------------------------------------------------------------------------------


NOSE_MOUNTS = ("hook", "open")


@dataclass(frozen=True)
class NoseGeom:
    """The shared nose shell and the tangent-ogive constants behind it (r, z frame)."""

    outer: bd.Part  # solid of revolution of the outside surface
    shell: bd.Part  # outer minus the cavity
    rho: float      # ogive arc radius
    cr: float       # ogive arc centre radius coordinate (centre at z = zb)
    zb: float       # ogive base / top of the shoulder
    r_sh: float     # shoulder outer radius
    r_sh_in: float  # shoulder inner radius
    apex: float

    def r_offset(self, d: float, z: float) -> float:
        """Radius of the ogive surface offset inward by d, at height z."""
        return self.cr + math.sqrt((self.rho - d) ** 2 - (z - self.zb) ** 2)


def nose_geom() -> NoseGeom:
    """Hollow tangent-ogive nose with a blunted tip and a slip-fit shoulder."""
    R, L, rn, t = R_BODY, p.NOSE_OGIVE_LEN, p.NOSE_TIP_RADIUS, p.NOSE_WALL
    zb = p.NOSE_SHOULDER_LEN  # ogive base (shoulder below it, base on the bed)
    rho = (R * R + L * L) / (2 * R)
    cr, cz = R - rho, zb  # ogive arc centre in (r, z)

    # Spherical tip tangent to the ogive arc, centred on the axis.
    zc = zb + math.sqrt((rho - rn) ** 2 - (rho - R) ** 2)
    k = rho / (rho - rn)
    tr, tz = cr + k * (0.0 - cr), cz + k * (zc - cz)
    apex = zc + rn

    def on_arc(radius: float, phi: float) -> bd.Vector:
        return bd.Vector(cr + radius * math.cos(phi), 0, cz + radius * math.sin(phi))

    phi_t = math.atan2(tz - cz, tr - cr)
    psi_t = math.atan2(tz - zc, tr)
    psi_m = (psi_t + math.pi / 2) / 2
    r_sh = (p.BODY_ID - p.SLIP_FIT) / 2
    c = p.EDGE_CHAMFER
    V = bd.Vector
    outer_edges = [
        bd.Edge.make_line(V(0, 0, 0), V(r_sh - c, 0, 0)),
        bd.Edge.make_line(V(r_sh - c, 0, 0), V(r_sh, 0, c)),
        bd.Edge.make_line(V(r_sh, 0, c), V(r_sh, 0, zb)),
        bd.Edge.make_line(V(r_sh, 0, zb), V(R, 0, zb)),
        bd.Edge.make_three_point_arc(V(R, 0, zb), on_arc(rho, phi_t / 2), V(tr, 0, tz)),
        bd.Edge.make_three_point_arc(
            V(tr, 0, tz), V(rn * math.cos(psi_m), 0, zc + rn * math.sin(psi_m)), V(0, 0, apex)
        ),
        bd.Edge.make_line(V(0, 0, apex), V(0, 0, 0)),
    ]
    solid = bd.revolve(bd.Face(bd.Wire(outer_edges)), bd.Axis.Z)

    # Cavity: shoulder bore, then the ogive offset inward by the wall (a concentric arc).
    ri = rho - t
    r_sh_in = r_sh - t
    # 45 deg inner step from shoulder bore to ogive wall, raised above the outer
    # shoulder step so the joint keeps >= 2 mm of wall on every diagonal.
    z_s0 = zb + p.NOSE_STEP_RISE
    z_s = z_s0 + (R - t - r_sh_in)
    r_s = cr + math.sqrt(ri * ri - (z_s - cz) ** 2)
    z_top = apex - p.NOSE_SOLID_TIP
    r_top = cr + math.sqrt(ri * ri - (z_top - cz) ** 2)
    phi_s = math.atan2(z_s - cz, r_s - cr)
    phi_e = math.atan2(z_top - cz, r_top - cr)
    cavity_edges = [
        bd.Edge.make_line(V(0, 0, -1), V(r_sh_in, 0, -1)),
        bd.Edge.make_line(V(r_sh_in, 0, -1), V(r_sh_in, 0, z_s0)),
        bd.Edge.make_line(V(r_sh_in, 0, z_s0), V(r_s, 0, z_s)),
        bd.Edge.make_three_point_arc(V(r_s, 0, z_s), on_arc(ri, (phi_s + phi_e) / 2), V(r_top, 0, z_top)),
        bd.Edge.make_line(V(r_top, 0, z_top), V(0, 0, z_top + r_top)),  # 45 deg ceiling
        bd.Edge.make_line(V(0, 0, z_top + r_top), V(0, 0, -1)),
    ]
    shell = solid - bd.revolve(bd.Face(bd.Wire(cavity_edges)), bd.Axis.Z)
    return NoseGeom(solid, shell, rho, cr, zb, r_sh, r_sh_in, apex)


def make_nose_cone(mount: str) -> bd.Part:
    """Hollow tangent-ogive nose cone with a blunted tip and shoulder.

    mount="hook": closed base with a boss and pilot hole for a screw hook.
    mount="open": open base with a bar across it to tie the shock cord.
    """
    if mount not in NOSE_MOUNTS:
        raise ValueError(f"mount must be one of {NOSE_MOUNTS}, got {mount!r}")
    g = nose_geom()
    nose, r_sh_in = g.shell, g.r_sh_in
    V = bd.Vector
    if mount == "open":
        # Shock-cord bar across the open shoulder base (printed on the bed, ridge-topped).
        w, h = p.NOSE_BAR_WIDTH, p.NOSE_BAR_HEIGHT
        sec = [(-w / 2, 0), (w / 2, 0), (w / 2, h - 2), (w / 4, h), (-w / 4, h), (-w / 2, h - 2)]
        bar_face = bd.Face(bd.Wire.make_polygon([V(0, y, z) for y, z in sec], close=True))
        bar = bd.extrude(bar_face, amount=r_sh_in + 1.0, dir=(1, 0, 0), both=True)
        bar = bar & bd.Cylinder(r_sh_in + 1.0, h + 1, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        return _finish(nose + bar, "nose_cone_open")

    # Shock-cord attachment: bulkhead across the shoulder base (printed on the bed)
    # and a central boss with a blind pilot hole for a screw hook. Bulkhead, 45 deg
    # fillet, boss, hole lead-in and drill-point tip are ONE revolved profile, so
    # their junctions are profile vertices rather than boolean seams (a fillet
    # cone fused onto the boss left open triangles in the mesh export). Gussets
    # then tie the boss to the shoulder wall.
    t_b = p.NOSE_BULKHEAD_THICKNESS
    r_boss = p.NOSE_HOOK_BOSS_D / 2
    r_pilot = p.NOSE_HOOK_PILOT / 2
    z_hole = p.NOSE_HOOK_DEPTH
    z_tip = z_hole + r_pilot
    z_boss = z_tip + p.NOSE_HOOK_BOSS_CAP
    r_wall = r_sh_in + 0.5  # reaches into the shoulder wall
    fillet = 3.5
    hook_mount = _revolve_rz([
        (r_pilot + 0.5, 0), (r_wall, 0), (r_wall, t_b), (r_boss + fillet, t_b), (r_boss, t_b + fillet),
        (r_boss, z_boss), (0, z_boss), (0, z_tip), (r_pilot, z_hole), (r_pilot, 0.5),
    ])
    rib = bd.extrude(bd.Face(bd.Wire.make_polygon([
        V(r_boss - 0.5, 0, t_b - 0.5), V(r_wall, 0, t_b - 0.5), V(r_wall, 0, t_b + 8.0), V(r_boss - 0.5, 0, z_boss - 2.0),
    ], close=True)), amount=p.NOSE_HOOK_RIB_THICKNESS / 2, dir=(0, 1, 0), both=True)
    for i in range(p.NOSE_HOOK_RIBS):
        hook_mount += bd.Rot(0, 0, 45.0 + i * 360.0 / p.NOSE_HOOK_RIBS) * rib
    return _finish(nose + hook_mount, "nose_cone_hook")


# --- side-door nose ---------------------------------------------------------------------

DOOR_K = math.tan(math.radians(p.NOSE_DOOR_JOINT_ANGLE))


def _align_min():
    """Centred in x/y, base at z = 0 (a function: module level must not touch the kernel)."""
    return (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


def _xz_extrude(points, half_y: float = 40.0) -> bd.Part:
    """Extrude an (x, z) polygon drawn at y = 0 across +/- half_y."""
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, 0, z) for x, z in points], close=True))
    return bd.extrude(face, amount=half_y, dir=(0, 1, 0), both=True)


def _x_cylinder(radius: float, x0: float, x1: float, y: float, z: float) -> bd.Part:
    """Cylinder along +x from x0 to x1, centred on (y, z)."""
    return bd.Pos(x0, y, z) * bd.Rot(0, 90, 0) * bd.Cylinder(radius, x1 - x0, align=_align_min())


def _x_prism(yz_points, x0: float, x1: float) -> bd.Part:
    """Prism along +x from x0 to x1 over a (y, z) polygon."""
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x0, y, z) for y, z in yz_points], close=True))
    return bd.extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def _x_diamond(half_diag: float, x0: float, x1: float, y: float, z: float) -> bd.Part:
    """Square rotated 45 deg, along +x: a pin that prints sideways with 45 deg flanks."""
    h = half_diag
    return _x_prism([(y - h, z), (y, z - h), (y + h, z), (y, z + h)], x0, x1)


def _x_teardrop(radius: float, x0: float, x1: float, y: float, z: float) -> bd.Part:
    """Horizontal bore along +x with a 45 deg peaked roof, so it prints without support."""
    s = radius / math.sqrt(2)
    roof = _x_prism([(y - s, z + s), (y + s, z + s), (y, z + radius * math.sqrt(2))], x0, x1)
    return _x_cylinder(radius, x0, x1, y, z) + roof


def _x_cone(r0: float, r1: float, x0: float, x1: float, y: float, z: float) -> bd.Part:
    """Cone along +x from radius r0 at x0 to r1 at x1, centred on (y, z)."""
    return bd.Pos(x0, y, z) * bd.Rot(0, 90, 0) * bd.Cone(r0, r1, x1 - x0, align=_align_min())


def door_spring_x() -> tuple[float, float, float]:
    """Pocket bottom, funnel end and pin tip positions along x (door closed)."""
    c = p.NOSE_DOOR_CLEARANCE
    x_bottom = c + p.NOSE_DOOR_SPRING_POCKET_DEPTH
    x_funnel = x_bottom + (p.NOSE_DOOR_SPRING_POCKET_D - p.NOSE_DOOR_PIN_HOLE_D) / 2
    return x_bottom, x_funnel, x_funnel + p.NOSE_DOOR_PIN_TIP


def _ogive_band(g: NoseGeom, d_out: float, d_in: float, z0: float, z1: float) -> bd.Part:
    """Revolved band between the ogive offset inward by d_out and by d_in (d_out < d_in)."""
    V = bd.Vector
    zm = (z0 + z1) / 2

    def pt(d: float, z: float) -> bd.Vector:
        return V(g.r_offset(d, z), 0, z)

    edges = [
        bd.Edge.make_line(pt(d_in, z0), pt(d_out, z0)),
        bd.Edge.make_three_point_arc(pt(d_out, z0), pt(d_out, zm), pt(d_out, z1)),
        bd.Edge.make_line(pt(d_out, z1), pt(d_in, z1)),
        bd.Edge.make_three_point_arc(pt(d_in, z1), pt(d_in, zm), pt(d_in, z0)),
    ]
    return bd.revolve(bd.Face(bd.Wire(edges)), bd.Axis.Z)


def door_joint_z(x: float) -> float:
    """Joint plane between the door top and the tip; rises outward on the door side (x > 0)."""
    return p.NOSE_DOOR_JOINT_Z + DOOR_K * x


def door_levels() -> tuple[float, float]:
    """Door bottom (on the band) and floor-block top heights in the nose frame."""
    z_d0 = p.NOSE_SHOULDER_LEN + p.NOSE_DOOR_BAND
    return z_d0, z_d0 + p.NOSE_DOOR_FLOOR


@dataclass(frozen=True)
class ServoPose:
    """SG90 placement in the nose frame: shaft along +x (radial, toward the door)."""

    x_bottom: float  # servo bottom face
    x_seat: float    # ear underside = door-side face of the mounting plate
    x_horn: float    # horn mid-plane = latch groove centre
    z_shaft: float
    z_body_lo: float
    z_body_hi: float
    z_holes: tuple[float, float]


def servo_pose() -> ServoPose:
    z_d0, _ = door_levels()
    x_horn = p.NOSE_DOOR_GROOVE_R
    x_bottom = x_horn - p.SERVO_HORN_H
    z_shaft = z_d0 + 4.0 - p.SERVO_ARM  # latched arm tip sits 4 mm up the groove
    z_hi = z_shaft + p.SERVO_SHAFT_OFFSET
    z_lo = z_hi - p.SERVO_BODY_L
    zc = (z_lo + z_hi) / 2
    return ServoPose(x_bottom, x_bottom + p.SERVO_EAR_H, x_horn, z_shaft, z_lo, z_hi,
                     (zc - p.SERVO_HOLE_SPACING / 2, zc + p.SERVO_HOLE_SPACING / 2))


def make_nose_door_housing() -> bd.Part:
    """Side-door nose housing: shoulder, band, one half-shell and the tip, plus the
    servo mount, spring pins, a ramp floor and a parachute tie eye. Print upright."""
    g = nose_geom()
    shell, outer = g.shell, g.outer
    c = p.NOSE_DOOR_CLEARANCE
    z_d0, z_f = door_levels()
    sv = servo_pose()
    reach = 40.0
    housing = shell - _xz_extrude([(-c, z_d0), (reach, z_d0), (reach, door_joint_z(reach)), (-c, door_joint_z(-c))])
    # Chamfer the band's top outer edge on the door side: the door's bottom swings past
    # it. (The sharp edge there also met the shell's revolve seam, which the mesh
    # exporter folded into non-manifold triangles.) The cutter rises past the band top
    # so none of its faces is coplanar with it.
    ch, e = p.NOSE_DOOR_BAND_CHAMFER, 0.3
    ring = _revolve_rz([(R_BODY - ch - e, z_d0 + e), (R_BODY + 1.0, z_d0 + e), (R_BODY + 1.0, z_d0 - ch - 1.0)])
    housing -= ring & _zprism(-c, reach, -reach, reach, z_d0 - 5.0, z_d0 + 5.0)

    # One plate on the split face, printed from the bed: below the door it is thick
    # enough to seat the servo ears on its door-side face; above, it carries the spring pins.
    x_split = -c - p.NOSE_DOOR_SPLIT_PLATE
    plate = _xz_extrude([(x_split, 0.0), (sv.x_seat, 0.0), (sv.x_seat, z_d0 - 0.5), (-c, z_d0 - 0.5),
                         (-c, z_f), (x_split, z_f)]) & outer
    sc = p.SERVO_CLEARANCE
    plate -= _zprism(x_split - 1.0, sv.x_seat + 1.0, -(p.SERVO_BODY_W / 2 + sc), p.SERVO_BODY_W / 2 + sc,
                     sv.z_body_lo - sc, sv.z_body_hi + sc)
    for z in sv.z_holes:
        plate -= _x_cylinder(p.SERVO_SCREW_PILOT / 2, x_split - 1.0, sv.x_seat + 1.0, 0.0, z)
    housing += plate
    # Spring pins on the split face: a collar the spring's base coils screw onto, then
    # the guide pin, whose tip locates the door when it is closed.
    _, _, x_tip = door_spring_x()
    z_sp = z_d0 + p.NOSE_DOOR_SPRING_Z
    for y in (-p.NOSE_DOOR_SPRING_Y, p.NOSE_DOOR_SPRING_Y):
        housing += _x_diamond(p.NOSE_DOOR_PIN_COLLAR_D / 2, -c - 1.0, -c + p.NOSE_DOOR_PIN_COLLAR_LEN, y, z_sp)
        housing += _x_diamond(p.NOSE_DOOR_PIN_D / 2, -c - 1.0, x_tip, y, z_sp)

    # Compartment floor on the housing side: a ramp rising from the split edge at
    # NOSE_DOOR_RAMP_ANGLE (self-supporting), so the packed chute slides out the door.
    kr = math.tan(math.radians(p.NOSE_DOOR_RAMP_ANGLE))
    t_v = p.NOSE_DOOR_RAMP_T / math.cos(math.radians(p.NOSE_DOOR_RAMP_ANGLE))

    def ramp_top(x: float) -> float:
        return z_f + kr * (-c - x)

    ramp = _xz_extrude([(-c, z_f - t_v), (-c, z_f), (-reach, ramp_top(-reach)), (-reach, ramp_top(-reach) - t_v)]) & outer
    # Tie eye standing on the ramp; its base follows the ramp (buried 0.5 mm above the
    # ramp's underside), so it adds no downward-facing face.
    x0, x1 = -12.0, -4.0
    eye = _xz_extrude([(x0, ramp_top(x0) - t_v + 0.5), (x1, ramp_top(x1) - t_v + 0.5), (x1, ramp_top(x0) + 7.0),
                       (x0, ramp_top(x0) + 7.0)], half_y=4.0)
    housing += ramp + eye
    housing -= bd.Pos(-8.0, 0, ramp_top(-8.0) + 4.5) * bd.Rot(90, 0, 0) * bd.Cylinder(p.NOSE_DOOR_EYE_HOLE / 2, 12.0)
    housing -= bd.Pos(-17.5, 0, z_f - 15.0) * bd.Cylinder(p.NOSE_DOOR_CORD_HOLE / 2, 60.0, align=_align_min())
    return _finish(housing, "nose_cone_door_housing")


def make_nose_door() -> bd.Part:
    """Side door, in print orientation (floor block on the bed); the assembly lifts it
    by the band height. Its lip tucks inside the tip shell; its floor block takes the
    two spring pockets and has the downward-open groove the servo arm latches into."""
    g = nose_geom()
    c = p.NOSE_DOOR_CLEARANCE
    z_d0, z_f = door_levels()
    gap = p.NOSE_DOOR_JOINT_GAP
    reach = 40.0
    zone = _xz_extrude([(c, z_d0), (reach, z_d0), (reach, door_joint_z(reach) - gap), (c, door_joint_z(c) - gap)])
    door = (g.shell & zone) + (g.outer & _zprism(c, reach, -reach, reach, z_d0, z_f))

    # Top tab inside the tip shell, rising from a bead that thickens the door wall
    # inward just below the joint (50 deg underside). It sits at the door centre, where
    # the inclined joint is highest, i.e. level with the hinge the door swings about.
    zj, t = p.NOSE_DOOR_JOINT_Z, p.NOSE_WALL
    d_lip_out = t + p.NOSE_DOOR_TONGUE_CLEARANCE
    d_lip_in = d_lip_out + p.NOSE_DOOR_TONGUE_T
    z0 = zj - p.NOSE_DOOR_BEAD - 2.0
    z1 = door_joint_z(reach) + p.NOSE_DOOR_TONGUE + 2.0
    w2 = p.NOSE_DOOR_TONGUE_W / 2
    half = _zprism(c, reach, -w2, w2, z0 - 1.0, z1 + 1.0)

    def slab(lo: float, hi: float) -> bd.Part:
        return _xz_extrude([(c - 1.0, door_joint_z(c - 1.0) + lo), (reach, door_joint_z(reach) + lo),
                            (reach, door_joint_z(reach) + hi), (c - 1.0, door_joint_z(c - 1.0) + hi)])

    # Level tab top (no knife edge): the tab height is set at its mid radius.
    x_tab = g.r_offset((d_lip_out + d_lip_in) / 2, door_joint_z(g.r_offset(0.0, zj)))
    z_tab = door_joint_z(x_tab) + p.NOSE_DOOR_TONGUE
    x_hi = (z_tab + p.NOSE_DOOR_BEAD - zj) / DOOR_K - 0.5
    lip_zone = _xz_extrude([(c - 1.0, door_joint_z(c - 1.0) - p.NOSE_DOOR_BEAD), (x_hi, door_joint_z(x_hi) - p.NOSE_DOOR_BEAD),
                            (x_hi, z_tab), (c - 1.0, z_tab)])
    lip = _ogive_band(g, d_lip_out, d_lip_in, z0, z1) & lip_zone & half
    bead = _ogive_band(g, t - 0.5, d_lip_in, z0, z1) & slab(-p.NOSE_DOOR_BEAD, -gap) & half
    door += lip + bead

    gw, gl = p.NOSE_DOOR_GROOVE_W / 2, p.NOSE_DOOR_GROOVE_LEN / 2
    door -= _zprism(p.NOSE_DOOR_GROOVE_R - gw, p.NOSE_DOOR_GROOVE_R + gw, -gl, gl, z_d0 - 1.0, z_d0 + p.NOSE_DOOR_GROOVE_H)
    # Spring pockets (teardrop bores), a 45 deg funnel and the pin-tip locating hole.
    # The funnel runs 0.3 mm past the hole radius so its end disc does not land on the
    # hole's wall (the exporter left open edges there).
    x_bottom, x_funnel, x_tip = door_spring_x()
    r_p, r_t = p.NOSE_DOOR_SPRING_POCKET_D / 2, p.NOSE_DOOR_PIN_HOLE_D / 2
    z_sp = z_d0 + p.NOSE_DOOR_SPRING_Z
    for y in (-p.NOSE_DOOR_SPRING_Y, p.NOSE_DOOR_SPRING_Y):
        door -= _x_teardrop(r_p, c - 1.0, x_bottom, y, z_sp)
        door -= _x_cone(r_p, r_t - 0.3, x_bottom - 0.01, x_funnel + 0.3, y, z_sp)
        door -= _x_teardrop(r_t, x_bottom, x_tip + 0.5, y, z_sp)
    # Optional tether lug on the floor, by the split edge: a thread through it to the
    # tie eye keeps the ejected door from being lost.
    t_r = p.NOSE_DOOR_TETHER_HOLE / 2
    lug = _x_prism([(-3.0, z_f - 0.5), (3.0, z_f - 0.5), (3.0, z_f + 3.0), (0.0, z_f + 6.0), (-3.0, z_f + 3.0)], c + 1.0, c + 6.0)
    lug -= bd.Pos(c + 3.5, 0, z_f + 2.8) * bd.Rot(90, 0, 0) * bd.Cylinder(t_r, 8.0)
    door += lug
    return _finish(bd.Pos(0, 0, -z_d0) * door, "nose_cone_door")


def make_spring_dummies(extended: bool = False) -> list[bd.Part]:
    """The two compression springs as tubes (not printed): closed, or at 18 mm free length."""
    c = p.NOSE_DOOR_CLEARANCE
    x_bottom, _, _ = door_spring_x()
    z_sp = door_levels()[0] + p.NOSE_DOOR_SPRING_Z
    length = 18.0 if extended else x_bottom + c
    r_o = p.SPRING_OD_MAX / 2 - 0.1
    r_i = max(p.SPRING_ID_MIN, p.NOSE_DOOR_PIN_COLLAR_D) / 2 + 0.05  # envelope clears the collar
    springs = []
    for i, y in enumerate((-p.NOSE_DOOR_SPRING_Y, p.NOSE_DOOR_SPRING_Y)):
        coil = _x_cylinder(r_o, -c, -c + length, y, z_sp) - _x_cylinder(r_i, -c - 1.0, -c + length + 1.0, y, z_sp)
        springs.append(_finish(coil, f"spring_not_printed:{i + 1}", "#9AA3AD"))
    return springs


def make_servo_dummy(arm_angle: float = 0.0) -> bd.Part:
    """SG90-class servo envelope with a single-arm horn, for fit checks (not printed).
    arm_angle 0 = latched (arm up in the door groove)."""
    sv = servo_pose()
    w2 = p.SERVO_BODY_W / 2
    xb, xt = sv.x_bottom, sv.x_bottom + p.SERVO_BODY_H
    ear = (p.SERVO_EAR_SPAN - p.SERVO_BODY_L) / 2
    servo = _zprism(xb, xt, -w2, w2, sv.z_body_lo, sv.z_body_hi)
    servo += _zprism(sv.x_seat, sv.x_seat + p.SERVO_EAR_T, -w2, w2, sv.z_body_lo - ear, sv.z_body_hi + ear)
    x_horn0 = sv.x_horn - 0.9
    servo += _x_cylinder(w2 - 0.3, xt - 0.1, xt + 2.5, 0.0, sv.z_shaft)        # gear tower
    servo += _x_cylinder(2.4, xt + 2.4, x_horn0 + 0.1, 0.0, sv.z_shaft)        # output spline
    horn = _x_cylinder(3.5, x_horn0, x_horn0 + 1.8, 0.0, sv.z_shaft)
    horn += _zprism(x_horn0, x_horn0 + 1.8, -2.25, 2.25, sv.z_shaft, sv.z_shaft + p.SERVO_ARM)
    horn = horn.rotate(bd.Axis((0, 0, sv.z_shaft), (1, 0, 0)), arm_angle)
    return _finish(servo + horn, "servo_sg90_not_printed", p.MOTOR_TUBE_COLOR)


def make_coupler() -> bd.Part:
    """Body-tube coupler: two glue stubs, a body-diameter band with rail guide and lug."""
    R = R_BODY
    r_stub = (p.BODY_ID - p.GLUE_FIT) / 2
    r_in = r_stub - p.STUB_WALL
    z1 = p.COUPLER_STUB_LEN
    z2 = z1 + p.COUPLER_BAND_LEN
    z3 = z2 + p.COUPLER_STUB_LEN
    c, lead = p.EDGE_CHAMFER, 0.8
    body = _revolve_rz([
        (r_in + c, 0), (r_stub - lead, 0), (r_stub, lead), (r_stub, z1), (R, z1), (R, z2),
        (r_stub, z2), (r_stub, z3 - lead), (r_stub - lead, z3), (r_in + c, z3), (r_in, z3 - c),
        (r_in, c),
    ])
    body += rail_guide_1010(z1, p.COUPLER_BAND_LEN, p.RAIL_GUIDE_ANGLE, chamfer_bottom=True)
    body += launch_lug(z1, p.COUPLER_BAND_LEN, p.LAUNCH_LUG_ANGLE, chamfer_bottom=True)
    return _finish(body, "coupler")


def fin_housing_radii() -> tuple[float, float, float]:
    """Channel floor, channel ceiling (lip underside at the side walls) and housing top."""
    floor = p.FIN_HOUSING_FLOOR_R
    ceiling = floor + p.FIN_FLANGE_THICKNESS + 2 * p.SLOT_CLEARANCE
    return floor, ceiling, ceiling + p.FIN_HOUSING_LIP


def _fin_housing() -> bd.Part:
    """One external T-channel on +X: closed at the aft end, open at the forward face."""
    floor, ceiling, top = fin_housing_radii()
    neck = p.FIN_THICKNESS / 2 + p.SLOT_CLEARANCE
    ch = p.FIN_FLANGE_WIDTH / 2 + p.SLOT_CLEARANCE
    hw = ch + p.FIN_HOUSING_WALL
    crown, corner = p.FIN_HOUSING_CROWN, 0.8
    # Lip tops slope from `top` at the slot mouth down to the outer corners; the
    # outline's apex sits on that line at y = 0 so the neck cut adds no shared vertex.
    apex = top + crown * neck / (hw - corner - neck)
    x_in = R_BODY - 1.5
    outline = _xy_polygon([
        (x_in, -hw), (top - crown - corner, -hw), (top - crown, -hw + corner), (apex, 0.0),
        (top - crown, hw - corner), (top - crown - corner, hw), (x_in, hw),
    ])
    lean = SHOULDER_SLOPE * (ch - neck)  # lips thicken toward the neck, matching the fin flange
    cavity = _zextrude(_xy_polygon([
        (floor, -ch), (ceiling, -ch), (ceiling - lean, -neck), (apex + 1.0, -neck),
        (apex + 1.0, neck), (ceiling - lean, neck), (ceiling, ch), (floor, ch),
    ]), p.FIN_HOUSING_AFT_STOP, p.FIN_CAN_LEN + 1.0)
    return _zextrude(outline, 0.0, p.FIN_CAN_LEN) - cavity


def _stub_radius() -> float:
    return (p.BODY_ID - p.GLUE_FIT) / 2


def engine_stop_z() -> float:
    """Motor tube / motor forward end: the motor's aft face ends flush with the male retainer."""
    return p.MOTOR_LEN - (p.MALE_BAND_LEN + p.MALE_THREAD_LEN)


def make_fin_can() -> bd.Part:
    """Fin can: 3 external fin housings, motor-tube bore with engine block, aft lug and
    guide, and a detent-grooved stub that carries the fin lock ring."""
    R = R_BODY
    r_stub = _stub_radius()
    r_stub_in = r_stub - p.STUB_WALL
    r_bore = (p.MOTOR_TUBE_OD + p.MOTOR_TUBE_FIT) / 2
    r_ledge = r_bore - p.ENGINE_STOP_LEDGE
    r_blk = p.ENGINE_BLOCK_BORE / 2
    z_top = p.FIN_CAN_LEN
    z_stub = z_top + p.FIN_CAN_STUB_LEN
    z_stop = engine_stop_z()
    z_blk = z_stop + (r_ledge - r_blk) + 3.0  # straight part of the block bore ends here
    c, lead = p.EDGE_CHAMFER, 0.8
    body = _revolve_rz([
        (r_bore + c, 0), (R - c, 0), (R, c), (R, z_top), (r_stub, z_top), (r_stub, z_stub - lead),
        (r_stub - lead, z_stub), (r_stub_in, z_stub), (r_stub_in, z_top + (r_stub_in - r_bore)),
        (r_bore, z_top), (r_bore, z_blk + (r_bore - r_blk)), (r_blk, z_blk),
        (r_blk, z_stop + (r_ledge - r_blk)), (r_ledge, z_stop), (r_bore, z_stop), (r_bore, c),
    ])

    # External T-channel housings: fins enter from the forward face, under the
    # lock ring's notches, and stop on the closed aft end.
    housing = _fin_housing()
    for i in range(p.FIN_COUNT):
        body += bd.Rot(0, 0, p.FIN_ANGLE0 + i * 360.0 / p.FIN_COUNT) * housing

    # 45 deg detent grooves along the stub, one every 60 deg: the lock ring's
    # fingers click into them in both the open and the locked position. They
    # start just above the ring seat so no cut face lies on the fin-can top face.
    d = p.DETENT_DEPTH
    groove = _zextrude(_xy_polygon([(r_stub - d, 0.0), (r_stub + 0.5, -(d + 0.5)), (r_stub + 0.5, d + 0.5)]),
                       z_top + 0.3, z_stub + 1.0)
    for i in range(p.DETENT_GROOVES):
        body -= bd.Rot(0, 0, p.FIN_ANGLE0 + i * 360.0 / p.DETENT_GROOVES) * groove

    body += rail_guide_1010(0.0, p.AFT_GUIDE_LEN, p.RAIL_GUIDE_ANGLE, chamfer_bottom=False)
    body += launch_lug(0.0, p.AFT_GUIDE_LEN, p.LAUNCH_LUG_ANGLE, chamfer_bottom=False)

    # Internal anchor rib with a horizontal hole for the aramid shock-cord leader.
    # It starts just outside the bore and 2 mm down in solid material, so it never
    # touches the bore/cone junction circle tangentially.
    rib_angle = p.RAIL_GUIDE_ANGLE + 240.0
    hole_r = p.CORD_ANCHOR_HOLE / 2
    rib_x0 = r_bore + 0.4
    hole_x = rib_x0 + 1.6 + hole_r
    rib = _zprism(rib_x0, r_stub_in + 0.5, -4.0, 4.0, z_top - 2.0, z_top + 18.0)
    rib -= bd.Pos(hole_x, 0, z_top + 12.0) * bd.Rot(90, 0, 0) * bd.Cylinder(hole_r, 12.0)
    body += bd.Rot(0, 0, rib_angle) * rib
    return _finish(body, "fin_can")


def make_fin() -> bd.Part:
    """One fin standing on its trailing edge. x = 0 is the housing top; the T-rail
    root (x < 0) rides in the housing channel, above the body tube's surface."""
    t = p.FIN_THICKNESS
    V = bd.Vector
    root_top = V(0, 0, p.FIN_ROOT_LEN)
    le_mid = V(p.FIN_LE_MID[0], 0, p.FIN_LE_MID[1])
    le_tip = V(p.FIN_LE_TIP[0], 0, p.FIN_LE_TIP[1])
    te_tip = V(p.FIN_TE_TIP_SPAN, 0, 0)
    edges = [
        bd.Edge.make_line(V(0, 0, 0), te_tip),
        bd.Edge.make_line(te_tip, le_tip),
        bd.Edge.make_three_point_arc(le_tip, le_mid, root_top),
        bd.Edge.make_line(root_top, V(0, 0, 0)),
    ]
    web = bd.extrude(bd.Face(bd.Wire(edges)), amount=t / 2, dir=(0, 1, 0), both=True)
    floor, _, top = fin_housing_radii()
    x_fl_in = floor + p.SLOT_CLEARANCE - top
    x_fl_out = x_fl_in + p.FIN_FLANGE_THICKNESS
    w = p.FIN_FLANGE_WIDTH / 2
    lean = SHOULDER_SLOPE * (w - t / 2)  # flange slightly thinner at the neck
    rail = _zextrude(_xy_polygon([
        (x_fl_in, -w), (x_fl_out, -w), (x_fl_out - lean, -t / 2), (0.0, -t / 2),
        (0.0, t / 2), (x_fl_out - lean, t / 2), (x_fl_out, w), (x_fl_in, w),
    ]), 0.0, p.FIN_ROOT_LEN)
    return _finish(web + rail, "fin")


LOCK_ANGLE = 360.0 / (2 * p.FIN_COUNT)  # twist from open (notches on the fins) to locked


def make_fin_lock_ring() -> bd.Part:
    """Twist-lock ring, printed aft face down, that rides on the fin-can stub.

    Its notches (local 0/120/240 deg) pass the fin rails when lined up with the
    housings; turned LOCK_ANGLE, solid ring covers the channel ends. Three flexing
    fingers with 45 deg nubs click into the stub grooves at both positions.
    """
    r_in = _stub_radius() + p.LOCK_RING_CLEARANCE
    _, _, r_out = fin_housing_radii()
    t, c = p.LOCK_RING_THICKNESS, 0.4
    ring = _revolve_rz([
        (r_in + c, 0), (r_out - c, 0), (r_out, c), (r_out, 2.0), (p.LOCK_RING_FAIRING_R, t),
        (r_in, t), (r_in, c),
    ])
    half = p.LOCK_RING_NOTCH_WIDTH / 2
    notch = _zprism(p.LOCK_RING_NOTCH_R, r_out + 1.0, -half, half, -1.0, t + 1.0)
    # Finger = the ring band between the bore and an arc relief slot behind it.
    r_slot = r_in + p.DETENT_BEAM_THICKNESS + p.DETENT_RELIEF / 2
    arc_deg = math.degrees(p.DETENT_BEAM_ARC / r_slot)
    d = p.DETENT_DEPTH
    nub = _zextrude(_xy_polygon([(r_in - d, 0.0), (r_in + 0.3, -(d + 0.3)), (r_in + 0.3, d + 0.3)]), 0.5, t)
    for i in range(p.FIN_COUNT):
        a = i * 360.0 / p.FIN_COUNT
        ring -= bd.Rot(0, 0, a) * notch
    for i in range(p.DETENT_COUNT):
        a = LOCK_ANGLE + i * 360.0 / p.DETENT_COUNT
        arc = bd.Edge.make_circle(r_slot, start_angle=a - arc_deg / 2, end_angle=a + arc_deg / 2)
        slot = bd.SlotArc(arc, p.DETENT_RELIEF)
        ring -= bd.Pos(0, 0, -1.0) * bd.extrude(slot, amount=t + 2.0)
        ring += bd.Rot(0, 0, a) * nub
    return _finish(ring, "fin_lock_ring")


def make_retainer_male() -> bd.Part:
    """Male retainer, printed band-down: glued over the motor tube against the fin can."""
    r_bore = (p.MOTOR_TUBE_OD + p.MOTOR_TUBE_FIT) / 2
    r_band = p.MALE_BAND_OD / 2
    r_maj, r_min = male_thread_radii()
    zb = p.MALE_BAND_LEN
    zt = zb + p.MALE_THREAD_LEN
    c = p.EDGE_CHAMFER
    core = _revolve_rz([
        (r_bore + c, 0), (r_band - c, 0), (r_band, c), (r_band, zb - c), (r_band - c, zb),
        (r_min, zb), (r_min, zt), (r_bore + c, zt), (r_bore, zt - c), (r_bore, c),
    ])
    ridge = _thread_ridge(r_min, r_maj, p.THREAD_CREST, zb - p.THREAD_PITCH,
                          p.MALE_THREAD_LEN + 2 * p.THREAD_PITCH)
    lead = r_maj + 0.1 - r_min
    envelope = _revolve_rz([(r_min - 1.0, zb - 0.5), (r_maj + 0.1, zb - 0.5), (r_maj + 0.1, zt - lead),
                            (r_min, zt), (r_min - 1.0, zt)])
    return _finish(core + (ridge & envelope), "retainer_male")


def make_retainer_female() -> bd.Part:
    """Knurled female cap, printed lip-down; the lip holds the motor's aft face."""
    r_maj, r_min = male_thread_radii()
    rf_maj = r_maj + p.THREAD_RADIAL_CLEARANCE  # groove bottom (in the wall)
    rf_min = r_min + p.THREAD_RADIAL_CLEARANCE  # ridge crest
    r_cap = p.CAP_OD / 2
    r_hole = p.CAP_HOLE / 2
    h = p.CAP_LIP + p.CAP_THREAD_LEN
    c = p.EDGE_CHAMFER
    body = _revolve_rz([
        (r_hole + 0.5, 0), (r_cap - c, 0), (r_cap, c), (r_cap, h - c), (r_cap - c, h), (rf_maj, h),
        (rf_maj, p.CAP_LIP), (r_hole, p.CAP_LIP), (r_hole, 0.5),
    ])
    # Female ridge sits in the male groove with the radial and per-flank axial clearances.
    groove_at_crest = p.THREAD_ROOT_GAP + 2 * (rf_min - r_min)
    w_tip = groove_at_crest - 2 * p.THREAD_AXIAL_CLEARANCE
    ridge = _thread_ridge(rf_maj, rf_min, w_tip, p.CAP_LIP - p.THREAD_PITCH,
                          p.CAP_THREAD_LEN + 2 * p.THREAD_PITCH)
    # The ridge stops 0.3 mm above the lip and just below the lead-in chamfer:
    # running it into the lip face or through the chamfer makes the mesh
    # exporter emit duplicate / open triangles. 11.7 mm (4.7 turns) stay engaged.
    r_entry = rf_maj + 0.6
    z_ridge_top = h - (r_entry - rf_min) - 0.1
    ridge = ridge & _revolve_rz([(rf_min - 0.2, p.CAP_LIP + 0.3), (rf_maj + 0.35, p.CAP_LIP + 0.3),
                                 (rf_maj + 0.35, z_ridge_top), (rf_min - 0.2, z_ridge_top)])
    body += ridge
    # 45 deg lead-in at the open end. The triangular cutter crosses the top face
    # at r_entry without a vertex on it, and starts inside the nozzle hole so its
    # profile stays off the axis.
    r0 = r_hole - 1.0
    body -= _revolve_rz([(r0, h - (r_entry - r0)), (r_entry + 1.0, h + 1.0), (r0, h + 1.0)])
    r_fc = r_cap - p.CAP_FLUTE_DEPTH + p.CAP_FLUTE_RADIUS
    for i in range(p.CAP_FLUTES):
        a = 2 * math.pi * i / p.CAP_FLUTES
        body -= bd.Pos(r_fc * math.cos(a), r_fc * math.sin(a), -1.0) * bd.Cylinder(
            p.CAP_FLUTE_RADIUS, h + 2.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
        )
    return _finish(body, "retainer_female")


def make_fit_gauge() -> bd.Part:
    """Stepped gauge: outer steps test the body-tube ID, inner steps the motor-tube OD."""
    step_h = 5.0
    ods = [p.BODY_ID + d for d in (0.3, 0.0, -0.3, -0.6, -0.9, -1.2)]       # bottom -> top
    bores = [p.MOTOR_TUBE_OD + d for d in (-0.6, -0.3, 0.0, 0.3, 0.6, 0.9)]  # bottom -> top
    n = len(ods)
    pts = [(bores[0] / 2, 0), (ods[0] / 2, 0)]
    for i in range(n):
        pts.append((ods[i] / 2, (i + 1) * step_h))
        if i + 1 < n:
            pts.append((ods[i + 1] / 2, (i + 1) * step_h))
    pts.append((bores[-1] / 2, n * step_h))
    for i in range(n - 1, 0, -1):
        pts.append((bores[i] / 2, i * step_h))
        pts.append((bores[i - 1] / 2, i * step_h))
    gauge = _revolve_rz(pts)
    # Index notch on the top so steps can be counted from a known side.
    gauge -= _zprism(ods[-1] / 2 - 1.0, ods[-1] / 2 + 1.0, -0.75, 0.75, n * step_h - 3.0, n * step_h + 1.0)
    return _finish(gauge, "fit_gauge")


def make_tube(od: float, id_: float, length: float, label: str, color: str) -> bd.Part:
    """Non-printed reference tube for the assembly preview."""
    tube = bd.Cylinder(od / 2, length, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    tube -= bd.Pos(0, 0, -1) * bd.Cylinder(id_ / 2, length + 2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return _finish(tube, label, color)
