// Fig 2 · the latch, turning. The servo latch at the foot of Helios's side door, set on a turntable and
// drawn in the kit's 3D mode: every part is re-projected and re-shaded each frame. Drag it round; Unlatch
// turns the servo 60°, which swings its arm down out of the door block's groove, and the two springs push
// the block off the split plate.
//
//   node fig2.mjs [--light]            writes fig2.html, a standalone page for checks
//   node fig2.mjs --audit [--quick]    kit audit, then the orbit audit
//
// Coordinates are the nose frame of nose.json: millimetres, z up from the foot of the shoulder, x toward
// the door. The springs' pins are left out: they sit inside the coils, and the 3D mode only draws convex parts.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SKILL = "file:///C:/Users/Pedro/.claude/skills/anatomy/";
const k = await import(SKILL + "kit/iso-kit.mjs");
const G = await import(SKILL + "kit/lathe.mjs");
const A = await import(SKILL + "kit/audit.mjs");
const { turning } = await import(SKILL + "kit/turn-build.mjs");
const TA = await import(SKILL + "kit/turn-audit.mjs");
const { turnScript } = await import(SKILL + "scripts/inline-kit.mjs");

const HERE = dirname(fileURLToPath(import.meta.url));
const N = JSON.parse(readFileSync(join(HERE, "nose.json"), "utf8"));
const SV = N.servo;
const argv = process.argv.slice(2);

export const W = 640;
export const H = 500;
const AZ = 38;
const EL = 26;
const R = N.R;
const RR = R - 0.05;
const PLINTH = { r: 52, z0: -16, z1: -6 };
const BEARING = { r: 38, z0: -6, z1: -4 };
const PLATTER = { r: 41, z0: -4, z1: 0 };
const ZS = SV.z_shaft;
const CLEAR = N.NOSE_DOOR_CLEARANCE;
const SPRING_Y = N.NOSE_DOOR_SPRING_Y;
const SPRING_Z = N.z_d0 + N.NOSE_DOOR_SPRING_Z;
const CLOSED = N.pocket_bottom_x + CLEAR;            // 11.4 mm between the split plate and the pocket floor
export const KICK = N.SPRING_FREE_LEN - CLOSED;      // 8.6 mm of push before the springs are spent
export const OUT = KICK + 5;                         // the block coasts on once they are
const COILS = 8;

const ring = (r, z, n = 24) => Array.from({ length: n }, (_, i) => [r * Math.cos((i / n) * 2 * Math.PI), r * Math.sin((i / n) * 2 * Math.PI), z]);
export const P = k.fitProjection([...ring(PLINTH.r + 3, PLINTH.z0 - 2), ...ring(R + 2, 52), [R + OUT, 0, 48]], W, H, { pad: 22, azimuth: AZ, elevation: EL });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const frameOf = (o, a, u) => {
  const axis = G.unit3(a);
  const uu = G.unit3(G.sub3(u, G.mul3(axis, G.dot3(u, axis))));
  return { o, a: axis, u: uu, v: G.cross3(axis, uu) };
};
const VERT = (x = 0, y = 0) => frameOf([x, y, 0], [0, 0, 1], [1, 0, 0]);
const UP = { o: [0, 0, 0], a: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] };
const ALONG_X = { o: [0, 0, 0], a: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1] };

export const REC = A.recorder(P);
const put = (item) => REC.put({ ...item, shapes: item.shapes.map((shape, index) => REC.solid(Object.assign(shape, { name: shape.name ?? (index ? `${item.name}#${index + 1}` : item.name) }))) });

