"""SRM100-102 nozzle holder (aft closure), 304 stainless: two A3 sheets.

Sheet 1 (2:1): half section in the plane of hole 0, details D (case gland + nose),
E (insert gland) and F (retaining lip) at 5:1, the seal-diameter table.
Sheet 2 (1:1): SECTION C-C through the radial tapped holes, VIEW G on the aft end
(puller threads), notes.

View frame of the main view: u = motor z (forward to the RIGHT), v = radius (model x).
The part is turned rot = -0.8 so that hole 0 (theta 0.8 deg) lies in the section
plane of the upper half.  Face B (flange forward face) is motor z = 0, so axial
positions from B are motor z directly.  SECTION C-C and VIEW G are seen from aft:
paper angle = 180 - theta, theta running clockwise on the paper.
"""

import math

import numpy as np
from shapely.geometry import Point

import srm_dwg as D
import srm_params as P
import nozzle_holder as NH
from srm_dwg import DEG, DEPTH, DIA, GDT, PM, TIMES, Hatch, Part, Sheet, View, fmt

# ---- geometry (the numbers the STEP was built from) ----------------------------------
R_LAND, R_GROOVE, R_FL = NH.R_LAND, NH.R_GROOVE, NH.R_FL
R_BORE, R_IG, R_BODY = NH.R_BORE, NH.R_IGROOVE, NH.R_BODY
R_LIP, R_LIP_AFT = NH.R_LIP, NH.R_LIP_AFT
Z_FACE, Z_SEAT, Z_AFT, Z_FL = NH.Z_FACE, NH.Z_SEAT, NH.Z_AFT, NH.Z_FL
NOSE_Z, NOSE_R = NH.NOSE_Z, P.PLUG_NOSE_CHAMFER
LEAD_Z, LEAD_R = P.HOLDER_BORE_LEAD_IN, NH.LEAD_R
GR, BRK, UNDER, BODY_R, SEAT_R, ET = NH.GR, NH.BRK, NH.UNDER, NH.BODY_R, NH.SEAT_R, NH.ET
GW, IGW = P.GROOVE_W, P.INSERT_GROOVE_W
G1, G2 = sorted((P.GROOVE_1_Z, P.GROOVE_2_Z))
ZIG = P.INSERT_GROOVE_Z
ZH = P.bolt_z_aft()                                   # radial hole row, from B
TH = P.bolt_thetas()
PTH = P.puller_thetas()
R_PUL = P.HOLDER_PULLER_R
DRILL_D = P.BOLT_TAP_DRILL
M_D = P.BOLT_D
ENGAGE = P.BOLT_L_AFT - P.CASE_WALL - P.PLUG_CLEAR   # 5.97 in the steel
T_DEPTH = ENGAGE + P.THREAD_OVER                     # full thread from the land, 7.97
D_DEPTH = T_DEPTH + P.DRILL_OVER                     # tap drill (full dia) from the land, 9.97
R_TEND = R_LAND - T_DEPTH                            # thread limit radius, 38.0
PUL_D_DEPTH = P.HOLDER_PULLER_DEPTH                  # puller drill, 10
PUL_T_DEPTH = PUL_D_DEPTH - P.DRILL_OVER             # puller full thread, 8 (drafting choice)
MASS = 1501.2
ROT = -TH[0]

THREAD = f"M{fmt(M_D, 0)}{TIMES}{fmt(P.BOLT_PITCH, 0)}-6H"
HOLE_TXT = [f"{len(TH)}{TIMES} {THREAD} {DEPTH}{fmt(T_DEPTH, 1)}",
            f"{DIA}{fmt(DRILL_D, 1)} {DEPTH}{fmt(D_DEPTH, 1)}"]
PUL_TXT = [f"{len(PTH)}{TIMES} {THREAD} {DEPTH}{fmt(PUL_T_DEPTH, 1)}",
           f"{DIA}{fmt(DRILL_D, 1)} {DEPTH}{fmt(PUL_D_DEPTH, 1)}"]
