"""SRM100-105 nozzle insulator (glass phenolic washer): A3, 2:1 half-section,
detail C (bore edge, 5:1), installation view (2:1, reference) and notes.

View frame of the part views: the insulator's own frame (nozzle_insulator.py):
u = z from its aft face (0) forward (+), v = radius.  In the motor it is placed at
axial_trsf(Z_HOLDER_FACE): its aft face lies on the holder's forward face and the
graphite's forward face, its forward face carries the liner and the aft grain spacer.
Datum A = the aft face; datum B = the OD.
The installation view is drawn in the MOTOR frame (u = motor z).

Detail C carries the cone's runout frame with its Ra 1.6 symbol standing on the frame
(ISO 1302 indication on a geometrical tolerance frame, via sheet.finish_symbol).
"""

import math

import srm_dwg as D
import srm_params as P
import srm_assembly as A
import nozzle_insulator as NI
from srm_dwg import DIA, DEG, TIMES, PM, Hatch, Part, Sheet, View, fmt

MASS = 38.8                             # 20981 mm3 (STEP) x 1.85 g/cm3
T = P.NOZ_INSUL_T                       # 5.0
R_OUT = NI.R_OUT                        # 45.9
R_AFT = NI.R_AFT                        # 26.0 (= graphite entry, CONV_ENTRY_D / 2)
R_FWD = NI.R_FWD                        # 29.50
T35 = math.tan(math.radians(P.CONV_HALF_DEG))
ZF = P.Z_HOLDER_FACE                    # 38.0, motor z of the aft face
CASE_D = P.CASE_ID                      # 92.0, bore it sits in (honed, up to CASE_BORE_MAX)
# G1-rev: the aft honed zone is A +TOL_BORE/0 with CASE_ID <= A <= SEAL_A_MAX, so its
# largest bore is SEAL_A_MAX + TOL_BORE[1] = CASE_BORE_MAX (92.10), as between the zones
BORE_MAX = P.SEAL_A_MAX + P.TOL_BORE[1]
assert abs(BORE_MAX - P.CASE_BORE_MAX) < 1e-9
LE = chr(8804)
OD_MAX, OD_MIN = 2 * R_OUT, 2 * R_OUT - 0.05   # 91.80 0/-0.05
NBSP = chr(0xA0)                        # no-break space: textwrap keeps the pair on one line

sh = Sheet("SRM100-105", "NOZZLE INSULATOR",
           "Phenolic washer on the holder face - bore continues the 35° convergent",
           size="A3", material="Glass phenolic NEMA LI 1 G-3",
           mass_g=MASS, scale="2:1", finish="Ra 3.2")


def detail(view, *a, **k):
    """View.detail, labelled 'DETAIL <L> (<scale>)' (the kit's label is the last text)."""
    dv = view.detail(*a, **k)
    t = view.sheet.texts[-1]
    t.set_text("DETAIL " + t.get_text())
    return dv


# ---- main view: half-section, 2:1 ------------------------------------------------------
OX, OY = 120.0, 150.0
v = View(sh, Part("nozzle_insulator.step", hatch=Hatch(45, 2.0)), origin=(OX, OY), scale=2.0,
         look="side", section="half")

# OD (datum B), far left so the flatness frame fits between it and the part
v.dim_dia(0.0, R_OUT, at=-30.0, tol=("0", "-0.05"))
v.datum((-30.0, -R_OUT), "B", (0, -1), length=5.0)
# bore at the aft face: half dimension through the axis
v.dim_dia_half(0.0, R_AFT, at=-5.0, tol=("0", "-0.1"), text=DIA + fmt(2 * R_AFT, 0))
# bore at the forward face: reference
v.dim_dia_half(T, R_FWD, at=T + 8.0, text="(" + DIA + fmt(2 * R_FWD, 1) + ")")
# thickness
v.dim_h((0.0, R_OUT), (T, R_OUT), off=10.0, tol=PM + "0.05")
# datum A on the aft face (lower, outside half) + flatness
v.datum((0.0, -38.0), "A", (-1, 0), length=5.0)
v.fcf((0.0, -20.0), -27.0, -3.2, ["flatness", "0.05"])
# forward face parallel to A
v.fcf((T, -20.0), 9.0, -3.2, ["parallelism", "0.05", "A"])
# OD edge breaks (not modelled)
v.leader((0.0, R_OUT), -8.0, 7.0, ["0.3" + TIMES + "45" + DEG + " both OD edges"])
# detail C: the bore edge
c = detail(v, (1.5, 26.8), 5.2, 5.0, (205, 222), "C", circle_label_ang=330)

# ---- detail C (5:1) ----------------------------------------------------------------------
# 35 deg between the axis-parallel ray and the cone, both extended past the edge (u < 0 is free)
c.dim_ang((0.0, R_AFT), 180.0, 180.0 + P.CONV_HALF_DEG, 10.0, ext=True, ext_from=1.0, dec=0)
c.leader((0.0, R_AFT), -17.5, 14.0, ["SHARP, BURR-FREE", "ISO 13715  -0.05"])
# runout of the cone to datum B, with the cone's texture on the frame (ISO 1302)
u_fcf = 4.4
p_fcf = c.pt(u_fcf, R_AFT + u_fcf * T35)
fb = c.fcf((u_fcf, R_AFT + u_fcf * T35), 200.5 - p_fcf[0], 201.5 - p_fcf[1], ["runout", "0.1", "B"])
sh.finish_symbol((fb[0] + 2.0, fb[3]), "Ra 1.6")

