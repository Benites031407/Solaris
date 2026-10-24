"""SRM100-000 sheet 3 of 3: MOTOR ASSEMBLY - FORWARD END (installation sheet, A2).

Main view: partial half-section E-E at 1:1 (window + ISO 128 zig-zag break) of the
forward closure build-up in the case's forward end, with the forward end of the
grain stack.  Every srm_assembly.placements() row is turned rot = -0.8 so that
screw / hole 0 (theta 0.8 deg) lies in the cutting plane.  End view F (reference
arrow method) from forward: tightening sequence, keying, pullers.  Details G (case
seal gland) and H (take-up ring, liner float, bonded EPDM insulator) at 5:1.  The
grain stack is shown as an interrupted view of the same section E-E at 1:1 (five
windows), with the stack-up in a table: nominal lengths from srm_params and
srm_assembly, the cavity and gap measured at loading.

View frame: u = motor z (0 at the case's aft end face, + forward), v = radius.
Item numbers are those of the parts list on sheet 1.

Local primitives (not in srm_dwg): cut_path / _split_path (stepped cutting-plane
line with a thick corner, copied from sheet 2), seq_tag (boxed tightening-sequence
number), view_arrow (ISO 128 reference arrow with its letter), dim_across (linear
dimension between points of two different windows of an interrupted view),
thread_34 (ISO 6410 thin 3/4 arc on a tapped hole seen end on), sym_mark (ISO 128
symmetry mark: two short parallel lines across the end of a symmetry line).
"""

import json
import math

import numpy as np

import srm_dwg as D
import srm_params as P
import srm_assembly as A
import nozzle_insulator as NI
import nozzle_cap as NC
from srm_dwg import DEG, DEPTH, DIA, PM, TIMES, THIN, Hatch, Part, Sheet, View, fmt

PL = {n: (st, tr) for g, n, st, tr in A.placements()}
S = P.nozzle_stations()
TH = P.bolt_thetas()
PTH = P.puller_thetas()
ROT = -TH[0]                                   # hole 0 into the cutting plane

# ---- model stations (motor frame) ----------------------------------------------------
Z_CF = P.Z_CASE_FWD                            # case forward end face = flange bearing face
Z_FT = Z_CF + P.FLANGE_T                       # flange forward face = thrust face
Z_PF = P.Z_FWD_PLUG_FACE                       # closure inboard face = item 7 forward face
Z_IA = P.Z_FWD_INSUL_AFT                       # item 7 aft face = forward end of the cavity
Z_LF = P.Z_LINER_FWD                           # liner forward end
Z_LA = P.Z_LINER_AFT                           # item 4 forward face = liner / S0 aft face
Z_TU = P.takeup_z()                            # take-up aft face = S4 forward face
Z_S4 = P.spacer_z(P.N_SPACERS - 1)
Z_BF = P.bolt_z_fwd()                          # bolt row
Z_GO = Z_CF - P.GROOVE_1_Z                     # outer groove (toward the flange)
Z_GI = Z_CF - P.GROOVE_2_Z                     # inner groove
GW = P.GROOVE_W / 2.0
R_CASE = P.CASE_OD / 2.0
R_BORE = P.CASE_ID / 2.0
R_LAND = P.PLUG_OD / 2.0
R_GRV = P.ORING_GROOVE_D / 2.0
R_HEAD = R_CASE + P.BOLT_HEAD_K
R_TUI = P.TAKEUP_ID / 2.0
R_LO = P.LINER_OD / 2.0
R_NIF = NI.R_FWD                               # item 4 bore at its forward face

# fits (srm_params)
CLR_MIN = (P.CASE_ID + P.TOL_BORE[0]) - (P.PLUG_OD + P.TOL_LAND[1])
CLR_MAX = (P.CASE_ID + P.TOL_BORE[1]) - (P.PLUG_OD + P.TOL_LAND[0])
GLAND = (P.CASE_ID - P.ORING_GROOVE_D) / 2.0
SQ = 1.0 - GLAND / P.ORING_CS
TQ = P.BOLT_TORQUE_FWD_NM
f3 = lambda x: f"{x:.3f}"
f2 = lambda x: f"{x:.2f}"
f1 = lambda x: f"{x:.1f}"
NM = "N·m"
TQS = f"{f1(TQ[0])}-{f1(TQ[1])} {NM}"
ENGAGE = P.BOLT_L_FWD - P.CASE_WALL - P.PLUG_CLEAR
# seal zone (decision G1-rev): honed to the smallest diameter that cleans up, A (the
# smallest reading in the zone), CASE_ID <= A <= SEAL_A_MAX (92.000 ... 92.070), zone held
# to A +0.030/0, so it never passes CASE_BORE_MAX; item 6 is cut to the forward zone's A
A_LO, A_HI = P.CASE_ID, P.SEAL_A_MAX
A_RANGE = f"{f3(A_LO)} ≤ A ≤ {f3(A_HI)}"
LAND_OFF = P.CASE_ID - P.PLUG_OD               # land A - 0.06
GRV_OFF = P.CASE_ID - P.ORING_GROOVE_D         # groove bottoms A - 5.67
# clocking (decision G3): seen from forward, hole 0 is this far clockwise of puller P1
P1_TO_H0 = PTH[0] - TH[0]
PUL_TXT = (f"2 {TIMES} M6{TIMES}1-6H {DEPTH}{fmt(P.PULLER_DEPTH - P.DRILL_OVER)}, "
           f"{DIA}{fmt(P.PULLER_TAP_DRILL)} {DEPTH}{fmt(P.PULLER_DEPTH)}")
