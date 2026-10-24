import numpy as np
import soak
from soak import run, MAT, gap_conductance, CAS_OD, T_AMB

np.set_printoptions(linewidth=200)

print("=== INTERFACE CONDUCTANCES (computed, referred to wrapped bore area) ===")
r = CAS_OD / 2
for nm, bore, th0, th1, drop, extra in [
    ("cradle_ring  38.8 lower half", 38.8, 0.0, np.pi / 2, 0.4, 2000 * 0.30 / (np.pi * 19.4 / 2)),
    ("cradle_cap   39.4 upper half", 39.4, np.pi / 2, np.pi, -0.4, 0.0),
    ("travel_collar 38.3 CLAMPED  ", 38.3, 0.0, 2 * np.pi, 0.0, 900.0),
    ("thrust_cap sleeve 39.0 slip ", 39.0, 0.0, 2 * np.pi, 0.0, 0.0),
]:
    h, g = gap_conductance(r, bore / 2e3, drop * 1e-3, th0, th1)
    print(f" {nm}  mean gap {g*1e3:5.3f} mm   h_gap {h:7.1f}"
          f"   + solid {extra:6.1f}  = {h+extra:7.1f} W/m2K")

print("\n=== BASELINE RUN: t_burn 1.2 s, h_aft 1250, liner bare over aft 45 mm, ABS ===")
hist, parts = run(t_burn=1.2, h_aft=1250.0, l_bare=45e-3, mat="ABS", t_end=1800.0)
s, t, Tc = hist["s"], hist["t"], hist["Tc"]


def at(tt):
    return int(np.argmin(np.abs(t - tt)))


ib = at(1.2)
print("\n CASING AXIAL TEMPERATURE (C), s = mm forward of the aft rim")
hdr = " t(s)  " + "".join(f"{v:>7.0f}" for v in [0, 25, 50, 75, 100, 113, 142, 171, 200, 240])
print(hdr + "   nozzle  closure")
idx = [int(np.argmin(np.abs(s * 1e3 - v))) for v in
       [0, 25, 50, 75, 100, 113, 142, 171, 200, 240]]
for tt in (1.2, 5, 10, 20, 30, 60, 120, 300, 600, 1200, 1800):
    i = at(tt)
    row = "".join(f"{Tc[i, j]:7.1f}" for j in idx)
    print(f"{t[i]:6.1f}" + row + f"  {hist['Tn'][i]:7.0f}  {hist['Tk'][i]:7.1f}")

print("\n CASING PEAK per station and when it arrives")
print("   s(mm)   T_peak(C)   t_peak(s)    what is there")
what = {0: "nozzle joint", 25: "", 50: "", 75: "", 100: "aft ring trough starts",
        113: "AFT RING trough centre", 125: "aft ring trough ends",
        142: "TRAVEL COLLAR centre", 171: "FWD RING trough centre",
        200: "", 229: "thrust_cap sleeve mid", 240: "casing rim / closure plane"}
for v, lbl in what.items():
    j = int(np.argmin(np.abs(s * 1e3 - v)))
    k = int(np.argmax(Tc[:, j]))
    print(f"  {v:6.0f}  {Tc[k,j]:9.1f}  {t[k]:10.1f}    {lbl}")

# energy retained
AL_RHO, AL_CP = 2700.0, 896.0
A_CS = np.pi / 4 * ((38.1e-3) ** 2 - (34.8e-3) ** 2)
ds = s[1] - s[0]
E = []
for i in range(len(t)):
    e_cas = ((Tc[i] - T_AMB) * AL_RHO * AL_CP * A_CS * ds).sum()
    e_noz = (hist["Tn"][i] - T_AMB) * 0.130 * 490
    e_clo = (hist["Tk"][i] - T_AMB) * 0.031 * 896
    E.append(e_cas + e_noz + e_clo)
E = np.array(E)
Qp = 255e-3 * 2.265e6
print(f"\n ENERGY: propellant total {Qp/1e3:.0f} kJ")
print(f"  in hardware at burnout   {E[ib]/1e3:7.2f} kJ  = {E[ib]/Qp*100:5.2f} %")
k = int(np.argmax(E))
print(f"  hardware maximum         {E[k]/1e3:7.2f} kJ  = {E[k]/Qp*100:5.2f} %  at t={t[k]:.1f}s")
print(f"  (liner still holds the rest of what crossed the wall at burnout)")

print("\n=== PRINTED PARTS: baseline, motor LEFT IN ===")
print(f"{'part':22s} {'mat':5s} {'h_int':>7s} {'Tsurf':>7s} {'t@pk':>6s}"
      f" {'Tmid':>6s} {'Tout':>6s} {'>Tg?':>5s} {'depth>Tg':>9s} {'depth>HDT':>10s}")
for p in parts:
    m = p.m
    k = int(np.argmax(p.peak))
    print(f"{p.name:22s} {p.mat:5s} {p.h_int:7.0f} {p.peak[0]:7.1f} "
          f"{'':6s} {p.peak[len(p.peak)//2]:6.1f} {p.peak[-1]:6.1f} "
          f"{'YES' if p.peak[0]>m['Tg'] else 'no':>5s} "
          f"{p.depth_above(m['Tg']):8.2f}mm {p.depth_above(m['hdt']):9.2f}mm")
