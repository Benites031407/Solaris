"""SRM100-103 forward closure (6061-T651): A3, 2 sheets.

Sheet 1 (2:1): half section with hole 0 in the cutting plane, detail D (seal groove,
20:1).  The closure is solid (no pocket, no port: decisions G24, G25), PLUG_L +
FLANGE_T from the inboard face to the forward face, and the forward face is one
flat surface from the axis to the flange edge break: the thrust face for a horizontal
static-test load cell, broken only by the 2 axial puller holes.
Sheet 2 (1:1): section A-A through the radial tapped holes, view C (forward end, the
flat face and the 2 puller holes), notes.

View frame: u = closure z (z = 0 on the flange bearing face = datum B, forward to the
right), v = radius.  Every number below comes from fwd_closure.py / srm_params.py /
fwd_closure.step / out/mass_budget.json.  Datum A = the plug land (the O-ring grooves
sit in it), datum B = the flange bearing face that butts the case's forward end face.
"""

import inspect
import json
import math

import numpy as np

import srm_dwg as D
import srm_params as P
import fwd_closure as F
import srm_build
from srm_dwg import (DIA, DEG, TIMES, DEPTH, PM, THIN, THICK, H, Hatch, Part, Sheet, View,
                     fmt)

STEP = "fwd_closure.step"
HATCH = Hatch(45, 2.0)
TH = chr(952)                                   # theta
NBSP = chr(160)                                 # keeps "Ra 3.2" on one line in the notes
# G13 mass: fwd_closure.step (G25 solid, regenerated 09-25), adaptive BRepGProp (eps 1e-9):
# 285 359.34 mm3 x 2.70 g/cm3 = 770.47 g, the same as srm_verify's out/mass_budget.json
# entry, which the title blocks read; re-checked against the STEP at run time (below,
# before the sheets are drawn)
MB = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())["parts"]["fwd_closure"]
MASS = round(1000.0 * MB["mass_each_kg"], 1)
MATERIAL = "6061-T651 bar, ASTM B211/B221\nor equal, stock " + DIA + "105 " + TIMES + " 50 min"

# ---- geometry (model values) --------------------------------------------------
R_LAND, R_GROOVE, R_FL = F.R_LAND, F.R_GROOVE, F.R_FL
Z_IN, Z_TOP = F.Z_IN, F.Z_TOP
SOLID_L = Z_TOP - Z_IN                    # G25: solid, inboard face -> flat forward face (44)
assert abs(SOLID_L - (P.PLUG_L + P.FLANGE_T)) < 1e-9
# the generator's profile starts on the axis at the inboard face and ends on the axis at
# the forward face: solid on the axis, no pocket, no port (the STEP is checked below)
assert F.section()[0] == (0.0, Z_IN) and F.section()[-1] == (0.0, Z_TOP)
BRK, GR, ET = F.BRK, F.GR, F.ET
G1, G2, GW = -P.GROOVE_1_Z, -P.GROOVE_2_Z, P.GROOVE_W
Z_BOLT = -P.BOLT_EDGE
ENG = P.BOLT_L_FWD - P.CASE_WALL - P.PLUG_CLEAR          # screw engagement in the plug
TH_DEPTH = ENG + P.THREAD_OVER                            # full thread, from the land
DR_DEPTH = TH_DEPTH + P.DRILL_OVER                        # full-diameter drill, from the land
R_TH = R_LAND - TH_DEPTH                                  # thread end radius (32.0)
R_DR = R_LAND - DR_DEPTH                                  # drill end radius (30.0)
# drill point: the generator's radial_drill default (118 deg twist drill)
DRILL_PT = inspect.signature(srm_build.radial_drill).parameters["point_deg"].default
R_TIP = R_DR - (P.BOLT_TAP_DRILL / 2.0) / math.tan(math.radians(DRILL_PT / 2.0))
# G25: the closure is solid, so the metal that matters where the 18 radial holes end is
# the ligament between neighbouring holes at the drill points; the closest pair is the
# keyed hole 0 and its neighbour.  Computed exactly as srm_params.self_check does.
_TH = sorted(P.bolt_thetas())
DTH = min((b - a) % 360.0 for a, b in zip(_TH, _TH[1:] + _TH[:1]))
LIG = 2.0 * R_TIP * math.sin(math.radians(DTH / 2.0)) - P.BOLT_TAP_DRILL
assert LIG >= P.MIN_WALL_UNDER_HOLE, LIG
_k = min(range(len(_TH)), key=lambda i: (_TH[(i + 1) % len(_TH)] - _TH[i]) % 360.0)
LIG_PAIR = tuple(sorted(P.bolt_thetas().index(t) for t in (_TH[_k], _TH[(_k + 1) % len(_TH)])))
R_M6 = P.BOLT_D / 2.0                                     # M6 major (thin line)
PUL_THREAD = P.PULLER_DEPTH - P.DRILL_OVER                # full thread in the puller holes
CASE_OD_R = P.CASE_OD / 2.0
PITCH = 360.0 / P.N_BOLTS
THETAS = P.bolt_thetas()
PULLERS = P.puller_thetas()
EDGE_R_LIM = (0.08, 0.13)                                  # srm_params GROOVE_EDGE_R comment
GR_TOL = 0.1                                               # srm_params GROOVE_R_BOTTOM +/-0.1
# G1-rev: seal zone A = smallest reading, CASE_ID <= A <= SEAL_A_MAX, zone A +TOL_BORE/0
A_MIN, A_MAX, A_TOL = P.CASE_ID, P.SEAL_A_MAX, P.TOL_BORE[1]
assert abs(A_MAX + A_TOL - P.CASE_BORE_MAX) < 1e-9          # the zone never passes 92.10
LE = chr(8804)
# G20: SRM100-101 op 130 leaves the ream's entry cone in the closure, 0.5 deep max,
# DIA CASE_HOLE_D at the land; it lies inside the THREAD_LOST that the strength check drops
REAM_CONE = 0.5
assert REAM_CONE <= P.THREAD_LOST
# note order on sheet 2; the views refer to notes by key, so the numbers can't drift.
# Other sheets cite these numbers (e.g. note 11, marking): never reorder.  G25: note 5
# ("lig", was the pocket wall) and note 7 ("solid", was the web) keep their numbers.
NOTE_KEYS = ["mat", "finish", "A", "match", "lig", "edges", "solid", "bond", "seals",
             "pull", "mark", "insp", "reuse"]