TOL_LAND = ("0", "-0.02")
TOL_GROOVE = ("0", "-0.04")
TOL_W = ("+0.08", "0")
TOL_BORE = ("+0.025", "0")
TOL_IG = ("+0.05", "0")
TOL_SEAT = ("+0.05", "0")
TOL_R04 = PM + "0.1"
TOL_R01 = ("+0.03", "-0.02")
TOL_R08 = PM + "0.1"
TOL_LIP = ("+0.1", "0")                               # G9: aft face -> lip seat
# G1-rev: the seal diameters follow the recorded honed bore A of the case (SRM100-101):
# A = the smallest reading in the zone, the zone held to A +0.030/0, never over 92.10
A_MIN, A_MAX = P.CASE_ID, P.SEAL_A_MAX               # 92.000 ... 92.070
A_TOL = P.TOL_BORE[1]                                # (the local TOL_BORE is the insert bore's)
assert P.TOL_BORE[0] == 0.0 and abs(A_MAX + A_TOL - P.CASE_BORE_MAX) < 1e-9
LAND_OFF = P.CASE_ID - P.PLUG_OD                     # land = A - 0.06
GROOVE_OFF = P.CASE_ID - P.ORING_GROOVE_D            # grooves = A - 5.67
assert (P.TOL_LAND[0], P.TOL_GROOVE[0]) == (float(TOL_LAND[1]), float(TOL_GROOVE[1]))
# G20: SRM100-101 op 130 leaves the ream's entry cone in the holder, 0.5 deep max,
# DIA CASE_HOLE_D at the land; it lies inside the THREAD_LOST that the strength check drops
REAM_CONE = 0.5
assert REAM_CONE <= P.THREAD_LOST
# G17: temperature labels on the aft body at theta 90 / 270, clear of the cap tape, which
# runs at theta 0 / 180 onto the aft body, its ends at most 15 from the aft face
# (SRM100-106 note 6).  A 15 wide band (as on the case, SRM100-101 note 8) centred in
# the body length left between the tape ends and the R2 root, in motor z (= from B).
LABEL_TH = (90.0, 270.0)
TAPE_ON = 15.0
LAB_W = 15.0
_zc = 0.5 * ((Z_AFT + TAPE_ON) + (Z_FL - BODY_R))
LAB_Z = (float(round(_zc - LAB_W / 2.0)), float(round(_zc + LAB_W / 2.0)))    # (-30, -15)
assert LAB_Z[0] - (Z_AFT + TAPE_ON) >= 5.0 and (Z_FL - BODY_R) - LAB_Z[1] >= 5.0, LAB_Z
# match-drilling depth stops, set from the case OD (the land is covered by the case)
R_CASE_OD = P.CASE_OD / 2.0
STOP_DRILL = R_CASE_OD - (R_LAND - D_DEPTH)          # full dia 5 to 14.0 below the case OD
STOP_THREAD = R_CASE_OD - (R_LAND - T_DEPTH)         # full thread to 12.0
TIP_H = DRILL_D / 2.0 / math.tan(math.radians(59.0)) # 118 deg drill point
WALL_TIP = R_LAND - D_DEPTH - TIP_H - R_BORE         # drill point -> insert bore, 2.71
SUB = f"Aft closure - {len(TH)}{TIMES} M6 radial - insert bore {DIA}{fmt(2 * R_BORE)}"
MATERIAL = "304 stainless (1.4301)\nASTM A479 annealed bar"
USED_ON = "USED ON: SRM100-000 item 2; SRM100-001 item 2"
STEP = "nozzle_holder.step"
HATCH = Hatch(45, 2.0)


# ---- local primitives ----------------------------------------------------------------
def _tol_w(s, tol):
    if isinstance(tol, (tuple, list)):
        return max(s.text_width(str(t), D.H * 0.72) for t in tol) + 0.6
    return s.text_width(" " + str(tol)) if tol else 0.0


def unit_ang(a):
    return np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])


def rad_concave(v, center, r, ang, length, text, tol=None, side=None):
    """Radius of a concave fillet whose centre lies in open air (ISO 129-1): arrow on the
    arc at polar angle `ang` (view frame) pointing away from the centre, the dimension
    line back through the centre and on `length` paper mm into the air, then a
    horizontal reference line carrying the value."""
    s = v.sheet
    c = v.pt(*center)
    d = unit_ang(ang)
    p = c + d * r * v.scale
    q = c - d * length
    s.line([p, q], D.THIN)
    s.arrow(p, d)
    sg = side if side is not None else (1.0 if -d[0] >= 0 else -1.0)
    w = s.text_width(text) + _tol_w(s, tol) + 1.6
    s.line([q, q + (sg * w, 0.0)], D.THIN)
    v._dimtext((q[0] + sg * 0.8, q[1] + D.TEXT_GAP), 0.0, text, tol,
               anchor="left" if sg > 0 else "right")


def thread_side(v, u_c, r_top, r_end, d_major):
    """ISO 6410-1 internal thread cut lengthwise, hole axis along v: thin lines at the
    major diameter from the entry to the thread limit, thick limit line across."""
    h = d_major / 2.0
    for du in (-h, h):
        v.line([(u_c + du, r_top), (u_c + du, r_end)], D.THIN)
    v.line([(u_c - h, r_end), (u_c + h, r_end)], D.THICK)


def thread_radial(s, c, ang, r_entry, r_end, d_major):
    """The same for a radial hole in an end view: axis at paper angle `ang` from the
    view centre c, entry on the circle r_entry."""
    e, h = unit_ang(ang), d_major / 2.0
    n = np.array([-e[1], e[0]])
    for t in (-h, h):
        rho0 = math.sqrt(r_entry ** 2 - t ** 2)
        s.line([c + e * rho0 + n * t, c + e * r_end + n * t], D.THIN)
    s.line([c + e * r_end - n * h, c + e * r_end + n * h], D.THICK)


def thread_end(s, c, d_major, a0=95.0, a1=355.0):
    """ISO 6410-1 end view of an internal thread: thin ~3/4 circle at the major
    diameter (the drill circle is the model's thick outline); gap upper right."""
    s.circle(c, d_major / 2.0, D.THIN, a0=a0, a1=a1)


def thread_oblique(v, th_rot, z_c, R, d_major):
    """Major-diameter outline (thin, ~3/4) of a radial tapped hole at azimuth th_rot
    (the view's rotated frame) seen from +Y in a side view: the intersection of the
    major cylinder with the land cylinder R, projected (u = z, v = x)."""
    th, rho = math.radians(th_rot), d_major / 2.0
    er = np.array([math.cos(th), math.sin(th)])
    et = np.array([-math.sin(th), math.cos(th)])
    pts = []
    for phi in np.radians(np.linspace(5.0, 265.0, 90)):
        t, dz = rho * math.sin(phi), rho * math.cos(phi)
        xy = math.sqrt(R ** 2 - t ** 2) * er + t * et
        pts.append((z_c + dz, xy[0]))
    v.line(pts, D.THIN)


