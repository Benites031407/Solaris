"""Every number for the Helios 38 mm casting tooling: three printed molds for the three
silicone pieces that cast one BATES segment.

What one segment is cast in (as used, z = 0 on the table):
  silicone BASE    a cup that takes the bottom of the casting tube.  Its floor has a centre
                   hole that grips the sleeve and centres the core at the bottom.
  silicone SLEEVE  a plain Ø14 tube around the aluminium core rod, standing on the table,
                   through the base, up the middle of the tube and out through the cap.
  casting tube     the 0.2 mm liner itself, cut to the segment length.  The grain is cast
                   in it, so its OD comes out inhibited and bonded (memorial 16.2, item 1).
  silicone CAP     a cup over the top of the tube.  Its hole grips the sleeve and centres
                   the core at the top; five vents let excess propellant out.
Both grain faces form on silicone, flush with the tube ends: segment length = tube length.

The base and cap molds are cups whose boss stands in for the casting tube: the base sits
in its mold upside down, the cap the right way up.  Either way the pour surface (the only
surface a mold doesn't form) is the outside face that never touches propellant.  The
sleeve mold is a clamshell standing on end, and the sleeve cures on the real core rod: its
bore fits whatever the rod actually measures.  Only the rod seat and guide depend on D_ROD.

Sources:
  [P]  Motor_KNSB_38mm_Calculos_V10_corrigido.xlsx, sheet 2_Geometria_Grao
  [M]  Memorial de calculo da tubeira, 27/09/2026 (physical stack 3 x 67.5, cap. 13.3)
  [A]  assumed here -- check it against the real parts before printing
"""

import math

# ---- the grain and the tube it is cast in ---------------------------------------------
D_CORE = 14.0            # grain port = sleeve OD [P 2!C13]
D_GRAIN = 34.4           # grain OD = casting-tube ID [P 2!C10]
T_TUBE = 0.2             # casting tube = liner wall [P 2!C31]
D_TUBE = D_GRAIN + 2 * T_TUBE        # 34.8 tube OD; the case bore is 35.0 [P 2!C8]
L_SEG = 67.5             # physical segment, 3 of them with spacers [M 13.3]
L_SEG_MAX = 70.0         # the spreadsheet's segment [P 2!C14]; the sleeve reaches past it

# ---- core rod ---------------------------------------------------------------------------
D_ROD = 10.0             # [A] aluminium core rod.  Change it and regenerate if yours differs.
L_ROD_MIN = 110.0        # shortest rod that sits in the sleeve mold's seat and clears its guide

# ---- silicone base and cap, as used -----------------------------------------------------
SOCKET_DEPTH = 12.0      # how far the tube goes into the base and into the cap
CUP_WALL = 3.5           # silicone around the tube
D_CUP = D_TUBE + 2 * CUP_WALL        # 41.8
MOUTH_CHAMFER = 1.0      # 45 deg lead-in on the tube socket mouth, inner edge
BASE_FLOOR = 8.0         # silicone under the grain's bottom face; it grips the sleeve over
                         # BASE_FLOOR - BASE_LEADIN = 7 mm
CAP_TOP = 5.0            # silicone over the grain's top face (= the cap's grip length)
GRIP_INTERF = 0.10       # base and cap holes squeeze the sleeve this much, radial
D_GRIP = D_CORE - 2 * GRIP_INTERF    # 13.8 centre holes in the base and cap
BASE_LEADIN = 1.0        # 45 deg chamfer on the base hole, underside only (the sleeve enters there)
N_VENT = 5
D_VENT = 4.0
R_VENT = 12.0            # mid-web: the web runs r 7.0 .. 17.2
VENT_THETA0 = 90.0       # first vent azimuth, deg