// --- the turntable: static plinth and bearing, a live platter -------------------------------------------
function plinth() {
  // the knurl runs between two grooves; the scale's ticks run between two rings
  const knurlBand = L(k.knurl(0, 0, PLINTH.r, PLINTH.z0 + 3, PLINTH.z1 - 3, 180, P, 0), { tone: "lo" }) + L(k.sideArc(0, 0, PLINTH.r, PLINTH.z0 + 3, P, 120) + k.sideArc(0, 0, PLINTH.r, PLINTH.z1 - 3, P, 120), { tone: "lo" });
  const ticks = k.radialTicks(0, 0, PLINTH.r - 1.2, 72, 6, PLINTH.z1, [2.4, 2.4], P);
  const scale = L(ticks.minor, { tone: "lo" }) + L(ticks.major, { tone: "mid" }) + L(k.ring(0, 0, PLINTH.r - 1.2, PLINTH.z1, P, 144) + k.ring(0, 0, PLINTH.r - 3.6, PLINTH.z1, P, 144), { tone: "lo" });
  const svg = S(k.cylinder(0, 0, PLINTH.r + 3, PLINTH.z0 - 2, 2, P, 120), { tone: "lo" }) + S(k.cylinder(0, 0, PLINTH.r, PLINTH.z0, PLINTH.z1 - PLINTH.z0, P, 120, 0.8), { tone: "mid", inner: knurlBand }) + scale;
  put({ name: "stand.plinth", layer: "back", at: [0, 0, PLINTH.z0], svg, shapes: [A.cylinder(0, 0, PLINTH.r + 3, PLINTH.z0 - 2, 2, { ground: true }), A.cylinder(0, 0, PLINTH.r, PLINTH.z0, PLINTH.z1 - PLINTH.z0)] });
  put({ name: "stand.bearing", layer: "back", at: [0, 0, BEARING.z0], svg: S(k.cylinder(0, 0, BEARING.r, BEARING.z0, BEARING.z1 - BEARING.z0, P, 96), { tone: "lo" }), shapes: [A.cylinder(0, 0, BEARING.r, BEARING.z0, BEARING.z1 - BEARING.z0)] });
  // the index the platter's scale is read against, on the plinth's front
  const a = (AZ * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  const wedge = [[PLATTER.r + 1.4, -0.8], [PLATTER.r + 1.4, 0.8], [PLATTER.r + 6.5, 2.6], [PLATTER.r + 6.5, -2.6]].map(([r, t]) => [c * r - s * t, s * r + c * t]);
  put({ name: "stand.index", layer: "back", at: [c * (PLATTER.r + 4), s * (PLATTER.r + 4), PLINTH.z1], svg: `<g data-mat="brass">${S(k.extrude(wedge, PLINTH.z1, 1.4, P, { bevel: 0.3 }), { tone: "hi" })}</g>`, shapes: [A.extruded(wedge, PLINTH.z1, 1.4)] });
}

export const T = turning(P, { recorder: REC });
const spin = T.group("spin", { turn: { pivot: [0, 0] } });
const arm = T.group("arm", { parent: spin, hinge: { point: [0, 0, ZS], axis: [1, 0, 0], range: [-60, 0] } });
const door = T.group("door", { parent: spin, slide: { direction: [1, 0, 0], travel: OUT } });
const coil = {};
for (const side of ["l", "r"]) for (let i = 1; i < COILS; i++) coil[`${side}${i}`] = T.group(`coil.${side}.${i}`, { parent: spin, slide: { direction: [1, 0, 0], travel: (KICK * i) / (COILS - 1) } });
const latch = T.layer("latch");
T.stack(["back", "latch", "front"]);

// figure values → group values: one servo fraction, one door travel; the coils share the spring's stretch
export const follow = (values) => {
  const out = { ...values };
  out.arm = -60 * (values.servo ?? 0);
  out.door = values.door ?? 0;
  const e = Math.min(out.door, 8.6);
  for (const side of ["l", "r"]) for (let i = 1; i < 8; i++) out[`coil.${side}.${i}`] = (e * i) / 7;
  return out;
};
// the release, 5× slower than the servo's 0.1 s so it can be watched: the arm swings down, the springs
// throw the block, it coasts, someone pushes it home, the servo turns back
export const CLIP_END = 3.4;
export const clipAt = (t) => {
  const s = (a, b, x) => {
    const u = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return u * u * (3 - 2 * u);
  };
  const servo = s(0, 0.5, t) * (1 - s(2.65, 3.15, t));
  const u = Math.min(1, Math.max(0, (t - 0.52) / 0.8));
  const door = 13.6 * (1 - (1 - u) ** 3) * (1 - s(2.0, 2.6, t));
  return { servo, door };
};
export const poses = () => {
  const out = Array.from({ length: 720 }, (_, i) => follow({ spin: i * 0.5 }));
  for (let start = 0; start < 360; start += 30) for (let f = 0; f <= CLIP_END * 30; f++) out.push(follow({ spin: start + f * 0.4, ...clipAt(f / 30) }));
  return out;
};

const L_ = { group: spin, layer: latch };
// platter, with a degree scale on its rim that turns with it
const platter = T.round({ name: "spin.platter", ...L_, F: VERT(), s0: PLATTER.z0, s1: PLATTER.z1, r: PLATTER.r, tone: "mid", crease: "lo" });
{
  const tick = (deg, r0, r1) => {
    const a = (deg * Math.PI) / 180;
    return `M${(Math.cos(a) * r0).toFixed(3)} ${(Math.sin(a) * r0).toFixed(3)}L${(Math.cos(a) * r1).toFixed(3)} ${(Math.sin(a) * r1).toFixed(3)}`;
  };
  const circle = (r) => Array.from({ length: 180 }, (_, i) => `${i ? "L" : "M"}${(r * Math.cos((i / 180) * 2 * Math.PI)).toFixed(3)} ${(r * Math.sin((i / 180) * 2 * Math.PI)).toFixed(3)}`).join("") + "Z";
  const minor = [];
  const major = [];
  for (let d = 0; d < 360; d += 5) (d % 30 ? minor : major).push(tick(d, PLATTER.r - 3.2, PLATTER.r - 0.6));
  const svg = `<path class="iso-line" data-tone="lo" d="${circle(PLATTER.r - 0.6)}${circle(PLATTER.r - 3.2)}"/><path class="iso-line" data-tone="lo" d="${minor.join("")}"/><path class="iso-line" data-tone="mid" d="${major.join("")}"/><path class="iso-line" data-tone="faint" d="${circle(PLATTER.r - 6)}"/>`;
  T.plane({ part: platter, o: [0, 0, PLATTER.z1], u: [1, 0, 0], v: [0, 1, 0], svg, fade: [0.04, 0.3] });
}

// servo plate: the housing's printed plate with a window the servo body passes through
const XS = -CLEAR - N.NOSE_DOOR_SPLIT_PLATE;
const Y_IN = Math.sqrt(N.r_sh_in ** 2 - Math.max(XS * XS, SV.x_seat ** 2)) - 0.2;
const HOLE = { y: 6.1 + N.SERVO_CLEARANCE, z0: SV.z_lo - N.SERVO_CLEARANCE, z1: SV.z_hi + N.SERVO_CLEARANCE };
const PLATE_TOP = N.z_d0 - 0.5;
const plate = (name, y0, y1, z0, z1) => T.prism({ name, ...L_, plan: { x: XS, y: y0, w: SV.x_seat - XS, d: y1 - y0, r: 0.4 }, z: z0, h: z1 - z0, steps: 2, tone: "mid", crease: "lo" });
plate("plate.left", -Y_IN, -HOLE.y, 0, PLATE_TOP);
plate("plate.right", HOLE.y, Y_IN, 0, PLATE_TOP);
plate("plate.top", -HOLE.y, HOLE.y, HOLE.z1, PLATE_TOP);
plate("plate.bottom", -HOLE.y, HOLE.y, 0, HOLE.z0);
// split plate: the wall the springs push from, across the nose at the door's split
const Y_TOP = Math.sqrt((R - N.NOSE_WALL) ** 2 - XS * XS) - 0.2;
T.prism({ name: "plate.split", ...L_, plan: { x: XS, y: -Y_TOP, w: -CLEAR - XS, d: 2 * Y_TOP, r: 0.4 }, z: PLATE_TOP, h: 50 - PLATE_TOP, steps: 2, tone: "mid", crease: "lo" });

// MG90S: body through the window, ears on the plate's face, gear tower, brass spline
const XT = SV.x_bottom + N.SERVO_BODY_H;
const rect = (y0, y1, z0, z1) => [[y0, z0], [y1, z0], [y1, z1], [y0, z1]];
const body = T.prism({ name: "servo.body", ...L_, F: ALONG_X, polygon: rect(-6.1, 6.1, SV.z_lo, SV.z_hi), s0: SV.x_bottom, s1: XT, round: 0.8, steps: 3, bevel: 0.3, tone: "hi", crease: "lo", material: "gunmetal", details: { seams: [SV.x_bottom + 3.2, XT - 2.4] } });
T.plane({ part: body, o: [2.2, 6.1, (SV.z_lo + SV.z_hi) / 2], u: [-1, 0, 0], v: [0, 0, -1], normal: [0, 1, 0], svg: `<text class="iso-face-text" data-tone="lo" font-size="2.6" text-anchor="middle" transform="translate(0 0.9)">MG90S</text>`, fade: [0.05, 0.35] });
const EAR = (N.SERVO_EAR_SPAN - N.SERVO_BODY_L) / 2;
for (const [name, z0, z1] of [["servo.ear.lo", SV.z_lo - EAR, SV.z_lo], ["servo.ear.hi", SV.z_hi, SV.z_hi + EAR]]) {
  const zh = SV.z_holes.find((z) => z > z0 && z < z1);
  T.prism({ name, ...L_, F: ALONG_X, polygon: rect(-6.1, 6.1, z0, z1), s0: SV.x_seat, s1: SV.x_seat + N.SERVO_EAR_T, steps: 2, tone: "hi", crease: "lo", material: "gunmetal" });
  T.round({ name: `${name}.screw`, ...L_, F: frameOf([SV.x_seat + N.SERVO_EAR_T, 0, zh], [1, 0, 0], [0, 0, 1]), s0: 0, s1: 0.9, r: 1.6, tone: "mid", material: "steel", details: { rules: [{ points: [[0.9, -1.6, 0], [0.9, 1.6, 0]], tone: "lo" }] } });
}
T.round({ name: "servo.tower", ...L_, F: frameOf([XT, 0, ZS], [1, 0, 0], [0, 0, 1]), s0: 0, s1: 2.5, r: 5.8, tone: "hi", crease: "lo", material: "gunmetal" });
T.round({ name: "servo.spline", ...L_, F: frameOf([XT + 2.5, 0, ZS], [1, 0, 0], [0, 0, 1]), s0: 0, s1: SV.x_horn - 0.9 - XT - 2.5, r: 2.4, tone: "mid", material: "brass" });
// the horn: a hub on the spline and one arm, standing up in the door block's groove when latched
const X0 = SV.x_horn - 0.9;
const X1 = SV.x_horn + 0.9;
T.round({ name: "arm.hub", group: arm, layer: latch, F: frameOf([X0, 0, ZS], [1, 0, 0], [0, 0, 1]), s0: 0, s1: X1 - X0, r: 3.5, tone: "hi", crease: "lo", details: { dots: [{ at: [X1 - X0, 0, 0], normal: [1, 0, 0], size: 0.5, tone: "mid" }] } });
const ARM_F = { o: [0, 0, ZS], a: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1] };
T.prism({ name: "arm.blade", group: arm, layer: latch, F: ARM_F, polygon: [[-2.25, 3.5], [2.25, 3.5], [1.55, N.SERVO_ARM], [-1.55, N.SERVO_ARM]], s0: X0, s1: X1, steps: 2, bevel: 0.2, tone: "hi", crease: "lo", lit: true, details: { dots: [7, 10, 13].map((v) => ({ at: [X1, 0, v], normal: [1, 0, 0], size: 0.45, tone: "mid" })) } });