def cut_plane(v, u, v_lo, v_hi, letter, look=(1.0, 0.0), ext=1.5, thick=5.0, arr=6.0):
    """Cutting plane (ISO 128-44) at u in a side view, shown by its thick ends only
    (the chain inside the view is the holes' centre line, drawn separately): thick
    ends from `ext` outside the outline, arrows along `look`, the letter beyond."""
    s = v.sheet
    x = v.pt(u, 0)[0]
    y_lo, y_hi = v.pt(0, v_lo)[1], v.pt(0, v_hi)[1]
    L_ = np.asarray(look, float)
    for sg, yb in ((1.0, y_hi), (-1.0, y_lo)):
        e0 = np.array([x, yb + sg * ext])
        e1 = e0 + (0.0, sg * thick)
        s.line([e0, e1], 0.7, cap="butt")
        s.line([e1, e1 + L_ * arr], D.THIN)
        s.arrow(e1 + L_ * arr, L_)
        t = e1 + (0.0, sg * 2.2)
        s.text(t[0], t[1] if sg > 0 else t[1] - 3.5, letter, 3.5, ha="center")


def view_arrow(s, tip, direction, letter, length=12.0):
    """Reference arrow for a view (ISO 128-30), letter at the tail."""
    d = D._unit(direction)
    tip = np.asarray(tip, float)
    tail = tip - d * length
    s.line([tail, tip - d * D.ARROW_L * 0.5], D.THIN)
    s.arrow(tip, d)
    s.text(tail[0] + d[0] * 2.0, tail[1] + 1.8, letter, 3.5, ha="center")


def detail(v, center, radius, scale, origin, letter, circle_label_ang=45.0, label_gap=5.0):
    """View.detail with the label 'DETAIL <L> (<scale>)'."""
    s = v.sheet
    v.circle(center, radius, D.THIN)
    tp = v.pt(*center) + unit_ang(circle_label_ang) * (radius * v.scale + 3.0)
    s.text(tp[0], tp[1] - 1.75, letter, 3.5, ha="center")
    dv = View.__new__(View)
    dv.sheet, dv.parts, dv.geo = s, v.parts, v.geo
    dv.scale, dv.look, dv.section, dv.z_cut = scale, v.look, v.section, v.z_cut
    dv.hidden, dv.smooth, dv.window = v.hidden, v.smooth, None
    dv.origin = np.asarray(origin, float) - scale * np.asarray(center, float)
    dv.clip = Point(*np.asarray(origin, float)).buffer(radius * scale, 256)
    dv.draw(axis=False)
    s.circle(origin, radius * scale, D.THIN)
    s.text(origin[0], origin[1] - radius * scale - label_gap - 3.5,
           f"DETAIL {letter} ({D.scale_str(scale)})", 3.5, ha="center")
    return dv


def dim_h_text_left(v, u_a, u_b, vv, text, tol=None):
    """Horizontal dimension too short for its text: arrows outside pointing in, the
    value on the line extended to the LEFT (clear of what lies right of u_b)."""
    s = v.sheet
    xa, xb = sorted((v.pt(u_a, 0)[0], v.pt(u_b, 0)[0]))
    y = v.pt(0, vv)[1]
    tw = s.text_width(text) + _tol_w(s, tol)
    tail = D.ARROW_L + 1.5
    s.arrow((xa, y), (1.0, 0.0))
    s.arrow((xb, y), (-1.0, 0.0))
    s.line([(xa - tail - tw - 1.0, y), (xb + tail, y)], D.THIN)
    v._dimtext((xa - tail - tw / 2.0 - 0.5, y + D.TEXT_GAP), 0.0, text, tol)


def dia_short(v, u, r, length, text, tol=None):
    """Diameter on a detail whose axis lies outside it (ISO 129-1, shortened dimension
    line): one arrow on the feature at (u, r), the line toward the axis `length` paper
    mm, the value along it."""
    s = v.sheet
    tip = v.pt(u, r)
    sgn = -1.0 if r > 0 else 1.0
    end = tip + (0.0, sgn * length)
    s.line([tip, end], D.THIN)
    s.arrow(tip, tip - end)
    v._dimtext((tip[0] - D.TEXT_GAP, tip[1] + sgn * length / 2.0), 90.0, text, tol)


def rot_flag(s, x_line, y_centre, main, tol, flag):
    """A rotated note flag ('(NOTE 2)') after a vertical dimension's text."""
    W = s.text_width(main) + _tol_w(s, tol)
    s.text(x_line - D.TEXT_GAP, y_centre + W / 2.0 + 1.5, flag, D.H, rot=90.0)


def dia_end(s, c, r, ang, text, tol=None, gap=1.5):
    """Diameter in an end view: dimension line through the centre at `ang`, arrows on
    the circle, the value `gap` paper mm outside the circle on the extended line."""
    d = unit_ang(ang)
    c = np.asarray(c, float)
    W = s.text_width(text) + _tol_w(s, tol)
    a, b = c - d * r, c + d * r
    s.line([a, b + d * (gap + W + 1.5)], D.THIN)
    s.arrow(a, -d)
    s.arrow(b, d)
    rot = ang if -90.0 < ang <= 90.0 else ang - 180.0
    dt = unit_ang(rot)
    n = np.array([-dt[1], dt[0]])                    # the text's 'up', as _dimtext uses
    tp = b + d * (gap + W / 2.0) + n * D.TEXT_GAP
    View._dimtext(_Dummy(s), tp, rot, text, tol)


