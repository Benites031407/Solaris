"""Every number the 100 mm motor is built from, with where it came from.

DESIGN BASIS
------------
"Solid Rocket Engines - Collegiate Research" (the PAPER below), plus standard data
it does not carry: AS568 O-ring sizes and Parker gland practice, ISO 7380-1 fastener
dimensions, MMPDS-style bearing allowables for 6061-T6.  Where the paper gives a rule
the rule is quoted next to the number that satisfies it, and self_check() re-asserts
it, so an edit that breaks a paper rule fails loudly.

Sections:
  1. PROPELLANT        the paper's APCP, unchanged
  2. GRAIN             4 BATES segments
  3. NOZZLE FLOW PATH  throat, expansion, angles
  4. CASE              the tube
  5. CLOSURES          the two plugs, their bolts and their O-ring glands
  6. INTERNALS         liner, casting tubes, spacers, insulators
  7. STACK             every axial station, DERIVED -- nothing in 7 is typed in
  8. LOADS             the numbers self_check() compares against allowables

FRAME
-----
Motor axis = Z.  +Z points FORWARD (toward the payload).  z = 0 is the case's AFT
END FACE.  Azimuth theta: 0 = +X, degrees, counter-clockwise seen from forward.
Every part generator draws its part in its OWN local frame (documented in that file)
and srm_assembly.py places it; placements() there is the only place a part is moved.

UNITS: mm, MPa (= N/mm^2), N, s, kg -- unless a name says otherwise (_SI, _M, _PA).
"""

from __future__ import annotations

import math

# =============================================================================
# 1.  PROPELLANT  -- PAPER, "APCP 70/16/14" (AP / Al / HTPB)
# =============================================================================
PROP_NAME = "APCP 70/16/14 (AP/Al/HTPB)"
RHO_PROP = 1770.0e-9       # kg/mm^3   (paper: 1770 kg/m^3)
RHO_PROP_SI = 1770.0       # kg/m^3
CSTAR = 1550.0             # m/s       (paper)
GAMMA = 1.21               # -         (paper)
BURN_A = 3.5               # mm/s at 1 MPa   r = a * P^n, P in MPa   (paper)
BURN_N = 0.35              # -               (paper)
# The burn rate is the least certain number in the motor.  It must be measured
# (strand burner or a sub-scale motor) on the actual batch before this motor is
# loaded; srm_ballistics.py sweeps a x 0.8 .. 1.4 to show what an error costs.
# Combustion temperature is not needed by the ballistics (c* carries it), but
# OpenMotor wants a T/M pair; T is picked, M is solved so that c* comes out 1550.
T_FLAME_K = 3400.0
# The paper's 1770 kg/m^3 is above the ~1753 theoretical maximum for 70/16/14, and its
# 1550 m/s is a theoretical c*.  Both are kept as the PRESSURE BOUND (they overstate
# Pc).  The PERFORMANCE estimate uses what a cast grain actually delivers:
RHO_PROP_ASCAST_SI = 1718.0   # kg/m^3, 98 % of 1753 (vacuum-cast, typical voids)
CSTAR_EFF = 0.95              # delivered / theoretical c*, small APCP motors 0.93 - 0.97
# Temperature sensitivity of the burn rate, sigma_p = d ln(r) / dT at constant P.
# Typical AP/HTPB 0.1 - 0.3 %/K; the upper-middle value, since the batch is unmeasured.
SIGMA_P = 0.002            # 1/K
T_REF_C = 20.0             # the burn-rate law's reference grain temperature
T_GRAIN_MAX_C = 40.0       # hottest grain the motor may be fired at (sun on a pad)
# Erosive burning.  The aft core runs G/(rho r0) above Mukunda-Paul's threshold of 35
# at ignition, so srm_ballistics.py carries an erosive term; these are its constants.
EROSIVE_MU = 8.0e-5        # Pa s, chamber-gas viscosity (Mukunda-Paul Re0, L-R alpha)
LR_BETA = 53.0             # Lenoir-Robillard beta
LR_CP, LR_PR, LR_CS = 1900.0, 0.7, 1250.0      # gas cp, Prandtl, propellant c (SI)
LR_TS_K, LR_TI_K = 1000.0, 293.0               # burning-surface and initial temperature

# =============================================================================
# 2.  GRAIN  -- 4 x BATES, both ends burning
# =============================================================================
# PAPER, 98 mm column of the design table: grain OD ~93, core 28-35, segment
# 150-155 mm, 4-6 segments, Kn 180-250, 3-10 MPa.  Our case ID is 92 (100 x 4 tube),
# so the grain OD is what is left inside a 1.5 mm liner and a 0.8 mm casting tube.
N_GRAINS = 4
GRAIN_OD = 86.8            # = casting-tube ID; the grain is cast into the tube
GRAIN_CORE = 34.0          # core / OD = 0.39     (paper: 0.3 - 0.4)
# PAPER: neutral segment length L = (3D + d) / 2
GRAIN_L = (3.0 * GRAIN_OD + GRAIN_CORE) / 2.0      # 147.2

# =============================================================================
# 3.  NOZZLE FLOW PATH
# =============================================================================
THROAT_D = 23.0            # Kn0 = 248 with the grains above (paper: 180 - 250)
EXIT_D = 52.0              # expansion 5.11  (paper: 4 - 8 for APCP)
# The graphite's exit edge is broken 0.2 x 45 deg (a knife edge chips).  EXIT_D stays
# the nominal cone/face intersection; the break shaves the last 0.27 mm of cone, so
# the smallest diameter the exit plane actually sees is 51.85 (eps 5.08).
EXIT_BREAK = 0.2
CONV_HALF_DEG = 35.0       # paper: 30 - 45
DIV_HALF_DEG = 15.0        # paper: 12 - 15; 15 deg keeps ~98.3 % of ideal thrust
THROAT_LAND = 4.0          # cylindrical throat length; takes the first erosion
R_THROAT_UP = 1.0 * THROAT_D / 2.0     # blend, convergent -> land
R_THROAT_DN = 0.5 * THROAT_D / 2.0     # blend, land -> divergent
NOZZLE_EFF = 0.95          # thrust-coefficient efficiency, on top of divergence
AMBIENT_PA = 101325.0

# =============================================================================
# 4.  CASE  -- 6061-T6 drawn tube, 100.0 OD x 4.0 wall
# =============================================================================
CASE_OD = 100.0
CASE_WALL = 4.0
CASE_ID = CASE_OD - 2.0 * CASE_WALL          # 92.0, honed in the seal zones
# O-ring lead-in on the bore, both ends.  Parker 10.1.2: 15-20 deg, and its radial
# depth must exceed the free ring's protrusion past the plug OD (0.80 mm here).
CASE_END_CHAMFER = 1.1     # radial
CASE_END_CHAMFER_DEG = 20.0   # from the axis -> 3.0 mm long
# The O-rings are dragged over the bolt holes on the way in: every hole gets a
# 0.5 x 45 deg break on the BORE side so its edge cannot nibble them (Parker 10.1.2.2).
# The break is taken off the bearing length: the wall bears on 4.0 - 0.5 = 3.5 mm.
CASE_HOLE_BORE_BREAK = 0.5
# Drawn tube is bought at +/-10 % wall.  The case is UT-mapped at the bolt rows and
# rejected below CASE_WALL_MIN; the honed bore is not allowed past CASE_BORE_MAX.  The joint
# is checked at both extremes, not just at nominal.
CASE_WALL_MIN = 3.80
CASE_BORE_MAX = 92.10

# 6061-T6.  PAPER quotes yield ~270 MPa -- a typical value.  Sizing uses guaranteed
# minimums instead, the lower of drawn tube (ASTM B210 / MMPDS: Fty 35, Ftu 42 ksi)
# and extruded tube (EN 755-2: Rp0.2 240, Rm 260), since a 100 x 4 tube may be either.
AL_FTY = 240.0             # MPa
AL_FTU = 260.0             # MPa
AL_FSU = 165.0             # MPa, ultimate shear (MMPDS extruded, 24 ksi)
AL_FBRY = 386.0            # MPa, bearing yield at e/D = 2.0 (MMPDS 56 ksi)
AL_E = 68900.0             # MPa
AL_RHO = 2.70e-6           # kg/mm^3

