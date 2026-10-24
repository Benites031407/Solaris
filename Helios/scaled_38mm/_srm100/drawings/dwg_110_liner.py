"""SRM100-110 liner (paper phenolic): A3, 1:1 broken half-section, detail C (10:1) of
the aft end, fit table.

View frame: u = the liner's local z (z = 0 at its AFT end, forward to the right),
v = radius.  The liner is placed at motor z = P.Z_LINER_AFT (srm_assembly), so a
motor station is local u + Z_LINER_AFT.
Datum A = the OD axis (the OD slides in the case bore).  The length is a reference
value: the liner is cut at assembly to the measured cavity (README Build step 3).

Local primitives (the kit has no equivalent): dim_across() for a length dimension
across a broken view, finish_any() for an ISO 1302 'any process' symbol on a leader,
general_finish_iso() (basic symbol in the parentheses), para() for a wrapped paragraph.
"""

import math

import numpy as np

import srm_dwg as D
import srm_params as P
from srm_dwg import DIA, DEG, TIMES, PM, Hatch, Part, Sheet, View, fmt

R_OD = P.LINER_OD / 2.0          # 45.8
R_ID = P.LINER_ID / 2.0          # 44.3
L = P.LINER_L                    # 606.3
CAVITY = P.Z_FWD_INSUL_AFT - P.Z_LINER_AFT       # 606.8, nominal cavity C
MASS = 347.5

# tolerances of this sheet (the fits below are computed from them)
OD_TOL = (0.0, -0.1)
ID_TOL = (0.1, 0.0)
LEN_TOL = (0.0, -0.1)            # on L = C - LINER_FLOAT
STRAIGHT = 0.1                   # axis straightness at MMC (virtual size = OD max + 0.1)
MMC = "Ⓜ"                   # (M): ISO 1101 maximum material requirement modifier
# mating parts' tolerances, as drawn on their own sheets (read-only here)
TUBE_OD_TOL = (0.0, -0.1)        # SRM100-111
SPACER_OD_TOL = (0.0, -0.1)      # SRM100-109
TAKEUP_OD_TOL = (0.0, -0.4)      # SRM100-108 (sponge, free state)
CASE_SL_STRAIGHT = 0.3           # SRM100-101: bore surface lines straight within 0.3
CASE_GO_PLUG = 91.70             # SRM100-101: GO plug that passes the full bore length
CASE_HONE = 45.0                 # SRM100-101: honed seal zone, 45 +5/0 from each end face
# G1-rev: the honed seal zones are A +0.030/0 with CASE_ID <= A <= SEAL_A_MAX (recorded
# per zone on SRM100-101), so no zone passes CASE_BORE_MAX: the bore is CASE_ID ...
# CASE_BORE_MAX everywhere, zones included, and the liner fit is stated over that range.
BORE_MIN, BORE_MAX = P.CASE_ID, P.CASE_BORE_MAX                   # 92.000 ... 92.10
A_MAX, A_TOL = P.SEAL_A_MAX, P.TOL_BORE[1]                        # 92.070, +0.030/0
assert A_MAX + A_TOL <= BORE_MAX + 1e-9                           # zone max A + 0.030 <= 92.10
VC_LINER = P.LINER_OD + OD_TOL[0] + STRAIGHT                      # 91.70
assert abs(VC_LINER - (P.CASE_ID - CASE_SL_STRAIGHT)) < 1e-9       # = smallest straight bore
assert abs(VC_LINER - CASE_GO_PLUG) < 1e-9


