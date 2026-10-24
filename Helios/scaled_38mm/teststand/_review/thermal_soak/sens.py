import numpy as np
import soak
from soak import run, MAT

print("=" * 100)
print("SENSITIVITY 1  interface conductance (my biggest modelling assumption)")
print("=" * 100)
print("  g_min = assumed minimum air gap at the tightest point (printed-bore roughness)")
print("  h_solid_collar = solid contact conductance of the CLAMPED collar\n")
print(f"{'g_min':>7s} {'h_sol':>7s} | {'ring h_int':>10s} {'collar h_int':>12s} |"
      f" {'ring Tpk':>9s} {'collar Tpk':>11s} {'cap Tpk':>8s}")
orig_gmin = 60e-6
for gmin in (40e-6, 60e-6, 120e-6, 250e-6):
    for hs in (300.0, 900.0, 2000.0):
        # monkey-patch the two knobs
        src_gap = soak.gap_conductance
        def patched(r_c, r_b, drop, t0, t1, T_m=90.0, g_min=gmin):
            return src_gap(r_c, r_b, drop, t0, t1, T_m, g_min)
        soak.gap_conductance = patched
        bp = soak.build_parts
        def bp2(mat, mo=None, _hs=hs):
            ps, bs = bp(mat, mo)
            for p in ps:
                if p.name == "travel_collar":
                    p.h_int = p.h_gap + _hs
            return ps, bs
        soak.build_parts = bp2
        h, p = run(t_burn=1.2, h_aft=1250, l_bare=0.045, mat="ABS", t_end=900.0)
        d = {q.name: q for q in p}
        print(f"{gmin*1e6:6.0f}u {hs:7.0f} | "
              f"{d['cradle_ring aft'].h_int:10.0f} {d['travel_collar'].h_int:12.0f} | "
              f"{d['cradle_ring aft'].peak[0]:8.1f}C {d['travel_collar'].peak[0]:10.1f}C "
              f"{d['thrust_cap annulus'].peak[0]:7.1f}C")
        soak.gap_conductance = src_gap
        soak.build_parts = bp

print("""
 READ: the parts' peak temperature is remarkably INSENSITIVE to the interface
 conductance. Reason: once h_int * sqrt(alpha*t)/k >> 1 the plastic surface is
 slaved to the casing temperature regardless. Characteristic time to slave the
 surface is (b/h_int)^2; with b ~ 540 and h_int ~ 300-1200 that is 0.2-3 s,
 negligible against the 20-40 s the casing takes to peak. The conclusion is
 therefore driven by the CASING temperature, not by the contact model.""")

print()
print("=" * 100)
print("SENSITIVITY 2  what actually drives it: the casing")
print("=" * 100)
b = 540.0
for hi in (70, 300, 364, 1203, 5000):
    print(f"  h_int {hi:5.0f} W/m2K -> surface slaved to the casing in "
          f"{(b/hi)**2:7.3f} s")

print()
print("=" * 100)
print("FITS: PRINT SHRINK (repo table) + ANNEAL SHRINK, cumulative over firings")
print("=" * 100)
E_int, D_o, d_i = 2200.0, 50.8, 38.8
Cg = (D_o**2 + d_i**2) / (D_o**2 - d_i**2) + 0.35
A_wrap = np.pi * (d_i / 2) * 25.0
print("  repo README:0.800 nominal -> 0.645 @0.4% print shrink -> 0.490 @0.8%")
print("  anneal shrink then eats into whatever is left.\n")
print(f"  {'start clear':>11s} | " + " | ".join(f"{a*100:.1f}% anneal" for a in
      (0.0, 0.005, 0.01, 0.015, 0.02)))
for start, lbl in ((0.800, "0.800 ideal"), (0.645, "0.645 @0.4%"), (0.490, "0.490 @0.8%")):
    cells = []
    for a in (0.0, 0.005, 0.01, 0.015, 0.02):
        c = start - d_i * a
        if c > 0.05:
            cells.append(f"{c:5.3f} ok  ")
        elif c > 0:
            cells.append(f"{c:5.3f} TIGHT")
        else:
            p = (-c / d_i) * E_int / Cg
            cells.append(f"{0.35*p*A_wrap:5.0f}N GRIP")
    print(f"  {lbl:>11s} | " + " | ".join(cells))
print("""
  And FDM anneal shrink is ANISOTROPIC (in-plane >> layer axis), so the bore
  does not just get smaller, it goes OVAL. An oval trough contacts the casing
  on two side flanks instead of one bottom line -- which is precisely the
  stick-slip the README's fish-scale acceptance test is written to detect.""")

print()
print("=" * 100)
print("HANDLING: when is the motor cool enough to touch / to pull?")
print("=" * 100)
for lb, lbl in ((0.045, "central"), (0.090, "harsh")):
    h, p = run(t_burn=1.2 if lb < 0.07 else 1.5, h_aft=1250 if lb < 0.07 else 1460,
               l_bare=lb, mat="ABS", t_end=1800.0)
    t, Tc = h["t"], h["Tc"]
    Tmax = Tc.max(axis=1)
    print(f"\n  {lbl}: hottest point anywhere on the casing")
    for lim in (200, 150, 100, 60, 45):
        m = Tmax < lim
        # first time after the burn that it drops below lim and stays below
        idx = None
        for i in range(len(t)):
            if t[i] > 2.0 and Tmax[i:].max() < lim:
                idx = i
                break
        print(f"    below {lim:3d} C from t = "
              + (f"{t[idx]:6.0f} s" if idx else " never within 1800 s"))