HEAD_SWEEP_D = 106.04                          # README / srm_verify envelope (ref)
THROAT_RETIRE = 23.9                           # README "After every firing"
CASE_LEN_TOL = 0.1                             # SRM100-101: case length +/-0.1
# after every firing (README, decision G8-rev), as sheet 2
REPLACE = ("items 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, all 36 screws (items 15, 16) and the "
           "temperature labels")
REUSE = ("items 1, 2 and 6 after inspection (SRM100-101 R10 for the case), and item 3 while its "
         f"throat is ≤ {DIA}{fmt(THROAT_RETIRE)} and it is uncracked")
# extraction collar (README extraction, decision G18) and the marking zone (SRM100-101
# note 8), both measured from the end face being extracted
COLLAR_MIN = 50.0
MARK_Z = (20.0, 45.0)
NB = chr(0xA0)                                 # no-break space: textwrap never splits it
# sheet 2 note numbers cited here (dwg_000_sh2_aft_end.NOTE_KEYS)
SH2_FIRST, SH2_PLUGS, SH2_CAP, SH2_READ = 2, 6, 11, 12
SH1_NOPORT = 11                                # sheet 1 note 11: no pressure port (asserted there)
MB = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())
M_LOADED_G = round(1000.0 * MB["loaded_kg"])   # title block: loaded motor, g

# ---- stack and gauging at loading (nominal) -------------------------------------------
T_F = P.PLUG_L + P.FWD_INSUL_T                 # t: plug + bonded item 7, measured on item 6
D_NI = Z_CF - Z_LA                             # depth: case fwd end face -> item 4 fwd face
CAV = Z_IA - Z_LA                              # cavity C = D_NI - t
D_LIN = Z_CF - Z_LF                            # depth to the liner's forward end
FLOAT_MIN = 0.30                               # README / srm_params self_check
D_S4 = Z_CF - Z_TU                             # depth to the top of S4
GAP = D_S4 - T_F                               # take-up gap g
LINER_TOL = ("0", "-0.10")                     # SRM100-110: L = C - 0.5 0/-0.1
T7_TOL = 0.2                                   # SRM100-107 sheet 3.0 +/-0.2
TF_TOL = 0.4                                   # SRM100-108 free 4.8 +/-0.4
assert abs(CAV - (D_NI - T_F)) < 1e-9 and abs(GAP - P.TAKEUP_T) < 1e-9
assert abs(P.LINER_L - (CAV - P.LINER_FLOAT)) < 1e-9
C_LO = 1.0 - (P.TAKEUP_T + P.TOL_STACK) / P.TAKEUP_FREE_T
C_HI = 1.0 - (P.TAKEUP_T - P.TOL_STACK) / P.TAKEUP_FREE_T
# sheet choice: 25-50 % compression -> 0.50 <= g / t_free <= 0.75
BANDS = [(ts, 0.50 * ts, 0.75 * ts) for ts in (3.2, P.TAKEUP_FREE_T, 6.4)]
Z_IGN = P.grain_z(P.N_GRAINS - 1) + P.GRAIN_L / 2.0     # middle of G4
L_IGN = Z_IGN - S["z_exit"]
L_ALL = Z_FT - NC.Z_BACK                       # cap back face to thrust face

# tightening sequence (opposite pairs, then +90 deg): step k -> hole index (as sheet 2)
SEQ = [0, 9, 5, 14, 2, 11, 7, 16, 1, 10, 6, 15, 3, 12, 8, 17, 4, 13]
assert sorted(SEQ) == list(range(P.N_BOLTS))

# ---- section hatching (same classes as sheets 1 and 2, spacing for 1:1) ---------------
HATCH = {
    "case": Hatch(45, 2.0),
    "nozzle_holder": Hatch(135, 2.0),
    "nozzle_insert": Hatch(45, 1.5, cross=True, offset=0.5),
    "nozzle_insulator": Hatch(45, 1.0, offset=0.5),
    "fwd_closure": Hatch(135, 2.0),
    "fwd_insulator": Hatch(0, 1.0),
    "takeup_ring": Hatch(0, 0.8, cross=True),
    "liner": Hatch(135, 0.8),
    "casting_tube": Hatch(solid=True),
    "grain_spacer": Hatch(90, 0.6),
    "grain": Hatch(30, 3.0, cross=True),
}


def part(name, **kw):
    st, tr = PL[name]
    if name.startswith("oring"):
        return Part(st, tr, hatch=Hatch(solid=True), name=name)
    if name.startswith("bolt"):
        return Part(st, tr, cut=False, name=name, **kw)
    key = ("grain_spacer" if name.startswith("spacer") else
           "casting_tube" if name.startswith("casting_tube") else
           "grain" if name.startswith("grain") else name)
    return Part(st, tr, hatch=HATCH[key], name=name)


# ---- local primitives ------------------------------------------------------------------
def _split_path(pp, gaps):
    """Polyline pp (paper points) minus the arc-length intervals `gaps` -> pieces."""
    pieces, cur, s0 = [], [pp[0]], 0.0
    cuts = sorted(gaps)
    for a, b in zip(pp[:-1], pp[1:]):
        L = float(np.hypot(*(b - a)))
        d = (b - a) / L
        for g0, g1 in cuts:
            if s0 < g1 and g0 < s0 + L:
                t0, t1 = max(g0 - s0, 0.0), min(g1 - s0, L)
                if t0 > 0:
                    cur.append(a + d * t0)
                if len(cur) > 1:
                    pieces.append(cur)
                cur = [a + d * t1]
        cur.append(b)
        s0 += L
    if len(cur) > 1:
        pieces.append(cur)
    return pieces


