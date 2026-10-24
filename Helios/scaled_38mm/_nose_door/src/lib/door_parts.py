"""Parametric factories for the Helios side-door nose (build123d, millimetres).

Ported from the Scorpio side-door nose (Foguete-Scorpio/src/lib/rocket_parts.py):
same door, latch, springs and ramp; new outer shape (cone.stl's skirt + secant
ogive), the Helios shoulder, two screw pads for the airframe, and the shock-cord
hole moved to the ramp root.

Each factory returns one closed solid. Every downward-facing surface is on the bed,
a short bridge, or 45 deg or steeper, so no part needs support material.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cadgen import build123d as bd
from cadgen import srgb

from lib import params as p

R_BODY = p.BODY_OD / 2
DOOR_K = math.tan(math.radians(p.NOSE_DOOR_JOINT_ANGLE))


# --- small helpers ----------------------------------------------------------------


def _align_min():
    """Centred in x/y, base at z = 0 (a function: module level must not touch the kernel)."""
    return (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


def _revolve_rz(points) -> bd.Part:
    """Revolve a closed (r, z) polygon drawn in the XZ half-plane about Z."""
    wire = bd.Wire.make_polygon([bd.Vector(r, 0, z) for r, z in points], close=True)
    return bd.revolve(bd.Face(wire), bd.Axis.Z)


def _zprism(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> bd.Part:
    """Axis-aligned box from corner ranges."""
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(x1 - x0, y1 - y0, z1 - z0, align=_align_min())


def _finish(part: bd.Part, label: str, color: str = p.PRINT_COLOR) -> bd.Part:
    solids = part.solids()
    if len(solids) != 1:
        raise ValueError(f"{label}: expected one solid, got {len(solids)}")
    solid = solids[0]
    solid.label = label
    solid.color = srgb(color)
    return solid


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


# --- nose shell -------------------------------------------------------------------------


@dataclass(frozen=True)
class NoseGeom:
    """The nose shell and the secant-ogive constants behind it (r, z frame)."""

    outer: bd.Part  # solid of revolution of the outside surface
    shell: bd.Part  # outer minus the cavity
    rho: float      # ogive arc radius
    cr: float       # arc centre (r, z)
    cz: float
    z_og: float     # skirt / ogive junction
    r_sh: float     # shoulder outer radius
    r_sh_in: float  # shoulder inner radius
    apex: float

    def r_offset(self, d: float, z: float) -> float:
        """Radius of the outer surface offset inward by d, at height z (skirt or arc)."""
        z_i = self.cz + math.sqrt((self.rho - d) ** 2 - (R_BODY - d - self.cr) ** 2)
        if z <= z_i:
            return R_BODY - d
        return self.cr + math.sqrt((self.rho - d) ** 2 - (z - self.cz) ** 2)


def ogive_centre() -> tuple[float, float]:
    """Centre of the arc of radius OGIVE_RHO through (R, OGIVE_Z0) and the sharp apex."""
    p1, p2 = (R_BODY, p.OGIVE_Z0), (0.0, p.SHARP_APEX_Z)
    mx, mz = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    dx, dz = p2[0] - p1[0], p2[1] - p1[1]
    chord = math.hypot(dx, dz)
    h = math.sqrt(p.OGIVE_RHO ** 2 - (chord / 2) ** 2)
    nx, nz = -dz / chord, dx / chord
    cands = [(mx + h * nx, mz + h * nz), (mx - h * nx, mz - h * nz)]
    return min(cands, key=lambda c: c[0])  # on the far side of the axis


def nose_geom() -> NoseGeom:
    """Hollow nose: shoulder, a flat seat on Mbody's rim with a 45 deg step out to the
    cylindrical skirt, the secant ogive and a blunted tip."""
    R, rho, rn, t = R_BODY, p.OGIVE_RHO, p.NOSE_TIP_RADIUS, p.NOSE_WALL
    cr, cz = ogive_centre()
    z_rim, z_og = p.SHOULDER_LEN, p.OGIVE_Z0

    # Spherical tip tangent to the ogive arc, centred on the axis.
    zc = cz + math.sqrt((rho - rn) ** 2 - cr ** 2)
    k = rho / (rho - rn)
    tr, tz = cr + k * (0.0 - cr), cz + k * (zc - cz)
    apex = zc + rn

    def on_arc(radius: float, phi: float) -> bd.Vector:
        return bd.Vector(cr + radius * math.cos(phi), 0, cz + radius * math.sin(phi))

    phi_0 = math.atan2(z_og - cz, R - cr)
    phi_t = math.atan2(tz - cz, tr - cr)
    psi_t = math.atan2(tz - zc, tr)
    psi_m = (psi_t + math.pi / 2) / 2
    r_sh, c = p.SHOULDER_R, p.EDGE_CHAMFER
    V = bd.Vector
    outer_edges = [
        bd.Edge.make_line(V(0, 0, 0), V(r_sh - c, 0, 0)),
        bd.Edge.make_line(V(r_sh - c, 0, 0), V(r_sh, 0, c)),
        bd.Edge.make_line(V(r_sh, 0, c), V(r_sh, 0, z_rim)),
        bd.Edge.make_line(V(r_sh, 0, z_rim), V(p.SEAT_R_OUT, 0, z_rim)),
        bd.Edge.make_line(V(p.SEAT_R_OUT, 0, z_rim), V(R, 0, z_rim + R - p.SEAT_R_OUT)),
        bd.Edge.make_line(V(R, 0, z_rim + R - p.SEAT_R_OUT), V(R, 0, z_og)),
        bd.Edge.make_three_point_arc(V(R, 0, z_og), on_arc(rho, (phi_0 + phi_t) / 2), V(tr, 0, tz)),
        bd.Edge.make_three_point_arc(
            V(tr, 0, tz), V(rn * math.cos(psi_m), 0, zc + rn * math.sin(psi_m)), V(0, 0, apex)
        ),
        bd.Edge.make_line(V(0, 0, apex), V(0, 0, 0)),
    ]
    solid = bd.revolve(bd.Face(bd.Wire(outer_edges)), bd.Axis.Z)

    # Cavity: shoulder bore, a 45 deg step out to the skirt wall, the skirt bore, then
    # the ogive offset inward by the wall (a concentric arc). The skirt bore meets the
    # arc where the two offsets cross, a little below the outside kink.
    ri = rho - t
    r_sh_in = r_sh - t
    z_s0 = z_rim + p.NOSE_STEP_RISE
    z_s = z_s0 + (R - t - r_sh_in)
    z_i = cz + math.sqrt(ri * ri - (R - t - cr) ** 2)
    z_top = apex - p.NOSE_SOLID_TIP
    r_top = cr + math.sqrt(ri * ri - (z_top - cz) ** 2)
    phi_i = math.atan2(z_i - cz, R - t - cr)
    phi_e = math.atan2(z_top - cz, r_top - cr)
    cavity_edges = [
        bd.Edge.make_line(V(0, 0, -1), V(r_sh_in, 0, -1)),
        bd.Edge.make_line(V(r_sh_in, 0, -1), V(r_sh_in, 0, z_s0)),
        bd.Edge.make_line(V(r_sh_in, 0, z_s0), V(R - t, 0, z_s)),
        bd.Edge.make_line(V(R - t, 0, z_s), V(R - t, 0, z_i)),
        bd.Edge.make_three_point_arc(V(R - t, 0, z_i), on_arc(ri, (phi_i + phi_e) / 2), V(r_top, 0, z_top)),
        bd.Edge.make_line(V(r_top, 0, z_top), V(0, 0, z_top + r_top)),  # 45 deg ceiling
        bd.Edge.make_line(V(0, 0, z_top + r_top), V(0, 0, -1)),
    ]
    shell = solid - bd.revolve(bd.Face(bd.Wire(cavity_edges)), bd.Axis.Z)
    return NoseGeom(solid, shell, rho, cr, cz, z_og, r_sh, r_sh_in, apex)


# --- side door ---------------------------------------------------------------------------


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
    z_d0 = p.SHOULDER_LEN + p.NOSE_DOOR_BAND
    return z_d0, z_d0 + p.NOSE_DOOR_FLOOR


def door_hinge() -> bd.Axis:
    """Axis the door's bottom swings out about: its top outer edge on the centre line."""
    g = nose_geom()
    z_p = p.NOSE_DOOR_JOINT_Z
    for _ in range(30):  # outer surface meets the (gapped) joint plane on the door centre line
        z_p = door_joint_z(g.r_offset(0.0, z_p)) - p.NOSE_DOOR_JOINT_GAP
    x_p = g.r_offset(0.0, z_p)
    return bd.Axis((x_p, 0, z_p), (0, -1, 0))  # +angle swings the bottom outward


