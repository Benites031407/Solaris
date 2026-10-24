"""Every dimension of the simple clamshell nose, in one place.

FRAME
-----
z = 0 is the aft face of the base ring's spigot, +z toward the tip, apex at
248.9655 -- the same origin as `cone_fixed.stl`, so the parts drop straight into
`rocket_assembly.py`'s stack.

The split plane is y = 0.  Half A occupies y > 0, half B occupies y < 0.  Each
half hinges about its own axis PARALLEL TO X, half A at y = +Y_PIN, half B at
y = -Y_PIN.  They open like a bivalve.

WHY THE HINGE AXIS SITS ON THE SKIN
-----------------------------------
Put the pin at (y = R_AIRFRAME, z = Z_SHELL_ROOT) and the opening is provably
interference-free with NO relief pockets anywhere.  Rotating a point by theta
about that axis gives

    dz' = -dy*sin(theta) + dz*cos(theta)

and every point of a shell has dy <= 0 (nothing is outboard of the skin) and
dz >= 0 (nothing is below the root), so dz' >= 0 for all theta <= 90 deg: no
shell point can ever reach below the root plane, so it cannot touch the ring.
Move the pin even 1 mm inboard and that stops being true -- the outboard corner
then dips sin(theta) mm per mm of offset and needs a swept-cylinder relief cut in
the ring's rim.  The price of the clean version is that the knuckle stands
R_KNUCKLE proud of the OD.  Paid, and faired.

ONE PART, PRINTED TWICE
-----------------------
Half B is half A rotated 180 deg about Z.  Every feature has to map onto its
counterpart under x -> -x, y -> -y:

    shell body      half annulus y>0 -> y<0                             ok
    hinge knuckle   centred on x = 0, so it maps to itself              ok
    latch tongue    at +x on half A -> -x on half B, so the two tongues
                    sit side by side and can never collide              ok
    vents           45/135 deg -> 225/315 deg, no mating requirement    ok
    seam sockets    placed at MIRRORED x, same z, so A's +x socket lines
                    up with B's +x socket (which is A's -x socket
                    rotated).  Loose dowels, not moulded pins: printing
                    flat on the split face, y = print-Z, so anything
                    protruding past y = 0 would protrude into the bed.
                    Only recesses are printable on a seam face.        ok

NAMING
------
Extents carry both ends (`Z_SHELL_ROOT` / `Z_SHELL_TIP`), never a bare number,
because the recurring bug on this project is a length spent against the wrong end
or in the wrong direction.  And A WALL IS ONLY A WALL PERPENDICULAR TO THE FACE
IT BACKS: `WALL` is normal to the skin, and `nose_profile.wall_normal_to_radial`
converts it to the radial step the CAD actually needs.
"""

from __future__ import annotations

import math

import nose_profile as prof

# ============================================================ airframe datums
# Measured off the STLs by radial ray casting plus vertex-ring extraction, and
# cross-checked against the scale factor on four independent features.
R_AIRFRAME = prof.R_AIRFRAME     # 32.75861; tube OD 65.51721
SCALE = prof.SCALE               # 1.310345 = 65.51721 / 50
Z_TIP = prof.Z_TIP               # 248.9655
Z_OGIVE = prof.Z_OGIVE           # 52.4138; plain cylinder below, ogive above

# The rocket's standard tube joint, reproduced so the base ring drops into
# Mbody's forward socket exactly like every other part in the stack.
SPIGOT_LEN = 26.2069             # = 20.000 x SCALE
R_SPIGOT = 31.1207               # male spigot OD radius, same as every spigot
R_MBODY_BORE = 31.2845           # Mbody's forward socket bore
SPIGOT_RADIAL_CLEAR = R_MBODY_BORE - R_SPIGOT        # 0.1638 radial, 0.3276 dia
MBODY_SOCKET_DEPTH = 27.5172     # socket is DEEPER than the spigot is long
SPIGOT_SPARE_TRAVEL = 1.6513     # so the joint is SHOULDER-located, not bottomed:
                                 # the OD step at z = SPIGOT_LEN lands on Mbody's
                                 # forward rim and that face sets the axial datum.
R_BEAD_MIN = 29.8901             # Mbody's depth-stop bead, 1.65 mm below the spigot

# ================================================================= the split
Z_SHELL_ROOT = 52.4138   # root of the printed half-shells
Z_SHELL_TIP = Z_TIP
SHELL_LEN = Z_SHELL_TIP - Z_SHELL_ROOT               # 196.5517 DESIGN length.
# NOT the printed length, and that word used to be here.  The half stops at
# Z_SHELL_TOP, TIP_DEFICIT below the apex -- see the tip block after SEAM_SETBACK.
# Split exactly at the tangent station.  It is the only z where the ring's top
# face is a true full-OD cylinder with zero taper, so ring and shell meet on a
# plain cylindrical land.  Split higher and the ring stands proud of the shell
# root by R_AIRFRAME - r(z) -- 0.113 mm at 54, 0.397 at 58 -- a forward-facing
# step into the airflow.  Split lower and the shells swallow plain cylinder the
# ring needs for the servo, the knuckles and the latch.

WALL = 2.0               # shell wall, NORMAL to the skin.  5 x 0.42 mm.
WALL_MIN = 1.26          # never fewer than 3 extrusions anywhere
R_SHELL_ROOT_IN = R_AIRFRAME - prof.wall_normal_to_radial(WALL, Z_SHELL_ROOT)
SEAM_SETBACK = 0.15      # per half, measured PERPENDICULAR to y=0, so 0.30 total

# --------------------------------------------------------------- THE BLUNT TIP
# The printed half does NOT reach the apex, and that is arithmetic, not a bug.
# The seam cut keeps y >= SEAM_SETBACK, so it deletes every section whose radius
# has fallen below 0.15 -- and any solid of revolution ends with r -> 0.  The
# profile's tip is a dead-straight cone of half-angle TIP_HALF_ANGLE over its
# last 6.25 mm (the per-row tangent is 0.260141 from z 242.664 to 248.914 and
# extrapolates to r = 0 at 248.96552 = Z_TIP + 1.5e-5), so the truncation is
# exactly SEAM_SETBACK / tan(TIP_HALF_ANGLE).  Measured: out/half_shell.stl tops
# out at 248.38885 against Z_SHELL_TOP 248.3888904 -- a 4.0e-5 mm float32 gap.
#
# DO NOT "FIX" THIS BY TAPERING THE SEAM TO ZERO AT THE APEX.  It was built and
# measured: a tilted half-space {y >= min(0.15, k(Z_TIP - z))} does put the CAD
# and STL apex at Z_TIP exactly (+0.000000 mm) for +0.05 mm3, and the halves
# still self-mate exactly (A & Rot180z(A) = 0.000000 mm3).  It buys nothing that
# prints.  y IS the build direction, so the taper moves the part's lowest point
# from the 1042.03 mm2 flat seam face to the apex: seat the flat face and all the
# new material is under the bed (printed gain 0.0000 mm), seat the apex and the
# whole seam face floats 0.15 mm over air on 0.114 mm2 of contact -- or prints
# flush and spends 100% of SEAM_SETBACK over all 194 mm of seam.  It also emits a
# zero-area facet at the razor apex, which makes nose_checks.assert_watertight
# RAISE and kills nose_verify before check 1.  The printer is the real limit and
# it is 1.33x coarser than the CAD: see Z_TIP_AS_PRINTED.  Fill and sand instead.
# (If you ever want the STL closed for a render or CFD only, the unique taper
# start that costs zero over-close margin is Z_TIP - (SEAM_SETBACK+EXTRUSION_W)/
# tan(TIP_HALF_ANGLE) = 246.774383, a 3.9163 deg tilt.  244.0 costs 63% of it.)
TIP_HALF_ANGLE = prof.slope_deg(Z_TIP - 2.0)         # 14.5818011757 deg
Z_SHELL_TOP = Z_TIP - SEAM_SETBACK / math.tan(math.radians(TIP_HALF_ANGLE))
TIP_DEFICIT = Z_TIP - Z_SHELL_TOP                    # 0.5766096, 0.232% of length
SHELL_LEN_PRINTED = Z_SHELL_TOP - Z_SHELL_ROOT       # 195.9751

ROOT_GAP = 0.20          # ring top sits this far below the shell root
Z_RING_TOP = Z_SHELL_ROOT - ROOT_GAP                 # 52.2138
ROOT_CHAMFER = 0.3       # NO locating lip -- see below.
# AND IT IS NOT A JOINT CHAMFER, WHICH IS WHAT THIS USED TO SAY.  The old comment
# read "on both mating faces, so the butt joint cannot be held open by a print
# corner" and every clause of that was wrong.  There is no butt joint here: the
# shell's root face sits ROOT_GAP = 0.20 mm ABOVE the ring's top face and the two
# never touch, by design.  Nor can they be brought together -- the knuckle has
# (PIN_BORE_KNUCKLE - D_PIN)/2 = 0.15 mm of slop on the pin, so the pin bottoms in
# its bore 0.05 mm before the faces would meet, and steel takes that load rather
# than a printed annulus.  Nor is the chamfer on both faces: the ring's own edge
# carries base_ring.TOP_CHAMFER = 0.4, a different number for a different reason.
# What this chamfer is actually for is the OUTSIDE: it breaks the shell root's OD
# edge so a first-layer bulge cannot stand proud into the airflow.  0.6 mm of it,
# facing 0.4 mm of ring chamfer across a 0.2 mm gap, cut a 1.2 mm wide by 0.6 mm
# deep groove right round the airframe at the shoulder.  0.3 halves that and still
# de-burrs the edge, which is all it was ever doing.  self_check() asserts the pin
# bottoms first, so the claim above stays true if either number moves.
# A tall internal locating lip is impossible here and it is worth knowing why.
# The shell turns rigidly about a pin in the root plane, so a root-plane point at
# distance d from the pin lifts by d*sin(theta).  AT THE HINGE AZIMUTH that
# distance is one wall thickness, 2.005 mm, so the tallest lip that still clears
# is 0.52 mm at 15 deg and 1.00 mm at 30 deg.  The lip height would be spent
# along z, but the motion available is set by a lever arm one wall thick.  So:
# plain butt face, chamfered, and take shear through the knuckles and the latch.

# ==================================================================== hinge
# THE PIN SITS OUTBOARD OF THE SKIN, not on it.  On the skin is where the
# kinematics want it, but it cannot be BUILT there: the ring's lug has to close
# around the pin, so it needs material inboard of the bore, and inboard of a
# bore centred on the skin is inside the shell's own wall -- the lug would grow
# into the very volume the shell sweeps through.  Offsetting the pin outboard
# buys that material outside the OD where nothing else lives.
#
# It does not weaken the no-interference proof, it strengthens it.  The proof
# needs dy <= 0 for every shell point, i.e. the whole shell inboard of the pin.
# Moving the pin OUT makes every dy more negative, so -dy*sin(theta) grows and
# every point rises FASTER.  Moving it in is what breaks the proof.  A useful
# side effect: at the hinge azimuth the root face lifts off the ring immediately
# at PIN_OFFSET*sin(theta) -- 0.16 mm per degree -- so the mating faces separate
# before anything can scrub.
#
# AND IT SITS ABOVE THE ROOT PLANE, not in it.  A pin lying in the root plane can
# only ever be half-wrapped by the shell, because the shell's material starts at
# that plane -- the knuckle comes out a hook open downward, and the pin bore
# boolean removes exactly half the volume it should, which is how this was
# caught.  Raising the pin by PIN_RISE puts the whole bore inside shell material.
#
# The proof survives the raise, in a slightly weaker but sufficient form.  With
# dz measured from the pin, shell points now have dz >= -PIN_RISE rather than
# dz >= 0, and dz' = |dy|*sin(t) + dz*cos(t).  If dz >= 0 then dz' >= 0.  If
# dz < 0 then dz' >= dz*cos(t) >= dz.  Either way dz' >= -PIN_RISE, which is
# exactly the root plane: still no shell point can ever dip below it.
PIN_OFFSET = 3.0
PIN_RISE = 2.6
Y_PIN = R_AIRFRAME + PIN_OFFSET          # 35.7586
Z_PIN = Z_SHELL_ROOT + PIN_RISE          # 55.0138
D_PIN = 2.0                              # 2 mm steel rod (TIG filler, or a nail)
PIN_BORE_KNUCKLE = 2.30                  # +0.30: this is the rotating joint
PIN_BORE_LUG = 2.10                      # tighter, so the pin cannot walk out
R_KNUCKLE = 2.6                          # shell side, about the pin
KNUCKLE_W = 10.0                         # centred on x = 0 so it maps to itself
KNUCKLE_WEB_Y = 31.5     # web reaches this far in, and it has to end up INSIDE the
                         # wall: in the shell's print pose y is the build direction,
                         # so this face's normal points at the bed.  Buried it is not
                         # a face at all; exposed it is a 10 x 5.2 mm island printed
                         # on air.  Which it is depends on the skin at the worst
                         # corner -- largest |x|, largest z -- and at 32.0 the margin
                         # there was +0.0010 mm.  One micron, i.e. gone the moment
                         # ABS_SHRINK compensation or a tuned flow rate touches it.
                         # 31.5 buries it by 0.5010 mm and costs 26 mm3.
                         # self_check() asserts the margin.
KNUCKLE_Z_TOP = Z_PIN + R_KNUCKLE        # 57.6138: 1.45 mm of material over the bore,
                                         # and 1.45 mm under it down to the root plane
KNUCKLE_CHAMFER = 1.5                    # outboard-BOTTOM corner.  Same corner as the
                                         # lug's, for the mirror-image reason: this is
                                         # the one part of the shell standing outboard
                                         # of the pin, so it swings DOWN and IN as the
                                         # nose opens, and at 90 deg the sharp corner
                                         # would pass 0.40 mm off the ring's collar.
                                         # Chamfered, the closest approach is 1.47 mm.
TORSION_GAP = 5.5                        # one torsion spring each side
LUG_W = 4.5
LUG_X_IN = KNUCKLE_W / 2 + TORSION_GAP   # 10.5
LUG_X_OUT = LUG_X_IN + LUG_W             # 15.0
PIN_LEN = 2 * LUG_X_OUT                  # 30.0 -> cut a 32 mm rod
LUG_Y_IN = 33.5                          # 0.74 clear of the OD; see the sweep check
LUG_Y_OUT = 39.11                        # 2.30 of material outboard of the bore
LUG_Z_TOP = Z_PIN + 2.35                 # 57.3638: 1.30 mm over the (tighter) lug bore.
                                         # Kept as LOW as the bore allows -- the lower
                                         # the lug's top, the more room the shell swings
LUG_CHAMFER = 1.4                        # on the OUTBOARD-BOTTOM corner, the one corner
                                         # of the lug that the shell's sweep can reach;
                                         # see the sweep check for the 1.4 mm
LUG_Y_BORE = 20.0                        # the lug is built reaching well INSIDE the
                                         # bore and then trimmed by the boring cut, so
                                         # its inboard face ends up following the bore
                                         # exactly.  A flat inboard face at y = 28.5
                                         # would leave only 0.63 mm of shared wall at
                                         # x = 15 -- a hinge lug hanging off a 0.6 mm
                                         # web.  Both of these points sit BELOW the
                                         # root plane, where no shell point in the
                                         # lug's x band can ever reach, so they do not
                                         # enter the sweep check.
LUG_Z_BOT = 44.0
LUG_RAMP_Z = 38.0                        # fairing starts here, ~63 deg from
                                         # horizontal, so it prints upright unsupported
TORSION_COIL_OD_MAX = 6.0                # so the coil (r <= 3.0 about the pin) stays
                                         # outboard of the OD and needs no relief cut

# The opening spring: a torsion spring per side, over the pin, legs seated in the
# knuckle's end face and the lug's inner face.  Chosen over compression springs
# after trying to package those: a pocket for even a 4 mm spring does not fit in
# the collar wall, and every variant needed a new boss, a new tab and a new
# clearance check.  A torsion spring needs almost none of that -- the pin, the
# knuckle and the lug already exist, the moment lands straight on the hinge axis
# with no lever-arm bookkeeping, and the COIL needs no retention at all because
# TORSION_GAP is bounded by two existing flat faces that already trap it.
#
# WHAT IT GETS YOU, AND THIS BLOCK HAS NOW BEEN WRONG TWICE.  It first claimed 30
# N.mm per spring, 60 per half, which was simply invented.  It then claimed 5.44 and
# 10.88, which came out of a UNIT ERROR in TORSION_RATE below: the 10.8 in that
# formula is a per-TURN constant, and this file divided by 180/pi as though it were
# per radian, so every spring number in this block was too large by exactly 2 pi.
# Corrected, the spring that was ALREADY SPECIFIED here (0.32 wire, 15 coils) delivers
# 0.87 N.mm each, not 5.44 -- and, far more usefully, it sat at 269 of the 1700 N/mm2
# allowable, not the 1690 this block used to report.  So the claim that "no spring
# that fits this pocket can do that, and no amount of shopping will find one" was an
# arithmetic artefact.  The pocket was never the constraint.  The wire was 16% loaded.
#
# Re-solved with the correct rate, same method as before: take the thickest wire whose
# bending stress at the FULL 100 deg of travel stays inside TORSION_SIGMA_ALLOW, with
# the body inside the gap, both legs still engaged in their seats at worst-case float,
# and the coil unable to reach the skin even when shoved fully off-centre on the pin
# -- and the answer is 10.20 N.mm each, 20.40 N.mm per half, at 831 of 1700 (49%).
# spring_check() asserts every one of those constraints and now also asserts that
# OPEN_MOMENT beats BENCH_MOMENT_WORST AT ALL, which nothing in this project ever did
# -- which is exactly how a 2 pi error got as far as a bill of materials.
#
# The consequences, restated because they are now the opposite of what stood here:
#   * IN FLIGHT this is fine.  At apogee the rocket is in free fall, so gravity does
#     not oppose the halves at all -- the springs fight only pin friction and the
#     halves' own inertia, and 20.40 N.mm swings a half 60 deg in 144 ms.
#   * ON THE BENCH it is now fine in EVERY attitude.  Worst-case gravity on one half
#     about the hinge is W * r_cg = 0.2486 N * 69.32 mm = 17.24 N.mm, against 20.40
#     -- 1.18x.  A half that hangs nose-down off a horizontal pin lifts itself.  The
#     whole acceptance box below spans 1.14..1.62x, so that does not depend on hitting
#     the nominal spring.  TORSION_GAP stays 5.5: the note that used to stand here
#     about needing to widen it to ~10 to reach 1.0x was chasing the same 2 pi.
# Both legs sit in BLIND SEATS, which is what fixes the travel at 100 deg: the free
# angle must be the fully-open leg angle, because a spring that went slack early would
# then be driven the other way and push the nose shut.  That in turn forbids the
# stiffer short-stroke springs that would otherwise fit -- and it is no loss, because
# energy is 1/2 T theta, so a longer stroke delivers the same energy at LOWER peak
# torque, which is also lower latch load and lower servo torque.
#
# IT ALSO PINS THE FREE ANGLE AT 170 AND NOT THE MORE BUYABLE 180, and that is a
# strength limit, not a packaging one.  There is no designed stop, so an undamped half
# released from closed turns past open to theta_max = 2 * (F - 70), where F is the free
# included leg angle -- and THE RATE CANCELS, so the overswing is a property of F
# alone, identical for a weak spring and a strong one.  The airframe body tube is the
# stop: swept against the tube envelope, the shell's inner surface first touches at
# THETA_TUBE_STOP = 190.5 deg.  At F = 170 the free turning point is 200 deg, so the tube
# is met 9.5 deg short of it, nearly at rest -- 5.99 rad/s, 3.22 mJ, 1.18 m/s at the tip
# (spring_check() derives all three from the rate; they are not quoted).  At F = 180 the
# turning point moves to 220 deg and the half is still accelerating hard when it arrives.
# The rate is unchanged by F, so the arrival speed goes as TRAVEL * sin(phi_tube) and the
# energy as its square: (110/100 * 0.6816/0.4254)^2 = 3.1x.  A 180 deg spring is easier
# to buy.  Arriving at the tube with 3x the energy is not worth it, and see WHY THIS IS
# WOUND AND NOT BOUGHT below.  (This used to claim 13x, which no calculation in this file
# reproduces; the honest figure is 3.1x and it is still the right decision.)
#
# WHY THIS IS WOUND AND NOT BOUGHT.  Ø0.50 mm ASTM A228 is a stock MATERIAL -- it is
# a plain steel guitar string; .020 in is 0.508 mm and lands inside the acceptance box
# below -- but a finished spring to this drawing is not a stock PART, and correcting
# the 2 pi did not change that.  Three things rule the catalogue out, and none is
# torque: (1) the coil has to clear a Ø2.0 pin AND stay inside POCKET_FREE_R, so
# D_mean is boxed into 3.10..4.45 mm, which is the very fine end of any stock range;
# (2) TORSION_GAP is 5.5 mm, so n*d < 5.5 -- a stock 0.5 mm spring with the usual
# 15..20 coils is three times too long; (3) the killer -- stock torsion springs come
# with STRAIGHT TANGENTIAL legs, and bending one to reach an axial seat at
# TORSION_LEG_R shifts its tail by arccos((D_mean/2)/TORSION_LEG_R) = 50 deg.  The two
# legs leave the coil in opposite helical senses, so the two shifts ADD: 100 deg of
# free-angle error, which no stock free-angle tolerance absorbs.  What makes the wound
# part easy instead is that the JIG gauges the finished tail azimuths directly, so
# that 100 deg never has to be held -- and the acceptance box is 3 coils and 0.9 mm of
# mean diameter wide, so nothing is bought or made to a tolerance.  See spring_jig.py.
TORSION_WIRE_D = 0.50            # ASTM A228 music wire (= a plain steel guitar string;
                                 # .020 in = 0.508 mm is inside the box).  ACCEPTANCE
                                 # BOX: n in {7.472, 8.472, 9.472, 10.472} (see
                                 # TORSION_COILS -- the fractional part is not free),
                                 # D_mean 3.20..4.30 (low end from ID over the Ø2.0 pin,
                                 # high end from the unwound far edge vs POCKET_FREE_R),
                                 # and the one governing inequality n * D_mean <= 34,
                                 # which is the strict bench limit of 38.61 with 14% held
                                 # back, since
                                 # T = 5324.07 * d^4 / (D_mean * n) at 100 deg.  The
                                 # stress-only floor for 1.0x bench gravity is
                                 # d = 0.3724 -- THINNER than the 0.32 this file used
                                 # to call the ceiling.  Ø0.47..0.66 all clear 1.0x;
                                 # above 0.66 the wound body no longer fits the gap.
TORSION_COILS = 8.472            # NOT an integer, and it cannot be one.  The two legs
                                 # leave opposite ends of the coil, so the angle between
                                 # them IS the total wrap: the free included angle of
                                 # 170 deg forces n mod 1 = 170/360 = 0.4722, and the
                                 # only legal coil counts are 7.472, 8.472, 9.472,
                                 # 10.472.  This constant read a round 8 until
                                 # spring_jig.py had to answer "wind how many turns?"
                                 # and the answer came back "8 turns, then lay the tail
                                 # in the 170 deg gauge", which is 8.472.  Rounding it
                                 # to 8 overstated the torque by 5.5%.
                                 # 8.472 is mid-window: fewer coils is MORE torque and a
                                 # shorter part to wind, both of which point the same way
                                 # here, but 7.472 wants a longer wire tail for the same
                                 # grip.  All four legal counts pass spring_check() at
                                 # D_mean 3.60; at 9.472 and above, D_mean 4.10 does not
                                 # (0.99x bench), which is what n * D_mean <= 34 below is
                                 # protecting.
TORSION_COIL_D_MEAN = 3.85       # -> OD 4.35, ID 3.35 over the 2.0 mm pin.  This is NOT
                                 # a chosen number, it is what a Ø3.0 mandrel gives: 3.0
                                 # + d = 3.50 as-wound, plus the 5..15% springback music
                                 # wire at index 7 takes on release = 3.68..4.03, and
                                 # 3.85 is the middle.  Ø3.0 because a 3 mm dowel pin,
                                 # drill blank or drill shank is in every drawer, which
                                 # was the entire point of revisiting this spring; 2.7
                                 # would centre D_mean on 3.60 and is a real but much
                                 # rarer size.  The one number the jig cannot hold, and
                                 # it does not have to: 0..24% springback all lands in
                                 # the box, and at 24% the coil's unwound far edge hits
                                 # POCKET_FREE_R, which spring_jig.py's Ø6.90 ring
                                 # physically refuses.  If it comes out FAT (over 4.0),
                                 # wind 7.472 turns instead of 8.472 and the bench margin
                                 # goes back from 1.09x to 1.23x.
TORSION_SIGMA_ALLOW = 1700.0     # N/mm2, ~70% of A228 tensile at this wire size.
                                 # One cycle per flight, not fatigue service.
TORSION_E = 207000.0             # N/mm2
TORSION_LEG_R = 2.8              # both leg seats sit this far off the pin axis, so
                                 # one spring serves either end.  2.4 also lands in
                                 # solid material but leaves the knuckle only 0.80 mm
                                 # of wall to the pin bore and puts the leg inside the
                                 # coil's own OD; 2.8 gives 1.20 and clears it.
TORSION_SEAT_D = 0.9             # Ø0.9 for a Ø0.50 wire, and Ø0.9 DELIBERATELY kept
                                 # when the wire grew: 0.7 would halve the slop but a
                                 # Ø0.7 hole printed at 0.42 mm extrusion width
                                 # finishes undersize and may refuse the wire.  NOT a
                                 # press fit -- the leg only ever pushes, so the
                                 # remaining 0.20 mm of radial slop costs
                                 # atan(0.20/2.8) = +-4.09 deg of free angle per leg,
                                 # i.e. 170 +-8.2 worst case both legs -> 1.23..1.45x
                                 # and a resting open angle of 91.8..108.2 deg.  That
                                 # is BETTER than the 0.29 mm the Ø0.32 wire had.
                                 # Sized to print as an open feature and to clean up
                                 # with a 0.9 mm drill.
