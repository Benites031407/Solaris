"""SRM100-000 sheet 2 of 3: MOTOR ASSEMBLY - AFT END (installation sheet, A2).

Main view: partial half-section A-A at 1:1 (window + ISO 128 zig-zag break) of the
aft closure build-up in the case's aft end, with the aft end of the grain stack.
Every srm_assembly.placements() row is turned rot = -0.8 so that screw / hole 0
(theta 0.8 deg) lies in the cutting plane.  Section B-B across the bolt row
(tightening sequence, keying), details C (case seal gland) and D (insert O-ring
gland) at 5:1, view J (1:2, the aft end seen from aft at entry: clocking of hole 0
against puller P1), the assembled reference stations, and the numbered build-up /
installation sequence taken from the README.

View frame: u = motor z (0 at the case's aft end face, + forward), v = radius.
Item numbers are those of the parts list on sheet 1.

Local primitives (not in srm_dwg): cut_path (a stepped cutting-plane line with a
thick corner), seq_tag (boxed tightening-sequence number), view_arrow (ISO 128
reference arrow with its letter, as sheet 3), thread_34 (ISO 6410 thin 3/4 arc on a
tapped hole seen end on, as sheet 3), text_block (unnumbered pre-wrapped lines
under a bold title).
"""

import json
import math

import numpy as np

import srm_dwg as D
import srm_params as P
import srm_assembly as A
import nozzle_holder as NH
import nozzle_cap as NC
from srm_dwg import DEPTH, DIA, DEG, TIMES, THIN, Hatch, Part, Sheet, View, fmt

PL = {n: (st, tr) for g, n, st, tr in A.placements()}
MB = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())
M_LOADED_G = round(1000.0 * MB["loaded_kg"])        # title block: loaded motor, g
S = P.nozzle_stations()
TH = P.bolt_thetas()
PTH = P.puller_thetas()                        # P1, P2 (theta 10, 190)
ROT = -TH[0]                                   # hole 0 into the cutting plane
P1_TO_H0 = PTH[0] - TH[0]                      # 9.2 deg: hole 0 from puller P1

# ---- model stations (motor frame) ----------------------------------------------------
Z_EXIT = S["z_exit"]                           # nozzle exit plane = graphite aft face
Z_HAFT = NH.Z_AFT                              # holder aft face
Z_CAPB = NC.Z_BACK                             # cap flange back face = motor aft end
Z_FACE = P.Z_HOLDER_FACE                       # holder / insert forward faces
Z_FL = -P.FLANGE_T                             # holder flange aft face
Z_B = P.bolt_z_aft()                           # bolt row
Z_G1, Z_G2 = P.Z_CASE_AFT + P.GROOVE_1_Z, P.Z_CASE_AFT + P.GROOVE_2_Z
Z_IG = P.INSERT_GROOVE_Z
GW = P.GROOVE_W / 2.0
R_CASE = P.CASE_OD / 2.0
R_BORE = P.CASE_ID / 2.0
R_LAND = P.PLUG_OD / 2.0
R_GRV = P.ORING_GROOVE_D / 2.0
R_IB = P.INSERT_BORE_D / 2.0
R_IOD = P.INSERT_OD / 2.0
R_IGRV = P.INSERT_GROOVE_D / 2.0
R_BODY = NH.R_BODY
R_CAPF = P.CAP_FLANGE_OD / 2.0
R_HEAD = R_CASE + P.BOLT_HEAD_K

