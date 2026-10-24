"""SRM100-101 MOTOR CASE (A2, 1 sheet): full longitudinal section at 1:2 in the plane of
hole 0, details C / D (2:1) of the aft and forward ends, SECTION B-B (1:1) through the
aft bolt row, hole table, operations split between the loose tube and assembly
SRM100-000, case record table (R1 ... R10: what is measured, when, where and the
acceptance), notes.

Seal zones per decision G1-rev: each zone honed to the smallest diameter that cleans it
up and held to A +0.030/0, A = the smallest of the zone's six R4 readings; accept
CASE_ID <= A <= SEAL_A_MAX (92.070 = CASE_BORE_MAX - TOL_BORE[1]), so the bore is
<= CASE_BORE_MAX everywhere, zones included.  Drawn at A = 92.000; A recorded per
zone and marked on the tube.  theta = 0 per G3: set at match-drilling from the closure's puller P1
(theta 10), then carried on the case by hole 0, the clocking line and the marking.

View frame of the side views: u = motor z (0 at the aft end face, + forward),
v = model x.  The part is turned rot = -0.8 so that hole 0 (theta 0.8 deg) lies in
the cutting plane, at the top of the view.  B-B is seen from forward: u = x, v = y,
theta counter-clockwise, theta = 0 = +X.

Datum A = axis of the aft honed seal zone, datum E = axis of the forward one (the
closure that seats on each end face is located by its plug in that zone).  Letters
B, C, D are taken by the views.

Local primitives (the kit has none): finish_leader() (ISO 1302 symbol on a leader,
with the manufacturing method in position c and the lay in position d),
rect_detail() (rounded-rectangle detail indicator), cut_short() (cutting-plane ends
with short arrows, letters beside the thick ends), hole_callout() (a size dimension
with text beyond and a suffix after the tolerance), dia_ref() (a diameter across the
axis with a note reference after the tolerance), wrap_mm() (text wrapped to a width in
mm for table cells).
"""

import math

import numpy as np

import srm_dwg as D
import srm_params as P
from srm_dwg import DIA, DEG, TIMES, PM, Hatch, Part, Sheet, View, fmt

RI, RO = P.CASE_ID / 2.0, P.CASE_OD / 2.0          # 46, 50
L = P.CASE_L                                        # 690.8
CH = P.CASE_END_CHAMFER                             # 1.1 radial
CHZ = CH / math.tan(math.radians(P.CASE_END_CHAMFER_DEG))   # 3.022
OC = 0.5                                            # OD break (case.py)
BRK = P.CASE_HOLE_BORE_BREAK                        # 0.5 x 45, bore side
HR = P.CASE_HOLE_D / 2.0                            # 3.2
ZA = P.BOLT_EDGE                                    # aft row, 13
ZF = L - P.BOLT_EDGE                                # fwd row, 677.8
TH = P.bolt_thetas()
ROT = -TH[0]                                        # hole 0 into the cutting plane
HONE = 45.0                                         # honed seal-zone length (this sheet)
MARK = (20.0, 45.0)                                 # marking zone, z from each end face
LABEL_Z = (20.0, 35.0)                              # temperature labels, z from the aft face (G17)
LEN_TOL = 0.1
EDGE_TOL = 0.1                                      # bolt-row position from the end face, +/-
HOLE_TOL = (0.0, 0.03)                              # case hole 6.40 +0.03/0
LIG_NOM = ZA - HR                                   # 9.80
LIG_NEW_MIN = (ZA - EDGE_TOL) - (P.CASE_HOLE_D + HOLE_TOL[1]) / 2.0   # 12.9 - 3.215 = 9.685
HOLE_CHG_MAX = 0.05     # retire: hole length growth / ligament loss vs its own baseline (G14)
MASS = 2234.4

# take-up ring compression over the stack + case-length tolerance (note 6)
GAP_LO = P.TAKEUP_T - P.TOL_STACK - LEN_TOL
GAP_HI = P.TAKEUP_T + P.TOL_STACK + LEN_TOL
C_HI = 100.0 * (1.0 - GAP_LO / P.TAKEUP_FREE_T)
C_LO = 100.0 * (1.0 - GAP_HI / P.TAKEUP_FREE_T)

sh = Sheet("SRM100-101", "MOTOR CASE",
           "Case tube " + DIA + "100 " + TIMES + " 4 " + TIMES + " " + fmt(L)
           + ", bare 6061-T6, 2 " + TIMES + " 18 radial bolt holes",
           size="A2", material="6061-T6 drawn tube, ASTM B210M", mass_g=MASS, scale="1:2",
           finish="Ra 3.2")


# ---- local primitives --------------------------------------------------------------
NB = chr(160)    # no-break space: wrap_mm never splits there ('2 °C', '232 °C')


def wrap_mm(s, width, h=D.H):
    """Greedy word wrap to `width` paper mm (measured), lines joined with newlines;
    NB joins words that must stay on one line (written as a plain space)."""
    return _wrap_mm(s, width, h).replace(NB, " ")


def _wrap_mm(s, width, h=D.H):
    out = []
    for para in s.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w) if cur else w
            if cur and sh.text_width(t, h) > width:
                out.append(cur)
                cur = w
            else:
                cur = t
        out.append(cur)
    return "\n".join(out)


