"""Check the ASSEMBLED geometry -- the STEPs as placed -- not the parameters.

srm_params.self_check() proves the numbers are right; this proves the solids are
the numbers.  It loads every part STEP that scripts/step wrote, places it with
srm_assembly.placements() (the same transforms the assembly STEP carries), and
measures:

  1. interference     every pair of parts whose boxes meet is intersected.  The
                      only overlaps allowed are bolt threads in the closures'
                      tap-drill holes; anything else over INTERFERENCE_TOL fails.
  2. threads          engagement length and overlap volume read back off those
                      bolt / closure overlaps, and a 4.8 core probe down every bolt
                      axis proving each tapped hole is open to the bolt tip
  3. glands           groove bottom, bore and ring measured on radial probe lines
                      through each placed O-ring: squeeze from the geometry
  4. stack            every axial contact that captures the liner and grains, with
                      its bearing footprint; the liner's forward float
  5. flow path        throat, exit, insulator -> graphite step, the free radius at
                      every grain core, spacer and the take-up, all probed
  6. propellant       grain volume x density vs srm_params.prop_mass()
  7. mass budget      out/mass_budget.json, loaded and empty, with CG
  8. proof build      srm_assembly.proof_placements(): interference, the 304 dummy
                      seated on the lip, the insert gland squeezed by the dummy
  9. .eng             out/SRM100_<designation>.eng from the NOMINAL ballistics run

Run after scripts/step has generated every part:   python srm_verify.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from build123d import Edge, Plane, Solid, import_step
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

import srm_params as P
from srm_assembly import placements, proof_placements
from srm_build import location

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
INTERFERENCE_TOL = 0.01          # mm^3: coincident faces come back as ~0
KEEP_OUT_D = 108.0               # mm: the airframe / test-stand bore the heads must clear
FOOTPRINT_MIN = 0.2              # mm: radial overlap every axial bearing contact must have
PROBE_THETA = P.BOLT_THETA0 + 1.5 * 360.0 / P.N_BOLTS   # mid-way between bolts 1 and 2,
                                                        # clear of both pullers and the case seam
CORE_PROBE_D = 4.8               # just under the 5.0 tap drill
TIP_CHAMFER = 0.5                # srm_build.button_head_screw's default
ENG_MAX_POINTS = 32
ENG_IMPULSE_TOL = 0.005

# part STEP -> (material, density kg/mm^3)
MATERIALS = {
    "case.step": ("6061-T6 tube", P.AL_RHO),
    "fwd_closure.step": ("6061-T651 bar", P.AL_RHO),
    "nozzle_holder.step": ("304 stainless", P.SS_RHO),
    "nozzle_insert.step": ("isomolded graphite", P.GR_RHO),
    "nozzle_insulator.step": ("glass phenolic", 1.85e-6),
    "nozzle_cap.step": ("LDPE", 0.92e-6),
    "oring_case.step": ("FKM 90A", 1.85e-6),
    "oring_insert.step": ("FKM 90A", 1.85e-6),
    "liner.step": ("paper phenolic", 1.35e-6),
    "grain_spacer.step": ("linen phenolic", 1.35e-6),
    "casting_tube.step": ("spiral kraft", 0.95e-6),
    "grain.step": ("APCP 70/16/14, as cast", P.RHO_PROP_ASCAST_SI * 1e-9),
    "takeup_ring.step": ("silicone sponge, closed cell", 0.50e-6),
    "fwd_insulator.step": ("EPDM", 1.15e-6),
    "bolt_m6x10.step": ("steel, 10.9", P.BOLT_RHO),
    "bolt_m6x16.step": ("steel, 10.9", P.BOLT_RHO),
    "proof_dummy.step": ("304 stainless", P.SS_RHO),
}
CLOSURE_OF = {"bolt_m6x10.step": "nozzle_holder", "bolt_m6x16.step": "fwd_closure"}


class Report:
    def __init__(self):
        self.fails: list[str] = []

    def ck(self, cond: bool, ok: str, bad: str) -> None:
        if cond:
            print(f"  ok   {ok}")
        else:
            self.fails.append(bad)
            print(f"  FAIL {bad}")


def volume(shape) -> float:
    """Tight-tolerance volume: the default integration is loose enough to read a
    thread overlap a few tenths of a percent off."""
    total = 0.0
    for s in shape.solids():
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(s.wrapped, props, 1e-7, True)
        total += props.Mass()
    return total


def load_parts(rows, cache: dict):
    parts = []
    for group, name, step, trsf in rows:
        if step not in cache:
            shape = import_step(str(HERE / step))
            solids = shape.solids()
            if len(solids) != 1:
                raise SystemExit(f"{step}: expected 1 solid, got {len(solids)}")
            cache[step] = solids[0]
        placed = cache[step].moved(location(trsf))
        parts.append({"group": group, "name": name, "step": step, "trsf": trsf,
                      "shape": placed, "bbox": placed.bounding_box()})
    return parts


def boxes_meet(a, b, pad=1e-3) -> bool:
    return (a.min.X - pad <= b.max.X and b.min.X - pad <= a.max.X and
            a.min.Y - pad <= b.max.Y and b.min.Y - pad <= a.max.Y and
            a.min.Z - pad <= b.max.Z and b.min.Z - pad <= a.max.Z)


def common_volume(a, b) -> tuple[float, object]:
    c = a.intersect(b)
    if c is None or not hasattr(c, "solids"):
        return 0.0, None
    return volume(c), c


def radial_hits(shape, z: float, r0: float, r1: float, theta_deg: float = PROBE_THETA):
    """Where a radial probe line at station z (azimuth theta) runs inside `shape`:
    sorted (r_in, r_out) segments."""
    t = math.radians(theta_deg)
    u = (math.cos(t), math.sin(t))
    line = Edge.make_line((r0 * u[0], r0 * u[1], z), (r1 * u[0], r1 * u[1], z))
    inter = shape.intersect(line)
    segs = []
    if inter is not None:
        for e in inter.edges():
            ra = math.hypot(e.start_point().X, e.start_point().Y)
            rb = math.hypot(e.end_point().X, e.end_point().Y)
            segs.append((min(ra, rb), max(ra, rb)))
    return sorted(segs)


def footprint(lower, upper, z: float, d: float = 1e-3) -> float:
    """Radial overlap of `lower` just below z and `upper` just above it.  With no
    interference between them, a positive value means the two faces meet at z
    (within 2 d) over that width."""
    a = radial_hits(lower, z - d, 0.0, 60.0)
    b = radial_hits(upper, z + d, 0.0, 60.0)
    return max([min(a1, b1) - max(a0, b0) for a0, a1 in a for b0, b1 in b] or [0.0])


def check_interference(parts, rep: Report, label: str = "") -> dict:
    print(f"-- 1/2. {label}interference, and the threads from the bolt overlaps")
    engagement = {}
    n_pairs = n_tested = 0
    unexpected = []
    by_name = {p["name"]: p for p in parts}
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            n_pairs += 1
            if not boxes_meet(a["bbox"], b["bbox"]):
                continue
            n_tested += 1
            vol, common = common_volume(a["shape"], b["shape"])
            bolt, other = (a, b) if a["step"] in CLOSURE_OF else (b, a)
            if bolt["step"] in CLOSURE_OF and other["name"] == CLOSURE_OF[bolt["step"]]:
                # thread engagement: the overlap's extent along the bolt's own axis
                local = common.moved(location(bolt["trsf"]).inverse())
                bb = local.bounding_box()
                engagement[bolt["name"]] = {"length": bb.max.Z - bb.min.Z, "tip_z": bb.min.Z,
                                            "top_z": bb.max.Z, "volume": vol}
                continue
            if vol > INTERFERENCE_TOL:
                unexpected.append((a["name"], b["name"], vol))
    print(f"  info {n_pairs} pairs, {n_tested} with meeting boxes intersected")
    rep.ck(not unexpected, f"{label}no unexpected interference between any two parts",
           f"{label}interference: {', '.join(f'{x}/{y} {v:.3f} mm^3' for x, y, v in unexpected[:12])}")

    # the overlap is the thread annulus (major dia over the tap drill) down the engaged
    # length, less the screw's tip chamfer (all of it outside the tap drill: 3 - 0.5 >=
    # 2.5), less the sliver where the hole's mouth meets the plug's curved OD: the
    # surface falls x^2 / 2R away from the bolt axis across the hole
    rs, rt, c = P.BOLT_D / 2.0, P.BOLT_TAP_DRILL / 2.0, TIP_CHAMFER
    tip_loss = math.pi * (rs * rs * c - (rs ** 3 - (rs - c) ** 3) / 3.0)
    mouth_loss = math.pi * (rs ** 4 - rt ** 4) / 4.0 / (2.0 * P.PLUG_OD / 2.0)
    for kind, L, need in (("aft", P.BOLT_L_AFT, 1.0), ("fwd", P.BOLT_L_FWD, 2.0)):
        bolts = [p for p in parts if p["name"].startswith(f"bolt_{kind}_")]
        vals = [engagement[p["name"]] for p in bolts if p["name"] in engagement]
        rep.ck(len(vals) == P.N_BOLTS, f"{kind}: all {P.N_BOLTS} bolts engage their closure",
               f"{kind}: only {len(vals)} of {P.N_BOLTS} bolts reach their closure")
        if not vals:
            continue
        lengths = [v["length"] for v in vals]
        expect = L - P.CASE_WALL - P.PLUG_CLEAR
        rep.ck(max(lengths) - min(lengths) < 1e-3 and abs(min(lengths) - expect) < 0.01,
               f"{kind}: engagement {min(lengths):.2f} mm measured ({min(lengths) / P.BOLT_D:.2f} d), "
               f"expected {expect:.2f}",
               f"{kind}: engagement {min(lengths):.2f}..{max(lengths):.2f} mm, expected {expect:.2f}")
        rep.ck(min(lengths) >= need * P.BOLT_D - 0.1, f"{kind}: engagement >= {need:.0f} d",
               f"{kind}: engagement below {need:.0f} d")
        v_exp = math.pi * (rs * rs - rt * rt) * expect - tip_loss - mouth_loss
        vols = [v["volume"] for v in vals]
        worst = max(abs(v - v_exp) / v_exp for v in vols)
        rep.ck(worst < 0.002,
               f"{kind}: thread overlap {min(vols):.3f}..{max(vols):.3f} mm^3 vs {v_exp:.3f} "
               f"(annulus x length - tip chamfer - mouth curvature), worst {100 * worst:.3f} %",
               f"{kind}: thread overlap {min(vols):.2f}..{max(vols):.2f} mm^3 vs {v_exp:.2f}")
        # and the hole is open down its core all the way to the bolt tip
        closure = by_name[CLOSURE_OF[bolts[0]["step"]]]["shape"]
        blocked = []
        for p in bolts:
            core = Solid.make_cylinder(CORE_PROBE_D / 2.0, L - P.CASE_WALL, Plane.XY.offset(-L))
            v, _ = common_volume(core.moved(location(p["trsf"])), closure)
            if v > INTERFERENCE_TOL:
                blocked.append((p["name"], v))
        rep.ck(not blocked, f"{kind}: a {CORE_PROBE_D} core probe runs clear down all {len(bolts)} "
                            f"tapped holes to the bolt tip",
               f"{kind}: tapped holes blocked: {blocked[:6]}")
    return engagement


def check_glands(by_name, rep: Report, seat: str = "nozzle_insert") -> list:
    print(f"-- 3. O-ring glands, measured on radial probes through each placed ring ({seat})")
    rows = []
    case = by_name["case"]["shape"]
    glands = [
        ("oring_aft_outer", "nozzle_holder", P.Z_CASE_AFT + P.GROOVE_1_Z, "case"),
        ("oring_aft_inner", "nozzle_holder", P.Z_CASE_AFT + P.GROOVE_2_Z, "case"),
        ("oring_fwd_outer", "fwd_closure", P.Z_CASE_FWD - P.GROOVE_1_Z, "case"),
        ("oring_fwd_inner", "fwd_closure", P.Z_CASE_FWD - P.GROOVE_2_Z, "case"),
        ("oring_insert", "nozzle_holder", P.INSERT_GROOVE_Z, "insert"),
    ]
    for ring, carrier, z, kind in glands:
        ring_seg = radial_hits(by_name[ring]["shape"], z, 20.0, 55.0)
        if kind == "case":
            groove = radial_hits(by_name[carrier]["shape"], z, 30.0, 55.0)
            bore = radial_hits(case, z, 30.0, 55.0)
            r_groove = groove[-1][1]            # outermost steel/alu surface at the groove
            r_seal = bore[0][0]                 # case bore
            cs = P.ORING_CS
        else:
            groove = radial_hits(by_name[carrier]["shape"], z, 20.0, 55.0)
            rod = radial_hits(by_name[seat]["shape"], z, 5.0, 55.0)
            r_groove = groove[0][0]             # rod groove bottom in the holder
            r_seal = rod[-1][1]                 # graphite (or dummy) OD
            cs = P.INSERT_ORING_CS
        gland = abs(r_groove - r_seal)
        squeeze = (cs - gland) / cs
        ok_ring = (len(ring_seg) == 1 and
                   abs(min(ring_seg[0][0], ring_seg[0][1]) - min(r_groove, r_seal)) < 0.02 and
                   abs(max(ring_seg[0][0], ring_seg[0][1]) - max(r_groove, r_seal)) < 0.02)
        rows.append({"ring": ring, "z": z, "gland_depth": gland, "squeeze": squeeze,
                     "ring_span": ring_seg})
        rep.ck(ok_ring and 0.15 <= squeeze <= 0.25,
               f"{ring:16s} z {z:7.2f}: gland {gland:.3f} mm, squeeze {100 * squeeze:.1f} %, ring fills it",
               f"{ring}: gland {gland:.3f}, squeeze {100 * squeeze:.1f} %, ring {ring_seg}")
    return rows


def check_stack(by_name, rep: Report) -> list:
    print("-- 4. axial stack: the liner and grains are captured end to end")
    bb = {k: v["bbox"] for k, v in by_name.items()}
    # (lower part, upper part): the lower one's forward face carries the upper one's aft
    # face.  The liner is NOT in the chain at its forward end: it floats (below).
    chain = [("nozzle_holder", "nozzle_insulator"),
             ("nozzle_insulator", "liner"),
             ("nozzle_insulator", "spacer_0"),
             *[(f"spacer_{i}", f"grain_{i + 1}") for i in range(P.N_GRAINS)],
             *[(f"grain_{i + 1}", f"spacer_{i + 1}") for i in range(P.N_GRAINS)],
             (f"spacer_{P.N_SPACERS - 1}", "takeup_ring"),
             ("takeup_ring", "fwd_insulator"),
             ("fwd_insulator", "fwd_closure")]
    worst = 0.0
    rows = []
    for a, b in chain:
        za, zb = bb[a].max.Z, bb[b].min.Z
        worst = max(worst, abs(za - zb))
        rows.append({"lower": a, "upper": b, "z": za, "gap": zb - za,
                     "footprint": footprint(by_name[a]["shape"], by_name[b]["shape"], za)})
    rep.ck(worst < 1e-6, f"{len(chain)} axial contacts close to {worst:.1e} mm",
           f"stack has a {worst:.4f} mm gap or overlap")
    thin = [(r["lower"], r["upper"], round(r["footprint"], 3)) for r in rows if r["footprint"] < FOOTPRINT_MIN]
    fp = min(rows, key=lambda r: r["footprint"])
    rep.ck(not thin, f"every contact bears over >= {FOOTPRINT_MIN} mm radially "
                     f"(least {fp['footprint']:.2f}, {fp['lower']} -> {fp['upper']})",
           f"contacts with under {FOOTPRINT_MIN} mm of bearing: {thin}")
    gap = bb["fwd_insulator"].min.Z - bb["liner"].max.Z
    rep.ck(abs(gap - P.LINER_FLOAT) < 1e-6 and gap >= 0.3,
           f"liner floats {gap:.3f} mm short of the forward insulator (LINER_FLOAT, >= 0.3)",
           f"liner forward gap {gap:.4f} mm, want LINER_FLOAT {P.LINER_FLOAT} and >= 0.3")
    for flange, z_face in (("nozzle_holder", P.Z_CASE_AFT), ("fwd_closure", P.Z_CASE_FWD)):
        # the flange's bearing face sits on the case end
        seg = radial_hits(by_name[flange]["shape"], z_face - 0.001 if flange == "nozzle_holder" else z_face + 0.001,
                          40.0, 55.0)
        rep.ck(bool(seg) and seg[-1][1] > P.CASE_OD / 2.0 - 0.6,
               f"{flange} flange bears on the case end at z {z_face:.1f}",
               f"{flange} flange not at the case end")
    return rows


def check_seat(by_name, part: str, rep: Report) -> float:
    """`part` (the insert, or the proof dummy) sits on the holder's aft lip."""
    z = P.nozzle_stations()["z_exit"]
    fp = footprint(by_name["nozzle_holder"]["shape"], by_name[part]["shape"], z)
    z_aft = by_name[part]["bbox"].min.Z
    rep.ck(abs(z_aft - z) < 1e-6 and fp >= FOOTPRINT_MIN,
           f"{part} seated on the holder's lip at z {z:.2f}, bearing {fp:.2f} mm radially",
           f"{part}: aft face z {z_aft:.4f} vs lip {z:.4f}, bearing {fp:.3f} mm")
    return fp


