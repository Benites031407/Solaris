"""SRM100-000 sheet 1 of 3: GENERAL ARRANGEMENT of the loaded SRM-100 motor (A2).

Rocket: Helios.  Main view A-A: half-section of the whole motor at 1:2, axis
horizontal, forward to the right; every row of srm_assembly.placements() is turned
rot = -0.8 deg so that screw / hole 0 (theta 0.8 deg) lies in the cutting plane.
Aft end view (first angle: drawn to the right), details B (5:1, wall build-up at a
spacer) and C (5:1, forward end of the stack), section-hatching key, motor data,
general notes, and the ISO 7573 parts list above the title block.  Every dimension on
this sheet is a reference dimension.

View frame: u = motor z (0 at the case's aft end face, + forward), v = radius.
All numbers come from srm_params, out/mass_budget.json and out/srm_ballistics.json.
"""

import json
import math
import textwrap
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

import srm_dwg as D
import srm_params as P
import srm_assembly as A
from srm_dwg import DIA, DEG, TIMES, THIN, THICK, Hatch, Part, Sheet, View, fmt

OUT = D.ROOT / "out"
MB = json.loads((OUT / "mass_budget.json").read_text())
BAL = json.loads((OUT / "srm_ballistics.json").read_text())
NOM = BAL["runs"]["nominal"]
BND = BAL["runs"]["bound"]
S = P.nozzle_stations()

SC = 0.5                                   # 1:2
ROT = -P.BOLT_OFFSET0                      # hole 0 into the cutting plane
Z_CAP = MB["envelope"]["z_min"]            # cap flange's aft face
Z_FWD = MB["envelope"]["z_max"]            # forward closure's flange face
Z_EXIT = S["z_exit"]                       # nozzle exit plane (graphite aft face)
R_HEAD = MB["envelope"]["max_diameter_mm"] / 2.0
CG_L = MB["cg_loaded_mm_from_case_aft_face"]
CG_E = MB["cg_empty_mm_from_case_aft_face"]
R_CASE = P.CASE_OD / 2.0
R_CG = 2.5                                 # CG symbol radius, paper
TH = "θ"
P1_TH, P2_TH = P.puller_thetas()           # 10, 190: puller P1 carries theta 0 on the closures
P1_TO_H0 = P1_TH - P.BOLT_OFFSET0          # 9.2: hole 0 is this far from P1
assert abs(P1_TH - 10.0) < 1e-9 and abs(P1_TO_H0 - 9.2) < 1e-9, (P1_TH, P1_TO_H0)


def thou(x, dec=0):
    """10495.3 -> '10 495' (ISO digit grouping)."""
    return f"{x:,.{dec}f}".replace(",", " ")


# ---- parts list (ISO 7573): fixed item numbers -------------------------------------
# item, part no. / standard, description, material, STEP stem (mass_budget key)
ITEMS = [
    (1, "SRM100-101", "Motor case", "6061-T6 drawn tube", "case"),
    (2, "SRM100-102", "Nozzle holder (aft closure)", "304 stainless", "nozzle_holder"),
    (3, "SRM100-104", "Nozzle insert", "isomolded graphite", "nozzle_insert"),
    (4, "SRM100-105", "Nozzle insulator", "glass phenolic", "nozzle_insulator"),
    (5, "SRM100-106", "Nozzle cap", "LDPE", "nozzle_cap"),
    (6, "SRM100-103", "Forward closure", "6061-T651", "fwd_closure"),
    (7, "SRM100-107", "Forward insulator", "EPDM", "fwd_insulator"),
    (8, "SRM100-110", "Liner", "paper phenolic", "liner"),
    (9, "SRM100-111", "Casting tube", "spiral-wound kraft", "casting_tube"),
    (10, "SRM100-112", "Propellant grain, BATES", "APCP", "grain"),
    (11, "SRM100-109", "Grain spacer", "linen phenolic", "grain_spacer"),
    (12, "SRM100-108", "Take-up ring", "silicone sponge", "takeup_ring"),
    (13, "AS568-237", "O-ring, case seal", "FKM 90A", "oring_case"),
    (14, "AS568-230", "O-ring, insert seal", "FKM 90A", "oring_insert"),
    (15, "ISO 7380-1 M6" + TIMES + "10-010.9", "Button-head screw, aft", "steel 010.9", "bolt_m6x10"),
    (16, "ISO 7380-1 M6" + TIMES + "16-010.9", "Button-head screw, fwd", "steel 010.9", "bolt_m6x16"),
]
QTY = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 4, 10: 4, 11: 5, 12: 1, 13: 4, 14: 1,
       15: 18, 16: 18}
MASS_G = {1: 2234.4, 2: 1501.2, 3: 311.1, 4: 38.8, 5: 6.6, 6: 770.5, 7: 22.8, 8: 347.5, 9: 30.8,
          10: 1266.8, 11: 1.3, 12: 1.7, 13: 5.1, 14: 3.8, 15: 3.4, 16: 4.7}
ITEM = {stem: n for n, _, _, _, stem in ITEMS}

# the model must agree with the fixed table
_count = {}
for _g, _n, _st, _tr in A.placements():
    _count[Path(_st).stem] = _count.get(Path(_st).stem, 0) + 1
for n, _, _, _, stem in ITEMS:
    mb = MB["parts"][stem]
    assert mb["count"] == QTY[n] == _count[stem], (stem, mb["count"], _count[stem])
    assert f"{mb['mass_each_kg'] * 1000:.1f}" == f"{MASS_G[n]:.1f}", (stem, mb["mass_each_kg"])
_total = sum(MB["parts"][s]["count"] * MB["parts"][s]["mass_each_kg"] for *_, s in ITEMS)
# the budget's parts add up to its loaded mass, and the fixed table (QTY x MASS_G, 0.1 g
# rounding) adds up to the same total within its rounding
_table = sum(QTY[n] * MASS_G[n] for n in QTY)
assert abs(_total - MB["loaded_kg"]) < 1e-6 and abs(_table - 1000.0 * _total) <= 0.05 * sum(QTY.values()), \
    (_total, _table)
M_LOADED_G = round(1000.0 * MB["loaded_kg"])       # title block, g