# ---- installation view (reference), motor frame, 2:1 -----------------------------------------
PL = {n: (st, tr) for g, n, st, tr in A.placements()}
HATCH = {
    "case": Hatch(135, 2.0),
    "nozzle_holder": Hatch(45, 2.0),
    "nozzle_insert": Hatch(45, 1.5, cross=True),
    "nozzle_insulator": Hatch(135, 1.0),
    "liner": Hatch(45, 1.0),
    "spacer_0": Hatch(135, 0.6),
    "casting_tube_1": Hatch(solid=True),
    "grain_1": Hatch(45, 3.0, offset=0.5),
}
names = list(HATCH)
parts = [Part(PL[n][0], PL[n][1], hatch=HATCH[n], name=n) for n in names]
WIN = (33.5, 18.0, 50.0, 51.0)
IX0, IY0 = 185.0, 84.0                                 # paper of the window's lower-left
iv = View(sh, parts, (IX0 - 2.0 * WIN[0], IY0 - 2.0 * WIN[1]), 2.0, section="half", window=WIN,
          axis=False)
iv.zigzag((WIN[0], WIN[1]), (WIN[0], WIN[3] - 1.0), ext=0.0)
iv.zigzag((WIN[2], WIN[1]), (WIN[2], WIN[3] - 1.0), ext=0.0)
iv.zigzag((WIN[0], WIN[1]), (WIN[2], WIN[1]), ext=0.0)
sh.text(IX0 + (WIN[2] - WIN[0]), IY0 + 2.0 * (WIN[3] - WIN[1]) + 6.0,
        "INSTALLATION (REFERENCE) 2:1", 3.5, ha="center")

# item balloons (SRM100-000 item numbers); targets in motor (z, r)
r_liner = (P.LINER_OD + P.LINER_ID) / 4
r_tube = (P.TUBE_OD + P.TUBE_ID) / 4
r_sp = (P.SPACER_OD + P.SPACER_ID) / 4
z_sp = P.Z_LINER_AFT + P.SPACER_T / 2
BAL = [  # (item, target (z, r), balloon paper, end)
    (2, (35.5, 39.0), (174.0, 128.0), "dot"),
    (3, (35.5, 28.0), (174.0, 100.0), "dot"),
    (4, (40.5, 35.0), (197.0, 72.0), "dot"),
    (11, (z_sp, r_sp), (207.0, 72.0), "dot"),
    (1, (48.0, 48.0), (230.0, 148.0), "dot"),
    (8, (48.0, r_liner), (230.0, 139.0), "dot"),
    (9, (48.0, P.TUBE_ID / 2), (230.0, 128.0), "arrow"),
    (10, (48.0, 30.0), (230.0, 110.0), "dot"),
]
for n, (z, r), at, end in BAL:
    sh.balloon(iv.pt(z, r), n, at, end=end)

# ---- notes -------------------------------------------------------------------------------------
X0 = 240.0
notes = [
    "Material: glass-fabric reinforced phenolic laminate, NEMA LI 1 grade G-3, or "
    "compression-moulded glass-phenolic (MXB-360 / Durite class); density about 1.85 g/cm³. "
    "G-10 / G-11 are epoxy-glass grades and are not acceptable. Certificate of conformity.",
    "Stock: sheet 6.35 (1/4 in) min, faced both sides to 5; laminations parallel to the faces. "
    "Turn OD and bore in one set-up on a mandrel located on datum A.",
    "Machine dry with carbide or PCD tools, with dust extraction. No coolant, no oil. "
    "Blow clean with dry, oil-free air; deliver and store bagged, clean and dry.",
    "The bore edge on the aft face is sharp, free of burrs and chips (detail C): it meets the "
    "graphite entry " + DIA + fmt(P.CONV_ENTRY_D, 0) + " of insert SRM100-104 with no forward-"
    "facing step. " + DIA + fmt(2 * R_AFT, 0) + " is never exceeded.",
    "Edges: OD edges 0.3" + TIMES + "45" + DEG + " (not in the 3-D model): the part slides "
    "through the honed seal bore of case SRM100-101 at assembly. Other edges per the "
    "title block.",
    "Loose fit in the aft honed zone of case SRM100-101, bore " + DIA + f"{CASE_D:.3f}" + " to "
    + f"{BORE_MAX:.2f}" + " (A" + NBSP + f"+{P.TOL_BORE[1]:.3f}/0, A{NBSP}{LE}{NBSP}"
    + f"{P.SEAL_A_MAX:.3f}" + ", SRM100-101 note 4): diametral clearance "
    + f"{CASE_D - OD_MAX:.2f}" + " to " + f"{BORE_MAX - OD_MIN:.2f}" + ". Not bonded; "
    "located radially by the case bore. "
    "Aft face (A) down on the holder and graphite forward faces; clamped axially by the aft "
    "grain spacer on its forward face (grain stack, take-up ring). Liner SRM100-110 also "
    "rests on its forward face and carries no axial load. Grease the OD and edges: "
    + P.LUBE.replace(" film", NBSP + "film") + ".",
    "Inspect 100 %: thickness at 4 places 90" + DEG + " apart, OD, bore " + DIA + "52 at the aft "
    "face (optical comparator or taper gauge), flatness and parallelism on a surface plate, "
    "runout on a mandrel. Visual: no delamination, cracks or chipped edges. Record values.",
    "Mark SRM100-105 and serial on the aft face between " + DIA + "70 and " + DIA + "86, "
    "indelible ink or laser, no engraving.",
    "Single use: a new part for every firing, scrapped after it (charred bore; README, "
    "After every firing). Never re-use a fired part.",
    "Used on SRM100-000 item 4 (aft closure bench subassembly). Item numbers in the "
    "installation view per SRM100-000.",
]
y_end = sh.notes(X0, 282.0, notes, 165.0)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")

if __name__ == "__main__":
    print("notes end y", round(y_end, 1))
    sh.lint()
    sh.save("nozzle_insulator")
