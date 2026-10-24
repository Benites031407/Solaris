# 38 mm Horizontal Rocket Motor Test Stand

A mostly-3D-printed static test stand for a 38 mm OD KNSB motor, built around a
500 mm length of 2020 aluminium extrusion and a 500 kgf cylindrical compression
load cell.

---

## 1. How it measures thrust

The motor is **not clamped**. It is a free sliding fit in two printed guide
rings and it pushes an inline load cell:

```
motor fwd closure -> thrust_cap -> [Ø40 boss, FLAT ON the cell's FLAT end face]
   -> load cell body -> cell_spacer stack -> cup floor -> reaction wedge
   -> saddle -> [BUTT JOINT] -> thrust reaction foot -> M8 lag screws
   -> baseboard
```

There is **no washer and no load button** in that chain. Earlier revisions had
both, on the assumption that the cell had a crowned button like most compression
cells. It does not: the manufacturer's model shows **both ends are flat,
full-diameter annuli**, so the cap now bears flat on steel over Ø24–Ø40
(804 mm², 2.5 MPa at the 2 kN design load) and the parts in between are gone.
Deleting them improved the joint — one face of that washer was always printed
plastic, so all it ever did was funnel the same load through a smaller circle.

Three decisions make this work, and each one is there to kill a specific error:

**The motor slides; it is not clamped.** The guide rings carry the motor's
weight only. Friction therefore acts *in parallel* with the load cell, so the
error is bounded at `mu x motor weight` — 0.8 to 3.5 N, i.e. **under 0.7 % of a
500 N peak**. If the motor were clamped, an unknown fraction of the thrust would
bypass the cell entirely and there would be no way to know how much.

**The motor axis and the cell axis are collinear** at z = 65 mm. A cylindrical
compression cell reads pure axial load and its output is corrupted by bending
moments. Any offset between the two axes would apply thrust x offset as a
moment straight into the cell.

**The thrust does not pass through the rail.** See section 3 — this is the one
structural conclusion that is easy to get wrong.

### Expected performance

| | |
|---|---|
| Load cell full scale | **5000 N** (nameplate "MAX CAPACITY KN. 5" = 500 kgf) |
| Expected motor peak | ~300–900 N = **6–18 % of full scale** |
| Cell nonlinearity at 0.05 % FS | ±2.5 N |
| Realistic total uncertainty | **±3 to ±6 N** after dead-weight calibration |
| Guide friction error | +0.8 to +3.5 N, always *reducing* the reading |
| Mechanical resonance | ~900–1400 Hz |

**Honest caveat on the cell choice.** A 500 kgf cell measuring a 500 N motor
uses a tenth of its range, so you pay roughly ±3–6 N of uncertainty that a
100 kgf cell would not cost you. In exchange it survives a CATO without being
destroyed. For characterising a KNSB motor that is a good trade, but do not
expect to resolve fine ignition-transient structure.

**The real bandwidth limit is your ADC, not this stand.** The mechanics resonate
near 1 kHz, but an HX711 samples at 80 SPS — about 160 points across a 2 s burn.
That is enough for total impulse and average thrust, and too coarse for the
ignition spike. If you want the transient, use an ADS1232/ADS1256 or an
instrumentation amp feeding a faster ADC. Total impulse is an integral and is
tolerant of a low sample rate; peak thrust is not.

---

## 2. The cell is measured and identified — and it changed the design

Superseded. This section used to carry two placeholders and a promise that
**"the reaction tower never needs reprinting"** whatever the cell turned out to
be. The promise did not survive the measurement, and the honest thing is to say
so rather than quietly edit it out.

Measured 2026-08-11: **Ø57 × 80.0 mm long, with a central M20 × 1.5 threaded
hole.** Both figures were 40.0 placeholders. Both broke a documented limit — the
old text said in as many words that a cell over 49.4 mm in diameter would not fit
and the tower would have to change. Ø57 is over 49.4, so it did.

