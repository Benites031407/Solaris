# Helios — avionics bay: ESP32 + BMP280 in the 38 mm body tube

**Two printed parts.** A *support* seats itself on a ring the airframe already
has and is held by two M3 screws through the wall. A *plate* carries the
electronics, is populated on the bench, and then slides into the support from the
forward end, tail first, fully wired. It stops on a plug at the far end and can
only go in one way. There are no bulkheads, no carrier, and no fasteners other
than the same two screws — which now catch both parts at once, so the split added
nothing to the airframe.

    support         _avionics/out/bay_support.step   (also .stl)
                    station 27.31 .. 209.00,  41.2 g in ABS
    plate           _avionics/out/bay_plate.step     (also .stl)
                    station 27.31 .. 204.50 as drawn, 205.00 seated,  18.9 g
    both, seated    _avionics/out/bay_assembly.step  -- for VIEWING only
    mass            60.1 g for the pair, 125.3 g with electronics and the
                    heaviest candidate cell
    verification    87 checks on the numbers, 150 on the exported meshes

---

## The two ideas

### 1. The bead is a datum the airframe already has

The tube has a depth-stop bead 33 mm in: the bore necks from r 31.411 down to
r 29.870 and back out again. Every idea for this bay had the same problem with
it. Anything that must *pass* the bead is capped at r 29.870, and is then
permanently ≥ 1.54 mm clear of the working bore behind it — so the bore cannot
locate it, and you have to add something whose job is to locate it.

