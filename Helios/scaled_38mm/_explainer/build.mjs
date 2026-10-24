// Helios · how it flies. An anatomy figure of the whole 38 mm rocket on its
// launch rail: quarter cutaways through the fin can, motor and avionics bay, the
// side-door nose, a flight replay from the model in model.mjs, and an exploded
// view of the five sections on their spigots.
//
//   node build.mjs            writes helios.html (dark)
//   node build.mjs --light    writes helios-light.html
//   node build.mjs --audit    also runs the geometry audit
//
// World frame = rocket_assembled_boattail.stl: millimetres, z up the rocket axis,
// x toward Mbody's cord anchor (azimuth 0). The camera looks from azimuth 30°.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as M from "./model.mjs";
import { buildFig2 } from "./fig2.mjs";

const SKILL = "file:///C:/Users/Pedro/.claude/skills/anatomy/";
const k = await import(SKILL + "kit/iso-kit.mjs");
const G = await import(SKILL + "kit/lathe.mjs");
const { tubePieces, tubeSvg } = await import(SKILL + "kit/tube.mjs");
const A = await import(SKILL + "kit/audit.mjs");
const { glCamera } = await import(SKILL + "kit/gl.mjs");
const { kitScript, glScript } = await import(SKILL + "scripts/inline-kit.mjs");

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME = process.argv.includes("--light") ? "light" : "dark";
const N = JSON.parse(readFileSync(join(HERE, "nose.json"), "utf8"));
const DEG = Math.PI / 180;

// --- camera ------------------------------------------------------------------------------
const AZ = 30;
const EL = 20;
const W = 800;
const H = 1000;

// --- stations (world z) -------------------------------------------------------------------
const R = 32.76;            // airframe outer radius (Ø65.52)
const R_IN = 31.45;         // tube bore
const R_SPIGOT = 31.12;     // every male spigot
const R_SOCKET = 31.28;     // every female socket
const Z = {
  cap0: -26.21, capTop: 28.83,
  tail0: 0, tailSpigot: 236.0, tailTop: 262.07,
  lower0: 235.86, lowerSpigot: 471.72, lowerTop: 497.93,
  coupler0: 471.72, couplerTop: 524.14,
  mbody0: 497.93, mbodyNeck: 524.9, mbodyTop: 760.0,
  nose0: 760.0 - N.SHOULDER_LEN,
};
const NOSE_ROT = 120;       // nose azimuth + 120° = world azimuth (cord hole over the anchor)
const s2z = (s) => Z.mbodyTop - s;   // Mbody station (mm aft of its forward rim) to world z
const nz = (z) => Z.nose0 + z;       // nose frame z to world z
const FIN_AZ = [60, 180, 300];
const FIN = [[31.46, 0], [136.28, 91.72], [136.28, 117.92], [31.46, 209.64]]; // (r, z) planform
const FIN_T = 2.62;
const GUIDE_AZ = 240;
const RAIL = { r: 53.7, half: 12.7, z0: -150, z1: 1080 };  // 1010 rail: the guide neck passes its slot lips at r 41
const PAD = { z: -150, plate: { x: -150, y: -150, w: 300, d: 300, r: 10 }, ground: -330 };

// --- projection fitted to the exploded extents -----------------------------------------------
const EXPLODE_TOP = 1570;
const P = k.fitProjection(
  [
    ...k.boxCorners({ x: -260, y: -260, w: 520, d: 520, r: 0 }, PAD.ground, PAD.ground),
    [0, 0, EXPLODE_TOP],
    [-140, 0, 120], [140, 0, 120], [0, -140, 120], [0, 140, 120],
    [RAIL.r * Math.cos(GUIDE_AZ * DEG), RAIL.r * Math.sin(GUIDE_AZ * DEG), RAIL.z1],
  ],
  W,
  H,
  { pad: 24, azimuth: AZ, elevation: EL },
);
const V = G.viewOf(P);
const KS = G.scaleOf(P);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const polar = (deg, r, z) => [r * Math.cos(deg * DEG), r * Math.sin(deg * DEG), z];
const dir = (deg) => [Math.cos(deg * DEG), Math.sin(deg * DEG), 0];
const VERT = (x = 0, y = 0, z = 0) => G.frameOf([x, y, z], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
const AXIS = VERT();
const FADE = [0.04, 0.42];

// --- assemblies, explode vectors, stagger ----------------------------------------------------
const PIECES = {
  stand: { name: "Launch pad and rail", move: [0, 0, 0] },
  cap: { name: "Boattail motor cap", move: [0, 0, 0] },
  motor: { name: "38 mm KNSB motor", move: [0, 0, 35] },
  tail: { name: "Fin can", move: [0, 0, 200] },
  lower: { name: "Lower body", move: [0, 0, 250] },
  coupler: { name: "Coupler sleeve", move: [0, 0, 300] },
  mbody: { name: "Main body", move: [0, 0, 350] },
  bay: { name: "Avionics bay", move: [0, 0, 570] },
  nose: { name: "Side-door nose", move: [0, 0, 590] },
  door: { name: "Door", move: G.add3([0, 0, 590], polar(NOSE_ROT, 70, 0)) },
};
const STAGGER = ["door", "nose", "bay", "mbody", "coupler", "lower", "tail", "motor", "cap", "stand"];
const SPRING = { stagger: 0.04, stiffness: 64, damping: 14.2, substeps: 4 };
const REC = A.recorder(P, { order: STAGGER, spring: SPRING });
const { nameFor } = REC;
const record = REC.solid;

function put(piece, ref, svg, { bias = 0, shapes = [], name, ride, move, route, chunk, layer } = {}) {
  REC.put({ piece, ride: ride ?? piece, at: ref, bias, svg, move: move ?? PIECES[piece].move, shapes, name: name ?? nameFor(`${piece}.item`), route, chunk, layer });
}

// An upright tube or disc cut to an azimuth sector [a0, a1] (degrees), drawn as a
// concave kit prism. With rIn = 0 it is a solid sector of a disc.
function sectorRing(rIn, rOut, a0, a1) {
  const span = a1 - a0;
  const steps = Math.max(4, Math.ceil((span / 360) * G.stepsFor(rOut, 32, 160, KS)));
  const outer = Array.from({ length: steps + 1 }, (_, i) => polar(a0 + (span * i) / steps, rOut, 0).slice(0, 2));
  if (rIn <= 0) return [[0, 0], ...outer];
  const inner = Array.from({ length: steps + 1 }, (_, i) => polar(a1 - (span * i) / steps, rIn, 0).slice(0, 2));
  return [...outer, ...inner];
}
function sector(piece, name, z0, z1, rIn, rOut, a0, a1, { tone = "hi", bias = 0, inner = "", extra = "", seated, cut } = {}) {
  const ring = sectorRing(rIn, rOut, a0, a1);
  const id = nameFor(name);
  const mid = (a0 + a1) / 2;
  const ref = polar(mid, (rIn + rOut) / 2, (z0 + z1) / 2);
  put(piece, ref, S(k.extrude(ring, z0, z1 - z0, P, { convex: false }), { tone, inner }) + extra, {
    bias, name: id, shapes: [record(A.extruded(ring, z0, z1 - z0, { name: id, ...(seated ? { seated, cut } : {}) }))],
  });
  REC.items[REC.items.length - 1].sec = [z0, z1, rIn, rOut, a0, a1, tone];
  return id;
}

// A tube from z0 to z1, split for painter's order: the back half (behind the axis)
// and the front half, which may carry a window [a0, a1] over [w0, w1].
const BACK = [AZ + 90, AZ + 270];
const FRONT = [AZ - 90, AZ + 90];
function tube(piece, name, z0, z1, rIn, rOut, { window, tone = "hi", seams = [] } = {}) {
  const seamLine = (a0, a1, zLo, zHi) => seams.filter((z) => z > zLo + 0.1 && z < zHi - 0.1).map((z) => G.arcOf(AXIS, z, rOut, P, { from: a0 * DEG, to: a1 * DEG })).join("");
  const faint = (d) => (d ? Ln(d, { tone: "faint" }) : "");
  sector(piece, `${name}.back`, z0, z1, rIn, rOut, BACK[0], BACK[1], { tone });
  if (!window) {
    sector(piece, `${name}.front`, z0, z1, rIn, rOut, FRONT[0], FRONT[1], { tone, inner: faint(seamLine(FRONT[0], FRONT[1], z0, z1)) });
    return;
  }
  const { a0, a1, w0, w1 } = window;
  if (w0 > z0) sector(piece, `${name}.front`, z0, w0, rIn, rOut, FRONT[0], FRONT[1], { tone, inner: faint(seamLine(FRONT[0], FRONT[1], z0, w0)) });
  if (w1 < z1) sector(piece, `${name}.front`, w1, z1, rIn, rOut, FRONT[0], FRONT[1], { tone, inner: faint(seamLine(FRONT[0], FRONT[1], w1, z1)) });
  const lo = Math.max(z0, w0);
  const hi = Math.min(z1, w1);
  sector(piece, `${name}.flank`, lo, hi, rIn, rOut, FRONT[0], a0, { tone, inner: faint(seamLine(FRONT[0], a0, lo, hi)) });
  sector(piece, `${name}.flank`, lo, hi, rIn, rOut, a1, FRONT[1], { tone, inner: faint(seamLine(a1, FRONT[1], lo, hi)) });
}

// --- the launch pad ------------------------------------------------------------------------------
const back = [];
{
  const plate = PAD.plate;
  back.push(`<path class="iso-halo" d="${k.haloOf(k.insetPlan(plate, -40), PAD.ground, 4, P)}"/>`);
  // ground board and three legs
  const BOARD = { x: -250, y: -250, w: 500, d: 500, r: 14 };
  back.push(S(k.slabOf(BOARD, PAD.ground, 12, P, 8, 1.4), { tone: "lo" }));
  record(A.slab(BOARD, PAD.ground, 12, { name: "stand.board", owner: "stand.frame" }));
  back.push(Ln(k.planOutline(k.insetPlan(BOARD, 8), PAD.ground + 12, P), { tone: "faint" }));
  const boardTop = PAD.ground + 12;
  const strip = { x: BOARD.x + 30, y: BOARD.y + BOARD.d - 22, w: 300, d: 10, r: 1.5 };
  back.push(S(k.slabOf(strip, boardTop, 1, P, 3), { tone: "lo", crease: "none" }));
  const ticks = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 10, 5, strip.y + 1, boardTop + 1, [3, 6], P);
  back.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
  back.push(Dots(k.corners(BOARD, 18).map(([x, y]) => at([x, y, boardTop])), { size: 0.55 }));
  back.push(Ln(k.corners(BOARD, 18).map(([x, y]) => k.ring(x, y, 3.2, boardTop, P, 16)).join(""), { tone: "lo" }));
}
const PAD_TOP = PAD.z + 8;
const LEGS = [70, 190, 310].map((deg) => polar(deg, 150, 0));
const depthSort = (list, f) => [...list].sort((a, b) => k.depthOf(f(a), P) - k.depthOf(f(b), P));
for (const leg of depthSort(LEGS, (l) => [l[0], l[1], 0])) {
  const [x, y] = leg;
  const top = PAD.z;
  const foot = PAD.ground + 12;
  back.push(S(k.cylinder(x, y, 9, foot, 2, P, 28), { tone: "lo" }));
  back.push(S(k.cylinder(x, y, 6, foot + 2, top - foot - 2, P, 28), { tone: "mid", crease: "none" }));
  record(A.cylinder(x, y, 6, foot, top - foot, { name: "stand.leg", owner: "stand.frame" }));
  back.push(Ln(k.sideArc(x, y, 6, foot + 30, P, 16) + k.sideArc(x, y, 6, top - 30, P, 16), { tone: "faint" }));
}
{
  const plate = PAD.plate;
  back.push(S(k.slabOf(plate, PAD.z, 8, P, 8, 1.2), { tone: "mid" }));
  record(A.slab(plate, PAD.z, 8, { name: "stand.plate", owner: "stand.frame" }));
  back.push(Ln(k.planOutline(k.insetPlan(plate, 6), PAD_TOP, P), { tone: "faint" }));
  back.push(Dots(LEGS.map(([x, y]) => at([x, y, PAD_TOP])), { size: 0.7, tone: "mid" }));
  back.push(Ln(LEGS.map(([x, y]) => k.ring(x, y, 4, PAD_TOP, P, 16)).join(""), { tone: "lo" }));
  // blast deflector: a steel plate bolted to the pad under the nozzle
  const DEF = { x: -60, y: -60, w: 120, d: 120, r: 4 };
  back.push(S(k.slabOf(DEF, PAD_TOP, 4, P, 4, 0.6), { tone: "lo" }));
  record(A.slab(DEF, PAD_TOP, 4, { name: "stand.deflector", owner: "stand.frame" }));
  back.push(Dots(k.corners(DEF, 8).map(([x, y]) => at([x, y, PAD_TOP + 4])), { size: 0.5 }));
}
// the 1010 rail with its base clamp
{
  const [rx, ry] = polar(GUIDE_AZ, RAIL.r, 0);
  const half = RAIL.half;
  const clamp = { x: rx - 22, y: ry - 22, w: 44, d: 44, r: 3 };
  back.push(S(k.slabOf(clamp, PAD_TOP, 26, P, 3, 0.8), { tone: "mid" }));
  record(A.slab(clamp, PAD_TOP, 26, { name: "stand.rail-clamp", owner: "stand.frame" }));
  back.push(Dots(k.corners(clamp, 6).map(([x, y]) => at([x, y, PAD_TOP + 26])), { size: 0.5 }));
}

