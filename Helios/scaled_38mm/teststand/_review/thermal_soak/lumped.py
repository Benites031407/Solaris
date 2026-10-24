"""ITEM 1 - lumped-capacitance soak of casing + closures + nozzle.

Independent of the FD model: pure energy bookkeeping + a single-node cooldown,
so the FD result can be checked against it.
"""
import numpy as np

SIG = 5.670374419e-8
T_AMB = 20.0
AL_RHO, AL_CP = 2700.0, 896.0
ST_CP = 490.0

# ---- hardware inventory (Nakka Impulser 38.1 x 1.65 6061, 240 mm) ----------
OD, WALL = 38.1, 1.65
ID = OD - 2 * WALL
L = 240.0
V_cas = np.pi / 4 * (OD**2 - ID**2) * L * 1e-9        # m3
m_cas = V_cas * AL_RHO
m_clo = np.pi / 4 * (ID * 1e-3) ** 2 * 12e-3 * AL_RHO   # 34.8 x 12 mm plug
m_noz = 0.130                                          # low-carbon steel

C_cas, C_clo, C_noz = m_cas * AL_CP, m_clo * AL_CP, m_noz * ST_CP
C_hw = C_cas + C_clo + C_noz

print("=== HARDWARE THERMAL MASS ===")
print(f" casing  {m_cas*1e3:6.1f} g  {C_cas:6.1f} J/K")
print(f" closure {m_clo*1e3:6.1f} g  {C_clo:6.1f} J/K")
print(f" nozzle  {m_noz*1e3:6.1f} g  {C_noz:6.1f} J/K")
print(f" TOTAL   {(m_cas+m_clo+m_noz)*1e3:6.1f} g  {C_hw:6.1f} J/K")

# ---- printed parts that are thermally attached -----------------------------
# STEP volumes measured from the repo; x solid fraction for walls/infill
PARTS = [                     # name, cm3, solid frac, material
    ("cradle_ring x2 (bore region only)", 2 * 79.80 * 0.22, 0.45),
    ("cradle_cap x2",                     2 * 13.14, 0.45),
    ("travel_collar (2 halves)",          2 * 6.74, 0.55),
    ("thrust_cap",                        43.68, 1.00),
]
C_pl = 0.0
print("\n=== PRINTED PARTS (ABS 1.05 g/cm3, cp 1400) ===")
for n, v, f in PARTS:
    m = v * f * 1.05e-3
    C = m * 1400
    C_pl += C
    print(f" {n:36s} {v*f:6.1f} cm3  {m*1e3:6.1f} g  {C:6.1f} J/K")
print(f" {'TOTAL printed':36s} {'':6s}      {'':6s}      {C_pl:6.1f} J/K")
print(f"\n printed / metal heat-capacity ratio = {C_pl/C_hw:.2f}")

# ---- propellant energy -----------------------------------------------------
BORE = ID - 2 * 0.84            # inside the 2-ply liner = 33.1 mm
print("\n=== PROPELLANT ENERGY ===")
for core in (11.0, 13.0, 15.0):
    for Lg in (180.0, 200.0):
        V = np.pi / 4 * (BORE**2 - core**2) * Lg * 1e-3   # cm3
        m = V * 1.75                                       # g, ~95% TMD KNSB
        print(f" core {core:4.1f} grain {Lg:5.1f}  {V:6.1f} cm3  {m:6.1f} g"
              f"  Q = {m*2.265:7.0f} J")
m_prop = 255.0
Q_tot = m_prop * 2265.0
print(f"\n design point: {m_prop:.0f} g -> Q_total = {Q_tot/1e3:.0f} kJ")

# ---- equilibrium soak temperature vs retained fraction ---------------------
print("\n=== ADIABATIC EQUILIBRIUM SOAK (no ambient loss, motor still in stand) ===")
print(" f_ret   dT metal-only   T_eq metal-only   dT +printed   T_eq +printed")
for f in (0.01, 0.02, 0.03, 0.05, 0.08):
    d1 = f * Q_tot / C_hw
    d2 = f * Q_tot / (C_hw + C_pl)
    print(f" {f*100:4.1f}%   {d1:9.1f} K      {T_AMB+d1:9.1f} C     "
          f"{d2:9.1f} K   {T_AMB+d2:9.1f} C")

# ---- with ambient loss: the peak is NOT the adiabatic equilibrium ----------
# Single node at C_hw, area = casing OD + nozzle, heat released into it over
# the equilibration time tau_eq (axial+radial conduction), lost at h_amb.
A_out = np.pi * OD * 1e-3 * L * 1e-3 + 4e-3          # m2
print(f"\n motor external area = {A_out*1e4:.0f} cm2")


def h_amb(T):
    dT = max(T - T_AMB, 1e-3)
    Tf = T_AMB + dT / 2 + 273.15
    nu = 1.6e-5 * (Tf / 300) ** 1.75
    k = 0.0263 * (Tf / 300) ** 0.85
    Ra = 9.81 * (1 / Tf) * dT * (OD * 1e-3) ** 3 / (nu * nu / 0.7)
    Nu = (0.60 + 0.387 * Ra ** (1 / 6) / (1 + (0.559 / 0.7) ** (9 / 16)) ** (8 / 27)) ** 2
    hc = Nu * k / (OD * 1e-3)
    Tk, Tik = T + 273.15, T_AMB + 273.15
    hr = 0.25 * SIG * (Tk**4 - Tik**4) / max(Tk - Tik, 1e-6)
    return hc + hr


print("\n=== LUMPED SOAK WITH AMBIENT LOSS ===")
print(" heat is deposited at burnout then released to the outer surface over")
print(" tau_eq (internal equilibration); ambient loss runs the whole time.\n")
print(" f_ret  tau_eq   T_peak    t_peak    T@60s   T@300s   tau_cool")
for f in (0.02, 0.03, 0.05):
    for tau_eq in (15.0, 30.0, 60.0):
        C = C_hw + C_pl
        T, t, dt = T_AMB, 0.0, 0.01
        Tpk, tpk = T, 0.0
        T60 = T300 = None
        while t < 1200:
            q_in = f * Q_tot / tau_eq if t < tau_eq else 0.0
            h = h_amb(T)
            T += (q_in - h * A_out * (T - T_AMB)) * dt / C
            t += dt
            if T > Tpk:
                Tpk, tpk = T, t
            if T60 is None and t >= 60:
                T60 = T
            if T300 is None and t >= 300:
                T300 = T
        tau_c = C / (h_amb(Tpk) * A_out)
        print(f" {f*100:4.1f}%  {tau_eq:5.1f}s  {Tpk:6.1f}C  {tpk:6.1f}s  "
              f"{T60:6.1f}C  {T300:6.1f}C  {tau_c:6.0f}s")