def cut_path(view, pts, letter, look_dir, ext=4.0, gaps=()):
    """Stepped cutting-plane line (ISO 128-44): thin chain along the view polyline
    `pts`, thick strokes at both ends and at every change of direction, arrows along
    paper `look_dir` and the letter beyond each arrow.  `gaps`: arc-length intervals
    (paper mm from the extended start) where the chain is interrupted."""
    s = view.sheet
    pp = [view.pt(*p) for p in pts]
    d0 = D._unit(pp[1] - pp[0])
    d1 = D._unit(pp[-1] - pp[-2])
    pp[0] = pp[0] - d0 * ext
    pp[-1] = pp[-1] + d1 * ext
    for piece in _split_path(pp, gaps):
        s.line(piece, THIN, "center")
    L = D._unit(look_dir)
    for p, d in ((pp[0], d0), (pp[-1], -d1)):
        s.line([p, p + d * 5.0], 0.7)
        q = p + d * 1.0
        s.line([q, q + L * 7.0], THIN)
        s.arrow(q + L * 7.0, L)
        t = q + L * 9.8
        s.text(t[0], t[1] - 1.75, letter, 3.5, ha="center")
    for k in range(1, len(pp) - 1):
        a = D._unit(pp[k - 1] - pp[k])
        b = D._unit(pp[k + 1] - pp[k])
        s.line([pp[k] + a * 3.0, pp[k], pp[k] + b * 3.0], 0.7, cap="butt")


def seq_tag(sh, p, s, a=4.6):
    """Tightening-sequence number in a square (distinct from the round item balloons)."""
    x, y = p
    sh.line([(x - a / 2, y - a / 2), (x + a / 2, y - a / 2), (x + a / 2, y + a / 2),
             (x - a / 2, y + a / 2), (x - a / 2, y - a / 2)], THIN)
    sh.text(x, y - 1.25, s, 2.5, ha="center")


def view_arrow(sh, tip, direction, letter, shaft=9.0):
    """Reference arrow (ISO 128-30, reference-arrow method): thin shaft ending in a
    filled arrowhead at paper `tip`, pointing along `direction`; the view's letter
    stands on the shaft's upper side."""
    d = D._unit(direction)
    tail = np.asarray(tip, float) - d * shaft
    sh.line([tail, tip], THIN)
    sh.arrow(tip, d)
    m = (tail + np.asarray(tip, float)) / 2.0
    sh.text(m[0], m[1] + 1.4, letter, 3.5, ha="center")


def dim_across(va, a, vb, b, at_v, text, tol=None):
    """Linear (horizontal) dimension from view point a of window va to view point b of
    window vb of one interrupted view (ISO 129-1: the dimension line is not broken and
    carries the true length); the line sits at view v = at_v."""
    return va._linear(va.pt(*a), vb.pt(*b), (1, 0), (0, va.pt(0, at_v)[1]), text, tol)


def thread_34(sh, c, d):
    """ISO 6410-1 tapped hole seen end on: the thread root (major diameter d) as a thin
    arc of about 3/4 of the circle, open in the upper right quadrant."""
    sh.circle(c, d / 2.0, THIN, a0=100.0, a1=370.0)


def sym_mark(sh, p, axis_dir, L=5.0, gap=1.6):
    """ISO 128-30 symmetry mark: two short thin parallel lines across the symmetry line
    at paper point p (its end), `gap` apart along it."""
    d = D._unit(axis_dir)
    n = D._perp(d)
    for k in (-0.5, 0.5):
        c = np.asarray(p, float) + d * gap * k
        sh.line([c - n * L / 2, c + n * L / 2], THIN)


# =======================================================================================
sh = Sheet("SRM100-000", "MOTOR ASSEMBLY - FORWARD END",
           "Forward closure build-up, grain stack loading and stack-up, tightening",
           size="A2", material="See parts list, sheet 1", mass_g=M_LOADED_G, scale="1:1",
           sheet=(3, 3), doc_type="ASSEMBLY DRAWING", finish=None, edges="-")

# ---- main view: partial half-section E-E (1:1) ------------------------------------------
names = ["case", "liner", "spacer_4", "casting_tube_4", "grain_4", "takeup_ring",
         "fwd_insulator", "fwd_closure", "oring_fwd_outer", "oring_fwd_inner"]
parts = [part(n) for n in names]
parts.append(part("bolt_fwd_00", occlude=True))        # the one in the cutting plane
# screws 1-4 lie in the removed quadrant, 10-17 behind the case: only 5-9 are seen
parts += [part(f"bolt_fwd_{i:02d}", occlude=False) for i in range(5, 10)]

OX, OY = 190.0 - Z_CF, 318.0
WIN = (628.0, -57.0, 704.0, 57.0)
v = View(sh, parts, (OX, OY), 1.0, section="half", rot=ROT, window=WIN)
v.zigzag((WIN[0], WIN[1] + 2), (WIN[0], WIN[3] - 2))
# screw 0's axis, run up past the dimension line: it is the 13's extension line
v.centerline((Z_BF, R_BORE - 16.0), (Z_BF, 62.0), ext=2.0)
v.label("E-E (1:1)", where="below", gap=7.0)

