"""SRM100-112 propellant grain (BATES segment, APCP 70/16/14): A3, 1:1 half-section,
detail D (10:1) of the OD / end-face corner with the casting tube and grain spacer in
phantom, propellant and grain data tables, acceptance notes.

View frame: u = the grain's local z (z = 0 at the segment's AFT face, grain.py),
v = radius.  Four instances, at motor z = P.grain_z(i).
Datum A = the OD axis.  The OD is formed by the casting tube's bore (SRM100-111).

The drawing defines geometry, properties and acceptance only: no manufacturing
instructions (legal notice on the sheet).  The casting mandrel is tooling, not drawn.

Local primitives: phantom_clipped() (adjacent parts in phantom, clipped to a detail
circle), the burning-surface thick chain line (ISO 128 type 04.2), a framed notice.
"""

import json
import math

import numpy as np

import srm_dwg as D
import srm_params as P
from srm_dwg import DIA, PM, Hatch, Part, Sheet, View, fmt

R_OD = P.GRAIN_OD / 2.0          # 43.4
R_C = P.GRAIN_CORE / 2.0         # 17.0
L = P.GRAIN_L                    # 147.2
R_TUBE = P.TUBE_OD / 2.0         # 44.2
R_SPC = P.SPACER_ID / 2.0        # 43.0
SPACER_ID_TOL = (0.0, -0.1)      # SRM100-109 bore (G10)
R_SPC_MIN = (P.SPACER_ID + SPACER_ID_TOL[1]) / 2.0                 # 42.95
COVER_LO, COVER_HI = R_OD - R_SPC, R_OD - R_SPC_MIN               # 0.40 ... 0.45 radial
MASK_LO = 2.0 * math.pi * (R_OD ** 2 - R_SPC ** 2)                  # both end faces, mm²
MASK_HI = 2.0 * math.pi * (R_OD ** 2 - R_SPC_MIN ** 2)
MASS = 1266.8

VOL_CM3 = math.pi / 4.0 * (P.GRAIN_OD ** 2 - P.GRAIN_CORE ** 2) * L / 1000.0
RHO_TMD = P.RHO_PROP_ASCAST_SI / 0.98                     # srm_params: 1718 = 98 % of TMD
M_NOM = VOL_CM3 * P.RHO_PROP_ASCAST_SI / 1000.0           # g
M_TOL = 0.015                                             # ASSUMPTION (not in the design basis)
M_LO, M_HI = M_NOM * (1 - M_TOL), M_NOM * (1 + M_TOL)
AB0 = P.grain_burn_area(0.0)                              # mm² per grain
# G21: every Kn names its basis.  Geometric (srm_params.kn, uniform regression): initial and
# max over the web; simulated: the peak of the nominal run (erosive burning, srm_ballistics)
KN0 = P.kn(0.0)
KN_MAX = max(P.kn(x) for x in np.linspace(0.0, P.web(), 4001))
KN_SIM = json.loads((D.ROOT / "out" / "srm_ballistics.json").read_text(encoding="utf-8"))[
    "runs"]["nominal"]
assert f"{KN_SIM['kn_initial']:.1f}" == f"{KN0:.1f}" and KN_MAX < KN_SIM["kn_peak"], KN_SIM
AP_AT = (P.GRAIN_CORE / P.THROAT_D) ** 2

CORE_TOL = ("+0.3", "0")
OD_TOL = PM + "0.1"              # = casting tube bore, SRM100-111
L_TOL = PM + fmt(P.TOL_GRAIN_L)


# ---- local primitives ------------------------------------------------------------
PHANTOM_SHORT = (4.0, 1.0, 0.5, 1.0, 0.5, 1.0)   # mm: 8 mm period, for a 10:1 detail


