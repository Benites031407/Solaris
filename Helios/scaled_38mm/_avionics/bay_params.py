"""Every number the avionics bay is built from, with its provenance.

Split into four sections:

  1. THE AIRFRAME, AS MEASURED   -- facts about Mbody.stl.  Nothing here is a
     choice.  Every value is reproducible by a script in _scratch/ and the script
     is named next to the value.  Where a number here disagrees with the docstring
     in `scaled_38mm/bay_design.py` or `fwd3drocketfiles/bay_design.py`, THIS FILE
     IS RIGHT and the disagreement is recorded, because those docstrings contain at
     least three values that measurement contradicts.
  2. MATERIAL AND PRINTER        -- inherited from the nose, same machine, same spool.
  3. WHAT GOES IN IT             -- the payload, including the battery the owner has
     not chosen, which is handled by not requiring the choice.
  4. THE BAY ITSELF              -- the actual design choices.

`self_check()` at the bottom re-asserts the relationships that the geometry
depends on, so a careless edit to one number fails loudly instead of quietly
producing a part that does not fit.

FRAME
-----
z = STATION s: mm aft of the body tube's FORWARD RIM, growing aft.  The bay is
modelled directly in this frame so that every dimension in the part is directly
comparable to the measured tables below without a transform in between.

The nose cone's frame runs the other way and relates by nose_z = 26.2069 - s;
NOSE_Z() does that conversion and is the only place the two frames touch.

Azimuth theta: 0 = +x, 90 = +y, degrees, measured in the TUBE's frame.
"""

from __future__ import annotations

import math

# =============================================================================
# 1.  THE AIRFRAME, AS MEASURED
# =============================================================================
# All of section 1 comes off scaled_38mm/Mbody.stl with its forward rim zeroed:
#     m = trimesh.load("Mbody.stl"); m.apply_translation([0, 0, -m.bounds[0, 2]])
# Sources: _scratch/_env_probe.py    (station x azimuth free-radius map)
#          _scratch/_bead_probe.py   (the bead, at 0.25 mm, with wall thickness)
#          _scratch/_tunnel_probe.py (the cord duct's topology and skin)

TUBE_LEN = 262.1          # mm, Mbody's full length
R_OD = 32.745             # outer radius, constant over the whole tube

# --- the nose socket, s 0 .. 27.5 --------------------------------------------
S_SOCKET_END = 27.5       # where the bead's forward flank starts
R_SOCKET = 31.247         # D62.495, constant to within 0.002 over s 0..27.5
WALL_SOCKET = 1.497

# The finished nose's spigot fills the socket.  Committed in _nose_simple.
S_NOSE_SPIGOT_END = 26.2069    # nose_z = 0 -> the spigot's aft face
R_NOSE_SPIGOT = 31.1207        # nose_params.R_SPIGOT
S_NOSE_SCREWS = 13.207         # the nose's 2 retention screws pierce here
NOSE_SCREW_THETA = (0.0, 180.0)  # in the NOSE's frame; see ROTATE_NOSE_BY below

# --- the depth-stop bead, s 27.5 .. 39.5 ------------------------------------
# A TRUE FULL RING: at the throat the free radius varies by 0.008 mm around the
# azimuth, so a keyway cannot defeat it.  This is the hard cap on anything that
# must travel PAST it -- and, because it is a ring, the one free 360-degree
# self-centring datum in the tube for anything that stops AT it.
S_BEAD_THROAT = 32.75
R_BEAD_THROAT = 29.870    # D59.741  <- the forward insertion limit
WALL_BEAD_THROAT = 2.874  # 2.16x the plain tube: the strongest ring up front
S_BEAD_END = 39.5

# The forward flank, measured at 0.25 mm.  Concave (a fillet, quadratic
# coefficient +0.023), so it is matched by a CONVEX crown and not by a cone: a
# cone touches one circle at whichever end its angle happens to match, a crown
# touches a full circle wherever its radius equals the local bore.
# bay_design.py calls this a "depth-stop bead ... necks to D59.82 at z 33.5".
# Measured it is D59.741 at s 32.75.  Close, but the shape is the point.
BEAD_FLANK = (               # (station, free radius)
    (27.50, 31.247), (27.75, 31.142), (28.00, 31.027), (28.25, 30.912),
    (28.50, 30.794), (28.75, 30.670), (29.00, 30.564), (29.25, 30.487),
    (29.50, 30.409), (29.75, 30.332), (30.00, 30.254), (30.25, 30.177),
    (30.50, 30.115), (30.75, 30.072), (31.00, 30.029), (31.25, 29.985),
    (31.50, 29.942), (31.75, 29.924), (32.00, 29.909), (32.25, 29.893),
    (32.50, 29.878), (32.75, 29.870),
)

# --- the working bore, s 39.5 .. 213.5 --------------------------------------
S_WORK_START = 39.5
S_WORK_END = 213.5
R_WORK = 31.411           # D62.821
WALL_WORK = 1.333         # NOT 1.4741 -- that figure is the SOCKET wall.
                          # _loadcase.py used 1.4741 for its bearing sums; the
                          # plain tube is 10% thinner than that and the bead is
                          # 2.16x thicker, so where a screw lands matters.

# --- the shock-cord duct, s 46 .. 63, at theta 0 -----------------------------
# bay_design.py describes this as "a ~7 x 9 mm axial channel in a 15 deg sector
# ... reaching in to r 21.10".  Two of those three numbers are wrong:
#   * the sector is 24 deg, not 15  (_env_probe.py)
#   * it is not a channel over s 49..63 but a FLARED FAIRLEAD: side walls that
#     dive inward from s 46, a roof that stays at r 30.94, and a floor that only
#     closes across at s 56 -- so s 46..56 is a U-channel OPEN to the bore and
#     s 56..62 is a sealed duct.  (_tunnel_probe.py, loop counting + a ray scan)
# The r 21.10 is right.
S_DUCT_START = 46.0
S_DUCT_CLOSED = 56.0      # floor closes; sealed duct from here
S_DUCT_END = 63.0
DUCT_THETA = 0.0          # centreline, measured
DUCT_HALF_ANG = 12.0      # 24 deg total, measured (NOT the 15 deg in bay_design)
R_DUCT_INNER = 21.10      # how far the fairlead reaches toward the axis
R_DUCT_ROOF = 30.94       # the bore at theta 0 over s 46..55, slightly inboard
                          # of R_WORK because the wall thickens locally to 1.78
DUCT_LUMEN_MM2 = 65.7     # sealed cross-section, r 21.74..30.94, 20 deg wide
DUCT_SKIN = 0.66          # the floor between the lumen and the bore.  Thin, but
                          # the bay never loads it: see LOAD NOTE below.

# --- the aft end, s 213.5 .. 262.1 ------------------------------------------
S_TAPER_START = 213.5
S_AFT_BORE_START = 223.0
R_AFT_BORE = 29.44        # D58.88, the aft spigot's bore, clear to s 262
                          # (the coupler sleeve is EXTERNAL, so this bore is free)

# --- the two insertion bottlenecks -----------------------------------------
# These are the numbers that cap the design.  Forward is the LESS restrictive
# one, and it is also the end that already opens (the nose is two screws; the
# tail is the motor mount), so the bay loads from the front.
R_ENTRY_FWD = R_BEAD_THROAT   # 29.870, a full ring: no keyway helps
R_ENTRY_AFT = R_AFT_BORE      # 29.440

# LOAD NOTE.  The cord duct means the shock cord is carried by the AIRFRAME, in
# its own channel, and never shares a volume with the avionics.  _loadcase.py
# section 4 asked the bay to stay out of the ~253 N snatch path; the tube already
# does it.  So the bay's only duty here is to not obstruct the duct's mouth.


def NOSE_Z(s: float) -> float:
    """Station s -> the nose cone's own z.  The only bridge between the frames."""
    return S_NOSE_SPIGOT_END - s


