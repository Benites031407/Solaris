"""SRM100-001 HYDROSTATIC PROOF ASSEMBLY (A2): the srm_assembly.proof_placements()
build - flight case, both closures, all five O-rings and all 36 screws, with the 304
proof dummy SRM100-120 in the graphite insert's gland and nothing inside the case.

Main view: half-section of the whole assembly at 1:2, every row turned rot = -0.8 so
that screw / hole 0 (theta 0.8 deg) lies in the cutting plane.  Partial views B (aft
end) and C (forward end) at 1:1, framed on the main view (ISO 128-3).  The proof
fills and bleeds through ONE port, the dummy's 1/8-27 NPT port (view B), the motor's
only port: item 6 is solid, no port (view C).  Proof set-up schematic
(motor vertical, aft end up: rig tee on item 17's port, dip tube for the fill), fits
and seals table, proof schedule, parts list (ISO 7573, header at the bottom, above
the title block), and the test procedure and acceptance criteria taken from the
README's "Hydrostatic proof" section.

View frame: u = motor z (0 at the case's aft end face, + forward), v = radius.
Item numbers are the fixed SRM-100 numbers; the dummy, which is not in the flight
parts list, is item 17 and takes item 3's place.

Local primitives (not in srm_dwg): mask (white ground under dimension text on
hatching), frame_rect (framed partial-view indication on the parent view),
flow_arrow (fill / bleed direction, one or both ends headed), the schematic symbols
valve / gauge / relief / pump / tank, and the bottom-header parts list (two sh.table
calls).
"""

import json
import math

import numpy as np

import srm_dwg as D
import srm_params as P
import srm_assembly as A
import nozzle_holder as NH
import fwd_closure as FC
import proof_dummy as PD
from srm_dwg import DIA, DEG, TIMES, PM, THIN, THICK, Hatch, Part, Sheet, View, fmt

S = P.nozzle_stations()
TH = P.bolt_thetas()
PTH = P.puller_thetas()                        # P1 10 deg, P2 190 deg: theta 0 on a closure
THETA = "θ"
ROT = -TH[0]                                   # hole 0 into the cutting plane

# ---- model stations (motor frame) ---------------------------------------------------
Z_HAFT = NH.Z_AFT                              # holder aft face: aft end of the build
Z_TOP = P.CASE_L + FC.Z_TOP                    # forward closure flange face: fwd end
Z_BA, Z_BF = P.bolt_z_aft(), P.bolt_z_fwd()    # bolt rows
Z0 = PD.Z0                                     # dummy aft face (the fill / bleed port's face)
Z_SOLID = (P.CASE_L + FC.Z_IN, P.CASE_L + FC.Z_TOP)   # item 6, solid: inboard face .. forward face
Z_CEIL = S["z_fwd"]                            # aft end up: items 2 / 17 forward faces, one flat ceiling
R_CASE = P.CASE_OD / 2.0
R_BORE = P.CASE_ID / 2.0
R_BODY = NH.R_BODY
R_FL = P.FLANGE_OD / 2.0
MB = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())
R_SWEEP = MB["envelope"]["max_diameter_mm"] / 2.0   # screw-head sweep, 106.04 (ref)
Z_G = (P.GROOVE_1_Z, P.GROOVE_2_Z)             # aft closure grooves (motor z)
Z_GF = tuple(P.CASE_L - g for g in Z_G)        # forward closure grooves
R_GRV = P.ORING_GROOVE_D / 2.0

# ---- fits (srm_params) ----------------------------------------------------------------
CLR = ((P.CASE_ID + P.TOL_BORE[0]) - (P.PLUG_OD + P.TOL_LAND[1]),
       (P.CASE_ID + P.TOL_BORE[1]) - (P.PLUG_OD + P.TOL_LAND[0]))
ICLR = ((P.INSERT_BORE_D + P.TOL_INSERT_BORE[0]) - (P.INSERT_OD + P.TOL_INSERT_OD[1]),
        (P.INSERT_BORE_D + P.TOL_INSERT_BORE[1]) - (P.INSERT_OD + P.TOL_INSERT_OD[0]))
SQ = 1.0 - P.GLAND_DEPTH / P.ORING_CS
ISQ = 1.0 - P.INSERT_GLAND_DEPTH / P.INSERT_ORING_CS
SEAT = NH.Z_FACE - NH.Z_SEAT                   # seat depth = dummy length, nominal
FLUSH_MAX = 0.05 - (-0.05)                     # seat +0.05/0, dummy 0/-0.05
LIG = P.BOLT_EDGE - P.CASE_HOLE_D / 2.0        # 9.80 nominal ligament
HOLE_CHG_MAX = 0.05     # retire: hole length growth / ligament loss vs its own baseline (G14, 101 R7)
TQA, TQF = P.BOLT_TORQUE_AFT_NM, P.BOLT_TORQUE_FWD_NM
P_PROOF = P.PROOF_X_MEOP * P.MEOP
f1 = lambda x: f"{x:.1f}"
f2 = lambda x: f"{x:.2f}"
f3 = lambda x: f"{x:.3f}"
NM = "N" + "·" + "m"
TQS_A = f1(TQA[0]) + "-" + f1(TQA[1]) + " " + NM                    # 3.0-3.5 N.m
TQS_F = f1(TQF[0]) + "-" + f1(TQF[1]) + " " + NM                    # 4.0-6.0 N.m
DL, DG = P.CASE_ID - P.PLUG_OD, P.CASE_ID - P.ORING_GROOVE_D        # land A - 0.06, groove A - 5.67
M6 = ("M6" + TIMES + "1-6H " + D.DEPTH + fmt(P.PULLER_DEPTH - P.DRILL_OVER) + " / " + DIA
      + fmt(P.PULLER_TAP_DRILL) + " " + D.DEPTH + fmt(P.PULLER_DEPTH))          # puller, G5