// the rail stands behind the rocket and under the plume, so it lives in the back layer;
// its T-slot faces the rocket and the guides ride in it
{
  const [rx, ry] = polar(GUIDE_AZ, RAIL.r, 0);
  const half = RAIL.half;
  const plan = { x: rx - half, y: ry - half, w: 2 * half, d: 2 * half, r: 1.2 };
  const z0 = PAD_TOP + 26;
  const toward = dir(GUIDE_AZ + 180);
  const side = dir(GUIDE_AZ + 90);
  const face = (o) => [rx + toward[0] * half + side[0] * o, ry + toward[1] * half + side[1] * o];
  const slot = [-3.1, 3.1].map((o) => { const [x, y] = face(o); return k.segment([x, y, z0], [x, y, RAIL.z1], P); }).join("");
  back.push(S(k.slabOf(plan, z0, RAIL.z1 - z0, P, 3, 0.5), { tone: "mid", inner: Ln(slot, { tone: "lo" }) }));
  record(A.slab(plan, z0, RAIL.z1 - z0, { name: "stand.rail", owner: "stand.frame" }));
}

// --- the airframe -------------------------------------------------------------------------------------
// Fin can: outer tube, three fins through the wall, the forward spigot.
const TAIL_WINDOW = { a0: -40, a1: 45, w0: 18, w1: 150 };
tube("tail", "tail.tube", Z.tail0, 220, R_IN, R, { window: TAIL_WINDOW });
tube("tail", "tail.shoulder", 220, Z.tailSpigot, 29.47, R);
tube("tail", "tail.spigot", Z.tailSpigot, Z.tailTop, 29.47, R_SPIGOT);
for (const az of FIN_AZ) {
  const F = G.frameOf([0, 0, 0], dir(az + 90), dir(az), [0, 0, 1]);
  const poly = FIN.map(([r, z]) => [r, z]);
  const paths = G.prismOf(F, poly, -FIN_T / 2, FIN_T / 2, P);
  const id = nameFor("tail.fin");
  put("tail", polar(az, 84, 105), S(paths, { tone: "hi" }), { name: id, shapes: [record(A.prism(F, poly, -FIN_T / 2, FIN_T / 2, { name: id }))] });
}

// ===== helpers for the parts =========================================================
const NROT = NOSE_ROT * DEG;
const rotN = ([x, y]) => [x * Math.cos(NROT) - y * Math.sin(NROT), x * Math.sin(NROT) + y * Math.cos(NROT)];
const nosePt = (x, y, z) => [...rotN([x, y]), nz(z)];
const NX = dir(NOSE_ROT);
const NY = dir(NOSE_ROT + 90);
const noseRect = (x0, x1, y0, y1) => [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].map(rotN);
const NOSE_F = G.frameOf([0, 0, Z.nose0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
const towardCam = dir(AZ);

function turned(piece, name, profile, { tone = "hi", inner = "", extra = "", bias = 0, smooth, steps, F = AXIS, cut, rims } = {}) {
  const options = {};
  if (smooth !== undefined) options.smooth = smooth;
  if (steps) options.steps = steps;
  if (rims) options.rims = rims;
  const paths = G.solidOf(profile, F, P, options);
  const id = nameFor(name);
  const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
  const shape = record(A.solid(F, profile, { name: id, ...(cut ? { cut } : {}) }));
  put(piece, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone, inner }) + extra, { bias, name: id, shapes: [shape] });
  return shape;
}
function prism(piece, name, ring, z0, z1, { tone = "hi", inner = "", extra = "", bias = 0, convex = true, bevel } = {}) {
  const id = nameFor(name);
  const c = ring.reduce((a, p) => [a[0] + p[0] / ring.length, a[1] + p[1] / ring.length], [0, 0]);
  put(piece, [c[0], c[1], (z0 + z1) / 2], S(k.extrude(ring, z0, z1 - z0, P, { convex, ...(bevel ? { bevel } : {}) }), { tone, inner }) + extra, {
    bias, name: id, shapes: [record(A.extruded(ring, z0, z1 - z0, { name: id }))],
  });
  return id;
}
function slab(piece, name, plan, z0, z1, { tone = "hi", inner = "", extra = "", bias = 0, bevel = 0.3, steps = 3 } = {}) {
  const id = nameFor(name);
  put(piece, [plan.x + plan.w / 2, plan.y + plan.d / 2, (z0 + z1) / 2], S(k.slabOf(plan, z0, z1 - z0, P, steps, bevel), { tone, inner }) + extra, {
    bias, name: id, shapes: [record(A.slab(plan, z0, z1 - z0, { name: id }, steps))],
  });
  return id;
}
function disc(piece, name, centre, axis, s0, s1, r, { tone = "hi", extra = "", bias = 0, bevel = 0, inner = "" } = {}) {
  const F = G.frameAlong(centre, axis);
  const id = nameFor(name);
  put(piece, G.add3(centre, G.mul3(F.a, (s0 + s1) / 2)), S(G.disc(s0, s1, r, F, P, { bevel }), { tone, inner }) + extra, {
    bias, name: id, shapes: [record(A.disc(F, s0, s1, r, { name: id }))],
  });
  return F;
}
function ball(piece, name, centre, r, { tone = "hi", bias = 0 } = {}) {
  const id = nameFor(name);
  put(piece, centre, S(G.sphereOf(centre, r, P, { steps: G.stepsFor(r, 24) }), { tone }), { bias, name: id, shapes: [record(A.ball(centre, r, { name: id }))] });
}
function tubeItems(piece, name, route, r, { tone = "hi", bias = 0, maxLength = 18, spacing, touch, limp = false, gaps = [], caps = true, ends = [true, true], rims, free = [false, false], bundle } = {}) {
  const id = nameFor(name);
  REC.route(id, route, r, { owner: id, touch, limp, gaps, ends, rims, free, bundle, piece, move: PIECES[piece].move, ride: piece });
  tubePieces(route, r, P, { maxLength, spacing: spacing ?? Math.max(0.5, Math.min(2.2, r * 0.3)), gaps, caps }).forEach((part, index) =>
    put(piece, part.mid, tubeSvg(part, { tone }), { bias, name: `${id}:${index}`, route: id, chunk: index, shapes: [A.tube(part.points, part.radii)] }),
  );
  return id;
}
function cable(piece, name, points, { r = 0.6, bend = 4, tone = "mid", bias = 0.2, touch, bundle, shells = [false, false], free } = {}) {
  const route = G.fillet(points, bend, 10, { P, tube: r });
  const total = G.pathLength(route);
  const SHELL = 2.4;
  const gaps = [...(shells[0] ? [[0, SHELL]] : []), ...(shells[1] ? [[total - SHELL, total]] : [])];
  const id = tubeItems(piece, name, route, r, { tone, bias, maxLength: 12, spacing: 0.8, touch, bundle, limp: true, gaps, free, rims: shells.map((on) => (on ? r * 2 : r)) });
  [0, 1].forEach((index) => {
    const end = index ? route[route.length - 1] : route[0];
    if (!shells[index]) {
      put(piece, end, Dots([at(end)], { size: 0.5, tone: "hi" }), { bias: bias + 0.15, name: `${id}.end`, shapes: [A.ball(end, 0.5 / KS)] });
      return;
    }
    const tangent = G.tangentAlong(route, index ? total : 0);
    const F = G.frameAlong(end, tangent);
    const [s0, s1] = index ? [-SHELL, 0] : [0, SHELL];
    put(piece, G.add3(end, G.mul3(tangent, (s0 + s1) / 2)), S(G.disc(s0, s1, r * 2, F, P, { bevel: 0.2 }), { tone: "mid" }), {
      bias: bias + 0.1, name: `${id}.shell`, shapes: [record(A.disc(F, s0, s1, r * 2, { name: `${id}.shell`, owner: id }))],
    });
  });
  return route;
}
// A helix as two line items (back half, front half) round an axis; live code rebuilds it.
function coilPaths(o, a, r, len, turns) {
  const F = G.frameAlong(o, a);
  const steps = Math.ceil(turns * 28);
  const back = [];
  const front = [];
  let run = null;
  let side = null;
  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const s = len * (u - (0.6 * Math.sin(2 * Math.PI * u)) / (2 * Math.PI));
    const ang = 2 * Math.PI * turns * u;
    const p = G.pointOf(F, s, r, ang);
    const facing = G.dot3(G.radialOf(F, ang), V) >= 0;
    if (facing !== side) {
      if (run) run.push(at(p));
      run = [at(p)];
      (facing ? front : back).push(run);
      side = facing;
    } else run.push(at(p));
  }
  const d = (runs) => runs.map((pts) => "M" + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L")).join("");
  return { back: d(back), front: d(front), F };
}
// A box in the nose frame, rotated into the world.
function noseBox(piece, name, x0, x1, y0, y1, z0, z1, options = {}) {
  return prism(piece, name, noseRect(x0, x1, y0, y1), nz(z0), nz(z1), options);
}

