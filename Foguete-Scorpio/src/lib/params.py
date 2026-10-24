"""Shared dimensions (mm) for the Estes Pro Series II Scorpio 3D printed-parts replica.

Every model imports these literals: change a value here and rerun the models.
Convention: Z is the rocket axis, +Z points forward (toward the nose), and each
printable part is modelled in its print orientation (lowest face on Z = 0).
Angles are degrees about +Z, measured from +X.

Scale source: Estes product page for kit #9733 (2 in / 51 mm body, 29 mm motor,
1/4 in rod or 1010 rail, nose cone needs >= 260 mm build height). Everything
else is measured from the reference photos and scaled to that body diameter.
"""

# --- Purchased tubes (not printed) ------------------------------------------
BODY_OD = 50.8          # 2.00 in body tube (Estes: "2 in (51 mm)")
BODY_ID = 48.5          # ASSUMED (~1.15 mm wall): verify with fit_gauge first
MOTOR_TUBE_OD = 31.0    # 29 mm motor mount tube (~1.22 in OD kraft tube)
MOTOR_TUBE_ID = 29.1
MOTOR_DIA = 29.0        # Estes E16-4 / F15-6, 29 x 114 mm
MOTOR_LEN = 114.0

# --- Fits (diametral clearances) --------------------------------------------
GLUE_FIT = 0.25         # coupler and fin-can stubs inside the body tube (glued)
SLIP_FIT = 0.45         # nose shoulder (must slide out at ejection)
MOTOR_TUBE_FIT = 0.4    # fin-can bore and male retainer bore over the motor tube

# --- Common walls -----------------------------------------------------------
STUB_WALL = 2.4         # coupler / fin-can stub wall (6 perimeters at 0.4 mm)
EDGE_CHAMFER = 0.6      # elephant-foot / lead-in chamfers on printed edges

# --- Nose cone (tangent ogive, blunted tip) ----------------------------------
NOSE_OGIVE_LEN = 216.0  # generating sharp ogive; blunting shortens it ~8.5 mm.
                        # Total nose height 247.5 mm: fits the K1C (250 mm Z) and the K1 Max
NOSE_TIP_RADIUS = 2.5
NOSE_SHOULDER_LEN = 40.0
NOSE_WALL = 2.0
NOSE_SOLID_TIP = 16.0   # solid length below the tip (cavity stops here)
NOSE_STEP_RISE = 1.5    # inner shoulder-to-ogive step starts this far above the joint
# Two shock-cord attachments, one model each:
#  - nose_cone_open: open shoulder base with a ridge-topped bar to tie the cord
#    around (the cavity stays reachable for clay nose weight)
NOSE_BAR_WIDTH = 8.0
NOSE_BAR_HEIGHT = 10.0
#  - nose_cone_hook: a bulkhead closes the shoulder base and carries a central
#    boss with a blind pilot hole (open at the bottom) for a screw hook / screw eye.
NOSE_BULKHEAD_THICKNESS = 4.0
NOSE_HOOK_PILOT = 2.8       # pilot for a ~3.5 mm (#6) screw hook in ABS; 3.2 for a 4 mm thread
NOSE_HOOK_DEPTH = 20.0      # usable thread depth from the shoulder base
NOSE_HOOK_BOSS_D = 12.0
NOSE_HOOK_BOSS_CAP = 4.0    # solid material above the hole tip
NOSE_HOOK_RIBS = 4          # gussets from the boss to the shoulder wall
NOSE_HOOK_RIB_THICKNESS = 2.0

# --- Side-door nose (same mechanism as the reference Parachute_housing/door) ----
# Housing = shoulder + a full band + one half-shell + the tip; door = the other
# half-shell. The door's top lip tucks inside the tip shell, two spring pins locate
# its floor block, and a micro servo's arm swinging up into a groove under that
# block latches it. Turning the arm down frees the door's bottom: the springs kick
# it out about the top, the door flies off and the parachute leaves sideways.
NOSE_DOOR_BAND = 12.0          # full ring above the shoulder joint, below the door
NOSE_DOOR_BAND_CHAMFER = 0.5   # band's top outer edge on the door side (door swings past it)
NOSE_DOOR_FLOOR = 10.0         # door floor block = compartment floor height above the band
NOSE_DOOR_JOINT_Z = 175.0      # door top / tip joint height at the split plane
NOSE_DOOR_JOINT_ANGLE = 50.0   # joint rises outward so the tip's door side prints unsupported
NOSE_DOOR_JOINT_GAP = 0.8      # vertical gap door top to tip (room to lift as it swings)
NOSE_DOOR_CLEARANCE = 0.2      # per side at the split faces
NOSE_DOOR_TONGUE = 4.0         # top tab height above the joint: holds ~1.4 mm inside the tip, and
                               # lets go once the spring-kicked door has swung ~32 deg
