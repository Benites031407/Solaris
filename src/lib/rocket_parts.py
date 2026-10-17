"""Parametric factories for the Scorpio replica parts (build123d, millimetres).

Each factory returns one closed solid in its print orientation (see params.py).
Every downward-facing surface is either on the bed, a short bridge, or 45 deg or
steeper, so no part needs support material.
"""

from __future__ import annotations

import math

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


def make_nose_cone() -> bd.Part:
    """Hollow tangent-ogive nose cone with a blunted tip, shoulder and shock-cord bar."""
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
    nose = solid - bd.revolve(bd.Face(bd.Wire(cavity_edges)), bd.Axis.Z)

    # Shock-cord bar across the shoulder base (printed on the bed, ridge-topped).
    w, h = p.NOSE_BAR_WIDTH, p.NOSE_BAR_HEIGHT
    sec = [(-w / 2, 0), (w / 2, 0), (w / 2, h - 2), (w / 4, h), (-w / 4, h), (-w / 2, h - 2)]
    bar_face = bd.Face(bd.Wire.make_polygon([V(0, y, z) for y, z in sec], close=True))
    bar = bd.extrude(bar_face, amount=r_sh_in + 1.0, dir=(1, 0, 0), both=True)
    bar = bar & bd.Cylinder(r_sh_in + 1.0, h + 1, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return _finish(nose + bar, "nose_cone")


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


def fin_slot_radii() -> tuple[float, float]:
    """Inner and outer radius of the T-slot flange channel."""
    r_in = p.FIN_FLANGE_INNER_R - p.SLOT_CLEARANCE
    return r_in, p.FIN_FLANGE_INNER_R + p.FIN_FLANGE_THICKNESS + p.SLOT_CLEARANCE


def engine_stop_z() -> float:
    """Motor tube / motor forward end: the motor's aft face ends flush with the male retainer."""
    return p.MOTOR_LEN - (p.MALE_BAND_LEN + p.MALE_THREAD_LEN)


def make_fin_can() -> bd.Part:
    """Fin can: T-slots for 3 fins, motor-tube bore with engine block, aft lug and guide."""
    R = R_BODY
    r_stub = (p.BODY_ID - p.GLUE_FIT) / 2
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

    # T-slots, open at the aft face so the fins slide in from below.
    ch_in, ch_out = fin_slot_radii()
    neck_half = p.FIN_THICKNESS / 2 + p.SLOT_CLEARANCE
    ch_half = p.FIN_FLANGE_WIDTH / 2 + p.SLOT_CLEARANCE + 0.05
    lean = SHOULDER_SLOPE * (ch_half - neck_half)  # matches the fin's shoulder lean
    slot = _zextrude(_xy_polygon([
        (ch_in, -ch_half), (ch_out, -ch_half), (ch_out - lean, -neck_half), (R + 1.0, -neck_half),
        (R + 1.0, neck_half), (ch_out - lean, neck_half), (ch_out, ch_half), (ch_in, ch_half),
    ]), -1.0, p.FIN_SLOT_TOP)
    for i in range(p.FIN_COUNT):
        body -= bd.Rot(0, 0, p.FIN_ANGLE0 + i * 360.0 / p.FIN_COUNT) * slot

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
    """One fin standing on its trailing edge; the T-rail root runs along x < 0."""
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
    x_fl_in = p.FIN_FLANGE_INNER_R - R_BODY
    x_fl_out = x_fl_in + p.FIN_FLANGE_THICKNESS
    w = p.FIN_FLANGE_WIDTH / 2
    lean = SHOULDER_SLOPE * (w - t / 2)  # flange slightly thinner at the neck
    rail = _zextrude(_xy_polygon([
        (x_fl_in, -w), (x_fl_out, -w), (x_fl_out - lean, -t / 2), (0.0, -t / 2),
        (0.0, t / 2), (x_fl_out - lean, t / 2), (x_fl_out, w), (x_fl_in, w),
    ]), 0.0, p.FIN_ROOT_LEN)
    return _finish(web + rail, "fin")


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