**Then the cell was identified, and that mattered more than the tape measure.**
The nameplate reads **tecnotest, MODENA – ITALY / MOD. AP 032/005 / MAX CAPACITY
KN. 5 / Nr. 641 / 500 Kg**. That model is the **AEP TCE Ø57**, and AEP publishes
[the datasheet](https://www.aep.it/wp-content/uploads/2020/02/TCE.pdf) *and a
solid model*. `ref/TCE_57.stp` is now in this directory and the assembly imports
it, so the interference check runs against the manufacturer's geometry rather
than against my own guess — which only ever proves the guess is self-consistent.

```python
LC_BODY_DIA = 57.2          # measured off ref/TCE_57.stp: cylinder r = 28.600
LC_BODY_LEN = 80.0          # flat end face to flat end face
LC_CUP_BORE = 62.0          # = 57.2 + clearance + 2 x 2.0 liner wall + fit
```

Five things in the shipped design were wrong, and the reference model corrected
all five:

| Assumed | Actually | Consequence |
|---|---|---|
| Crowned load button, 3 mm proud | **Flat annular end faces, both ends** | The washer and the button are gone from the BOM, and the contact plane moved 1.5 mm aft |
| M20 hole, one end or through | **Blind M20 × 1.5 × 18 mm deep in BOTH ends** | 44 mm of solid steel between them; a retaining bolt in *either* end is safe |
| Cable boss 20 mm wide | **40 mm across × 20 mm axial, 20.1 mm proud** | The 21 mm relief would not have passed it at all |
| Boss position unknown | **Axially centred**, mid-length | The relief can be a short window instead of a full-length channel |
| Cable leaves radially | **Rigid gland leaves TANGENTIALLY**, sideways | This is the change you asked for — see below |

> **What the geometry does not tell you, and you should still check with the cell
> in your hand:** the ends are flat and symmetric in the model, so nothing in the
> file distinguishes the load end from the base end. Fit the retaining bolt to
> whichever end sits on the cup floor and leave the other empty.

What that cost, and why:

| | Was | Now | Why |
|---|---|---|---|
| Cup bore | 50.0 | **62.0** | Ø57 cell + a 2 mm minimum liner wall |
| Cup depth | 45.0 | **85.0** | 80 mm body + a 5 mm spacer |
| Side plates | 20.7 | **26.7** | derived from the cup OD, not chosen |
| Tower volume | ~370 cm³ | **509 cm³** | the above, compounded |
| Tower saddle | 112 mm | **140 mm** | deeper cup + the reaction wedge |

Two of those are worth understanding before you print:

**The bore is 62 and not a round 65 for a reason.** 62 is the largest bore whose
cable channel floor still clears the saddle roof — it lands at z = 28.000, exactly
`ROOF_TOP`. A 64 mm bore would cut 1 mm into the roof the thrust passes through.
This is a hard geometric ceiling, not a comfort margin.

**The bigger cell made the thrust joint better, not worse.** Side-plate thickness
is derived from the cup OD, so growing the bore thickened the plates, and the butt
joint that carries the whole 2 kN went from 793.6 to **913.6 mm²** — contact
stress *down* from 2.52 to 2.19 MPa. The tower got heavier and stronger at once.

### ⚠ The cable boss and the sideways gland — the cell is not a cylinder

The cell carries a **40 × 20 mm rectangular boss standing 20.1 mm proud of the
Ø57.2 body at mid-length**, and a **rigid threaded gland** leaving that boss's
*side* face. That feature lands in the tightest region of the entire stand.

Here is all the room there is:

| Direction from the cell | Radial room | Why that is the limit |
|---|---|---|
| Any direction, unrelieved | **2.40 mm** | Ø57.2 cell in a Ø62 bore, and 2.1 mm of that is liner wall |
| Down, tower cable channel | 8.50 mm over 12 mm wide | and it **cannot be deepened** — the floor is already at z = 28.0 = `ROOF_TOP`. Far too small for a 20.1 mm boss regardless |
| Sideways, through the cup wall | 2.40 mm | and the relief would land where the ears are tapped |
| **Up, through the strap** | **unlimited** | 6 mm of wall (r 31 → 37), then open air |

So the boss is indexed **UP**. And because the gland is **tangential to the
boss**, boss-up is what makes the cable leave **horizontally** — which is the
orientation you want and the reason nothing here needs to change to get it.

#### The relief is a transverse WINDOW, not a full-length channel

It used to be a 21 mm groove running the whole 81 mm of the strap, because the
boss's axial length and position were unknown and a full-length channel makes both
irrelevant. They are measured now, so:

```python
LC_BOSS_SLOT_W   = 46.0     # across the strap
LC_BOSS_SLOT_LEN = 26.0     # = 20 mm boss + 3 mm clear at each end
LC_BOSS_SLOT_X0  = 27.0     # from the cell's load face
```

That is a **26 mm opening in the crown with 25 mm of roof kept aft of it and
30 mm forward**, instead of 75 mm of missing roof. Only `cell_strap` carries it.

**The width is set by the GLAND, not the boss.** This is the one number here worth
checking rather than trusting, because it is counter-intuitive: 41 mm clears the
40 mm boss comfortably, and still **fouls**. The gland's Ø16 collar leaves
sideways with its axis at z = `AXIS_Z` + 38.7, so it has to pass over the strap's
Ø74 outside diameter at the window's edge:

| `LC_BOSS_SLOT_W` | Clearance under the gland collar |
|---|---|
| 41 mm (boss + 0.5 a side) | **−0.10 mm — fouls** |
| **46 mm (chosen)** | **+1.72 mm** |
| 48 mm | +2.52 mm |

`stand_params.gland_clearance()` computes that, and **raises at import** if it
ever drops below 0.5 mm, so this cannot silently regress. The assembly then
measures the real distance through the real surfaces and prints it: **1.701 mm,
with the closest approach at (x 277.0, y −23.0, z 95.7)** — exactly the
collar-over-window-edge point the 46 mm was chosen for. Analysis and geometry
agree, which is the only reason to believe either.

**Never let the boss bottom out in the window.** A boss bearing axially is a
**parallel load path**: it shunts an unknown share of the thrust from the cell
into the strap, and the channel then reads *low* while everything looks perfectly
healthy. `LC_BOSS_SLOT_END_CLEAR` = 3 mm a side, which is roughly ten times the
cell's own full-scale deflection. This is the same failure as leaving a travel
collar in contact with a cradle ring (§6), and it is the single most dangerous
error class in this design — a wrong number is far worse than a dead channel.

#### Which way the cable leaves is your choice, not a reprint

`GLAND_SIDE` in `test_stand_assembly.py` is `−1.0`, i.e. the gland points to −y.
Because the cell is symmetric end for end and the boss is axially centred,
swapping sides is a plain 180° rotation of the cell about the vertical: the body,
both end faces and the boss all land back on themselves and **only the gland
changes side**. Decide it with the cell in your hand, on the day, based on where
your amplifier sits. Nothing needs reprinting either way.

#### Routing the cable — and why it needs a clamp

The gland is **rigid** and it is threaded into the cell. That makes the cable a
lever on the cell's own body, so the route matters more than it would with a
flying lead:

```
gland, horizontal at z = 103.7  ->  out sideways past the strap
  ->  a gentle loop DOWN outside the tower  ->  clamp to the baseboard
  ->  forward along the board to the electronics tray
```

Three rules for it:

1. **Strain-relieve it to the baseboard, not to the stand.** One P-clip or cable
   tie base within ~100 mm of the gland, so that anything that pulls the cable
   pulls on the board. Never let the cable's weight or a tug reach the gland.
2. **Loop, do not bend.** Armoured cable has a real minimum bend radius; leave a
   slack loop below the gland rather than a tight turn at the gland's throat.
3. **Keep it clear of the plume and out from under the strap.** Do not route it
   back *over* the tower — it has to cross the window, and the window is the one
   opening that must stay free so the boss can be checked for axial float.

The tower's bottom cable channel and the Ø21 M20 relief are still modelled, but
**this cell does not use either.** They remain as routes for a cell with a
downward or axial lead.

**Wiring** (from the AEP TCE datasheet — confirm against your own cell before you
power it):

| Wire | Function |
|---|---|
| Red | EXC+ |
| Black | EXC− |
| White | OUT+ |
| Yellow | OUT− |

#### The liner's slot stays full length — deliberately

`cell_liner` keeps a 46 mm slot running its whole 70 mm. It cannot become a window
like the strap's, for two reasons: the slot is also what makes the liner a **springy
C**, which is how a 2.1 mm printed wall takes up slop instead of jamming, and it is
how you get the liner onto the cell at all. Close it into a ring and it becomes a
press fit on the sensing element's own body.

A 46 mm mouth still wraps 253° of the cell and cannot let it escape — Ø57.2 does
not pass through a 46 mm gap. The measured cell-to-liner distance is **0.125 mm**,
which is just the 0.3 mm diametral bore clearance seen at the slot corner.

**Assembly consequence:** the boss must be **rotated into the slot**. The bore has
only 0.15 mm of radial clearance, so there is no orientation of the cell that
clears an unrelieved liner — however small the boss is, it must be indexed.

Two things came free. The boss in the slot **rotationally keys the cell**, so it
cannot twist in the cup and torque its own gland. And the liner's C opens upward,
so it cradles the cell under gravity instead of hanging it from its own split —
which is what you want in a part you drop in from above.

#### One thing deliberately *not* done

The cell has **four Ø30 counterbores on its flanks, at ±15 mm from mid-length**
(`LC_FLEXURE_X`), and those are the sensing flexures. The liner passes over them
with no relief, on purpose: they are *recesses*, so a slip-fit liner cannot preload
them, and cutting relief bands there would remove most of the liner's centring
surface for no gain. What matters instead is that **the liner is a slip fit and
never a press fit** — if you scale it up for shrink, scale the bore with it.

### What still absorbs tolerance, and what does not

- **`cell_liner.py`** — centring only, no longer size adaptation. Family at
  56.0 / 56.5 / **57.2 (the measured cell)** / 57.4 mm. **Asymmetric on purpose:**
  under-reading is free (a smaller cell just gets a thicker liner), over-reading is
  not. **57.4 mm is the largest cell this cup can hold.** Above that the liner is
  not the fix — `LC_CUP_BORE` goes up and the tower is reprinted.
- **`cell_spacer.py`** — absorbs the residual: a few mm of cell-length tolerance.
  Nominal stack is one 5 mm disc, and at that nominal the cell's load face lands
  **exactly flush with the cup mouth**, because `stand_params` *derives*
  `LC_CUP_DEPTH = LC_BODY_LEN + LC_SPACER_T` rather than choosing it. It does
  **not** absorb cell length in general; 80 mm moved the tower.

### ⚠ The M20 × 1.5 holes — read this before you bolt anything

This used to be three speculative cases. It is now one measured fact: the cell has
a **blind M20 × 1.5 hole 18.0 mm deep in each end**, with **44 mm of solid steel
between them**. It is not a through hole.

That is good news, and it removes a whole class of worry:

- **A retaining bolt in either end is safe.** Both threads stop 7 mm short of the
  sensing flexures at ±15 mm from mid-length, so a bolt in either end sits
  *downstream* of the sensing element and cannot shunt load around it.
- **The nominal build uses one M20 × 1.5 bolt, ~30 mm, up through the cup floor
  into the cell's base end, hand tight.** It is a retainer, not a preload. The
  Ø21 relief through the cup floor is a through hole so this bolt can enter from
  the forward side — the cell drops into the open trough from above, so there is
  nowhere else for it to come from.
- **Leave the load-end thread empty.** Nothing needs to screw into it, and the
  thrust cap's Ø24 central relief means its bearing face can never land on that
  hole's edge or on a burr inside it.

> **The one thing still worth stating plainly:** never try to run a stud end to end
> through both threads by drilling the cell out. That would put the sensing element
> inside a bolt clamp, *in parallel* with it, and preload alone can overload the
> cell — M20 at 100 N·m is ~25 kN, about **5× the cell's 5 kN full scale.** The
> geometry now prevents it, which is why it is a footnote rather than a table.

**A load button would make this joint worse, not better.** If you are tempted to
screw an M20 load button into the load end for a "proper" contact: 2 kN through a
typical Ø14 button face against printed plastic is ~13 MPa and climbing as it
brinells in, against 2.5 MPa for the flat Ø24–Ø40 annulus the cap uses now. Flat
on flat wins here precisely *because* the other face is plastic.

### One knock-on: the stand outgrew the 500 mm rail

Everything forward of the cup floor moved 40 mm. The thrust foot now ends at
x = 437.0, leaving 63 mm of rail for an 80 mm electronics tray, so **the tray
overhangs the rail's forward end by 18.5 mm and runs to x = 518.5.** That is
deliberate and it is load-free: the tray's side plates reach the baseboard like
every other bracket's, so the overhang is carried by the board, and both its bolt
stations sit in the aft 60 mm where there is still extrusion.

The tray was chosen to absorb this because it is the only part in the stand that
carries nothing. The alternatives were cutting the tower's reaction wedge (drops
its bending margin from 5.3× to 2.2×) or shortening a 2 kN load-bearing foot —
neither is worth trading for a junction box. **If you would rather have the whole
stand on the extrusion, buy a 600 mm rail and set `RAIL_LEN = 600`.** That is the
only change needed; nothing else in the design depends on the rail's length.

