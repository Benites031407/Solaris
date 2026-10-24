"""The motor case: 6061-T6 drawn tube, 100.0 OD x 4.0 wall, both ends radially bolted.

Frame: the MOTOR frame.  z = 0 at the aft end face, +Z forward.  Identity placement.

Features
  * bore 92.000 +0.030/0, honed Ra 0.4 (0.8 max), circumferential lay, over the
    plug seal zones at both ends.  A drawn tube will not arrive at 92.00: hone to
    the smallest clean-up diameter A and cut the plugs to it (srm_params: groove
    = A - 5.67, land = A - 0.06).
  * 20 deg x 1.1 radial O-ring lead-in on the bore at each end: deeper than the
    free ring's 0.80 protrusion, so the rings are squeezed, not sheared, going in.
  * 0.5 x 45 deg break on the outside edges.
  * 18 x CASE_HOLE_D radial holes per end, BOLT_EDGE from the end face (e/D 2.03),
    hole 0 keyed 0.8 deg off the even 20 deg pattern.  Match-drill with the
    closure in place, then ream the case holes to 6.40 +0.03/0 and tap the closure:
    eighteen holes cannot be made to line up any other way.  The keyed hole means
    the pair then only goes together one way; serialise each case end / closure
    pair anyway and engrave AFT / FWD on the case next to hole 0.
  * every hole broken 0.5 x 45 deg on the BORE side and polished: the O-rings are
    dragged across these holes on assembly.  Record each hole's axial and
    circumferential diameter as a baseline (the README's hole-gauging procedure).

Pressure boundary: the O-rings sit INBOARD of the bolt rows, so the bolt holes are
on the dry side of the seal and never see chamber gas.
"""

import math

from build123d import Axis

import srm_params as P
from srm_build import finish, one_solid, radial_countersink, radial_cylinder, revolve_rz

RI, RO, L = P.CASE_ID / 2.0, P.CASE_OD / 2.0, P.CASE_L
CH = P.CASE_END_CHAMFER
CHZ = CH / math.tan(math.radians(P.CASE_END_CHAMFER_DEG))
OC = 0.5
# the revolve's seam goes mid-pitch, clear of every hole: on the seam, hole 0's
# bore-side break (keyed 0.8 deg off it) cuts badly and is lost from the STEP
SEAM = P.BOLT_THETA0 + 0.5 * 360.0 / P.N_BOLTS


def gen_step():
    body = revolve_rz([
        (RI, CHZ), (RI + CH, 0.0), (RO - OC, 0.0), (RO, OC),
        (RO, L - OC), (RO - OC, L), (RI + CH, L), (RI, L - CHZ),
    ]).rotate(Axis.Z, SEAM)
    cutters = []
    for z in (P.bolt_z_aft(), P.bolt_z_fwd()):
        for th in P.bolt_thetas():
            cutters.append(radial_cylinder(P.CASE_HOLE_D, RI - 1.0, RO + 1.0, th, z))
            cutters.append(radial_countersink(P.CASE_HOLE_D, RI, P.CASE_HOLE_BORE_BREAK, th, z,
                                              outward=False))
    for c in cutters:
        body = body - c
    return finish(one_solid(body), "case_6061t6", (0.74, 0.76, 0.80))
