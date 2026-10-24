// Helios flight model: the KNSB motor's internal ballistics, a one-dimensional
// vertical flight with drag, the ESP32's barometric apogee detection, and the
// side-door deployment. Pure functions of documented inputs, so the build, the
// audit and the page all replay the same numbers.
//
// Measured (Helios files): airframe Ø65.52; part volumes from the STLs at
// 1.04 g/cm³ (ABS, solid); grain 34.4 × 14 BATES, two 67.5 mm segments, 91.5 g
// each (_casting_molds); bay 125.3 g with electronics and battery (_avionics);
// side-door nose 114 g, MG90S servo, 0.5 × 5 × 20 springs, door releases at 26°.
// Assumed (marked): KNSB burn rate from R. Nakka's measured coefficients, c*
// 95 % of 908 m/s, Cf 1.36, throat Ø7.5, Cd 0.55, 30 in flat canopy Cd 0.75,
// 1.2 m rail, still air at sea level, BMP280 noise 0.3 m.

export const MOTOR = {
  caseOD: 38, caseID: 35, caseLen: 152,
  grainOD: 34.4, coreD: 14.0, segLen: 67.5, segments: 2, linerOD: 34.8,
  segMass: 91.5,           // g, _casting_molds/README
  throatD: 7.5, exitD: 16.8,
  cStar: 908 * 0.95,       // m/s
  Cf: 1.36,
  web: (34.4 - 14.0) / 2,  // mm
};

// Nakka, KNSB (fine oxidiser): r = a · P^n, P in MPa, r in mm/s.
const RATE = [
  [0.807, 10.708, 0.625],
  [1.503, 8.763, -0.314],
  [3.792, 7.852, -0.013],
  [8.259, 3.907, 0.535],
  [Infinity, 9.653, 0.064],
];
export function burnRate(P) {
  const [, a, n] = RATE.find(([top]) => P < top);
  return a * Math.max(P, 0.101) ** n;
}

export function burnArea(x) {
  const { coreD, segLen, grainOD, segments } = MOTOR;
  const d = Math.min(coreD + 2 * x, grainOD);
  const L = Math.max(segLen - 2 * x, 0);
  if (d >= grainOD || L <= 0) return 0;
  return segments * (Math.PI * d * L + 2 * (Math.PI / 4) * (grainOD ** 2 - d ** 2));
}

// Equilibrium chamber pressure for a Kn: P = Kn·ρ·r(P)·c* (fixed point).
const RHO = (MOTOR.segMass / ((Math.PI / 4) * (MOTOR.grainOD ** 2 - MOTOR.coreD ** 2) * MOTOR.segLen)) * 1e-3 * 1e9; // kg/m³
function pressureOf(Kn) {
  let P = 2;
  for (let i = 0; i < 60; i++) P = 0.5 * P + 0.5 * ((Kn * RHO * burnRate(P) * 1e-3 * MOTOR.cStar) / 1e6);
  return P;
}

// Motor burn: web regression x(t), chamber pressure, thrust, mass flow. A 40 ms
// fill on ignition and a 60 ms tail-off as the chamber empties.
export function motorBurn(dt = 0.001) {
  const At = (Math.PI / 4) * MOTOR.throatD ** 2; // mm²
  const out = [];
  let x = 0, t = 0, Pc = 0, burned = 0;
  const total = MOTOR.segMass * MOTOR.segments;
  while (true) {
    const Ab = burnArea(x);
    const Peq = Ab > 0 ? pressureOf(Ab / At) : 0;
    const tau = Ab > 0 ? 0.04 : 0.06;
    Pc += (Peq - Pc) * (1 - Math.exp(-dt / tau));
    const r = Ab > 0 ? burnRate(Math.max(Pc, 0.2)) : 0;
    const mdot = (RHO * (Ab * 1e-6) * (r * 1e-3)) * 1000; // g/s
    const F = Math.max(0, MOTOR.Cf * Pc * 1e6 * At * 1e-6 - 0.101e6 * (Math.PI / 4) * (MOTOR.exitD * 1e-3) ** 2 * 0);
    out.push({ t, x, Pc, F, mdot, Ab });
    if (Ab > 0) {
      x += r * dt;
      burned += mdot * dt;
    }
    t += dt;
    if (Ab <= 0 && Pc < 0.02) break;
  }
  const scale = total / burned; // the burned mass equals the cast mass
  for (const s of out) s.mdot *= scale;
  const impulse = out.reduce((sum, s) => sum + s.F * dt, 0);
  return { samples: out, impulse, burn: out.find((s) => s.Ab <= 0)?.t ?? t, peakF: Math.max(...out.map((s) => s.F)), peakP: Math.max(...out.map((s) => s.Pc)), rho: RHO };
}

// Masses (g).
const ABS = 1.04;
export const MASS = {
  tail: 246.5 * ABS, lower: 79.9 * ABS, coupler: 15.5 * ABS, mbody: 80.2 * ABS, cap: 71.7 * ABS, guides: 2 * 5.5 * ABS,
  bay: 125.3, noseHousing: 73.1 * ABS, door: 36.6 * ABS, servo: 13.4, springsScrews: 1.5,
  chute: 45, cord: 30,
  motorCase: Math.PI * ((19 ** 2 - 17.5 ** 2) * 152) * 2.7e-3, nozzle: 24, closure: 14, liners: 2,
  propellant: MOTOR.segMass * MOTOR.segments,
};
export const LIFTOFF = Object.values(MASS).reduce((a, b) => a + b, 0);

