"""SRM100-106 nozzle cap (LDPE moisture / debris cap, igniter-lead retainer): A3,
2:1 half-section, detail C (cone wall, 5:1), detail D (lead hole, 5:1),
installation view (2:1, reference) and notes.

View frame: the MOTOR frame (nozzle_cap.py is modelled there, identity placement):
u = motor z (forward to the right), v = radius.  The plug sits in the graphite's 15 deg
divergent, its flange on the holder's aft face.
Datum A = the flange's forward (seat) face, on the holder's aft face; axial stations are
measured from A.  Datum B = the axis of the DIA 51.9 cylinder (turned with the cone).

Tolerancing: the STEP is the maximum-material cap (0.05 radial clearance to the nominal
divergent); every tolerance on the cone's diameters and stations goes towards clearance
(smaller / shorter), so the plug can never wedge in the graphite.

Local primitives: the tape strip and the igniter leads in the installation view are
drawn as phantom lines (sheet.line style 'phantom') through iv.pt; the cone wall's
normal thickness uses a local aligned dimension (_wall_dim) that puts its text on the
free (inner) side, because View.dim_al always puts an 'out' text beyond the upper point.
"""

import math

import numpy as np

import srm_dwg as D
import srm_params as P
import srm_assembly as A
import nozzle_cap as NC
from srm_dwg import DIA, DEG, TIMES, PM, Hatch, Part, Sheet, View, fmt

S = P.nozzle_stations()
T15 = math.tan(math.radians(P.DIV_HALF_DEG))
Z_EXIT, Z_FWD, Z_SEAT, Z_BACK = NC.Z_EXIT, NC.Z_FWD, NC.Z_SEAT, NC.Z_BACK
R_FL = P.CAP_FLANGE_OD / 2.0            # 33.0
R_CYL = NC.r_out(Z_EXIT)                # 25.95  cylinder through the lip, cone base
R_END = NC.r_out(Z_FWD)                 # 23.27  cone at the plug end
R_IN = R_CYL - NC.OFFSET                # 24.71  bore
Z_IN = Z_FWD - P.CAP_WALL               # inner face of the end wall
R_HOLE = NC.R_HOLE                      # 1.5
WALL = P.CAP_WALL                       # 1.2, normal to the cone and at the end
MASS = 6.6                              # 7161.5 mm3 (STEP) x 0.92 g/cm3
CLR = S["r_exit"] - R_CYL               # 0.05 radial at maximum material, nominal lip
R_AFT_BODY = P.INSERT_BORE_D / 2 + P.HOLDER_AFT_WALL   # 35.79, holder aft body (labels)
TAPE_ON_BODY = 14.0                     # tape end length on the aft body
# G17: the temperature labels on the holder's aft body sit at theta 90 / 270 deg; the two
# tape strips are centred at theta 0 / 180 deg, 90 deg from them.  The installation view's
# upper half is the section at theta 0 (kit "side" look: paper-up = +X), so the strip drawn
# there is the theta 0 strip.
TH = chr(952)
LABEL_TH = (90.0, 270.0)
TAPE_TH = (0.0, 180.0)
assert min(abs((a - b + 180.0) % 360.0 - 180.0) for a in LABEL_TH for b in TAPE_TH) == 90.0
NBSP = chr(0xA0)            # no-break space (textwrap never splits it): value + tol / unit

sh = Sheet("SRM100-106", "NOZZLE CAP",
           "Moisture / debris cap - LDPE plug in the 15° divergent",
           size="A3", material="LDPE natural, unfilled, rod " + DIA + "70",
           mass_g=MASS, scale="2:1", finish="Ra 3.2")


def detail(view, *a, **k):
    """View.detail, labelled 'DETAIL <L> (<scale>)' (the kit's label is the last text)."""
    dv = view.detail(*a, **k)
    t = view.sheet.texts[-1]
    t.set_text("DETAIL " + t.get_text())
    return dv


