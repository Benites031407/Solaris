# Helios clamshell nose — build, print and fly

A 65.52 mm nose cone that splits along its axis into two halves, hinged at the
base, sprung open, held shut by **one servo turning one bar 30°**. It releases a
30 in (762 mm) parachute out of the top — a **flat-cut or cruciform** one; a bulky
high-drag 30 in canopy may not fit, and §6 has the measured numbers rather than a
reassurance.

**Four flying parts, one of them printed twice.** Nothing else moves. Two more files
print but do not fly: `seam_pin`, a Ø3.0 × 6.5 dowel — four off — for a builder with
sockets and no Ø3 rod, and `spring_jig`, the bench tool that winds the four torsion
springs.

```
      ┌─ half_shell ──┐   ×2, the SAME file rotated 180°
      │               │
      │   chute       │
      ├───────────────┤   ← bulkhead: disc + servo cradle + thrust pad
      │  servo   arm  │   ← latch_arm: one bar on the servo horn
      ├───────────────┤
      │  base_ring    │   ← plugs into Mbody, carries both hinge pins
      └───────────────┘
```

Everything is in one coordinate frame: **z = 0 is the aft face of the spigot,
+z toward the tip, apex at z = 248.9655.** Same origin as `cone_fixed.stl`.

---

## 1. Files

### Print these

| STL / STEP | Qty | Volume | Mass (ABS) |
|---|---|---|---|
| `out/half_shell.*` | **2** | 24.56 cm³ | 25.5 g each |
| `out/base_ring.*` | 1 | 39.00 cm³ | 40.6 g |
| `out/bulkhead.*` | 1 | 9.92 cm³ | 10.3 g |
| `out/latch_arm.*` | 1 | 2.47 cm³ | 2.6 g |

Total flying mass **104.5 g** in ABS at 1.04 g/cm³, solid — real infill will be
less. Measured off the exported meshes, not summed from the CAD. The arm gained
0.65 cm³ and the bulkhead lost 0.31 when the servo horn was finally measured and the
arm had to be widened to swallow it — see §4.

### Print these only if you have no Ø3 rod

| STL / STEP | Qty | Volume | Note |
|---|---|---|---|
| `out/seam_pin.*` | 4 | 0.045 cm³ | **The seam dowel, Ø3.0 × 6.5 with 0.3 × 45° both ends.** Buy steel if you can — a Ø3.0 h9 dowel pin, a 3 mm drill blank, or 3 mm rod out of the same bag the winding mandrel came from. This is the fallback, and it is a legal one: the withdrawal sweep allows up to **Ø3.2492** before a half stops opening, so a printed pin has **0.249 mm of diameter to be wrong in** — about 8× what a tuned ABS printer misses by on a 3 mm peg. Print all four **standing on end**: the layer lines then cross the seam's shear plane (40 MPa) instead of lying in it (11 MPa). Sand the first layer flat before use. |

### And print this once, for the bench

| STL / STEP | Qty | Volume | Note |
|---|---|---|---|
| `out/spring_jig.*` | 1 | 8.34 cm³ | **The spring winder.** Not part of the rocket. Prints flat with no supports; PLA or PETG rather than ABS. Makes and gauges all four torsion springs from one guitar string and a Ø3 mm rod — see §4a. |

The second half shell is **not a mirror**. It is the same part rotated 180° about
Z. Print the same STL twice.

### Look at these

| File | What it is |
|---|---|
| `out/nose_closed.glb` | latched, closed — how it flies |
| `out/nose_open.glb` | released, both halves open 100° — how it deploys |
| `out/nose_closed.step`, `out/nose_open.step` | same, as CAD |
| `out/nose_linked.step`, `out/nose_linked_open.step` | true linked assemblies: five occurrences pointing at the four part STEPs |
| `out/spring_jig_views.png` | the spring winder, shaded and in annotated plan — every label on it is computed from `nose_params`/`spring_jig`, not typed in (`_scratch/_jig_views.py`) |

The fused scenes carry the servo, the hinge pins, the two airframe retention screws
and the four seam dowels as extra bodies labelled `_REF_`, so the viewer shows you
what goes where — **14 bodies in both** scenes. **Do not slice them.**

The dowels are in the *open* scene too, and that is deliberate. They used to be
drawn only when closed, which hid the fact that the rods as then dimensioned could
not withdraw from the far half as the halves swung apart. Now, if a future edit
breaks that again, you can see it.

The retention screws are drawn at the M2.5 major diameter, so in the viewer each one
visibly bites 0.2 mm into the spigot wall. That is the thread, not an error. Their
heads float **1.6379 mm** off the spigot OD because the airframe is not in the scene.
That gap is **not** all tube wall: it is 1.4741 mm of tube plus the 0.1638 mm of
radial clearance in the socket — and the second term is the slop these two screws
exist to take out.

### Watch it work

One release cycle — latched, servo sweeps, dwell, springs open it, held open —
rendered straight off the real STLs and the real hinge/shaft kinematics, so what
moves in these is what the geometry does. 1280 × 720, 30 fps, 7.2 s each.

| File | Shot |
|---|---|
| `out/nose_mechanism.mp4` | **all three, 21.5 s.** Start here. |
| `out/nose_overview.mp4` | exterior, slow orbit. What the rocket does. |
| `out/nose_section.mp4` | cut at y = 1.65 mm, looking at the cut face. The hook's foot and the arm are coplanar in this plane, so this is the one view where you can see the engagement itself. |
| `out/nose_cutaway.mp4` | ring and bulkhead cut away, half B hidden. The same event in 3D. |
| `out/nose_*.gif` | the same three as GIFs, if you want them inline somewhere. |
| `out/how_the_latch_holds.png` | one annotated still, if you only look at one thing. |

The hook is highlighted in red in the section and cutaway shots so you can follow
which bit of the shell is doing the work.

**`out/nose_section_before.mp4` and `out/nose_cutaway_before.mp4` are the design
that did not work**, kept deliberately and captioned as such. They are the same
cycle with the original flat blade resting on top of the bar: watch the blade lift
straight off the arm during the sweep and you can see that the bar was never holding
anything. Side by side with the current pair, that is the clearest statement of what
the J hook is for.

### Open them in CAD Explorer

Start or reuse the viewer through the `render` skill — it picks the port itself,
reuses a live server, and prints the URL:

```bash
cd ~/.claude/skills/render
npm --prefix scripts/viewer run dev:ensure -- \
  --workspace-root ~/Arquivos/Impressoes-3D/Pessoal/fwd3drocketfiles \
  --file _nose_simple/out/nose_open.step
```

Every file in the scan root is then reachable as
`http://127.0.0.1:<port>/?file=_nose_simple/out/<name>.step`. Don't pick a port
by hand and don't run `vite dev` directly — `dev:ensure` exists so you don't end
up with duplicate Explorer servers.

### Source

`nose_params.py` holds every dimension — and running it (`python nose_params.py`)
prints every derived number and asserts every relation between them, which is the
fastest way to see what a change did. `nose_profile.py` holds the measured ogive.
`nose_build.py` is the shared geometry helpers. `nose_verify.py` checks the
**exported STLs**, not the build scripts — run it after any change (**356 checks**).
`nose_video.py` renders the mechanism animations in `out/`. `spring_jig.py` is the
bench tool that makes the springs; its `__main__` re-derives the springback sweep, the
legal coil counts, the wire length per spring and the wire-substitution table from the
same constants, so it cannot drift out of step with `spring_check()`.

`_scratch/` is the working-out: **171 one-off probe scripts** plus 13 saved outputs and
14 `.npy` intermediates — refutation attempts and sizing analyses, none of
them imported by anything. It is kept because several numbers quoted as fact above
were computed there — the sealed-vent burst load in §6 comes from
`_scratch/_loadpath_out.txt`, the spring sizing in §4a from `_spring_envelope.py`,
`_spring_bench.py` and `_spring_pick.py`, the chute envelope in §6 from
`_chute_envelope.py`, the azimuth table in §6 from `_fin_azimuth.py`, and the proof in
§4c that the root-post socket left the hook's weld alone from `_post_probe.py`. It has
its own README. **The numbers in it are not maintained**;
where one still matters it was moved into `nose_params.py` as an assertion — which is
what `spring_check()` is. Two of those files now carry tombstones instead of results:
`_spring_pick.py` printed every torque 2π too large, and its integer coil counts are not
makeable anyway. Do not quote a spring number from `_scratch/`.

---

## 2. How it works

```
spring pushes half open
        ↓
   the hook's FOOT pushes UP on the arm's UNDERSIDE at z = 38.6, out at r 20.5–22.14
        ↓
   the arm bends — BOTTOM fibre in tension, the two loads 8.4 mm apart
        ↓
   the arm's TOP face pushes UP into the bulkhead's THRUST PAD at z = 47.0, in at r 6.5–9.5
        ↓
   bulkhead → ring seat at z = 47.5 → two M2.5 screws → base ring
        ↓
   two radial M2.5 screws through the spigot → airframe
```

**Which way it pushes is the whole design, and this document had it backwards
until the mechanism was checked frame by frame.** Every point of a half is inboard
of its own hinge pin, so `dz/dθ = Y_PIN − |y| > 0`: as a half swings open, the
part of it near the latch **rises**, at +0.62 mm per degree. A flat blade lying on
top of the bar is therefore lifted straight off the bar by the very motion the bar
is supposed to stop — which is exactly what the first version of this part was, and
why it held nothing shut.