assert NOTE_KEYS.index("lig") == 4 and NOTE_KEYS.index("solid") == 6 and NOTE_KEYS.index("mark") == 10
USED_ON = "USED ON: SRM100-000 item 6 (1 off); SRM100-001 item 6"


def note(k):
    return str(NOTE_KEYS.index(k) + 1)


def tol2(t, dec=3):
    """(lo, hi) deviation pair -> ('+hi' | '0', 'lo' | '0') for the stacked tolerance."""
    lo, hi = t
    return ("0" if hi == 0 else "+" + fmt(hi, dec), "0" if lo == 0 else fmt(lo, dec))


def e(deg):
    a = math.radians(deg)
    return np.array([math.cos(a), math.sin(a)])


# ---- local primitives (not in srm_dwg) -------------------------------------------
def rad_void(view, centre, r, ang, length, text):
    """Radius of a concave fillet dimensioned from the void side (ISO 129): arrow on the
    arc at polar angle `ang` about `centre`, pointing outward onto the arc, the line
    running back through the centre `length` paper mm, then the reference line."""
    s = view.sheet
    c = view.pt(*centre)
    d = e(ang)
    p = c + d * r * view.scale
    q = c - d * length
    s.line([p, q], THIN)
    s.arrow(p, d)
    sg = 1.0 if -d[0] >= 0 else -1.0
    w = s.text_width(text, H) + 1.6
    s.line([q, q + (sg * w, 0.0)], THIN)
    s.text(q[0] + sg * 0.8, q[1] + D.TEXT_GAP, text, H, ha="left" if sg > 0 else "right")


def arc34(sheet, c, a, b=None, lw=THIN):
    """ISO 6410 thread root in an end view: thin arc of about 3/4 of the circle (or an
    ellipse a x b), open in the upper-right quadrant."""
    b = a if b is None else b
    t = np.radians(np.linspace(95.0, 365.0, 90))
    sheet.line(np.c_[c[0] + a * np.cos(t), c[1] + b * np.sin(t)], lw)