def free_radius(s: float, theta: float = 90.0) -> float:
    """The measured free radius at a station, for a given azimuth.

    Piecewise from the tables above rather than from the mesh, so that part
    scripts can call it without loading a 3 MB STL -- but `bay_verify.py` checks
    it AGAINST the mesh, which is what makes it trustworthy.

    theta matters only inside the cord duct; the default of 90 deg is the clear
    side.  Anything that has to be true at every azimuth should pass theta=0.
    """
    d = abs((theta - DUCT_THETA + 180.0) % 360.0 - 180.0)
    in_duct_sector = d <= DUCT_HALF_ANG

    if s < 0.0 or s > TUBE_LEN:
        raise ValueError(f"station {s} is outside the tube (0..{TUBE_LEN})")
    if s <= S_SOCKET_END:
        return R_SOCKET
    if s <= S_BEAD_THROAT:                     # forward flank: interpolate
        xs = [p[0] for p in BEAD_FLANK]
        ys = [p[1] for p in BEAD_FLANK]
        for i in range(len(xs) - 1):
            if xs[i] <= s <= xs[i + 1]:
                t = (s - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + t * (ys[i + 1] - ys[i])
        return R_BEAD_THROAT
    if s <= S_BEAD_END:                        # aft flank, linear is close enough
        t = (s - S_BEAD_THROAT) / (S_BEAD_END - S_BEAD_THROAT)
        return R_BEAD_THROAT + t * (R_WORK - R_BEAD_THROAT)
    if s <= S_WORK_END:
        if S_DUCT_START <= s <= S_DUCT_END and in_duct_sector:
            return R_DUCT_INNER
        return R_WORK
    if s <= S_AFT_BORE_START:                  # the taper
        t = (s - S_TAPER_START) / (S_AFT_BORE_START - S_TAPER_START)
        return R_WORK + t * (R_AFT_BORE - R_WORK)
    return R_AFT_BORE


def bead_seat_station(d_crown: float) -> float:
    """Where a convex crown of diameter d_crown lands on the bead's forward flank.

    The flank is monotonic, so the root is unique -- but r(s) over the WHOLE bead
    is not, because it falls to the throat and rises again.  Searching the whole
    bead finds two roots and the wrong one is on the aft flank, unreachable from
    the front.  _bead_probe.py made exactly that mistake and reported a D61.20
    crown seating at s 36.75 instead of s 28.92.  Hence: flank only.
    """
    r_c = d_crown / 2.0
    xs = [p[0] for p in BEAD_FLANK]
    ys = [p[1] for p in BEAD_FLANK]
    if not (ys[-1] <= r_c <= ys[0]):
        raise ValueError(
            f"a crown of D{d_crown:.3f} (r {r_c:.3f}) does not meet the bead's "
            f"forward flank, which spans r {ys[-1]:.3f}..{ys[0]:.3f} "
            f"(D{2*ys[-1]:.3f}..D{2*ys[0]:.3f})")
    for i in range(len(xs) - 1):
        if ys[i + 1] <= r_c <= ys[i]:
            t = (ys[i] - r_c) / (ys[i] - ys[i + 1])
            return xs[i] + t * (xs[i + 1] - xs[i])
    return xs[-1]


def bead_flank_angle(s: float, span: float = 1.0) -> float:
    """Local flank half-angle in degrees, over a finite span.

    Over a SPAN, not a single 0.25 mm step: the mesh's facets are coarse enough
    here that a one-step difference reads near-zero on a tread and near-vertical
    on a riser.  _bead_probe.py reported 0.2 deg on a flank that provably drops
    1.3 mm of radius, for that reason.
    """
    xs = [p[0] for p in BEAD_FLANK]
    lo, hi = max(s - span / 2, xs[0]), min(s + span / 2, xs[-1])
    if hi <= lo:
        return 0.0
    return math.degrees(math.atan2(free_radius(lo) - free_radius(hi), hi - lo))


# =============================================================================
# 2.  MATERIAL AND PRINTER
# =============================================================================
# Same machine and spool as the nose; copied from _nose_simple/nose_params.py so
# that _avionics/ stands alone.
PRINTER = "Creality K1 Max"
BED = 300.0               # mm, cubic
NOZZLE = 0.4
EXTRUSION_W = 0.42
LAYER_H = 0.2
MATERIAL = "ABS"
ABS_RHO = 1.04 / 1000.0   # g/mm3
ABS_SHRINK = 0.006        # 0.6%, already in the airframe's measured numbers
WALL_MIN = 1.26           # 3 extrusions -- the thinnest wall worth printing
FUSE_MERGE = 0.5          # THE ONE RULE FOR EVERY UNION IN THESE PARTS: a feature
                          # must overlap what it joins by this much, and must never
                          # merely touch it on a face.  Applies to the rib feet
                          # (sunk into the plate), the plate's own edges when it was
                          # still fused to the shell, the slide rails' outer faces
                          # (buried in the wall rather than clipped to its OD) and
                          # the screw bosses (outer face inside the wall, not on it).
                          # Every one of those was drawn flush first, and two of the
                          # three produced a solid that OCCT reported with a
                          # plausible volume and then destroyed on the NEXT
                          # boolean -- see bay_build.one_solid().
                          #
                          # It lives up here with the other process constants
                          # because it IS one, and because the slide's geometry
                          # needs it 170 lines before the rib block it used to sit
                          # in.  Note that SLIDE_CLR_X and SLIDE_CLR_R are its exact
                          # opposite and must never be confused with it: a fused
                          # face overlaps by 0.5, a sliding face is never allowed to
                          # touch at all.

# =============================================================================
# 3.  WHAT GOES IN IT
# =============================================================================
# The owner said "an esp32 and a bmp280, don't know what battery to use yet".
# So: size the two known boards for the LARGEST common variant of each, and solve
# the battery by not needing to know it (see BATT_* below).

# ESP32.  _clamshell/PARAMS.py pins MCU = "ESP32-WROOM-32" and _clamshell/
# DESIGN.md explains why it must be the classic part and not an S3 (the pin map
# needs GPIO22/25, and the servo asks LEDC for 16-bit duty at 50 Hz, which the
# S3 cannot do).  The 38-pin DevKitC is the biggest board that carries it, so it
# sets the envelope; the 30-pin DevKit V1 (51.4 x 25.4) then also drops in.
ESP32_L = 54.4
ESP32_W = 27.9
ESP32_PCB_T = 1.6
ESP32_H_TOP = 5.0         # WROOM module + can, above the PCB
ESP32_H_BOT = 3.5         # soldered male header pins, below the PCB
ESP32_CLEAR = 1.0         # all round, for a printed pocket

# BMP280 breakout.  Sized to swallow the range of common modules rather than one
# of them: the bare GY-BMP280-3.3 is 11.5 x 15, the Adafruit board 25.4 x 17.8.
BMP_L = 26.0
BMP_W = 18.5
BMP_H = 4.0
BMP_HOLE_D = 2.2          # M2 clearance, for the boards that have mounting holes

# Battery: NOT a pocket.  A flat deck plus two strap slots, so the compartment is
# defined by the strap and not by the cell.  _loadcase.py established that one
# pocket taking all four candidate cells would have to be 65.2 x 30.0 x 18.6 --
# the union of extremes, which no single cell comes close to filling.  A strap
# swallows the unknown at the cost of two slots, which is the cheapest answer to
# "don't know yet" that exists and does not need revisiting when the owner picks.
BATT_L_MAX = 65.2         # 18650 sets this
BATT_W_MAX = 30.0         # 2S 850 mAh pack sets this
BATT_H_MAX = 18.6         # 18650 sets this
STRAP_W = 5.0             # a 4.8 mm zip tie or 5 mm velcro passes
STRAP_T = 2.0

# Masses.  _loadcase.py sweeps these against a 35.0 g ALLOWANCE for the printed
# part, because when it was written there was no part to weigh.  There is one now,
# so these are measurements off the built solids, and bay_support.py's and
# bay_plate.py's __main__ each assert their own still matches what it just built --
# which is how the deck rise below was caught rather than discovered later.
#
# THE NUMBERS HAVE MOVED THREE TIMES.  Keep exactly one live generation here; the
# whole point of asserting them is defeated if a stale copy survives somewhere else
# in the file to be quoted by mistake.
#   gen 1  35.0 g allowance, guessed        -> boost 14.74 N, landing 39.31 N, 24x
#   gen 2  54.10 cm3 = 56.3 g, measured     -> boost 17.87 N, landing 47.66 N, 20x
#   gen 3  55.82 cm3 = 58.1 g, DECK_RISE 6  -> boost 18.13 N, landing 48.35 N, 19x
#   gen 4  57.78 cm3 = 60.1 g, SPLIT IN TWO -> the values below
# Raising the deck ADDED material because the deck is a chord of the bore and a
# chord nearer the axis is a wider one: it grew from 24.69 to 26.38 mm of half-width
# (26.38, not 26.79 -- the plate is clipped SLIDE_CLR_R inside the bore now), which
# is 1.4 g of ABS over its span.  Splitting it added 2.0 g more: two rails, a stop,
# and two lugs, none of which the one-piece part needed.
M_ESP32 = 9.0
M_BMP = 1.2
M_WIRING = 7.0
M_SUPPORT = 41.2          # MEASURED, 39642.64 mm3 -- head, shell, bosses, rails, stop
M_PLATE = 18.9            # MEASURED, 18136.28 mm3 -- deck, ribs, lugs, less its slots
M_SLED = M_SUPPORT + M_PLATE             # 60.1: what the pair weighs, for every load
                                         # case that does not care which of the two a
                                         # gram sits in -- which is all of them, since
                                         # both fly.  The split ADDED 2.0 g: the rails
                                         # and stop are new material and so are the
                                         # two lugs, where the one-piece sled's deck
                                         # was simply part of the shell.
M_BATT_WORST = 48.0       # the 2S 850 mAh pack, heaviest of the four candidates
F_BOOST_N = 18.43         # 15 g on 125.29 g, and it pushes the plate AFT, onto the
                          # support's stop
F_LANDING_N = 49.15       # 40 g FORWARD, the case that breaks solder joints and
                          # the LARGER of the two -- so whatever retains a sliding
                          # plate at its forward end carries the bigger load, which
                          # is why the two M3s exist and friction was never an option

# =============================================================================
# 4.  THE BAY ITSELF
# =============================================================================
# Rotational alignment.  The tube is externally featureless over the socket, so
# the nose's two retention screws may be drilled at any tube azimuth.  Putting
# them at tube theta 90/270 lands the nose's D8 shock-cord hole (nose theta 270)
# directly over the tube's cord duct (tube theta 0), so the cord runs straight
# from the nose into the fairlead without crossing the bay.
ROTATE_NOSE_BY = 90.0     # deg: nose theta 0 -> tube theta 90

# -----------------------------------------------------------------------------
# THE ARCHITECTURE, and why it is this one
# -----------------------------------------------------------------------------
# ONE printed part, TWO screws, ONE strap.  A trough that hangs off the bead at
# the front and is screwed to the wall at the back.
#
# The measurements force most of this.  The bead caps anything that must pass it
# at r 29.870 while the working bore is r 31.411, so a rigid part that reaches the
# payload volume is permanently >= 1.54 mm clear of the bore and CANNOT be located
# by it.  Something has to span that gap.  But a part that STOPS at the bead is
# not capped at all -- and the bead's forward flank is a concave fillet on the
# thickest ring in the forward tube, which is the one full-360-degree self-centring
# radial datum the tube has.  So:
#
#   FORWARD  a crown circle at r 30.60 seats in the bead's fillet at s 28.92, on a
#            measured 21.7 deg flank.  Radial datum, and the stop for FORWARD
#            inertia (landing, F_LANDING_N) reacted as hoop compression on a
#            2.87 mm ring.  Costs nothing: it is just the trough's outer profile.
#   AFT      2 M3 self-tappers at s 201.5, tube theta 90/270.  These take AFT
#            inertia (boost, F_BOOST_N -- note boost pushes the sled AFT, so it
#            LIFTS OFF the crown and the crown cannot react it), stop the sled
#            rattling in its 1.96 mm annulus, and prevent it pivoting about the
#            crown.  2 x M3 = 353 N, and self_check() prints the live margin.
# The load figures are deliberately NOT repeated here as literals: this block used
# to quote 39.31 N, 14.74 N and "24x" from a generation of the design two revisions
# old, sitting 40 lines below the corrected values and reading just as
# authoritatively.  Name the constants instead, so prose cannot go stale.
#
# With both ends located the payload sits BETWEEN the two supports rather than
# beyond them, so this is a simply-supported beam and not the cantilever an earlier
# and shorter layout would have been.  That is a consequence of putting the boards
# in series and letting the sled grow to 181.7 mm: the working bore is 174 mm long
# and there was never a reason to pack the payload into the forward half of it.
#
# Each end does one job and neither duplicates the other.  The 1.14 mm gap to the
# nose spigot is deliberate: trapping the sled under the nose would delete the two
# screws, but it would also put the sled's boost load into the nose's retention
# screws and make removing the nose drop the sled.  The subsystems stay decoupled.
#
# WHY A TROUGH OPEN TOWARDS theta = 0
# The cord duct intrudes to r 21.10 over s 46..63 in a 24 deg sector at theta 0.
# Opening the trough there means the sled has NO MATERIAL in the duct's sector at
# any station, so the keyway is free -- and inserting the sled rotated the wrong
# way binds at s 46 instead of going in and fouling, which makes the clash a
# self-enforcing key rather than something to mark and remember.
#
# WHY A STRAP FOR THE BATTERY
# The owner has not chosen one.  A pocket that took all four candidates would have
# to be 65.2 x 30.0 x 18.6 (the union of extremes, which no single cell fills), so
# a pocket is both the biggest and the most likely to be wrong.  Two slots and a
# zip tie take anything up to the deck's width and never need revisiting.

# --- radii -------------------------------------------------------------------
R_SHELL_O = 29.45         # trough OD: 0.42 mm inside the bead throat (29.870),
                          # 1.96 mm inside the working bore (31.411)
SHELL_T = 2.0             # trough wall -- 1.6x WALL_MIN
R_SHELL_I = R_SHELL_O - SHELL_T          # 27.45
R_CROWN = 30.60           # THE DATUM.  D61.20, seats at s 28.92.
X_OPEN = 4.0              # the trough is cut away for x > X_OPEN, which opens it
                          # over theta -82.2 .. +82.2 -- wider than the duct's
                          # +/-12 deg by a factor of 6.8

# --- the head ----------------------------------------------------------------
S_CROWN = 28.92           # = bead_seat_station(2 * R_CROWN); asserted, not assumed
PILOT_L = 1.61            # the r 30.60 land forward of the crown, which guides
                          # into the socket (0.647 mm clearance) before seating
S_HEAD_FWD = S_CROWN - PILOT_L           # 27.31
S_HEAD_AFT = 30.60        # where the crown taper reaches R_SHELL_O
# The taper from R_CROWN to R_SHELL_O must fall away FASTER than the bead's flank,
# or contact migrates off the crown circle to the taper's aft end and the datum
# stops being a known diameter.  Checked in self_check().

# --- the deck ----------------------------------------------------------------
# ONE number moves the deck: DECK_RISE.  This used to be two independent
# coordinates with DECK_T *derived* from their difference, so editing either
# coordinate silently changed the plate's THICKNESS -- and a zero-thickness deck
# still passed every check, because nothing compared DECK_T to anything.
# Thickness is primary now and position is derived, which kills that failure mode
# by construction rather than by adding a guard against it.
DECK_T = 2.0              # 10 layers at LAYER_H 0.2
DECK_X_BOT_0 = -14.0      # where the deck sat before the rise: a chord across
                          # the trough giving 13.45 mm of channel on the centreline
DECK_RISE = 6.0           # A MEASURED CHOICE -- see _scratch/_deck_rise_out.txt,
                          # which bisects each ceiling on cross-sections of the
                          # real Mbody.stl rather than on the table below.
                          #
                          # What it buys, which is the point of the whole edit:
                          #   channel area   449.8 -> 750.7 mm2   (+67%)
                          #   depth at y=0    13.45 -> 19.45 mm
                          #   depth at the PIN SLOTS 10.34 -> 16.34 mm  <- the one
                          #     that mattered: 3.5 mm of ESP32 header pin hangs
                          #     down into exactly that space.
                          #
                          # Every ceiling, nearest first.  All are checked below,
                          # none is merely asserted here:
                          #    7.63  the screw bosses' x-band, |x| <= 4.372
                          #   10.75  the screw pilots' band, |x| <= 1.25
                          #   13.50  X_OPEN starts shaving the BMP ribs
                          #   14.48  THE AIRFRAME: the 18.6 mm cell's top corner
                          #          meets the cord duct's floor (r 21.0966 at
                          #          s 56.50, theta 1.25) -- on the way IN, not
                          #          seated.  See the note at the duct check.
                          #   16.00  the deck's own top face reaches X_OPEN
                          #
                          # 6.0 leaves 1.63 mm to the nearest of them.  Deliberately
                          # NOT the maximum: this deck now has to SLIDE, and the
                          # clearances that allows do not exist yet, so margin is
                          # worth more here than channel area.  Going to 7.0 would
                          # buy 7% more area and spend 60% of the boss margin.
DECK_X_BOT = DECK_X_BOT_0 + DECK_RISE    # -8.0
DECK_X_TOP = DECK_X_BOT + DECK_T         # -6.0
# The deck closes the open C into a D below it, which is what makes a 181 mm span
# stiff enough to bother with; the closed channel underneath is also the strap's
# return path and the BMP280's static plenum.

# --- stations ----------------------------------------------------------------
S_BOARDS_0 = 36.0         # the payload starts here, which is INSIDE the bead's aft
                          # flank (s 32.75..39.5).  That is fine and not an
                          # oversight: the flank restricts r 29.87..31.41, the
                          # sled's own shell is already at 29.45, and everything
                          # standing on the deck is inside r 17.  Only the shell's
                          # OD ever has to clear the bead, and it does, everywhere.
S_ESP32_0 = 68.0
S_ESP32_1 = S_ESP32_0 + ESP32_L + 2 * ESP32_CLEAR      # 124.4
S_BATT_0 = 128.0
S_BATT_1 = S_BATT_0 + BATT_L_MAX                        # 193.2
S_TAIL = 209.0            # the sled's aft end, still inside the working bore
S_SCREW = 201.5           # the 2 retention screws
S_BOSS_RAMP = 189.0       # the boss's underside starts ramping in here...
S_BOSS_0 = 194.0          # ...and reaches full depth here, at an angle shallow
S_BOSS_1 = S_TAIL         #    enough to print with no support under it
# Everything is IN SERIES along the axis rather than packed side by side.  The
# working bore is 174 mm long and the payload needs about 155 of it, so there is
# no reason to nest anything: in series means one constant cross-section, one
# strap orientation, and no board overhanging another.
R_BOSS_I = 23.0           # boss reaches in to here, giving 6.45 mm of thread
SCREW_PILOT_D = 2.5       # M3 self-tapper pilot in ABS
SCREW_THETA = (90.0, 270.0)
BOSS_HALF_ANG = 9.0

# --- THE SLIDE: two parts, and how the plate gets into the support ------------
# The sled used to be one printed part, so the deck was FUSED to the shell and the
# only way to reach behind it was through the vent holes.  It is now two:
#
#   the support   head ring, shell, trough opening, screw bosses, and the rails
#                 that form a pocket for the plate.  Printed forward-end-down,
#                 axis = build Z, exactly as before.
#   the plate     the chord plate and everything that touches a component --
#                 ribs, pin slots, tie slots, vents, static ports.  Printed FLAT.
#                 This is the part that gets populated on the bench.
#
# The plate enters from the FORWARD end and slides aft, which is the only end that
# is ever accessible: the support is retained by two screws through the airframe
# and its aft end is 209 mm down a 38 mm tube.  So the electronics can be serviced
# without disturbing the support, or the airframe, at all.
#
# WHY RAILS STANDING PROUD AND NOT GROOVES IN THE WALL
# The head is a COMPLETE ring with a bore of r 27.45 and the plate has to pass
# through it.  Grooves cut into the shell wall would put the plate's edges OUTSIDE
# r 27.45 -- wider than the hole it has to go through -- so the plate could never
# be inserted, and the grooves would thin a 2.0 mm wall to under WALL_MIN as well.
# Rails standing inward of the bore invert both problems: the plate is NARROWER
# than the bore, and the wall is untouched.
#
# Everything here is a constant cross-section extruded along z, so it prints with
# no support in the support's pose -- see the note on print orientation in
# bay_support.py.  The one exception is the aft face of the pocket (the stop),
# which is a bridge, and it is a small one.
SLIDE_CLR_X = 0.30        # per face, plate to pocket, in x.  NOT ABS_SHRINK-sized:
                          # this is a printed-to-printed SLIDING fit over 177 mm,
                          # where the error that matters is not shrink (the slicer
                          # compensates it) but bow.  A 2 mm plate 177 mm long will
                          # not come off the bed dead flat, and a pocket printed
                          # 209 mm up a vertical axis will not be dead straight
                          # either.  0.30 per face gives 0.60 mm of total x slop:
                          # loose enough to slide dry with the payload on it,
                          # tight enough that the plate cannot cock far enough to
                          # jam.  FUSE_MERGE is the opposite rule and must not be
                          # reused here -- fused features overlap by 0.5 mm, sliding
                          # ones are never allowed to touch at all.
SLIDE_CLR_R = 0.40        # plate edge to bore.  Larger than SLIDE_CLR_X because a
                          # radial interference here is a hard stop, not a tight
                          # fit: the plate cannot flex out of its own plane easily,
                          # and this is also where the shell's own roundness error
                          # lands.
RAIL_ENGAGE = 1.00        # how far the plate's edge reaches OUTBOARD of the rail's
                          # inner face.  This overlap is the whole retention: the
                          # plate cannot lift, because to lift on one side it would
                          # have to move 1.00 mm inboard on that side, and its other
                          # edge is already against the bore.
RAIL_T = 2.00             # rail thickness in x, = SHELL_T.  1.59x WALL_MIN.
R_PLATE = R_SHELL_I - SLIDE_CLR_R        # 27.05, the plate's clip radius
R_RAIL_I = R_PLATE - RAIL_ENGAGE         # 26.05, the rails' inner face
R_RAIL_O = R_SHELL_I + FUSE_MERGE        # 27.95, buried in the wall, same reason
                                         # as the old deck's clip radius
POCKET_X_BOT = DECK_X_BOT - SLIDE_CLR_X  # -8.30
POCKET_X_TOP = DECK_X_TOP + SLIDE_CLR_X  # -5.70
RAIL_L_X_BOT = POCKET_X_BOT - RAIL_T     # -10.30, the lower rail's underside
RAIL_U_X_TOP = POCKET_X_TOP + RAIL_T     # -3.70, the upper rail's top

# The upper rail stops SHORT of the screw bosses.  It has to: the bosses are
# annular sectors, so their x-extent is +/-(R_SHELL_I + FUSE_MERGE)*sin(9 deg) =
# +/-4.372, and RAIL_U_X_TOP is -3.70 -- inside that band.  Run the upper rail the
# full length and it fuses into both bosses over s 189..209, which is harmless
# metal but destroys every closed-form volume prediction in the boss's own
# construction and puts rail material on the ray that bay_verify uses to prove the
# boss is a local sector and not a ring.  Ending it 1 mm forward of the ramp costs
# 16.5 mm of upper capture at the aft end, and the two retention screws land in
# the middle of exactly that gap.
S_RAIL_U_1 = S_BOSS_RAMP - 1.0           # 188.0
S_RAIL_0 = S_HEAD_FWD                    # both rails start on the bed, at the
                                         # forward face, for the same reason the
                                         # deck used to: a rail that begins part
                                         # way up the build is floating
S_STOP = 205.0            # THE HARD STOP: the pocket is filled from here to S_TAIL,
                          # so the plate cannot pass through and out the aft end.
                          # This is the "only slides in one way" part.
                          #
                          # It fills the pocket only over the RAILS' radial band
                          # (R_RAIL_I..R_RAIL_O), not the full chord.  A full-chord
                          # plug looks more solid and is unprintable: its forward
                          # face is the one downward-facing surface the slide adds,
                          # and drawn across the whole chord it would have to bridge
                          # ~52 mm from one side of the bore to the other with
                          # nothing underneath, against BRIDGE_MAX 6.0.  Kept inside
                          # the rail band it lands on the lower rail below it and on
                          # the shell wall outboard of it, and no point of it is
                          # further than 1.40 mm from one of the two.  It still
                          # blocks the plate: the plate's aft face overlaps this band
                          # by RAIL_ENGAGE, which is 4.3 mm2 of bearing for
                          # F_BOOST_N -- about 4 MPa, a tenth of what ABS takes.
SLIDE_GAP_Z = 0.5         # the plate is drawn 0.5 mm short of the stop so that it
                          # ALWAYS seats on it rather than sometimes fouling first.
                          # Pushed home, the plate is then located axially by the
                          # stop to within this gap, which is what makes the lug
                          # pilots below line up: they are only 3.0 mm from the
                          # stop, so the plate's own 177 mm length -- and all of
                          # its shrink error -- is out of that alignment chain.
S_PLATE_FWD = S_HEAD_FWD                 # 27.31, flush with the support's face
S_PLATE_AFT = S_STOP - SLIDE_GAP_Z       # 204.5
PLATE_L = S_PLATE_AFT - S_PLATE_FWD      # 177.19

# --- forward retention: the plate's two screw lugs ----------------------------
# The stop takes the boost load (F_BOOST_N, aft).  Landing is the bigger case and
# it pushes FORWARD, i.e. back out of the mouth the plate came in through, so the
# plate needs a positive forward stop too -- friction is not a retention scheme.
#
# It reuses the two screws the support already has, lengthened.  Each M3 crosses
# the airframe, the boss, and then 0.80 mm of air, and takes 5 mm of thread in a
# lug standing off the plate's top face.  No third and fourth hole in the airframe,
# one screw length in the whole assembly, and the load path is the screw in shear
# rather than anything printed in tension.
#
# The lug is a plain BOX, not a sector clipped to a radius, so that its volume is
# exact and its worst case is a single corner instead of a surface: hypot(
# LUG_X_TOP, LUG_Y_O) is the only radius that matters and it is checked below
# against the boss's inner face, which the lug has to pass under on the way in.
LUG_Y_O = 22.0            # the lug's outboard face; the screw enters here.  22.2
                          # was the first value and it is 0.2 mm too far out: the
                          # worst point below comes to r 22.477 against the boss's
                          # 23.0, which is 0.523 mm -- under LUG_CLR.  Pulling the
                          # face in to 22.0 buys 0.726 mm and costs 0.2 mm of the
                          # screw's spare length, of which there was 0.455.
LUG_DEPTH = 6.0           # so the inboard face is at y 16.0, and the screw tip at
                          # y 16.745 still has 0.75 mm of lug in front of it
LUG_X_TOP = 3.0           # 9.0 mm off the plate's top face.  NOT 1.5, which is what
                          # this was until the pilot was actually drawn: the screw's
                          # axis is the x = 0 line, an M3 self-tapper forms thread
                          # out to a 1.5 mm major radius, and a lug whose top face
                          # IS x = 1.5 therefore has zero material over the crest --
                          # the first turn of the screw splits it lengthwise.  3.0
                          # leaves 1.5 mm over the thread, just over WALL_MIN, and
                          # is checked below.  It cannot go much higher: the lug has
                          # to pass under the bosses, which caps it near 3.3.
LUG_X_BOT = DECK_X_TOP - FUSE_MERGE      # -6.5, sunk into the plate for the same
                                         # reason the ribs are -- a lug laid flush
                                         # on the deck's top face touches it and
                                         # overlaps it nowhere
LUG_CLR = 0.55            # what the lug's worst POINT keeps from the boss's r 23.0
                          # inner face as it slides under it.  "Point", not
                          # "corner": see the check, which had this wrong.
S_LUG_1 = S_PLATE_AFT     # 204.5, flush with the plate's aft face
S_LUG_0 = 197.5           # 7.0 mm long, and the screw sits 3.0 mm inside its aft
                          # end once the plate is seated -- see SLIDE_GAP_Z and
                          # S_LUG_PILOT on why THAT distance is the one that has to
                          # be short, and why the pilot is not drawn at S_SCREW
LUG_PILOT_D = SCREW_PILOT_D              # the lug is pre-piloted; a self-tapper
                                         # that has just finished forming 6.45 mm
                                         # of thread in the boss will not start a
                                         # fresh hole in mid-air reliably.  Bored
                                         # THROUGH the lug, not blind: the screw
                                         # then stops where its length says rather
                                         # than bottoming out and splitting it, and
                                         # in the plate's flat print pose the hole
                                         # is horizontal either way -- a 2.5 mm
                                         # bridge at its crown, which is nothing.
S_LUG_PILOT = S_SCREW - SLIDE_GAP_Z      # 201.0 as drawn -> 201.5 seated; see the
                                         # check, and SLIDE_GAP_Z
SCREW_L = 16.0            # M3 x 16, up from the M3 x 12 the one-piece sled used

# The BMP280 sits forward, between two ribs, with static ports through the
# deck into the closed channel below.  It is NOT sealed: the tube's interior
# already vents to ambient through the nose (servo bay -> bulkhead holes -> chute
# cavity -> 2 x D4.0 vents), and sealing a bay against a 1.33 mm printed wall is
# exactly what the old design found put 18 MPa of interlayer tension into a
# spigot.  Unsealed is adequate because apogee detection is the job and at apogee
# the airspeed is zero, so there is no dynamic error left to shield from.  The
# ports plus the closed channel give the sensor a stagnant volume rather than a
# through-flow, which is all that is actually needed.
S_BMP_0 = S_BOARDS_0
S_BMP_1 = S_BOARDS_0 + BMP_L + 2.0                      # 64.0
BMP_PORT_D = 2.5
BMP_PORT_STATIONS = (43.0, 49.0, 55.0)   # on the centreline, y = 0, so they never
BMP_PORTS = len(BMP_PORT_STATIONS)       # meet the strap slots out at y +/-13

# -----------------------------------------------------------------------------
# HOW THE BOARDS ARE HELD -- and why there are no posts
# -----------------------------------------------------------------------------
# Printing forward-end-down with the axis as build Z has one consequence that
# decides every retention feature: ANY shape whose cross-section is constant along
# z has no downward-facing surface at all, so it prints with zero support whatever
# its profile.  Anything that grows in +x at a fixed station does not.
#
# That kills the fence posts this file used to specify.  A post along +x is a
# horizontal 6 mm cantilever rod in the print -- its underside is an overhang and
# its tip is a bridge over nothing.  Extruded RIBS do the same job, print perfectly,
# and locate the board over its whole length instead of at four points.  Ribs still
# need one 45 deg ramp where they rise off the deck, because a rib that simply
# begins at a station has an unsupported bottom face.
#
# It also kills the idea of resting the ESP32 flat on the deck: a DevKitC carries
# 3.5 mm of soldered header pin UNDER the PCB, so flat on the deck means crushed
# pins.  Rails to lift it clear cannot work either -- a ledge that supports the
# board's edge has to be inboard of it, a lip that locates the board has to be
# outboard of it, and the pin rows sit 1.25 mm inboard of the edge, so there is no
# room for both.  Instead the pins drop through TWO SLOTS in the deck.  The board
# then sits flat, the pins hang into the closed channel (10 mm of depth there for a
# 3.5 mm pin), the slots key the board laterally, and they double as the wire route.
# One void, three jobs, and it is a constant cross-section along z.
STRAP_SLOT_Z = 5.0        # along the axis: the strap's width
STRAP_SLOT_Y = 2.5        # across: the strap's thickness

RIB_T = 1.5               # rib thickness; > WALL_MIN so it is two solid walls
RIB_RAMP = 45.0           # the ramp angle where a rib rises off the deck, fixed by
                          # construction (the ramp runs h in x over h in z)

# The BMP280 gets ribs: it is light, it has no pins under it, and it has to stay
# put so its wires are not the thing holding it.
RIB_Y_BMP = 10.5          # centreline; inner faces at +/-9.75 for an 18.5 board
RIB_H_BMP = 2.5           # shorter than BMP_H (4.0) so a tie presses the BOARD
S_RIB_BMP_0 = S_BMP_0
S_RIB_BMP_1 = S_BMP_1

# The ESP32 gets pin slots instead of ribs.
PIN_SLOT_Y = 12.7         # 38-pin DevKitC headers sit here; the 30-pin V1's at
PIN_SLOT_W = 3.6          # 11.4 also fall inside a 3.6 mm slot centred on 12.7
S_PIN_SLOT_0 = 68.0
S_PIN_SLOT_1 = 126.0

# The battery gets NEITHER.  Ribs sized for the 27.9 mm ESP32 leave a 29.1 mm gap
# and the widest candidate cell is 30.0, so one rib pair cannot serve both -- and
# of the two, the cell is the one whose width is not yet known.  Bare deck plus two
# ties, which was the whole point of choosing a strap over a pocket.
STRAP_Y_BMP = 13.0        # just outboard of the BMP ribs' 11.25 outer face
STRAP_Y_MAIN = 18.0
STRAP_STATIONS_BMP = (50.0,)
STRAP_STATIONS_ESP32 = (78.0, 112.0)
STRAP_STATIONS_BATT = (140.0, 185.0)     # both inside the battery bay, 128..193.2

# Vents run down the deck's SHOULDERS rather than its centreline.  The boards are
# at most 27.9 mm wide (|y| <= 14.0) but the deck is clear out to |y| = 24.7 for
# its whole length, so a hole at y = +/-20 can never collide with a board footprint
# whatever station it is at -- which also means these two do not have to be
# re-checked every time the axial layout moves, and the axial layout moved twice.
VENT_D = 5.0              # deck holes for wiring and drainage.  5, not 6: at
                          # y 20 a D6 hole reaches y 23 and the plate's usable
                          # half-width at its top face is 26.39, which leaves too
                          # little edge for the extra millimetre to be worth it.
                          # (That half-width was 24.69 when the deck sat at x -12
                          # and was clipped to the bore; the rise moved the chord
                          # towards the axis, which WIDENS it, and the slide then
                          # took 0.40 mm back off as SLIDE_CLR_R.)
VENT_Y = 20.0
VENT_STATIONS = (66.0, 193.0)   # the aft one used to be at s 200, which is now
                                # inside the screw lugs (s 197.5..204.5, |y|
                                # 16.2..22.2) -- the hole and the lug wanted the
                                # same material.  193.0 keeps it aft of everything
                                # it drains and 2.0 mm clear of the lug's face.


def support_h() -> float:
    """The SUPPORT's height on the bed, which is its whole length end to end.

    It prints forward-end down with its axis vertical, so length IS height.  This
    was sled_len() when the bay was one part and that name is now a trap: the
    plate is a different length AND prints in a different pose, so nothing about
    its bed footprint follows from this number.  See plate_footprint().
    """
    return S_TAIL - S_HEAD_FWD


def plate_footprint() -> tuple[float, float, float]:
    """The PLATE lying flat: (across, along, tall), all in bed coordinates.

    Lying flat, the part's own x becomes the build axis, so the height is the x
    extent -- deck underside to the top of a lug -- and the bed is the y-s plane.
    The widest y is NOT at the deck's underside where it touches the bed: the
    chord's edge is a cylinder, so the section grows as x rises and the widest
    point is at the deck's TOP face.  Taking the bottom face's width would
    under-report the footprint by 1.07 mm, which is the sort of error that only
    shows up as a part fouling a bed clip.
    """
    across = 2.0 * math.sqrt(R_PLATE ** 2 - DECK_X_TOP ** 2)
    return across, PLATE_L, LUG_X_TOP - DECK_X_BOT


def self_check() -> None:
    """Re-assert the relationships the geometry leans on."""
    fails = []

    def ck(cond, ok, bad):
        # both strings built before looking at cond, so a broken f-string in the
        # failure branch cannot hide behind a passing test
        ok_s, bad_s = str(ok), str(bad)
        if cond:
            print(f"  ok   {ok_s}")
        else:
            fails.append(bad_s)
            print(f"  FAIL {bad_s}")

    print("bay_params.self_check()")
    print("-- section 1: the airframe as measured")
    ck(R_BEAD_THROAT < R_WORK,
       f"the bead ({R_BEAD_THROAT:.3f}) is tighter than the working bore "
       f"({R_WORK:.3f}) -- a part that passes it can never touch the bore, and so "
       f"cannot be located by it",
       "the bead is not tighter than the bore, which contradicts every probe")
    ck(abs((R_WORK - R_BEAD_THROAT) - 1.541) < 0.01,
       f"the slop a passing part must span is {R_WORK - R_BEAD_THROAT:.3f} mm",
       f"radial slop moved to {R_WORK - R_BEAD_THROAT:.3f}, expected 1.541")
    ck(R_ENTRY_FWD > R_ENTRY_AFT,
       f"forward entry (r {R_ENTRY_FWD:.3f}) is less restrictive than aft "
       f"(r {R_ENTRY_AFT:.3f}), so the bay loads from the front",
       "aft entry is now the roomier one -- the loading direction should be revisited")
    ck(WALL_BEAD_THROAT > 2.0 * WALL_WORK,
       f"the bead's wall ({WALL_BEAD_THROAT:.3f}) is over twice the plain tube's "
       f"({WALL_WORK:.3f}), so a reaction there closes as hoop compression",
       f"the bead is no longer a strong ring: {WALL_BEAD_THROAT:.3f} vs "
       f"{WALL_WORK:.3f}")
    ck(S_NOSE_SPIGOT_END < S_SOCKET_END,
       f"the nose's spigot (ends s {S_NOSE_SPIGOT_END:.4f}) stops short of the "
       f"socket's end (s {S_SOCKET_END:.2f}), leaving "
       f"{S_SOCKET_END - S_NOSE_SPIGOT_END:.3f} mm of free socket",
       "the nose spigot runs past the socket into the bead, which cannot be")
    ck(R_NOSE_SPIGOT < R_SOCKET,
       f"the nose spigot (r {R_NOSE_SPIGOT:.4f}) clears the socket "
       f"(r {R_SOCKET:.3f}) by {R_SOCKET - R_NOSE_SPIGOT:.3f} mm",
       f"the nose spigot does not fit its own socket: r {R_NOSE_SPIGOT:.4f} vs "
       f"{R_SOCKET:.3f}")

    print("-- the bead flank, and the seat it offers")
    ck(all(BEAD_FLANK[i + 1][1] < BEAD_FLANK[i][1]
           for i in range(len(BEAD_FLANK) - 1)),
       "the bead's forward flank is monotonic, so a crown diameter has ONE seat",
       "the flank table is not monotonic -- bead_seat_station() would be ambiguous")
    ck(abs(BEAD_FLANK[0][1] - R_SOCKET) < 0.01,
       f"the flank starts at the socket bore (r {BEAD_FLANK[0][1]:.3f})",
       f"the flank table starts at r {BEAD_FLANK[0][1]:.3f}, not the socket's "
       f"{R_SOCKET:.3f} -- there is a step between them")
    ck(abs(BEAD_FLANK[-1][1] - R_BEAD_THROAT) < 0.001,
       f"the flank table ends exactly at the throat (r {R_BEAD_THROAT:.3f})",
       f"the flank table ends at r {BEAD_FLANK[-1][1]:.3f}, not the throat's "
       f"{R_BEAD_THROAT:.3f}")
    s28 = bead_seat_station(61.20)
    ck(abs(s28 - 28.92) < 0.05,
       f"a D61.20 crown seats at s {s28:.2f}, on a "
       f"{bead_flank_angle(s28):.1f} deg flank",
       f"a D61.20 crown now seats at s {s28:.2f}, not the measured 28.92")
    ck(bead_flank_angle(s28) > 15.0,
       f"that flank is {bead_flank_angle(s28):.1f} deg, steep enough to release "
       f"(ABS on ABS self-locks below about 19 deg)",
       f"that flank is only {bead_flank_angle(s28):.1f} deg -- the seat may jam")

    print("-- free_radius() against the tables it came from")
    for s, want, th in ((5.0, R_SOCKET, 90.0), (26.0, R_SOCKET, 90.0),
                        (32.75, R_BEAD_THROAT, 90.0), (100.0, R_WORK, 90.0),
                        (200.0, R_WORK, 90.0), (250.0, R_AFT_BORE, 90.0),
                        (56.0, R_DUCT_INNER, 0.0), (56.0, R_WORK, 90.0),
                        (56.0, R_WORK, 180.0)):
        got = free_radius(s, th)
        ck(abs(got - want) < 0.01,
           f"free_radius(s={s}, theta={th}) = {got:.3f}",
           f"free_radius(s={s}, theta={th}) = {got:.3f}, expected {want:.3f}")
    ck(free_radius(56.0, 11.0) == R_DUCT_INNER
       and free_radius(56.0, 13.0) == R_WORK,
       f"the duct sector's edge is between theta 11 and 13 deg, matching the "
       f"measured {DUCT_HALF_ANG:.0f} deg half-angle",
       "the duct sector is not where DUCT_HALF_ANG says it is")

    print("-- section 3: the payload")
    ck(BATT_L_MAX < S_WORK_END - S_WORK_START,
       f"the longest candidate cell ({BATT_L_MAX:.1f} mm) fits inside the working "
       f"bore's {S_WORK_END - S_WORK_START:.1f} mm",
       f"no candidate cell fits the working bore")
    ck(2 * R_ENTRY_FWD > BATT_W_MAX + 2 * WALL_MIN,
       f"the widest cell ({BATT_W_MAX:.1f} mm) plus two walls passes the bead "
       f"(D{2*R_ENTRY_FWD:.2f})",
       f"the widest cell will not pass the bead")
    ck(NOSE_Z(0.0) == S_NOSE_SPIGOT_END and NOSE_Z(S_NOSE_SPIGOT_END) == 0.0,
       f"NOSE_Z maps the rim to nose_z {NOSE_Z(0.0):.4f} and the spigot's aft "
       f"face to 0",
       "NOSE_Z is not the inverse it claims to be")

    print("-- section 4: the sled against the bore it lives in")
    ck(R_SHELL_O < R_ENTRY_FWD,
       f"the trough (r {R_SHELL_O:.2f}) passes the bead throat "
       f"(r {R_ENTRY_FWD:.3f}) with {R_ENTRY_FWD - R_SHELL_O:.3f} mm to spare",
       f"the trough (r {R_SHELL_O:.2f}) will not pass the bead "
       f"(r {R_ENTRY_FWD:.3f}) -- it cannot be installed")
    ck(abs(S_CROWN - bead_seat_station(2 * R_CROWN)) < 0.005,
       f"S_CROWN ({S_CROWN:.2f}) is where a D{2*R_CROWN:.2f} crown actually "
       f"seats ({bead_seat_station(2 * R_CROWN):.2f})",
       f"S_CROWN is {S_CROWN:.2f} but a D{2*R_CROWN:.2f} crown seats at "
       f"{bead_seat_station(2 * R_CROWN):.2f} -- the head is drawn in the wrong place")
    gap_nose = S_HEAD_FWD - S_NOSE_SPIGOT_END
    ck(gap_nose > 1.0,
       f"the head's forward face clears the nose spigot by {gap_nose:.3f} mm, so "
       f"the bay and the nose stay decoupled",
       f"the head clears the nose by only {gap_nose:.3f} mm -- they will touch and "
       f"the nose's screws will carry bay load")
    # the pilot land must fit the socket over its whole length
    ck(R_CROWN < R_SOCKET,
       f"the pilot land (r {R_CROWN:.2f}) enters the socket (r {R_SOCKET:.3f}) "
       f"with {R_SOCKET - R_CROWN:.3f} mm clearance",
       f"the pilot land (r {R_CROWN:.2f}) does not fit the socket "
       f"(r {R_SOCKET:.3f})")
    # THE ONE THAT MATTERS: the crown taper must fall away faster than the flank,
    # or contact leaves the crown circle and the datum diameter stops meaning
    # anything.  Checked at every 0.25 mm station between the seat and the throat.
    taper_deg = math.degrees(math.atan2(R_CROWN - R_SHELL_O, S_HEAD_AFT - S_CROWN))
    ck(taper_deg > bead_flank_angle(S_CROWN),
       f"the crown taper is {taper_deg:.1f} deg against the flank's "
       f"{bead_flank_angle(S_CROWN):.1f} deg, so contact stays on the crown circle",
       f"the crown taper ({taper_deg:.1f} deg) is shallower than the flank "
       f"({bead_flank_angle(S_CROWN):.1f} deg) -- contact migrates aft off the datum")
    # ...and aft of the seat the sled must actually fall away from the bore.
    #
    # The sweep starts one step AFT of S_CROWN, not at it.  At the seat station the
    # sled's radius equals the bore's BY DEFINITION -- that is what "seats" means --
    # so a gap > 0 test evaluated there is measuring the datum, not a foul, and
    # reports whatever sign the interpolation of BEAD_FLANK happens to land on.  It
    # read -0.002 mm and called a working seat a jam.  The question worth asking is
    # whether the gap OPENS going aft, which is what this now measures.
    worst, worst_s = 1e9, None
    s = S_CROWN + 0.25
    while s <= S_BEAD_END:
        r_sled = (R_CROWN - (s - S_CROWN) / (S_HEAD_AFT - S_CROWN)
                  * (R_CROWN - R_SHELL_O)) if s <= S_HEAD_AFT else R_SHELL_O
        gap = free_radius(s) - r_sled
        if gap < worst:
            worst, worst_s = gap, s
        s += 0.25
    ck(worst > 0.0,
       f"aft of the seat the sled stays clear of the bead by at least "
       f"{worst:.3f} mm (worst at s {worst_s:.2f}), so it seats on the crown and "
       f"nothing else",
       f"the sled fouls the bead by {-worst:.3f} mm at s {worst_s:.2f} -- it will "
       f"jam before the crown ever touches")

    print("-- the trough's opening against the cord duct")
    th_open = math.degrees(math.acos(min(1.0, X_OPEN / R_SHELL_O)))
    ck(th_open > DUCT_HALF_ANG,
       f"the trough is open over theta +/-{th_open:.1f} deg, clearing the duct's "
       f"+/-{DUCT_HALF_ANG:.0f} deg by a factor of {th_open/DUCT_HALF_ANG:.1f}",
       f"the trough's opening (+/-{th_open:.1f} deg) is narrower than the duct's "
       f"+/-{DUCT_HALF_ANG:.0f} deg -- the sled will foul at s 46")
    # The deck plate's OWN material against the duct.  The old form was
    #     DECK_X_TOP < 0.0 and math.hypot(DECK_X_TOP, 0.0) < R_DUCT_INNER
    # and its second conjunct is just |DECK_X_TOP| < 21.10, which gets LOOSER as
    # the deck rises and can only ever fire on a LOWER.  So the thing actually
    # stopping a raise was the bare sign test, wearing a message that blamed the
    # duct.  State what is true instead: the duct sector is +/-DUCT_HALF_ANG about
    # theta 0, i.e. a set of directions that requires x > 0, so a plate whose
    # highest face sits at negative x has no material in that sector at ANY radius.
    #
    # That argument covers the DECK, and since the slide it no longer covers the whole
    # part: the two screw lugs stand to x +3.0, on the far side of the axis from the
    # deck, and "x < 0" says nothing about them.  What saves them is the other
    # coordinate -- they are 16.0 mm out in y at their nearest, so their closest
    # approach to theta 0 is atan2(16.0, 3.0) = 79.4 deg, nowhere near the duct's 12.
    # Both halves are stated here because dropping the second one is exactly the kind
    # of silent gap a raised deck or a taller lug would walk into.
    th_lug = math.degrees(math.atan2(LUG_Y_O - LUG_DEPTH, LUG_X_TOP))
    ck(DECK_X_TOP < 0.0 and th_lug > DUCT_HALF_ANG,
       f"the deck's top face is at x {DECK_X_TOP:.1f} < 0, so no part of it lies in "
       f"the duct's sector (theta +/-{DUCT_HALF_ANG:.0f} deg needs x > 0) at any "
       f"radius -- {-DECK_X_TOP:.2f} mm of margin to the axis; the lugs do reach "
       f"x {LUG_X_TOP:+.1f} but sit at theta {th_lug:.1f} deg or more",
       (f"the deck's top face has reached x {DECK_X_TOP:.1f} >= 0, so the plate "
        f"itself -- not just what rides on it -- now needs checking against the duct"
        if DECK_X_TOP >= 0.0 else
        f"a lug corner (x {LUG_X_TOP:+.1f}, y {LUG_Y_O - LUG_DEPTH:.1f}) is at "
        f"theta {th_lug:.1f} deg, inside the duct's +/-{DUCT_HALF_ANG:.0f}"))
    # The tallest thing ON the deck against the duct.  This is NOT the conservative
    # proxy it looks like; two independent readings of this file called it one
    # before the mesh settled the question.  The tempting objection is that the
    # battery bay (s 128.0..193.2) never overlaps the duct (s 46.0..63.0), so the
    # cell is never at the duct's station.  That is FALSE, because the sled is
    # inserted from the FRONT, tail first, ALREADY POPULATED: an item at sled
    # station z sweeps every tube station in [0, z] on the way home, so the cell
    # passes s 46..63 on every single assembly.  bay_verify.py's insertion sweep
    # is built on exactly that model.
    # Measured confirmation, bisected on Mbody.stl cross-sections: the cell's top
    # corner touches the duct floor (r 21.0966 at s 56.50, theta 1.25) at
    # DECK_RISE 14.476, against the 14.50 this arithmetic gives.  The 0.024 mm
    # difference is cos(1.25 deg) plus mesh faceting.  The test is near-exact.
    x_top = DECK_X_TOP + BATT_H_MAX
    ck(x_top < R_DUCT_INNER,
       f"the tallest cell on the deck reaches x {x_top:.1f}, inboard of the duct's "
       f"r {R_DUCT_INNER:.2f} by {R_DUCT_INNER - x_top:.2f} mm",
       f"the tallest cell reaches x {x_top:.1f} and hits the duct at "
       f"r {R_DUCT_INNER:.2f}")

    print("-- the deck, and what has to sit on it")
    # Measured at the deck's TOP face against the shell's INNER wall, because that
    # is the rectangle a board actually gets.  sqrt(R_SHELL_O^2 - DECK_X_BOT^2)
    # reads 2.4 mm wider and describes nothing real: the deck is clipped short of
    # the OD, and anything lying on it is bounded by the bore, not by the outside
    # of the shell.  There is no fence to leave room for -- ribs replaced the
    # fence posts (see above) and the spare width is what the cable ties use.
    half_w = math.sqrt(max(0.0, R_SHELL_I ** 2 - DECK_X_TOP ** 2))
    widest = max(ESP32_W, BATT_W_MAX)
    ck(2 * half_w > widest + 4.0,
       f"the deck offers {2*half_w:.1f} mm of usable width at its top face, "
       f"taking the widest item ({widest:.1f} mm) with "
       f"{2*half_w - widest:.1f} mm to spare",
       f"the deck offers only {2*half_w:.1f} mm at its top face -- the widest "
       f"item ({widest:.1f} mm) does not fit between the shell walls")
    # DECK_T is a real printed thickness and a whole number of layers.  It used to
    # be DERIVED from the two face coordinates and referenced by no check at all,
    # so editing one coordinate changed the plate's thickness silently and a
    # zero-thickness deck passed this entire file.  It is primary now; this is what
    # keeps it honest.
    n_layers = DECK_T / LAYER_H
    ck(DECK_T >= WALL_MIN and abs(n_layers - round(n_layers)) < 1e-6,
       f"the deck is {DECK_T:.2f} mm thick: {round(n_layers)} whole layers at "
       f"LAYER_H {LAYER_H:.1f}, and {DECK_T/WALL_MIN:.1f}x WALL_MIN",
       f"the deck is {DECK_T:.2f} mm thick, which is either under WALL_MIN "
       f"({WALL_MIN:.2f}) or not a whole number of {LAYER_H:.1f} mm layers "
       f"({n_layers:.3f})")
    # The deck against the trough's OWN opening plane.  Nothing related these two
    # before, yet X_OPEN is the plane that cuts the trough open: a deck at or above
    # it would be partly removed by the very operation that makes the bay loadable,
    # and the BMP ribs standing on the deck are shaved first, being the tallest
    # fixed feature on it.  Measured onset of rib shaving: DECK_RISE 13.50.
    x_rib_top = DECK_X_TOP + RIB_H_BMP
    ck(x_rib_top < X_OPEN,
       f"the tallest fixed feature on the deck (a BMP rib, top face "
       f"x {x_rib_top:.2f}) stays {X_OPEN - x_rib_top:.2f} mm below the trough's "
       f"opening plane x {X_OPEN:.1f}, so the cut that opens the bay touches "
       f"neither the deck nor its ribs",
       f"a BMP rib reaches x {x_rib_top:.2f} and the trough is cut away above "
       f"x {X_OPEN:.1f} -- the opening cut shaves {x_rib_top - X_OPEN:.2f} mm off "
       f"the ribs")
    # --- the slide ------------------------------------------------------------
    # The plate has to fit through the head's bore, because the head is a complete
    # ring and the bore is the hole it goes through.  This is the check that rules
    # out the obvious alternative design -- grooves cut into the shell wall, which
    # would put the plate's edges outboard of r 27.45 and make it uninsertable.
    ck(R_PLATE < R_SHELL_I,
       f"the plate's edge (r {R_PLATE:.2f}) passes the head ring's bore "
       f"(r {R_SHELL_I:.2f}) with {SLIDE_CLR_R:.2f} mm to spare, so the rails "
       f"stand PROUD of the bore and the plate is narrower than the hole",
       f"the plate reaches r {R_PLATE:.2f} against a bore of {R_SHELL_I:.2f} -- it "
       f"cannot pass the head ring at all")
    # And the capture: the plate's edge must reach OUTBOARD of the rails' inner
    # face, or the rails are two ledges the plate rests on and lifts off.
    ck(R_RAIL_I < R_PLATE and R_RAIL_I > 0.0,
       f"the plate's edge overlaps the rails by {R_PLATE - R_RAIL_I:.2f} mm "
       f"radially (edge r {R_PLATE:.2f}, rail face r {R_RAIL_I:.2f}), so it is "
       f"captured in x and cannot be lifted out of the pocket",
       f"the rails' inner face (r {R_RAIL_I:.2f}) is not inboard of the plate's "
       f"edge (r {R_PLATE:.2f}) -- there is no overlap, so nothing retains the "
       f"plate radially")
    ck(RAIL_T >= WALL_MIN and R_SHELL_I - R_RAIL_I >= WALL_MIN,
       f"each rail is {RAIL_T:.2f} mm thick in x and stands "
       f"{R_SHELL_I - R_RAIL_I:.2f} mm proud of the bore, both over WALL_MIN "
       f"({WALL_MIN:.2f})",
       f"a rail is {RAIL_T:.2f} mm thick and stands "
       f"{R_SHELL_I - R_RAIL_I:.2f} mm proud, one of which is under WALL_MIN "
       f"({WALL_MIN:.2f})")
    # The POCKET's top face is what the stop plug is bounded by, and the stop runs
    # aft to S_TAIL straight through the bosses' station range -- so the pocket,
    # unlike the upper rail, has to be clear of the boss x-band on its own.
    x_boss_band = (R_SHELL_I + FUSE_MERGE) * math.sin(math.radians(BOSS_HALF_ANG))
    ck(POCKET_X_TOP < -x_boss_band,
       f"the pocket's top face (x {POCKET_X_TOP:.2f}) stays "
       f"{-x_boss_band - POCKET_X_TOP:.2f} mm below the bosses' x-band "
       f"(|x| <= {x_boss_band:.3f}), so the stop plug can run aft to S_TAIL "
       f"without touching a boss",
       f"the pocket's top face (x {POCKET_X_TOP:.2f}) is inside the bosses' x-band "
       f"(|x| <= {x_boss_band:.3f}) -- the stop plug at s {S_STOP:.1f}..{S_TAIL:.1f} "
       f"would fuse into both bosses")
    # The upper rail's top IS inside that band, which is why it stops early.  This
    # is a conditional guard on purpose: it fires only in the case that matters.
    ck(RAIL_U_X_TOP < -x_boss_band or S_RAIL_U_1 <= S_BOSS_RAMP,
       f"the upper rail's top (x {RAIL_U_X_TOP:.2f}) is inside the bosses' x-band, "
       f"so it ends at s {S_RAIL_U_1:.1f}, forward of the ramp at "
       f"s {S_BOSS_RAMP:.1f}",
       f"the upper rail reaches x {RAIL_U_X_TOP:.2f}, inside the bosses' x-band "
       f"(|x| <= {x_boss_band:.3f}), AND runs aft to s {S_RAIL_U_1:.1f}, past the "
       f"ramp at s {S_BOSS_RAMP:.1f} -- it will fuse into both bosses")
    # The stop, the plate's aft face and the lugs, in order along the axis.
    ck(S_LUG_0 < S_SCREW < S_LUG_1 <= S_PLATE_AFT < S_STOP < S_TAIL,
       f"along the axis: lug {S_LUG_0:.1f}..{S_LUG_1:.1f} with the screw at "
       f"s {S_SCREW:.1f} ({S_LUG_1 - S_SCREW:.1f} mm inside its aft end), plate "
       f"ends {S_PLATE_AFT:.1f}, stop {S_STOP:.1f}..{S_TAIL:.1f}",
       f"the aft end is out of order: lug {S_LUG_0:.1f}..{S_LUG_1:.1f}, screw "
       f"{S_SCREW:.1f}, plate aft {S_PLATE_AFT:.1f}, stop {S_STOP:.1f}, tail "
       f"{S_TAIL:.1f}")
    # The lug slides the whole length of the bay UNDER the bosses, so what has to
    # clear the boss's inner radius is the lug's furthest point INSIDE THE BOSS'S
    # OWN AZIMUTH SECTOR -- and that is neither the lug's top corner nor its bottom
    # one.  This check used to read hypot(LUG_X_TOP, LUG_Y_O), the top-outboard
    # corner, and that is simply the wrong point: it is at theta 86.1 deg, well
    # inside the sector, but the outboard FACE y = LUG_Y_O keeps going as x falls,
    # and radius on that face grows with |x|.  The face leaves the sector at
    # |x| = LUG_Y_O*tan(9 deg) = 3.48, and hypot(3.48, 22.0) = 22.27 is 0.20 mm
    # further out than the corner the old check measured.  Reading the corner made
    # the clearance look like 0.75 mm when at LUG_Y_O 22.2 it was really 0.52 --
    # under LUG_CLR, i.e. the old numbers did not pass their own test.
    #
    # The lug's BOTTOM-outboard corner (x -6.5, y 22.0) is further out still,
    # r 22.94, and it is NOT a problem: it sits at theta 106.4 deg, 7.4 deg outside
    # the sector, where there is no boss to hit.  Radius alone cannot tell those two
    # points apart, which is exactly why this is clipped by azimuth first.
    x_sector = LUG_Y_O * math.tan(math.radians(BOSS_HALF_ANG))
    x_lo = max(LUG_X_BOT, -x_sector)
    x_hi = min(LUG_X_TOP, x_sector)
    x_worst = x_lo if abs(x_lo) > abs(x_hi) else x_hi
    r_lug = math.hypot(x_worst, LUG_Y_O)
    ck(r_lug < R_BOSS_I - LUG_CLR,
       f"the lug's worst point inside the bosses' sector (x {x_worst:+.3f}, "
       f"y {LUG_Y_O:.1f}, theta "
       f"{math.degrees(math.atan2(LUG_Y_O, x_worst)):.1f} deg) is at "
       f"r {r_lug:.3f}, {R_BOSS_I - r_lug:.3f} mm inside the bosses' inner face "
       f"(r {R_BOSS_I:.1f}) that it has to slide under",
       f"the lug's worst point reaches r {r_lug:.3f} against the bosses' "
       f"r {R_BOSS_I:.1f} -- clearance {R_BOSS_I - r_lug:.3f} mm is under the "
       f"{LUG_CLR:.2f} mm this design asks for, so the plate jams at s "
       f"{S_BOSS_0:.1f}")
    # The pilot is bored on the screw's axis, x = 0, and the thread forms outward to
    # an M3's major radius.  There has to be a wall left above it.
    over_thread = LUG_X_TOP - 3.0 / 2.0
    ck(over_thread >= WALL_MIN and LUG_X_BOT < -3.0 / 2.0,
       f"the lug leaves {over_thread:.2f} mm of material over the M3's crest "
       f"(top x {LUG_X_TOP:+.1f} against a 1.50 mm major radius on the x = 0 "
       f"axis), over WALL_MIN ({WALL_MIN:.2f}), and {-1.5 - LUG_X_BOT:.2f} mm "
       f"under it",
       f"the lug tops out at x {LUG_X_TOP:+.1f} and the M3's thread forms out to "
       f"x +1.50, leaving {over_thread:.2f} mm above the crest -- under WALL_MIN "
       f"({WALL_MIN:.2f}), so the screw splits the lug lengthwise on the first turn")
    ck(LUG_X_TOP < X_OPEN and S_LUG_0 > S_BATT_1,
       f"the lug tops out at x {LUG_X_TOP:+.1f}, below the trough's opening plane "
       f"(x {X_OPEN:.1f}), and starts at s {S_LUG_0:.1f}, aft of the battery bay's "
       f"end ({S_BATT_1:.1f})",
       f"the lug (top x {LUG_X_TOP:+.1f}, from s {S_LUG_0:.1f}) either breaks the "
       f"opening plane x {X_OPEN:.1f} or runs into the battery bay ending at "
       f"s {S_BATT_1:.1f}")
    # The screw has to end up INSIDE the lug, not through it and out the far side.
    # Measured from the AIRFRAME's OD, where the head bears -- not from the support's
    # shell OD, which is what this used to do.  The support floats 1.96 mm inside the
    # tube's bore aft of the bead (R_SHELL_O 29.45 had to pass the bead throat), so
    # a reach measured from r 29.45 is short by the tube wall plus that gap: 3.30 mm
    # of the screw unaccounted for, which turned a 15.75 mm requirement into a
    # 12.45 mm one and would have passed an M3 x 14 that cannot reach the lug.
    r_tip = R_OD - SCREW_L                   # 16.745, where the tip ends up
    thread = LUG_Y_O - r_tip                 # 5.255 mm of thread formed in the lug
    ck(thread >= 4.0 and r_tip > LUG_Y_O - LUG_DEPTH,
       f"each M3 x {SCREW_L:.0f}, head on the tube's OD (r {R_OD:.3f}), crosses "
       f"{R_OD - R_WORK:.2f} mm of airframe, {R_WORK - R_SHELL_O:.2f} mm of gap, "
       f"{R_SHELL_O - R_BOSS_I:.2f} mm of boss and {R_BOSS_I - LUG_Y_O:.2f} mm of "
       f"air, then forms {thread:.2f} mm of thread in the lug and stops at "
       f"r {r_tip:.3f}, {r_tip - (LUG_Y_O - LUG_DEPTH):.3f} mm short of its "
       f"inboard face",
       f"an M3 x {SCREW_L:.0f} puts its tip at r {r_tip:.3f}: "
       + (f"only {thread:.2f} mm of thread in a lug whose face is at "
          f"{LUG_Y_O:.1f}" if thread < 4.0 else
          f"straight through a lug that ends at r {LUG_Y_O - LUG_DEPTH:.1f}"))
    # And the pilot's STATION.  The plate is drawn SLIDE_GAP_Z short of the stop, so
    # pushed home it sits that much AFT of where it was drawn -- and its lug pilots
    # go with it.  Drawn at S_SCREW they would seat at S_SCREW + 0.5 and miss the
    # boss's pilot by the whole gap, in a hole only 2.5 mm across.  So they are drawn
    # that much FORWARD, and the alignment is exact in the one state that matters:
    # seated.  This is the entire reason the pilots are 3.0 mm from the stop and not
    # in the middle of the plate -- the error being cancelled here is a constant, but
    # only if nothing 177 mm long is between the two features.
    ck(abs((S_LUG_PILOT + SLIDE_GAP_Z) - S_SCREW) < 1e-9,
       f"the lug pilots are drawn at s {S_LUG_PILOT:.1f}, which is "
       f"{SLIDE_GAP_Z:.1f} mm forward of the bosses' s {S_SCREW:.1f} -- exactly the "
       f"distance the plate travels aft as it seats, so seated they line up",
       f"the lug pilots are drawn at s {S_LUG_PILOT:.1f}; seated they land at "
       f"{S_LUG_PILOT + SLIDE_GAP_Z:.1f} against the bosses' {S_SCREW:.1f}")

    ck(S_BATT_1 < S_BOSS_0,
       f"the battery bay (to s {S_BATT_1:.1f}) ends before the screw bosses "
       f"start (s {S_BOSS_0:.1f})",
       f"the battery bay (to s {S_BATT_1:.1f}) runs into the screw bosses at "
       f"s {S_BOSS_0:.1f}")
    ck(S_ESP32_1 < S_BATT_0,
       f"the ESP32 bay (to s {S_ESP32_1:.1f}) ends before the battery bay "
       f"(s {S_BATT_0:.1f})",
       f"the ESP32 bay (to s {S_ESP32_1:.1f}) overlaps the battery bay at "
       f"s {S_BATT_0:.1f}")
    ck(S_BMP_1 < S_ESP32_0,
       f"the BMP280 pad (to s {S_BMP_1:.1f}) ends before the ESP32 "
       f"(s {S_ESP32_0:.1f})",
       f"the BMP280 pad (to s {S_BMP_1:.1f}) overlaps the ESP32 at "
       f"s {S_ESP32_0:.1f}")
    # the deck's USABLE half-width is at its top face, not its bottom: a feature is
    # only on the deck if it is on the deck all the way through it
    # R_PLATE, not R_SHELL_I: the deck is a separate part now and it is clipped
    # SLIDE_CLR_R short of the bore so it can slide.  Measuring its width against
    # the bore overstates it by 0.40 mm of radius -- 0.41 mm of half-width here --
    # which is small but is on the wrong side, and every slot and vent placed near
    # the edge is bounded by this number.
    half_w_top = math.sqrt(max(0.0, R_PLATE ** 2 - DECK_X_TOP ** 2))
    for y, lbl in ((STRAP_Y_MAIN, "main"), (STRAP_Y_BMP, "BMP")):
        ck(y + STRAP_SLOT_Y / 2 < half_w_top,
           f"the {lbl} strap slots at y +/-{y:.1f} sit inside the deck's usable "
           f"{half_w_top:.2f} mm half-width",
           f"the {lbl} strap slots at y +/-{y:.1f} run off the deck's top face at "
           f"{half_w_top:.2f}")
    for s_st, a, b, lbl in ([(s, S_BATT_0, S_BATT_1, "battery")
                             for s in STRAP_STATIONS_BATT]
                            + [(s, S_ESP32_0, S_ESP32_1, "ESP32")
                               for s in STRAP_STATIONS_ESP32]
                            + [(s, S_BMP_0, S_BMP_1, "BMP280")
                               for s in STRAP_STATIONS_BMP]):
        ck(a < s_st < b,
           f"a strap crosses the {lbl} bay at s {s_st:.1f}",
           f"the {lbl} strap at s {s_st:.1f} is outside that bay "
           f"({a:.1f}..{b:.1f}) and holds nothing")

    print("-- ribs, pin slots and ports")
    ck(2 * (RIB_Y_BMP - RIB_T / 2) > BMP_W + 0.5,
       f"the BMP ribs leave a {2*(RIB_Y_BMP - RIB_T/2):.2f} mm gap for an "
       f"{BMP_W:.1f} mm board ({2*(RIB_Y_BMP - RIB_T/2) - BMP_W:.2f} mm of slop)",
       f"the BMP ribs leave only {2*(RIB_Y_BMP - RIB_T/2):.2f} mm for an "
       f"{BMP_W:.1f} mm board")
    ck(RIB_H_BMP < BMP_H,
       f"the BMP ribs ({RIB_H_BMP:.1f} mm) are lower than the board's "
       f"{BMP_H:.1f} mm stack, so a tie over them still presses the BOARD",
       f"the BMP ribs ({RIB_H_BMP:.1f} mm) stand above the {BMP_H:.1f} mm board -- "
       f"a tie would clamp the ribs and leave the board loose")
    ck(RIB_Y_BMP + RIB_T / 2 < STRAP_Y_BMP - STRAP_SLOT_Y / 2,
       f"the BMP ribs (out to y {RIB_Y_BMP + RIB_T/2:.2f}) are inboard of their "
       f"strap slots (from y {STRAP_Y_BMP - STRAP_SLOT_Y/2:.2f}), so the tie can "
       f"get around the board",
       f"the BMP ribs reach y {RIB_Y_BMP + RIB_T/2:.2f} and the strap slots start "
       f"at {STRAP_Y_BMP - STRAP_SLOT_Y/2:.2f} -- the tie cannot pass outside them")
    ck(2 * (RIB_Y_BMP - RIB_T / 2) < ESP32_W,
       f"the BMP ribs' {2*(RIB_Y_BMP - RIB_T/2):.2f} mm gap is narrower than the "
       f"ESP32 ({ESP32_W:.1f} mm), which is why the ESP32 does not share them",
       f"the BMP ribs would also take the ESP32, so two rib pairs is one too many")
    ck(S_RIB_BMP_1 <= S_ESP32_0 and S_PIN_SLOT_1 <= S_BATT_0,
       f"the ribs end at s {S_RIB_BMP_1:.1f} and the pin slots at "
       f"s {S_PIN_SLOT_1:.1f}, so the battery bay ({S_BATT_0:.1f}+) is bare deck",
       f"a rib or pin slot runs into the battery bay at s {S_BATT_0:.1f}, which "
       f"would size the bay for a cell nobody has chosen")
    # the pin slot has to catch BOTH candidate header spacings
    for y_pins, board in ((12.7, "38-pin DevKitC"), (11.4, "30-pin DevKit V1")):
        ck(PIN_SLOT_Y - PIN_SLOT_W / 2 < y_pins < PIN_SLOT_Y + PIN_SLOT_W / 2,
           f"the {board}'s headers at y +/-{y_pins:.1f} drop into the slot "
           f"({PIN_SLOT_Y - PIN_SLOT_W/2:.2f}..{PIN_SLOT_Y + PIN_SLOT_W/2:.2f})",
           f"the {board}'s headers at y +/-{y_pins:.1f} miss the slot "
           f"({PIN_SLOT_Y - PIN_SLOT_W/2:.2f}..{PIN_SLOT_Y + PIN_SLOT_W/2:.2f}) "
           f"and would be crushed against the deck")
    # and the channel under the deck has to be deeper than the pins are long
    depth = math.sqrt(max(0.0, R_SHELL_I ** 2 - PIN_SLOT_Y ** 2)) + DECK_X_BOT
    ck(depth > ESP32_H_BOT + 1.0,
       f"under the pin slots the channel is {depth:.2f} mm deep against "
       f"{ESP32_H_BOT:.1f} mm of header pin",
       f"the channel is only {depth:.2f} mm deep under the pin slots and the pins "
       f"are {ESP32_H_BOT:.1f} mm -- they will bottom out")
    ck(PIN_SLOT_Y + PIN_SLOT_W / 2 < STRAP_Y_MAIN - STRAP_SLOT_Y / 2,
       f"the pin slots (to y {PIN_SLOT_Y + PIN_SLOT_W/2:.2f}) do not run into the "
       f"strap slots (from y {STRAP_Y_MAIN - STRAP_SLOT_Y/2:.2f})",
       f"the pin slots and strap slots overlap in y and would merge into one void")
    for s_p in BMP_PORT_STATIONS:
        ck(S_BMP_0 < s_p < S_BMP_1,
           f"a static port at s {s_p:.1f} is under the BMP280 pad",
           f"the static port at s {s_p:.1f} is outside the BMP pad "
           f"{S_BMP_0:.1f}..{S_BMP_1:.1f}")
    for s_v in VENT_STATIONS:
        clashes = [n for n, (a, b) in (("BMP pad", (S_BMP_0, S_BMP_1)),
                                       ("ESP32", (S_ESP32_0, S_ESP32_1)),
                                       ("battery", (S_BATT_0, S_BATT_1)))
                   if a - VENT_D / 2 < s_v < b + VENT_D / 2]
        ck(VENT_Y - VENT_D / 2 > max(ESP32_W, BATT_W_MAX) / 2 or not clashes,
           f"the vent at s {s_v:.1f} sits at y +/-{VENT_Y:.1f}, outboard of the "
           f"widest footprint (|y| <= {max(ESP32_W, BATT_W_MAX)/2:.1f}) whatever it "
           f"shares a station with",
           f"the vent at s {s_v:.1f} is under {', '.join(clashes)} and its "
           f"y +/-{VENT_Y:.1f} does not clear the footprint")
        ck(VENT_Y + VENT_D / 2 < half_w_top,
           f"the vent at y +/-{VENT_Y:.1f} stays on the deck all the way through "
           f"it (usable half-width {half_w_top:.2f} mm)",
           f"the vent at y +/-{VENT_Y:.1f} reaches "
           f"{VENT_Y + VENT_D/2:.2f} and breaks out of the deck's top face at "
           f"{half_w_top:.2f}")
        ck(VENT_Y - VENT_D / 2 > RIB_Y_BMP + RIB_T / 2,
           f"the vent at y +/-{VENT_Y:.1f} clears every rib "
           f"(outermost face y {RIB_Y_BMP + RIB_T/2:.2f})",
           f"the vent at y +/-{VENT_Y:.1f} undercuts a rib's foot")

    # WHY THE BOSSES AND THE BATTERY DO NOT FIGHT, which is not the station test
    # above.  S_BATT_1 clears S_BOSS_0 by only 0.8 mm, and it would be wrong to let
    # the design rest on that: the real separation is AZIMUTHAL.  The bosses are a
    # +/-9 deg sector at theta 90/270 reaching in to r 23.0, so their closest
    # approach to the centreline is 23.0*sin(81 deg) = 22.7 mm, while the widest
    # cell only reaches |y| = 15.0.  The boss is outboard of every payload item at
    # every station, so a cell longer than the bay reads as sticking out of the
    # tail, not as an interference.
    y_boss = R_BOSS_I * math.sin(math.radians(90.0 - BOSS_HALF_ANG))
    ck(y_boss > BATT_W_MAX / 2 + 2.0,
       f"the bosses come no closer to the centreline than y {y_boss:.2f}, clearing "
       f"the widest cell (|y| {BATT_W_MAX/2:.1f}) by {y_boss - BATT_W_MAX/2:.2f} mm "
       f"-- they are separated by AZIMUTH, not by station",
       f"the bosses reach y {y_boss:.2f} and the widest cell reaches "
       f"{BATT_W_MAX/2:.1f} -- they overlap in space, so the station clearance is "
       f"load-bearing and 0.8 mm of it is not enough")
    # The bosses against the deck plate, in the coordinate that decides it: x.
    # The old form was `abs(DECK_X_TOP) + 1.0 < R_BOSS_I`, i.e. 13.0 < 23.0, which
    # compares an x against a RADIUS.  It reads as 10 mm of headroom and passes for
    # every deck height up to x = +22, so it stayed green while the deck climbed
    # bodily into the bosses.  A boss is an annular sector, so its x-extent is
    # bounded by r*sin(BOSS_HALF_ANG) at its OUTER radius -- a narrow band
    # straddling the axis, nothing like a radius test.
    #
    # This mattered little while the deck and the bosses were one printed part: a
    # boss that merely fused into a fixed deck was harmless.  It matters now,
    # because a boss standing in a SLIDING plate's swept volume stops the plate
    # before it is home.  (The screw pilots' band, |x| <= SCREW_PILOT_D/2 = 1.25 at
    # s 201.5, lies wholly inside this one and is covered by the same test -- so
    # bay_sled.py's remark that the deck is "nowhere near the pilot's axis" is
    # guarded here rather than asserted there.)
    x_boss = (R_SHELL_I + FUSE_MERGE) * math.sin(math.radians(BOSS_HALF_ANG))
    ck(DECK_X_TOP < -x_boss,
       f"the deck plate (x {DECK_X_BOT:.1f}..{DECK_X_TOP:.1f}) stays clear of the "
       f"bosses' x-band (|x| <= {x_boss:.3f}) by {-x_boss - DECK_X_TOP:.2f} mm, so "
       f"nothing at s {S_BOSS_RAMP:.0f}..{S_TAIL:.0f} stands in the plate's path",
       f"the deck plate reaches x {DECK_X_TOP:.1f} and the bosses occupy "
       f"|x| <= {x_boss:.3f} over s {S_BOSS_RAMP:.0f}..{S_TAIL:.0f} -- they overlap, "
       f"so a sliding plate jams {S_TAIL - S_BOSS_RAMP:.0f} mm short of home "
       f"(DECK_RISE {DECK_RISE:.2f} is past the {-x_boss - DECK_X_BOT_0 - DECK_T:.2f} "
       f"mm ceiling this sets)")

    print("-- the aft screws")
    ck(S_BOSS_0 < S_SCREW < S_BOSS_1,
       f"the screws at s {S_SCREW:.1f} land inside the bosses "
       f"({S_BOSS_0:.1f}..{S_BOSS_1:.1f})",
       f"the screws at s {S_SCREW:.1f} are outside the bosses "
       f"({S_BOSS_0:.1f}..{S_BOSS_1:.1f}) -- they thread into a 2 mm shell")
    ck(free_radius(S_SCREW) > R_SHELL_O,
       f"at s {S_SCREW:.1f} the bore is r {free_radius(S_SCREW):.3f}, so the "
       f"screws pass a plain {WALL_WORK:.3f} mm wall",
       f"the screw station s {S_SCREW:.1f} is not in the plain bore")
    thread = R_SHELL_O - R_BOSS_I
    ck(thread > 4.0,
       f"each screw threads {thread:.2f} mm into the boss",
       f"each screw only gets {thread:.2f} mm of thread")
    ck(all(abs((t - DUCT_THETA + 180) % 360 - 180) > DUCT_HALF_ANG
           for t in SCREW_THETA),
       f"the screws at theta {SCREW_THETA} are clear of the duct sector",
       f"a screw at theta {SCREW_THETA} pierces the cord duct")
    n_screw_shear = 2 * math.pi * (3.0 / 2) ** 2 * 25.0
    ck(n_screw_shear / F_BOOST_N > 10.0,
       f"2 x M3 in shear is {n_screw_shear:.0f} N against a {F_BOOST_N:.2f} N "
       f"boost load: {n_screw_shear/F_BOOST_N:.0f}x",
       f"2 x M3 gives only {n_screw_shear/F_BOOST_N:.1f}x on boost")

    print("-- printability: TWO parts, two poses")
    ck(R_CROWN >= R_SHELL_O,
       f"radius never increases going aft through the head "
       f"({R_CROWN:.2f} -> {R_SHELL_O:.2f}), so the crown is self-supporting with "
       f"the forward face on the bed",
       "the head grows in radius going aft -- the crown would need support")
    # the boss's outer face is buried FUSE_MERGE into the wall, so the ramp runs
    # from there, not from the bore -- which makes it slightly steeper than the
    # nominal figure and is the number that actually gets printed
    ramp = math.degrees(math.atan2(R_SHELL_I + FUSE_MERGE - R_BOSS_I,
                                   S_BOSS_0 - S_BOSS_RAMP))
    ck(ramp < 50.0,
       f"the boss ramps in at {ramp:.1f} deg from the axis, self-supporting",
       f"the boss ramp is {ramp:.1f} deg -- too steep to print unsupported")
    ck(support_h() < BED,
       f"the support stands {support_h():.2f} mm tall on the bed, inside the "
       f"{BED:.0f} mm it has",
       f"the support is {support_h():.2f} mm, taller than the {BED:.0f} mm bed")
    across, along, tall = plate_footprint()
    ck(max(across, along) < BED,
       f"the plate lies FLAT at {across:.2f} x {along:.2f} mm and only "
       f"{tall:.2f} mm tall -- a different pose from the support's, and the pose "
       f"the split was for: nothing on this part overhangs lying down",
       f"the plate's flat footprint is {across:.2f} x {along:.2f} mm, outside "
       f"the {BED:.0f} mm bed -- it would have to print standing up, which is "
       f"the pose whose ramps and bridges the split removed")
    ck(tall < across and tall < along,
       f"and it is the FLAT dimension that is smallest ({tall:.2f} mm), so lying "
       f"down is the pose with the largest bed contact and the shortest build",
       f"the plate is {tall:.2f} mm in x against {across:.2f} x {along:.2f} on "
       f"the bed -- it is no longer plate-shaped, so 'print it flat' needs "
       f"re-deciding rather than re-asserting")

    print()
    if fails:
        raise AssertionError(f"{len(fails)} check(s) failed:\n  - "
                             + "\n  - ".join(fails))
    print("all checks passed")


if __name__ == "__main__":
    self_check()