# ---- silicone sleeve, as used -----------------------------------------------------------
SLEEVE_STICKOUT = 5.0    # sleeve left above the cap with the longest (70) tube
L_SLEEVE = BASE_FLOOR + L_SEG_MAX + CAP_TOP + SLEEVE_STICKOUT      # 88, table to tip
SLEEVE_TIP_CHAMFER = (D_CORE - D_ROD) / 2.0  # 45 deg bevel on the molded end, the full wall (2.0):
                         # the rod seat's funnel runs straight into it.  That end goes up, into the cap.

# ---- printing allowances (FDM) ----------------------------------------------------------
HOLE_COMP = 0.15         # [A] printed vertical holes come out this much small on the diameter
GROOVE_COMP = 0.10       # [A] ... half-round grooves printed lying down (sleeve mold)
FIT_ROD_SEAT = 0.40      # diametral clearance on the rod in the sleeve mold's bottom seat: the
                         # silicone under the rod has to get out past it as the rod goes in
FIT_ROD_GUIDE = 0.30     # ... in the top guide (net)
FIT_BOX = 0.50           # stand pocket and guide skirt over the closed sleeve mold, per side x2
FIT_KEY = 0.30           # registration cone in its socket, diametral

# ---- printed cup molds (base, cap) ------------------------------------------------------
WALL = 3.0               # plastic around the silicone
FLOOR = 3.0              # plastic under the socket annulus
PIN_PROUD = 1.0          # centre and vent pins stand this far above the rim: holes come out open

# ---- sleeve clamshell -------------------------------------------------------------------
SM_W = 40.0              # closed mold, across the parting plane
SM_T = 12.0              # each half, parting face to back
SM_FLOOR = 3.0           # plastic under the rod seat
ROD_SEAT = 6.0           # rod seat depth below the sleeve's molded tip
KEY_D0, KEY_D1, KEY_H = 6.0, 3.0, 2.5    # registration cone: base dia, tip dia, height
KEY_X = 14.0             # keys and bolts sit this far off the axis
KEY_INSET = 12.0         # bottom key this far up from the bottom end
KEY_STAGGER = 8.0        # top key this much further in from the top end than the bottom key is
                         # from the bottom: a half turned end-for-end lands its cones on flat face
D_BOLT = 3.6             # M3 clearance.  The bolts are REQUIRED: the stand and the guide only
                         # locate the ends (0.25 play a side), they don't hold the seam shut
WASHER_OD = 7.0          # [A] M3 washer; the nut is 6.4 across corners
GUIDE_GAP = 6.0          # guide plate stands this far above the pour surface
GUIDE_PLATE = 4.0
GUIDE_HUB_DROP = 0.0     # hub below the plate (none: it stays 6 mm clear of the pour surface)
GUIDE_HUB_WALL = 0.8     # thin, so a ring of the cavity mouth shows past it through the windows
GUIDE_BAR_W = 6.0        # the two bars that hold the hub
GUIDE_LEDGE = 3.0        # guide sits on this band around the top face's edge
BOX_SKIRT = 8.0          # stand pocket depth / guide skirt depth over the closed mold
BOX_WALL = 2.5
STAND_PLATE = 3.0
STAND_MARGIN = 12.0      # stand plate past the pocket rim: catches drips
BED_CHAMFER = 0.6        # 45 deg on the halves' four bed-face edges: room for elephant foot
MOUTH_LEADIN = 0.8       # 45 deg lead-in on the stand pocket and guide skirt mouths
BORE_CHAMFER = 0.5       # 45 deg on both ends of the guide bore

# ---- derived: BASE MOLD, z = 0 on the print bed (the base upside down) ------------------
ZB_MOUTH = FLOOR                                # tube socket mouth (cup-wall rim, as used)
ZB_FACE = ZB_MOUTH + SOCKET_DEPTH               # boss top = grain bottom face
ZB_RIM = ZB_FACE + BASE_FLOOR                   # pour surface = base underside
ZB_PIN_TOP = ZB_RIM + PIN_PROUD