def finish_leader(p, q, value, process=None, lay=None, removal=True):
    """ISO 1302 / 21920-1 symbol on a leader: arrow on the surface at paper p, leader to
    q, horizontal reference line from q (to the right if q is right of p), the symbol
    standing on it.  value in position a (under the bar), process in position c (over
    the bar), lay symbol in position d (right of the V).  removal=False draws the
    'no material removal' circle instead of the bar."""
    s = sh
    p, q = np.asarray(p, float), np.asarray(q, float)
    s.line([p, q], D.THIN)
    s.arrow(p, p - q)
    t60 = math.tan(math.radians(60.0))
    h1, h2 = 3.5, 7.5
    tw = max(s.text_width(value) if value else 0.0, s.text_width(process) if process else 0.0)
    w = h1 / t60 + h2 / t60 + tw + 1.5          # symbol width, short arm to bar end
    sg = 1.0 if q[0] >= p[0] else -1.0
    x_tip = q[0] + (2.0 + h1 / t60) if sg > 0 else q[0] - 2.0 - w + h1 / t60
    T = np.array([x_tip, q[1]])
    x_end = q[0] + sg * (w + 3.0)
    s.line([q, (x_end, q[1])], D.THIN)
    ps, pl = T + (-h1 / t60, h1), T + (h2 / t60, h2)
    s.line([ps, T, pl], D.THIN)
    if removal:
        s.line([ps, T + (h1 / t60, h1)], D.THIN)
    else:
        r = h1 / 3.0
        s.circle(T + (0.0, 2.0 * r), r, D.THIN)
    s.line([pl, pl + (tw + 1.5, 0.0)], D.THIN)
    if value:
        s.text(pl[0] + 0.2, T[1] + h2 - 1.2 - D.H, value)
    if process:
        s.text(pl[0] + 0.2, T[1] + h2 + 0.8, process)
    if lay:
        s.text(T[0] + 2.2, T[1] + 0.4, lay)


def rect_detail(v, u0, v0, u1, v1, letter, at, r=1.5):
    """Detail indicator: thin rounded rectangle round view box (u0, v0)-(u1, v1),
    letter (3.5) centred at paper `at`."""
    a, b = v.pt(u0, v0), v.pt(u1, v1)
    x0, y0, x1, y1 = a[0], a[1], b[0], b[1]
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90),
                       (x0 + r, y0 + r, 180)):
        t = np.radians(np.linspace(a0, a0 + 90, 8))
        pts += list(np.c_[cx + r * np.cos(t), cy + r * np.sin(t)])
    pts.append(pts[0])
    sh.line(pts, D.THIN)
    sh.text(at[0], at[1] - 1.75, letter, 3.5, ha="center")


def cut_short(v, u, v_lo, v_hi, letter, look=(-1.0, 0.0), ext=2.5, thick=5.0, arr=4.5):
    """Cutting-plane indication (ISO 128-44) across a side view at u: thin chain from
    v_lo to v_hi, thick ends `thick` long outside them (starting `ext` paper mm out),
    arrows `arr` long along `look` at the outer ends, letter beyond each thick end."""
    pa, pb = v.pt(u, v_lo), v.pt(u, v_hi)
    sh.line([pa, pb], D.THIN, "center")
    L_ = np.asarray(look, float)
    for p, sg in ((pb, 1.0), (pa, -1.0)):
        e0 = p + (0.0, sg * ext)
        e1 = e0 + (0.0, sg * thick)
        sh.line([e0, e1], 0.7, cap="butt")
        sh.line([e1, e1 + L_ * arr], D.THIN)
        sh.arrow(e1 + L_ * arr, L_)
        t = e1 + (0.0, sg * 2.2)
        sh.text(t[0], t[1] if sg > 0 else t[1] - 3.5, letter, 3.5, ha="center")


def hole_callout(v, a, b, y, pre, tol, suffix, lines, dec=2):
    """Size dimension across a hole seen in section (arrows outside, text beyond b),
    `suffix` after the tolerance and further text lines above it (list, top first).
    The value is |b.u - a.u| in model mm, written with `dec` places (6.40: the same
    number of places as the tolerance)."""
    s = sh
    pa, pb = v.pt(*a), v.pt(*b)
    for p in (pa, pb):
        s.line([(p[0], p[1] + D.EXT_GAP), (p[0], y + D.EXT_OVER)], D.THIN)
    tail = D.ARROW_L + 2.5
    s.arrow((pa[0], y), (1.0, 0.0))
    s.arrow((pb[0], y), (-1.0, 0.0))
    main = pre + DIA + f"{abs(b[0] - a[0]):.{dec}f}"
    x0 = pb[0] + tail + 0.5
    W = v._dimtext((x0, y + D.TEXT_GAP), 0.0, main, tol, anchor="left")
    x1 = x0 + W + 0.3
    s.text(x1, y + D.TEXT_GAP, suffix)
    x2 = x1 + s.text_width(suffix)
    s.line([(pa[0] - tail, y), (x2 + 1.0, y)], D.THIN)
    for k, t_ in enumerate(lines[::-1]):
        s.text(x0, y + D.TEXT_GAP + 5.2 + 3.9 * k, t_)


# ---- main view: full section at 1:2 ---------------------------------------------------
X0, Y0 = 48.0, 350.0
part_m = Part("case.step", hatch=Hatch(45, 1.0))
vm = View(sh, part_m, (X0, Y0), 0.5, look="side", section="full", rot=ROT, axis=False)

# overall length (note 6)
vm.dim_h((0.0, RO - OC), (L, RO - OC), off=18.0, tol=PM + fmt(LEN_TOL))

