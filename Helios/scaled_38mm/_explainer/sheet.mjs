// The printable sheet for Fig 1: node C:/Users/Pedro/.claude/skills/anatomy/scripts/print.mjs sheet.mjs --format all --png
// Every number here comes from model.mjs through the built page (caption and readouts).
const piece = (id) => `.it[data-piece="${id}"]`;
const launch = (wait) => [["key", "Escape"], ["wait", 300], ["key", "l"], ["wait", wait]];
const reset = [["key", "Escape"], ["wait", 1500]];

export default {
  page: "helios-light.html",
  out: "helios",
  layers: ".hx > .iso-plate > .hx-stage > svg.hx-back, .hx > .iso-plate > .hx-stage > svg.hx-front",
  rasterSelector: ".hx > .iso-plate > .hx-stage",
  strip: [".hx-controls"],
  reduced: true,
  views: {
    rest: { actions: [["key", "Escape"], ["wait", 800]] },
    apart: { actions: [["key", "Escape"], ["key", " "], ["wait", 1200]], reset: [["key", " "], ["wait", 1200]] },
    // reduced motion plays the flight as stills, 2.6 s each: boost, deployment, canopy
    boost: { actions: launch(900), raster: { region: [-50, -950, 900, 900], scale: 2 }, reset },
    deploy: { actions: launch(3500), reset },
    canopy: { actions: launch(6100), reset },
  },

  name: "Helios",
  title: "Helios: how a 38 mm rocket flies",
  number: "HX-001",
  tagline: "KNSB motor · servo side-door recovery",
  question: "How does a small rocket fly, and bring itself back?",
  lead: "A 38 mm motor burns two grains of potassium nitrate and sorbitol for 1.3 s and throws the 1.15 kg rocket off a 1.2 m rail. It coasts to about 800 m. There a small computer in the main body sees the air pressure start to rise, turns a servo in the nose, and two springs kick a side door open so the parachute can come out.",
  quote: "No ejection charge: a servo and two springs open the nose",
  numbers: [
    ["218", "N·s", "total impulse"],
    ["170", "N", "peak thrust"],
    ["800", "m", "apogee"],
    ["1.15", "kg", "at liftoff"],
    ["6.5", "m/s", "under the canopy"],
  ],
  spec: [
    ["Airframe", "65.5 mm, five printed sections"],
    ["Motor", "38 mm KNSB, 2 BATES grains"],
    ["Burn", "1.3 s, 218 N·s, 170 N peak"],
    ["Rail exit", "16.6 m/s off 1.2 m"],
    ["Apogee", "about 800 m at T+12 s"],
    ["Recovery", "servo side door, 0.76 m canopy"],
    ["Descent", "6.5 m/s"],
  ],
  why: {
    title: "Why a servo door?",
    text: "Most small rockets push their nose off with a powder charge timed from the motor. Helios's ESP32 waits until its barometer shows the rocket has started to fall, then turns a servo, so the parachute opens at the top whatever the motor did, with nothing to burn.",
  },

  parts: [
    { id: "nose", name: "Side-door nose", say: "Holds the servo latch, the springs and the packed parachute.", select: piece("nose") },
    { id: "door", name: "Door", say: "One quarter of the nose; its foot is held by the servo's arm.", select: piece("door") },
    { id: "chute", name: "Parachute", say: "Packed in a bag on a ramp; slides out once the door is gone.", select: piece("chute") },
    { id: "bay", name: "Avionics bay", say: "ESP32, BMP280 barometer and an 18650 cell on a sliding deck.", select: piece("bay") },
    { id: "mbody", name: "Main body", say: "Anchors the Kevlar shock cord and carries the bay.", select: piece("mbody") },
    { id: "coupler", name: "Coupler sleeve", say: "Joins the main body to the lower body on their spigots.", select: piece("coupler") },
    { id: "lower", name: "Lower body", say: "The middle tube, between the coupler and the fin can.", select: piece("lower") },
    { id: "tail", name: "Fin can", say: "Three fins through the wall, around the motor tube.", select: piece("tail") },
    { id: "motor", name: "38 mm KNSB motor", say: "Two BATES grains burning from the core and the ends.", select: piece("motor") },
    { id: "cap", name: "Boattail motor cap", say: "Holds the motor in and tapers the tail.", select: piece("cap") },
    { id: "stand", name: "Launch pad and rail", say: "A 1010 rail, a blast plate, the controller and ground station.", select: piece("stand") },
    { id: "cord", select: piece("cord") },
  ],

  main: { view: "rest", crop: [103, 229.6, 593.9, 742.4] },
  inset: { label: "Taken apart", view: "apart", crop: [-2.2, -7.6, 804.5, 1005.6] },
  steps: [
    { view: "rest", title: "On the rail", text: "The rocket hangs on its two guides on a 1.2 m rail over a blast plate. The igniter leads run from the nozzle to the controller's clips.", focus: ["stand", "motor"] },
    { view: "boost", title: "The grains burn", text: "Both grains burn from their cores and ends at about 2.8 MPa. The motor gives up to 170 N for 1.3 s and the rocket leaves the rail at 16.6 m/s." },
    { view: "rest", title: "The barometer watches", text: "The BMP280 in the bay reads the pressure many times a second. When the altitude has dropped for three readings in a row, the ESP32 knows it is past the top.", focus: ["bay"] },
    { view: "deploy", frame: [230, -1060, 340, 360], title: "The door kicks off", text: "The servo turns 60° and its arm leaves the door's groove. Two springs push the door off and it swings away, and the parachute bag slides out." },
    { view: "canopy", frame: [100, -1400, 600, 1000], title: "Under the canopy", text: "The Kevlar cord, anchored in the main body, catches the canopy. The rocket comes down at about 6.5 m/s." },
  ],
  details: [
    { view: "rest", title: "The latch", text: "A servo arm stands in a groove under the door's floor block. Two springs wait, squeezed to 11.4 mm, behind it.", around: ["door"], focus: ["nose", "door"] },
    { view: "rest", title: "The avionics", text: "The ESP32 and the BMP280 ride on a deck over the 18650 cell.", around: ["bay"], focus: ["bay"] },
    { view: "rest", title: "The motor", text: "Two BATES grains in a 38 mm case, a nozzle with a 7.5 mm throat.", around: ["motor"], focus: ["motor"] },
  ],
};