# ---- derived: CAP MOLD, z = 0 on the print bed (the cap as used, skirt down) ------------
ZC_MOUTH = FLOOR
ZC_FACE = ZC_MOUTH + SOCKET_DEPTH               # boss top = grain top face
ZC_RIM = ZC_FACE + CAP_TOP                      # pour surface = cap top
ZC_PIN_TOP = ZC_RIM + PIN_PROUD

R_BOSS = D_TUBE / 2.0                           # printed OUTER surfaces are nominal
R_CUP = D_CUP / 2.0
R_HEAD = R_CUP + WALL
R_GRIP_PIN = D_GRIP / 2.0
R_VENT_PIN = D_VENT / 2.0

# ---- derived: SLEEVE MOLD, closed, z = 0 on the stand, axis = Z, parting plane y = 0 -----
ZS_SEAT = SM_FLOOR                              # rod seat bottom
ZS_END = ZS_SEAT + ROD_SEAT                     # sleeve's molded (chamfered) end
ZS_TOP = ZS_END + L_SLEEVE                      # top face = pour surface = sleeve's other end
R_SLEEVE_CAV = (D_CORE + GROOVE_COMP) / 2.0
R_SEAT = (D_ROD + GROOVE_COMP + FIT_ROD_SEAT) / 2.0
ZS_FUNNEL = ZS_END + SLEEVE_TIP_CHAMFER - (R_SLEEVE_CAV - R_SEAT)   # the tip bevel's cone reaches R_SEAT
R_GUIDE = (D_ROD + HOLE_COMP + FIT_ROD_GUIDE) / 2.0
R_GUIDE_HUB = R_GUIDE + GUIDE_HUB_WALL
KEY_Z = (KEY_INSET, ZS_TOP - KEY_INSET - KEY_STAGGER)             # 12, 77
BOLT_Z = (20.0, 52.0, 84.0)     # a row just past each key, washers clear of the stand and skirt
R_KEY_SOCKET = (KEY_D0 + FIT_KEY) / 2.0 + 0.5 * (KEY_D0 - KEY_D1) / 2.0 / KEY_H   # at the face
BOX_X = SM_W + FIT_BOX                          # pocket / skirt inside, x
BOX_Y = 2 * SM_T + FIT_BOX                      # ... y
ZG_PLATE0 = ZS_TOP + GUIDE_GAP
ZG_PLATE1 = ZG_PLATE0 + GUIDE_PLATE
ZG_HUB0 = ZG_PLATE0 - GUIDE_HUB_DROP


def vent_thetas():
    return [VENT_THETA0 + i * 360.0 / N_VENT for i in range(N_VENT)]


def grain_mass_g(length=L_SEG, rho=1.74895):
    """One segment as cast, g (rho in g/cm3, memorial's ideal density)."""
    return math.pi / 4.0 * (D_GRAIN ** 2 - D_CORE ** 2) * length * rho / 1000.0


def sleeve_volume_ml():
    return math.pi / 4.0 * (D_CORE ** 2 - D_ROD ** 2) * L_SLEEVE / 1000.0