def _wall_dim(view, p_out, n_in, t, tail=5.0):
    """Local aligned dimension of a wall of thickness t (view units): outer point p_out,
    unit inward normal n_in (view).  Arrows outside pointing in, text beyond the inner
    point (on the free side), along the dimension line."""
    s = view.sheet
    a = view.pt(*p_out)
    b = view.pt(p_out[0] + n_in[0] * t, p_out[1] + n_in[1] * t)
    m = D._unit(b - a)                       # outer -> inner
    val = fmt(t, 2)
    tw = s.text_width(val, D.H)
    s.arrow(a, m)
    s.arrow(b, -m)
    s.line([a - m * tail, b + m * (tail + tw + 1.0)], D.THIN)
    ang = math.degrees(math.atan2(m[1], m[0]))
    rd = -m if (ang <= -90.0 or ang > 90.0) else m     # readable direction
    rot = math.degrees(math.atan2(rd[1], rd[0]))
    c = b + m * (tail - 1.0 + tw / 2)
    nrm = D._perp(rd)
    tp = c + nrm * D.TEXT_GAP - rd * tw / 2
    s.text(tp[0], tp[1], val, D.H, rot=rot)


# ---- main view: half-section, 2:1 -------------------------------------------------------
OX, OY = 70.0 - 2.0 * Z_BACK, 150.0      # the flange's aft face at paper x 70
v = View(sh, Part("nozzle_cap.step", hatch=Hatch(45, 1.2)), origin=(OX, OY), scale=2.0,
         look="side", section="half")

# flange and bore (general tolerances)
v.dim_dia(Z_BACK, R_FL, at=Z_BACK - 5.0)
v.dim_dia_half(Z_BACK + 2.5, R_IN, at=Z_BACK + 2.5)
# the plug: diameters at maximum material, tolerances towards clearance
v.dim_dia(Z_FWD, R_END, at=Z_FWD + 5.0, tol=("0", "-0.2"), shift=24.0)
v.dim_dia(Z_EXIT, R_CYL, at=Z_FWD + 10.0, tol=("0", "-0.2"), shift=24.0)
v.datum((Z_FWD + 10.0, -R_CYL), "B", (0, -1), length=5.0)
# stations from A (seat face)
v.dim_h((Z_SEAT, R_FL), (Z_EXIT, R_CYL), off=6.0, tol=("0", "-0.2"))
v.dim_h((Z_SEAT, R_FL), (Z_FWD, R_END), off=13.0, tol=("0", "-0.2"))
v.datum((Z_SEAT, 30.5), "A", (1, 0), length=3.0)
# flange thickness and overall length (reference) below
v.dim_h((Z_BACK, -R_FL), (Z_SEAT, -R_FL), off=-6.0)
v.dim_h((Z_BACK, -R_FL), (Z_FWD, -R_END), off=-14.0, ref=True)
# seat face square to B
v.fcf((Z_SEAT, -29.5), 6.0, -3.25, ["runout", "0.1", "B"])
# details
c = detail(v, (Z_EXIT + 4.5, 24.6), 5.6, 5.0, (185.0, 180.0), "C", circle_label_ang=60)
d = detail(v, (Z_FWD - 0.6, 1.0), 3.0, 5.0, (190.0, 250.0), "D", circle_label_ang=30)

# ---- detail C (5:1): cone wall ----------------------------------------------------------
# cone half-angle (reference: follows from DIA 51.9, DIA 46.54 and 10)
c.dim_ang((Z_EXIT, R_CYL), -P.DIV_HALF_DEG, 0.0, 30.0, text="(" + fmt(P.DIV_HALF_DEG, 0) + DEG + ")",
          text_r=18.0)
# wall normal to the cone
u_w = Z_EXIT + 8.3
n_in = (-math.sin(math.radians(P.DIV_HALF_DEG)), -math.cos(math.radians(P.DIV_HALF_DEG)))
_wall_dim(c, (u_w, NC.r_out(u_w)), n_in, WALL)
# runout of the cone to B
u_r = Z_EXIT + 6.8
p_r = c.pt(u_r, NC.r_out(u_r))
c.fcf((u_r, NC.r_out(u_r)), 203.0 - p_r[0], 214.0 - p_r[1], ["runout", "0.05", "B"])

# ---- detail D (5:1): lead hole and end wall --------------------------------------------
d.dim_h((Z_IN, 0.6), (Z_FWD, 0.6), at=0.6)                       # end wall 1.2
d.dim_dia_half(Z_IN, R_HOLE, at=Z_IN - 1.4)                      # DIA 3
d.leader((Z_IN, R_HOLE), -14.0, 16.0, ["HOLE EDGES, BOTH ENDS:", "ISO 13715  -0.1 / -0.3"])