def dia_ref(v, u, r, main, tol, ref, arrows=(True, True), centre=1.5):
    """Bore diameter across the axis at u with a note reference written after the
    tolerance on the same line (the kit puts a suffix before the tolerance).  The whole
    text is centred `centre` paper mm above the axis; returns the paper x range the
    text occupies, so the axis can be interrupted there."""
    h = D.H
    up, lo = tol
    W = sh.text_width(main, h) + max(sh.text_width(up, h * 0.72),
                                     sh.text_width(lo, h * 0.72)) + 0.6
    gap = 0.9
    Wc = W + gap + sh.text_width(ref, h)
    shift = centre - Wc / 2.0 + W / 2.0
    v.dim_dia(u, r, at=u, text=main, tol=tol, arrows=arrows, shift=shift)
    xl = v.pt(u, 0)[0]
    y0 = v.pt(u, 0)[1] + centre - Wc / 2.0
    sh.text(xl - D.TEXT_GAP, y0 + W + gap, ref, h, rot=90.0)
    # the upper tolerance stands 0.62 h off the baseline and is 0.72 h tall (kit _dimtext)
    return (xl - D.TEXT_GAP - h * (0.62 + 0.72) - 0.7, xl + 0.6)


# OD: stock, arrows from outside, text in the bore
U_OD = 480.0
vm.dim_dia(U_OD, RO, at=U_OD, suf=" (NOTE 1)", where="out")
x_od = vm.pt(U_OD, 0)[0]
axis_gaps = [(x_od - 4.8, x_od + 0.6)]
# the OD stays as drawn: material removal not permitted (the general Ra 3.2 is for
# the machined surfaces)
p_od = vm.pt(110.0, -RO)
finish_leader(p_od, p_od + (6.0, -14.0), "", process="drawn tube", removal=False)

# honed seal zones (decision G1): the drawn size is A +0.030/0 at A = 92.000 (note 4);
# size + datum feature (triangle in line with the dimension line, replacing an arrow)
UA, UF = 32.0, L - 32.0
tol_bore = tuple(("+" if t > 0 else "") + (f"{t:.3f}" if t else "0") for t in P.TOL_BORE[::-1])
BORE_TXT = DIA + f"{P.CASE_ID:.3f}"
axis_gaps.append(dia_ref(vm, UA, RI, BORE_TXT, tol_bore, "(NOTE 4)", arrows=(False, True)))
vm.datum((UA, -RI), "A", (0, -1), length=8.0)
axis_gaps.append(dia_ref(vm, UF, RI, BORE_TXT, tol_bore, "(NOTE 4)", arrows=(False, True)))
vm.datum((UF, -RI), "E", (0, -1), length=8.0)

# the bore between the seal zones: as drawn (note 5); straightness of its lines
UM = L / 2.0
axis_gaps.append(dia_ref(vm, UM, RI, DIA + f"{P.CASE_ID:.2f}",
                         (f"+{P.CASE_BORE_MAX - P.CASE_ID:.2f}", "0"), "(NOTE 5)"))
pm_ = vm.pt(UM + 38.0, -RI)
sh.fcf(pm_[0] - 8.0, pm_[1] + 7.0, ["straightness", "0.3"], leader=pm_)

# axis, interrupted where the diameter texts cross it
xa = [vm.pt(0, 0)[0] - 3.0]
for g0, g1 in sorted(axis_gaps):
    xa += [g0, g1]
xa.append(vm.pt(L, 0)[0] + 3.0)
for k in range(0, len(xa), 2):
    sh.line([(xa[k], Y0), (xa[k + 1], Y0)], D.THIN, "center")

# cutting plane B-B through the aft row, detail indicators C and D
cut_short(vm, ZA, -RO, RO, "B")
rect_detail(vm, -6.0, 43.5, 54.0, 52.5, "C", vm.pt(58.0, 57.0))
rect_detail(vm, L - 54.0, 43.5, L + 6.0, 52.5, "D", vm.pt(L - 58.0, 57.0))
# forward-row hole centre lines (hole 0 on top, hole 9 at the bottom, 0.8 deg off the plane)
for vv in (RO, -RO):
    sg = 1.0 if vv > 0 else -1.0
    vm.line([(ZF, sg * (RI - 3.0)), (ZF, sg * (RO + 3.0))])

yl = Y0 - RO * 0.5 - 22.0
sh.text(vm.pt(0, 0)[0], yl, "AFT END", 2.5)
sh.text(vm.pt(L, 0)[0], yl, "FWD END", 2.5, ha="right")
sh.text(vm.pt(L / 2.0, 0)[0], yl, "Full section in the plane of hole 0 (" + chr(952) + " "
        + fmt(TH[0], 1) + DEG + " / " + fmt(TH[0] + 180.0, 1) + DEG + "), see SECTION B-B",
        2.5, ha="center")

# ---- details C (aft end) and D (fwd end), 2:1 ------------------------------------------
S2 = 2.0
YB = 248.0                                  # paper y of the bore line in both details
XC = 54.0                                   # paper x of u = 0 in C
XD = 372.0                                  # paper x of u = L in D
part_d = Part("case.step", hatch=Hatch(45, 1.5))
vc = View(sh, part_d, (XC, YB - S2 * RI), S2, look="side", section="full", rot=ROT,
          axis=False, window=(-3.0, RI - 0.1, 56.0, RO + 2.5))