---

## 3. Where the thrust actually goes (do not skip this)

**A 2020 extrusion cannot take a transverse through-bolt at mid-height.** Its
central Ø4.2 mm axial screw boss sits directly in the path. So every side-slot
station is **two independent M5 bolts into two T-nuts**, one per side — not one
bolt through the rail.

That has a consequence. A T-nut resists load *along* the slot (the x /
thrust direction) only by **friction**, about 330 N each under a plain M5 head.
The tower's original 3 stations gave **1970 N against a 2000 N design load** — no
margin at all. Its 4 stations now give ~2630 N, which is 1.3× and still not
something to hang a primary load path on: oversized Ø15 washers would raise it to
~7300 N, but that means the thrust path depends on how hard someone tightened a
bolt, and on a friction coefficient nobody measured.

So it doesn't. **The reaction tower's forward face butts directly against the
thrust reaction foot**, and the thrust crosses that joint as direct PLA-on-PLA
compression over **913.6 mm² (2.19 MPa)** into the foot's M8 lag screws and thence
into the baseboard.

The result: **the rail carries no thrust.** It is an alignment spine — its job
is to hold the guide rings and the tower coaxial and coplanar, which is exactly
what an extrusion is good at. The rail's T-nuts carry only the residual tipping
moment, which they take as bearing on the slot lips: their strong direction.