// door block: the foot of the door, a circular segment of the nose cut by the groove the arm stands in
// and the two spring pockets, built from convex slices
const G0 = N.NOSE_DOOR_GROOVE_R - N.NOSE_DOOR_GROOVE_W / 2;
const G1 = N.NOSE_DOOR_GROOVE_R + N.NOSE_DOOR_GROOVE_W / 2;
const GY = N.NOSE_DOOR_GROOVE_LEN / 2;
const PH = N.NOSE_DOOR_SPRING_POCKET_D / 2;
const XP = N.pocket_bottom_x;
const Z = { a: N.z_d0, b: SPRING_Z - PH, c: N.z_d0 + N.NOSE_DOOR_GROOVE_H, d: SPRING_Z + PH, e: N.z_f };
// the part of the disc of radius RR with xa ≤ x ≤ xb and ya ≤ y ≤ yb, as a convex polygon
function slice(xa, xb, ya = -Infinity, yb = Infinity) {
  const chord = (x) => Math.sqrt(Math.max(0, RR * RR - x * x));
  const inside = (x, y) => x >= xa - 1e-9 && x <= xb + 1e-9 && y >= ya - 1e-9 && y <= yb + 1e-9 && x * x + y * y <= RR * RR + 1e-6;
  const cand = [];
  for (let i = 0; i <= 720; i++) {
    const a = -Math.PI / 2 + (i / 720) * Math.PI;
    cand.push([RR * Math.cos(a), RR * Math.sin(a)]);
  }
  for (const y of [ya, yb]) if (Number.isFinite(y)) for (const x of [xa, xb]) cand.push([x, y]);
  for (const x of [xa, xb]) for (const s of [-1, 1]) cand.push([x, s * chord(x)]);
  for (const y of [ya, yb]) if (Number.isFinite(y) && Math.abs(y) < RR) for (const s of [-1, 1]) cand.push([s * Math.sqrt(RR * RR - y * y), y]);
  const keep = cand.filter(([x, y]) => inside(x, y));
  // the convex hull of the corners and a fine arc, then thinned
  keep.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [];
  for (const p of keep) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 1e-9) lower.pop();
    lower.push(p);
  }
  const upper = [];
  for (const p of [...keep].reverse()) {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 1e-9) upper.pop();
    upper.push(p);
  }
  return thin([...lower.slice(0, -1), ...upper.slice(0, -1)]);
}
// keep every corner and thin the arc so a slice has at most 16 vertices: the 3D mode's plane search
// samples each part at 32 points, and a part with more drops points it needs
function thin(hull) {
  const onArc = (p) => Math.abs(Math.hypot(p[0], p[1]) - RR) < 1e-6;
  const corner = (i) => {
    const p = hull[i];
    const prev = hull[(i - 1 + hull.length) % hull.length];
    const next = hull[(i + 1) % hull.length];
    return !(onArc(p) && onArc(prev) && onArc(next));
  };
  const corners = hull.filter((_, i) => corner(i)).length;
  let arc = 0;
  for (let i = 0; i < hull.length; i++) {
    const q = hull[(i + 1) % hull.length];
    if (onArc(hull[i]) && onArc(q)) arc += Math.hypot(q[0] - hull[i][0], q[1] - hull[i][1]);
  }
  const spacing = arc / Math.max(1, 16 - corners);
  const out = [];
  let walked = Infinity;
  for (let i = 0; i < hull.length; i++) {
    const p = hull[i];
    const prev = hull[(i - 1 + hull.length) % hull.length];
    if (!corner(i)) {
      walked += Math.hypot(p[0] - prev[0], p[1] - prev[1]);
      if (walked < spacing) continue;
    }
    walked = 0;
    out.push(p);
  }
  return out;
}
const DB = { group: door, layer: latch, tone: "hi", crease: "lo", steps: 2 };
const block = (name, poly, z0, z1) => T.prism({ name, ...DB, F: UP, polygon: poly, s0: z0, s1: z1 });
const XA = CLEAR;
// the block is cut away on the +y side below the pockets' roof, so the arm in its groove and one
// spring in its pocket show as the platter turns
// A: under the pockets, cut by the groove
block("door.a1", slice(XA, G0, -Infinity, 0), Z.a, Z.b);
block("door.a2", slice(G0, G1, -Infinity, -GY), Z.a, Z.b);
block("door.a3", slice(G1, RR, -Infinity, 0), Z.a, Z.b);
// B: the pockets and the groove
block("door.b1", slice(XA, XP, -(SPRING_Y - PH), 0), Z.b, Z.c);
block("door.b2", slice(XA, XP, -Infinity, -(SPRING_Y + PH)), Z.b, Z.c);
block("door.b3", slice(XP, G0, -Infinity, 0), Z.b, Z.c);
block("door.b4", slice(G0, G1, -Infinity, -GY), Z.b, Z.c);
block("door.b5", slice(G1, RR, -Infinity, 0), Z.b, Z.c);
// C: the pockets' tops, over the groove's roof
block("door.c1", slice(XA, XP, -(SPRING_Y - PH), SPRING_Y - PH), Z.c, Z.d);
block("door.c2+", slice(XA, XP, SPRING_Y + PH, Infinity), Z.c, Z.d);
block("door.c2-", slice(XA, XP, -Infinity, -(SPRING_Y + PH)), Z.c, Z.d);
block("door.c3", slice(XP, RR), Z.c, Z.d);
// D: the floor's top
block("door.d", slice(XA, RR), Z.d, Z.e);