// ===== tail internals ===============================================================
const W_TAIL = TAIL_WINDOW;
tube("tail", "tail.mount", Z.tail0, 150, 19.3, 26.0, { window: W_TAIL });
sector("tail", "tail.web", 35, 125, 26.0, R_IN, 178.6, 181.4);
// the cap's spigot inside the tail, bayonet lugs on the motor mount
tube("cap", "cap.spigot", 0, Z.capTop, 26.43, 30.78, { window: { ...W_TAIL, w1: Z.capTop } });
{
  // boattail cone, from the nozzle bore out to the body
  const cone = [[Z.cap0, 17.68], [Z.cap0, 18.4], [-25, 19.0], [-1.4, 30.8], [0, 30.8], [0, 17.68]];
  const F = AXIS;
  const id = nameFor("cap.cone");
  const paths = G.lathe(cone, F, P, { steps: 120 });
  const lip = Ln(G.arcOf(F, -12.5, 25.6, P, { slope: 0.55 }), { tone: "faint" });
  put("cap", [0, 0, -13], S(paths, { tone: "hi", inner: lip }) + Dots(G.dotsOf(F, -6, 29.4, 18, P, { slope: 0.55, fade: FADE }), { size: 0.42, tone: "mid" }), {
    name: id, shapes: [record(A.lathe(F, cone, { name: id }))],
  });
}

// ===== the motor ====================================================================
const MO = M.MOTOR;
const MZ = { nozzle: [0, 11], seg: [[11.5, 79], [79.5, 147]], closure: [147, 152] };
tube("motor", "motor.case", 0, 152, MO.caseID / 2, MO.caseOD / 2, { window: W_TAIL, seams: [6, 146] });
{
  // nozzle insert: convergent 45°, throat Ø7.5, divergent 15°, exit Ø16.8 at the case end
  const rt = MO.throatD / 2;
  const re = MO.exitD / 2;
  const sThroat = 7.6;
  const noz = [[0, re], [sThroat, rt], [sThroat + 0.6, rt], [11, 13.2], [11, 17.5], [0, 17.5]];
  const F = AXIS;
  const id = nameFor("motor.nozzle");
  put("motor", [0, 0, 5.5], S(G.lathe(noz, F, P, { steps: 96 }), { tone: "mid" }), {
    name: id, shapes: [record(A.lathe(F, noz, { name: id }))],
  });
}
// two BATES segments in their 0.2 mm casting tubes; live code burns them back
const GRAINS = [];
MZ.seg.forEach(([z0, z1], index) => {
  tube("motor", `motor.liner${index}`, z0, z1, MO.grainOD / 2, MO.linerOD / 2, { window: W_TAIL });
  const name = `motor.grain${index}`;
  const before = REC.items.length;
  tube("motor", name, z0, z1, MO.coreD / 2, MO.grainOD / 2, { window: W_TAIL });
  REC.items.slice(before).forEach((item) => (item.grain = { index, z0, z1 }));
  GRAINS.push({ z0, z1 });
});
turned("motor", "motor.closure", [[147, 17.5], [152, 17.5], [152, 6], [152.6, 6], [152.6, 0]], { tone: "mid" });
// igniter: a pyrogen stick in the lower core, its two leads out of the nozzle
const IGNITER = [[0, 0, 40], [0, 0, 6]];

// ===== lower body and coupler =========================================================
tube("lower", "lower.socket", Z.lower0, Z.tailTop, R_SOCKET, R);
tube("lower", "lower.tube", Z.tailTop, Z.lowerSpigot, R_IN, R, { seams: [366.8] });
tube("lower", "lower.spigot", Z.lowerSpigot, Z.lowerTop, 29.48, R_SPIGOT);
tube("coupler", "coupler.sleeve", Z.coupler0, Z.couplerTop, R_SOCKET, R, { seams: [Z.couplerTop - 26.2] });
{
  // rail guide on the fin can, between the fins at 180° and 300°
}

// ===== main body ======================================================================
const W_MB = { a0: -5, a1: 85, w0: 545, w1: Z.mbodyTop };
tube("mbody", "mbody.neck", Z.mbody0, Z.mbodyNeck, 29.48, R_SPIGOT);
tube("mbody", "mbody.tube", Z.mbodyNeck, s2z(39.5), R_IN, R, { window: W_MB });
tube("mbody", "mbody.bead", s2z(39.5), s2z(27.5), 29.9, R, { window: W_MB });
const NOSE_CUT = { a0: -20, a1: 112 };
const Z_CUT = nz(50);
tube("mbody", "mbody.socket", s2z(27.5), Z.mbodyTop, R_SOCKET, R, { window: { ...NOSE_CUT, w0: s2z(27.5), w1: Z.mbodyTop } });
// cord anchor lug at azimuth 0: a block off the wall with a vertical tunnel; its
// part inside the window wedge is cut, so the cut face shows the cord in the tunnel
{
  const zLow = s2z(62.5);
  const zHigh = s2z(56);
  const zRamp = s2z(46);
  sector("mbody", "mbody.lug", zLow, zHigh, 21.1, R_IN, -16, -10);
  sector("mbody", "mbody.lug", zLow, zHigh, 21.1, 21.75, -10, W_MB.a0);
  sector("mbody", "mbody.lug", zLow, zHigh, 30.92, R_IN, -10, W_MB.a0);
  sector("mbody", "mbody.lug-ramp", zHigh, zRamp, 26.5, R_IN, -16, W_MB.a0);
}
// screws: the bay's two M3 at 90/270, the nose's two M2.5 at 90/270
for (const az of [90, 270]) {
  disc("mbody", "mbody.m3-head", polar(az, R, s2z(201.5)), dir(az), 0, 2.2, 2.75, { tone: "mid", bevel: 0.25 });
  disc("mbody", "mbody.m25-head", polar(az, R, nz(N.RETAIN_Z)), dir(az), 0, 1.7, 2.25, { tone: "mid", bevel: 0.25 });
}

// ===== rail guides ======================================================================
function guide(piece, z0) {
  const z1 = z0 + 65.5;
  const F = G.frameOf([0, 0, 0], [0, 0, 1], dir(GUIDE_AZ), dir(GUIDE_AZ + 90));
  const shapes = [];
  const parts = [
    [[R - 0.6, -5.9], [R + 4, -5.9], [R + 4, 5.9], [R - 0.6, 5.9]],
    [[R + 4, -3], [43.06, -3], [43.06, 3], [R + 4, 3]],
  ];
  const id = nameFor(`${piece}.guide`);
  const svg = parts.map((poly) => S(G.prismOf(F, poly, z0, z1, P), { tone: "mid" })).join("");
  parts.forEach((poly) => shapes.push(record(A.prism(F, poly, z0, z1, { name: id }))));
  put(piece, polar(GUIDE_AZ, R + 5, (z0 + z1) / 2), svg + Dots([at(polar(GUIDE_AZ, R + 4, z0 + 8)), at(polar(GUIDE_AZ, R + 4, z1 - 8))], { size: 0.45 }), { name: id, shapes });
}
guide("tail", 152);
guide("mbody", 600);