# fits (srm_params)
CLR_MIN = (P.CASE_ID + P.TOL_BORE[0]) - (P.PLUG_OD + P.TOL_LAND[1])
CLR_MAX = (P.CASE_ID + P.TOL_BORE[1]) - (P.PLUG_OD + P.TOL_LAND[0])
ICLR_MIN = (P.INSERT_BORE_D + P.TOL_INSERT_BORE[0]) - (P.INSERT_OD + P.TOL_INSERT_OD[1])
ICLR_MAX = (P.INSERT_BORE_D + P.TOL_INSERT_BORE[1]) - (P.INSERT_OD + P.TOL_INSERT_OD[0])
GLAND = (P.CASE_ID - P.ORING_GROOVE_D) / 2.0
IGLAND = (P.INSERT_GROOVE_D - P.INSERT_OD) / 2.0
SQ = 1.0 - GLAND / P.ORING_CS
ISQ = 1.0 - IGLAND / P.INSERT_ORING_CS
SEAT = Z_FACE - Z_EXIT                         # holder seat depth = insert length, nominal
SEAT_TOL = (0.0, 0.05)                         # seat depth +0.05/0 (SRM100-102)
INS_TOL = (-0.05, 0.0)                         # insert length 0/-0.05 (SRM100-104)
FLUSH_MAX = SEAT_TOL[1] - INS_TOL[0]           # insert fwd face below the holder face, max
TQ = P.BOLT_TORQUE_AFT_NM
f3 = lambda x: f"{x:.3f}"
f2 = lambda x: f"{x:.2f}"
f1 = lambda x: f"{x:.1f}"
NM = "N·m"
TQS = f"{f1(TQ[0])}-{f1(TQ[1])} {NM}"
# seal zones (SRM100-101, README, decision G1-rev): each zone honed to the smallest
# diameter that cleans up, A (the smallest reading in the zone), held to A +0.030/0 and
# recorded per zone; CASE_ID <= A <= SEAL_A_MAX (92.000 ... 92.070), so no zone passes
# CASE_BORE_MAX.  The plug is cut to its zone's A.  The details are drawn at A = CASE_ID.
A_LO, A_HI = P.CASE_ID, P.SEAL_A_MAX
A_RANGE = f"{f3(A_LO)} ≤ A ≤ {f3(A_HI)}"
BORE_TOL = f"+{f3(P.TOL_BORE[1])}/0"           # zone A +0.030/0
LAND_OFF = P.CASE_ID - P.PLUG_OD               # land = A - 0.06 0/-0.02
GRV_OFF = P.CASE_ID - P.ORING_GROOVE_D         # groove bottoms = A - 5.67 0/-0.04
LAND_TOL = f"0/{f2(P.TOL_LAND[0])}"
GRV_TOL = f"0/{f2(P.TOL_GROOVE[0])}"
ORING_TXT = P.ORING_COMPOUND                   # FKM 90A (Parker V0709-90 or equal)
# holder puller threads P1 / P2 (SRM100-102): full thread = drill depth - DRILL_OVER
PUL_TXT = (f"2 {TIMES} M6{TIMES}1-6H {DEPTH}{fmt(P.HOLDER_PULLER_DEPTH - P.DRILL_OVER)}, "
           f"{DIA}{fmt(P.PULLER_TAP_DRILL)} {DEPTH}{fmt(P.HOLDER_PULLER_DEPTH)}")
# after every firing (README, decision G8-rev): replaced / re-used after inspection
THROAT_RETIRE = 23.9                           # README: re-use item 3 while throat <= 23.9
HEAD_SWEEP_D = 106.04                          # README / srm_verify envelope over the heads (ref)
REPLACE = ("items 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, all 36 screws (items 15, 16) and the "
           "temperature labels")
REUSE = ("items 1, 2 and 6 after inspection (SRM100-101 R10 for the case), and item 3 while its "
         f"throat is ≤ {DIA}{fmt(THROAT_RETIRE)} and it is uncracked")
# temperature labels (README static-fire procedure, decision G17): fitted new every firing
LABEL_T = (177, 204, 232, 260)                 # degC, irreversible strips
LABEL_Z = (20.0, 35.0)                         # on item 1's OD, z from the aft end face
LABEL_TH = (90.0, 270.0)                       # on item 1 and on item 2's aft body
LABEL_LIMIT = 232                              # >= this: retire or re-proof that end
# extraction collar (README extraction, decision G18) and the marking zone (SRM100-101 note 8)
COLLAR_MIN = 50.0                              # collar at least this far from the end face
MARK_Z = (20.0, 45.0)


# note numbers by key, so that the references in the views cannot drift
NOTE_KEYS = ["tooling", "first", "new", "orings", "insert", "plugs", "clock", "screws",
             "fwd", "labels", "cap", "read", "extract", "after"]


def note(k):
    return str(NOTE_KEYS.index(k) + 1)


