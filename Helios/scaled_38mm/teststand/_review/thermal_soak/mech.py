"""ITEMS 3 & 4 - what the heat DOES mechanically: preload, creep, fits."""
import numpy as np
from soak import run, MAT

# ---- modulus / strength retention working curves (grounded research) -------
RT = np.array([23, 40, 60, 80, 100, 110, 130.0])
E_RET = np.array([1.00, 0.95, 0.90, 0.78, 0.35, 0.12, 0.005])
S_RET = np.array([1.00, 0.85, 0.68, 0.45, 0.12, 0.05, 0.015])


def ret(T, curve, Tg_ref=105.0, Tg=105.0):
    """shift the ABS curve by (Tg - 105) for other materials"""
    return float(np.interp(T - (Tg - Tg_ref), RT, curve))


E_ABS, SC_ABS = 2200.0, 88.3          # MPa, printed compressive yield
CTE = [(20, 50, 79.6e-6), (50, 70, 150e-6), (70, 90, 262.9e-6),
       (90, 105, 800e-6), (105, 130, 2350e-6)]


def free_strain(T0, T1):
    e = 0.0
    for a, b, c in CTE:
        lo, hi = max(a, T0), min(b, T1)
        if hi > lo:
            e += (hi - lo) * c
    return e


print("=" * 100)
print("ITEM 4a  TRAVEL COLLAR - the only part with a DESIGNED-IN residual preload")
print("=" * 100)
BORE, OD, W = 38.3, 52.0, 12.0
print(f" geometry: bore {BORE} pulled onto 38.0 casing, wall {(OD-BORE)/2:.2f} mm,"
      f" width {W} mm, 2x M4")
print(f" take-up: circumference to close 38.3->38.0 = pi*0.3 = {np.pi*0.3:.2f} mm"
      f" over 2 split planes = {np.pi*0.3/2:.2f} mm each")
print(f" split gap available 1.00 mm each -> residual gap"
      f" {1.0-np.pi*0.3/2:.2f} mm  (never closes: correct)")

# lug bearing under an M4 washer
A_LUG = np.pi / 4 * (9.0**2 - 4.3**2)
GRIP = 16.0                      # 8 mm of lug per half
A_BOLT = 8.78
k_b = 200e3 * A_BOLT / 20.0      # N/mm
print(f"\n lug bearing area under M4 washer = {A_LUG:.1f} mm2 ; "
      f"grip length {GRIP:.0f} mm ; k_bolt {k_b:.0f} N/mm")

print("\n clamp pressure on the casing, p = 2N/(D*W):")
for Fb in (250, 500, 1000, 1500):
    p = 2 * Fb / (38.0 * W)
    print(f"   preload {Fb:5.0f} N/bolt -> casing contact pressure {p:5.2f} MPa"
          f" ; lug stress {Fb/A_LUG:5.1f} MPa")

print("\n WHAT HEAT DOES TO THAT PRELOAD (F = d_total / (1/k_b + 1/k_p)):")
print(f" {'T':>5s} {'E_hot':>7s} {'k_plast':>8s} {'freeExp':>8s} {'F_hot':>7s}"
       f" {'lug sig':>8s} {'hot sig_c':>9s} {'sig/sig_y':>9s}")
for F0 in (500.0, 1250.0):
    print(f"\n  assembled cold at {F0:.0f} N/bolt:")
    k_p0 = E_ABS * A_LUG / GRIP
    d_tot0 = F0 / (1 / (1 / k_b + 1 / k_p0))
    for T in (23, 60, 80, 97, 105, 120, 159):
        Eh = E_ABS * ret(T, E_RET)
        k_p = Eh * A_LUG / GRIP
        dth = free_strain(23, T) * GRIP - 12e-6 * (T - 23) * GRIP
        F = max((d_tot0 + dth) / (1 / k_b + 1 / k_p), 0.0)
        sc = SC_ABS * ret(T, S_RET)
        print(f" {T:5.0f} {Eh:7.0f} {k_p:8.0f} {dth:8.3f} {F:7.0f}"
              f" {F/A_LUG:8.2f} {sc:9.1f} {F/A_LUG/sc:9.2f}")

print("""
 READ: the hot plastic is so much softer than the steel bolt that it swallows
 its own thermal expansion elastically -- the bolt does NOT get overloaded.
 The failure is the opposite one: k_plastic collapses, so the SAME geometric
 take-up now generates far less force. Grip is lost while hot, and whatever
 creep strain accumulates while hot is subtracted from the take-up forever.
""")

print("=" * 100)
print("ITEM 4b  CREEP SET -> PRELOAD LOST AFTER COOLDOWN")
print("=" * 100)
print(" creep strain needed to zero the preload = d_total0 / GRIP:")
for F0 in (500.0, 1250.0):
    k_p0 = E_ABS * A_LUG / GRIP
    d0 = F0 * (1 / k_b + 1 / k_p0)
    print(f"   assembled at {F0:5.0f} N -> take-up {d0:.4f} mm = "
          f"{d0/GRIP*100:.3f} % strain over the {GRIP:.0f} mm grip")