def rotated_section_geometry(part, section, rot, look="side"):
    """Work-around for srm_dwg.compute_geometry with rot != 0 (kit left untouched):
    the rotated copy loses its G1 edge regularity, so every tangent edge comes back as
    a thick visible line, and HLR adds phantom lines across the section face (here at
    the groove inboard walls, z -24 / -32.8, across the whole face).  Same pipeline, plus
    BRepLib.EncodeRegularity on the cut solid and dropping any line that runs through
    the interior of the section face (nothing can be seen through the cut face)."""
    import hashlib
    import pickle
    from OCP.BRepLib import BRepLib
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    key = hashlib.sha1(repr((part.key(), section, round(rot, 9), look, "fc103-enc1")).encode())
    cache = D.CACHE / f"fc103_{key.hexdigest()[:16]}.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    basis = D._uv_basis(look)
    s = D._place(D.load(part.src), part.trsf, rot)
    inter = s.intersect(D._section_face(section))
    faces = [(0, D._face_polys(f.wrapped, basis)) for f in (inter.faces() if inter else [])]
    cut = s - D._cut_tool(section)
    BRepLib.EncodeRegularity_s(cut.wrapped, 1e-3)
    lines = D._hlr(cut.wrapped, look)
    inner = unary_union([pg for _, pg in faces]).buffer(-0.02)
    for cat in ("vis", "smooth"):
        keep = []
        for p in lines[cat]:
            g = LineString(p).difference(inner)
            for ln in getattr(g, "geoms", [g]):
                if isinstance(ln, LineString) and not ln.is_empty and ln.length > 1e-3:
                    keep.append(np.asarray(ln.coords))
        lines[cat] = keep
    a = np.vstack([p for c in lines.values() for p in c])
    geo = {"lines": lines, "faces": faces, "occluders": [],
           "bounds": (a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())}
    D.CACHE.mkdir(parents=True, exist_ok=True)
    with open(cache, "wb") as f:
        pickle.dump(geo, f)
    return geo


def view_arrow(sheet, tip, direction, letter, length=12.0):
    """ISO 128-30 reference arrow for a view direction, with its letter."""
    d = np.asarray(direction, float) / np.hypot(*direction)
    tip = np.asarray(tip, float)
    sheet.line([tip - d * D.ARROW_L, tip - d * length], THIN)
    sheet.arrow(tip, d)
    m = tip - d * length / 2
    sheet.text(m[0], m[1] + 2.0, letter, 3.5, ha="center")


def axes_from_centre(view, x_neg, x_pos, y_neg, y_pos):
    """The two centre lines of an end view, each drawn as two halves starting at the
    axis, so both chains begin with a long dash there and cross on long dashes
    (ISO 128-20); the arguments are the view radii where the four halves end."""
    o = view.pt(0.0, 0.0)
    for p in ((-x_neg, 0.0), (x_pos, 0.0), (0.0, -y_neg), (0.0, y_pos)):
        view.sheet.line([o, view.pt(*p)], THIN, "center")


def step_mass_g():
    """fwd_closure.step volume by adaptive BRepGProp (build123d's .volume is not
    adaptive and reads low on trimmed faces) x the srm_verify density, in g."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(D.load(STEP).wrapped, g, 1e-9, True)
    return g.Mass() * P.AL_RHO * 1e3


def step_solid_through(n=45):
    """G25 on the STEP itself: every point on the axis from the inboard face to the
    forward face, and along a radius (theta 0, clear of the puller holes) just under the
    forward face out to the edge break, is inside the metal: no pocket, no port."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN
    cl = BRepClass3d_SolidClassifier(D.load(STEP).wrapped)
    eps = 0.1
    pts = [(0.0, z) for z in np.linspace(Z_IN + eps, Z_TOP - eps, n)]
    pts += [(r, Z_TOP - eps) for r in np.linspace(0.0, R_FL - BRK - eps, n)]
    for r, z in pts:
        cl.Perform(gp_Pnt(r, 0.0, z), 1e-6)
        assert cl.State() == TopAbs_IN, (r, z)
    return True


def self_check_ligament():
    """srm_params.self_check()'s forward-ligament line, captured from its printout."""
    import contextlib
    import io
    import re
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        P.self_check()
    m = re.search(r"forward tapped holes end at r ([\d.]+) in solid metal, ([\d.]+) mm apart "
                  r"\(closest pair, ([\d.]+) deg\)", buf.getvalue())
    return m.groups()


# G13: the title-block mass (out/mass_budget.json) is the STEP's mass
M_STEP = step_mass_g()
assert abs(M_STEP - 1000.0 * MB["mass_each_kg"]) < 0.1 and round(M_STEP, 1) == MASS, (M_STEP, MASS)
assert step_solid_through()
# note 5's numbers are the ones srm_params.self_check prints
assert self_check_ligament() == (f"{R_TIP:.2f}", f"{LIG:.2f}", f"{DTH:.1f}"), \
    (self_check_ligament(), R_TIP, LIG, DTH)


# =============================================================================
# SHEET 1
# =============================================================================
sh = Sheet("SRM100-103", "FORWARD CLOSURE", "Half section (solid, flat forward face), seal groove D",
           size="A3", material=MATERIAL, mass_g=MASS, scale="2:1", sheet=(1, 2))
part = Part(STEP, hatch=HATCH)
# hole 0 (theta 0.8 deg) turned into the cutting plane
v = View(sh, part, origin=(128.0, 152.0), scale=2.0, look="side", section="half",
         rot=-P.BOLT_OFFSET0, draw=False)