# tightening sequence (opposite pairs, then +90 deg): step k -> hole index
SEQ = [0, 9, 5, 14, 2, 11, 7, 16, 1, 10, 6, 15, 3, 12, 8, 17, 4, 13]
assert sorted(SEQ) == list(range(P.N_BOLTS))

# ---- section hatching (same classes as sheet 1, spacing for 1:1) ----------------------
HATCH = {
    "case": Hatch(45, 2.0),
    "nozzle_holder": Hatch(135, 2.0),
    "nozzle_insert": Hatch(45, 1.5, cross=True, offset=0.5),
    "nozzle_insulator": Hatch(45, 1.0, offset=0.5),
    "nozzle_cap": Hatch(solid=True),
    "liner": Hatch(135, 0.8),
    "casting_tube_1": Hatch(solid=True),
    "spacer_0": Hatch(90, 0.6),
    "grain_1": Hatch(30, 3.0, cross=True),
}


def part(name, **kw):
    st, tr = PL[name]
    if name.startswith("oring"):
        return Part(st, tr, hatch=Hatch(solid=True), name=name)
    if name.startswith("bolt"):
        return Part(st, tr, cut=False, name=name, **kw)
    return Part(st, tr, hatch=HATCH[name], name=name)


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
    (paper mm from the extended start) where the chain is interrupted, e.g. round a
    tag it would cross."""
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


def thread_34(sh, c, d):
    """ISO 6410-1 tapped hole seen end on: the thread root (major diameter d, paper mm)
    as a thin arc of about 3/4 of the circle, open in the upper right quadrant."""
    sh.circle(c, d / 2.0, THIN, a0=100.0, a1=370.0)


def text_block(sh, x, y_top, title, lines, h=D.H, gap=1.55):
    """Bold title, then pre-wrapped unnumbered lines; returns the y below the block."""
    y = y_top
    if title:
        sh.text(x, y - 3.5, title, 3.5, bold=True)
        y -= 3.5 + h * 1.9
    for s in lines:
        sh.text(x, y, s, h)
        y -= h * gap
    return y


# =======================================================================================
sh = Sheet("SRM100-000", "MOTOR ASSEMBLY - AFT END",
           "Aft closure build-up and installation, seal glands, tightening sequence",
           size="A2", material="See parts list, sheet 1", mass_g=M_LOADED_G, scale="1:1",
           sheet=(2, 3), doc_type="ASSEMBLY DRAWING", finish=None, edges="-")

# ---- main view: partial half-section A-A (1:1) ------------------------------------------
names = ["case", "nozzle_holder", "nozzle_insert", "oring_insert", "oring_aft_outer",
         "oring_aft_inner", "nozzle_insulator", "nozzle_cap", "liner", "spacer_0",
         "casting_tube_1", "grain_1"]
parts = [part(n) for n in names]
parts.append(part("bolt_aft_00", occlude=True))        # the one in the cutting plane
# screws 1-4 lie in the removed quadrant, 10-17 behind the case: only 5-9 are seen
parts += [part(f"bolt_aft_{i:02d}", occlude=False) for i in range(5, 10)]

OX, OY = 172.0, 302.0
WIN = (-58.0, -57.0, 80.0, 57.0)
v = View(sh, parts, (OX, OY), 1.0, section="half", rot=ROT, window=WIN)
v.zigzag((WIN[2], WIN[1] + 2), (WIN[2], WIN[3] - 2))
v.centerline((Z_B, R_BORE - 7.5), (Z_B, R_HEAD + 1.0), ext=2.0)      # screw 0 axis
v.label("A-A (1:1)", where="below", gap=18.0)
# the B-B plane is the bolt row: its chain line also serves as the extension line of
# the 13 below, so it runs up past that dimension line
v.cut_line((Z_B, -54.0), (Z_B, 66.0), "B", (1, 0))

# assembled reference dimensions, from the case aft end face (= flange bearing face)
v.dim_h((0.0, R_CASE), (Z_B, R_HEAD), at=62.0, ext=(True, False))
v.dim_h((Z_HAFT, -R_BODY), (0.0, -R_CASE), at=-64.0, ref=True)
v.dim_h((Z_CAPB, -R_CAPF), (0.0, -R_CASE), at=-72.0, ref=True)
v.leader((Z_EXIT, 0.5 * (S["r_exit"] + 1.0 + R_IOD)), -14.0, -30.0,
         ["NOZZLE EXIT PLANE (ref),", "graphite aft face on the lip:",
          f"{f2(-Z_EXIT)} aft of the case aft end face"])
v.leader((0.0, R_CASE), -30.0, 30.0,
         ["FLANGE BUTTED ON THE CASE END FACE: zero gap,",
          "a 0.05 feeler must not enter anywhere round.",
          "Hole 0 lies in this plane (B-B); clocking of",
          "item 2 to item 1: view J and note " + note("clock") + "."])
# reference arrow for view J (the aft end seen from aft, at entry)
view_arrow(sh, v.pt(Z_CAPB - 1.5, -20.0), (1, 0), "J")

# balloons (item numbers as sheet 1)
bal = [
    (15, (Z_B + 3.8, R_CASE + 1.6), (206.0, 386.0)),
    (13, (Z_G2, R_GRV + 1.4), (220.0, 386.0)),
    (3, (22.0, 24.0), (234.0, 386.0)),
    (4, (40.5, 32.0), (248.0, 386.0)),
    (11, (44.5, 43.6), (270.0, 378.0)),
    (8, (72.0, 45.05), (270.0, 366.0)),
    (9, (68.0, 43.8), (270.0, 354.0)),
    (10, (60.0, 30.0), (270.0, 342.0)),
    (1, (60.0, -40.0), (270.0, 258.0)),
    (2, (-3.0, 42.0), (100.0, 352.0)),
    (14, (Z_IG, R_IGRV - 1.2), (100.0, 340.0)),
    (5, (Z_CAPB + 0.75, R_CAPF - 2.5), (100.0, 328.0)),
]
for n, tgt, at in bal:
    sh.balloon(v.pt(*tgt), n, at)

# ---- section B-B: the bolt row, seen from aft ------------------------------------------
bb_parts = [part(n) for n in ("case", "nozzle_holder", "nozzle_insert")]
bb_parts += [part(f"bolt_aft_{i:02d}", occlude=True) for i in range(P.N_BOLTS)]
BX, BY = 366.0, 306.0
w = View(sh, bb_parts, (BX, BY), 1.0, look="aft", z_cut=Z_B, keep="above", rot=ROT)
w.center_mark((0.0, 0.0), 14.0, ext=0.0)
w.label("B-B (1:1)", where="below", gap=13.0)


def bb_uv(theta_deg, r):
    """Motor (theta, r), after the view rotation -> B-B view (u, v): u = -x, v = y."""
    t = math.radians(theta_deg + ROT)
    return (-r * math.cos(t), r * math.sin(t))


def bb_ang(theta_deg):
    u, vv = bb_uv(theta_deg, 1.0)
    return math.degrees(math.atan2(vv, u)) % 360.0


R_TAG = R_HEAD + 8.0
TAG_A = 4.6
for k, i in enumerate(SEQ, 1):
    seq_tag(sh, w.pt(*bb_uv(TH[i], R_TAG)), str(k), TAG_A)
# A-A: the plane y = 0 through hole 0 (horizontal leg) and x = 0 bounding the removed
# quarter (vertical leg); the vertical leg turns outside the part so that its end
# arrow can point along the viewing direction too.  The chain is broken round tag 1.
R_CP = R_HEAD + 15.0
EXT_CP = 4.0
cut_path(w, [(-R_CP, 0.0), (0.0, 0.0), (0.0, R_HEAD + 18.0), (-16.0, R_HEAD + 18.0)],
         "A", (0, -1), ext=EXT_CP,
         gaps=[(R_CP + EXT_CP - R_TAG - TAG_A / 2 - 0.6, R_CP + EXT_CP - R_TAG + TAG_A / 2 + 0.6)])
# keying: hole 0 is 0.8 deg off the 20 deg pitch.  The chain line is hole 0's axis
# and serves as that extension line; the arcs sit beyond its end.
R_ANG = 78.0
a1, a0, a17 = bb_ang(TH[1]), bb_ang(TH[0]), bb_ang(TH[17])
w.dim_ang((0.0, 0.0), a1, a0, R_ANG, ext=False)
w.dim_ang((0.0, 0.0), a0, a17, R_ANG, ext=False)
for a, r0 in ((a1, R_TAG + 3.6), (a17, R_TAG + 3.6), (a0, R_CP + EXT_CP + 1.0)):
    dd = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
    sh.line([w.pt(0, 0) + dd * r0, w.pt(0, 0) + dd * (R_ANG + 2.0)], THIN)
# screws: callout under the view, from screw 16's head
w.leader(bb_uv(TH[16], R_HEAD), -4.0, -50.0,
         [f"18 {TIMES} item 15, M6{TIMES}10-010.9 (ISO 7380-1)",
          f"{TQS}, nickel anti-seize on the",
          "threads only, head face dry. Order: the",
          "boxed numbers, 3 passes (note " + note("screws") + "). Holes",
          f"in item 1: {DIA}{f2(P.CASE_HOLE_D)} +0.03/0 (ref)"])

# ---- detail C: case seal gland (5:1) -----------------------------------------------------
c = v.detail((0.5 * (Z_G1 + Z_G2), R_BORE), 8.2, 5.0, (112.0, 140.0), "C",
             circle_label_ang=60)
# kit fmt() drops trailing zeros: the measured width is formatted here to 2 places
c.dim_h((Z_G1 - GW, R_LAND), (Z_G1 + GW, R_LAND), at=R_CASE + 2.4, tol=("+0.08", "0"),
        text="2" + TIMES + " " + f2(abs((Z_G1 + GW) - (Z_G1 - GW))))
c.leader((Z_G2 + GW + 1.0, R_BORE), 22.0, 22.0,
         [f"BORE, item 1: {DIA}A {BORE_TOL}, honed",
          "Ra 0.4 (0.8 max), circumferential lay;",
          f"{A_RANGE}, recorded per zone",
          f"(SRM100-101). Drawn at A = {f3(P.CASE_ID)}."])
c.leader((Z_G2 + GW + 0.4, R_LAND), 27.0, -14.0,          # inside the detail circle
         [f"LAND, item 2: {DIA}A - {f2(LAND_OFF)} {LAND_TOL}",
          f"({DIA}{f2(P.PLUG_OD)} at A = {f3(P.CASE_ID)})",
          f"clearance on {DIA} {f2(CLR_MIN)}-{f2(CLR_MAX)}",
          f"({f3(CLR_MIN / 2)}-{f3(CLR_MAX / 2)} radial)"])
c.leader((Z_G1 + GW - 0.5, R_GRV), 26.0, -42.0,
         [f"2 GROOVES {DIA}A - {f2(GRV_OFF)} {GRV_TOL}",
          f"({DIA}{f2(P.ORING_GROOVE_D)} at A = {f3(P.CASE_ID)})",
          f"gland depth {f3(GLAND)} (ref)"])
c.leader((Z_G1 - 1.0, R_GRV + 1.0), -10.0, -28.0,
         [f"2 {TIMES} item 13, {P.ORING_DASH}",
          ORING_TXT.split(" or ")[0],
          f"or {ORING_TXT.split(' or ')[1]}, squeeze {100 * SQ:.1f} %",
          "lube: " + P.LUBE.split(" or ")[0],
          "or " + P.LUBE.split(" or ")[1]])

# ---- detail D: insert O-ring gland (5:1) --------------------------------------------------
d = v.detail((Z_IG, 0.5 * (R_IOD + R_IGRV)), 6.2, 5.0, (272.0, 140.0), "D",
             circle_label_ang=135)
d.dim_h((Z_IG - GW, R_IGRV), (Z_IG + GW, R_IGRV), at=R_IGRV + 5.4, tol=("+0.08", "0"),
        text=f2(abs((Z_IG + GW) - (Z_IG - GW))))
d.leader((Z_IG + GW + 1.6, R_IB), 22.0, 26.0,
         [f"BORE, item 2: {DIA}{f2(P.INSERT_BORE_D)} +0.025/0",
          f"INSERT, item 3: {DIA}{f2(P.INSERT_OD)} 0/-0.05",
          f"clearance on {DIA} {f3(ICLR_MIN)}-{f3(ICLR_MAX)}"])
d.leader((Z_IG + GW, R_IGRV - 0.8), 26.0, -8.0,
         [f"GROOVE {DIA}{f2(P.INSERT_GROOVE_D)} +0.05/0 at z {fmt(Z_IG)}",
          f"gland depth {f3(IGLAND)} (ref)"])
d.leader((Z_IG - 0.8, R_IOD + 1.2), 20.0, -40.0,
         [f"item 14, {P.INSERT_ORING_DASH}, {ORING_TXT},",
          f"squeeze {100 * ISQ:.1f} %, lube as item 13,",
          "fitted in item 2's groove first"])
d.leader((Z_IG - 4.0, R_IOD - 2.5), -12.0, -38.0,
         ["ITEM 3: slide in by hand, aft end first.", "Never press or knock it in.",
          "Push sleeve: extraction only (note " + note("extract") + ")."])

# ---- view J: the aft end at entry, seen from aft (1:2): clocking ---------------------------
# item 2 in item 1, no screws, no cap.  Hole 0 is radial (hidden from aft): its axis is
# drawn, with puller P1 / P2 on the holder aft face and the 9.2 deg from P1 to hole 0.
j_parts = [part(n) for n in ("case", "nozzle_holder", "nozzle_insert")]
JX, JY, JS = 400.0, 195.0, 0.5
jv = View(sh, j_parts, (JX, JY), JS, look="aft", rot=ROT)
jv.center_mark((0.0, 0.0), 14.0, ext=0.0)
jc = np.array(jv.pt(0.0, 0.0))


def j_dir(theta_deg):
    """Paper unit vector of motor angle theta in view J (u = -x, v = y, turned ROT)."""
    t = math.radians(theta_deg + ROT)
    return np.array([-math.cos(t), math.sin(t)])


def j_ang(theta_deg):
    d = j_dir(theta_deg)
    return math.degrees(math.atan2(d[1], d[0])) % 360.0


R_JP = P.HOLDER_PULLER_R * JS                  # puller circle, paper
R_JC = R_CASE * JS                             # case / flange OD, paper
sh.circle(jc, R_JP, THIN, "center")
for lab, th, sgn in (("P1", PTH[0], 1.0), ("P2", PTH[1], -1.0)):
    pc = jc + j_dir(th) * R_JP
    thread_34(sh, pc, 6.0 * JS)
    # label on a leader out past the flange OD (P1 up-left, P2 down-right), clear of
    # the 9.2 deg dimension and of the thin tangent-edge circles on the flange face
    uv = (pc - jc) / JS + np.array([0.0, sgn * 3.2])
    jv.leader(tuple(uv), -4.0 * sgn, 14.0 * sgn, [lab])
# hole 0 axis (radial, carries the clocking line and the AFT markings) and P1's ray
R_JA = 34.0
for th, r0 in ((TH[0], R_JC - 6.0), (PTH[0], R_JP + 2.5)):
    dd = j_dir(th)
    sh.line([jc + dd * r0, jc + dd * (R_JA + 2.0)], THIN, "center" if th == TH[0] else "solid")
# hole 0 is counter-clockwise of P1 seen from aft: arc P1 -> hole 0, CCW on the paper
jv.dim_ang((0.0, 0.0), j_ang(PTH[0]), j_ang(TH[0]), R_JA, ext=False)
q = jc + j_dir(TH[0]) * (R_JA + 3.0)
sh.text(q[0], q[1] - 4.2, "HOLE 0", D.H, ha="right")
jv.label("J (1:2)", where="below", gap=6.0)
text_block(sh, JX - 34.0, JY - R_JC - 16.5, None,
           ["At entry, seen from aft: hole 0 of item 2 on",
            "hole 0 of item 1, clocking line straight across",
            f"both, AFT markings side by side (note {note('clock')}).",
            f"Hole 0 is {fmt(P1_TO_H0, 1)}{DEG} counter-clockwise of puller",
            f"P1 ({chr(952)} {fmt(PTH[0], 0)}{DEG}); P2 at {chr(952)} {fmt(PTH[1], 0)}{DEG}, "
            f"both on r {fmt(P.HOLDER_PULLER_R)}:",
            f"{PUL_TXT} (SRM100-102)."])

# ---- notes: build-up and installation ----------------------------------------------------
NX = 442.0
TH_ = chr(952)
NB = chr(0xA0)                                 # no-break space: textwrap never splits it
LABEL_TXT = " / ".join(str(t) for t in LABEL_T) + f" {DEG}C"
NOTES = {
    "tooling":
    "Item numbers, materials and part numbers: parts list on sheet 1. Tooling named here "
    "(hole plugs, push sleeve, puller bridge) is not part of this drawing set.",
    "first":
    "Before the first build (README, case): item 1 per SRM100-101, each seal zone honed to "
    "the smallest diameter that cleans up, A (the smallest reading in the zone, "
    f"{A_RANGE}), held to A {BORE_TOL} and recorded per zone; items 2 and 6 cut to their "
    "zone's A; each end match-drilled with its closure, serialised and marked (SRM100-101 "
    "note 8, SRM100-102 note 8, SRM100-103 note 11), clocking line scribed; hole baseline "
    "recorded (SRM100-101 R7). Then the hydrostatic proof (SRM100-001, proof dummy "
    "SRM100-120 in place of item 3, no insulators, liner or propellant): before the first "
    "firing and after any repair, any retired-and-replaced part or a label reading "
    f"≥ {LABEL_LIMIT} {DEG}C (note {note('read')}).",
    "new":
    f"The parts replaced after every firing (note {note('after')}) are always new. Lubricant "
    f"for every O-ring, the liner OD and the insulator edges: {P.LUBE}.",
    "orings":
    f"Fit item 14 in the bore groove of item 2, then 2 {TIMES} item 13 in the grooves of "
    "its seal land (details C, D). Item 2 is cut to the aft-zone bore A recorded on "
    f"SRM100-101 ({A_RANGE}): land A - {f2(LAND_OFF)} {LAND_TOL}, groove bottoms "
    f"A - {f2(GRV_OFF)} {GRV_TOL} ({f2(P.PLUG_OD)} / {f2(P.ORING_GROOVE_D)} at "
    f"A = {f3(P.CASE_ID)}). Details C and D are drawn at A = {f3(P.CASE_ID)}.",
    "insert":
    "Slide insert item 3 into item 2 by hand, aft (exit) end first, until it seats on the "
    "lip. Never press or knock it. Check: its forward face lies flush with item 2's forward "
    f"face to {f2(FLUSH_MAX)} below it (seat {f2(SEAT)} +0.05/0, insert {f2(SEAT)} 0/-0.05). "
    "Then seat nozzle insulator item 4 on item 2's forward face.",
    "plugs":
    f"Hole plugs: push 18 flat-ended acetal (Delrin) plugs, {DIA}6.35 {TIMES} 3.85 with an "
    "outside head, into the case's aft-end holes. Their ends sit about 0.15 mm shy of the "
    "bore, so no O-ring is dragged across an open hole edge.",
    "clock":
    "Clocking (view J): enter item 2 with its hole 0 on the case's hole 0, the scribed "
    "clocking line straight across the case end and the flange and the AFT markings of "
    "items 1 and 2 (SRM100-101 note 8, SRM100-102 note 8) side by side. Check: seen from "
    f"aft, hole 0 is {fmt(P1_TO_H0, 1)}{DEG} counter-clockwise of puller P1 "
    f"({TH_} {fmt(PTH[0], 0)}{DEG}). Push in by hand until the flange butts on the case end "
    "face (zero gap).",
    "screws":
    f"Pull each plug as its screw goes in. Screws 18 {TIMES} item 15, {TQS}, nickel "
    "anti-seize on the threads only, head face dry. Tighten in the boxed order of section "
    f"B-B (opposite pairs, criss-cross): pass 1 to about {f1(TQ[0] / 2)}{NB}{NM}, pass 2 to "
    "final torque, pass 3 at final torque hole by hole round the circle, as a check. Never "
    f"fit an M6{TIMES}16 (item 16) here: it bottoms with its head proud.",
    "fwd":
    "Load the liner and grain stack and close the forward end: sheet 3.",
    "labels":
    f"Temperature labels, new for every firing: irreversible {LABEL_TXT} strips on item 1's "
    f"OD at z{NB}{fmt(LABEL_Z[0], 0)}-{fmt(LABEL_Z[1], 0)}, {TH_} {fmt(LABEL_TH[0], 0)}{DEG} and "
    f"{fmt(LABEL_TH[1], 0)}{DEG} (SRM100-101 note{NB}8), and on item 2's aft body "
    f"{DIA}{f2(2 * R_BODY)} at {TH_} {fmt(LABEL_TH[0], 0)}{DEG} and {fmt(LABEL_TH[1], 0)}{DEG} "
    f"(SRM100-102 note{NB}8), clear of the cap tape (note {note('cap')}).",
    "cap":
    "Cap item 5: fit it now, in the exit, flange on item 2's aft face, taped per SRM100-106 "
    "note 6. It is the debris seal and stays on through storage and transport. At the stand "
    "it comes off only to insert the igniter, which always goes in last (leads shunted, out "
    f"through the cap's {DIA}{fmt(P.CAP_LEAD_HOLE)} hole); then it is refitted and re-taped "
    "with new tape (sheet 1 note 4). Never move the motor with an igniter in it.",
    "read":
    "After every firing, before extraction: read and record the temperature labels on "
    f"items 1 and 2 (note {note('labels')}). A reading ≥ {LABEL_LIMIT} {DEG}C: retire or "
    "re-proof that end (SRM100-101 R10, SRM100-001).",
    "extract":
    "Extraction, never lever or knock. Closure: split clamp collar (100.0 bore) on the case "
    f"OD at least {fmt(COLLAR_MIN, 0)} mm from the end, clear of the screw heads at "
    f"z{NB}{fmt(Z_B)} (sweep {DIA}{f2(HEAD_SWEEP_D)} ref), the labels and the marking at "
    f"z{NB}{fmt(MARK_Z[0], 0)}-{fmt(MARK_Z[1], 0)}; puller bridge and 2 {TIMES} M6 draw screws "
    "in item 2's puller threads P1, P2 (view J). Insert: with item 2 out, support it on its "
    "forward face in an arbor press and push item 3 out forward with the push sleeve "
    f"({DIA}52.4 ID {TIMES} {DIA}53.8 OD) through the lip bore onto its push face, "
    "r 26.2-27.0. The push sleeve is for extraction only.",
    "after":
    f"Then, after every firing: measure the throat. Replace {REPLACE}. Re-use {REUSE}. "
    "On the aft case end, measure hardness and conductivity again and re-gauge every bolt "
    "hole against its baseline (SRM100-101 R10).",
}
assert list(NOTES) == NOTE_KEYS
notes = [NOTES[k] for k in NOTE_KEYS]
yb = sh.notes(NX, 402.0, notes, 138.0, title="AFT END BUILD-UP AND INSTALLATION")

# ---- reference stations --------------------------------------------------------------
rows = [["STATION (ref)", "z"],
        ["Cap flange back face (motor aft end)", f2(Z_CAPB)],
        ["Holder aft face", f2(Z_HAFT)],
        ["Nozzle exit plane (graphite aft face)", f2(Z_EXIT)],
        ["Holder flange aft face", f2(Z_FL)],
        ["Insert O-ring groove, centre", f2(Z_IG)],
        ["Case aft end face = flange face (datum)", f2(0.0)],
        [f"Bolt row, 18 {TIMES} item 15", f2(Z_B)],
        ["Case O-ring grooves, centres", f"{f2(Z_G1)} / {f2(Z_G2)}"],
        ["Holder and insert forward faces", f2(Z_FACE)],
        ["Insulator fwd face = liner and spacer 0 aft", f2(P.Z_NOZ_INSUL_FWD)],
        ["Grain 1 aft face", f2(P.grain_z(0))]]
# bottom left of the title block, under details C / D: the notes column is full
TBX, TBY = 262.0, 78.0
sh.text(TBX, TBY + 2.0, "AXIAL STATIONS, z from the case aft end face, + forward", 2.5, bold=True)
yt = sh.table(TBX, TBY, [110.0, 28.0], rows, row_h=5.0, align=["l", "r"])
sh.text(NX, yb - 5.0, "USED ON: SRM-100 motor (Helios) - static test and flight", D.H)

if __name__ == "__main__":
    sh.lint()
    sh.save("aft_end")