def phantom_clipped(view, uv, dash=PHANTOM_SHORT):
    """Adjacent part outline (ISO 128 type 05.1 long dash double-dotted), clipped like the
    view's own geometry (a detail's circle).  Local: each segment is drawn on its own with
    a shorter period, so the pattern restarts with a dash at every corner and an 8 mm
    segment still reads as phantom (the kit's 17.5 mm period draws it solid)."""
    s = view.sheet
    ls = (0, tuple(x * D.PT for x in dash))
    for poly in view._clip_lines([view.pts(uv)]):
        poly = np.asarray(poly, float)
        for a, b in zip(poly[:-1], poly[1:]):
            s.ax.plot([a[0], b[0]], [a[1], b[1]], lw=D.THIN * D.PT, color="k",
                      linestyle=ls, dash_capstyle="butt", zorder=3)


def chain_thick(view, uv):
    """Thick long-dashed dotted line (ISO 128 type 04.2): surface with a special
    requirement, drawn just off the surface."""
    view.sheet.line(view.pts(uv), D.THICK, "center")


def notice_box(s, x0, y_top, width, title, text, h=D.H, gap=1.55):
    """Framed notice: bold title, then the text wrapped to the box width."""
    lines, cur = [], ""
    for w in text.split():                       # greedy wrap on measured widths
        t = (cur + " " + w).strip()
        if cur and s.text_width(t, h) > width - 5.0:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    y = y_top - 1.8 - 3.5
    s.text(x0 + 2.0, y, title, 3.5, bold=True)
    y -= 3.5 + 0.6
    for ln in lines:
        s.text(x0 + 2.0, y, ln, h)
        y -= h * gap
    y_bot = y + h * gap - h - 1.6
    s.line([(x0, y_top), (x0 + width, y_top), (x0 + width, y_bot), (x0, y_bot), (x0, y_top)],
           D.THICK)
    return y_bot


# ---- sheet -----------------------------------------------------------------------
sh = Sheet("SRM100-112", "PROPELLANT GRAIN", "BATES segment " + DIA + fmt(P.GRAIN_OD) + " / "
           + DIA + fmt(P.GRAIN_CORE) + " x " + fmt(L) + " - APCP 70/16/14, cast in SRM100-111",
           size="A3", material="APCP 70/16/14 (AP / Al / HTPB)\ncast in casting tube SRM100-111",
           mass_g=MASS, scale="1:1", finish="as cast", edges="ISO 13715  -0.5")

part = Part("grain.step", hatch=Hatch(45, 2.0))
X0, Y0 = 60.0, 197.0
v = View(sh, part, (X0, Y0), 1.0, look="side", section="half")

# legal notice, framed, across the top of the drawing field
notice_box(sh, 24.0, 285.0, 232.0, "NOTICE - PROPELLANT MANUFACTURE",
           "Propellant grains are made only by a person or facility licensed / certified for "
           "propellant manufacture under the applicable local law. This drawing defines "
           "geometry, properties and acceptance only; it is not a manufacturing "
           "instruction and gives no mixing, casting or curing process.")

# length, OD (formed by the tube bore) + datum A, core
v.dim_h((0.0, R_OD), (L, R_OD), off=16.0, tol=L_TOL)
v.dim_dia(0.0, R_OD, at=-13.0, tol=OD_TOL, arrows=(False, True))
v.datum((-13.0, -R_OD), "A", (0, -1), length=5.0)
U_C = 40.0
v.dim_dia_half(U_C, R_C, at=U_C, tol=CORE_TOL, text_at=Y0 + 7.0)
v.fcf((U_C, -3.0), 7.0, -15.0, ["coaxiality", DIA + "0.5", "A"])

# end faces square to A
v.fcf((0.0, -30.0), 8.0, -3.25, ["perpendicularity", "0.1", "A"])
v.fcf((L, -30.0), -27.5, -3.25, ["perpendicularity", "0.1", "A"])

# burning surfaces: core and both end faces (thick chain, just off the surface)
OFF = 1.2
chain_thick(v, [(-OFF, R_OD), (-OFF, R_C - OFF), (L + OFF, R_C - OFF), (L + OFF, R_OD)])
v.leader((L + OFF, 31.0), 8.0, 11.0, ["BURNING SURFACES:", "CORE, BOTH ENDS (NOTE 4)"])
v.leader((L - 25.0, -R_OD), -8.0, -8.0, ["OD INHIBITED BY CASTING TUBE SRM100-111 (NOTE 5)"])