vd = View(sh, part_d, (XD - S2 * L, YB - S2 * RI), S2, look="side", section="full", rot=ROT,
          axis=False, window=(L - 56.0, RI - 0.1, L + 3.0, RO + 2.5))
vc.zigzag((56.0, RI), (56.0, RO))
vd.zigzag((L - 56.0, RI), (L - 56.0, RO))


def end_detail(v, e, s, letter):
    """Dimensions of one end.  e = u of the end face, s = +1 (aft, material to the
    right) or -1 (fwd)."""
    z = lambda d: e + s * d                       # u at distance d in from the end face
    x = lambda d: v.pt(z(d), 0)[0]
    # hole centre line
    v.line([(z(ZA), RI - 1.5), (z(ZA), RO + 1.5)], D.THIN, "center")
    # 20 deg x 1.1 radial O-ring lead-in
    v.dim_v((z(0.0), RI + CH), (z(CHZ), RI), at=z(-4.0))
    if s > 0:
        v.dim_ang((z(CHZ), RI), 180.0 - P.CASE_END_CHAMFER_DEG, 180.0, 24.0, dec=0,
                  ext_from=6.5)
    else:
        v.dim_ang((z(CHZ), RI), 0.0, P.CASE_END_CHAMFER_DEG, 24.0, dec=0, ext_from=6.5)
    # outside break
    v.leader((z(OC / 2), RO - OC / 2), -8.0 * s, 12.0, "0.5" + TIMES + "45" + DEG)
    # honed seal zone: thick chain line beside the bore, length from the end face
    yb = v.pt(0, RI)[1]
    sh.line([(x(CHZ), yb - 1.5), (x(HONE), yb - 1.5)], D.THICK, "center")
    v.dim_h((z(0.0), RI + CH), (z(ZA), RI), off=-22.0, tol=PM + fmt(EDGE_TOL, 1))
    v.dim_h((z(0.0), RI + CH), (z(HONE), RI), off=-30.0, tol=("+5", "0"))
    # form of the seal zone, its texture
    xf = x(8.0)
    fw = 6.5 + sh.text_width("0.02") + 2.4
    sh.fcf(xf - 8.0 if s > 0 else xf - fw + 8.0, yb - 14.0, ["cylindricity", "0.02"],
           leader=(xf, yb))
    xs = x(26.0)
    finish_leader((xs, yb), (xs + 6.0 * s, yb - 16.0), "Ra max 0.8", process="honed",
                  lay="⊥")
    # end face square to the local seal-zone axis
    datum = "A" if s > 0 else "E"
    pw = 6.5 + sh.text_width("0.05") + 2.4 + 6.5
    xe = x(0.0)
    sh.fcf(xe - 6.3 - pw if s > 0 else xe + 6.0, yb - 20.0,
           ["perpendicularity", "0.05", datum], leader=(xe, yb - 16.75))
    # marking zone on the OD (note 8)
    yo = v.pt(0, RO)[1]
    sh.line([(x(MARK[0]), yo + 1.3), (x(MARK[1]), yo + 1.3)], D.THICK, "center")
    if s > 0:      # clear of the hole callout
        v.leader((z(MARK[1] - 2.0), RO + 0.65), 12.0, 8.0, "MARKING (NOTE 8)", end="dot")
    else:          # clear of the bore-break callout
        v.leader((z(MARK[1] - 4.0), RO + 0.65), -6.0, 19.0, "MARKING (NOTE 8)", end="dot")
    sh.text((x(-3.0) + x(56.0)) / 2, 284.0, f"DETAIL {letter} (2:1)", 3.5, ha="center")


end_detail(vc, 0.0, 1.0, "C")
end_detail(vd, L, -1.0, "D")

# C: the bolt holes (36 = 18 per end)
hole_callout(vc, (ZA - HR, RO), (ZA + HR, RO), vc.pt(0, RO)[1] + 8.0,
             "36" + TIMES + " ", (f"+{HOLE_TOL[1]:.2f}", "0"), " THRU",
             ["REAMED, MATCH-DRILLED WITH", "THE CLOSURE SEATED (NOTE 7)"])
# D: bore-side break of the holes, through the hole
vd.leader((ZF + HR + BRK / 2, RI + BRK / 2), -16.0, 14.0,
          ["36" + TIMES + " 0.5" + TIMES + "45" + DEG, "BORE SIDE, POLISHED"])

# ---- hole table ------------------------------------------------------------------------
TX, TY = 190.0, 290.0
sh.text(TX, TY + 3.0, "BOLT HOLES, EACH ROW", 2.5, bold=True)
th_s = lambda t: fmt(t, 1) + DEG
rows = [["HOLE", chr(952) + " " + PM + "0.1" + DEG, "HOLE", chr(952) + " " + PM + "0.1" + DEG]]
for k in range(9):
    rows.append(["0 KEY" if k == 0 else str(k), th_s(TH[k]), str(k + 9), th_s(TH[k + 9])])
sh.table(TX, TY, [14, 16, 12, 16], rows, row_h=6.0, align=["c", "r", "c", "r"])

