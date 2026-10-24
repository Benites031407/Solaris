"""The deployed configuration: latch swept, both halves open 100 deg.

Everything lives in nose_assembly.build().  This file exists only because the
exporter takes one gen_step() per target, and the two configurations are worth
having as two files you can open side by side.

100 deg is not a round number picked for the picture -- it is the angle
nose_verify.py checks the halves against the ring, against each other and
against the bulkhead at, and the angle at which it measures the deployment
axis clear for 40 mm above the bulkhead face.
"""

from __future__ import annotations

import nose_assembly
import nose_build as B
import nose_params as P

OPEN_DEG = 100.0


def gen_step():
    return nose_assembly.build(OPEN_DEG, released=True)


if __name__ == "__main__":
    asm = gen_step()
    lo, hi = B.bbox(asm)
    print(f"{asm.label}  open {OPEN_DEG:.0f} deg, latch swept {P.LATCH_SWEEP:.0f} deg")
    print(f"  bbox  x {lo[0]:8.3f}..{hi[0]:8.3f}   y {lo[1]:8.3f}..{hi[1]:8.3f}   "
          f"z {lo[2]:8.3f}..{hi[2]:8.3f}")
    for c in asm.children:
        clo, chi = B.bbox(c)
        print(f"    {c.label:38s} z {clo[2]:8.3f}..{chi[2]:8.3f}")
