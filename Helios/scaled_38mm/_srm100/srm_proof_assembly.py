"""SRM-100 as it goes on the hydrostatic proof rig: case, both closures, all five
O-rings, all 36 screws, and the 304 proof dummy in the insert's gland.  No graphite,
no insulators, no liner and no propellant.

Nothing is drawn or placed here: the rows are srm_assembly.proof_placements(), the
full motor's placements with the internals dropped and the dummy added, so every
part the proof loads sits exactly where it sits in the motor.
"""

from srm_assembly import proof_placements, tree


def gen_step():
    return {"children": tree(proof_placements())}
