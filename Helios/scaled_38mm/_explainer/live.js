const D = __DATA__;
const root = document.querySelector(".hx");
const stage = root.querySelector(".hx-stage");
const backSvg = stage.querySelector(".hx-back");
const front = stage.querySelector(".hx-front");
const rocket = front.querySelector(".hx-rocket");
const anim = front.querySelector(".hx-anim");
const doorLive = front.querySelector(".hx-door-live");
const doorClip = front.querySelector("#hx-door-live path");
const canopyG = front.querySelector(".hx-canopy");
const plumeCanvas = stage.querySelector(".hx-plume");
const veilCanvas = stage.querySelector(".hx-veil");
const readout = root.querySelector("[data-readout]");
const liveText = root.querySelector("[data-live]");
const launchBtn = root.querySelector("[data-launch]");
const launchLabel = root.querySelector("[data-launch-label]");
const apartBtn = root.querySelector("[data-apart]");
const partButtons = [...root.querySelectorAll(".hx-part")];
const needle = backSvg.querySelector("[data-needle]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const P = D.P;
const DEGR = Math.PI / 180;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const lerpN = (a, b, f) => a + (b - a) * f;
const ss = (a, b, x) => smooth(a, b, x);
const fmt = (v, d = 0) => v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

// --- items ---------------------------------------------------------------------------------------
const V = D.V;
const nodes = [...rocket.querySelectorAll(".it")].map((el) => {
  const m = el.dataset.m.split(",").map(Number);
  return {
    el, piece: el.dataset.piece, ride: el.dataset.ride || el.dataset.piece, name: el.dataset.name,
    key: Number(el.dataset.k), m, lift: m[0] * V[0] + m[1] * V[1] + m[2] * V[2],
    grain: el.dataset.grain, sec: el.dataset.sec ? el.dataset.sec.split(",") : null, shown: "", flies: el.dataset.piece !== "stand",
  };
});
let order = nodes.map((_, i) => i);
const byName = (prefix) => nodes.filter((n) => n.name.startsWith(prefix));
const grainNodes = nodes.filter((n) => n.grain !== undefined);
const doorNodes = nodes.filter((n) => n.piece === "door");
const bagNodes = nodes.filter((n) => n.piece === "chute");
const armNode = byName("nose.arm")[0];
const springNodes = D.springs.map((s) => ({ back: byName(`${s.name}.back`)[0], front: byName(`${s.name}.front`)[0], ...s }));
const igniterNodes = nodes.filter((n) => n.name.startsWith("motor.igniter"));
const clipNodes = nodes.filter((n) => n.name.startsWith("stand.clip"));

// --- assemblies: one spring each, staggered --------------------------------------------------------
const IDS = Object.keys(D.pieces);
const STAGGER = D.stagger;
const SPRING = D.spring;
const piece = Object.fromEntries(IDS.map((id) => [id, { x: 0, v: 0, target: 0, pending: null }]));
let clock = 0;
let apart = false;
let selected = null;

function steerSpring(state, dt, calm) {
  if (state.pending && clock >= state.pending.at) {
    state.target = state.pending.value;
    state.pending = null;
  }
  if (calm) {
    state.x = state.target;
    state.v = 0;
    return state.pending !== null;
  }
  for (let i = 0; i < SPRING.substeps; i++) {
    const h = dt / SPRING.substeps;
    state.v += ((state.target - state.x) * SPRING.stiffness - state.v * SPRING.damping) * h;
    state.x += state.v * h;
  }
  if (Math.abs(state.target - state.x) < 2e-4 && Math.abs(state.v) < 2e-4) {
    state.x = state.target;
    state.v = 0;
    return state.pending !== null;
  }
  return true;
}

function setApart(on) {
  if (apart === on) return;
  apart = on;
  const goal = on ? 1 : 0;
  let index = 0;
  for (const id of on ? STAGGER : [...STAGGER].reverse()) {
    if (!piece[id]) continue;
    if (piece[id].target === goal) piece[id].pending = null;
    else piece[id].pending = { value: goal, at: clock + (still.matches ? 0 : index++ * SPRING.stagger) };
  }
  apartBtn.toggleAttribute("data-on", on);
  stage.toggleAttribute("data-apart", on);
  apartBtn.textContent = on ? "Put together" : "Take apart";
  describe();
  run();
}

function select(id) {
  if (selected === id) return;
  selected = id;
  for (const n of nodes) n.el.toggleAttribute("data-on", id !== null && n.piece === id);
  stage.toggleAttribute("data-focus", id !== null);
  partButtons.forEach((b) => b.toggleAttribute("data-on", b.dataset.part === id));
  stage.setAttribute("aria-valuenow", String(id ? D.order.indexOf(id) + 1 : 0));
  describe();
  run();
}

// --- camera: the viewBox follows a target window --------------------------------------------------------
const cam = { x: D.cams.rest[0], y: D.cams.rest[1], w: D.cams.rest[2], h: D.cams.rest[3] };
const camV = { x: 0, y: 0, w: 0, h: 0 };
let camTarget = D.cams.rest;
let anchor = [0, 0];
function moveAnchor(next) {
  cam.x += next[0] - anchor[0];
  cam.y += next[1] - anchor[1];
  anchor = next;
}
function steerCamera(dt, calm, seconds = 0.45) {
  const [tx, ty, tw] = camTarget;
  const goal = { x: tx + tw / 2, y: camTarget[1] + camTarget[3] / 2, w: Math.log(tw) };
  const now = { x: cam.x + cam.w / 2, y: cam.y + cam.h / 2, w: Math.log(cam.w) };
  let moving = false;
  for (const key of ["x", "y", "w"]) {
    const s = { x: now[key], v: camV[key] };
    if (settle(s, goal[key], dt, seconds, calm)) moving = true;
    now[key] = s.x;
    camV[key] = s.v;
  }
  cam.w = Math.exp(now.w);
  cam.h = (cam.w * D.H) / D.W;
  cam.x = now.x - cam.w / 2;
  cam.y = now.y - cam.h / 2;
  const box = `${cam.x.toFixed(2)} ${cam.y.toFixed(2)} ${cam.w.toFixed(2)} ${cam.h.toFixed(2)}`;
  if (backSvg.getAttribute("viewBox") !== box) {
    backSvg.setAttribute("viewBox", box);
    front.setAttribute("viewBox", box);
  }
  return moving;
}
const windowAt = (sx, sy, height) => [sx - (height * D.W) / D.H / 2, sy - height / 2, (height * D.W) / D.H, height];

// --- the flight ---------------------------------------------------------------------------------------------
const F = D.flight;
const EV = F.events;
const ROWS = F.rows;
function sampleAt(t) {
  if (t <= ROWS[0][0]) return ROWS[0];
  let lo = 0;
  let hi = ROWS.length - 1;
  if (t >= ROWS[hi][0]) return ROWS[hi];
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (ROWS[mid][0] <= t) lo = mid;
    else hi = mid;
  }
  const a = ROWS[lo];
  const b = ROWS[hi];
  const f = (t - a[0]) / (b[0] - a[0]);
  return a.map((v, i) => v + (b[i] - v) * f);
}
// replay seconds → flight seconds: slow through the burn and the deployment, fast through the descent
const SEGS = [
  [0, 1.4, -1.4, 0, "countdown"],
  [1.4, 5.4, 0, 2.0, "×½"],
  [5.4, 8.6, 2.0, EV.apogee - 0.6, "×3"],
  [8.6, 15.6, EV.apogee - 0.6, EV.inflated + 0.5, "×0.4"],
  [15.6, 20.6, EV.inflated + 0.5, EV.touchdown, "×24"],
  [20.6, 22.6, EV.touchdown, EV.touchdown, "landed"],
];
const REPLAY_END = SEGS[SEGS.length - 1][1];
function flightTime(tau) {
  for (const [a, b, t0, t1, label] of SEGS) if (tau <= b) return { t: lerpN(t0, t1, clamp((tau - a) / (b - a), 0, 1)), label };
  return { t: EV.touchdown, label: "landed" };
}
const fl = { on: false, armed: false, tau: 0, ended: false, peak: 0, stopping: 0, still: -1, stillAt: 0 };
// reduced motion: the replay shows three still moments instead of moving
const STILLS = [3.4, 11.9, 15.2, REPLAY_END];
const LIFT_CAP = 2600; // mm of real climb drawn before the camera stops following the ground