TORSION_SEAT_DEPTH = 3.0         # also the axial length of the bent leg, which is what
                                 # makes the spring self-locating: see spring_check().
                                 # 2.0 -> 3.0 is the one printed-geometry change the
                                 # new spring needs, and it buys coil-body clearance
                                 # one-for-one, because leg engagement at worst float
                                 # is body_unwound + DEPTH - TORSION_GAP.  At 2.0 the
                                 # legal coil count is n in (8.28, 10.72), a 2.44-coil
                                 # window; at 3.0 it is (6.28, 10.72), 4.44 coils.
                                 # Still under KNUCKLE_W/2 = 5.0 and LUG_W = 4.5, which
                                 # assertion 8 checks and which is what makes it legal.
TORSION_SEAT_AZ_KNUCKLE = 180.0  # measured about the pin from +y (radially OUT),
TORSION_SEAT_AZ_LUG = 250.0      # +z = 90.  Both mesh-verified 15/15 solid at r 2.8 by
                                 # _scratch/_seat_probe.py.  The bands are disjoint:
                                 # 210..290 on the knuckle is air (KNUCKLE_CHAMFER eats
                                 # it) and 180 on the lug falls inboard of LUG_Y_IN, so
                                 # no single azimuth serves both ends.
TORSION_TRAVEL = 100.0           # deg of wind-up from free (open) to closed
TORSION_COUNT_PER_HINGE = 2
POCKET_FREE_R = 3.45             # mm, the SMALLEST free radius about the pin anywhere
                                 # the coil can reach -- at the knuckle end of the
                                 # pocket, not the roomier 4.05 at its middle, because
                                 # the coil can slide up against that face.  Measured
                                 # off the exported meshes by _spring_envelope.py.
# k = E d^4 / (10.8 D n) N.mm PER TURN, hence the /360 to get N.mm per degree.
#
# THE UNIT IS THE WHOLE POINT AND THIS FILE GOT IT WRONG.  Shigley's / Associated
# Spring's 10.8 form is moment per REVOLUTION.  This line used to divide by
# 57.29577951308232 = 180/pi, which is the conversion you apply to a per-RADIAN rate,
# and the result was every spring number in this file too large by 360/(180/pi) = 2 pi.
# Two independent checks that 360 is right: (a) a torsion coil is a straight beam of
# length L = pi D n in bending, so k = E I / L with I = pi d^4 / 64, which gives
# E d^4 / (10.186 D n) per turn -- the 10.8 is that same expression softened ~6% for
# coil friction, so it is unambiguously per turn; (b) run it both ways for the old
# 0.32/15/4.30 spring: /360 gives 0.008655 N.mm/deg, beam theory gives 0.009177, and
# the /57.2958 this file used gave 0.054383 -- 6.28319x the first, which is 2 pi.
#
# Straight legs would add (L1+L2)/(3 pi D) ~ 0.13 to the effective coil count, lowering
# the rate; ignoring them errs toward MORE stress than the spring really sees, which is
# the safe way.
TORSION_RATE = (TORSION_E * TORSION_WIRE_D ** 4
                / (10.8 * TORSION_COIL_D_MEAN * TORSION_COILS)) / 360.0
TORSION_MOMENT_EACH = TORSION_RATE * TORSION_TRAVEL            # 10.20 N.mm at closed
OPEN_MOMENT = TORSION_MOMENT_EACH * TORSION_COUNT_PER_HINGE    # 20.40 N.mm per half

# What the spring has to beat, and how fast it moves the half once it wins.  All three
# are properties of the printed half, so all three are measured off the exported mesh
# by _scratch/_spring_bench.py rather than estimated here.
HALF_W_N = 0.25033               # N, one printed half (25.518 g of ABS)
HALF_R_CG = 68.920               # mm from the hinge AXIS to that half's CG
HALF_I_PIN = 1.8007e-4           # kg.m2 about the hinge axis (I_cg,xx 5.886e-5 plus
                                 # 1.212e-4 of parallel-axis term -- the CG is 69 mm
                                 # off the pin, so the transfer term dominates 2.1:1)
# The hook fix and the root post pad added 0.17 cm3 to the half, so W went up 0.7 % --
# and r_cg went DOWN 0.40 mm, because all of the new material is within 6 mm of the
# root and it pulled the CG toward the hinge.  The two very nearly cancel: the bench
# moment moved 17.236 -> 17.253 N.mm, 0.1 %.  Worth writing down because the obvious
# worry about a heavier half is that the springs stop lifting it, and they did not
# notice.
BENCH_MOMENT_WORST = HALF_W_N * HALF_R_CG      # 17.25 N.mm, pin horizontal, half
                                               # hanging nose-down.  The pad case
                                               # (pin horizontal, rocket vertical) is
                                               # only W*|dy| = 5.31 N.mm.
THETA_TUBE_STOP = 190.5          # deg of opening at which the half's INNER SURFACE first
                                 # touches the airframe body tube -- the only stop this
                                 # design has, and it is not a designed one.  Swept off
                                 # the exported half against the tube envelope by
                                 # _scratch/_spring_bench.py.  It matters because there
                                 # is no latch or damper past open: the half coasts to
                                 # 2 * TORSION_TRAVEL and this is what it hits on the way.

# =========================================================== latch and tongue
# THE TONGUE IS A HOOK, AND WHICH SIDE OF THE ARM IT GRABS IS THE WHOLE DESIGN.
#
# Every point of a half lies INBOARD of its own hinge pin (|y| < Y_PIN), so from
# rotate_open below,
#
#     dz'/dtheta = Y_PIN - |y|  >  0     ALWAYS
#
# i.e. the tongue RISES as the half opens -- +0.595 mm per degree at the latch.
# A bar sitting UNDER a flat blade therefore restrains nothing at all: it blocks
# the one direction the tongue never goes.  This design shipped once with exactly
# that mistake (a "plain blade, no hook, no notch", its flat bottom face called
# "the latch load face, facing DOWN"), and the halves were held shut by nothing.
# Confirmed four ways before it was changed: the velocity is +34.109*omega at the
# blade; rotate_open puts the old face at z 47.60 after 1 deg and 50.00 after 5;
# unilateral-contact statics admits no non-negative normal force (the only
# solution to sum Mx = 0 is N = -OPEN_MOMENT/34.1086 = -0.5982 N, i.e. tension,
# which a face cannot supply -- the SIGN is the whole argument and it does not
# depend on the spring, which is why this has now survived OPEN_MOMENT being 60,
# then 10.88, then 23.11, then 20.40); and a face-normal census of
# the exported STL found 15.000 mm2 of
# DOWN-facing area at z = 47.0 and 0.000 mm2 of UP-facing area anywhere below the
# root -- there was no hook.  So:
#
#     THE LATCH FACE IS Z_LATCH_FACE = Z_ARM_BOT AND IT FACES UP (+z).
#     The foot passes UNDER the arm and pushes the arm UP into the thrust pad.
#
# The tongue is one J-shaped polygon in the (x, z) plane, extruded across y:
# an upper blade at the shell root, a WEB that runs down OUTBOARD of the arm's
# swept circle, and a FOOT that turns back inboard underneath the arm.  The
# pocket between the web and the upper blade is where the arm lives.
TONGUE_X0 = 20.5         # half A at +x; half B gets -x, so they sit side by side
TONGUE_X1 = 25.5
TONGUE_Y0 = SEAM_SETBACK          # entirely on half A's side of the split plane,
TONGUE_Y1 = SEAM_SETBACK + 3.0    # so it cannot foul half B's wall
Z_TONGUE_TOP = 62.0     # top of the gusset that ties it into the shell wall
GUSSET_X = 25.5         # documents where the gusset USED to start narrowing; the
                        # gusset is now full depth, so nothing reads this.

# THE GUSSET USED TO TAPER BACKWARDS, AND THAT IS WHY THE HOOKS SNAP.
# GUSSET_Z_TOP was the literal Z_SHELL_ROOT + 0.6 = 53.0138, buried inside
# tongue_profile().  The gusset is the tongue's ONLY attachment to the shell, and
# at 0.6 mm it was 9.5862 mm deep in z at x = 25.5 where the load enters and
# 0.6000 mm at x = 31.2 at the support -- the bending moment grew toward the
# support exactly as the depth collapsed.  Measured weld: 4.7188 mm2, 1.4689 to
# 1.7565 mm tall, S = 1.2310 mm3, 4.2725 MPa at the 0.5982 N latch load on an
# 8.79 mm arm.  With Kt 2.2 for the sharp re-entrant corner that breaks at 2.546 N
# at the foot = 0.448 N (46 gf) applied at the nose tip, and a 5 g knock on one
# half already reaches 0.99x of it.  Sideways it is worse: a y-load twists that
# 3.0 x 1.5691 mm patch and the shear lands on constant-y planes, which ARE the
# layer bonds, so it peels at 1.248 N -- while a stalled MG90S driven into a foot
# that is not fully down delivers 9.86 N.  That is the failure, 7.9x over.
# Full depth makes the weld 28.8310 mm2 / 9.5862 mm tall / S 45.9476 mm3 (x37.3)
# at 0.1145 MPa.  Nothing binds it: the spur's outboard face at x 31.2, y 0.15 is
# r 31.2004, while r_in runs 30.7536 -> 30.073 and r_out 32.7586 -> 32.078 over
# z 52.4138..62.0, so the face is buried in the wall at every station.  Costs
# 76.83 mm3 of tongue (0.080 g) and 55.04 mm3 = 0.055 cm3 of chute cavity.
GUSSET_Z_TOP = Z_TONGUE_TOP      # 62.0; was Z_SHELL_ROOT + 0.6 = 53.0138

# THE ARM'S WIDTH AND ITS HALF-LENGTH ARE NOT INDEPENDENT, AND THE DEPENDENCE RUNS
# BACKWARDS FROM WHAT THE NAMES SUGGEST.  LATCH_ARM_R never enters the built solid
# at all: latch_arm._blank() is (bar 2*ARM_CORNER_R + 2 long x LATCH_ARM_W) & (disc
# of ARM_CORNER_R), so it is the DISC that decides where the arm ends, at every
# azimuth, and LATCH_ARM_R is only the corner's x when y = LATCH_ARM_W/2.  Every
# downstream number the hook cares about -- WEB_X_IN, t_web, the foot overlap, the
# bearing land, f_z_break -- reads ARM_CORNER_R and nothing else (latch_bearing_r(),
# :1618).  So ARM_CORNER_R is FROZEN as a literal here and LATCH_ARM_R is DERIVED
# from it, which is the inversion that lets the bar be widened for the servo horn
# without disturbing one digit of the hook load path.
#
# The frozen value is sqrt(500) = 22.360680, which is what hypot(22.0, 4.0) rounded
# to at the old LATCH_ARM_W 8.0 -- 23.3452 was the stale comment on the old line and
# was never the value.  Widening the bar 8.0 -> 10.50 therefore pulls LATCH_ARM_R in
# 22.0 -> 21.7356 rather than pushing the corner out to 24.0, and WEB_X_IN stays at
# 23.07, t_web at 2.4300, the foot overlap at exactly 1.6377 mm against the > 1.5
# assert in latch_arm.py, and f_z_break at 20.1392 N = 361.0 gf.  Letting the corner
# float instead collapses the hook to 299.2 gf and FAILS the > 3.0x handling assert
# at :2185.  Verified bit-identical, not argued.
#
# Why the old 22.0 was right, kept because the reasoning is what pins sqrt(500): the
# comment before it said "must reach under the blades at x 20.5..25.5", which was
# never true -- the arc made the arm stop at 23.1317, not 25.5.  Pulling the corner
# in 1.0 mm pulled WEB_X_IN from 24.05 to 23.07 and took the hook's web from 1.450 to
# 2.430 mm, Sy 1.0512 -> 2.9524 mm3, which is the only lever that thickens the web
# without reprinting the bulkhead, and it left WEB_CLEAR -- the running fit, 0.710 mm
# -- untouched.  A corner at 21.5 would leave 1.1409 mm of foot and FAIL.
# Together with the full-depth gusset: break load at the foot 2.546 -> 18.294 N
# (x7.19), at the nose tip 46 -> 328 gf, sideways 1.248 -> 12.901 N (x10.34),
# which finally clears the 10.54 N stalled-servo jam by 1.22x.
#
# LATCH_ARM_W IS 10.50 BECAUSE THE HORN'S BLADE IS 7.2 mm WIDE, MEASURED.  A 7.2 mm
# blade needs a 7.6 mm slot (0.20 mm per flank, and see HORN_SLOT_W for why 7.5 is
# not enough), and a 7.6 mm slot in an 8.0 mm bar leaves 0.20 mm flanks -- half an
# extrusion, which does not print, and horn_drive_stress() puts the factor of safety
# of that flank at 0.054 against a stalled servo even if it did.  The
# feasible window was found by running the real asserts, not by reasoning: W must be
# >= 10.26 to leave WALL_MIN either side of the Ø7.73 hub recess AND the 7.6 slot,
# and < 10.759658 before th_free (:2437) eats the sweep.  10.50 sits in the middle of
# a 0.50 mm window.  It costs a bulkhead reprint -- fin_notch_half() widens with W --
# and nothing else.
LATCH_ARM_W = 10.50     # was 8.0; 8.0 cannot swallow a 7.2 mm blade at any T
ARM_CORNER_R = math.sqrt(500.0)     # 22.360680, FROZEN.  See the note above: this
                                    # is the arm's real outline and the whole hook
                                    # load path hangs off it, so it is a literal and
                                    # LATCH_ARM_R is what moves when the bar widens.
LATCH_ARM_R = math.sqrt(ARM_CORNER_R ** 2 - (LATCH_ARM_W / 2) ** 2)     # 21.7356
# THE ARM IS 8.4 THICK, NOT 4.4, AND THE SERVO MOVED DOWN 4 mm TO PAY FOR IT.
# 4.4 was set by "just thick enough to be stiff", which is the wrong criterion:
# the arm has to SWALLOW THE HORN.  Its top face is pinned at 47.0 by the thrust
# pad and its underside clears the servo case by 0.1 mm, so there is nowhere for a
# stock MG90S horn to live except inside the arm.  That horn's hub stands about
# 4.7 mm off the case, so a 4.4 mm arm cannot contain it -- the hub would come out
# 0.3 mm above the arm's own top face and hold it off the pad.
# Thickening the arm costs only z in the servo bay, of which there was 20 mm going
# spare below the servo, and the user said not to worry about mass.
LATCH_ARM_T = 8.4       # z 38.6..47.0
Z_ARM_TOP = 47.0        # bears UP on the bulkhead's thrust pad.  A literal, not
                        # Z_BULK_BOT - THRUST_PAD_DROP, only because both of those
                        # are declared further down; self_check() asserts the two
                        # agree, and that assert is now load-bearing for real.
Z_ARM_BOT = Z_ARM_TOP - LATCH_ARM_T      # 38.6 -- the LATCH face; the foot bears
                                         # UP on this, so the arm is in bending
# --- how the arm couples to the shaft.  Torque through the SLOT, retention
# through the shaft screw: the horn's lever sits in a 4.6 mm slot in the arm's
# underside and its flanks carry it -- 9.4 N.mm at worst, re-latching, which is
# what spring_check() reports; this said 35.7 back when the springs were believed
# to be 30 N.mm each.  Meanwhile the servo's own centre screw
# clamps arm + horn + shaft into one stack.  No auxiliary screws, no printed
# spline (a 25T spline at 0.6 mm pitch does not survive a 0.4 mm nozzle), and no
# fastener heads anywhere near the 0.5 mm gap under the bulkhead.
#
# HORN_POCKET_DEPTH IS THE ONE DIMENSION TO MEASURE BEFORE PRINTING.  Horn hubs
# vary by a millimetre between brands, and the clamp only works if the pocket
# floor actually lands on the hub's top face.  Nominal 5.70, which is also the
# CEILING at LATCH_ARM_T 8.4; if yours is shorter the arm floats and the screw
# clamps nothing, so shim it -- and if it is taller, file the hub's TOP face down
# to 5.70, which is free because this design does not use the hub's own screw
# countersink.  Reprint the arm: it is a 2.0 g part (this used to say 10 g while
# README.md's own table said 2.28 cm3 / 2.4 g).
#
# THE HORN IS DATA NOW, NOT A BACK-DERIVED CARTOON.  These four numbers lived in
# nose_assembly.py as HORN_HUB_D 8.0 / HORN_HUB_H 4.7 / HORN_LEVER_W 4.4 /
# HORN_LEVER_R 9.0, every one of them obtained by subtracting a clearance from the
# pocket it was supposed to fit -- so the reference solid could never disagree with
# the pocket and the pocket was never checked against a real part.  It did not
# fit: HORN_LEVER_R was wrong by a factor of two.
HORN_HUB_D = 7.43        # MEASURED across the round hub in the middle of the horn
HORN_HUB_H = 5.00        # MEASURED hub height above the servo case face.  Was 5.70,
                         # which was the CEILING at LATCH_ARM_T 8.4 taken as a
                         # nominal; the real hub is 5.00, so the pocket floor comes
                         # down with it and the counterbore gains 0.70 mm of floor.
                         # IDENTICALLY HORN_POCKET_DEPTH -- that is the clamp
                         # condition, and asserting it is what this file is for.
# THE BLADE IS NOT A CONSTANT WIDTH AND PRETENDING IT WAS IS WHY THE ARM DID NOT FIT.
# MEASURED: 7.2 mm across the middle, tapering to 4.1 mm at the tips, and the 7.2 mm
# section runs 22.5 mm end to end -- so it is 7.2 wide out to |x| = 11.25 and only
# then starts to narrow.  A slot sized on the tip width (the old 4.6, a number that
# was itself back-derived from the pocket it was meant to fit) interferes with 6.75 mm
# of blade per side.  horn_lever_w() is the envelope and the asserts walk it, so a
# slot that is wide at the hub and narrow further out fails loudly.
HORN_LEVER_W = 7.2       # MEASURED, at the middle.  The MAXIMUM of the envelope --
                         # this is the one that sizes HORN_SLOT_W and hence the bar.
HORN_LEVER_W_TIP = 4.1   # MEASURED, at the tip
HORN_LEVER_W_FULL = 11.25    # |x| out to which the blade is still the full 7.2,
                             # i.e. half of the MEASURED 22.5 mm wide section
HORN_LEVER_R = 18.0      # MEASURED 36.0 mm tip to tip on a 2-arm horn, halved
HORN_BLADE_T = 1.6       # blade thickness in z, top face flush with the hub's top.
                         # STILL THE ONE UNMEASURED NUMBER.  1.6 is what
                         # nose_assembly.py's reference horn has always drawn, so it
                         # is an inherited assumption, not a measurement.
                         # It decides the only load-governed stress in the arm --
                         # horn_drive_stress() -- AND IT RUNS THE OPPOSITE WAY TO
                         # INTUITION: a THICKER blade is WORSE.  The sideways force
                         # per mm of flank is T/L^2 and does not depend on the
                         # thickness at all, so a thicker blade does not reduce the
                         # load, it only moves the load's centroid further below the
                         # flank's root and lengthens the lever.  At a stalled
                         # 216 N.mm the resultant factor of safety against the 11.0
                         # MPa interlaminar strength is 4.07 at 1.0 mm, 2.70 at 1.6,
                         # 2.20 at 2.0, and crosses 2.0 at 2.30 and 1.5 at 3.00.
                         # So: measure it, and if yours is over 2.3 mm say so before
                         # printing.  Under 1.6 needs no action.

HORN_POCKET_D = 7.73     # hub recess = the MEASURED 7.43 hub + the 0.3 minimum the
                         # assert at :2207 demands, and no more.  Was 8.2, chosen
                         # when LATCH_ARM_W was 8.0 and the recess therefore broke
                         # clean out of the bar over |x| <= 0.900 -- at which width
                         # tightening it to 7.9 left 0.05 mm slivers that either do
                         # not print or, counted as structure, dropped S at x = 0
                         # from 5.862 to 2.622 mm3.  At W 10.50 the recess no longer
                         # breaks out, so every 0.1 mm taken off it is 0.05 mm added
                         # to each flank: 7.73 leaves 1.3850 mm, which is the
                         # governing wall in the whole pocket and still clears
                         # WALL_MIN 1.26.  8.2 would leave 1.1500 and FAIL.
HORN_POCKET_DEPTH = HORN_HUB_H   # 5.00, MEASURED.  At LATCH_ARM_T 8.4 and
                         # ARM_CB_DEPTH 1.6 the floor is 3.40 mm, of which 1.80 mm
                         # sits under the screw head against the > 1.0 assert in
                         # latch_arm.py -- the old 5.70 left only 1.10 there, so the
                         # measured hub being shorter than nominal is pure profit.
                         # The CEILING is still 6.40 and reachable only by deleting
                         # the counterbore (which costs HORN_ACCESS_D 5.0 -> 6.0, a
                         # bulkhead reprint and an M2.5 x 10).
HORN_SLOT_W = 7.6        # the lever's slot; carries all the torque.  7.6 for the
                         # MEASURED 7.2 mm blade: 0.20 mm per flank, which is a
                         # hand-press fit, not a running fit, and that is what is
                         # wanted -- the flanks are the drive.  7.5 is the bare
                         # assert minimum and does not survive the slicer: a slot
                         # this deep prints with its walls pulled in by roughly half
                         # an extrusion, so a nominal 7.5 measures ~7.4 and the
                         # blade does not enter.  Was 5.0, sized on a blade width
                         # that had been back-derived from this very slot, which is
                         # the circularity the MEASURED envelope broke.  HELD
                         # CONSTANT out to HORN_SLOT_R -- see the note there; a slot
                         # that narrows where the blade is still 7.2 wide is the
                         # failure being fixed.
HORN_SLOT_R = 18.4       # half-length: 36.8 for a MEASURED 36.0 mm tip-to-tip
                         # 2-arm horn, 0.40 mm per end.  15.0 was 3.00 mm SHORT
                         # PER END -- it was set by "so a 2-arm horn fits as well"
                         # with no horn to hand, and it is why the arm would not
                         # seat.  The slot keeps HORN_SLOT_W all the way out to here
                         # rather than tapering with the blade: the taper would save
                         # nothing (the section that matters is at x = 0, where the
                         # hub recess already governs) and stopping the full width at
                         # |x| = 11.45 drops the flank-root factor of safety to 0.39
                         # at stall, because the blade is still 7.2 wide there and
                         # would bear on the step instead of the flank.
                         # The CEILING moved when the slot widened: the pocket's
                         # corner sits at hypot(R, W/2) and must stay 1.5 mm inside
                         # the hooks' bearing footprint at r = hypot(TONGUE_X0,
                         # TONGUE_Y0) = 20.50055.  The corner would TOUCH that
                         # footprint at R 20.348 with a 5.0 slot and at 20.145 with a
                         # 7.6 one, but the 1.5 mm of land pulls the real ceiling in
                         # much harder: 18.836 before, 18.617 now.  18.4 clears it by
                         # 0.217 mm of R, which is 0.212 mm of radial land where it
                         # used to be 0.432 -- the slot is 2.6 mm wider and the land
                         # paid for half of it.  This is the binding constraint on
                         # HORN_SLOT_R and the reason it did not simply go to 18.8.
ARM_SHAFT_CLEAR = 2.70           # M2.5 clearance for the servo's centre screw
ARM_CB_D = 5.0                   # counterbore, so its head cannot foul the
ARM_CB_DEPTH = 1.6               # bulkhead 0.5 mm above the arm's top face
# The centre screw has to cross the counterbore, the pocket floor and whatever the
# spline stands proud of the case before it finds thread, and there is 6.90 mm of
# air in the way: the head bears at Z_ARM_TOP - ARM_CB_DEPTH = 45.40 and the case
# top is Z_SERVO_TOP = 38.50.  The stock 6 mm screw reaches only 2.1 mm of thread
# and MUST NOT BE USED.  x8 gives 4.1 mm at a 3.0 mm stand-off.
CENTRE_SCREW_L = 8.0             # M2.5 x 8, under the head
SPLINE_STANDOFF = 3.0            # how far the output spline stands off the case
LATCH_SWEEP = 31.0      # deg from latched to clear.  Only 2.5 mm of overlap has
                        # to be broken; 31 deg moves the tip 11.2 mm.  Keeping the
                        # sweep small is what lets the servo cradle fins reach the
                        # bulkhead everywhere except one small notch.
                        # WAS 30.0, and the +1.0 is bought by LATCH_ARM_W: the arm
                        # clears the foot's azimuth band only once its TRAILING edge
                        # has swung past it, and that edge lags the centreline by
                        # asin((W/2)/r_in), which grew with the bar.  th_free went
                        # 20.00 -> 23.60 deg, and the :2437 check reserves the last
                        # 20% of the sweep for trim error: 0.8 * 30 = 24.0 left only
                        # 0.40 deg of headroom where the 8.0 bar had 4.00, and 0.40
                        # deg is inside the trim error it is meant to cover.  31 deg
                        # puts it back to 1.20.  Note the ABSOLUTE daylight is a
                        # comfortable 7.40 deg either way -- it is the reserve, not
                        # the geometry, that ran out.
                        # This is the ONLY cost of the wider bar that is not local to
                        # the arm, because fin_notch_half() reads both W and the
                        # sweep: the notch goes 10.5150 -> 12.2326, of which the bar
                        # accounts for 1.4433 and this extra degree for 0.2743.  That
                        # notch is the bulkhead reprint.
# ARM_CORNER_R is declared UP with LATCH_ARM_W, not here, because LATCH_ARM_R is now
# derived from it and not the other way round.  It used to read
#     ARM_CORNER_R = math.hypot(LATCH_ARM_R, LATCH_ARM_W / 2)   # 23.3452
# whose comment was stale by 1.0 mm (the value was 22.3607) and which made every hook
# dimension a function of the bar's width -- so widening the bar for the horn silently
# moved the web, the foot overlap and the break load.  See the note at LATCH_ARM_W.

# --- the hook, all of it derived from the arm it has to reach around ----------
# The arm sweeps a disc of radius ARM_CORNER_R about the shaft, so the web has to
# stand OUTBOARD of that disc for the whole 8.4 mm of the arm's thickness and then
# turn back inboard underneath it.  WEB_CLEAR is a running fit on a face the arm
# passes 30 deg across on every cycle, so it is sized like FIN_ARM_CLEAR (0.7) and
# not like a static gap; note the radius that matters is at the SMALLEST |y|,
# hypot(WEB_X_IN, TONGUE_Y0), because that is where the web comes closest to the
# axis.  Measuring at TONGUE_Y1 instead flatters the gap by 0.21 mm.
WEB_CLEAR = 0.705
WEB_X_IN = round(math.sqrt(max((ARM_CORNER_R + WEB_CLEAR) ** 2
                               - TONGUE_Y0 ** 2, 0.0)), 2)      # 23.07, and it said
                         # 24.05 until this was noticed: 24.05 is 23.3452 + 0.705, the
                         # value back when LATCH_ARM_R was 23.0, and pulling it in to
                         # 22.0 with the hook took ARM_CORNER_R to 22.3607 without
                         # touching this comment.  Same failure as the "# 23.3452" that
                         # sat on the old ARM_CORNER_R line -- see the note at
                         # LATCH_ARM_W.  23.07 is the number the freeze holds, and
                         # nose_verify.py's volume ledger depends on it holding.