v.geo = rotated_section_geometry(part, "half", -P.BOLT_OFFSET0)
v.draw()
Y = lambda vv: v.pt(0.0, vv)[1]
X = lambda uu: v.pt(uu, 0.0)[0]

# ---- axial dimensions from datum B, above the view ------------------------------
v.dim_h((Z_BOLT, 48.0), (0.0, 48.0), at=48.0, ext=(False, False), tol=PM + "0.1")
v.dim_h((G1 + GW / 2, R_LAND), (0.0, R_FL - BRK), at=55.0)                  # 19.2
v.dim_h((G2 + GW / 2, R_LAND), (0.0, R_FL - BRK), at=59.0)                  # 28
v.cut_line((Z_BOLT, R_FL), (Z_BOLT, -(R_LAND + 2.5)), "A", (-1, 0))
sh.fcf(X(0.0) + 6.0, Y(52.0), ["perpendicularity", "0.03", "A"],
       leader=(X(0.0), Y(53.625)))

# ---- datum A: the land ------------------------------------------------------------
v.dim_dia(Z_IN + F.NOSE_Z, R_LAND, at=-44.0, tol=tol2(P.TOL_LAND, 2), arrows=(False, True))
v.datum((-44.0, -R_LAND), "A", (0, -1), length=5.0)
sh.fcf(24.0, Y(49.0), ["cylindricity", "0.01"], leader=(X(-41.0), Y(R_LAND)))
# groove bottoms: runout to A (both grooves)
fr = sh.fcf(44.0, Y(55.0), ["runout", "0.03", "A"], leader=(X(-32.0), Y(R_GROOVE)))
sh.text(fr[0], fr[3] + 1.2, "2" + TIMES, H)
v.dim_dia_half(G1, -R_GROOVE, at=G1, text="2" + TIMES + " " + DIA + fmt(2 * R_GROOVE),
               tol=tol2(P.TOL_GROOVE, 2))
# G1: both sizes are drawn for A = 92.000; the plug is cut to the recorded bore A (note 3).
# Flags on the same dimension lines, clear of the dimension texts.
A_NOM = P.CASE_ID
sh.text(X(-44.0) - D.TEXT_GAP, Y(0.0) + 12.0,
        "= A - " + fmt(A_NOM - 2 * R_LAND) + ", NOTE " + note("A"), H, rot=90.0)
sh.text(X(G1) - D.TEXT_GAP, Y(-R_GROOVE / 2.0) + 14.0,
        "= A - " + fmt(A_NOM - 2 * R_GROOVE), H, rot=90.0)

# ---- nose lead, under-flange radius, datum B, lengths -------------------------------
v.leader((Z_IN + F.NOSE_Z / 2, -(R_LAND - P.PLUG_NOSE_CHAMFER / 2)), 6.0, -10.0,
         [fmt(F.NOSE_Z) + " " + TIMES + " 30" + DEG])
rad_void(v, (-F.UNDER, -(R_LAND + F.UNDER)), F.UNDER, 45.0, 7.0, "R" + fmt(F.UNDER))
sh.datum((X(0.0), Y(-52.0)), "B", (-1, 0), 4.0)
v.dim_h((0.0, -(R_FL - BRK)), (Z_TOP, -(R_FL - BRK)), at=-54.0)              # 6
v.dim_h((Z_IN, -(R_LAND - P.PLUG_NOSE_CHAMFER)), (0.0, -(R_FL - BRK)), at=-58.0)   # 38
# G25: the closure is solid, inboard face -> forward face = SOLID_L; 38 and 6 from datum B
# already fix it, so the overall length is a reference dimension (no double dimensioning)
v.dim_h((Z_IN, -(R_LAND - P.PLUG_NOSE_CHAMFER)), (Z_TOP, -(R_FL - BRK)), at=-62.0,
        ref=True)                                                          # (44)

# ---- forward end: flange diameter (half dimension through the axis), thrust face ----
# G25: the forward face is one flat surface from the axis to the flange edge break, the
# thrust face; parallelism and Ra 1.6 now cover the whole face
v.dim_dia_half(Z_TOP - BRK, R_FL, at=10.0)
sh.fcf(X(Z_TOP) + 10.0, Y(-33.5), ["parallelism", "0.05", "B"], leader=v.pt(Z_TOP, -30.0))
sh.text(X(Z_TOP) + 10.0, Y(-33.5) + 8.5 + H * 1.55, "THRUST FACE,", H)
sh.text(X(Z_TOP) + 10.0, Y(-33.5) + 8.5, "FLAT TO THE AXIS, NOTE " + note("solid"), H)
v.finish((Z_TOP, -40.0), "Ra 1.6", leader=(10.0, -6.0))
view_arrow(sh, (X(Z_TOP) + 28.0, Y(0.0)), (-1, 0), "C")