def cord_hole_xy() -> tuple[float, float]:
    a = math.radians(p.NOSE_DOOR_CORD_AZ)
    return p.NOSE_DOOR_CORD_R * math.cos(a), p.NOSE_DOOR_CORD_R * math.sin(a)


@dataclass(frozen=True)
class ServoPose:
    """MG90S placement in the nose frame: shaft along +x (radial, toward the door), the
    case's long side along y with its near end at -y, its width along z."""

    x_bottom: float  # case bottom face
    x_ear: float     # ear underside (faces the case bottom)
    x_mount: float   # ear top face = the mount plate's face the ears bear on
    x_arm: float     # horn arm mid-plane = latch groove centre
    z_shaft: float
    z_lo: float      # case faces across its width
    z_hi: float
    y_near: float    # case end nearest the shaft
    y_far: float
    ear_y: tuple[float, float]  # ear tips


def servo_pose() -> ServoPose:
    z_d0, _ = door_levels()
    x_arm = p.NOSE_DOOR_GROOVE_R
    x_bottom = x_arm - (p.SERVO_ARM_TOP - p.SERVO_ARM_T / 2)
    x_ear = x_bottom + p.SERVO_EAR_H
    z_shaft = z_d0 + 4.0 - p.SERVO_ARM  # latched arm tip sits 4 mm up the groove
    ear = (p.SERVO_EAR_SPAN - p.SERVO_BODY_L) / 2
    y_near, y_far = -p.SERVO_SHAFT_OFFSET, p.SERVO_BODY_L - p.SERVO_SHAFT_OFFSET
    w2 = p.SERVO_BODY_W / 2
    return ServoPose(x_bottom, x_ear, x_ear + p.SERVO_EAR_T, x_arm, z_shaft, z_shaft - w2, z_shaft + w2,
                     y_near, y_far, (y_near - ear, y_far + ear))