def check_flow_path(by_name, rep: Report) -> None:
    print("-- 5. flow path, probed")
    S = P.nozzle_stations()
    ins = by_name["nozzle_insert"]["shape"]
    z_mid = 0.5 * (S["z_land_fwd"] + S["z_land_aft"])
    d_t = 2.0 * radial_hits(ins, z_mid, 0.0, 40.0)[0][0]
    rep.ck(abs(d_t - P.THROAT_D) < 1e-3, f"throat {d_t:.3f} mm", f"throat measures {d_t:.3f}")
    # the exit carries an EXIT_BREAK x 45 deg break: probe just forward of where it
    # meets the 15 deg divergent, and expect the cone's own diameter there
    tb = math.tan(math.radians(P.DIV_HALF_DEG))
    h = P.EXIT_BREAK / (1.0 - tb) + 0.001
    d_exp = 2.0 * (S["r_exit"] - h * tb)
    d_e = 2.0 * radial_hits(ins, S["z_exit"] + h, 0.0, 40.0)[0][0]
    rep.ck(abs(d_e - d_exp) < 0.002,
           f"exit {d_e:.3f} mm {h:.3f} forward of the exit plane (cone {d_exp:.3f}; "
           f"{P.EXIT_D:.1f} at the plane), expansion {(P.EXIT_D / d_t) ** 2:.2f}",
           f"exit measures {d_e:.3f} vs {d_exp:.3f}")
    r_ins = radial_hits(by_name["nozzle_insulator"]["shape"], P.Z_HOLDER_FACE + 0.001, 0.0, 50.0)[0][0]
    r_gr = radial_hits(ins, P.Z_HOLDER_FACE - 0.001, 0.0, 50.0)[0][0]
    rep.ck(abs(r_ins - r_gr) < 0.01, f"insulator -> graphite step {abs(r_ins - r_gr) * 1e3:.1f} um",
           f"insulator/graphite step {r_ins - r_gr:.3f} mm")
    check_seat(by_name, "nozzle_insert", rep)
    # the free radius at each station: the first solid ANY part puts on the probe
    stations = ([(f"grain_{i + 1}", P.GRAIN_CORE / 2.0) for i in range(P.N_GRAINS)] +
                [(f"spacer_{i}", P.SPACER_ID / 2.0) for i in range(P.N_SPACERS)] +
                [("takeup_ring", P.TAKEUP_ID / 2.0)])
    bad = []
    for part, r_want in stations:
        z = 0.5 * (by_name[part]["bbox"].min.Z + by_name[part]["bbox"].max.Z)
        first = min(((seg[0], name) for name, p in by_name.items()
                     if p["bbox"].min.Z <= z <= p["bbox"].max.Z
                     for seg in radial_hits(p["shape"], z, 0.0, 60.0)[:1]), default=(None, None))
        if first[1] != part or abs(first[0] - r_want) > 1e-3:
            bad.append((part, first))
    rep.ck(not bad, f"free radius {P.GRAIN_CORE / 2:.1f} in all {P.N_GRAINS} cores, "
                    f"{P.SPACER_ID / 2:.1f} at all {P.N_SPACERS} spacers, {P.TAKEUP_ID / 2:.1f} at the take-up",
           f"free radius wrong at {bad}")
    # the core, spacer bores and nozzle insulator are open end to end: probe the axis
    axis = Edge.make_line((0, 0, S["z_exit"] - 10.0), (0, 0, P.Z_FWD_INSUL_AFT - 0.001))
    blocked = [p for p in by_name if p not in ("nozzle_cap",) and
               by_name[p]["shape"].intersect(axis) is not None and
               sum(e.length for e in by_name[p]["shape"].intersect(axis).edges()) > 1e-6]
    rep.ck(not blocked, "axis open from the exit to the forward insulator (cap aside)",
           f"axis blocked by {blocked}")
    # no port and no pocket: the EPDM disc and the closure are solid on the axis from the
    # cavity to the forward (thrust) face
    z_face = P.CASE_L + P.FLANGE_T
    head = Edge.make_line((0, 0, P.Z_FWD_INSUL_AFT + 0.001), (0, 0, z_face - 0.001))
    solid_len = sum(sum(e.length for e in by_name[p]["shape"].intersect(head).edges())
                    for p in ("fwd_insulator", "fwd_closure")
                    if by_name[p]["shape"].intersect(head) is not None)
    rep.ck(abs(solid_len - head.length) < 1e-3,
           f"head end solid on the axis (no port): {solid_len:.3f} of {head.length:.3f} mm",
           f"head end open on the axis: {solid_len:.3f} of {head.length:.3f} mm solid")
    # the thrust face is flat and whole: probe just under it, from the axis out to the
    # flange's edge break, in the hole-0 plane (clear of the pullers)
    face = Edge.make_line((0, 0, z_face - 0.25), (P.FLANGE_OD / 2.0 - 1.0, 0, z_face - 0.25))
    xf = by_name["fwd_closure"]["shape"].intersect(face)
    face_len = sum(e.length for e in xf.edges()) if xf is not None else 0.0
    rep.ck(abs(face_len - face.length) < 1e-3,
           f"thrust face flat and whole: solid from the axis to r {face.length:.1f}, 0.25 under it",
           f"thrust face not whole: {face_len:.3f} of {face.length:.3f} mm solid")