# ---- section hatching by material class (ISO 128-50) --------------------------------
# metals 45 / 135 alternating between neighbours (case | holder, case | closure),
# graphite cross-hatched, glass phenolic dense 45, propellant a coarse 30 / 120 cross,
# EPDM horizontal, silicone a fine grid; O-rings, the LDPE cap and, at 1:2, the
# sub-1 mm liner / casting tube / spacer walls solid.  Screws are not sectioned.
H_MAIN = {
    "case": Hatch(45, 1.2),
    "nozzle_holder": Hatch(135, 1.5),
    "nozzle_insert": Hatch(45, 1.1, cross=True, offset=0.5),
    "nozzle_insulator": Hatch(45, 0.7, offset=0.5),
    "nozzle_cap": Hatch(solid=True),
    "fwd_closure": Hatch(135, 1.5),
    "fwd_insulator": Hatch(0, 0.7),
    "liner": Hatch(solid=True),
    "casting_tube": Hatch(solid=True),
    "grain": Hatch(30, 3.0, cross=True),
    "grain_spacer": Hatch(solid=True),
    "takeup_ring": Hatch(0, 0.6, cross=True),
    "oring_case": Hatch(solid=True),
    "oring_insert": Hatch(solid=True),
}
# detail B (5:1): the thin sections are wide enough to hatch
H_DET = dict(H_MAIN)
H_DET.update({
    "liner": Hatch(135, 0.8),
    "casting_tube": Hatch(45, 0.8, offset=0.5),
    "grain_spacer": Hatch(90, 0.8, offset=0.5),
})


def make_parts(hatches, skip=()):
    parts = []
    for g, n, st, tr in A.placements():
        k = Path(st).stem
        if n in skip:
            continue
        if k.startswith("bolt"):
            # not sectioned; only the in-plane screw (hole 0) masks the section hatch,
            # the others lie behind the cutting plane
            parts.append(Part(st, tr, cut=False, occlude=n.endswith("_00"), name=n))
        else:
            parts.append(Part(st, tr, hatch=hatches[k], name=n))
    return parts


# ---- annotation bookkeeping for the local crossing / text checker -------------------
SEGS = []


def seg(tag, a, b):
    SEGS.append((tag, np.asarray(a, float), np.asarray(b, float)))


def bal(target, n, at, end="dot", mask=False, halo=False):
    at_, tg = np.asarray(at, float), np.asarray(target, float)
    d = D._unit(tg - at_)
    sh.balloon(tg, n, at_, end=end)
    seg(f"balloon {n}@{at_[0]:.0f}", at_ + d * 4.0, tg)
    if mask:
        mask_leader(tg, at_)
    if halo:        # white ring under the leader dot on a dense hatch (z 2.5: over hatch, under lines)
        t = np.linspace(0.0, 2.0 * np.pi, 33)
        sh.fill(np.c_[tg[0] + (D.DOT_R + 0.6) * np.cos(t), tg[1] + (D.DOT_R + 0.6) * np.sin(t)], "w", z=2.5)


def mask_leader(tip, at, length=D.ARROW_L + 0.8, w=D.ARROW_W / 2 + 0.3):
    """White island in the section hatching around a leader's arrowhead where it
    reaches a solid-black part (O-ring) through hatched metal; solids stay black."""
    tip, at = np.asarray(tip, float), np.asarray(at, float)
    strip = LineString([tip, tip + D._unit(at - tip) * length]).buffer(w, cap_style=2)
    m = strip.intersection(HATCHED).difference(SOLID)
    for g in getattr(m, "geoms", [m]):
        if isinstance(g, Polygon) and not g.is_empty:
            sh.fill(np.asarray(g.exterior.coords), "w", z=2.5)


def lead(view, tip, knee, lines, end="arrow", tag="leader"):
    """Leader from paper `tip` to paper `knee`, reference line + text beyond."""
    tip, knee = np.asarray(tip, float), np.asarray(knee, float)
    at = (tip - view.origin) / view.scale
    e = view.leader(tuple(at), *(knee - tip), lines, end=end)
    seg(tag, tip, knee)
    seg(tag + ":ref", knee, e)
    return e


def reg_dim_h(tag, view, a, b, at):
    pa, pb = view.pt(*a), view.pt(*b)
    y = view.pt(0, at)[1]
    seg(tag + ":line", (pa[0], y), (pb[0], y))
    for p in (pa, pb):
        sg = np.sign(y - p[1])
        seg(tag + ":ext", (p[0], p[1] + sg * D.EXT_GAP), (p[0], y + sg * D.EXT_OVER))


def reg_dia_half(tag, view, u, r, at, beyond=3.0):
    x = view.pt(at, 0)[0]
    tip = np.array([x, view.pt(0, r)[1]])
    foot = view.pt(u, r)
    ay = view.pt(0, 0)[1]
    seg(tag + ":line", tip, (x, ay - np.sign(tip[1] - ay) * beyond))
    if abs(foot[0] - x) > D.EXT_GAP + 0.3:
        sg = np.sign(x - foot[0])
        seg(tag + ":ext", (foot[0] + sg * D.EXT_GAP, foot[1]), (x + sg * D.EXT_OVER, foot[1]))


def faces_of(view, prefix):
    return [pg for i, pg in view.geo["faces"] if view.parts[i].name.startswith(prefix)]


def inside_uv(view, prefix, u, side=1.0):
    """Midpoint (view coords) of the longest radial chord at u through the section
    faces of the parts whose name starts with `prefix`."""
    best = None
    ln = LineString([(u, 0.0), (u, side * 300.0)])
    for pg in faces_of(view, prefix):
        g = ln.intersection(pg)
        for s in getattr(g, "geoms", [g]):
            if isinstance(s, LineString) and not s.is_empty and (best is None or s.length > best.length):
                best = s
    assert best is not None, (prefix, u)
    c = best.interpolate(0.5, normalized=True)
    return c.x, c.y


def top_of(view, prefix):
    """Paper point at the top of the section face (upper half) of a part."""
    pgs = [pg for pg in faces_of(view, prefix) if pg.bounds[3] > 0]
    pg = max(pgs, key=lambda q: q.area)
    u = pg.centroid.x
    g = LineString([(u, 0.0), (u, 300.0)]).intersection(pg)
    vmax = max(max(c[1] for c in s.coords) for s in getattr(g, "geoms", [g]))
    return view.pt(u, vmax)


