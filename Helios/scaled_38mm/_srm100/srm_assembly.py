"""SRM-100: the whole motor, assembled.  Every part placed, nothing drawn here.

Frame: the MOTOR frame of srm_params (z = 0 at the case's aft end face, +Z forward,
theta = 0 on +X).  The case, the nozzle holder, the graphite insert and the nozzle
cap are drawn in it and placed with the identity; everything else is drawn in its
own local frame and moved by a transform built in placements() below -- the one
and only place a part is positioned.  srm_verify.py imports placements() and
places the same STEPs with the same numbers, so what it checks is what ships.

Tree:
  case
  aft_closure   nozzle holder, graphite insert, its O-ring, 2 case O-rings,
                phenolic nozzle insulator, LDPE nozzle cap, 18 x M6x10
  grain_stack   liner, 5 spacers, 4 BATES grains in 4 casting tubes, take-up ring
  fwd_closure   EPDM insulator, forward closure, 2 case O-rings, 18 x M6x16

proof_placements() is the hydrostatic-proof configuration (srm_proof_assembly.py):
the same case, closures, seals and screws in the same places, with the 304 proof
dummy in the insert's gland and nothing inside the case.
"""

from __future__ import annotations

import srm_params as P
from srm_build import axial_trsf, radial_trsf

IDENTITY = axial_trsf(0.0)


def placements() -> list[tuple[str, str, str, list[float]]]:
    """(group, instance name, STEP file, row-major 4x4) for every part in the motor."""
    out: list[tuple[str, str, str, list[float]]] = [("", "case", "case.step", IDENTITY)]

    def add(group, name, step, trsf):
        out.append((group, name, step, trsf))

    g = "aft_closure"
    add(g, "nozzle_holder", "nozzle_holder.step", IDENTITY)
    add(g, "nozzle_insert", "nozzle_insert.step", IDENTITY)
    add(g, "oring_insert", "oring_insert.step", axial_trsf(P.INSERT_GROOVE_Z))
    add(g, "oring_aft_outer", "oring_case.step", axial_trsf(P.Z_CASE_AFT + P.GROOVE_1_Z))
    add(g, "oring_aft_inner", "oring_case.step", axial_trsf(P.Z_CASE_AFT + P.GROOVE_2_Z))
    add(g, "nozzle_insulator", "nozzle_insulator.step", axial_trsf(P.Z_HOLDER_FACE))
    add(g, "nozzle_cap", "nozzle_cap.step", IDENTITY)
    for i, th in enumerate(P.bolt_thetas()):
        add(g, f"bolt_aft_{i:02d}", "bolt_m6x10.step", radial_trsf(th, P.CASE_OD / 2.0, P.bolt_z_aft()))

    g = "grain_stack"
    add(g, "liner", "liner.step", axial_trsf(P.Z_LINER_AFT))
    for i in range(P.N_SPACERS):
        add(g, f"spacer_{i}", "grain_spacer.step", axial_trsf(P.spacer_z(i)))
    for i in range(P.N_GRAINS):
        add(g, f"grain_{i + 1}", "grain.step", axial_trsf(P.grain_z(i)))
        add(g, f"casting_tube_{i + 1}", "casting_tube.step", axial_trsf(P.grain_z(i)))
    add(g, "takeup_ring", "takeup_ring.step", axial_trsf(P.takeup_z()))

    g = "fwd_closure"
    add(g, "fwd_insulator", "fwd_insulator.step", axial_trsf(P.Z_FWD_INSUL_AFT))
    add(g, "fwd_closure", "fwd_closure.step", axial_trsf(P.CASE_L))
    add(g, "oring_fwd_outer", "oring_case.step", axial_trsf(P.Z_CASE_FWD - P.GROOVE_1_Z))
    add(g, "oring_fwd_inner", "oring_case.step", axial_trsf(P.Z_CASE_FWD - P.GROOVE_2_Z))
    for i, th in enumerate(P.bolt_thetas()):
        add(g, f"bolt_fwd_{i:02d}", "bolt_m6x16.step", radial_trsf(th, P.CASE_OD / 2.0, P.bolt_z_fwd()))
    return out


PROOF_KEEP = ("case", "nozzle_holder", "oring_insert", "oring_aft_outer", "oring_aft_inner",
              "fwd_closure", "oring_fwd_outer", "oring_fwd_inner")


def proof_placements() -> list[tuple[str, str, str, list[float]]]:
    """The hydrostatic-proof build: placements() less the graphite, the insulators, the
    cap and everything inside the case, plus the proof dummy where the insert goes.
    The EPDM disc is bonded on after the proof, so it is not in the proof either."""
    out = [p for p in placements() if p[1] in PROOF_KEEP or p[1].startswith("bolt_")]
    at = next(i for i, p in enumerate(out) if p[1] == "nozzle_holder") + 1
    out.insert(at, ("aft_closure", "proof_dummy", "proof_dummy.step", IDENTITY))
    return out


def tree(rows) -> list[dict]:
    """Placement rows -> assembly children, one node per group."""
    top: list[dict] = []
    groups: dict[str, list[dict]] = {}
    for group, name, step, trsf in rows:
        node = {"path": step, "name": name, "transform": trsf, "use_source_colors": True}
        if not group:
            top.append(node)
            continue
        if group not in groups:
            groups[group] = []
            top.append({"name": group, "transform": IDENTITY, "children": groups[group]})
        groups[group].append(node)
    return top


def gen_step():
    # a dict literal: scripts/step reads the return statement to tell an assembly
    return {"children": tree(placements())}