class _Dummy:
    """Lets View._dimtext run against a bare sheet."""
    def __init__(self, s):
        self.sheet = s


def pol(c, r, ang):
    return np.asarray(c, float) + r * unit_ang(ang)


# =====================================================================================
# SHEET 1
# =====================================================================================
sh = Sheet("SRM100-102", "NOZZLE HOLDER", SUB, size="A3", material=MATERIAL, mass_g=MASS,
           scale="2:1", sheet=(1, 2))
O1 = np.array([152.0, 140.0])
part = Part(STEP, hatch=HATCH)
v = View(sh, part, O1, 2.0, look="side", section="half", rot=ROT)
X = lambda u: v.pt(u, 0)[0]
Y = lambda vv: v.pt(0, vv)[1]

# ---- hole 0 in the section plane (ISO 6410 thread), the other holes' threads outside -
thread_side(v, ZH, R_LAND, R_TEND, M_D)
for th in TH:
    t_rot = th + ROT
    if 90.0 < t_rot < 170.0:           # holes seen on the lower (outside) half
        thread_oblique(v, t_rot, ZH, R_LAND, M_D)
CUT_EXT = 1.5                          # paper mm, outline -> thick end of the plane
v.line([(ZH, R_BORE + 1.2), (ZH, R_LAND + CUT_EXT / v.scale)], D.THIN, "center")   # hole 0
v.line([(ZH, -3.0), (ZH, -R_LAND - CUT_EXT / v.scale)], D.THIN, "center")         # the row
cut_plane(v, ZH, -R_LAND, R_LAND, "C", ext=CUT_EXT)
# hole row from B, in the outside half, to the row's centre line
v.dim_h((0.0, -15.0), (ZH, -15.0), at=-15.0, ext=(False, False))

# ---- axial positions from B (top rows) --------------------------------------------------
for zc, at in ((G1, 55.0), (G2, 59.0)):
    v.line([(zc, R_GROOVE - 0.6), (zc, at + 1.0)], D.THIN, "center")
    v.dim_h((0.0, R_FL - BRK), (zc, at), at=at, ext=(True, False))
v.dim_h((0.0, R_FL - BRK), (Z_FACE, R_LAND - NOSE_R), at=63.0)
v.dim_h((Z_AFT, R_BODY - BRK), (Z_FACE, R_LAND - NOSE_R), at=67.0, ref=True)
# datum B on the extension line of the flange forward face, B square to A
v.datum((0.0, 57.0), "B", (-1, 0), length=4.0)
pB = v.pt(0.0, 61.0)
fw = 2 * 6.5 + sh.text_width("0.02") + 2.4
sh.fcf(pB[0] - 5.0 - fw, pB[1] - 3.25, ["perpendicularity", "0.02", "A"], leader=pB)

# ---- right: land (datum A), bore, lead-in ------------------------------------------------
v.dim_dia_half(34.5, R_LAND, at=46.0, tol=TOL_LAND)
rot_flag(sh, X(46.0), (Y(R_LAND) + O1[1]) / 2.0, DIA + fmt(2 * R_LAND), TOL_LAND, "(NOTE 2)")
v.datum((46.0, R_LAND), "A", (0, 1), length=4.0)
v.dim_dia_half(36.0, R_BORE, at=42.0, tol=TOL_BORE)
v.fcf((42.0, -1.0), 4.0, -10.0, ["coaxiality", DIA + "0.05", "A"])
v.finish((-24.0, R_BORE), "Ra 0.8", leader=(6.0, -12.0))
dim_h_text_left(v, Z_FACE - LEAD_Z, Z_FACE, 27.0, fmt(LEAD_Z))
v.dim_ang((Z_FACE - LEAD_Z, R_BORE), 180.0, 180.0 + math.degrees(math.atan2(LEAD_R, LEAD_Z)),
          18.0, dec=0)

# ---- in the bore: seat depth, insert gland position, seat parallel to B, lip bore ------
v.dim_h((Z_SEAT, 24.0), (Z_FACE, 24.0), at=24.0, tol=TOL_SEAT, ext=(False, False), shift=27.0)
v.dim_h((ZIG + IGW / 2.0, 20.0), (Z_FACE, 20.0), at=20.0, ext=(False, False))
# seat face parallel to B: arrow on the seat face (section), from the bore side
pS = v.pt(Z_SEAT, 28.5)
sh.fcf(pS[0] + 6.5, pS[1] - 3.25, ["parallelism", "0.02", "B"], leader=pS)
v.dim_dia_half(Z_SEAT, R_LIP, at=-48.0)

# ---- left: aft body, breaks, R2 ---------------------------------------------------------
v.dim_dia_half(-40.0, -R_BODY, at=-40.0)
# temperature-label band on the aft body OD (G17, note 8): thick chain line beside it
yl = Y(-R_BODY) - 1.3
sh.line([(X(LAB_Z[0]), yl), (X(LAB_Z[1]), yl)], D.THICK, "center")
v.leader((0.5 * (LAB_Z[0] + LAB_Z[1]), -R_BODY - 0.65), -12.0, -17.0,
         ["TEMPERATURE LABELS AT " + chr(952) + " " + fmt(LABEL_TH[0], 0) + DEG + " / "
          + fmt(LABEL_TH[1], 0) + DEG + ",",
          fmt(-LAB_Z[1], 0) + " ... " + fmt(-LAB_Z[0], 0) + " FROM B (NOTE 8)"], end="dot")