# ---- thread representation (ISO 6410): hole 0 in the section ------------------------
for s_ in (-1.0, 1.0):
    v.line([(Z_BOLT + s_ * R_M6, R_LAND), (Z_BOLT + s_ * R_M6, R_TH)], THIN)
v.line([(Z_BOLT - R_M6, R_TH), (Z_BOLT + R_M6, R_TH)], THICK)
# tapped holes seen on the outside half (lower): root as a thin 3/4 ellipse
for th in THETAS:
    tp = th - P.BOLT_OFFSET0
    sn = math.sin(math.radians(tp))
    if 90.0 < tp < 180.0 and sn > 0.6:
        arc34(sh, v.pt(Z_BOLT, R_LAND * math.cos(math.radians(tp))), R_M6 * v.scale,
              R_M6 * v.scale * sn)

# ---- detail D: seal groove (20:1), centred in the right half of the sheet ------------
D_SC, D_R = 20.0, 3.0                            # scale, radius (model mm)
D_O = np.array([300.0, 186.0])                   # paper centre
d = v.detail((G1, 44.6), D_R, D_SC, tuple(D_O), "D", circle_label_ang=90.0)
d.dim_h((G1 - GW / 2, 45.5), (G1 + GW / 2, 45.5), at=45.5, ext=(False, False),
        tol=tol2(P.TOL_GROOVE_W, 2))
d.dim_rad((G1 - GW / 2 - ET, R_LAND - ET), ET, 45.0, length=12.0,
          text="2" + TIMES + " R" + fmt(ET),
          tol=("+" + fmt(EDGE_R_LIM[1] - ET), fmt(EDGE_R_LIM[0] - ET)))
rad_void(d, (G1 - GW / 2 + GR, R_GROOVE + GR), GR, 225.0, 9.0,
         "2" + TIMES + " R" + fmt(GR) + " " + PM + fmt(GR_TOL))
sh.finish_symbol(d.pt(G1 + 0.6, R_GROOVE), "Ra 0.8")
d.finish((G1 + GW / 2, 44.6), "Ra 1.6", leader=(-16.0, -4.0))
d.finish((G1 + GW / 2 + 0.2, R_LAND), "Ra 1.6", leader=(14.0, 14.0))
sh.text(D_O[0], D_O[1] - D_R * D_SC - 5.0 - 3.5 - 5.0, "BOTH GROOVES", H, ha="center")

# ---- sheet 1 foot -----------------------------------------------------------------------
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")
sh.text(272.0, sh.tb[3] + 8.0, "NOTES, MATCH-DRILLING AND SECTION A-A: SHEET 2", H)
sh.text(272.0, sh.tb[3] + 3.0, USED_ON, H)


# =============================================================================
# SHEET 2
# =============================================================================
sh2 = Sheet("SRM100-103", "FORWARD CLOSURE", "Section A-A (radial tapped holes), view C, notes",
            size="A3", material=MATERIAL, mass_g=MASS, scale="1:1", sheet=(2, 2))

# ---- section A-A through the bolt row, looking aft ------------------------------------
a = View(sh2, part, origin=(105.0, 200.0), scale=1.0, look="fwd", z_cut=Z_BOLT, keep="below")
a.label("A-A", where="above", gap=8.0)
# G25: solid to the axis; each hole's centre line starts a little inside its drill point,
# the horizontal one stops short of hole 0's (0.8 deg off it) so the two do not merge
R_CL0, R_CL1 = R_TIP - 2.0, R_LAND + 3.0
axes_from_centre(a, R_CL1, R_CL0 - 2.0, R_CL1, R_CL1)
for k, th in enumerate(THETAS):
    u = e(th)
    n = e(th + 90.0)
    if abs(((th - 180.0) + 180.0) % 360.0 - 180.0) > 1e-6:    # 180 deg: on the chain line
        sh2.line([a.pt(*(u * R_CL0)), a.pt(*(u * R_CL1))], THIN, "center")
    for s_ in (-1.0, 1.0):
        sh2.line([a.pt(*(u * R_LAND + n * s_ * R_M6)), a.pt(*(u * R_TH + n * s_ * R_M6))], THIN)
    sh2.line([a.pt(*(u * R_TH - n * R_M6)), a.pt(*(u * R_TH + n * R_M6))], THICK)
a.dim_ang((0.0, 0.0), 0.0, THETAS[0], 56.0, text=fmt(THETAS[0]) + DEG, ext=True,
          ext_from=R_CL1, text_r=58.5, text_dy=2.2)