So the tongue is a **J**. It drops past the arm on the inboard side (the web, at
x = 23.07, clearing the arm's swept disc by 0.710 mm), turns outboard *under* the
arm, and its **foot catches the arm's underside**. Opening now drives the foot
*into* the arm instead of away from it.

**The servo still carries no latch load.** The foot pushes the arm up at r 20.5–22.14;
the bulkhead's thrust pad — a 0.5 mm boss on its underside — pushes back down on the
arm's top face at r 6.5–9.5, 8.4 mm above and with 11 mm of unloaded span between the
two bearing patches. Opposite faces, opposite directions, so the arm works as a short
beam in **hogging** — ends pushed up, centre held down, **bottom fibre in tension** —
and `LATCH_ARM_T` is sized for that rather than for the 1.20 N itself. Its shaft sees no
net axial force either, because both ends are loaded at once and symmetrically. All
the servo ever fights is
friction: **12.3 N·mm to release, out of the MG90S's 216 N·mm stall — 6%.**
Re-latching costs more, **17.4 N·mm (8%)**, because going that way the arm has to
climb the foot's lead-in ramp.

*Which fibre goes into tension was stated backwards here for a long time.* An upward
load on an outboard overhang puts the **far** fibre in tension — a diving board,
inverted. It changes no dimension, because the print pose lays both fibres in-layer
(40 MPa, not the 11 MPa bond), but a beam sketch drawn from the old sentence would be
upside down.

And that ramp is why **you can cut power to the servo once it is latched.** Its
slope is tan 0.200 against a printed-ABS friction coefficient of 0.35 — a 1.75×
margin — so the springs cannot back-drive the arm out from under the hooks. The
servo is only needed for the two transitions.

The arm's ends are **arcs of R 22.361 centred on the rotation axis**, not round
caps. Two consequences: its furthest point is 22.361 mm at *every* angle, so it
clears the bulkhead seat's Ø53.8 bore by 4.54 mm through the whole sweep; and the
swept volume equals the part, so nothing outside its static outline needs
clearing.

Latched, the foot reaches under the arm across **r 20.50–22.14 = 1.64 mm of
ledge** (the outboard limit is that arc, not the 22.0 half-length). The honest
bearing area is smaller than the footprint, because the foot's top is a ramp: on a
fresh print the arm lands on the **flat land only, 1.83 mm² at 0.327 MPa**, easing
to the full 4.91 mm² at 0.122 MPa once the ramp beds in. Both are nowhere near ABS's
~45 MPa in bearing — and the reason for quoting the *smaller* one is that the
footprint is the number it is tempting to quote and it is the number that flatters.
Read risk 11 in §8 before you rely on either.

Swept 31°, the arm's trailing edge is out from over the foot after **23.60°** — a
1.31× margin on the release, and 11.2 mm of travel at the arm's tip. (Read 30° and
20° for a 1.50× margin until the bar went 8.0 → 10.50 wide: the trailing edge lags
the centreline by `asin((W/2)/r_in)`, so it grew with the bar, and `LATCH_SWEEP`
went 30 → 31 to keep `self_check()`'s 20%-of-sweep trim reserve from being eaten —
it was down to 0.40° of headroom, inside the trim error the reserve exists to
cover. The absolute daylight was never the problem: it is 7.40° either way.) The hook then
climbs out through its slot in the bulkhead disc, staying inside that slot until
**22.5° of opening**, at which point it is above the disc and free. It never comes
within 0.50 mm of either side of the slot on the way, and its outermost point while
level with the seat is r 25.80 against a 26.9 bore — clear by 1.10 mm. Those are
swept numbers, not static ones; a static fit proves nothing about a joint that
hinges open.

### Why the hooks were snapping, and what changed

They were snapping because the hook stood on a **0.6 mm** gusset. That is the number
that mattered and nothing in this document mentioned it.

The gusset is the diagonal that ties the hook's web into the shell wall. The whole
spring moment crosses it, and its own root at `Z_SHELL_ROOT` is where the bending
stress peaks — so its depth in z *is* its section modulus. At 0.6 mm that was
**1.23 mm³**. It is now **9.5862 mm deep, for S = 45.95 mm³**: a **37× gain**, and
that is the fix. The web went with it, to 2.430 mm thick (S 2.9524 mm³ radially,
3.6450 sideways), and the tongue's whole J-section now measures 161.14 mm².

What that buys, in the two directions a hook actually breaks:

| | 0.6 mm gusset | full-depth gusset |
|---|---|---|
| breaks **downward** at | 2.55 N | **20.14 N** |
| = held by the nose tip | **46 gf** | **361 gf** |
| = a knock of | 5 g | 40 g |
| breaks **sideways** at | 1.25 N | **12.90 N** |
| vs a stalled MG90S's 10.54 N | **0.12× — it loses** | **1.22× — it holds** |

The downward figures are quoted *at the nose tip* because that is where a hand goes,
and the hinge amplifies it **5.69×** on the way to the hook. 46 gf at the tip is
picking the rocket up by its nose cone. **The old hooks were not marginal; they were
weaker than handling.** The sideways column is the one that matters in service: a
servo that stalls with the arm jammed against a foot delivers 10.54 N, and at 1.25 N
the hook lost every time. Sideways is also the worse direction for a second reason —
that load is torsion of the weld, and its shear lands on constant-y planes, which in
the print pose below *are* the layer bonds at 11 MPa rather than beads at 40.

`nose_params.self_check()` derives all eight numbers and asserts each one, so none of
them can drift. `nose_verify.py` probes the gusset's full 9.59 mm of depth on the
exported mesh at x = 27 — inboard of the skin, so the wall cannot answer for it —
plus a probe above `GUSSET_Z_TOP` that requires the diagonal to have *ended* rather
than run on.

> **Before you reprint: check which way the broken halves were printed.** Every load
> above assumes the pose in §3 — the half lying on its split face, layers running
> along the rocket's axis, so the hook's loads are carried **in-layer at ~40 MPa**.
> Printed base-down instead, those same loads cross the layer bond at **~11 MPa** and
> every number in the table scales by **11/40 = 0.275**. That is a **3.63× error,
> larger than the geometry fix itself.** Look at the broken part: **layer lines
> running around the cone means base-down, and that alone could be why it snapped.**
> Layer lines running along the cone's axis is the correct pose.

### And what holds the nose in the airframe

**Two M2.5 × 8 self-tapping screws, radial, at the two seam azimuths (0° and
180°), 13.21 mm below the airframe's forward rim.** You drill Ø3.2 through the
tube; the nose brings its own Ø2.1 pilot.

A conventional nose needs no fasteners — it is *supposed* to come off. This one
never separates, so the slip fit is not enough on its own: the shoulder takes drag
in compression and the spigot takes side load in shear, but there is 0.1638 mm of
radial clearance in the joint, so pull and the nose comes out, twist and it turns.
Two screws diametrically opposite fix both: translation and rotation. Killing the
rotation is the point of the second one — it is what stops the servo wire being
wound up over the flight.

Three details that are not arbitrary:

- **The hole in the tube is deliberately loose and the pilot in the nose is not.**
  The screws must not set the nose's station — the shoulder does that. The Ø3.2 hole
  on a Ø2.5 screw gives **±0.35 mm of free play**, and inside that band the screw
  finds the pilot with the shoulder still hard on the rim. Past it the screw has to
  drag the nose axially by (error − 0.35) mm to line the two holes up, and **the
  dangerous direction is too CLOSE to the rim, not too far** — a hole 0.5 mm *forward*
  of station pulls the nose 0.15 mm out of the tube and holds the joint open, and
  every measurement of the assembled rocket would still look right. Drilled 0.5 mm
  *aft* of station the screw pushes the other way, into a shoulder that is already
  seated, so it binds or refuses to start instead of opening the joint. (This bullet
  used to name the aft direction as the hazard, which is backwards.)
- **The pilots are blind**, with 1.00 mm of floor left behind them. No screw tip can
  ever appear in the bay where the servo wire and the shock cord run. Grip is
  5.36 mm of thread and the tip stops 0.56 mm short of the floor, so an M2.5 × 8
  cannot bottom out and jack the joint open. **Do not substitute an M2.5 × 10.**
- **The mouth of each pilot is countersunk 45° from Ø2.1 to Ø4.1.** That is the
  tolerance budget for a hole you drill by hand off a tape measure: ±1.0 mm of
  misplacement and the screw still finds the pilot, and the cone makes it
  self-centre instead of starting crooked.

The thread depth comes from an internal pad — a 5.52 mm thickening 11 mm along the
circumference inside the spigot, because 2.40 mm of spigot wall is not a thread.
Its closest approach to the axis is |x| 22.54, which clears the cradle fins by
13.5 mm and the servo by 16.4 mm, and the shock cord is a whole quadrant away at
azimuth 270°.

---

## 3. Print plan

Creality K1 Max, 300³ enclosed, ABS, 0.4 nozzle, 0.2 mm layers, 0.42 extrusion
width. Every pose below is what `nose_verify.py` checked for bed fit.

| Part | Pose | Footprint × height | Support |
|---|---|---|---|
| `half_shell` ×2 | **split face flat on the bed** | 65.5 × 212.3 × 39.0 mm | none — but read the note on the cavity crown |
| `base_ring` | **upright, spigot down** on z = 0 | 65.5 × 78.2 × 57.4 mm | none |
| `bulkhead` | **top face on the bed**, fins growing up | 56.8 × 56.8 × 34.0 mm | none — one 13.8 mm bridge |
| `latch_arm` | **top face on the bed**, pocket opening up | 44.7 × 10.5 × 8.4 mm | none |

Both half shells fit on the bed side by side. All four parts fit in one plate if
you want, but print the arm on its own — it is the one part whose top face has to
come out genuinely flat.

**Why the half shell lies on its split face:** layers then run *along* the rocket
axis, so the hinge and latch loads are carried in-layer (~40 MPa for ABS) instead
of across the layer bond (~11 MPa). Printed nose-up, every one of those loads
would be peeling layers apart. The whole flat face lands on the bed — the seam is
a single plane at y = 0.15 — and each successive layer of a half-ogive on its
diameter plane is narrower than the one below, so **the skin** never overhangs.

**But the cavity does, and this is worth knowing before you blame the model.** The
cavity is the skin's complement: it *narrows* as the print rises, so the material
closes inward over air. On the root section it passes 45° at a build height of
21.75 mm, meaning the top 9.01 mm of every cross-section is shallower than that,
with the per-layer inward step growing 0.20 → 0.32 → 0.57 → 0.89 → 1.31 mm (48% →
311% of a 0.42 mm bead) and closing on a **7.00 mm bridge at the crown, under
2.01 mm of solid wall**.

None of that needs support — a 7 mm bridge in an enclosed ABS printer is routine
and it is roofed by four more solid layers — but it is where this part will look
worst *inside*. If the crown sags enough to matter, fix it slicer-side: raise the
bridging flow and cool the bridge layer only. **Do not put support in there.** The
chute has to come out.