def cg_symbol(p, r=R_CG):
    """Centre-of-gravity symbol: circle, quadrants 1 and 3 black."""
    p = np.asarray(p, float)
    t = np.linspace(0.0, 2.0 * np.pi, 73)
    sh.fill(np.c_[p[0] + r * np.cos(t), p[1] + r * np.sin(t)], "w", z=5.5)
    for a0 in (0.0, 180.0):
        tt = np.radians(np.linspace(a0, a0 + 90.0, 25))
        sh.fill(np.vstack([p, np.c_[p[0] + r * np.cos(tt), p[1] + r * np.sin(tt)]]), "k", z=5.6)
    sh.circle(p, r, THIN, z=5.7)
    sh.line([p - (r, 0), p + (r, 0)], THIN, z=5.7)
    sh.line([p - (0, r), p + (0, r)], THIN, z=5.7)


# ---- general notes (text; drawn in two columns after the parts list) ------------------
# defined before the views so that leaders and parts-list lines can cite note numbers
steps = " / ".join(fmt(p, 1) for p in P.PROOF_STEPS_MPA)
tqf = "-".join(fmt(t, 1) for t in P.BOLT_TORQUE_FWD_NM)
tqa = "-".join(fmt(t, 1) for t in P.BOLT_TORQUE_AFT_NM)
# G1-rev: seal-zone A band and the plug offsets / tolerances
assert P.TOL_BORE[0] == 0.0 and P.TOL_LAND[1] == 0.0 and P.TOL_GROOVE[1] == 0.0
A_TXT = f"{P.CASE_ID:.3f} ≤ A ≤ {P.SEAL_A_MAX:.3f}"
# G18: the screw heads sit this far from each end face
Z_HEADS = P.bolt_z_aft()
assert abs((P.CASE_L - P.bolt_z_fwd()) - Z_HEADS) < 1e-9, (P.CASE_L, P.bolt_z_fwd(), Z_HEADS)
# G17 / G19 bands on the case OD, as SRM100-101 states them (MARK, LABEL_Z there)
MARK_Z, LABEL_Z = (20.0, 45.0), (20.0, 35.0)       # from each end face / from the aft face
Z_COLLAR = 50.0                                    # G18: collar at least this far from the end
assert Z_COLLAR > max(MARK_Z[1], LABEL_Z[1], Z_HEADS)
notes = [
    "Assemble per sheet 2 (aft end: items 2-5, 13-15) and sheet 3 (liner, grain stack and "
    "forward closure).",
    f"Hydrostatic proof per SRM100-001 before the first firing and after any repair, any "
    f"retired-and-replaced part, or a temperature label reading ≥ 232 °C: {steps} MPa, "
    f"{P.PROOF_HOLD_S:.0f} s holds, relief valve {fmt(P.PROOF_RELIEF_MPA)} MPa, decay "
    f"≤ {P.PROOF_DECAY_MAX * 100:.0f} %, permanent set ≤ {fmt(P.PROOF_SET_MAX)} mm. The proof "
    "build uses proof dummy SRM100-120 in place of item 3 (item 14 stays); items 4, 5 and 7-12 "
    "are not fitted. "
    "Never wet or hydro-test the graphite.",
    "ENERGETIC MATERIAL: item 10 (APCP) makes this an N-class research motor. Make, store, "
    "transport and fire it only as local law allows and under the Tripoli Research (Level 3) "
    "and NFPA 1127 rules; minimum distance for N: 1000 ft (≈ 305 m). The site RSO's rules govern.",
    "Nozzle cap item 5: fitted at assembly as the debris seal, taped per SRM100-106 note 6, "
    "kept on through storage and transport. At the stand it comes off only to insert the "
    "igniter (leads shunted, out of its " + DIA + f"{fmt(P.CAP_LEAD_HOLE)} hole), then it is "
    "refitted and re-taped with new tape. It blows out at ignition.",
    f"The igniter is not part of this drawing (README: {fmt(P.IGNITER_CHARGE_G)} g BKNO3 or "
    f"pyrogen, tube ≤ {DIA}{fmt(P.IGNITER_TUBE_D)} {TIMES} {fmt(P.IGNITER_TUBE_L_MAX)}, dual-bridge "
    "e-match). It goes in last, at the stand, leads shunted. Never move the motor with an "
    "igniter in it.",
    f"Screws, new ISO 7380-1 010.9 every firing: 18 {TIMES} item 15 at {tqa} N·m, nickel "
    f"anti-seize on the threads only, head face dry; 18 {TIMES} item 16 at {tqf} N·m with "
    "Loctite 243. Tighten criss-cross (opposite pairs) in 3 passes, sheets 2 and 3. Never "
    "interchange the lengths: an M6" + TIMES + "16 in item 2 bottoms with its head proud, an "
    "M6" + TIMES + "10 in item 6 engages only 1 d.",
    f"O-rings 13, 14: {P.ORING_COMPOUND}, new every firing. Lube them, the liner OD and the "
    f"insulator edges with {P.LUBE}. Bond item 7 to item 6 with RTV106 or equal on SS4004P "
    "primer, bondline 0.1-0.2 (sheet 3).",
    "Seal zones of item 1, both ends: each honed to the smallest diameter that cleans it up, "
    f"A (the smallest reading in the zone, recorded per zone, SRM100-101 note 4), {A_TXT}, "
    f"held to A +{P.TOL_BORE[1]:.3f}/0, Ra 0.4 (0.8 max); the bore is ≤ "
    f"{P.CASE_BORE_MAX:.2f} everywhere. Items 2 and 6 are cut to their own case zone's A: land "
    f"A - {P.CASE_ID - P.PLUG_OD:.2f} 0/{P.TOL_LAND[0]:.2f}, groove bottom "
    f"A - {P.CASE_ID - P.ORING_GROOVE_D:.2f} 0/{P.TOL_GROOVE[0]:.2f}.",
    "Each case end and its closure are a match-drilled, serialised pair. " + TH + " 0 is carried "
    "on item 1 by hole 0, the scribed clocking line and the AFT / FWD engraving; on items 2 "
    f"and 6 by puller P1 at {TH} {P1_TH:.0f}{DEG} (r {fmt(P.HOLDER_PULLER_R)} on item 2, "
    f"r {fmt(P.PULLER_R)} on item 6). Hole 0 ({TH} {fmt(P.BOLT_OFFSET0, 1)}{DEG}) is "
    f"{fmt(P1_TO_H0, 1)}{DEG} clockwise of P1 seen from forward and {fmt(P1_TO_H0, 1)}{DEG} "
    f"counter-clockwise seen from aft (end view); keyed {fmt(P.BOLT_OFFSET0, 1)}{DEG} off the "
    f"20{DEG} pattern, a pair goes together one way only.",
    "Marking and temperature labels per SRM100-101 note 8 (item 1) and SRM100-102 note 8 "
    "(item 2); marking of item 6 per SRM100-103 note 11. Labels: "
    f"irreversible 177 / 204 / 232 / 260 °C strips, new for every firing, at {TH} 90{DEG} "
    f"and 270{DEG} on the item 1 OD at z {fmt(LABEL_Z[0])}-{fmt(LABEL_Z[1])} and the item 2 aft "
    "body " + DIA
    + f"{2 * (P.INSERT_BORE_D / 2.0 + P.HOLDER_AFT_WALL):.2f}, clear of the cap tape. After "
    "firing read and record them before extraction; ≥ 232 °C: retire or re-proof that end "
    "(note 2).",
    "No pressure port: item 6 is solid (no port, no pocket) and item 7 is a full disc. The motor "
    "is fired "
    "without a chamber transducer; the static-fire record is the load cell. A transducer needs "
    "a new, ported item 6 and a re-proof. The proof fills and bleeds through SRM100-120's port "
    "(SRM100-001).",
    f"Liner item 8: cut to the measured cavity minus {fmt(P.LINER_FLOAT, 1)} float. Check the "
    "float by depth gauging before item 6 goes in, not with a feeler (the gap is closed off). "
    "Take-up ring item 12: 3.2, 4.8 or 6.4 sheet chosen from the measured gap for 25-50 % "
    "compression. Both per sheet 3.",
    "After every firing replace items 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, all 36 screws "
    "(items 15, 16) and the temperature labels; re-use items 1, 2, 6 after inspection "
    f"(SRM100-101 R10 for the case), and item 3 while the throat is ≤ {DIA}23.9 and uncracked.",
    f"Static fire: item 6's forward face is the thrust face, flat from the axis to "
    f"{DIA}{fmt(P.FLANGE_OD)}, broken only by the {P.PULLER_N} M6 puller holes at r {fmt(P.PULLER_R)}; a "
    "load cell or button bears anywhere clear of them. Flight: the "
    "airframe needs a " + DIA + "108 keep-out for the screw heads and a thrust ring or a "
    "forward-closure thrust path.",
    "All dimensions on this sheet are reference dimensions. Masses and CG are from the STEP "
    "solids (mass_budget.json); CG measured forward from the case's aft end face.",
    "Tooling, referenced by name only: acetal hole plugs, push sleeve, casting mandrel, "
    f"puller bridge with a split clamp collar ({2 * R_CASE:.1f} bore) on the case OD "
    f"≥ {fmt(Z_COLLAR)} from the end being extracted, clear of the screw heads {fmt(Z_HEADS)} "
    f"from each end face ({DIA}{2 * R_HEAD:.2f} sweep), the labels and the marking "
    f"{fmt(MARK_Z[0])}-{fmt(MARK_Z[1])} from each end face.",
    "Proof dummy SRM100-120 and proof assembly SRM100-001 are proof hardware only: never fired, "
    "not part of this assembly.",
]