HOOK_X_IN = TONGUE_X0    # the foot reaches as far inboard as the blade above it,
                         # so the tongue's inboard face is one straight line.  Its
                         # OUTBOARD limit is set by ARM_CORNER_R and not by
                         # LATCH_ARM_R: latch_arm._blank() cuts a bar deliberately
                         # 2*ARM_CORNER_R + 2 long with the arc, so the arc governs
                         # everywhere and sqrt(ARM_CORNER_R^2 - y^2) is the real
                         # reach.  That gives a 7.90 mm2 footprint (8.31 by exact
                         # arc integral) -- but see the latch-bearing line in
                         # self_check(): the foot's top is RAMPED, so what actually
                         # bears on a fresh print is the 2.82 mm2 flat land.
HOOK_T = 2.5             # foot thickness; 2.1 at the thin end of the ramp
Z_LATCH_FACE = Z_ARM_BOT                 # 38.6 -- FACING UP.  See the note above.
LATCH_FACE_UP = True     # the sign, declared as data so a check can test it.  The
                         # previous design had this False in effect and nothing in
                         # 236 assertions noticed, because nothing asked.
Z_HOOK_BOT = Z_LATCH_FACE - HOOK_T       # 36.1, the tongue's lowest point
Z_TONGUE_BOT = Z_HOOK_BOT                # kept as an alias: it is still "the
                                         # bottom of the tongue", it is just no
                                         # longer the load face
Z_STEP = Z_ARM_TOP + 0.6                 # 47.6, the pocket's ceiling.  0.6 rather
                         # than 0.3 because this is ONE IN-PLANE shell dimension
                         # (Z_STEP - Z_ARM_BOT = 9.0 mm, printed in x/z) minus ONE
                         # LAYER-STACKED arm dimension (LATCH_ARM_T = 42 layers),
                         # and a slicer that scales XY for ABS_SHRINK but not Z
                         # eats 0.05 mm of it before anything is measured.
                         # AND THAT IS ALL IT IS -- a printing allowance.  Closing
                         # this gap so each half "reacts its own hook load" buys
                         # exactly nothing: the ceiling faces DOWN onto the arm's
                         # top, so it can only resist OVER-closing, and over-closing
                         # is already arrested at 0.0445 deg = 0.0277 mm of foot
                         # travel by the butting seam faces, 21.7x short of the
                         # 0.6 mm.  Nor can any down-bearing stop ever arrest
                         # OPENING: dz'/dtheta = Y_PIN - |y| > 0 at every point of a
                         # half (+0.6215 mm/deg at y = 0.15, +0.6983 at y = -4.25),
                         # so opening LIFTS everything and only an up-facing catch
                         # can restrain it -- which is what the latch already is.
STEP_CHAM = 0.5          # 45 deg chamfer filling the pocket's top-outboard
                         # re-entrant corner at (WEB_X_IN, Z_STEP).  It lives in
                         # z 47.1..47.6, above Z_ARM_TOP = 47.0 and inside the
                         # bulkhead's existing 20.0..25.75 tongue slot, so it is
                         # free -- but CLAIM NO STRENGTH CREDIT FOR IT.  The web
                         # carries a constant moment M = Fz*e over its whole 9.0 mm,
                         # so the identical corner at (WEB_X_IN, Z_LATCH_FACE) is
                         # equally stressed and CANNOT be filleted: a 0.6 mm fillet
                         # there needs WEB_CLEAR 1.1, which drops the web to 2.04 mm
                         # and NETS 16.26 N against 18.294 N unfilleted.  This is
                         # insurance against one crack starter, not a fix.
#
# THE FOOT'S TOP FACE IS A RAMP, NOT A FLAT, AND THAT IS NOT A DETAIL.
# Flat and coplanar with the arm's underside, the arm would have to sweep into a
# zero-clearance slot -- and there is nowhere for the halves to give: the two seam
# faces butt after 0.0445 deg of over-closing, which is 0.026 mm of foot travel.
# Any flat clearance instead becomes slop, amplified 5.69x per half into a gap at
# the nose tip: 0.15 mm at the foot is 1.7 mm of open seam at the tip.
# So the foot's top is a flat LAND at Z_LATCH_FACE over the first RAMP_LAND of y --
# the part of the foot the arm covers LAST as it sweeps in -- falling away by
# RAMP_DROP across the rest.  The arm then enters over the low side and cams the
# halves shut as it advances, ending with zero slop and no shimming, and it
# tolerates +-RAMP_DROP of error in the servo/horn z stack (which the code already
# flags as measure-yours) instead of jamming on it.
# tan(ramp) = 0.20 against LATCH_MU = 0.35, a 1.75x margin, so it cannot
# back-drive: the springs cannot push the arm out, and power can be cut once
# latched.  self_check() asserts that ratio stays above 1.5.
RAMP_LAND = 1.0          # y TONGUE_Y0 .. TONGUE_Y0+RAMP_LAND is the bearing land
RAMP_DROP = 0.40         # over the remaining 2.0 mm of y
LATCH_MU = 0.35          # ABS on ABS, dry, as-printed.  Deliberately the LOW end of
                         # the 0.35..0.5 usually quoted: a low mu is pessimistic for
                         # back-driving (the thing that must not happen) and
                         # optimistic for servo torque, so the two checks that use
                         # it below want opposite ends and 0.35 is the one that
                         # makes the back-drive check honest.  release_torque() and
                         # engage_torque() take mu as an argument if you want the
                         # other end.

# The arm's upward load is taken by an annular THRUST PAD on the bulkhead, not by
# the servo's output shaft.  The servo therefore only has to beat friction.
THRUST_PAD_R0 = 6.5
THRUST_PAD_R1 = 9.5
THRUST_PAD_DROP = 0.5    # protrudes below the bulkhead so the pad, not the disc,
                         # is the bearing face and the friction radius is small

# ==================================================================== servo
# MG90S, metal gear: 2.2 kg.cm = 216 N.mm stall at 4.8 V, 13.4 g.
SERVO_L = 22.8           # along Y here
SERVO_W = 12.2           # along X here
SERVO_H = 22.5
SERVO_SHAFT_FROM_END = 6.2       # shaft is off-centre along the length
SERVO_FLANGE_FROM_BOT = 16.0     # underside of the mounting flange
SERVO_FLANGE_HOLE_PITCH = 28.0
SERVO_POCKET_CLEAR = 0.8         # per face
SERVO_STALL_NMM = 216.0
Z_SERVO_TOP = Z_ARM_BOT - 0.1    # 38.5.  That 0.1 mm is the arm-to-case gap, and
                                 # it is now on the RIGHT side of the load: the
                                 # foot pushes the arm UP, away from the case,
                                 # instead of down into it.
Z_SERVO_BOT = Z_SERVO_TOP - SERVO_H              # 16.0
Z_FLANGE_FACE = Z_SERVO_BOT + SERVO_FLANGE_FROM_BOT   # 32.0, top of the pads
# The servo lies with its LENGTH along Y and its shaft on the rocket axis, so the
# 28 mm flange span points at the hinges -- the one azimuth the latch arm never
# sweeps to.  With the shaft at the origin the body runs y -6.2..+16.6, so its
# CENTRELINE -- which is what the flange holes are symmetric about, not the shaft --
# sits at y = +5.2, and the holes land at -8.8 and +19.2.
#
# The sign here is worth spelling out because it was wrong once and it is invisible
# in a top view: the body is longer on the +y side of the shaft, so the flange
# centre is at +(L/2 - shaft_from_end), NOT at (shaft_from_end - L/2).  Getting it
# backwards mirrors both holes about the shaft, moves them 10.4 mm, and the servo
# simply will not bolt to the cradle -- while every drawing still looks plausible.
SERVO_BODY_Y = (-SERVO_SHAFT_FROM_END, SERVO_L - SERVO_SHAFT_FROM_END)   # -6.2..16.6
SERVO_FLANGE_MID_Y = SERVO_L / 2 - SERVO_SHAFT_FROM_END                  # +5.2
SERVO_HOLE_Y = (SERVO_FLANGE_MID_Y - SERVO_FLANGE_HOLE_PITCH / 2,
                SERVO_FLANGE_MID_Y + SERVO_FLANGE_HOLE_PITCH / 2)        # -8.8, +19.2
M2_PILOT = 1.70
# Cradle: fins hanging off the bulkhead, servo clamped between them by its own
# flange screws.  Fins, not a box: a box would need a floor.
FIN_X_IN = SERVO_W / 2 + SERVO_POCKET_CLEAR      # 6.9
FIN_T = 2.1
FIN_Y0 = -15.0           # far enough aft to give the notch's aft tab a real root
FIN_Y1 = 22.5            # far enough forward to carry the +19.2 pad's outboard end
FIN_Z_BOT = Z_SERVO_BOT
FIN_ARM_CLEAR = 0.7      # around the arm's swept span, per side
# THE NOTCH, AND WHY IT IS SYMMETRIC ABOUT y = 0.
# At a plane x = x_p the arm's material spans
#     y in [ x_p*tan(t) - w/cos(t), x_p*tan(t) + w/cos(t) ]
# for half-width w, and both bounds are monotonic in t, so the union over the
# sweep is just the two endpoints -- no search needed.  But the arm is a BAR
# THROUGH THE ORIGIN, not a single-sided lever: it crosses the -x fin at the same
# time as the +x one, and there its band is the point reflection of the +x band.
# The fins are identical, so each must clear the UNION, which is symmetric:
#     |y| <= (FIN_X_IN + FIN_T)*tan(T) + w/cos(T)   = 9.815
# Evaluated at the fin's OUTER plane, where the band is widest.  Taking the +x
# band alone gives -4.00..+9.81, which looks like a 15 mm notch and is really a
# 21 mm one -- the arm then drives straight through the aft fin at 28 deg.
FIN_NOTCH_Z0 = Z_ARM_BOT - FIN_ARM_CLEAR         # 37.9, just under the arm
# ...AND WHY IT CLOSES AT 45 DEG INSTEAD OF HAVING A FLAT FLOOR.
# The notch only has to exist over the arm's own z band, 38.6..47.0.  A flat
# floor at FIN_NOTCH_Z0 would be a 21 mm island of new material appearing in
# mid-print -- in this part's pose (disc on the bed, building toward -z) the fin
# starts at the disc as two separate tabs, so that floor is a 21 mm bridge
# between them.  Closing the notch as a 45 deg V instead grows the material in
# from the two tabs, needs no bridge and no support, and -- the reason it matters
# structurally -- it puts fin back under the aft flange pad, which straddles
# y = -8.8, right in the middle of the notch.
PAD_T = 5.0              # enough thread for a self-tapper; 2.5 was not
PAD_Y_HALF = 3.0         # pad reaches this far either side of each hole, then gets
                         # clipped where it would foul the servo body
PAD_BODY_CLEAR = 0.4
# THE PADS HANG BELOW THE FLANGE FACE, they do not stand on top of it.  The servo
# goes in from underneath and its flange lands on Z_FLANGE_FACE, so the launch
# load runs into the pads in COMPRESSION and the two M2 screws only locate it.
# That is also why the pads cannot be a full-width slab: at 3.0 mm either side of
# the -8.8 hole a pad would reach y = -5.8 and collide with the body's own end at
# -6.2, so each pad is clipped to the body edge less PAD_BODY_CLEAR.
SERVO_ACCESS_D = 4.2     # bulkhead holes over the two flange screws -- Ø4.2 passes
                         # an M2 head, so the screw can be dropped in and driven
                         # with the cradle already built.  Without them the servo
                         # cannot be fitted at all: the bulkhead is solid directly
                         # above both screws and the screw axis is +z.
HORN_ACCESS_D = 5.0      # ditto for the horn's factory screw, on the axis

# ===================================================================== bulkhead
# A separate flat-printed plate. It is the mechanism module: it carries the servo
# cradle, the arm's thrust pad, the tongue slots and the cord pass-through, and it
# closes the chute cavity so the canopy can never reach anything that moves.
# Separate rather than integral to the ring because a full disc across the bore of
# an UPRIGHT-printed tube is a 57 mm bridge; printed flat it is trivial, and its
# layers then run in the plane that carries the latch load.
Z_BULK_BOT = 47.5
BULK_T = 2.5
Z_BULK_TOP = Z_BULK_BOT + BULK_T                 # 50.0
R_BULK = 28.4
D_CORD_HOLE = 8.0
Y_CORD_HOLE = -18.0      # OFF-AXIS, at azimuth 270 deg.  On-axis is blocked -- the
                         # servo, its horn and the latch arm all live there -- but
                         # the sign matters as much as the offset, and getting it
                         # wrong is not obvious from a top view.
                         #
                         # The servo is NOT symmetric about its shaft: the shaft
                         # sits 6.2 mm from one end, so the body runs y -6.2..+16.6
                         # and the flange tabs reach y -8.8 and +19.2.  At azimuth
                         # 90 a cord dropping from y = +18 lands straight on the
                         # far flange tab and its mounting screw at z 36..38.5 --
                         # it would saw across a screw head under deployment load.
                         # At azimuth 270 the last obstruction is the near flange
                         # at y -8.8 and the cradle fins at y -12.5, so a 8 mm
                         # hole centred at y = -18 (spanning -22..-14) has a
                         # clear straight drop from the bulkhead to z = 0.
                         # Checked against every part below, not just eyeballed.
SLOT_CLEAR_X_IN = 0.5    # inboard; wide open, nothing is near it
SLOT_CLEAR_X_OUT = 0.25  # outboard, and it is 0.25 rather than 0.5 to keep the
                         # deepened slot's corner off the ring's seat bore -- see
                         # SEAT_R_IN.  x never changes as the half swings (the pin
                         # is parallel to x), so 0.25 mm is a pure print tolerance
                         # here, not a motion clearance.
# HOW DEEP THE SLOT HAS TO BE IS SET BY THE HOOK, AND IT IS 3x WHAT A FLAT BLADE
# NEEDED.  The tongue does not go straight up through this slot: it swings on the
# hinge, so it also drifts toward -y on its way out, and how far depends on how far
# BELOW the pin its lowest point hangs.  The old flat blade started at z = 47.0,
# 8.0 mm under the pin, and drifted 0.41 mm.  The hook's foot starts at
# Z_HOOK_BOT = 36.1, 18.9 mm under it, and drifts to y = -4.2483 mm -- and it is
# still inside this disc's z band when it gets there (theta = 20.83 deg, z' =
# 49.999, clear at 22.47 deg).  At the old -1.5 the halves jam solid at ~9 deg of
# opening and the chute never comes out; that was measured as 22.7 mm3 of boolean
# overlap against the exported bulkhead.  self_check() now scans the whole tongue
# profile over the whole sweep instead of testing one corner at one angle, which is
# how this got missed.
SLOT_Y0 = -4.75          # = -4.2483 worst drift, less the same 0.5 mm the slot
                         # uses in x.  Verified by a 0.005 deg sweep of every
                         # polygon edge on both y faces.
SLOT_Y1 = TONGUE_Y1 + 0.5

# --- the seat the bulkhead lands on, cut into the ring's bore
SEAT_R_IN = 26.9         # NOT 25.0, and that 1.9 mm deletes a whole feature.  At
                         # 25.0 the seat's inner edge overlapped the latch tongues
                         # (whose outer corner reaches radius 25.69) and the seat
                         # needed two notches cut in it at azimuth 0/180 for them
                         # to pass.  At 26.9 the tongues clear it by 1.21 mm and
                         # the notches are unnecessary -- and the tongue can never
                         # drift into it in x either, because the hinge axis is
                         # parallel to x, so opening changes y and z but NEVER x.
                         # Still leaves 1.82 mm of land under the bulkhead's rim.
                         #
                         # 26.5 -> 26.9 came with the hook.  Two things ate the old
                         # margin: the deepened blade slot's outboard/-y corner now
                         # reaches r = 26.18, and the FOOT swings out to r = 25.79
                         # at 17.3 deg of opening because it hangs so far below the
                         # pin (a point 40.3 mm from the pin crosses the seat's z
                         # band while it is still well off the split plane -- the
                         # old blade, 36.5 mm out, crossed it at y = +0.04).  Both
                         # were inside 0.1 mm of the seat at 26.5.  Cost of moving
                         # it: the bulkhead's bearing annulus goes 1.9 -> 1.5 mm,
                         # against a latch load of 0.64 N total (this said 3.5 --
                         # see spring_check(); the trade was easy either way).
SEAT_Z0 = 44.5
SEAT_Z1 = Z_BULK_BOT     # 47.5
# --- and the two lobes the retaining screws thread into
LOBE_THETA = (135.0, 315.0)
LOBE_R_IN = 22.0
LOBE_Z0 = 40.0
LOBE_HALF_CHORD = 6.0
M2_5_PILOT = 2.10
M2_5_CLEAR = 2.70
R_BULK_SCREW = 25.5
BULK_SCREW_DEPTH = 6.0
BULK_SCREW_LEN = 8.0             # M2.5 x 8, and this is NOT the same choice as
                         # RETAIN_SCREW_LEN happening to agree.  The head lands on
                         # the bulkhead's TOP face, so the budget is BULK_T 2.5 of
                         # disc plus BULK_SCREW_DEPTH 6.0 of pilot = 8.5 mm.  A x 10
                         # bottoms 1.5 mm early, and a screw that bottoms before the
                         # bulkhead is down on SEAT_Z1 holds the seat OPEN -- on the
                         # one joint the whole latch load crosses.  The README said
                         # x 10 twice; nothing here contradicted it, because the
                         # length was not a constant at all.  See the assert in
                         # self_check() -- there has never been a load_path_report(),
                         # which is what this comment and the README both claimed.
# WHY SCREWS AT ALL, AND WHY ONLY TWO.  The latch pushes the bulkhead UP, so a
# seat under it resists the one load that never occurs; it has to be held from
# ABOVE.  Two M2.5 screws through the rim into the lobes, diametrically opposite,
# fully restrain uplift -- and the load is 0.64 N total, roughly the weight of a
# 65 g mass, against a 6 mm thread engagement in ABS.  (3.5 N / 350 g was the
# figure before spring_check() found what actually fits the hinge pocket; the
# conclusion only got more lopsided.)  Enormously overbuilt, and
# still simpler than the bayonet alternative, which needs four seat notches and
# can rotate itself loose under vibration.
# 135/315 deg is not arbitrary: it is the only band clear of BOTH the latch arm's
# sweep (which covers -11..41 and 169..221 deg) and the servo's flange pads
# (which reach out to 113 deg).

# ================================================================ base ring
Z_RING_BOT = 0.0
Z_SHOULDER = SPIGOT_LEN                  # 26.2069, seats on Mbody's forward rim
RING_BORE = 28.7207                      # spigot wall 2.400 (vs 1.33 original)
# Reproduce: an OPEN bore.  The original cone has a SOLID 10.48 mm plug at
# z 0..10.48 with one 4.58 mm axial hole -- a bulkhead plus tether anchor for the
# conventional scheme where the nose separates under ejection pressure.  A
# clamshell nose never separates, so the piston face is pointless and the plug
# would seal the chute cavity off from the body tube.  Also do NOT reproduce the
# 0.3276 x 24.9 mm annular void the original carries between z 27.5 and 52.4 --
# that is the socket clearance left wrapped around the spigot in CAD, unprintable
# with a 0.4 mm nozzle, and a genuine artifact rather than a feature.

# ========================================================= airframe retention
# NOTHING ELSE HOLDS THE NOSE IN THE TUBE.  The shoulder takes drag in
# compression and the spigot takes side load in shear, but the joint is a plain
# slip fit with 0.1638 mm of radial clearance: pull and the nose comes out, twist
# and it turns.  On a conventional nose that IS the design -- it is supposed to
# separate under ejection pressure.  A clamshell nose never separates, so it has
# to be FASTENED, and fastening it also kills the free rotation, which is what
# stops the servo wire being wound up over the flight.
#
# TWO RADIAL SCREWS THROUGH THE AIRFRAME INTO THE SPIGOT, AT THE SEAM AZIMUTH.
# Two, diametrically opposite, is enough: a pin in a hole at 0 deg and another at
# 180 deg fix translation and rotation both.  Screws rather than shear pins
# because a shear pin is sized to BREAK, and here nothing is supposed to.
#
# WHY AZIMUTH 0/180 AND NOT 90/270.  Below the shoulder the ring's bore is the
# servo bay, and everything in it lives near the axis or at +-Y:
#     servo body        |x| <= 6.1,  y -6.2..16.6,  z 16.0..38.5
#     cradle fins       |x| 6.9..9.0,  z 16.0..47.5
#     shock cord        |x| <= 4.0,  y -22..-14  (azimuth 270)
#     hinge lugs        +-Y, and all of them above z 38
# A boss at +-X reaching in to r 23.2 has its closest point at |x| 22.54, so it
# misses the fins by 13.5 mm and the cord by a whole quadrant.  At +-Y the same
# boss would sit 0.5 mm off the shock cord's hole -- the one thing in the bay that
# moves under load.  0/180 is also the azimuth the user can find without
# measuring: it is the split seam, the most visible line on the closed nose.
RETAIN_THETA = (0.0, 180.0)
Z_RETAIN = 13.0          # mid-spigot: 13.0 mm of pad below the hole, and the
                         # hole's top edge stays 1.95 mm below the bay floor at 16
Z_RETAIN_BELOW_RIM = SPIGOT_LEN - Z_RETAIN       # 13.2069 -- see the note below
# The pad is an internal thickening, because 2.40 mm of spigot wall is not a
# thread.  It is a revolve intersected with a chord box, exactly like the screw
# lobes: that way its inboard face is a true cylinder and its top a true 45 deg
# cone at EVERY azimuth across the pad, not just on the centreline.
RETAIN_PAD_R_IN = 23.20  # 5.52 mm of thickening inboard of the bore
RETAIN_HALF_CHORD = 5.5  # 11 mm along the tube's circumference
RETAIN_PAD_Z_TOP = 21.0  # full thickness to 15.48, then a 45 deg cone back out to
                         # the bore -- no downward-facing face, no ledge for the
                         # shock cord to catch on, and the pad starts at z = 0 so
                         # in the ring's upright print pose it grows off the bed
RETAIN_PILOT = M2_5_PILOT        # 2.10, for an M2.5 self-tapper
RETAIN_PILOT_R0 = 24.20          # BLIND.  1.00 mm of floor left inboard of it, so
                                 # no screw tip can ever appear in the servo bay
RETAIN_MOUTH_CS = 1.0            # 45 deg countersink at the spigot OD, Ø2.1 -> Ø4.1.
                                 # This is the tolerance budget for a hole drilled
                                 # by hand in the airframe: +-1.0 mm of misplacement
                                 # and the screw still finds the pilot.
RETAIN_SCREW_LEN = 8.0           # M2.5 x 8.  NOT 10 -- see the assert below
RETAIN_TUBE_CLEAR = 3.20         # in the AIRFRAME, and deliberately loose for M2.5:
                                 # the nose's pilot locates the screw, the tube hole
                                 # only has to let it through.  One part locates, the
                                 # other clears; both locating means neither does.
RETAIN_X_MIN = math.sqrt(RETAIN_PAD_R_IN ** 2 - RETAIN_HALF_CHORD ** 2)   # 22.54
# NOT RETAIN_PAD_R_IN.  That is a radius; the chord box cuts the pad back, so the
# closest the pad comes to the axis along x is sqrt(r^2 - half_chord^2).  Using
# the radius here reads 0.66 mm pessimistic, which sounds harmless until the same
# mistake is made in the direction that flatters.

# ====================================================================== vents
# Sea-level air carried to apogee tries to burst the nose open from inside.  The
# seam and the cord hole leak, but leaks are not a vent budget.
VENT_D = 4.0
Z_VENT = 60.0
VENT_THETA = (45.0, 135.0)               # per half; 45 deg off both seam and hinge

# ================================================================ seam dowels
# Anti-shear and anti-flutter only; the halves are located by their hinges and
# the latch.  Blind sockets on both seam faces at mirrored x, loose dowels glued
# into one half.
#
# THE DOWEL HAS TO GET OUT, AND THE FIRST VERSION OF IT COULD NOT.
# A seam dowel is a peg spanning a joint that HINGES OPEN, so it is not a static
# fit -- it has to withdraw along its own axis while the two halves rotate away
# from each other.  Relative to half B, half A turns by 2*theta about a virtual
# hinge lying on the split plane near Z_PIN (dowel_relative() below), so a dowel
# at z = 120 pulls out of B at 1.7 mm per degree of opening while its axis skews
# sideways at 0.06 mm per degree.  Whether it binds is a race between those two,
# and the ONLY thing that decides it is how far the rod sticks into B: sideways
# skew grows with engagement squared, withdrawal only linearly.
#
# The first version lost that race.  Ø3.2 sockets 6.0 deep with the 10 mm rod
# nose_assembly drew, centred, put 4.85 mm of rod into B and needed 0.186 mm of
# radial room where 0.100 was available: at z = 120 the rod's surface stands
# 0.086 mm INSIDE B's bore wall, from 0.69 deg of opening through to 2.08 deg,
# worst at 2.06 -- with the springs pulling and the servo already out of the way.
# A nose that cracks open 2 deg and stops is worse than one that never opens.
# (Those four numbers were re-derived from dowel_relative() on 2026-09-14 and
# they are not what this comment used to claim.  It said 0.297 mm and 2.8 deg,
# and the README said 0.03 mm and 1.85 deg; neither reproduces.  The z = 180
# station is the other half of the correction: it did NOT jam, it cleared by
# 0.0016 mm, which is not clearance, it is a coin toss.)
#
# A MOUTH CHAMFER CANNOT FIX IT, and the reason is the opposite of what this
# comment used to give.  The interference is not worst at the mouth and roughly
# flat with depth -- it grows monotonically INWARD, and the mouth is the one place
# that was never touching:
#
#     depth into B   0.5     1.5     2.5     3.5     4.5    4.85 (the tip)
#     overrun      -0.097  -0.080  -0.048  -0.001  +0.061  +0.086
#
# so a chamfer relieves only the clear end.  Moving the stations does not fix it
# either: the crossover for that rod is z = 178, and past it the margin is
# -0.002 mm at z = 180 and only -0.015 at z = 200, so both dowels would have to
# live in the top third of the cone on a hairline.
#
# So: SHORT ENGAGEMENT, and the rod glued BOTTOMED in one half.
DOWEL_D = 3.0
DOWEL_BORE = 3.3         # 0.15 mm/side of slack, same fit as PIN_BORE_KNUCKLE
DOWEL_DEPTH = 4.5
DOWEL_LEN = 6.5          # cut length of the rod.  Bottomed in half A's socket it
                         # leaves 6.5 - 4.5 = 2.0 mm proud of A's seam face and
                         # engages B by 1.70 mm, and B's socket is 4.5 deep, so
                         # the tip stays 2.80 mm off the floor at every angle --
                         # the dowel can therefore never bottom in B and never
                         # sets the closed position.  The seam faces do that.
                         # 6.5 RATHER THAN 8.0 SO THE PIN CAN BE PRINTED.  The
                         # binding constraint on withdrawal is z-girth skew growing
                         # as the engagement SQUARED, so shortening the rod raises
                         # the largest ACTUAL pin diameter that still withdraws from
                         # Ø3.1328 to Ø3.2492 -- +0.2492 mm of allowable oversize
                         # against the +0.05..+0.20 an FDM part runs on an external
                         # diameter, which is what makes seam_pin.py legal.  Bought
                         # Ø3.0 rod is still preferred (straight, cheap, nominal).
                         # It also takes the swept margins 1.79x -> 5.90x at z 120
                         # and 3.40x -> 11.19x at z 180, for 0.002 mm of root
                         # registration.