**Why the arm's top face is on the bed:** that face is the bearing surface for the
thrust pad; the *hooks* bear on the opposite face, at r 20.5–22.14, which in this
pose is the print's last layer and a solid top surface (iron it if your slicer
offers it). Nothing there is bridged and nothing sinks — the horn pocket **opens in
that same face** rather than being spanned by it. But that makes the two features
neighbours, and the gap is smaller than it looks: the pocket's furthest corner is at
**r 18.79** (`hypot(18.4, 3.8)` — the far corner of the 36.8 mm lever slot, not the
Ø7.73 hub recess at r 3.87), leaving **1.71 mm of full-thickness land** out to the
r 20.50 the hooks land on. That land was 1.93 mm until the horn was measured: taking
the slot from 5.0 to 7.6 mm for a 7.2 mm blade spent 0.22 mm of it, which is why
`HORN_SLOT_R` stopped at 18.4 rather than the 18.8 the end clearance would have
liked — the real ceiling is 18.617, and `self_check()` asserts it. That land is what carries the thrust off the hooks and
into the bar, and `nose_verify.py` probes all three of its boundaries. (This line
has said r ≤ 9.1 and then r 15.18; neither was the corner, and both made the land
look three to six times wider than it is.) Both bearing faces still come out flat
for free.

**Why the bulkhead prints upside down:** the disc's layers then lie in the plane
of the latch load, and the cradle fins grow straight up off the bed. The cost is
that z *decreases* as the print rises, so a +z-facing surface is an overhang.
There is exactly one: each flange pad's mounting face is a **13.8 mm bridge**
between two fins. It cannot be supported from above (the servo's own flange plate
occupies that space) or ramped in from the fins (same reason). A 13.8 mm bridge is
routine. If the servo rocks after assembly, take one pass off the pads with a
file.

**Settings that matter:**
- Walls: ≥ 3 perimeters everywhere. The shell wall is 2.0 mm measured normal to
  the skin, which on a cone tilted 5–13° off the axis is **2.005–2.067 mm measured
  radially** — thicker than the normal figure, not thinner, because the radial
  direction cuts the wall at a slant. (This line used to say 1.92–1.96, which had
  the trigonometry inverted. `nose_verify.py`'s mesh probe reads ~0.09 mm low
  because it starts its inward walk at `r_nom − 0.1`; the numbers here are
  `nose_profile.wall_normal_to_radial()`.) So 3 × 0.42 = 1.26 mm of perimeter plus
  infill.
- The two hinge fairings, the latch hook and the arm want to be **solid** — set
  100% infill or enough walls that they come out solid anyway. The hook especially:
  its foot is the one place in the whole nose that carries a point load.
- ABS shrink is taken as 0.6% in `nose_params`; if your printer's profile already
  compensates, do not compensate twice.
- Print the arm slowly. It is 8.4 mm tall and 44.7 mm long and it will rock if it
  is printed fast — though less than it used to, since the bar went 8.0 → 10.5 wide
  for the horn. (It really was 46.7 mm long — `2 × 23.3452`, measured on the mesh in
  `_scratch/_hookaudit_3.txt` — until `LATCH_ARM_R` came in **23.0 → 22.0** with the
  hook, which took `ARM_CORNER_R` to `hypot(22.0, 4.0)` = 22.3607 and the arm to
  44.72. The `# 23.3452` comment on that line went stale at that moment and stayed
  stale until the horn fix froze the constant; see the note at `LATCH_ARM_W`.)

---

## 4. Hardware

| Qty | Item | Where | Note |
|---|---|---|---|
| 1 | **MG90S** metal- or plastic-gear micro servo | bulkhead cradle | 22.8 × 12.2 × 22.5 mm, 216 N·mm at 4.8 V. The body is **not** symmetric about the shaft — it runs −6.2…+16.6 mm in y. |
| 1 | servo's own **centre screw** | through the arm into the horn/shaft | counterbored Ø5.0 × 1.6 so the head stays below the arm's top face |
| 1 | the **DOUBLE-ARM horn** from the servo kit | in the arm's pocket | **Measured, not nominal — and the blade is not one width: 36.0 mm tip to tip, 7.2 mm across its middle 22.5 mm tapering to 4.1 at the tips, hub Ø7.43 × 5.00 tall.** The pocket is cut to those: Ø7.73 × 5.00 hub recess and a **36.8 × 7.6 through-slot** held to full width all the way out, taking both spurs with 0.40 mm of end clearance per spur, 0.20 mm per flank, and **1.385 mm of wall beside the hub recess** — the thinnest wall in the part. It was Ø8.2 × 5.70 into a 36.8 × **5.0** slot, sized to a blade width that had itself been back-derived from the slot, so the two could never disagree; the real blade interferes with 6.75 mm of solid arm per side, which is why it would not seat. A 7.6 slot needs a **10.50 mm bar** (was 8.0 — a 7.6 slot in an 8.0 bar leaves 0.20 mm flanks, half an extrusion, at a factor of safety of 0.054 against a stalled servo), so **the arm and the bulkhead reprint; the shells and the ring do not.** **Measure your own horn:** the hub height must equal `HORN_POCKET_DEPTH` or the centre screw clamps thin air — file a tall hub, do not deepen the pocket. The one number still unmeasured is the **blade's thickness in z**, assumed 1.6 mm; a *thicker* blade is worse, not better, and over 2.3 mm needs a rethink. |
| 2 | **M2 × 8** self-tapping | servo flange → bulkhead flange pads | Ø1.7 pilots, **straight through** the 5.0 mm pads — not blind, which is why the length is not critical here the way it is for the retention screws. Through the servo's 2.5 mm flange, an ×8 leaves 5.5 mm of thread for 5.0 mm of pad and stands **0.5 mm proud underneath**, in clear air: the pilots are at y = −8.8 and +19.2, outboard of the servo body's −6.2…+16.6. Driven through the Ø4.2 access holes in the disc. |
| 2 | **M2.5 × 8** self-tapping | bulkhead → base ring screw lobes | Ø2.7 clearance in the bulkhead, Ø2.1 × 6 pilot in the ring. **× 8, not × 10** — the head lands on the disc's top face, so the budget is 2.5 mm of disc plus 6.0 of pilot = **8.5 mm**. A × 10 bottoms 1.5 mm early, and a screw that bottoms before the bulkhead is down on its seat holds that seat *open* — on the one joint the whole latch load crosses. An × 8 leaves 5.5 mm of thread and 0.5 mm of floor. (`BULK_SCREW_LEN`, asserted in `self_check()`. This README said × 10 in two places and nothing in the model contradicted it, because the length was not a constant at all.) |
| 2 | **M2.5 × 8** self-tapping, pan or button head | **airframe → nose spigot**, radial | **You drill the airframe: Ø3.2 through the tube, 13.21 mm below its forward rim, at the two seam azimuths (0° and 180°).** Ø2.1 blind pilot 6.92 mm deep in the spigot, countersunk Ø4.1 at the mouth. **× 8, not × 10** — a 10 bottoms out. |
| 2 | **Ø2.0 × 30 mm** steel pin or music wire | hinge pins | 2.3 bore in the knuckle, 2.1 in the lugs |
| 4 | **torsion springs — Ø0.50 mm ASTM A228 music wire, 8.472 coils, Ø3.85 mean (OD 4.35 / ID 3.35), body 4.24 mm free, free at a 170° included angle.** Each leg runs radially out of the coil to r 2.8 and is then bent 90° to run **3.0 mm parallel to the pin**. **10.20 N·mm each** at the closed position. | 2 per hinge, one each side of the knuckle | **You wind these — see §4a and `spring_jig.py`.** All four the same hand. They sit in the 5.5 mm gaps between knuckle and lug, over the Ø2.0 pin, legs dropped into the Ø0.9 × 3.0 blind seats. |
| 1 m | **Ø0.50 mm (.020 in) plain steel guitar string** — the wire above, as bought | raw material for the four springs | 110.2 mm ends up in each spring; cut 150 mm to have something to pull on, so **one string makes six and four are needed.** A plain (unwound) .020 single is A228 music wire. |
| 1 | **Ø3.0 mm steel rod ≥ 25 mm** — dowel pin, drill blank, silver steel, or the shank of a 3 mm drill | the winding mandrel, into `spring_jig` station W | Not consumed. Ø3.0 is what sets Ø3.85 mean after springback; see §4a. |
| 1 | **`out/spring_jig.*`** — printed, 8.34 cm³ / 8.7 g | the bench | Prints flat, no supports; PLA or PETG preferred over ABS. Makes all four springs and gauges them. |
| 4 | **Ø3.0 rod cut to 6.5 mm** — dowel pin, drill blank, silver steel, or 3 mm brass rod. No rod? print `out/seam_pin.*` | seam, at z = 120 and z = 180 | Ø3.3 sockets **4.5 mm** deep in both halves; **glue each rod bottomed into ONE half only.** See §4b — 6.5 and 4.5 are not free choices, and 8 mm was the old length. |
| 1 | **Ø4 mm** shock cord / kevlar | through the bulkhead's Ø8 hole at y = −18 | see the warning in §7 |
| 1 | **30 in parachute + deployment bag** | the cavity | 762 mm canopy. **Flat-cut or cruciform, thin ripstop.** The pack has to fit a Ø40 × 95 mm cylinder = 120 cm³ — see §6, which measures it rather than assuming it. A bulky toroidal 30 in may not go. |

Springs: 2 × 10.20 N·mm per hinge = **20.40 N·mm per half**. The hook's load face sits
34.11 mm from the hinge axis *measured in y* — which is the only component that
makes a moment about an x-parallel pin — so the latch carries **0.5982 N per half,
1.20 N total.**

### 4a. The springs — what they are, why you wind them, and how

**Two corrections live in this section, and both used to be quoted as results.**

1. `TORSION_RATE` divided by 57.296 (= 180/π) where the formula
   `k = d⁴E/(10.8·D·n)` is a moment **per turn** and needs 360. Every spring number
   in this file was **2π too large** — the Ø0.32 mm / 15-coil / 5.44 N·mm spring this
   section recommended for a while was really delivering **0.87 N·mm each**, and its
   "1690 of 1700 N/mm²" stress was really 269. It was not 0.63× of bench gravity; it
   was **0.10×**. That spring would not have opened the nose in any attitude.
2. `TORSION_COILS` read a round **8**, and a round number is not makeable here. See
   *the coil count is not a free choice*, below.

**What the pocket allows.** The gap between knuckle and lug is 5.50 mm along the pin
and — measured against the exported meshes, not guessed off the profiles — its
*smallest* free radius about the pin is only **3.45 mm**, at the knuckle end. With a
Ø2.0 pin down the middle those two numbers box the coil into `D_mean` 3.20…4.30 and
`n·d < 5.5`, and everything else follows.

Within that box torque goes as `T = 5324.07·d⁴/(D_mean·n)` at the 100° travel, so the
whole design reduces to one inequality:

