"""Measure the enlarged tower variants. Every number printed is measured."""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from build123d import Axis, Plane, Pos

from enlarged_tower import bed_area, build_tower, butt_joint
import anchor_foot
import reaction_tower as RT

FOOT = anchor_foot.gen_step()

CASES = {
    "A bore 57.6 (no liner)": dict(bore=57.6, cup_wall=6.0, cup_depth=60.0,
                                   floor_t=10.0, stud_bore=22.0, stud_depth=25.0,
                                   wedge_deg=50.0,
                                   side_bolt_xs=(12.0, 52.0, 92.0, 132.0)),
    "B bore 62.0 (liner kept)": dict(bore=62.0, cup_wall=6.0, cup_depth=60.0,
                                     floor_t=10.0, stud_bore=22.0, stud_depth=25.0,
                                     wedge_deg=50.0,
                                     side_bolt_xs=(12.0, 52.0, 92.0, 132.0)),
}

ABS_RHO = 1.04e-3  # g/mm3

for name, kw in CASES.items():
    part, f = build_tower(**kw)
    bb = part.bounding_box()
    ba = bed_area(part)
    area, cen = butt_joint(part, FOOT, f["SADDLE_LEN"])
    print(f"=== {name}")
    print(f"  CUP_OD {f['CUP_OD']:.1f}  PLATE_T {f['PLATE_T']:.2f}"
          f"  FLOOR_X1 {f['FLOOR_X1']:.1f}  FLOOR_TOP {f['FLOOR_TOP']:.1f}"
          f"  WEDGE_RUN {f['WEDGE_RUN']:.1f}  SADDLE_LEN {f['SADDLE_LEN']:.1f}")
    print(f"  solids={len(part.solids())}  volume {part.volume/1000:.1f} cm3"
          f"  mass(ABS solid) {part.volume*ABS_RHO:.0f} g")
    print(f"  bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}"
          f"   z {bb.min.Z:.1f}..{bb.max.Z:.1f}")
    print(f"  first-layer bed area {ba:.1f} mm2")
    if cen is not None:
        print(f"  butt joint {area:.1f} mm2  centroid z {cen.Z:.2f}"
              f"  arm {65.0-cen.Z:.2f} mm"
              f"  M@2kN {2000*(65.0-cen.Z)/1000:.1f} N.m"
              f"  M@900N {900*(65.0-cen.Z)/1000:.1f} N.m")
        print(f"  bearing {2000/area:.2f} MPa @2kN, {900/area:.2f} MPa @900N")
    # how much of the joint is the tower's side plates vs its roof
    print()

# baseline for comparison
base = RT.gen_step()
bba = bed_area(base)
a0, c0 = butt_joint(base, FOOT, RT.SADDLE_LEN)
print("=== BASELINE bore 50.0")
print(f"  PLATE_T {RT.PLATE_T:.2f} SADDLE_LEN {RT.SADDLE_LEN:.1f}"
      f"  volume {base.volume/1000:.1f} cm3  mass(ABS) {base.volume*ABS_RHO:.0f} g")
print(f"  bed area {bba:.1f} mm2  butt {a0:.1f} mm2 centroid z {c0.Z:.2f}")