# hardness / conductivity positions, as SRM100-101 record R8 (decision G22): between the
# holes at theta 50 / 130 / 230 / 310, a band z 5-25 and a reference at z 100 from each end
HAZ = [TH[k] + 0.5 * 360.0 / P.N_BOLTS for k in (2, 6, 11, 15)]
HZ, HREF = (5.0, 25.0), 100.0
COLLAR_MIN = 50.0                              # extraction collar from the end (decision G18)
MARK_Z = (20.0, 45.0)                          # case marking / labels zone, SRM100-101 note 8


def _mass_g(src, rho):
    """Adaptive BRepGProp volume (build123d's .volume reads low on trimmed faces) x rho."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(D.load(src).wrapped, props, 1e-9, True)
    return props.Mass() * rho * 1000.0


# ---- parts list (fixed item numbers; masses from out/mass_budget.json) ----------------
MB_G = {k: v["mass_each_kg"] * 1000.0 for k, v in MB["parts"].items()}
MB_G["proof_dummy"] = _mass_g("proof_dummy.step", P.SS_RHO)    # not in the flight budget
FKM = "FKM 90A (Parker\nV0709-90 or equal)"
ITEMS = [  # item, qty, part number, description, material, mass_budget key
    (1, 1, "SRM100-101", "Motor case", "6061-T6 drawn tube", "case"),
    (2, 1, "SRM100-102", "Nozzle holder (aft closure)", "304 stainless", "nozzle_holder"),
    (6, 1, "SRM100-103", "Forward closure", "6061-T651", "fwd_closure"),
    (13, 4, "AS568-237", "O-ring, case seal", FKM, "oring_case"),
    (14, 1, "AS568-230", "O-ring, insert seal", FKM, "oring_insert"),
    (15, 18, "ISO 7380-1 M6" + TIMES + "10-010.9", "Button-head screw, aft", "steel 010.9",
     "bolt_m6x10"),
    (16, 18, "ISO 7380-1 M6" + TIMES + "16-010.9", "Button-head screw, fwd", "steel 010.9",
     "bolt_m6x16"),
    (17, 1, "SRM100-120", "Proof dummy (replaces item 3)", "304 stainless, ASTM A479",
     "proof_dummy"),
]
# exact STEP masses x qty (water excluded), not the sum of the rounded list (G25, item 6
# solid, no port, no pocket: 6089.8 g)
MASS = round(sum(q * MB_G[k] for _, q, _, _, _, k in ITEMS), 1)

sh = Sheet("SRM100-001", "HYDROSTATIC PROOF ASSEMBLY",
           "Flight case and closures, proof dummy SRM100-120 in the insert gland",
           size="A2", material="See parts list", mass_g=MASS, scale="1:2",
           doc_type="ASSEMBLY DRAWING", finish=None, edges="-")


# ---- local primitives ------------------------------------------------------------------
def mask(first, pad=0.7):
    """White ground behind sh.texts[first:], over hatching (z 2), under lines (z >= 3)."""
    for t in sh.texts[first:]:
        bb = t.get_window_extent(sh._renderer).transformed(sh.ax.transData.inverted())
        sh.fill([(bb.x0 - pad, bb.y0 - pad), (bb.x1 + pad, bb.y0 - pad),
                 (bb.x1 + pad, bb.y1 + pad), (bb.x0 - pad, bb.y1 + pad)], color="w", z=2.5)


def rect(p0, p1, lw=THIN, style="solid"):
    (x0, y0), (x1, y1) = p0, p1
    sh.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], lw, style)


def frame_rect(view, win, letter, at):
    """Partial / enlarged view indication on the parent view: the window framed by a
    continuous narrow line, designated by its letter at paper offset `at` from the
    frame's lower-left corner."""
    p0, p1 = view.pt(win[0], win[1]), view.pt(win[2], win[3])
    rect(p0, p1)
    sh.text(p0[0] + at[0], p0[1] + at[1], letter, 3.5, ha="center")