// --- rebuilds: grains, arm, springs, door, canopy --------------------------------------------------------------
const lightGrain = (n, x) => {
  const [z0, z1, rIn, rOut, a0, a1, tone] = n.sec;
  const core = Number(rIn) <= D.grain.rCore + 0.01;
  if (!core) return;
  const r = D.grain.rCore + x;
  const lo = Number(z0) + x;
  const hi = Number(z1) - x;
  if (r >= Number(rOut) - 0.05 || hi - lo < 0.2) {
    n.el.setAttribute("data-gone", "");
    return;
  }
  n.el.removeAttribute("data-gone");
  const ring = sectorRing(r, Number(rOut), Number(a0), Number(a1));
  n.el.innerHTML = solidSvg(extrude(ring, lo, hi - lo, P, { convex: false }), { tone });
};
function sectorRing(rIn, rOut, a0, a1) {
  const span = a1 - a0;
  const steps = Math.max(4, Math.ceil((span / 360) * 120));
  const out = [];
  for (let i = 0; i <= steps; i++) out.push([rOut * Math.cos((a0 + (span * i) / steps) * DEGR), rOut * Math.sin((a0 + (span * i) / steps) * DEGR)]);
  for (let i = 0; i <= steps; i++) out.push([rIn * Math.cos((a1 - (span * i) / steps) * DEGR), rIn * Math.sin((a1 - (span * i) / steps) * DEGR)]);
  return out;
}
let grainBurn = -1;
function burnGrains(x) {
  const q = Math.round(x * 20) / 20;
  if (q === grainBurn) return;
  grainBurn = q;
  for (const n of grainNodes) {
    if (q <= 0) {
      if (n.cold) n.el.innerHTML = n.cold;
      n.el.removeAttribute("data-gone");
      continue;
    }
    n.cold ??= n.el.innerHTML;
    lightGrain(n, q);
  }
}

let armShown = 0;
function setArm(deg) {
  if (Math.abs(deg - armShown) < 0.05) return;
  armShown = deg;
  const A = D.arm;
  armNode.cold ??= armNode.el.innerHTML;
  if (deg === 0) {
    armNode.el.innerHTML = armNode.cold;
    return;
  }
  const c = Math.cos(deg * DEGR);
  const s = Math.sin(deg * DEGR);
  const poly = [[-A.half, 0], [A.half, 0], [A.half, A.len], [-A.half, A.len]].map(([y, z]) => [y * c - z * s, y * s + z * c]);
  const F3 = G.frameOf(A.o, A.a, A.u, [0, 0, 1]);
  armNode.el.innerHTML = solidSvg(G.prismOf(F3, poly, A.x0, A.x1, P), { tone: "hi" });
}

function coilPaths(o, a, r, len, turns) {
  const F3 = G.frameAlong(o, a);
  const steps = Math.ceil(turns * 28);
  const runs = { back: [], front: [] };
  let run = null;
  let side = null;
  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const s = len * (u - (0.6 * Math.sin(2 * Math.PI * u)) / (2 * Math.PI));
    const ang = 2 * Math.PI * turns * u;
    const p = iso(G.pointOf(F3, s, r, ang), P);
    const facing = G.dot3(G.radialOf(F3, ang), V) >= 0;
    if (facing !== side) {
      if (run) run.push(p);
      run = [p];
      runs[facing ? "front" : "back"].push(run);
      side = facing;
    } else run.push(p);
  }
  const d = (list) => list.map((pts) => "M" + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L")).join("");
  return { back: d(runs.back), front: d(runs.front) };
}
let springShown = -1;
function setSprings(length) {
  const q = Math.round(length * 20) / 20;
  if (q === springShown) return;
  springShown = q;
  for (const s of springNodes) {
    const c = coilPaths(s.o, s.a, 2.25, q, 10);
    s.back.el.querySelector("path").setAttribute("d", c.back);
    s.front.el.querySelector("path").setAttribute("d", c.front);
  }
}

// door: a rotation about the hinge plus a translation, rebuilt from the kit's lathe
const DO = D.door;
const og = DO.og;
const ogSlope = (z) => {
  if (z <= og.zog) return 0;
  if (z >= og.tipZ) return -(z - og.zc) / Math.max(1e-6, Math.sqrt(Math.max(1e-9, og.rn * og.rn - (z - og.zc) ** 2)));
  return -(z - og.cz) / Math.sqrt(og.rho ** 2 - (z - og.cz) ** 2);
};
function rotation(axis, deg) {
  const [x, y, z] = G.unit3(axis);
  const c = Math.cos(deg * DEGR);
  const s = Math.sin(deg * DEGR);
  const t = 1 - c;
  return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y], [t * x * y + s * z, t * y * y + c, t * y * z - s * x], [t * x * z - s * y, t * y * z + s * x, t * z * z + c]];
}
const mulM = (M3, p) => [M3[0][0] * p[0] + M3[0][1] * p[1] + M3[0][2] * p[2], M3[1][0] * p[0] + M3[1][1] * p[1] + M3[1][2] * p[2], M3[2][0] * p[0] + M3[2][1] * p[1] + M3[2][2] * p[2]];
const polyD = (pts) => "M" + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L") + "Z";
const lineD = (pts) => "M" + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L");
function doorSvg(deg, shift, lift) {
  const Rm = rotation(DO.axis, deg);
  const H3 = DO.hinge;
  const xf = (p) => G.add3(G.add3(H3, mulM(Rm, G.sub3(p, H3))), [shift[0], shift[1], shift[2] + lift]);
  const pr = (p) => iso(xf(p), P);
  const frame = (o) => ({ o: xf(o), a: mulM(Rm, [0, 0, 1]), u: mulM(Rm, [1, 0, 0]), v: mulM(Rm, [0, 1, 0]) });
  doorClip.setAttribute("d", polyD(DO.region3.map(pr)) + polyD(DO.window3.map(pr)));
  const shell = G.solidOf(DO.ogive, frame(DO.origin), P, { smooth: { slope: ogSlope, rows: 4 } });
  let out = `<g clip-path="url(#hx-door-live)">${solidSvg(shell, { tone: "hi" })}</g>`;
  for (const f of DO.floor) out += solidSvg(G.prismOf(frame([0, 0, 0]), f.ring, f.z0, f.z0 + f.h, P), { tone: "hi" });
  out += lineSvg(lineD(DO.joint.map(pr)), { tone: "lo" }) + lineSvg(lineD(DO.split.map(pr)), { tone: "faint" });
  return out;
}
// the door's motion after the servo lets go: the springs kick its foot out, it swings
// about its top tab and flies off at 26°, still turning
const KICK = D.deploy.kick + D.deploy.release;
function doorPose(since) {
  if (since <= 0) return { deg: 0, shift: [0, 0, 0] };
  const x = Math.min(1, since / KICK);
  const deg = 26 * (0.35 * x + 0.65 * x * x);
  if (since <= KICK) return { deg, shift: [0, 0, 0] };
  const dt = since - KICK;
  const w = (26 * 1.65) / KICK;
  const out = [Math.cos(120 * DEGR), Math.sin(120 * DEGR), 0];
  const fly = 0.45 * dt + 2.2 * dt * dt;
  return { deg: deg + w * dt, shift: [out[0] * fly * 1000, out[1] * fly * 1000, -900 * dt * dt] };
}
function springLength(pose, lift) {
  const s = D.springs[0];
  if (pose.shift[0] !== 0 || pose.shift[1] !== 0) return s.free;
  const Rm = rotation(DO.axis, pose.deg);
  const p = G.add3(s.o, G.mul3(s.a, s.closed));
  const q = G.add3(DO.hinge, mulM(Rm, G.sub3(p, DO.hinge)));
  return clamp(s.closed + G.dot3(G.sub3(q, p), s.a), s.closed, s.free);
}