# ---- SECTION B-B (1:1): the aft row seen from forward ----------------------------------
CB = np.array([490.0, 340.0])
part_b = Part("case.step", hatch=Hatch(45, 1.5))
vb = View(sh, part_b, CB, 1.0, look="fwd", z_cut=ZA, keep="below")
sh.line([CB - (56.0, 0.0), CB + (84.0, 0.0)], D.THIN, "center")
sh.line([CB - (0.0, 56.0), CB + (0.0, 56.0)], D.THIN, "center")
for k, t in enumerate(TH):
    d = np.array([math.cos(math.radians(t)), math.sin(math.radians(t))])
    sh.line([CB + d * (RI - 4.0), CB + d * (RO + 4.0)], D.THIN, "center")
    # holes 0 and 9 sit on the axis: their numbers go below / above it (P1 is above 0)
    p = CB + d * 40.0 + {0: (0.0, -2.9), 9: (0.0, 2.6)}.get(k, (0.0, 0.0))
    sh.text(p[0], p[1], str(k), 2.5, ha="center", va="center")
p0 = CB + np.array([math.cos(math.radians(TH[0])), math.sin(math.radians(TH[0]))]) * 40.0
sh.text(p0[0] - 2.2, p0[1] - 2.9, "KEY", 2.5, ha="right", va="center")
# angles: hole 0 off theta = 0, the even pattern
vb.dim_ang((0.0, 0.0), 0.0, TH[0], 70.0, ext=False, text_r=72.0, text_dy=2.2)
d0 = np.array([math.cos(math.radians(TH[0])), math.sin(math.radians(TH[0]))])
sh.line([CB + d0 * (RO + 4.5), CB + d0 * 72.0], D.THIN)
vb.dim_ang((0.0, 0.0), 0.0, TH[1], 62.0, ext_from=RO + 4.5,
           text="17" + TIMES + " " + fmt(TH[1], 0) + DEG + " (= " + fmt(TH[-1], 0) + DEG + ")")
sh.text(CB[0] + 72.0, CB[1] - 4.0, chr(952) + " = 0", 2.5)
# +theta sense
t = np.radians(np.linspace(40.0, 70.0, 20))
arc = np.c_[CB[0] + 24.0 * np.cos(t), CB[1] + 24.0 * np.sin(t)]
sh.line(arc, D.THIN)
sh.arrow(arc[-1], arc[-1] - arc[-3])
pt_ = CB + 18.0 * np.array([math.cos(math.radians(55.0)), math.sin(math.radians(55.0))])
sh.text(pt_[0], pt_[1], "+" + chr(952), 2.5, ha="center", va="center")
sh.text(CB[0], CB[1] + 60.0, "SECTION B-B (1:1)", 3.5, ha="center")
# the closure's puller holes P1 / P2 (adjacent part, phantom): they carry theta = 0
# until match-drilling (decision G3)
PUL = P.puller_thetas()
for lab, t_p in (("P1", PUL[0]), ("P2", PUL[1])):
    d = np.array([math.cos(math.radians(t_p)), math.sin(math.radians(t_p))])
    c_ = CB + d * P.HOLDER_PULLER_R            # aft row: the nozzle holder's pullers
    sh.circle(c_, 3.0, D.THIN, "phantom")      # M6 puller thread (decision G5), outline
    sg = 1.0 if d[0] > 0 else -1.0
    sh.text(c_[0] - sg * 4.2, c_[1], lab, 2.5, ha="right" if sg > 0 else "left", va="center")
TH_ = chr(952)
bb_notes = [
    "Seen from forward: " + TH_ + " counter-clockwise (clockwise seen from aft), " + TH_
    + " = 0 = +X. Hole 0 (KEY) at " + fmt(TH[0], 1) + DEG + ", holes 1 ... 17 at "
    + fmt(TH[1], 0) + DEG + " steps. Forward row (z " + fmt(ZF, 1) + ", 13 " + PM + "0.1 "
    "from the fwd end face): the same pattern and numbering, its hole 0 in line with the "
    "aft hole 0 within " + PM + "2" + DEG + ".",
    TH_ + " = 0 is set at match-drilling (op 120) from the closure's puller hole P1 at "
    + TH_ + " " + fmt(PUL[0], 0) + DEG + " (P2 at " + fmt(PUL[1], 0) + DEG + "; shown in "
    "phantom at the nozzle holder's R" + fmt(P.HOLDER_PULLER_R) + ", on its aft face; "
    "forward closure: R" + fmt(P.PULLER_R) + ", on its fwd face): hole 0 goes "
    + fmt(PUL[0] - TH[0], 1) + DEG + " clockwise of P1 seen from forward ("
    + fmt(PUL[0] - TH[0], 1) + DEG + " counter-clockwise seen from aft). From then on "
    "hole 0, the clocking line and the AFT / FWD marking (note 8) carry " + TH_ + " = 0 on "
    "the case.",
]
yb_ = sh.notes(432.0, 280.0, bb_notes, 150.0, title=None, numbered=False)

# ---- operations -------------------------------------------------------------------------
LE, GE = chr(8804), chr(8805)
A_MIN, A_MAX = P.CASE_ID, P.SEAL_A_MAX             # decision G1-rev: 92.000 <= A <= 92.070
A_TOL = P.TOL_BORE[1]                               # zone held to A +0.030/0: <= 92.10
LAND_OFF = P.CASE_ID - P.PLUG_OD                    # plug land A - 0.06
GRV_OFF = P.CASE_ID - P.ORING_GROOVE_D              # groove bottom A - 5.67
CLK = P.puller_thetas()[0] - TH[0]                  # hole 0 is 9.2 deg from P1
ZA_REC = (10.0, 25.0, 40.0)                         # A read at these z from the end face
HAZ = [TH[k] + 0.5 * 360.0 / P.N_BOLTS for k in (2, 6, 11, 15)]   # 50/130/230/310, between holes
HZ, HREF = (5.0, 25.0), 100.0                       # hardness band and reference, from each end
STN = [60.0, L / 4.0, L / 2.0, 3.0 * L / 4.0, L - 60.0]            # proof OD stations S1 ... S5

