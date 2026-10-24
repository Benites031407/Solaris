"""Post-burnout soak model for the 38 mm KNSB stand.

Question: after burnout (thrust = 0), does the casing soak enough heat outward
to PERMANENTLY damage or DIMENSIONALLY change the printed parts that touch it?

Model
-----
A) Motor: 1-D axial finite-difference bar (6061 casing, 38.1 OD x 1.65 wall,
   240 mm) with a radially-resolved paperboard liner at each station, a lumped
   steel nozzle at s=0 and a lumped 6061 closure at s=240. Burn phase applies
   gas-side h(s) ~ G(s)^0.8 + radiation; soak phase applies natural convection
   + radiation to ambient and drains heat into the printed parts.

B) Each printed part: 1-D radial FD wall (solid printed shell + sparse infill
   core), coupled to the casing through a computed interface conductance --
   annular-gap air conduction + radiation + (where clamped) solid contact.

Coordinates: s = distance forward from the casing AFT rim, mm.
  casing            s = 0 .. 240      (global x = -25 .. 215)
  aft ring trough   s = 100.5 .. 125.5
  travel collar     s = 136 .. 148
  fwd ring trough   s = 158.5 .. 183.5
  thrust cap sleeve s = 218 .. 240 ; bearing annulus at s = 240
"""
import numpy as np

SIG = 5.670374419e-8
T_AMB = 20.0

AL_RHO, AL_CP, AL_K = 2700.0, 896.0, 167.0
ST_CP = 490.0
CAS_OD, CAS_WALL = 38.1e-3, 1.65e-3
CAS_ID = CAS_OD - 2 * CAS_WALL
CAS_L = 240e-3
A_CS = np.pi / 4 * (CAS_OD**2 - CAS_ID**2)
P_OUT, P_IN = np.pi * CAS_OD, np.pi * CAS_ID

LIN_T, LIN_K, LIN_RHO, LIN_CP = 0.84e-3, 0.060, 700.0, 1400.0
T_GAS = 1600.0 - 273.15
H_RAD_GAS = 112.0
NOZ_M, CLO_M = 0.130, 0.031
G_NOZ, G_CLO = 5.0, 3.0
K_AIR_GAP = 0.030
EPS_PL, EPS_AL = 0.90, 0.25

MAT = {
    "PLA":  dict(k=0.130, rho=1240, cp=1800, Tg=60.0, hdt=55.0, svc=50.0, E=2.3),
    "PETG": dict(k=0.220, rho=1280, cp=1150, Tg=81.0, hdt=68.0, svc=65.0, E=1.5),
    "ASA":  dict(k=0.180, rho=1070, cp=1300, Tg=100.0, hdt=86.0, svc=75.0, E=1.6),
    "ABS":  dict(k=0.200, rho=1050, cp=1400, Tg=105.0, hdt=95.0, svc=80.0, E=2.2),
}


def h_air_cyl(dT, D=CAS_OD, T_inf=T_AMB):
    dT = np.maximum(np.abs(dT), 1e-3)
    Tf = T_inf + dT / 2 + 273.15
    nu = 1.6e-5 * (Tf / 300) ** 1.75
    k = 0.0263 * (Tf / 300) ** 0.85
    Ra = 9.81 * dT * D**3 / (Tf * nu * nu / 0.7)
    Nu = (0.60 + 0.387 * Ra ** (1 / 6) / (1 + (0.559 / 0.7) ** (9 / 16)) ** (8 / 27)) ** 2
    return Nu * k / D


def h_rad_surf(T, eps, T_inf=T_AMB):
    Tk, Tik = np.asarray(T) + 273.15, T_inf + 273.15
    return eps * SIG * (Tk**4 - Tik**4) / np.maximum(Tk - Tik, 1e-6)


def gap_conductance(r_cas, r_bore, drop, th0, th1, T_m=90.0, g_min=60e-6):
    """Air-gap conduction + radiation over arc [th0,th1] from bottom-dead-centre.
    Motor centre sits `drop` below the bore centre (negative = above)."""
    th = np.linspace(th0, th1, 4001)
    g = np.maximum((r_bore - r_cas) - drop * np.cos(th), g_min)
    h_r = 1 / (1 / EPS_PL + 1 / EPS_AL - 1) * SIG * 4 * (T_m + 273.15) ** 3
    h = K_AIR_GAP / g + h_r
    return float(np.trapezoid(h, th) / (th1 - th0)), float(np.trapezoid(g, th) / (th1 - th0))