// canopy: a dome that streams out of its bag, then fills
const NX = [Math.cos(120 * DEGR), Math.sin(120 * DEGR), 0];
function canopySvg(q, axis, u, s, lift) {
  const R0 = 262;
  const H0 = 230;
  const L = 580;
  const se = s >= 1 ? s : s * s * (3 - 2 * s);
  const rs = lerpN(0.07 * R0, R0, se);
  const hd = lerpN(1.6 * H0, H0, se);
  const zs = Math.sqrt(Math.max(1, L * L - rs * rs)) * u;
  const prof = [];
  for (let i = 0; i <= 16; i++) {
    const b = (1.72 * i) / 16;
    prof.push([zs + hd * Math.cos(b) - hd * Math.cos(1.72), Math.max(0.1, rs * Math.sin(b)), i > 0 && i < 16 ? 1 : 0]);
  }
  prof.reverse();
  const F3 = G.frameAlong(G.add3(q, [0, 0, lift]), axis);
  const dome = G.lathe([[prof[0][0], 0], ...prof, [prof[prof.length - 1][0], 0]], F3, P, { smooth: true, steps: 64 });
  const seams = [];
  for (let g = 0; g < 8; g++) {
    const ang = (g / 8) * Math.PI * 2;
    const facing = G.dot3(G.radialOf(F3, ang), V);
    if (facing < 0.05) continue;
    seams.push(lineD(prof.map(([z, r]) => iso(G.pointOf(F3, z, r * 0.995, ang), P))));
  }
  const lines = [];
  for (let g = 0; g < 8; g++) {
    const ang = (g / 8) * Math.PI * 2;
    const skirt = prof[prof.length - 1];
    lines.push(lineD([iso(G.pointOf(F3, 0, 0, 0), P), iso(G.pointOf(F3, skirt[0], skirt[1], ang), P)]));
  }
  return { dome: solidSvg(dome, { tone: "hi", inner: lineSvg(seams.join(""), { tone: "faint" }) }), lines: lineSvg(lines.join(""), { tone: "lo" }) };
}

// --- placing everything -------------------------------------------------------------------------------------------
let lift = 0; // mm the rocket is drawn above the pad
let bagShift = [0, 0];
let sway = 0;
function place() {
  const lx = D.EZ[0] * lift;
  const ly = D.EZ[1] * lift;
  for (const n of nodes) {
    const share = piece[n.ride]?.x ?? 0;
    let tx = (D.EX[0] * n.m[0] + D.EY[0] * n.m[1] + D.EZ[0] * n.m[2]) * share;
    let ty = (D.EX[1] * n.m[0] + D.EY[1] * n.m[1] + D.EZ[1] * n.m[2]) * share;
    if (n.flies) {
      tx += lx;
      ty += ly;
    }
    if (n.piece === "chute") {
      tx += bagShift[0];
      ty += bagShift[1];
    }
    const text = Math.abs(tx) < 0.005 && Math.abs(ty) < 0.005 ? "" : `translate(${tx.toFixed(2)} ${ty.toFixed(2)})`;
    if (text !== n.shown) {
      n.shown = text;
      if (text) n.el.setAttribute("transform", text);
      else n.el.removeAttribute("transform");
    }
  }
  const key = (i) => nodes[i].key + nodes[i].lift * (piece[nodes[i].ride]?.x ?? 0);
  const next = nodes.map((_, i) => i).sort((a, b) => key(a) - key(b));
  if (next.some((index, at) => index !== order[at])) {
    const fragment = document.createDocumentFragment();
    for (const index of next) fragment.appendChild(nodes[index].el);
    rocket.appendChild(fragment);
    order = next;
  }
  const pivot = iso([0, 0, D.rocketTop + 900 + lift], P);
  const rot = Math.abs(sway) > 0.01 ? `rotate(${sway.toFixed(3)} ${pivot[0].toFixed(1)} ${pivot[1].toFixed(1)})` : "";
  if (rocket.getAttribute("transform") !== rot) {
    if (rot) rocket.setAttribute("transform", rot);
    else rocket.removeAttribute("transform");
    if (rot) anim.setAttribute("transform", rot);
    else anim.removeAttribute("transform");
  }
}

// --- the flight, frame by frame ---------------------------------------------------------------------------------------
let phaseWord = "";
function announce(word) {
  if (phaseWord === word) return;
  phaseWord = word;
  if (liveText) liveText.textContent = word;
}
function say(text) {
  if (readout.textContent !== text) readout.textContent = text;
}
function describe() {
  const text = fl.on ? "flying" : selected ? D.pieces[selected].name : apart ? "apart, five sections" : "On the pad";
  if (stage.getAttribute("aria-valuetext") !== text) stage.setAttribute("aria-valuetext", text);
}

function launch(fromTour = false) {
  if (fl.on) return;
  select(null);
  setApart(false);
  fl.on = true;
  fl.armed = true;
  fl.tour = fromTour;
  fl.tau = 0;
  fl.ended = false;
  fl.peak = 0;
  fl.stopping = 0;
  fl.still = -1;
  launchBtn.dataset.state = "armed";
  launchLabel.textContent = "Stop";
  root.setAttribute("data-armed", "");
  describe();
  run();
}
// a stop in mid-flight fades the rocket out before it is put back on the pad
function stopFlight() {
  if (!fl.on || fl.stopping) return;
  if (still.matches) return endFlight();
  fl.stopping = clock + 0.4;
  rocket.style.opacity = anim.style.opacity = "0";
  paintPlume(null);
  run();
}
function endFlight() {
  fl.on = false;
  fl.stopping = 0;
  anchor = [0, 0];
  fl.armed = false;
  lift = 0;
  sway = 0;
  burnGrains(0);
  setArm(0);
  setSprings(D.springs[0].closed);
  doorLive.innerHTML = "";
  canopyG.innerHTML = "";
  for (const n of doorNodes) n.el.removeAttribute("data-gone");
  for (const n of bagNodes) n.el.removeAttribute("data-gone");
  for (const n of igniterNodes) n.el.removeAttribute("data-blown");
  for (const n of clipNodes) n.el.removeAttribute("data-fade");
  bagShift = [0, 0];
  backSvg.style.opacity = "";
  rocket.style.opacity = anim.style.opacity = "";
  delete launchBtn.dataset.state;
  launchLabel.textContent = "Launch";
  root.removeAttribute("data-armed");
  camTarget = D.cams.rest;
  if (fl.tour) tourClock = 0;
  announce("on the pad");
  describe();
  paintPlume(null);
}