SS_FTY = 205.0             # MPa, 304 annealed minimum (paper quotes ~290 typical)
SS_FTU = 515.0             # MPa, 304 annealed minimum (ASTM A479)
SS_E = 193000.0            # MPa
SS_NU = 0.29
SS_RHO = 8.00e-6           # kg/mm^3

# Isomolded fine-grain graphite for the throat insert: ISO-63, TTK-4 or IG-43 class
# (rho >= 1.78, flexural >= 50 MPa).  Not extruded rod.  Minimum-of-grades values.
GR_E = 10000.0             # MPa
GR_NU = 0.20
GR_FCU = 90.0              # MPa, compressive strength
GR_RHO = 1.80e-6           # kg/mm^3

MEOP = 7.0                 # MPa, maximum expected operating pressure
FOS_YIELD = 2.0            # PAPER: FoS 2.0 on yield is standard practice
BURST_MIN_X_MEOP = 1.5     # PAPER: metallic casings, burst >= 1.5 x MEOP
PROOF_X_MEOP = 1.5         # hydrostatic proof, before the first fire

# =============================================================================
# 5.  CLOSURES
# =============================================================================
# PAPER: radial bolts scale well to 75 - 150 mm.  18 per end: the case wall bears on
# the thread root over 3.5 mm (the bore-side break is lost), and the joint must hold
# FoS 2 on bearing at the thinnest wall and largest bore the case is accepted with.
# 16 did that only at nominal wall.
N_BOLTS = 18
BOLT_THETA0 = 0.0          # first bolt azimuth, deg
# Bolt 0 is clocked 0.8 deg off the even pattern.  A closure put in one position off
# (or a case turned end for end: the pattern is chiral) then misses a hole by 0.64 mm
# at the plug OD, against 0.2 mm of float in the 6.4 hole, so the screws will not
# start: a match-drilled pair can only go together one way.
BOLT_OFFSET0 = 0.8         # deg
BOLT_EDGE = 13.0           # case end -> bolt-row centre: e/D 2.03 on the 6.4 hole
                           # (paper 1.5 - 2 d; MMPDS Fbry is tabulated at e/D 2.0)
BOLT_D = 6.0               # M6 x 1
BOLT_PITCH = 1.0
BOLT_MINOR_D = 4.917       # M6x1 d1 (internal minor); shear area uses d3 below
BOLT_D3 = 4.773            # M6x1 external minor diameter, the shear plane
CASE_HOLE_D = 6.4          # ISO 273 fine clearance for M6
BOLT_TAP_DRILL = 5.0

# ISO 7380-1 button head, property class 10.9
BOLT_HEAD_DK = 10.5
BOLT_HEAD_K = 3.3
BOLT_HEAD_S = 4.0          # hex socket across flats
BOLT_HEAD_T = 2.3          # socket depth
BOLT_FU = 1040.0           # MPa, 10.9 ultimate
BOLT_FY = 940.0            # MPa, 10.9 yield
BOLT_PROOF_LOAD = 16700.0  # N, ISO 898-1 M6 10.9 proof load (20.1 mm^2 x 830 MPa)
BOLT_RHO = 7.85e-6
BOLT_SPEC = "ISO 7380-1 M6 x L, property class 010.9, black oxide or zinc flake"
# Radial bolts carry shear, so preload is not structural: it only stops fretting.
# Each end has its own torque.  Into the 304 holder with nickel anti-seize (K down to
# 0.11), 6 N m would put 9.1 kN on 6 mm of annealed thread, a mean shear above its
# yield; 3.0-3.5 N m keeps it under 0.75 of yield and still clamps the head.
BOLT_TORQUE_FWD_NM = (4.0, 6.0)   # into the 6061 closure, Loctite 243
BOLT_TORQUE_AFT_NM = (3.0, 3.5)   # into the 304 holder, nickel anti-seize
THREAD_SHEAR_YIELD_FRAC = 0.75    # mean thread shear at top torque / shear yield, max
# The tapped threads are checked against the tension the torque can put in the screw
# at the lowest nut factor a lubricated thread gives (F = T / (K d), K 0.11).
BOLT_K_MIN = 0.11
# Internal-thread shear area per mm of engagement, M6x1 6H/6g (FED-STD-H28:
# pi Ds,min (1/2n + 0.57735 (Ds,min - En,max)), Ds,min 5.794, En,max 5.500).  The
# first thread under the counterbore / chamfer is not counted.
THREAD_AS_PER_MM = 12.19   # mm^2 / mm
THREAD_LOST = 1.0          # mm of engagement not counted
BOLT_THREADLOCK = ("Loctite 243 into the 6061 closure; nickel anti-seize on the threads only "
                   "(head face dry) into the 304 holder")

# The forward closure is aluminium and wants 2 d of engagement; the nozzle holder
# is steel, where 1 d is the usual rule, and has only 14.2 mm of wall between its
# seal land and the graphite's bore -- 2 mm of which must stay behind the drill
# point.  So the two ends get different lengths.
BOLT_L_FWD = 16.0          # engages CASE_WALL..16 -> 12.0 mm in 6061 (2.0 d)
BOLT_L_AFT = 10.0          # engages 6.0 mm in 304 (1.0 d; steel into steel)
THREAD_OVER = 2.0          # full thread beyond the bolt tip
DRILL_OVER = 2.0           # drill beyond the last full thread (2 pitch: bottoming tap)
MIN_WALL_UNDER_HOLE = 2.0  # material left between a tapped hole's drill point and a bore

# Both plugs share one outside geometry.
PLUG_L = 38.0              # length inside the case
# Seal land.  Bore 92.000 +0.030/0, land 91.94 0/-0.02 -> diametral gap 0.06-0.11.
# The case breathes 0.115 mm diametral at MEOP, so the worst extrusion gap is 0.225 mm
# against Parker Fig 3-2's 0.47 mm for 90A (0.25 mm for 75A: too close).  A looser
# plug was the first draft; it was over the 75A line.
PLUG_CLEAR = 0.03          # radial, nominal
PLUG_OD = CASE_ID - 2.0 * PLUG_CLEAR          # 91.94
PLUG_NOSE_CHAMFER = 1.0    # 30 deg lead on the plug's inboard edge
FLANGE_T = 6.0             # shoulder that butts the case end
FLANGE_OD = CASE_OD

# --- case O-ring glands: 2 per plug, grooves in the plug (piston gland) --------
# Parker Design Chart 4-2 (static radial, 0.139" CS, no back-up to 1500 psi), sized
# for a 92.00 bore.  If the honed bore A comes out different: groove = A - 5.67 and
# land = A - 0.06.  -237 is the only 0.139" size that is stretched on this groove
# and under Parker's 5 % (-236: 5.9 % worst case; -238: loose, sags into the bore).
ORING_CS = 3.53            # 0.139 +/- 0.004"
ORING_ID = 85.32           # AS568-237, 3.359 +/- 0.024"
ORING_DASH = "AS568-237"
ORING_GROOVE_D = CASE_ID - 5.67                 # 86.33 0/-0.04
GLAND_DEPTH = (CASE_ID - ORING_GROOVE_D) / 2.0  # bore -> groove bottom, 2.835
GROOVE_W = 4.80            # +0.08/0, no back-up ring
GROOVE_R_BOTTOM = 0.4      # +/-0.1
GROOVE_EDGE_R = 0.10       # groove top edges, R 0.08 - 0.13 (Parker: break, don't leave sharp)
# groove centres, measured INBOARD from the case end.  Bolt holes span 9.8-16.2;
# the outer groove starts 3.0 past them, 4.0 land between grooves, 5.2 to the nose.
GROOVE_1_Z = 21.6
GROOVE_2_Z = 30.4
ORING_COMPOUND = "FKM 90A (Parker V0709-90 or equal)"   # NBR is rated 4 in HCl gas
# tolerance bands the self-check stacks up (mm): (minus, plus)
TOL_BORE = (0.0, 0.030)
SEAL_A_MAX = CASE_BORE_MAX - TOL_BORE[1]   # 92.070: largest clean-up A, zone stays <= CASE_BORE_MAX
TOL_LAND = (-0.02, 0.0)
TOL_GROOVE = (-0.04, 0.0)
TOL_GROOVE_W = (0.0, 0.08)
TOL_CS = (-0.10, 0.10)
TOL_ID_237 = (-0.61, 0.61)
# Parker Fig 3-2, max diametral extrusion gap at 1015 psi (7.0 MPa), no back-ups,
# digitised from the handbook's vector curves: 70A 0.19, 75A ~0.25, 80A 0.31, 90A 0.47
EXTRUSION_GAP_90A = 0.47
EXTRUSION_GAP_75A = 0.25
# ... and for 90A at 1500 psi (10.3 MPa), the hydrostatic proof pressure
EXTRUSION_GAP_90A_PROOF = 0.357
LUBE = "Parker Super O-Lube or DC-55, thin film"