> **Assembly consequence:** when you fit the thrust reaction foot, slide it aft
> until it makes firm contact with the tower's forward face *before* you tighten
> its bolts. A gap here puts the thrust back onto T-nut friction.

### Anchoring is mandatory, not optional

The load loop is **open** — the motor slides, so the net external force on the
stand equals the thrust. An unanchored 5 kg stand under 500 N accelerates at
100 m/s². The stand must be lag-screwed to a baseboard (18 mm plywood, ~600 x
300 mm) and the baseboard staked, weighted, or clamped down. This is a
load-path requirement, not a safety suggestion.

---

## 4. Printed parts

Print in the orientation stated in each file's `PRINT ORIENTATION` note. Every
part is modelled in **assembly orientation** and moved only on STL export, so
"as modelled" and "as printed" differ for a few of them. **The exported STLs are
already in print orientation** — drop them in your slicer as-is and do not
re-orient them.

| Part | Qty | Material | Walls / infill | Notes |
|---|---|---|---|---|
| `reaction_tower` | 1 | PLA | 5 / 30 % | **509 cm³**, 140 × 94 × 102 mm — by far the big print. Upright as modelled, 7476 mm² on the bed, no supports. |
| `cell_strap` | 1 | PLA | 4 / 30 % | **53.9 cm³.** Split face down, translated not rotated. Retains the cell; carries no thrust. Carries the **46 × 26 mm cable-boss window** — see §2. |
| `cradle_ring` | 2 | PETG / PLA | 4 / 30 % | Upright as modelled. Bore is the motor's sliding surface. |
| `cradle_cap` | 2 | PETG / PLA | 4 / 30 % | Split face down (597 mm²). Bore is 0.6 mm larger than the ring's — it must never pinch. |
| `travel_collar` | 2 halves | PLA | 4 / 40 % | Split face down. Two identical halves = one collar. |
| `thrust_cap` | 1 | **PETG/ASA** | 6 / 100 % | Axis vertical, **mouth DOWN**, on the Ø42–Ø48 mouth annulus (424 mm², use a brim). Mouth up has the bigger footprint but prints the cell bearing face as a first layer — see the file's docstring. In the load path *and* touches the hot closure. |
| `cell_liner` | 1 | PLA | 3 / 30 % | Ø57.2 bore family for the measured cell (2.10 mm wall). 70 mm long — **must stay shorter than the cell**, see §2. Slot goes **UP**, over the cable boss, and stays full length. |
| `cell_spacer` | 2–3 | PLA | — / **100 %** | Solid. Takes full thrust in pure compression (0.76 MPa). |
| `anchor_foot` | 2 | PLA | 4 / 40 % | One aft, one as the thrust reaction foot. |
| `deflector_bracket` | 2 | **PETG/ASA** | 4 / 40 % | Sits in the plume recirculation zone. |
| `electronics_tray` | 1 | PLA | 3 / 20 % | Non-structural. Overhangs the rail end by 18.5 mm — intended, see §2. |
| `calib_platform` | 1 | PLA | 4 / 30 % | Calibration only, never fired. |
| `motor_liner_29` | 2 | PLA | 3 / 40 % | Optional — runs a 29 mm motor in the same rings. |

Common settings: 0.4 mm nozzle, 0.2 mm layers, 6 top/bottom layers on load-path
parts. **No part in this design requires support material** in its stated
orientation; if your slicer wants supports, you have it in the wrong
orientation.

**Bridging is expected, and is not the same as needing support.** Three parts
print a horizontal bore that closes over itself as an arch — `cradle_cap`
(Ø39.4 over 25 mm), `cell_strap` (Ø62, but see below) and `travel_collar` (Ø38.3
over 12 mm) — plus `thrust_cap` has one Ø34 internal bridge where the closure
relief closes. Your slicer will show these as bridge regions and they will droop
a few tenths at the apex. That is designed for: none of those four surfaces is a
fit or bearing surface.

**`cell_strap` got harder again when the groove became a window, and that is the
right trade.** The old full-length groove deleted the bore's apex over 75 of the
81 mm, leaving almost nothing to bridge. The 26 mm window leaves **25 mm of crown
aft and 30 mm forward**, so the Ø62 apex is a real overhang over both. It is an
ordinary horizontal-hole overhang on a Ø62 arch, not a flat bridge — it closes
gradually and it prints. Paying for that in print difficulty buys back a roof over
the cell instead of an open trough, which is what the strap is for.

**Do not add support inside that bore.** You would have to pick it out of the
surface the liner has to sit against. The one bore that *is* a precision sliding
surface, `cradle_ring`'s, opens **upward** as an open trough and never bridges at
all.

