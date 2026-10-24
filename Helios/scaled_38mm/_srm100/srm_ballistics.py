"""Internal ballistics for the motor srm_params.py describes.  Independent of OpenMotor.

WHY A SECOND SIMULATOR
----------------------
The paper recommends dual verification with OpenMotor.  This file is the other half:
a from-scratch model that shares nothing with OpenMotor except the inputs, so
agreement between the two means something.  It writes an OpenMotor .ric of the same
motor (out/srm100.ric) so the comparison is one file-open away, and
srm_openmotor_check.py runs OpenMotor's own solver on that file when its source is
available.

MODEL
-----
  * Each BATES segment is cut into N_CELLS axial cells.  Every cell's core regresses
    at its own rate  r = r0 eta(G),  r0 = a exp(sigma_p (T - T_ref)) Pc^n;  both ends
    of every segment regress at r0 (no cross-flow along a face).  A cell whose core
    reaches the casting tube has burnt through and stops contributing.
  * Erosive burning, per cell, from the mass flux G that the surfaces upstream of it
    put through its port.  Flow runs forward -> aft: the segment's forward face, the
    core cells ahead of this one, and every segment forward of it, both faces.
      mukunda_paul      eta = 1 + 0.023 (g^0.8 - 35^0.8) when g > 35, else 1
                        g = G/(rho_p r0) (Re0/1000)^-0.125,   Re0 = rho_p r0 d / mu
      lenoir_robillard  r = r0 + alpha G^0.8 d^-0.2 exp(-beta rho_p r / G), solved
                        per cell;  alpha from the gas cp, Pr, mu and the surface
                        temperatures in srm_params (about 1.6e-5 SI)
      none              eta = 1: what OpenMotor's BATES solver assumes
    eta lags one step behind the flux; at dt = 1e-4 s against a chamber time
    constant of ~3.7 ms that costs well under 0.1 % (checked: dt 2e-4 vs 1e-4 below).
    G/(rho_p r0) = Ab_upstream / Ap does not depend on a, so Mukunda-Paul erosion is
    present at nominal a: the start-up is humped and the aft segment burns through
    first.  The mass-flux limit (1406 kg/m2s) is reported, not relied on.
  * Chamber: one gas volume at one pressure, filled from ambient at ignition, blown
    down after burnout:
        d(rho_g V)/dt = sum(rho_p A r)  -  Pc At / c*
    with rho_g = Pc / RT and RT = (c* Gamma)^2.  V is the free volume -- cores, spacer
    gaps, take-up bore, insulator bore and convergent -- plus what has burnt.
  * c* efficiency: c*_delivered = c* x CSTAR_EFF, in RT and in the nozzle flow.
  * Nozzle: 1-D isentropic Cf at the actual expansion ratio and back-pressure,
    times the conical divergence factor (1 + cos a)/2, times NOZZLE_EFF.
  * Throat does not erode (graphite; measured erosion goes in THROAT_D after a
    static fire).
  * Not modelled: the head-end-to-aft pressure drop along the core (one Pc), two-
    phase losses beyond CSTAR_EFF / NOZZLE_EFF, and the igniter.

RUNS
----
  nominal  as-cast density (RHO_PROP_ASCAST_SI), c* x CSTAR_EFF, Mukunda-Paul, T_ref.
           What the motor is expected to deliver: the csv, the plot, the .eng
           (srm_verify.py) and the designation.
  bound    theoretical density 1770 and ideal c*, both of which raise Pc, with
           Mukunda-Paul.  The MEOP basis: the burn-rate sweep, the hot-grain row and
           the critical burn-rate multiplier.
  ideal    bound with no erosive term.  This is the motor in out/srm100.ric, so
           srm_openmotor_check.py compares like with like.
  hot      bound at T_GRAIN_MAX_C.
  Lenoir-Robillard is carried as a sensitivity: it is the harsher correlation, and a
  full-scale static-fire thrust trace (load cell; the motor has no pressure port) is
  the only thing that will say which is right.

Outputs (out/):
    srm_ballistics.csv       the nominal run: t, Pc, F, Kn, regression, mdot, G at the aft port
    srm_thrust_curve.png     thrust and chamber pressure, nominal, with the bound Pc
    srm100.ric               the ideal run's motor, for OpenMotor 0.6
    srm_ballistics.json      every run's summary, the sweep and the critical a

Run:  python srm_ballistics.py
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

import srm_params as P

OUT = Path(__file__).resolve().parent / "out"

G0 = 9.80665
N_CELLS = 40
MASS_FLUX_LIMIT = 2.0 / 0.001422          # 2 lb/in^2 s, OpenMotor's default warning
EROSIVE_G_TH = 35.0                       # Mukunda-Paul threshold


# -----------------------------------------------------------------------------
# gas dynamics
# -----------------------------------------------------------------------------
def vdk_gamma(g: float = P.GAMMA) -> float:
    """Vandenkerckhove function, Gamma = sqrt(g) (2/(g+1))^((g+1)/(2(g-1)))."""
    return math.sqrt(g) * (2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0)))


def area_ratio_of_mach(M: float, g: float = P.GAMMA) -> float:
    return (1.0 / M) * ((2.0 / (g + 1.0)) * (1.0 + (g - 1.0) / 2.0 * M * M)) ** (
        (g + 1.0) / (2.0 * (g - 1.0)))


def exit_mach(eps: float, g: float = P.GAMMA) -> float:
    lo, hi = 1.0 + 1e-9, 20.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if area_ratio_of_mach(mid, g) < eps:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def pressure_ratio(M: float, g: float = P.GAMMA) -> float:
    """pe / pc for isentropic flow at Mach M."""
    return (1.0 + (g - 1.0) / 2.0 * M * M) ** (-g / (g - 1.0))


def cf_ideal(pc_pa: float, eps: float, pa: float = P.AMBIENT_PA, g: float = P.GAMMA,
             pe_pc: float | None = None) -> float:
    if pe_pc is None:
        pe_pc = pressure_ratio(exit_mach(eps, g), g)
    mom = vdk_gamma(g) * math.sqrt(2.0 * g / (g - 1.0) * (1.0 - pe_pc ** ((g - 1.0) / g)))
    return mom + eps * (pe_pc - pa / pc_pa)


def optimum_eps(pc_pa: float, pa: float = P.AMBIENT_PA, g: float = P.GAMMA) -> float:
    """Expansion ratio at which pe = pa."""
    pr = pa / pc_pa
    M = math.sqrt(2.0 / (g - 1.0) * (pr ** (-(g - 1.0) / g) - 1.0))
    return area_ratio_of_mach(M, g)


DIV_FACTOR = (1.0 + math.cos(math.radians(P.DIV_HALF_DEG))) / 2.0


# -----------------------------------------------------------------------------
# geometry
# -----------------------------------------------------------------------------
def convergent_volume_mm3() -> float:
    """Gas inside the graphite from its forward face to the start of the throat land:
    the 35 deg cone, then the upstream blend (integrated)."""
    S = P.nozzle_stations()
    r1, r2, h = S["r_entry"], S["r_up"], S["z_fwd"] - S["z_up"]
    v = math.pi * h / 3.0 * (r1 * r1 + r1 * r2 + r2 * r2)
    cr, cz = S["c_up"]
    R = P.R_THROAT_UP
    z = np.linspace(S["z_land_fwd"], S["z_up"], 401)
    r = cr - np.sqrt(np.maximum(R * R - (z - cz) ** 2, 0.0))
    return v + float(np.trapezoid(math.pi * r * r, z))


def chamber_volume() -> dict:
    """Free volume at ignition, cm^3, by where it is.  'empty' (mm^3) is the case with
    no propellant: the casting-tube bores over the grain lengths, not the cores."""
    q = math.pi / 4.0
    r_a = P.CONV_ENTRY_D / 2.0
    r_f = r_a + P.NOZ_INSUL_T * math.tan(math.radians(P.CONV_HALF_DEG))
    parts = {
        "cores": P.N_GRAINS * q * P.GRAIN_CORE ** 2 * P.GRAIN_L,
        "spacer_gaps": P.N_SPACERS * q * P.SPACER_ID ** 2 * P.SPACER_T,
        "takeup_bore": q * P.TAKEUP_ID ** 2 * P.TAKEUP_T,
        "insulator_bore": math.pi * P.NOZ_INSUL_T / 3.0 * (r_a * r_a + r_a * r_f + r_f * r_f),
        "convergent": convergent_volume_mm3(),
    }
    free = sum(parts.values())
    empty = free + P.N_GRAINS * q * (P.TUBE_ID ** 2 - P.GRAIN_CORE ** 2) * P.GRAIN_L
    out = {k + "_cm3": v / 1e3 for k, v in parts.items()}
    out.update({"free_cm3": free / 1e3, "empty_mm3": empty,
                "L_star_m": free / P.throat_area() / 1e3})
    return out


def lr_alpha(rho: float) -> float:
    """Lenoir-Robillard alpha, SI: 0.0288 cp mu^0.2 Pr^-2/3 / (rho_p c_s) (Tf-Ts)/(Ts-Ti)."""
    return (0.0288 * P.LR_CP * P.EROSIVE_MU ** 0.2 * P.LR_PR ** (-2.0 / 3.0) / (rho * P.LR_CS)
            * (P.T_FLAME_K - P.LR_TS_K) / (P.LR_TS_K - P.LR_TI_K))


# -----------------------------------------------------------------------------
# the simulation
# -----------------------------------------------------------------------------
def simulate(a_mult: float = 1.0, rho: float = P.RHO_PROP_SI, cstar: float = P.CSTAR,
             erosive: str = "mukunda_paul", T_grain_C: float = P.T_REF_C,
             throat_d: float | None = None, dt: float = 1e-4, record_dt: float = 1e-3):
    """One firing.  rho kg/m^3, cstar m/s (already multiplied by any efficiency).
    Rows every record_dt: t, pc_mpa, thrust_n, kn, xe_mm, x_core_max_mm, mdot, G_aft,
    g_aft (= G/(rho_p r0) at the aft segment's core exit), eta_max."""
    if erosive not in ("mukunda_paul", "lenoir_robillard", "none"):
        raise ValueError(erosive)
    dt_ = throat_d if throat_d is not None else P.THROAT_D
    At_mm2 = math.pi / 4.0 * dt_ ** 2
    At = At_mm2 * 1e-6
    eps = (P.EXIT_D / dt_) ** 2
    pe_pc = pressure_ratio(exit_mach(eps))
    RT = (cstar * vdk_gamma()) ** 2
    a_mm = a_mult * P.BURN_A * math.exp(P.SIGMA_P * (T_grain_C - P.T_REF_C))   # mm/s at 1 MPa
    n = P.BURN_N
    rho_mm = rho * 1e-9                                    # kg/mm^3
    mu = P.EROSIVE_MU
    alpha = lr_alpha(rho)
    g_th08 = EROSIVE_G_TH ** 0.8

    NG, NC = P.N_GRAINS, N_CELLS
    R_OD, R0, L0 = P.GRAIN_OD / 2.0, P.GRAIN_CORE / 2.0, P.GRAIN_L
    dz = L0 / NC
    z0 = np.arange(NC) * dz
    z1 = z0 + dz
    r = np.full((NG, NC), R0)          # core radius; row 0 = forward segment (flow order)
    eta = np.ones((NG, NC))
    xe = 0.0
    V_empty = chamber_volume()["empty_mm3"]
    pc = P.AMBIENT_PA
    zeros = np.zeros(NG)

    rows = []
    t, next_rec = 0.0, 0.0
    burnthrough_aft = None
    while True:
        lo, hi = xe, L0 - xe
        ell = np.clip(np.minimum(z1, hi) - np.maximum(z0, lo), 0.0, None)
        alive = (r < R_OD) & (ell > 0.0)[None, :]
        A_core = np.where(alive, 2.0 * math.pi * r * ell, 0.0)
        if hi > lo:
            kf = min(int(lo / dz), NC - 1)
            ka = min(max(int(math.ceil(hi / dz)) - 1, 0), NC - 1)
            rf, ra = r[:, kf], r[:, ka]
            A_ff = np.where(rf < R_OD, math.pi * (R_OD ** 2 - rf ** 2), 0.0)
            A_fa = np.where(ra < R_OD, math.pi * (R_OD ** 2 - ra ** 2), 0.0)
        else:
            ka = NC - 1
            A_ff = A_fa = zeros
        Ab = float(A_core.sum() + A_ff.sum() + A_fa.sum())
        burning = Ab > 0.0

        r0 = a_mm * (pc / 1e6) ** n                        # mm/s
        rate = r0 * eta
        m_core = rho_mm * A_core * rate                    # kg/s
        m_ff, m_fa = rho_mm * A_ff * r0, rho_mm * A_fa * r0
        tot = m_core.sum(axis=1) + m_ff + m_fa
        m_gen = float(tot.sum())
        m_in = np.concatenate(([0.0], np.cumsum(tot)[:-1])) + m_ff
        Ap = math.pi * np.minimum(r, R_OD) ** 2 * 1e-6    # m^2
        G = (m_in[:, None] + np.cumsum(m_core, axis=1) - 0.5 * m_core) / Ap

        r0_si = r0 * 1e-3
        d_si = 2e-3 * np.minimum(r, R_OD)
        if erosive == "mukunda_paul":
            gg = G / (rho * r0_si) * (rho * r0_si * d_si / mu / 1000.0) ** -0.125
            eta_new = np.where(gg > EROSIVE_G_TH, 1.0 + 0.023 * (np.maximum(gg, 0.0) ** 0.8 - g_th08), 1.0)
        elif erosive == "lenoir_robillard":
            C = alpha * G ** 0.8 / d_si ** 0.2
            k = P.LR_BETA * rho / np.maximum(G, 1e-9)
            rs = r0_si * eta
            for _ in range(5):
                rs = r0_si + C * np.exp(-k * rs)
            eta_new = rs / r0_si
        else:
            eta_new = eta

        if t >= next_rec - 1e-12:
            cf = cf_ideal(pc, eps, pe_pc=pe_pc) * DIV_FACTOR * P.NOZZLE_EFF if pc > 1.2 * P.AMBIENT_PA else 0.0
            G_aft = float((m_in[-1] + m_core[-1].sum()) / Ap[-1, ka]) if burning else 0.0
            rows.append({"t": t, "pc_mpa": pc / 1e6, "thrust_n": max(cf * pc * At, 0.0),
                         "kn": Ab / At_mm2, "xe_mm": xe,
                         "x_core_max_mm": float(np.minimum(r, R_OD).max() - R0),
                         "mdot": pc * At / cstar, "G_aft": G_aft,
                         "g_aft": G_aft / (rho * r0_si) if burning else 0.0,
                         "eta_max": float(eta[alive].max()) if burning else 1.0})
            next_rec += record_dt

        V = (V_empty - float(np.sum(np.where(alive, math.pi * (R_OD ** 2 - r ** 2) * ell, 0.0)))) * 1e-9
        m_noz = pc * At / cstar
        pc += RT / V * (m_gen - m_noz - pc / RT * m_gen / rho) * dt
        r = np.where(alive, r + rate * dt, r)
        if burning:
            xe += r0 * dt
        eta = eta_new
        t += dt
        if burnthrough_aft is None and bool((r[-1] >= R_OD).any()):
            burnthrough_aft = t
        if not burning and pc < 1.05 * P.AMBIENT_PA:
            break
        if t > 30.0:
            raise RuntimeError("simulation did not burn out")
    return rows, {"a_mult": a_mult, "rho_kg_m3": rho, "cstar_m_s": cstar, "erosive": erosive,
                  "T_grain_C": T_grain_C, "throat_d_mm": dt_, "dt_s": dt,
                  "aft_burnthrough_s": burnthrough_aft}


def class_of(impulse: float) -> tuple[str, float]:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    k = max(0, math.ceil(math.log2(impulse / 2.5)))
    lo, hi = 2.5 * 2 ** (k - 1), 2.5 * 2 ** k
    return letters[k], 100.0 * (impulse - lo) / (hi - lo)


def summarize(result) -> dict:
    rows, inp = result
    t = np.array([r["t"] for r in rows])
    F = np.array([r["thrust_n"] for r in rows])
    pc = np.array([r["pc_mpa"] for r in rows])
    impulse = float(np.trapezoid(F, t))
    fmax = float(F.max())
    on = np.nonzero(F >= 0.05 * fmax)[0]
    burn = float(t[on[-1]] - t[on[0]])
    burning = [r for r in rows if r["kn"] > 0 and r["pc_mpa"] > 0.5]
    pc_avg = sum(r["pc_mpa"] for r in burning) / len(burning)
    mprop = P.prop_mass() * inp["rho_kg_m3"] / P.RHO_PROP_SI
    letter, pct = class_of(impulse)
    early = t <= 0.5
    return {
        "inputs": inp,
        "impulse_ns": impulse,
        "class": letter,
        "class_percent": pct,
        "designation": f"{letter}{round(impulse / burn):d}",
        "burn_time_s": burn,
        "avg_thrust_n": impulse / burn,
        "peak_thrust_n": fmax,
        "pc_peak_mpa": float(pc.max()),
        "t_pc_peak_s": float(t[int(pc.argmax())]),
        "pc_startup_peak_mpa": float(pc[early].max()),
        "pc_avg_mpa": pc_avg,
        "kn_initial": P.kn(0.0),
        "kn_peak": max(r["kn"] for r in rows),
        "isp_s": impulse / (mprop * G0),
        "prop_mass_kg": mprop,
        "G_aft_peak_kg_m2s": max(r["G_aft"] for r in rows),
        "g_aft_initial": next(r["g_aft"] for r in rows if r["g_aft"] > 0),
        # over the burn proper: at the first instants Pc (and so Re0) is low and eta spikes
        "eta_max": max(r["eta_max"] for r in rows if r["pc_mpa"] >= 0.5 * float(pc.max())),
        "aft_burnthrough_s": inp["aft_burnthrough_s"],
        "port_throat": (math.pi / 4.0 * P.GRAIN_CORE ** 2) / P.throat_area(),
        "expansion": P.expansion_ratio(),
        "eps_optimum_at_avg_pc": optimum_eps(1e6 * pc_avg),
        "cf_delivered_at_avg": cf_ideal(1e6 * pc_avg, P.expansion_ratio()) * DIV_FACTOR * P.NOZZLE_EFF,
    }


def critical_a(**kw) -> float:
    """The burn-rate multiplier at which the peak pressure reaches MEOP.  Pc goes as
    a^(1/(1-n)), so a <- a (MEOP/Pc)^(1-n) converges in a few runs."""
    a = 1.0
    for _ in range(10):
        pk = max(r["pc_mpa"] for r in simulate(a_mult=a, dt=2e-4, **kw)[0])
        if abs(pk - P.MEOP) < 1e-3:
            break
        a *= (P.MEOP / pk) ** (1.0 - P.BURN_N)
    return a


# -----------------------------------------------------------------------------
# outputs
# -----------------------------------------------------------------------------
def write_csv(rows, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: f"{v:.6g}" for k, v in r.items()})