def check_propellant(by_name, rep: Report) -> float:
    print("-- 6. propellant")
    v = sum(volume(by_name[f"grain_{i + 1}"]["shape"]) for i in range(P.N_GRAINS))
    m = v * P.RHO_PROP
    rep.ck(abs(m - P.prop_mass()) / P.prop_mass() < 1e-4,
           f"grain volume {v / 1e3:.1f} cm^3 -> {m:.3f} kg at {P.RHO_PROP_SI:.0f} kg/m^3, "
           f"matches srm_params ({P.prop_mass():.3f}); {v * P.RHO_PROP_ASCAST_SI * 1e-9:.3f} kg as cast",
           f"grain geometry gives {m:.3f} kg vs {P.prop_mass():.3f}")
    return m


def mass_budget(parts) -> dict:
    print("-- 7. mass budget")
    rows = {}
    tot = {"loaded": [0.0, 0.0], "empty": [0.0, 0.0]}
    for p in parts:
        mat, rho = MATERIALS[p["step"]]
        s = p["shape"]
        m = volume(s) * rho
        zc = s.center().Z
        key = p["step"].removesuffix(".step")
        r = rows.setdefault(key, {"material": mat, "count": 0, "mass_each_kg": m, "mass_kg": 0.0})
        r["count"] += 1
        r["mass_kg"] += m
        tot["loaded"][0] += m
        tot["loaded"][1] += m * zc
        if p["step"] != "grain.step":
            tot["empty"][0] += m
            tot["empty"][1] += m * zc
    for key, r in sorted(rows.items(), key=lambda kv: -kv[1]["mass_kg"]):
        print(f"  {key:18s} {r['count']:3d} x {r['mass_each_kg'] * 1e3:8.1f} g = {r['mass_kg']:7.3f} kg  "
              f"({r['material']})")
    m_l, m_e = tot["loaded"][0], tot["empty"][0]
    out = {
        "parts": rows,
        "loaded_kg": m_l, "empty_kg": m_e, "propellant_kg": m_l - m_e,
        "propellant_mass_fraction": (m_l - m_e) / m_l,
        "cg_loaded_mm_from_case_aft_face": tot["loaded"][1] / m_l,
        "cg_empty_mm_from_case_aft_face": tot["empty"][1] / m_e,
    }
    print(f"  loaded {m_l:.3f} kg, empty {m_e:.3f} kg, propellant fraction {out['propellant_mass_fraction']:.3f}; "
          f"CG {out['cg_loaded_mm_from_case_aft_face']:.0f} / {out['cg_empty_mm_from_case_aft_face']:.0f} mm "
          f"forward of the case's aft face")
    return out