@dataclass(frozen=True)
class ServoMount:
    """The cuts in the housing's plate that the servo and its keeper fill."""

    x_split: float   # split plate's housing-side face
    x_plate: float   # mount plate's door-side face
    x_back: float    # ear channel's back wall
    z_slot: float    # slot roof (the servo's top face stops 0.25 below it)
    slot_y: tuple[float, float]
    ear_y: tuple[float, float]       # ear channel ends
    tab_y: tuple[tuple[float, float], tuple[float, float]]  # keeper tab pockets
    tab_x: tuple[float, float]
    z_tab: float     # pocket roof: the keeper's tabs are screwed up against it
    screws: tuple[tuple[float, float], tuple[float, float]]


def servo_mount() -> ServoMount:
    sv = servo_pose()
    c, sc = p.NOSE_DOOR_CLEARANCE, p.SERVO_CLEARANCE
    x_split = -c - p.NOSE_DOOR_SPLIT_PLATE
    x_back = sv.x_ear - p.KEEPER_CLEARANCE
    ey0, ey1 = sv.ear_y[0] - sc, sv.ear_y[1] + sc
    w = p.KEEPER_TAB_W
    x_screw = (x_split + x_back) / 2
    return ServoMount(x_split, sv.x_mount + p.MOUNT_PLATE_T, x_back, sv.z_hi + sc,
                      (sv.y_near - sc, sv.y_far + sc), (ey0, ey1), ((ey0 - w, ey0), (ey1, ey1 + w)),
                      (x_split + 0.6, sv.x_mount), p.KEEPER_TAB_T + p.KEEPER_CLEARANCE,
                      ((x_screw, ey0 - w / 2), (x_screw, ey1 + w / 2)))