v.leader((Z_AFT + BRK / 2, R_BODY - BRK / 2), 8.0, 10.0, "0.5" + TIMES + "45" + DEG)
v.leader((Z_FL + BRK / 2, R_FL - BRK / 2), -8.0, 3.0, "2" + TIMES + " 0.5" + TIMES + "45" + DEG)
rad_concave(v, (Z_FL - BODY_R, R_BODY + BODY_R), BODY_R, 315.0, 8.0, "R" + fmt(BODY_R))
view_arrow(sh, (v.pt(Z_AFT, 0)[0] - 3.5, v.pt(0, -20.0)[1]), (1.0, 0.0), "G", length=14.0)

# ---- lower half: flange, groove diameter, R0.5 -----------------------------------------
v.dim_h((Z_FL, -(R_FL - BRK)), (0.0, -(R_FL - BRK)), at=-54.0)
rad_concave(v, (UNDER, -(R_LAND + UNDER)), UNDER, 135.0, 7.0, "R" + fmt(UNDER))
u_g = G1 + 1.2
v.dim_dia_half(u_g, -R_GROOVE, at=u_g, pre="2" + TIMES + " ", tol=TOL_GROOVE)
rot_flag(sh, X(u_g), (Y(-R_GROOVE) + O1[1]) / 2.0, "2" + TIMES + " " + DIA + fmt(2 * R_GROOVE),
         TOL_GROOVE, "(NOTE 2)")

# ---- detail indicators, details --------------------------------------------------------
dD = detail(v, (33.0, 44.3), 5.6, 5.0, (305.0, 250.0), "D", circle_label_ang=135.0)
dE = detail(v, (-3.0, 32.2), 4.2, 5.0, (290.0, 176.0), "E", circle_label_ang=270.0)
dF = detail(v, (-47.5, 29.5), 4.5, 5.0, (367.0, 176.0), "F", circle_label_ang=165.0)

# D: case gland (both alike) and the nose chamfer
z0, z1 = G2 - GW / 2.0, G2 + GW / 2.0
dD.dim_h((z0, R_GROOVE + 2.2), (z1, R_GROOVE + 2.2), at=R_GROOVE + 2.2, tol=TOL_W,
         ext=(False, False))
dD.dim_rad((z0 + GR, R_GROOVE + GR), GR, 225.0, length=9.0,
           text="2" + TIMES + " R" + fmt(GR), tol=TOL_R04)
dD.dim_rad((z1 + ET, R_LAND - ET), ET, 135.0, length=7.0,
           text="2" + TIMES + " R" + fmt(ET), tol=TOL_R01)
dD.dim_v((Z_FACE - NOSE_Z, R_LAND), (Z_FACE, R_LAND - NOSE_R), at=40.0)
dD.dim_ang((Z_FACE - NOSE_Z, R_LAND), 330.0, 360.0, 26.0, dec=0)
dD.finish((34.6, R_LAND), "Ra 1.6", leader=(5.0, 9.0))
sh.finish_symbol(dD.pt(z0 + 1.0, R_GROOVE), "Ra 0.8")
sh.text(305.0, 250.0 - 28.0 - 5.0 - 3.5 - 4.5, "BOTH CASE GROOVES ALIKE, WALLS Ra 1.6", D.H,
        ha="center")

# E: insert gland (same corner radii as the case glands: NH.GR, NH.ET)
e0, e1 = ZIG - IGW / 2.0, ZIG + IGW / 2.0
dE.dim_h((e0, 29.2), (e1, 29.2), at=29.2, tol=TOL_W, ext=(False, False), shift=-2.0)
dia_short(dE, ZIG + 1.4, R_IG, 21.85, DIA + fmt(2 * R_IG), TOL_IG)
sh.text(290.0, 176.0 - 21.0 - 5.0 - 3.5 - 4.5, "R" + fmt(GR) + " AND R" + fmt(ET)
        + " AS DETAIL D", D.H, ha="center")

# F: retaining lip, seat root
dF.dim_h((Z_AFT, R_LIP_AFT), (Z_SEAT, R_LIP), at=26.0, ext=(False, False), tol=TOL_LIP)
dF.dim_ang((Z_SEAT, R_LIP), 180.0 - P.HOLDER_LIP_BORE_DEG, 180.0, 20.0, dec=0)
rad_concave(dF, (Z_SEAT + SEAT_R, R_BORE - SEAT_R), SEAT_R, 135.0, 14.0, "R" + fmt(SEAT_R),
            tol=TOL_R08)
# seat face finish: on a leader to the seat face's far-side edge line in the main view
# (in F the far-wall line of the R0.8 tangent edge runs 4 mm off the face)
v.finish((Z_SEAT, 15.0), "Ra 1.6", leader=(8.0, -8.0))