def envelope(parts) -> dict:
    """Length from the placed boxes; diameter from the bolts' true radial extent.  A
    box, even with the bolt turned onto +X, only reads the crown line: the socket rim
    sits off the bolt's axis and sweeps a larger circle."""
    xs = [p["bbox"] for p in parts]
    zmin, zmax = min(b.min.Z for b in xs), max(b.max.Z for b in xs)
    rmax = max(max(abs(b.min.X), abs(b.max.X), abs(b.min.Y), abs(b.max.Y))
               for p, b in zip(parts, xs) if p["step"] not in CLOSURE_OF)
    for p in parts:
        if p["step"] in CLOSURE_OF:
            verts, _ = p["shape"].tessellate(0.001, 0.05)
            rmax = max(rmax, max(math.hypot(v.X, v.Y) for v in verts))
    return {"length_mm": zmax - zmin, "z_min": zmin, "z_max": zmax, "max_diameter_mm": 2.0 * rmax}


def check_proof(cache: dict, rep: Report) -> dict:
    print("-- 8. hydrostatic proof build (srm_proof_assembly)")
    parts = load_parts(proof_placements(), cache)
    by_name = {p["name"]: p for p in parts}
    print(f"  info {len(parts)} parts: {', '.join(p['name'] for p in parts if not p['name'].startswith('bolt_'))}"
          f" and {sum(p['name'].startswith('bolt_') for p in parts)} screws")
    check_interference(parts, rep, "proof: ")
    fp = check_seat(by_name, "proof_dummy", rep)
    glands = check_glands(by_name, rep, seat="proof_dummy")
    return {"dummy_lip_bearing_mm": fp,
            "glands": [{k: v for k, v in g.items() if k != "ring_span"} for g in glands]}