> **`n · D_mean ≤ 34`** — strictly the spring clears bench gravity up to 38.61, and 34
> keeps 14% back.

The answer is **Ø0.50 mm A228, 8.472 coils, Ø3.85 mean → 10.20 N·mm each**, at **831
of 1700 N/mm² (49%)**. OD 4.35, ID 3.35 over the Ø2.0 pin, body 4.10 / 4.24 / 4.37 mm
unwound / free / wound inside the 5.5 mm gap, far edge 2.85 mm (2.98 unwound) against
the 3.45 available.

**Why you wind these instead of buying them.** This was asked directly and it is the
honest answer: *the material is off the shelf, the finished part is not.* Three things
rule out a catalogue torsion spring, and only the third is fatal:

- `D_mean` is boxed into 3.2–4.3 mm — the very fine end of any stock range;
- `n·d < 5.5` means a stock Ø0.5 spring's usual 15–20 coils is **three times too long**;
- **stock torsion springs have straight tangential legs.** Bending one to reach an
  axial seat at r 2.8 rotates its tail by `arccos(1.925/2.8) = 46.6°`, the two legs leave
  the coil in opposite helical senses so the two shifts **add to ~93°**, and no stock
  free-angle tolerance absorbs that. You would be re-forming both legs of a bought
  spring by hand anyway.

So "generally available" is met at the level of **material and tooling**, which is
where it is actually cheap:

| what | what it is |
|---|---|
| wire | Ø0.50 mm A228 = a **plain .020 in guitar string** (.020 in = 0.508 mm, inside the box). 110.2 mm per spring; one 1 m string makes six. |
| mandrel | a **Ø3.0 mm dowel pin, drill blank, silver steel rod or drill shank** |
| gauge pin | the same Ø2.0 stock as the hinge pins |
| tools | side cutters and one pair of pliers |
| jig | **`spring_jig.py`** — one printed plate, 8.7 g, no supports. Picture: `out/spring_jig_views.png` |

And the tolerances are not tolerances. The acceptance box is **two legal coil counts
wide and 1.1 mm of mean diameter wide**; a Ø3.0 mandrel gives `D_mean` 3.50 as wound
and 3.68…4.03 after the 5–15% springback music wire takes at this index, so the
mandrel **cannot miss**. `spring_jig.py` prints the whole springback sweep: 0%
→ 1.30× bench, 15% → 1.13×, 20% → 1.09×, and past ~24% the coil's unwound far edge
exceeds `POCKET_FREE_R` and **the jig's Ø6.90 ring physically refuses it**. Nothing
here is measured to make it; one caliper reading at the end confirms `n · D_mean ≤ 34`.

**The coil count is not a free choice — and that is what makes it easy.** The two legs
leave **opposite ends** of the coil, so the angle between them *is* the total wrap. A
free included angle of 170° therefore forces

    n mod 1 = 170/360 = 0.4722

and the only makeable counts are 7.472, 8.472, 9.472, 10.472 — of which `n·D_mean ≤ 34`
leaves **7.472 and 8.472**. This is why `TORSION_COILS` is not 8: a round 8 is not a
spring you can build with legs 170° apart, and treating it as one **overstated the
torque by 5.5%**. `spring_check()` assertion 10 now refuses a count that is not
leg-legal.

The happy consequence is that you never *count* the fraction, you **cut** it. Wind nine
turns on the Ø3 rod (deliberately long — springback drops it to 7.8…8.6), take it off,
drop it into the jig's gauge station, find where the last turn crosses the 170° slot and
bend the leg out **there**. The fraction comes out right by construction. Full
step-by-step in `spring_jig.py`'s docstring.

**Both legs sit in blind seats**, one Ø0.9 × **3.0** mm hole in each knuckle end face
(azimuth 180° about the pin) and one in each lug's inner face (azimuth 250° — the
two solid bands are disjoint, so no single azimuth serves both ends). That is what
fixes the travel at 100°, and fixing the travel is what makes the torque as high as
it is: energy is ½·T·θ, so a *longer* stroke delivers the same push at a *lower*
peak torque, which is also why the latch and servo loads above are so small. The
spring spans 10.10 mm across the 5.50 mm gap, so each leg is guaranteed **1.60 mm of
engagement** at the worst axial float — it locates itself, with nothing to shim.

> **The seats are the one printed dimension that moved for the springs.**
> `TORSION_SEAT_DEPTH` went **2.0 → 3.0 mm**. Nothing else in the pocket changed:
> `TORSION_GAP` 5.5, `TORSION_SEAT_D` Ø0.9, `TORSION_LEG_R` 2.8, the lugs, the knuckle
> and the pin are all as they were, and the two parts lost 0.0025 and 0.0013 cm³ — four
> and two extra millimetres of blind hole. If you printed `half_shell` or `base_ring`
> before this, they still work with 2.0 mm legs, at 1.60 → 0.60 mm of guaranteed
> engagement.

**In flight this is plenty.** At apogee the rocket and both halves are in free fall
together, so gravity has no moment about the pin at all; the spring works against
the half's 1.799 × 10⁻⁴ kg·m² of inertia alone at ω_n = 8.06 rad/s and swings it
**60° in 144 ms**, inside the seconds of near-zero-g either side of apogee.

**And on the bench it now clears gravity in every attitude.** Worst-case gravity on one
half is 0.2486 N at 69.32 mm from the hinge axis = **17.24 N·mm**, against the spring's
20.40 — a ratio of **1.18×**. Worst case across the whole springback range (20%,
`D_mean` 4.20) is still **1.09×**. If yours comes out fat, wind 7.472 turns instead of
8.472: torque goes as 1/n, so that is a flat 1.13× back on the margin.

> Being over 1.0× does **not** make this a strong opening. 1.18× means a half *just*
> lifts its own weight, so nose-down on the bench it will crawl. Test hinge-line
> vertical or nose-up to see it move properly, and treat nose-down as the proof that
> it opens *at all*, not as the demonstration.

**If you want more, the wire is the knob** — same jig, same mandrel, same seats, `T` goes
as `d⁴`:

| wire | per half | vs bench | σ |
|---|---|---|---|
| Ø0.50 (nominal) | 20.40 N·mm | 1.18× | 831 |
| Ø0.508 = .020 in | 21.69 | 1.26× | 843 |
| **Ø0.56 = .022 in** | **31.56** | **1.83×** | 915 |
| Ø0.60 | 41.13 | 2.39× | 970 |
| Ø0.63 and up | — | — | wound body exceeds `TORSION_GAP` at 8.472 coils |

`nose_params.spring_check()` asserts every constraint above at import, and prints the
ratio, so it cannot quietly drift. `spring_jig.py` re-derives the springback sweep and
the substitution table from the same constants.

### 4b. Why the dowels are 6.5 mm long, and not 8 and not 10

A dowel bridging the seam has to **get back out** while the two halves rotate away
from each other, and those two requirements fight: the sideways skew the rod has to
survive grows with the **square** of how far it reaches into the far half, while the
withdrawal that relieves it grows only **linearly**. Reach too far and it binds
before it clears.

That is not hypothetical. The earlier Ø3 × 10 rod, sitting centred in two 6.0 mm
Ø3.2 sockets, put 4.85 mm of itself into the far half and needed **0.186 mm of radial
room where 0.100 was available**: at the z = 120 station its surface stands
**0.086 mm inside the far bore's wall, from 0.69° of opening through to 2.08°** —
enough to stop the release, and invisible to every check in the project at the time,
because the opening sweep only sampled from 5° upward and by then the rod is long
clear. The z = 180 station did *not* jam, but it cleared by 0.0016 mm, which is not
clearance, it is a coin toss.

*(Those figures were re-derived from `dowel_relative()` on 2026-09-14 and they are
not what this file used to claim. It said 0.03 mm at 1.85°, and `nose_params.py` said
0.297 mm and 2.8°; neither reproduces. The conclusion is unchanged and the built
geometry never depended on them.)*

The fix is short engagement, not a bigger bore or a chamfered mouth. **A mouth
chamfer relieves the one place that was never touching:** the interference grows
monotonically *inward* — −0.097 mm at 0.5 mm of depth, −0.001 at 3.5 mm, +0.086 at
the 4.85 mm tip — so it is the deep end that binds. Moving the stations is no better:
the crossover for that rod is z = 178, and past it the margin is only −0.015 mm even
at z = 200.

**As built: rod cut 6.5 mm**, glued **bottomed** in one half's 4.5 mm socket, so it
stands **2.00 mm** proud of that seam face and engages the other half by **1.70 mm**
once the 0.30 mm total seam gap is paid for. Its tip stays **2.80 mm off the far
socket's floor at every angle**, which matters — it means the dowel can never bottom
out and never sets the closed position. **The seam faces do that.** The worst skew
then wants 0.0254 mm of the 0.150 mm the Ø3.3 bore provides: a **5.90× margin** at
z = 120 (peaking at 0.72° and clear by 0.77°) and **11.19×** at z = 180 (peaking at
0.38°, clear by 0.40°). Both stations are swept degree by degree in
`nose_params.dowel_withdrawal()` and again against the exported mesh in
`nose_verify.py`.

Going 8.0 → 6.5 is what bought that margin, and it bought something else with it:
at 8.0 the same sweep allowed a printed pin no fatter than Ø3.1328, i.e. 0.133 mm of
oversize. At 6.5 it allows **Ø3.2492 — 0.249 mm** — which is what makes `seam_pin.py`
a fallback rather than a compromise, and the reason that file could be written at
all.

---

### 4c. The pin that IS printed: the two root posts

The four seam dowels are loose rods because **a half prints on its split face**, which
makes y the build direction and `y = SEAM_SETBACK` the bed. A boss growing from one
half toward the other would need material *below the bed*. On a seam face only recesses
are printable — that is not a preference, it is the pose, and the pose is what puts the
hinge and latch loads in-layer at 40 MPa instead of across the layer bond at 11.

So the moulded-in pin goes somewhere else. **The base ring prints upright, spigot down,
so its collar top can grow a +z pillar for free** — and that is where it is:

**Ø2.0 × 3.0 mm, on the ring's collar top at r 29.79, into a Ø2.7 × 4.0 socket in the
half. Two of them, one per half, on opposite diagonals.**

Four facts about that, in the order they were decided:

- **Two, not four.** Half B is half A turned 180° about Z, so a single socket at
  (`POST_X`, `POST_Y`) images to the opposite corner. Two posts on opposite diagonals
  means **each half only ever meets its own** — there is no second post for it to hunt
  for, and no mirrored socket costing skin where nothing enters. `nose_verify.py` probes
  the *wrong* diagonal and requires it empty, because a mirrored pair would pass every
  other check.
