"""SRM100-111 casting tube (spiral-wound kraft): A3, 1:1 half-section, detail C (10:1)
of the wall at the aft end.

View frame: u = the tube's local z (z = 0 at the segment's AFT face, as grain.py),
v = radius.  Four instances, at motor z = P.grain_z(i).
Datum A = the OD axis (the OD slides in the liner bore).
The 0.8 wall is a thin section: solid black at 1:1 (ISO 128-50); the detail is
drawn hatched (the part's hatch is swapped after the main view is drawn).
Local primitives: finish_any() (ISO 1302 'any process' symbol on a leader),
general_finish_iso() (basic symbol in the parentheses).
"""

import math

import numpy as np

import srm_dwg as D
import srm_params as P
from srm_dwg import DIA, DEG, TIMES, PM, Hatch, Part, Sheet, View, fmt

R_OD = P.TUBE_OD / 2.0           # 44.2
R_ID = P.TUBE_ID / 2.0           # 43.4 (= grain OD / 2)
L = P.GRAIN_L                    # 147.2
MASS = 30.8
OD_TOL = (0.0, -0.1)
ID_TOL = PM + "0.1"
L_TOL = PM + fmt(P.TOL_GRAIN_L)  # the grain's length tolerance, srm_params
LINER_ID_TOL = (0.1, 0.0)        # SRM100-110


def tol_s(t):
    return tuple(("+" if x > 0 else "") + fmt(x, 3) for x in t)


def finish_any(v, at, value, leader):
    """ISO 1302 basic symbol (any process) on a leader from view point `at` (local:
    View.finish is hard-wired to 'material removal required')."""
    s = v.sheet
    p = v.pt(*at)
    q = p + np.array(leader, float)
    s.line([p, q], D.THIN)
    s.arrow(p, p - q)
    t60 = math.tan(math.radians(60))
    sg = 1.0 if leader[0] >= 0 else -1.0
    w = 7.5 / t60 + s.text_width(value, D.H) + 1.5 + 3.5 / t60
    s.line([q, q + (sg * (w + 2.0), 0)], D.THIN)
    s.finish_symbol(q + (sg * 2.0 + (0 if sg > 0 else -w), 0), value, removal=False)


def general_finish_iso(s, x, y, value):
    """ISO 1302 general requirement next to the title block: the general symbol
    (material removal: the cut ends) with its value, then the BASIC symbol in
    parentheses ('other requirements as indicated').  Local: Sheet.general_finish
    puts a removal symbol in the parentheses."""
    w = s.finish_symbol((x + 2.2, y), value, removal=True)
    xx = x + w + 4
    s.text(xx, y + 2.0, "(", 5.0)
    s.finish_symbol((xx + 3.6, y + 0.8), "", removal=False, small=True)
    s.text(xx + 7.0, y + 2.0, ")", 5.0)


sh = Sheet("SRM100-111", "CASTING TUBE", "Grain casting tube / OD inhibitor, "
           + DIA + fmt(P.TUBE_OD) + " / " + DIA + fmt(P.TUBE_ID) + " x " + fmt(L) + " - kraft",
           size="A3", material="Spiral-wound kraft paper tube\nstock ID 86.8 x 0.8 wall",
           mass_g=MASS, scale="1:1", finish="Ra 6.3", edges="ISO 13715  -0.2")

part = Part("casting_tube.step", hatch=Hatch(solid=True))
X0, Y0 = 72.0, 200.0
v = View(sh, part, (X0, Y0), 1.0, look="side", section="half")

# length (= grain length), OD + datum A, ID
v.dim_h((0.0, R_OD), (L, R_OD), off=16.0, tol=L_TOL)
v.dim_dia(0.0, R_OD, at=-13.0, tol=tol_s(OD_TOL), arrows=(False, True))
v.datum((-13.0, -R_OD), "A", (0, -1), length=5.0)
U_ID = 52.0
v.dim_dia_half(U_ID, R_ID, at=U_ID, tol=ID_TOL)
v.fcf((U_ID, -3.0), 7.0, -15.0, ["coaxiality", DIA + "0.1", "A"])

# end faces: bearing faces in the stack, square to A
v.fcf((0.0, -30.0), 8.0, -3.25, ["perpendicularity", "0.1", "A"])
v.fcf((L, -30.0), -27.5, -3.25, ["perpendicularity", "0.1", "A"])