const AREA = Math.PI * (65.52e-3 / 2) ** 2;
export const AERO = { Cd: 0.55, area: AREA, tumbleCdA: 0.012, chuteCdA: 0.75 * Math.PI * (0.762 / 2) ** 2, rail: 1.2 };

export const atmosphere = (h) => {
  const T = 288.15 - 0.0065 * h;
  const p = 101325 * (T / 288.15) ** 5.25588;
  return { p, rho: p / (287.05 * T) };
};
export const altitudeOf = (p) => 44330.77 * (1 - (p / 101325) ** 0.190263);

// Deployment timing after the ESP32 commands OPEN (s), from the nose CAD and
// the servo: MG90S 0.10 s/60° (no load); springs kick the door, it leaves at 26°.
export const DEPLOY = { servo: 0.1, kick: 0.035, release: 0.055, bagOut: 0.25, lineStretch: 0.6, inflate: 0.9, snatchN: 253 };

function mulberry(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function flight({ dt = 0.002 } = {}) {
  const motor = motorBurn();
  const thrustAt = (t) => {
    const i = Math.floor(t / 0.001);
    return i < motor.samples.length ? motor.samples[i] : { F: 0, mdot: 0, x: MOTOR.web, Pc: 0 };
  };
  const g = 9.80665;
  const ignite = 0.25; // igniter to first thrust
  let t = 0, h = 0, v = 0, m = LIFTOFF;
  const rows = [];
  const events = { ignition: 0, firstThrust: ignite };
  const rand = mulberry(20261018);
  const gauss = () => Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand());
  let baroAlt = 0, baroMax = 0, nextSample = 0, armedAt = 0, below = 0;
  let detect = null, chuteCdA = 0, landed = false, doorGone = false;
  while (!landed && t < 400) {
    const burnT = t - ignite;
    const s = burnT >= 0 ? thrustAt(burnT) : { F: 0, mdot: 0, x: 0, Pc: 0 };
    const atm = atmosphere(Math.max(h, 0));
    let F = s.F;
    let drag = 0;
    const since = detect === null ? -1 : t - detect;
    if (since >= DEPLOY.servo + DEPLOY.kick + DEPLOY.release && !doorGone) {
      doorGone = true;
      m -= MASS.door;
      events.doorGone = t;
    }
    if (since >= DEPLOY.lineStretch) {
      const f = Math.min(1, (since - DEPLOY.lineStretch) / DEPLOY.inflate);
      chuteCdA = AERO.chuteCdA * f * f * (3 - 2 * f);
      if (!events.lineStretch) events.lineStretch = t;
      if (f >= 1 && !events.inflated) events.inflated = t;
    }
    const tumbling = events.apogee !== undefined;
    const CdA = (tumbling ? AERO.tumbleCdA : AERO.Cd * AERO.area) + chuteCdA;
    drag = 0.5 * atm.rho * v * Math.abs(v) * CdA;
    const weight = m * 1e-3 * g;
    let a = (F - drag - weight) / (m * 1e-3);
    if (h <= 0 && a < 0 && v <= 0 && !events.liftoff) a = 0; // on the pad
    if (a > 0 && !events.liftoff && h <= 0) events.liftoff = t;
    v += a * dt;
    h += v * dt;
    if (h < 0 && events.liftoff) {
      h = 0;
      landed = true;
      events.touchdown = t;
      events.touchdownV = -v;
    }
    if (h < 0) h = 0;
    m -= s.mdot * dt;
    if (!events.railExit && h >= AERO.rail) events.railExit = t, events.railV = v;
    if (!events.burnout && burnT > 0 && s.F <= 0 && events.liftoff) events.burnout = t, events.burnoutV = v, events.burnoutH = h;
    if (events.apogee === undefined && events.liftoff && v <= 0 && t > ignite + 1) events.apogee = t, events.apogeeH = h;
    // ESP32 loop at 50 Hz: BMP280 altitude, an EMA, apogee once 2 m below the
    // best for 3 samples in a row, armed 3 s after lift-off above 60 m.
    if (t >= nextSample) {
      nextSample += 0.02;
      const raw = altitudeOf(atmosphere(Math.max(h, 0)).p) + 0.3 * gauss();
      baroAlt += (raw - baroAlt) * 0.35;
      baroMax = Math.max(baroMax, baroAlt);
      if (events.liftoff && !armedAt && t - events.liftoff > 3 && baroAlt > 60) armedAt = t;
      if (armedAt && detect === null) {
        below = baroMax - baroAlt > 2 ? below + 1 : 0;
        if (below >= 3) {
          detect = t;
          events.detect = t;
          events.detectH = h;
        }
      }
    }
    rows.push([t, h, v, a, F, m, baroAlt, s.x, s.Pc, chuteCdA, drag]);
    t += dt;
  }
  return { rows, events, motor, dt };
}