NOSE_DOOR_TONGUE_T = 1.6
NOSE_DOOR_TONGUE_W = 10.0      # tab only at the door centre, level with the hinge: a full-width
                               # lip on the inclined joint would hit the tip as the door swings
NOSE_DOOR_TONGUE_CLEARANCE = 0.6  # tab to tip shell, lets the door swing ~15 deg
NOSE_DOOR_BEAD = 4.0           # thickened band under the lip
# Ejection springs where the reference has pegs: a pin on the housing's split face
# carries each compression spring and still locates the door; the door's floor block
# holds the spring pocket. Closed, the springs push the door against the servo arm;
# released, they kick the door's bottom out.
NOSE_DOOR_SPRING_Y = 10.0      # +/- from the centre line
NOSE_DOOR_SPRING_Z = 5.0       # above the band (pin and pocket axis)
SPRING_OD_MAX = 5.0            # spring must fit the pocket...
SPRING_ID_MIN = 3.4            # ...and slide over the 3.0 mm pin (pen springs fit)
NOSE_DOOR_SPRING_POCKET_D = 5.6
NOSE_DOOR_SPRING_POCKET_DEPTH = 8.0  # closed spring length = depth + 2 x split clearance
NOSE_DOOR_PIN_D = 3.0          # pin across corners (45 deg square: prints sideways cleanly)
NOSE_DOOR_PIN_COLLAR_D = 3.8   # spring's base coils screw onto this collar
NOSE_DOOR_PIN_COLLAR_LEN = 2.5
NOSE_DOOR_PIN_TIP = 2.0        # pin tip engagement in the door's locating hole
NOSE_DOOR_PIN_HOLE_D = 3.6
NOSE_DOOR_TETHER_HOLE = 2.5    # optional thread lug so the ejected door is not lost
NOSE_DOOR_SPLIT_PLATE = 3.0    # housing plate on the split face; carries the spring pins
NOSE_DOOR_GROOVE_R = 14.7      # latch groove centre (= servo horn plane) from the axis
NOSE_DOOR_GROOVE_W = 3.4       # reference uses 4.0; 3.4 leaves 0.8 mm play per side on a 1.8 mm horn arm
NOSE_DOOR_GROOVE_H = 7.0
NOSE_DOOR_GROOVE_LEN = 30.0
NOSE_DOOR_RAMP_ANGLE = 50.0    # housing-side compartment floor slopes down toward the door
NOSE_DOOR_RAMP_T = 2.5
NOSE_DOOR_EYE_HOLE = 5.0       # parachute / shock-cord tie eye
NOSE_DOOR_CORD_HOLE = 7.0      # shock cord up from the body through the ramp
# SG90-class micro servo (also MG90S): 22.8 x 12.2 x 22.7 mm body, 32.3 mm ear span
SERVO_BODY_L = 22.8
SERVO_BODY_W = 12.2
SERVO_BODY_H = 22.7
SERVO_EAR_SPAN = 32.3
SERVO_EAR_T = 2.5
SERVO_EAR_H = 15.9             # ear underside above the servo's bottom face
SERVO_HOLE_SPACING = 27.8
SERVO_SHAFT_OFFSET = 5.9       # shaft centre from the near body end
SERVO_HORN_H = 26.7            # horn mid-plane above the servo's bottom face
SERVO_ARM = 15.0               # horn arm, shaft centre to latch tip (trim the horn to this)
SERVO_UNLOCK_ANGLE = 60.0      # arm rotation that drops it out of the groove
SERVO_CLEARANCE = 0.25
SERVO_SCREW_PILOT = 1.8        # for the servo's 2 mm self-tapping ear screws

# --- Body tube coupler --------------------------------------------------------
COUPLER_STUB_LEN = 38.0
COUPLER_BAND_LEN = 26.0

# --- Fin can -------------------------------------------------------------------
FIN_CAN_LEN = 118.0     # main body, body-tube diameter (fin housings run its full length)
FIN_CAN_STUB_LEN = 30.0 # lock ring (5 mm) + 25 mm of body-tube engagement
FIN_COUNT = 3
FIN_ANGLE0 = 0.0        # first fin; the others follow every 360 / FIN_COUNT
AFT_GUIDE_LEN = 24.0    # aft rail guide / launch lug length
ENGINE_STOP_LEDGE = 1.7     # flat thrust ledge width inside the bore
ENGINE_BLOCK_BORE = 24.0    # ejection passage through the engine block
CORD_ANCHOR_HOLE = 4.0      # aramid cord hole in the internal anchor rib
# External T-channel fin housings (as on the Estes part): fins slide in from the
# FORWARD end, riding over the body tube, and stop on the closed aft end.
FIN_HOUSING_FLOOR_R = 25.7  # channel floor plane; above the body tube (25.4) so rails clear it
FIN_HOUSING_LIP = 1.8       # lip over the rail flange (>= 1.6 mm even at the crowned edge)
FIN_HOUSING_WALL = 1.6      # side walls
FIN_HOUSING_CROWN = 0.3     # lip tops slope down outward
FIN_HOUSING_AFT_STOP = 3.0  # closed aft end of each channel

