"""SRM100-104 nozzle insert (graphite): A3, 2:1 half-section, details C (aft corner,
10:1) and D (throat, 5:1), and the flow-path contour station table.

View frame: u = motor z (forward to the right), v = radius; the insert is modelled
in the motor frame, so the numbers here are nozzle_stations() values directly.
Datum A = the OD (63.50, the seal surface); datum B = the aft bearing face on the
holder's lip.  Axial stations on the sheet are measured from B.

Flow path: the station table holds the theoretically exact contour (ISO 1101 TEDs in
a table) and the profile frame refers to it; the flow-path values in the views are
the same contour, shown in parentheses as auxiliary dimensions (each feature is
defined once, by the table).  The throat carries its own size tolerance.

Local primitives: detail() relabels View.detail's '<L> (<scale>)' as
'DETAIL <L> (<scale>)' by editing the label text object the kit just created.
"""

import math

import srm_dwg as D
import srm_params as P
import nozzle_insert as N
from srm_dwg import DIA, DEG, TIMES, Hatch, Part, Sheet, View, fmt

S = P.nozzle_stations()
R_OD = P.INSERT_OD / 2.0
ZB = S["z_exit"]                       # datum B, the aft face
ZF = S["z_fwd"]
T15 = math.tan(math.radians(P.DIV_HALF_DEG))
T35 = math.tan(math.radians(P.CONV_HALF_DEG))
Z_XB = ZB + N.XB_H                     # divergent meets the exit break
R_XB = S["r_exit"] - N.XB_H * T15
R_XBF = S["r_exit"] + N.XB             # exit break meets the aft face
R_LEAD = R_OD - N.LEAD_R               # aft face meets the lead-in
Z_LEAD = ZB + P.INSERT_LEAD_IN
R_BRK = R_OD - N.BRK                   # forward break
R_PUSH = P.EXIT_D / 2.0 + P.HOLDER_LIP_STEP   # lip bore: the push face lies outside it
L_INS = ZF - ZB                        # 83.21
MASS = 311.1                           # 172813.75 mm3 (STEP) x 1.80 g/cm3
RHO = 1.80
SEAT_TOL, INS_TOL = ("+0.05", "0"), ("0", "-0.05")
FLUSH_MAX = float(SEAT_TOL[0]) - float(INS_TOL[1])            # 0.10
BORE_MIN, BORE_MAX = P.INSERT_BORE_D + P.TOL_INSERT_BORE[0], P.INSERT_BORE_D + P.TOL_INSERT_BORE[1]
OD_MIN, OD_MAX = P.INSERT_OD + P.TOL_INSERT_OD[0], P.INSERT_OD + P.TOL_INSERT_OD[1]
NBSP = chr(0xA0)                       # no-break space: textwrap keeps a value with its tolerance

sh = Sheet("SRM100-104", "NOZZLE INSERT", "Throat " + DIA + "23 - 35° / 15° conical de Laval - graphite",
           size="A3", material="Isomolded graphite, ISO-63 class",
           mass_g=MASS, scale="2:1", finish="Ra 3.2")


def detail(view, *a, **k):
    """View.detail, labelled 'DETAIL <L> (<scale>)' (the kit's label is the last text)."""
    dv = view.detail(*a, **k)
    t = view.sheet.texts[-1]
    t.set_text("DETAIL " + t.get_text())
    return dv


def aux(s):
    return "(" + s + ")"


part = Part("nozzle_insert.step", hatch=Hatch(45, 2.0, cross=False))
v = View(sh, part, origin=(150, 185), scale=2.0, look="side", section="half")

# ---- main view -------------------------------------------------------------------
v.dim_h((ZB, R_LEAD), (ZF, R_BRK), off=14.0, tol=INS_TOL)                    # 83.21
v.dim_dia(Z_LEAD, R_OD, at=ZB - 8.0, tol=("0", "-0.05"), arrows=(False, True))
v.datum((ZB - 8.0, -R_OD), "A", (0, -1), length=5.0)
v.finish((0.0, R_OD), "Ra 0.8")
v.leader((ZF - N.BRK / 2, R_OD - N.BRK / 2), 10.0, 7.0, ["0.5" + TIMES + "45" + DEG])
# datum B: the aft face, lower (outside) half
v.datum((ZB, -28.5), "B", (-1, 0), length=5.0)
v.fcf((ZB, -18.0), 9.0, -3.2, ["perpendicularity", "0.02", "A"])
v.fcf((ZF, -18.0), -34.0, -3.2, ["parallelism", "0.05", "B"])
# flow path (auxiliary: the table defines it): entry / exit diameters, cone angles
v.dim_dia_half(ZF, S["r_entry"], at=ZF + 4.0, text=aux(DIA + fmt(2 * S["r_entry"])))
v.dim_dia_half(ZB, S["r_exit"], at=ZB - 4.0, text=aux(DIA + fmt(2 * S["r_exit"])))
v.dim_ang((ZF - S["r_entry"] / T35, 0.0), 0.0, P.CONV_HALF_DEG, 60.0, ext=False,
          text=aux(fmt(P.CONV_HALF_DEG, 0) + DEG))