# ---- installation view (reference), motor frame, 2:1 -------------------------------------
PL = {n: (st, tr) for g, n, st, tr in A.placements()}
HATCH = {
    "nozzle_holder": Hatch(45, 2.0),
    "nozzle_insert": Hatch(45, 1.5, cross=True),
    "nozzle_cap": Hatch(solid=True),
}
parts = [Part(PL[n][0], PL[n][1], hatch=HATCH[n], name=n) for n in HATCH]
WIN = (-56.0, 0.0, -31.0, 36.0)
IX0, IY0 = 150.0, 22.0                                # paper of the window's lower-left
iv = View(sh, parts, (IX0 - 2.0 * WIN[0], IY0 - 2.0 * WIN[1]), 2.0, section="half", window=WIN,
          axis=False)
iv.centerline((WIN[0], 0.0), (WIN[2], 0.0), ext=0.0)
iv.zigzag((WIN[2], 21.5), (WIN[2], 36.0), ext=0.0)
sh.text(IX0 + (WIN[2] - WIN[0]), IY0 + 2.0 * (WIN[3] - WIN[1]) + 12.0,
        "INSTALLATION (REFERENCE) 2:1", 3.5, ha="center")
# tape strip (adjacent item, phantom): flange aft face, over its rim, holder aft face, body
tt = 0.4
tape = [(Z_BACK - tt, 27.5), (Z_BACK - tt, R_FL + tt), (Z_SEAT - tt, R_FL + tt),
        (Z_SEAT - tt, R_AFT_BODY - 0.5), (Z_SEAT + 0.5, R_AFT_BODY + tt),
        (Z_SEAT + TAPE_ON_BODY, R_AFT_BODY + tt)]
sh.line(iv.pts(tape), 0.35, "phantom")
# igniter leads (phantom) along the axis, out through the lead hole
leads = [(WIN[2], 0.7), (WIN[0] + 0.5, 0.7)]
sh.line(iv.pts(leads), 0.35, "phantom")
BAL = [  # (item, target (z, r), balloon paper, end)
    (2, (-45.0, 34.0), (214.0, 86.0), "dot"),
    (3, (-36.0, 27.5), (214.0, 66.0), "dot"),
    (5, (Z_BACK, 26.0), (138.0, 72.0), "arrow"),
]
for n, (z, r), at, end in BAL:
    sh.balloon(iv.pt(z, r), n, at, end=end)
iv.leader((Z_SEAT + 12.0, R_AFT_BODY + tt), 12.0, 5.0,
          ["TAPE AT " + TH + " " + fmt(TAPE_TH[0], 0) + DEG + " (NOTE 6)"], end="none")
iv.leader((WIN[0] + 2.0, 0.7), -6.0, -8.0, ["IGNITER LEADS"], end="none")