- **It is on the −x meridian, and that is structural, not tidiness.** +x is where the
  latch hook welds to the shell: with the full-depth gusset, that weld *is* the plane
  x = +30.7536 over y 0.15…3.15. A Ø2.70 socket there takes 0.6795 mm out of a 3.0 mm
  weld **at its most-stressed fibre — 17% of S**, and the servo-jam margin falls from
  1.22× to 1.02×. The threshold that caught it was a volume assertion: placed at +x the
  pad added only 51.6 mm³, because the gusset already fills that corner. At −x it is
  bare skin and adds 113.0 mm³. `_scratch/_post_probe.py` is the mesh proof that the pad
  is one-sided and that the +x weld is continuous across all 3.0 mm of y.
- **It engages first, and that is the whole point of it.** The post is clear of its
  socket by 5.09° of opening; the nearer dowel is clear by 0.77°. So on the way *shut*
  the post is in **4.3° before the first dowel** — which is what makes the two halves
  clamp onto the *ring* rather than hunting for each other across the seam. Withdrawal
  margin is **3.26×** (worst skew wants 0.1073 mm of the 0.350 mm available, peaking at
  4.68°), and the post's top stays 1.20 mm off the socket floor throughout, so it
  locates the joint without ever setting its position.
- **It is a strictly easier print than the dowel sockets it sits beside.** The socket is
  bored along +z, which in the half's pose lies *in* the bed plane, so it has no
  downward-facing floor at all — just a 2.70 mm slot in plan view whose largest
  single-layer step is 0.3386 mm, 81% of a bead. Each dowel socket, bored along the
  build direction, roofs 8.55 mm² of bridged floor. The post itself is a 3 mm pillar on
  a face the ring is already printing flat.

The socket's mouth is chamfered 0.3554 mm — capped by the skin outboard of it — which is
what lets a half find its post while still skewed rather than catching on the bore's
edge.

---

## 5. Assembly

Build the mechanism as a module on the bench, test it, *then* put it in the ring.

0. **Wind the four springs first**, because step 7 needs them and nothing else does.
   Print `spring_jig`, chuck a Ø3.0 mm rod in station W, and follow the eight steps in
   `spring_jig.py`'s docstring: 150 mm of Ø0.50 mm music wire (a plain .020 in guitar
   string), a 3.0 mm tail bent on the fence, nine turns on the rod, then off the rod and
   into the gauge station to set the 170° free angle by *where you bend the second leg*,
   not by counting. Accept each one in the jig unloaded — tail bottomed, second arm free
   in the slot, coil not proud of the 5.5 mm ring, coil loose inside the ring — then one
   caliper reading: **`n × D_mean ≤ 34`.** All four the same hand. Make six; the string
   is long enough and two spares cost nothing. §4a explains every number in that
   sentence.