apex_dn = S["z_dn"] + S["r_dn"] / T15
v.dim_ang((apex_dn, 0.0), 180.0 - P.DIV_HALF_DEG, 180.0, 120.0, ext=False,
          text=aux(fmt(P.DIV_HALF_DEG, 0) + DEG))
# throat: diameter on the land (size tolerance), coaxial to A; its frame below, in line
z_th = S["z_land_fwd"] - 0.6
v.dim_dia_half(z_th, S["r_throat"], at=z_th, tol=("+0.05", "0"), dec=2,
               text=DIA + fmt(2 * S["r_throat"], 2), text_at=v.pt(0, 5.2)[1])
x_th = v.pt(z_th, 0)[0]
sh.fcf(x_th - 4.0, v.pt(0, -1.5)[1] - 13.0, ["coaxiality", DIA + "0.05", "A"],
       leader=v.pt(z_th, -1.5))
v.dim_h((ZB, 4.0), (S["z_land_aft"], S["r_throat"]), at=4.0, ext=(False, True), ref=True)
# profile of the flow path, stations 1 to 7 of the table, to A and B; the flow path's
# texture stands on the frame (ISO 1302 indication on a geometrical tolerance frame)
u_pf = -28.0
p_pf = v.pt(u_pf, S["r_exit"] - (u_pf - ZB) * T15)
fb = sh.fcf(p_pf[0] - 24.0, 211.0, ["profile_surface", "0.1", "A", "B"], leader=p_pf)
sh.finish_symbol((fb[0] + 2.5, fb[3]), "Ra 1.6")
sh.text(fb[0], fb[1] - 4.2, "FLOW PATH, STATIONS 1 TO 7", D.H)
c = detail(v, (-43.75, 28.84), 3.4, 10.0, (80, 72), "C", circle_label_ang=180)
d = detail(v, (11.67, 12.8), 5.0, 5.0, (178, 80), "D", circle_label_ang=308)

# ---- detail C: aft corner (10:1) ---------------------------------------------------
c.dim_h((ZB, R_LEAD), (Z_LEAD, R_OD), off=8.0)                         # 3
c.dim_ang((Z_LEAD, R_OD), 180.0, 180.0 + 20.0, 20.0, ext=True, dec=0)   # 20 deg lead-in
c.leader((ZB + N.XB_H / 2, (R_XB + R_XBF) / 2), -16.0, -8.0, ["45" + DEG + " BREAK,", "STATIONS 6-7"])
c.leader((ZB, 0.5 * (R_PUSH + R_XBF)), -20.0, 8.9,
         ["PUSH FACE", "(inside " + DIA + fmt(2 * R_PUSH) + ")"])

# ---- detail D: throat (5:1) ---------------------------------------------------------
d.dim_h((S["z_land_aft"], S["r_throat"]), (S["z_land_fwd"], S["r_throat"]), at=9.9, dec=2,
        ref=True)
d.dim_rad(S["c_up"][::-1], P.R_THROAT_UP, 280.0, length=13.0, text=aux("R" + fmt(P.R_THROAT_UP)))
d.dim_rad(S["c_dn"][::-1], P.R_THROAT_DN, 257.0, length=13.0, text=aux("R" + fmt(P.R_THROAT_DN)))