# ---- notes -------------------------------------------------------------------------------
# igniter depth from the nozzle exit to the middle of the forward grain (README: about 615)
IGN_DEPTH = PL[f"grain_{P.N_GRAINS}"][1][11] + P.GRAIN_L / 2.0 - S["z_exit"]
X0 = 240.0
notes = [
    "Material: low-density polyethylene PE-LD (ISO 17855), natural, unfilled, unpigmented, "
    "no regrind; density about 0.92 g/cm³. Extruded rod " + DIA + "70. Certificate of conformity.",
    "Turned from rod, one cap per firing. Op 1: face the aft end, bore " + DIA
    + fmt(2 * R_IN, 2) + " and the inner cone to the " + fmt(WALL, 1) + " end wall, drill "
    + DIA + fmt(2 * R_HOLE, 0) + ", turn " + DIA + fmt(2 * R_FL, 0) + ", part off long. "
    "Op 2: on a turned mandrel in the bore, turn the cone, " + DIA + fmt(2 * R_CYL, 2)
    + ", seat face A and the plug end to length. Sharp high-rake tools, light finishing cuts, "
    "no oil. The geometry also suits injection moulding (no undercuts, core drawn aft).",
    "Fit: slip fit in the 15° graphite divergent of insert SRM100-104, " + fmt(CLR, 2)
    + " radial clearance at maximum material. All size and station tolerances on the plug go "
    "towards clearance: at worst it touches the graphite (profile 0.1) along a line and never "
    "wedges; a 15° cone is not self-locking and LDPE cannot score graphite. Seat face A bears "
    "on the aft face of holder SRM100-102, but the graphite (and its divergent) is placed by "
    "the holder's lip, " + fmt(P.HOLDER_LIP_T, 1) + NBSP + "+0.1/0 (SRM100-102): the clearance "
    "holds only with that tolerance. Each 0.1 the lip is thinner moves the divergent "
    + f"{0.1 * T15:.3f}" + " radially onto the plug; " + f"{CLR / T15:.2f}" + " thin gives "
    "contact. " + DIA + fmt(2 * R_CYL, 2) + " clears the lip bore " + DIA
    + fmt(2 * S["r_exit"] + 2 * P.HOLDER_LIP_STEP, 0) + " by over 1 mm and the plug clears "
    "the graphite's 45° exit break (SRM100-104, stations 6-7).",
    "Measure at 20 ± 2 °C (LDPE grows about 0.01 per K on " + DIA + "52). Runouts on the Op 2 "
    "mandrel. Inspect 100 %: plug diameters, stations 6 and 16 from A, walls, " + DIA
    + "3; trial fit in the holder with the insert fitted: enters by hand, flange seats with "
    "no rock, lifts out by hand. Visual: no burrs, swarf, cracks or dirt.",
    "Edges: both ends of the " + DIA + "3 lead hole ISO 13715 -0.1 / -0.3, no burr (it would "
    "cut the lead insulation); other edges per the title block. No marking on the part: "
    "bag each cap and label the bag SRM100-106 A.",
    "Fitting (SRM100-000 sheet 1 note 4; README, static-fire procedure): fitted at assembly "
    "as the debris seal (taped per this note) and kept on through storage and transport. "
    "At the stand it comes off only to insert the igniter (leads shunted, pushed through "
    "the throat about " + fmt(IGN_DEPTH, 0) + NBSP + "mm to the middle of the forward grain's "
    "core, out through the cap's " + DIA + fmt(2 * R_HOLE, 0) + " hole from the plug end), "
    "then it is refitted, flange on the holder, and re-taped with new tape. The igniter "
    "always goes in last, at the stand: never move a motor with an igniter in it. Tape: two "
    "strips of PVC electrical tape, 19 wide, centred at " + TH + " " + fmt(TAPE_TH[0], 0) + DEG
    + " and " + fmt(TAPE_TH[1], 0) + DEG + ", 90" + DEG + " from the temperature labels at "
    + TH + " " + fmt(LABEL_TH[0], 0) + DEG + " and " + fmt(LABEL_TH[1], 0) + DEG + " (SRM100-102 note 8), "
    "from the flange's aft face over its rim and the holder's aft face onto its aft body "
    + DIA + fmt(2 * R_AFT_BODY, 2) + ", the ends at most " + fmt(TAPE_ON_BODY + 1.0, 0)
    + " long there; never over a label, the cup opening or the leads.",
    "Removal: the cap blows out at ignition (a moisture and debris seal, not a pressure "
    "closure). Misfire: disarm and wait at least 60 s (5 min advised for an N motor) "
    "before approaching; cut the tape, pull the cap off along the leads, then remove the "
    "igniter. Single use: scrap the cap after every firing or misfire; never re-use it. "
    "After firing, once the temperature labels have been read and recorded (before "
    "extraction, SRM100-102 note 15), remove the tape residue from the holder with IPA.",
    "Store bagged, clean and dry, away from solvents, heat and sunlight.",
    "Used on SRM100-000 item 5 (nozzle cap: fitted at assembly as the debris seal, refitted "
    "at the stand over the igniter leads). Item numbers in the installation view per "
    "SRM100-000.",
]
y_end = sh.notes(X0, 282.0, notes, 165.0)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2", others=False)

if __name__ == "__main__":
    print("notes end y", round(y_end, 1))
    sh.lint()
    sh.save("nozzle_cap")