OPA = [
    ("10", "Receive the tube with its mill certificate (note 1, R1). Cut and face both ends "
     "to " + fmt(L) + " " + PM + fmt(LEN_TOL) + "; end faces square to the bore ("
     + D.GDT["perpendicularity"] + " 0.05 A / E, checked after op 30)."),
    ("20", "Turn the 0.5" + TIMES + "45" + DEG + " OD break and bore the 20" + DEG + TIMES
     + "1.1 radial O-ring lead-in at both ends (details C, D); lead-in blended into the "
     "bore, no step, Ra 0.8."),
    ("30", "Label the ends AFT and FWD (removable tape). Measure each seal zone (two-point). "
     "Hone the zone, " + fmt(HONE, 0) + " +5/0 from the end face, to the smallest diameter "
     "that cleans it up: Ra 0.4 (0.8 max), circumferential lay, cylindricity 0.02, run-out "
     "blended into the as-drawn bore. A = the smallest of its six R4 readings; accept "
     + f"{A_MIN:.3f} {LE} A {LE} {A_MAX:.3f}" + ", zone A +" + f"{A_TOL:.3f}" + "/0 "
     "(note 4). Record A (R4) and write it on the tape label."),
    ("40", "Inspect and record (R2 ... R6): UT wall " + GE + " " + f"{P.CASE_WALL_MIN:.2f}"
     + " and bore " + DIA + " " + LE + " " + f"{P.CASE_BORE_MAX:.2f}" + " (note 3); seal "
     "zones A +" + f"{A_TOL:.3f}" + "/0; mid bore, straightness, GO plug and liner trial "
     "(note 5); length and " + D.GDT["perpendicularity"] + "."),
    ("50", "Clean (IPA), cap the ends, tag with the case serial and both A values. The tube "
     "leaves this stage with NO bolt holes and NO permanent marking; the closures are "
     "finished to the A of their end (SRM100-102, -103)."),
]
OPB = [
    ("110", "Take the AFT end (tape label) and the nozzle holder SRM100-102 finished to its "
     "A (FWD end: forward closure SRM100-103). Seat the closure in the bore, flange on the "
     "end face, O-rings not fitted. Clamp the pair."),
    ("120", "Clock hole 0 from the closure's puller hole P1 (" + TH_ + " "
     + fmt(P.puller_thetas()[0], 0) + DEG + "): " + fmt(CLK, 1) + DEG + " clockwise of P1 "
     "seen from forward, " + fmt(CLK, 1) + DEG + " counter-clockwise seen from aft "
     "(SECTION B-B). Drill " + DIA + fmt(P.BOLT_TAP_DRILL, 1) + " (tap "
     "drill) through the case wall into the closure, depth stops per SRM100-102 / -103: "
     "hole 0 first, then holes 1 ... 17."),
    ("130", "Case wall only, closure still in place: drill " + DIA + "6.2 and ream " + DIA
     + f"{P.CASE_HOLE_D:.2f} +{HOLE_TOL[1]:.2f}/0" + ", piloted in the " + DIA + fmt(P.BOLT_TAP_DRILL, 1) + " hole; stop "
     "when the full diameter is through the case bore (the entry cone left in the closure, "
     "0.5 deep max, lies in its first, uncounted thread). Tap the closure M6 through the "
     "case holes (per SRM100-102 / -103)."),
    ("140", "Scribe the clocking line at " + TH_ + " = 0 across the case end and the "
     "closure flange; mark the closure per SRM100-102 note 8 / SRM100-103 note 11 (pair "
     "serial included); the case end is marked at op 160 (note 8). Remove the closure."),
    ("150", "Break every hole on the bore side 0.5" + TIMES + "45" + DEG + " and polish "
     "(the O-rings are dragged over it); deburr the OD edges. Remove all chips; re-inspect "
     "the seal zone. Repeat ops 110 ... 150 at the FWD end, the forward closure turned so "
     "that its P1 lies " + fmt(CLK, 1) + DEG + " counter-clockwise (seen from forward) of "
     "the aft hole 0 line, transferred along the tube, " + PM + "2" + DEG + "."),
    ("160", "Remove the tape labels and mark the case (note 8). Record the hole baseline "
     "(R7). Proof test on SRM100-001 (R9), then take the hardness / conductivity baseline "
     "(R8)."),
]
OX, OY = 24.0, 197.0          # below the centring mark at y 210
WA, WB = 176.0, 176.0
sh.text(OX, OY + 1.5, "OPERATIONS", 3.5, bold=True)
rows = [["OP", "LOOSE TUBE (as supplied to assembly)", "OP",
         "AT ASSEMBLY SRM100-000, each end with its closure seated"]]
for i in range(max(len(OPA), len(OPB))):
    a = OPA[i] if i < len(OPA) else ("", "")
    b = OPB[i] if i < len(OPB) else ("", "")
    rows.append([a[0], wrap_mm(a[1], WA - 3.0), b[0], wrap_mm(b[1], WB - 3.0)])