def _retention_pad(g: NoseGeom, az: float) -> bd.Part:
    """Internal thickening for one radial M2.5 pilot: full depth from the bed, then a
    45 deg cone back out to the bore (no ledge); a revolve cut by a chord box, so its
    inner face is a true cylinder and its top a true cone across the whole pad."""
    r_in, r_w = p.RETAIN_PAD_R_IN, g.r_sh_in + 0.5
    z_full = p.RETAIN_PAD_Z_FULL
    ring = _revolve_rz([(r_in, 0.0), (r_w, 0.0), (r_w, z_full + (r_w - r_in)), (r_in, z_full)])
    w = p.RETAIN_PAD_HALF_CHORD
    return ring & (bd.Rot(0, 0, az) * _zprism(r_in - 3.0, r_w + 3.0, -w, w, -1.0, 40.0))


def _retention_pilot(g: NoseGeom, az: float) -> bd.Part:
    """Blind teardrop pilot along the radius at RETAIN_Z, countersunk 45 deg at the OD."""
    r_p, cs, z = p.RETAIN_PILOT / 2, p.RETAIN_MOUTH_CS, p.RETAIN_Z
    hole = _x_teardrop(r_p, p.RETAIN_PILOT_R0, g.r_sh + 1.0, 0.0, z)
    hole += _x_cone(r_p, r_p + cs + 0.5, g.r_sh - cs, g.r_sh + 0.5, 0.0, z)
    return bd.Rot(0, 0, az) * hole


def make_nose_door_housing() -> bd.Part:
    """Side-door nose housing: shoulder (with two airframe screw pads), band, one
    half-shell and the tip, plus the servo mount, spring pins, a ramp floor with the
    shock-cord hole, and a tie eye. Print upright, shoulder down."""
    g = nose_geom()
    shell, outer = g.shell, g.outer
    c = p.NOSE_DOOR_CLEARANCE
    z_d0, z_f = door_levels()
    sv = servo_pose()
    reach = 40.0
    housing = shell - _xz_extrude([(-c, z_d0), (reach, z_d0), (reach, door_joint_z(reach)), (-c, door_joint_z(-c))])
    # Chamfer the band's top outer edge on the door side: the door's bottom swings past
    # it, and a sharp edge there met the shell's revolve seam, which the mesh exporter
    # folded into non-manifold triangles. The cutter rises past the band top so none
    # of its faces is coplanar with it.
    ch, e = p.NOSE_DOOR_BAND_CHAMFER, 0.3
    ring = _revolve_rz([(R_BODY - ch - e, z_d0 + e), (R_BODY + 1.0, z_d0 + e), (R_BODY + 1.0, z_d0 - ch - 1.0)])
    housing -= ring & _zprism(-c, reach, -reach, reach, z_d0 - 5.0, z_d0 + 5.0)

    # One plate on the split face, printed from the bed: below the door it holds the
    # servo; above, it carries the spring pins. The servo slides up into it from the
    # shoulder's open base: a slot for the case, open at the bottom, and a channel for
    # the ears between a back wall and the mount plate, whose face they bear on. The
    # ear channel's roof rises at 45 deg past the case, so only the case slot is bridged.
    mt = servo_mount()
    x_split = mt.x_split
    plate = _xz_extrude([(x_split, 0.0), (mt.x_plate, 0.0), (mt.x_plate, z_d0 - 0.5), (-c, z_d0 - 0.5),
                         (-c, z_f), (x_split, z_f)]) & outer
    (sy0, sy1), (ey0, ey1), zs = mt.slot_y, mt.ear_y, mt.z_slot
    plate -= _zprism(x_split - 1.0, mt.x_plate + 1.0, sy0, sy1, -1.0, zs)
    plate -= _x_prism([(ey0, -1.0), (ey1, -1.0), (ey1, zs + ey1 - sy1), (sy1, zs), (sy0, zs), (ey0, zs + sy0 - ey0)],
                      mt.x_back, sv.x_mount)
    # Pockets for the keeper's two tabs, each with a blind pilot for its screw.
    for y0, y1 in mt.tab_y:
        plate -= _zprism(mt.tab_x[0], mt.tab_x[1], y0, y1, -1.0, mt.z_tab)
    for x, y in mt.screws:
        plate -= bd.Pos(x, y, mt.z_tab - 0.01) * bd.Cylinder(p.KEEPER_SCREW_PILOT / 2, p.KEEPER_PILOT_DEPTH + 0.01,
                                                            align=_align_min())
    housing += plate
    # Spring pins on the split face: a collar the spring's base coils sit on, then the
    # guide pin, whose tip locates the door when it is closed.
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
    xc, yc = cord_hole_xy()
    housing -= bd.Pos(xc, yc, z_f - 5.0) * bd.Cylinder(p.NOSE_DOOR_CORD_HOLE / 2, 35.0, align=_align_min())

    # Airframe retention: two pads with blind pilots for radial M2.5 x 8 self-tappers.
    for az in p.RETAIN_AZ:
        housing += _retention_pad(g, az)
    for az in p.RETAIN_AZ:
        housing -= _retention_pilot(g, az)
    return _finish(housing, "helios_nose_door_housing")