def write_plot(nominal, bound, ideal, s, path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    t = [r["t"] for r in nominal]
    fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
    ax.plot(t, [r["thrust_n"] for r in nominal], color="#c0392b", lw=2, label="thrust, nominal")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("thrust [N]", color="#c0392b")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(t, [r["pc_mpa"] for r in nominal], color="#2c3e50", lw=1.4, ls="--", label="Pc, nominal")
    ax2.plot([r["t"] for r in bound], [r["pc_mpa"] for r in bound], color="#8e44ad", lw=1.0, ls="-.",
             label="Pc, MEOP bound (1770, ideal c*, erosive)")
    ax2.plot([r["t"] for r in ideal], [r["pc_mpa"] for r in ideal], color="#7f8c8d", lw=0.9, ls=":",
             label="Pc, no erosive term (OpenMotor case)")
    ax2.axhline(P.MEOP, color="#7f8c8d", lw=1, ls=":")
    ax2.text(t[-1], P.MEOP, "  MEOP", va="center", color="#7f8c8d", fontsize=8)
    ax2.set_ylabel("chamber pressure [MPa]", color="#2c3e50")
    ax2.set_ylim(0, P.MEOP * 1.1)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", fontsize=7)
    ax.set_title(f"SRM-100  {s['designation']}   I = {s['impulse_ns']:.0f} N s   "
                 f"tb = {s['burn_time_s']:.2f} s   Isp = {s['isp_s']:.0f} s  (nominal)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def openmotor_dict() -> dict:
    """The motor in OpenMotor 0.6's own schema (SI): the IDEAL run's inputs (density
    1770, ideal c*, no erosive term).  T is picked; M is solved so that OpenMotor's
    c* = sqrt(g R T / M) / (g sqrt((2/(g+1))^((g+1)/(g-1)))) equals ours."""
    g = P.GAMMA
    term = g * math.sqrt((2.0 / (g + 1.0)) ** ((g + 1.0) / (g - 1.0)))
    M = g * 8314.462618 * P.T_FLAME_K / (P.CSTAR * term) ** 2
    grain = {"type": "BATES", "properties": {
        "diameter": P.GRAIN_OD * 1e-3, "coreDiameter": P.GRAIN_CORE * 1e-3,
        "length": P.GRAIN_L * 1e-3, "inhibitedEnds": "Neither"}}
    return {
        "config": {"ambPressure": P.AMBIENT_PA, "burnoutThrustThres": 0.1,
                   "burnoutWebThres": 0.001 / 39.37, "flowSeparationWarnPercent": 0.05,
                   "mapDim": 750, "maxMachNumber": 0.7, "maxMassFlux": MASS_FLUX_LIMIT,
                   "maxPressure": P.MEOP * 1e6, "minPortThroat": 2.0,
                   "sepPressureRatio": 0.4, "timestep": 0.01},
        "grains": [grain for _ in range(P.N_GRAINS)],
        "nozzle": {"throat": P.THROAT_D * 1e-3, "exit": P.EXIT_D * 1e-3,
                   "efficiency": P.NOZZLE_EFF, "divAngle": P.DIV_HALF_DEG,
                   "convAngle": P.CONV_HALF_DEG, "throatLength": P.THROAT_LAND * 1e-3,
                   "slagCoeff": 0.0, "erosionCoeff": 0.0},
        "propellant": {"name": P.PROP_NAME, "density": P.RHO_PROP_SI, "tabs": [{
            "minPressure": 0.0, "maxPressure": 1.0e7,
            "a": P.BURN_A * 1e-3 / (1e6 ** P.BURN_N), "n": P.BURN_N,
            "k": g, "t": P.T_FLAME_K, "m": M}]},
    }


def write_ric(path: Path) -> None:
    """OpenMotor's file is YAML with a python-tagged header; written by hand so this
    script does not need OpenMotor installed."""
    import yaml
    body = yaml.safe_dump({"data": openmotor_dict()}, sort_keys=True, default_flow_style=False)
    body += ("type: !!python/object/apply:uilib.fileIO.fileTypes\n- 3\n"
             "version: !!python/tuple\n- 0\n- 6\n- 2\n")
    path.write_text(body)


def main() -> dict:
    OUT.mkdir(exist_ok=True)
    cstar_del = P.CSTAR * P.CSTAR_EFF
    cham = chamber_volume()
    print(f"SRM-100 ballistics ({P.N_GRAINS} x {N_CELLS} cells, independent of OpenMotor)")
    print(f"  free volume {cham['free_cm3']:.1f} cm^3 (cores {cham['cores_cm3']:.1f}, gaps "
          f"{cham['spacer_gaps_cm3']:.1f}, take-up {cham['takeup_bore_cm3']:.1f}, insulator "
          f"{cham['insulator_bore_cm3']:.1f}, convergent {cham['convergent_cm3']:.1f});  "
          f"L* {cham['L_star_m']:.2f} m")

    res = {
        "nominal": simulate(rho=P.RHO_PROP_ASCAST_SI, cstar=cstar_del),
        "bound": simulate(),
        "ideal": simulate(erosive="none"),
        "hot": simulate(T_grain_C=P.T_GRAIN_MAX_C),
        "lenoir_robillard": simulate(erosive="lenoir_robillard"),
        "lenoir_robillard_hot": simulate(erosive="lenoir_robillard", T_grain_C=P.T_GRAIN_MAX_C),
    }
    runs = {k: summarize(v) for k, v in res.items()}
    nom = runs["nominal"]
    write_csv(res["nominal"][0], OUT / "srm_ballistics.csv")
    plotted = write_plot(res["nominal"][0], res["bound"][0], res["ideal"][0], nom, OUT / "srm_thrust_curve.png")
    write_ric(OUT / "srm100.ric")

    keys = ("designation", "impulse_ns", "class_percent", "burn_time_s", "avg_thrust_n", "peak_thrust_n",
            "pc_startup_peak_mpa", "pc_peak_mpa", "pc_avg_mpa", "kn_peak", "isp_s", "prop_mass_kg",
            "G_aft_peak_kg_m2s", "g_aft_initial", "eta_max", "aft_burnthrough_s")
    names = list(runs)
    print(f"\n  {'':22s}" + "".join(f"{k[:14]:>15s}" for k in names))
    for k in keys:
        cells = []
        for nm in names:
            v = runs[nm][k]
            cells.append(f"{v:>15s}" if isinstance(v, str) else
                         f"{'-':>15s}" if v is None else f"{v:15.4g}")
        print(f"  {k:22s}" + "".join(cells))
    print(f"  (nominal: rho {P.RHO_PROP_ASCAST_SI:.0f}, c* {cstar_del:.0f}, Mukunda-Paul, {P.T_REF_C:.0f} C;"
          f"  bound/ideal/hot: rho {P.RHO_PROP_SI:.0f}, c* {P.CSTAR:.0f};  hot = {P.T_GRAIN_MAX_C:.0f} C)")

    # dt convergence on the bound case
    pk2 = max(r["pc_mpa"] for r in simulate(dt=2e-4)[0])
    dt_err = abs(pk2 - runs["bound"]["pc_peak_mpa"]) / runs["bound"]["pc_peak_mpa"]
    print(f"\n  dt check: bound peak Pc at dt 2e-4 differs from dt 1e-4 by {100 * dt_err:.3f} %")

    print(f"\nburn-rate uncertainty, MEOP bound (rho {P.RHO_PROP_SI:.0f}, ideal c*, Mukunda-Paul), "
          f"MEOP {P.MEOP:.1f} MPa;  * = aft-port flux over {MASS_FLUX_LIMIT:.0f} kg/m2s")
    sweep = []
    rows_spec = [(k, P.T_REF_C, "mukunda_paul") for k in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4)]
    rows_spec += [(1.0, P.T_GRAIN_MAX_C, "mukunda_paul"),
                  (1.0, P.T_REF_C, "lenoir_robillard"), (1.0, P.T_GRAIN_MAX_C, "lenoir_robillard")]
    for k, T, ero in rows_spec:
        ss = summarize(simulate(a_mult=k, T_grain_C=T, erosive=ero, dt=2e-4))
        over = bool(ss["G_aft_peak_kg_m2s"] > MASS_FLUX_LIMIT)
        sweep.append({"a_mult": k, "T_grain_C": T, "erosive": ero, "pc_peak_mpa": ss["pc_peak_mpa"],
                      "pc_startup_peak_mpa": ss["pc_startup_peak_mpa"], "impulse_ns": ss["impulse_ns"],
                      "burn_time_s": ss["burn_time_s"], "margin_to_meop": P.MEOP / ss["pc_peak_mpa"],
                      "G_aft_peak_kg_m2s": ss["G_aft_peak_kg_m2s"], "g_aft_initial": ss["g_aft_initial"],
                      "eta_max": ss["eta_max"], "over_mass_flux_limit": over})
        tag = {"mukunda_paul": "M-P", "lenoir_robillard": "L-R"}[ero]
        print(f"  a x {k:.1f} {T:3.0f} C {tag}: Pc peak {ss['pc_peak_mpa']:5.2f} MPa  MEOP/Pc "
              f"{P.MEOP / ss['pc_peak_mpa']:4.2f}  start {ss['pc_startup_peak_mpa']:4.2f}  "
              f"G_aft {ss['G_aft_peak_kg_m2s']:5.0f}{'*' if over else ' '}  G/(rho r0) "
              f"{ss['g_aft_initial']:5.1f}  eta {ss['eta_max']:4.2f}  tb {ss['burn_time_s']:4.2f} s  "
              f"I {ss['impulse_ns']:6.0f} N s")

    crit = {
        "none_20C": critical_a(erosive="none"),
        "mukunda_paul_20C": critical_a(),
        "mukunda_paul_40C": critical_a(T_grain_C=P.T_GRAIN_MAX_C),
        "lenoir_robillard_20C": critical_a(erosive="lenoir_robillard"),
        "lenoir_robillard_40C": critical_a(erosive="lenoir_robillard", T_grain_C=P.T_GRAIN_MAX_C),
    }
    print("\ncritical burn-rate multiplier (peak Pc = MEOP), MEOP bound:")
    for k, v in crit.items():
        print(f"  {k:22s} a x {v:.3f}")

    hot, lr_hot = runs["hot"], runs["lenoir_robillard_hot"]
    meop = {
        "rule": "peak Pc x 1.3 <= MEOP, MEOP bound, hottest grain",
        "mukunda_paul_hot_pc_mpa": hot["pc_peak_mpa"],
        "mukunda_paul_hot_x1p3_mpa": 1.3 * hot["pc_peak_mpa"],
        "mukunda_paul_passes": bool(1.3 * hot["pc_peak_mpa"] <= P.MEOP),
        "lenoir_robillard_hot_pc_mpa": lr_hot["pc_peak_mpa"],
        "lenoir_robillard_hot_margin": P.MEOP / lr_hot["pc_peak_mpa"],
        "lenoir_robillard_passes": bool(1.3 * lr_hot["pc_peak_mpa"] <= P.MEOP),
    }
    print(f"\nMEOP rule (x 1.3, {P.T_GRAIN_MAX_C:.0f} C grain):  Mukunda-Paul {hot['pc_peak_mpa']:.2f} x 1.3 = "
          f"{meop['mukunda_paul_hot_x1p3_mpa']:.2f} MPa {'<=' if meop['mukunda_paul_passes'] else '>'} "
          f"{P.MEOP:.1f};  Lenoir-Robillard sensitivity {lr_hot['pc_peak_mpa']:.2f} MPa, margin "
          f"{meop['lenoir_robillard_hot_margin']:.2f}"
          f"{'' if meop['lenoir_robillard_passes'] else ' (under 1.3)'}")

    letter, pct = nom["class"], nom["class_percent"]
    label = (f"{nom['designation']} nominal ({pct:.1f} % into class {letter}); "
             + (f"{chr(ord(letter) - 1)}/{letter} borderline until a static fire measures it"
                if pct < 10.0 else f"class {letter}"))
    print(f"\ndesignation: {label}")
    s = {
        "designation": nom["designation"],
        "class_label": label,
        "chamber": cham,
        "model": {"cells_per_grain": N_CELLS, "erosive_threshold_g": EROSIVE_G_TH,
                  "mu_pa_s": P.EROSIVE_MU, "lr_alpha_si": lr_alpha(P.RHO_PROP_SI), "lr_beta": P.LR_BETA,
                  "sigma_p_per_K": P.SIGMA_P, "cstar_eff": P.CSTAR_EFF, "dt_check_rel": dt_err},
        "runs": runs,
        "a_sweep": sweep,
        "critical_a": crit,
        "meop_check": meop,
        "mass_flux_limit_kg_m2s": MASS_FLUX_LIMIT,
    }
    (OUT / "srm_ballistics.json").write_text(json.dumps(s, indent=2))
    print(f"\nwrote out/srm_ballistics.csv (nominal), out/srm100.ric (ideal), out/srm_ballistics.json"
          f"{', out/srm_thrust_curve.png' if plotted else ' (no matplotlib: no plot)'}")
    return s


if __name__ == "__main__":
    main()