# --- Fin lock ring (twist 60 deg: notches over the housings = open, between = locked)
LOCK_RING_THICKNESS = 5.0
LOCK_RING_CLEARANCE = 0.2   # radial, ring bore to fin-can stub
LOCK_RING_NOTCH_WIDTH = 7.8 # passes the fin rail flange (7.0)
LOCK_RING_NOTCH_R = 25.6    # notch floor; the continuous inner band is below it
LOCK_RING_FAIRING_R = 27.6  # forward face outer radius (fairing cone down toward the tube)
DETENT_COUNT = 3            # flexing fingers in the ring
DETENT_GROOVES = 6          # vertical grooves on the stub, every 60 deg
DETENT_DEPTH = 0.8          # groove depth = nub height (45 deg flanks)
DETENT_BEAM_THICKNESS = 1.2 # meets the 1.2 mm FDM wall; ~1 % bending strain at full flex
DETENT_BEAM_ARC = 29.0      # finger length along the bore
DETENT_RELIEF = 0.8         # gap behind the finger (> nub interference 0.6)

# --- Fin (T-rail root that slides into a fin-can housing) ----------------------
FIN_THICKNESS = 3.0
FIN_FLANGE_WIDTH = 7.0
FIN_FLANGE_THICKNESS = 1.8
SLOT_CLEARANCE = 0.2        # per side, fin rail to housing channel
FIN_ROOT_LEN = 114.6        # = FIN_CAN_LEN - FIN_HOUSING_AFT_STOP - 0.4 axial play
# Planform from the photos, as (span from the housing top, height above aft edge).
# The concave leading edge is the R ~173 mm arc that best fits the 7 traced
# points (0.74 mm rms) from the root top through FIN_LE_MID to FIN_LE_TIP.
FIN_LE_MID = (41.5, 56.0)
FIN_LE_TIP = (83.0, 27.6)
FIN_TE_TIP_SPAN = 74.0      # span at the trailing (aft) edge

# --- Launch guides (centred between fins, same angles on coupler and fin can) --
RAIL_GUIDE_ANGLE = 60.0     # 1010 rail guide (Estes Pro Series II launch rail)
LAUNCH_LUG_ANGLE = 180.0    # 1/4 in launch rod lug
RAIL_STANDOFF = 1.2         # guide face clearance above the body surface
RAIL_NECK_WIDTH = 5.6       # 1010 slot opening is 6.5 mm (0.256 in)
RAIL_NECK_HEIGHT = 3.0      # 1010 slot lip is ~2.2 mm
RAIL_HEAD_WIDTH = 11.0      # 1010 inner channel is ~14.8 mm
RAIL_HEAD_THICKNESS = 2.6
RAIL_PAD_WIDTH = 12.0
LUG_BORE = 6.9              # 1/4 in (6.35 mm) rod + clearance
LUG_WALL = 1.6
LUG_CLEARANCE = 0.55        # bore edge to body surface

# --- Motor retainer (threaded, 45 deg flanks for support-free FDM threads) -----
THREAD_PITCH = 2.5
THREAD_DEPTH = 0.9
THREAD_CREST = 0.3          # male crest flat
THREAD_ROOT_GAP = 0.4       # male root flat
THREAD_RADIAL_CLEARANCE = 0.4
THREAD_AXIAL_CLEARANCE = 0.35   # per flank, axial
MALE_THREAD_MAJOR = 37.0
MALE_BAND_OD = 40.0         # forward band: glue face + fin-rail stop
MALE_BAND_LEN = 6.0
MALE_THREAD_LEN = 13.0
CAP_OD = 43.0
CAP_LIP = 2.4               # aft wall that retains the motor
CAP_HOLE = 24.0             # nozzle opening; lip covers the motor's aft face
CAP_THREAD_LEN = 13.6
CAP_FLUTES = 16
CAP_FLUTE_RADIUS = 1.5
CAP_FLUTE_DEPTH = 0.9

# --- Non-printed tube lengths, for the assembly preview only --------------------
LOWER_TUBE_LEN = 229.0      # ~9 in
UPPER_TUBE_LEN = 457.0      # 18 in

# --- Print colour (matches the reference photos) ---------------------------------
PRINT_COLOR = "#4F7DB3"
TUBE_COLOR = "#3A3D42"
MOTOR_TUBE_COLOR = "#B08A5A"
