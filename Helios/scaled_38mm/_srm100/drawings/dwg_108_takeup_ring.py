"""SRM100-108 take-up ring (closed-cell silicone sponge): A4 portrait detail drawing.

End view 1:1 (the cutting profile, = takeup_ring.dxf), SECTION A-A 1:1 in the FREE
state (as cut from the sheet), installed position 5:1 (reference, adjacent parts in
phantom) and notes.

The STEP (takeup_ring.step) models the ring at its nominal INSTALLED thickness
TAKEUP_T; the part is cut from TAKEUP_FREE_T sheet.  Section A-A is therefore drawn
from an in-memory solid of the same generator call at the free thickness (the profile
is unchanged); the installed view uses the STEP at its assembly placement.  The
title-block mass is the STEP (installed volume) at srm_verify's 0.50 g/cm3; note 7 gives
the as-cut mass (free volume x the certified 0.30 - 0.40 g/cm3) beside it.
Non-rigid part (ISO 10579-NR): dimensions apply in the free state.

View frames: end view look 'fwd' (u = x, v = y); section look 'side' (u = local z,
v = radius); installed view look 'side' in the MOTOR frame (u = motor z).
"""

import json
import math

import srm_dwg as D
import srm_params as P
import srm_verify as V
from srm_build import tube
from srm_dwg import DIA, PM, Hatch, Part, Sheet, View, fmt

import dwg_10x_flat_common as C

MASS = 1.7
R_OD = P.TAKEUP_OD / 2.0                  # 44.2
R_ID = P.TAKEUP_ID / 2.0                  # 40.0
TF = P.TAKEUP_FREE_T                      # 4.8, free (sheet) thickness
TI = P.TAKEUP_T                           # 3.0, installed (STEP)
ZA = P.takeup_z()                         # motor z of the aft face (on spacer 5)
ZF = ZA + TI                              # = Z_FWD_INSUL_AFT
OD_TOL = (0.0, -0.4)
ID_TOL = (0.4, 0.0)
TF_TOL = 0.4
LINER_ID_TOL = (0.1, 0.0)                 # SRM100-110
C_NOM = 1.0 - TI / TF                     # nominal installed compression
GAP_TOL = P.TOL_STACK                     # stack tolerance -> gap tolerance
# fit in the liner (the OD never meets the case bore 92.000 ... 92.10, decision G1)
CLR = (P.LINER_ID + LINER_ID_TOL[1] - (P.TAKEUP_OD + OD_TOL[0]),
       P.LINER_ID + LINER_ID_TOL[0] - (P.TAKEUP_OD + OD_TOL[1]))
AIM = (P.TAKEUP_OD + sum(OD_TOL) / 2.0, P.TAKEUP_ID + sum(ID_TOL) / 2.0)   # mid-tolerance cut
# take-up rule, as SRM100-000 sheet 3 (dwg_000_sh3_fwd_end.py: T_F, D_S4, GAP, BANDS)
T_F = P.PLUG_L + P.FWD_INSUL_T            # t: closure flange face to item 7's aft face
D_S4 = P.Z_CASE_FWD - ZA                  # d_S: case forward end face to the top of S4
GAP = D_S4 - T_F                          # take-up gap g
assert abs(GAP - TI) < 1e-9
BANDS = [(ts, 0.50 * ts, 0.75 * ts) for ts in (3.2, TF, 6.4)]
f2 = lambda x: f"{x:.2f}"                 # noqa: E731 (as sheet 3)
NB = " "                        # no-break space: textwrap keeps "g 2.40-3.60" together
bands = ", ".join(f"{fmt(ts, 1)} for g{NB}{f2(lo)}-{f2(hi)}" for ts, lo, hi in BANDS)

# mass: the title block is the STEP (installed, TI thick) at srm_verify's sponge density;
# the part as cut is the free volume at the certified free density of note 1
RHO_FREE = (0.30, 0.40)                   # g/cm3, free density band (material, note 1)
M_STEP = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())[
    "parts"]["takeup_ring"]["mass_each_kg"] * 1000.0                        # g