# assembled reference dimensions, from the case forward end face (= flange bearing face)
v.dim_h((Z_CF, R_CASE), (Z_BF, R_HEAD), at=62.0, ext=(True, False))
v.dim_h((Z_CF, R_CASE), (Z_FT, R_CASE), at=62.0, ref=True, ext=(False, True))
v.leader((Z_CF, -R_CASE), 22.0, -18.0,
         ["FLANGE BUTTED ON THE CASE FORWARD END FACE:",
          "zero gap, a 0.05 feeler must not enter anywhere.",
          "Hole 0 lies in this plane (view F). Item 6 is",
          "a serialised pair with item 1; clocking: note 12."])
view_arrow(sh, v.pt(Z_FT + 1.5, 32.0), (-1, 0), "F")

# detail circles (drawn with the details below)
bal = [
    (9, (632.0, 43.8), (118.0, 392.0)),
    (8, (636.0, 0.5 * (P.LINER_ID / 2 + R_LO)), (130.0, 392.0)),
    (11, (Z_S4 + 1.5, 0.5 * (P.SPACER_ID / 2 + P.SPACER_OD / 2)), (142.0, 392.0)),
    (12, (Z_TU + 1.5, 42.0), (154.0, 392.0)),
    (13, (Z_GO, R_GRV + 1.4), (166.0, 392.0)),
    (10, (632.0, 30.0), (108.0, 348.0)),
    (7, (Z_IA + 1.5, 8.0), (108.0, 326.0)),
    (1, (640.0, -40.0), (108.0, 278.0)),
    (6, (Z_FT - 2.0, 27.0), (222.0, 341.0)),
    (16, (Z_BF + 1.0, 40.0), (222.0, 364.0)),            # on screw 0's shank
]
for n, tgt, at in bal:
    sh.balloon(v.pt(*tgt), n, at)

# ---- view F: the forward end, seen from forward (reference arrow on E-E) ----------------
f_parts = [part(n) for n in ("case", "fwd_closure")]
f_parts += [part(f"bolt_fwd_{i:02d}", occlude=False) for i in range(P.N_BOLTS)]
FX, FY = 345.0, 322.0
w = View(sh, f_parts, (FX, FY), 1.0, look="fwd", rot=ROT)
w.center_mark((0.0, 0.0), 14.0, ext=0.0)
w.label("F (1:1)", where="below", gap=13.0)


def f_uv(theta_deg, r):
    """Motor (theta, r), after the view rotation -> view F (u, v): u = x, v = y."""
    t = math.radians(theta_deg + ROT)
    return (r * math.cos(t), r * math.sin(t))


def f_ang(theta_deg):
    u, vv = f_uv(theta_deg, 1.0)
    return math.degrees(math.atan2(vv, u)) % 360.0


R_TAG = R_HEAD + 8.0
TAG_A = 4.6
for k, i in enumerate(SEQ, 1):
    seq_tag(sh, w.pt(*f_uv(TH[i], R_TAG)), str(k), TAG_A)
# E-E: the plane y = 0 through hole 0 (horizontal leg) and x = 0 bounding the removed
# quarter (vertical leg), turned outside the part so that its end arrow also points
# along the viewing direction.  The chain is broken round tag 1.
R_CP = R_HEAD + 15.0
EXT_CP = 4.0
cut_path(w, [(R_CP, 0.0), (0.0, 0.0), (0.0, R_HEAD + 18.0), (16.0, R_HEAD + 18.0)],
         "E", (0, -1), ext=EXT_CP,
         gaps=[(R_CP + EXT_CP - R_TAG - TAG_A / 2 - 0.6, R_CP + EXT_CP - R_TAG + TAG_A / 2 + 0.6)])
# keying: hole 0 is 0.8 deg off the 20 deg pitch; the chain line is hole 0's axis and
# serves as that extension line, the arcs sit beyond its end
R_ANG = 78.0
a1, a0, a17 = f_ang(TH[1]), f_ang(TH[0]), f_ang(TH[17])
w.dim_ang((0.0, 0.0), a0, a1, R_ANG, ext=False)
w.dim_ang((0.0, 0.0), a17, a0, R_ANG, ext=False)
for a, r0 in ((a1, R_TAG + 3.6), (a17, R_TAG + 3.6), (a0, R_CP + EXT_CP + 1.0)):
    dd = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
    sh.line([w.pt(0, 0) + dd * r0, w.pt(0, 0) + dd * (R_ANG + 2.0)], THIN)
# pullers: pitch circle, centre marks, thread roots
sh.circle(w.pt(0, 0), P.PULLER_R, THIN, "center")
for th in PTH:
    c = f_uv(th, P.PULLER_R)
    w.center_mark(c, P.PULLER_TAP_DRILL / 2.0, ext=1.5, angle=th + ROT)
    thread_34(sh, w.pt(*c), 6.0)
for lab, th in (("P1", PTH[0]), ("P2", PTH[1])):
    q = w.pt(*f_uv(th, P.PULLER_R - 8.0))
    sh.text(q[0], q[1] - 1.25, lab, D.H, ha="center")
# clocking check (G3): hole 0 (the E-E chain line) to P1's radial line
R_PK = 66.0
aP1 = f_ang(PTH[0])
dd = np.array([math.cos(math.radians(aP1)), math.sin(math.radians(aP1))])
sh.line([w.pt(0, 0) + dd * (P.PULLER_R + 3.5), w.pt(0, 0) + dd * (R_PK + 2.0)], THIN)
w.dim_ang((0.0, 0.0), a0, aP1, R_PK, ext=False)
q = w.pt(0, 0) + np.array([R_ANG + 3.5, 0.0])
sh.text(q[0], q[1] - 1.25, "HOLE 0", D.H)
cp = np.array(f_uv(PTH[1], P.PULLER_R)) + 3.0 * np.array([math.cos(math.radians(225)),
                                                           math.sin(math.radians(225))])