A part that **stops** at the bead is not capped by it. The bead's forward flank
is a concave fillet on the thickest ring in the forward tube (2.874 mm of wall
against the plain tube's 1.333). So the support's nose is simply drawn *larger*
than the throat — a D61.20 crown — and left to seat in the fillet:

* it is a **full 360° self-centring radial datum**. The flank scatters only
  0.0074 mm around the azimuth, so the crown meets it as a ring, not at three
  points.
* it is a **reaction face for forward inertia**, taken as hoop compression on
  the strongest ring available.
* it **cannot be lost aft**: the crown overlaps the throat by 0.730 mm.
* it still **withdraws forwards** through the nose socket (r 31.247), clearing
  by 0.647 mm, once the nose is off.
* it **costs nothing** — it is just the outer profile the part already had.

Everything aft of the crown is r 29.450, which passes the throat with 0.420 mm
to spare. That 1.96 mm of radial float between the shell and the bore is
deliberate: the support is located by the crown at the front and by two screws
at the back, and by nothing in between. A 2 mm walled trough over 181 mm does
not need anything in between.

### 2. The deck is a separate part, and it slides

The deck used to be fused into the shell, which meant every wire, every solder
joint and every strap had to be reached down a 55 mm bore past the boards
already in it. It is now its own part, assembled on the bench and inserted as a
unit — and it was **raised 6.0 mm** at the same time, because the space that
matters for working behind it is the closed channel *under* the deck:

    channel area          449.8 -> 750.7 mm2   (+67%)
    depth on centreline    13.45 -> 19.45 mm
    depth at the pin slots 10.34 -> 16.34 mm

The last of those is the one that mattered: 3.5 mm of ESP32 header pin hangs
down into exactly that space. The rise is a measured choice, not the maximum —
every ceiling above the deck was bisected on cross-sections of the real
`Mbody.stl` (`DECK_RISE` in `bay_params.py` lists all five), and 6.0 leaves
1.63 mm to the nearest of them, the screw bosses' x-band. Going to 7.0 would
buy 7% more area and spend 60% of that margin, and this deck now has to *slide*.

---

## How the slide works

The head of the support is a **complete ring**, bore r 27.45, so the plate has
to pass through it. That single fact picks the architecture:

> The rails stand **proud of the bore**, they are not grooves in the wall.
> A groove puts the plate's edges at r > 27.45 — wider than the hole they have
> to pass — and thins a 2.0 mm wall below `WALL_MIN` into the bargain. Rails
> standing inward invert both problems: the plate is *narrower* than the bore
> and the wall is never touched.

| | x band | radial band | stations |
|---|---|---|---|
| lower rail | −10.30 .. −8.30 | r 26.05 .. 27.95 | 27.31 .. 209.0 (full length) |
| **the pocket** | **−8.30 .. −5.70** | **r 26.05 .. 27.45, air** | |
| upper rail | −5.70 .. −3.70 | r 26.05 .. 27.95 | 27.31 .. 188.0 |
| the plate's chord | −8.00 .. −6.00 | out to r 27.05 | 27.31 .. 204.5 |

Read off the two exported meshes, not off the table that drew them:

    pocket width        2.600 mm     (POCKET_X_TOP - POCKET_X_BOT 2.600)
    plate thickness     2.000 mm     (DECK_T 2.000)
    clearance under     0.300 mm     (SLIDE_CLR_X 0.30)
    clearance over      0.300 mm     (SLIDE_CLR_X 0.30)
    radial clearance    0.400 mm     (SLIDE_CLR_R 0.40)
    rail engagement     1.000 mm     (RAIL_ENGAGE 1.00)

The engagement is what makes it a pocket and not a channel: lift the plate
0.40 mm either way in x and it drives 30–42 mm³ into a rail. The upper rail
stops at s 188 because the bosses' x-band reaches |x| ≤ 4.372 and it would
otherwise fuse into both of them; over that last 21 mm the two M3s are what hold
the plate down, which is why they are there.

### It only goes in one way

The pocket is **filled from s 205 to the tail**. The plate runs free up to it
and no further, so it cannot continue and drop out of an aft end that is 209 mm
down a 38 mm tube and unreachable. The stop blocks 7.55 mm² of the pocket's
section; the plate's aft face bears on 4.15 mm² of that, which is 4.44 MPa on
boost against ABS's ~40. Forward retention is the two M3s.

The stop's own forward face is the only new downward-facing surface the slide
adds, and it is deliberately kept inside the rails' radial band so it lands on
the lower rail below it and the shell outboard of it — no point of it is more
than 1.40 mm from one of the two. Drawn across the full chord instead, which
looks stronger, it would bridge some 52 mm of open bore.

---

## Frame

`z` = **station s**, mm aft of the body tube's forward rim, growing aft. This
is Mbody.stl's own direction, so no measured table had to be negated to use it.
The nose's frame relates by `nose_z = 26.2069 − s` (`bay_params.NOSE_Z`).

Azimuth θ: 0 = +x, 90 = +y. θ 0 is where the airframe's shock-cord duct runs.

---

## Station by station

**The support** — head, shell, trough, rails, stop, bosses.

| s | feature |
|---|---|
| 27.31 | forward face — the print's first layer |
| 28.92 | **crown, D61.20** — seats in the bead's forward flank |
| 30.60 | head ends, trough opens (everything forward of here is a complete ring) |
| 27.31 – 209.0 | lower rail, x −10.30 .. −8.30 |
| 27.31 – 188.0 | upper rail, x −5.70 .. −3.70 |
| 189 – 209 | two screw bosses at θ 90 and 270, ramping in from the wall |
| 201.5 | **two D2.5 pilots for M3 self-tappers** |
| 205 – 209 | **the aft stop** — the pocket filled, the one-way part |
| 209.0 | aft face, 4.5 mm forward of where the tube's aft taper starts |

**The plate** — deck, ribs, slots, lugs. Its x band is −8.00 .. −6.00 except
where a feature stands off it.

| s | feature |
|---|---|
| 27.31 | forward face, flush with the support's — reachable with a fingernail |
| 36 – 64 | BMP280 between two ribs at y ±10.5, 2.5 mm tall |
| 43, 49, 55 | three D2.5 static ports on the centreline, into the closed channel under the deck |
| 50 | BMP280 cable-tie slots, y ±13.0 |
| 66, 193 | four D5.0 deck vents at y ±20 |
| 68 – 126 | two 3.6 mm pin slots at y ±12.7 — the ESP32's header pins hang through, 5.6 mm of drop for 3.5 mm pins |
| 69 – 123.4 | ESP32 cell, 6.6 × 27.9 × 54.4 mm (the slots run 68 – 126, wider than the board) |
| 78, 112 | ESP32 cable-tie slots, y ±18.0 |
| 128 – 193.2 | battery cell, 18.6 × 30.0 × 65.2 mm — **bare deck**, no features |
| 140, 185 | battery cable-tie slots, y ±18.0 |
| 197.5 – 204.5 | **two screw lugs**, x −6.50 .. +3.00, y ±16 .. ±22 |
| 201.0 | the lugs' D2.5 pilots — drawn 0.5 mm forward of the bosses' 201.5 **on purpose** |
| 204.5 | aft face, 0.5 mm short of the stop as drawn |

The trough is open towards θ 0 over ±82°, which is a plane cut at x = 4.0 rather
than a radial one. That is what clears the cord duct — see *Installation*.

The shock cord never enters the bay. The airframe's duct is a **closed channel**
with its own wall (three closed loops in a cross-section, not two), so the
~253 N chute snatch is reacted by the tube and is structurally isolated from the
electronics for free.

### Why the plate is drawn 0.5 mm short of home

`bay_plate.py` draws the plate at s 27.31..204.5 and the stop's face is at
205.0, so the part as drawn sits `SLIDE_GAP_Z` forward of where it ends up.
That is what makes the two pilots a *check* rather than a coincidence:
`S_LUG_PILOT` is `S_SCREW − SLIDE_GAP_Z`, so the lug's pilot lines up with the
boss's **only after the plate has slid home**. A plate that is not seated
cannot be screwed down, and `bay_assembly.py` drives a 2.3 mm probe down the
screw's axis through both solids at once to prove it.

---

## What to buy

| qty | item | why this size |
|---|---|---|
| 2 | **M3 × 16 self-tapping screw**, pan head | 1.34 mm of airframe + 1.96 mm of air + 6.45 mm of boss + 1.00 mm of air = 10.74 mm under the head *before it reaches the lug*. It then forms 5.26 mm of thread in the lug — 1.8 diameters — and stops 0.74 mm short of breaking through into the trough. |
| ~8 | 2.5 mm cable ties | slots are 5.0 mm along the tube × 2.5 mm across |
| 1 | ESP32 dev board | budgeted at 54.4 × 27.9 mm, 5.0 mm above the PCB, 3.5 mm of header below |
| 1 | BMP280 breakout | budgeted at 26.0 × 18.5 × 4.0 mm |
| 1 | battery | **not chosen yet** — see below |

An M3 × 12 was enough when the support was the only thing being retained, and it
*does* still reach the lug — but with only 1.26 mm left to thread, which is why
`SCREW_L` is 16. Pilots are D2.5 for M3 self-tappers in ABS; do not drill them
out. The thread forms in the 6.45 mm of boss behind the wall and again in the
6.0 mm of lug behind that, and both are sized for it.

### The battery

The bay does not need to know which battery you use, which is the point. The
aft 65 mm of deck is bare, with two cable-tie slot pairs and nothing else. The
keep-out was drawn as the union of four candidates:

    length   65.2 mm   (18650 sets this)
    width    30.0 mm   (a 2S 850 mAh LiPo pack sets this)
    height   18.6 mm   (18650 sets this)

Anything inside that envelope drops in and straps down with no change to either
part. The mass allowance is 48 g. If you pick something heavier, or outside the
envelope, re-run `python bay_plate.py` — `M_BATT_WORST` in `bay_params.py` feeds
the load case and every module asserts its own margin, so it will tell you
rather than let the number go stale.

---

## Build, verify, view

```bash
cd _avionics

python bay_params.py                  # 87 checks on the numbers
python bay_support.py                 # the support, asserts its own mass
python bay_plate.py                   # the plate, asserts its own mass
python bay_assembly.py                # THE PAIR: the slide, the stop, capture,
                                      # the screw path, the loads

PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \
    -o out/bay_support.step --stl bay_support.stl bay_support.py
PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \
    -o out/bay_plate.step --stl bay_plate.stl bay_plate.py
PYTHONIOENCODING=utf-8 python ~/.claude/skills/cad/scripts/step \
    -o out/bay_assembly.step bay_assembly.py        # viewing only, do not print

python bay_verify.py                  # 150 checks on the EXPORTED meshes
```

The exporter also drops a `.glb` beside each `.step` (hidden, `.bay_*.step.glb`)
if you want to look at one in a viewer.

Each script answers a different question and none of them is redundant:

* `bay_support.py` and `bay_plate.py` check themselves against the numbers that
  built them, and each asserts its own mass so a part cannot change weight while
  the load case quotes the old one.
* `bay_assembly.py` is the only place that can see **both solids at once**: the
  support intersected with the plate's swept envelope over the whole travel
  (ribs and lugs and all), the plate driven *past* the stop, the plate lifted
  out of the pocket, and a probe down the screw axis through both parts.
* `bay_verify.py` is the one that matters. It loads the exported STLs and the
  airframe back in and asks whether the parts actually go down the tube — full
  insertion sweeps at every depth from 215 mm out to home, not just the
  assembled position. It also caught the only real defect in this design (see
  its docstring), and it is the only file that measures the slide's clearances
  on the *meshes* rather than trusting the parameters.

A note on what a mesh sweep can resolve: the sweep's grid is 2.5° of azimuth and
0.5 mm of station, which is ample for a 1.96 mm support-to-bore gap and useless
for a 0.30 mm rail-to-plate gap. So the slide's clearances are measured instead
by **marched spans at 0.05 mm along a single ray**, at stations where every
feature involved is constant in z, on a grid deliberately offset half a step from
every design face so that the offset cancels in the difference of two samples.

---

## Printing

**Two parts, two poses, no support anywhere on either.**

### The support: forward end down, part axis vertical

A shape whose cross-section is constant along z has no downward-facing surface
*whatever its profile*, so in this orientation the shell and both rails are
support-free by construction. The head's radius only ever decreases going aft
(30.60 → 29.45), so the crown overhangs nothing and its forward face is the bed.

    pose                 61.2 x 61.2 x 181.7 mm, fits the 300 mm bed unrotated
    bed contact          one contiguous face, 585.8 mm2 on the mesh.  The head's
                         annulus is 574.5 and the four rail ends are 15.8, which
                         sums to 590.3 -- the 4.5 mm2 difference is the rails'
                         own overlap with the annulus over r 27.45..27.95,
                         counted twice by the arithmetic and once by the mesh.
                         That overlap is exactly what makes this ONE region and
                         not five, so the discrepancy IS the load-bearing fact.
    unsupported          32.1 mm2 in 4 regions -- 2 screw pilots, 2 stop faces.
                         Widest bridge 2.16 mm.
    shallowest surface   44.4 deg from horizontal (the boss ramps)

**585 mm² of bed contact under a 182 mm tall part is tippy — use a brim.** And
ABS at this height wants an enclosure; a draught will delaminate the shell before
it fails anywhere the analysis looked.

### The plate: flat, deck underside on the bed

This is the pose the split bought, and it is why the plate has no awkward
features left. Lying flat, the part's own x becomes the build axis, so every
hole bored along x — the ports, the vents — is vertical and needs nothing, and
the ribs' 45° ramps face *up*.

    footprint            51.7 x 177.2 mm
    bed contact          one contiguous face, 8521 mm2 (9157 before the slots)
    unsupported          23.2 mm2 in 2 regions -- the two lug pilots' crowns.
                         Widest bridge 1.75 mm.
    interlayer note      the lugs' layers end up PERPENDICULAR to the landing
                         load.  The root sees 3.01 MPa across them, against
                         ~20 MPa for a well-bonded ABS interface -- the one
                         stress in this bay not compared against bulk material.

Settings both parts were drawn for: ABS, 0.4 mm nozzle, 0.42 mm extrusion width,
0.2 mm layers. Shell and deck are both 2.0 mm — five extrusions; the thinnest
feature anywhere is the 1.5 mm ribs, against a 1.26 mm floor of three extrusions.

---

## Installation

1. **Print** the support forward-end down and the plate flat.
2. **Populate the plate on the bench** — this is the whole point of the split.
   BMP280 between the forward ribs, ESP32 with its header pins dropped through
   the two slots, battery on the bare aft deck. Cable-tie everything; the ties
   pass *over* each item, since all three slot pairs sit outboard of their
   item's own half-width.
3. **Seat the support** in the airframe from the front, tail first, trough
   opening towards θ 0. It stops when the crown seats in the bead; worst
   approach anywhere along the whole 215 mm of travel is 0.422 mm, at the bead
   itself, which is by design. Measured, the crown lands at s 28.81 against the
   designed 28.92.
4. **Slide the plate in** from the forward end, tail first, 177.7 mm of travel,
   until it stops on the plug at s 205. It goes in fully populated: the
   widest-reaching item is the battery, whose far corner stands to x +12.6 —
   past the opening plane — and reaches r 19.59, which is 7.86 mm inside the
   head ring's bore of 27.45. That bore, not the bead, is the hole the loaded
   plate has to pass.
5. **Two M3 × 16** through the airframe at s 201.5, θ 90 and 270. They catch the
   bosses *and* the lugs, and they will not go in unless the plate is home.

To service it, back out the two screws and the plate draws straight out the way
it went in, with the support left seated in the airframe.

### The support cannot go in the wrong way round

The airframe's cord duct bulges inward to r 21.10 over s 46–63 in a 24° sector
at θ 0. Inserted correctly, the support has no material in that sector at *any*
station. Inserted 180° out, the shell fouls the duct by 0.18 mm and stops at an
insertion depth of 160.5 mm — the tail has reached only s 48.5 of 209.0, so the
part stands **160 mm out of the tube**. The clash is the instruction.

It is also the *only* instruction, and that is worth knowing: `SCREW_THETA` is
(90, 270), which maps to itself under a half turn, so a backwards support still
lines its bosses up with the airframe's holes. Nothing about that error is
visible except the duct.

The duct excludes the half turn but not a small misalignment — measured, the
support goes fully home over rotations of **−60° to +60°** about nominal. The two
screw holes are the fine key; the duct is the coarse one.

### The plate clears the duct too, and for a different reason

The support is a C, open at x > 4.0, so the duct intrudes *through* that opening
into the space the plate travels down. The plate's lugs stand to x +3.0, which
is 1.0 mm short of the opening plane — but that margin is not what saves it.
Measured on the mesh, the plate has **no material in any of the ten azimuth bins
the duct occupies**, at any of its 357 stations: its nearest material to θ 0 sits
78.75° away, and that material is the lug's own inboard corner (x +3.0, y 16.0,
which is at 79.38°). The nearest feature is the one the design says it is.

