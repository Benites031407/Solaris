"""The printed set, positioned -- as a LINKED assembly, not a fused solid.

`nose_assembly.py` fuses everything into one scene so you can look at it.  This
file does the other thing: it returns an assembly spec whose children POINT AT the
four exported part STEPs and give each one a 4x4 placement.  Nothing is re-baked,
so the assembly cannot drift from what the slicer gets -- change base_ring.py,
re-export, and this assembly is different too, with no edit here.

That also makes the placements readable.  In the flight configuration:

    base_ring    identity
    bulkhead     identity
    latch_arm    identity
    half_shell   identity           <- the +Y half
    half_shell   Rz(180)            <- the -Y half, SAME STEP FILE

Four printed bodies from four part files, one of which is instanced twice.  The
only non-identity transform in the whole closed assembly is that 180 deg spin,
which is the design's central claim: the two halves are one part.

nose_linked_open.py is the same list with the two hinge rotations applied.

REFERENCE BODIES ARE NOT HERE
-----------------------------
The servo, pins and dowels have no STEP of their own to link to, so they only
appear in the fused `nose_assembly` scenes.  This file is exactly the printed set.
"""

from __future__ import annotations

import numpy as np

import nose_params as P
from nose_assembly import hinge_m, rz_m

PARTS = {
    "base_ring": "out/base_ring.step",
    "bulkhead": "out/bulkhead.step",
    "latch_arm": "out/latch_arm.step",
    "half_shell": "out/half_shell.step",
}


def _flat(m: np.ndarray) -> list[float]:
    """Row-major 16, which is what the assembly spec wants."""
    return [float(x) for x in np.asarray(m, dtype=float).reshape(16)]


def children(open_deg: float = 0.0, released: bool = False) -> list[dict]:
    """One node per printed body, in assembly coordinates.

    `half_shell` appears twice under different instance names -- that is the
    point of a linked assembly, and the reason the -Y half needs no mirrored
    STEP file of its own.
    """
    arm = rz_m(P.LATCH_SWEEP if released else 0.0)
    spec = [
        ("base_ring", "base_ring", np.eye(4)),
        ("bulkhead", "bulkhead", np.eye(4)),
        ("latch_arm", "latch_arm", arm),
        ("half_shell_A", "half_shell", hinge_m(open_deg, +1)),
        ("half_shell_B", "half_shell", hinge_m(open_deg, -1) @ rz_m(180.0)),
    ]
    return [{"name": name, "path": PARTS[src], "transform": _flat(m)}
            for name, src, m in spec]


def gen_step():
    return {"children": children(0.0, released=False)}


if __name__ == "__main__":
    # The transforms here and the joint placements in nose_assembly must agree.
    # They are computed by the same two functions, so this checks the wiring --
    # which instance gets which matrix, and whether the 180 deg spin composes on
    # the correct side of the hinge -- not the matrix maths.
    import nose_assembly as A

    for deg, rel in ((0.0, False), (100.0, True)):
        asm = A.build(deg, rel)
        fused = {c.label: A._verts(c) for c in asm.children}
        raw = {"base_ring": None, "bulkhead": None, "latch_arm": None,
               "half_shell": None}
        import base_ring, bulkhead, half_shell, latch_arm
        raw["base_ring"] = A._verts(base_ring.gen_step())
        raw["bulkhead"] = A._verts(bulkhead.gen_step())
        raw["latch_arm"] = A._verts(latch_arm.gen_step())
        raw["half_shell"] = A._verts(half_shell.gen_step())

        label_of = {
            "base_ring": "base_ring",
            "bulkhead": "bulkhead",
            "latch_arm": "latch_arm_" + ("released" if rel else "latched"),
            "half_shell_A": "half_shell_A",
            "half_shell_B": "half_shell_B_same_part_rotated_180",
        }
        print(f"open {deg:5.1f} deg, latch {'released' if rel else 'latched'}")
        for node in children(deg, rel):
            m = np.array(node["transform"], dtype=float).reshape(4, 4)
            src = next(k for k, v in PARTS.items() if v == node["path"])
            want = A._apply(m, raw[src])
            got = fused[label_of[node["name"]]]
            err = A._pointset_err(got, want)
            assert err < 1e-6, f"{node['name']}: linked vs fused differ by {err:.2e} mm"
            ident = np.allclose(m, np.eye(4))
            print(f"  {node['name']:14s} <- {node['path']:24s} "
                  f"{'identity' if ident else 'placed  '}  agrees to {err:.1e} mm")