w.leader(tuple(cp), -20.0, -30.0,
         [f"PULLERS P1, P2: {PUL_TXT}",
          f"on r {fmt(P.PULLER_R)} at {chr(952)} {fmt(PTH[0], 0)}{DEG} and "
          f"{fmt(PTH[1], 0)}{DEG} (ref, SRM100-103).",
          f"From forward, hole 0 is {fmt(P1_TO_H0, 1)}{DEG} clockwise of P1"])
# thrust face (G25: flat from the axis to the flange edge): the dot sits on the face
# between the pitch circle and the edge, the leader leaves through the middle of the
# gap between the heads of holes 7 and 8 (view F is 1:1, unmirrored: view = paper offsets)
assert np.allclose(w.pt(1.0, 2.0) - w.pt(0.0, 0.0), (1.0, 2.0))
G_TF = np.array(f_uv(0.5 * (TH[7] + TH[8]), R_CASE))
D_TF = D._unit(np.array([-1.0, 1.0]))                  # outward, up-left, 45 deg
DOT_TF = G_TF - D_TF * 8.0
assert P.PULLER_R + 3.0 < float(np.hypot(*DOT_TF)) < R_CASE - 3.0, DOT_TF
w.leader(tuple(DOT_TF), *(D_TF * 36.0),
         ["THRUST FACE, flat to the axis", "(static-test load cell)"], end="dot")
# screws: callout under the view, from screw 15's head
w.leader(f_uv(TH[15], R_HEAD), 4.0, -38.0,
         [f"18 {TIMES} item 16, M6{TIMES}16-010.9",
          f"(ISO 7380-1), {TQS}, Loctite 243.",
          "Order: the boxed numbers, 3 passes",
          f"(note 13). Holes in item 1: {DIA}{f2(P.CASE_HOLE_D)}",
          f"+0.03/0; {fmt(ENGAGE, 0)} engaged in item 6 (ref)"])

# ---- detail G: forward case seal gland (5:1) ----------------------------------------------
GX, GY = 125.0, 180.0
g = v.detail((0.5 * (Z_GO + Z_GI), R_BORE), 8.2, 5.0, (GX, GY), "G", circle_label_ang=100)
# kit fmt() drops trailing zeros: the measured width is formatted here to 2 places
g.dim_h((Z_GO - GW, R_LAND), (Z_GO + GW, R_LAND), at=R_BORE + 8.8, tol=("+0.08", "0"),
        text="2" + TIMES + " " + f2(abs((Z_GO + GW) - (Z_GO - GW))))
g.leader((Z_GI - GW - 0.8, R_BORE), -5.0, 30.0,
         [f"BORE, item 1: {DIA}A +{f3(P.TOL_BORE[1])}/0,",
          "honed Ra 0.4 (0.8 max),",
          "circumferential lay;",
          f"{A_RANGE},",
          "recorded per zone (SRM100-101).",
          f"Drawn at A = {f3(A_LO)}."])
g.leader((Z_GO + GW + 0.8, R_LAND), 20.0, -12.0,
         [f"LAND, item 6: {DIA}A - {f2(LAND_OFF)} 0/{f2(P.TOL_LAND[0])}",
          f"({DIA}{f2(P.PLUG_OD)} at A = {f3(A_LO)})",
          f"clearance on {DIA} {f2(CLR_MIN)}-{f2(CLR_MAX)}",
          f"({f3(CLR_MIN / 2)}-{f3(CLR_MAX / 2)} radial)"])
g.leader((Z_GO - GW + 0.5, R_GRV), 30.0, -36.0,
         [f"2 GROOVES {DIA}A - {f2(GRV_OFF)} 0/{f2(P.TOL_GROOVE[0])}",
          f"({DIA}{f2(P.ORING_GROOVE_D)} at A = {f3(A_LO)})",
          f"gland depth {f3(GLAND)} (ref)"])
oc = P.ORING_COMPOUND.split(" or ")
g.leader((Z_GI - 1.0, R_GRV + 1.0), -14.0, -30.0,
         [f"2 {TIMES} item 13, {P.ORING_DASH}",
          oc[0],
          f"or {oc[1]}, squeeze {100 * SQ:.1f} %",
          "lube: note 4"])

# ---- detail H: take-up ring, liner float, EPDM insulator (5:1) ---------------------------
HX, HY = 330.0, 185.0
hd = v.detail((649.2, 44.0), 6.6, 5.0, (HX, HY), "H", circle_label_ang=100)
hd.dim_h((Z_TU, R_TUI), (Z_IA, 38.6), at=38.6, ext=(True, False))
hd.leader((Z_LF, 45.05), -30.0, 38.0,
          ["LINER END, item 8: floats", f"{f2(P.LINER_FLOAT)} short of item 7",
           f"({f2(FLOAT_MIN)} min, note 8)"])
hd.leader((Z_IA + 1.5, 41.0), 30.0, -22.0,
          [f"item 7, EPDM {f1(P.FWD_INSUL_T)} {PM}{f1(T7_TOL)}, RTV-bonded",
           "to item 6 (note 3); the 0.1-0.2 bondline",
           "is not in the model"], end="dot")