# ---- seal-diameter table, cross references ------------------------------------------
TX, TY = 256.0, 116.0
sh.text(TX, TY + 3.0, "SEAL DIAMETERS FROM THE MEASURED CASE BORE A (NOTE 2)", D.H, bold=True)
tl = lambda t: f"{t[0]}/{t[1]}"
f2 = lambda x: f"{x:.2f}"
rows = [["FEATURE", "CUT TO", f"A = {A_MIN:.3f} (DRAWN)", f"A = {A_MAX:.3f} (MAX)"],
        ["Land (datum A)", "A - " + f2(LAND_OFF) + " " + tl(TOL_LAND),
         DIA + f2(A_MIN - LAND_OFF) + " " + tl(TOL_LAND),
         DIA + f2(A_MAX - LAND_OFF) + " " + tl(TOL_LAND)],
        [f"Case grooves (2{TIMES})", "A - " + f2(GROOVE_OFF) + " " + tl(TOL_GROOVE),
         DIA + f2(A_MIN - GROOVE_OFF) + " " + tl(TOL_GROOVE),
         DIA + f2(A_MAX - GROOVE_OFF) + " " + tl(TOL_GROOVE)],
        ["Case bore A", "recorded: ______", f"{A_MIN:.3f}", f"{A_MAX:.3f}"]]
yt = sh.table(TX, TY, [34, 36, 37, 37], rows, row_h=6.0, align=["l", "l", "l", "l"])
sh.text(TX, yt - 4.5, "A = the smallest reading in the case's aft seal zone, honed and recorded",
        D.H)
sh.text(TX, yt - 8.5, "on SRM100-101 (op 30, R4): " + f"{A_MIN:.3f} {chr(8804)} A {chr(8804)} "
        + f"{A_MAX:.3f}; the zone is held to A +{A_TOL:.3f}/0, {chr(8804)} "
        + f"{P.CASE_BORE_MAX:.2f}.", D.H)
sh.text(TX, yt - 15.0, "Upper half: section in the plane of hole 0 (" + chr(952) + " "
        + fmt(TH[0], 1) + DEG + "). SECTION C-C, VIEW G and", D.H)
sh.text(TX, yt - 19.0, "the NOTES (for both sheets) are on sheet 2.", D.H)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")
sh.text(sh.tb[2] - 2.0, sh.tb[3] + 3.0, USED_ON, D.H, ha="right")


# =====================================================================================
# SHEET 2
# =====================================================================================
sh2 = Sheet("SRM100-102", "NOZZLE HOLDER", SUB, size="A3", material=MATERIAL, mass_g=MASS,
            scale="1:1", sheet=(2, 2))
phi = lambda th: 180.0 - th                          # theta -> paper angle, seen from aft

# ---- SECTION C-C through the hole row ----------------------------------------------------
CC = np.array([118.0, 205.0])
vc = View(sh2, Part(STEP, hatch=HATCH), CC, 1.0, look="aft", z_cut=ZH, keep="above")
sh2.line([CC - (68.0, 0.0), CC + (52.0, 0.0)], D.THIN, "center")
sh2.line([CC - (0.0, 52.0), CC + (0.0, 52.0)], D.THIN, "center")
for th in TH:
    a = phi(th)
    sh2.line([pol(CC, R_BORE - 3.0, a), pol(CC, R_LAND + 4.0, a)], D.THIN, "center")
    thread_radial(sh2, CC, a, R_LAND, R_TEND, M_D)
# angles: hole 0 off theta = 0, the even pattern
vc.dim_ang((0.0, 0.0), phi(TH[0]), 180.0, 64.0, ext=False, text_r=66.0, text_dy=2.2)
sh2.line([pol(CC, R_LAND + 4.5, phi(TH[0])), pol(CC, 66.0, phi(TH[0]))], D.THIN)
vc.dim_ang((0.0, 0.0), phi(TH[1]), 180.0, 56.0, ext_from=R_LAND + 4.5,
           text="17" + TIMES + " " + fmt(TH[1], 0) + DEG + " (= " + fmt(TH[-1], 0) + DEG + ")")
sh2.text(CC[0] - 66.5, CC[1] - 4.5, chr(952) + " = 0", D.H, ha="right")   # clear of the 0.8° tail
sh2.text(*(pol(CC, 22.0, phi(TH[0])) + (0.0, 1.8)), "HOLE 0", D.H)
# +theta sense: clockwise seen from aft
t_ = np.radians(np.linspace(125.0, 95.0, 20))
arc = np.c_[CC[0] + 20.0 * np.cos(t_), CC[1] + 20.0 * np.sin(t_)]
sh2.line(arc, D.THIN)
sh2.arrow(arc[-1], arc[-1] - arc[-3])
tp = pol(CC, 14.5, 110.0)
sh2.text(tp[0], tp[1], "+" + chr(952), D.H, ha="center", va="center")
# the callout, on the thread of the hole at theta 140
a_c = phi(140.0)
e_c = unit_ang(a_c)
p_c = CC + e_c * 42.0 + np.array([-e_c[1], e_c[0]]) * (M_D / 2.0)
q_c = p_c + (16.0, 20.0)
vc.leader(((p_c - CC) / 1.0), 16.0, 20.0,
          HOLE_TXT + ["DRILL AND TAP AT ASSEMBLY", "(MATCH-DRILLED), NOTE 6"])
sh2.text(CC[0], CC[1] + 58.0, "SECTION C-C", 3.5, ha="center")