// ===== avionics bay =====================================================================
const bz = (s) => s2z(s);
// support: the head ring (crown seats on the bead), the trough shell open toward 0°
tube("bay", "bay.head", bz(30.6), bz(27.31), 27.45, 30.6, { window: { a0: W_MB.a0, a1: W_MB.a1, w0: bz(30.6) - 1, w1: bz(27.31) + 1 } });
sector("bay", "bay.trough", bz(209), bz(30.6), 27.95, 29.45, 82, 278);
for (const sgn of [1, -1]) {
  const ang = (x) => (sgn > 0 ? Math.acos(x / 27) : -Math.acos(x / 27)) / DEG;
  for (const [x0, x1, top] of [[-10.3, -8.3, 209], [-5.7, -3.7, 188]]) {
    const y0 = Math.sqrt(27.95 ** 2 - x0 ** 2) * sgn;
    const ring = [[x0, sgn * 26.05], [x1, sgn * 26.05], [x1, sgn * Math.sqrt(27.95 ** 2 - x1 ** 2) + 0.2 * sgn], [x0, y0 + 0.2 * sgn]];
    prism("bay", "bay.rail", sgn > 0 ? ring : ring.reverse(), bz(top), bz(27.31), { tone: "mid" });
    void ang;
  }
}
for (const az of [90, 270]) sector("bay", "bay.boss", bz(209), bz(189), 22.6, 28.0, az - 9, az + 9, { tone: "mid" });
// deck: x −8 .. −6, out to r 27.05, s 27.31 .. 204.5
const DECK_HALF = Math.sqrt(27.05 ** 2 - 7 ** 2);
const deckFace = -6;
{
  const plan = { x: -8, y: -DECK_HALF, w: 2, d: 2 * DECK_HALF, r: 0.3 };
  const slot = (y, s0, s1, w = 2.5) => k.planOutline({ x: deckFace - 0.01, y: y - w / 2, w: 0.01, d: w, r: 0 }, bz(s1), P);
  void slot;
  const holes = [43, 49, 55].map((s) => k.sideRing([deckFace, 0, bz(s)], 1.25, "x", P)).join("");
  const vents = [66, 193].flatMap((s) => [-20, 20].map((y) => k.sideRing([deckFace, y, bz(s)], 2.5, "x", P))).join("");
  slab("bay", "bay.deck", plan, bz(204.5), bz(27.31), { tone: "mid", bevel: 0.2, extra: Ln(holes + vents, { tone: "lo" }) });
  for (const y of [-10.5, 10.5]) slab("bay", "bay.rib", { x: deckFace, y: y - 0.6, w: 2.5, d: 1.2, r: 0.2 }, bz(64), bz(36), { tone: "mid", bevel: 0 });
  // screw lugs at the deck's aft end
  for (const sgn of [-1, 1]) slab("bay", "bay.lug", { x: -6.5, y: sgn > 0 ? 16 : -22, w: 9.5, d: 6, r: 0.6 }, bz(204.5), bz(197.5), { tone: "mid" });
}
// ESP32 dev board: PCB, WROOM module with its can and antenna, USB, buttons, LDO
const ESP = { s0: 69, s1: 123.4, half: 27.9 / 2 };
{
  const pcbPlan = { x: deckFace, y: -ESP.half, w: 1.6, d: 2 * ESP.half, r: 0.4 };
  const pcbTop = deckFace + 1.6;
  const rows = [-12.7, 12.7].map((y) => Array.from({ length: 15 }, (_, i) => [pcbTop, y, bz(ESP.s0 + 3 + i * 2.54)]));
  slab("bay", "bay.esp32-pcb", pcbPlan, bz(ESP.s1), bz(ESP.s0), { tone: "hi", bevel: 0, extra: Dots(rows.flat().map((p) => at(p)), { size: 0.38, tone: "lo" }) });
  slab("bay", "bay.wroom", { x: pcbTop, y: -9, w: 0.8, d: 18, r: 0.2 }, bz(ESP.s0 + 25.5), bz(ESP.s0), { tone: "mid", bevel: 0 });
  slab("bay", "bay.wroom-can", { x: pcbTop + 0.8, y: -7.9, w: 2.4, d: 15.8, r: 0.3 }, bz(ESP.s0 + 23.8), bz(ESP.s0 + 6.4), { tone: "hi", bevel: 0.3,
    extra: Ln(k.segment([pcbTop + 3.2, -5, bz(ESP.s0 + 12)], [pcbTop + 3.2, 5, bz(ESP.s0 + 12)], P), { tone: "faint", free: true }) });
  // PCB antenna meander on the module's forward end
  const meander = [];
  for (let i = 0; i < 6; i++) {
    const y = -7 + i * 2.8;
    meander.push([pcbTop + 0.8, y, bz(ESP.s0 + 1.2)], [pcbTop + 0.8, y, bz(ESP.s0 + 4.6)], [pcbTop + 0.8, y + 1.4, bz(ESP.s0 + 4.6)], [pcbTop + 0.8, y + 1.4, bz(ESP.s0 + 1.2)]);
  }
  put("bay", [pcbTop + 0.8, 0, bz(ESP.s0 + 3)], Ln("M" + meander.map((p) => at(p).map((v) => v.toFixed(2)).join(" ")).join("L"), { tone: "lo" }), { bias: 0.4, name: "bay.antenna", shapes: [A.box([pcbTop + 0.7, -7.2, bz(ESP.s0 + 4.8)], [pcbTop + 0.9, 7.2, bz(ESP.s0 + 1)], { name: "bay.antenna" })] });
  slab("bay", "bay.usb", { x: pcbTop, y: -4, w: 2.8, d: 8, r: 0.4 }, bz(ESP.s1 + 0.6), bz(ESP.s1 - 5.2), { tone: "mid", bevel: 0.2 });
  for (const y of [-9, 9]) slab("bay", "bay.button", { x: pcbTop, y: y - 1.6, w: 1.6, d: 3.2, r: 0.4 }, bz(ESP.s1 - 4), bz(ESP.s1 - 7.4), { tone: "mid", bevel: 0 });
  slab("bay", "bay.ldo", { x: pcbTop, y: -2, w: 1.6, d: 4, r: 0.2 }, bz(ESP.s1 - 12), bz(ESP.s1 - 18.5), { tone: "mid", bevel: 0 });
}
// BMP280 breakout between its ribs, the sensor can with its vent
{
  const plan = { x: deckFace, y: -9.25, w: 1.2, d: 18.5, r: 0.3 };
  slab("bay", "bay.bmp280-pcb", plan, bz(63), bz(37), { tone: "hi", bevel: 0, extra: Dots([-6, -3, 0, 3, 6].map((y) => at([deckFace + 1.2, y, bz(38.5)])), { size: 0.36, tone: "lo" }) });
  slab("bay", "bay.bmp280", { x: deckFace + 1.2, y: -1.25, w: 0.95, d: 2.5, r: 0.2 }, bz(52), bz(50), { tone: "mid", bevel: 0, extra: Dots([at([deckFace + 2.15, 0.5, bz(51)])], { size: 0.32, tone: "lo" }) });
}
// the cell: an 18650 strapped to the bare aft deck
{
  const cx = deckFace + 9.3;
  const z0 = bz(193.2);
  const z1 = bz(128);
  const seam = Ln(k.sideArc(cx, 0, 9.3, z1 - 4, P, 40) + k.sideArc(cx, 0, 9.3, z0 + 4, P, 40), { tone: "faint" });
  const id = nameFor("bay.cell");
  put("bay", [cx, 0, (z0 + z1) / 2], S(k.cylinder(cx, 0, 9.3, z0, z1 - z0, P, 48, 0.4), { tone: "hi", inner: seam }), { name: id, shapes: [record(A.cylinder(cx, 0, 9.3, z0, z1 - z0, { name: id }))] });
  slab("bay", "bay.cell-cap", { x: cx - 3, y: -3, w: 6, d: 6, r: 3 }, z1, z1 + 0.8, { tone: "mid", bevel: 0 });
  for (const s of [140, 185]) {
    const z = bz(s);
    const id2 = nameFor("bay.tie");
    put("bay", [cx, 0, z], S(k.cylinder(cx, 0, 9.55, z - 0.7, 1.4, P, 48), { tone: "mid", crease: "none" }), { name: id2, shapes: [record(A.cylinder(cx, 0, 9.55, z - 0.7, 1.4, { name: id2 }))] });
  }
}