hd.leader((Z_TU + 1.5, 42.5), -30.0, -24.0,
          [f"item 12, {f2(P.TAKEUP_FREE_T)} free, {f2(P.TAKEUP_T)} installed "
           f"({100 * (1.0 - P.TAKEUP_T / P.TAKEUP_FREE_T):.1f} %);",
           f"{100 * C_LO:.1f}-{100 * C_HI:.1f} % over the {PM}{f2(P.TOL_STACK)} stack (note 9)"],
          end="dot")
hd.leader((Z_S4 + 1.5, 43.6), -24.0, 12.0,
          [f"S4, item 11, {f2(P.SPACER_T)} {PM}{f2(P.TOL_SPACER_T)}"], end="dot")

# ---- grain stack: interrupted view of section E-E (1:1) ----------------------------------
st_names = (["case", "nozzle_holder", "nozzle_insert", "nozzle_insulator", "liner"]
            + [f"spacer_{i}" for i in range(P.N_SPACERS)]
            + [f"grain_{i + 1}" for i in range(P.N_GRAINS)]
            + [f"casting_tube_{i + 1}" for i in range(P.N_GRAINS)]
            + ["takeup_ring", "fwd_insulator", "fwd_closure"])
st_parts = [part(n) for n in st_names]
SW = ([(36.0, 55.0)]
      + [(P.spacer_z(i) - 8.0, P.spacer_z(i) + P.SPACER_T + 8.0) for i in range(1, P.N_SPACERS - 1)]
      + [(Z_S4 - 7.0, Z_PF + 5.0)])
SGAP, SX0, SY0, SV1 = 9.0, 40.0, 40.0, 52.0
sv, xc = [], SX0
for u0, u1 in SW:
    sv.append(View(sh, st_parts, (xc - u0, SY0), 1.0, section="half", rot=ROT,
                   window=(u0, 0.0, u1, SV1), axis=False))
    xc += (u1 - u0) + SGAP
# break lines where a window cuts material; the axis is the symmetry line of the
# half view, one chain line through all the windows, marked at its two ends
for k, (vw, (u0, u1)) in enumerate(zip(sv, SW)):
    vw.zigzag((u0, 23.0 if k == 0 else 15.0), (u0, SV1 - 1.0))
    vw.zigzag((u1, 2.5 if k == len(SW) - 1 else 15.0), (u1, SV1 - 1.0))
AX0, AX1 = sv[0].pt(SW[0][0], 0.0), sv[-1].pt(SW[-1][1], 0.0)
sh.line([AX0 - (6.0, 0.0), AX1 + (6.0, 0.0)], THIN, "center")
sym_mark(sh, AX0 - (4.0, 0.0), (1, 0))
sym_mark(sh, AX1 + (4.0, 0.0), (1, 0))
# positions: spacers above the windows, grains in the gaps
for i in range(P.N_SPACERS):
    k = 0 if i == 0 else (len(SW) - 1 if i == P.N_SPACERS - 1 else i)
    p = sv[k].pt(P.spacer_z(i) + P.SPACER_T / 2, SV1 + 3.0)
    sh.text(p[0], p[1], f"S{i}", D.H, ha="center")
for k in range(len(SW) - 1):
    xa = sv[k].pt(SW[k][1], 0)[0]
    sh.text(xa + SGAP / 2, SY0 + 30.0, f"G{k + 1}", D.H, ha="center")
# true lengths across the breaks
# the windows break the paper distance: the true lengths are the model stations'
assert abs((Z_TU - Z_LA) - P.STACK_L) < 1e-9
dim_across(sv[0], (Z_LA, R_NIF), sv[-1], (Z_TU, R_TUI), -6.0, f2(Z_TU - Z_LA),
           PM + f2(P.TOL_STACK))
# cavity: to item 7's aft face, a full disc, taken where it meets the axis
dim_across(sv[0], (Z_LA, R_NIF), sv[-1], (Z_IA, 0.0), -13.0, f"({f2(Z_IA - Z_LA)})")
xm = 0.5 * (SX0 + xc - SGAP)
sh.text(xm, SY0 - 26.0, "E-E (1:1), GRAIN STACK - INTERRUPTED VIEW", 3.5, ha="center")
for n, tgt, at in [(2, (37.0, 40.0), (28.0, 84.0)), (4, (40.5, 34.0), (28.0, 72.0)),
                   (3, (37.0, 28.0), (28.0, 60.0))]:
    sh.balloon(sv[0].pt(*tgt), n, at)

# ---- stack-up table ---------------------------------------------------------------------
rows = [["POS", "ELEMENT", "ITEM", "LENGTH", "TOL", "z AFT", "z FWD"]]
for i in range(P.N_SPACERS):
    z = P.spacer_z(i)
    rows.append([f"S{i}", f"Spacer {i}" + (" (on item 4)" if i == 0 else ""), "11",
                 f2(P.SPACER_T), PM + f2(P.TOL_SPACER_T), f2(z), f2(z + P.SPACER_T)])
    if i < P.N_GRAINS:
        z = P.grain_z(i)
        rows.append([f"G{i + 1}", f"Grain {i + 1} in its casting tube", "10, 9",
                     f2(P.GRAIN_L), PM + f2(P.TOL_GRAIN_L), f2(z), f2(z + P.GRAIN_L)])
