const D2 = __DATA2__;
const follow = null;
const fig = document.querySelector(".hx2");
const stage = fig.querySelector(".hx2-stage");
const readout = fig.querySelector("[data-readout]");
const liveText = fig.querySelector("[data-say]");
const unlatchBtn = fig.querySelector("[data-unlatch]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const SPEED = 9;           // degrees per second while touring
const EVERY = 9;           // seconds between releases while touring
let angle = 0;
let target = 0;
let frame = 0;
let last = 0;
let visible = false;
let touring = !still.matches;
let idle = 0;
let drawn = null;
let own = false;
let clip = null;           // { t } while the release plays
let tourClock = 2;
let pose = { servo: 0, door: 0 };

const phaseOf = ({ servo, door }) => {
  if (door > 0.05) {
    const e = Math.min(door, D2.kick);
    return door < D2.kick - 0.05 ? `springs ${(D2.closed + e).toFixed(1)} mm` : `door off · ${door.toFixed(0)} mm out`;
  }
  if (servo < 0.01) return "latched";
  return servo > 0.99 ? "arm clear · free" : "servo turning";
};
const show = () => {
  const deg = Math.round(D2.unlock * pose.servo);
  const text = `servo ${deg}° · ${phaseOf(pose)}`;
  if (readout.textContent !== text) readout.textContent = text;
  const turn = Math.round((((angle % 360) + 360) % 360));
  stage.setAttribute("aria-valuenow", String(turn));
  stage.setAttribute("aria-valuetext", `${phaseOf(pose)}, ${turn} degrees`);
};
const hold = () => {
  touring = false;
  clearTimeout(idle);
  idle = setTimeout(() => {
    touring = !still.matches;
    run();
  }, 3600);
};
const controller = TURN.mount(stage, D2.turn, {
  follow,
  onHold: () => {
    touring = false;
    clearTimeout(idle);
  },
  onFrame: (turned) => {
    if (own) return;
    angle = target = drawn = turned.values.spin ?? angle;
    pose = { servo: turned.values.servo ?? 0, door: turned.values.door ?? 0 };
    show();
  },
});
const draw = () => {
  own = true;
  controller.set({ spin: angle, ...pose });
  own = false;
  drawn = angle;
  show();
};
function release() {
  if (clip) return;
  clip = { t: 0 };
  unlatchBtn.setAttribute("data-on", "");
  if (liveText) liveText.textContent = "unlatching";
  run();
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  if (touring && !calm) {
    target += SPEED * dt;
    tourClock += dt;
    if (tourClock > EVERY) {
      tourClock = 0;
      release();
    }
  }
  angle = calm ? target : angle + (target - angle) * (1 - Math.exp(-dt / 0.12));
  if (Math.abs(target - angle) < 1e-3) angle = target;
  let moved = false;
  if (clip) {
    // reduced motion: hold the released pose for a moment, then put it back, without the motion between
    clip.t += calm ? 0 : dt;
    if (calm) {
      clip.wait = (clip.wait ?? 0) + dt;
      pose = clip.wait < 2.4 ? clipAt(1.6) : clipAt(D2.clipEnd);
      if (clip.wait >= 2.4) clip.t = D2.clipEnd;
    } else pose = clipAt(clip.t);
    moved = true;
    if (clip.t >= D2.clipEnd) {
      clip = null;
      pose = { servo: 0, door: 0 };
      unlatchBtn.removeAttribute("data-on");
      if (liveText) liveText.textContent = "latched";
    }
  }
  if (moved || drawn === null || Math.abs(angle - drawn) > 1e-4) draw();
  const settled = !touring && angle === target && !clip;
  frame = visible && !settled ? requestAnimationFrame(tick) : 0;
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
  else if (frame) {
    cancelAnimationFrame(frame);
    frame = 0;
  }
}, { rootMargin: "120px 0px" }).observe(stage);

let drag = null;
stage.addEventListener("pointerdown", (event) => {
  hold();
  drag = { from: controller.angleAt(event.clientX, event.clientY, 0, "spin"), base: target, id: event.pointerId, captured: false };
});
stage.addEventListener("pointermove", (event) => {
  if (!drag || event.pointerId !== drag.id) return;
  hold();
  const delta = controller.angleAt(event.clientX, event.clientY, 0, "spin") - drag.from;
  if (!drag.captured && Math.abs(delta) > 1.5) {
    drag.captured = true;
    stage.setPointerCapture(event.pointerId);
    stage.setAttribute("data-drag", "");
  }
  if (!drag.captured) return;
  target = drag.base + delta;
  run();
});
const letGo = (event) => {
  if (!drag || event.pointerId !== drag.id) return;
  drag = null;
  stage.removeAttribute("data-drag");
  try {
    stage.releasePointerCapture(event.pointerId);
  } catch {}
};
stage.addEventListener("pointerup", letGo);
stage.addEventListener("pointercancel", letGo);
stage.addEventListener("keydown", (event) => {
  if (event.key === "u" || event.key === "U" || event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    hold();
    release();
    return;
  }
  const step = event.shiftKey ? 45 : 10;
  let next = null;
  if (event.key === "ArrowRight" || event.key === "ArrowUp") next = target - step;
  if (event.key === "ArrowLeft" || event.key === "ArrowDown") next = target + step;
  if (event.key === "Home") next = 0;
  if (next === null) return;
  event.preventDefault();
  hold();
  target = next;
  run();
});
unlatchBtn.addEventListener("click", () => {
  hold();
  release();
});
if (still.matches) touring = false;
draw();