function stepFlight(dt, calm) {
  if (!fl.on) return false;
  if (fl.armed) {
    if (IDS.every((id) => piece[id].x < 0.002 && !piece[id].pending)) {
      fl.armed = false;
      launchBtn.dataset.state = "on";
    } else {
      say("closing up · arming");
      return true;
    }
  }
  if (fl.stopping) {
    if (clock >= fl.stopping) endFlight();
    return true;
  }
  if (calm) {
    if (fl.still < 0 || clock - fl.stillAt > 2.6) {
      fl.still += 1;
      fl.stillAt = clock;
    }
    fl.tau = STILLS[Math.min(fl.still, STILLS.length - 1)];
  } else fl.tau += dt;
  if (fl.tau >= REPLAY_END) {
    endFlight();
    return true;
  }
  const { t, label } = flightTime(fl.tau);
  const row = sampleAt(t);
  const [, h, v, thrust, baro, web] = row;
  // the rocket climbs; past LIFT_CAP the ground has left the picture and it stays put
  lift = t < EV.apogee ? Math.min(h * 1000, LIFT_CAP) : LIFT_CAP;
  moveAnchor([D.EZ[0] * lift, D.EZ[1] * lift]);
  burnGrains(clamp(web, 0, D.grain.web));
  // the igniter is blown out of the nozzle at ignition; the clips drop away as the rocket leaves
  for (const n of igniterNodes) n.el.toggleAttribute("data-blown", t > EV.firstThrust - 0.04);
  for (const n of clipNodes) n.el.toggleAttribute("data-fade", t > EV.liftoff + 0.08);
  // deployment
  const since = EV.detect !== undefined ? t - EV.detect : -1;
  const arm = since > 0 ? -D.arm.unlock * ss(0, D.deploy.servo, since) : 0;
  setArm(arm);
  const pose = doorPose(since - D.deploy.servo);
  const doorMoving = since > D.deploy.servo;
  for (const n of doorNodes) n.el.toggleAttribute("data-gone", doorMoving);
  if (doorMoving && since - D.deploy.servo < 2.2) doorLive.innerHTML = doorSvg(pose.deg, pose.shift, lift);
  else doorLive.innerHTML = "";
  setSprings(doorMoving ? springLength(pose, lift) : D.springs[0].closed);
  // the bag slides off the ramp once the door is gone, then streams out and fills
  const gone = EV.doorGone !== undefined ? t - EV.doorGone : -1;
  const bagOut = ss(0, D.deploy.bagOut, gone);
  const stretch = EV.lineStretch !== undefined ? t - EV.lineStretch : -1;
  const inflate = clamp((t - EV.lineStretch) / (EV.inflated - EV.lineStretch), 0, 1.2);
  const bo = D.bag.out;
  bagShift = [(D.EX[0] * bo[0] + D.EY[0] * bo[1] + D.EZ[0] * bo[2]) * bagOut, (D.EX[1] * bo[0] + D.EY[1] * bo[1] + D.EZ[1] * bo[2]) * bagOut];
  for (const n of bagNodes) {
    n.el.toggleAttribute("data-gone", gone > D.deploy.bagOut + 0.15);
  }
  if (gone > D.deploy.bagOut) {
    const q0 = G.add3(D.cordExit, G.add3(G.mul3(NX, 80), [0, 0, 60]));
    const q1 = G.add3(D.cordExit, G.add3(G.mul3(NX, 240), [0, 0, 420]));
    const qf = G.add3([0, 0, D.rocketTop], G.add3(G.mul3(NX, 60), [0, 0, 380]));
    const pay = ss(0, Math.max(0.05, EV.lineStretch - EV.doorGone - D.deploy.bagOut), gone - D.deploy.bagOut);
    const f2 = ss(0, 1, inflate);
    const q = stretch < 0 ? G.add3(q0, G.mul3(G.sub3(q1, q0), pay)) : G.add3(q1, G.mul3(G.sub3(qf, q1), f2));
    const tilt = stretch < 0 ? 60 - 30 * pay : 30 * (1 - f2);
    const axis = G.add3(G.mul3([0, 0, 1], Math.cos(tilt * DEGR)), G.mul3(NX, Math.sin(tilt * DEGR)));
    const breathe = inflate >= 1 ? 1 + 0.012 * Math.sin(clock * 3.6) : inflate * (1 + 0.08 * Math.sin(Math.PI * inflate));
    const c = canopySvg(q, axis, stretch < 0 ? 0.08 + 0.92 * pay : 1, stretch < 0 ? 0 : breathe, lift);
    const exit = iso(G.add3(D.cordExit, [0, 0, lift]), P);
    const conf = iso(G.add3(q, [0, 0, lift]), P);
    canopyG.innerHTML = lineSvg(`M${exit[0].toFixed(2)} ${exit[1].toFixed(2)}L${conf[0].toFixed(2)} ${conf[1].toFixed(2)}`, { tone: "mid" }) + c.lines + c.dome;
  } else canopyG.innerHTML = "";
  // descent: a slow pendulum under the canopy
  sway = t > EV.inflated ? 2.2 * ss(EV.inflated, EV.inflated + 3, t) * Math.sin((t - EV.inflated) * 1.8) : 0;
  // ground station needle: what the ESP32 reports, held at the highest reading
  if (needle) {
    fl.peak = Math.max(fl.peak, baro);
    const a = (clamp(fl.peak, 0, 1000) / 1000) * 360 * DEGR;
    const tip = [D.dial.x + Math.sin(a) * (D.dial.r - 5), D.dial.y - Math.cos(a) * (D.dial.r - 5)];
    const tail = [D.dial.x - Math.sin(a) * 3, D.dial.y + Math.cos(a) * 3];
    needle.setAttribute("d", lineOnTop(tail, tip, D.dial.z, P));
  }
  // the ground falls away as it climbs; after touchdown the rocket fades and returns to the pad
  backSvg.style.opacity = (1 - ss(1300, 2500, lift)).toFixed(3);
  const landed = fl.tau - SEGS[SEGS.length - 1][0];
  rocket.style.opacity = anim.style.opacity = landed > 0 ? (1 - ss(0.4, 1.6, landed)).toFixed(3) : "";
  // camera
  const mid = iso([0, 0, 480 + lift], P);
  const nose = iso([0, 0, D.rocketTop - 120 + lift], P);
  const tail = iso([0, 0, 40 + lift], P);
  if (t < EV.liftoff) camTarget = windowAt(tail[0], tail[1] + 40, 520);
  else if (t < EV.apogee - 1.2) camTarget = windowAt(mid[0], mid[1], 1250);
  else if (t < EV.inflated - 0.2) camTarget = windowAt(nose[0], nose[1], 420);
  else {
    const top = iso([0, 0, D.rocketTop + 1250 + lift], P);
    camTarget = windowAt((top[0] + tail[0]) / 2, (top[1] + tail[1]) / 2, 2500);
  }
  // shader
  paintPlume({ thrust, t, lift, v, h, pc: row[6], ground: 1 - ss(1300, 2500, lift) });
  // words
  const tPlus = t < 0 ? `T−${(-t).toFixed(1)}` : `T+${t.toFixed(1)}`;
  let word;
  if (t < 0) word = "countdown";
  else if (t < EV.firstThrust) word = "igniter firing";
  else if (thrust > 1 && h < 1.25) word = "ignition · on the rail";
  else if (thrust > 1) word = "boost";
  else if (EV.detect === undefined || t < EV.detect) word = t < EV.apogee ? "coast" : "apogee";
  else if (t < (EV.doorGone ?? 1e9)) word = "servo open · door kicked";
  else if (t < EV.inflated) word = "chute out";
  else if (t < EV.touchdown) word = "under canopy";
  else word = "touchdown";
  announce(word);
  const numbers = t < 0 ? "" : word === "touchdown" ? ` · ${EV.touchdownV.toFixed(1)} m/s` : ` · ${fmt(h)} m · ${fmt(Math.abs(v))} m/s${thrust > 1 ? ` · ${fmt(thrust)} N` : ""}`;
  say(`${tPlus} s · ${word}${numbers} · ${label}`);
  return true;
}

