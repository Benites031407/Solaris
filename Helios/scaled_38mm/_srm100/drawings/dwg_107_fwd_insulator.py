"""SRM100-107 forward insulator (EPDM disc): A4 portrait detail drawing.

End view 1:1 (the cutting profile, = fwd_insulator.dxf: one OD circle on layer CUT),
SECTION A-A 1:1, installed position 5:1 (reference, adjacent parts in phantom) and notes.

The disc is cut from 3.0 sheet; the STEP (fwd_insulator.step) is the part as cut: a
full disc, no centre hole (tube(0, FWD_INSUL_OD/2, 0, FWD_INSUL_T)), since the forward
closure has no port.  Its forward face is RTV-bonded over the whole face to the forward
closure's inboard face (README, Build step 1).  The title-block mass is the
out/mass_budget.json part mass (STEP x srm_verify's EPDM density).
Non-rigid part (ISO 10579-NR): dimensions apply in the free state.

View frames: end view look 'fwd' (u = x, v = y); section look 'side' (u = local z,
v = radius); installed view look 'side' in the MOTOR frame (u = motor z).
No datum: with no hole there is no geometric tolerance to refer to one.
"""

import json
import math

import srm_dwg as D
import srm_params as P
import srm_verify as V
from srm_dwg import DIA, PM, Hatch, Part, Sheet, View, fmt

import dwg_10x_flat_common as C

R_OD = P.FWD_INSUL_OD / 2.0               # 45.9
T = P.FWD_INSUL_T                         # 3.0
ZA = P.Z_FWD_INSUL_AFT                    # motor z of the aft face (take-up side)
ZF = P.Z_FWD_INSUL_FWD                    # = closure inboard face (bonded)
OD_TOL = 0.1
T_TOL = 0.2
# mass: out/mass_budget.json (srm_verify: fwd_insulator.step x its EPDM density), 22.8 g;
# the STEP is the full disc, so it equals pi/4 OD^2 T x the same density
M_JSON = json.loads((D.ROOT / "out" / "mass_budget.json").read_text())[
    "parts"]["fwd_insulator"]["mass_each_kg"] * 1000.0                        # g
RHO = V.MATERIALS["fwd_insulator.step"][1] * 1e3                            # g/mm3
MASS = round(M_JSON, 1)
assert abs(M_JSON - math.pi / 4.0 * P.FWD_INSUL_OD ** 2 * T * RHO) < 0.01, (M_JSON, RHO)
# SRM100-101 (decision G1-rev): the forward seal zone is honed to the recorded clean-up
# diameter A +0.030/0, 92.000 <= A <= SEAL_A_MAX (92.070), so the zone never passes
# CASE_BORE_MAX; the disc (38 - 41 from the case forward end) sits in it.  Its fit is
# stated over the whole bore range 92.000 ... 92.10.
A_MAX, A_TOL = P.SEAL_A_MAX, P.TOL_BORE[1]
BORE = (P.CASE_ID + P.TOL_BORE[0], P.CASE_BORE_MAX)
assert A_MAX + A_TOL <= BORE[1] + 1e-9
CLEAR = (BORE[0] - (P.FWD_INSUL_OD + OD_TOL), BORE[1] - (P.FWD_INSUL_OD - OD_TOL))

sh = Sheet("SRM100-107", "FORWARD INSULATOR",
           "EPDM disc on the forward closure face - cut from " + fmt(T, 1) + " sheet",
           size="A4", portrait=True,
           material="EPDM, 60 " + PM + "5 Shore A\nASTM D2000 M2DA610, sheet " + fmt(T, 1),
           mass_g=MASS, scale="1:1", finish=None, tol="ALL TOLERANCED",
           edges="SQUARE, AS CUT")

# ---- end view 1:1: the cutting profile --------------------------------------------------
EX, EY = 72.0, 224.0
ev = View(sh, Part("fwd_insulator.step"), origin=(EX, EY), scale=1.0, look="fwd")
ev.centerline((-R_OD, 0.0), (R_OD, 0.0), ext=3.0)
ev.cut_line((0.0, -R_OD), (0.0, R_OD), "A", (1, 0), ext=6.0)

# ---- SECTION A-A 1:1 --------------------------------------------------------------------------
SX = 150.0
sv = View(sh, Part("fwd_insulator.step", hatch=Hatch(45, 1.0)), origin=(SX, EY), scale=1.0,
          look="side", section="full")
OFF_OD = 20.0
sv.dim_dia(T, R_OD, off=OFF_OD, tol=PM + fmt(OD_TOL, 1))
sv.dim_h((0.0, -R_OD), (T, -R_OD), off=-8.0, tol=PM + fmt(T_TOL, 1))
sv.label("SECTION A-A", where="below", gap=13.0)