DOWEL_Z = (120.0, 180.0)                 # 120 rather than 110: same cost, and the
                                         # worst withdrawal margin goes 1.53 -> 1.79x
DOWEL_PAD_T = 6.0        # local wall thickening, radial
DOWEL_PAD_LEN = 11.0                     # 2.8 mm of rib past each end of the bore     # along z
DOWEL_INSET = 3.0        # socket axis this far inboard of the outer surface

# ==================================================== the pin that IS moulded in
# THE TWO SHELLS CANNOT GROW A PIN AT EACH OTHER.  Half B is half A turned 180 deg
# about Z and both print on the split face, so y = SEAM_SETBACK IS THE BUILD PLATE
# (nose_verify asserts it: the built half's bbox min y is 0.1500 exactly).  A boss
# pointing from one half at the other needs material at y < 0.15, i.e. under the
# bed.  All four escapes were measured and all four fail: a local seam tilt needs
# only 2.05 deg to clear a 3.0 mm boss at z 120 but turns all 1042.0 mm2 of seam
# face into an 87.95 deg overhang over air, on the one face that must be flat and
# must carry load in-layer (40 vs 11 MPa); an inner-surface interlock still has to
# cross y = 0.15, because the halves' inner surfaces only meet at the seam strips;
# a lap/shiplap has no step wall, the closed seam being two disjoint annular
# strips; and an axial key would be a ~190 mm separately-printed spline.
#
# WHAT IS MOULDABLE IS A POST ON THE RING.  The base ring prints upright, spigot
# down, and needs no support anywhere, so an axial +z pillar on its collar top is
# free.  Two of them, one under each half at the seam meridian, entering a bore in
# each half's root -- and the socket's axis then lies along z, which is IN the bed
# plane for the shell, making it a strictly EASIER print than the existing dowel
# sockets (14 layers, 0.3386 mm largest single-layer step = 81% of a bead, and no
# downward-facing floor disc at all, against the Ø3.30 dowel socket's 0.3830 mm
# step = 91% PLUS 8.55 mm2 of bridged floor).
#
# Measured: withdrawal is clear at every angle over 0..110 deg (0 collisions in
# 42 angles x 938 points x 2 halves, worst signed distance -0.2680 mm), and the
# requirement has a closed form independent of post diameter, height and x:
# (Z_PIN - Z_SHELL_ROOT)^2 / (2*(Y_PIN - POST_Y)) = 0.10381 mm, peaking at 4.68
# deg.  Half B's numbers are byte-identical to half A's, which IS the proof the
# feature is self-mating.  It buys the ROOT joint (step 0.594 -> 0.369 mm, 1.61x)
# and the absolute tip position (2.597 -> 2.417 mm); it buys almost nothing at the
# tip SEAM step (0.404 -> 0.399), which the dowel bore clearance dominates.  Its
# real prize is the feel: the post is still engaged at 5.09 deg of opening while
# the z=120 dowel is clear by 0.77 deg, so it engages FIRST by 4.3 deg and guides
# each half onto the ring before either dowel has to find its socket.
POST_D = 2.0             # not thinner: Ø1.65-in-Ø2.35 gives the identical
                         # clearance and a 0.49 mm siting window instead of 0.1406,
                         # but the post drops to 1.62 N of side load bare / 4.10 N
                         # at the fillet root, against 2.88 / 6.33 N for Ø2.0.  A
                         # vertical pillar's layers are transverse to any side load,
                         # so this is the 11 MPa number, not the 40 -- the same
                         # argument spring_jig.py makes for its own mandrel.
POST_BORE = 2.70         # 0.35 mm/side, NOT the project's usual 0.15, AND THAT IS
                         # THE WHOLE REASON THIS IS SAFE.  D_PIN and DOWEL_D are
                         # BOUGHT rod at nominal, so 0.15/side only has to absorb
                         # the printed bore's error.  Here BOTH SIDES ARE PRINTED.
                         # Withdrawal needs 0.10381 mm; at 0.15/side that is 1.44x
                         # nominal but exactly 0.00x once the post comes out 0.10
                         # over and the bore 0.10 under -- and a jam at the root
                         # fights the torsion springs and the latch, i.e. the nose
                         # JAMS SHUT.  At 0.35/side the same stack still leaves
                         # 1.44x.  Ø2.20 (0.10/side) jams even nominally (margin
                         # 0.95x).  It costs 0.204 mm of root registration (0.369
                         # instead of 0.165) and nothing at all at the tip.  This
                         # design already shipped a jamming seam fit once and had to
                         # be redesigned; do not do it twice.
POST_H = 3.0             # engagement POST_H - ROOT_GAP = 2.80 mm, which must beat
                         # PIN_RISE 2.6 or the post leaves the bore before the
                         # closing skew is over
POST_BORE_DEPTH = 4.0    # leaves 1.20 mm of floor gap, so the post can never set
                         # the closed position -- the root face on the ring top does
POST_R_C = 29.79         # THE WHOLE FEASIBLE WINDOW IS 0.1406 mm WIDE: the shank
                         # must stand on the ring's top land (>= RING_BORE 28.7207
                         # + POST_D/2 = 29.7207) and the socket's outboard skin must
                         # hold WALL_MIN at the bore's FLOOR, not its mouth, because
                         # the ogive is already curving at the root (r_outer falls
                         # 0.0710 mm per mm of z), which caps it at 29.8613.  An
                         # earlier candidate at 30.15 measured 1.120 mm of skin at
                         # z 56.80 -- a real WALL_MIN violation, found on the mesh.
POST_Y = 3.20            # >= POST_BORE/2 + SEAM_SETBACK + WALL_MIN + chamfer.  It
                         # wants to be SMALL for another reason: the withdrawal
                         # requirement is PIN_RISE**2 / (2*(Y_PIN - POST_Y)), so
                         # moving the post toward the hinge makes the fit worse.  The
                         # ceiling is about 13; 3.20 is the floor set by the skin.
# NEGATIVE, and this is not cosmetic.  The seam has two meridians, and half A carries
# its latch tongue on the +x one.  With the new full-depth gusset that tongue's weld
# to the shell IS the plane x = r_in = 30.7536 over y 0.15..3.15, and a socket at
# +POST_X reaches x 30.9676 -- so it would cut 0.6795 mm out of the 3.0 mm weld
# EXACTLY AT ITS MOST-STRESSED FIBRE, costing 17 % of S and taking the servo-jam
# margin from 1.22x back to 1.02x.  That is the one number this whole change exists
# to buy, so the post moves instead.  Half A's -x root meridian is bare skin: the
# tongue is only at +x, the nearest dowel pad is 62.1 mm further up, the vents are at
# z 60 on the 45/135 deg meridians and the knuckle is out at y 35.76.
#
# Self-mating is unaffected, because it never depended on the sign: half B is half A
# turned 180 deg about z, so B's socket lands at (+|POST_X|, -POST_Y) and the ring
# simply carries its two posts at (POST_X, POST_Y) and (-POST_X, -POST_Y).  The
# withdrawal sweep is invariant too -- the hinge axis is parallel to X, so x never
# enters the rotation.
POST_X = -math.sqrt(POST_R_C ** 2 - POST_Y ** 2)     # -29.6176
POST_FILLET = 0.3        # a cone narrowing UPWARD, so it is an inward taper and the
                         # ring still needs no support.  Added BEFORE the bore cut,
                         # so the bore trims its 1.479 x 0.2307 mm inboard sliver --
                         # the technique base_ring.py already uses for the lugs.
                         # Free for withdrawal: the binding point is near the post's
                         # TOP at the bore MOUTH, 0.403 mm below the top.
POST_PAD_Y = 5.9         # >= POST_Y + POST_BORE/2 + WALL_MIN
POST_PAD_LEN = 6.0       # along z, from the root face up
POST_MOUTH_CHAMFER = 0.3         # <= 0.3554, the limit set by the outboard skin at
                                 # the root face where the chamfer is widest

# ============================================================== chute + cord
CHUTE_D_IN = 30.0
CHUTE_D_MM = CHUTE_D_IN * 25.4           # 762
D_SHOCK_CORD = 4.0                       # the CORD's own diameter.  Not to be confused
                                         # with D_CORD_HOLE = 8.0, the bulkhead through-
                                         # hole, which is 2x the cord on purpose so the
                                         # run needs no bend.  Both are declared here
                                         # and neither is referenced by any build
                                         # script -- they are documentation, and the
                                         # self_check line below is the only consumer.
ABS_DENSITY = 1.04                       # g/cm3, as carried by stability.py

# ANISOTROPY IS THE WHOLE STRENGTH STORY ON THIS PART, so the two numbers get named
# here instead of living as prose in half_shell.py's PRINT ORIENTATION paragraph.
# Printed on the split face, layer planes are y = const: sigma_zz and sigma_xx are
# carried by continuous beads, sigma_yy and tau_*y by the bond BETWEEN beads.  The
# ratio is 3.6x, which is bigger than any geometry change in this file, and it is
# why the hook survives the latch load in every direction and still snaps sideways.
SIGMA_ABS = 40.0                 # MPa, in-layer.  BOOK VALUES, not measured on the
SIGMA_ABS_LAYER = 11.0           # user's filament/printer/profile -- real FDM ABS
                                 # runs 30-45 in-layer and 8-25 across the bond
                                 # (250-255 C, enclosure, fan off on the tongue is
                                 # worth about 1.8x on the layer number alone).  So
                                 # every break load computed from these carries
                                 # +/-30%, and the interlaminar ones more.  They are
                                 # used for RATIOS between candidate geometries and
                                 # for order-of-magnitude margins, never as a
                                 # certificate.

# WHAT ACTUALLY FITS, AND WHY cavity_volume() IS THE WRONG QUESTION.  247.3 cm3 is the
# integral of pi r_inner^2 above the split, and it was quoted for a long time as though
# it settled whether a 30 in canopy fits.  It does not, three ways: it is blind to the
# tongues, dowel pads and dowel rods that stand into the void; it starts at the split
# rather than at the bulkhead's top face 2.41 mm lower; and a DEPLOYMENT BAG CANNOT
# TAPER, so what a bagged pack has to beat is the largest right cylinder the cone
# admits -- which is half the total volume.  All four numbers below are measured off
# out/nose_closed.stl by _scratch/_chute_envelope.py, 0.5 mm sections, 360 rays each.
CHUTE_VOID_CM3 = 253.3           # free void above the bulkhead face, every intrusion
                                 # taken out.  (cavity_volume() reads 247.3 from the
                                 # split with none of them; the 2.41 mm of extra floor
                                 # is worth +6.3 and the intrusions only -2.3, which is
                                 # why the blind number happened to land close.)
CHUTE_BAG_D = 40.12              # STRICT largest right cylinder, seated on the
CHUTE_BAG_H = 95.0               # bulkhead: Ø40.12 x 95.0 = 120.1 cm3.  Clears every
CHUTE_BAG_CM3 = 120.1            # fin and pad at every azimuth.  THIS is the budget a
                                 # bagged pack must beat, not 247.3 and not 253.3.
CHUTE_BAG_SOFT_CM3 = 127.0       # Ø45.39 x 78.5, allowing a fabric bag to deform past
                                 # the intrusions.  MEASURED off the exported half at
                                 # 0.25 deg of azimuth by _scratch/_fin_azimuth.py, for
                                 # the PAIR of halves, blocked azimuth out of 360:
                                 #   z 52.4..58.4   33.5 deg  gusset + root post pad
                                 #   z 58.4..62.0   11.5 deg  gusset alone
                                 #   z 62.0..119    0 deg     nothing at all
                                 #   z 120          16.0 deg  four dowel pads
                                 #   z 180          29.0 deg  four dowel pads
                                 # so every one of them is a fin and none is a throat.
                                 # This said "two 8 deg latch tongue fins", which named
                                 # the wrong feature: the gussets END at GUSSET_Z_TOP
                                 # 62.0, so over most of the bag's height the thing it
                                 # deforms round is a DOWEL PAD.  8 deg was the figure
                                 # for the 0.6 mm gusset measured at its inboard face;
                                 # the blocked angle depends on the radius you ask at,
                                 # because every intrusion here is a prism in y and a
                                 # fixed y band subtends more angle at smaller r.
                                 # NEITHER cylinder number moved, because both are set
                                 # at z 120.  They agree to 6 %, so the bag budget is
                                 # 120-127 cm3 either way.
CHUTE_PACK_FLAT_CM3 = (44.0, 122.0)   # a FLAT-CUT 30 in nylon canopy plus 8 lines and
                                      # a bag: 0.75..1.9 oz/yd2 ripstop, tight-rolled
                                      # to loose-stuffed.  From areal density x area /
                                      # packing fraction, with Knacke NWC TP 6575's
                                      # hand-pack 0.400..0.481 g/cm3 as the check.
CHUTE_PACK_HIDRAG_CM3 = (121.0, 261.0)  # PUBLISHED pack volumes for canopies SOLD as
                                        # 30 in but built for drag (toroidal /
                                        # elliptical, ~1.7x the fabric of a flat disc):
                                        # Fruity Chutes IFC-30-SUL 7.4 cu in through
                                        # CFC-30 15.9 cu in.  The small end exactly
                                        # equals the bag cylinder; the big end is 2.2x
                                        # it and DOES NOT FIT.  See self_check().

# ============================================================ print settings
NOZZLE = 0.4
EXTRUSION_W = 0.42
LAYER_H = 0.2
ABS_SHRINK = 0.006
BED = (300.0, 300.0, 300.0)              # Creality K1 Max, enclosed

# WHERE THE TIP ACTUALLY ENDS UP, which is not Z_TIP and not Z_SHELL_TOP either.
# The half lies on its split face, so the seam plane at |y| = SEAM_SETBACK is the
# bed and the FIRST LAYER is a slice of the cone at |y| = SEAM_SETBACK + LAYER_H.
# Declared here rather than up with the tip block because it needs LAYER_H, and it
# is the number to quote when someone measures the printed nose against cone.stl:
# the slicer costs 2.33x what the seam cut does, so no CAD change can beat it.
Z_TIP_AS_PRINTED = Z_TIP - (SEAM_SETBACK + LAYER_H) / math.tan(
    math.radians(TIP_HALF_ANGLE))                    # 247.6201


def hinge_moment_arm(y: float, z: float) -> float:
    """Perpendicular distance from half A's hinge axis to the point (y, z).

    The axis is a LINE PARALLEL TO X, so the distance lives in the YZ plane and
    the x coordinate does not enter it.  A tongue at x = 25 and one at x = 5 have
    the SAME leverage.  Forgetting that is the most repeated error on this project.
    """
    return math.hypot(y - Y_PIN, z - Z_PIN)


def rotate_open(y: float, z: float, theta_deg: float) -> tuple[float, float]:
    """Where (y, z) on half A goes after opening by theta about the hinge axis."""
    t = math.radians(theta_deg)
    dy, dz = y - Y_PIN, z - Z_PIN
    return (Y_PIN + dy * math.cos(t) + dz * math.sin(t),
            Z_PIN - dy * math.sin(t) + dz * math.cos(t))


def dowel_relative(y: float, z: float, theta_deg: float) -> tuple[float, float]:
    """Where a point of half A appears in half B's OWN frame, both halves open.

    Everything that has to pass through the seam -- the dowels above all -- lives
    in this frame and not in the world, because what matters to a socket in B is
    where the rod is RELATIVE TO B, and B is moving too.  Composing A's forward
    map with B's inverse gives a rotation by 2*theta about a virtual hinge on the
    split plane, so the seam opens twice as fast as either half turns.

    Only valid while the feature is still near the seam.  Carried far enough it
    reports nonsense for a sound reason: at theta = 90 deg the relative rotation
    is a full 180 deg, the two split planes are coincident again, and a point
    71 mm away from the joint reads as though it were inside it.  Callers must
    stop at the angle where the feature clears B's seam face -- see
    dowel_withdrawal().
    """
    t = math.radians(theta_deg)
    dy, dz = y - Y_PIN, z - Z_PIN                      # half A -> world
    yw = Y_PIN + dy * math.cos(t) + dz * math.sin(t)
    zw = Z_PIN - dy * math.sin(t) + dz * math.cos(t)
    dY, dZ = yw + Y_PIN, zw - Z_PIN                    # world -> half B
    return (dY * math.cos(t) + dZ * math.sin(t) - Y_PIN,
            -dY * math.sin(t) + dZ * math.cos(t) + Z_PIN)


def dowel_withdrawal(z0: float, n_phi: int = 72, n_y: int = 41,
                     dt: float = 0.01) -> tuple[float, float, float, float]:
    """Can the dowel at station z0 get out?  Swept, in half B's frame.

    Returns (overrun, peak_deg, out_by_deg, floor_gap):

        overrun    how far the rod's surface reaches past B's bore wall, mm.
                   NEGATIVE means it never touches -- that is the pass condition.
        peak_deg   where the worst case happens (not at 0 deg, which is why a
                   static fit check proves nothing here)
        out_by_deg the angle at which the last of the rod clears B's seam face
        floor_gap  smallest clearance from the rod's tip to B's socket floor

    Steps the whole rod surface, not its axis: the axis skews AND the rod has
    girth, and at the far end of the engagement those add.
    """
    import nose_profile as prof
    x_soc = float(prof.r_outer(z0)) - DOWEL_INSET
    r_rod, r_bore = DOWEL_D / 2, DOWEL_BORE / 2
    y_hi = SEAM_SETBACK + DOWEL_DEPTH              # glued BOTTOMED in half A
    y_lo = y_hi - DOWEL_LEN
    y_face_B, y_floor_B = -SEAM_SETBACK, -(SEAM_SETBACK + DOWEL_DEPTH)

    pts = []
    for i in range(n_phi):
        phi = 2 * math.pi * i / n_phi
        dx, zA = r_rod * math.sin(phi), z0 + r_rod * math.cos(phi)
        for j in range(n_y):
            pts.append((dx, y_lo + (y_hi - y_lo) * j / (n_y - 1), zA))

    overrun, peak, floor_gap, k = -9e9, 0.0, 9e9, 0
    while True:
        th = dt * k
        inside = False
        for dx, yA, zA in pts:
            yB, zB = dowel_relative(yA, zA, th)
            if yB >= y_face_B:
                continue                           # clear of B's seam face
            inside = True
            rad = math.hypot(dx, zB - z0) - r_bore
            if rad > overrun:
                overrun, peak = rad, th
            floor_gap = min(floor_gap, yB - y_floor_B)
        if not inside:
            return overrun, peak, th, floor_gap
        k += 1
        assert th < 20.0, f"dowel at z={z0} never leaves B's seam face"


def post_withdrawal(n_phi: int = 72, n_z: int = 41, dt: float = 0.01,
                    theta_max: float = 110.0) -> tuple[float, float, float, float]:
    """Can a half lift off the ring's root post?  Swept, in the HALF's frame.

    Returns the same four numbers as dowel_withdrawal(), and for the same reason:
    the post's axis is fixed but the SOCKET swings, so the worst case is not at
    0 deg and a static fit check proves nothing.  Expect
    (-0.24274, 4.68, 5.09, 1.200).

    ONE ROTATION, NOT TWO.  dowel_relative() composes A's forward map with B's
    inverse because both ends of that fit move; here the post belongs to the RING,
    which never moves, so relative to the ring a half turns by theta and by theta
    only.  Using 2*theta here would double the skew and condemn a fit that works.
    The rotation below is therefore the inverse of rotate_open(): it carries a
    fixed world point into the coordinates of a half that has opened by theta.

    The requirement has a closed form the sweep exists to confirm, not to find:

        need = PIN_RISE**2 / (2 * (Y_PIN - POST_Y))            = 0.10381 mm

    -- independent of POST_D, POST_H and POST_X, because to first order the socket
    translates in y by PIN_RISE*theta while the girth term grows as theta**2.  That
    is why the fit is bought with POST_BORE and cannot be bought by shortening the
    post the way DOWEL_LEN buys the dowel.
    """
    r_p, r_b = POST_D / 2, POST_BORE / 2
    pts = [(POST_X + r_p * math.cos(2 * math.pi * i / n_phi),
            POST_Y + r_p * math.sin(2 * math.pi * i / n_phi),
            Z_RING_TOP + POST_H * j / (n_z - 1))
           for i in range(n_phi) for j in range(n_z)]

    overrun, peak, floor_gap, k = -9e9, 0.0, 9e9, 0
    while True:
        th = dt * k
        t = math.radians(th)
        inside = False
        for px, py, pz in pts:
            dy, dz = py - Y_PIN, pz - Z_PIN
            yB = Y_PIN + dy * math.cos(t) - dz * math.sin(t)
            zB = Z_PIN + dy * math.sin(t) + dz * math.cos(t)
            if zB < Z_SHELL_ROOT:
                continue                           # below the half's root face
            inside = True
            rad = math.hypot(px - POST_X, yB - POST_Y) - r_b
            if rad > overrun:
                overrun, peak = rad, th
            floor_gap = min(floor_gap, Z_SHELL_ROOT + POST_BORE_DEPTH - zB)
        if not inside:
            return overrun, peak, th, floor_gap
        k += 1
        assert th < theta_max, "the root post never leaves the half's socket"


def knuckle_profile() -> list[tuple[float, float]]:
    """(y, z) outline of the SHELL-side hinge boss, extruded over |x| <= KNUCKLE_W/2.

    Deliberately rectangular-with-chamfers rather than a round knuckle.  In the
    shell's print pose y is the build direction, so a cylindrical knuckle's entire
    lower half would be unsupported overhang.  Here the two chamfers are 45 deg and
    every other face is either vertical or points straight up -- EXCEPT the web face
    at y = KNUCKLE_WEB_Y, whose normal points at the bed.  That one is fine only
    because it is buried inside the shell's own wall, so it is never a face on the
    finished solid.  It is not fine by construction, it is fine by 0.5 mm of margin
    at the worst corner, and self_check() measures it.  See KNUCKLE_WEB_Y.

    Lives here, not in half_shell.py, because the swept-clearance check below has
    to run on the SAME polygon that gets built.  Two copies would drift.
    """
    c, ct = KNUCKLE_CHAMFER, 1.5
    return [(KNUCKLE_WEB_Y, Z_SHELL_ROOT),
            (LUG_Y_OUT - c, Z_SHELL_ROOT),
            (LUG_Y_OUT, Z_SHELL_ROOT + c),
            (LUG_Y_OUT, KNUCKLE_Z_TOP - ct),
            (LUG_Y_OUT - ct, KNUCKLE_Z_TOP),
            (KNUCKLE_WEB_Y, KNUCKLE_Z_TOP)]


def lug_profile() -> list[tuple[float, float]]:
    """(y, z) outline of the RING-side hinge lug, extruded over |x| LUG_X_IN..LUG_X_OUT.

    The long edge from (LUG_Y_IN, LUG_RAMP_Z) out to (LUG_Y_OUT, root + LUG_CHAMFER)
    is a single 70 deg fairing, and it doubles as the outboard-bottom chamfer the
    sweep check needs: it means the lug does not reach its full LUG_Y_OUT width
    until 1.4 mm ABOVE the root plane, which is what keeps its furthest corner
    inside the shell's closest orbit.  The ring prints upright, so 70 deg is also
    what makes the lug self-supporting -- no horizontal underside anywhere on it.
    """
    ct = 1.5
    return [(LUG_Y_BORE, LUG_RAMP_Z),
            (LUG_Y_IN, LUG_RAMP_Z),
            (LUG_Y_OUT, Z_SHELL_ROOT + LUG_CHAMFER),
            (LUG_Y_OUT, LUG_Z_TOP - ct),
            (LUG_Y_OUT - ct, LUG_Z_TOP),
            (LUG_Y_IN, LUG_Z_TOP),
            (LUG_Y_IN, Z_RING_TOP),
            (LUG_Y_BORE, Z_RING_TOP)]


def _arc_gap(a, b) -> float:
    """Angular gap in degrees between two azimuth bands, negative if they overlap.

    Azimuth wraps, so a plain interval comparison gets 350..10 wrong.  Sampled
    instead of case-analysed, because the case analysis is where the bug hides.
    """
    (a0, a1), (b0, b1) = a, b
    best = 360.0
    n = max(2, int((a1 - a0) * 4) + 2)
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        d0 = ((t - b0 + 180.0) % 360.0) - 180.0
        d1 = ((t - b1 + 180.0) % 360.0) - 180.0
        best = 0.0 if (d0 >= 0.0) != (d1 >= 0.0) else min(best, min(abs(d0), abs(d1)))
        if best == 0.0:
            return -1.0
    return best