def note_no(prefix):
    return 1 + next(i for i, s in enumerate(notes) if s.startswith(prefix))


N_LUBE = note_no("O-rings 13, 14")
N_MARK, N_CLOCK = note_no("Marking and temperature labels"), note_no("Each case end")
# cited by number from other sheets: note 4 (sheet 2, SRM100-106), note 11 (sheet 3 note 14),
# note 13 (SRM100-102): the numbers must not move
assert (note_no("Nozzle cap item 5"), note_no("No pressure port"), note_no("After every firing")) \
    == (4, 11, 13)

# =====================================================================================
sh = Sheet("SRM100-000", "GENERAL ARRANGEMENT", "SRM-100 motor, loaded - parts list, motor data",
           size="A2", material="See parts list", mass_g=M_LOADED_G, scale="1:2", sheet=(1, 3),
           rev="A", doc_type="ASSEMBLY DRAWING", finish=None, edges="-")

# ---- main view A-A: half-section, forward to the right -------------------------------
X0, Y0 = 72.0, 318.0                       # paper position of motor z 0 on the axis
PARTS_MAIN = make_parts(H_MAIN)
v = View(sh, PARTS_MAIN, origin=(X0, Y0), scale=SC, look="side", section="half", rot=ROT)
v.label("A-A", gap=6.0)
HATCHED = unary_union([v._paper_poly(pg) for i, pg in v.geo["faces"]])
SOLID = unary_union([v._paper_poly(pg) for i, pg in v.geo["faces"] if PARTS_MAIN[i].hatch.solid])


def mask_ext(x, y0, y1, w=0.45):
    """White gap in the section hatching where an extension line crosses it."""
    m = box(x - w, y0, x + w, y1).intersection(HATCHED)
    for g in getattr(m, "geoms", [m]):
        if isinstance(g, Polygon) and not g.is_empty:
            sh.fill(np.asarray(g.exterior.coords), "w", z=2.5)


