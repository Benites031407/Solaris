"""Dimensions (mm) for the Helios side-door nose: the Scorpio side-door nose, resized
to replace ../cone.stl on the 65.52 mm Helios airframe.

Frame (same as cone.stl and the clamshell nose): Z is the rocket axis, z = 0 is the
aft face of the shoulder, +Z points to the tip. The housing is modelled in its print
orientation (shoulder on the bed); the door is printed standing on its floor block.
Angles are degrees about +Z from +X. The door is on +X, the split plane is x = 0.

Interface numbers are measured off ../cone.stl and ../Mbody.stl (trimesh sections) and
agree with _nose_simple/nose_params.py.
"""

# --- Airframe interface (measured) ------------------------------------------------
BODY_OD = 65.52          # Mbody OD at its forward rim (r 32.758)
SHOULDER_R = 31.1207     # cone.stl spigot radius; Mbody's socket bore is r 31.2845
SHOULDER_LEN = 26.2069   # spigot length: its top face lands on Mbody's forward rim
MBODY_BORE_R = 31.2845   # for the fit check only
EDGE_CHAMFER = 0.6       # lead-in at the shoulder's bottom edge
SEAT_R_OUT = 32.0        # the shoulder face is flat out to here (it seats on the rim from r 31.28),
                         # then rises 45 deg to the skirt: a 0.88 mm ledge prints, a 1.64 mm one sags

# --- Outer shape: cone.stl's profile -----------------------------------------------
# A cylindrical skirt above the rim, then a secant ogive (a circular arc that meets
# the skirt with a 4.3 deg kink) to the tip. Fitted to 97 sections of cone.stl with
# the arc ending at its sharp tip: 0.07 mm rms, 0.14 mm worst.
OGIVE_Z0 = 54.284        # skirt / ogive junction
OGIVE_RHO = 1077.484     # arc radius
SHARP_APEX_Z = 248.966   # cone.stl's tip
NOSE_TIP_RADIUS = 1.5    # blunted for printing; the tip ends ~4.4 mm lower than cone.stl's
NOSE_WALL = 2.0
NOSE_SOLID_TIP = 16.0    # solid length below the tip (cavity stops here)
NOSE_STEP_RISE = 1.5     # inner shoulder-to-skirt step starts this far above the rim

# --- Retention: two radial M2.5 x 8 self-tappers through the airframe ----------------
# Same station and pad as the clamshell nose (_nose_simple): 13.21 mm below Mbody's
# rim, 90 deg either side of the shock-cord hole, so a tube already drilled for the
# clamshell takes this nose too.
RETAIN_Z = 13.0
RETAIN_AZ = (150.0, 330.0)   # cord hole azimuth +/- 90
RETAIN_PAD_R_IN = 23.20      # pad inner face (the bore is r 29.12)
RETAIN_PAD_HALF_CHORD = 5.5
RETAIN_PAD_Z_FULL = 15.48    # full thickness from the bed to here, then a 45 deg cone out to the bore
RETAIN_PILOT = 2.10          # blind, for an M2.5 self-tapper
RETAIN_PILOT_R0 = 24.20      # pilot bottom: 1.0 mm of floor left inside it
RETAIN_MOUTH_CS = 1.0        # 45 deg countersink at the shoulder OD, Ø2.1 -> Ø4.1

# --- Side-door mechanism (as on the Scorpio nose) ------------------------------------
# Housing = shoulder + a full band + one half-shell + the tip; door = the other
# half-shell. The door's top tab tucks inside the tip shell, two spring pins locate
# its floor block, and a micro servo's arm swinging up into a groove under that
# block latches it. Turning the arm down frees the door's bottom: the springs kick
# it out about the top, the door flies off and the parachute leaves sideways.
NOSE_DOOR_BAND = 12.0          # full ring above the rim, below the door
NOSE_DOOR_BAND_CHAMFER = 0.5   # band's top outer edge on the door side (door swings past it)
NOSE_DOOR_FLOOR = 10.0         # door floor block = compartment floor height above the band
NOSE_DOOR_JOINT_Z = 175.0      # door top / tip joint height at the split plane
NOSE_DOOR_JOINT_ANGLE = 50.0   # joint rises outward so the tip's door side prints unsupported
NOSE_DOOR_JOINT_GAP = 0.8      # vertical gap door top to tip (room to lift as it swings)
NOSE_DOOR_CLEARANCE = 0.2      # per side at the split faces
NOSE_DOOR_TONGUE = 4.0         # top tab height above the joint
NOSE_DOOR_TONGUE_T = 1.6
NOSE_DOOR_TONGUE_W = 10.0      # tab only at the door centre, level with the hinge
NOSE_DOOR_TONGUE_CLEARANCE = 0.6
NOSE_DOOR_BEAD = 4.0           # thickened band under the tab
# Ejection springs (0.5 x 5 x 20 mm bought): pins on the housing's split face carry
# them and locate the door; the door's floor block holds the pockets. The pockets are
# 3 mm deeper than on the Scorpio (the bigger nose has room), so the springs close to
# 11.4 mm instead of 8.4 and push ~25 % less.
NOSE_DOOR_SPRING_Y = 10.0      # +/- from the centre line
NOSE_DOOR_SPRING_Z = 5.0       # above the band (pin and pocket axis)
SPRING_OD_MAX = 5.0
SPRING_ID_MIN = 3.4
SPRING_FREE_LEN = 20.0
NOSE_DOOR_SPRING_POCKET_D = 5.6
NOSE_DOOR_SPRING_POCKET_DEPTH = 11.0  # closed spring length = depth + 2 x split clearance
NOSE_DOOR_PIN_D = 3.0          # pin across corners (45 deg square: prints sideways cleanly)
NOSE_DOOR_PIN_COLLAR_D = 3.8
NOSE_DOOR_PIN_COLLAR_LEN = 2.5
NOSE_DOOR_PIN_TIP = 2.0        # pin tip engagement in the door's locating hole
NOSE_DOOR_PIN_HOLE_D = 3.6
NOSE_DOOR_TETHER_HOLE = 2.5    # optional thread lug so the ejected door is not lost
NOSE_DOOR_SPLIT_PLATE = 3.0    # housing plate on the split face; carries the spring pins
NOSE_DOOR_GROOVE_R = 17.7      # latch groove centre (= servo horn plane); 3 mm out from the Scorpio's for the deeper pockets
NOSE_DOOR_GROOVE_W = 3.4
NOSE_DOOR_GROOVE_H = 7.0
NOSE_DOOR_GROOVE_LEN = 30.0
NOSE_DOOR_RAMP_ANGLE = 50.0    # housing-side compartment floor slopes down toward the door
NOSE_DOOR_RAMP_T = 2.5
NOSE_DOOR_EYE_HOLE = 5.0       # tie eye on the ramp: door tether, chute bundle tie-down
# The shock cord comes up from Mbody's anchor tunnel through this hole, at the ramp's
# root by the split plate: once the door is gone it turns toward the opening over the
# plate/ramp corner, not over a thin edge. Ø8 for a Ø4 kevlar cord, as the clamshell.
NOSE_DOOR_CORD_HOLE = 8.0
NOSE_DOOR_CORD_AZ = 240.0
NOSE_DOOR_CORD_R = 20.0
# SG90-class micro servo (MG90S recommended): 22.8 x 12.2 x 22.7 mm body, 32.3 mm ear span
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

# --- Display ---------------------------------------------------------------------------
PRINT_COLOR = "#C8553D"
HARDWARE_COLOR = "#B08A5A"
SPRING_COLOR = "#9AA3AD"
