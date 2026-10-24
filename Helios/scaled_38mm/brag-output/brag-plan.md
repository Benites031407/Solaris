# Brag Plan: Canarinho

## What is this app?
Not an app — a **38 mm high-power model rocket** designed entirely in parametric Python
and printed in five sections that spigot together into one 983 mm airframe, with an
ESP32 avionics bay and a servo-released clamshell nose that throws a 762 mm parachute.

## The angle
**A rocket that arrives as a box of parts and leaves as one object.**

The whole project's obsession is *fit* — every joint is a measured spigot, every part is
verified against the exported mesh before it is ever printed. So the video is literally
that: parts floating in the dark, converging, locking. Then two proofs that the fit is
real and not a render: the avionics sled slides into a bore it was dimensioned for, and
the nose opens on a hinge that was recovered from the geometry rather than animated by
eye. The closing number is not a marketing claim, it is the verification residual.

Specific to this project and no other: the numbers are all measured, from
`stack.py`'s 244-station check, `_avionics/README.md`'s 105 checks, and
`_nose_simple/README.md`'s hinge and canopy figures.

## Hook (first 2-3 seconds)
A dark, near-empty frame. Five rim-lit printed sections drifting apart in space, slowly
rotating, going nowhere. Then the word **CANARINHO** arrives. You do not yet know it is
a rocket — the parts read as a disassembled *something*, and the reveal of what they add
up to is the reason to keep watching.

## Key moments (the middle)
- **The four joints seating, aft to forward.** Not one mushy convergence — four distinct
  arrivals, tail → lower body → sleeve → mid body → nose cone, each one a lock you can
  hear. The warm-coloured sleeve at the middle joint is the only non-grey part on screen,
  so the eye knows where to look.
- **The avionics sled sliding into the mid body**, seen through a cutaway of the tube.
  One printed part carrying an ESP32 and a BMP280, 56.2 g of ABS, seating on the bead it
  was dimensioned against. `105 CHECKS PASS`.
- **The clamshell nose releasing.** The servo turns one bar 30°, nothing appears to
  happen for a beat, and then both halves swing 100° and the cone is gone. This is a
  recovered hinge, not a guess: fit residual 4.58e-06 mm.

## Outro / punchline
The finished 983 mm rocket in one slow orbit, filling the diagonal of the frame.
**ONE ROCKET.** Then, small and dry underneath it, the thing an engineer actually cares
about: `244 STATIONS CHECKED · MAX ERROR 0.0001 MM`. The brag is the tolerance.

## User flow worth showing
Not a software flow — a **build** flow, which is the real equivalent here and is shown in
order:
1. **Assemble the airframe** — five printed sections onto four spigots (Scenes 1–2).
2. **Install the avionics** — the sled slides forward into the mid-body bore and seats
   on the bead (Scene 3).
3. **Arm and release recovery** — one servo, one bar, 30°, and the clamshell lets the
   parachute go (Scene 4).

## Tone
- Preset: `cinematic`
- Creative direction: engineering-trailer. Hardware in the void, big restrained type,
  numbers treated as drama. Closer to a launch-vehicle reveal than a maker vlog.
- Interpretation: five scenes of 4–5s, wide framing, few words per scene held long,
  dramatic wipes and slow crossfades rather than cuts, and absolutely no jokes — the
  scale of the claim does the work, and every claim is a measured number.

## Format: landscape — 1920x1080
## Duration: 22.24 seconds

## Visual identity (from the project)
Taken from the renderer that produced every clip (`brag-output/render/shots.py`), so
type and footage share one palette exactly.

- Background: `#16191E` (renderer `BG` = 0.086, 0.098, 0.118)
- Accent: `#C7B894` (the `conection` sleeve — the joint, the only warm part on screen)
- Accent alt: `#D99E61` (the latch bar) and `#8CB8D9` (the avionics sled)
- Text: `#EDF1F6` primary, `#B8BFCC` secondary (matches the ABS grey of the parts)
- Display font: heavy condensed grotesque, ALL CAPS, wide letter-spacing — local/system
  stack only (e.g. Arial Narrow Bold → Helvetica Neue Condensed → system-ui). No
  network fonts.
- Body font: monospace for every number (Consolas → ui-monospace) — the project's own
  telemetry-readout look, and it keeps digits from shifting as they animate.