def make_nose_door() -> bd.Part:
    """Side door, in print orientation (floor block on the bed); the assembly lifts it
    by the band height. Its tab tucks inside the tip shell; its floor block holds the
    two spring pockets and the downward-open groove the servo arm latches into."""
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

    # Swing relief: about its hinge the door's bottom near the split first dips, by up
    # to (x_h - x)^2 / 2(z_h - z_d0), 0.6 mm at the split edge, before it rises clear of
    # the band. A plane from the hinge line up to NOSE_DOOR_SWING_RELIEF at the split
    # edge keeps it off the band ring all the way. Only the two side strips pass over
    # the ring; the middle stays flat, on the bed when printed (the strips' undersides
    # slope 3.8 deg and are only 0.9 mm high).
    x_h, dz = door_hinge().position.X, p.NOSE_DOOR_SWING_RELIEF
    k = dz / (x_h - c)
    yr = p.NOSE_DOOR_SWING_RELIEF_Y
    wedge = _xz_extrude([(c - 1.0, z_d0 - 1.0), (x_h, z_d0 - 1.0), (x_h, z_d0), (c - 1.0, z_d0 + dz + k)])
    door -= wedge - _zprism(c - 2.0, x_h + 1.0, -yr, yr, z_d0 - 2.0, z_d0 + dz + 2.0)
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
    return _finish(bd.Pos(0, 0, -z_d0) * door, "helios_nose_door")


def make_spring_dummies(extended: bool = False) -> list[bd.Part]:
    """The two compression springs as tubes (not printed): closed, or at free length."""
    c = p.NOSE_DOOR_CLEARANCE
    x_bottom, _, _ = door_spring_x()
    z_sp = door_levels()[0] + p.NOSE_DOOR_SPRING_Z
    length = p.SPRING_FREE_LEN if extended else x_bottom + c
    r_o = p.SPRING_OD_MAX / 2 - 0.1
    r_i = max(p.SPRING_ID_MIN, p.NOSE_DOOR_PIN_COLLAR_D) / 2 + 0.05  # envelope clears the collar
    springs = []
    for i, y in enumerate((-p.NOSE_DOOR_SPRING_Y, p.NOSE_DOOR_SPRING_Y)):
        coil = _x_cylinder(r_o, -c, -c + length, y, z_sp) - _x_cylinder(r_i, -c - 1.0, -c + length + 1.0, y, z_sp)
        springs.append(_finish(coil, f"spring_not_printed:{i + 1}", p.SPRING_COLOR))
    return springs


def keeper_lift() -> float:
    """The keeper is modelled printed (tabs on the bed); in place it sits this high."""
    return p.KEEPER_CLEARANCE