Loaded, the margin moves from the part to the payload: inside the duct's ±12°
the payload reaches only r 12.88 — the battery's top face, where the sector is
5.36 mm wide — against the duct's 21.10. That is 8.22 mm, and it is a *separate*
limit from the head-ring bore in step 4. Neither implies the other, because the
item that stands furthest out in x is the one pointing straight at the duct.

---

## Loads

    boost, 15 g            18.43 N on 125.3 g of bay
    2 x M3 in shear        353 N  ->  19x on the boost case
    landing, 40 g          49.15 N -- sized the cable ties and the lug root, and
                           is the case that breaks solder joints
    on the stop            4.44 MPa on 4.15 mm2, against ABS's ~40
    lug root, bending      3.01 MPa INTERLAYER, against ~20 for the interface
    lug thread, pullout    0.50 MPa on 49.5 mm2 of shear cylinder

Boost pushes the whole bay aft — the support into its two screws, the plate into
the stop. Forward inertia goes the other way, into the crown as hoop
compression on the bead, the thickest ring in the forward tube.

Only 84.1 g of the 125.3 actually pulls on the screws, since the support is
bolted to the airframe and does not move; the full 49.15 N is used for the lugs
anyway, because a conservative number that is already committed beats a tighter
one that has to be kept in step. `bay_assembly.py` recomputes both forces from
the two measured masses every run and asserts they still match
`bay_params.F_BOOST_N` and `F_LANDING_N`, so a part that changes weight cannot
leave the margins quoted here stale.