// --- plume shader: the KNSB flame, its smoke trail and the cloud on the pad ----------------------------------------
// One fragment on two canvases: .hx-plume under the rocket and .hx-veil over it. A cylinder proxy of the airframe
// sends every smoke sample that lies between the rocket and the viewer to the veil, so nothing is drawn twice.
const PL = D.plume;
const LIGHT = (root.closest("[data-theme]")?.getAttribute("data-theme") ?? "dark") === "light" ? 1 : 0;
const f1 = (v) => Number(v).toFixed(2);
const PLUME_GLSL = `
uniform vec3 uNoz;
uniform vec4 uFlame;
uniform vec4 uTrail;
uniform vec4 uCloud;
uniform vec3 uBody;
uniform float uGain;
uniform float uVeil;
uniform float uLight;
const float RE=${f1(PL.exitR)};
const float ZDEF=${f1(PL.zDef)};
const float ZPLATE=${f1(PL.zPlate)};
const float DEFH=${f1(PL.def)};
const float PLATEH=${f1(PL.plate)};
const vec3 RAIL=vec3(${PL.rail.slice(0, 3).map(f1).join(",")});
const vec2 RAILZ=vec2(${PL.rail.slice(3).map(f1).join(",")});
const vec3 CLAMP=vec3(${PL.clamp.slice(0, 3).map(f1).join(",")});
const vec2 CLAMPZ=vec2(${PL.clamp.slice(3).map(f1).join(",")});
const vec2 WIND=vec2(.866,-.5)*260.;
float boxNear(vec3 o,vec3 V,vec3 lo,vec3 hi){
  vec3 a=(lo-o)/V;vec3 b=(hi-o)/V;
  vec3 mn=min(a,b);vec3 mx=max(a,b);
  float tIn=max(mn.x,max(mn.y,mn.z));float tOut=min(mx.x,min(mx.y,mx.z));
  return tOut>tIn?tOut:-1e9;
}
float structNear(vec3 o,vec3 V){
  float r=boxNear(o,V,vec3(RAIL.xy-RAIL.z,RAILZ.x),vec3(RAIL.xy+RAIL.z,RAILZ.y));
  float c=boxNear(o,V,vec3(CLAMP.xy-CLAMP.z,CLAMPZ.x),vec3(CLAMP.xy+CLAMP.z,CLAMPZ.y));
  return max(r,c);
}
float bodyNear(vec3 o,vec3 V){
  vec2 h=V.xy;float hl2=dot(h,h);
  float tc=-dot(o.xy,h)/hl2;
  vec2 q=o.xy+tc*h;float d2=dot(q,q);
  float R=uBody.z;
  if(d2>R*R)return -1e9;
  float tn=tc+sqrt((R*R-d2)/hl2);
  float z=o.z+tn*V.z;
  return (z>uBody.x&&z<uBody.y)?tn:-1e9;
}
float sdRect(vec2 p,float hw,float r){vec2 q=abs(p)-hw+r;return length(max(q,0.))+min(max(q.x,q.y),0.)-r;}
float flameLen(){return 16.*uFlame.y+215.*uFlame.x;}
float flameR(float s,float L,float sP){
  float r=RE*(.9+.1*smoothstep(0.,12.,s))+.09*max(s,0.)*(1.-.3*smoothstep(0.,L+1.,s));
  return r+1.5*max(s-(sP-26.),0.);
}
// the trail: a constant-acceleration climb back to the launch point gives each depth below the nozzle
// its age and the speed the rocket had when it laid that smoke
vec2 trailAt(float d){
  float v=uTrail.x;float a=max(uTrail.y,1.);
  float disc=v*v-2.*a*d;
  if(d<0.)return vec2(-1.,0.);
  if(disc<=0.)return vec2(v/a,0.);
  float ve=sqrt(disc);
  return vec2((v-ve)/a,ve);
}
float trailR(float d,float age){float jet=RE+.05*min(max(d,0.),600.);return sqrt(jet*jet+5000.*age);}
struct Cloud{vec3 c;float rh;float hc;float k;};
Cloud cloudOf(){
  Cloud C;
  float age=uCloud.y;
  C.rh=60.+220.*(1.-exp(-age/.9));
  C.hc=38.+80.*(1.-exp(-age/1.));
  C.c=vec3(WIND*age*.6,ZPLATE+.5*C.hc+25.*(1.-exp(-age/2.)));
  C.k=uCloud.x*6000./(C.rh*C.rh*C.hc)*exp(-age/7.)*uCloud.z;
  return C;
}
float after(float t,float tS){return tS<-1e8?1.:smoothstep(tS-1.5,tS+1.5,t);}
float vis(float t,float tS){return 1.-uCloud.z*(1.-after(t,tS));}
float layerOf(float t,float tB){float f=tB<-1e8?0.:smoothstep(tB-1.,tB+1.,t);return mix(1.-f,f,uVeil);}
// lit grey for smoke: crown, edge and self-shadowed underside, warmed near the flame
vec3 smokeTone(vec3 n,float warm){
  float lit=.5+.5*dot(normalize(n),lightDir());
  vec3 light=mix(vec3(.62,.63,.66),vec3(.93,.93,.925),smoothstep(.1,.95,lit));
  light=mix(light,vec3(1.,.82,.6),warm*.7);
  vec3 dark=vec3(.6,.62,.66)*(.5+.6*lit)+vec3(1.,.5,.2)*warm*.55;
  return mix(dark,light,uLight);
}
struct Acc{vec3 c;float a;vec3 e;};
void smokeStep(inout Acc S,float sigma,vec3 tone,float dt){
  float al=1.-exp(-sigma*dt);
  S.c=S.c*(1.-al)+tone*al;
  S.a=S.a*(1.-al)+al;
  S.e*=1.-al;
}
void cloudMarch(inout Acc S,vec3 g0,vec3 V,float ta,float tb,Cloud C,float tS,float tB,float L,float sP,float dith){
  float dt=max(tb-ta,0.)/10.;
  if(dt<=0.)return;
  float T=uTime;
  float splash=smoothstep(0.,40.,L-sP)*uCloud.z;
  float Rs=25.+1.3*max(L-sP,0.);
  for(int i=0;i<10;i++){
    float t=ta+(float(i)+dith)*dt;
    vec3 p=g0+t*V;
    float w=vis(t,tS)*layerOf(t,tB);
    float floorK=smoothstep(ZPLATE+1.,ZPLATE+8.,p.z);
    vec3 q=p-C.c;
    float rh=length(q.xy);
    float qq=pow((rh-.4*C.rh)/(.75*C.rh),2.)+pow(q.z/C.hc,2.);
    float n=fbm3(p*.018+vec3(0.,0.,-uCloud.y*.3));
    float puff=smoothstep(.3,.75,n+.3-.22*qq);
    float sigma=C.k*exp(-qq*1.2)*(.08+1.8*puff)*floorK*(1.-smoothstep(1.8,2.3,qq));
    float warm=uFlame.x*exp(-length(p-vec3(0.,0.,max(uNoz.z-L*.6,ZDEF+8.)))/70.);
    smokeStep(S,sigma*w,smokeTone(vec3(q.xy/C.rh,q.z/C.hc+.4),warm),dt);
    if(splash>.0004){
      float sheet=exp(-pow(length(p.xy)/Rs,2.)*1.5)*exp(-max(p.z-ZDEF,0.)/7.)*smoothstep(ZDEF-1.,ZDEF+1.5,p.z);
      float lick=.6+.8*fbm2(vec2(length(p.xy)*.05-T*6.,p.x*.02-p.y*.017));
      S.e+=vec3(1.,.5,.2)*sheet*lick*splash*dt*.03*w*uFlame.x;
    }
  }
}
void main(){
  vec2 vb=viewOf(gl_FragCoord.xy);
  vec3 V=towardViewer();
  vec3 g0=rayOf(vb);
  float sE=uCam.z;
  float cE=uCam.w;
  float T=uTime;
  float dith=hash12(gl_FragCoord.xy+fract(T*.37)*41.);
  float L=flameLen();
  float sP=uNoz.z-ZDEF;
  float tS=structNear(g0,V);
  float tB=bodyNear(g0,V);
  Acc S;S.c=vec3(0.);S.a=0.;S.e=vec3(0.);
  vec4 pool=vec4(0.);

  // the flame's light on the deflector and the pad plate
  float px=pixelOf()/sE;
  if(uFlame.x+uFlame.y>.0004&&uVeil<.5&&uCloud.z>.0004){
    vec3 hd=onFloor(vb,ZDEF);
    vec3 hp=onFloor(vb,ZPLATE);
    float onDef=1.-smoothstep(-.7*px,.7*px,sdRect(hd.xy,DEFH,4.));
    float onPlate=(1.-smoothstep(-.7*px,.7*px,sdRect(hp.xy,PLATEH,10.)))*(1.-onDef);
    vec3 src=vec3(0.,0.,max(uNoz.z-L*.55,ZDEF+10.));
    float power=(uFlame.x*1.+uFlame.y*.25)*uCloud.z;
    float ld=exp(-length(hd-src)/60.)*onDef*after((ZDEF-g0.z)/sE,tS);
    float lp=exp(-length(hp-src)/75.)*onPlate*after((ZPLATE-g0.z)/sE,tS);
    float I=(ld+lp*.8)*power;
    pool=vec4(vec3(1.,.55,.22)*I*.75,I);
  }

  // the column: flame below the nozzle, then the smoke it leaves behind
  float s0=uNoz.z-g0.z;
  float d0=max(s0,0.);
  vec2 ta0=trailAt(d0);
  vec2 drift0=ta0.x>0.?WIND*ta0.x:vec2(0.);
  float rT0=ta0.x>0.?trailR(d0,ta0.x):0.;
  float rF0=s0>-30.&&s0<L+30.?flameR(clamp(s0,0.,L),L,sP)*1.5:0.;
  float B=max(2.3*rT0*step(.0004,uTrail.w),rF0*1.6)+6.;
  vec2 h=V.xy;
  float hl2=dot(h,h);
  float tc=dot(drift0-g0.xy,h)/hl2;
  vec2 qc=g0.xy+tc*h-drift0;
  float uc2=dot(qc,qc);
  float tmid=tc;
  Cloud C=cloudOf();
  vec3 cq=g0-C.c;
  float cB=max(2.3*C.rh,1.7*(25.+1.3*max(L-sP,0.)));
  float ctc=dot(-cq.xy,h)/hl2;
  vec2 cqc=cq.xy+ctc*h;
  float cu2=dot(cqc,cqc);
  float cHalf=cu2<cB*cB?sqrt((cB*cB-cu2)/hl2):0.;
  float cLo=max(ctc-cHalf,(ZPLATE-g0.z)/sE);
  float cHi=min(ctc+cHalf,(C.c.z+2.6*C.hc-g0.z)/sE);
  bool cloudOn=(C.k>1e-7||L>sP-30.)&&cHi>cLo&&uCloud.z>.0004;
  if(cloudOn)cloudMarch(S,g0,V,cLo,min(cHi,tmid),C,tS,tB,L,sP,dith);

  if(uc2<B*B){
    float hw=sqrt((B*B-uc2)/hl2);
    float ta=tc-hw;
    float tb=tc+hw;
    float dt=(tb-ta)/22.;
    float tongue=fbm2(vec2(T*3.1,7.));
    float Lt=L*(1.+(tongue-.5)*.16);
    float flick=.92+.08*sin(T*83.)+.06*sin(T*131.+1.7);
    for(int i=0;i<22;i++){
      float t=ta+(float(i)+dith)*dt;
      vec3 p=g0+t*V;
      float w=vis(t,tS)*layerOf(t,tB);
      float s=uNoz.z-p.z;
      // flame
      if(L>.5&&s>-2.&&s<Lt+8.){
        float r=length(p.xy);
        float e=fbm2(vec2(r*.09+s*.02,s*.045-T*24.));
        float rf=flameR(s,Lt,sP)*(1.+(e-.5)*.34*smoothstep(8.,Lt,s));
        float along=smoothstep(-1.,3.,s)*(1.-smoothstep(.5*Lt,Lt,s))*smoothstep(ZDEF-1.,ZDEF+2.,p.z);
        float fill=smoothstep(1.05,.68,r/rf);
        vec3 hue=mix(vec3(1.,.82,.5),vec3(1.,.5,.2),smoothstep(0.,.35*Lt,s));
        hue=mix(hue,vec3(1.,.36,.3),smoothstep(.45*Lt,Lt,s));
        float wB=dt*cE/(2.*rf);
        vec3 em=hue*fill*wB*(.55+.6*e)*along;
        float rc=max(rf*.38,2.);
        em+=vec3(1.,.9,.7)*exp(-(r*r)/(rc*rc))*exp(-s/(.28*Lt+5.))*(dt*cE/(rc*1.772))*1.6*smoothstep(-1.,2.,s);
        // faint shock diamonds: the nozzle runs a little over-expanded at sea level
        for(int k=0;k<3;k++){
          float sk=45.+50.*float(k);
          float amp=exp(-float(k)*.55)*smoothstep(.3,.8,uFlame.z)*(1.-smoothstep(Lt*.55,Lt*.8,sk));
          float rd=RE*(.55-.08*float(k));
          float q=length(vec2(r/rd,(s-sk)/(rd*1.6)));
          em+=vec3(1.,.93,.78)*exp(-q*q*2.)*(dt*cE/(rd*1.25))*.55*amp;
        }
        S.e+=em*flick*(uFlame.x+.6*uFlame.y)/(uFlame.x+uFlame.y+1e-4)*w;
      }
      // trail
      vec2 tr=trailAt(max(s,0.));
      if(uTrail.w>.0004&&tr.x>=0.&&s>0.){
        vec2 c=WIND*tr.x;
        vec2 rel=p.xy-c;
        float rT=trailR(s,tr.x);
        float n=fbm3(vec3(rel*.05,(uCloud.w-tr.x)*14.+tr.x*.8));
        float n2=noise3(vec3(rel*.09,(uCloud.w-tr.x)*31.));
        float rr=length(rel)/(rT*(.86+.3*n2));
        float puff=smoothstep(.3,.78,n+.32-.3*rr*rr);
        float lf=1./(1.+tr.y/6000.);
        float tauC=14.*uTrail.w*lf*(30./rT)*exp(-tr.x/10.);
        float streak=.75+.5*noise2(vec2(rel.x/rT*2.6+rel.y/rT*1.3,s*.0025+uCloud.w*.4));
        float sigma=tauC*cE/(rT*1.772)*exp(-rr*rr)*(1.-smoothstep(1.7,2.2,rr))*(.3+1.4*puff)*streak;
        sigma*=smoothstep(.7*L,1.3*L+4.,s)*smoothstep(ZDEF+1.,ZDEF+14.,p.z)*mix(1.,uCloud.z,smoothstep(0.,-40.,uTrail.z-s));
        float warm=uFlame.x*exp(-max(s-L*.8,0.)/60.);
        smokeStep(S,sigma*w,smokeTone(vec3(rel/rT,.35),warm),dt);
      }
    }
  }
  if(cloudOn)cloudMarch(S,g0,V,max(cLo,tmid),cHi,C,tS,tB,L,sP,dith);

  // ignition flash at the nozzle
  if(uFlame.w>.0004&&uVeil<.5){
    vec3 N=uNoz-vec3(0.,0.,6.);
    float tf=dot(N-g0,V);
    float dist=length(g0+tf*V-N);
    S.e+=vec3(1.,.72,.42)*(exp(-pow(dist/34.,2.))*mix(.5,.12,uLight)+exp(-dist/9.)*.9)*uFlame.w;
  }

  vec4 outc;
  if(uLight<.5){
    // normal blending: the smoke hides what is behind it, the flame covers by its own brightness
    vec3 fire=tonemap(S.e*1.5+pool.rgb,1.1);
    float fa=max(fire.r,max(fire.g,fire.b));
    vec4 smoke=vec4(S.c,S.a);
    outc=(vec4(fire,fa)+smoke*(1.-fa))*uGain;
  }else{
    // paper: smoke is grey ink, the flame is solved for the colour the paper should show
    float e=1.-exp(-1.5*max(S.e.r,max(S.e.g,S.e.b)));
    vec3 seen=mix(vec3(1.),vec3(1.,.83,.6),smoothstep(0.,.22,e));
    seen=mix(seen,vec3(.97,.5,.14),smoothstep(.16,.55,e));
    seen=mix(seen,vec3(1.,.9,.62),smoothstep(.62,.95,e));
    vec3 absorbed=1.-seen;
    float fa=max(max(absorbed.r,max(absorbed.g,absorbed.b)),.92*smoothstep(.6,.92,e));
    vec4 flame=vec4(vec3(fa)-absorbed,fa);
    float pa=min(pool.a*.8,.55);
    vec4 tint=vec4(vec3(1.,.66,.38)*pa,pa);
    vec4 smoke=vec4(S.c,S.a);
    vec4 under=smoke+tint*(1.-smoke.a);
    outc=(flame+under*(1.-flame.a))*uGain;
    outc.rgb=min(outc.rgb,vec3(outc.a));
  }
  float m=max(outc.a,max(outc.r,max(outc.g,outc.b)));
  float n=(hash12(gl_FragCoord.xy+fract(T*.61)*91.)+hash12(gl_FragCoord.yx*1.37+fract(T*.37)*57.)-1.)/255.;
  outc=max(outc+n*smoothstep(0.,1.5/255.,m),0.);
  outc.rgb=min(outc.rgb,vec3(outc.a));
  gl_FragColor=outc;
}`;
const PLUME_UNIFORMS = ["uNoz", "uFlame", "uTrail", "uCloud", "uBody", "uGain"];
const makeLayer = (canvas, veil) => glLayer({ canvas, fragment: PLUME_GLSL, view: [D.W, D.H], camera: D.camera, uniforms: PLUME_UNIFORMS, fixed: { uVeil: veil, uLight: LIGHT }, onError: (message) => console.warn(message) });
let plumeLayer = null;
let veilLayer = null;
try {
  plumeLayer = makeLayer(plumeCanvas, 0);
  veilLayer = plumeLayer ? makeLayer(veilCanvas, 1) : null;
} catch (error) {
  plumeLayer = veilLayer = null;
}
if (plumeLayer) stage.setAttribute("data-gl", "");