RHO_INST = V.MATERIALS["takeup_ring.step"][1] * 1e6                           # g/cm3, 0.50
V_INST = M_STEP / RHO_INST                                                    # cm3, 3.33
V_FREE = V_INST * TF / TI                 # same profile, free thickness: cm3, 5.33
assert f"{M_STEP:.1f}" == f"{MASS:.1f}", (M_STEP, MASS)
assert abs(V_INST - math.pi / 4.0 * (P.TAKEUP_OD ** 2 - P.TAKEUP_ID ** 2) * TI / 1000.0) < 1e-3
M_CUT = (V_FREE * RHO_FREE[0], V_FREE * RHO_FREE[1])                         # g, 1.60 ... 2.13
assert M_CUT[0] <= MASS <= M_CUT[1]       # the model's mass is a plausible as-cut mass
rho_s = f"{RHO_FREE[0]:.2f} - {RHO_FREE[1]:.2f} g/cm³"


def tol_s(t):
    return tuple(("+" if x > 0 else "") + fmt(x, 3) for x in t)


# ---- notes (defined before the views and leaders that cite them) ---------------------------
notes = [
    "Material (certified): closed-cell silicone sponge, medium, ASTM D1056 2A2 / AMS "
    "3195, e.g. Rogers BISCO HT-800; free density " + rho_s + "; compression set "
    "≤ 10 % (22 h at 100 °C, 50 % deflection).",
    "Stock: skinned 3/16 in sheet, free " + fmt(TF, 1) + " " + PM + fmt(TF_TOL, 1)
    + "; where note {rule} selects it, 3.2 or 6.4 " + PM + fmt(TF_TOL, 1)
    + " of the same grade. Do not split or skive.",
    "Cut to takeup_ring.dxf (1:1, mm, layer CUT) by steel rule die or oscillating knife; "
    "water jet acceptable; no laser or hot wire. The DXF sizes are limits (" + DIA
    + fmt(P.TAKEUP_OD, 1) + " max, " + DIA + fmt(P.TAKEUP_ID, 1) + " min): aim " + DIA
    + fmt(AIM[0], 1) + " / " + DIA + fmt(AIM[1], 1) + ".",
    "Inspect 100 %, no tears: free thickness t_s at 4 points 90° apart (dial gauge, flat "
    "foot, light load), mean on the bag; OD, ID by template, no squeeze.",
    "Fit: OD in liner SRM100-110 bore " + DIA + fmt(P.LINER_ID, 1) + " +0.1/0, diametral "
    f"clearance {CLR[0]:.2f} ... {CLR[1]:.2f} (free), whatever the case bore ("
    + DIA + f"{P.CASE_ID:.3f} ... {P.CASE_BORE_MAX:.2f}). Bears on spacer SRM100-109 (S4) "
    "and insulator SRM100-107.",
    "Take-up (SRM100-000 sheet 3): d_S from the case forward end face to the top of S4 "
    "and t from the closure flange face to the insulator's aft face, 4 points each, mean; "
    f"g = d_S - t (nominal {f2(GAP)} {PM}{f2(GAP_TOL)}). Accept "
    "0.50 ≤ g / t_s ≤ 0.75 (25-50 % compression), no shims: sheet " + bands
    + ". Lay the ring on S4.",
    "ISO 10579-NR: free state, lying flat, at 23 °C. The 3D model and title-block mass are "
    "the ring installed, " + fmt(TI, 1) + " thick: " + f"{V_INST:.2f}{NB}cm³ × "
    + f"{RHO_INST:.2f}{NB}g/cm³. As cut: " + f"{V_FREE:.2f}{NB}cm³ × "
    + rho_s.replace(" ", NB) + " = " + f"{M_CUT[0]:.1f}{NB}-{NB}{M_CUT[1]:.1f}{NB}g.",
    "Replace after every firing. Bag label: SRM100-108, batch, sheet, t_s; do not mark "
    "the part.",
    f"USED ON: SRM100-000 motor, item 12 (1{NB}off); not fitted in SRM100-001.",
]
N_RULE = next(k for k, s in enumerate(notes, 1) if s.startswith("Take-up"))
N_STOCK = next(k for k, s in enumerate(notes, 1) if s.startswith("Stock"))
notes = [s.replace("{rule}", str(N_RULE)) for s in notes]
N_LEFT = 6                                               # notes 1..6 left, the rest right


sh = Sheet("SRM100-108", "TAKE-UP RING",
           "Grain-stack axial take-up - silicone sponge, cut from " + fmt(TF, 1) + " sheet",
           size="A4", portrait=True,
           material="Silicone sponge, closed cell\nASTM D1056 2A2, sheet " + fmt(TF, 1),
           mass_g=MASS, scale="1:1", finish=None, tol="ALL TOLERANCED",
           edges="SQUARE, AS CUT")