# case aft end face -> nozzle exit plane (graphite aft face)
v.dim_h((Z_EXIT, S["r_exit"]), (0.0, R_CASE), at=66.0, dec=1, ref=True)
reg_dim_h("d_exit", v, (Z_EXIT, S["r_exit"]), (0.0, R_CASE), 66.0)
mask_ext(v.pt(Z_EXIT, 0)[0], v.pt(0, S["r_exit"])[1] + D.EXT_GAP, v.pt(0, 66.0)[1] + D.EXT_OVER)
# case OD (lower, outside half) and max diameter over the screw heads (forward end)
v.dim_dia_half(560.0, -R_CASE, at=560.0, pre="(", suf=")")
reg_dia_half("d_case", v, 560.0, -R_CASE, 560.0)
U_HEADS = (430.0 - X0) / SC
v.dim_dia_half(P.bolt_z_fwd(), R_HEAD, at=U_HEADS, pre="(", suf=")")
reg_dia_half("d_heads", v, P.bolt_z_fwd(), R_HEAD, U_HEADS)
# centres of gravity, from the case's aft end face
AT_CGE, AT_CGL, AT_L = (268.0 - Y0) / SC, (260.0 - Y0) / SC, (250.0 - Y0) / SC
v.dim_h((0.0, -R_CASE), (CG_E, -R_CG / SC), at=AT_CGE, dec=0, ref=True)
reg_dim_h("d_cge", v, (0.0, -R_CASE), (CG_E, -R_CG / SC), AT_CGE)
v.dim_h((0.0, -R_CASE), (CG_L, -R_CG / SC), at=AT_CGL, dec=0, ref=True)
reg_dim_h("d_cgl", v, (0.0, -R_CASE), (CG_L, -R_CG / SC), AT_CGL)
# overall length: nozzle cap's aft face to the forward flange face
v.dim_h((Z_CAP, -P.CAP_FLANGE_OD / 2.0), (Z_FWD, -R_CASE), at=AT_L, dec=1, ref=True)
reg_dim_h("d_len", v, (Z_CAP, -P.CAP_FLANGE_OD / 2.0), (Z_FWD, -R_CASE), AT_L)
for z, s, ha, dx in ((CG_E, "CG EMPTY", "right", -1.5), (CG_L, "CG LOADED", "left", 1.5)):
    p = v.pt(z, 0.0)
    cg_symbol(p)
    sh.text(p[0] + np.sign(dx) * (R_CG - 1.0) + dx, p[1] - 7.0, s, D.H, ha=ha)

# item balloons: row above (section half) and row below (outside half)
Y_TOP, Y_BOT = 372.0, 280.0
cap_face = v.pt(Z_CAP, 24.0)
bal(cap_face, 5, (34.0, Y_TOP), "arrow")
bal(top_of(v, "oring_insert"), 14, (84.0, Y_TOP), "arrow", mask=True)
bal(top_of(v, "oring_aft_inner"), 13, (94.0, Y_TOP), "arrow", mask=True)
bal(v.pt(*inside_uv(v, "nozzle_insert", 25.0)), 3, (104.0, Y_TOP))
zi = 0.5 * (P.Z_HOLDER_FACE + P.Z_LINER_AFT)
bal(v.pt(*inside_uv(v, "nozzle_insulator", zi)), 4, (114.0, Y_TOP))
bal(v.pt(*inside_uv(v, "grain_1", 120.0)), 10, (135.0, Y_TOP))
# 7 and 12 are ballooned in detail C (the take-up ring is 1.5 mm wide at 1:2)
bal(top_of(v, "oring_fwd_outer"), 13, (402.0, Y_TOP), "arrow", mask=True)
# lower row: outside view
bal(v.pt(-30.0, -24.0), 2, (56.0, Y_BOT))


def head_face_uv(z, k):
    """View point on the face-on head of screw k (outside half), off its socket."""
    th = math.radians(P.bolt_thetas()[k] + ROT)
    rh = R_CASE + 1.6
    return z, rh * math.cos(th)


ua, va = head_face_uv(P.bolt_z_aft(), 5)
bal(v.pt(ua, va) + (1.2, -1.3), 15, (86.0, Y_BOT))
bal(v.pt(206.0, -36.0), 1, (170.0, Y_BOT))
uf, vf = head_face_uv(P.bolt_z_fwd(), 5)
bal(v.pt(uf, vf) + (-1.2, -1.3), 16, (398.0, Y_BOT))
bal(v.pt(P.CASE_L + 3.0, -35.0), 6, (413.0, Y_BOT))

# ---- detail B (5:1): wall build-up at a grain spacer ---------------------------------
Z_B = P.spacer_z(1) + P.SPACER_T / 2.0     # centred on the second spacer
R_B = 45.5
v.parts = make_parts(H_DET)                 # detail hatches (the kit's detail() reuses view.parts)
dB = v.detail((Z_B, R_B), 6.0, 5.0, (65.0, 212.0), "B", circle_label_ang=60.0)
v.parts = PARTS_MAIN
lin_uv = (Z_B + 4.0, 0.25 * (P.LINER_OD + P.LINER_ID))
tub_uv = (Z_B + 4.4, 0.25 * (P.GRAIN_OD + P.TUBE_OD))
spc_uv = inside_uv(v, "spacer_1", Z_B)
bal(dB.pt(*lin_uv), 8, (108.0, 222.0))
bal(dB.pt(*tub_uv), 9, (108.0, 205.0))
bal(dB.pt(*spc_uv), 11, (108.0, 190.0))

# ---- aft end view (first angle: seen from aft, drawn to the right) -------------------
XE = 530.0
e = View(sh, make_parts(H_MAIN, skip=("nozzle_cap",)), origin=(XE, Y0), scale=SC, look="aft",
         rot=ROT)
C = np.array([XE, Y0])


def polar(a_deg, r_paper):
    a = math.radians(a_deg)
    return C + r_paper * np.array([math.cos(a), math.sin(a)])