yo_ = sh.table(OX, OY - 2.5, [12, WA, 12, WB], rows, row_h=6.0, align=["c", "l", "c", "l"])

# ---- case record: what is measured, when, where, and the acceptance -----------------------
fz = lambda z: fmt(z, 1)
REC = [
    ("R1", "Mill certificate", "op 10",
     "ASTM B210M, 6061-T6, heat / lot number", "per B210M"),
    ("R2", "Wall, ultrasonic map", "op 40",
     "8 azimuths every 50 along the full length; all round each bolt row, z 5 ... 21 from "
     "each end face", "wall " + GE + " " + f"{P.CASE_WALL_MIN:.2f}" + " everywhere"),
    ("R3", "Bore, two-point", "op 30 (pre-hone), op 40",
     "every 50 along the length, 2 directions 90" + DEG + " apart",
     LE + " " + f"{P.CASE_BORE_MAX:.2f}" + " everywhere, honed zones included (R4); mid "
     "bore note 5"),
    ("R4", "Seal zones AFT, FWD: A and diameters", "op 30, op 40",
     "z " + ", ".join(fmt(z, 0) for z in ZA_REC) + " from the end face " + TIMES + " 2 "
     "directions 90" + DEG + " apart, to 0.001: A = the smallest of these 6 readings, per "
     "zone; Ra; A also marked on the tube (note 8)",
     f"{A_MIN:.3f} {LE} A {LE} {A_MAX:.3f}; zone A +{A_TOL:.3f}/0 (so {LE} "
     f"{P.CASE_BORE_MAX:.2f}); Ra {LE} 0.8"),
    ("R5", "Mid bore", "op 40",
     "surface-line straightness; GO plug " + DIA + "91.70 " + TIMES + " 150 over the full "
     "length; liner SRM100-110 slide trial", "note 5"),
    ("R6", "Length, end faces", "op 40",
     "length at 4 azimuths; each end face to its datum A / E",
     fmt(L) + " " + PM + fmt(LEN_TOL) + "; " + D.GDT["perpendicularity"] + " 0.05"),
    ("R7", "Hole baseline, 36 holes", "op 160, before the first proof; after every proof",
     "per hole: axial and circumferential " + DIA + ", ligament end face to hole edge "
     "(nominal " + fmt(ZA, 1) + " - " + fmt(HR, 1) + " = " + f"{LIG_NOM:.2f}" + "; a new "
     "in-tolerance case can start at " + fmt(ZA - EDGE_TOL, 1) + " - "
     + f"{(P.CASE_HOLE_D + HOLE_TOL[1]) / 2.0:.3f}" + " = " + f"{LIG_NEW_MIN:.3f}"
     + ", so no absolute limit)",
     "retire the end if any hole's axial length has grown, or its ligament has shrunk, by "
     "more than " + f"{HOLE_CHG_MAX:.2f}" + " from that hole's own baseline"),
    ("R8", "Hardness and conductivity baseline", "op 160, after the first proof",
     "HRB or Webster B, and eddy-current %IACS, at " + TH_ + " "
     + ", ".join(fmt(t, 0) + DEG for t in HAZ) + " (between the holes): aft end z "
     + fz(HZ[0]) + " ... " + fz(HZ[1]) + " and z " + fz(HREF) + "; fwd end z "
     + fz(L - HZ[1]) + " ... " + fz(L - HZ[0]) + " and z " + fz(L - HREF),
     "record, same instrument and scale for life (6061-T6: about 95 HB (about 60 HRB), "
     "Webster B " + GE + " 15, 40 ... 46 %IACS)"),
    ("R9", "Proof OD, SRM100-001", "before and after every proof",
     "stations S1 ... S5 at z " + ", ".join(fz(z) for z in STN) + " from the aft face, "
     "on removable tape; diameters through " + TH_ + " 45" + DEG + " and 135"
     + DEG + ", micrometer 0.001, tube temperature at the two readings within 2" + NB + DEG + "C",
     "permanent set " + LE + " " + fmt(P.PROOF_SET_MAX) + " at every station"),
    ("R10", "After every firing, before re-use", "each firing",
     "temperature labels (note 8), read and recorded before extraction; hardness and %IACS "
     "on the aft end at the R8 positions; holes as R7; seal zones visual (no scratch across "
     "the lay)",
     "label " + GE + " 232" + NB + DEG + "C: re-proof or retire that end; > 46 %IACS, or "
     "hardness more than 10 % below its R8 baseline on the same instrument and scale: "
     "retire"),
]
RW = [10.0, 50.0, 48.0, 160.0, 108.0]
yr0 = yo_ - 7.0
sh.text(OX, yr0 + 1.5, "CASE RECORD (note 9)", 3.5, bold=True)
rows = [["REC", "CHECK", "WHEN", "WHERE / HOW", "ACCEPT"]]
for r_ in REC:
    rows.append([r_[0]] + [wrap_mm(c, w - 2.6) for c, w in zip(r_[1:], RW[1:])])
yr_ = sh.table(OX, yr0 - 2.5, RW, rows, row_h=5.2, align=["c", "l", "l", "l", "l"])

