import numpy as np
from soak import run, MAT

print("=" * 96)
print("COLLAR DEPTH PROFILE - the lugs/bolts sit 2-13 mm outboard of the bore")
print("=" * 96)
for lb, tb, ha, lbl in ((0.045, 1.2, 1250, "central"), (0.090, 1.5, 1460, "harsh")):
    h, p = run(t_burn=tb, h_aft=ha, l_bare=lb, mat="ABS", t_end=900.0)
    d = {q.name: q for q in p}
    q = d["travel_collar"]
    print(f"\n {lbl}:  travel_collar, 6.85 mm wall")
    for fr in (0.0, 0.15, 0.3, 0.5, 0.75, 1.0):
        j = int(np.argmin(np.abs(q.x - fr * q.wall)))
        print(f"   {fr*q.wall*1e3:5.2f} mm deep: peak {q.peak[j]:6.1f} C "
              f"at t={q.tpeak[j]:4.0f} s")
    r = d["cradle_ring aft"]
    print(f" {lbl}:  cradle_ring aft, 6.00 mm wall (1.8 mm solid shell + 30% infill)")
    for fr in (0.0, 0.3, 0.5, 1.0):
        j = int(np.argmin(np.abs(r.x - fr * r.wall)))
        print(f"   {fr*r.wall*1e3:5.2f} mm deep: peak {r.peak[j]:6.1f} C "
              f"at t={r.tpeak[j]:4.0f} s")

print()
print("=" * 96)
print("ITEM 5 QUANTIFIED: fraction of the total absorbed heat delivered by time T")
print("=" * 96)
POI = ["cradle_ring aft", "travel_collar", "thrust_cap sleeve", "thrust_cap annulus"]
for lb, tb, ha, lbl in ((0.045, 1.2, 1250, "central"), (0.090, 1.5, 1460, "harsh")):
    h, p = run(t_burn=tb, h_aft=ha, l_bare=lb, mat="ABS", t_end=1800.0)
    d = {q.name: q for q in p}
    print(f"\n  {lbl}")
    print(f"  {'part':20s} " + "".join(f"{f'@{s}s':>8s}" for s in (30, 60, 120, 300)))
    for n in POI:
        q = d[n]
        # stored energy in the slab vs its own maximum
        Ecur = ((q.hist_T - 20.0) * q.rc * q.dx).sum(axis=1)
        Emax = Ecur.max()
        cells = []
        for s in (30, 60, 120, 300):
            i = int(np.argmin(np.abs(q.hist_t - s)))
            cells.append(f"{Ecur[i]/Emax*100:7.0f}%")
        print(f"  {n:20s} " + "".join(cells))

print("""
  READ: by 60 s the mid-body parts have already taken 60-80 % of all the heat
  they will ever take, but the thrust_cap has taken under 25 %. That is the
  whole story of item 5 in one table.""")

print()
print("=" * 96)
print("ITEM 6  MARGIN TABLE: peak surface T vs each material's limits")
print("=" * 96)
cases = {}
for lb, tb, ha, lbl in ((0.020, 1.0, 1050, "mild"), (0.045, 1.2, 1250, "central"),
                        (0.090, 1.5, 1460, "harsh")):
    h, p = run(t_burn=tb, h_aft=ha, l_bare=lb, mat="ABS", t_end=900.0)
    cases[lbl] = {q.name: q.peak[0] for q in p}

print(f"  {'part':20s} {'mild':>7s} {'central':>8s} {'harsh':>7s} | "
      f"margin to Tg (C):  {'PLA':>6s} {'PETG':>6s} {'ASA':>6s} {'ABS':>6s}")
for n in ["cradle_ring aft", "cradle_cap aft", "travel_collar",
          "thrust_cap sleeve", "thrust_cap annulus"]:
    row = f"  {n:20s} " + "".join(f"{cases[c][n]:7.0f}" for c in ("mild", "central", "harsh"))
    T = cases["central"][n]
    m = "".join(f"{MAT[x]['Tg']-T:6.0f}" for x in ("PLA", "PETG", "ASA", "ABS"))
    print(row + "  |  (at central T)   " + m)
print("""
  Negative = already above Tg at the CENTRAL case. The two mid-body bores and
  the collar are the decision; the thrust_cap is not close to being the driver.""")

print()
print("  repo's per-part spec vs what the temperatures ask for:")
spec = {"cradle_ring aft": "PETG/PLA", "cradle_cap aft": "PETG/PLA",
        "travel_collar": "PLA", "thrust_cap sleeve": "PETG/ASA",
        "thrust_cap annulus": "PETG/ASA"}
for n, s in spec.items():
    T = cases["central"][n]
    Th = cases["harsh"][n]
    need = [m for m in ("PLA", "PETG", "ASA", "ABS") if MAT[m]["Tg"] > Th]
    print(f"    {n:20s} repo={s:9s} central {T:5.0f}C harsh {Th:5.0f}C "
          f"-> clears Tg in harsh: {','.join(need) if need else 'NONE'}")
