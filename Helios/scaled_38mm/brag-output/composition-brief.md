# Hyperframes Composition Brief: Canarinho

## Objective
Create a short launch-style brag video for **Canarinho**, a 38 mm 3D-printed high-power
model rocket, cut from four pre-rendered caption-free 3D clips plus type.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080, 30 fps
- Duration: 22.24 seconds

## Source Material
- Project root: `C:/Users/Pedro/Arquivos/Impressoes-3D/Pessoal/fwd3drocketfiles/scaled_38mm`
- Primary files read: `_nose_simple/README.md`, `_avionics/README.md`,
  `__pycache__/rocket_assembly.cpython-311.pyc` (recovered), and the renderer that made
  the footage, `brag-output/render/{stack,shots,nose}.py`
- Product name: **Canarinho**
- Tagline / strongest claim: *Five printed sections. One 983 mm rocket. 0.0001 mm of
  disagreement.*
- Key visual moment to recreate: **nothing needs recreating** — the four clips below ARE
  the product, rendered from the shipped STLs. Do not build HTML/CSS mockups of hardware.
- Copy that must appear verbatim (every number is measured, do not round or invent):
  - `CANARINHO`
  - `983 MM`
  - `5 PRINTED SECTIONS`
  - `4 SPIGOT JOINTS`
  - `26.207 MM OF SPIGOT EACH`
  - `THE BRAIN GOES IN`
  - `ESP32 + BMP280`
  - `56.2 G OF ABS`
  - `105 CHECKS PASS`
  - `ONE SERVO. ONE BAR. 30°.`
  - `100°`
  - `762 MM CANOPY`
  - `ONE ROCKET.`
  - `244 STATIONS CHECKED · MAX ERROR 0.0001 MM`

### Footage (already rendered — embed, do not regenerate)
Copy these into `composition/assets/video/` and embed them as video clips:

| File | Duration | Content |
|---|---|---|
| `brag-output/render/clips/stack.mp4` | 9.0s | Five sections exploded, converging, four joints seating aft→forward, ending as one rocket on the diagonal |
| `brag-output/render/clips/bay.mp4` | 4.5s | Mid-body cut away at centreline; blue avionics sled slides aft and seats on the bead |
| `brag-output/render/clips/nose.mp4` | 5.0s | Clamshell nose: closed, bar sweeps 30°, dwell, both halves swing to 100° |
| `brag-output/render/clips/hero.mp4` | 4.0s | Finished 983 mm rocket, one slow orbit, camera continuing exactly from `stack.mp4`'s last frame |

All four are 1920x1080/30fps, share one palette and one lighting rig, and carry **no
burnt-in text**. Two continuity facts to preserve:
- **Scenes 1 and 2 are one continuous take.** `stack.mp4` must play straight through
  0.00→8.74s without a restart, seek jump, or re-entry. Only the type changes at 4.20s.
- **`hero.mp4` begins on `stack.mp4`'s exact camera pose,** so the cut at 18.24s should be
  clean and the rocket must not jump in size or attitude.

## Creative Direction
- Tone preset: `cinematic`
- Creative direction: engineering-trailer — hardware in the void, big restrained type,
  numbers treated as drama. A launch-vehicle reveal, not a maker vlog.
- Interpretation: wide framing, few words per scene held long, dramatic wipes and slow
  crossfades over hard cuts (except the one beat-locked hard cut at 8.74s), no jokes, no
  bounce easing. Type is authoritative and still once it lands.
- Angle: A rocket that arrives as a box of parts and leaves as one object. The project's
  obsession is *fit* — every joint a measured spigot, every part verified against the
  exported mesh before printing. So the video is that: parts converging and locking, then
  two proofs the fit is real (the sled seats in a bore dimensioned for it; the nose opens
  on a hinge recovered from the geometry, not eyeballed), closing on the verification
  residual rather than a marketing claim.
- Hook: a near-empty dark frame, five rim-lit parts drifting nowhere, then `CANARINHO`.
  The viewer doesn't yet know it's a rocket — that's the reason to keep watching.