class Slab:
    """1-D radial FD wall: solid printed shell of shell_t then sparse infill."""

    def __init__(self, name, mat, r_i, wall, shell_t, infill, area_m2, h_int, nn=41):
        m = MAT[mat]
        self.name, self.mat, self.m = name, mat, m
        self.r_i, self.wall, self.A, self.h_int = r_i, wall, area_m2, h_int
        self.infill = infill
        x = np.linspace(0, wall, nn)
        self.x, self.dx = x, x[1] - x[0]
        f = np.where(x <= shell_t, 1.0, infill)
        self.k = m["k"] * f + 0.026 * (1 - f)
        self.rc = m["rho"] * m["cp"] * f
        self.kf = 2 * self.k[:-1] * self.k[1:] / (self.k[:-1] + self.k[1:])
        cap = self.rc * self.dx
        cap[0] *= 0.5
        cap[-1] *= 0.5
        self.cap = cap
        self.T = np.full(nn, T_AMB)
        self.peak = np.full(nn, T_AMB)
        self.tpeak = np.zeros(nn)
        self.above = {}          # material-threshold -> seconds above, at x=0
        self.hist_t, self.hist_T = [], []

    def step(self, T_cas, dt, t, attached=True):
        T = self.T
        q = np.zeros_like(T)
        flux = self.kf * (T[:-1] - T[1:]) / self.dx
        q[:-1] -= flux
        q[1:] += flux
        if attached:
            q_in = self.h_int * (T_cas - T[0])
        else:
            h = h_air_cyl(T[0] - T_AMB, 2 * self.r_i) + h_rad_surf(T[0], EPS_PL)
            q_in = h * (T_AMB - T[0])
        q[0] += q_in
        h_o = (h_air_cyl(T[-1] - T_AMB, 2 * (self.r_i + self.wall))
               + h_rad_surf(T[-1], EPS_PL))
        q[-1] += h_o * (T_AMB - T[-1])
        self.T = T + q / self.cap * dt
        newpk = self.T > self.peak
        self.tpeak[newpk] = t
        self.peak = np.where(newpk, self.T, self.peak)
        for lim in (self.m["svc"], self.m["hdt"], self.m["Tg"]):
            if self.T[0] > lim:
                self.above[lim] = self.above.get(lim, 0.0) + dt
        return -q_in * self.A

    def depth_above(self, Tlim):
        a = self.peak > Tlim
        return 0.0 if not a[0] else float(self.x[a][-1] * 1e3)

    def frac_above(self, Tlim):
        return self.depth_above(Tlim) / (self.wall * 1e3)


def build_parts(mat, mat_over=None):
    r_cas = CAS_OD / 2
    parts, bands = [], []
    mo = mat_over or {}

    def add(name, bore_d, wall, shell_t, infill, L_ax, th0, th1, drop,
            h_solid, s0, s1):
        r_b = bore_d / 2e3
        h_g, g_bar = gap_conductance(r_cas, r_b, drop * 1e-3, th0, th1)
        A = (th1 - th0) * r_b * L_ax * 1e-3
        p = Slab(name, mo.get(name, mat), r_b, wall * 1e-3, shell_t * 1e-3,
                 infill, A, h_g + h_solid)
        p.h_gap, p.g_bar, p.h_solid, p.s0, p.s1 = h_g, g_bar, h_solid, s0, s1
        parts.append(p)
        bands.append((s0 * 1e-3, s1 * 1e-3))
        return p

    # solid line contact under motor weight: ~0.30 mm wide Hertzian strip,
    # h_c 2000 W/m2K there, smeared over the wrapped lower half.
    h_line = 2000.0 * (0.30 / (np.pi * 19.4 / 2))
    add("cradle_ring aft", 38.8, 6.0, 1.8, 0.30, 25.0, 0.0, np.pi / 2, 0.4,
        h_line, 100.5, 125.5)
    add("cradle_ring fwd", 38.8, 6.0, 1.8, 0.30, 25.0, 0.0, np.pi / 2, 0.4,
        h_line, 158.5, 183.5)
    add("cradle_cap aft", 39.4, 5.7, 1.8, 0.30, 25.0, np.pi / 2, np.pi, -0.4,
        0.0, 100.5, 125.5)
    add("cradle_cap fwd", 39.4, 5.7, 1.8, 0.30, 25.0, np.pi / 2, np.pi, -0.4,
        0.0, 158.5, 183.5)
    # travel_collar: two M4 bolts pull 38.3 closed onto 38.0 -> real contact
    add("travel_collar", 38.3, 6.85, 1.8, 0.40, 12.0, 0.0, 2 * np.pi, 0.0,
        900.0, 136.0, 148.0)
    add("thrust_cap sleeve", 39.0, 4.5, 2.4, 1.00, 22.0, 0.0, 2 * np.pi, 0.0,
        0.0, 218.0, 240.0)
    # bearing annulus: 286.7 mm2 face on the casing rim, UNLOADED after burnout
    # (thrust = 0), 16 mm of 100% infill behind it.
    tca = Slab("thrust_cap annulus", mo.get("thrust_cap annulus", mat),
               0.017, 16e-3, 16e-3, 1.0, 286.7e-6, 300.0)
    tca.h_gap, tca.g_bar, tca.h_solid, tca.s0, tca.s1 = 300.0, 0.0, 300.0, 238.0, 240.0
    parts.append(tca)
    bands.append((238e-3, 240e-3))
    return parts, bands