# --- nozzle-insert O-ring: groove in the holder bore (rod / female gland) ------
# Parker Design Table 4-2 female row 2-230: tube (insert) B 2.500 +0/-.002",
# groove A-1 2.722 +.002/-0, throat (holder bore) D 2.503 +.001/-0.  The insert OD
# is set BY the gland: a 62 mm insert fits no standard row (-229 stretches 3.5 %).
INSERT_ORING_CS = 3.53
INSERT_ORING_ID = 63.09    # AS568-230, 2.484 +/- 0.020"
INSERT_ORING_DASH = "AS568-230"
INSERT_OD = 63.50          # 2.500", graphite
INSERT_BORE_D = 63.58      # holder bore, 2.503"
INSERT_CLEAR = (INSERT_BORE_D - INSERT_OD) / 2.0   # radial 0.04; >= 0.08 diametral
INSERT_GROOVE_D = 69.14    # 2.722", cut in the holder bore
INSERT_GLAND_DEPTH = (INSERT_GROOVE_D - INSERT_OD) / 2.0   # 2.82
INSERT_GROOVE_W = 4.80
INSERT_GROOVE_Z = -3.0     # motor z of the groove centre: in the flange, 13 mm aft
                           # of the throat, where graphite and steel are both thick
# 90A, not 75A: at MEOP the gland gap opens by the holder's growth AND the graphite's
# shrink under the pressure on its OD (insert_gap_growth()), which puts a 75A ring
# past its extrusion line.  This ring sees the hottest steel in the motor; it is a
# consumable.  FFKM (Kalrez / Chemraz) is the upgrade if it comes out hard or cut.
INSERT_ORING_COMPOUND = "FKM 90A (Parker V0709-90); sacrificial, replace after every firing"
# Graphite (~5 um/m/K) heats long before the steel does.  The design review's 1-D
# transient conduction model gives 0.20 - 0.215 mm of free differential growth on
# diameter; 0.22 carries it.  Against a minimum clearance of 0.08 the insert briefly
# bears on the holder.  self_check() turns that interference into a contact pressure;
# radial compression is the benign direction for a brittle insert.
INSERT_DIFF_GROWTH = 0.22
TOL_INSERT_OD = (-0.05, 0.0)
TOL_INSERT_BORE = (0.0, 0.025)
TOL_INSERT_GROOVE = (0.0, 0.05)
TOL_ID_230 = (-0.51, 0.51)
INSERT_LEAD_IN = 3.0       # 20 deg x 3.0 axial on the insert's aft (leading) OD edge
HOLDER_BORE_LEAD_IN = 1.8  # 20 deg x 1.8 axial at the holder bore's forward entry
CONV_ENTRY_D = 52.0        # convergent diameter at the insert's forward face

# --- forward closure ---------------------------------------------------------
# Solid: no lightening pocket and no pressure port.  The forward face is one flat
# surface to the axis, the thrust face for a horizontal static-test load cell (a
# 50 x 26 pocket saved 137 g but left only an r 25 .. 50 annulus to push on).  The
# motor is fired without a chamber transducer; the proof fills and bleeds through
# the proof dummy's port (below).
PULLER_N = 2
PULLER_R = 37.5
PULLER_TAP_DRILL = 5.0     # M6
PULLER_DEPTH = 10.0

# --- nozzle holder (304 stainless: PAPER, steel not aluminium behind graphite) --
HOLDER_LIP_T = 6.0         # aft retaining lip
HOLDER_LIP_STEP = 1.0      # lip bore starts this far outside the exit radius
HOLDER_LIP_BORE_DEG = 20.0 # lip bore opens at this half-angle, > divergence
HOLDER_AFT_WALL = 4.0      # wall around the graphite aft of the flange
# Root fillet where the holder bore meets the lip face: stress relief at the lip's
# bending root.  The insert's 20 deg lead-in clears it by 0.31 mm; R 1.0 would leave
# only 0.12, so 0.8 it is.
HOLDER_SEAT_R = 0.8
# two M6 puller threads in the flange's aft face, axial, between bolts: the holder
# is drawn out by a bridge and two screws instead of being levered (MIT cracked a
# graphite insert in an "energetic" extraction)
HOLDER_PULLER_R = 41.0
HOLDER_PULLER_DEPTH = 10.0

# --- nozzle cap / igniter retainer (LDPE, consumable) ---------------------------
# Commercial practice: the pyrogen igniter goes in through the throat and up the
# core; this push-in cap keeps debris out, holds the igniter leads through a hole
# and blows out at ignition.  It seats on the holder's aft face.
CAP_PLUG_L = 10.0          # conical plug inside the graphite divergent
CAP_FLANGE_T = 1.5
CAP_FLANGE_OD = 66.0
CAP_LEAD_HOLE = 3.0
CAP_WALL = 1.2

# --- hydrostatic proof dummy (304, stands in for the graphite insert) ------------
# The proof must load the joints, the holder lip and every seal as a firing does, so
# the holder is proofed with a steel dummy of the insert's outside geometry sitting in
# the insert's own gland: never with the graphite, which would be wetted (and one
# found cracked at proof is scrap anyway).  Its closed aft end carries the motor's
# only port: filled and bled with the motor vertical, aft end up, where the port is
# the cavity's highest point.
PROOF_CUP_D = 40.0         # bore, open forward (to the chamber)
PROOF_BOTTOM_T = 15.0      # closed aft end
PORT_TAP_DRILL = 8.73      # 1/8-27 NPT fill / bleed port (11/32" drill)
PORT_CSK_D = 11.0          # 90 deg thread-entry countersink: clears the NPT major at the face
PORT_THREAD_DEPTH = 10.0
PROOF_PASSAGE_D = 6.0      # fill / bleed port -> cup
# Aft end up, the dummy's and the holder's forward faces are one flat ceiling at z 38
# out to the bore: tilting drives bubbles OUT to the bore corner, away from the port.
# So fill from the bottom, through a dip tube down the port and passage resting on the
# forward closure's face (end cut at 45 deg), and let the water rise level.
PROOF_DIP_TUBE_OD = 4.0    # PE / nylon, through the passage with an annulus for the air
PROOF_DIP_TUBE_L = 800.0   # rests on item 6's face and stands clear above the port
PROOF_RELIEF_MPA = 11.0    # relief valve on the pump, set before the test
PROOF_STEPS_MPA = (3.5, 7.0, 10.5)
PROOF_HOLD_S = 300.0       # at each step
PROOF_DECAY_MAX = 0.02     # pressure decay allowed over a hold, fraction
PROOF_SET_MAX = 0.02       # permanent OD change allowed at any station, mm

# --- igniter (not modelled: a consumable, sized here so it is written down) ------
# A pyrogen or BKNO3 charge in a paper tube, pushed up through the throat to the
# forward grain's core so the whole core is swept by the ignition gas, both leads out
# through the cap's CAP_LEAD_HOLE.  Dual-bridge e-match; the firing box must deliver
# >= 2x the match's all-fire current.
IGNITER_CHARGE_G = 3.0     # BKNO3 granules or pyrogen: ~0.5 g per 100 cm^3 free volume, x2
IGNITER_TUBE_D = 10.0      # max OD: slides up the 23 mm throat and 34 mm core
IGNITER_TUBE_L_MAX = 40.0
IGNITION_DELAY_MAX_S = 0.5 # acceptance: fire signal -> 90 % of the initial Pc
HANGFIRE_WAIT_S = 60.0     # minimum wait before approaching a misfire (5 min advised)