- Outro / punchline: `ONE ROCKET.` over the finished airframe, then dry and small,
  `244 STATIONS CHECKED · MAX ERROR 0.0001 MM`. The brag is the tolerance.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals, particles, starfields, lens flares, grids
  - Any HTML re-creation or restyling of the hardware
  - Rounding, embellishing, or inventing a number that isn't in the verbatim list

## Visual Identity
Sampled from the renderer that produced the footage
(`brag-output/render/shots.py`), so type and clips share one palette exactly.

- Background: `#16191E` (renderer `BG` = 0.086, 0.098, 0.118) — must match the clips' own
  background so type sits on the same field with no visible letterbox seam
- Text: `#EDF1F6` primary, `#B8BFCC` secondary
- Accent: `#C7B894` — the `conection` sleeve, the only warm part on screen; use it for the
  verification/payoff lines (`105 CHECKS PASS`) and nothing else
- Accent alt: `#D99E61` (latch bar) and `#8CB8D9` (avionics sled) — available if a scene
  needs to tie type to the coloured part it describes
- Display font: heavy condensed grotesque, ALL CAPS, wide letter-spacing.
  **Local/system stack only** (e.g. `"Arial Narrow", "Helvetica Neue Condensed", system-ui`)
  — no network font requests, the render must not depend on the network.
- Body font: monospace for every number (`Consolas, ui-monospace, monospace`) — the
  project's own telemetry-readout look, and it stops digits from shifting mid-animation.
- Visual references from the project: the caption-free renders themselves; the near-black
  field and single warm joint; the telemetry-box aesthetic of `_nose_simple/nose_video.py`.

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary (cumulative start → end):

1. **PARTS IN THE DARK** — 4.20s (0.00→4.20) — `stack.mp4` 0.00–4.20. Parts drifting
   upper-left; `CANARINHO` huge at ~1.64s holding to the cut; `983 MM` at ~2.73s.
2. **FIVE INTO ONE** — 4.54s (4.20→8.74) — same take continues. Four joints seat.
   Three spec lines arrive one at a time upper-right at 4.91 / 6.00 / 7.09s and **all
   three stay on screen** through the last second.
3. **THE BRAIN GOES IN** — 4.50s (8.74→13.24) — `bay.mp4`. Title slams on the cut;
   `ESP32 + BMP280` and `56.2 G OF ABS`; `105 CHECKS PASS` in accent as the sled seats.
4. **ONE SERVO, ONE BAR** — 5.00s (13.24→18.24) — `nose.mp4`. `ONE SERVO. ONE BAR. 30°.`
   while still shut; `100°` at 15.84s mid-swing; `762 MM CANOPY` at ~17.47s. Type must
   never run ahead of the mechanism.
5. **ONE ROCKET.** — 4.00s (18.24→22.24) — `hero.mp4`. `ONE ROCKET.` slams at 18.56s and
   holds; `244 STATIONS CHECKED · MAX ERROR 0.0001 MM` at 20.19s holds to the end.

Total: 4.20 + 4.54 + 4.50 + 5.00 + 4.00 = **22.24s**.

### Type placement (measured, not estimated)
The clips render on a flat `#16191E` field, so thresholding each frame against that
colour yields the exact pixel box the hardware occupies. These are the **union over
every frame the type is on screen** — worst case, not a sampled guess:

| Clip / window | Occupied rows | Rows left free |
|---|---|---|
| `stack.mp4` f0–135 (scene 1) | 250–725 | 0–249, 726–1079 |
| `stack.mp4` f126–269 (scene 2) | 324–726 | 0–323, 727–1079 |
| `bay.mp4` all | 356–791 | 0–355, 792–1079 |
| `nose.mp4` f78–149 | 240–839 | 0–239, 840–1079 |
| `hero.mp4` all | 332–722 | 0–331, 723–1079 |

The practical consequence: **in every scene the subject owns the middle of the frame and
the type belongs in the top band and on the floor**, not in corners. Two earlier
assumptions were wrong and are corrected here — the rocket is much closer to horizontal
than diagonal, so there is no clear lower-left corner in scene 5; and the parts in scene 1
reach row 725, so `CANARINHO` cannot sit in the lower-right.