print("""   Grounded creep data: printed ABS at 30 C / 3 MPa adds +32 % over elastic
   strain in 1 h; at 60 C / 20 MPa it creep-RUPTURES in ~3 min. The soak holds
   the collar at 97-159 C (central..harsh) for 100-300 s. Elastic strain alone
   at the hot modulus is already 1-3 %, i.e. 10-30x the take-up above. So even
   a few percent of that recovered as permanent set zeroes the clamp.""")

print()
print("=" * 100)
print("ITEM 4c  MOTOR WEIGHT ON A HOT CRADLE_RING BORE - Hertz line contact")
print("=" * 100)
R1, R2 = 19.0, 19.4
R = R1 * R2 / (R2 - R1)
print(f" near-conforming internal contact: R_eff = {R:.0f} mm (very large)")
m_dry, m_wet = 0.285, 0.540
print(f" motor mass {m_wet*1e3:.0f} g loaded / {m_dry*1e3:.0f} g burnt out"
      f" -> {m_dry*9.81:.1f} N after burnout, 2 rings, 25 mm each")
Pp = m_dry * 9.81 / 2 / 25.0
print(f" load per unit length P' = {Pp:.4f} N/mm")
print(f"\n {'T':>5s} {'E_hot':>7s} {'E*':>8s} {'2b':>7s} {'p0':>7s} {'hot sig_c':>9s}"
      f" {'p0/sig_y':>9s} {'indent':>9s}")
for T in (23, 60, 80, 100, 130, 178):
    Eh = E_ABS * ret(T, E_RET)
    Es = 1 / ((1 - 0.33**2) / 69e3 + (1 - 0.41**2) / Eh)
    b = np.sqrt(2 * Pp * R / (np.pi * Es))
    p0 = 2 * Pp / (np.pi * b)
    sc = SC_ABS * ret(T, S_RET)
    print(f" {T:5.0f} {Eh:7.0f} {Es:8.0f} {2*b:7.3f} {p0:7.3f} {sc:9.2f}"
          f" {p0/sc:9.3f} {p0*b/Es*1e3:8.2f}um")
print("""
 READ: because the fit is near-conforming the effective radius is ~920 mm, so
 the contact simply WIDENS as the plastic softens and the peak pressure FALLS.
 p0 never approaches even the hot compressive yield, and the indentation stays
 sub-micron. The motor's own weight cannot emboss the trough at any temperature
 this soak reaches. Weight is a NON-issue; preload is the issue.""")

print()
print("=" * 100)
print("ITEM 3  THE (ii) MECHANISM: ANNEALING SHRINKAGE OF A BORE THAT MUST SLIDE")
print("=" * 100)
print(" A printed part taken above Tg with no load relaxes its frozen-in bead")
print(" orientation: it shrinks along the extrusion direction. Published anneal")
print(" shrinkage for printed ABS/PLA above Tg is ~0.3-2 % in X/Y.\n")
print(f" {'anneal':>8s} {'d_bore':>8s} {'clearance left':>15s} {'p_interf':>9s}"
      f" {'mu*p*A':>10s} {'verdict':>28s}")
E_int = 2200.0
D_o, d_i = 50.8, 38.8
Cg = (D_o**2 + d_i**2) / (D_o**2 - d_i**2) + 0.35
A_wrap = np.pi * (d_i / 2) * 25.0
for sh in (0.0, 0.003, 0.005, 0.01, 0.015, 0.0206, 0.03):
    dbore = d_i * sh
    clear = 0.8 - dbore
    if clear >= 0:
        p, fr, v = 0.0, 0.0, "slides; friction = mu*W only"
    else:
        p = (-clear / d_i) * E_int / Cg
        fr = 0.35 * p * A_wrap
        v = "GRIPS: parallel load path"
    print(f" {sh*100:7.2f}% {dbore:7.3f}mm {clear:14.3f}mm {p:8.2f}M"
          f" {fr:9.0f}N   {v:>28s}")
print(f"\n reference: friction budget in the README is mu*W = 0.8-3.5 N, and the")
print(f" acceptance test is 'fish scale pulls the motor through at <=3 N'.")
print(f" One ring gripping at only 0.1 mm interference already makes")
p01 = (0.1 / d_i) * E_int / Cg
print(f" mu*p*A = {0.35*p01*A_wrap:.0f} N -- i.e. {0.35*p01*A_wrap/500*100:.0f} % of a 500 N peak,")
print(f" swallowed silently and NOT bounded by mu*W any more.")

print()
print("=" * 100)
print("ITEM 3  where the thrust_cap actually is thermally (depth profile)")
print("=" * 100)
for lb, lbl in ((0.045, "central"), (0.090, "harsh")):
    h, p = run(t_burn=1.2 if lb < 0.07 else 1.5, h_aft=1250 if lb < 0.07 else 1460,
               l_bare=lb, mat="ABS", t_end=900.0)
    d = {q.name: q for q in p}
    q = d["thrust_cap annulus"]
    print(f"\n {lbl}: thrust_cap annulus, 16 mm of 100% infill between the hot")
    print(f"   casing rim and the Ø40 boss that bears on the steel cell face")
    for frac in (0.0, 0.125, 0.25, 0.5, 0.75, 1.0):
        j = int(np.argmin(np.abs(q.x - frac * q.wall)))
        print(f"     {frac*q.wall*1e3:5.1f} mm from the hot face: peak "
              f"{q.peak[j]:6.1f} C at t = {q.tpeak[j]:5.0f} s")