---

## Alternatives considered

Four architectures were generated and adversarially judged before this one was
built. Scores are two independent judges each:

| architecture | score | verdict |
|---|---|---|
| **Bead Hanger** — seat a crown on the depth-stop bead | 8, 8 | built (this bay) |
| SPINE — a full-length structural spine, boards on both faces | 7, 6 | denser, but needs its own radial location the whole way |
| SHIM SLED — a loose sled shimmed to the bore | 5.5, 4.5 | the shims *are* the design, and they are the weak part |

The Bead Hanger's one judged flaw was relying on adhesive EVA foam pads to
centre the aft end of the cantilever. The two aft M3 screws replace them: a
positive, serviceable, measurable location instead of a glued one.

The judged runners-up both scored on density, and both lost on the same thing —
they need to *add* a radial datum, where the bead is one the airframe already
has.

The split into two parts and the 6.0 mm deck rise came later and for a reason
neither the proposal nor the judges raised: **serviceability**. The one-piece
version was verified, printable and correct, and it still meant working down a
55 mm bore. It is kept at `_scratch/_bay_sled_one_piece.py` — it no longer runs,
and it is the clearest statement of what the split changed, since every awkward
feature on the old deck (the ribs' ramps, the pin slots' 3.6 mm bridge, the
horizontal vent bores) was awkward only because the whole part had to print
standing on end.