def douglas_peucker(pts: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
    """Keep the endpoints and every point more than eps (N) off the chord between the
    points kept either side of it."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    todo = [(0, len(pts) - 1)]
    while todo:
        i0, i1 = todo.pop()
        (t0, f0), (t1, f1) = pts[i0], pts[i1]
        best, ib = -1.0, -1
        for i in range(i0 + 1, i1):
            t, f = pts[i]
            d = abs(f - (f0 + (f1 - f0) * (t - t0) / (t1 - t0)))
            if d > best:
                best, ib = d, i
        if ib > 0 and best > eps:
            keep[ib] = True
            todo += [(i0, ib), (ib, i1)]
    return [p for p, k in zip(pts, keep) if k]


def impulse(pts) -> float:
    return sum(0.5 * (fa + fb) * (tb - ta) for (ta, fa), (tb, fb) in zip(pts, pts[1:]))


def write_eng(budget: dict, env: dict, rep: Report) -> Path | None:
    """RASP .eng of the NOMINAL run.  The format starts every curve at an implicit
    (0, 0) and must end on zero thrust; Douglas-Peucker picks the <= 32 points that
    keep the curve's shape, and the impulse they carry is checked against the run's."""
    print("-- 9. .eng")
    csv_path = OUT / "srm_ballistics.csv"
    js_path = OUT / "srm_ballistics.json"
    if not csv_path.exists() or not js_path.exists():
        rep.ck(False, "", "out/srm_ballistics.csv / .json missing: run srm_ballistics.py first")
        return None
    js = json.loads(js_path.read_text())
    nom, bound = js["runs"]["nominal"], js["runs"]["bound"]
    with csv_path.open() as f:
        rows = [(float(r["t"]), float(r["thrust_n"])) for r in csv.DictReader(f)]
    rep.ck(rows[0] == (0.0, 0.0), "the nominal curve starts at (0, 0), as RASP assumes",
           f"the nominal curve starts at {rows[0]}, not (0, 0)")
    ipk = max(range(len(rows)), key=lambda i: rows[i][1])
    iend = next((i for i in range(ipk, len(rows)) if rows[i][1] <= 0.0), None)
    if iend is None:
        rows.append((rows[-1][0] + 1e-3, 0.0))
        iend = len(rows) - 1
    curve = rows[:iend + 1]
    lo, hi = 0.0, nom["peak_thrust_n"]
    for _ in range(60):                      # the smallest eps that fits in 32 points
        mid = 0.5 * (lo + hi)
        if len(douglas_peucker(curve, mid)) - 1 > ENG_MAX_POINTS:
            lo = mid
        else:
            hi = mid
    pick = douglas_peucker(curve, hi)[1:]    # drop (0, 0): RASP puts it back
    i_full, i_eng = impulse(curve), impulse([(0.0, 0.0)] + pick)
    d_i = (i_eng - i_full) / i_full
    rep.ck(len(pick) <= ENG_MAX_POINTS and pick[-1][1] == 0.0 and abs(d_i) < ENG_IMPULSE_TOL,
           f"{len(pick)} points (Douglas-Peucker, {hi:.1f} N), ends at F = 0, impulse {i_eng:.0f} N s vs "
           f"{i_full:.0f} ({100 * d_i:+.2f} %)",
           f".eng: {len(pick)} points, last F {pick[-1][1]}, impulse off by {100 * d_i:+.2f} %")
    rep.ck(abs(budget["propellant_kg"] - nom["prop_mass_kg"]) / nom["prop_mass_kg"] < 1e-3,
           f"propellant {budget['propellant_kg']:.3f} kg matches the nominal run's",
           f"propellant {budget['propellant_kg']:.3f} kg vs the nominal run's {nom['prop_mass_kg']:.3f}")
    lines = [f"; SRM-100 research motor, {P.PROP_NAME}.  NOMINAL run of srm_ballistics.py:",
             f";   as-cast density {P.RHO_PROP_ASCAST_SI:.0f} kg/m^3, c* x {js['model']['cstar_eff']}, "
             f"Mukunda-Paul erosive burning; {nom['impulse_ns']:.0f} N s in {nom['burn_time_s']:.2f} s",
             f";   the ideal / bound run is {bound['designation']} -- the class is M/N borderline "
             f"until a static fire measures it",
             f"; not a certified motor.  Burn rate assumed a = {P.BURN_A} mm/s/MPa^n, n = {P.BURN_N}: "
             f"characterise it before relying on this curve",
             f"SRM100-{nom['designation']} {P.CASE_OD:.0f} {env['length_mm']:.0f} P "
             f"{budget['propellant_kg']:.4f} {budget['loaded_kg']:.4f} RESEARCH"]
    lines += [f"   {t:.3f} {F:.1f}" for t, F in pick]
    lines.append(";")
    path = OUT / f"SRM100_{nom['designation']}.eng"
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rep = Report()
    print("srm_verify: loading and placing parts")
    cache: dict[str, object] = {}
    parts = load_parts(placements(), cache)
    by_name = {p["name"]: p for p in parts}
    print(f"  info {len(parts)} parts from {len({p['step'] for p in parts})} STEPs; "
          f"radial probes at {PROBE_THETA:.1f} deg")
    engagement = check_interference(parts, rep)
    glands = check_glands(by_name, rep)
    contacts = check_stack(by_name, rep)
    check_flow_path(by_name, rep)
    check_propellant(by_name, rep)
    budget = mass_budget(parts)
    env = envelope(parts)
    head_d = 2.0 * (P.CASE_OD / 2.0 + P.BOLT_HEAD_K)
    print(f"  info envelope {env['length_mm']:.1f} mm long, {env['max_diameter_mm']:.2f} mm over the bolt heads "
          f"(ISO 7380 k = {P.BOLT_HEAD_K} -> {head_d:.1f} to the crown the socket removes)")
    # the socket takes the dome's crown: the head stands ~2.98, not k = 3.3, off the case
    rep.ck(head_d - 1.0 < env["max_diameter_mm"] <= min(head_d, KEEP_OUT_D),
           f"head sweep {env['max_diameter_mm']:.2f} mm inside the {KEEP_OUT_D:.0f} mm keep-out",
           f"head sweep {env['max_diameter_mm']:.2f} mm vs nominal {head_d:.2f} / keep-out {KEEP_OUT_D:.0f}")
    proof = check_proof(cache, rep)
    eng = write_eng(budget, env, rep)
    budget["envelope"] = env
    budget["thread_engagement_mm"] = {k: v["length"] for k, v in sorted(engagement.items())}
    budget["thread_overlap_mm3"] = {k: v["volume"] for k, v in sorted(engagement.items())}
    budget["glands"] = [{k: v for k, v in g.items() if k != "ring_span"} for g in glands]
    budget["contacts"] = contacts
    budget["proof"] = proof
    (OUT / "mass_budget.json").write_text(json.dumps(budget, indent=2))
    print(f"\nwrote out/mass_budget.json{', ' + str(eng.relative_to(HERE)) if eng else ''}")
    print(f"-- {len(rep.fails)} failure(s)")
    if rep.fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