// the cloud on the pad: exhaust that reached the plate while the nozzle was low, with its mass-weighted birth time
const CLOUD = (() => {
  const out = [];
  let mass = 0;
  let moment = 0;
  let prev = null;
  for (const row of ROWS) {
    if (row[0] > 4) break;
    if (prev) {
      const w = (row[3] / F.peakF) * Math.exp(-row[1] / 0.45) * (row[0] - prev[0]);
      mass += w;
      moment += w * row[0];
    }
    out.push([row[0], mass, mass > 0 ? moment / mass : 0]);
    prev = row;
  }
  const total = out[out.length - 1][1] || 1;
  return out.map(([t, m, born]) => [t, m / total, born]);
})();
function cloudAt(t) {
  if (t <= CLOUD[0][0]) return CLOUD[0];
  for (let i = 1; i < CLOUD.length; i++) if (CLOUD[i][0] >= t) {
    const a = CLOUD[i - 1];
    const b = CLOUD[i];
    const f = (t - a[0]) / (b[0] - a[0] || 1);
    return [t, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
  }
  return CLOUD[CLOUD.length - 1];
}

const plume = { thrust: { x: 0, v: 0 }, gain: { x: 0, v: 0 }, on: false, input: null, values: null };
function paintPlume(input) {
  if (input) {
    plume.on = true;
    plume.input = input;
  } else plume.on = false;
}
// called once a frame after the camera moves; returns true while the plume is still changing
// without WebGL the flame is two flat SVG tongues under the nozzle, sized from the same thrust
const flameOuter = front.querySelector(".hx-flame-outer");
const flameCore = front.querySelector(".hx-flame-core");
function flameFallback(dt, calm) {
  const on = plume.on && plume.input;
  const target = on ? plume.input.thrust / F.peakF : 0;
  const moving = settle(plume.thrust, target, dt, 0.05, calm);
  const thr = plume.thrust.x;
  if (thr < 0.01 || !on) {
    flameOuter.setAttribute("d", "");
    flameCore.setAttribute("d", "");
    return moving;
  }
  const z0 = D.rocketBottom + plume.input.lift;
  const tongue = (length, r0, grow) => {
    const left = [];
    const right = [];
    for (let i = 0; i <= 12; i++) {
      const s = (length * i) / 12;
      // a tongue: full width near the exit, closing to a point at its tip
      const r = (r0 + grow * s) * Math.sqrt(Math.max(0, 1 - (i / 12) ** 2));
      const a = iso([0, 0, z0 - s], P);
      const w = r * D.camera.k;
      left.push([a[0] - w, a[1]]);
      right.push([a[0] + w, a[1]]);
    }
    return "M" + [...left, ...right.reverse()].map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L") + "Z";
  };
  const L = 16 + 200 * thr;
  flameOuter.setAttribute("d", tongue(L, D.nozzleR, 0.09));
  flameCore.setAttribute("d", tongue(L * 0.4, D.nozzleR * 0.55, 0.03));
  return true;
}
function drawPlume(dt, calm) {
  if (!plumeLayer) return flameFallback(dt, calm);
  let moving = settle(plume.gain, plume.on ? 1 : 0, dt, plume.on ? 0.08 : 0.22, calm);
  const input = plume.input;
  if (!input) {
    plumeLayer.clear();
    veilLayer?.clear();
    return false;
  }
  if (plume.on) {
    const { t, thrust, lift, v, h, ground } = input;
    if (plume.gain.x < 0.01 && t <= 0) plume.thrust = { x: 0, v: 0 };
    if (settle(plume.thrust, thrust / F.peakF, dt, 0.05, calm)) moving = true;
    const ign = t > 0 ? ss(0, 0.04, t) * (1 - ss(EV.firstThrust - 0.02, EV.firstThrust + 0.1, t)) : 0;
    const flash = calm ? 0 : burst(t - EV.firstThrust, 0.03, 0.05);
    const vm = Math.max(0, v) * 1000;
    const hm = Math.max(0, h) * 1000;
    const climbing = t > EV.liftoff && t < EV.apogee && hm > 1;
    const [, mass, born] = cloudAt(t);
    const age = Math.max(0, t - born);
    plume.values = {
      uNoz: [0, 0, D.rocketBottom + lift],
      uFlame: [plume.thrust.x, ign, clamp((input.pc ?? 0) / PL.pcDesign, 0, 1.2), flash],
      uTrail: [vm, climbing ? (vm * vm) / (2 * hm) : 1, hm, climbing ? plume.thrust.x : 0],
      uCloud: [mass, age, ground, t],
      uBody: [D.rocketBottom + lift, D.rocketBottom + PL.length + lift, PL.bodyR],
    };
    plume.activity = Math.max(plume.thrust.x, ign, flash, mass * Math.exp(-age / 7) * ground);
  }
  const values = plume.values;
  if (!values || plume.gain.x * plume.activity < 1e-3) {
    plumeLayer.clear();
    veilLayer?.clear();
    if (!plume.on) plume.input = null;
    return moving;
  }
  const view = { uView: [cam.w, cam.h], uOrigin: [D.camera.origin[0] - cam.x, D.camera.origin[1] - cam.y], uGain: plume.gain.x };
  const time = calm ? 0.8 : clock;
  plumeLayer.draw({ ...values, ...view }, time);
  veilLayer?.draw({ ...values, ...view }, time);
  return moving || plume.on;
}

// --- tour, input, loop ---------------------------------------------------------------------------------------------------------
let touring = !still.matches;
let tourClock = -1.4;
let idleTimer = 0;
let visible = false;
let frame = 0;
let last = 0;
const TOUR = [
  [0, () => { select(null); setApart(false); }],
  [1.2, () => select("nose")],
  [3.8, () => select("bay")],
  [6.4, () => select("motor")],
  [9.0, () => { select(null); setApart(true); }],
  [12.4, () => setApart(false)],
  [14.6, () => launch(true)],
];
let tourStep = 0;
function stepTour(dt) {
  if (!touring || fl.on) return;
  tourClock += dt;
  while (tourStep < TOUR.length && tourClock >= TOUR[tourStep][0]) TOUR[tourStep++][1]();
}
function quietTour() {
  touring = false;
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    if (fl.on || inside) return quietTour();
    touring = !still.matches;
    tourClock = -0.4;
    tourStep = 0;
    run();
  }, 3600);
}
let inside = false;