Per scene:
- **Scene 1:** the parts fill 250–725 and span x 289–1809, so the only place a 176px title
  fits is the top band. `983 MM` and its rule go to the floor.
- **Scene 2:** the rocket never rises above row 324; the three specs sit in the top-right.
- **Scene 3:** the cutaway tube spans 356–791 across the full width. Title and rule above,
  data below — but the floor band is only 288px tall, so the data rows are smaller here
  than in scene 2. Keep type off the bore so the sled is visible for its whole travel.
- **Scene 4:** the only scene where the safe area *changes mid-shot*, because the subject
  does. Closed, the nose is a full-height column at x 584–1531; once the halves swing, the
  tip clears the top and rows 0–239 / 840–1079 open completely. So `ONE SERVO. ONE BAR. 30°.`
  uses the **left rail** while the nose is shut, and `100°` / `762 MM CANOPY` — which only
  appear from clip frame 78 (t=15.84s), after the tip has dropped — take the top band and
  the floor. Note that the `100°` slam time and the frame the top band opens are the same
  frame; that is the scene working, not a coincidence to be nudged.
- **Scene 5:** rows 332–722 across x 228–1746. Title in the top band, closing stat on the
  floor, rocket framed between them — the same split as scene 4's release.

## Audio
- Audio role: cinematic support — a quiet ~8s build under the hook, then weight.
- Audio arc: sparse and cold under the drifting parts; the first real hit lands on the cut
  into the avionics bay and the bed carries full weight through the install; drops to
  near-silence for the nose's dwell so the release is the loudest moment in the video; one
  announcement hit on the final rocket, then fade to nothing under the tolerance number.
- Music: `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`
  (109.96 BPM, 117.36s source). Chosen because it is the slowest bundled track and its
  first strong cue is at 8.74s, so the opening is genuinely sparse rather than cheerful.
- Music treatment: start at 0.0, bed around 0.30–0.38, slightly up from the 8.74s hit,
  small dip through the nose dwell (~15.0–15.6s), then fade out across the final ~1.2s
  (≈21.0→22.24s) so the closing tolerance line lands in near-silence. Let the final SFX
  ring past the music fade.
- Music cue guidance: preset read from
  `assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`.
  **Exactly three strong-cue locks** (±0.15s):
  - **8.74s** (intensity 0.985) — hard cut to `bay.mp4` + `THE BRAIN GOES IN` slam
  - **15.84s** (0.960) — `100°` slam as the nose halves fly
  - **18.56s** (0.992) — `ONE ROCKET.` slam

  **Beat grid** (±0.10s), every *other* beat for readable text — the grid is ~0.55s apart
  and that outruns reading:
  - scene 2 spec lines at **4.91 / 6.00 / 7.09s**
  - scene 5 closing stat at **20.19s**

  Non-text accents (joint flashes, rule wipes) may use every beat: 4.39, 4.91, 5.34, 6.00,
  6.56, 7.09, 8.19. Other strong cues exist at 9.29, 10.93, 12.55, 13.11, 13.64, 17.47,
  19.66, 22.37 — 17.47 (0.995) is a good non-locked snap for `762 MM CANOPY`.
- Audio-reactive treatment: **subtle**. Drive the **rim-light intensity over the hardware
  and the density of the background vignette** from music RMS/bass, so the parts feel lit
  by the track and breathe very slightly. Peak-to-trough must be small enough that the
  viewer notices mood, not mechanism. Absolutely no bars, waveform, particles, strobing,
  or text scaling. Follow the `hyperframes-creative` audio-reactive workflow and let it
  locate its own extraction helper; ffmpeg **and** ffprobe are on PATH at
  `~/.local/bin/` (ffmpeg 9.0.1) — if the shell can't see them, `export PATH="$HOME/.local/bin:$PATH"`.