# ---- notes --------------------------------------------------------------------------------
notes = [
    "Material: 6061-T6 seamless drawn tube to ASTM B210M, " + DIA + "100 " + TIMES + " 4.0 wall, "
    "mill certificate with heat / lot number (R1). OD and wall not machined: " + DIA + "100 "
    "to the B210M tolerance, ISO 2768-mK does not apply to it. No heat treatment, welding, "
    "straightening or stamping.",
    "Finish: none. The case is left bare (no anodising, paint or coating). Clean, oil-free, "
    "no marking ink or tape residue left on it.",
    "Tube acceptance (op 40, R2, R3): wall " + GE + " " + f"{P.CASE_WALL_MIN:.2f}"
    + " everywhere and bore " + DIA + " " + LE + " " + f"{P.CASE_BORE_MAX:.2f}" + " everywhere "
    "(two-point), the honed seal zones included (note 4 keeps them there). Reject the tube "
    "otherwise.",
    "Seal zones (thick chain lines, details C, D; drawn at A = " + f"{A_MIN:.3f}" + "): hone "
    "each zone to the smallest diameter that cleans it up, A, and hold it to A +"
    + f"{A_TOL:.3f}" + "/0, Ra 0.4 (Ra 0.8 max), circumferential lay. A = the smallest of "
    "the zone's six R4 readings, recorded per zone and marked next to it (note 8). Accept "
    + f"{A_MIN:.3f} {LE} A {LE} {A_MAX:.3f}" + " (so no zone exceeds "
    + f"{P.CASE_BORE_MAX:.2f}" + "), else reject the tube. Closures finished to the A of "
    "their zone: plug land A - " + f"{LAND_OFF:.2f}" + " (0/" + f"{P.TOL_LAND[0]:.2f}"
    + "), O-ring groove bottom A - " + f"{GRV_OFF:.2f}" + " (0/" + f"{P.TOL_GROOVE[0]:.2f}"
    + "), i.e. " + f"{P.PLUG_OD:.2f}" + " / " + f"{P.ORING_GROOVE_D:.2f}" + " at A = "
    + f"{A_MIN:.3f}" + " (SRM100-102, -103). Hone run-out blended into the as-drawn bore, "
    "no step. Datum A / E: axis of the aft / fwd honed zone.",
    "Bore between the seal zones as drawn: " + DIA + f"{P.CASE_ID:.2f}" + " ... "
    + f"{P.CASE_BORE_MAX:.2f}" + " (the clearance parts are sized to it), surface lines "
    "straight within 0.3. A GO plug " + DIA + "91.70 " + TIMES + " 150 and liner SRM100-110 "
    "must pass the full length by hand. A bore under " + f"{P.CASE_ID:.2f}"
    + " is honed to " + f"{P.CASE_ID:.2f}" + " ... " + f"{P.CASE_BORE_MAX:.2f}"
    + " full length.",
    f"Length {fmt(L)} {PM}{fmt(LEN_TOL)} closes the axial stack (SRM100-000): 2 closure plugs, "
    f"2 insulators, {P.N_GRAINS} grains {PM}{fmt(P.TOL_GRAIN_L)}, {P.N_SPACERS} spacers "
    f"{PM}{fmt(P.TOL_SPACER_T)} and the take-up ring, {fmt(P.TAKEUP_T, 1)} installed. Stack "
    f"{PM}{fmt(P.TOL_STACK)} + case {PM}{fmt(LEN_TOL)} gives a take-up gap of "
    f"{fmt(GAP_LO, 1)} ... {fmt(GAP_HI, 1)}, i.e. {C_HI:.0f} ... {C_LO:.0f} % compression of "
    f"the {fmt(P.TAKEUP_FREE_T, 1)} silicone sponge (limit 25 ... 50 %). The gap is measured "
    f"at assembly.",
    "Bolt holes ONLY at assembly (ops 110 ... 150), the mating closure seated. Each case "
    "end and its closure are a serialised pair: never interchange closures or turn the case "
    "end for end.",
    f"Marking (op 160), laser or dot-peen, 0.05 deep max, 3 mm characters: on the OD next "
    f"to hole 0 at each end, z {fmt(MARK[0], 0)} ... {fmt(MARK[1], 0)} from the end face, "
    "centred on " + TH_ + " = 0, reading round the tube: 'SRM100-101  S/N ...' over "
    "'AFT  A 92.xxx' (aft end) or 'FWD  A 92.xxx' (fwd end), A of that zone (note 4). "
    "Clocking line (op 140): scribed 0.05 deep max at " + TH_ + " = 0, z 0 ... 8, continued "
    "across the closure flange. Temperature labels, fitted new at assembly for every "
    "firing: irreversible 177 / 204 / 232 / 260 " + DEG + "C strips on the OD at z "
    + fmt(LABEL_Z[0], 0) + " ... " + fmt(LABEL_Z[1], 0) + " from the aft face, " + TH_
    + NB + "90" + DEG + " and 270" + DEG + ", clear of the marking and head sweep (two more on "
    "the holder, SRM100-102); read and recorded before extraction (R10).",
    "Re-use: the case is re-used after inspection (R10) after every firing. Proof test on "
    "SRM100-001 (R9) before first use and after any repair, any retired-and-replaced "
    "closure, or a temperature label reading " + GE + " 232 " + DEG + "C. The case record "
    "R1 ... R10 stays with the case serial for its life, with the closure pair serials.",
    "Edges ISO 13715 -0.3 / +0.3 unless stated.",
    "USED ON: SRM100-000 motor, item 1 (1 off); SRM100-001 hydrostatic proof assembly, item 1.",
]
yn = sh.notes(410.0, yb_ - 3.0, notes, 168.0)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")

if __name__ == "__main__":
    sh.lint()
    sh.save("case")