def cut_path_half(view, r_model, letter, ext=4.0):
    """ISO 128-44 cutting-plane path of a half-section in the end view: left leg
    (plane y = 0, x >= 0) and upper leg (x = 0, y >= 0), thick at the ends and the
    bend; one arrow (view direction, paper -v) at the left end."""
    c = view.pt(0.0, 0.0)
    R = r_model * view.scale + ext
    pl, pu = c + (-R, 0.0), c + (0.0, R)
    sh.line([pl, c, pu], THIN, "center")
    sh.line([pl, pl + (5.0, 0.0)], 0.7, cap="butt")
    sh.line([pu, pu - (0.0, 5.0)], 0.7, cap="butt")
    sh.line([c + (-3.0, 0.0), c, c + (0.0, 3.0)], 0.7, cap="butt")
    q = pl + (1.0, 0.0)
    sh.line([q, q + (0.0, -7.0)], THIN)
    sh.arrow(q + (0.0, -7.0), (0.0, -1.0))
    sh.text(q[0] - 2.2, q[1] - 9.8 - 1.75, letter, 3.5, ha="center")
    sh.text(pu[0] + 3.2, pu[1] - 2.5 - 1.75, letter, 3.5, ha="center")
    seg("cutpath:l", pl, c)
    seg("cutpath:u", c, pu)
    seg("cutpath:arrow", q, q + (0.0, -7.0))


cut_path_half(e, R_HEAD + 10.0, "A")
# the 20 deg pattern (holes 11 -> 10, lower right); hole k at paper 180.8 - 20 k
a11, a10 = 180.0 + P.BOLT_OFFSET0 - 20.0 * 11, 180.0 + P.BOLT_OFFSET0 - 20.0 * 10
e.dim_ang((0.0, 0.0), a11, a10, 34.0, ext_from=27.5, dec=0)
for a in (a11, a10):
    seg(f"pattern:ext{a:.0f}", polar(a, 27.5), polar(a, 36.0))
# hole 0: keyed, in plane A-A
R_HD = R_HEAD * SC
tip0 = C + (-(R_HD - 0.0) + 0.75, -2.0)
lead(e, tip0, (488.0, 289.0),
     [f"HOLE 0 ({TH} {fmt(P.BOLT_OFFSET0, 1)}{DEG}), IN PLANE A-A:",
      f"keyed {fmt(P.BOLT_OFFSET0, 1)}{DEG} off the 20{DEG} pattern;",
      f"marking per note {N_MARK}"], tag="hole0")
# puller P1 (theta 10) on item 2 carries theta 0; the leader leaves between heads 1 and 2
A_P1, A_P2 = 180.0 - (P1_TH + ROT), 180.0 - (P2_TH + ROT)       # paper 170.8, -9.2
R_P1 = P.HOLDER_PULLER_R * SC
c_p1 = polar(A_P1, R_P1)
# aim 1.5 deg past the mid-gap angle (150.8): the slanted leader then crosses r 25-26.5
# about centred between heads 1 and 2
aim = polar(180.0 - (P1_TH + 20.0 + ROT) - 1.5, 25.75)
u_p1 = D._unit(aim - c_p1)
knee_p1 = c_p1 + u_p1 * ((351.0 - c_p1[1]) / u_p1[1])
lead(e, c_p1 + u_p1 * (P.PULLER_TAP_DRILL / 2.0 * SC), knee_p1,
     [f"PULLER P1 ({TH} {P1_TH:.0f}{DEG}) CARRIES {TH} 0 ON ITEM 2",
      f"2 {TIMES} M6, r {fmt(P.HOLDER_PULLER_R)}, at {TH} {P1_TH:.0f}{DEG} (P1) and {P2_TH:.0f}{DEG} (P2);",
      f"seen from aft, hole 0 is {fmt(P1_TO_H0, 1)}{DEG} counter-clockwise of P1"], tag="p1")
# P1 -> hole 0, 9.2 deg (CCW on paper = counter-clockwise seen from aft).  The arc is
# short, so the arrows stand outside it with tails (drawn here: kit dim_ang's short-arc
# tails run back over the arc).  Hole 0's ray is the cutting-plane line itself.
R_ANG = 29.5
ta = np.radians(np.linspace(A_P1, 180.0, 16))
sh.line(np.c_[C[0] + R_ANG * np.cos(ta), C[1] + R_ANG * np.sin(ta)], THIN)
for a, sg in ((A_P1, 1.0), (180.0, -1.0)):
    p = polar(a, R_ANG)
    tcw = D._rot(np.array([1.0, 0.0]), a - 90.0)             # clockwise tangent at a
    d_in = -tcw * sg                                         # arrow points into the arc
    sh.arrow(p, d_in)
    sh.line([p, p - d_in * (D.ARROW_L + 2.5)], THIN)
    seg(f"ang92:tail{a:.0f}", p, p - d_in * (D.ARROW_L + 2.5))
ext_a, ext_b = polar(A_P1, R_P1 + P.PULLER_TAP_DRILL / 2.0 * SC + D.EXT_GAP), polar(A_P1, R_ANG + 2.0)
sh.line([ext_a, ext_b], THIN)
seg("ang92:ext", ext_a, ext_b)
sh.text(C[0] - 30.5, C[1] + 7.8, f"{fmt(P1_TO_H0, 1)}{DEG}", D.H, ha="right")
# nozzle exit
a_x = 180.0 + P.BOLT_OFFSET0 - 20.0 * 7.5    # between the heads of holes 7 and 8
lead(e, polar(a_x, S["r_exit"] * SC), polar(a_x, 38.0), ["EXIT (" + DIA + fmt(2 * S["r_exit"]) + ")"],
     tag="exit")
sh.text(XE, Y0 - R_HD - 6.0 - 3.5, "AFT END VIEW (item 5 not shown)", 3.5, ha="center")

# ---- section hatching key (under detail B) -------------------------------------------
KX, KY = 24.0, 164.0
sh.text(KX, KY, "SECTION HATCHING (ISO 128-50)", 3.5, bold=True)
KEY = [
    ([H_MAIN["case"], H_MAIN["nozzle_holder"]], "Metal, alternating: 1 (45" + DEG + "); 2, 6 (135" + DEG + ")"),
    ([H_MAIN["nozzle_insert"]], "Graphite: 3"),
    ([H_MAIN["nozzle_insulator"]], "Glass phenolic: 4"),
    ([H_DET["liner"]], "Paper phenolic: 8 (detail B)"),
    ([H_DET["casting_tube"]], "Spiral-wound kraft: 9 (detail B)"),
    ([H_DET["grain_spacer"]], "Linen phenolic: 11 (detail B)"),
    ([H_MAIN["grain"]], "Propellant, APCP: 10"),
    ([H_MAIN["fwd_insulator"]], "EPDM: 7"),
    ([H_MAIN["takeup_ring"]], "Silicone sponge: 12 (detail C)"),
    ([Hatch(solid=True)], "Solid: 13, 14 (O-rings), 5; at 1:2 also 8, 9, 11"),
    ([], "Not sectioned: screws 15, 16"),
]
y = KY - 9.0
for hs, s in KEY:
    x0 = KX
    w = 12.0 / max(1, len(hs))
    for h in hs:
        v._hatch(Polygon([(x0, y), (x0 + w, y), (x0 + w, y + 5.0), (x0, y + 5.0)]), h)
        x0 += w
    sh.line([(KX, y), (KX + 12.0, y), (KX + 12.0, y + 5.0), (KX, y + 5.0), (KX, y)], THIN)
    sh.text(KX + 15.0, y + 1.3, s, D.H)
    y -= 7.5