a.dim_ang((0.0, 0.0), 0.0, THETAS[1], 66.0,
          text=f"{P.N_BOLTS - 1}{TIMES} {fmt(PITCH)}{DEG} (={fmt((P.N_BOLTS - 1) * PITCH)}{DEG})",
          ext=True, ext_from=R_CL1)
p0 = a.pt(68.0 + 1.5, 0.0)
sh2.text(p0[0], p0[1] - 1.2, TH + " = 0", H)
p0 = a.pt(R_LAND + 2.0, -7.5)
sh2.text(p0[0], p0[1], "HOLE 0 (KEY)", H)
# +theta sense
t_ = np.radians(np.linspace(35.0, 55.0, 30))
cc = a.pt(0.0, 0.0)
sh2.line(np.c_[cc[0] + 58.0 * np.cos(t_), cc[1] + 58.0 * np.sin(t_)], THIN)
sh2.arrow(cc + e(55.0) * 58.0, e(145.0))
p0 = cc + e(45.0) * 61.0
sh2.text(p0[0], p0[1], "+" + TH, H)
# callout on hole 6 (120 deg), leader leaving between holes 6 and 7
h6 = e(THETAS[6]) * 40.0 + e(THETAS[6] + 90.0) * (P.BOLT_TAP_DRILL / 2.0)
q6 = e(130.0) * 64.0
a.leader(tuple(h6), q6[0] - h6[0], q6[1] - h6[1],
         [f"{P.N_BOLTS}{TIMES} M6{TIMES}1-6H {DEPTH}{fmt(TH_DEPTH)}",
          DIA + fmt(P.BOLT_TAP_DRILL) + " " + DEPTH + fmt(DR_DEPTH),
          "DEPTHS FROM THE LAND",
          "MATCH-DRILLED, NOTE " + note("match")])

# ---- view C: forward end ------------------------------------------------------------------
c = View(sh2, part, origin=(105.0, 80.0), scale=1.0, look="fwd")
c.label("C", where="above", gap=6.0)
# G25: the face is flat to the axis (no pocket circle): the centre lines cross on it
axes_from_centre(c, R_FL + 3.0, R_FL + 2.0, R_FL + 3.0, R_FL + 3.0)
c.circle((0.0, 0.0), P.PULLER_R, THIN, "center")
for k, th in enumerate(PULLERS):
    u = e(th)
    r_out = R_FL + 2.0 if k == 0 else P.PULLER_R + 5.0
    sh2.line([c.pt(*(u * (P.PULLER_R - 5.0))), c.pt(*(u * r_out))], THIN, "center")
    arc34(sh2, c.pt(*(u * P.PULLER_R)), R_M6)
c.dim_ang((0.0, 0.0), 0.0, PULLERS[0], 56.0, ext=True, ext_from=R_FL + 2.0, dec=0)
pp = e(PULLERS[0]) * P.PULLER_R + e(45.0) * (P.PULLER_TAP_DRILL / 2.0)
c.leader(tuple(pp), 21.0, 24.0,
         [f"{P.PULLER_N}{TIMES} M6{TIMES}1-6H {DEPTH}{fmt(PUL_THREAD)}",
          DIA + fmt(P.PULLER_TAP_DRILL) + " " + DEPTH + fmt(P.PULLER_DEPTH)])
pc = e(135.0) * P.PULLER_R
c.leader(tuple(pc), -17.3, 17.3, [DIA + fmt(2 * P.PULLER_R)])
# puller names (G3: P1 carries theta 0 until match-drilling)
for lab, th in (("P1", PULLERS[0]), ("P2", PULLERS[1])):
    pl = c.pt(*(e(th) * (P.PULLER_R - 8.5)))
    sh2.text(pl[0], pl[1] - H / 2.0, lab, H, ha="center")
# +theta sense, seen from forward
t_ = np.radians(np.linspace(35.0, 55.0, 30))
cc = c.pt(0.0, 0.0)
sh2.line(np.c_[cc[0] + 58.0 * np.cos(t_), cc[1] + 58.0 * np.sin(t_)], THIN)
sh2.arrow(cc + e(55.0) * 58.0, e(145.0))
p0 = cc + e(45.0) * 61.0
sh2.text(p0[0], p0[1], "+" + TH, H)
# clocking line (scribed at match-drilling) and the marking on the flange OD (G7)
c.leader((R_FL, 0.0), 10.0, -10.0,
         ["CLOCKING LINE " + TH + " = 0, NOTE " + note("match") + ";",
          "MARKING ON THE FLANGE OD,",
          "CENTRED ON HOLE 0, NOTE " + note("mark")])