# ---- installed position 5:1 (reference) -----------------------------------------------------
S5 = 5.0
WIN = (ZA - 2.2, 42.6, ZF + 2.4, 47.6)                 # motor z, radius
IX0, IY0 = 127.0, 117.0                                 # paper of the window's lower-left
IO = (IX0 - S5 * WIN[0], IY0 - S5 * WIN[1])
PL = C.placed(["takeup_ring", "liner", "case", "fwd_closure", "fwd_insulator"])
nb = [Part(PL[n][0], PL[n][1], name=n) for n in ("takeup_ring", "liner", "case", "fwd_closure")]
me = Part(PL["fwd_insulator"][0], PL["fwd_insulator"][1], hatch=Hatch(45, 1.5))
C.phantom_parts(sh, nb, IO, S5, WIN, occluders=[me])
iv = C.part_view(sh, me, IO, S5, WIN)
C.zig_window(iv, WIN, ("left", "right", "bottom", "top"))
wx0, wy0 = iv.pt(WIN[0], WIN[1])
wx1, wy1 = iv.pt(WIN[2], WIN[3])


def to_right(u, v, dy, s):
    """Leader from (u, v) to a reference line starting 3 mm right of the window."""
    iv.leader((u, v), wx1 + 3.0 - iv.pt(u, v)[0], dy, s, end="dot")


def to_y(u, v, dx, y, s, end="dot"):
    """Leader from (u, v) to a reference line at paper height y."""
    iv.leader((u, v), dx, y - iv.pt(u, v)[1], s, end=end)


# ---- notes (defined before the leaders that cite them) ---------------------------------------
NB = " "                             # no-break space: textwrap keeps "(1 off)" together
notes = [
    "Material: EPDM, peroxide cured, no fabric insert, to ASTM D2000 M2DA610; "
    "certificate required.",
    "Stock: sheet " + fmt(T, 1) + " " + PM + fmt(T_TOL, 1) + ", smooth faces, no release "
    "agent or bloom. The thickness does not stack: the take-up gap is measured at "
    "assembly (SRM100-000 sheet 3).",
    "Cut to fwd_insulator.dxf (1:1, mm, one OD circle on layer CUT): full disc, no hole; "
    "pure water jet or CNC oscillating knife. No laser. Edges square, no tears or nicks.",
    "ISO 10579-NR: free state, lying flat, at 23 °C.",
    "Inspect 100 %: OD at 2 × 90° by template or caliper, no squeeze; "
    "thickness at 4 points, dial gauge, flat foot, light load. No cuts or voids.",
    "Fit in the forward seal zone of case SRM100-101, honed to A +" + f"{A_TOL:.3f}"
    + "/0, A ≤ " + f"{A_MAX:.3f}" + ": bore " + DIA
    + f"{BORE[0]:.3f}{NB}...{NB}{BORE[1]:.2f}, diametral clearance "
    + f"{CLEAR[0]:.2f}{NB}...{NB}{CLEAR[1]:.2f}.",
    "Bond after the hydrostatic proof to the aft face of closure SRM100-103: abrade both "
    "faces P180, IPA wipe, silicone primer SS4004P or equal, RTV106 or equal over the "
    "whole face, bondline 0.1 - 0.2; OD centred on the land within 0.1. Cure 24 h, "
    "23 °C.",
    "At assembly grease the OD edge: " + P.LUBE + ".",
    "Replace after every firing. Bag label: SRM100-107, batch, cure date; do not mark "
    "the part.",
    f"USED ON: SRM100-000 motor, item 7 (1{NB}off); not fitted in SRM100-001.",
]
N_BOND = next(k for k, s in enumerate(notes, 1) if s.startswith("Bond"))
N_LEFT = 7                                               # notes 1..7 left, the rest right

to_y(ZF - 1.6, 47.1, 3.0, wy1 + 6.0, "CASE SRM100-101")
to_y(ZA - 1.5, 45.05, 3.0, wy1 + 13.0, "LINER SRM100-110")
to_right(ZF + 1.6, 44.0, 3.0, ["CLOSURE", "SRM100-103"])
to_y(ZF, 43.3, 4.0, wy0 - 5.0, f"RTV BOND, NOTE {N_BOND}", end="arrow")
to_y(ZA - 1.2, 43.4, 2.0, wy0 - 12.0, "TAKE-UP RING SRM100-108")
YL = wy0 - 21.0
sh.text((wx0 + wx1) / 2 + 12.0, YL, "INSTALLED (5:1) - REFERENCE", 3.5, ha="center")

# ---- notes: two columns (left under the end view, right under the installed view) -----------
YB = (C.notes_block(sh, 22.0, 161.0, notes[:N_LEFT], 100.0),     # "2." clears the mark
      C.notes_block(sh, 127.0, YL - 5.0, notes[N_LEFT:], 72.0, start=N_LEFT + 1, title=None))
C.clear_centring_mark(sh)

if __name__ == "__main__":
    print("notes bottom y (left, right):", [round(y, 1) for y in YB], "title block top",
          sh.tb[3])
    sh.lint()
    C.lint_marks(sh)
    sh.save("fwd_insulator")