# detail D: OD / end-face corner, tube and spacer in phantom
C = (0.0, R_OD)
d = v.detail(C, 2.4, 10.0, (72.0, 104.0), "D", circle_label_ang=135.0)
phantom_clipped(d, [(0.0, R_OD), (0.0, R_TUBE), (L, R_TUBE)])                  # tube
phantom_clipped(d, [(0.0, R_SPC), (-P.SPACER_T, R_SPC), (-P.SPACER_T, R_TUBE),
                    (0.0, R_TUBE)])                                              # spacer
d.leader((-1.0, 0.5 * (R_SPC + R_TUBE)), 6.0, 26.0,
         ["SPACER SRM100-109, BORE " + DIA + f"{P.SPACER_ID:.1f}" + " 0/" + fmt(SPACER_ID_TOL[1], 1),
          f"COVERS {COVER_LO:.2f} ... {COVER_HI:.2f} OF THE END FACE"], end="dot")
d.leader((1.6, 0.5 * (R_OD + R_TUBE)), 16.0, 12.0, ["CASTING TUBE", "SRM100-111"], end="dot")
d.leader((0.0, R_OD - 1.2), -12.0, -14.0, ["END FACE (BURNING)"])

# ---- propellant data --------------------------------------------------------------
TX, TY = 138.0, 134.0
sh.text(TX, TY + 4.0, "PROPELLANT DATA (srm_params.py)", 3.5)
rows = [["PROPERTY", "VALUE"],
        ["Propellant", P.PROP_NAME + ", mass %"],
        ["Density, as cast", f"{P.RHO_PROP_ASCAST_SI:.0f} kg/m³ = 98 % of TMD {RHO_TMD:.0f}: nominal"],
        ["Density, paper", f"{P.RHO_PROP_SI:.0f} kg/m³ (above TMD): pressure / hardware bound"],
        ["Burn rate, " + fmt(P.T_REF_C, 0) + " °C",
         f"r = a·Pⁿ, P in MPa: a = {fmt(P.BURN_A)} mm/s (at 1 MPa), n = {fmt(P.BURN_N)}"],
        ["Temp. sens.", f"σp = {fmt(P.SIGMA_P * 100)} %/K; grain ≤ {fmt(P.T_GRAIN_MAX_C, 0)} °C fired"],
        ["c*", f"{P.CSTAR:.0f} m/s theoretical; efficiency {fmt(P.CSTAR_EFF)}"],
        ["Heat ratio γ", fmt(P.GAMMA)]]
yb = sh.table(TX, TY, [32, 88], rows, align=["l", "l"])
sh.text(TX, yb - 4.5, "a, n: the paper's generic values; measure on the batch (NOTE 2).", D.H)

