"""SRM100-109 grain spacer (linen phenolic ring, 5 off): A4 portrait detail drawing.

End view 1:1 (the cutting profile, = grain_spacer.dxf), SECTION A-A 1:1 with the
diameters, detail C (10:1) of the rim with the thickness and the geometrical
tolerances, installed position 5:1 (reference, spacer_1 between grains 1 and 2,
adjacent parts in phantom) and notes.

Datum A = one face (either: the ring is symmetrical); datum B = the OD axis (the OD
locates the ring in the liner bore).  The thickness TOL_SPACER_T is the stack
tolerance srm_params budgets per spacer (TOL_STACK).

View frames: end view look 'fwd' (u = x, v = y); section look 'side' (u = local z,
v = radius); installed view look 'side' in the MOTOR frame (u = motor z).
"""

import srm_dwg as D
import srm_params as P
from srm_dwg import DIA, PM, Hatch, Part, Sheet, View, fmt

import dwg_10x_flat_common as C

MASS = 1.3
R_OD = P.SPACER_OD / 2.0                  # 44.2
R_ID = P.SPACER_ID / 2.0                  # 43.0
T = P.SPACER_T                            # 3.0
OD_TOL = (0.0, -0.1)
ID_TOL = (0.0, -0.1)                      # decision G10: ID 86.0 0/-0.1 (SRM100-112 detail D)
T_TOL = P.TOL_SPACER_T                    # 0.02
COAX = 0.1
PAR = 0.02
LINER_ID = (P.LINER_ID, P.LINER_ID + 0.1)                 # SRM100-110: 88.6 +0.1/0
CLEAR = (LINER_ID[0] - P.SPACER_OD, LINER_ID[1] - (P.SPACER_OD + OD_TOL[1]))
R_GRAIN = P.GRAIN_OD / 2.0                # = casting-tube ID / 2
# radial cover of the grain end face at the nominal grain OD, spacer concentric: 0.40 ... 0.45
COVER = (R_GRAIN - (R_ID + ID_TOL[0] / 2.0), R_GRAIN - (R_ID + ID_TOL[1] / 2.0))
AIM = (P.SPACER_OD + sum(OD_TOL) / 2.0, P.SPACER_ID + sum(ID_TOL) / 2.0)   # mid-tolerance cut
EDGE_ID = 0.05                            # ID edges: the ID band is the grain-face cover
STOCK_T = 4.0                             # sheet as bought, ground to T


def tol_s(t):
    return tuple(("+" if x > 0 else "") + fmt(x, 3) for x in t)


# ---- notes (defined before the title block and the leader that cite them) -----------------
NB = " "                             # no-break space: textwrap keeps a range on one line
notes = [
    "Material (certified): linen phenolic, NEMA LI 1 grade LE (IEC 60893-3-4 PF CC 203 or "
    "equal).",
    "Stock: sheet " + fmt(STOCK_T, 1) + " (5/32 in), surface-ground equally on both faces to "
    + fmt(T, 1) + " " + PM + fmt(T_TOL, 2) + " before profiling. Machine dry, no coolant.",
    "Cut to grain_spacer.dxf (1:1, mm, layer CUT) by CNC router (carbide compression "
    "cutter) or turn a clamped stack on a mandrel; no laser, water jet or punching. The DXF "
    "sizes are upper limits: aim " + DIA + fmt(AIM[0], 2) + " / " + DIA + fmt(AIM[1], 2) + ".",
    "Edges: ISO 13715 -0.2, but both ID edges burr-free, -" + fmt(EDGE_ID, 2)
    + " max: the ID band bears on the grain face.",
    "Fit: OD in liner SRM100-110 bore " + DIA + fmt(P.LINER_ID, 1) + " +0.1/0, diametral "
    f"clearance {CLEAR[0]:.2f}{NB}...{NB}{CLEAR[1]:.2f}, whatever the case bore (" + DIA
    + f"{P.CASE_ID:.3f}{NB}...{NB}{P.CASE_BORE_MAX:.2f}). The ID covers {COVER[0]:.2f}{NB}...{NB}{COVER[1]:.2f} of "
    "each grain face (" + DIA + fmt(P.GRAIN_OD, 1) + ", radial, concentric).",
    "Inspect 100 %: t at 4 points (micrometer), mean on the bag label; OD and ID at "
    f"2{NB}×{NB}90°; parallelism on a surface plate, face A down.",
    "Replace after every firing. Bag label SRM100-109, batch, mean t; store sealed, with "
    "desiccant.",
    "USED ON: SRM100-000 motor, item 11 (" + str(P.N_SPACERS) + " off); not fitted in "
    "SRM100-001.",
]
N_EDGE = next(k for k, s in enumerate(notes, 1) if s.startswith("Edges"))