// ===== the side-door nose ==================================================================
const rn = N.NOSE_TIP_RADIUS;
const zc = N.cz + Math.sqrt((N.rho - rn) ** 2 - N.cr ** 2);
const kk = N.rho / (N.rho - rn);
const tipZ = N.cz + kk * (zc - N.cz);
const APEX = zc + rn;
const ogR = (z, d = 0) => {
  if (z <= N.z_og) return R - d;
  if (z >= tipZ) return Math.max(0, Math.sqrt(Math.max(0, (rn - d) ** 2 - (z - zc) ** 2)));
  return N.cr + Math.sqrt((N.rho - d) ** 2 - (z - N.cz) ** 2);
};
const ogSlope = (z) => {
  if (z <= N.z_og) return 0;
  if (z >= tipZ) return -(z - zc) / Math.max(1e-6, Math.sqrt(Math.max(1e-9, rn * rn - (z - zc) ** 2)));
  return -(z - N.cz) / Math.sqrt(N.rho ** 2 - (z - N.cz) ** 2);
};
const ogiveProfile = (zFrom) => {
  const pts = [[zFrom, ogR(zFrom)], [N.z_og, R]];
  for (let z = N.z_og + 2; z < tipZ; z += 2) pts.push([z, ogR(z), 1]);
  for (let i = 0; i <= 10; i++) {
    const a = (i / 10) * Math.acos((tipZ - zc) / rn);
    const z = zc + rn * Math.cos(Math.acos((tipZ - zc) / rn) - a);
    pts.push([z, ogR(z), i < 10 ? 1 : 0]);
  }
  pts.push([APEX, 0]);
  return pts.filter((p, i, all) => i === 0 || p[0] > all[i - 1][0] + 1e-6);
};
const OGIVE = ogiveProfile(N.z_d0);
// screen regions: the camera looks along the split plane, so the door is the half of
// the picture on the 120° side of the axis, between its bottom ring and the joint
const jointZ = (thetaN, gap) => {
  let z = N.NOSE_DOOR_JOINT_Z;
  for (let i = 0; i < 40; i++) z = N.NOSE_DOOR_JOINT_Z - gap + N.door_k * ogR(z) * Math.cos(thetaN * DEG);
  return z;
};
function doorRegion(gap) {
  const pts = [];
  for (let t = 30; t <= 120; t += 2) pts.push(at(polar(t, R, nz(N.z_d0))));
  const limb = at(polar(120, R, nz(N.z_d0)));
  const out = Math.sign(limb[0] - at([0, 0, nz(N.z_d0)])[0]) * 40;
  pts.push([limb[0] + out, limb[1]]);
  const top = [];
  for (let t = 120; t >= 30; t -= 2) {
    const z = jointZ(t - NOSE_ROT, gap);
    top.push(at(polar(t, ogR(z), nz(z))));
  }
  pts.push([top[0][0] + out, top[0][1] - 2]);
  pts.push(...top);
  return pts;
}
const polyD = (pts) => "M" + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L") + "Z";
function skirtWindow(a0 = 30, a1 = NOSE_CUT.a1) {
  const pts = [];
  for (let t = a0; t <= a1; t += 2) pts.push(at(polar(t, R + 0.5, nz(N.z_d0) - 0.4)));
  for (let t = a1; t >= a0; t -= 2) pts.push(at(polar(t, R + 0.5, Z_CUT)));
  return pts;
}
const DOOR_CLIP = polyD(doorRegion(0)) + polyD(skirtWindow());
const HOUSE_CLIP = `M-2000 -2000H${W + 2000}V${H + 2000}H-2000Z` + polyD(doorRegion(0)) + polyD(skirtWindow(NOSE_CUT.a0, 30));
const defs = [`<clipPath id="hx-door"><path clip-rule="evenodd" d="${DOOR_CLIP}"/></clipPath>`, `<clipPath id="hx-door-solid"><path d="${polyD(doorRegion(N.NOSE_DOOR_JOINT_GAP))}"/></clipPath>`, `<clipPath id="hx-house"><path clip-rule="evenodd" d="${HOUSE_CLIP}"/></clipPath>`];
const nearHalf = A.orientedBox(G.add3([0, 0, Z.nose0 + 140], G.mul3(towardCam, 200)), [towardCam, dir(AZ + 90), [0, 0, 1]], [200, 300, 400], { name: "cut.near" });
const doorHalfBox = A.orientedBox(G.add3([0, 0, Z.nose0 + 140], G.mul3(NX, 200)), [NX, NY, [0, 0, 1]], [200, 300, 400], { name: "cut.door" });
const houseHalfBox = A.orientedBox(G.add3([0, 0, Z.nose0 + 140], G.mul3(NX, -200)), [NX, NY, [0, 0, 1]], [200, 300, 400], { name: "cut.house" });
{
  const paths = G.solidOf(OGIVE, NOSE_F, P, { smooth: { slope: ogSlope, rows: 6 } });
  const seams = Ln(G.arcOf(NOSE_F, N.z_og, R, P) , { tone: "faint" });
  const hid = nameFor("nose.ogive");
  put("nose", [0, 0, nz(140)], `<g clip-path="url(#hx-house)">${S(paths, { tone: "hi", inner: seams })}</g>`, { name: hid, shapes: [record(A.solid(NOSE_F, OGIVE, { name: hid, cut: [doorHalfBox] }))] });
  const did = nameFor("door.shell");
  const jointLine = [];
  for (let t = 30; t <= 120; t += 1.5) {
    const z = jointZ(t - NOSE_ROT, 0);
    jointLine.push(at(polar(t, ogR(z) - 0.15, nz(z))));
  }
  const splitLine = [at(polar(30, R, Z_CUT)), at(polar(30, ogR(jointZ(-90, N.NOSE_DOOR_JOINT_GAP)), nz(jointZ(-90, N.NOSE_DOOR_JOINT_GAP))))];
  const doorSeams = Ln("M" + jointLine.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L"), { tone: "lo" }) + Ln(`M${splitLine.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join("L")}`, { tone: "faint" });
  put("door", [0, 0, nz(110)], `<g clip-path="url(#hx-door)">${S(paths, { tone: "hi", inner: seams })}</g>` + doorSeams, { name: did, shapes: [record(A.solid(NOSE_F, OGIVE, { name: did, cut: [houseHalfBox] }))] });
  // the housing's inside, seen once the door is off: its far wall, a darker cavity
  const inner = [];
  for (let z = N.z_f; z < APEX - N.NOSE_SOLID_TIP; z += 3) inner.push([z, ogR(z, N.NOSE_WALL)]);
  const wall = [...inner, ...[...inner].reverse().map(([z, r]) => [z, r + 0.6])];
  const cid = nameFor("nose.cavity");
  const voidD = G.outlineOf([[N.z_f, 0], ...inner, [inner[inner.length - 1][0], 0]], NOSE_F, P).fill;
  put("nose", [0, 0, nz(110)], `<g clip-path="url(#hx-door)"><path class="hx-void" d="${voidD}"/></g>`, { name: cid, shapes: [record(A.body(NOSE_F, wall, { name: cid, cut: [nearHalf] }))] });
}
// shoulder (inside Mbody's socket) and band, both cut to show the latch
tube("nose", "nose.shoulder", Z.nose0, Z.mbodyTop, N.r_sh_in, N.r_sh, { window: { ...NOSE_CUT, w0: Z.nose0 - 1, w1: Z.mbodyTop } });
tube("nose", "nose.band", Z.mbodyTop, nz(N.z_d0), R - N.NOSE_WALL, R, { window: { ...NOSE_CUT, w0: Z.mbodyTop, w1: nz(N.z_d0) } });
for (const az of N.RETAIN_AZ) {
  const a = az + NOSE_ROT;
  sector("nose", "nose.pad", Z.nose0, nz(N.RETAIN_PAD_Z_FULL), N.RETAIN_PAD_R_IN, N.r_sh_in + 0.3, a - 12, a + 12, { tone: "mid" });
}
// servo plate and split plate
const SV = N.servo;
const xSplit = -N.NOSE_DOOR_CLEARANCE - N.NOSE_DOOR_SPLIT_PLATE;
{
  const yIn = Math.sqrt(N.r_sh_in ** 2 - Math.max(xSplit * xSplit, SV.x_seat ** 2)) - 0.2;
  // cut on y = 0: the half toward the camera is inside the wedge
  noseBox("nose", "nose.servo-plate", xSplit, SV.x_seat, 6.35, yIn, 0.5, N.z_d0 - 0.5, { tone: "mid" });
  noseBox("nose", "nose.servo-plate", xSplit, SV.x_seat, 0, 6.35, SV.z_hi + 0.25, N.z_d0 - 0.5, { tone: "mid" });
  noseBox("nose", "nose.servo-plate", xSplit, SV.x_seat, 0, 6.35, 0.5, SV.z_lo - 0.25, { tone: "mid" });
  const yTop = Math.sqrt((R - N.NOSE_WALL) ** 2 - xSplit ** 2) - 0.2;
  noseBox("nose", "nose.split-plate", xSplit, -N.NOSE_DOOR_CLEARANCE, 0, yTop, N.z_d0 - 0.5, nz(50) - Z.nose0, { tone: "mid" });
  noseBox("nose", "nose.split-plate", xSplit, -N.NOSE_DOOR_CLEARANCE, -yTop, yTop, nz(50) - Z.nose0, N.z_f, { tone: "mid" });
}
// MG90S: body, ears, gear tower, spline, horn and the arm standing in the door's groove
const SERVO = {};
{
  const w2 = N.SERVO_BODY_W / 2;
  const xb = SV.x_bottom;
  const xt = SV.x_bottom + N.SERVO_BODY_H;
  const ear = (N.SERVO_EAR_SPAN - N.SERVO_BODY_L) / 2;
  noseBox("nose", "nose.servo", xb, xt, -w2, w2, SV.z_lo, SV.z_hi, { tone: "hi", bevel: 0.3 });
  noseBox("nose", "nose.servo-ears", SV.x_seat, SV.x_seat + N.SERVO_EAR_T, -w2, w2, SV.z_lo - ear, SV.z_hi + ear, { tone: "mid" });
  for (const z of SV.z_holes) disc("nose", "nose.ear-screw", nosePt(SV.x_seat + N.SERVO_EAR_T, 0, z), NX, 0, 0.9, 1.6, { tone: "mid" });
  disc("nose", "nose.gear-tower", nosePt(xt - 0.1, 0, SV.z_shaft), NX, 0, 2.6, w2 - 0.3, { tone: "hi" });
  disc("nose", "nose.spline", nosePt(xt + 2.5, 0, SV.z_shaft), NX, 0, SV.x_horn - 0.9 - xt - 2.5, 2.4, { tone: "mid" });
  SERVO.hub = nosePt(SV.x_horn - 0.9, 0, SV.z_shaft);
}
// door floor block, cut by the wedge (kept: nose angles -8 to 90 deg), with the latch groove
{
  const Rr = R - 0.05;
  const t8 = Math.tan(-8 * DEG);
  const edge = Rr * Math.cos(8 * DEG);
  const region = (xa, xb) => {
    const pts = [];
    const xr = Math.min(xb, edge);
    for (let i = 0; i <= 6; i++) {
      const x = xa + ((xr - xa) * i) / 6;
      pts.push([x, x * t8]);
    }
    const open = xb >= edge;
    const a0 = open ? -8 : Math.acos(xb / Rr) / DEG;
    const a1 = Math.acos(xa / Rr) / DEG;
    if (!open) pts.push([xb, Math.sqrt(Rr * Rr - xb * xb)]);
    for (let i = open ? 0 : 1; i <= 16; i++) {
      const a = (a0 + ((a1 - a0) * i) / 16) * DEG;
      pts.push([Rr * Math.cos(a), Rr * Math.sin(a)]);
    }
    return pts.map(rotN);
  };
  const g0 = N.NOSE_DOOR_GROOVE_R - N.NOSE_DOOR_GROOVE_W / 2;
  const g1 = N.NOSE_DOOR_GROOVE_R + N.NOSE_DOOR_GROOVE_W / 2;
  const zg = N.z_d0 + N.NOSE_DOOR_GROOVE_H;
  prism("door", "door.floor", region(N.NOSE_DOOR_CLEARANCE, g0), nz(N.z_d0), nz(zg), { tone: "hi", convex: false });
  prism("door", "door.floor", region(g1, R), nz(N.z_d0), nz(zg), { tone: "hi", convex: false });
  prism("door", "door.floor", region(N.NOSE_DOOR_CLEARANCE, R), nz(zg), nz(N.z_f), { tone: "hi", convex: false });
  sector("door", "door.cut", nz(N.z_d0), Z_CUT, R - N.NOSE_WALL, R, NOSE_CUT.a1 - 0.4, NOSE_CUT.a1, { tone: "hi" });
  sector("nose", "nose.skirt-cut", nz(N.z_d0), Z_CUT, R - N.NOSE_WALL, R, NOSE_CUT.a0, NOSE_CUT.a0 + 0.4, { tone: "hi" });
}
// horn hub and the single arm, standing up in the door's groove (latched)
const ARM = { x0: SV.x_horn - 0.9, x1: SV.x_horn + 0.9, half: 2.25, len: N.SERVO_ARM };
disc("nose", "nose.horn-hub", nosePt(ARM.x0, 0, SV.z_shaft), NX, 0, ARM.x1 - ARM.x0, 3.5, { tone: "hi" });
function armPaths(deg) {
  const F = G.frameOf(nosePt(0, 0, SV.z_shaft), NX, NY, [0, 0, 1]);
  const c = Math.cos(deg * DEG);
  const sn = Math.sin(deg * DEG);
  const poly = [[-ARM.half, 0], [ARM.half, 0], [ARM.half, ARM.len], [-ARM.half, ARM.len]].map(([y, z]) => [y * c - z * sn, y * sn + z * c]);
  return { F, poly };
}
{
  const { F, poly } = armPaths(0);
  const id = nameFor("nose.arm");
  put("nose", nosePt(SV.x_horn, 0, SV.z_shaft + 7), S(G.prismOf(F, poly, ARM.x0, ARM.x1, P), { tone: "hi" }), { name: id, shapes: [record(A.prism(F, poly, ARM.x0, ARM.x1, { name: id }))] });
}

// ===== on the ground board: launch controller, ground station, igniter =================
const BOARD_TOP = PAD.ground + 12;
const CONTROLLER = { x: 150, y: 20, w: 70, d: 92, r: 4 };
const STATION = { x: 30, y: 160, w: 76, d: 56, r: 4 };
const DIAL = { x: STATION.x + 38, y: STATION.y + 28, r: 21 };
{
  const c = CONTROLLER;
  const top = BOARD_TOP + 34;
  back.push(`<path class="iso-halo" d="${k.haloOf(c, BOARD_TOP, 34, P)}"/>`);
  back.push(S(k.slabOf(c, BOARD_TOP, 34, P, 4, 1), { tone: "mid", inner: Ln(k.sideSeam(c, top - 8, P, 4), { tone: "faint" }) }));
  record(A.slab(c, BOARD_TOP, 34, { name: "stand.controller", owner: "stand.frame" }));
  back.push(Ln(k.planOutline(k.insetPlan(c, 4), top, P, 3), { tone: "faint" }));
  back.push(Dots(k.corners(c, 5).map(([x, y]) => at([x, y, top])), { size: 0.5 }));
  const key = [c.x + 18, c.y + 26];
  back.push(S(k.cylinder(key[0], key[1], 7, top, 3, P, 32, 0.4), { tone: "hi" }));
  back.push(Ln(k.knurl(key[0], key[1], 7, top + 0.4, top + 2.6, 28, P), { tone: "lo" }));
  back.push(S(k.slabOf({ x: key[0] - 1.2, y: key[1] - 4.5, w: 2.4, d: 9, r: 0.8 }, top + 3, 2.2, P, 2), { tone: "hi", lit: true }));
  const lamp = [c.x + 18, c.y + 52];
  back.push(S(k.cylinder(lamp[0], lamp[1], 4.2, top, 2, P, 24), { tone: "mid" }));
  const lp = at([lamp[0], lamp[1], top + 2]);
  back.push(`<ellipse class="hx-lamp" data-lamp cx="${lp[0].toFixed(1)}" cy="${lp[1].toFixed(1)}" rx="${(2.6 * KS).toFixed(2)}" ry="${(2.6 * KS * Math.sin(EL * DEG)).toFixed(2)}"/>`);
  const button = [c.x + 46, c.y + 40];
  back.push(S(k.cylinder(button[0], button[1], 11, top, 2.5, P, 40, 0.6), { tone: "mid" }));
  back.push(S(k.cylinder(button[0], button[1], 8, top + 2.5, 4, P, 40, 0.6), { tone: "hi" }));
  const plate = { x: c.x + 8, y: c.y + 68, w: 52, d: 14, r: 1.5 };
  back.push(S(k.slabOf(plate, top, 0.8, P, 3), { tone: "lo" }));
  back.push(Ln(k.planOutline(k.insetPlan(plate, 1.6), top + 0.8, P, 2), { tone: "faint" }));
  back.push(Ln([0, 1].map((row) => k.onTop([[plate.x + 5, plate.y + 4.5 + row * 4.5], [plate.x + (row ? 30 : 42), plate.y + 4.5 + row * 4.5]], top + 0.8, P)).join(""), { tone: "lo", free: true }));
}
{
  const st = STATION;
  const top = BOARD_TOP + 22;
  back.push(`<path class="iso-halo" d="${k.haloOf(st, BOARD_TOP, 22, P)}"/>`);
  back.push(S(k.slabOf(st, BOARD_TOP, 22, P, 4, 1), { tone: "mid", inner: Ln(k.sideSeam(st, top - 6, P, 4), { tone: "faint" }) }));
  record(A.slab(st, BOARD_TOP, 22, { name: "stand.station", owner: "stand.frame" }));
  back.push(Dots(k.corners(st, 4.5).map(([x, y]) => at([x, y, top])), { size: 0.5 }));
  const dz = top;
  back.push(S(k.cylinder(DIAL.x, DIAL.y, DIAL.r, dz, 6, P, 64, 0.6), { tone: "hi", crease: "lo" }));
  back.push(Ln(k.knurl(DIAL.x, DIAL.y, DIAL.r, dz + 2.6, dz + 6, 72, P, 0.3), { tone: "lo" }));
  back.push(Ln(k.ring(DIAL.x, DIAL.y, DIAL.r - 2, dz + 6, P, 64), { tone: "lo" }));
  const ticks = k.radialTicks(DIAL.x, DIAL.y, DIAL.r - 2.6, 50, 5, dz + 6, [1.4, 3], P);
  back.push(Ln(ticks.minor, { tone: "lo" }), Ln(ticks.major, { tone: "mid" }));
  back.push(Ln(k.ring(DIAL.x, DIAL.y, 1.6, dz + 6, P, 16), { tone: "hi" }));
  back.push(`<path class="iso-line" data-tone="lit" data-needle style="stroke-width:1.1" d="${k.lineOnTop([DIAL.x, DIAL.y + 3], [DIAL.x, DIAL.y - DIAL.r + 5], dz + 6.2, P)}"/>`);
  const ant = [st.x + st.w - 9, st.y + 9];
  back.push(S(k.cylinder(ant[0], ant[1], 3.4, top, 4, P, 20), { tone: "mid" }));
  back.push(S(k.cylinder(ant[0], ant[1], 1.1, top + 4, 92, P, 12), { tone: "mid", crease: "none" }));
  back.push(Dots([at([ant[0], ant[1], top + 96])], { size: 1.4, tone: "hi" }));
}
// controller lead along the board to the pad's terminal block, igniter leads up to the nozzle
const TERMINAL = [62, 46];
{
  back.push(S(k.slabOf({ x: TERMINAL[0] - 9, y: TERMINAL[1] - 6, w: 18, d: 12, r: 1 }, PAD_TOP, 6, P, 2, 0.4), { tone: "mid" }));
  back.push(Dots([at([TERMINAL[0] - 4, TERMINAL[1], PAD_TOP + 6]), at([TERMINAL[0] + 4, TERMINAL[1], PAD_TOP + 6])], { size: 0.8, tone: "hi" }));
  const lead = G.fillet([[CONTROLLER.x, CONTROLLER.y + 70, BOARD_TOP + 10], [CONTROLLER.x - 30, CONTROLLER.y + 70, BOARD_TOP + 1.2], [100, 46, BOARD_TOP + 1.2], [100, 46, PAD.z - 2], [TERMINAL[0] + 9, TERMINAL[1], PAD_TOP + 3]], 8, 10);
  for (const part of tubePieces(lead, 1.6, P, { maxLength: 400 })) back.push(tubeSvg(part, { tone: "lo" }));
}
for (const side of [-1, 1]) {
  const tip = [side * 1.2, side * 0.6, Z.cap0 - 1];
  const clip = [TERMINAL[0] - 30 + side * 6, TERMINAL[1] - 20, -95];
  cable("motor", "motor.igniter-lead", [[side * 0.8, 0, 8], tip, [side * 6, 2, -60], clip], { r: 0.35, bend: 10, tone: "lo", bias: 0.4 });
  slab("stand", "stand.clip", { x: clip[0] - 2, y: clip[1] - 5, w: 4, d: 10, r: 0.8 }, clip[2] - 3, clip[2] + 1, { tone: "hi" });
  cable("stand", "stand.clip-lead", [[clip[0], clip[1] - 5, clip[2] - 1], [clip[0], clip[1] - 14, -120], [TERMINAL[0] + side * 4, TERMINAL[1], PAD_TOP + 6]], { r: 0.45, bend: 8, tone: "lo" });
}

// spring pins with collars, springs (compressed), ramp, eye and the cord hole
const SPRINGS = [];
{
  const zsp = N.z_d0 + N.NOSE_DOOR_SPRING_Z;
  for (const y of [-N.NOSE_DOOR_SPRING_Y, N.NOSE_DOOR_SPRING_Y]) {
    const half = N.NOSE_DOOR_PIN_D / 2;
    const F = G.frameOf(nosePt(0, y, zsp), NX, NY, [0, 0, 1]);
    const diamond = [[0, -half], [half, 0], [0, half], [-half, 0]];
    const id = nameFor("nose.pin");
    put("nose", nosePt(7, y, zsp), S(G.prismOf(F, diamond, -N.NOSE_DOOR_CLEARANCE - 1, N.pin_tip_x, P), { tone: "mid" }), { name: id, shapes: [record(A.prism(F, diamond, -N.NOSE_DOOR_CLEARANCE - 1, N.pin_tip_x, { name: id }))] });
    const ch = N.NOSE_DOOR_PIN_COLLAR_D / 2;
    const collar = [[0, -ch], [ch, 0], [0, ch], [-ch, 0]];
    const cid = nameFor("nose.collar");
    put("nose", nosePt(1, y, zsp), S(G.prismOf(F, collar, -N.NOSE_DOOR_CLEARANCE - 1, -N.NOSE_DOOR_CLEARANCE + N.NOSE_DOOR_PIN_COLLAR_LEN, P), { tone: "mid" }), { name: cid, shapes: [record(A.prism(F, collar, -N.NOSE_DOOR_CLEARANCE - 1, -N.NOSE_DOOR_CLEARANCE + N.NOSE_DOOR_PIN_COLLAR_LEN, { name: cid }))] });
    const o = nosePt(-N.NOSE_DOOR_CLEARANCE, y, zsp);
    const coil = coilPaths(o, NX, 2.25, N.pocket_bottom_x + N.NOSE_DOOR_CLEARANCE, 10);
    const sid = nameFor("nose.spring");
    const centre = G.add3(o, G.mul3(NX, 6));
    const helix = Array.from({ length: 41 }, (_, i) => G.add3(o, G.mul3(NX, ((N.pocket_bottom_x + 0.2) * i) / 40)));
    put("nose", G.add3(centre, G.mul3(towardCam, -2.5)), Ln(coil.back, { tone: "lo" }), { name: `${sid}.back`, shapes: [A.tube(helix.map((p) => G.add3(p, G.mul3(towardCam, -1.6))), 0.6)] });
    put("nose", G.add3(centre, G.mul3(towardCam, 2.5)), Ln(coil.front, { tone: "hi" }), { name: `${sid}.front`, shapes: [A.tube(helix.map((p) => G.add3(p, G.mul3(towardCam, 1.6))), 0.6)] });
    SPRINGS.push({ y, o, name: sid });
  }
  const kr = Math.tan(N.NOSE_DOOR_RAMP_ANGLE * DEG);
  const tv = N.NOSE_DOOR_RAMP_T / Math.cos(N.NOSE_DOOR_RAMP_ANGLE * DEG);
  // ramp: a plate rising at 50° from the split edge to the wall, drawn as slices
  const rampTop = (x) => N.z_f + kr * (-N.NOSE_DOOR_CLEARANCE - x);
  const xs = [-0.2, -6, -12, -18, -24, -29.5];
  for (let i = 0; i < xs.length - 1; i++) {
    const [x0, x1] = [xs[i + 1], xs[i]];
    const yw = Math.sqrt(Math.max(0, (ogR(rampTop(x0), N.NOSE_WALL) - 0.3) ** 2 - x0 * x0));
    const F = G.frameOf(nosePt(0, 0, 0), NY, NX, [0, 0, 1]);
    const poly = [[x1, nz(rampTop(x1)) - Z.nose0 - tv], [x1, nz(rampTop(x1)) - Z.nose0], [x0, nz(rampTop(x0)) - Z.nose0], [x0, nz(rampTop(x0)) - Z.nose0 - tv]].map(([x, z]) => [x, z]);
    const G2 = G.frameOf(nosePt(0, 0, 0), NY, NX, [0, 0, 1]);
    const id = nameFor("nose.ramp");
    const polygon = poly.map(([x, z]) => [x, z]);
    put("nose", nosePt((x0 + x1) / 2, 0, (rampTop(x0) + rampTop(x1)) / 2), S(G.prismOf(G2, polygon, -yw, yw, P), { tone: "mid" }), { name: id, shapes: [record(A.prism(G2, polygon, -yw, yw, { name: id }))] });
    void F;
  }
  // tie eye on the ramp
  const ex0 = -12;
  const ex1 = -4;
  const eyePoly = [[ex0, rampTop(ex0) - tv + 0.5], [ex1, rampTop(ex1) - tv + 0.5], [ex1, rampTop(ex0) + 7], [ex0, rampTop(ex0) + 7]];
  const G2 = G.frameOf(nosePt(0, 0, 0), NY, NX, [0, 0, 1]);
  const eid = nameFor("nose.eye");
  put("nose", nosePt(-8, 0, rampTop(-8) + 3), S(G.prismOf(G2, eyePoly, -4, 4, P), { tone: "mid" }) + Ln(k.sideRing(nosePt(-8, -4, rampTop(-8) + 4.5), 2.5, "y", P), { tone: "lo" }), { name: eid, shapes: [record(A.prism(G2, eyePoly, -4, 4, { name: eid }))] });
}
// the packed chute on the ramp and floor
const BAG = { x: 4, y: 0, r: 15, z0: N.z_f + 12.5, z1: 150 };
{
  const c = nosePt(BAG.x, BAG.y, 0);
  const F = G.frameOf([c[0], c[1], nz(0)], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  const prof = [[BAG.z0, 0], [BAG.z0, BAG.r - 3], [BAG.z0 + 3, BAG.r, 1], [BAG.z1 - 12, BAG.r, 1], [BAG.z1 - 5, BAG.r - 4, 1], [BAG.z1 - 1, BAG.r - 10, 1], [BAG.z1, 0]];
  const id = nameFor("chute.bag");
  const folds = Ln([BAG.z0 + 20, BAG.z0 + 45, BAG.z0 + 70].map((z) => G.arcOf(F, z, BAG.r, P)).join(""), { tone: "faint" });
  PIECES.chute = { name: "Parachute", move: PIECES.nose.move };
  put("chute", [c[0], c[1], nz((BAG.z0 + BAG.z1) / 2)], S(G.solidOf(prof, F, P, { smooth: { rows: 4 } }), { tone: "hi", inner: folds }), { name: id, ride: "nose", shapes: [record(A.solid(F, prof, { name: id }))] });
}
// the shock cord: anchor tunnel, up the wall at 0°, through the bay's head ring and
// the nose's ramp hole, into the bag
{
  const [hx, hy] = rotN(N.cord_hole);
  const route = [[26.3, 0, s2z(62)], [26.3, 0, s2z(50)], [24.6, 0, s2z(20)], [22.5, 0, nz(20)], [hx, hy, nz(50)], [hx, hy, nz(64)], [...rotN([BAG.x - 6, -8]), nz(BAG.z0 + 4)]];
  PIECES.cord = { name: "Shock cord", move: [0, 0, 0] };
  tubeItems("cord", "cord.kevlar", G.fillet(route, 8, 10, { P, tube: 2 }), 2, { tone: "mid", limp: true, maxLength: 14, spacing: 0.9 });
}
// servo lead: from the servo down through the head ring to the ESP32's header
{
  const start = nosePt(SV.x_bottom + 2, 4, SV.z_lo - 0.5);
  cable("bay", "bay.servo-lead", [start, nosePt(SV.x_bottom + 2, 4, SV.z_lo - 6), [-2, 9, bz(26)], [-1.5, 9.5, bz(60)], [-2, 9.5, bz(ESP.s0 + 1)], [deckFace + 3, 9.5, bz(ESP.s0 + 3)]], { r: 0.75, bend: 5, shells: [false, true] });
  cable("bay", "bay.i2c", [[deckFace + 2.2, -4, bz(38.4)], [deckFace + 4, -4, bz(40)], [deckFace + 4, -4, bz(ESP.s0 - 2)], [deckFace + 2.4, -4, bz(ESP.s0 + 3)]], { r: 0.55, bend: 2 });
  cable("bay", "bay.cell-lead", [[deckFace + 9.3, 4, bz(128) + 0.8], [deckFace + 9.3, 4, bz(126)], [deckFace + 3, 6, bz(ESP.s1 + 2)], [deckFace + 2.4, 6, bz(ESP.s1 - 1)]], { r: 0.6, bend: 2.5 });
}

// camera windows: viewBox rectangles at the card's aspect, fitted to world boxes
function windowOf(points, pad = 18) {
  const sp = points.map((p) => at(p));
  let [x0, y0, x1, y1] = [Math.min(...sp.map((p) => p[0])), Math.min(...sp.map((p) => p[1])), Math.max(...sp.map((p) => p[0])), Math.max(...sp.map((p) => p[1]))];
  x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
  const w = x1 - x0, h = y1 - y0, aspect = W / H;
  if (w / h < aspect) { const nw = h * aspect; x0 -= (nw - w) / 2; x1 = x0 + nw; } else { const nh = w / aspect; y0 -= (nh - h) / 2; y1 = y0 + nh; }
  return [x0, y0, x1 - x0, y1 - y0].map((v) => Math.round(v * 10) / 10);
}
const ring3 = (r, z) => Array.from({ length: 12 }, (_, i) => polar(i * 30, r, z));
const CAMS = {
  rest: windowOf([...ring3(250, PAD.ground), ...ring3(140, 120), [0, 0, APEX + Z.nose0 + 10], ...ring3(60, RAIL.z1)], 14),
  motor: windowOf([...ring3(60, Z.cap0 - 10), ...ring3(60, 200)], 10),
  bay: windowOf([...ring3(40, s2z(210)), ...ring3(40, s2z(20))], 10),
  nose: windowOf([...ring3(45, Z.nose0), ...ring3(30, nz(200)), [0, 0, nz(APEX)]], 10),
  latch: windowOf([...ring3(36, Z.nose0 - 4), ...ring3(36, nz(62))], 4),
};
// ===== painter's order, live data, page ===========================================================
const items = REC.items;
A.settle(REC, P);
items.sort((a, b) => a.key - b.key);
const groups = items.map((item, index) => {
  const [mx, my, mz] = item.move;
  const sec = item.sec ? ` data-sec="${item.sec.slice(0, 6).map((v) => +v.toFixed(3)).join(",")},${item.sec[6]}"` : "";
  const grain = /^motor\.grain(\d)/.exec(item.name);
  return `<g class="it" data-piece="${item.piece}" data-name="${item.name}"${grain ? ` data-grain="${grain[1]}"` : ""}${sec}${item.ride !== item.piece ? ` data-ride="${item.ride}"` : ""} data-k="${item.key.toFixed(2)}" data-m="${mx.toFixed(1)},${my.toFixed(1)},${mz.toFixed(1)}" data-i="${index}">${item.svg}</g>`;
});

// camera windows for every assembly, at rest and apart, from the recorded shapes
const boxOf = (shape) => {
  const b = A.boundsOf(shape);
  return Array.isArray(b) ? b : [b.min, b.max];
};
const pieceWin = {};
for (const id of Object.keys(PIECES)) {
  const pts = [];
  for (const item of items.filter((it) => it.piece === id)) for (const shape of item.shapes ?? []) {
    const [lo, hi] = boxOf(shape);
    if (!lo || hi[0] - lo[0] > 2000) continue;
    for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]]) pts.push([x, y, z]);
  }
  if (!pts.length) continue;
  const mv = PIECES[id].move;
  pieceWin[id] = { rest: windowOf(pts, 16), apart: windowOf(pts.map((p) => G.add3(p, mv)), 16) };
}
pieceWin.door.rest = CAMS.nose;
pieceWin.nose.rest = CAMS.nose;
const apartPts = [];
for (const item of items) for (const shape of item.shapes ?? []) {
  const [lo, hi] = boxOf(shape);
  if (!lo || hi[0] - lo[0] > 2000) continue;
  const mv = item.move;
  for (const p of [lo, hi]) apartPts.push(G.add3(p, mv));
}
CAMS.apart = windowOf([...apartPts, ...ring3(250, PAD.ground)], 40);