function idleText() {
  if (selected) return D.pieces[selected].name;
  const moving = IDS.some((id) => Math.abs(piece[id].x - piece[id].target) > 0.002 || piece[id].pending);
  if (moving) return apart ? "taking apart" : "putting together";
  return apart ? "apart · five sections on their spigots" : `${(F.liftoff / 1000).toFixed(2)} kg · on the pad`;
}

function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  clock += dt;
  const calm = still.matches;
  stepTour(dt);
  let moving = false;
  for (const id of IDS) if (steerSpring(piece[id], dt, calm)) moving = true;
  const flying = stepFlight(dt, calm);
  if (!fl.on) {
    const win = selected ? (apart ? D.pieceWin[selected]?.apart : D.pieceWin[selected]?.rest) : apart ? D.cams.apart : D.cams.rest;
    camTarget = win ?? D.cams.rest;
    say(idleText());
  }
  if (steerCamera(dt, calm, fl.on ? 0.35 : 0.5)) moving = true;
  if (drawPlume(dt, calm)) moving = true;
  place();
  frame = visible && (moving || flying || touring) ? requestAnimationFrame(tick) : 0;
}
function run() {
  if (!frame && visible) {
    last = 0;
    frame = requestAnimationFrame(tick);
  }
}
new IntersectionObserver((entries) => {
  visible = entries[entries.length - 1].isIntersecting;
  if (visible) run();
}, { rootMargin: "120px 0px" }).observe(stage);