# ---- motor data ----------------------------------------------------------------------
MX, MY = 124.0, 244.0                      # top of MOTOR DATA and of the NOTES column 1
sh.text(MX, MY - 3.5, "MOTOR DATA", 3.5, bold=True)
inp = NOM["inputs"]
cls = NOM["class"]
RHO_TH = 1753.0                            # theoretical max, 70/16/14 (srm_params section 1)
# G21: every Kn names its basis; the geometric max is srm_params.kn over the web
# (uniform regression, the sampling of srm_params.self_check), the peak is the nominal run's
KN_GEO_MAX = max(P.kn(i * P.web() / 400.0) for i in range(400))
assert f"{NOM['kn_initial']:.1f}" == f"{P.kn(0.0):.1f}" and KN_GEO_MAX < NOM["kn_peak"], KN_GEO_MAX
assert inp["rho_kg_m3"] == P.RHO_PROP_ASCAST_SI and round(100 * inp["rho_kg_m3"] / RHO_TH) == 98
rows = [
    ["PARAMETER", "VALUE (nominal run unless stated)"],
    ["Propellant", P.PROP_NAME],
    ["Density, as cast", f"{thou(inp['rho_kg_m3'])} kg/m³ ({100 * inp['rho_kg_m3'] / RHO_TH:.0f} % of "
                         f"{thou(RHO_TH)} theoretical)"],
    ["Grains", f"{P.N_GRAINS} {TIMES} BATES, {DIA}{fmt(P.GRAIN_OD)} / {DIA}{fmt(P.GRAIN_CORE)} "
               f"{TIMES} {fmt(P.GRAIN_L)}\nboth ends burning"],
    ["Designation", BAL["designation"]],
    ["Total impulse / class", f"{thou(NOM['impulse_ns'])} N·s / {cls} ({NOM['class_percent']:.1f} % into {cls})\n"
                              "M/N borderline until a static fire"],
    ["Thrust, average / peak", f"{NOM['avg_thrust_n']:.0f} / {NOM['peak_thrust_n']:.0f} N"],
    ["Burn time", f"{NOM['burn_time_s']:.2f} s"],
    ["Specific impulse", f"{NOM['isp_s']:.1f} s"],
    ["Pc, average / peak", f"{NOM['pc_avg_mpa']:.2f} / {NOM['pc_peak_mpa']:.2f} MPa"],
    ["Kn, initial / peak", f"{NOM['kn_initial']:.1f} / {NOM['kn_peak']:.1f}, nominal simulated run (erosive)\n"
                           f"{KN_GEO_MAX:.1f} max geometric (uniform regression)"],
    ["MEOP", f"{P.MEOP:.1f} MPa"],
    ["Hydrostatic proof", f"{P.PROOF_X_MEOP * P.MEOP:.1f} MPa ({fmt(P.PROOF_X_MEOP)} {TIMES} MEOP), SRM100-001"],
    ["Throat / exit", f"{DIA}{P.THROAT_D:.2f} / {DIA}{P.EXIT_D:.1f}"],
    ["Expansion ratio", f"{NOM['expansion']:.2f}"],
    ["Mass, loaded / empty", f"{MB['loaded_kg']:.3f} / {MB['empty_kg']:.3f} kg"],
    ["Propellant mass", f"{MB['propellant_kg']:.3f} kg (fraction {MB['propellant_mass_fraction']:.3f})"],
    ["CG, loaded / empty", f"{CG_L:.0f} / {CG_E:.0f} mm fwd of the case aft face"],
    ["Bound run (sizing)", f"{BND['designation']}: {thou(BND['impulse_ns'])} N·s, Pc peak "
                           f"{BND['pc_peak_mpa']:.2f} MPa\n(the paper's ideal inputs)"],
]
yb = sh.table(MX, MY - 6.0, [48.0, 86.0], rows, h=D.H, header=1)
yf = sh.notes(MX, yb - 5.0, [
    f"Nominal run: {thou(inp['rho_kg_m3'])} kg/m³ as cast, c* {TIMES} {fmt(BAL['model']['cstar_eff'])}, "
    f"Mukunda-Paul erosive burning, grain at {fmt(inp['T_grain_C'])} °C. Predictions from "
    "srm_ballistics, not measured: the static fire settles the class."], 134.0, title=None,
    numbered=False)

# ---- detail C (5:1): forward end of the stack - spacer, take-up ring, liner float, insulator
Z_C = 0.5 * (P.Z_LINER_FWD + P.Z_FWD_INSUL_AFT)   # centred on the liner's float gap
R_C, RAD_C, SC_C = 43.0, 7.0, 5.0
OC = np.array([185.0, 56.0])
assert OC[1] + RAD_C * SC_C < yf + 2.0 and OC[1] - RAD_C * SC_C - 5.0 - 3.5 > sh.frame[1] + 1.5, yf
v.parts = make_parts(H_DET)
dC = v.detail((Z_C, R_C), RAD_C, SC_C, tuple(OC), "C", circle_label_ang=90.0)
v.parts = PARTS_MAIN
# balloons from below-left, through the empty cavity inside the rings
bal(dC.pt(P.takeup_z() + P.TAKEUP_T / 2.0, 0.25 * (P.TAKEUP_ID + P.TAKEUP_OD)), 12, (146.0, 26.0),
    halo=True)