# ---- notes ------------------------------------------------------------------------
NX = 262.0
notes = [
    "Material: composite propellant APCP 70/16/14, ammonium perchlorate / aluminium / "
    "HTPB binder in % by mass, cast into casting tube SRM100-111, which stays bonded to the "
    "grain as its OD inhibitor. Properties: PROPELLANT DATA table.",
    "Burn rate: a and n are the paper's generic values, not a batch property. Before "
    "loading, the burn rate of the actual batch is measured (strand burner or sub-scale "
    "motor), entered in srm_params.py and both simulations are re-run. A batch 21 % "
    f"faster than the table reaches MEOP {P.MEOP:.1f} MPa at {fmt(P.T_GRAIN_MAX_C, 0)} °C "
    "(README, Burn-rate sensitivity: Lenoir-Robillard erosion, bound inputs).",
    "Datum A is the OD axis. The OD is the bore of casting tube SRM100-111 (" + DIA
    + fmt(P.TUBE_ID) + " " + OD_TOL + ", coaxial " + DIA + "0.1 to the tube OD); it is not "
    "measured on the grain: simulate A on the tube OD. Sizes at 20 °C.",
    "Burning surfaces (thick chain line): core and both end faces, uninhibited: no "
    "inhibitor, tape, adhesive, release agent or tube overlap on them. Each end face flush "
    "with the tube end within 0.1.",
    "OD inhibited by the casting tube: the grain is bonded to the tube over its full "
    "area; no separation visible at either end, no propellant on the tube OD.",
    f"Mass, net propellant (segment minus its tube): {fmt(M_NOM, 1)} g {PM}{fmt(M_TOL * 100, 1)} % "
    f"= {M_LO:.1f} ... {M_HI:.1f} g (bulk density {M_LO / VOL_CM3 * 1000:.0f} ... "
    f"{M_HI / VOL_CM3 * 1000:.0f} kg/m³). Matched set: each of the 4 grains of a motor within 1 % of their mean. "
    "PROVISIONAL: this tolerance is an assumption, not in the design basis.",
    "Visual, 100 %, core and both end faces: no cracks of any size, no voids or pits "
    "over 1 mm, no foreign matter, no unmixed or discoloured areas; edge chips within "
    "ISO 13715 -0.5. A grain with a crack is rejected. Surfaces as cast: no roughness "
    "value applies.",
    "Dimensional, 100 %: core at both ends, 2 directions 90° apart; web (OD to core) at 4 "
    "positions each end, spread ≤ 0.5; length at 4 positions 90° apart. Record per "
    "grain with the mass and batch.",
    "One batch per motor: the 4 grains and the burn-rate sample of note 2 come from the "
    "same batch.",
    "Mark on the casting tube OD, never on the propellant: SRM100-112, batch, grain no., "
    "cast date, net mass in g. Indelible ink, 3 mm characters. Hazard labelling, storage "
    "and transport per local law.",
    "Installed with the aft face at motor z " + " / ".join(fmt(P.grain_z(i), 1)
                                                         for i in range(P.N_GRAINS))
    + " (grain 1 aft), between grain spacers SRM100-109. Either end may face aft: the "
    "segment is symmetric. The casting mandrel is tooling and is not covered by this "
    "drawing.",
    "Used on SRM100-000 item 10 (4 off). Single use: consumed in the firing; a new "
    "matched set of 4 (note 6) for every firing (README, After every firing).",
]
yn = sh.notes(NX, 282.0, notes, 146.0)

# ---- grain data (reference) --------------------------------------------------------
GY = yn - 8.0
sh.text(NX, GY + 4.0, "GRAIN DATA (REFERENCE, NOMINAL GEOMETRY)", 3.5)
grows = [["ITEM", "VALUE"],
         ["Volume", f"{VOL_CM3:.1f} cm³ per grain"],
         ["Initial burning area", f"{AB0:,.0f} mm² per grain (core + 2 ends)".replace(",", " ")],
         ["Of which under spacers", f"{MASK_LO:.0f} ... {MASK_HI:.0f} mm² = "
          f"{MASK_LO / AB0 * 100:.2f} ... {MASK_HI / AB0 * 100:.2f} % (detail D), not deducted"],
         ["Web; port / throat area", fmt(P.web(), 1) + "; " + fmt(AP_AT) + " (throat " + DIA
          + fmt(P.THROAT_D) + ")"],
         ["Kn, 4 grains, geometric", f"{KN0:.1f} initial, {KN_MAX:.1f} max (uniform regression, "
          "srm_params.kn)"],
         ["Kn, 4 grains, simulated", f"{KN_SIM['kn_peak']:.1f} peak, nominal run (erosive burning, "
          "srm_ballistics)"],
         ["Propellant, 4 grains", f"{4 * M_NOM / 1000:.3f} kg as cast; "
          f"{4 * VOL_CM3 * P.RHO_PROP_SI / 1e6:.3f} kg at {P.RHO_PROP_SI:.0f}"]]
sh.table(NX, GY, [46, 98], grows, align=["l", "l"])

if __name__ == "__main__":
    sh.lint()
    sh.save("grain")