1. **Clean up.** Ream the **four** Ø2.1 lug bores and the **two** Ø2.3 knuckle bores
   until a Ø2.0 pin slides. Check the **eight** Ø3.3 dowel sockets, four per half — a
   Ø3 rod should drop in under its own weight and **bottom at 4.5 mm**; if a socket
   came out shallow, drill it to depth rather than shortening the rod. Clean the
   **six Ø0.9 × 3.0 spring-leg seats** (two in the knuckle end faces, four in the
   lugs' inner faces) with a 0.9 mm bit turned by hand — they are printed
   horizontally, so a first layer of stringing is normal and a spring leg needs the
   full 3.0 mm. Check the arm's **top and bottom** faces are flat; both are bearing
   faces now. Leave the two Ø2.1 retention pilots in the spigot **alone** — those are
   meant to be tight; the screws cut their own thread.
2. **Measure your horn — three numbers, and the third has never been measured.**
   Put the **double-arm** horn on the servo and measure (a) how far the hub stands
   above the case face, (b) the blade's width *across its middle* and how far that
   width runs, and (c) the blade's thickness in z.
   - `HORN_POCKET_DEPTH` is **5.00 mm**, measured off an MG90S double-arm horn, and it
     leaves 3.40 mm of floor with 1.80 mm under the screw head. The ceiling is 6.40.
     If your hub is *shallower*, drop the number and re-export — a pocket deeper than
     the hub means the centre screw clamps thin air. If your hub is **taller, file the
     hub**, not the pocket; going past 6.40 means deleting the counterbore or growing
     `LATCH_ARM_T`, and both drag other parts with them (§8 risk 5).
   - **`HORN_SLOT_W` is 7.6 mm, and this is the tweak that fixed the fit.** It used to
     be 5.0, for a blade "measured" at 4.6 mm — a number that had in fact been
     back-derived from the slot it was supposed to fit, so the two could never
     disagree. The real blade is **7.2 mm wide and stays 7.2 for 22.5 mm of its
     length**, so a 5.0 slot interferes with 6.75 mm of solid arm on each side and the
     arm simply does not go on. The slot is now held at full width for all 36.8 mm
     rather than tapering after the hub, because the blade is still 7.2 wide at
     11.25 mm out and a slot that narrowed at 11.45 would leave the blade bearing on
     the step: factor of safety 0.39 at stall instead of 2.70.
   - That slot forced **`LATCH_ARM_W` 8.0 → 10.50** — a 7.6 slot in an 8.0 bar leaves
     0.20 mm flanks, half an extrusion wide. The feasible window is **10.26 to 10.76**
     and it exists at all only because `ARM_CORNER_R` is now a frozen literal with
     `LATCH_ARM_R` derived from it, which holds the entire hook load path bit-identical
     while the bar widens. **The arm and the bulkhead reprint. The shells and the ring
     do not** — `WEB_X_IN` stays 23.07, which is the whole point of the freeze.
   - `HORN_BLADE_T`, **the blade's thickness in z, is still assumed and not measured**
     — 1.6 mm, inherited from the reference solid. It sets the only load-governed
     stress in the arm, and it runs backwards from intuition: the sideways force per mm
     of flank is fixed by the torque and the bearing length, so a *thicker* blade does
     not lower the load, it only moves the load further below the flank's root and
     lengthens the lever. At a stalled 216 N·mm the resultant factor of safety against
     the 11.0 MPa interlaminar strength is 4.07 at 1.0 mm, **2.70 at 1.6**, 2.20 at
     2.0, and crosses 1.5 at 3.0. Under 1.6 needs no action; over 2.3, say so before
     printing. `nose_params.horn_drive_stress()` states the model it comes from.
3. **Servo into the cradle.** It drops in between the four fins, flange down onto
   the two pads. Drive the two M2 screws *through the Ø4.2 access holes in the
   disc* — you cannot reach them any other way, which is exactly why those holes
   exist.
4. **Arm onto the horn.** Horn into the arm's pocket, lever in the slot, then the
   servo's centre screw down through the counterbore. Torque comes from the slot
   flanks, not the screw.
5. **Power the servo and set the two end positions.** Latched = arm along ±X.
   Released = 30° from there. Watch it sweep: the arm must clear the cradle fins
   (0.606 mm at the worst angle) and never touch the seat bore.
6. **Bulkhead module into the ring.** It drops onto the annular seat at z = 47.5
   and lands on the two screw lobes at 135° and 315°. **Two M2.5 × 8 — not × 10**,
   which bottoms in the 6 mm pilot before the bulkhead is down on the seat and holds
   that seat open. See §4.
7. **Hinges.** For each side: knuckle of one half between the two ring lugs, one
   torsion spring in each 5.5 mm gap, then push the Ø2.0 pin through — the pin
   threads lug, spring, knuckle, spring, lug, so it goes in last and holds the lot.
   Each spring's **outboard leg drops into the lug's seat and its inboard leg into
   the knuckle's**; you will feel both find their holes. The spring is free at a 170°
   included angle and the seats stand 70° apart with the nose shut, so it arrives
   already wound 100° and there is no "which way round" to get wrong: **if it is in
   both seats it is pushing the half open.** All four are the same hand — two of the
   four therefore *unwind* rather than wind, which grows the mean coil to 3.98 mm and
   is accounted for (the unwound far edge is checked against `POCKET_FREE_R`, not just
   the wound one). Going to thicker wire is fine and §4a has the table; the Ø0.50 is
   only at **49% of its allowable stress**, so the limit is the 5.5 mm gap, not the
   steel.
8. **Dowels — before you test the latch, not after.** Four Ø3 rods cut to **6.5 mm**
   (or four printed `seam_pin`s).
   Glue each one **bottomed into one half's socket** and leave the opposite socket
   dry. All four in the same half is fine; so is two and two. What matters is that
   **no rod is glued at both ends** — a rod fixed in both halves is a pin through the
   seam and the nose will not open. Fitting them now means the twenty cycles in the
   next step exercise the dowels withdrawing, which is the thing worth exercising.
   They locate the seam and stiffen it; they are not fasteners, and they must not set
   the closed position.
9. **Check the latch by hand. The order matters, and it is the opposite of what you
   would guess.** The arm sits *over* the hooks, so you cannot press the halves shut
   against a latched arm — the feet have nowhere to go.

   **Hold the nose with the hinge line vertical, or nose-up, for this test.** The
   springs deliver 20.40 N·mm per half against 17.24 N·mm of worst-case gravity —
   **1.18×** — so nose-down a half *does* lift its own weight, but only just, and it
   will crawl rather than fly open. Hinge-line vertical takes gravity out of the
   moment entirely and is what you want while learning the latch sequence. In flight
   it is moot: the whole rocket is in free fall at apogee and gravity has no moment
   about the pin at all. See §4a.
   - Put the servo in **RELEASED** first, so the arm is clear of both hooks.
   - Press both halves shut against their springs. Each hook's web drops past the arm
     on the inboard side and the foot swings under it.
   - Holding them there, sweep the servo to **LATCHED**. The arm advances over both
     feet, climbing each foot's lead-in ramp, and the ramp cams the halves the last
     fraction of a millimetre shut. This is the expensive direction: 9.4 N·mm.
   - Let go. **The halves should stay shut with the servo unpowered** — the ramp is
     self-locking with a 1.75× margin. If they creep open, the ramp faces need a
     touch of dry lubricant, not more spring.
   - Sweep to RELEASED. Both halves should fly open.

   Twenty cycles before you fly it, and watch the *first* two degrees of each opening —
   that is where a dowel would bind if one is going to.
10. **Fasten it to the airframe — last, and with the nose in the tube.** Push the
    nose home until the **shoulder lands on the tube's forward rim**; that, not the
    screws, is the datum. Mark 13.21 mm back from the rim on the two seam
    meridians — the split line is the most visible feature on the closed nose, so
    you can find them without measuring the azimuth. Drill **Ø3.2 through the tube
    wall only** (it is 1.47 mm thick there; a 3.2 mm bit will punch through it in
    one turn, so back off before you reach the nose), then drive an **M2.5 × 8**
    self-tapper into each pilot. If a screw feels tight before the head lands, back
    it out and check the hole is on station — it should never bottom. **If you are
    going to be off, be off toward the aft**: the hole has ±0.35 mm of free play, and
    past that an error toward the rim pulls the nose out of the tube while an error
    away from it just binds against a shoulder that is already seated. Check the
    shoulder is still tight against the rim once both screws are in.

    Do this after step 9, not before: with the screws in, you cannot get the
    bulkhead module back out without removing them again.

---

## 6. Packing the 30 in chute

**Does a 30 in chute fit? A flat-cut nylon one, yes. A high-drag one, only just, and
the big ones not at all.** This section used to answer with a cavity volume, which is
the wrong number, and it used to say "room to spare", which was not warranted.

**The right number is the largest right CYLINDER, and it is about half the cavity.**
`cavity_volume()` integrates `πr²` down the profile: it is blind to the two latch
tongues, the four dowel pads and the four dowel rods, it starts at the split rather
than at the bulkhead face, and — decisively — **a deployment bag cannot taper.** So the
cavity was re-measured by sectioning the exported `out/nose_closed.stl` at 0.5 mm and
casting 360 rays per section (`_scratch/_chute_envelope.py`):

| measure | value | what it means |
|---|---|---|
| `cavity_volume()` above the split | 247.3 cm³ | the number this section used to quote. Blind to intrusions, and starts 2.41 mm too high. |
| free void above the bulkhead face, measured | **253.3 cm³** | all the air there is |
| **strict largest right cylinder** | **Ø40.12 × 95.0 mm = 120.1 cm³** | clears every fin and pad at every azimuth — a rigid tube would fit |
| soft-bag cylinder (median azimuth) | Ø45.39 × 78.5 mm = 127.0 cm³ | every intrusion is a **fin, not a throat**, and fabric deforms round a fin. Measured off the exported half at 0.25° of azimuth (`_scratch/_fin_azimuth.py`), the pair blocks **33.5° of 360 at worst** — and see below, because this row named the wrong feature for a long time |

The two cylinder numbers agree to 6%, so **the bag budget is 120–127 cm³** and does not
depend on which you prefer. The entry is Ø57.4–61.1 over 344 of 360 azimuths; the
chokes further up are Ø40.1 at z 120 and Ø19.8 at z 180 (the dowel pads), which is why
the cylinder is 95 mm and not the full 198 mm of cavity.

**What the bag actually squeezes past, by height** — for the pair of halves, out of 360
azimuths, walked at 0.25°:

| z band | blocked | what is blocking it |
|---|---|---|
| 52.4 – 58.4 | **33.5°** | latch gusset **and** root-post pad, on opposite meridians |
| 58.4 – 62.0 | 11.5° | the latch gusset alone (the post pad is 6.0 mm long and has ended) |
| 62.0 – 119 | **0°** | nothing at all — bare skin all the way round |
| 120 | 16.0° | the four dowel pads |
| 180 | **29.0°** | the four dowel pads, and this is the widest blockage anywhere |

This table replaces "the two latch tongues occupy 16 of 360 azimuths — two 8° fins",
which named the wrong feature. **The gussets end at z 62.0**, so over most of the
cylinder's height the thing a bag deforms round is a *dowel pad*, and the widest
blockage in the whole cavity is at z 180 where no latch part exists. The old 8° came
from the 0.6 mm gusset measured at its inboard face — and the blocked angle depends on
the radius you ask at, because every intrusion here is a prism in y and a fixed 3 mm
y band subtends more angle at smaller r. Neither cylinder number moves: both are set
at z 120.

**Against that:**

| 30 in canopy | pack volume | on the 120.1 cm³ cylinder |
|---|---|---|
| **flat / cruciform nylon**, 1.1–1.9 oz, + lines + bag | 44–122 cm³ | **0.98–2.73× — fits** |
| **high-drag** (toroidal, elliptical; e.g. Fruity Chutes IFC-30 … CFC-30) | 121–261 cm³ published | **0.46–0.99× — the small end only just, the large end not at all** |

So: **buy a flat-cut or cruciform 30 in canopy in thin ripstop and it goes in with
margin.** If you have your heart set on a toroidal 30 in, measure its stuffed volume
before printing — a 1.1 oz IFC-30 will go, a heavier CFC-30 will not, and no amount of
packing technique recovers a factor of two. Both figures are re-derived in
`nose_params.self_check()`, so they print every time anything is built.

- The canopy goes in a **deployment bag**, not loose. The bulkhead is a solid disc
  precisely so the canopy can never reach the servo, the horn, the arm or the
  springs.
- **Pack the bag as a cylinder, not a ball.** The governing dimension is Ø40 × 95, and
  a spherical pack of the same volume is Ø61 — wider than the choke at z 120.
- Pack from the base up, into one open half, then close both against the springs
  **with the servo already in RELEASED** and sweep it to LATCHED to take them. Same
  order as assembly step 9 — you cannot push the halves shut onto a latched arm.
- **Nothing pushes the chute out.** There is no piston and no ejection gas in the
  nose. The pack leaves because the airframe is falling away from it while the
  shock cord is anchored *in the body tube*, not to the nose. Opened 100°, the
  axis is clear for 40 mm above the bulkhead face — there is a straight way out.
- **Two Ø4 mm vents per half at z = 60** (45° and 135°, i.e. 45° off both the seam
  and the hinge). **Do not paint over them, tape them, or fill them.** This is the
  single largest load in the whole design and the only one that can be created by a
  finishing mistake:

  | Vent state | Load on the latch |
  |---|---|
  | all four clear | **0.60 N per half** (springs; the air term is 0.0003 N) |
  | sealed — painted or taped | **255 N per half** |

  That is a factor of **430**, and it is the reason this table exists rather than a
  sentence. The air term is quoted at the built Ø4.0; `_scratch/_loadpath_out.txt`
  computed 0.002 N at the Ø2.5 the sizing pass had assumed, and cavity lag goes as
  1/area², so the vents growing to Ø4 divided it by 6.6.

  Sea-level air carried to a 1500 m apogee is a 16.8 kPa differential across a
  247 cm³ cavity, and it acts outward on the whole inner skin. Vented, the vent does
  not *reduce* that load, it **deletes** it. The four Ø4 holes total 50.3 mm² — 2.6×
  what the sizing analysis called for and 178× the pure flow requirement — so three
  of the four can be blocked and the air term is still only 0.005 N. The seam and the
  cord hole do leak, but a leak is not a vent budget.

  Note which way round the flight loads run: **boost is self-latching** (dynamic
  pressure presses the shells inward and aft, and inertia presses the nose down into
  the ring). Apogee is not. Drag is never the latch-sizing load on this design.

---

## 7. What was checked, and against what

`nose_verify.py` runs **356 checks on the exported STLs** — not on the build
scripts, because what the printer gets is the STL. Exit 0, all passing.

It was 350, and the six new ones are all from the horn: the governing-wall pair at
the hub recess, the blade-envelope pair at ±`HORN_LEVER_W_FULL`, and one probe on the
aft side of the widened cradle notch (see below). Four other probes were **coordinate
literals the changed parts overtook** and now read off `nose_params` — two on the arm's
own width, two on the fin notch, which `fin_notch_half()` widened 10.5150 → 12.2326 the
moment `LATCH_ARM_W` reached 10.50. Those two failed on the first run after the change,
which is the harness doing its job: the probes were stale, not the geometry.

- All **five** printed parts **watertight and a single body**; mesh volume within
  0.03 cm³ of the CAD solid. The CAD figures are literals in `nose_verify.py`,
  deliberately — importing the part scripts to ask them would make the check
  tautological — so they have to be re-read by hand when a part changes, and one of
  them (`half_shell`) was 0.09 cm³ stale for a while, hidden inside a 6% tolerance.
  That 6% floors at 1.0 cm³ and so says nothing at all about a 0.045 cm³ `seam_pin`,
  which is why the pin's volume is re-checked tightly against the closed form
  (cylinder less two chamfer annuli) in its own block.
- All five fit the 300³ bed in their print poses.
- **`seam_pin` is chamfered at BOTH ends, proved by a probe pair inside and outside
  each taper.** Its cutter is the annulus *outside* the taper; subtracting the
  frustum instead — the easy inversion — yields a tube with a countersunk hole,
  which is watertight, one body, the right bounding box and useless. And its widest
  point as exported is measured against the radius the withdrawal sweep allows, not
  against the nominal bore, so a printed pin that survived tessellation fat enough
  to jam a half would fail here rather than on the bench.
- Collar OD by radial ray **32.7586 mm** = the airframe radius exactly. Spigot OD
  **31.1135** measured (nominal 31.1207; the 0.007 mm deficit is one facet chord),
  giving **0.17 mm** radial clearance in Mbody's socket.
- Exported ogive vs `nose_profile` at four stations: agreement within **0.009 mm**.
- Every feature probed at the azimuth/coordinate it **is** at *and* one it should
  **miss** — spigot step, collar, seat land, both screw lobes, both pilots, both
  hinge lugs and their pin bores, thrust pad, both cradle fins and the V notch,
  both flange pads, both hook slots, cord hole and its chamfers, three access
  holes, horn pocket and slot, all four dowel sockets (**4.50 mm deep, backed by
  material, and the Ø3.3 bore radius pinned by a probe pair either side of its
  wall**), both vents, knuckle, hook web, hook foot and gusset, plus 25 probes
  confirming there is nothing on the y < 0 side of a half.
- **Two pairs were added for the horn, and they are the ones that answer the fit.**
  The first straddles the **governing wall**: void inside the Ø7.73 hub recess, solid
  0.3 mm outboard of it, on both flanks — that 1.385 mm wall is the thinnest thing in
  the part and the one a slot-width edit would eat first. The second is the
  **blade-envelope pair at ±`HORN_LEVER_W_FULL`**, i.e. at x = ±11.25, void at
  `HORN_SLOT_W / 2 − 0.4` and solid at `+ 0.3`: it reads the slot's width *at the
  extremes of the 22.5 mm the measured blade is full-width over*, on both spurs. Every
  earlier probe sat at x = 10, inside that span, so a slot that pinched anywhere
  outboard of it would have passed. Nothing in the CAD asserts can catch that — the
  slot is one `Box` there and a `Box` is right by construction — which is exactly the
  class of error this file exists for.
- **The gusset is probed at x = 27, not out at the wall.** The obvious place to look
  is just inboard of `TONGUE_X_WALL`, and it is the wrong place: r there is 30.84,
  *inside the skin*, so a solid answer is the shell wall answering for the gusset and
  the probe proves nothing. x = 27 is 3.7 mm inboard of the cavity wall and can only
  be gusset. Four probes walk its full 9.59 mm of depth and one confirms the diagonal
  has **ended** at `GUSSET_Z_TOP` rather than run on.
- **The half shell comes to a point, and the harness says so.** Three probes at the
  apex: solid 1.0 mm down, nothing above `Z_SHELL_TOP`, and nothing in the last
  **0.5766 mm** up to the true `Z_TIP` — which is `SEAM_SETBACK / tan(TIP_HALF_ANGLE)`
  exactly. At `Z_SHELL_TOP` the outer radius is 0.150004 mm, equal to `SEAM_SETBACK`
  to four decimals, so the seam plane is *tangent* to the section circle there and the
  half ends in a mathematical point rather than a flat. See §8 risk 14.
- **The arm's section is measured off the mesh, not derived.** A 0.025 mm grid on the
  x = 0 plane finds **36.49 mm² of area at S = 38.08 mm³** — 59% of the 88.20 mm² gross
  gone to the horn pocket and its slot, leaving **σ 0.348 MPa, 115× inside in-layer
  ABS**. Those were 10.69 mm² and S = 4.19 mm³ — 84% gone — at `LATCH_ARM_W` 8.0, where
  the hub recess broke clean out through both flanks and the section hung on the pocket
  floor alone. Widening the bar to 10.50 for the measured horn keeps 1.385 mm of flank
  through x = 0 and multiplies S by nine, which is the single largest structural
  side-effect of that change and was not its purpose. That plane is also where the
  bending moment peaks (one hook's worth of load from each side, in the same sense), so
  the weakest section and the worst-loaded section are the same section, which is the
  only reason the number is worth measuring. The harness's thresholds moved with it,
  10.0/4.0 → **30.0/30.0**: left where they were they could no longer fail for anything
  worth catching, including a revert to the 8.0 bar the measured horn does not fit.
- **The two root posts, five probes.** Present on both diagonal corners of the ring's
  collar top, **absent on the other diagonal** — there are two, not four, and that is
  what makes each half meet only its own — absent above `POST_H`, and absent just
  outboard of `POST_D/2`. The wrong-diagonal probe is the discriminating one: a
  mirrored pair would pass every other check here.
- **The six spring-leg seats** (two in the knuckle end faces, four in the lugs'
  inner faces) get the dowel sockets' treatment plus one check that is specific to
  them: bored where the leg goes; **blind**, so a leg driven in cannot come out the
  back and the two seats in one knuckle do not meet in the middle; Ø0.9 and not
  wider, pinned by a probe pair either side of `TORSION_SEAT_D/2`; **solid midway
  between the seat and the pin bore**, because a cut that broke through into the
  bore would foul the leg on the pin and would still have passed `assert_cut` —
  breaking through removes *more* material, not less; and **2.05 mm deep measured
  by walking down each seat's own axis**, because a shallow seat passes every point
  probe above while silently eating the 1.30 mm of guaranteed engagement §4a
  spends.
- **The foot's lead-in ramp is proved as a ramp, by a pair.** One probe cannot tell
  a ramp from a flat, and a flat foot is a jam: the same z is solid in the bearing
  land near the split plane and void at the foot's far edge. That pair is what says
  the arm has somewhere to enter.
- **The two retention pads and pilots**, which get their own treatment because they
  are the only feature whose failure mode is a screw appearing inside the servo bay:
  each pad solid at its own azimuth and absent at 90° and 270°; its chord limit
  proved from both sides; its 45° top cone proved as a cone rather than a step; each
  pilot bored at r = 30 where the wall is otherwise unbroken, **walked down its own
  radial axis over 25 stations** to show the bore runs the full 6.92 mm, then walked
  back through the floor over 8 stations to show **0.70 mm of its 1.00 mm thickness**
  is unbroken — 0.15 mm short of each face, because a probe closer than that to a mesh
  facet is not worth trusting, and the check reports the span it actually covered
  rather than rounding it up to the whole floor; material 1.6 mm to each side of the
  pilot and 0.5 mm above its top edge; and the countersunk mouth proved as a flare by
  one probe each side of it.
- **No interpenetration** in any pair, including the halves opened 5/15/30/60/90/
  110° against the ring, each other and the bulkhead, and the arm at seven angles
  through its sweep.
- **The four dowels withdraw**, checked separately and *finely*, because the sweep
  above cannot see it. Every angle it samples starts at 5°, and a dowel that binds
  does it in the first two degrees and is long clear by five — so that sample set was
  blind to exactly this failure, and was. The rods as actually glued are now stepped
  against the far half at **0.25° increments from 0.25° to 6°**, plus 10/30/90°.
- **The latch is real contact, and it resists.** Zero overlapping samples and
  ≤ 0.1 µm gap across the **20.5–22.14 × 0.15–1.15 mm bearing land** (a 9 × 5 grid inset
  0.2/0.1 mm from its edges), on a deterministic grid — so the foot lands flat on the
  arm, not on a corner. The land, *not* the 0.15–3.15 mm footprint: outboard of
  `RAMP_LAND` the foot's top deliberately falls away on the lead-in ramp, so a grid
  over the full y band would measure the ramp's drop and call it a gap. And separately, in the
  direction that actually matters: rotating a half *open* drives its foot **into** the
  arm's underside, and rotating the arm *out* leaves that same motion unobstructed.
  Contact alone is not resistance; that pair of checks is the one this project did not
  have when the latch was a flat blade resting on top of the bar, and it is why the
  bug was found.
- **The root post withdraws too, and its neighbour never touches.** The post sweep
  reuses the dowels' fine step — 0.25° to 6° at 0.25°, plus 10/30/90° — and the posts
  it sweeps are cut out of the *real* ring by a plane at `Z_RING_TOP`, so the root
  fillet in the check is the built fillet and cannot drift from `base_ring.py`
  (19.42 mm³ against 18.85 for two plain cylinders). Two claims in one pass: half A's
  own post comes out, and half B's post — sitting at y −4.5…−1.9, on the wrong side of
  A's seam — never touches half A at any angle.
- **A real MG90S fits:** body envelope clear over 1323 points, both flange ears
  clear, both flange pilots ringed by material in all 16 directions.
- Assembled bbox x ±32.759, y ±39.110, z 0…248.389.

`inspect refs --facts --planes --positioning` returns `ok: true` with no warnings and
no errors on all **nine** STEP files: the five parts as a single solid each
(**123 / 94 / 51 / 21 / 5** faces and **353 / 242 / 142 / 54 / 7** edges for
`half_shell` / `base_ring` / `bulkhead` / `latch_arm` / `seam_pin`), the two fused
scenes as **14 bodies each**, and the two linked assemblies as 5 shapes totalling
**412 faces and 1144 edges** — exactly the sum of the flying parts
(2 × 123 + 94 + 51 + 21 = 412, and 2 × 353 + 242 + 142 + 54 = 1144), so the
assemblies really are the parts and not a copy of them. `seam_pin` is the ninth file
and is deliberately *not* in the linked assemblies: it is loose hardware, and putting
it in a scene would imply the model knows which half each rod is glued into.

The assembly placements are cross-checked two ways. In `nose_assembly.py` the
halves and the arm are positioned by build123d `RevoluteJoint`s on the real pin
and shaft axes, and every resulting vertex is asserted against the datum
arithmetic (`hinge_m`) to better than 1e-6 mm; the bulkhead is positioned by the
ring's seat face, which fails loudly the day `SEAT_Z1` and `Z_BULK_BOT` stop
agreeing. `nose_linked.py` then re-derives the same five placements as 4×4
matrices over the exported part STEPs and asserts they match the fused scene to
6e-14 mm.

### What in this README is *not* traceable to the model

The doctrine here is that a number quoted as fact should be re-derivable by running
something. Every dimension, clearance, area, moment and sweep above is. These are the
exceptions, and they are exceptions because no amount of geometry can settle them —
each one is a handbook value or an estimate, and each one is load-bearing somewhere:

| Number | Where | What it really is |
|---|---|---|
| ABS **~45 MPa** in bearing | §2, risk 11 | Handbook compressive figure for bulk ABS. Not measured, not print-specific, and the margins quoted against it (212×, 594×) are so large that being wrong by 2× changes nothing. |
| **~40 MPa** in-layer vs **~11 MPa** across the bond | §3 | Handbook figures for printed ABS. The *ratio* is what the print-orientation argument rests on, and that ratio is not controversial; the absolute values would move with your printer, chamber temperature and filament. |
| packed-canopy springback **10–30 N** | risk 11 | An order-of-magnitude guess, stated as one. It is the largest unmeasured load in the design, which is exactly why risk 11 re-runs the bearing numbers at 50 N instead of arguing about it. |
| canopy pack volume **44–122 cm³** flat-cut, **121–261 cm³** high-drag | §6, `nose_params.py` | The only genuinely external numbers left in §6. Flat-cut is estimated from canopy area × fabric thickness plus lines and bag; high-drag is *published* vendor stuffed volume. What they have to fit in — the **120.1 cm³** largest right cylinder — is measured off the exported mesh. This is the one place in the document where being wrong by 2× changes the answer, which is why §6 says measure your canopy. |
| ABS density **1.04 g/cm³** | §1, risk 13 | Nominal. All masses scale linearly with it. |
| music wire **springback 5–15%** on release | §4a, `spring_jig.py` | Handbook range for A228 at a spring index near 7. It is what turns the Ø3.0 mandrel into `D_mean` 3.85, so it sets the spring torque — but the whole 0–24% band lands inside the acceptance box, and past 24% the jig's ring refuses the coil. That is the point of gauging instead of calculating. |
| A228 **allowable 1700 N/mm²** | §4a | Conventional torsional-bending allowable for music wire, roughly 0.7 × tensile. The spring runs at 831, so this one has a factor of 2 in hand. |
| MG90S **216 N·mm** stall | §4 | Datasheet, at 4.8 V, and datasheets flatter. The servo is used at **8%** of it (12.5 N·mm to release, 17.7 to re-engage), so this is the one place a 2× error is genuinely irrelevant. |

Everything else — including every number added or corrected in §4a — comes out of
`nose_params.py`, `nose_verify.py` or `_scratch/`, and can be reproduced by running
them.

---

## 8. Residual risks — read this before you fly it

> **Before anything else: sealing the vents turns 0.60 N into 255 N.** A factor of
> **800.** That is the largest load in the design and the only one you can create
> *after* the model is already correct — with a coat of paint, a strip of tape or a
> smear of filler. If you finish this nose, mask the four Ø4 holes and check they are
> open afterwards. See §6.

1. **The hinge fairing stands 6.35 mm proud of the 65.52 mm OD**, at ±Y. It has
   to: the pins live outside the tube. x stays within 0.000 mm of the OD, so
   **put your rail guides at ±X.** This is drag you are paying for the simplest
   possible hinge.
2. **Chute extraction is not proven, only argued.** Nothing ejects the pack; it
   relies on airframe drag pulling it out via a shock cord anchored in Mbody.
   Ground-test it: hang the rocket nose-down and see if the pack falls out when
   the servo fires.
3. **The shock cord must anchor in the body tube, not the nose.** If you tie it to
   the bulkhead you have made the nose the recovery load path, and the whole descent
   load then runs through four M2.5 screws in printed ABS — two into the ring's screw
   lobes and two into the spigot's retention pads. They are sized to keep the nose in
   place, not to catch a rocket.
4. **Pin retention is a Ø2.10 bore on a Ø2.0 pin** and nothing else. Add a dab of
   epoxy on the outer lug face, or bend one end of the pin, before flying.
5. **The horn's blade thickness is the last unmeasured dimension in the design, and
   it is the only load-governed one in the arm.** Everything else about the horn has
   now been measured off a real part: hub Ø7.43 × 5.00, blade 36.0 tip to tip and
   7.2 wide across its middle 22.5 mm. The thickness in z is still the 1.6 mm the
   reference solid has always drawn. It decides the flank stress, and *thicker is
   worse* — the force per mm of flank is torque ÷ bearing length² and does not depend
   on the thickness at all, so thickness only lengthens the lever down to the flank's
   root. **2.70× against a stalled servo at 1.6 mm; 2.20× at 2.0; 1.49× at 3.0.**
   Measure it, and if yours is over 2.3 mm say so before printing.
   `HORN_POCKET_DEPTH` is no longer the risk it was: the measured hub came in at 5.00
   rather than the 5.70 that had been assumed, so there is 1.80 mm under the screw head
   where there used to be 1.10, and the ceiling is 6.40. It is still a
   **measure-before-printing** number — a pocket deeper than your hub means the centre
   screw clamps thin air — but file a tall hub rather than deepening the pocket,
   because going past 6.40 costs `HORN_ACCESS_D` 5.0 → 6.0, a bulkhead reprint and a
   longer centre screw. See step 2 and §4.
6. **The two retention screws are the only thing holding the nose in, and you drill
   their airframe holes yourself.** The joint under them is a plain slip fit with
   0.1638 mm of clearance and no key. Two thresholds, and they are 6× apart: **beyond
   ±0.35 mm** off station the screw starts dragging the nose axially instead of just
   passing through, and **beyond ±2.05 mm** its tip no longer lands in the countersunk
   lead-in cone at all and it is boring into the spigot wall. Between the two it will
   still bite, and will still be wrong — the direction that matters is **too close to
   the rim**, which holds the joint open (see §3). Measure from the tube's forward rim,
   with the shoulder seated, and check both screws bite *and* that the shoulder is
   still tight against the rim afterwards, before you fly. Then route the servo wire
   with a little slack anyway — the screws stop the nose rotating, but only while they
   are in.
7. **The flange pads print as a 13.8 mm bridge.** See §3.
8. **The cavity crown is a 7.00 mm bridge with a 311%-of-a-bead step leading into
   it.** No support, and none wanted — but this is where the part will look worst
   inside, and if it sags it is the slicer's bridging settings, not the model. See §3.
9. **The seam dowels now have a 5.90× margin — but only because the rods are 6.5 mm.**
   The worst of the four needs 0.0254 mm of the 0.150 mm of clearance in its bore, at
   0.72° of opening, and is clear by 0.77°. That is real margin rather than the 1.79×
   it was at 8.0 mm — so **do not lengthen the rods past 6.5 mm**, do not shorten the
   sockets, do not glue a rod into both halves, and if you re-site a station, re-run
   `nose_params.py` and let `dowel_withdrawal()` sweep it. The skew a rod has to
   survive grows with the **square** of its reach into the far half; the withdrawal
   that relieves it grows only linearly. A dowel that binds looks exactly like a servo
   that failed.
10. **The 0.2 mm root gap is a gap on purpose.** The shell root stands 0.2 mm clear
    of the ring's top face and stays clear, because the knuckle can only drop 0.15 mm
    before the pin bottoms in its bore. `ROOT_CHAMFER` is **0.3 mm** and is an edge
    break for the airflow — it is *not* a joint relief. Do not increase it "to be
    safe": at 0.6 mm it combined with the ring's own 0.4 mm chamfer across that gap to
    cut a 1.2 mm × 0.6 mm groove all the way round the airframe.
11. **The latch is dimensioned to the springs, and the springs are the smallest
    thing that will ever pull on it.** 0.60 N per half puts **0.327 MPa** on the foot's
    **1.83 mm²** flat land — a **138×** margin, which is not a boast, it is a warning
    that the steady-state number tells you nothing. The loads that are *not* in it are
    packed-canopy springback (order 10–30 N across both shells, never measured here)
    and handling. Sized to 50 N per half instead, the flat land sees 27.3 MPa (1.6×)
    and the bedded-in 4.91 mm² footprint 10.2 MPa (4.4×) — still standing, but that is
    the honest margin, and the ledge is narrower than it was (1.64 mm, not 2.63) because
    `LATCH_ARM_R` came in to 22.0. **Do not design a variant of this latch to 0.60 N.**
12. **The spring margin over bench gravity is 1.18×, and 1.18× is not "fine".**
    20.40 N·mm per half of spring moment against a worst-case 17.24 N·mm of gravity
    moment. It does not bite in flight, because at apogee the rocket and both halves
    are in free fall together and gravity opposes nothing (60° in 144 ms, computed in
    §4a); on a bench, nose-down, a half lifts its own weight with 16% to spare and
    will crawl open rather than snap. Anything that eats 16% — a tight pin bore, a
    burr in a leg seat, a spring wound at the fat end of the springback range — puts
    it back under 1.0. So:
    > **Ground-test with the hinge line VERTICAL first**, confirm the mechanism, and
    > only then check nose-down. Nose-down is the *worst case*, not the demonstration.

    This number was **0.10× until the 2π error in `TORSION_RATE` was found**, and the
    fix is what moved it — not a geometry change. The pocket is unchanged at
    `TORSION_GAP` 5.5. If you want real margin, the wire is the knob: Ø0.56 on the same
    jig gives **1.83×**. The full derivation, the springback sweep and the substitution
    table are §4a and `spring_jig.py`. See also §5 step 9.
12a. **The coil count cannot be a round number, and this is easy to get wrong twice.**
    The two legs leave opposite ends of the coil, so the leg angle *is* the wrap, and a
    170° free angle forces `n mod 1 = 0.4722`. `TORSION_COILS` read 8 for a while; 8 is
    not buildable and reading it as buildable overstated the torque 5.5%. Do not
    "clean up" 8.472 to 8. Assertion 10 in `spring_check()` will stop you.
13. Mass was explicitly out of scope, as asked. **104.1 g solid, with its centre of
    mass at z = 75.86 mm** — i.e. **173.1 mm aft of the apex**, not at 248 mm, which is
    what this line used to say; 248 mm is the apex itself, and putting the whole mass
    there would overstate the moment by more than a factor of three. Most of it is low
    down: the base ring is 40.5 g of the 104.1 and the two shells contribute 25.5 g
    each with their own CGs at z = 120.6. All four figures are measured off the
    exported meshes. It will still move your CG forward. Check stability before you
    fly.
14. **The tip is 0.577 mm short of the true apex in CAD, and there is nothing useful to
    do about it.** Each half is cut back `SEAM_SETBACK` = 0.15 mm from the split plane,
    and near a 14.9° half-angle apex that costs
    `SEAM_SETBACK / tan(TIP_HALF_ANGLE)` = **0.5766 mm** of height. It cannot be
    reclaimed by moving the seam: at `Z_SHELL_TOP` the section radius *is* 0.150 mm, so
    the seam plane is tangent to the circle and the half already comes to a point. And
    it is not the number that governs — **the slicer's first layer alone costs
    1.3454 mm, 2.33× the CAD deficit**, because a 0.15 mm-radius spire cannot be
    printed. So the assembled cone measures ~248.39 mm to the CAD tip and less than
    that off the printer, against 248.9655 nominal. If you want the last millimetre,
    fill and sand it; do not chase it in the model.

---

## 9. Note on the earlier clamshell

`_clamshell/` — the earlier, far more elaborate clamshell design — **is no longer on
disk.** This README said "untouched, exactly as it was" for a long time after it went,
and the way that surfaced is worth recording: `nose_profile.py` carried a fallback
that read `_clamshell/ogive_measured.npy`, so `python nose_profile.py` died on a
`FileNotFoundError` and put the numbers that justify its own docstring in a traceback
instead of a report. The measured bias is a constant in that file now, and the primary
table is resolved from a tuple — sibling `_clam/ogive_prof.npy` first, local copy
second, so a re-measurement upstream is picked up rather than shadowed by a stale
local one.

What survives of the old design is the one thing that was measurement rather than
design: **`_clam/ogive_prof.npy`**, the measured ogive profile, which is the only file
in that directory. Everything in `_nose_simple/` is built from it.

Do **not** use `ogive_measured.npy` if you find a copy of it. It was produced by
taking the maximum vertex radius per z-slice, which over-reads a taper by up to
0.59 mm; the "base flare" it appears to show is an artifact of the estimator, and
`nose_profile.bias_vs_raw()` reports the +0.3468 mm mean / +0.5859 mm worst so that
nobody re-derives the flare from it.