# ---- station table ------------------------------------------------------------------
X0 = 252.0
rows = [["STATION", "z FROM B", DIA, "NOTE"]]
stations = [
    ("1", ZF, 2 * S["r_entry"], "entry, forward face: sharp edge (note 3)"),
    ("2", S["z_up"], 2 * S["r_up"], "35° cone / R11.5 tangent"),
    ("3", S["z_land_fwd"], 2 * S["r_throat"],
     "R11.5 / land tangent (throat area " + f"{P.throat_area():.1f}" + " mm²)"),
    ("4", S["z_land_aft"], 2 * S["r_throat"], "land / R5.75 tangent"),
    ("5", S["z_dn"], 2 * S["r_dn"], "R5.75 / 15° cone tangent"),
    ("6", Z_XB, 2 * R_XB, "15° cone / 45° exit break"),
    ("7", ZB, 2 * R_XBF, "45° exit break / aft face B"),
]
for n, z, dia, note in stations:
    rows.append([n, f"{z - ZB:.3f}", f"{dia:.3f}", note])
rows.append(["E", f"{0.0:.3f}", f"{2 * S['r_exit']:.3f}",
             "exit, 15° cone meets B (construction; area ratio " + f"{P.expansion_ratio():.2f})"])
rows.append(["C1", f"{S['c_up'][1] - ZB:.3f}", f"{2 * S['c_up'][0]:.3f}", "centre of R11.5"])
rows.append(["C2", f"{S['c_dn'][1] - ZB:.3f}", f"{2 * S['c_dn'][0]:.3f}", "centre of R5.75"])
sh.text(X0, 145.0, "FLOW-PATH CONTOUR (THEORETICALLY EXACT)", 3.5)
yb = sh.table(X0, 141.0, [16, 22, 22, 93], rows, align=["c", "r", "r", "l"])
sh.text(X0, yb - 4.5, "Table values are TEDs (profile frame); values in parentheses in the "
        "views are auxiliary.", D.H)

notes = [
    "Material: isostatically moulded fine-grain graphite, grade ISO-63, TTK-4, IG-43 or equal: "
    "density ≥ 1.78 g/cm³, flexural strength ≥ 50 MPa, grain ≤ 15 µm; not extruded or "
    "vibration-moulded. Certificate required. Blank " + DIA + "68 " + TIMES + " 88 min from "
    "one block. Mass " + fmt(MASS, 1) + " g at " + f"{RHO:.2f}" + " g/cm³.",
    "Machine dry. Never wet this part, never hydro-test it: the proof test uses the steel "
    "proof dummy SRM100-120 in its place. No tool marks across the throat land.",
    "Edges: forward OD 0.5" + TIMES + "45°; aft OD 20° " + TIMES + " 3 lead-in; exit 45° break "
    "(stations 6-7). Entry edge (station 1) sharp, burr-free, ISO 13715 -0.05, to meet "
    "insulator SRM100-105 with no step. Throat blends tangent: do not break. Other edges "
    "per the title block.",
    "Slip fit in holder SRM100-102 bore " + DIA + fmt(P.INSERT_BORE_D, 2) + NBSP + "+0.025/0 "
    "(clearance " + fmt(BORE_MIN - OD_MAX, 2) + " to " + fmt(BORE_MAX - OD_MIN, 3)
    + "): by hand, aft end first; never press or knock it. Seated on the lip (seat "
    + fmt(L_INS, 2) + NBSP + "+0.05/0) the forward face lies flush to " + fmt(FLUSH_MAX, 2)
    + " below the holder face. Seal: O-ring " + P.INSERT_ORING_DASH + ", "
    + P.ORING_COMPOUND + ", in the holder gland; grease " + P.LUBE + ".",
    "Inspect 100 %: OD and throat at three axial positions, length, contour to the table, "
    "coaxiality, perpendicularity, parallelism; 10" + TIMES + " visual of the flow path and "
    "OD: no cracks, chips or pits. Record against the serial.",
    "Laser-mark SRM100-104 and serial on the forward face, between " + DIA + "56 and " + DIA +
    "62, 2 mm characters, 0.05 deep max (no dot-peen: brittle graphite).",
    "Clean with dry, oil-free compressed air only: no liquids, solvents or ultrasonic bath "
    "(porous). Handle with clean gloves; store bagged with desiccant.",
    "Re-usable. After each firing measure the throat at three axial positions and enter it as "
    "THROAT_D (README). Re-use while the throat is ≤ " + DIA + "23.9 and uncracked, with "
    "no chips on the flow path or the OD seal surface; otherwise scrap.",
    "Used on SRM100-000 item 3. Not fitted on proof assembly SRM100-001 (proof dummy "
    "SRM100-120 in its place).",
]
y_end = sh.notes(X0, 282.0, notes, 153.0)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")

if __name__ == "__main__":
    print("notes end y", round(y_end, 1), " table bottom", round(yb, 1))
    sh.lint()
    sh.save("nozzle_insert")