def _case_sheet_values():
    """SRM100-101's surface-line straightness, GO plug and hone length as written in
    dwg_101_case.py (read as text, not imported: importing it would draw that sheet).
    Every occurrence must equal this sheet's copy, or the asserts above are stale."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parent / "dwg_101_case.py").read_text(encoding="utf-8")
    num = r"(\d+(?:\.\d+)?)"                     # a number, not a sentence's full stop
    found = {
        "straightness": re.findall(r'"straightness",\s*"' + num, src)
        + re.findall(r"straight within " + num, src),
        "GO plug": re.findall(r'GO plug " \+ DIA \+ "' + num, src),
        "HONE": re.findall(r"^HONE\s*=\s*" + num, src, re.M),
    }
    ours = {"straightness": CASE_SL_STRAIGHT, "GO plug": CASE_GO_PLUG, "HONE": CASE_HONE}
    for k, vals in found.items():
        assert vals, f"dwg_101_case.py: no {k} value found; re-check SRM100-110's copy"
        assert all(abs(float(x) - ours[k]) < 1e-9 for x in vals), (k, vals, ours[k])


_case_sheet_values()


def tol_s(t):
    return tuple(("+" if x > 0 else "") + fmt(x, 3) for x in t)


# ---- local primitives ------------------------------------------------------------
def dim_across(va, a, vb, b, y, tol=None, ref=False):
    """Horizontal dimension from view point a on view `va` to view point b on view `vb`
    (the two halves of a broken view), line at paper y.  The value is |b.u - a.u| in
    model mm: the true length across the break."""
    val = fmt(abs(b[0] - a[0]))
    if ref:
        val = f"({val})"
    return va._linear(va.pt(*a), vb.pt(*b), (1, 0), (0, y), val, tol)


def finish_any(v, at, value, leader):
    """ISO 1302 basic symbol (any process) on a leader from view point `at`."""
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


def para(s, x, y_top, text, width, h=D.H, gap=1.55):
    """Plain paragraph wrapped on measured text widths; returns the y below it."""
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if cur and s.text_width(t, h) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    y = y_top - h
    for ln in lines:
        s.text(x, y, ln, h)
        y -= h * gap
    return y


# ---- sheet -----------------------------------------------------------------------
sh = Sheet("SRM100-110", "LINER", "Case liner / thermal barrier, "
           + DIA + fmt(P.LINER_OD) + " / " + DIA + fmt(P.LINER_ID) + " - paper phenolic",
           size="A3", material="Paper-base phenolic tube\nNEMA LI 1 grade X / XX or equal",
           mass_g=MASS, scale="1:1", finish="Ra 6.3")

part = Part("liner.step", hatch=Hatch(45, 1.0))
UA = 80.0                         # aft piece: u 0 .. UA
UF = L - 80.0                     # forward piece: u UF .. L
X0, Y0 = 56.0, 196.0              # paper position of the aft end, on the axis
GAP = 12.0
va = View(sh, part, (X0, Y0), 1.0, look="side", section="half", axis=False,
          window=(-3.0, -50.0, UA, 50.0))
vf = View(sh, part, (X0 + UA + GAP - UF, Y0), 1.0, look="side", section="half", axis=False,
          window=(UF, -50.0, L + 3.0, 50.0))
va.zigzag((UA, -R_OD), (UA, R_OD))
vf.zigzag((UF, -R_OD), (UF, R_OD))
# one continuous centre line across the break
sh.line([va.pt(-4.0, 0), vf.pt(L + 4.0, 0)], D.THIN, "center")

# length: reference, cut to the measured cavity (note 3)
yl = Y0 + R_OD + 16.0
dim_across(va, (0.0, R_OD), vf, (L, R_OD), yl, ref=True)
xm = (va.pt(0, 0)[0] + vf.pt(L, 0)[0]) / 2
wl = va._dimtext((xm - 9.0, yl - 5.6), 0.0, "L = C - " + fmt(P.LINER_FLOAT, 1), tol_s(LEN_TOL))
sh.text(xm - 9.0 + wl / 2 + 1.5, yl - 5.6, "(NOTE 3)")

# OD, datum A, straightness of the axis
va.dim_dia(0.0, R_OD, at=-12.0, tol=tol_s(OD_TOL), arrows=(False, True))
va.datum((-12.0, -R_OD), "A", (0, -1), length=5.0)
p_top = va.pt(-12.0, R_OD)
sh.fcf(p_top[0] - 10.0, p_top[1] + 4.0, ["straightness", DIA + fmt(STRAIGHT, 1) + " " + MMC],
       leader=p_top)

# ID: half dimension through the axis, coaxial to A
U_ID = 46.0
va.dim_dia_half(U_ID, R_ID, at=U_ID, tol=tol_s(ID_TOL))
va.fcf((U_ID, -3.0), 7.0, -15.0, ["coaxiality", DIA + "0.1", "A"])

# end faces square to A
va.fcf((0.0, -30.0), 8.0, -3.25, ["perpendicularity", "0.1", "A"])
vf.fcf((L, -30.0), -27.5, -3.25, ["perpendicularity", "0.1", "A"])

# surface texture: OD (standing on it), bore (leader from inside)
sh.finish_symbol(vf.pt(UF + 22.0, R_OD), "Ra 3.2", removal=False)
finish_any(vf, (UF + 50.0, R_ID), "Ra 3.2", (-6.0, -12.0))

# detail C: aft end, wall and edges
C = (0.7, 0.5 * (R_OD + R_ID))
c = va.detail(C, 2.6, 10.0, (76.0, 98.0), "C", circle_label_ang=62.0)
c.dim_v((0.0, R_ID), (0.0, R_OD), at=C[0] + 3.4, ref=True)
c.leader((0.0, R_OD), -12.0, 9.0, ["0.5" + TIMES + "45" + DEG])
c.leader((0.0, R_ID), -12.0, -9.0, ["0.3" + TIMES + "45" + DEG])

# ---- fit table ---------------------------------------------------------------------
TX, TY = 118.0, 136.0
sh.text(TX, TY + 4.0, "FITS (DIAMETRAL CLEARANCE)", 3.5)
od_lo, od_hi = P.LINER_OD + OD_TOL[1], P.LINER_OD + OD_TOL[0]
id_lo, id_hi = P.LINER_ID + ID_TOL[1], P.LINER_ID + ID_TOL[0]


def shaft_row(name, nom, tol):
    lo, hi = nom + tol[1], nom + tol[0]
    return [name, DIA + f"{id_lo:.2f} ... {id_hi:.2f}", DIA + f"{lo:.2f} ... {hi:.2f}",
            f"{id_lo - hi:.2f} ... {id_hi - lo:.2f}"]


rows = [["MATING PART", "BORE", "SHAFT", "CLEARANCE"],
        ["Liner OD in case bore\nSRM100-101, full length",
         DIA + f"{BORE_MIN:.3f} ... {BORE_MAX:.2f}", DIA + f"{od_lo:.2f} ... {od_hi:.2f}",
         f"{BORE_MIN - od_hi:.2f} ... {BORE_MAX - od_lo:.2f}"],
        shaft_row("Casting tube SRM100-111\nin liner bore", P.TUBE_OD, TUBE_OD_TOL),
        shaft_row("Grain spacer SRM100-109\nin liner bore", P.SPACER_OD, SPACER_OD_TOL),
        shaft_row("Take-up ring SRM100-108\nin liner bore", P.TAKEUP_OD, TAKEUP_OD_TOL)]
yb = sh.table(TX, TY, [46, 30, 30, 24], rows, align=["l", "c", "c", "c"])
NB = " "                                   # no-break space: para() splits on " " only
OVL_AFT = CASE_HONE - P.Z_LINER_AFT                        # 2.0
OVL_FWD = P.Z_LINER_FWD - (P.CASE_L - CASE_HONE)            # 3.5
para(sh, TX, yb - 2.0,
     "Both liner ends lie in the honed seal zones of SRM100-101 (" + fmt(CASE_HONE, 0)
     + " +5/0 from each case end face: overlap ≥ " + fmt(OVL_AFT, 1) + " aft, ≥ "
     + fmt(OVL_FWD, 1) + " fwd), held to A +" + f"{A_TOL:.3f}" + "/0 with "
     + f"{BORE_MIN:.3f}{NB}≤{NB}A{NB}≤{NB}{A_MAX:.3f}" + ", A recorded per zone: the bore "
     "is ≤ " + f"{BORE_MAX:.2f}" + " everywhere, zones included, so the clearance "
     + f"{BORE_MIN - od_hi:.2f}{NB}...{NB}{BORE_MAX - od_lo:.2f}" + " holds over the "
     "full length. Straightness " + DIA + fmt(STRAIGHT, 1) + NB + MMC
     + ": liner virtual size " + DIA + f"{VC_LINER:.2f}" + " = smallest straight case bore, "
     "GO plug " + DIA + f"{CASE_GO_PLUG:.2f}" + " (bore min" + NB + f"{BORE_MIN:.3f}" + ", surface "
     "lines straight within " + fmt(CASE_SL_STRAIGHT, 1) + ", SRM100-101).", 132.0)

# ---- notes ------------------------------------------------------------------------
NX = 262.0
notes = [
    "Material: phenolic-impregnated kraft paper tube, convolute or spiral wound; paper-base "
    "phenolic to NEMA LI 1 grade X / XX or equal, density approx. 1.35 g/cm³. Stock: tube "
    "bought to the drawn OD and bore, or OD ground / bore honed from an oversize tube; "
    "supply length ≥ 612. Free of delamination, blisters, soft spots and cracks. "
    "Certificate of conformity required.",
    "Datum A is the OD axis. Sizes are two-point sizes at 20 °C on a tube conditioned "
    "dry (sealed with desiccant ≥ 24 h): paper phenolic swells with humidity. Store sealed.",
    f"Length L is cut at assembly to the measured cavity C, nozzle-insulator forward face "
    f"to forward-insulator aft face (SRM100-000): L = C - {fmt(P.LINER_FLOAT, 1)} 0/-0.1. "
    f"({fmt(L)}) is L at the nominal C = {fmt(CAVITY)}. The liner carries no axial load: "
    f"before the forward closure goes in, the depth from the case forward end face to the "
    f"liner forward end must be ≥ t + 0.30 at 4 points, t = closure flange bearing face "
    f"to forward-insulator aft face (SRM100-000 sheet 3, note 8).",
    "Edges drawn sharp. Break both OD end edges 0.5x45° (protects the honed seal zones "
    "of SRM100-101 when the liner is pushed in) and both bore end edges 0.3x45°. Cut "
    "ends clean: no loose fibres, no crushed or split ends.",
    "Clean and dry inside and out before assembly. Grease the OD at assembly: "
    + P.LUBE + "; no grease in the bore. Must slide by hand through case SRM100-101 "
    "over its full length. Casting tubes, spacers and take-up ring must slide freely in "
    "the bore.",
    "Inspect 100 %: OD and bore at both ends and mid-length, 2 directions 90° apart; "
    "wall ≥ 1.35 at 4 positions each end; straightness " + DIA + fmt(STRAIGHT, 1) + " "
    + MMC + ": a full-length sleeve gauge " + DIA + f"{VC_LINER:.2f}" + " passes over "
    "the OD by hand; length at 4 positions 90° apart after cutting. Visual inside and "
    "out. Record with the case serial.",
    "Mark SRM100-110, batch and the serial of the case it is cut for on the OD, within "
    "30 of one end: indelible ink, 3 mm characters. Do not engrave or stamp.",
    f"Installed from motor z {fmt(P.Z_LINER_AFT, 1)} (bears on nozzle insulator "
    f"SRM100-105) to z {fmt(P.Z_LINER_FWD, 1)}; the forward end floats "
    f"{fmt(P.LINER_FLOAT, 1)} short of forward insulator SRM100-107.",
    "Used on SRM100-000 item 8 (1 off). Single use: replaced after every firing "
    "(README, After every firing).",
]
sh.notes(NX, 282.0, notes, 146.0)
general_finish_iso(sh, sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 6.3")

if __name__ == "__main__":
    sh.lint()
    sh.save("liner")