- Audio-coupled moments:
  - Scene 1, `CANARINHO` arrival — one very soft low accent, not a hit
  - Scene 2, four joint arrivals — short dry low impacts, timed to the **footage**, not the
    grid. Exact seat times, computed from the renderer's own easing
    (`start = 0.06 + i*0.15`, window `0.28`, over a 9.0s clip starting at composition
    time 0): **4.41s, 5.76s, 7.11s, 8.46s**. Note two of them already fall on beats
    (4.39, 7.09), and 8.46 sits just before the 8.74 lock — so the joints and the music
    agree without being forced. Because the easing is smootherstep, the perceived lock is
    a few frames *before* each figure; nudge earlier if it reads late, never later.
  - Scene 2, three spec lines — light key/tick accents
  - Scene 3, sled travel → seat — a low sliding presence ending in one firm seat click
  - Scene 3, `105 CHECKS PASS` — small interface tick
  - Scene 4, bar sweep — small servo/interface movement; then **silence through the
    dwell**; then one sharp release as the halves let go: the biggest single sound here
  - Scene 5, `ONE ROCKET.` — one full-weight announcement hit, allowed to ring past the
    music fade. **Nothing at all on the closing stat.**
- SFX selection guidance: sparse and motion-matched, roughly **7–9 hits in 22s, not more**.
  Every hit must correspond to something physically happening. No whooshes on camera
  moves, no riser into every scene, no sound on type that is merely moving. Sound means
  metal or plastic met something, or a number landed. The silence in the nose dwell is
  deliberate — do not fill it. Keep one coherent palette: this is plastic and metal
  meeting, so the impact family fits and the casino family does not.
- SFX analysis guidance: `composition/assets/sfx/sfx-analysis.md` (and `.json`) are copied
  in. Prefer low high-frequency-risk files — the palette is dark and the repeated joint
  hits will expose any harshness.
- Exact SFX choice: Hyperframes should choose filenames, timestamps, density, and volume
  after the visual animation exists. Copy the chosen files into
  `composition/assets/sfx/<family>/`.
- Audio files: music and cue preset are already copied into
  `composition/assets/music/`; SFX analysis into `composition/assets/sfx/`. Music bed
  0.30–0.38, SFX 0.55–0.85, nothing above 0.5 for music. Music on a low track index, each
  overlapping SFX on its own ascending index.

## Hyperframes Instructions
Load the composition-building Hyperframes domain skills — `hyperframes-core` (composition
contract + `data-*` timing), `hyperframes-animation` (motion), `hyperframes-creative`
(design spec, beats, audio-reactive), `hyperframes-keyframes` (seek-safe keyframes), and
`hyperframes-cli` (lint/check/render). /brag is its own workflow: do not enter the
`hyperframes` entry-point intent interview and do not route into its generic promo /
launch-video workflow. Prefer native Hyperframes conventions over anything in `/brag`.

Requirements:
- Show at least one real visual element from the source project — satisfied by the four
  embedded clips, which are rendered from the project's own shipped STLs. **Embed them;
  do not substitute HTML mockups of hardware.**
- Keep all text readable in the final render: short label ~0.8s settled minimum, sentence
  ~0.3s/word. Slam-in then hold is correct; fast-in then gone is not.
- Keep the video within 15-25 seconds (target 22.24s).
- Include the planned music/SFX layer.
- Treat `/brag` audio notes as guidance, not a fixed cue sheet. Choose SFX after the
  visual animation exists.
- Treat music cue metadata as optional timing hints; ignore any cue that hurts
  readability, scene pacing, or the product story.
- Use only the 3 strong-cue locks listed above (8.74 / 15.84 / 18.56), marked
  `// beat-locked`. Snap sequential text to the listed beat-grid times, marked
  `// beat-grid`.
- Use SFX to support motion and interaction; restraint when the edit is already busy.
- Honor the music treatment: dip through the nose dwell, fade out across the last ~1.2s,
  and let the final SFX ring over the fade.
- Wire at least one visual element to per-frame audio data (rim light / vignette density),
  per the `hyperframes-creative` audio-reactive workflow. If extraction is unavailable,
  note it and do not block the render.
- Use local assets only — no network fonts, no CDN runtime, no absolute paths.
- Because scenes 1–2 share one continuous video take, use seek-safe keyframes so the
  video element's `currentTime` is a pure function of composition time; the render seeks
  frame by frame and any play/pause or restart logic will desync it.
- Run `hyperframes check` before render — it is brag's single gate.