// springs: each coil is a short steel round in its own slide, so the stack stretches as the block leaves
const PITCH = CLOSED / COILS;
for (const [side, y] of [["l", -SPRING_Y], ["r", SPRING_Y]]) {
  for (let i = 0; i < COILS; i++) {
    const group = i === 0 ? spin : coil[`${side}${i}`];
    T.round({ name: `spring.${side}.${i}`, group, layer: latch, F: frameOf([-CLEAR + i * PITCH, y, SPRING_Z], [1, 0, 0], [0, 0, 1]), s0: 0, s1: PITCH, r: N.SPRING_OD_MAX / 2, tone: "mid", crease: "lo", material: "steel", details: { seams: [PITCH / 2] } });
  }
}

export function buildFig2({ theme = "dark", verify = false } = {}) {
  plinth();
  const out = T.build({ statics: REC.items, poses, verify });
  A.settle(REC, P);
  const layerOf = (name) => REC.items.filter((item) => item.layer === name).sort((a, b) => a.key - b.key).map((item) => item.svg);
  const BACK = [`<path class="iso-halo" d="${k.haloOf({ x: -PLINTH.r, y: -PLINTH.r, w: 2 * PLINTH.r, d: 2 * PLINTH.r, r: PLINTH.r }, PLINTH.z0 - 2, 2, P)}"/>`, ...layerOf("back")];
  const FRONT = layerOf("front");
  const LABEL = "The servo latch at the foot of Helios's side door, on a turntable: the housing's servo plate and split plate, an MG90S servo with its horn arm standing in the groove of the door's floor block, and the two springs in their pockets between the split plate and the block.";
  const backSvg = k.figureSvg({ width: W, height: H, label: LABEL, body: BACK });
  const frontSvg = `<svg xmlns="http://www.w3.org/2000/svg" class="iso-svg iso-layer" viewBox="0 0 ${W} ${H}" aria-hidden="true">${FRONT.join("")}</svg>`;
  const stage = `<div class="iso-stage iso-turn hx2-stage" tabindex="0" role="slider" aria-label="The door latch on a turntable. Drag or use the arrow keys to turn it; press U or the Unlatch button to release the door." aria-valuemin="0" aria-valuemax="359" aria-valuenow="0" aria-valuetext="latched, 0 degrees">${backSvg}${out.layerSvg("latch", { width: W, height: H })}${frontSvg}</div>`;
  const corners = `<div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig">Fig 2</span><span class="iso-plate-corner" data-corner="title">The latch, turning</span><span class="iso-plate-corner" data-corner="readout" data-readout>servo 0° · latched</span></div>`;
  const controls = `<div class="hx-controls"><button type="button" class="hx-btn" data-unlatch>Unlatch</button><span class="hx-hint">Drag to turn it</span><span class="hx-live" aria-live="polite" data-say></span></div>`;
  const caption = `The door block is cut away on one side to show the latch. The arm on the servo's horn stands ${(N.SERVO_ARM).toFixed(0)} mm tall in a ${N.NOSE_DOOR_GROOVE_W} mm groove under the door's floor block, so the block can't move off the split plate. Turning the servo ${N.SERVO_UNLOCK_ANGLE}° swings the arm down and out of the groove, and the two ${N.SPRING_OD_MAX} mm springs, squeezed to ${CLOSED.toFixed(1)} mm in their pockets, push the block ${KICK.toFixed(1)} mm before they reach their free length of ${N.SPRING_FREE_LEN} mm. Shown five times slower than the servo's 0.1 s; the pins inside the springs are left out.`;
  const html = `<figure class="iso-figure hx hx2"><div class="iso-plate">${corners}${stage}${controls}</div><figcaption class="iso-legend"><span class="iso-caption">${caption}</span></figcaption></figure>`;
  const DATA2 = { turn: out.data, kick: KICK, closed: CLOSED, unlock: N.SERVO_UNLOCK_ANGLE, clipEnd: CLIP_END };
  const FN = `const follow = ${follow.toString()};\nconst clipAt = ${clipAt.toString()};`;
  const live = readFileSync(join(HERE, "fig2.js"), "utf8").replace("__DATA2__", JSON.stringify(DATA2)).replace("const follow = null;", FN);
  const css = out.css + "\n" + readFileSync(join(HERE, "fig2.css"), "utf8");
  return { html, css, script: turnScript() + live, out, verify: out.verify };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const theme = argv.includes("--light") ? "light" : "dark";
  const verify = argv.includes("--verify");
  const fig = buildFig2({ theme, verify });
  const helios = readFileSync(join(HERE, "helios.css"), "utf8");
  const page = k.pageHtml({ title: "Helios · the latch", theme, body: `<style>${helios}${fig.css}</style>${fig.html}`, script: (verify ? `window.__isoVerify = ${JSON.stringify(fig.verify)};\n` : "") + fig.script, width: 700 });
  const name = `fig2${verify ? "-verify" : ""}${theme === "light" ? "-light" : ""}.html`;
  writeFileSync(join(HERE, name), page);
  const r = fig.out.report;
  console.log(`wrote ${name} · ${(page.length / 1024).toFixed(0)} KB · ${r.parts} parts · ${r.layers.map((l) => `${l.name}: ${l.planar} planes, ${l.dynamic} dynamic`).join(" · ")} · build ${r.seconds.toFixed(1)} s`);
  if (argv.includes("--audit")) {
    A.auditOrExit(REC, P);
    TA.orbitOrExit(T, REC, P, {
      sweep: { at: (x) => follow({ spin: x }), from: 0, to: 360, frame: 0.3 },
      clips: [{ name: "unlatch", at: (t) => follow({ spin: 30 + 8 * t, ...clipAt(t) }), from: 0, to: CLIP_END, frame: 1 / 60 }],
      quick: argv.includes("--quick"),
      only: argv.find((a) => a.startsWith("--only="))?.slice(7).split(",") ?? null,
      log: argv.includes("--verbose") ? (text) => console.log(`  … ${text}`) : null,
    });
  }
}