// geometry the page rebuilds while it moves: the door, the arm, the springs, the canopy
const region3 = (() => {
  const pts = [];
  for (let t = 30; t <= 120; t += 2) pts.push(polar(t, R, nz(N.z_d0)));
  pts.push(polar(120, R + 30, nz(N.z_d0)));
  const z120 = jointZ(0, 0);
  pts.push(polar(120, R + 30, nz(z120)));
  for (let t = 120; t >= 30; t -= 2) {
    const z = jointZ(t - NOSE_ROT, 0);
    pts.push(polar(t, ogR(z), nz(z)));
  }
  return pts;
})();
const window3 = (() => {
  const pts = [];
  for (let t = 30; t <= NOSE_CUT.a1; t += 2) pts.push(polar(t, R + 0.5, nz(N.z_d0) - 0.4));
  for (let t = NOSE_CUT.a1; t >= 30; t -= 2) pts.push(polar(t, R + 0.5, Z_CUT));
  return pts;
})();
const jointPts = [];
for (let t = 30; t <= 120; t += 1.5) {
  const z = jointZ(t - NOSE_ROT, 0);
  jointPts.push(polar(t, ogR(z) - 0.15, nz(z)));
}
const doorFloor = items.filter((it) => it.name.startsWith("door.floor")).map((it) => {
  const sh = it.shapes[0];
  return { ring: sh.ring ?? sh.poly, z0: sh.z ?? sh.z0, h: sh.height ?? sh.h };
});
const unitOf = (vector) => {
  const o = at([0, 0, 0]);
  const p = at(vector);
  return [p[0] - o[0], p[1] - o[1]];
};
const flightRows = (() => {
  const f = M.flight();
  const out = [];
  let last = -1;
  for (const row of f.rows) {
    const t = row[0];
    const dense = t < f.events.inflated + 1.5;
    if (t - last < (dense ? 0.02 : 0.5)) continue;
    last = t;
    out.push([+t.toFixed(3), +row[1].toFixed(2), +row[2].toFixed(2), +row[4].toFixed(1), +row[6].toFixed(2), +row[7].toFixed(3), +row[8].toFixed(3)]);
  }
  return { rows: out, events: f.events, impulse: f.motor.impulse, burn: f.motor.burn, peakF: f.motor.peakF, liftoff: M.LIFTOFF };
})();
const DATA = {
  W, H, V, EX: unitOf([1, 0, 0]), EY: unitOf([0, 1, 0]), EZ: unitOf([0, 0, 1]),
  P: { origin: P.origin, scale: P.scale, azimuth: P.azimuth, elevation: P.elevation },
  camera: glCamera(P),
  cams: CAMS, pieceWin,
  pieces: Object.fromEntries(Object.entries(PIECES).map(([id, piece]) => [id, { name: piece.name }])),
  stagger: STAGGER, spring: SPRING,
  order: ["nose", "door", "chute", "bay", "mbody", "coupler", "lower", "tail", "motor", "cap"],
  flight: flightRows, deploy: M.DEPLOY,
  rocketTop: nz(APEX), rocketBottom: Z.cap0,
  nozzle: [0, 0, Z.cap0], nozzleR: M.MOTOR.exitD / 2,
  grain: { rCore: M.MOTOR.coreD / 2, web: M.MOTOR.web },
  door: {
    ogive: OGIVE, og: { cr: N.cr, cz: N.cz, rho: N.rho, zog: N.z_og, tipZ, zc, rn, R },
    origin: [0, 0, Z.nose0], region3, window3, joint: jointPts,
    split: [polar(30, R, Z_CUT), polar(30, ogR(jointZ(-90, 0)), nz(jointZ(-90, 0)))],
    floor: doorFloor,
    hinge: nosePt(...N.hinge_point), axis: G.mul3(NY, -1),
    mass: M.MASS.door,
  },
  arm: { o: nosePt(0, 0, SV.z_shaft), a: NX, u: NY, x0: ARM.x0, x1: ARM.x1, half: ARM.half, len: ARM.len, unlock: N.SERVO_UNLOCK_ANGLE },
  springs: SPRINGS.map(({ o, name }) => ({ o, a: NX, name, closed: N.pocket_bottom_x + N.NOSE_DOOR_CLEARANCE, free: N.SPRING_FREE_LEN })),
  bag: { out: G.add3(G.mul3(NX, 62), [0, 0, 26]) },
  dial: { x: DIAL.x, y: DIAL.y, r: DIAL.r, z: BOARD_TOP + 22 + 6.2 },
  cordExit: nosePt(28, -6, N.z_f + 8),
  plume: {
    exitR: M.MOTOR.exitD / 2, zDef: PAD_TOP + 4, zPlate: PAD_TOP, def: 60, plate: 150,
    rail: [...polar(GUIDE_AZ, RAIL.r, 0).slice(0, 2), RAIL.half, PAD_TOP + 26, RAIL.z1],
    clamp: [...polar(GUIDE_AZ, RAIL.r, 0).slice(0, 2), 22, PAD_TOP, PAD_TOP + 26],
    bodyR: R + 1.5, length: nz(APEX) - Z.cap0, pcDesign: 2.8,
  },
};

