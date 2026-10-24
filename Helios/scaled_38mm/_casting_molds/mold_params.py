"""Every number for the Helios 38 mm casting tooling: three printed molds for the three
silicone pieces that cast one BATES segment.

What one segment is cast in (as used, z = 0 on the table):
  silicone BASE    a short cylinder.  On top, a socket the casting tube's bottom end sits
                   in, down on its shoulder; in the middle of the shoulder, a blind pocket
                   the core's end plugs into.
  core             the silicone SLEEVE, a plain Ø14 tube, on the aluminium rod.  Its end
                   sits in the base pocket; it runs up the tube and out through the cap.
  casting tube     the 0.2 mm liner itself, cut to the segment length.  The grain is cast
                   in it, so its OD comes out inhibited and bonded (memorial 16.2, item 1).
  silicone CAP     a plain disc with a hole the core slides through.  It sits on the tube's
                   rim, edge flush with the tube, and holds the top of the core in the middle.
Both grain faces form on silicone, flush with the tube ends: segment length = tube length.

The molds:
  base mold    a cup holding the base upside down: a boss (the tube socket) with a pin on
               it (the core pocket).  Pour to the rim = the base's underside.
  cap mold     a cup with a pin in the middle.  Pour to the rim = the cap's top.
  sleeve mold  an inner cylinder inside a bigger cylinder.  The outer cylinder's Ø14 bore
               forms the sleeve's OD, the inner cylinder its bore.  A foot holds the outer
               cylinder's bottom end and seats the inner one; a guide on top holds the
               inner one on the axis.  The inner cylinder is the aluminium rod itself (the
               sleeve cures straight onto it), or the printed pin in its place.

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
D_ROD = 10.0             # [A] aluminium core rod = the sleeve's bore.  Measure yours, regenerate.
L_ROD_MIN = 110.0        # shortest rod (and the printed pin's length): it seats in the sleeve
                         # mold's foot and stands clear above the guide

# ---- silicone base, as used -------------------------------------------------------------
BASE_FLOOR = 3.0         # silicone under the core pocket
POCKET_DEPTH = 6.0       # the core's end goes this far in, below the grain's bottom face
SOCKET_DEPTH = 6.0       # the tube's bottom end goes this far in, down to the shoulder
SOCKET_INTERF = 0.05     # the socket squeezes the tube this much, radial: it holds it, not just
                         # locates it.  Squeezing the tube's end in only adds room in the case
CUP_WALL = 3.5           # silicone around the tube
D_BASE = D_TUBE + 2 * CUP_WALL                    # 41.8
H_BASE = BASE_FLOOR + POCKET_DEPTH + SOCKET_DEPTH  # 15
MOUTH_CHAMFER = 1.0      # 45 deg lead-in on the socket mouth, inner edge

# ---- silicone cap, as used --------------------------------------------------------------
D_CAP = D_TUBE           # flush with the tube: line the edges up and the core's top is centred
CAP_T = 6.0

# ---- both holes that hold the core ------------------------------------------------------
GRIP_INTERF = 0.10       # the base pocket and the cap hole squeeze the sleeve this much, radial
D_GRIP = D_CORE - 2 * GRIP_INTERF    # 13.8

# ---- silicone sleeve, as used -----------------------------------------------------------
SLEEVE_STICKOUT = 5.0    # sleeve left above the cap with the longest (70) tube
L_SLEEVE = POCKET_DEPTH + L_SEG_MAX + CAP_T + SLEEVE_STICKOUT      # 87

# ---- printing allowances (FDM) ----------------------------------------------------------
HOLE_COMP = 0.15         # [A] printed vertical holes come out this much small on the diameter;
                         # printed OUTER surfaces are taken as nominal
FIT_ROD_SEAT = 0.30      # diametral clearance on the inner cylinder in the foot's seat (net)
FIT_ROD_GUIDE = 0.30     # ... in the top guide's bore (net)
FIT_SOCKET = 0.30        # the outer cylinder's ends in the foot and the guide skirt (net)

# ---- printed cup molds (base, cap) ------------------------------------------------------
WALL = 3.0               # plastic around the silicone
FLOOR = 3.0              # plastic under the silicone
PIN_PROUD = 1.0          # the cap mold's pin stands this far above the rim: the hole comes out open

# ---- sleeve mold ------------------------------------------------------------------------
SM_OD = 22.0             # outer cylinder
SM_END_CH = 0.6          # 45 deg on the outer cylinder's outside edges, both ends: room for
                         # elephant foot, and a lead-in into the foot and the guide skirt
FOOT_D = 45.0            # foot flange: keeps the tall mold from tipping
FOOT_FLOOR = 5.0         # foot floor top = the sleeve's bottom end
SEAT_DEPTH = 3.0         # the inner cylinder's seat, in the foot floor
SEAT_LEADIN = 0.6        # 45 deg on the seat mouth: the rod's tip finds it blind
SKIRT = 6.0              # foot collar / guide skirt over the outer cylinder's ends
SKIRT_WALL = 2.5
MOUTH_LEADIN = 0.8       # 45 deg on the collar and skirt mouths
GUIDE_GAP = 5.0          # guide plate stands this far above the pour surface
GUIDE_PLATE = 4.0
R_CHAMBER = 8.5          # the space between the pour surface and the plate, seen from above
GUIDE_HUB_WALL = 0.8     # thin, so a ring of the bore's mouth shows past it through the windows:
                         # watch the level there, top up with a syringe.  Not the way to fill it --
                         # the silicone goes in before the rod (see sleeve_mold.py)
GUIDE_BAR_W = 6.0        # the two bars that hold the hub
BORE_CHAMFER = 0.5       # 45 deg on both ends of the guide bore
PIN_TIP_CH = 0.8         # printed pin: chamfer on the end that goes down into the seat
PIN_TOP_CH = 0.5         # ... and on the bed end (elephant foot)

# ---- derived: BASE MOLD, z = 0 on the print bed (the base upside down) ------------------
ZB_MOUTH = FLOOR                                # socket mouth (the base's top, as used)
ZB_SHOULDER = ZB_MOUTH + SOCKET_DEPTH           # boss top = shoulder = grain bottom face
ZB_POCKET = ZB_SHOULDER + POCKET_DEPTH          # pin top = pocket floor
ZB_RIM = ZB_POCKET + BASE_FLOOR                 # pour surface = the base's underside

# ---- derived: CAP MOLD, z = 0 on the print bed (the cap as used) ------------------------
ZC_FACE = FLOOR                                 # mold floor = cap underside = grain top face
ZC_RIM = ZC_FACE + CAP_T                        # pour surface = cap top
ZC_PIN_TOP = ZC_RIM + PIN_PROUD

R_BOSS = D_TUBE / 2.0 - SOCKET_INTERF           # printed outer surfaces: nominal
R_GRIP_PIN = D_GRIP / 2.0
R_BASE_CAV = (D_BASE + HOLE_COMP) / 2.0         # printed holes: + HOLE_COMP
R_CAP_CAV = (D_CAP + HOLE_COMP) / 2.0
R_BASE_HEAD = R_BASE_CAV + WALL
R_CAP_HEAD = R_CAP_CAV + WALL

# ---- derived: SLEEVE MOLD, assembled, z = 0 on the table, axis = Z -----------------------
ZS_SEAT = FOOT_FLOOR - SEAT_DEPTH               # seat bottom: the inner cylinder's foot
ZS_END = FOOT_FLOOR                             # the sleeve's bottom end, on the foot floor
ZS_TOP = ZS_END + L_SLEEVE                      # top face = pour surface = the sleeve's other end
ZF_COLLAR = ZS_END + SKIRT                      # foot collar top
ZG_SKIRT = ZS_TOP - SKIRT                       # guide skirt mouth
ZG_PLATE0 = ZS_TOP + GUIDE_GAP
ZG_PLATE1 = ZG_PLATE0 + GUIDE_PLATE
R_BORE = (D_CORE + HOLE_COMP) / 2.0             # outer cylinder bore
R_SM = SM_OD / 2.0
R_SEAT = (D_ROD + FIT_ROD_SEAT + HOLE_COMP) / 2.0
R_GUIDE = (D_ROD + FIT_ROD_GUIDE + HOLE_COMP) / 2.0
R_GUIDE_HUB = R_GUIDE + GUIDE_HUB_WALL
R_SKIRT_IN = (SM_OD + FIT_SOCKET + HOLE_COMP) / 2.0
R_SKIRT_OUT = R_SKIRT_IN + SKIRT_WALL
ROD_SLIDE = ZS_END - ZS_SEAT                    # rod past the sleeve's bottom end as molded


def grain_mass_g(length=L_SEG, rho=1.74895):
    """One segment as cast, g (rho in g/cm3, memorial's ideal density)."""
    return math.pi / 4.0 * (D_GRAIN ** 2 - D_CORE ** 2) * length * rho / 1000.0


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
    warn(wall >= 1.5, f"sleeve wall {wall:.2f} >= 1.5: thinner tears easily")
    ecc = (FIT_SOCKET + FIT_ROD_SEAT) / 2
    need(wall - ecc >= 1.0, f"sleeve wall >= {wall - ecc:.2f} with every fit's play stacked to one side")
    need(D_TUBE <= 34.9, f"tube OD {D_TUBE:.2f} slides into the 35.0 case bore")
    stick = L_SLEEVE - POCKET_DEPTH - L_SEG_MAX - CAP_T
    need(stick >= 3.0, f"sleeve stands {stick:.1f} mm above the cap on a {L_SEG_MAX} tube")
    need(GRIP_INTERF >= 0.05, f"pocket / cap hole {D_GRIP:.2f} squeezes the {D_CORE} sleeve {GRIP_INTERF} radial")
    need(0.0 < SOCKET_INTERF <= 0.10, f"base socket {2 * R_BOSS:.2f} squeezes the {D_TUBE:.1f} tube {SOCKET_INTERF} radial")
    need(BASE_FLOOR >= 2.0, f"{BASE_FLOOR} mm of silicone under the core pocket")
    need(CUP_WALL >= 3.0, f"{CUP_WALL} mm of silicone around the tube socket")
    need(D_GRAIN / 2 - D_CORE / 2 >= 5.0, f"cap ring {D_GRAIN / 2 - D_CORE / 2:.1f} wide over the grain web")
    need(R_SM - R_BORE >= 3.0, f"outer cylinder wall {R_SM - R_BORE:.2f}")
    need(FOOT_FLOOR - SEAT_DEPTH >= 1.5, f"{FOOT_FLOOR - SEAT_DEPTH:.1f} mm of foot under the seat")
    need(R_CHAMBER - R_BORE >= 1.0, f"the chamber shows the whole pour surface ({R_CHAMBER - R_BORE:.2f} past the bore)")
    ledge = (R_SM - SM_END_CH) - R_CHAMBER
    need(ledge >= 1.5, f"the guide sits on a {ledge:.2f} mm band of the top face")
    need(R_BORE - R_GUIDE_HUB >= 0.5, f"a {R_BORE - R_GUIDE_HUB:.2f} mm ring of the bore's mouth shows past the "
         f"guide hub (r {R_GUIDE_HUB:.3f})")
    need(GUIDE_GAP >= 4.0, f"guide plate {GUIDE_GAP} mm clear of the pour surface")
    need(ZS_SEAT + L_ROD_MIN >= ZG_PLATE1 + 5.0,
         f"a {L_ROD_MIN:.0f} mm rod stands {ZS_SEAT + L_ROD_MIN - ZG_PLATE1:.0f} mm above the guide")
    need(L_ROD_MIN >= L_SLEEVE + 10.0, f"in use the rod stands {L_ROD_MIN - L_SLEEVE:.0f} mm out of the sleeve's top")
    for m in msgs:
        print(m)
    return ok


if __name__ == "__main__":
    print(f"tube OD {D_TUBE:.2f}; base {D_BASE:.1f} x {H_BASE:.0f}; cap {D_CAP:.1f} x {CAP_T:.0f}; "
          f"sleeve {D_CORE:.0f}/{D_ROD:.0f} x {L_SLEEVE:.0f}")
    print(f"base mold {2 * R_BASE_HEAD:.1f} x {ZB_RIM:.0f}; cap mold {2 * R_CAP_HEAD:.1f} x {ZC_PIN_TOP:.0f}; "
          f"sleeve mold {ZG_PLATE1:.0f} tall assembled, {ZS_SEAT + L_ROD_MIN:.0f} to the rod's top")
    print(f"segment {L_SEG} mm: {grain_mass_g():.1f} g, x3 = {3 * grain_mass_g():.1f} g")
    print("self_check:", self_check())