rows += [
    ["STACK", f"{P.N_SPACERS} spacers + {P.N_GRAINS} grains (worst case)", "-", f2(P.STACK_L),
     PM + f2(P.TOL_STACK), f2(Z_LA), f2(Z_TU)],
    ["T", f"Take-up ring, installed ({f2(P.TAKEUP_FREE_T)} free)", "12", f2(P.TAKEUP_T),
     "= g", f2(Z_TU), f2(Z_IA)],
    ["C", "Cavity = stack + take-up", "-", f"({f2(CAV)})", "meas.", f2(Z_LA), f2(Z_IA)],
    ["L", f"Liner, cut to C - {f2(P.LINER_FLOAT)}", "8", f2(P.LINER_L), "0/-0.10",
     f2(Z_LA), f2(Z_LF)],
    ["-", "Liner float to item 7", "-", f2(P.LINER_FLOAT), f"{f2(FLOAT_MIN)} min", f2(Z_LF),
     f2(Z_IA)],
    ["I", "Forward insulator, EPDM, bonded", "7", f2(P.FWD_INSUL_T), PM + f2(T7_TOL), f2(Z_IA),
     f2(Z_PF)],
    ["P", "Forward closure, plug", "6", f2(P.PLUG_L), "gen.", f2(Z_PF), f2(Z_CF)],
    ["F", "Forward closure, flange", "6", f2(P.FLANGE_T), "gen.", f2(Z_CF), f2(Z_FT)],
    ["-", "Case (aft end face z 0)", "1", f2(P.CASE_L), PM + f2(CASE_LEN_TOL), f2(0.0), f2(Z_CF)],
]
TX, TY = 214.0, 118.0
sh.text(TX, TY + 3.0, "GRAIN STACK AXIAL STACK-UP (nominal; z from the case aft end face)", 2.5,
        bold=True)
yt = sh.table(TX, TY, [14.0, 61.0, 11.0, 17.0, 17.0, 17.0, 17.0], rows, row_h=4.6,
              align=["l", "l", "c", "r", "c", "r", "r"])
sh.text(TX, yt - 4.0, f"Stations (ref): O-ring grooves {f2(Z_GI)} / {f2(Z_GO)}, bolt row "
        f"{f2(Z_BF)}, thrust face {f2(Z_FT)}.", D.H)
sh.text(TX, yt - 8.0, f"Motor overall {f2(L_ALL)} (cap back face z {f2(NC.Z_BACK)} to the "
        f"thrust face). Igniter tip station z {f1(Z_IGN)} (note 15).", D.H)
sh.text(TX, yt - 12.0, "TOL gen. = ISO 2768-mK (SRM100-103), case per SRM100-101; the build "
        "uses the measured t, d_N and d_S.", D.H)