# =============================================================================
# 6.  INTERNALS
# =============================================================================
LINER_OD = 91.6            # paper-phenolic
LINER_ID = 88.6
TUBE_OD = 88.4             # kraft casting tube
TUBE_ID = GRAIN_OD         # 86.8
SPACER_OD = TUBE_OD        # phenolic ring between segments
SPACER_ID = 86.0           # covers only 0.4 mm of each grain face
SPACER_T = 3.0
N_SPACERS = N_GRAINS + 1   # aft, between each pair, forward: both ends burn
# Axial take-up.  A closed-cell silicone sponge ring at the forward end of the stack
# takes the grain and spacer tolerance and keeps the segments from rattling.  The
# stack (4 grains +/-0.10, 5 spacers +/-0.02) is +/-0.50 worst case, so the space
# left for the ring is 3.0 +/-0.5 and a 4.8 sheet sits at 27 - 48 % compression
# (silicone sponge: 25 - 50 %).  Drawn at its nominal installed thickness.  At
# assembly the gap is MEASURED (cavity - stack); the procedure in the README picks
# the sheet from it.
TOL_GRAIN_L = 0.10
TOL_SPACER_T = 0.02
TAKEUP_T = 3.0             # installed, nominal
TAKEUP_FREE_T = 4.8        # as cut (3/16" = 4.76 sheet); 3.2 or 6.4 sheet for off-nominal gaps
TAKEUP_OD = TUBE_OD
TAKEUP_ID = 80.0
FWD_INSUL_T = 3.0          # EPDM disc on the forward closure face
FWD_INSUL_OD = 91.8        # caps the liner end AND the liner/case annulus
NOZ_INSUL_T = 5.0          # phenolic washer over the holder's forward face
NOZ_INSUL_OD = 91.8
# its bore continues the convergent cone from the graphite's entry diameter
# The liner is cut SHORT of the cavity so it never carries the closure load and never
# stops the take-up from compressing: it bears on the nozzle insulator and floats at
# the forward end (float >= 0.30 by depth gauge at assembly: SRM100-000 sheet 3).
LINER_FLOAT = 0.5

# =============================================================================
# 7.  STACK -- derived.  Aft to forward.
# =============================================================================
Z_CASE_AFT = 0.0
Z_HOLDER_FACE = Z_CASE_AFT + PLUG_L                  # holder's inboard face
Z_NOZ_INSUL_FWD = Z_HOLDER_FACE + NOZ_INSUL_T
Z_LINER_AFT = Z_NOZ_INSUL_FWD
STACK_L = N_SPACERS * SPACER_T + N_GRAINS * GRAIN_L  # spacers + grains, in the liner
TOL_STACK = N_GRAINS * TOL_GRAIN_L + N_SPACERS * TOL_SPACER_T      # worst case, +/-
Z_FWD_INSUL_AFT = Z_LINER_AFT + STACK_L + TAKEUP_T   # take-up bears on the EPDM disc
LINER_L = STACK_L + TAKEUP_T - LINER_FLOAT
Z_LINER_FWD = Z_LINER_AFT + LINER_L
Z_FWD_INSUL_FWD = Z_FWD_INSUL_AFT + FWD_INSUL_T
Z_FWD_PLUG_FACE = Z_FWD_INSUL_FWD                    # forward closure's inboard face
CASE_L = Z_FWD_PLUG_FACE + PLUG_L
Z_CASE_FWD = CASE_L


def nozzle_stations() -> dict:
    """The graphite flow path in MOTOR z, forward to aft.  Built from the throat out:
    the forward face is fixed at Z_HOLDER_FACE with CONV_ENTRY_D, the convergent runs
    at CONV_HALF_DEG into the upstream blend, then the land, the downstream blend and
    the divergent at DIV_HALF_DEG out to EXIT_D.  Tangent points are exact."""
    rt = THROAT_D / 2.0
    a, b = math.radians(CONV_HALF_DEG), math.radians(DIV_HALF_DEG)
    r_up = rt + R_THROAT_UP * (1.0 - math.cos(a))          # convergent meets the blend
    z_fwd = Z_HOLDER_FACE
    z_up = z_fwd - (CONV_ENTRY_D / 2.0 - r_up) / math.tan(a)
    z_land_fwd = z_up - R_THROAT_UP * math.sin(a)
    z_land_aft = z_land_fwd - THROAT_LAND
    r_dn = rt + R_THROAT_DN * (1.0 - math.cos(b))           # blend meets the divergent
    z_dn = z_land_aft - R_THROAT_DN * math.sin(b)
    z_exit = z_dn - (EXIT_D / 2.0 - r_dn) / math.tan(b)
    return {"z_fwd": z_fwd, "r_entry": CONV_ENTRY_D / 2.0, "z_up": z_up, "r_up": r_up,
            "z_land_fwd": z_land_fwd, "z_land_aft": z_land_aft, "r_throat": rt,
            "z_dn": z_dn, "r_dn": r_dn, "z_exit": z_exit, "r_exit": EXIT_D / 2.0,
            "c_up": (rt + R_THROAT_UP, z_land_fwd), "c_dn": (rt + R_THROAT_DN, z_land_aft)}


def z_nozzle_exit() -> float:
    return nozzle_stations()["z_exit"]


def grain_z(i: int) -> float:
    """Aft face of grain i (0 = aftmost)."""
    return Z_LINER_AFT + SPACER_T + i * (GRAIN_L + SPACER_T)


def spacer_z(i: int) -> float:
    """Aft face of spacer i (0 = aftmost, N_SPACERS-1 = forwardmost)."""
    return Z_LINER_AFT + i * (GRAIN_L + SPACER_T)


def takeup_z() -> float:
    """Aft face of the take-up ring: right on top of the forwardmost spacer."""
    return Z_LINER_AFT + STACK_L


def bolt_z_aft() -> float:
    return Z_CASE_AFT + BOLT_EDGE


def bolt_z_fwd() -> float:
    return Z_CASE_FWD - BOLT_EDGE


def bolt_thetas() -> list[float]:
    return [BOLT_THETA0 + i * 360.0 / N_BOLTS + (BOLT_OFFSET0 if i == 0 else 0.0)
            for i in range(N_BOLTS)]


def bolt_pitch_min_deg() -> float:
    th = bolt_thetas()
    return min((th[(i + 1) % N_BOLTS] - th[i]) % 360.0 for i in range(N_BOLTS))


def puller_thetas() -> list[float]:
    # half-way between bolts, opposite each other (N_BOLTS even), clear of bolt 0
    return [BOLT_THETA0 + 180.0 / N_BOLTS + i * 360.0 / PULLER_N for i in range(PULLER_N)]


# =============================================================================
# 8.  LOADS
# =============================================================================
def bore_area() -> float:
    return math.pi / 4.0 * CASE_ID ** 2


def closure_load(p: float = MEOP) -> float:
    return p * bore_area()


def hoop_stress(p: float = MEOP) -> float:
    # PAPER: t = P r / sigma  ->  sigma = P r / t, taken at the mean radius
    return p * (CASE_ID + CASE_WALL) / 2.0 / CASE_WALL


def bore_growth(p: float = MEOP, nu: float = 0.33) -> float:
    """Diametral growth of the case bore under p (Lame, thick wall, open-ended so no
    axial stress: the conservative case for the seal gap)."""
    ri, ro = CASE_ID / 2.0, CASE_OD / 2.0
    s_theta = p * (ro * ro + ri * ri) / (ro * ro - ri * ri)
    return 2.0 * ri * (s_theta + nu * p) / AL_E


def bolt_load(p: float = MEOP, bore: float = CASE_ID) -> float:
    return p * math.pi / 4.0 * bore ** 2 / N_BOLTS


def thread_strip_load(engagement: float, tau_u: float) -> float:
    """Load that strips a tapped M6 hole of this engagement in a material of
    ultimate shear tau_u (internal threads shear at the screw's major diameter)."""
    return tau_u * THREAD_AS_PER_MM * (engagement - THREAD_LOST)


def insert_gap_growth(p: float = MEOP, graphite: bool = True) -> float:
    """How much the insert gland's diametral gap opens under p (Lame, both parts):
    the holder bore grows under the pressure behind the ring (c = plug OD: the
    flange is bigger, so this over-reads), and the graphite shrinks under the same
    pressure on its OD with the divergent's bore, where the flow is supersonic and
    the pressure low, taken as unloaded (the conservative case).  graphite=False is
    the proof test, where a steel dummy sits in the gland and its shrink is nil."""
    a, c = INSERT_BORE_D / 2.0, PLUG_OD / 2.0
    grow = 2.0 * a * p / SS_E * ((c * c + a * a) / (c * c - a * a) + SS_NU)
    if not graphite:
        return grow
    st = nozzle_stations()
    ri = st["r_dn"] + (st["z_dn"] - INSERT_GROOVE_Z) * math.tan(math.radians(DIV_HALF_DEG))
    b = INSERT_OD / 2.0
    shrink = 2.0 * b * p / GR_E * ((b * b + ri * ri) / (b * b - ri * ri) - GR_NU)
    return grow + shrink