const LABEL_TEXT =
  "The Helios 38 mm rocket on its launch pad, cut away: a three-fin can holding a 38 mm KNSB motor with two BATES grains, a boattail motor cap, the lower body, a coupler sleeve, the main body with its avionics bay (ESP32, BMP280 and an 18650 cell on a sliding deck) and the side-door nose, whose servo latch, ejection springs, packed parachute and Kevlar shock cord show through a window. A launch controller and a ground station with an altimeter dial sit on the board.";
const backSvg = k.figureSvg({ width: W, height: H, label: LABEL_TEXT, body: back, className: "hx-back" }).replace(`viewBox="0 0 ${W} ${H}"`, `viewBox="${CAMS.rest.join(" ")}"`);
const frontSvg = `<svg xmlns="http://www.w3.org/2000/svg" class="iso-svg hx-front" viewBox="${CAMS.rest.join(" ")}" aria-hidden="true"><defs>${defs.join("")}<clipPath id="hx-door-live"><path clip-rule="evenodd" d=""/></clipPath></defs><g class="hx-rocket">${groups.join("")}</g><g class="hx-anim"><g class="hx-flame-fb"><path class="hx-flame-outer" d=""/><path class="hx-flame-core" d=""/></g><g class="hx-door-live"></g><g class="hx-canopy"></g></g></svg>`;
const PARTS = DATA.order.map((id, index) => `<button type="button" class="hx-part" data-part="${id}"><span class="hx-num">${String(index + 1).padStart(2, "0")}</span>${PIECES[id].name}</button>`).join("");
const corners = `<div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig">Fig 1</span><span class="iso-plate-corner" data-corner="title">Helios · how it flies</span><span class="iso-plate-corner" data-corner="readout" data-readout>${(M.LIFTOFF / 1000).toFixed(2)} kg · on the pad</span></div>`;
const controls = `<div class="hx-controls"><button type="button" class="hx-btn hx-launch" data-launch><span class="hx-lamp-ui" aria-hidden="true"></span><span data-launch-label>Launch</span></button><button type="button" class="hx-btn" data-apart>Take apart</button><span class="hx-hint">Pick a part to look inside</span><span class="hx-live" aria-live="polite" data-live></span></div>`;
const stage = `<div class="hx-stage" tabindex="0" role="slider" aria-label="The Helios rocket on its pad. Press L or the Launch button to replay a flight, Space to take it apart, arrow keys to step through the parts, Escape to reset." aria-valuemin="0" aria-valuemax="${DATA.order.length}" aria-valuenow="0" aria-valuetext="On the pad">${backSvg}<canvas class="hx-plume" aria-hidden="true"></canvas>${frontSvg}<canvas class="hx-veil" aria-hidden="true"></canvas></div>`;
const f = flightRows.events;
const caption = `Helios is a 1.15 kg, 65.5 mm rocket printed in five sections that slide together on spigots. Its 38 mm KNSB motor burns two BATES grains for ${flightRows.burn.toFixed(2)} s (${flightRows.impulse.toFixed(0)} N·s, peak ${flightRows.peakF.toFixed(0)} N), leaving the 1.2 m rail at ${f.railV.toFixed(1)} m/s and coasting to about ${f.apogeeH.toFixed(0)} m at T+${f.apogee.toFixed(1)} s. The ESP32 in the bay watches its BMP280: once the pressure has risen for three readings it turns the nose's servo 60°, two springs kick the side door off, and the parachute, tied to a Kevlar cord anchored in the main body, opens for a ${f.touchdownV.toFixed(1)} m/s descent. Numbers come from the flight model in model.mjs: the measured parts, the grain's burn rate from R. Nakka's KNSB data and an assumed drag.`;
const body = `<figure class="iso-figure hx"><div class="iso-plate">${corners}${stage}${controls}</div><figcaption class="iso-legend"><span class="hx-parts">${PARTS}</span><span class="iso-caption">${caption}</span></figcaption></figure>`;