def make_servo_keeper() -> bd.Part:
    """Fills the servo slot and the ear channel under the servo, so the servo can't drop
    out of the shoulder base; a tab at each end takes an M2 x 8 self-tapper into the
    plate. Print it on its tabs; the screw heads sit flush in counterbores."""
    sv, mt = servo_pose(), servo_mount()
    kc = p.KEEPER_CLEARANCE
    z0, z_top = keeper_lift(), sv.z_lo - 0.1
    (sy0, sy1), (ey0, ey1) = mt.slot_y, mt.ear_y
    keeper = _zprism(mt.x_split, mt.x_plate, sy0 + kc, sy1 - kc, z0, z_top)
    keeper += _zprism(mt.x_back + kc, sv.x_mount - kc, ey0 + kc, ey1 - kc, z0, z_top)
    # Each tab fills its pocket and joins the column through the ear channel's end.
    for y0, y1 in mt.tab_y:
        keeper += _zprism(mt.tab_x[0] + kc, mt.tab_x[1] - kc, y0 + kc, y1 - kc, z0, mt.z_tab)
        yj = y1 if y1 <= ey0 else y0
        keeper += _zprism(mt.x_back + kc, sv.x_mount - kc, yj - kc - 0.5, yj + kc + 0.5, z0, mt.z_tab)
    for x, y in mt.screws:
        keeper -= bd.Pos(x, y, z0 - 1.0) * bd.Cylinder(p.KEEPER_SCREW_CLEAR / 2, mt.z_tab - z0 + 2.0, align=_align_min())
        keeper -= bd.Pos(x, y, z0 - 1.0) * bd.Cylinder(p.KEEPER_HEAD_D / 2, p.KEEPER_HEAD_DEPTH + 1.0, align=_align_min())
    return _finish(bd.Pos(0, 0, -z0) * keeper, "helios_nose_servo_keeper")


def make_servo_dummy(arm_angle: float = 0.0, drop: float = 0.0) -> bd.Part:
    """MG90S envelope with its single-arm horn, for fit checks (not printed).
    arm_angle 0 = latched (arm up in the door groove); -60 = released (arm toward +y).
    drop lowers it along -z, down the path it is slid in by."""
    sv = servo_pose()
    xb = sv.x_bottom
    x_case = xb + p.SERVO_CASE_H
    servo = _zprism(xb, x_case, sv.y_near, sv.y_far, sv.z_lo, sv.z_hi)
    servo += _zprism(sv.x_ear, sv.x_mount, sv.ear_y[0], sv.ear_y[1], sv.z_lo, sv.z_hi)
    servo += _x_cylinder(p.SERVO_DOME_R, x_case - 0.01, xb + p.SERVO_DOME_H, 0.0, sv.z_shaft)
    servo += _x_cylinder(2.4, xb + p.SERVO_DOME_H - 0.01, xb + p.SERVO_SPLINE_H, 0.0, sv.z_shaft)
    x_arm0 = xb + p.SERVO_ARM_TOP - p.SERVO_ARM_T
    horn = _x_cylinder(p.SERVO_HUB_R, xb + p.SERVO_DOME_H + 0.2, x_arm0 + p.SERVO_ARM_T, 0.0, sv.z_shaft)
    r_tip, L = p.SERVO_ARM_W / 2, p.SERVO_ARM
    tip = [(r_tip * math.cos(math.radians(d)), sv.z_shaft + L - r_tip + r_tip * math.sin(math.radians(d)))
           for d in range(0, 181, 15)]
    horn += _x_prism([(-3.5, sv.z_shaft), (3.5, sv.z_shaft), *tip], x_arm0, x_arm0 + p.SERVO_ARM_T)
    horn = horn.rotate(bd.Axis((0, 0, sv.z_shaft), (1, 0, 0)), arm_angle)
    return _finish(bd.Pos(0, 0, -drop) * (servo + horn), "servo_mg90s_not_printed", p.HARDWARE_COLOR)


def make_screw_dummies() -> list[bd.Part]:
    """The two M2.5 x 8 retention screws as plain cylinders (not printed), seated: the
    head on the airframe's OD, the shank through the tube wall into the pilot."""
    out = []
    for i, az in enumerate(p.RETAIN_AZ):
        shank = _x_cylinder(1.0, R_BODY - 8.0, R_BODY, 0.0, p.RETAIN_Z)  # drawn at the root, inside the pilot
        head = _x_cylinder(2.25, R_BODY, R_BODY + 1.8, 0.0, p.RETAIN_Z)
        out.append(_finish(bd.Rot(0, 0, az) * (shank + head), f"m2_5x8_not_printed:{i + 1}", p.HARDWARE_COLOR))
    return out
