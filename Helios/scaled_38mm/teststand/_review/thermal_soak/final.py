import numpy as np
from soak import run, MAT, T_AMB

POI = ["cradle_ring aft", "cradle_cap aft", "travel_collar",
       "thrust_cap sleeve", "thrust_cap annulus"]
Qp = 255e-3 * 2.265e6


def cross(p, Tlim, frac=0.25):
    T, tt = p.hist_T, p.hist_t
    j = int(np.argmin(np.abs(p.x - frac * p.wall)))

    def first(c):
        m = T[:, c] > Tlim
        return float(tt[m][0]) if m.any() else None
    m = T[:, 0] > Tlim
    ab = float(tt[m][-1] - tt[m][0]) if m.any() else 0.0
    return first(0), first(j), ab


print("=" * 104)
print("ITEM 2  LINER-FAILURE SWEEP  (t_burn 1.2 s, h_aft 1250, ABS parts, motor left in)")
print("        the aft cradle_ring trough spans s = 100.5 .. 125.5 mm")
print("=" * 104)
print(f"{'bare aft':>9s} {'ring over':>10s} {'Ecas/Qp':>8s} {'casing pk':>10s}"
      f" {'@ring pk':>9s} | {'ring Tsurf':>11s} {'collar Ts':>10s} {'cap sleeve':>11s} {'annulus':>8s}")
res = {}
for lb in (0.0, 0.020, 0.045, 0.070, 0.090, 0.110, 0.140):
    h, p = run(t_burn=1.2, h_aft=1250, l_bare=lb, mat="ABS", t_end=900.0)
    d = {q.name: q for q in p}
    s = h["s"]
    ic = int(np.argmin(np.abs(s * 1e3 - 113)))
    res[lb] = (h, p)
    over = "YES" if lb * 1e3 > 100.5 else "no"
    print(f"{lb*1e3:8.0f}mm {over:>10s} {h['E'].max()/Qp*100:7.2f}% "
          f"{h['Tc'].max():9.0f}C {h['Tc'][:,ic].max():8.0f}C | "
          f"{d['cradle_ring aft'].peak[0]:10.1f}C {d['travel_collar'].peak[0]:9.1f}C "
          f"{d['thrust_cap sleeve'].peak[0]:10.1f}C {d['thrust_cap annulus'].peak[0]:7.1f}C")

print()
print("=" * 104)
print("ITEM 2  PER-MATERIAL Tg CROSSING, central (bare 45 mm) and harsh (bare 90 mm)")
print("=" * 104)
for lb, lbl in ((0.045, "CENTRAL bare 45 mm"), (0.090, "HARSH bare 90 mm")):
    print(f"\n  {lbl}")
    print(f"  {'part':20s} {'wall':>5s} | " + " | ".join(
        f"{m:>4s} Tpk  t>Tg  t>25%  s>Tg" for m in ("PLA", "PETG", "ASA", "ABS")))
    rows = {}
    for mat in ("PLA", "PETG", "ASA", "ABS"):
        h, p = run(t_burn=1.2 if lb < 0.07 else 1.5,
                   h_aft=1250 if lb < 0.07 else 1460,
                   l_bare=lb, mat=mat, t_end=900.0)
        for q in p:
            rows.setdefault(q.name, {})[mat] = q
    for nm in POI:
        line = f"  {nm:20s} {rows[nm]['ABS'].wall*1e3:4.1f}m | "
        cells = []
        for mat in ("PLA", "PETG", "ASA", "ABS"):
            q = rows[nm][mat]
            a, b, ab = cross(q, MAT[mat]["Tg"])
            cells.append(f"{q.peak[0]:5.0f} {('%.0f'%a) if a else '  -':>5s} "
                         f"{('%.0f'%b) if b else '  -':>6s} {ab:5.0f}")
        print(line + " | ".join(cells))

print()
print("=" * 104)
print("ITEM 5  DOES PULLING THE MOTOR HELP?  harsh case (1.5 s, h 1460, bare 90 mm), ABS")
print("=" * 104)
print(f"{'scenario':>16s} | " + " | ".join(f"{n[:14]:>14s}" for n in POI))
base = {}
for pull, lbl in ((None, "leave it in"), (300.0, "pull at 300 s"),
                  (120.0, "pull at 120 s"), (60.0, "pull at 60 s"),
                  (30.0, "pull at 30 s"), (15.0, "pull at 15 s")):
    h, p = run(t_burn=1.5, h_aft=1460, l_bare=0.090, mat="ABS",
               pull_at=pull, t_end=900.0)
    d = {q.name: q for q in p}
    if pull is None:
        base = {n: d[n].peak[0] for n in POI}
    cells = []
    for n in POI:
        q = d[n]
        a, b, ab = cross(q, MAT["ABS"]["Tg"])
        cells.append(f"{q.peak[0]:5.0f}C {ab:4.0f}s {q.depth_above(105.0):4.2f}mm")
    print(f"{lbl:>16s} | " + " | ".join(f"{c:>14s}" for c in cells))
print("  (cells: peak surface T / seconds surface above ABS Tg / depth above Tg)")

print()
print("      same, CENTRAL case (1.2 s, h 1250, bare 45 mm), parts as REPO SPECIFIES")
asspec = {"cradle_ring aft": "PETG", "cradle_ring fwd": "PETG",
          "cradle_cap aft": "PETG", "cradle_cap fwd": "PETG",
          "travel_collar": "PLA", "thrust_cap sleeve": "PETG",
          "thrust_cap annulus": "PETG"}
print(f"{'scenario':>16s} | " + " | ".join(f"{n[:14]:>14s}" for n in POI))
for pull, lbl in ((None, "leave it in"), (120.0, "pull at 120 s"),
                  (60.0, "pull at 60 s"), (30.0, "pull at 30 s")):
    h, p = run(t_burn=1.2, h_aft=1250, l_bare=0.045, mat="PLA",
               mat_over=asspec, pull_at=pull, t_end=900.0)
    d = {q.name: q for q in p}
    cells = []
    for n in POI:
        q = d[n]
        tg = MAT[q.mat]["Tg"]
        a, b, ab = cross(q, tg)
        cells.append(f"{q.peak[0]:5.0f}C {ab:4.0f}s {q.depth_above(tg):4.2f}mm")
    print(f"{lbl:>16s} | " + " | ".join(f"{c:>14s}" for c in cells))
print("  (threshold is each part's OWN Tg: PLA 60, PETG 81)")