# ---- notes: loading and forward end closing -----------------------------------------------
NX = 442.0
bands = ", ".join(f"{fmt(ts, 1)} for g {f2(lo)}-{f2(hi)}" for ts, lo, hi in BANDS)
notes = [
    "Item numbers and materials: parts list, sheet 1. Tooling (casting mandrel, hole plugs, "
    "clamp collar, puller bridge) is not in this drawing set.",
    f"Aft end first (sheet 2); first build and proof: sheet 2, note {SH2_FIRST}. Bond item 7 "
    "to item 6 "
    "only after the proof (run with no insulators or liner).",
    "Bond item 7 to item 6's inboard face (README assembly step 1, SRM100-107): abrade, IPA "
    "wipe, silicone primer SS4004P, RTV106 or equal over the whole face, bondline 0.1-0.2, "
    "OD centred on the land within 0.1; cure 24 h. Then measure t, "
    "flange bearing face to item 7's aft face, at 4 points, mean (nominal "
    f"{f2(T_F)} + bondline).",
    f"Lube (O-rings, liner OD, insulator edges): {P.LUBE}. Parts replaced per note 17 "
    "(labels included) are always new.",
    "Grains are cast in their casting tubes (item 9) on the casting mandrel; the tube stays "
    f"on the grain. Mandrel out, measure and record every grain length ({f2(P.GRAIN_L)} "
    f"{PM}{f2(P.TOL_GRAIN_L)}) and spacer ({f2(P.SPACER_T)} {PM}{f2(P.TOL_SPACER_T)}): "
    "stack-up table.",
    "Cavity and liner: with the aft end closed, measure the depth d_N from the case forward "
    f"end face to item 4's forward face (nominal {f2(D_NI)}). Cavity C = d_N - t (nominal "
    f"{f2(CAV)}). Cut item 8 to C - {f2(P.LINER_FLOAT)} 0/-0.10 (SRM100-110), lubricate its "
    "OD (note 4) and slide it in by hand until it bears on item 4.",
    "Load by hand, aft to forward: S0 on item 4, G1, S1, G2, S2, G3, S3, G4, S4 (stack view "
    "E-E). Each tube and spacer must slide freely in the liner.",
    "Liner float, in place of the README feeler check (the gap is closed off once item 6 is "
    "in): depth d_L from the case forward end face to the liner's forward end ≥ t + "
    f"{f2(FLOAT_MIN)} at 4 points (nominal {f2(D_LIN)} for t = {f2(T_F)}).",
    "Take-up gap: depth d_S from the case forward end face to the top of S4 at 4 points, "
    f"mean; g = d_S - t (nominal {f2(D_S4)} - {f2(T_F)} = {f2(GAP)}; {PM}{f2(P.TOL_STACK)} "
    f"stack, {PM}{f2(CASE_LEN_TOL)} case length). Measure the free thickness t_s of item 12 "
    "(4 points, mean) and accept 0.50 ≤ g / t_s ≤ 0.75 (25-50 % compression; nominal "
    f"{100 * (1.0 - P.TAKEUP_T / P.TAKEUP_FREE_T):.1f} %; SRM100-108): sheet {bands}. "
    "Lay item 12 on S4.",
    "Hole plugs: push 18 acetal plugs into the case's forward-end holes before item 6 goes "
    f"in (as sheet 2, note {SH2_PLUGS}).",
    f"Fit 2 {TIMES} item 13, {P.ORING_COMPOUND}, in the grooves of item 6 (detail G). Item 6 "
    f"is cut to the forward-zone bore A recorded on SRM100-101 ({A_RANGE}): land "
    f"A{NB}-{NB}{f2(LAND_OFF)} 0/{f2(P.TOL_LAND[0])}, groove bottoms A{NB}-{NB}{f2(GRV_OFF)} "
    f"0/{f2(P.TOL_GROOVE[0])}. Detail G is drawn at A = {f3(A_LO)}.",
    "Clocking (view F): enter item 6 with hole 0 on the case's hole 0, the scribed clocking "
    "line straight across case end and flange, the FWD markings of items 1 and 6 "
    "(SRM100-101 note 8, SRM100-103 note 11) side by side. Check: seen from forward, hole 0 "
    f"is {fmt(P1_TO_H0, 1)}{DEG} clockwise of puller "
    f"P1 ({chr(952)} {fmt(PTH[0], 0)}{DEG}). Serialised pair: never fit another closure. Push "
    "in by hand until the flange butts on the case end face (zero gap).",
    f"Pull each plug as its screw goes in. Screws 18 {TIMES} item 16 with Loctite 243, in the "
    "boxed order of view F (opposite pairs, criss-cross): pass 1 to about "
    f"{f1(TQ[0] / 2)} {NM}, pass 2 to {TQS}, pass 3 at final torque hole by hole round "
    f"the circle, as a check. Never an M6{TIMES}10 (item 15) here: 1 d engagement only.",
    f"No pressure port (sheet 1 note {SH1_NOPORT}): item 6 is solid (no port, no pocket) and "
    "item 7 is a "
    "full disc; nothing is fitted or plugged at the forward end.",
    f"Igniter last, at the stand; cap per sheet 2 note {SH2_CAP}. It goes up the throat "
    f"about {L_IGN:.0f}{NB}mm from the nozzle exit, to the middle of G4's core "
    f"(z{NB}{f1(Z_IGN)}).",
    f"Extraction, labels read first (sheet 2 note {SH2_READ}), never lever or knock: screws "
    "out; split clamp collar (100.0 bore) on the case OD at least "
    f"{fmt(COLLAR_MIN, 0)}{NB}mm from the forward end face, clear of the screw heads at "
    f"{fmt(Z_CF - Z_BF)} (sweep {DIA}{fmt(HEAD_SWEEP_D)} ref) and the marking at "
    f"{fmt(MARK_Z[0], 0)}-{fmt(MARK_Z[1], 0)} from that face; puller bridge, 2 {TIMES} M6 "
    "draw screws in item 6's P1, P2 (view F), or react on the stand's thrust plate.",
    f"After every firing: replace {REPLACE}. Re-use {REUSE}. Scrape item 7 and the old RTV "
    "off item 6 with a plastic scraper (SRM100-103); re-gauge every bolt hole against its "
    "baseline (SRM100-101 R10).",
]
# numbers cited elsewhere must not move: 8 (SRM100-110), 14 (no port), 17 (after firing)
assert (notes[7].startswith("Liner float"), notes[13].startswith("No pressure port"),
        notes[16].startswith("After every firing")) == (True, True, True)
yb = sh.notes(NX, 402.0, notes, 138.0, title="LOADING AND FORWARD END CLOSING")

# ---- gauging record at loading (nominal values from the model) ----------------------------
grows = [["QUANTITY (notes 3-9, 12, 13)", "NOMINAL", "ACCEPT", "MEASURED"],
         ["t: item 6 flange face to item 7, 4 pts", f2(T_F), "+ bondline", ""],
         ["d_N: case end face to item 4, 4 pts", f2(D_NI), "record", ""],
         ["C = d_N - t: cavity", f2(CAV), "record", ""],
         ["L: liner cut length", f2(P.LINER_L), f"C - {f2(P.LINER_FLOAT)} 0/-0.10", ""],
         ["Stack: measured spacers + grains", f2(Z_TU - Z_LA), PM + f2(P.TOL_STACK), ""],
         ["d_L: case end face to liner end, 4 pts", f2(D_LIN), f"≥ t + {f2(FLOAT_MIN)}", ""],
         ["d_S: case end face to S4 top, 4 pts", f2(D_S4), "record", ""],
         ["g = d_S - t: take-up gap", f2(GAP), "record", ""],
         ["t_s: item 12 free thickness, 4 pts", f2(P.TAKEUP_FREE_T), "sheet per g", ""],
         ["g / t_s", f3(GAP / P.TAKEUP_FREE_T), "0.50-0.75", ""],
         ["Flange gap to the case end face", "0", "0.05 feeler: no entry", ""],
         ["Screw torque, final pass", TQS, "3 passes", ""]]
sh.text(NX, yb - 4.0, "GAUGING RECORD AT LOADING (one per firing, file with the motor log)",
        2.5, bold=True)
yg = sh.table(NX, yb - 6.0, [63.0, 21.0, 35.0, 19.0], grows, row_h=4.6,
              align=["l", "r", "c", "c"])
sh.text(NX, yg - 4.5, "USED ON: SRM-100 motor (Helios) - static test and flight", D.H)

if __name__ == "__main__":
    sh.lint()
    sh.save("fwd_end")