---

## Files

    bay_params.py    single source of truth: measured airframe, payload budget,
                     architecture, load case.  87 self-checks.  Read this first.
    bay_build.py     build123d primitives and the boolean guards.  Plane
                     orientations here are MEASURED, not assumed.
    bay_support.py   the part that stays in the rocket: head, shell, trough,
                     rails, aft stop, screw bosses.
    bay_plate.py     the part that slides in: deck, ribs, slots, screw lugs.
    bay_assembly.py  the PAIR, and every check that needs both solids at once.
    bay_verify.py    150 checks of the two exported meshes against the exported
                     airframe.  Insertion sweeps, marched-span clearances,
                     containment probes, printability from the mesh's own
                     normals, in each part's own print pose.
    _scratch/        the probes that measured the airframe and the design in the
                     first place (_bead_probe.py, _tunnel_probe.py,
                     _seat_probe.py, _shallow.py, _bay_sled_one_piece.py, ...)
    out/             bay_support / bay_plate / bay_assembly .step and .stl

Nothing here touches `../Mbody.stl` or `../_clamshell/`. The airframe is
read-only input.

---

## Open items

* **The plate has no hard key against being inserted 180° out.** Rotated, its
  chord sits at x +6.0..+8.0 — inside the trough's *opening*, where it engages
  neither rail and misses the stop entirely, so it would not jam: it would drop
  through to the tube's aft end. Its lugs would still clear the bosses and its
  pilots would still be on x = 0, so it could even be screwed down there.
  Unlike the support's half turn, which the cord duct catches, nothing in the
  geometry catches this one. `bay_verify.py` probes it and says so out loud
  every run. Fixing it wants an asymmetric feature on the plate, which is a
  design change and not a verification.
* **The battery is not chosen.** Everything above holds for anything inside
  65.2 × 30.0 × 18.6 mm and 48 g. Nothing needs to change until you go outside
  that.
* **Nothing has been printed yet.** Every number in this file is measured off
  geometry, not off a part in hand.
* **The support's boss ramp clears the overhang rule by 0.4°, not 1.3°.** It is
  drawn at 45.29° and the *exported* facets read 44.40°, because an 18° sector
  tessellated in a facet or two runs further out in radius than the cone it
  samples — the bias always makes a facet shallower than the surface. A coarser
  export could push it through the 44° threshold. `_scratch/_shallow.py`
  measures it; if `bay_verify.py` ever flags the ramp, re-tessellate before
  widening the threshold.
* `free_radius()` is **optimistic by up to 0.288 mm over the bead's aft flank**
  (s 32.8–39.5), because the real flank is a fillet and the table draws a chord
  across it. Nothing in this design is sized off that region — the seat is on
  the *forward* flank, and the body clears the aft flank by 0.65 mm — but a
  future feature landing between s 32.8 and 39.5 must be checked against the
  mesh and not against the table. `bay_verify.py` prints this every run.