### Why these materials

PLA is stiffer and stronger than PETG and is fine for everything that stays
cool. It softens at 55–60 °C, which matters for exactly two places: the
`thrust_cap`, which sits on the motor's forward closure and takes conducted
heat as the casing soaks after burnout, and the `deflector_bracket`, which
lives in hot recirculating gas. Print those in PETG or ASA. The
`cradle_ring`/`cradle_cap` touch the casing mid-body and are the next most
exposed; PETG is a cheap upgrade there.

During the burn itself (1–2 s) nothing has time to soften. The heat problem is
*after* burnout — so let the motor cool before handling, and inspect the thrust
cap between firings.

### If you print the whole thing in ABS

ABS works, and it lets you build the entire stand from **one filament** — its
Tg of ~105 °C covers the two places PETG/ASA were specified for, so the material
column above collapses to "ABS everywhere". Structurally it is not close to
marginal: the governing interface in the whole design is the M8 lag screw
bearing in the anchor feet at **11.1 MPa**, against 40–55 MPa for ABS in
compression — about **4x at the 2 kN design load and ~10x at a realistic 500 N
peak**. Resonance drops with √E, from ~900–1400 Hz to roughly **710–1110 Hz**,
still ~9x above an HX711's 80 SPS, so the bandwidth story in section 1 does not
change.

**The risk in ABS is process, not strength.** Two things follow:

**1. Print a shrink coupon before anything else.** ABS free-shrinks 0.4–0.8 %
against PLA's 0.2–0.4 %, and this design has two printed-to-aluminium fits that
eat it directly:

| Fit | Nominal | At 0.4 % | At 0.8 % | Goes interference at |
|---|---|---|---|---|
| Motor in guide bore (diametral) | 0.800 | 0.645 | 0.490 | 2.06 % |
| Rail channel slop (total) | 0.600 | 0.518 | 0.435 | 2.91 % |

Both stay **positive** at any realistic ABS shrink — this is not a blocker, and
0.49 mm on a 38 mm plastic-on-aluminium sliding fit is still several times a
normal running clearance. But the margin roughly halves, so measure instead of
hoping: print a ~100 x 20.6 x 20.0 mm bar with a 38.8 mm bore (~15 g), measure
XY and Z, and scale by 1/(1−s) per axis in your slicer. That one step restores
every printed-to-metal fit in the design at once.

Do **not** worry about elephant foot closing the rail channel. Real extrusion
has R0.8–R1.5 external corners, so the first-layer bulge sits inside the rail's
own corner relief and never meets aluminium — and commercial 2020 runs 19.9–20.0
on width, which adds clearance rather than removing it.

**2. The tower is the print that can fail.** 96 mm tall, ~480 layers, and a
first layer split into two separate 20.7 x 112 mm islands either side of the
rail channel. Use an enclosure or draft shield, bed 100–110 °C, fan off or low,
0.3 mm first layer, and a 10 mm brim with mouse-ears on **both** islands.

The encouraging part: this shape is the *opposite* of the classic ABS warp
geometry. Its cross-section decreases monotonically with height — 6944 mm² at
z = 20 down to 625 mm² at z = 96 — so the largest contraction forces sit in the
bottom 20 mm where the bed holds the material near Tg, and the z = 20 plane
where the channel roof closes is the **most** continuous plane in the part, not
a weakened one. Still: inspect the side plates for horizontal splitting before
the part goes anywhere near a motor, and reject on any visible layer separation.

**Acceptance test, ABS or not:** with the rings mounted and the motor in, a fish
scale should pull the motor through at **≤3 N with no stick-slip**. Re-check it
before and after every firing. That single measurement is what bounds the
friction error in section 1, so it is worth doing properly.

---

## 5. Purchase list

### You must supply

| Item | Qty | Notes |
|---|---|---|
| 2020 aluminium extrusion, **500 mm (600 mm preferred)** | 1 | 500 works, but the electronics tray then overhangs the forward end by 18.5 mm onto the baseboard. 600 mm puts everything on the extrusion — set `RAIL_LEN = 600`. See §2. |
| 500 kgf cylindrical compression load cell | 1 | **You have this: Tecnotest AP 032/005 = AEP TCE Ø57, Ø57.2 × 80.0 mm, flat both ends, blind M20 × 1.5 × 18 in each.** Modelled from the manufacturer's own `ref/TCE_57.stp`. See §2. |
| Load cell amplifier | 1 | HX711 is the cheap option; see the bandwidth note in section 1. Wiring: **Red EXC+, Black EXC−, White OUT+, Yellow OUT−.** |
| **P-clip or adhesive cable-tie base** | 1–2 | **Strain relief for the cell cable.** The gland is rigid and threaded into the cell, so the cable must be clamped to the *baseboard* within ~100 mm of it — see §2. |
| Plywood baseboard, 18 mm, ~600 x 300 mm | 1 | Or a concrete paver. **Mandatory.** |
| Steel or aluminium plate, **200 x 200 x 3 mm** | 1 | Blast deflector. **Must be metal** — a printed deflector will be destroyed. 200 mm is the minimum: the brackets sit at y = ±60 and the plate must shadow them. |

### Fasteners

Rail mounting — **two bolts per station, each into its own T-nut**:

| Item | Qty | Goes where | Side plate |
|---|---|---|---|
| M5 x **40** bolt + M5 T-nut | **8** | reaction tower, **4 stations** | **26.7 mm** |
| M5 x 20 bolt + M5 T-nut | 8 | cradle rings, 2 stations x 2 rings | 15.1 mm |
| M5 x 16 bolt + M5 T-nut | 8 | anchor feet, 2 stations x 2 feet | 8.0 mm |
| M5 x 16 bolt + M5 T-nut | 4 | electronics tray, 2 stations | 8.0 mm |
| M5 flat washer, **Ø15 OD** | 28+ | Under every head. Spreads clamp load on PLA — a plain M5 head reaches ~97 MPa on the plate and will crush it. Buy spares; see the shim note. |