# surface texture: OD and bore as wound (any process); the cut ends take the general
sh.finish_symbol(v.pt(100.0, R_OD), "Ra 6.3", removal=False)
finish_any(v, (112.0, R_ID), "Ra 6.3", (-6.0, -12.0))

# the OD is the grain's inhibitor: indicate it
v.leader((L - 30.0, -R_OD), 10.0, -12.0,
         ["OD / BORE CONTINUOUS: NO HOLES,", "OPEN SEAMS OR SPLITS (NOTE 2)"])

# detail C: the wall at the aft end, hatched
part.hatch = Hatch(45, 2.0)
C = (1.1, 0.5 * (R_OD + R_ID))
c = v.detail(C, 2.6, 10.0, (122.0, 98.0), "C", circle_label_ang=62.0)
c.dim_v((0.0, R_ID), (0.0, R_OD), at=C[0] + 3.4, ref=True)
c.leader((0.0, R_OD - 0.25), -14.0, 12.0, ["END CUT SQUARE, CLEAN,", "NO FRAYING (NOTE 6)"])
c.leader((2.6, R_ID), 16.0, -16.0, ["BORE: GRAIN OD", "(SRM100-112)"])

# ---- fit / position table ------------------------------------------------------------
TX, TY = 262.0, 158.0
sh.text(TX, TY + 4.0, "FIT AND POSITION", 3.5)
lo, hi = P.TUBE_OD + OD_TOL[1], P.TUBE_OD + OD_TOL[0]
b_lo, b_hi = P.LINER_ID + LINER_ID_TOL[1], P.LINER_ID + LINER_ID_TOL[0]
rows = [["ITEM", "VALUE"],
        ["Liner SRM100-110 bore", DIA + f"{b_lo:.2f} ... {b_hi:.2f}"],
        ["Tube OD in liner bore", f"clearance {b_lo - hi:.2f} ... {b_hi - lo:.2f} (diametral)"],
        ["Case bore SRM100-101", "no contact: the liner wall is between"],
        ["Bore = grain SRM100-112 OD", DIA + fmt(P.GRAIN_OD) + " " + PM + "0.1, cast in place"],
        ["Aft face, motor z (tubes 1 ... 4)",
         " / ".join(fmt(P.grain_z(i), 1) for i in range(P.N_GRAINS))],
        ["Ends bear on", "grain spacers SRM100-109"]]
sh.table(TX, TY, [62, 64], rows, align=["l", "l"])

# ---- notes ------------------------------------------------------------------------
NX = 262.0
notes = [
    "Material: spiral-wound kraft paper tube, plain kraft (not phenolic-impregnated), wall "
    "0.8, density approx. 0.95 g/cm³. Stock: tube bought to the drawn bore and wall, cut "
    "to length. Plies bonded over their full area. Certificate of conformity required.",
    "Propellant grain SRM100-112 is cast into this tube and stays in it: the tube is the "
    "grain's OD inhibitor. It must be continuous: no holes, open or overlapping seams, "
    "splits, blisters, delamination, dents or crushed ends. Inspect against a light.",
    "Bore clean and dry: free of oil, wax, dust and loose fibres. OD free of raised "
    "seams and adhesive lumps.",
    "Datum A is the OD axis. Sizes are two-point sizes at 20 °C on a tube conditioned "
    "dry (sealed with desiccant ≥ 24 h): kraft swells with humidity. Store sealed.",
    "Length = grain length. In the finished segment the tube ends are flush with the "
    "grain end faces within 0.1 (SRM100-112).",
    "Edges drawn sharp: ends cut square and clean, edge break 0.2 max, no burr or "
    "fraying. The ends bear on the grain spacers.",
    "OD, also after the grain is cast in it, must pass freely over its full length "
    "through a " + DIA + f"{P.LINER_ID:.2f}" + " ring gauge (liner SRM100-110 bore min).",
    "Inspect 100 %: OD and bore at both ends, 2 directions 90° apart; length at 4 "
    "positions 90° apart; visual inside and out. Record per batch.",
    "Mark SRM100-111 and batch on the OD within 20 of one end: indelible ink, 3 mm "
    "characters. The grain marking (SRM100-112) goes on the same OD.",
    "Used on SRM100-000 item 9 (4 off), one per grain SRM100-112 (item 10). Single use: "
    "replaced with its grain after every firing (README, After every firing).",
]
sh.notes(NX, 282.0, notes, 146.0)
general_finish_iso(sh, sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 6.3")

if __name__ == "__main__":
    sh.lint()
    sh.save("casting_tube")