# ---- VIEW G: the aft end, puller threads -------------------------------------------------
CG = np.array([118.0, 85.0])
vg = View(sh2, Part(STEP), CG, 1.0, look="aft")
sh2.line([CG - (68.0, 0.0), CG + (56.0, 0.0)], D.THIN, "center")
sh2.line([CG - (0.0, 56.0), CG + (0.0, 56.0)], D.THIN, "center")
sh2.circle(CG, R_PUL, D.THIN, "center", n=360)
for th in PTH:
    pc = pol(CG, R_PUL, phi(th))
    e = unit_ang(phi(th))
    n = np.array([-e[1], e[0]])
    for dd in (e, n):
        sh2.line([pc - dd * 5.0, pc + dd * 5.0], D.THIN)
    thread_end(sh2, pc, M_D)
dia_end(sh2, CG, R_FL, 60.0, DIA + fmt(2 * R_FL))
dia_end(sh2, CG, R_PUL, 135.0, DIA + fmt(2 * R_PUL), gap=R_FL - R_PUL + 2.5)   # PCD
vg.dim_ang((0.0, 0.0), phi(PTH[0]), 180.0, 62.0, ext_from=R_FL + 2.0, dec=0)
sh2.text(CG[0] - 68.0, CG[1] - 4.5, chr(952) + " = 0", D.H)
t_ = np.radians(np.linspace(125.0, 95.0, 20))
arc = np.c_[CG[0] + 18.0 * np.cos(t_), CG[1] + 18.0 * np.sin(t_)]
sh2.line(arc, D.THIN)
sh2.arrow(arc[-1], arc[-1] - arc[-3])
tp = pol(CG, 12.5, 110.0)
sh2.text(tp[0], tp[1], "+" + chr(952), D.H, ha="center", va="center")
R_PLAB = 0.5 * (R_LIP_AFT + R_BODY - BRK)          # labels centred in the aft-face ring
for lab, th in (("P1", PTH[0]), ("P2", PTH[1])):
    sh2.text(*pol(CG, R_PLAB, phi(th)), lab, D.H, ha="center", va="center")
pc2 = pol(CG, R_PUL, phi(PTH[1])) + unit_ang(-45.0) * (M_D / 2.0)
vg.leader(pc2 - CG, 12.0, -14.0, PUL_TXT + ["PULLER, NOTE 9"])
sh2.text(CG[0], CG[1] + 58.0, "VIEW G", 3.5, ha="center")