def _poly_samples(pts, step: float = 0.1):
    """Every vertex of a closed polygon plus points along its edges.

    Checking corners alone is not enough once a profile has chamfers: the closest
    approach can land in the middle of a sloped edge, not on either end of it.
    """
    out = []
    n = len(pts)
    for i in range(n):
        y0, z0 = pts[i]
        y1, z1 = pts[(i + 1) % n]
        k = max(1, int(math.hypot(y1 - y0, z1 - z0) / step))
        for j in range(k):
            out.append((y0 + (y1 - y0) * j / k, z0 + (z1 - z0) * j / k))
    return out


def arm_span_at_plane(x_plane: float, sweep_deg: float = None) -> tuple[float, float]:
    """y range the latch arm occupies at the plane x = x_plane, over its whole sweep.

    Both bounds are monotonic in the sweep angle, so the union over the sweep is
    just the two endpoints -- there is nothing to search.
    """
    if sweep_deg is None:
        sweep_deg = LATCH_SWEEP
    w = LATCH_ARM_W / 2
    lo, hi = [], []
    for t in (0.0, math.radians(sweep_deg)):
        lo.append(x_plane * math.tan(t) - w / math.cos(t))
        hi.append(x_plane * math.tan(t) + w / math.cos(t))
    return min(lo), max(hi)


def horn_lever_w(x: float) -> float:
    """MEASURED width of the servo horn's blade at distance |x| from the shaft.

    Not a single number, which is what the old HORN_LEVER_W = 4.6 pretended: the
    blade is HORN_LEVER_W (7.2) across the middle, holds that full width out to
    HORN_LEVER_W_FULL (11.25, half of the measured 22.5 mm section) and then tapers
    straight to HORN_LEVER_W_TIP (4.1) at HORN_LEVER_R.  Sizing a slot on the tip
    width leaves 6.75 mm of blade per side interfering with solid arm, which is
    exactly why the arm would not go on.

    Beyond the tip the blade has ended, so the width is 0 -- callers walking stations
    past HORN_LEVER_R get nothing to clear rather than an extrapolated negative.
    """
    a = abs(x)
    if a > HORN_LEVER_R:
        return 0.0
    if a <= HORN_LEVER_W_FULL:
        return HORN_LEVER_W
    f = (a - HORN_LEVER_W_FULL) / (HORN_LEVER_R - HORN_LEVER_W_FULL)
    return HORN_LEVER_W + f * (HORN_LEVER_W_TIP - HORN_LEVER_W)


def horn_slot_w(x: float) -> float:
    """Width of the slot cut in the arm at |x|.  Constant, and deliberately so.

    Exists as a function only so the asserts can walk the blade's envelope against
    the slot's envelope station by station; the day someone tapers the slot to save
    a gram, the check that catches it is already written.
    """
    return HORN_SLOT_W if abs(x) <= HORN_SLOT_R else 0.0


def fin_notch_half() -> float:
    """Half-width of the gap the fins must leave for the arm, plus clearance.

    Symmetric about y = 0 because the arm is a bar through the origin -- see the
    note by FIN_NOTCH_Z0.  Evaluated at the fin's OUTER plane, where the arm's
    band is widest.
    """
    t = math.radians(LATCH_SWEEP)
    return ((FIN_X_IN + FIN_T) * math.tan(t) + (LATCH_ARM_W / 2) / math.cos(t)
            + FIN_ARM_CLEAR)


def fin_notch_half_at(z: float) -> float:
    """Notch half-width at height z: full above FIN_NOTCH_Z0, closing at 45 deg below."""
    g = fin_notch_half()
    return max(0.0, min(g, g - (FIN_NOTCH_Z0 - z)))


def fin_segments() -> list[tuple[float, float]]:
    """The y extents of one fin WITHIN THE ARM'S Z BAND -- i.e. where it is split.

    The arm lives entirely above FIN_NOTCH_Z0, so over its own z range the fin is
    exactly these two rectangles and the swept-clearance check can be done in 2D.
    """
    g = fin_notch_half()
    return [(FIN_Y0, -g), (g, FIN_Y1)]


TONGUE_X_WALL = 31.2     # the polygon runs this far out so it lands INSIDE the
                         # shell wall; half_shell trims it back to the real skin


def tongue_profile() -> list[tuple[float, float]]:
    """(x, z) outline of one latch tongue, extruded across y.  The J.

    Lives here, not in half_shell.py, for the same reason knuckle_profile() and
    fin_profile() do: the swept checks in self_check() have to run on the very
    polygon that gets built.  A second copy drifts, and then the checks are
    verifying a shape nobody prints.

    Reading it as a path, starting at the foot's inboard-bottom corner:

        foot      x HOOK_X_IN..TONGUE_X1 at z Z_HOOK_BOT   -- passes UNDER the arm
        outboard  up the face at TONGUE_X1 to the shell root
        wall      out to TONGUE_X_WALL and STRAIGHT UP to GUSSET_Z_TOP
        gusset    back inboard to TONGUE_X0, at the same z
        blade     down the inboard face to Z_STEP
        step      OUT to WEB_X_IN via a chamfer -- the pocket's ceiling
        web       down to Z_LATCH_FACE, standing outboard of the arm's swept disc
        ledge     back in to HOOK_X_IN -- the LATCH FACE, facing UP

    The pocket bounded by the step, the web and the ledge is where the arm sits,
    and it is open on its inboard side because the arm reaches in to the axis.

    THE WALL RISES FULL DEPTH.  It used to reach z Z_SHELL_ROOT + 0.6 and then
    slope in to GUSSET_X at Z_TONGUE_TOP, which tapered the gusset BACKWARDS --
    9.5862 mm of depth at x 25.5 where the latch load comes IN, 0.6000 mm at
    x 31.2 where the skin has to take it OUT.  The weld between tongue and wall was
    a 4.7188 mm2 patch only 1.4689..1.7565 mm tall on an 8.79 mm arm, S = 1.2310
    mm3, and it broke at 2.546 N at the foot = 46 gf held at the nose tip.  This is
    the break the user reported.  Squaring it off costs 76.83 mm3 of tongue and
    0.055 cm3 of chute volume, and multiplies the weld by 7.19x in bending and
    10.34x sideways -- which is the axis that actually failed, against a stalled
    servo trying to drive the arm into the hooks at 10.54 N.

    The old (TONGUE_X_WALL, Z_SHELL_ROOT + 0.6) vertex is GONE rather than raised to
    GUSSET_Z_TOP, because GUSSET_Z_TOP IS Z_TONGUE_TOP and keeping it would put
    three collinear vertices on that line, with a zero-length edge between the first
    two that OCC degenerates.  The count is back to eleven only because the step
    grew a chamfer: STEP_CHAM breaks the pocket's inboard-top corner, which was a
    sharp reentrant notch sitting 0.6 mm from the web -- a stress raiser on the
    surface the arm loads, for free.  Claim no strength credit for it; the weld is
    what carries the load.
    """
    return [(HOOK_X_IN, Z_HOOK_BOT),
            (TONGUE_X1, Z_HOOK_BOT),
            (TONGUE_X1, Z_SHELL_ROOT),
            (TONGUE_X_WALL, Z_SHELL_ROOT),
            (TONGUE_X_WALL, GUSSET_Z_TOP),
            (TONGUE_X0, Z_TONGUE_TOP),
            (TONGUE_X0, Z_STEP),
            (WEB_X_IN - STEP_CHAM, Z_STEP),
            (WEB_X_IN, Z_STEP - STEP_CHAM),
            (WEB_X_IN, Z_LATCH_FACE),
            (HOOK_X_IN, Z_LATCH_FACE)]


def ramp_profile() -> list[tuple[float, float]]:
    """(y, z) cutter that turns the foot's flat top into the lead-in ramp.

    Extruded across x over the foot's exposed top face only -- the web above
    WEB_X_IN must keep its full root.  Reaches past TONGUE_Y1 so the ramp runs off
    the end of the part instead of stopping in a sliver.
    """
    y_a = TONGUE_Y0 + RAMP_LAND
    y_b = TONGUE_Y1 + 0.5
    return [(y_a, Z_LATCH_FACE),
            (y_b, Z_LATCH_FACE - ramp_slope() * (y_b - y_a)),
            (y_b, Z_LATCH_FACE + 1.0),
            (y_a, Z_LATCH_FACE + 1.0)]


def fin_profile() -> list[tuple[float, float]]:
    """(y, z) outline of one cradle fin, extruded across FIN_T.

    A full-length wall with a V-bottomed notch cut down from its top edge.  Lives
    here rather than in bulkhead.py so the swept-clearance check runs on the same
    numbers that get built.
    """
    g = fin_notch_half()
    return [(FIN_Y0, FIN_Z_BOT), (FIN_Y1, FIN_Z_BOT), (FIN_Y1, Z_BULK_BOT),
            (g, Z_BULK_BOT), (g, FIN_NOTCH_Z0), (0.0, FIN_NOTCH_Z0 - g),
            (-g, FIN_NOTCH_Z0), (-g, Z_BULK_BOT), (FIN_Y0, Z_BULK_BOT)]


def flange_pads() -> list[tuple[float, float]]:
    """The y extents of the two servo flange pads, clipped off the servo body.

    Each pad is centred on its screw hole and reaches PAD_Y_HALF either way,
    except on the side facing the servo, where it stops PAD_BODY_CLEAR short of
    the body's end.  The aft hole is only 2.6 mm from that end, so without the
    clip the pad would be inside the servo.
    """
    y_aft, y_fwd = SERVO_HOLE_Y
    return [(y_aft - PAD_Y_HALF, min(y_aft + PAD_Y_HALF,
                                     SERVO_BODY_Y[0] - PAD_BODY_CLEAR)),
            (max(y_fwd - PAD_Y_HALF, SERVO_BODY_Y[1] + PAD_BODY_CLEAR),
             y_fwd + PAD_Y_HALF)]


def arm_azimuth_band(sweep_deg: float = None) -> tuple[float, float]:
    """Azimuth range the arm's corners sweep through, degrees (one of the two lobes)."""
    if sweep_deg is None:
        sweep_deg = LATCH_SWEEP
    half = math.degrees(math.atan2(LATCH_ARM_W / 2, LATCH_ARM_R))
    return -half, sweep_deg + half


def latch_bearing_r() -> tuple[float, float]:
    """Radial extent of the foot's bearing patch under the arm, (r_in, r_out).

    The arm is a bar of half-width LATCH_ARM_W/2, so how far out it reaches at a
    given y is sqrt(ARM_CORNER_R^2 - y^2), not LATCH_ARM_R -- the corner is the
    furthest point and the middle of the end face is 0.35 mm shy of it.  Taken at
    TONGUE_Y1, the y where the arm reaches LEAST far, so this is the guaranteed
    overlap rather than the best case.
    """
    return HOOK_X_IN, math.sqrt(max(ARM_CORNER_R ** 2 - TONGUE_Y1 ** 2, 0.0))


def latch_force_per_half() -> float:
    """Spring moment reacted at the tongue, N.  Torque balance about the hinge.

    THE LEVER IS |dy|, NOT hypot(dy, dz), and that is not a rounding argument.
    The latch reaction is purely along z, so Mx = (r x F)_x = dy*Fz and the dz term
    cancels identically: the moment arm is the tongue's y offset from the pin and
    NOTHING ELSE.  hinge_moment_arm() returns the perpendicular distance, which is
    the right lever only for a force perpendicular to the radius.  Using it here
    understated the reaction by 2.7% with the load face at z = 47.0 and would
    understate it by 11.0% now that the face is at 38.6 -- i.e. the error grew as
    the geometry got better, which is the wrong direction for a safety number.
    The corollary is worth keeping in mind: moving the load face 8.4 mm DOWN in z
    changed the latch force by exactly zero.
    """
    return OPEN_MOMENT / abs((TONGUE_Y0 + TONGUE_Y1) / 2 - Y_PIN)


def release_torque(mu: float = LATCH_MU) -> float:
    """Friction torque the servo must beat to sweep the arm out, N.mm.

    Two contributions, both at their own radius: the foot's top face sliding on the
    arm's UNDERSIDE, and the arm's top face sliding on the bulkhead's thrust pad.
    Both sides of that sandwich carry the same normal force, which is the point of
    the thrust pad -- the servo's output shaft carries neither.

    Not included: the ramp.  Releasing runs DOWN the ramp, so its 0.20 slope helps
    by as much as friction hurts; it is the ENGAGE direction that pays for it, and
    that is priced in self_check().
    """
    f = latch_force_per_half()
    r_in, r_out = latch_bearing_r()
    r_foot = (r_in + r_out) / 2
    r_pad = (THRUST_PAD_R0 + THRUST_PAD_R1) / 2
    return mu * (2 * f * r_foot + 2 * f * r_pad)


def engage_torque(mu: float = LATCH_MU) -> float:
    """Torque to sweep the arm back IN and cam the halves shut, N.mm.

    Worse than release_torque by the ramp's slope: the arm has to climb it against
    the springs.  Per half the tangential force is F*(tan(ramp) + mu).
    """
    f = latch_force_per_half()
    r_in, r_out = latch_bearing_r()
    r_foot = (r_in + r_out) / 2
    r_pad = (THRUST_PAD_R0 + THRUST_PAD_R1) / 2
    return (2 * f * (ramp_slope() + mu) * r_foot) + mu * 2 * f * r_pad


def ramp_slope() -> float:
    """tan of the foot's lead-in ramp.  Must stay well under mu or it back-drives."""
    return RAMP_DROP / (TONGUE_Y1 - TONGUE_Y0 - RAMP_LAND)


def horn_drive_stress(torque: float = None, blade_t: float = None) -> dict:
    """What the horn's blade does to the slot's flanks.  N.mm in, MPa out.

    THIS IS THE ONE STRESS IN THE ARM THAT IS NOT COMFORTABLE, and it is the reason
    HORN_BLADE_T matters.  Everything else in the part is governed by printability;
    this is governed by load.

    Defaults to SERVO_STALL_NMM rather than engage_torque(), because a stalled servo
    driving into a latch that will not close is the case that actually breaks things
    -- it is what put 10.54 N into the hooks -- and the flank has no fuse in front of
    it.  Pass engage_torque() for the everyday figure.

    The model, stated so it can be argued with:

      * Contact is on the +y flank for x > 0 and the -y flank for x < 0, over the
        blade's thickness HORN_BLADE_T in z, and along |x| <= HORN_LEVER_W_FULL only.
        Outboard of that the blade tapers away from a constant-width slot, so it
        stands off by more than the 0.20 mm fit and cannot bear.  Taking the contact
        all the way to the tip would halve every stress below; it is not claimed.
      * Uniform pressure p over that strip.  T = 2 * integral(p*t*x dx, 0..L) =
        p*t*L^2, so p = T / (t * L^2).
      * The blade's top face is flush with the hub's, which is the pocket floor, so
        the load lands AT the flank's root and the cantilever arm is only t/2.  A
        blade sitting lower in the hub would be worse and is not what was measured.

    Two stresses come out and BOTH act across layer bonds, because the arm prints
    with its layer planes normal to z: the flank's root is a plane of constant z, and
    the bending it sees runs along z.  So both are checked against SIGMA_ABS_LAYER
    (11.0), not SIGMA_ABS (40.0).  This is the only place in the arm where that
    distinction changes the answer.
    """
    t = HORN_BLADE_T if blade_t is None else blade_t
    b = (LATCH_ARM_W - HORN_SLOT_W) / 2          # flank thickness in y
    L = HORN_LEVER_W_FULL                        # bearing half-length
    tq = SERVO_STALL_NMM if torque is None else torque
    p = tq / (t * L ** 2)                        # MPa of bearing on the flank face
    w = p * t                                    # N per mm of x, sideways on the flank
    tau = w / b                                  # shear across the root plane
    sigma = w * (t / 2) / (b ** 2 / 6)           # bending at the root
    res = math.hypot(sigma, tau)
    return {"torque": tq, "flank_t": b, "bear_L": L, "p_bear": p,
            "tau_root": tau, "sigma_root": sigma, "resultant": res,
            "fos_bend": SIGMA_ABS_LAYER / sigma, "fos_shear": SIGMA_ABS_LAYER / tau,
            "fos": SIGMA_ABS_LAYER / res}


def torsion_seat_yz(az_deg: float, r: float = None) -> tuple[float, float]:
    """Centre of a spring-leg seat in the y-z plane, from its azimuth about the pin.

    Azimuth runs from +y (radially OUT of the airframe) towards +z (towards the tip),
    which is the convention `_scratch/_spring_envelope.py` measured the pocket in and
    `_scratch/_seat_probe.py` verified the seats in.  Both parts build the +Y hinge and
    mirror, so nothing here needs to know about the -Y side.

    Only the +Y hinge is described.  On -Y the whole hinge mirrors through y = 0, which
    reflects the azimuth; the parts get that for free from their own mirroring.
    """
    t = math.radians(az_deg)
    rr = TORSION_LEG_R if r is None else r
    return (Y_PIN + rr * math.cos(t), Z_PIN + rr * math.sin(t))


def torsion_leg_azimuths(theta_deg: float) -> tuple[float, float]:
    """(knuckle, lug) leg azimuths at `theta_deg` of opening.

    The lug seat is in the base ring and never moves.  The knuckle seat is in the half
    shell, so it orbits the pin as the half opens -- and by the sign of rotate_open,
    every point of a half moves so that its azimuth about its own pin DECREASES 1:1
    with the opening angle.  That is why the included angle between the two legs grows
    from 70 deg shut to 170 deg at 100 deg open, and why the travel is exactly 100.
    """
    return (TORSION_SEAT_AZ_KNUCKLE - theta_deg, TORSION_SEAT_AZ_LUG)


def spring_check() -> list[str]:
    """The torsion spring, sized TO the pocket instead of wished for.

    Every assertion here is a real feature of the printed parts, checked in the
    direction that can fail.  The block above the TORSION_* constants says why the
    answer is 10.20 N.mm -- and records both times this file got it wrong: the 30 N.mm
    it invented, and the 5.44 that a per-radian/per-turn unit slip in TORSION_RATE
    produced out of a spring really worth 0.87.  `_scratch/_spring_pick.py` is the
    enumeration, `_spring_envelope.py` measured the space and `_seat_probe.py` verified
    the seat sites against the meshes.  `spring_jig.py` is how the thing gets wound, and
    it is the reason TORSION_COILS is 8.472 rather than 8.
    """
    out = []
    d, n, dm = TORSION_WIRE_D, TORSION_COILS, TORSION_COIL_D_MEAN
    od, idia = dm + d, dm - d
    # A coil WINDS UP as the nose closes, so its body grows by d * turns; the pair on
    # the other hinge unwinds and shrinks by the same amount.  Which extreme is the bad
    # one depends on what is being checked, so both are named here: the long body is
    # the fit case (1) and the short body is the engagement case (2).  Using the free
    # length n*d for both, as this used to, is optimistic in BOTH directions at once.
    rev = TORSION_TRAVEL / 360.0
    body = n * d
    body_wound = (n + rev) * d
    body_unwound = (n - rev) * d
    t_each = TORSION_MOMENT_EACH

    # --- 1. the coil body fits between the two faces that already trap it -- checked
    # WOUND, i.e. at the closed position, which is when the body is longest.
    assert body_wound < TORSION_GAP, (
        f"wound {TORSION_TRAVEL:.0f} deg the coil body is {body_wound:.2f} mm long in "
        f"a {TORSION_GAP} mm gap -- it would be clamped between the knuckle's end face "
        f"and the lug's inner face")
    # --- 2. and both legs stay in their seats at the worst float.  The spring spans
    # leg-tip to leg-tip; the two engagements always SUM to span - gap, so the worst
    # single one is that sum less the full seat depth.  Checked UNWOUND, the shortest
    # body and therefore the shortest span -- the same wound/unwound asymmetry that
    # assertion 4 already handles for coil DIAMETER.
    span = body_unwound + 2 * TORSION_SEAT_DEPTH
    engage = (span - TORSION_GAP) - TORSION_SEAT_DEPTH
    assert engage > 0.5, (
        f"a leg engages its seat by only {engage:.2f} mm at the worst axial float: the "
        f"spring spans {span:.2f} mm across a {TORSION_GAP} mm gap into two "
        f"{TORSION_SEAT_DEPTH} mm seats")
    # --- 3. the coil goes over the pin, with room to be dropped on by hand
    assert idia > D_PIN + 0.6, (
        f"coil ID {idia:.2f} on a {D_PIN} mm pin is a press fit, not an assembly")
    # --- 4. and cannot reach anything even shoved fully off-centre on that pin.
    # Checked twice: as wound (the coil shrinks, so this is the loose case) and as
    # UNWOUND, because four same-hand springs mean two of them unwind and grow.
    slop = (idia - D_PIN) / 2
    far = od / 2 + slop
    dm_un = dm * n / (n - rev)
    far_un = (dm_un + d) / 2 + ((dm_un - d) - D_PIN) / 2
    assert far <= POCKET_FREE_R, (
        f"the coil's far edge sits {far:.2f} mm off the pin axis against "
        f"{POCKET_FREE_R} mm of free radius at the knuckle end of the pocket")
    assert far_un <= POCKET_FREE_R, (
        f"unwound to grow the coil to Ø{dm_un + d:.2f}, the far edge reaches "
        f"{far_un:.2f} mm against {POCKET_FREE_R} -- so the four springs cannot all "
        f"be the same hand")
    # --- 5. the leg clears the coil it comes off, and clears the pocket walls too
    assert TORSION_LEG_R - d / 2 > od / 2, (
        f"the leg at r {TORSION_LEG_R} is inside the coil's own OD {od:.2f}")
    assert TORSION_LEG_R + d / 2 <= POCKET_FREE_R, "the leg would foul the pocket wall"
    # --- 6. and the seat does not break into the pin bore it runs beside
    for label, bore in (("knuckle", PIN_BORE_KNUCKLE), ("lug", PIN_BORE_LUG)):
        wall = TORSION_LEG_R - TORSION_SEAT_D / 2 - bore / 2
        assert wall > 0.8, (
            f"the {label} seat leaves only {wall:.2f} mm of wall to its Ø{bore} pin "
            f"bore")
    # --- 7. Both legs are captive, so the spring is wound the full TORSION_TRAVEL
    # every flight, and the bending stress at that deflection is the ceiling on wire
    # diameter.  Note sigma = 32 T / (pi d^3) with T = k * travel, so at fixed travel
    # sigma goes as d/(D n) -- it is NOT the binding constraint at Ø0.50 (49% used),
    # and it is what caps a substitution at about Ø0.66.  This assertion used to be
    # billed as "the one that killed the 30 N.mm claim"; what actually killed that was
    # the same 2 pi that then made this read 1690 instead of 269.
    sigma = 32 * t_each / (math.pi * d ** 3)
    assert sigma <= TORSION_SIGMA_ALLOW, (
        f"wound {TORSION_TRAVEL} deg this spring reaches {sigma:.0f} N/mm2 against an "
        f"allowable of {TORSION_SIGMA_ALLOW:.0f} -- it would take a set on the first "
        f"flight and never close again")
    # --- 8. the seats must be where the mesh says there is material.  Recomputed here
    # so a later edit to TORSION_LEG_R cannot silently walk them off the part.
    yk, zk = torsion_seat_yz(TORSION_SEAT_AZ_KNUCKLE)
    yl, zl = torsion_seat_yz(TORSION_SEAT_AZ_LUG)
    assert yk - TORSION_SEAT_D / 2 > KNUCKLE_WEB_Y + 0.5, (
        f"the knuckle seat at y {yk:.3f} is within 0.5 mm of the web face at "
        f"{KNUCKLE_WEB_Y}")
    assert yl - TORSION_SEAT_D / 2 > LUG_Y_IN + 0.5, (
        f"the lug seat at y {yl:.3f} is within 0.5 mm of the lug's inner face at "
        f"{LUG_Y_IN}")
    assert TORSION_SEAT_DEPTH < KNUCKLE_W / 2, "the knuckle seat would meet its mirror"
    assert TORSION_SEAT_DEPTH < LUG_W, "the lug seat would break out of the lug's back"
    # --- 9. AND THAT IT OPENS THE NOSE AT ALL.  Nothing in this project asserted this
    # until the rate was found to be 2 pi too large, at which point every one of the
    # eight assertions above still passed on a spring delivering 0.10x of the moment
    # needed to lift a half.  Eight checks on whether the spring FITS and none on
    # whether it WORKS is how that survived into a bill of materials.
    assert OPEN_MOMENT > BENCH_MOMENT_WORST, (
        f"{OPEN_MOMENT:.2f} N.mm per half against {BENCH_MOMENT_WORST:.2f} N.mm of "
        f"worst-case bench gravity is {OPEN_MOMENT/BENCH_MOMENT_WORST:.3f}x -- the "
        f"spring cannot lift a half that hangs nose-down off a horizontal pin")
    # --- 10. AND THAT THE COIL COUNT IS ONE A JIG CAN ACTUALLY WIND.  The two legs
    # leave OPPOSITE ENDS of the coil, so the angle between them is not a free choice
    # bent in afterwards -- it IS the total wrap.  A free included angle of F therefore
    # forces n mod 1 = F/360, and the only legal counts are ... 7.472, 8.472, 9.472 ...
    # This constant read a round 8 until spring_jig.py had to say how many turns to
    # wind.  A round 8 is not a spring you can make with legs 170 deg apart, and taking
    # it as one overstated the torque by 5.5%.
    az_k_open, az_l = torsion_leg_azimuths(TORSION_TRAVEL)
    frac_needed = (az_l - az_k_open) / 360.0
    assert abs((n % 1.0) - frac_needed) < 0.01, (
        f"{n} coils puts the two legs {360*(n % 1.0):.0f} deg apart, but the free "
        f"angle has to be {360*frac_needed:.0f} deg -- the fractional part of the coil "
        f"count IS the leg angle, so it is not free.  Nearest legal counts: "
        f"{math.floor(n) + frac_needed - 1:.3f}, {math.floor(n) + frac_needed:.3f}, "
        f"{math.floor(n) + frac_needed + 1:.3f}")

    out.append(f"spring: Ø{d} wire, {n} coils, Ø{dm} mean -> OD {od:.2f}, ID "
               f"{idia:.2f} over the {D_PIN} mm pin, body {body_unwound:.2f}/{body:.2f}"
               f"/{body_wound:.2f} mm unwound/free/wound in the {TORSION_GAP} mm gap; "
               f"{TORSION_RATE:.4f} N.mm/deg x {TORSION_TRAVEL:.0f} deg = "
               f"{t_each:.2f} N.mm each, {OPEN_MOMENT:.2f} per half from "
               f"{TORSION_COUNT_PER_HINGE}")
    out.append(f"spring stress: {sigma:.0f} of {TORSION_SIGMA_ALLOW:.0f} N/mm2 "
               f"({100*sigma/TORSION_SIGMA_ALLOW:.0f} %) at the closed position -- not "
               f"the binding constraint at this size; what caps the wire is the wound "
               f"body in the {TORSION_GAP} mm gap, at about Ø0.66")
    out.append(f"spring clearance: far edge {far:.2f} mm off the pin axis wound "
               f"({far_un:.2f} unwound) against {POCKET_FREE_R} mm of measured free "
               f"radius; the leg rides at r {TORSION_LEG_R}, outside the coil's "
               f"{od/2:.2f} and inside that {POCKET_FREE_R}")
    out.append(f"spring seats: Ø{TORSION_SEAT_D} x {TORSION_SEAT_DEPTH} mm blind, "
               f"knuckle end face at az {TORSION_SEAT_AZ_KNUCKLE:.0f} deg -> y "
               f"{yk:.4f} z {zk:.4f}, lug inner face at az {TORSION_SEAT_AZ_LUG:.0f} "
               f"-> y {yl:.4f} z {zl:.4f}; spring spans {span:.2f} mm so each leg "
               f"engages at least {engage:.2f} of {TORSION_SEAT_DEPTH} mm")
    a0 = torsion_leg_azimuths(0.0)
    a1 = torsion_leg_azimuths(TORSION_TRAVEL)
    out.append(f"spring free angle: the legs stand {a0[1]-a0[0]:.0f} deg apart shut and "
               f"{a1[1]-a1[0]:.0f} deg apart at {TORSION_TRAVEL:.0f} deg open, so the "
               f"spring must be made FREE at {a1[1]-a1[0]:.0f} deg -- free anywhere "
               f"short of that and it drives the nose SHUT over the last few degrees")

    # --- what it buys.  The half is a torsional oscillator, not a constant-torque
    # drive: the spring's moment decays linearly to zero at the free angle, so
    # theta(t) = TRAVEL * (1 - cos(omega_n t)) and the time to any angle comes from an
    # arccos, not from sqrt(2 I theta / T).  The constant-torque form that stood here
    # reads 136 ms against the true 144 -- optimistic, which is the wrong direction.
    # It is also why the half overswings to 2 * TRAVEL if nothing stops it.
    f_latch = latch_force_per_half()
    k_rad = OPEN_MOMENT / TORSION_TRAVEL * (180.0 / math.pi) * 1e-3   # N.m/rad
    omega_n = math.sqrt(k_rad / HALF_I_PIN)
    t_60 = math.acos(1.0 - 60.0 / TORSION_TRAVEL) / omega_n
    out.append(f"spring vs gravity: {OPEN_MOMENT:.2f} N.mm per half against "
               f"{BENCH_MOMENT_WORST:.2f} N.mm of worst-case bench gravity "
               f"({HALF_W_N:.4f} N at {HALF_R_CG:.2f} mm) = "
               f"{OPEN_MOMENT/BENCH_MOMENT_WORST:.2f}x -- OVER 1.0, so a half lifts "
               f"itself in any attitude, nose-down included")
    out.append(f"spring in flight: at apogee the rocket is in free fall, so gravity has "
               f"no moment about the pin at all and the spring works against "
               f"{HALF_I_PIN:.3e} kg.m2 alone -- omega_n {omega_n:.2f} rad/s, 60 deg "
               f"in {1000*t_60:.0f} ms, well inside the seconds of near-zero-g either "
               f"side of apogee")
    # The overswing ANGLE is rate-independent, but what the half ARRIVES WITH is not, so
    # these three numbers are derived here rather than quoted.  They used to be a frozen
    # "6.37 rad/s / 3.65 mJ / 1.24 m/s" in the format string, which was true of a rate
    # this file no longer carries.  theta(t) = TRAVEL*(1 - cos w t), so at the tube
    # sin(w t) = sqrt(1 - (1 - theta_tube/TRAVEL)^2) and omega = TRAVEL_rad * w * sin.
    ct = 1.0 - THETA_TUBE_STOP / TORSION_TRAVEL
    om_tube = math.radians(TORSION_TRAVEL) * omega_n * math.sqrt(max(0.0, 1 - ct * ct))
    r_tip = math.hypot(Z_TIP - Z_PIN, Y_PIN)
    out.append(f"spring overswing: with no designed stop the half turns to "
               f"2 x TRAVEL = {2*TORSION_TRAVEL:.0f} deg, independent of the rate. The "
               f"airframe body tube is the stop, swept at {THETA_TUBE_STOP} deg -- "
               f"reached {2*TORSION_TRAVEL-THETA_TUBE_STOP:.1f} deg short of the turning "
               f"point, at {om_tube:.2f} rad/s / "
               f"{1000*0.5*HALF_I_PIN*om_tube**2:.2f} mJ / "
               f"{om_tube*r_tip/1000:.2f} m/s at the tip {r_tip:.0f} mm out.  This is "
               f"why the free angle stays "
               f"{a1[1]-a1[0]:.0f} and does not go to the more buyable 180")
    # --- and what that torque does to the ONE part of the arm that is load-governed.
    # Checked at stall, not at engage_torque(): the flank has no fuse in front of it,
    # and a servo driving into a latch that will not close is the case that broke the
    # hooks.  Everyday operation is 12.6x less severe -- see the two figures reported.
    hd = horn_drive_stress()
    hd_run = horn_drive_stress(engage_torque())
    assert hd["fos"] > 1.5, (
        f"the lever slot's {hd['flank_t']:.3f} mm flank reaches "
        f"{hd['resultant']:.2f} MPa at the root against {SIGMA_ABS_LAYER} interlaminar "
        f"({hd['fos']:.2f}x) with a stalled servo -- widen LATCH_ARM_W, narrow "
        f"HORN_SLOT_W, or find a thinner horn")
    assert hd["sigma_root"] > hd["tau_root"], (
        "bending is expected to dominate the flank root; if shear has taken over, the "
        "blade is thinner than the flank and this model's arm-length assumption "
        "(t/2 below the root) no longer bounds it -- re-derive before trusting it")
    out.append(f"horn drive: the blade bears on {hd['flank_t']:.3f} mm flanks over "
               f"{hd['bear_L']:.2f} mm each side (the full-width section only -- the "
               f"taper stands off) x {HORN_BLADE_T} of thickness.  At a STALLED "
               f"{hd['torque']:.0f} N.mm that is {hd['p_bear']:.3f} MPa of bearing, "
               f"{hd['sigma_root']:.2f} MPa of bending + {hd['tau_root']:.2f} of shear "
               f"at the root = {hd['resultant']:.2f} MPa resultant, {hd['fos']:.2f}x on "
               f"{SIGMA_ABS_LAYER} interlaminar (BOTH components cross layer bonds in "
               f"this print pose).  Re-engaging is {hd_run['resultant']:.3f} MPa, "
               f"{hd_run['fos']:.1f}x.  A THICKER blade is worse, not better: "
               f"{HORN_LEVER_W_FULL * 2:.1f} mm of bearing length fixes the force per "
               f"mm at T/L^2 regardless of thickness, so thickness only lengthens the "
               f"lever to the root -- 2.0 mm would be "
               f"{horn_drive_stress(blade_t=2.0)['fos']:.2f}x and 3.0 mm "
               f"{horn_drive_stress(blade_t=3.0)['fos']:.2f}x")
    out.append(f"spring downstream: the latch holds {f_latch:.4f} N per half and the "
               f"servo needs {release_torque():.1f} N.mm to release and "
               f"{engage_torque():.1f} to re-engage, "
               f"{100*engage_torque()/SERVO_STALL_NMM:.0f} % of an MG90S's "
               f"{SERVO_STALL_NMM:.0f} N.mm stall")
    return out


