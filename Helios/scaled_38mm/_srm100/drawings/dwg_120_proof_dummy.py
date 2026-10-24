"""SRM100-120 proof dummy (304 stainless): A3, 2:1 half-section, details C (aft
lead-in, 5:1) and D (the proof's fill / bleed port, 4:1).  The dummy's 1/8-27 NPT port
is the motor's only port (G24: item 6 has none): the proof fills through it, with a dip
tube down its passage, and bleeds through it, motor vertical and aft end up (SRM100-001).

View frame: u = motor z (forward to the right), v = radius.  The dummy is modelled in
the motor frame at the insert's place, so every number here is a proof_dummy /
srm_params value.  Datum A = the OD (63.50, the seal surface), datum B = the aft face
that bears on the holder's lip.  Axial features are measured from B.
"""

import math

import srm_dwg as D
import srm_params as P
import proof_dummy as PD
from srm_dwg import DIA, DEG, TIMES, DEPTH, PM, Hatch, Part, Sheet, View, fmt

S = P.nozzle_stations()
R_OD = PD.R_OD
Z0, Z1 = PD.Z0, PD.Z1                   # datum B (aft face), forward face
R_LEAD = R_OD - PD.LEAD_R               # aft face meets the 20 deg lead-in
Z_LEAD = Z0 + P.INSERT_LEAD_IN
R_BRK = R_OD - PD.BRK                   # forward OD break
R_CUP, CR = PD.R_CUP, PD.CR
Z_FLOOR = PD.Z_FLOOR
R_PORT, R_PASS, Z_PORT = PD.R_PORT, PD.R_PASS, PD.Z_PORT
R_LIP = S["r_exit"] + P.HOLDER_LIP_STEP  # holder lip bore at the seat
R_CSK = PD.R_CSK                         # 90 deg thread-entry countersink
Z_CSK = Z0 + (R_CSK - R_PORT)            # countersink meets the tap drill
NPT_P = 25.4 / 27.0
NPT_L1 = 0.1615 * 25.4                   # ASME B1.20.1, 1/8-27: hand-tight engagement
NPT_L3 = 3.0 * NPT_P                     # wrench makeup, 3 threads
R_NPT = (0.37476 * 25.4 + 0.8 * NPT_P) / 2.0   # major at face B, (E1 + h)/2 = 5.136
Z_THR = Z0 + (NPT_L1 + NPT_L3)           # min full thread L1 + L3 = 6.92 from face B


def r_npt(z):
    """Major radius of the tapered internal thread at z (1:16 on the diameter)."""
    return R_NPT - (z - Z0) / 32.0


# the thin major line starts where it meets the countersink cone r = R_CSK - (z - Z0)
Z_NPT0 = Z0 + (R_CSK - R_NPT) / (1.0 - 1.0 / 32.0)
F_PROOF = P.MEOP * P.PROOF_X_MEOP * math.pi / 4.0 * P.INSERT_OD ** 2 / 1000.0   # kN on the lip
F_FIRE = P.insert_thrust() / 1000.0                                           # kN, insert at MEOP