def self_check():
    msgs = []
    ok = True

    def need(cond, text):
        nonlocal ok
        ok &= bool(cond)
        msgs.append(("ok  " if cond else "FAIL") + "  " + text)

    def warn(cond, text):
        msgs.append(("ok  " if cond else "warn") + "  " + text)

    wall = (D_CORE - D_ROD) / 2
    need(wall >= 1.0, f"rod {D_ROD} leaves >= 1 mm of sleeve wall under the {D_CORE} port (wall {wall:.2f})")
    warn(wall >= 1.5, f"sleeve wall {wall:.2f} >= 1.5: thinner tears easily when you slide the rod")
    need(D_TUBE <= 34.9, f"tube OD {D_TUBE:.2f} slides into the 35.0 case bore")
    need(L_SLEEVE - BASE_FLOOR - L_SEG_MAX - CAP_TOP >= SLEEVE_TIP_CHAMFER + 2.0,
         f"sleeve {L_SLEEVE} clears the cap on a {L_SEG_MAX} tube with its bevel outside")
    need(R_VENT - R_VENT_PIN > D_CORE / 2 + 1.0 and R_VENT + R_VENT_PIN < D_GRAIN / 2 - 1.0,
         f"vents r {R_VENT - R_VENT_PIN:.1f}..{R_VENT + R_VENT_PIN:.1f} sit inside the web 7.0..17.2")
    web = 2 * R_VENT * math.sin(math.pi / N_VENT) - D_VENT
    need(web >= 3.0, f"{web:.1f} mm of cap between neighbouring vents")
    need(GRIP_INTERF >= 0.05, f"base/cap hole {D_GRIP:.2f} squeezes the {D_CORE} sleeve {GRIP_INTERF} radial")
    need(ZS_FUNNEL - ZS_SEAT >= 4.0, f"rod seat {ZS_FUNNEL - ZS_SEAT:.1f} deep below the funnel")
    need(KEY_X - R_KEY_SOCKET - R_SLEEVE_CAV >= 2.5 and SM_W / 2 - KEY_X - R_KEY_SOCKET >= 2.5,
         f"key sockets at x {KEY_X} leave {KEY_X - R_KEY_SOCKET - R_SLEEVE_CAV:.2f} to the cavity, "
         f"{SM_W / 2 - KEY_X - R_KEY_SOCKET:.2f} to the edge")
    need(SM_W / 2 - KEY_X - WASHER_OD / 2 >= 1.0, f"washers at x {KEY_X} stay on the back face")
    need(KEY_Z[1] - KEY_Z[0] > 0 and abs((ZS_TOP - KEY_Z[1]) - KEY_Z[0]) >= 2 * R_KEY_SOCKET,
         f"keys at z {KEY_Z[0]:.0f} / {KEY_Z[1]:.0f}: a half turned end-for-end can't close")
    gap = min(abs(zb - zk) for zb in BOLT_Z for zk in KEY_Z) - D_BOLT / 2 - R_KEY_SOCKET
    need(gap >= 1.5, f"bolt holes {gap:.2f} clear of the key sockets")
    need(min(BOLT_Z) - WASHER_OD / 2 >= BOX_SKIRT + 1.0 and max(BOLT_Z) + WASHER_OD / 2 <= ZS_TOP - BOX_SKIRT - 1.0,
         f"bolt rows z {BOLT_Z}: washers clear of the stand (z {BOX_SKIRT}) and the guide skirt "
         f"(z {ZS_TOP - BOX_SKIRT})")
    need(SM_T - R_SLEEVE_CAV >= 4.0, f"{SM_T - R_SLEEVE_CAV:.2f} mm of plastic behind the sleeve cavity")
    need(ZG_HUB0 - ZS_TOP >= 4.0, f"guide hub {ZG_HUB0 - ZS_TOP:.1f} mm clear of the pour surface")
    need(R_SLEEVE_CAV - R_GUIDE_HUB >= 0.5, f"a {R_SLEEVE_CAV - R_GUIDE_HUB:.2f} mm ring of the cavity mouth "
         f"shows past the guide hub (r {R_GUIDE_HUB:.2f})")
    need(ZS_SEAT + L_ROD_MIN >= ZG_PLATE1 + 5.0, f"a {L_ROD_MIN:.0f} mm rod stands >= 5 mm above the guide")
    for m in msgs:
        print(m)
    return ok


if __name__ == "__main__":
    print(f"tube OD {D_TUBE:.2f}, cup OD {D_CUP:.2f}, sleeve {L_SLEEVE:.1f} long")
    print(f"base mold {ZB_PIN_TOP:.1f} tall, cap mold {ZC_PIN_TOP:.1f} tall, "
          f"sleeve mold {SM_W:.0f} x {2 * SM_T:.0f} x {ZS_TOP:.1f} closed")
    print(f"segment {L_SEG} mm: {grain_mass_g():.1f} g, x3 = {3 * grain_mass_g():.1f} g; "
          f"sleeve {sleeve_volume_ml():.2f} ml")
    print("self_check:", self_check())