**28 rail bolts, not 14.** Each entry in a part's `SIDE_BOLT_XS` is a *station*, and
`side_slot_bolt()` cuts one hole straight through **both** side plates — so every
station is two bolts into two T-nuts, one per side. Counting stations instead of
bolts halves the order.

Two of those rows changed with the measured cell, and both will bite if you order
from the old list:

- **The tower is 4 stations now, not 3.** Its saddle grew from 112 to 140 mm, and
  three stations at the old 44 mm pitch spanned only 88 mm of it — the forward
  third was unbolted.
- **Its bolts are M5 × 40, not × 30.** The side plates went 20.7 → 26.7 mm, so a
  30 mm bolt loses 6 mm of the thread that used to reach the T-nut. This is the
  single easiest way to end up with hardware that will not assemble.

> **Bolt length must be dry-fitted, and err LONG.** The usable window is set by
> your extrusion's slot depth and your T-nut's thickness, neither of which is
> fixed across suppliers: the bolt must reach through the T-nut, and its tip must
> not bottom on the slot cavity floor before the nut clamps. A bolt that is too
> long is fixed by stacking Ø15 washers under the head until the protrusion is
> right — which is why the washer count says 28+. A bolt that is too short cannot
> be fixed at all. Assemble **one** station of each length before ordering 28.

Split-plane and clamping:

| Item | Qty | Goes where |
|---|---|---|
| M5 x 20 socket screw, **no nut** | **4** | cell strap to tower ears (counterbored). **Tapped straight into the ABS/PLA ear** — see below. |
| M4 x 25 bolt + nut | 4 | cradle caps to ring ears (2 per ring) |
| M4 x 25 bolt + nut | 2 | travel collar lugs |
| M4 grub / set screw, ~8 mm | 2 | thrust cap to casing |
| M4 grub / set screw, ~10 mm | 4 | deflector brackets to plate — **vertical**, down through the slot roof, 2 per bracket |

> **The strap bolts are tapped into plastic, and take no nuts.** Cut an M5 thread
> straight into the tower's ear with a Ø4.3 tap drill (already modelled). This
> replaced a real bug: the ear holes used to be M5 *clearance* drilled from the
> split plane upward, but `flange_ear`'s underside slopes at 45°, so the material
> continued 3.5 mm below where the drill stopped. Every one of those holes was a
> blind pocket — nothing to thread, and no way to get a nut to it. Tapping is the
> right fix rather than a longer drill, because a nut on a 45° slope could never
> have seated flat anyway.
>
> It is sufficient on merit, not just convenient: the strap carries **no thrust**,
> only cell retention, and M5 × 10 mm in ABS shears out around **3 kN per bolt**
> against a ~16 N cell weight. If you expect to pull the cell in and out often,
> fit **M5 brass heat-set inserts** instead — tapped plastic is good for maybe
> 10–20 cycles.
>
> **There are 4 of these now, not 2.** One ear station per side held the assumed
> 40 mm cell; on 80 mm the strap would simply pivot about that single bolt pair and
> let the far end lift.

Load cell retention (see the M20 section in §2 first):

| Item | Qty | Goes where |
|---|---|---|
| M20 × 1.5 bolt, ~30 mm | 1 | Up through the cup floor into the cell's base end, to retain it. **Hand tight — it is not a preload.** Both threads are blind and stop short of the flexures, so either end is safe. |

> **Nothing else goes between the cap and the cell.** Two items that were on this
> list in earlier revisions are gone, because the cell turned out to have flat
> ends rather than a crowned button:
>
> - ~~M12 hardened washer, 24 mm OD~~ — its whole purpose was to stop a crowned
>   button brinelling into printed plastic. There is no button. The cap now bears
>   flat on steel over Ø24–Ø40, 804 mm², 2.5 MPa at 2 kN.
> - ~~M20 × 1.5 load button / adapter~~ — fitting one would *raise* the contact
>   stress to ~13 MPa on a Ø14 face. See §2.
>
> There is still deliberately **no hole through the thrust cap's bearing face** —
> 14.5 mm of solid plastic backs it, because a hole there would let the face dish
> under load.

Anchoring:

| Item | Qty | Goes where |
|---|---|---|
| M8 lag screw into wood, 60–80 mm | 4 | anchor feet, 2 per foot |
| M8 lag screw or ground stake | 4 | deflector brackets — **2 per bracket**, 40 mm apart. One stake lets the bracket pivot under the plume's yaw couple. |

---

## 6. Assembly order

1. **Baseboard first.** Lay the rail on the plywood. Fit the aft `anchor_foot`
   at the aft end and the thrust reaction `anchor_foot` where the tower's
   forward face will land (**x = 377.0 mm** from the aft end). Do not tighten yet.
2. **Reaction tower.** Drop it over the rail at **x = 237.0 mm**. Fit its **4 × 2**
   M5 × **40** bolts and T-nuts with Ø15 washers. Snug, not final.
3. **Butt the thrust foot.** Slide the thrust reaction foot aft until it makes
   firm metal-to-plastic contact with the tower's forward face. *Now* tighten
   both. Verify by hand that there is no gap.
4. **Lag down.** Drill the baseboard through the four M8 wing holes and drive
   the lag screws. Check the rail cannot slide.