function pieceAt(event) {
  const hit = document.elementFromPoint(event.clientX, event.clientY);
  const item = hit && hit.closest ? hit.closest(".it") : null;
  return item ? item.dataset.piece : null;
}
stage.addEventListener("pointerenter", () => (inside = true));
stage.addEventListener("pointerleave", () => (inside = false));
stage.addEventListener("click", (event) => {
  quietTour();
  if (fl.on) return;
  const id = pieceAt(event);
  select(id && id !== "stand" && id !== selected ? id : null);
});
launchBtn.addEventListener("click", () => {
  quietTour();
  if (fl.on) stopFlight();
  else launch(false);
  run();
});
apartBtn.addEventListener("click", () => {
  quietTour();
  if (fl.on) return;
  setApart(!apart);
});
partButtons.forEach((button) => {
  button.addEventListener("click", () => {
    quietTour();
    if (fl.on) return;
    select(selected === button.dataset.part ? null : button.dataset.part);
  });
});
stage.addEventListener("keydown", (event) => {
  const index = selected ? D.order.indexOf(selected) : -1;
  let next = null;
  if (event.key === "ArrowRight" || event.key === "ArrowDown") next = Math.min(D.order.length - 1, index + 1);
  else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = Math.max(0, index - 1);
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = D.order.length - 1;
  else if (event.key === "Escape") {
    event.preventDefault();
    quietTour();
    if (fl.on) stopFlight();
    select(null);
    setApart(false);
    return;
  } else if (event.key === "l" || event.key === "L" || event.key === "Enter") {
    event.preventDefault();
    quietTour();
    if (fl.on) stopFlight();
    else launch(false);
    run();
    return;
  } else if (event.key === " ") {
    event.preventDefault();
    quietTour();
    if (!fl.on) setApart(!apart);
    return;
  }
  if (next === null || fl.on) return;
  event.preventDefault();
  quietTour();
  select(D.order[next]);
});
stage.addEventListener("focus", () => liveText && !liveText.textContent && (liveText.textContent = stage.getAttribute("aria-valuetext")));
if (still.matches) touring = false;
place();
say(idleText());