const latheSrc = readFileSync(fileURLToPath(SKILL + "kit/lathe.mjs"), "utf8").replace(/^import .*$/m, "").replace(/^export /gm, "");
const LATHE = `const G = (() => {\n${latheSrc}\nreturn { frameOf, frameAlong, pointOf, radialOf, solidOf, lathe, prismOf, disc, arcOf, circleOf, sphereOf, dot3, add3, sub3, mul3, unit3, cross3, len3, viewOf, scaleOf, stepsFor };\n})();\n`;
const CSS = readFileSync(join(HERE, "helios.css"), "utf8");
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));
// Fig 2 runs in its own module script: the 3D mode's runtime and its loop stay out of Fig 1's scope
const FIG2 = buildFig2({ theme: THEME });
const fig2Script = `<script type="module">${FIG2.script.replace(/<\/(script)/gi, "<\\/$1")}</script>`;
const page = k.pageHtml({ title: "Helios · how it flies", theme: THEME, body: `<style>${CSS}${FIG2.css}</style>${body}${FIG2.html}${fig2Script}`, script: kitScript() + LATHE + glScript() + LIVE, width: 860 });
const file = THEME === "light" ? "helios-light.html" : "helios.html";
writeFileSync(join(HERE, file), page);
console.log("wrote", file, `${(page.length / 1024).toFixed(0)} KB`, `${items.length} items`);
A.auditOrExit(REC, P);