5. **Load cell.** Decide first **which side you want the cable on**, then work to
   that — it is a free choice (§2), but it is easiest made now, before the cell is
   in the cup.
   1. Fit the `cell_liner` into the cup bore, **slot upward**.
   2. Drop the cell in with its **cable boss rotated to top dead centre**, so the
      boss sits in the liner's slot and **the gland points horizontally out to the
      side you chose.** There is no other orientation that fits: the bore has
      0.15 mm of radial clearance.
   3. Add `cell_spacer` discs behind it until **the cell's load face is flush with
      the cup mouth.** Nominal is one 5 mm disc and that lands it flush by
      construction. This is the single most important adjustment in the build —
      see the warning below. **Flush is the target, not proud.**
   4. Fit `cell_strap` over the top and its **4** M5 bolts (tapped into the
      tower's ears; no nuts). The boss now stands up through the strap's **window**
      with 3 mm of air at each end of it, and the gland passes out sideways with
      1.7 mm under its collar.
   5. **Confirm the cell can still be wiggled axially by hand after the bolts are
      tight.** If the boss is trapped fore-or-aft in the window, it is carrying
      thrust and the reading will be low.
   6. Fit the M20 retaining bolt up through the cup floor, **hand tight only.**
   7. **Strain-relieve the cable to the baseboard**, not to the stand: a slack loop
      down from the gland, then one P-clip or tie base within ~100 mm of it, then
      forward along the board to the tray. The gland is rigid, so an unclamped
      cable levers on the cell. The tower's bottom channel and the Ø21 M20 relief
      are **not used by this cell** — they remain for a downward or axial lead.
6. **Guide rings.** Fit both `cradle_ring`s at x = 66 and x = 124 mm. Leave
   their bolts loose.
7. **Motor in.** Slide the motor in from the aft end through both rings. It must
   slide **freely** — if it binds, the rings are not coaxial; loosen, re-seat on
   the rail top face, re-tighten. Fit both `cradle_cap`s. Their ears seat
   metal-to-metal on the ring ears, which is the hard stop that guarantees the
   cap cannot grip the casing.
8. **Thrust cap.** Slide `thrust_cap` onto the forward closure and set its two
   grub screws. Its Ø40 boss face is what will touch the cell — check it is clean,
   flat and free of stringing, because it is a printed face bearing on steel.
9. **Travel collar.** Fit the two collar halves around the casing at x = 111 mm,
   in the gap between the rings, with ~1 mm clearance to each ring face.
   Tighten until it grips the casing.
10. **Check the contact.** The cap's Ø40 boss face should be just touching, or
    within a fraction of a millimetre of, the cell's flat end face — and it must be
    touching **steel**, not the printed liner. A torch and a strip of paper is
    enough to tell. Adjust with spacers in step 5, not by moving the tower.
11. **Electronics tray** at **x = 438.5 mm** — hard up behind the thrust foot with
    ~1.5 mm of clearance, its two bolt stations landing at **x = 453.5 and 483.5**
    on the rail, and its forward **18.5 mm** resting on the baseboard past the
    rail's end. Then the deflector at least 150 mm aft of
    the nozzle. Stake the two brackets at **y = ±60 mm** either side of the
    plume, slot mouths facing forward, then drop the plate into both 45° slots
    and set the four vertical grub screws. Do not spread the brackets past
    ±65 mm — beyond that they leave the plate's shadow and the plume hits them
    directly. Then calibrate.

### The failure mode that silently ruins every reading

It has one signature and three causes, and they all look like a healthy stand.
**Anything that carries load in parallel with the cell steals an unknown share of
the thrust, and the channel reads low rather than dead.** A dead channel you
notice immediately; a channel reading 70 % you write down and believe.

The three parallel paths in this design, all of which the geometry already
prevents and all of which reassembly can reintroduce:

| Parallel path | What prevents it | Check |
|---|---|---|
| Thrust cap landing on the **printed liner** | liner 70 mm vs 80 mm cell → 10 mm proud | cap touches steel only |
| Cable **boss bottoming out** in the strap window | 3 mm of axial air at each end of the boss | boss wiggles axially by hand |
| Cap's Ø48 **shoulder** landing on the cup mouth | the Ø40 boss reaches 6 mm ahead of it | shoulder stands clear of the mouth |
| **Travel collar** in contact with a cradle ring | 1 mm gap each side | collar is free to slide |

**A fourth one was in the geometry itself, and is worth recording because it was
the most dangerous kind.** Before the cell was identified, the layout placed its
load face 3.5 mm *forward* of the thrust cap — it modelled a **gap in the load
path**, on the assumption of a 3 mm crowned button plus a proud washer that do not
exist. Assembled to those numbers the cap would never have reached the cell at all:
the motor would have slid until the travel collar hit a guide ring at 1.0 mm, and
**the entire thrust would have gone into the rail with the cell reading nothing.**
The contact plane is now derived as `CAP_X0 + CAP_LEN` with `CAP_LEN` imported from
`thrust_cap`, so the two cannot drift apart again.

The first row in detail, because it is the easiest to get wrong in *assembly*: if
the `cell_liner` were flush with, or longer than, the cell body, the thrust cap's
Ø40 boss would land on the **printed liner** instead of on the cell. The thrust
would go straight into the tower and **the stand would read almost nothing**.

Two things prevent it: the liner is **70 mm long against the measured 80 mm cell
body, so the cell's load face always stands 10 mm proud of the liner**, and the
cap's Ø40 boss reaches 6 mm ahead of its Ø48 shoulder. **Before every firing,
confirm the cap contacts the steel end face and nothing else** — a torch and a
sheet of paper is enough.

The liner had to grow 32 → 70 mm with the cell, and that is a fixed 10 mm margin,
not a coincidence: 32 mm of guidance inside an 85 mm bore would let an 80 mm cell
cock in the cup, and a cocked cell loads the sensing element off-axis — which the
datasheet limits to 50 % of capacity. **Do not lengthen `cell_liner` past 70 mm to
take up slack** — that is what the spacer stack behind the cell is for. The
assembly asserts this margin on every run and prints it as
`cell face proud of liner`.

### What the model checks for you

`python test_stand_assembly.py` runs three gates and prints all of them:

- **19 of 19 parts placed.** It raises rather than exporting a partial assembly —
  an early export silently wrote 4 of 19 solids and still reported a plausible
  bounding box.
- **Pairwise interference, measured by overlap DEPTH not volume.** AEP's own model
  has its end faces tilted 0.029° off the cell axis, which across a Ø57.2 face is
  7 mm³ of perfectly healthy face contact — a volume threshold cannot tell that
  from a collision, the overlap's minimum dimension can. Current result: **nothing
  deeper than 50 µm**, and the two sub-threshold face contacts are printed as
  grazes so a thin-and-wide interference cannot hide.
- **True minimum distance from the cell to every part it must clear**, through the
  real surfaces:

| | Measured | What it is |
|---|---|---|
| cell → `cell_strap` | **1.701 mm** | gland collar over the window edge — the number the 46 mm width exists to create |
| cell → `cell_liner` | 0.125 mm | the 0.3 mm diametral bore clearance, at the slot corner |
| cell → `reaction_tower` | 2.391 mm | cup bore below the split plane |
| cell → `cell_spacer` | 0.000 mm | intended face contact |
| cell → `thrust_cap` | 0.000 mm | intended face contact — the load path |

It **raises** if the strap or tower gap drops below 0.5 mm. Non-overlap is not
margin: the old 21 mm groove did not overlap this cell either, it just left the
gland 0.10 mm inside the crown, and you would have found that with a knife during
assembly.

---

## 7. Calibration

Calibrate **through the real load path**, not by hanging a weight off the cell.

1. Stand the rail vertically, **reaction tower at the bottom**, and secure it.
2. Remove the motor. Plug `calib_platform` into the `thrust_cap` bore (38.6 mm
   spigot in a 39.0 mm bore), and rest the cap on the cell as it normally sits.
3. Stack or hang known masses on the platform: water containers are convenient
   and 1 L = 9.81 N. Work up to ~50 kg (490 N) if you can, to cover the
   expected peak. The platform has **no retaining rim** — a lip on the weight
   face cannot be printed without either supports or bridging the whole Ø150
   plate. Retain the load through the 4 × Ø10 bolt circle at Ø120 instead:
   thread rod or cable ties through it and around the stack. A 50 kg pile
   balanced on a bare disc 65 mm above a bench is a crush hazard.
4. Record raw counts against load, both increasing and decreasing. Fit a
   straight line; the slope is your scale factor.

Load then travels `thrust_cap -> cell -> spacer stack -> floor` — exactly
the path a real burn uses — so the calibration constant absorbs everything in
that path, including any compliance in the printed cap.

**Deliberately excluded: guide-ring friction.** With the stand vertical the
rings are unloaded, so friction is not calibrated in. That is correct, not an
oversight: friction is a bounded *offset* (0.8–3.5 N), not a stiffness.
Calibrating it in would make it scale with load, which it does not.

**Hysteresis check.** If the up and down curves differ by more than ~1 % of the
applied load, something in the path is sticking. The usual suspects, in order:
the cap's boss face not seated flat on the cell's end face, the liner touching,
or the cable pulling on the gland. Find it before firing.

Re-zero (tare) immediately before each burn with the motor installed and at
rest. That removes the motor's weight and any preload.

---

## 8. Safety

This stand holds a live solid rocket motor. The mechanical design assumes you
already fire KNSB safely; these notes are only the parts specific to *this*
stand.

- **Anchor it.** Section 3. An unanchored stand is a projectile.
- **Nobody in line with the axis.** The failure mode of this architecture is a
  motor that slides forward out of its rings. The travel collar captures it if
  the load path lets go, but the collar is printed plastic — treat the forward
  axis as a danger zone and stand well off to the side.
- **Nobody aft either.** The nozzle overhangs the rail by 25 mm and the plume
  is unobstructed for a reason.
- **Metal deflector only**, at least 150 mm aft of the nozzle. A printed
  deflector in the plume cone will be destroyed and will throw burning debris.
- **The design load is 2000 N** against an expected peak of 300–900 N — roughly
  2–6x margin on the printed structure. That margin covers a hard ignition
  spike. It does **not** cover a full CATO: a pressure burst can far exceed it.
  The load cell will survive a CATO; the printed parts may not.
- **Let it cool.** The casing soaks heat after burnout, and PLA softens at
  55–60 °C. Do not handle or disassemble immediately. Inspect the `thrust_cap`
  and both `cradle_ring` bores between firings; replace them if the bore has
  glazed or deformed.
- **Fire remotely** with the data logger running before ignition.

---

## 9. Files

| File | What it is |
|---|---|
| `stand_params.py` | Every shared dimension and the global datum convention. **Start here.** |
| `stand_common.py` | Shared builders: `saddle()`, `flange_ear()`, `vbolt()`, `hex_pocket()`. |
| `reaction_tower.py` | The structural part. Takes the whole thrust reaction. |
| `ref/TCE_57.stp` | **The manufacturer's own model of your load cell** (AEP TCE Ø57 = Tecnotest AP 032/005). Not a dummy and not printed — the assembly imports it, so every clearance around the cell is checked against real geometry. `ref/TCE-20t.stp` is the larger sibling, unused. |
| `test_stand_assembly.py` | Full assembly: dummy rail and motor, **real cell**. Run it for the layout table, the clearance table, the interference check and the cell-to-part distances. |
| *(per-part files)* | One generator per printed part; each prints its own bbox and print orientation when run directly. |

Global datum convention: **z = 0** is the baseboard, the rail occupies z ∈ [0,
20]; **x** runs along the rail with **+x forward = the thrust direction**, so
the nozzle points −x; **y = 0** is the rail centreline; **z = 65** is the motor
and load-cell centreline, which are collinear by design.

Every part is parametric. Change `MOTOR_OD` or `MOTOR_LEN` in `stand_params.py`
and re-run — the assembly's axial chain is derived, not hardcoded.