def self_check() -> list[str]:
    out = []

    assert abs(Z_SHELL_ROOT - Z_OGIVE) < 1e-9, "split must be at the tangent station"
    out.append(f"split at the tangent station z {Z_SHELL_ROOT:.4f}; ring top "
               f"{Z_RING_TOP:.4f}, shell root {Z_SHELL_ROOT:.4f}, gap {ROOT_GAP}")
    out.append(f"shell: root {Z_SHELL_ROOT:.4f} .. DESIGN tip {Z_SHELL_TIP:.4f} = "
               f"{SHELL_LEN:.4f} mm, of which {SHELL_LEN_PRINTED:.4f} mm survives the "
               f"seam cut (apex {Z_SHELL_TOP:.4f}) and {Z_TIP_AS_PRINTED - Z_SHELL_ROOT:.4f} "
               f"mm survives the slicer (apex {Z_TIP_AS_PRINTED:.4f}); root bore r "
               f"{R_SHELL_ROOT_IN:.4f} ({WALL} mm NORMAL wall = "
               f"{prof.wall_normal_to_radial(WALL, Z_SHELL_ROOT):.4f} radial)")

    # --- THE BLUNT TIP, as arithmetic rather than as a suspicion.  The user compared
    # this nose to cone.stl and found it short.  It is, by TIP_DEFICIT, and that is
    # not drift, a scaling error or a profile bug: it is SEAM_SETBACK divided by the
    # tangent of the tip half-angle, exact to 1e-12.  The seam cut at |y| = 0.15
    # outruns the ogive once the ogive is narrower than 0.30 mm across.
    assert abs(TIP_DEFICIT - SEAM_SETBACK / math.tan(math.radians(TIP_HALF_ANGLE))) < 1e-12, \
        "TIP_DEFICIT must BE SEAM_SETBACK/tan(half-angle), not track it"
    assert abs(TIP_DEFICIT - 0.5766096) < 1e-6, (
        f"the tip deficit moved to {TIP_DEFICIT:.7f} -- if that was intended, the "
        f"printed-apex line below and nose_verify's bbox check move with it")
    # the datum hangs on one tangent, so guard the tangent: the ogive is straight
    # over the last 6 mm and every station in that band must agree to 1e-6.
    assert max(abs(prof.slope_deg(z) - TIP_HALF_ANGLE)
               for z in (243.0, 244.0, 246.0, 248.0)) < 1e-6, (
        "the tip cone is no longer straight over its last 6 mm, so Z_SHELL_TOP is "
        "being computed from a tangent that does not apply where it is used")
    # AND THE ASSERT THAT CLOSES THE QUESTION.  Even a perfectly pointed CAD apex
    # prints blunter than this one, because the FIRST LAYER is what lands on the bed.
    assert (SEAM_SETBACK + LAYER_H) / math.tan(math.radians(TIP_HALF_ANGLE)) > TIP_DEFICIT, (
        "if the slicer's first layer cost less than the seam cut, closing the CAD "
        "apex would be worth doing -- check the tip taper in _scratch before ruling "
        "it out again")
    assert 2 * SEAM_SETBACK / (2 * R_AIRFRAME) < 0.01, (
        f"the closed apex flat is {2 * SEAM_SETBACK:.2f} mm = "
        f"{100 * SEAM_SETBACK / R_AIRFRAME:.3f} % of the base diameter; past 1 % this "
        f"stops being a nose cone and starts being a truncated one")
    out.append(f"tip: the seam cut at |y| = {SEAM_SETBACK} outruns the ogive at z "
               f"{Z_SHELL_TOP:.4f}, so each half is {TIP_DEFICIT:.4f} mm "
               f"({100 * TIP_DEFICIT / SHELL_LEN:.3f} %) short of the {Z_TIP:.4f} apex "
               f"-- exactly SEAM_SETBACK/tan({TIP_HALF_ANGLE:.4f} deg), leaving a "
               f"{2 * SEAM_SETBACK:.2f} mm flat.  The first {LAYER_H} mm layer then "
               f"loses another {Z_SHELL_TOP - Z_TIP_AS_PRINTED:.4f}, so the printed "
               f"apex is {Z_TIP_AS_PRINTED:.4f}: the SLICER costs "
               f"{(SEAM_SETBACK + LAYER_H) / SEAM_SETBACK:.2f}x what the CAD does, and "
               f"no change to this file can recover it.  Fill and sand, or accept it")

    # --- hinge: the no-interference proof, checked numerically not just claimed.
    # This covers the SKIN, every point inboard of the OD.  Such a point has
    # y <= R_AIRFRAME < Y_PIN so dy < 0, which is the hypothesis the proof needs.
    # This used to sweep 0..90 deg in 1 deg steps, which is a HOLE: TORSION_TRAVEL is
    # 100, so the last 10 degrees of designed travel were never checked, and it turns
    # out that is where all the margin is.  Swept at 0.1 deg to the full travel and
    # beyond, the first skin point crosses the root plane at 101.3 deg -- 1.3 deg past
    # open, and exactly 0.000000 AT open.  The design travel sits on the geometric
    # limit, which is worth knowing before anyone increases it.
    worst, first_dip = 0.0, None
    sites = [(y, z)
             for y in (0.0, 10.0, 20.0, 30.0, R_AIRFRAME)
             for z in (Z_SHELL_ROOT, Z_SHELL_ROOT + 2.6, Z_SHELL_ROOT + 5, 120.0, Z_TIP)
             if y <= prof.r_outer(z) + 1e-9]
    for i in range(0, int(10 * 2 * TORSION_TRAVEL) + 1):
        th = i / 10.0
        low = min(rotate_open(y, z, th)[1] - Z_SHELL_ROOT for y, z in sites)
        if th <= TORSION_TRAVEL:
            worst = min(worst, low)
        if first_dip is None and low < -1e-9:
            first_dip = th
    assert worst >= -1e-9, f"a shell point dipped {worst:.4f} mm below the root plane"
    assert first_dip is None or first_dip > TORSION_TRAVEL, (
        f"the skin crosses the root plane at {first_dip:.1f} deg, inside the "
        f"{TORSION_TRAVEL:.0f} deg of designed travel")
    out.append(f"pin {PIN_OFFSET} outboard and {PIN_RISE} above the root: over the full "
               f"theta 0..{TORSION_TRAVEL:.0f} deg of travel the lowest any point of "
               f"the SKIN reaches is {worst:+.6f} mm relative to the root plane -- no "
               f"relief cut needed anywhere.  First crossing is at {first_dip:.1f} deg, "
               f"so there is only {first_dip - TORSION_TRAVEL:.1f} deg of slack: past "
               f"it the skin sweeps down OUTSIDE the airframe OD (free air) until the "
               f"overswing puts it back on the tube at {THETA_TUBE_STOP} deg")

    # --- the KNUCKLE is the one part of the shell that stands OUTBOARD of the pin,
    # so its dy is positive and the proof above does not cover it: it genuinely
    # does swing below the root plane.  That is allowed, because outboard of the OD
    # and below the root plane is empty air -- the ring's collar stops at
    # R_AIRFRAME and its lugs are in a different x band.  What must be checked is
    # the pair: a knuckle point may be low, or inboard, but never both at once.
    # Swept to 2 x TORSION_TRAVEL, not to 90 as it was: the knuckle keeps orbiting for
    # the whole overswing, and unlike the skin it never stops being the part closest to
    # the collar.  The worst point is NOT at either end of the sweep -- it is at 145.6
    # deg, well past open, which is precisely why stopping at 90 was not conservative.
    k_low, k_margin, k_at = Z_SHELL_ROOT, 1e9, 0.0
    for y0, z0 in _poly_samples(knuckle_profile(), 0.1):
        for i in range(0, int(10 * 2 * TORSION_TRAVEL) + 1):
            th = i / 10.0
            yy, zz = rotate_open(y0, z0, th)
            k_low = min(k_low, zz)
            if zz < Z_RING_TOP:                    # low enough to matter
                if yy - R_AIRFRAME < k_margin:
                    k_margin, k_at = yy - R_AIRFRAME, th
    assert k_margin > 0.5, (f"the knuckle swings into the ring collar: only "
                            f"{k_margin:.3f} mm outboard of the OD while below the "
                            f"ring's top face, at theta {k_at:.1f} deg")
    out.append(f"knuckle sweep: it dips to z {k_low:.3f}, {Z_SHELL_ROOT - k_low:.3f} mm "
               f"below the root plane -- but whenever it is below the ring's top face "
               f"it is at least {k_margin:.3f} mm outboard of the OD, i.e. in free air. "
               f"Worst at theta {k_at:.1f} deg, swept over the whole "
               f"0..{2*TORSION_TRAVEL:.0f} deg overswing, not just to open")

    # --- and the knuckle's WEB face must stay buried in the wall, or it becomes an
    # island in the print pose.  Worst corner: largest |x|, largest z, because the
    # skin's y falls with both.  This margin was +0.0010 mm once.
    x_k = KNUCKLE_W / 2
    web_bury = min(math.sqrt(max(float(prof.r_outer(z)) ** 2 - x_k ** 2, 0.0))
                   - KNUCKLE_WEB_Y
                   for z in (Z_SHELL_ROOT + 0.05 * i
                             for i in range(int((KNUCKLE_Z_TOP - Z_SHELL_ROOT) / 0.05) + 1)))
    assert web_bury > 0.3, (
        f"the knuckle's web face at y={KNUCKLE_WEB_Y} is only {web_bury:.4f} mm inside "
        f"the skin at its worst corner -- in the print pose that face points at the "
        f"bed, so if it ever emerges it is a {KNUCKLE_W:.0f} x "
        f"{KNUCKLE_Z_TOP - Z_SHELL_ROOT:.1f} mm island printed on air")
    out.append(f"knuckle web: buried {web_bury:.4f} mm inside the skin at its worst "
               f"corner (x {x_k:.0f}, z {KNUCKLE_Z_TOP:.4f}), so the one face on this "
               f"boss that points at the bed is never a face on the finished part")

    # --- the shell must also swing past the RING's lugs, which stand outboard.
    # Every shell point orbits the pin at a FIXED radius d, so if the whole lug
    # lies strictly inside the circle of the CLOSEST shell point, nothing can ever
    # touch at any angle -- one number settles it, with no search over theta.
    # Only the lug above the root plane counts: every shell point in the lug's x
    # band has y <= 31.03 < Y_PIN, so by the proof above it stays above the root.
    lug_prof = [(y, z) for y, z in _poly_samples(lug_profile(), 0.1)
                if z >= Z_SHELL_ROOT - 1e-9]
    d_crit = max(hinge_moment_arm(y, z) for y, z in lug_prof)
    zs = [Z_SHELL_ROOT + 0.2 * i for i in range(101)]
    d_min = min(hinge_moment_arm(math.sqrt(max(float(prof.r_outer(z)) ** 2
                                               - LUG_X_IN ** 2, 0.0)), z) for z in zs)
    assert d_min > d_crit, (f"the shell would sweep through the ring lug: closest "
                            f"shell orbit d={d_min:.3f} vs lug reach {d_crit:.3f}")
    out.append(f"lug sweep: the lug's furthest corner above the root reaches "
               f"{d_crit:.3f} mm from the pin (the outboard-bottom one, which is why "
               f"it carries a {LUG_CHAMFER} mm chamfer); the nearest shell point in "
               f"the lug's x band {LUG_X_IN}..{LUG_X_OUT} orbits at {d_min:.3f} mm -- "
               f"clear by {d_min - d_crit:.3f} mm at EVERY angle, since d never changes")
    assert LUG_Y_IN > R_AIRFRAME, "lug must stay outboard of the skin above the root"
    assert Y_PIN - PIN_BORE_LUG / 2 - LUG_Y_IN > 1.1, "too little material inboard of the lug bore"
    assert LUG_Y_OUT - (Y_PIN + PIN_BORE_LUG / 2) > 1.1, "too little material outboard of it"
    assert LUG_Z_TOP - (Z_PIN + PIN_BORE_LUG / 2) > 1.1, "too little material above it"
    assert TORSION_COIL_OD_MAX / 2 <= PIN_OFFSET, \
        "torsion coil would foul the skin; it must stay outboard of the OD"
    out.append(f"hinge stack along x: lug {-LUG_X_OUT}..{-LUG_X_IN} | coil | knuckle "
               f"{-KNUCKLE_W/2}..{KNUCKLE_W/2} | coil | lug {LUG_X_IN}..{LUG_X_OUT}; "
               f"pin {PIN_LEN} mm long, boss stands "
               f"{LUG_Y_OUT - R_AIRFRAME:.2f} mm proud of the OD")
    out.extend(spring_check())

    # ======================================================================
    # THE LATCH DIRECTION CHECK.  THIS IS THE CHECK THIS PROJECT DID NOT HAVE.
    # ======================================================================
    # 236 other assertions passed a latch that could not latch, because every one
    # of them measured a DISTANCE and none of them measured a SIGN.  The blade was
    # exactly coplanar with the arm, exactly the right size, exactly clear of
    # everything -- and on the wrong side, so it restrained nothing.
    #
    # A face restrains opening if and only if the material that opposes it lies on
    # the side the face MOVES TOWARD.  So: compute the load face's velocity as the
    # half opens, and require its sign to match the side of the arm the face bears
    # on.  One line of arithmetic, and no amount of correct dimensions can satisfy
    # it if the topology is backwards.
    dz_dth = (rotate_open(TONGUE_Y0, Z_LATCH_FACE, 1e-4)[1] - Z_LATCH_FACE) / 1e-4
    assert dz_dth > 0.0, (
        f"the latch face moves {dz_dth:+.4f} mm/deg as the half opens; every point "
        f"of a half is inboard of its own pin so this must be POSITIVE")
    assert LATCH_FACE_UP, "the latch face rises, so it must bear UPWARD on the arm"
    assert abs(Z_LATCH_FACE - Z_ARM_BOT) < 1e-9, (
        "an UP-facing latch face must be coplanar with the arm's BOTTOM, not its "
        "top -- coplanar with the top is the configuration that restrains nothing")
    assert Z_HOOK_BOT < Z_ARM_BOT, "the foot has to pass under the arm to reach it"
    assert HOOK_X_IN < math.sqrt(ARM_CORNER_R ** 2 - TONGUE_Y1 ** 2), \
        "the foot must reach inboard of the arm's end at EVERY y it occupies"
    r_in, r_out = latch_bearing_r()
    assert r_out - r_in > 1.5, (
        f"only {r_out - r_in:.2f} mm of the foot is actually under the arm")
    assert WEB_X_IN > ARM_CORNER_R, "the web would sit inside the arm's swept disc"
    web_gap = math.hypot(WEB_X_IN, TONGUE_Y0) - ARM_CORNER_R
    assert web_gap > 0.5, (f"the web clears the arm's swept disc by only "
                           f"{web_gap:.3f} mm and the arm crosses it every cycle")
    assert Z_STEP > Z_ARM_TOP + 0.4, "the pocket's ceiling would rub the arm's top"
    assert WEB_X_IN + 1.26 <= TONGUE_X1, "the web is thinner than one printable wall"
    assert LATCH_MU / ramp_slope() > 1.5, (
        f"the foot's ramp is {ramp_slope():.3f} against mu={LATCH_MU} -- only "
        f"{LATCH_MU / ramp_slope():.2f}x from back-driving, so the springs could "
        f"push the arm out of engagement on their own")
    assert engage_torque() < 0.5 * SERVO_STALL_NMM, (
        f"engaging needs {engage_torque():.0f} N.mm of the servo's "
        f"{SERVO_STALL_NMM:.0f}")
    out.append(f"LATCH DIRECTION: the load face at z {Z_LATCH_FACE} rises "
               f"{dz_dth:+.4f} mm/deg as the half opens, and the arm is ABOVE it -- "
               f"the foot hooks under x {r_in:.2f}..{r_out:.2f}, {r_out - r_in:.2f} mm "
               f"of overlap (the outboard limit is ARM_CORNER_R's arc, not "
               f"LATCH_ARM_R).  For the area it bears on see the latch-bearing line "
               f"below: the footprint is {(r_out - r_in) * (TONGUE_Y1 - TONGUE_Y0):.2f} "
               f"mm2 but the FLAT land is smaller and it is the land that governs")
    out.append(f"latch load {latch_force_per_half():.4f} N per half (lever |dy| = "
               f"{abs((TONGUE_Y0 + TONGUE_Y1) / 2 - Y_PIN):.4f} mm, independent of the "
               f"face's z); web clears the arm's disc by {web_gap:.3f} mm, pocket "
               f"ceiling by {Z_STEP - Z_ARM_TOP:.2f} mm; release "
               f"{release_torque():.0f} N.mm, engage {engage_torque():.0f} N.mm of "
               f"{SERVO_STALL_NMM:.0f} available")

    # ======================================================================
    # THE HOOK STRENGTH CHECK.  THE SECOND CHECK THIS PROJECT DID NOT HAVE.
    # ======================================================================
    # Every assert above measures the DESIGN load, 0.5982 N, and the hook was never
    # close to failing at it -- 4.3x at the weld, 11.5x at the web, 120x on
    # interlaminar peel.  The hooks still broke, because the loads that break them
    # are not the design load.  They are:
    #
    #   HANDLING   the whole nose picked up by the tip, amplified 5.69x by the
    #              hinge geometry into the tongue
    #   SERVO JAM  a stalled MG90S driven SIDEWAYS into a foot that is not fully
    #              down, which loads the one axis where the load path is a layer
    #              bond at 11 MPa instead of a bead at 40
    #
    # so those are what is asserted here, in newtons, with the mechanism named.
    #
    # The break that happened was #1 in the ranking: a flat fracture on the plane
    # z = Z_SHELL_ROOT running the full 3.0 mm of y, the hook, web and blade coming
    # away as one piece and leaving a scar on the INSIDE of the shell wall.  If the
    # user's broken parts show a SMOOTH glossy surface with parallel bead ridges
    # instead, it was #2, the servo jam, and the servo needs re-zeroing as well.
    h_weld = GUSSET_Z_TOP - Z_SHELL_ROOT
    s_weld = (TONGUE_Y1 - TONGUE_Y0) * h_weld ** 2 / 6.0
    assert h_weld > 6.0, (
        f"the gusset is the tongue's ONLY attachment to the shell and its depth in z "
        f"IS its section modulus: {h_weld:.4f} mm gives S = {s_weld:.2f} mm3; the "
        f"0.6 mm version gave 1.23 mm3 and broke at 46 gf applied at the nose tip")
    # 8.79 mm: MEASURED on the built solid, from the weld patch to the bearing land.
    # Kt 2.2 for the sharp 90 deg re-entrant corner -- there is no fillet anywhere on
    # this profile and half_shell.py extrudes it straight.
    WELD_ARM, KT_WELD, KT_WEB = 8.79, 2.2, 1.977
    assert KT_WELD * latch_force_per_half() * WELD_ARM / s_weld < SIGMA_ABS / 6.0, (
        f"less than 6x on the hook's weld at the design latch load: "
        f"{KT_WELD * latch_force_per_half() * WELD_ARM / s_weld:.3f} MPa")

    # --- what it takes to break it, down (in-plane, 40 MPa) and sideways
    # (torsion of the weld, whose shear lands on constant-y planes = the layer
    # bonds, 11 MPa).  Both section moduli are the printed geometry's, not literals.
    t_web = TONGUE_X1 - WEB_X_IN
    s_web_x = (TONGUE_Y1 - TONGUE_Y0) * t_web ** 2 / 6.0        # bends radially
    s_web_y = t_web * (TONGUE_Y1 - TONGUE_Y0) ** 2 / 6.0        # bends sideways
    r_in, r_out = latch_bearing_r()
    lever_web = (WEB_X_IN + TONGUE_X1) / 2 - (r_in + r_out) / 2
    f_z_break = min(SIGMA_ABS * s_weld / (KT_WELD * WELD_ARM),
                    SIGMA_ABS * s_web_x / (KT_WEB * lever_web))
    # torsion of the weld rectangle, Roark's alpha, interpolated -- and which side
    # is "long" FLIPS once the weld is taller than 3.0 mm, which is exactly what
    # this change does.  Hardcoding b = 3.0 as the long side is a real bug that was
    # in an earlier pass of this arithmetic.
    _AR = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0]
    _AL = [0.208, 0.231, 0.246, 0.258, 0.267, 0.282, 0.299, 0.312]
    long_w, short_w = max(h_weld, TONGUE_Y1 - TONGUE_Y0), min(h_weld, TONGUE_Y1 - TONGUE_Y0)
    alpha = _AL[-1] if long_w / short_w >= _AR[-1] else next(
        _AL[i] + (_AL[i + 1] - _AL[i]) * (long_w / short_w - _AR[i]) / (_AR[i + 1] - _AR[i])
        for i in range(len(_AR) - 1) if _AR[i] <= long_w / short_w < _AR[i + 1])
    lever_y = Z_SHELL_ROOT + h_weld / 2 - (Z_LATCH_FACE - HOOK_T / 2)
    f_y_weld = SIGMA_ABS_LAYER * alpha * long_w * short_w ** 2 / lever_y
    f_y_web = SIGMA_ABS * s_web_y / (Z_STEP - (Z_LATCH_FACE - HOOK_T / 2))
    f_y_break = min(f_y_weld, f_y_web)

    # THE ASSERT THAT WOULD HAVE CAUGHT THE DESIGN.  A stalled servo bearing on the
    # foot's END instead of its ramp -- which happens whenever a half is more than
    # 0.672 deg from shut, i.e. 4.55 mm of visible seam gap at the tip.
    f_jam = SERVO_STALL_NMM / r_in
    assert f_y_break > f_jam, (
        f"a stalled servo delivers {f_jam:.2f} N sideways at r = {r_in:.2f} and the "
        f"hook breaks at {f_y_break:.3f} N ({'weld torsion' if f_y_weld < f_y_web else 'the web'}"
        f") -- the old 0.6 mm gusset gave 1.248 N, 8.4x UNDER, and that is the "
        f"failure the user reported")
    # HANDLING, stated where the user's hand actually is: the nose tip.
    amp = (Z_TIP - Z_PIN) / abs((TONGUE_Y0 + TONGUE_Y1) / 2 - Y_PIN)
    assert f_z_break / amp > 3.0, (
        f"the hook must survive 300 gf applied at the nose tip -- it holds "
        f"{1000 * f_z_break / amp / 9.81:.0f} gf, and 46 gf is a part you break "
        f"putting it in a box")
    # and one half surviving a knock, in g, which is the number a builder can feel.
    g_hold = f_z_break * abs((TONGUE_Y0 + TONGUE_Y1) / 2 - Y_PIN) / (HALF_W_N * HALF_R_CG)
    assert g_hold > 20.0, (
        f"the latch holds one half through only {g_hold:.1f} g -- a 20 g knock is an "
        f"ordinary bench drop and the old geometry survived 5.0")
    out.append(f"HOOK STRENGTH: the gusset is {h_weld:.4f} mm deep in z (S "
               f"{s_weld:.2f} mm3) and the web {t_web:.3f} mm thick (S "
               f"{s_web_x:.4f} radially, {s_web_y:.4f} sideways); it breaks DOWN at "
               f"{f_z_break:.2f} N = "
               f"{1000 * f_z_break / amp / 9.81:.0f} gf held at the nose tip "
               f"(amplified {amp:.2f}x by the hinge) or a {g_hold:.0f} g knock, and "
               f"SIDEWAYS at {f_y_break:.2f} N against {f_jam:.2f} N from a stalled "
               f"servo = {f_y_break / f_jam:.2f}x.  The 0.6 mm gusset it replaces gave "
               f"2.55 N / 46 gf / 5 g / 1.25 N and 0.12x -- THAT is why they snapped")

    # --- the servo horn.  Four of these numbers are MEASURED off the user's horn
    # and the asserts exist so a different horn fails loudly instead of quietly not
    # fitting, which is what happened: a 30.0 mm slot was cut for a 36.0 mm horn.
    assert HORN_POCKET_D >= HORN_HUB_D + 0.3, (
        f"the hub recess Ø{HORN_POCKET_D} does not clear a Ø{HORN_HUB_D} hub")
    assert abs(HORN_POCKET_DEPTH - HORN_HUB_H) < 1e-9, (
        "the pocket floor must land ON the hub's top face: deeper and the centre "
        "screw clamps thin air, shallower and the arm rides high")
    assert HORN_HUB_H - HORN_POCKET_DEPTH <= Z_BULK_BOT - Z_ARM_TOP, (
        f"a hub {HORN_HUB_H} tall in a {HORN_POCKET_DEPTH} pocket rides the arm's top "
        f"face to {Z_ARM_TOP + HORN_HUB_H - HORN_POCKET_DEPTH} and jams the bulkhead "
        f"at {Z_BULK_BOT}")
    assert HORN_SLOT_R >= HORN_LEVER_R + 0.3, (
        f"a {2 * HORN_LEVER_R:.1f} mm tip-to-tip horn will not seat in a "
        f"{2 * HORN_SLOT_R:.1f} mm slot")
    # WALK THE BLADE'S ENVELOPE, do not compare two scalars.  Comparing the slot to
    # one blade width is what let a 7.6-wide blade root be checked against a 4.6 tip
    # measurement and pass.  Station every 0.1 mm from the shaft to the tip and demand
    # 0.3 mm of clearance at each; with a constant slot the binding station is x = 0,
    # but the loop is what makes a tapered slot fail loudly instead of quietly.
    worst_x, worst_gap = 0.0, float("inf")
    for i in range(0, int(HORN_LEVER_R * 10) + 1):
        x = i / 10.0
        need = horn_lever_w(x)
        if need <= 0.0:
            continue
        gap = horn_slot_w(x) - need
        if gap < worst_gap:
            worst_x, worst_gap = x, gap
    assert worst_gap >= 0.3 - 1e-9, (
        f"the blade is {horn_lever_w(worst_x):.2f} mm wide at x {worst_x:.1f} and the "
        f"slot is only {horn_slot_w(worst_x):.2f} there -- {worst_gap:+.2f} mm of "
        f"clearance, and it needs 0.3.  A blade measured 7.2 across 22.5 mm of its "
        f"length does not go into a slot sized on its 4.1 mm tip")
    # The two walls either side of the pocket.  Both of these sit within 0.13 mm of
    # WALL_MIN, so the epsilon is not decoration: WALL_MIN is 1.26 as a literal but
    # 3 * EXTRUSION_W evaluates to 1.2599999999999998, and (LATCH_ARM_W -
    # HORN_POCKET_D) / 2 lands on 1.3849999999999998 rather than 1.385.  Without the
    # slack a design point that is right to the last printable micron fails on the
    # last bit of the mantissa.
    assert (LATCH_ARM_W - HORN_SLOT_W) / 2 >= WALL_MIN - 1e-9, (
        f"the slot's flanks carry all the torque and must be at least one "
        f"3-extrusion wall: a {HORN_SLOT_W} slot in a {LATCH_ARM_W} bar leaves "
        f"{(LATCH_ARM_W - HORN_SLOT_W) / 2:.4f}, and {WALL_MIN} is the floor")
    assert HORN_POCKET_D >= LATCH_ARM_W or \
        (LATCH_ARM_W - HORN_POCKET_D) / 2 >= WALL_MIN - 1e-9, (
        f"the hub recess must either break clean out of the bar or leave a printable "
        f"wall -- never a sliver: Ø{HORN_POCKET_D} in a {LATCH_ARM_W} bar leaves "
        f"{(LATCH_ARM_W - HORN_POCKET_D) / 2:.4f}")
    # THE NEW BINDING CHECK, and the one that catches a naive HORN_SLOT_R = 20:
    # there has to be solid arm left under the foot.
    assert math.hypot(HORN_SLOT_R, HORN_SLOT_W / 2) <= \
        math.hypot(TONGUE_X0, TONGUE_Y0) - 1.5, (
        f"the pocket corner reaches r {math.hypot(HORN_SLOT_R, HORN_SLOT_W / 2):.3f} "
        f"and the hooks bear from r {math.hypot(TONGUE_X0, TONGUE_Y0):.3f} -- there "
        f"must be solid arm under the foot")
    dead = Z_ARM_TOP - ARM_CB_DEPTH - Z_SERVO_TOP - SPLINE_STANDOFF
    assert CENTRE_SCREW_L - dead >= 4.0, (
        f"an M2.5 x {CENTRE_SCREW_L:.0f} spends {dead:.2f} mm crossing the spline "
        f"standoff and the counterbore before it reaches the horn, leaving "
        f"{CENTRE_SCREW_L - dead:.2f} mm of thread -- the stock 6 mm screw leaves "
        f"{6.0 - dead:.2f}")
    out.append(f"servo horn (DOUBLE-ARM): hub Ø{HORN_HUB_D} x {HORN_HUB_H} "
               f"tall into a Ø{HORN_POCKET_D} x {HORN_POCKET_DEPTH} pocket; blade "
               f"{2 * HORN_LEVER_R:.0f} mm tip to tip, {HORN_LEVER_W} wide across the "
               f"middle {2 * HORN_LEVER_W_FULL:.1f} mm and {HORN_LEVER_W_TIP} at the "
               f"tips, {HORN_BLADE_T} thick (THIS ONE STILL UNMEASURED), into a "
               f"{2 * HORN_SLOT_R:.1f} x {HORN_SLOT_W} slot held to full width "
               f"throughout -- {worst_gap:.2f} mm of side clearance at its worst "
               f"station (x {worst_x:.1f}), {HORN_SLOT_R - HORN_LEVER_R:.2f} "
               f"mm per end, was 3.00 mm SHORT per end); "
               f"{(LATCH_ARM_W - HORN_SLOT_W) / 2:.2f} mm flanks; the pocket corner "
               f"stops at r {math.hypot(HORN_SLOT_R, HORN_SLOT_W / 2):.3f} with "
               f"{math.hypot(TONGUE_X0, TONGUE_Y0) - 1.5 - math.hypot(HORN_SLOT_R, HORN_SLOT_W / 2):.3f} "
               f"mm to spare under the foot; M2.5 x {CENTRE_SCREW_L:.0f} threads "
               f"{CENTRE_SCREW_L - dead:.2f} mm past {dead:.2f} mm of dead travel")

    # --- tongue clears its slot, and how far sideways it wanders getting there.
    # SWEPT, over every edge of the tongue's own polygon and both of its y faces,
    # because the answer depends on how far below the pin a point hangs and the
    # worst point is not the one any single-corner test would pick.  The previous
    # version of this check sampled ONE face at ONE angle and reported 0.41 mm of
    # drift for a tongue that drifts 4.25 mm.
    y_lo, y_hi, th_worst, th_clear = 1e9, -1e9, 0.0, None
    prof_pts = _poly_samples(tongue_profile(), 0.05)
    for i in range(0, 6001):
        th = i / 200.0
        inside = False
        for x0, z0 in prof_pts:
            for y0 in (TONGUE_Y0, TONGUE_Y1):
                yy, zz = rotate_open(y0, z0, th)
                if Z_BULK_BOT <= zz <= Z_BULK_TOP:
                    inside = True
                    if yy < y_lo:
                        y_lo, th_worst = yy, th
                    y_hi = max(y_hi, yy)
        if inside:
            th_clear = th
    assert th_clear is not None and th_clear < 30.0, \
        "the tongue never gets out of the bulkhead slot"
    assert SLOT_Y0 < y_lo - 0.3, (
        f"the tongue drifts to y={y_lo:.4f} at {th_worst:.2f} deg while still inside "
        f"the disc; the slot only reaches {SLOT_Y0} -- the halves would jam shut")
    assert y_hi + 0.3 < SLOT_Y1, (
        f"the tongue reaches y={y_hi:.4f}, outboard of the slot's {SLOT_Y1}")
    out.append(f"tongue vs its slot, SWEPT: it is inside the disc's z band until "
               f"{th_clear:.2f} deg of opening and drifts to y {y_lo:+.4f} at "
               f"{th_worst:.2f} deg (outboard extreme {y_hi:+.3f}); slot spans "
               f"{SLOT_Y0:+.2f}..{SLOT_Y1:+.2f}, so clear by "
               f"{y_lo - SLOT_Y0:.3f} / {SLOT_Y1 - y_hi:.3f} mm")

    # --- and the tongue clears the SEAT, which is why the seat needs no notches.
    # x is fixed for all time (the hinge axis is parallel to x), but the RADIUS is
    # not: |y| changes as the half swings, and the foot hangs far enough below the
    # pin that it is still crossing the seat's z band when its |y| has grown.  So
    # this one IS a sweep, unlike the flat blade's version of it, which was one
    # number and was right for the wrong reason.
    r_seat_worst, th_seat = 0.0, 0.0
    for i in range(0, 6001):
        th = i / 200.0
        for x0, z0 in prof_pts:
            for y0 in (TONGUE_Y0, TONGUE_Y1):
                yy, zz = rotate_open(y0, z0, th)
                if SEAT_Z0 - 0.5 <= zz <= SEAT_Z1 + 0.5:
                    r = math.hypot(x0, yy)
                    if r > r_seat_worst:
                        r_seat_worst, th_seat = r, th
    assert r_seat_worst < SEAT_R_IN - 0.5, (
        f"the tongue reaches r={r_seat_worst:.3f} at {th_seat:.2f} deg while level "
        f"with the seat, which starts at {SEAT_R_IN} -- move the seat out or notch it")
    slot_corner_r = math.hypot(TONGUE_X1 + SLOT_CLEAR_X_OUT, abs(SLOT_Y0))
    assert slot_corner_r < SEAT_R_IN - 0.25, (
        f"the blade slot's outer corner reaches r={slot_corner_r:.3f} against a seat "
        f"bore of {SEAT_R_IN} -- the bulkhead would lose the annulus it seats on")
    assert R_BULK - slot_corner_r > 1.5, "too little bulkhead rim outboard of the slot"
    out.append(f"tongue vs seat: swept, its outermost point while level with the "
               f"seat is r {r_seat_worst:.2f} at {th_seat:.2f} deg against a seat "
               f"bore of {SEAT_R_IN} -- clear by {SEAT_R_IN - r_seat_worst:.2f} mm; "
               f"the slot's own outer corner sits at r {slot_corner_r:.2f}, clear by "
               f"{SEAT_R_IN - slot_corner_r:.2f} with {R_BULK - slot_corner_r:.2f} mm "
               f"of rim left outboard of it")

    # --- the shock cord needs ONE clear straight drop past the servo bay.  Every
    # obstruction between the bulkhead and z=0 is listed here by name; a cord
    # that has to bend around something is a cord that gets pinched.
    rc = D_CORD_HOLE / 2
    y0c, y1c = Y_CORD_HOLE - rc, Y_CORD_HOLE + rc
    x0c, x1c = -rc, rc
    obstructions = [
        ("servo body",   (-SERVO_W / 2, SERVO_W / 2), SERVO_BODY_Y),
        ("flange tabs",  (-SERVO_W / 2, SERVO_W / 2),
         (SERVO_HOLE_Y[0] - 2.0, SERVO_HOLE_Y[1] + 2.0)),
        ("cradle fin -", (-FIN_X_IN - FIN_T, -FIN_X_IN), (FIN_Y0, FIN_Y1)),
        ("cradle fin +", (FIN_X_IN, FIN_X_IN + FIN_T), (FIN_Y0, FIN_Y1)),
        ("flange pad -", (-FIN_X_IN - FIN_T, FIN_X_IN + FIN_T), flange_pads()[0]),
        ("flange pad +", (-FIN_X_IN - FIN_T, FIN_X_IN + FIN_T), flange_pads()[1]),
        ("access hole -", (-SERVO_ACCESS_D / 2, SERVO_ACCESS_D / 2),
         (SERVO_HOLE_Y[0] - SERVO_ACCESS_D / 2, SERVO_HOLE_Y[0] + SERVO_ACCESS_D / 2)),
        ("access hole +", (-SERVO_ACCESS_D / 2, SERVO_ACCESS_D / 2),
         (SERVO_HOLE_Y[1] - SERVO_ACCESS_D / 2, SERVO_HOLE_Y[1] + SERVO_ACCESS_D / 2)),
        # the retention pads are the newest thing in the bay, so they go in the
        # SAME list rather than being argued about separately
        ("retention pad +x", (RETAIN_X_MIN, RING_BORE),
         (-RETAIN_HALF_CHORD, RETAIN_HALF_CHORD)),
        ("retention pad -x", (-RING_BORE, -RETAIN_X_MIN),
         (-RETAIN_HALF_CHORD, RETAIN_HALF_CHORD)),
    ]
    for name, (ox0, ox1), (oy0, oy1) in obstructions:
        gap = max(oy0 - y1c, y0c - oy1, ox0 - x1c, x0c - ox1)
        assert gap > 0.5, (f"the shock cord hole overlaps the {name} by "
                           f"{-gap:.2f} mm -- pick another azimuth for it")
    # and it must miss the moving arm and the screw lobes, by azimuth
    th_c = math.degrees(math.atan2(Y_CORD_HOLE, 0.0)) % 360.0
    half_c = math.degrees(math.atan2(rc, abs(Y_CORD_HOLE) - rc))
    ab0, ab1 = arm_azimuth_band()
    lobe_half = math.degrees(math.atan2(LOBE_HALF_CHORD, LOBE_R_IN))
    bands = [(ab0, ab1), (ab0 + 180.0, ab1 + 180.0)]
    bands += [(th - lobe_half, th + lobe_half) for th in LOBE_THETA]
    for lo, hi in bands:
        sep = _arc_gap((th_c - half_c, th_c + half_c), (lo, hi))
        assert sep > 3.0, (f"the cord hole's azimuth band "
                           f"{th_c - half_c:.0f}..{th_c + half_c:.0f} deg comes within "
                           f"{sep:.1f} deg of the band {lo:.0f}..{hi:.0f} deg")
    assert Y_CORD_HOLE - rc > -(SEAT_R_IN), "cord hole must stay inside the seat bore"
    out.append(f"shock cord: Ø{D_CORD_HOLE} at y {Y_CORD_HOLE} (azimuth "
               f"{th_c:.0f} deg, radius {abs(Y_CORD_HOLE):.0f}) drops clear of the "
               f"servo body, both flange tabs, both cradle fins, the flange pads, "
               f"the arm's sweep and both screw lobes -- a straight run from the "
               f"bulkhead to z=0 with no bend in it")

    # --- the arm must sit OVER the feet and still clear them when it swings
    assert LATCH_ARM_R > HOOK_X_IN, "arm must reach over the foot"
    assert ARM_CORNER_R < SEAT_R_IN, "arm corner must clear the bulkhead seat"
    out.append(f"arm half-length {LATCH_ARM_R}, corner radius {ARM_CORNER_R:.2f}; "
               f"sits over the foot across x {r_in:.2f}..{r_out:.2f} = "
               f"{r_out - r_in:.2f} mm, clears the seat at "
               f"{SEAT_R_IN} by {SEAT_R_IN - ARM_CORNER_R:.2f} mm")

    # --- the arm sweeps ACROSS the cradle fin planes, so the fins are notched.
    # The bar runs through the origin, so the notch has to clear its band on BOTH
    # sides of the axis at once; that is why it is symmetric and why it is 21 mm
    # wide rather than the 15 mm a one-sided reading gives.
    a0, a1 = arm_azimuth_band()
    g = fin_notch_half()
    segs = fin_segments()
    x_out = FIN_X_IN + FIN_T
    for xp in (FIN_X_IN, x_out):
        for k in range(61):
            t = math.radians(LATCH_SWEEP * k / 60.0)
            for sx in (+1, -1):
                for yy in (sx * xp * math.tan(t) - (LATCH_ARM_W / 2) / math.cos(t),
                           sx * xp * math.tan(t) + (LATCH_ARM_W / 2) / math.cos(t)):
                    assert abs(yy) <= g - FIN_ARM_CLEAR + 1e-9, (
                        f"at {math.degrees(t):.1f} deg the arm reaches y {yy:+.3f} on "
                        f"the x={sx*xp:+.2f} fin, outside the notch's {g:.3f} mm")
    assert FIN_NOTCH_Z0 - g > FIN_Z_BOT, "the notch's V would run off the bottom of the fin"
    assert -g > FIN_Y0 and g < FIN_Y1, "the notch is wider than the fin it is cut into"
    out.append(f"cradle notch: half-width {g:.3f} (arm's band is +-{g - FIN_ARM_CLEAR:.3f} "
               f"at x={x_out:.2f}, both signs of x), full depth above z {FIN_NOTCH_Z0}, "
               f"then closing at 45 deg to an apex at z {FIN_NOTCH_Z0 - g:.2f} -- so "
               f"nothing bridges and the fin is back under the pads by z {Z_FLANGE_FACE}")
    pads = flange_pads()
    for (py0, py1), yh in zip(pads, SERVO_HOLE_Y):
        assert py0 + 1.6 <= yh <= py1 - 1.6, (
            f"flange pad {py0:.2f}..{py1:.2f} leaves too little meat around its "
            f"Ø{M2_PILOT} pilot at y {yh:+.2f}")
        assert py1 <= SERVO_BODY_Y[0] - PAD_BODY_CLEAR + 1e-9 or \
               py0 >= SERVO_BODY_Y[1] + PAD_BODY_CLEAR - 1e-9, \
               f"flange pad {py0:.2f}..{py1:.2f} runs into the servo body"
        assert FIN_Y0 <= py0 and py1 <= FIN_Y1, (
            f"flange pad {py0:.2f}..{py1:.2f} overhangs the end of the fin "
            f"{FIN_Y0}..{FIN_Y1} -- its outboard end would print in mid-air")
        # and its ENDS must have fin above them, i.e. be outside the notch at z_pad
        gz = fin_notch_half_at(Z_FLANGE_FACE)
        assert min(abs(py0), abs(py1)) >= gz, (
            f"flange pad {py0:.2f}..{py1:.2f} reaches inside the notch, which is "
            f"still +-{gz:.2f} at z {Z_FLANGE_FACE} -- its ends would print in mid-air")
    out.append(f"flange pads {pads[0][0]:+.1f}..{pads[0][1]:+.1f} and "
               f"{pads[1][0]:+.1f}..{pads[1][1]:+.1f}, {PAD_T} mm thick hanging BELOW "
               f"z {Z_FLANGE_FACE} (so the servo's launch load is compression into "
               f"them); the notch is down to +-{fin_notch_half_at(Z_FLANGE_FACE):.2f} "
               f"there, so both pads land on fin at both ends and only their "
               f"{2*FIN_X_IN:.1f} mm middle bridges")
    for th in LOBE_THETA:
        band = ((th % 180.0) >= a1) and ((th % 180.0) <= 180.0 + a0)
        assert band, (f"screw lobe at {th} deg is inside the arm's sweep band "
                      f"{a0:.1f}..{a1:.1f} deg (mod 180)")
    out.append(f"the arm's corners sweep azimuth {a0:.1f}..{a1:.1f} deg (and its "
               f"mirror); the retaining lobes at {LOBE_THETA} deg sit outside both")
    # --- the sweep must clear the foot in AZIMUTH, not just move the tip a long
    # way.  x never changes as the half opens, so the released arm is clear of the
    # foot for all time once its trailing edge has swung past the foot's outboard
    # corner -- and that is an angle, not a distance.
    th_free = None
    for i in range(0, int(LATCH_SWEEP * 20) + 1):
        s = i / 20.0
        # the arm's material at radius r spans azimuth s +- asin(w/2 / r)
        lo = s - math.degrees(math.asin(min(1.0, (LATCH_ARM_W / 2) / r_in)))
        hi_foot = math.degrees(math.atan2(TONGUE_Y1, HOOK_X_IN))
        if lo > hi_foot:
            th_free = s
            break
    # TWO guards, not one.  The RATIO is what forced LATCH_SWEEP to 31: at
    # LATCH_ARM_W 10.50 the trailing edge needs 23.60 deg, and 0.8 * 30.0 = 24.0 left
    # 0.40 deg of the reserved 20% -- less than the trim error that reserve exists to
    # cover, so the arm could stop with its corner still inside the foot's band and
    # the halves would not separate.  The ABSOLUTE guard below is not binding today
    # (7.40 deg of daylight) and is here for the opposite failure: a ratio test passes
    # trivially if someone simply commands a much larger sweep, which buys nothing
    # because th_free does not move with it.  Neither check catches the other's case.
    assert th_free is not None, (
        f"the arm never clears the foot's azimuth band anywhere in {LATCH_SWEEP} deg")
    assert th_free < LATCH_SWEEP * 0.8, (
        f"the arm needs {th_free} deg to clear the foot's azimuth band but only "
        f"sweeps {LATCH_SWEEP}, and 20% of the sweep is reserved for trim error")
    assert LATCH_SWEEP - th_free >= 1.0, (
        f"the arm clears the foot at {th_free:.2f} deg and stops at {LATCH_SWEEP} -- "
        f"only {LATCH_SWEEP - th_free:.2f} deg of daylight, which is inside the "
        f"backlash of an MG90S gear train.  Widening LATCH_ARM_W pushes th_free out "
        f"by asin((W/2)/r_in); either give the sweep the degree back or narrow the bar")
    out.append(f"release: the arm's trailing edge clears the foot's azimuth band "
               f"(0..{math.degrees(math.atan2(TONGUE_Y1, HOOK_X_IN)):.1f} deg) after "
               f"{th_free:.1f} deg of sweep, out of {LATCH_SWEEP:.0f} -- "
               f"{LATCH_SWEEP / th_free:.2f}x margin and {LATCH_SWEEP - th_free:.2f} "
               f"deg of absolute daylight; a {LATCH_SWEEP:.0f} deg sweep "
               f"moves the arm tip "
               f"{LATCH_ARM_R * math.sin(math.radians(LATCH_SWEEP)):.1f} mm")

    # --- z stack, top down, every neighbour checked
    assert Z_HOOK_BOT < Z_LATCH_FACE == Z_ARM_BOT < Z_ARM_TOP < Z_BULK_BOT
    assert abs((Z_BULK_BOT - THRUST_PAD_DROP) - Z_ARM_TOP) < 1e-9, \
        "the foot pushes the arm UP at Z_ARM_BOT, so the pad must bear DOWN on its " \
        "TOP face -- coplanar there, and NOT coplanar with the latch face"
    assert (Z_BULK_BOT - THRUST_PAD_DROP) != Z_LATCH_FACE, \
        "pad and latch face on the same side of the arm oppose nothing"
    assert Z_SERVO_TOP < Z_ARM_BOT
    assert Z_SERVO_BOT > Z_RING_BOT
    assert LOBE_Z0 < SEAT_Z0 < SEAT_Z1 <= Z_BULK_BOT
    # the pads hang BELOW the flange face, so it is the DOWNWARD room that matters
    assert Z_FLANGE_FACE - PAD_T > Z_SERVO_BOT, "flange pads must stay above the body's foot"
    assert Z_FLANGE_FACE < Z_SERVO_TOP, "flange must sit below the body top"
    out.append(f"z stack: servo {Z_SERVO_BOT}..{Z_SERVO_TOP} | foot {Z_HOOK_BOT}.."
               f"{Z_LATCH_FACE} | arm {Z_ARM_BOT}..{Z_ARM_TOP} | thrust pad face "
               f"{Z_BULK_BOT - THRUST_PAD_DROP} | pocket ceiling {Z_STEP} | bulkhead "
               f"{Z_BULK_BOT}..{Z_BULK_TOP} | ring top {Z_RING_TOP:.4f} | shell root "
               f"{Z_SHELL_ROOT:.4f}")
    out.append("load path, closed: springs -> tongue -> FOOT pushes the arm UP at "
               f"z {Z_LATCH_FACE} -> arm's top face pushes UP into the thrust pad at "
               f"z {Z_ARM_TOP} -> bulkhead -> 2 x M2.5 into the ring's lobes -> ring "
               "-> 2 x M2.5 radial into the airframe.  The servo shaft carries "
               "friction only, in either direction.")

    # --- identical halves
    assert TONGUE_X0 > 0 and TONGUE_Y0 > 0
    out.append(f"identical halves: tongue A x {TONGUE_X0}..{TONGUE_X1} y "
               f"{TONGUE_Y0:.2f}..{TONGUE_Y1:.2f}; tongue B is its 180 deg image at "
               f"x {-TONGUE_X1}..{-TONGUE_X0} -- disjoint in x AND on the far side "
               f"of the split plane, so neither fouls the other's wall")

    # --- the joint
    assert SPIGOT_RADIAL_CLEAR > 0.1
    assert SPIGOT_LEN < MBODY_SOCKET_DEPTH
    out.append(f"joint: spigot r {R_SPIGOT} x {SPIGOT_LEN} into bore "
               f"{R_MBODY_BORE} ({SPIGOT_RADIAL_CLEAR:.4f} radial clearance), "
               f"{SPIGOT_SPARE_TRAVEL:.4f} mm spare before the stop bead -- so the "
               f"SHOULDER at z {Z_SHOULDER:.4f} is the axial datum, not the spigot end")
    assert RING_BORE < R_SPIGOT
    out.append(f"ring bore r {RING_BORE:.4f}: spigot wall "
               f"{R_SPIGOT - RING_BORE:.3f}, collar wall {R_AIRFRAME - RING_BORE:.3f}")

    # --- and what actually holds the nose in it.  Every number here is a length
    # spent in a direction, which is this project's standing failure mode, so each
    # one is checked against the surface it is measured from rather than assumed.
    floor = RETAIN_PILOT_R0 - RETAIN_PAD_R_IN
    assert floor >= 0.8, (f"only {floor:.2f} mm of floor left under the retention "
                          f"pilot -- the screw tip would break into the servo bay")
    thread = (R_SPIGOT - RETAIN_MOUTH_CS) - RETAIN_PILOT_R0
    assert thread > 4.5, f"retention pilot gives only {thread:.2f} mm of thread"
    # A screw that BOTTOMS feels tight and clamps nothing, and if it bottoms while
    # the shoulder is still off its seat it jacks the joint open.  Length is
    # measured from where the head lands, which is the airframe's OD -- NOT the
    # spigot's, and that 1.64 mm of tube wall plus clearance is exactly the sort of
    # thickness that gets dropped from this sum.
    tip_r = R_AIRFRAME - RETAIN_SCREW_LEN
    assert tip_r > RETAIN_PILOT_R0, (
        f"an M2.5 x {RETAIN_SCREW_LEN:.0f} bottoms in the retention pilot: its tip "
        f"reaches r {tip_r:.2f} against a hole floor at {RETAIN_PILOT_R0:.2f}")
    # The OTHER pair of M2.5s, on the joint the latch load actually crosses.  Same
    # failure mode, different budget: this head lands on the bulkhead's top face, so
    # the sum is disc + pilot rather than tube wall + clearance + countersink.
    bulk_budget = BULK_T + BULK_SCREW_DEPTH
    assert BULK_SCREW_LEN < bulk_budget, (
        f"an M2.5 x {BULK_SCREW_LEN:.0f} bottoms in the ring's lobe pilot: "
        f"{BULK_T} mm of disc plus {BULK_SCREW_DEPTH} of pilot is only "
        f"{bulk_budget:.1f} mm, so the screw jacks the bulkhead off SEAT_Z1 instead "
        f"of pulling it down onto it")
    assert BULK_SCREW_LEN - BULK_T > 4.0, (
        f"an M2.5 x {BULK_SCREW_LEN:.0f} leaves only {BULK_SCREW_LEN - BULK_T:.1f} mm "
        f"of thread in the lobe")
    out.append(f"bulkhead retention: 2 x M2.5 x {BULK_SCREW_LEN:.0f} down through the "
               f"disc at r {R_BULK_SCREW} into the lobes at "
               f"{LOBE_THETA[0]:.0f}/{LOBE_THETA[1]:.0f} deg -- {BULK_T} mm of disc + "
               f"{BULK_SCREW_DEPTH} of Ø{M2_5_PILOT} pilot = {bulk_budget:.1f} mm of "
               f"budget, so {BULK_SCREW_LEN - BULK_T:.1f} mm of thread and "
               f"{bulk_budget - BULK_SCREW_LEN:.1f} mm of floor left.  NOT an x 10: "
               f"it bottoms 1.5 mm early and holds the seat open")
    grip = (R_AIRFRAME - R_MBODY_BORE) + SPIGOT_RADIAL_CLEAR
    assert tip_r < R_SPIGOT - RETAIN_MOUTH_CS - 3.0, "screw is too short to grip"
    # the pilot must lie entirely within the pad's FULL-thickness band, not in the
    # 45 deg cone at its top, or it breaks out sideways
    z_full = RETAIN_PAD_Z_TOP - (RING_BORE - RETAIN_PAD_R_IN)
    assert Z_RETAIN + RETAIN_PILOT / 2 + 1.0 <= z_full, (
        f"the retention pilot's top edge at z {Z_RETAIN + RETAIN_PILOT/2:.2f} is "
        f"inside the pad's 45 deg cone, which does not reach full thickness until "
        f"z {z_full:.2f} -- the hole would break out through the ramp")
    assert Z_RETAIN - RETAIN_PILOT / 2 - 1.0 > 0.0, "pilot too close to the spigot's aft face"
    assert Z_RETAIN + RETAIN_PILOT / 2 < SPIGOT_LEN - 2.0, "pilot must stay below the shoulder"
    # and the pad must miss everything else in the bay.  Its closest point to the
    # axis in x is NOT RETAIN_PAD_R_IN -- that is a radius; the chord box cuts it
    # back to sqrt(r^2 - half_chord^2), which is the number the fins care about.
    assert RETAIN_X_MIN > FIN_X_IN + FIN_T + 1.0, (
        f"the retention pad reaches in to |x| {RETAIN_X_MIN:.2f} and the cradle fin's "
        f"outer face is at {FIN_X_IN + FIN_T:.2f}")
    assert RETAIN_X_MIN > SERVO_W / 2 + 1.0, "retention pad fouls the servo body"
    assert RETAIN_PAD_Z_TOP < LOBE_Z0, "retention pad runs into the screw lobes"
    assert RETAIN_HALF_CHORD < abs(Y_CORD_HOLE) - D_CORD_HOLE / 2, \
        "retention pad reaches into the shock cord's drop"
    out.append(f"retention: 2 x M2.5 x {RETAIN_SCREW_LEN:.0f} radial at azimuth "
               f"{RETAIN_THETA[0]:.0f}/{RETAIN_THETA[1]:.0f} deg (the seam), z "
               f"{Z_RETAIN} = {Z_RETAIN_BELOW_RIM:.4f} mm below Mbody's forward rim; "
               f"Ø{RETAIN_TUBE_CLEAR} clearance in the tube, Ø{RETAIN_PILOT} pilot "
               f"{R_SPIGOT - RETAIN_PILOT_R0:.2f} deep in the spigot with "
               f"{floor:.2f} mm of floor behind it")
    out.append(f"retention screw budget: {R_AIRFRAME - R_MBODY_BORE:.4f} tube wall + "
               f"{SPIGOT_RADIAL_CLEAR:.4f} clearance + {RETAIN_MOUTH_CS} countersink = "
               f"{grip + RETAIN_MOUTH_CS:.2f} mm spent before the thread bites, then "
               f"{R_AIRFRAME - RETAIN_SCREW_LEN - RETAIN_PILOT_R0:.2f} mm of hole "
               f"left over past the tip -- so it grips over "
               f"{(R_SPIGOT - RETAIN_MOUTH_CS) - tip_r:.2f} mm and cannot bottom")
    out.append(f"retention pad: {RING_BORE - RETAIN_PAD_R_IN:.2f} mm thick, "
               f"{2*RETAIN_HALF_CHORD:.0f} mm along the circumference, z 0.."
               f"{RETAIN_PAD_Z_TOP} -- closest point to the axis |x| "
               f"{RETAIN_X_MIN:.2f}, so it clears the cradle fins by "
               f"{RETAIN_X_MIN - FIN_X_IN - FIN_T:.2f} mm and the servo by "
               f"{RETAIN_X_MIN - SERVO_W/2:.2f} mm")

    # --- servo packaging, done the right way round
    servo_circ_r = math.hypot(SERVO_L - SERVO_SHAFT_FROM_END, SERVO_W / 2)
    assert servo_circ_r < RING_BORE
    out.append(f"servo: body {SERVO_W} x {SERVO_L} x {SERVO_H} with the shaft "
               f"{SERVO_SHAFT_FROM_END} from one end, so its worst corner is "
               f"{servo_circ_r:.2f} mm off the axis against a bore of "
               f"{RING_BORE:.2f} -- the 32.2 mm flange span is a CHORD, not a radius")

    # --- forces
    f = latch_force_per_half()
    tq = release_torque()
    tq_in = engage_torque()
    # The lever is |dy| ALONE, because the latch reaction is purely +z.  Not
    # hypot(dy, dz): see latch_force_per_half's docstring.
    arm = abs((TONGUE_Y0 + TONGUE_Y1) / 2 - Y_PIN)
    r_in, r_out = latch_bearing_r()
    assert tq < 0.5 * SERVO_STALL_NMM, "release torque must stay well under stall"
    assert tq_in < 0.5 * SERVO_STALL_NMM, (
        f"engaging costs {tq_in:.1f} N.mm against a {SERVO_STALL_NMM:.0f} N.mm stall "
        f"-- closing is the expensive direction because the arm climbs the ramp")
    out.append(f"springs: {OPEN_MOMENT:.2f} N.mm opening moment per half; the tongue "
               f"sits {arm:.4f} mm from the hinge axis IN Y, so the latch carries "
               f"{f:.4f} N per half, {2*f:.2f} N total")
    # QUOTE THE LAND, NOT THE FOOTPRINT.  The foot's top is a ramp: only the first
    # RAMP_LAND of y is flat at Z_LATCH_FACE, and the rest falls away by RAMP_DROP,
    # so on a fresh print the arm bears on that land alone.  The whole footprint --
    # 2.63 x 3.00 = 7.90 mm2 as a rectangle, 8.31 as the exact arc integral -- only
    # comes into play once the ramp has bedded in, and reporting it as the bearing
    # area understates the stress by 2.8x.  Both are quoted; the land governs.
    y_land = TONGUE_Y0 + RAMP_LAND
    a_land = (math.sqrt(ARM_CORNER_R ** 2 - y_land ** 2) - HOOK_X_IN) * RAMP_LAND
    a_full = (r_out - r_in) * (TONGUE_Y1 - TONGUE_Y0)
    out.append(f"latch bearing: the foot reaches under the arm over r "
               f"{r_in:.2f}..{r_out:.2f} = {r_out - r_in:.2f} mm of ledge across the "
               f"full {TONGUE_Y1 - TONGUE_Y0:.1f} mm of y, but only y {TONGUE_Y0:.2f}.."
               f"{y_land:.2f} is FLAT, so it bears on {a_land:.2f} mm2 at "
               f"{f / a_land:.3f} MPa as printed, easing to {a_full:.2f} mm2 at "
               f"{f / a_full:.3f} MPa once the ramp beds in")
    out.append(f"release: {tq:.1f} N.mm of friction to beat vs {SERVO_STALL_NMM:.0f} "
               f"N.mm stall = {100 * tq / SERVO_STALL_NMM:.0f} %; engaging costs "
               f"{tq_in:.1f} N.mm = {100 * tq_in / SERVO_STALL_NMM:.0f} % because it "
               f"climbs the ramp -- and the servo never carries the latch load "
               f"itself, the thrust pad does")
    out.append(f"back-drive: ramp tan {ramp_slope():.3f} vs mu {LATCH_MU} = "
               f"{LATCH_MU / ramp_slope():.2f}x margin, so the springs cannot push "
               f"the arm out and the servo can be de-powered once latched")

    # --- the root joint is NOT a joint.  See ROOT_CHAMFER.
    pin_slop = (PIN_BORE_KNUCKLE - D_PIN) / 2
    assert pin_slop < ROOT_GAP, (
        f"the knuckle has {pin_slop:.2f} mm of slop on the pin against a "
        f"{ROOT_GAP} mm root gap -- the shell's root face would land on the ring's "
        f"top face, which is not a bearing surface and is not flat to 0.05 mm")
    out.append(f"root joint: the shell root stands {ROOT_GAP} mm clear of the ring top "
               f"and stays clear, because the knuckle can only drop {pin_slop:.2f} mm "
               f"before the pin bottoms in its bore -- so ROOT_CHAMFER "
               f"({ROOT_CHAMFER}) is an edge break for the airflow, not a joint relief")

    # --- seam dowels: SWEPT, not static.  A static fit check passes on a dowel
    # that jams 3 deg into the opening, which is exactly what shipped once.
    avail = (DOWEL_BORE - DOWEL_D) / 2
    # 2 x SEAM_SETBACK: it is per half, so the seam faces stand that far apart with
    # the nose shut and the rod spends it all crossing the gap, engaging nothing.
    engage = DOWEL_LEN - DOWEL_DEPTH - 2 * SEAM_SETBACK
    assert engage > 0, (
        f"the dowel does not reach the other half: {DOWEL_LEN} mm long with "
        f"{DOWEL_DEPTH} buried in half A and {2*SEAM_SETBACK} of seam gap to cross "
        f"leaves {engage:.2f} mm of engagement")
    for z0 in DOWEL_Z:
        w, peak, out_by, floor_gap = dowel_withdrawal(z0)
        assert w < 0.0, (
            f"the dowel at z={z0} jams: it needs {avail + w:.4f} mm of bore radius "
            f"where {avail:.3f} is available, worst at {peak:.2f} deg of opening")
        assert floor_gap > 0.5, (
            f"the dowel at z={z0} comes within {floor_gap:.3f} mm of B's socket "
            f"floor -- it would set the closed position instead of the seam faces")
        out.append(f"dowel z={z0:.0f}: engages half B by "
                   f"{engage:.2f} mm and is fully "
                   f"clear of it by {out_by:.2f} deg of opening; worst skew wants "
                   f"{avail + w:.4f} mm of the {avail:.3f} mm available = "
                   f"{avail / (avail + w):.2f}x margin (at {peak:.2f} deg), and the "
                   f"tip stays {floor_gap:.2f} mm off the socket floor throughout")
    # --- and whether a PRINTED rod would do, since 4 off Ø3 x 6.5 is a silly thing
    # to have to buy.  The withdrawal margin is what decides it: the largest ACTUAL
    # diameter that still gets out is DOWEL_BORE - 2*(worst skew), and an FDM part
    # runs +0.05..+0.20 on an external diameter.
    d_max = DOWEL_BORE - 2 * max(avail + dowel_withdrawal(z0)[0] for z0 in DOWEL_Z)
    assert d_max >= DOWEL_D + 0.20, (
        f"the largest dowel that still withdraws is Ø{d_max:.4f}, which leaves only "
        f"{d_max - DOWEL_D:.4f} mm of print oversize on a nominal Ø{DOWEL_D} -- a "
        f"printed seam_pin would jam.  At DOWEL_LEN 8.0 this is Ø3.1328 and FAILS")
    out.append(f"seam pin: bought Ø{DOWEL_D} rod is nominal and preferred, but the "
               f"largest diameter that still withdraws is Ø{d_max:.4f}, so a PRINTED "
               f"pin has {d_max - DOWEL_D:.3f} mm of oversize to play with -- enough, "
               f"which is why seam_pin.py exists")

    # --- the ring's root posts: the only pin in this design that is MOULDED IN
    # rather than glued in, because the ring is the only part whose print pose puts
    # a +z pillar in free air.  See the POST_* block for why it cannot be on the
    # seam faces.  SWEPT, for the same reason as the dowels, and the sweep is over
    # ONE rotation, not two -- the ring does not move.
    post_eng = Z_RING_TOP + POST_H - Z_SHELL_ROOT
    assert post_eng > PIN_RISE, (
        f"the post engages the socket by {post_eng:.2f} mm but the hinge lifts the "
        f"root {PIN_RISE} mm on the way open -- the post would be out of the bore "
        f"before the closing skew is over, so it would guide nothing")
    p_avail = (POST_BORE - POST_D) / 2
    p_ov, p_peak, p_out_by, p_fg = post_withdrawal()
    assert p_ov < 0.0, (
        f"the root post jams: the worst skew wants {p_avail + p_ov:.4f} mm of bore "
        f"radius where {p_avail:.3f} is available, at {p_peak:.2f} deg of opening")
    assert p_fg > 0.5, (
        f"the post's top comes within {p_fg:.3f} mm of the socket floor -- it would "
        f"set the closed position instead of the root face on the ring's top")
    # THE ONE THAT MATTERS, and the reason POST_BORE is 2.70 and not 2.30: BOTH
    # SIDES OF THIS FIT ARE PRINTED.  D_PIN and DOWEL_D are bought rod at nominal,
    # so 0.15 mm/side only has to absorb one printed surface's error; here it has to
    # absorb two, and a jam at the root drives the nose SHUT against the springs.
    assert p_avail - 0.20 > PIN_RISE ** 2 / (2 * (Y_PIN - POST_Y)), (
        f"the fit must still withdraw after the post prints 0.10 over and the bore "
        f"0.10 under: {p_avail - 0.20:.4f} mm left against "
        f"{PIN_RISE ** 2 / (2 * (Y_PIN - POST_Y)):.5f} needed")
    assert POST_R_C - POST_D / 2 >= RING_BORE, (
        f"the post's shank would cantilever {RING_BORE - (POST_R_C - POST_D / 2):.4f} "
        f"mm over the ring's bore instead of standing on its top land")
    z_floor = Z_SHELL_ROOT + POST_BORE_DEPTH
    assert POST_R_C + POST_BORE / 2 <= float(prof.r_outer(z_floor)) - \
        prof.wall_normal_to_radial(WALL_MIN, z_floor), (
        f"the socket's outboard skin fails WALL_MIN at the bore's FLOOR (z "
        f"{z_floor:.2f}), which is where it binds because r_outer falls as the ogive "
        f"curves -- not at the mouth, where an earlier POST_R_C 30.15 looked fine")
    assert POST_Y - POST_BORE / 2 - SEAM_SETBACK - POST_MOUTH_CHAMFER >= WALL_MIN, (
        "the seam-side floor under the socket is thinner than one printable wall "
        "once the mouth chamfer has eaten its share")
    assert POST_MOUTH_CHAMFER <= float(prof.r_outer(Z_SHELL_ROOT)) - POST_R_C - \
        POST_BORE / 2 - prof.wall_normal_to_radial(WALL_MIN, Z_SHELL_ROOT), \
        "the mouth chamfer eats the outboard skin at the root face"
    assert POST_PAD_Y >= POST_Y + POST_BORE / 2 + WALL_MIN, \
        "the pad does not actually roof the socket"
    # THE SIGN IS STRUCTURAL, NOT COSMETIC.  The socket has to be on the seam meridian
    # the latch hook is NOT on: with the full-depth gusset the hook's weld to the shell
    # is the plane x = +r_in over the tongue's y band, and the socket would cut 0.6795
    # of that 3.0 mm at z = Z_SHELL_ROOT, the extreme fibre -- 17 % of S, and the jam
    # margin below goes from 1.22x to 1.02x.  Withdrawal does not care which side it is
    # on, because the hinge axis is parallel to X and x never enters the rotation.
    assert POST_X < 0.0 < TONGUE_X0, (
        f"the root post socket (x {POST_X:.4f}) and the latch tongue (x {TONGUE_X0:.4f}"
        f"..{TONGUE_X_WALL:.4f}) are on the SAME seam meridian: the socket would be "
        f"bored through the hook's weld at its most-stressed fibre")
    x_soc_out = abs(POST_X) + POST_BORE / 2 + POST_MOUTH_CHAMFER
    assert x_soc_out < TONGUE_X0 or POST_X * TONGUE_X0 < 0.0, \
        "the socket reaches the tongue's x band even on its own meridian"
    out.append(f"root posts: Ø{POST_D} x {POST_H} moulded on the ring's collar top at "
               f"r {POST_R_C} (x {POST_X:.4f}, y {POST_Y}), one per half at the seam "
               f"meridian, into a Ø{POST_BORE} x {POST_BORE_DEPTH} socket -- engages "
               f"{post_eng:.2f} mm, clear of the socket by {p_out_by:.2f} deg of "
               f"opening; worst skew wants {p_avail + p_ov:.4f} mm of the "
               f"{p_avail:.3f} mm available = {p_avail / (p_avail + p_ov):.2f}x (at "
               f"{p_peak:.2f} deg), top stays {p_fg:.2f} mm off the socket floor.  It "
               f"engages {p_out_by - dowel_withdrawal(DOWEL_Z[0])[2]:.1f} deg BEFORE "
               f"the first dowel, which is what makes the halves clamp onto the ring "
               f"instead of hunting for each other.  It is on the -x meridian because "
               f"+x is the hook's weld, where it would have cost 17 % of S")

    # --- capacity
    cav = prof.cavity_volume(Z_SHELL_ROOT, WALL)
    fl, fh = CHUTE_PACK_FLAT_CM3
    hl, hh = CHUTE_PACK_HIDRAG_CM3
    out.append(f"chute cavity: {cav:.1f} cm3 by cavity_volume() above the split, but "
               f"{CHUTE_VOID_CM3:.1f} cm3 of MEASURED free void above the bulkhead "
               f"face, and only {CHUTE_BAG_CM3:.1f} cm3 as the largest right cylinder "
               f"a deployment bag can use (Ø{CHUTE_BAG_D:.2f} x {CHUTE_BAG_H:.1f} mm; "
               f"{CHUTE_BAG_SOFT_CM3:.1f} if a fabric bag deforms past the "
               f"intrusions, none of which blocks more than 33.5 of 360 azimuths -- "
               f"fins, not a throat, and above z 62 the widest is a DOWEL PAD and not "
               f"the latch gusset, which has ended by then)")
    out.append(f"chute fit, {CHUTE_D_IN:.0f} in = {CHUTE_D_MM:.0f} mm: a FLAT-CUT nylon "
               f"canopy plus lines and bag is {fl:.0f}-{fh:.0f} cm3 rolled to stuffed = "
               f"{CHUTE_BAG_CM3/fh:.2f}-{CHUTE_BAG_CM3/fl:.2f}x on the bag cylinder, so "
               f"it fits.  A HIGH-DRAG 30 in (toroidal/elliptical) is a published "
               f"{hl:.0f}-{hh:.0f} cm3 = {CHUTE_BAG_CM3/hh:.2f}-{CHUTE_BAG_CM3/hl:.2f}x "
               f"-- the small end only just, the big end NOT AT ALL.  Buy flat-cut, or "
               f"measure the pack before trusting this cone")
    assert fh <= CHUTE_BAG_SOFT_CM3, (
        f"a loose-stuffed flat-cut {CHUTE_D_IN:.0f} in canopy is {fh:.0f} cm3 against a "
        f"{CHUTE_BAG_SOFT_CM3:.1f} cm3 bag cylinder -- it no longer fits even bagged")
    return out


if __name__ == "__main__":
    for ln in self_check():
        print(ln)