# ---- notes -----------------------------------------------------------------------------
TQ = P.BOLT_TORQUE_AFT_NM
TH_ = chr(952)
NM = "N" + chr(183) + "m"
notes = [
    "Material: stainless steel 304 (1.4301, X5CrNi18-10), ASTM A479 annealed round bar "
    + DIA + "105 min " + TIMES + " 95 min, EN 10204 3.1 certificate. Substitutes (303 "
    "included) only with engineering approval.",
    "The holder is cut to its own case: land " + DIA + "(A - " + f2(LAND_OFF) + ") "
    + tl(TOL_LAND) + ", case grooves " + DIA + "(A - " + f2(GROOVE_OFF) + ") "
    + tl(TOL_GROOVE) + " (table, sheet 1), A being the honed size of the mating case's "
    "aft seal zone, recorded on SRM100-101 (note 4, R4): the smallest reading in the zone, "
    + f"{A_MIN:.3f} {chr(8804)} A {chr(8804)} {A_MAX:.3f}, the zone held to A +{A_TOL:.3f}/0 "
    f"(never over {P.CASE_BORE_MAX:.2f}). " + DIA + fmt(2 * R_LAND) + " and " + DIA
    + fmt(2 * R_GROOVE) + f" are drawn for A = {A_MIN:.3f}. Record A, the cut sizes and "
    "the pair serial.",
    "Finish-turn the land, both case grooves, the insert bore, the seat face and face B "
    "in one setup.",
    "Seat root R" + fmt(SEAT_R) + " " + PM + "0.1: smooth blend, no undercut, no step (the "
    "bending root of the lip). Glands: bottoms Ra 0.8, walls Ra 1.6, no tool marks across "
    "a groove; groove edges R" + fmt(ET) + " (" + fmt(ET - 0.02) + " - "
    + fmt(ET + 0.03) + ").",
    "Glands for 2" + TIMES + " " + P.ORING_DASH + " (case seal, on the land) and 1" + TIMES
    + " " + P.INSERT_ORING_DASH + " (insert seal, in the bore), SRM100-000 items 13 and 14: "
    + P.ORING_COMPOUND + ", new for every firing. Lubricant: " + P.LUBE + ".",
    str(len(TH)) + TIMES + " " + THREAD + " radial holes, made at assembly per SRM100-101 "
    "ops 110 - 150, the holder seated and clamped in its case, hole 0 first: "
    "tap drill " + DIA + fmt(DRILL_D, 1) + " through the case holes, depth stops set from the "
    "case OD (the land is covered): full " + DIA + fmt(DRILL_D, 1) + " to "
    + f"{STOP_DRILL:.1f}" + " (" + fmt(D_DEPTH, 2) + " from the land), full thread to "
    + f"{STOP_THREAD:.1f}" + " (" + fmt(T_DEPTH, 2) + " from the land); drill point "
    + chr(8805) + " "
    + fmt(P.MIN_WALL_UNDER_HOLE) + " from the insert bore (" + f2(WALL_TIP) + " nominal). "
    "Bottoming tap through the reamed case holes; M6-6H GO / NO-GO gauge. The SRM100-101 op "
    "130 ream entry cone is permitted (" + fmt(REAM_CONE, 1) + " deep max, " + DIA
    + f"{P.CASE_HOLE_D:.2f} at the land); full thread is counted below it. Case and holder "
    "are then a serialised pair.",
    "Clocking: " + TH_ + " is counter-clockwise seen from forward, clockwise seen from aft "
    "(SECTION C-C, VIEW G). Until match-drilling " + TH_ + " = 0 is carried by puller P1 ("
    + TH_ + " " + fmt(PTH[0], 0) + DEG + ", " + DIA + fmt(2 * R_PUL) + "): hole 0 (key, "
    + TH_ + " " + fmt(TH[0], 1) + DEG + ") is " + fmt(PTH[0] - TH[0], 1) + DEG + " clockwise "
    "of P1 seen from forward, " + fmt(PTH[0] - TH[0], 1) + DEG + " counter-clockwise seen "
    "from aft. The clocking line at " + TH_ + " = 0 is then scribed across the case end and "
    "the flange OD (SRM100-101 ops 120, 140).",
    "Mark 'SRM100-102 AFT', the part serial, the pair serial and A (note 2) on the flange "
    "OD, centred on hole 0 (" + TH_ + " " + fmt(TH[0], 1) + DEG + "), a 2 mm gap left in the "
    "text where the clocking line " + TH_ + " = 0 crosses: 2 mm characters, laser or "
    "dot-peen, 0.05 deep max. No marks on the aft body OD " + DIA + fmt(2 * R_BODY) + ": it "
    "carries the temperature labels (sheet 1), irreversible 177 / 204 / 232 / 260 °C strips "
    "fitted new at assembly for every firing, at " + TH_ + " " + fmt(LABEL_TH[0], 0) + DEG
    + " and " + fmt(LABEL_TH[1], 0) + DEG + ", " + fmt(-LAB_Z[1], 0) + " ... "
    + fmt(-LAB_Z[0], 0) + " from B, clear of the cap tape (SRM100-106 note 6: at " + TH_
    + " 0" + DEG + " / 180" + DEG + ", ends " + chr(8804) + " " + fmt(TAPE_ON, 0)
    + " from the aft face).",
    "Puller threads P1 / P2 (VIEW G): " + PUL_TXT[0] + ", tap drill " + PUL_TXT[1] + ", in "
    "the flange aft face on " + DIA + fmt(2 * R_PUL) + " at " + TH_ + " " + fmt(PTH[0], 0) + DEG
    + " (P1) and " + fmt(PTH[1], 0) + DEG + " (P2); machined in the shop, before match-"
    "drilling. For the puller bridge and two draw screws only (tooling). Never lever or "
    "knock the holder out of the case.",
    "Aft case screws: " + str(len(TH)) + TIMES + " SRM100-000 item 15, ISO 7380-1 M6" + TIMES
    + fmt(P.BOLT_L_AFT, 0) + "-010.9, new for every firing. Nickel anti-seize on the threads "
    "only, head face dry; " + f"{TQ[0]:.1f} - {TQ[1]:.1f} " + NM + " in the criss-cross "
    "sequence of SRM100-000 sheet 2 (3 passes). 6 " + NM + " with anti-seize yields the "
    "annealed 304 threads. Never fit an M6" + TIMES + fmt(P.BOLT_L_FWD, 0) + " here: it "
    "bottoms with the head proud.",
    "Insert removal: support the holder on its forward face; the push sleeve (tooling, "
    "52.4 ID " + TIMES + " 53.8 OD) bears on the insert's aft face through the lip bore. "
    "Never push on the lip.",
    "Proof test per SRM100-001 with the proof dummy SRM100-120 in place of the insert.",
    "Inspect 100 %: land, case grooves and insert groove (" + DIA + " and width), insert "
    "bore, seat depth, lip thickness " + fmt(P.HOLDER_LIP_T) + " " + tl(TOL_LIP) + ", the "
    "geometric tolerances; the glands and the seat root visually at 10" + TIMES
    + ". Record the values with the serial.",
    "Deburr and clean: every edge an O-ring passes over is burr-free and smooth (nose "
    "chamfer, land, case groove edges, bore lead-in, insert bore, insert groove edges). "
    "Tapped-hole entries on the land flush, no raised burr (the land slides in the honed "
    "bore). After machining and again after match-drilling: blow out, wash and degrease "
    "(IPA); no chips in the glands, threads or bore.",
    "After every firing: read and record the temperature labels before extraction; a "
    "reading " + chr(8805) + " 232 °C: retire or re-proof (SRM100-001) the aft end. "
    "Replace and re-use per SRM100-000 sheet 1 note 13; item 2 is re-used after inspection: "
    "clean and check the glands and seat face (no erosion, pitting, scoring), seat root and "
    "lip at 10" + TIMES + " (no crack), lip thickness and seat depth, all tapped holes with "
    "the M6-6H GO / NO-GO gauge. Any finding: quarantine, engineering decides.",
    "Surface texture indications per ISO 21920-1 (Ra, ISO 21920-2).",
]
yn2 = sh2.notes(222.0, 283.0, notes, 184.0, title="NOTES (SHEETS 1 AND 2)")
assert yn2 > sh2.tb[3] + 2.0, yn2          # clear of the USED ON line
sh2.text(sh2.tb[2] - 2.0, sh2.tb[3] + 3.0, USED_ON, D.H, ha="right")

if __name__ == "__main__":
    for s in (sh, sh2):
        s.lint()
    sh.save("nozzle_holder")
    sh2.save("nozzle_holder")
