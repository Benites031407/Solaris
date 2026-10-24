import numpy as np
from soak import run, MAT, T_AMB

PARTS_OF_INTEREST = ["cradle_ring aft", "cradle_ring fwd", "cradle_cap aft",
                     "travel_collar", "thrust_cap sleeve", "thrust_cap annulus"]


def cross_times(p, Tlim, frac=0.25):
    """(t_surface_crosses, t_25pct_depth_crosses, seconds_surface_above)."""
    T, tt = p.hist_T, p.hist_t
    j = int(np.argmin(np.abs(p.x - frac * p.wall)))
    def first(col):
        m = T[:, col] > Tlim
        return float(tt[m][0]) if m.any() else None
    above = 0.0
    m = T[:, 0] > Tlim
    if m.any():
        above = float(tt[m][-1] - tt[m][0])
    return first(0), first(j), above


def summarize(tag, hist, parts, mat_default):
    s, t, Tc = hist["s"], hist["t"], hist["Tc"]
    ic = int(np.argmin(np.abs(s * 1e3 - 113)))
    print(f"\n--- {tag}")
    print(f"    casing @aft-ring peak {Tc[:,ic].max():6.1f} C at "
          f"{t[np.argmax(Tc[:,ic])]:5.1f}s ; rim peak {Tc[:,-1].max():6.1f} C at "
          f"{t[np.argmax(Tc[:,-1])]:5.1f}s")
    print(f"    {'part':20s} {'mat':5s} {'Tsurf_pk':>9s} {'t_pk':>6s} "
          f"{'t>Tg':>7s} {'t>Tg@25%':>9s} {'s_above':>8s} {'d>Tg':>7s} {'d>HDT':>7s} {'d>svc':>7s}")
    for p in parts:
        if p.name not in PARTS_OF_INTEREST:
            continue
        m = p.m
        tsg, t25, ab = cross_times(p, m["Tg"])
        print(f"    {p.name:20s} {p.mat:5s} {p.peak[0]:9.1f} {p.tpeak[0]:6.0f} "
              f"{('%.0f'%tsg) if tsg else '  -':>7s} "
              f"{('%.0f'%t25) if t25 else '  -':>9s} "
              f"{ab:8.0f} {p.depth_above(m['Tg']):6.2f}mm "
              f"{p.depth_above(m['hdt']):6.2f}mm {p.depth_above(m['svc']):6.2f}mm")


print("=" * 100)
print("A. UNCERTAINTY BRACKET on the casing (ABS parts fitted, motor left in)")
print("=" * 100)
for tb, ha, lb, lbl in [
    (1.0, 1050, 0.020, "mild    : 1.0 s, h 1050, liner intact but for 20 mm"),
    (1.2, 1250, 0.045, "central : 1.2 s, h 1250, liner bare aft 45 mm"),
    (1.5, 1460, 0.090, "harsh   : 1.5 s, h 1460, liner bare aft 90 mm"),
    (2.0, 1460, 0.140, "worst   : 2.0 s, h 1460, liner bare aft 140 mm"),
]:
    h, p = run(t_burn=tb, h_aft=ha, l_bare=lb, mat="ABS", t_end=900.0)
    summarize(lbl, h, p, "ABS")

print()
print("=" * 100)
print("B. MATERIAL COMPARISON at the CENTRAL case (1.2 s, h 1250, bare 45 mm)")
print("=" * 100)
for mat in ("PLA", "PETG", "ASA", "ABS"):
    h, p = run(t_burn=1.2, h_aft=1250, l_bare=0.045, mat=mat, t_end=900.0)
    summarize(f"all parts in {mat}", h, p, mat)

print()
print("=" * 100)
print("C. MATERIAL COMPARISON at the HARSH case (1.5 s, h 1460, bare 90 mm)")
print("=" * 100)
for mat in ("PLA", "PETG", "ASA", "ABS"):
    h, p = run(t_burn=1.5, h_aft=1460, l_bare=0.090, mat=mat, t_end=900.0)
    summarize(f"all parts in {mat}", h, p, mat)

print()
print("=" * 100)
print("D. AS-SPECIFIED MIX (repo table) vs ABS EVERYWHERE, harsh case")
print("=" * 100)
asspec = {"cradle_ring aft": "PETG", "cradle_ring fwd": "PETG",
          "cradle_cap aft": "PETG", "cradle_cap fwd": "PETG",
          "travel_collar": "PLA",            # <-- repo says PLA 4/40%
          "thrust_cap sleeve": "PETG", "thrust_cap annulus": "PETG"}
h, p = run(t_burn=1.5, h_aft=1460, l_bare=0.090, mat="PLA", mat_over=asspec, t_end=900.0)
summarize("as specified (rings PETG, COLLAR PLA, cap PETG)", h, p, "mix")
h, p = run(t_burn=1.5, h_aft=1460, l_bare=0.090, mat="ABS", t_end=900.0)
summarize("ABS everywhere", h, p, "ABS")