def lip_bending(force: float) -> float:
    """Bending stress at the root of the holder's aft lip under an axial load spread
    uniformly over the seat annulus, treating the lip as a cantilever ring plate of
    thickness HOLDER_LIP_T rooted at the holder bore (a conservative strip model:
    it ignores the hoop stiffness that a real annular plate has)."""
    r_i = EXIT_D / 2.0 + HOLDER_LIP_STEP
    r_o = INSERT_OD / 2.0 - INSERT_LEAD_IN * math.tan(math.radians(20.0))
    r_c = 2.0 / 3.0 * (r_o ** 3 - r_i ** 3) / (r_o ** 2 - r_i ** 2)   # load centroid
    arm = INSERT_BORE_D / 2.0 - r_c
    return 6.0 * force * arm / (2.0 * math.pi * INSERT_BORE_D / 2.0 * HOLDER_LIP_T ** 2)


def failure_order() -> dict:
    """Ultimate pressure of each mode, MPa.  Which goes first decides how the motor
    fails if the burn rate is badly wrong."""
    a_bore = bore_area()
    tau_u = 0.62 * BOLT_FU
    return {
        "barrel hoop burst": 2.0 * CASE_WALL * AL_FTU / (CASE_ID + CASE_WALL),
        "bolt shear": N_BOLTS * tau_u * math.pi / 4.0 * BOLT_D3 ** 2 / a_bore,
        "case tear-out": N_BOLTS * AL_FSU * 2.0 * (BOLT_EDGE - CASE_HOLE_D / 2.0) * CASE_WALL / a_bore,
        "case net tension": AL_FTU * (math.pi / 4.0 * (CASE_OD ** 2 - CASE_ID ** 2)
                                      - N_BOLTS * CASE_HOLE_D * CASE_WALL) / a_bore,
    }


def insert_contact(delta_d: float) -> tuple[float, float, float]:
    """Graphite insert pressed by a diametral interference delta_d into the holder
    (Lame, both thick cylinders, at the throat section).  Returns the contact
    pressure, the graphite's hoop stress at its bore, and the steel's at its bore."""
    if delta_d <= 0.0:
        return 0.0, 0.0, 0.0
    a, b, c = THROAT_D / 2.0, INSERT_OD / 2.0, PLUG_OD / 2.0
    k_out = ((c * c + b * b) / (c * c - b * b) + SS_NU) / SS_E
    k_in = ((b * b + a * a) / (b * b - a * a) - GR_NU) / GR_E
    p = (delta_d / 2.0) / (b * (k_out + k_in))
    s_gr = -2.0 * p * b * b / (b * b - a * a)
    s_ss = p * (c * c + b * b) / (c * c - b * b)
    return p, s_gr, s_ss


def insert_thrust(p: float = MEOP) -> float:
    """Aft load on the graphite: chamber pressure over everything inside the O-ring
    on its OD, less the throat.  The divergent's pressure recovery is ignored."""
    return p * math.pi / 4.0 * (INSERT_OD ** 2 - THROAT_D ** 2)


def seat_area() -> float:
    """Flat contact between the insert's aft face and the holder's lip: from the
    lip bore out to where the insert's 20 deg lead-in chamfer starts."""
    r_in = EXIT_D / 2.0 + HOLDER_LIP_STEP
    r_out = INSERT_OD / 2.0 - INSERT_LEAD_IN * math.tan(math.radians(20.0))
    return math.pi * (r_out ** 2 - r_in ** 2)


def throat_area() -> float:
    return math.pi / 4.0 * THROAT_D ** 2


def expansion_ratio() -> float:
    return (EXIT_D / THROAT_D) ** 2


def grain_burn_area(x: float = 0.0) -> float:
    """One segment's burning area after regression x (core + both ends)."""
    d = GRAIN_CORE + 2.0 * x
    L = GRAIN_L - 2.0 * x
    if d >= GRAIN_OD or L <= 0.0:
        return 0.0
    return math.pi * d * L + 2.0 * math.pi / 4.0 * (GRAIN_OD ** 2 - d ** 2)


def kn(x: float = 0.0) -> float:
    return N_GRAINS * grain_burn_area(x) / throat_area()


def web() -> float:
    return min((GRAIN_OD - GRAIN_CORE) / 2.0, GRAIN_L / 2.0)


def pc_equilibrium(kn_: float, a_mult: float = 1.0) -> float:
    """PAPER: Pc = (Kn a rho c*)^(1/(1-n)), returned in MPa."""
    a_si = a_mult * BURN_A * 1e-3 / (1e6 ** BURN_N)
    return (kn_ * a_si * RHO_PROP_SI * CSTAR) ** (1.0 / (1.0 - BURN_N)) / 1e6


def prop_mass() -> float:
    return N_GRAINS * math.pi / 4.0 * (GRAIN_OD ** 2 - GRAIN_CORE ** 2) * GRAIN_L * RHO_PROP