def _mass_g(src, rho):
    """Adaptive BRepGProp volume (build123d's .volume reads low on trimmed faces) x rho."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(D.load(src).wrapped, props, 1e-9, True)
    return round(props.Mass() * rho * 1000.0, 1)


MASS = _mass_g("proof_dummy.step", P.SS_RHO)     # 304 at 8.00 g/cm3 -> 1414.1

sh = Sheet("SRM100-120", "PROOF DUMMY",
           "Hydrostatic-proof stand-in for insert SRM100-104 - 304 stainless",
           size="A3", material="AISI 304 / 1.4301, annealed\nround bar to ASTM A479",
           mass_g=MASS, scale="2:1", finish="Ra 3.2")


def mask(first, pad=0.7):
    """White ground behind the texts sh.texts[first:], over the hatching (z 2) and under
    every line (z >= 3): ISO 128-50, hatching interrupted for inscriptions."""
    for t in sh.texts[first:]:
        bb = t.get_window_extent(sh._renderer).transformed(sh.ax.transData.inverted())
        sh.fill([(bb.x0 - pad, bb.y0 - pad), (bb.x1 + pad, bb.y0 - pad),
                 (bb.x1 + pad, bb.y1 + pad), (bb.x0 - pad, bb.y1 + pad)], color="w", z=2.5)


part = Part("proof_dummy.step", hatch=Hatch(45, 2.0))
v = View(sh, part, origin=(140, 185), scale=2.0, look="side", section="half")

# ---- main view -------------------------------------------------------------------
v.dim_h((Z0, R_LEAD), (Z1, R_BRK), off=14.0, tol=("0", "-0.05"))            # 83.21
v.dim_dia(Z_LEAD, R_OD, at=Z0 - 8.0, tol=("0", "-0.05"), arrows=(False, True),
          text=DIA + f"{2 * R_OD:.2f}")          # 63.50: two places, as its deviation
v.datum((Z0 - 8.0, -R_OD), "A", (0, -1), length=5.0)
v.finish((0.0, R_OD), "Ra 0.8")
v.datum((Z0, -28.5), "B", (-1, 0), length=5.0)
v.fcf((Z0, -18.0), 9.0, -3.2, ["perpendicularity", "0.02", "A"])
v.fcf((Z1, -18.0), -34.0, -3.2, ["parallelism", "0.05", "B"])
# cup: bore, floor corner, closed end
v.dim_dia_half(0.0, R_CUP, at=10.0)                                            # 40
a135 = math.radians(135.0)
v.leader((Z_FLOOR + CR + CR * math.cos(a135), R_CUP - CR + CR * math.sin(a135)),
         8.0, -8.0, ["R" + fmt(CR)])                                           # R2, radial
n0 = len(sh.texts)
v.dim_h((Z0, 14.0), (Z_FLOOR, 14.0), at=14.0)                                  # 15
mask(n0)
# edge breaks
v.leader((Z1 - PD.BRK / 2, R_OD - PD.BRK / 2), 10.0, 5.0, ["0.5" + TIMES + "45" + DEG])
v.leader((Z1 - PD.BRK / 2, R_CUP + PD.BRK / 2), 10.0, -6.0, ["0.5" + TIMES + "45" + DEG])
c = v.detail((Z0 + 1.6, 28.6), 4.2, 5.0, (62, 72), "C", circle_label_ang=60)
DR, DS, DO = 8.15, 4.0, (182.0, 80.0)          # detail D: view radius, scale, paper centre
d = v.detail((Z0 + 7.5, 2.5), DR, DS, DO, "D", circle_label_ang=300)
# caption under the kit's 'D (4:1)' label (baseline DO_y - DR*DS - gap 5 - 3.5)
sh.text(DO[0], DO[1] - DR * DS - 5.0 - 3.5 - 5.0, "FILL / BLEED PORT (the motor's only port)",
        D.H, ha="center")

# ---- detail C: aft lead-in (5:1) ---------------------------------------------------
c.dim_h((Z0, R_LEAD), (Z_LEAD, R_OD), off=8.0)                  # 3, clear of the circle
c.dim_ang((Z_LEAD, R_OD), 180.0, 180.0 + 20.0, 13.0, ext=True, dec=0,
          text_r=15.8)                                                          # 20 deg

# ---- detail D: fill / bleed port (4:1) -------------------------------------------------------
# ISO 6410-1 in section: the tapered major diameter drawn thin, from where it meets the
# countersink cone to the thread limit; the thread limit drawn thick, across to the axis,
# at the minimum full thread L1 + L3 from face B.  The tap drill runs on to its depth
# (model), room for the tap's 2 ... 3 thread chamfer.
for vw in (v, d):
    vw.line([(Z_NPT0, r_npt(Z_NPT0)), (Z_THR, r_npt(Z_THR))], D.THIN)
    vw.line([(Z_THR, 0.0), (Z_THR, r_npt(Z_THR))], D.THICK)
d.leader((Z0 + 1.0, r_npt(Z0 + 1.0)), -14.0, -24.0,
         ["1/8-27 NPT per ASME B1.20.1", "gauge with L1 plug gauge " + PM + "1 turn",
          "tap drill " + DIA + fmt(2 * R_PORT) + ' (11/32") ' + DEPTH + fmt(Z_PORT - Z0)])
d.dim_h((Z0, 2.0), (Z_THR, 2.0), at=2.0, suf=" MIN")                            # 6.92
d.leader((Z0 + (Z_CSK - Z0) / 2.0, (R_CSK + R_PORT) / 2.0), -10.0, 12.0,
         ["CSK " + DIA + fmt(2 * R_CSK) + " " + TIMES + " 90" + DEG])
d.dim_dia_half(Z0 + 13.0, R_PASS, at=Z0 + 13.0)                                  # 6

# ---- notes -----------------------------------------------------------------------------
X0 = 252.0
notes = [
    "Material: AISI 304 / 1.4301 austenitic stainless, annealed, round bar to ASTM A479. "
    "Material certificate EN 10204 3.1.",
    "PROOF ONLY: never fired, never fitted for a firing. It takes the graphite insert "
    "SRM100-104's place in the hydrostatic proof SRM100-001, so the holder's lip, its bore "
    "gland and all five O-rings are proofed while the graphite stays dry.",
    "Carries the insert's fits. OD " + DIA + f"{2 * R_OD:.2f}" + " 0/-0.05: slip fit in the "
    "SRM100-102 bore " + DIA + f"{P.INSERT_BORE_D:.2f}" + " +0.025/0, slides in by hand, aft "
    "end first; do not press. Length " + fmt(Z1 - Z0) + " 0/-0.05 against the seat depth "
    + fmt(P.Z_HOLDER_FACE - Z0) + " +0.05/0: forward face flush to 0.10 below the holder "
    "face.",
    "Face B bears on the holder's lip from " + DIA + fmt(2 * R_LIP) + " out to " + DIA
    + fmt(2 * R_LEAD) + " (" + fmt(R_LEAD - R_LIP) + " radial). Closed, the dummy puts "
    + f"{F_PROOF:.0f}" + " kN on the lip at " + fmt(P.MEOP * P.PROOF_X_MEOP, 1) + " MPa, against "
    "the insert's " + f"{F_FIRE:.0f}" + " kN at MEOP " + fmt(P.MEOP, 1) + " MPa.",
    "OD Ra 0.8, free of axial scratches: the AS568-230 O-ring runs on it. Blend the "
    "lead-in into the OD, burr-free: the O-ring passes over it on assembly.",
    "Port (detail D): the proof's fill and bleed port, the motor's only port (item 6 has "
    "none), on the axis of face B, reached through the holder's lip bore; the " + DIA
    + fmt(2 * R_PASS) + " passage takes the " + DIA + fmt(P.PROOF_DIP_TUBE_OD) + " dip tube "
    "(SRM100-001). 1/8-27 NPT per ASME B1.20.1: 90" + DEG + " countersink " + DIA
    + fmt(2 * R_CSK) + ", tap drill " + DIA + fmt(2 * R_PORT) + ' (11/32") ' + DEPTH
    + fmt(Z_PORT - Z0) + ", 118" + DEG + " point, then the passage into the cup. Full thread "
    + fmt(Z_THR - Z0) + " min (L1 + L3): taper "
    "pipe tap with a 2 ... 3 thread chamfer. Rig tee: Loctite 567 or equal on the male "
    "thread, first 2 threads clear; no PTFE tape.",
    "Deburr, clean and degrease; passivate to ASTM A967. No chips or oil left in the cup, "
    "passage or port.",
    "Inspect 100 %: OD at three axial positions, length, perpendicularity to A, port with a "
    "1/8-27 NPT L1 plug gauge " + PM + "1 turn. Record the values against the serial.",
    "Mark SRM100-120, serial and PROOF ONLY on the forward face, between " + DIA
    + fmt(2 * (R_CUP + PD.BRK + 1.5)) + " and " + DIA + fmt(2 * (R_BRK - 1.25))   # 44 .. 60
    + ", by laser or dot-peen, 2 mm characters, 0.05 deep max.",
    "Extract as the insert: holder out, the insert push sleeve (tooling) through the lip "
    "bore onto face B. Never lever or knock.",
    "USED ON: SRM100-001 hydrostatic proof assembly, item 17, in place of the insert "
    "SRM100-104 (item 3).",
]
sh.notes(X0, 282.0, notes, 153.0)
sh.general_finish(sh.tb[0] + 2.0, sh.tb[3] + 3.0, "Ra 3.2")

if __name__ == "__main__":
    sh.lint()
    sh.save("proof_dummy")