bal(dC.pt(P.Z_FWD_INSUL_AFT + P.FWD_INSUL_T / 2.0, 40.8), 7, (158.0, 16.0), halo=True)

# ---- parts list (ISO 7573), directly above the title block, read bottom-up ------------
PX = sh.tb[0]
PW = [11.0, 10.0, 40.0, 53.0, 44.0, 22.0]
PAL = ["c", "c", "l", "l", "l", "r"]
# one line each where possible: the list's top must stay under the right-hand
# centring mark (ISO 5457, y = 210, 5 mm into the frame)
LUBE_PN = P.LUBE.split(",")[0].replace("Parker ", "")      # "Super O-Lube or DC-55"
assert LUBE_PN == "Super O-Lube or DC-55", P.LUBE
cons = [
    ["-", "4", "Temp. label 177-260 °C", f"On 1, 2: new each firing (note {N_MARK})", "irreversible strip",
     "-"],
    ["-", "a/r", "PVC tape, 19 wide", "Cap tape: 5 (SRM100-106 note 6)", "PVC electrical tape", "-"],
    ["-", "a/r", "RTV106 + SS4004P", f"Bond 7 to 6, primed (note {N_LUBE})", "RTV silicone + primer", "-"],
    ["-", "a/r", "Loctite 243; anti-seize", "Threads: 16 (243), 15 (anti-seize)", "anaerobic / nickel", "-"],
    ["-", "a/r", LUBE_PN, f"Lube: 13, 14, liner OD (note {N_LUBE})", "silicone, thin film", "-"],
]
item_rows = [[str(n), str(QTY[n]), pn, desc, mat, f"{MB['parts'][stem]['mass_each_kg'] * 1000:.1f}"]
             for n, pn, desc, mat, stem in reversed(ITEMS)]
body = cons + item_rows
hdr = [["ITEM", "QTY", "PART NO. /\nSTANDARD", "DESCRIPTION", "MATERIAL", "MASS g\n(each)"]]


def rows_h(rows, h=D.H):
    return sum(h * 2.4 + (max(len(str(c).split("\n")) for c in r) - 1) * h * 1.5 for r in rows)


y_hdr = sh.tb[3] + rows_h(hdr)
assert y_hdr + rows_h(body) < 0.5 * (sh.frame[1] + sh.frame[3]) - 2.0, y_hdr + rows_h(body)
sh.table(PX, y_hdr + rows_h(body), PW, body, h=D.H, header=0, align=PAL)
sh.table(PX, y_hdr, PW, hdr, h=D.H, header=1, align=["c", "c", "l", "l", "l", "r"])
Y_PLIST_TOP = y_hdr + rows_h(body)

# ---- general notes, two columns: under MOTOR DATA's right, then above the parts list ---
# (the kit's Sheet.notes() numbers from 1 and has no column break; this is its layout
# - same wrap width rule, pitch and gaps - with the numbering carried on)

def note_lines(item, width, h=D.H):
    cw = sh.text_width("M" * 20, h) / 20 * 0.78
    indent = sh.text_width("00. ", h)
    return indent, textwrap.wrap(item, max(10, int((width - indent) / cw))) or [""]


def notes_columns(cols, items, h=D.H, gap=1.55):
    """cols: [(x, y_top, width, y_floor, title)]; a note that would reach below its
    column's y_floor starts the next column.  Returns (x, y) under the last note."""
    k, col = 0, 0
    placed = []

    def start(c):
        x_, y_, w_, f_, t_ = cols[c]
        sh.text(x_, y_ - 3.5, t_, 3.5, bold=True)
        return x_, y_ - 3.5 - h * 1.9, w_, f_

    x, y, w, floor = start(0)
    while k < len(items):
        indent, wrapped = note_lines(items[k], w, h)
        need = len(wrapped) * h * gap
        if y - need < floor:
            col += 1
            assert col < len(cols), f"notes do not fit: note {k + 1}"
            x, y, w, floor = start(col)
            continue
        sh.text(x, y, f"{k + 1}.", h)
        for s in wrapped:
            sh.text(x + indent, y, s, h)
            y -= h * gap
        y -= h * 0.45
        placed.append((k + 1, col))
        k += 1
    return x, y, placed


NX, NW = 264.0, 136.0
# column 2 starts right of the (749.5) extension line at the forward flange face and
# stops short of the right-hand centring mark
X_EXT_FWD = v.pt(Z_FWD, 0.0)[0]
N2X = X_EXT_FWD + 3.5
N2W = sh.frame[2] - 6.0 - N2X
xn, yn, placed = notes_columns(
    [(NX, MY, NW, sh.frame[1] + 3.0, "NOTES"),
     (N2X, 283.0, N2W, Y_PLIST_TOP + 4.0, "NOTES (continued)")], notes)
sh.text(xn, yn - 3.0, "USED ON: HELIOS rocket - SRM-100 motor (static-fire stand, then flight)",
        D.H, bold=True)
assert yn - 3.0 > (Y_PLIST_TOP + 3.0 if placed[-1][1] == 1 else sh.frame[1] + 2.0), (yn, placed[-1])


# ---- local checker: annotation crossings, lines through text ---------------------------
def check():
    issues = []
    r = sh._renderer
    inv = sh.ax.transData.inverted()
    boxes = []
    for t in sh.texts:
        s = t.get_text().strip()
        if not s:
            continue
        bb = t.get_window_extent(r).transformed(inv)
        boxes.append((s, box(bb.x0 + 0.25, bb.y0 + 0.25, bb.x1 - 0.25, bb.y1 - 0.25)))
    segs = [(tag, LineString([a, b])) for tag, a, b in SEGS]
    grp = lambda t: t.split(":")[0]
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            (ti, li), (tj, lj) = segs[i], segs[j]
            if grp(ti) != grp(tj) and li.crosses(lj):
                issues.append(f"cross: {ti} / {tj}")
    for tag, ln in segs:
        for s, bx in boxes:
            if ln.intersects(bx):
                issues.append(f"through text: {tag} / {s!r}")
    for s in issues:
        print("CHECK", s)
    return issues


if __name__ == "__main__":
    check()
    sh.lint()
    sh.save("general_arrangement")