# =============================================================================
def self_check() -> None:
    """Re-assert every relationship the geometry and the paper's rules lean on."""
    fails = []

    def ck(cond, ok, bad):
        ok_s, bad_s = str(ok), str(bad)
        if cond:
            print(f"  ok   {ok_s}")
        else:
            fails.append(bad_s)
            print(f"  FAIL {bad_s}")

    print("srm_params.self_check()")
    print("-- grain and ballistics (paper rules)")
    r = GRAIN_CORE / GRAIN_OD
    ck(0.3 <= r <= 0.4, f"core/OD {r:.3f} in 0.3-0.4", f"core/OD {r:.3f} outside 0.3-0.4")
    kn0, knmax = kn(0.0), max(kn(i * web() / 400.0) for i in range(400))
    ck(180.0 <= kn0 <= 250.0, f"Kn0 {kn0:.1f} in 180-250", f"Kn0 {kn0:.1f} outside 180-250")
    p0, pmax = pc_equilibrium(kn0), pc_equilibrium(knmax)
    ck(3.0 <= p0 and pmax <= 10.0, f"Pc {p0:.2f} .. {pmax:.2f} MPa inside 3-10",
       f"Pc {p0:.2f} .. {pmax:.2f} MPa leaves 3-10")
    ck(pmax * 1.3 <= MEOP, f"peak Pc {pmax:.2f} MPa x 1.3 = {pmax * 1.3:.2f} <= MEOP {MEOP}",
       f"MEOP {MEOP} does not cover peak Pc {pmax:.2f} with 30 % margin")
    hot = math.exp(SIGMA_P * (T_GRAIN_MAX_C - T_REF_C)) ** (1.0 / (1.0 - BURN_N))
    ck(pmax * hot * 1.3 <= MEOP, f"... with the grain at {T_GRAIN_MAX_C:.0f} C (sigma_p {SIGMA_P * 100:.1f} %/K, "
       f"Pc x {hot:.3f}): {pmax * hot * 1.3:.2f} <= MEOP  (erosive burning: srm_ballistics.py)",
       f"hot-grain peak {pmax * hot:.2f} MPa x 1.3 exceeds MEOP")
    ap_at = (math.pi / 4.0 * GRAIN_CORE ** 2) / throat_area()
    ck(ap_at > 2.0, f"port/throat {ap_at:.2f} > 2.0", f"port/throat {ap_at:.2f} <= 2.0")
    ld = N_GRAINS * GRAIN_L / GRAIN_OD
    ck(ld < 8.0, f"propellant L/D {ld:.2f} < 8", f"propellant L/D {ld:.2f} >= 8")
    eps = expansion_ratio()
    ck(4.0 <= eps <= 8.0, f"expansion {eps:.2f} in 4-8", f"expansion {eps:.2f} outside 4-8")
    ck(30.0 <= CONV_HALF_DEG <= 45.0 and 12.0 <= DIV_HALF_DEG <= 15.0,
       f"cone angles {CONV_HALF_DEG:.0f}/{DIV_HALF_DEG:.0f} deg in 30-45 / 12-15",
       "cone angles outside the paper's ranges")

    print("-- case (paper: t = P r / (Fty / FoS), burst >= 1.5 MEOP)")
    t_req = MEOP * (CASE_ID / 2.0) / (AL_FTY / FOS_YIELD)
    ck(CASE_WALL >= t_req, f"wall {CASE_WALL} >= required {t_req:.2f} mm",
       f"wall {CASE_WALL} < required {t_req:.2f} mm")
    fos = AL_FTY / hoop_stress()
    ck(fos >= FOS_YIELD, f"hoop {hoop_stress():.1f} MPa, FoS {fos:.2f} on yield",
       f"hoop FoS {fos:.2f} < {FOS_YIELD}")
    p_burst = AL_FTU * CASE_WALL / ((CASE_ID + CASE_WALL) / 2.0)
    ck(p_burst >= BURST_MIN_X_MEOP * MEOP, f"tube burst ~{p_burst:.1f} MPa >= 1.5 MEOP",
       f"tube burst {p_burst:.1f} MPa < 1.5 MEOP")

    print(f"-- bolted joint at MEOP (radial bolts in single shear, {N_BOLTS} per end)")
    F = bolt_load()
    ck(BOLT_EDGE / CASE_HOLE_D >= 2.0 - 1e-9, f"edge distance e/D {BOLT_EDGE / CASE_HOLE_D:.2f} on the hole",
       f"edge distance e/D {BOLT_EDGE / CASE_HOLE_D:.2f} < 2.0")
    # ISO 7380 screws this short are threaded to the head, so the case wall bears on
    # thread: the minor diameter is the honest bearing width, and the bore-side break
    # comes off the bearing length.
    t_brg = CASE_WALL - CASE_HOLE_BORE_BREAK
    t_brg_min = CASE_WALL_MIN - CASE_HOLE_BORE_BREAK
    brg3 = F / (BOLT_D3 * t_brg)
    ck(AL_FBRY / brg3 >= FOS_YIELD, f"case bearing on d3 x {t_brg:.1f} {brg3:.0f} MPa, FoS {AL_FBRY / brg3:.2f} on Fbry",
       f"case bearing on d3 FoS {AL_FBRY / brg3:.2f} < {FOS_YIELD}")
    brg3_min = bolt_load(MEOP, CASE_BORE_MAX) / (BOLT_D3 * t_brg_min)
    ck(AL_FBRY / brg3_min >= FOS_YIELD,
       f"... at the thinnest accepted wall {CASE_WALL_MIN} and bore {CASE_BORE_MAX}: {brg3_min:.0f} MPa, "
       f"FoS {AL_FBRY / brg3_min:.2f}", f"min-wall bearing FoS {AL_FBRY / brg3_min:.2f} < {FOS_YIELD}")
    brg = F / (BOLT_D * t_brg)
    ck(0.9 * AL_FBRY / brg >= FOS_YIELD,
       f"case bearing on d {brg:.0f} MPa, FoS {0.9 * AL_FBRY / brg:.2f} on 0.9 Fbry (greased/wet pin)",
       f"case bearing on d FoS {0.9 * AL_FBRY / brg:.2f} < {FOS_YIELD}")
    shear_out = F / (2.0 * (BOLT_EDGE - CASE_HOLE_D / 2.0) * CASE_WALL)
    ck(AL_FTY / math.sqrt(3.0) / shear_out >= FOS_YIELD,
       f"case shear-out {shear_out:.1f} MPa, FoS {AL_FTY / math.sqrt(3) / shear_out:.2f} on shear yield",
       "case shear-out FoS below 2")
    tau = F / (math.pi / 4.0 * BOLT_D3 ** 2)
    ck(0.6 * BOLT_FU / tau >= FOS_YIELD, f"bolt shear {tau:.0f} MPa, FoS {0.6 * BOLT_FU / tau:.2f} on ultimate",
       f"bolt shear FoS {0.6 * BOLT_FU / tau:.2f} < 2")
    net = math.pi / 4.0 * (CASE_OD ** 2 - CASE_ID ** 2) - N_BOLTS * CASE_HOLE_D * CASE_WALL
    ck(AL_FTY / (closure_load() / net) >= FOS_YIELD,
       f"net section {closure_load() / net:.1f} MPa, FoS {AL_FTY / (closure_load() / net):.2f}",
       "net-section FoS below 2")
    half = math.radians(bolt_pitch_min_deg()) / 2.0
    pitch = (CASE_ID + CASE_WALL) * math.sin(half)            # centre-to-centre chord
    ck(pitch >= 2.5 * CASE_HOLE_D, f"closest bolt pitch {pitch:.2f} mm (the {BOLT_OFFSET0} deg keyed hole) on the "
       f"mid-wall circle >= 2.5 hole dia", f"bolt pitch {pitch:.2f} mm too tight")
    head_gap = CASE_OD * math.sin(half) - BOLT_HEAD_DK
    ck(head_gap >= 4.0, f"{head_gap:.2f} mm between the closest button heads (hex key and socket clearance)",
       f"button heads only {head_gap:.2f} mm apart")
    miss = math.radians(BOLT_OFFSET0) * PLUG_OD / 2.0
    ck(miss > 2.0 * (CASE_HOLE_D - BOLT_D) / 2.0, f"a closure clocked one hole off misses by {miss:.2f} mm, "
       f"> 2 x the {(CASE_HOLE_D - BOLT_D) / 2.0:.1f} mm hole float: it only goes together one way",
       f"keying offset {miss:.2f} mm is inside the hole float")
    p_pr = PROOF_X_MEOP * MEOP
    brg3_proof = bolt_load(p_pr) / (BOLT_D3 * t_brg)
    ck(brg3_proof < AL_FTY, f"proof {p_pr:.1f} MPa: bearing on d3 {brg3_proof:.0f} MPa < Fty {AL_FTY:.0f} (nominal wall)",
       f"proof bearing {brg3_proof:.0f} MPa >= Fty at nominal wall")
    brg3_proof_min = bolt_load(p_pr, CASE_BORE_MAX) / (BOLT_D3 * t_brg_min)
    ck(brg3_proof_min < AL_FBRY / 1.25, f"proof at the thinnest wall: {brg3_proof_min:.0f} MPa < Fbry / 1.25 = "
       f"{AL_FBRY / 1.25:.0f} (holes are gauged before and after)",
       f"proof bearing at min wall {brg3_proof_min:.0f} MPa over Fbry / 1.25")
    fo = failure_order()
    order = ", ".join(f"{k} {v:.1f}" for k, v in sorted(fo.items(), key=lambda kv: kv[1]))
    print(f"  info ultimate pressures, MPa, weakest first: {order}")
    ck(min(fo.values()) >= 3.0 * MEOP, f"nothing fails below {min(fo.values()):.1f} MPa = "
       f"{min(fo.values()) / MEOP:.1f} x MEOP", "an ultimate mode sits below 3 x MEOP")

    print("-- thread depths vs the material behind them")
    eng_f = BOLT_L_FWD - CASE_WALL - PLUG_CLEAR
    eng_a = BOLT_L_AFT - CASE_WALL - PLUG_CLEAR
    ck(eng_f >= 2.0 * BOLT_D - 0.1, f"forward engagement {eng_f:.2f} mm in 6061 (~2 d)",
       f"forward engagement {eng_f:.2f} < 2 d")
    ck(eng_a >= 1.0 * BOLT_D - 0.1, f"aft engagement {eng_a:.2f} mm in 304 (~1 d)",
       f"aft engagement {eng_a:.2f} < 1 d")
    # tapped threads must out-last the screw: stripping >= the screw's proof load, and
    # >= 1.5 x the most tension the top torque can put in it on a lubricated thread;
    # and that tension must not yield the tapped thread (mean shear vs 0.577 Fty)
    for where, eng, tau_u, fty, torque in (
            ("304 holder", eng_a, 0.6 * SS_FTU, SS_FTY, BOLT_TORQUE_AFT_NM),
            ("6061 closure", eng_f, AL_FSU, AL_FTY, BOLT_TORQUE_FWD_NM)):
        f_torque = torque[1] * 1e3 / (BOLT_K_MIN * BOLT_D)
        strip = thread_strip_load(eng, tau_u)
        ck(strip >= BOLT_PROOF_LOAD and strip >= 1.5 * f_torque,
           f"{where} thread strips at {strip / 1e3:.1f} kN: > screw proof load {BOLT_PROOF_LOAD / 1e3:.1f} kN and "
           f"{strip / f_torque:.2f} x the {f_torque / 1e3:.2f} kN of {torque[1]:.1f} N m at K {BOLT_K_MIN}",
           f"{where} thread strips at {strip / 1e3:.1f} kN, before the screw")
        tau = f_torque / (THREAD_AS_PER_MM * (eng - THREAD_LOST))
        tau_y = 0.577 * fty
        ck(tau <= THREAD_SHEAR_YIELD_FRAC * tau_y,
           f"{where} thread shear at {torque[1]:.1f} N m {tau:.0f} MPa = {tau / tau_y:.2f} x shear yield {tau_y:.0f}",
           f"{where} thread shear at {torque[1]:.1f} N m {tau:.0f} MPa = {tau / tau_y:.2f} x shear yield "
           f"(> {THREAD_SHEAR_YIELD_FRAC})")
    tip = BOLT_TAP_DRILL / 2.0 / math.tan(math.radians(59.0))
    aft_hole_bottom = PLUG_OD / 2.0 - (eng_a + THREAD_OVER + DRILL_OVER) - tip
    wall = aft_hole_bottom - INSERT_BORE_D / 2.0
    ck(wall >= MIN_WALL_UNDER_HOLE,
       f"aft tapped hole leaves {wall:.2f} mm of steel over the insert bore",
       f"aft tapped hole leaves only {wall:.2f} mm over the insert bore (< {MIN_WALL_UNDER_HOLE})")
    fwd_hole_bottom = PLUG_OD / 2.0 - (eng_f + THREAD_OVER + DRILL_OVER) - tip
    # the forward closure is solid: the 18 radial holes converge, so the metal that
    # matters is between neighbouring holes where they end (closest pair: hole 0 keyed)
    th = sorted(bolt_thetas())
    dth = min((b - a) % 360.0 for a, b in zip(th, th[1:] + th[:1]))
    lig = 2.0 * fwd_hole_bottom * math.sin(math.radians(dth / 2.0)) - BOLT_TAP_DRILL
    ck(lig >= MIN_WALL_UNDER_HOLE,
       f"forward tapped holes end at r {fwd_hole_bottom:.2f} in solid metal, {lig:.2f} mm apart "
       f"(closest pair, {dth:.1f} deg)", f"forward tapped holes run together: {lig:.2f} mm apart")

    print("-- case O-ring glands, tolerance extremes (Parker Chart 4-2)")
    bore = (CASE_ID + TOL_BORE[0], CASE_ID + TOL_BORE[1])
    land = (PLUG_OD + TOL_LAND[0], PLUG_OD + TOL_LAND[1])
    grv = (ORING_GROOVE_D + TOL_GROOVE[0], ORING_GROOVE_D + TOL_GROOVE[1])
    cs = (ORING_CS + TOL_CS[0], ORING_CS + TOL_CS[1])
    idr = (ORING_ID + TOL_ID_237[0], ORING_ID + TOL_ID_237[1])
    gl = ((bore[0] - grv[1]) / 2.0, (bore[1] - grv[0]) / 2.0)
    sq = ((cs[0] - gl[1]) / cs[0], (cs[1] - gl[0]) / cs[1])
    ck(0.15 <= sq[0] and sq[1] <= 0.25, f"squeeze {sq[0] * 100:.1f} - {sq[1] * 100:.1f} % (nominal "
       f"{100 * (ORING_CS - GLAND_DEPTH) / ORING_CS:.1f})", f"squeeze {sq[0] * 100:.1f} - {sq[1] * 100:.1f} % leaves 15-25")
    st = (grv[0] / idr[1] - 1.0, grv[1] / idr[0] - 1.0)
    ck(0.0 < st[0] and st[1] <= 0.05, f"stretch {st[0] * 100:.2f} - {st[1] * 100:.2f} % on groove {ORING_GROOVE_D:.2f}",
       f"stretch {st[0] * 100:.2f} - {st[1] * 100:.2f} % leaves 0-5")
    fill = (math.pi / 4.0 * cs[1] ** 2) / (gl[0] * (GROOVE_W + TOL_GROOVE_W[0]))
    ck(fill <= 0.85, f"gland fill {fill * 100:.1f} % max", f"gland fill {fill * 100:.1f} % > 85")
    gap = bore[1] - land[0] + bore_growth()
    ck(1.5 * gap <= EXTRUSION_GAP_90A,
       f"extrusion gap at MEOP {gap:.3f} mm incl. {bore_growth():.3f} breathing; 90A limit "
       f"{EXTRUSION_GAP_90A} (x{EXTRUSION_GAP_90A / gap:.2f})",
       f"extrusion gap {gap:.3f} mm too close to the 90A limit {EXTRUSION_GAP_90A}")
    gap_pr = bore[1] - land[0] + PROOF_X_MEOP * bore_growth()
    ck(gap_pr <= EXTRUSION_GAP_90A_PROOF,
       f"extrusion gap at proof {gap_pr:.3f} mm vs the 90A limit at 1500 psi {EXTRUSION_GAP_90A_PROOF} "
       f"(x{EXTRUSION_GAP_90A_PROOF / gap_pr:.2f}): no back-up rings", f"proof extrusion gap {gap_pr:.3f} mm "
       f"over the 90A limit {EXTRUSION_GAP_90A_PROOF} at proof")
    ck(GROOVE_2_Z + GROOVE_W / 2.0 <= PLUG_L - 5.0 + 1e-9
       and GROOVE_1_Z - GROOVE_W / 2.0 >= BOLT_EDGE + CASE_HOLE_D / 2.0 + 3.0 - 1e-9
       and (GROOVE_2_Z - GROOVE_1_Z) - GROOVE_W >= 4.0 - 1e-9,
       "grooves: >= 3 mm past the bolt holes, >= 4 mm land, >= 5 mm to the plug nose",
       "grooves collide with the bolt row, each other, or the plug nose")
    y = (grv[1] + 2.0 * cs[1] - CASE_ID) / 2.0      # free ring OD past the bore, worst case
    ck(CASE_END_CHAMFER > y, f"bore lead-in {CASE_END_CHAMFER} radial > ring protrusion {y:.2f}",
       f"bore lead-in {CASE_END_CHAMFER} does not cover the ring's {y:.2f} protrusion")

    print("-- nozzle-insert O-ring, rod gland, tolerance extremes (Parker Table 4-2 row 2-230)")
    b = (INSERT_OD + TOL_INSERT_OD[0], INSERT_OD + TOL_INSERT_OD[1])
    d = (INSERT_BORE_D + TOL_INSERT_BORE[0], INSERT_BORE_D + TOL_INSERT_BORE[1])
    a = (INSERT_GROOVE_D + TOL_INSERT_GROOVE[0], INSERT_GROOVE_D + TOL_INSERT_GROOVE[1])
    idi = (INSERT_ORING_ID + TOL_ID_230[0], INSERT_ORING_ID + TOL_ID_230[1])
    gl = ((a[0] - b[1]) / 2.0, (a[1] - b[0]) / 2.0)
    sq = ((cs[0] - gl[1]) / cs[0], (cs[1] - gl[0]) / cs[1])
    ck(0.15 <= sq[0] and sq[1] <= 0.25, f"squeeze {sq[0] * 100:.1f} - {sq[1] * 100:.1f} %",
       f"insert squeeze {sq[0] * 100:.1f} - {sq[1] * 100:.1f} % leaves 15-25")
    st_max = b[1] / idi[0] - 1.0
    ck(st_max <= 0.02, f"stretch on the insert {st_max * 100:.2f} % max (rod gland <= 2 %)",
       f"stretch on the insert {st_max * 100:.2f} % > 2 %")
    odc = (1.0 - a[1] / (idi[0] + 2 * cs[0]), 1.0 - a[0] / (idi[1] + 2 * cs[1]))
    ck(0.0 < odc[0] and odc[1] <= 0.03, f"ring OD compressed {odc[0] * 100:.2f} - {odc[1] * 100:.2f} % into the groove",
       f"ring OD compression {odc[0] * 100:.2f} - {odc[1] * 100:.2f} % leaves 0-3")
    clr = (d[0] - b[1], d[1] - b[0])
    ck(clr[0] >= 0.08 - 1e-9, f"insert clearance {clr[0]:.3f} - {clr[1]:.3f} mm diametral (>= 0.08 for graphite growth)",
       f"insert clearance {clr[0]:.3f} mm < 0.08")
    dil = insert_gap_growth()
    gap = clr[1] + dil
    ck(1.5 * gap <= EXTRUSION_GAP_90A,
       f"insert extrusion gap at MEOP {gap:.3f} mm incl. {dil:.3f} dilation (holder grows, graphite shrinks); "
       f"90A limit {EXTRUSION_GAP_90A} (x{EXTRUSION_GAP_90A / gap:.2f})",
       f"insert extrusion gap {gap:.3f} mm too close to the 90A limit")
    gap_pr = clr[1] + insert_gap_growth(PROOF_X_MEOP * MEOP, graphite=False)   # the dummy is steel
    ck(gap_pr <= EXTRUSION_GAP_90A_PROOF,
       f"insert gland at proof, on the 304 dummy: gap {gap_pr:.3f} mm vs {EXTRUSION_GAP_90A_PROOF} at 1500 psi",
       f"insert gland gap at proof {gap_pr:.3f} mm over the limit")
    fill = (math.pi / 4.0 * cs[1] ** 2) / (gl[0] * INSERT_GROOVE_W)
    ck(fill <= 0.85, f"insert gland fill {fill * 100:.1f} % max", f"insert gland fill {fill * 100:.1f} % > 85")
    pc, s_gr, s_ss = insert_contact(INSERT_DIFF_GROWTH - clr[0])
    ck(abs(s_gr) * FOS_YIELD <= GR_FCU and s_ss * FOS_YIELD <= SS_FTY,
       f"transient insert interference {INSERT_DIFF_GROWTH - clr[0]:.2f} mm -> contact {pc:.1f} MPa, graphite "
       f"bore hoop {s_gr:.0f} MPa (FoS {GR_FCU / abs(s_gr):.1f} on crush), holder hoop {s_ss:.0f} MPa",
       f"transient insert interference loads graphite {s_gr:.0f} / steel {s_ss:.0f} MPa")
    f_ins, a_seat = insert_thrust(), seat_area()
    ck(GR_FCU / (f_ins / a_seat) >= FOS_YIELD,
       f"insert on the lip: {f_ins / 1e3:.1f} kN over {a_seat:.0f} mm^2 = {f_ins / a_seat:.0f} MPa, "
       f"FoS {GR_FCU * a_seat / f_ins:.1f} on graphite crush",
       f"insert seat bearing {f_ins / a_seat:.0f} MPa too high for graphite")
    tau_lip = f_ins / (math.pi * INSERT_BORE_D * HOLDER_LIP_T)
    ck(SS_FTY / math.sqrt(3.0) / tau_lip >= FOS_YIELD,
       f"holder lip shear {tau_lip:.0f} MPa, FoS {SS_FTY / math.sqrt(3) / tau_lip:.1f} on 304 shear yield",
       f"holder lip shear FoS {SS_FTY / math.sqrt(3) / tau_lip:.1f} < 2")
    s_lip = lip_bending(f_ins)
    ck(SS_FTY / s_lip >= FOS_YIELD, f"holder lip bending at its root {s_lip:.0f} MPa, FoS {SS_FTY / s_lip:.2f} on yield",
       f"holder lip bending FoS {SS_FTY / s_lip:.2f} < 2")
    # at proof the steel dummy is closed: the whole gland area pushes on the lip
    f_pr = PROOF_X_MEOP * MEOP * math.pi / 4.0 * INSERT_OD ** 2
    s_lip_pr, tau_lip_pr = lip_bending(f_pr), f_pr / (math.pi * INSERT_BORE_D * HOLDER_LIP_T)
    ck(s_lip_pr * 1.25 <= SS_FTY and SS_FTY / math.sqrt(3.0) / tau_lip_pr >= FOS_YIELD,
       f"proof on the dummy: {f_pr / 1e3:.1f} kN on the lip, bending {s_lip_pr:.0f} MPa (x{SS_FTY / s_lip_pr:.2f} to "
       f"yield), shear {tau_lip_pr:.1f} MPa (FoS {SS_FTY / math.sqrt(3) / tau_lip_pr:.2f})",
       f"proof load {f_pr / 1e3:.1f} kN overloads the lip")
    # the dummy's closed end, a simply supported plate on the seat, uniform load over the
    # whole seat radius (over-reads: only the cup bore is loaded directly)
    a_pl = EXIT_D / 2.0 + HOLDER_LIP_STEP
    s_pl = 3.0 * (3.0 + SS_NU) * PROOF_X_MEOP * MEOP * a_pl ** 2 / (8.0 * PROOF_BOTTOM_T ** 2)
    ck(s_pl * FOS_YIELD <= SS_FTY, f"proof dummy end plate {PROOF_BOTTOM_T:.0f} thick: {s_pl:.0f} MPa, "
       f"FoS {SS_FTY / s_pl:.1f}", f"proof dummy end plate {s_pl:.0f} MPa too high")
    # the proof fill: dip tube through the dummy's passage, resting on the closure face
    ann = (PROOF_PASSAGE_D - PROOF_DIP_TUBE_OD) / 2.0
    stick = PROOF_DIP_TUBE_L - (Z_FWD_PLUG_FACE - nozzle_stations()["z_exit"])
    ck(ann >= 0.75 and stick >= 80.0,
       f"proof dip tube {PROOF_DIP_TUBE_OD:.0f} x {PROOF_DIP_TUBE_L:.0f}: {ann:.1f} mm air annulus in the "
       f"passage, {stick:.0f} mm above the port resting on item 6", "proof dip tube does not fit or reach")
    # the insert's lead-in must clear the root fillet at the seat
    r_ch = INSERT_OD / 2.0 - INSERT_LEAD_IN * math.tan(math.radians(20.0))
    clr_fil = (INSERT_BORE_D / 2.0 - HOLDER_SEAT_R - r_ch) * math.cos(math.radians(20.0))
    ck(clr_fil >= 0.2, f"lip root fillet R{HOLDER_SEAT_R}: the insert's lead-in clears it by {clr_fil:.2f} mm",
       f"lip root fillet R{HOLDER_SEAT_R} is only {clr_fil:.2f} mm off the insert's lead-in")
    ck(abs(INSERT_GROOVE_Z - bolt_z_aft()) > BOLT_TAP_DRILL / 2.0 + INSERT_GROOVE_W / 2.0 + 3.0,
       f"insert groove at z {INSERT_GROOVE_Z} is clear of the aft tapped holes at z {bolt_z_aft()}",
       "insert groove runs into the aft tapped holes")

    print("-- stack")
    ck(abs(CASE_L - (2 * PLUG_L + NOZ_INSUL_T + FWD_INSUL_T + STACK_L + TAKEUP_T)) < 1e-9,
       f"case length {CASE_L:.1f} = plugs + insulators + stack + take-up", "stack does not close")
    c_lo = 1.0 - (TAKEUP_T + TOL_STACK) / TAKEUP_FREE_T
    c_hi = 1.0 - (TAKEUP_T - TOL_STACK) / TAKEUP_FREE_T
    ck(0.25 <= c_lo and c_hi <= 0.5,
       f"take-up ring {TAKEUP_FREE_T} free: {100 * (1 - TAKEUP_T / TAKEUP_FREE_T):.1f} % compressed nominal, "
       f"{100 * c_lo:.1f} - {100 * c_hi:.1f} % over the +/-{TOL_STACK:.2f} stack",
       f"take-up ring compression {100 * c_lo:.1f} - {100 * c_hi:.1f} % leaves 25-50 %")
    ck(LINER_FLOAT >= 0.3 and Z_LINER_FWD < Z_FWD_INSUL_AFT,
       f"liner floats {LINER_FLOAT} mm short of the forward insulator: it carries no axial load",
       "liner is not short of the forward insulator")
    ck(LINER_ID > TUBE_OD and CASE_ID > LINER_OD,
       f"radial fits: bore {CASE_ID} > liner {LINER_OD} / {LINER_ID} > tube {TUBE_OD}",
       "radial fits interfere")

    print(f"-- {len(fails)} failure(s)")
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    self_check()
    print(f"\ncase {CASE_OD} x {CASE_WALL} x {CASE_L:.1f} mm; propellant {prop_mass():.3f} kg; "
          f"Kn {kn(0):.0f}; expansion {expansion_ratio():.2f}")