def run(t_burn=1.2, h_aft=1250.0, l_bare=45e-3, mat="ABS", mat_over=None,
        pull_at=None, t_end=1800.0, n_ax=49, dt=0.012, rec=1.0):
    s = np.linspace(0, CAS_L, n_ax)
    ds = s[1] - s[0]
    Tc = np.full(n_ax, T_AMB)
    Tn = Tk = T_AMB
    nl = 7
    dxl = LIN_T / (nl - 1)
    Tl = np.full((n_ax, nl), T_AMB)
    bare = s < l_bare
    hg = h_aft * ((CAS_L - s) / CAS_L) ** 0.8 + H_RAD_GAS

    parts, bands = build_parts(mat, mat_over)
    masks = [((s >= b0) & (s <= b1)) for b0, b1 in bands]
    cover = np.zeros(n_ax)
    for m, p in zip(masks, parts):
        if p.name != "thrust_cap annulus":
            cover[m] = 1.0

    capl = LIN_RHO * LIN_CP * dxl * np.ones(nl)
    capl[0] *= 0.5
    capl[-1] *= 0.5
    C_cas = AL_RHO * AL_CP * A_CS * ds
    cap_c = C_cas * np.ones(n_ax)
    cap_c[0] *= 0.5
    cap_c[-1] *= 0.5
    kl_f = LIN_K / dxl
    h_lc = 1000.0

    hist = dict(t=[], Tc=[], Tn=[], Tk=[], E=[])
    t, nxt, attached = 0.0, 0.0, True
    dt_b = min(dt, 0.004)
    while t < t_end:
        h = dt_b if t < t_burn + 0.5 else dt
        if pull_at is not None and attached and t >= pull_at:
            attached = False
        burning = t < t_burn
        ql = np.zeros_like(Tl)
        fl = kl_f * (Tl[:, :-1] - Tl[:, 1:])
        ql[:, :-1] -= fl
        ql[:, 1:] += fl
        if burning:
            ql[:, 0] += hg * (T_GAS - Tl[:, 0])
        q_lc = h_lc * (Tl[:, -1] - Tc)
        q_lc[bare] = 0.0          # no liner there: no barrier AND no phantom sink
        ql[:, -1] -= q_lc
        Tl_new = Tl + ql / capl * h
        Tl_new[bare, :] = T_AMB

        qc = np.zeros(n_ax)
        f_ax = AL_K * A_CS * (Tc[:-1] - Tc[1:]) / ds
        qc[:-1] -= f_ax
        qc[1:] += f_ax
        qc += q_lc * P_IN * ds
        if burning:
            qc[bare] += hg[bare] * (T_GAS - Tc[bare]) * P_IN * ds
        else:
            # after burnout the bore is open to atmosphere through the nozzle:
            # weak internal free convection + radiation out of the open ends
            qc[bare] += 15.0 * (T_AMB - Tc[bare]) * P_IN * ds
        h_amb = h_air_cyl(Tc - T_AMB) + h_rad_surf(Tc, EPS_AL)
        qc += h_amb * (T_AMB - Tc) * P_OUT * ds * (1 - 0.6 * cover * attached)
        qn = G_NOZ * (Tc[0] - Tn)
        qk = G_CLO * (Tc[-1] - Tk)
        qc[0] -= qn
        qc[-1] -= qk
        if burning:
            qn += (T_GAS - Tn) * 3000.0 * 900e-6
        qn -= (h_air_cyl(Tn - T_AMB, 0.03) + h_rad_surf(Tn, 0.5)) * (Tn - T_AMB) * 40e-4
        Tn = Tn + qn * h / (NOZ_M * ST_CP)
        Tk = Tk + qk * h / (CLO_M * AL_CP)
        for m, p in zip(masks, parts):
            Tb = float(Tc[m].mean()) if m.any() else float(Tc[-1])
            drawn = p.step(Tb, h, t, attached)
            if m.any() and attached:
                qc[m] -= drawn / m.sum()
        Tc = Tc + qc / cap_c * h
        Tl = Tl_new
        t += h
        if t >= nxt:
            hist["t"].append(t)
            hist["Tc"].append(Tc.copy())
            hist["Tn"].append(Tn)
            hist["Tk"].append(Tk)
            e = (((Tc - T_AMB) * C_cas).sum() + (Tn - T_AMB) * NOZ_M * ST_CP
                 + (Tk - T_AMB) * CLO_M * AL_CP)
            hist["E"].append(e)
            for p in parts:
                p.hist_t.append(t)
                p.hist_T.append(p.T.copy())
            nxt = t + (0.05 if t < 5 else rec)
    hist["s"] = s
    for k in ("t", "Tn", "Tk", "E"):
        hist[k] = np.array(hist[k])
    hist["Tc"] = np.array(hist["Tc"])
    for p in parts:
        p.hist_t = np.array(p.hist_t)
        p.hist_T = np.array(p.hist_T)
    return hist, parts