sh = Sheet("SRM100-109", "GRAIN SPACER",
           "Grain segment spacer - linen phenolic, " + str(P.N_SPACERS) + " off per motor",
           size="A4", portrait=True,
           material="Linen phenolic, NEMA LI 1 LE\nsheet " + fmt(STOCK_T, 1) + ", faces ground to "
           + fmt(T, 1),
           mass_g=MASS, scale="1:1", finish="Ra 3.2", tol="ISO 2768-mK",
           edges=f"ISO 13715  -0.2, NOTE {N_EDGE}")      # fits the 38 mm EDGES cell

# ---- end view 1:1: the cutting profile --------------------------------------------------
EX, EY = 72.0, 229.0
ev = View(sh, Part("grain_spacer.step"), origin=(EX, EY), scale=1.0, look="fwd")
ev.centerline((-R_OD, 0.0), (R_OD, 0.0), ext=3.0)
ev.cut_line((0.0, -R_OD), (0.0, R_OD), "A", (1, 0), ext=6.0)

# ---- SECTION A-A 1:1: the diameters -----------------------------------------------------
SX = 150.0
sv = View(sh, Part("grain_spacer.step", hatch=Hatch(45, 1.0)), origin=(SX, EY), scale=1.0,
          look="side", section="full")
OFF_ID, OFF_OD = -10.0, 20.0
sv.dim_dia(0.0, R_ID, off=OFF_ID, tol=tol_s(ID_TOL))
sv.dim_dia(T, R_OD, off=OFF_OD, tol=tol_s(OD_TOL))
x_od = sv.pt(T, 0.0)[0] + OFF_OD
sh.datum((x_od, sv.pt(0.0, R_OD)[1]), "B", (0, 1), length=5.0)
# coaxiality of the ID axis: frame below the ID dimension, leader in line with it
x_id = sv.pt(0.0, 0.0)[0] + OFF_ID
y_id = sv.pt(0.0, -R_ID)[1]
FCF_H = D.H * 2.6
sh.fcf(x_id - 9.0, y_id - 5.0 - FCF_H, ["coaxiality", DIA + fmt(COAX, 1), "B"],
       leader=(x_id, y_id))
sv.label("SECTION A-A", where="below", gap=14.0)

# ---- detail C 10:1: the rim ---------------------------------------------------------------
S10 = 10.0
DC = (T / 2.0, (R_ID + R_OD) / 2.0)
dv = sv.detail(DC, 2.0, S10, (150.0, 136.0), "C", circle_label_ang=135.0)
dv.dim_h((0.0, R_OD), (T, R_OD), off=8.0, tol=PM + fmt(T_TOL, 2))
dv.datum((0.0, R_ID + 0.3), "A", (-1, 0), length=7.0)
dv.fcf((T, R_ID + 0.3), 7.0, -FCF_H / 2.0, ["parallelism", fmt(PAR, 2), "A"])
dv.leader((T, R_ID), 10.0, -10.0, ["ID EDGES", f"NOTE {N_EDGE}"], end="arrow")

# ---- installed position 5:1 (reference) -----------------------------------------------------
S5 = 5.0
ZS = P.spacer_z(1)                                      # spacer_1, aft face
WIN = (ZS - 1.6, 42.3, ZS + T + 1.6, 46.6)              # motor z, radius
IX0, IY0 = 135.0, 66.0
IO = (IX0 - S5 * WIN[0], IY0 - S5 * WIN[1])
names = ["grain_1", "casting_tube_1", "grain_2", "casting_tube_2", "liner", "case"]
PL = C.placed(names + ["spacer_1"])
nb = [Part(PL[n][0], PL[n][1], name=n) for n in names]
me = Part(PL["spacer_1"][0], PL["spacer_1"][1], hatch=Hatch(45, 1.2))
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


ZR = ZS + T + 1.0                                       # dots in the forward neighbours
to_y(ZS + 1.5, 46.3, 3.0, wy1 + 4.0, "CASE SRM100-101")
to_y(ZS - 1.0, 45.05, 3.0, wy1 + 11.0, "LINER SRM100-110")
to_right(ZR, 43.8, 2.5, ["CASTING TUBE", "SRM100-111"])
to_right(ZR, 42.8, -2.0, ["GRAIN", "SRM100-112"])
sh.text((wx0 + wx1) / 2 + 12.0, wy0 - 7.0, "INSTALLED (5:1) - REFERENCE", 3.5, ha="center")

# ---- notes ------------------------------------------------------------------------------------
YB = C.notes_block(sh, 22.0, 169.0, notes, 96.0)
# ISO 1302 general indication close to the title block, right of the notes' short last line
sh.general_finish(106.0, sh.tb[3] + 2.5, "Ra 3.2", others=False)
C.clear_centring_mark(sh)

if __name__ == "__main__":
    print("notes bottom y:", round(float(YB), 1), "title block top", sh.tb[3], "| cover",
          [round(c, 3) for c in COVER], "| clearance", [round(c, 2) for c in CLEAR], "| aim", AIM,
          "| EDGES text width", round(sh.text_width(f"ISO 13715  -0.2, NOTE {N_EDGE}", 2.2), 1),
          "of 38")
    sh.lint()
    C.lint_marks(sh)
    sh.save("grain_spacer")