# ---- end view 1:1: the cutting profile --------------------------------------------------
EX, EY = 72.0, 229.0
ev = View(sh, Part("takeup_ring.step"), origin=(EX, EY), scale=1.0, look="fwd")
ev.centerline((-R_OD, 0.0), (R_OD, 0.0), ext=3.0)
ev.cut_line((0.0, -R_OD), (0.0, R_OD), "A", (1, 0), ext=6.0)

# ---- SECTION A-A 1:1, free state ------------------------------------------------------------
free = tube(R_ID, R_OD, 0.0, TF)          # the generator's call at the free thickness
SX = 150.0
sv = View(sh, Part(free, hatch=Hatch(45, 1.0), name="takeup_free"), origin=(SX, EY), scale=1.0,
          look="side", section="full")
sv.dim_dia(TF, R_ID, off=10.0, tol=tol_s(ID_TOL))
sv.dim_dia(TF, R_OD, off=20.0, tol=tol_s(OD_TOL))
sv.dim_h((0.0, R_OD), (TF, R_OD), off=8.0,
         tol=PM + fmt(TF_TOL, 1) + f" (NOTE {N_STOCK})")      # alternate sheets, note 2
sv.label("SECTION A-A", where="below", gap=6.0)
x0, y0, x1, y1 = sv.bbox()
sh.text((x0 + x1) / 2, y0 - 6.0 - 3.5 - 4.6, "FREE STATE", D.H, ha="center")

# ---- installed position 5:1 (reference) -----------------------------------------------------
S5 = 5.0
WIN = (ZA - 1.2, 39.6, ZF + 2.0, 46.8)                 # motor z, radius
IX0, IY0 = 126.0, 124.0                                 # paper of the window's lower-left
IO = (IX0 - S5 * WIN[0], IY0 - S5 * WIN[1])
PL = C.placed(["spacer_4", "liner", "case", "fwd_insulator", "takeup_ring"])
nb = [Part(PL[n][0], PL[n][1], name=n) for n in ("spacer_4", "liner", "case", "fwd_insulator")]
me = Part(PL["takeup_ring"][0], PL["takeup_ring"][1], hatch=Hatch(45, 1.0))
C.phantom_parts(sh, nb, IO, S5, WIN, occluders=[me])
iv = C.part_view(sh, me, IO, S5, WIN)
C.zig_window(iv, WIN, ("left", "right", "bottom", "top"))
wx0, wy0 = iv.pt(WIN[0], WIN[1])
wx1, wy1 = iv.pt(WIN[2], WIN[3])


def to_right(u, v, dy, s):
    """Leader from (u, v) to a reference line starting 3 mm right of the window."""
    iv.leader((u, v), wx1 + 3.0 - iv.pt(u, v)[0], dy, s, end="dot")


def to_y(u, v, dx, y, s):
    """Leader from (u, v) to a reference line at paper height y."""
    iv.leader((u, v), dx, y - iv.pt(u, v)[1], s, end="dot")


to_right(ZF + 1.2, 46.5, 2.0, "CASE SRM100-101")
to_right(ZF + 1.0, 41.5, -2.0, "INSULATOR SRM100-107")
to_y(ZA - 0.6, 45.1, 5.0, wy1 + 4.5, "LINER SRM100-110")
to_y(ZA + 1.5, 41.3, 4.0, wy0 - 6.0, "INSTALLED " + fmt(TI, 1) + " (REF)")
to_y(ZA - 0.6, 43.6, 2.0, wy0 - 12.5, "SPACER SRM100-109 (S4)")
YL = wy0 - 18.5
sh.text((wx0 + wx1) / 2 + 14.0, YL, "INSTALLED (5:1) - REFERENCE", 3.5, ha="center")

# ---- notes: two columns (left under the end view, right under the installed view) -----------
YB = (C.notes_block(sh, 22.0, 169.0, notes[:N_LEFT], 100.0),
      C.notes_block(sh, 127.0, YL - 4.5, notes[N_LEFT:], 72.0, start=N_LEFT + 1, title=None))
C.clear_centring_mark(sh)

if __name__ == "__main__":
    print("notes bottom y (left, right):", [round(float(y), 1) for y in YB], "title block top",
          sh.tb[3], "| nominal compression", round(100 * C_NOM, 1), "%, g/t_s",
          round(GAP / TF, 3), "| clearance", [round(c, 2) for c in CLR], "| aim", AIM)
    sh.lint()
    C.lint_marks(sh)
    sh.save("takeup_ring")