def flow_arrow(p, q, lw=0.5, L=4.0, W=1.8, both=False):
    """Flow direction p -> q (paper): line with a large filled head at q (and at p too,
    both=True: flow both ways through one port, fill in and bleed out)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = D._unit(q - p)
    n = D._perp(d)
    b = q - d * L
    a = p + d * L if both else p
    sh.line([a, b], lw, cap="butt")
    sh.fill([q, b + n * W / 2, b - n * W / 2], lw=0.05)
    if both:
        sh.fill([p, a + n * W / 2, a - n * W / 2], lw=0.05)


def valve(c, vertical=True, a=3.0):
    """Two-way valve (ISO 1219 style bow-tie), centred at c."""
    x, y = c
    if vertical:
        pts = [(x - a / 2, y - a), (x + a / 2, y - a), (x - a / 2, y + a), (x + a / 2, y + a),
               (x - a / 2, y - a)]
    else:
        pts = [(x - a, y - a / 2), (x - a, y + a / 2), (x + a, y - a / 2), (x + a, y + a / 2),
               (x - a, y - a / 2)]
    sh.line(pts, THIN)


def gauge(c, r=4.5):
    sh.circle(c, r, THIN)
    p = np.asarray(c) + (-0.6 * r, -0.6 * r)
    q = np.asarray(c) + (0.62 * r, 0.62 * r)
    sh.line([p, q - (0.9, 0.9)], THIN)
    sh.arrow(q, q - p)


def relief(c, w=8.0, h=11.0):
    """Pressure-relief valve: box, flow arrow offset from the inlet, spring on top."""
    x, y = c
    rect((x - w / 2, y), (x + w / 2, y + h))
    sh.line([(x - 1.2, y + 2.0), (x + 1.2, y + h - 3.5)], THIN)
    sh.arrow((x + 1.2, y + h - 3.0), (1.2, h - 5.5))
    zz = [(x, y + h)]
    for k in range(4):
        zz.append((x + (1.3 if k % 2 == 0 else -1.3), y + h + 1.0 + k * 1.1))
    zz.append((x, y + h + 5.4))
    sh.line(zz, THIN)


def pump(c, r=4.5, left=True):
    sh.circle(c, r, THIN)
    x, y = c
    s = -1.0 if left else 1.0
    sh.fill([(x + s * r * 0.95, y), (x - s * r * 0.35, y + r * 0.62),
             (x - s * r * 0.35, y - r * 0.62)], lw=0.05)


def tank(x0, y0, x1, y1, level):
    sh.line([(x0, y1), (x0, y0), (x1, y0), (x1, y1)], THIN)
    sh.line([(x0 + 1.0, level), (x1 - 1.0, level)], THIN)
    for k in range(2):
        yy = level - 1.3 * (k + 1)
        sh.line([(x0 + 3.0 + 1.5 * k, yy), (x1 - 3.0 - 1.5 * k, yy)], THIN)


def balloons(view, rows):
    for n, tgt, at in rows:
        sh.balloon(view.pt(*tgt), n, at)


# ---- parts, hatching (metals 45 / 135 alternating, O-rings solid) -------------------
H = {"case": Hatch(135, 1.5), "nozzle_holder": Hatch(45, 2.0), "fwd_closure": Hatch(45, 2.0),
     "proof_dummy": Hatch(135, 2.5, offset=0.5)}
# Screws are never sectioned.  Screw 0 lies in the cutting plane (its outline masks the
# hatching of its hole); screws 1-4 lie in the removed quadrant; 5-9 are seen in the
# lower (outside) half; 10-17 are behind the case, or behind the section faces, where
# an occluding outline would wrongly break the hatching: they are left out.
parts = []
for g, n, st, tr in A.proof_placements():
    if n.startswith("bolt"):
        i = int(n[-2:])
        th = TH[i] + ROT
        if i == 0:
            parts.append(Part(st, tr, cut=False, occlude=True, name=n))
        elif 90.0 < th <= 180.0:
            parts.append(Part(st, tr, cut=False, occlude=False, name=n))
    elif n.startswith("oring"):
        parts.append(Part(st, tr, hatch=Hatch(solid=True), name=n))
    else:
        parts.append(Part(st, tr, hatch=H[n], name=n))

# =======================================================================================
# main view: half-section, 1:2
# =======================================================================================
OX, OY = 60.6, 360.0
v = View(sh, parts, (OX, OY), 0.5, section="half", rot=ROT)
v.dim_h((Z_HAFT, R_BODY), (Z_TOP, R_FL), at=R_FL + 16.0, ref=True)           # 748.01
v.dim_dia(Z_BF, R_SWEEP, at=Z_TOP + 19.0, ref=True)                             # head sweep
v.text((Z_HAFT, -R_FL - 22.0), "HALF SECTION: cutting plane through the axis and screw "
       "holes 0 (" + fmt(TH[0], 1) + DEG + "); nothing inside the case", D.H)
WB = (-54.0, -57.0, 48.0, 57.0)
WC = (640.0, -57.0, 702.0, 57.0)
frame_rect(v, WB, "B", (-3.5, -6.0))
frame_rect(v, WC, "C", (34.5, -6.0))

# =======================================================================================
# B: aft end, 1:1 (partial view, broken on the forward side)
# =======================================================================================
BX, BY = 130.0, 250.0
b = View(sh, parts, (BX, BY), 1.0, section="half", rot=ROT, window=WB)
b.zigzag((WB[2], WB[1] + 3.0), (WB[2], WB[3] - 3.0))
b.label("B (1:1)", where="below", gap=6.0)
# fill AND bleed, both ways through one port: the dummy's 1/8-27 NPT port, the motor's
# only port (item 6 has none), reached through the holder's lip bore
pf = b.pt(Z0 - 0.6, 2.2)
flow_arrow((24.0, pf[1]), pf, both=True)
yb = pf[1] + 2.2
FB = ["FILL / BLEED:", "1/8-27 NPT port of item 17", "(the motor's only port),",
      "through the lip bore of item 2"]
for k, s in enumerate(FB[::-1]):
    sh.text(24.0, yb + k * 4.0, s, D.H, bold=(k == len(FB) - 1))
balloons(b, [
    (14, (P.INSERT_GROOVE_Z, P.INSERT_GROOVE_D / 2.0 - 1.4), (100.0, 318.0)),
    (15, (Z_BA, R_CASE + 1.6), (143.0, 318.0)),
    (1, (42.0, R_CASE - 2.0), (178.0, 318.0)),
    (13, (Z_G[1], R_GRV + 1.4), (196.0, 302.0)),
    (2, (26.0, 40.0), (196.0, 288.0)),
    (17, (20.0, 26.0), (196.0, 274.0)),
])
# torque, on a head of the lower (outside) half
th = math.radians(TH[13] + ROT)
hv = R_CASE * math.cos(th)
b.leader((Z_BA + 3.0, hv + 3.0), 44.0, -20.0,
         ["18 " + TIMES + " item 15, M6" + TIMES + "10:",
          TQS_A + ", nickel anti-seize",
          "on the threads only, head face dry"], end="dot")

# =======================================================================================
# C: forward end, 1:1 (partial view, broken on the aft side)
# =======================================================================================
CX, CY = 272.0 - WC[0], 250.0
c = View(sh, parts, (CX, CY), 1.0, section="half", rot=ROT, window=WC)
c.zigzag((WC[0], WC[1] + 3.0), (WC[0], WC[3] - 3.0))
c.label("C (1:1)", where="below", gap=6.0)
# item 6 has no port (G24) and no pocket (G25): solid from the inboard face to the flat
# forward face.  The dot sits near the axis 5 mm inside the forward face, so the leader
# crosses only that strip of hatching and the face outline, then leaves the view forward
c.leader((Z_SOLID[1] - 5.0, 8.0), 24.0, 8.0, ["item 6: solid, no port"], end="dot")
balloons(c, [
    (1, (646.0, R_CASE - 2.0), (262.0, 318.0)),
    (13, (Z_GF[1], R_GRV + 1.4), (286.0, 318.0)),
    (16, (Z_BF, R_CASE + 1.6), (310.0, 318.0)),
    (6, (682.0, 36.0), (350.0, 300.0)),
])
c.leader((Z_BF + 3.0, hv + 3.0), 38.0, -26.0,
         ["18 " + TIMES + " item 16, M6" + TIMES + "16:",
          TQS_F + ", Loctite 243"], end="dot")

# =======================================================================================
# proof set-up schematic (not to scale)
# =======================================================================================
sh.text(424.0, 398.0, "PROOF SET-UP (SCHEMATIC, NOT TO SCALE)", 3.5, bold=True)
sh.text(424.0, 391.0, "TEST ORIENTATION: AFT END UP", D.H, bold=True)
# the motor, vertical, aft end up: item 17's port (the only port) at the top
MX = 446.0
Y_FWD, Y_AFT = 308.0, 362.0
rect((MX - 8.0, Y_FWD), (MX + 8.0, Y_AFT), THICK)
sh.text(MX + 4.6, 0.5 * (Y_FWD + Y_AFT), "SRM100-001", D.H, ha="center", va="center",
        rot=90.0)
sh.text(MX - 10.0, Y_AFT - 4.5, "AFT", D.H, ha="right")
sh.text(MX - 10.0, Y_FWD + 1.0, "FWD", D.H, ha="right")
# dip tube (fill only), dashed: down the port and the passage to rest on item 6's inboard
# face, end cut at 45 deg
TW = 0.8
sh.line([(MX - TW, Y_AFT), (MX - TW, Y_FWD + 0.5)], THIN, "hidden")
sh.line([(MX + TW, Y_AFT), (MX + TW, Y_FWD + 0.5 + 2 * TW)], THIN, "hidden")
sh.line([(MX - TW, Y_FWD + 0.5), (MX + TW, Y_FWD + 0.5 + 2 * TW)], THIN)
DT = ["DIP TUBE " + DIA + fmt(P.PROOF_DIP_TUBE_OD) + " " + TIMES + " "
      + fmt(P.PROOF_DIP_TUBE_L), "(fill only; withdrawn before", "the tee is fitted)"]
for k, s in enumerate(DT):
    sh.text(424.0, Y_FWD - 9.0 - 4.0 * k, s, D.H)
# leader from 1 mm above the label's first line, up to the tube's left-hand wall
lp = np.array([424.0 + 0.6 * sh.text_width(DT[0], D.H), Y_FWD - 9.0 + D.H + 1.0])
lt = np.array([MX - TW - 0.3, Y_FWD + 6.0])
sh.line([lp, lt], THIN)
sh.arrow(lt, lt - lp)
# rig tee on the port: bleed valve on top (vented), pump line on the side branch
YT = Y_AFT + 6.0
sh.line([(MX, Y_AFT), (MX, YT + 3.0)], THICK)
sh.dot((MX, YT), 0.8)
valve((MX, YT + 6.0))
sh.line([(MX, YT + 9.0), (MX, YT + 11.0)], THICK)
flow_arrow((MX, YT + 11.0), (MX, YT + 17.0), lw=0.35, L=3.0, W=1.4)
sh.text(MX + 3.5, YT + 5.2, "BLEED VALVE", D.H)
sh.text(MX + 2.0, YT + 13.5, "vent", D.H)
sh.text(MX - 2.5, YT + 0.8, "RIG TEE on", D.H, ha="right")
sh.text(MX - 2.5, YT - 3.2, "item 17 port", D.H, ha="right")
# pump line: tee side branch -> barrier -> gauge, relief valve, pump <- water
YL = 304.0
XV = 466.0
XI = 535.0                         # isolates the pump for the decay holds (by the operator)
sh.line([(MX, YT), (XV, YT), (XV, YL), (XI - 3.0, YL)], THICK)
sh.line([(XI + 3.0, YL), (566.0, YL)], THICK)
flow_arrow((XV, 342.0), (XV, 352.0), lw=0.35, L=3.0, W=1.4)
sh.text(XV - 2.0, 322.0, "PUMP LINE", D.H, ha="center", rot=90.0)
XB = 474.0
sh.line([(XB, 290.0), (XB, 381.0)], 0.7, "hidden")
sh.text(XB + 4.5, 340.0, "BARRIER", D.H, rot=90.0)
sh.text(XB + 8.0, 332.0, "operator side", D.H, rot=90.0)
XG = 488.0
sh.line([(XG, YL), (XG, YL + 5.0)], THIN)
gauge((XG, YL + 9.5))
sh.text(XG, YL + 16.0, "GAUGE", D.H, ha="center")
valve((XI, YL), vertical=False)
sh.text(XI, YL + 3.2, "ISOLATION", D.H, ha="center")
XR = 512.0
sh.line([(XR, YL), (XR, YL + 4.0)], THIN)
relief((XR, YL + 4.0))
sh.line([(XR + 4.0, YL + 12.0), (573.0, YL + 12.0), (573.0, 292.0)], THIN)
sh.arrow((573.0, 292.0), (0, -1))
for k, s in enumerate(["RELIEF VALVE", "set " + fmt(P.PROOF_RELIEF_MPA, 1) + " MPa",
                       "before pressurising"]):
    sh.text(XR - 2.0, YL + 34.0 - k * 4.0, s, D.H, ha="center")
XP = 553.0
pump((XP, YL), left=True)
sh.text(XP, YL - 9.5, "PUMP", D.H, ha="center")
sh.line([(566.0, YL), (566.0, 290.0)], THICK)
tank(560.0, 280.0, 580.0, 294.0, 291.0)
sh.text(570.0, 275.5, "WATER", D.H, ha="center")
sh.text(424.0, 284.0, "Gauge, tee, bleed and isolation valves, fittings and hoses:", D.H)
sh.text(424.0, 280.0, "by the test operator (PROCEDURE note 10).", D.H)

# =======================================================================================
# fits and seals (ref), proof schedule
# =======================================================================================
TX = 404.0
sh.text(TX, 268.0, "FITS AND SEALS (ref, from the detail drawings)", 3.5, bold=True)
fits = [["JOINT", "HOLE / BORE (item)", "SHAFT / LAND (item)", "FIT (ref)"],
        ["Case bore / closure lands", "seal zones " + DIA + "A +0.030/0 (1)",
         DIA + "A - " + f2(DL) + " 0/-0.02 (2, 6)",
         "clearance " + f3(CLR[0]) + "-" + f3(CLR[1])],
        ["Case O-ring glands, 4", "groove " + DIA + "A - " + f2(DG) + " 0/-0.04\n"
         + TIMES + " " + f2(P.GROOVE_W) + " +0.08/0 (2, 6)", P.ORING_DASH + " (13)",
         f"squeeze {100 * SQ:.1f} %"],
        ["Holder bore / dummy OD", DIA + f2(P.INSERT_BORE_D) + " +0.025/0 (2)",
         DIA + f2(P.INSERT_OD) + " 0/-0.05 (17)", "clearance " + f3(ICLR[0]) + "-" + f3(ICLR[1])],
        ["Insert gland", "groove " + DIA + f2(P.INSERT_GROOVE_D) + " +0.05/0\n" + TIMES + " "
         + f2(P.INSERT_GROOVE_W) + " +0.08/0 (2)", P.INSERT_ORING_DASH + " (14)",
         f"squeeze {100 * ISQ:.1f} %"],
        ["Seat depth / dummy length", "seat " + f2(SEAT) + " +0.05/0 (2)",
         f2(SEAT) + " 0/-0.05 (17)", "0-" + f2(FLUSH_MAX) + " below face"],
        ["Screw holes, 2 " + TIMES + " 18", DIA + f2(P.CASE_HOLE_D) + " +0.03/0 (1)",
         "M6 tapped (2, 6)", "match-drilled pair"]]
yt = sh.table(TX, 264.0, [47.0, 49.0, 44.0, 40.0], fits, row_h=5.2)
for k, s in enumerate([
        "A = the smallest reading in each seal zone of item 1, " + f3(P.CASE_ID) + "-"
        + f3(P.SEAL_A_MAX) + ", zone A +" + f3(P.TOL_BORE[1]) + "/0 (so " + "≤" + " "
        + f2(P.CASE_BORE_MAX) + "), per zone:",
        "SRM100-101 R4. Items 2 and 6 are cut to their own end's A; at A = " + f3(P.CASE_ID)
        + ": land " + DIA + f2(P.PLUG_OD) + ", groove " + DIA + f2(P.ORING_GROOVE_D) + "."]):
    sh.text(TX, yt - 4.0 - 4.0 * k, s, D.H)

# the schedule starts below the right-hand centring mark (y 210, 5 mm into the field)
sh.text(TX, yt - 17.0, "PROOF SCHEDULE (medium: water)", 3.5, bold=True)
sched = [["STEP", "PRESSURE", "HOLD", "ACCEPT THE HOLD IF"]]
tags = ["", " = MEOP", " = " + fmt(P.PROOF_X_MEOP, 1) + " " + TIMES + " MEOP"]
for k, (p, t) in enumerate(zip(P.PROOF_STEPS_MPA, tags), 1):
    sched.append([str(k), f"{p:.1f}" + " MPa" + t, fmt(P.PROOF_HOLD_S, 0) + " s",
                  "decay " + "≤" + " " + fmt(100 * P.PROOF_DECAY_MAX, 0)
                  + " % over the hold, no visible leak or weep"])
ys = sh.table(TX, yt - 21.0, [12.0, 42.0, 14.0, 112.0], sched, row_h=5.2,
              align=["c", "l", "r", "l"])
sh.text(TX, ys - 5.0, "Relief valve set " + fmt(P.PROOF_RELIEF_MPA, 1) + " MPa before "
        "pressurising. Proof " + fmt(P_PROOF, 1) + " MPa = " + fmt(P.PROOF_X_MEOP, 1) + " "
        + TIMES + " MEOP " + f"{P.MEOP:.1f}" + " MPa.", D.H)
sh.text(TX, ys - 14.0, "AFTER THE TEST", 3.5, bold=True)
acc = [["CHECK", "ACCEPT / ACTION"],
       ["Case OD at stations S1 ... S5\n(SRM100-101 R9), before / after",
        "accept a permanent set " + "≤" + " " + f2(P.PROOF_SET_MAX) + " mm at every station"],
       ["Every bolt hole (2 " + TIMES + " 18), against\nits baseline (SRM100-101 R7)",
        "retire the end if any hole's axial length has grown, or its ligament\nhas "
        "shrunk, by more than " + f2(HOLE_CHG_MAX) + " mm from that hole's own baseline"],
       ["Case ends, after the first proof", "hardness / conductivity baseline, SRM100-101 R8 "
        "(PROCEDURE note 7)"]]
ya = sh.table(TX, ys - 18.0, [62.0, 118.0], acc, row_h=5.2)

# ---- parts list (ISO 7573: above the title block, header at the bottom) ---------------
PW = [10.0, 9.0, 38.0, 50.0, 49.0, 24.0]
rows = [[str(i), str(q), pn, d, m, f"{MB_G[k]:.1f}"] for i, q, pn, d, m, k in sorted(ITEMS, reverse=True)]
n_extra = sum(len(r[4].split("\n")) - 1 for r in rows)          # two-line material cells
ytop = sh.tb[3] + 9 * 5.2 + 1.0 + n_extra * D.H * 1.5
yb2 = sh.table(sh.tb[0], ytop, PW, rows, header=0, row_h=5.2,
               align=["c", "c", "l", "l", "l", "r"])
sh.table(sh.tb[0], yb2, PW, [["ITEM", "QTY", "PART NUMBER", "DESCRIPTION", "MATERIAL",
                              "MASS EACH g"]], header=1, row_h=yb2 - sh.tb[3],
         align=["c", "c", "l", "l", "l", "r"])
sh.text(sh.tb[0], ytop + 10.5, f"Mass {MASS:.1f} g, water not included: sum of qty " + TIMES
        + " unrounded mass each. Items 1, 2, 6, 13-16", D.H)
sh.text(sh.tb[0], ytop + 6.5, "from out/mass_budget.json; item 17 from its STEP, adaptive "
        "BRepGProp volume " + TIMES + " " + f"{P.SS_RHO * 1e6:.2f}" + " g/cm" + "³" + ".", D.H)
sh.text(sh.tb[0], ytop + 2.5, "Tooling (hole plugs, push sleeve, puller bridge, clamp collar) "
        "is not listed.", D.H)

# =======================================================================================
# notes
# =======================================================================================
asm = [
    "Build list: the flight case item 1, both closures (items 2, 6), all five O-rings "
    "(4 " + TIMES + " item 13, item 14) and all 36 screws (items 15, 16), with proof dummy item 17 "
    "in the insert's gland. No graphite insert item 3 (it must stay dry; a cracked one is "
    "scrap), no insulators, liner, grain or cap: nothing inside the case.",
    "Each closure goes to its own case end: match-drilled, serialised pair. " + THETA + "0: on "
    "the case, hole 0, the clocking line scribed across the pair and the AFT / FWD marking; "
    "on each closure, puller P1 at " + THETA + " " + fmt(PTH[0], 0) + DEG + " (item 2 r "
    + fmt(P.HOLDER_PULLER_R, 0) + ", item 6 r " + f1(P.PULLER_R) + "). Hole 0 is at "
    + fmt(TH[0], 1) + DEG + ", " + fmt(PTH[0] - TH[0], 1) + DEG + " clockwise of P1 seen from "
    "forward (counter-clockwise seen from aft).",
    "O-rings items 13, 14: FKM 90A, Parker V0709-90 or equal. Lube: " + P.LUBE + ". Fit item "
    "14 in item 2's bore groove, then 2 " + TIMES + " item 13 in each closure's land grooves. "
    "Items 2 and 6 are cut to their own case end's bore A (fits table).",
    "Slide item 17 into item 2 by hand, aft end first, until it seats on the lip. Never "
    "press or knock it (view B). Check: its forward face lies flush with item 2's forward "
    "face to " + f2(FLUSH_MAX) + " below it.",
    "Hole plugs (tooling): before each closure goes in, push 18 flat-ended acetal plugs, "
    + DIA + "6.35 " + TIMES + " 3.85 with an outside head, into that end's holes; their ends "
    "sit about 0.15 mm shy of the bore, so no O-ring is dragged across an open hole edge. "
    "Pull each plug as its screw goes in.",
    "Enter each closure at its own end (item 2 AFT, item 6 FWD) with its hole 0 on the "
    "case's hole 0 and clocking line, until its flange butts on the case end face: zero gap.",
    "Torques as for flight. Aft: 18 " + TIMES + " item 15 into item 2 (304), " + TQS_A
    + ", nickel anti-seize on the threads only, head face dry. Forward: 18 " + TIMES
    + " item 16 into item 6 (6061), " + TQS_F + ", Loctite 243. Criss-cross, in the boxed "
    "order of SRM100-000 sheet 2 (aft) / sheet 3 (fwd), 3 passes: about half the minimum "
    "torque (" + f1(TQA[0] / 2) + " / " + f1(TQF[0] / 2) + " " + NM + "), then to torque, "
    "then a check pass hole by hole round the circle. Do not mix the lengths: an M6" + TIMES
    + "16 in the holder bottoms with its head proud; an M6" + TIMES + "10 in the forward "
    "closure engages only 1 d.",
    "Before the first proof, record the hole baseline of all 36 case holes (SRM100-101 "
    "record R7), keyed to the serialised pair: the axial length of each hole, and the "
    "ligament from the case end face to the hole edge (nominal " + f1(P.BOLT_EDGE) + " - "
    + f1(P.CASE_HOLE_D / 2) + " = " + f2(LIG) + "). Each hole is judged against its own "
    "baseline only, never an absolute ligament limit (SRM100-101 R7).",
    "Mark the case OD stations S1 ... S5 with removable tape and record the OD at each "
    "before the test: stations, directions and micrometer per SRM100-101 record R9.",
    "Disassembly, never lever or knock: split clamp collar (100.0 bore) on the case OD at "
    "least " + fmt(COLLAR_MIN, 0) + " mm from the end being extracted (both ends), clear of "
    "the screw heads at z " + fmt(P.BOLT_EDGE, 0) + " (" + DIA + f2(2 * R_SWEEP) + " sweep, "
    "ref), the labels and the marking at z " + fmt(MARK_Z[0], 0) + "-" + fmt(MARK_Z[1], 0)
    + " (z from that end face); bridge and 2 " + TIMES + " M6 draw screws "
    "in the closure's puller threads, 2 " + TIMES + " " + M6 + " at " + THETA + " "
    + fmt(PTH[0], 0) + DEG + " and " + fmt(PTH[1], 0) + DEG + " (item 2 r "
    + fmt(P.HOLDER_PULLER_R, 0) + ", item 6 r " + f1(P.PULLER_R) + "). Item 17 comes out of "
    "item 2 as the insert does: holder on its forward face in an arbor press, push sleeve "
    "through the lip bore.",
    "USED ON: SRM-100 motor (Helios) - proof before the first firing and after any repair.",
]
proof = [
    "Medium: water. Proof pressure " + fmt(P_PROOF, 1) + " MPa = " + fmt(P.PROOF_X_MEOP, 1)
    + " " + TIMES + " MEOP (" + f"{P.MEOP:.1f}" + " MPa).",
    "Water-fill with the motor vertical, AFT END UP: item 17's 1/8-27 NPT port (view B) is "
    "the motor's only port (item 6 has none) and its cup floor the cavity's highest point. "
    "Items 2 and 17 make one flat ceiling at z " + fmt(Z_CEIL, 1) + ", so tilting would "
    "drive bubbles out to the bore: fill from the bottom instead (SET-UP schematic). Pass a "
    + DIA + fmt(P.PROOF_DIP_TUBE_OD) + " " + TIMES + " " + fmt(P.PROOF_DIP_TUBE_L) + " PE or "
    "nylon dip tube, end cut at 45" + DEG + ", down the port and the " + DIA
    + fmt(P.PROOF_PASSAGE_D) + " passage to rest on item 6's inboard face; fill slowly so "
    "the water rises level. Withdraw it, top up until the port overflows, fit the rig tee (bleed valve "
    "on top, pump line on the side branch), pump slowly with the bleed open until only "
    "water comes out, then close it. Trapped air is stored energy.",
    "Set the pump's relief valve to " + fmt(P.PROOF_RELIEF_MPA, 1) + " MPa before "
    "pressurising. Stand behind a barrier while the motor is under pressure.",
    "Pressurise in steps " + " → ".join(f"{p:.1f}" for p in P.PROOF_STEPS_MPA)
    + " MPa, holding " + fmt(P.PROOF_HOLD_S, 0) + " s at each. Accept a hold if the "
    "pressure decays ≤ " + fmt(100 * P.PROOF_DECAY_MAX, 0) + " % over it and there is "
    "no visible leak or weep.",
    "Measure the case OD at the marked stations (S1 ... S5, SRM100-101 record R9) before "
    "and after. Accept a permanent set ≤ " + f2(P.PROOF_SET_MAX) + " mm at every station.",
    "Re-gauge every bolt hole against its baseline (SRM100-101 record R7). Retire the end if "
    "any hole's axial length has grown by more than " + f2(HOLE_CHG_MAX) + " mm, or its "
    "ligament has shrunk by more than " + f2(HOLE_CHG_MAX) + " mm, from that hole's own "
    "baseline.",
    "After the first proof, take the hardness / conductivity baseline on each case end "
    "(SRM100-101 record R8): HRB or Webster B, and eddy-current %IACS, at " + THETA + " "
    + ", ".join(fmt(t, 0) + DEG for t in HAZ) + " (between the holes); aft end z "
    + fmt(HZ[0], 0) + "-" + fmt(HZ[1], 0) + " and z " + fmt(HREF, 0) + ", fwd end z "
    + f1(P.CASE_L - HZ[1]) + "-" + f1(P.CASE_L - HZ[0]) + " and z " + f1(P.CASE_L - HREF)
    + ". 6061-T6 reference: about 95 HB (about 60 HRB), Webster B ≥ 15, 40-46 %IACS. Later "
    "readings on the same instrument and scale; after a firing, retire the end if > 46 "
    "%IACS or hardness more than 10 % below this baseline (SRM100-101 R10).",
    "Re-proof after any repair, any retired-and-replaced part, or a temperature label "
    "reading ≥ 232 " + DEG + "C.",
    "Record against the serials of the case / closure pair and of item 17: the step "
    "pressures and hold decays; the OD before and after, the hole gauging and the hardness "
    "baseline on the SRM100-101 records R9, R7 and R8.",
    "Rig tee into item 17's 1/8-27 NPT port (ASME B1.20.1): Loctite 567 or equal on the "
    "male thread, first 2 threads clear; no PTFE tape. By the test operator, not defined "
    "in the design data: "
    "gauge range and accuracy, the isolation valve that holds the pump off during the "
    "holds, valves, fittings and hoses, water quality and temperature, drain and dry-out.",
    "After the test: drain through item 17's port, motor aft end down (or siphon out "
    "through the dip tube), then strip (PROOF BUILD note 10) and dry. Item 2's bore and gland "
    "must be dry before the graphite insert goes in. The flight build takes new O-rings "
    "and screws (items 13-16); the full replace / re-use list for every firing is on "
    "SRM100-000 sheet 2.",
]
NY = 176.0
sh.notes(23.0, NY, asm, 184.0, title="PROOF BUILD")
sh.notes(214.0, NY, proof, 186.0, title="HYDROSTATIC PROOF - PROCEDURE AND ACCEPTANCE")

if __name__ == "__main__":
    sh.lint()
    sh.save("proof_assembly")