- Strongest visual element: the rendered hardware itself on the near-black field. The
  frames are deliberately caption-free — type is the cut's job, so nothing competes.

## Share copy (draft)
Designed a 38 mm rocket in Python, printed it in five pieces, and it goes together in
983 mm of one object — the assembly checks out to 0.0001 mm across 244 stations. Nose
opens on one servo turning one bar 30°.

## Audio direction
- Role: cinematic support — a quiet 8-second build under the hook, then weight.
- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3` (109.96 BPM, the
  slowest of the five bundled tracks, and its first strong hit is at 8.74s — so the
  opening is genuinely sparse under the drifting parts instead of cheerful over them).
- Music treatment: start at 0.0, bed at roughly 0.55–0.65 through the assembly, up a
  little from the 8.74s hit, then fade out over the last ~1.2s so the closing tolerance
  line lands in near-silence. The closing bell is 1.48s long, so it decays at 20.00s and
  cannot ring past the 21.04s fade — the last 2.2s is music falling to nothing under the
  tolerance line, which is the better ending anyway.
- Music cue guidance: preset cue file read from
  `assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`.
  **Three strong-cue locks only** (±0.15s): **8.74s** (0.985) cut to the avionics bay,
  **15.84s** (0.960) the `100°` slam as the nose halves fly, **18.56s** (0.992) the
  `ONE ROCKET.` slam. Beat-grid windows for sequential text, using **every other beat**
  because the grid is ~0.55s and that outruns reading: scene 2's three spec lines at
  **4.91 / 6.00 / 7.09s**; scene 5's closing stat at **20.19s**. Non-text accents
  (joint flashes, rule wipes) may use every beat.
- Audio-reactive treatment: subtle. Use music RMS and bass energy for the **rim-light
  intensity on the hardware and the density of the background vignette** — the parts
  should feel like they are lit by the track, breathing very slightly. Nothing that
  reads as a visualiser: no bars, no waveform, no particles, no strobe. Peak-to-trough
  effect should be small enough that a viewer notices the mood, not the mechanism.
- SFX posture: sparse and motion-matched. Roughly 7–9 hits in 22s, not more. Each one
  must correspond to something physically happening on screen.
- Audio-coupled moments: the four joint arrivals in scene 2; the sled seating in scene 3;
  the servo turning and then the two halves letting go in scene 4; the title slams.
- Restraint rule: no whooshes on camera moves, no riser into every scene, no sound on
  anything that is only type moving. Sound means metal or plastic met something, or a
  number landed. Silence during the nose's dwell beat is deliberate — do not fill it.

## Storyboard

Footage is pre-rendered, caption-free, 1920x1080 / 30fps, in `brag-output/render/clips/`:
`stack.mp4` (9.0s), `bay.mp4` (4.5s), `nose.mp4` (5.0s), `hero.mp4` (4.0s).
Scenes 1 and 2 are **one continuous take** — `stack.mp4` plays across the cut without
restarting, and only the type changes.

### Scene 1 — PARTS IN THE DARK — 4.20s
`stack.mp4` from 0.00–4.20s: five printed sections spread apart on the near-black field,
each drifting and slowly rotating, edge-lit. Measured against the actual frames, the parts
fill rows 250–725 and span almost the full width, so the type lives in the top band, not in
a corner. **CANARINHO** arrives at ~1.64s in huge tracked caps and
holds to the cut (2.5s+ of settled read). Beneath it, smaller and monospace, `983 MM`
at ~2.73s. Nothing is named as a rocket yet.
Sequential/interaction: none — one title, one subline.
Audio intent: sparse, cold, and unresolved. Almost nothing. The track's first 8s are
quiet by choice; let the room tone carry it.
Audio-coupled idea: one very soft low accent under the CANARINHO arrival. No hit.
Music: cinematic build, low in the mix.
Transition mood: dramatic → Scene 2 (no cut — the take continues, type wipes through)

### Scene 2 — FIVE INTO ONE — 4.54s
`stack.mp4` continues 4.20–8.74s: the sections converge and seat aft-to-forward, four
joints locking in turn, the camera easing in and the warm sleeve visible at the middle
joint. By ~8.46s it is one rocket lying across the diagonal. Three spec lines arrive one
at a time in the empty upper-right, each holding ~1.09s and **all three still on screen**
through the last second: `5 PRINTED SECTIONS` (4.91s), `4 SPIGOT JOINTS` (6.00s),
`26.207 MM OF SPIGOT EACH` (7.09s).
Sequential/interaction: yes — three spec lines on every other beat (4.91 / 6.00 / 7.09),
then the full set holds. Four joint arrivals are the visual sequence underneath them.
Audio intent: the build resolving into weight. Each joint should land with mass — dry and
mechanical, not cinematic boom.
Audio-coupled idea: a short low impact on each of the four joint seatings, timed to the
footage rather than the grid; light key/tick accents on the three spec lines.
Music: the bed rising into the 8.74s hit.
Transition mood: **hard cut, beat-locked** → Scene 3. This is the video's only hard cut and
it is deliberate: the 8.74s strong cue is the first real hit in the track, and cutting on
it is stronger than wiping through it. Every other transition dips through the shared
background colour instead.

### Scene 3 — THE BRAIN GOES IN — 4.50s
Hard-cut on the **8.74s strong cue** to `bay.mp4` (full 4.5s): the mid-body tube cut away
at its centreline, and the blue avionics sled sliding aft into the bore to seat on the
bead. Title **THE BRAIN GOES IN** slams at the cut. Then two monospace lines under it:
`ESP32 + BMP280` and `56.2 G OF ABS`, and finally `105 CHECKS PASS` in the accent
colour, timed to the moment the sled seats.
Sequential/interaction: yes — the sled's travel *is* the interaction; two data lines
then the checks line, each held to the reading floor.
Audio intent: precision. A part going exactly where it was designed to go.
Audio-coupled idea: a low sliding presence under the travel, ending in one firm seat
click as it lands on the bead; a small interface tick on `105 CHECKS PASS`.
Music: full bed, steady.
Transition mood: slow crossfade → Scene 4

### Scene 4 — ONE SERVO, ONE BAR — 5.00s
`nose.mp4` (full 5.0s): the closed clamshell nose, tip to base. **ONE SERVO. ONE BAR.
30°.** on screen while it is still shut. The bar turns; visibly nothing else happens —
hold that beat, it is the point. Then both halves swing and are thrown wide to 100°.
**100°** slams on the **15.84s strong cue**, mid-swing. `762 MM CANOPY` follows at
~17.47s as the cone finishes opening.
Sequential/interaction: yes — the release is sequenced by the mechanism itself: bar
sweeps → dwell → halves let go. Type follows that order, never ahead of it.
Audio intent: tension then release. The dwell after the servo is the whole scene; it
should be almost silent so the springs winning actually startles.
Audio-coupled idea: a small servo/interface movement on the bar, **silence** through the
dwell, then one sharp release as the halves let go — the biggest single sound in the
video.
Music: bed dips slightly through the dwell, back up on the release.
Transition mood: dramatic → Scene 5

### Scene 5 — ONE ROCKET. — 4.00s
`hero.mp4` (full 4.0s), which picks up exactly where `stack.mp4`'s camera left off: the
finished 983 mm rocket in one slow orbit, nothing moving but the camera. In the rendered
frames it lies close to horizontal — rows 332–722, x 228–1746 — so the title takes the
empty top band and the stat the empty floor, and the rocket is framed between them.
**ONE ROCKET.** slams on the **18.56s strong cue**, 0.32s after the cut.
It holds. At 20.19s, small and monospace beneath it:
`244 STATIONS CHECKED · MAX ERROR 0.0001 MM`, which holds to the end. Music fades out
under it.
Sequential/interaction: none — one slam, one dry closing stat.
Audio intent: arrival, then let it go quiet. The last thing the viewer hears should be
the room, not a button.
Audio-coupled idea: one full-weight announcement hit on `ONE ROCKET.`, decaying over 1.48s
into the music's fade. Nothing at all on the closing stat.
Music: fade out across the final ~1.2s.
Transition mood: hold to black

**Scene durations:** 4.20 + 4.54 + 4.50 + 5.00 + 4.00 = **22.24s** ✓ (15–25s)

**Music mood for this video:** cinematic
**Audio summary:** Eight seconds of sparse, cold build under drifting parts; the first
real hit lands on the cut into the avionics bay and the bed carries full weight through
the install; it drops to near-silence for the nose's dwell so the release is the loudest
moment in the video; then one announcement hit on the final rocket and a fade to nothing
under the tolerance number.
