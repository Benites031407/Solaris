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
NOSE_BAR_WIDTH = 8.0    # shock-cord bar across the shoulder base
NOSE_BAR_HEIGHT = 10.0

# --- Body tube coupler --------------------------------------------------------
COUPLER_STUB_LEN = 38.0
COUPLER_BAND_LEN = 26.0

# --- Fin can -------------------------------------------------------------------
FIN_CAN_LEN = 118.0     # main body, body-tube diameter
FIN_CAN_STUB_LEN = 26.0
FIN_COUNT = 3
FIN_ANGLE0 = 0.0        # first fin; the others follow every 360 / FIN_COUNT
FIN_SLOT_TOP = 115.0    # slots open at the aft face, closed (stop) here
AFT_GUIDE_LEN = 24.0    # aft rail guide / launch lug length
ENGINE_STOP_LEDGE = 1.7     # flat thrust ledge width inside the bore
ENGINE_BLOCK_BORE = 24.0    # ejection passage through the engine block
CORD_ANCHOR_HOLE = 4.0      # aramid cord hole in the internal anchor rib

# --- Fin (T-rail root that slides into the fin-can slot) -----------------------
FIN_THICKNESS = 3.0
FIN_FLANGE_WIDTH = 8.0
FIN_FLANGE_THICKNESS = 2.4
FIN_FLANGE_INNER_R = 18.4   # flange inner face radius when seated
SLOT_CLEARANCE = 0.2        # per side, fin rail to slot
FIN_ROOT_LEN = 114.6
# Planform from the photos, as (span from body surface, height above aft edge).
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