xs, ys = sh2.frame[0] + 6.0, sh2.frame[1] + 12.0
sh2.text(xs, ys, "SECTION A-A AND VIEW C ARE SEEN FROM FORWARD: +" + TH
         + " COUNTER-CLOCKWISE, " + TH + " = 0 ON +X.", H)
sh2.text(xs, ys - 4.5, "P1 AT " + TH + " = " + fmt(PULLERS[0], 0) + DEG + ", P2 AT "
         + fmt(PULLERS[1], 0) + DEG + "; HOLE 0 (" + TH + " = " + fmt(THETAS[0], 1) + DEG
         + ") IS " + fmt(PULLERS[0] - THETAS[0], 1) + DEG + " CLOCKWISE OF P1.", H)

# ---- notes -----------------------------------------------------------------------------
tq = P.BOLT_TORQUE_FWD_NM
NM = "N" + chr(183) + "m"
NOTES = {
    "mat":
    "Material: aluminium alloy 6061-T651 round bar to ASTM B211 or ASTM B221 or equal "
    "(AMS 4117; B221 extruded bar may come as 6061-T6511), stock " + DIA + "105 " + TIMES
    + " 50 min, grain along the axis. Mill certificate with the heat / lot number required.",
    "finish":
    "Bare metal: no anodizing, conversion coat or paint. Texture: land and groove walls "
    "Ra" + NBSP + "1.6, groove bottoms Ra" + NBSP + "0.8, thrust face Ra" + NBSP + "1.6, "
    "elsewhere Ra" + NBSP + "3.2; circumferential lay on the land and grooves. Finish the "
    "land, both grooves and face B in one setup.",
    "A":
    "The plug is cut to its own case: land " + DIA + f"(A - {fmt(A_NOM - 2 * R_LAND)}) "
    f"0/{fmt(P.TOL_LAND[0])}, both groove bottoms {DIA}(A - {fmt(A_NOM - 2 * R_GROOVE)}) "
    f"0/{fmt(P.TOL_GROOVE[0])}, where A is the honed size of the mating case's forward seal "
    f"zone as recorded on SRM100-101 (note{NBSP}4,{NBSP}R4): the smallest reading in the zone, "
    f"{A_MIN:.3f}{NBSP}{LE}{NBSP}A{NBSP}{LE}{NBSP}{A_MAX:.3f}, the zone held to "
    f"A{NBSP}+{A_TOL:.3f}/0 (never over {P.CASE_BORE_MAX:.2f}). " + DIA + fmt(2 * R_LAND)
    + " and " + DIA + fmt(2 * R_GROOVE)
    + f" are drawn for A = {A_NOM:.3f}. Record the A used with the serial.",
    "match":
    f"Radial holes: made ONLY at assembly by match-drilling, per SRM100-101 ops 110 ... 150, "
    "this closure seated and clamped in its case (face B on the case forward end face, "
    f"O-rings out), hole 0 first. Until then {TH} = 0 is carried by puller P1 ({TH} = "
    f"{fmt(PULLERS[0], 0)}{DEG}): hole 0 ({TH} = {fmt(THETAS[0], 1)}{DEG}) is "
    f"{fmt(PULLERS[0] - THETAS[0], 1)}{DEG} clockwise of P1 seen from forward (view C). "
    "Depth stops from the case OD (the land is covered): full " + DIA
    + f"{fmt(P.BOLT_TAP_DRILL, 0)} to {CASE_OD_R - R_DR:.1f} ({fmt(DR_DEPTH)} from the land), "
    f"full thread to {CASE_OD_R - R_TH:.1f} ({fmt(TH_DEPTH)}); bottoming tap through the "
    "reamed case holes. The ream entry cone of SRM100-101 op 130 is permitted in each hole "
    f"({fmt(REAM_CONE, 1)} deep max, {DIA}{P.CASE_HOLE_D:.2f} at the land); full thread is "
    f"counted below it. Scribe the clocking line {TH} = 0 across the case end and the "
    "flange OD, 0.05 deep max. Case and closure are then a serialised pair: never "
    "interchange.",
    "lig":
    f"The {P.N_BOLTS} radial tap drills end at r{NBSP}{R_TIP:.2f} in solid metal; the closest "
    f"pair (holes {LIG_PAIR[0]} and {LIG_PAIR[1]}, {DTH:.1f}{DEG} apart) leave {LIG:.2f} "
    f"between their points, {P.MIN_WALL_UNDER_HOLE:.1f} min.",
    "edges":
    f"Undimensioned chamfers {fmt(BRK)} {TIMES} 45{DEG} (flange edges); "
    "groove edges per detail D. Every edge an O-ring passes over burr-free and smooth; "
    "tapped-hole entries on the land flush, no raised burr. After machining and again "
    "after match-drilling: blow out, wash and degrease (IPA); no chips in the grooves or "
    "threads.",
    "solid":
    f"No port and no pocket: item 6 is solid on the axis, {fmt(SOLID_L)} thick, and its "
    "forward face is one flat thrust face, broken only by the "
    f"{P.PULLER_N} M6 puller holes (note {NOTE_KEYS.index('pull') + 1}). Do not drill, tap or pocket it beyond this drawing. The "
    "motor is fired without a chamber transducer; a transducer needs a new, ported "
    "closure (new drawing) and a re-proof.",
    "bond":
    f"Item 7 (SRM100-107, EPDM full disc {DIA}{fmt(P.FWD_INSUL_OD)} {TIMES} "
    f"{fmt(P.FWD_INSUL_T)}) is bonded to the aft face only after the proof test "
    "(SRM100-000 sheet 3): leave that face as machined, unmarked. IPA degrease, abrade "
    "(P180 / Scotch-Brite), IPA wipe, silicone primer SS4004P, RTV106 or equal over the "
    "whole face, bondline 0.1 ... 0.2, disc OD centred on the land within 0.1; cure 24 h.",
    "seals":
    f"O-rings 2 {TIMES} {P.ORING_DASH}, {P.ORING_COMPOUND}, item 13; {P.LUBE}. Screws "
    f"{P.N_BOLTS} {TIMES} ISO 7380-1 M6{TIMES}{fmt(P.BOLT_L_FWD)}-010.9, item 16, Loctite "
    f"243, {fmt(tq[0])} ... {fmt(tq[1])} {NM}, criss-cross in 3 passes (SRM100-000 sheet 3).",
    "pull":
    f"Pullers P1 ({TH} = {fmt(PULLERS[0], 0)}{DEG}) and P2 ({fmt(PULLERS[1], 0)}{DEG}) on "
    + DIA + fmt(2 * P.PULLER_R) + f": {P.PULLER_N} {TIMES} M6{TIMES}1-6H {DEPTH}"
    f"{fmt(PUL_THREAD)}, {DIA}{fmt(P.PULLER_TAP_DRILL)} {DEPTH}{fmt(P.PULLER_DEPTH)}, "
    "machined before match-drilling; for the puller bridge and two draw screws only "
    "(tooling). Radial screws out first; never lever or knock the closure out.",
    "mark":
    "Mark 'SRM100-103 FWD', the part serial, the pair serial and A on the flange OD, "
    f"centred on hole 0 ({TH}{NBSP}{fmt(THETAS[0], 1)}{DEG}), a 2{NBSP}mm gap left in the text "
    f"where the clocking line {TH} = 0 crosses: 2{NBSP}mm characters, laser or dot-peen, "
    "0.05 deep max. No marks on the thrust face, face B, land, grooves or aft face.",
    "insp":
    "Inspect 100 %, record with the serial: land " + DIA + " (3 positions " + TIMES
    + " 2 directions), groove bottom " + DIA + " and widths, the geometric tolerances, "
    "grooves visually at 10" + TIMES + "; after match-drilling every radial thread with "
    "the M6-6H GO / NO-GO gauge, and its depth.",
    "reuse":
    "After every firing (SRM100-000 items): replace items 4, 5, 7, 8, 9, 10, 11, 12, 13, "
    "14, all 36 screws (items 15, 16) and the temperature labels; re-use items 1, 2, 6 after "
    "inspection (SRM100-101 R10 for the case), and item 3 while the throat is " + LE + " "
    + DIA + "23.9 and uncracked. This closure (item 6): remove item 7 and the old RTV with a "
    "plastic scraper (no metal tools), clean, and repeat the note " + note("insp")
    + " checks: no erosion, heat damage or scoring on the land, grooves or aft face, "
    "threads in gauge. Any finding: quarantine, engineering decides.",
}
assert list(NOTES) == NOTE_KEYS
notes = [NOTES[k] for k in NOTE_KEYS]
# x 219: clear of the ISO 5457 top centring mark, which the kit puts at the frame centre x 215
yn = sh2.notes(219.0, 281.0, notes, 188.0)
sh2.general_finish(sh2.tb[0] + 2.0, sh2.tb[3] + 3.0, "Ra 3.2")
sh2.text(272.0, sh2.tb[3] + 3.0, USED_ON, H)            # as on sheet 1, beside the finish symbol

if __name__ == "__main__":
    print("notes bottom y", round(yn, 1))
    sh.lint()
    sh.save("fwd_closure")
    sh2.lint()
    sh2.save("fwd_closure")
