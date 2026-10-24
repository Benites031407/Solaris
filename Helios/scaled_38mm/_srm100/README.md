# SRM-100 — 100 mm research solid rocket motor

A reloadable, radially bolted, 4-segment BATES APCP motor on a 100.0 × 4.0 mm
6061-T6 case, drawn in build123d and generated with text-to-cad.  Every dimension
comes from `srm_params.py`; every part is a `gen_step()` generator next to its STEP.

**Design basis:** *Solid Rocket Engines — Collegiate Research* (the "paper"), plus
standard data the paper does not carry: AS568 O-ring sizes and Parker gland
practice, ISO 7380-1 fastener dimensions, MMPDS-style allowables, FED-STD-H28
thread shear areas, and the Mukunda-Paul and Lenoir-Robillard erosive-burning
correlations.

> This is a design model, not a certified motor.  It has not been proof tested,
> the burn rate is the paper's generic APCP curve, and an N-class research motor
> may only be built and fired under the rules and supervision that apply to it
> (Tripoli Research / L3, local law).  See **Caveats** at the end.

## At a glance

| | |
|---|---|
| Case | 6061-T6 tube 100.0 OD × 4.0 wall × 690.8 long |
| Overall length | 749.5 mm, forward flange face to the nozzle cap (748.0 to the holder's aft face) |
| Max diameter | 106.04 mm over the button heads (Ø108 keep-out) |
| Grain | 4 × BATES, OD 86.8, core 34.0, length 147.2, both ends burning |
| Propellant | APCP 70/16/14; 5.067 kg as cast (1718 kg/m³), 5.221 kg at the paper's 1770 |
| Nozzle | isomolded graphite in a 304 holder; throat 23.00, exit 52.0 (ε 5.11), 35° / 15° |
| Closures | 18 × M6 radial ISO 7380-1 010.9 per end; 2 × AS568-237 FKM 90A per closure; AS568-230 FKM 90A on the insert |
| MEOP / proof | 7.0 MPa / 10.5 MPa hydrostatic, on the 304 proof dummy |
| Performance, nominal | **N2203**: 10 495 N·s, 4.76 s, peak 2.38 kN, Pc peak 4.05 MPa.  2.5 % into N: M/N borderline until a static fire measures it |
| Performance, bound | N2523 (11 504 N·s, Pc peak 4.59 MPa): the paper's ideal inputs, used to size the hardware |
| OpenMotor | N2484 on the ideal inputs, no alerts |
| Mass | 10.601 kg loaded, 5.534 kg empty, propellant fraction 0.478 |

## Files

| File | What it is |
|---|---|
| `srm_params.py` | every number, where it came from, and `self_check()` |
| `srm_build.py` | revolve / radial-hole / transform helpers (no numbers) |
| `case.py` … `bolt_m6x16.py` | one generator per part (table below) |
| `proof_dummy.py` | 304 stand-in for the graphite insert, for the hydrostatic proof |
| `srm_assembly.py` → `srm_assembly.step` | the whole motor.  `placements()` is the only place a part is positioned; `proof_placements()` derives the proof build from it |
| `srm_aft_closure.py` → `srm_aft_closure.step` | the nozzle end as built up on the bench |
| `srm_proof_assembly.py` → `srm_proof_assembly.step` | the motor as it goes on the proof rig: case, closures, all five O-rings, 36 screws, the dummy |
| `srm_verify.py` | measures the *placed STEP solids*: interference, thread engagement and overlap, glands, stack, flow path, mass, the proof build, the `.eng` |
| `srm_ballistics.py` | independent lumped-chamber ballistics with erosive burning; writes `out/srm100.ric` |
| `srm_openmotor_check.py` | runs OpenMotor 0.6's own solver on the same `.ric` |
| `out/` | `srm_ballistics.{csv,json}`, `srm_thrust_curve.png`, `srm100.ric`, `srm_openmotor_check.json`, `mass_budget.json`, `SRM100_N2203.eng` |
| `drawings/` | the manufacturing drawing set: `SRM100_drawing_set.pdf` plus one PDF per sheet, each from its `dwg_*.py`; `srm_dwg.py` is the drawing kit (HLR projection, sections, ISO frame and title block) |
| `fwd_insulator.dxf`, `takeup_ring.dxf`, `grain_spacer.dxf` | cutting profiles for the three flat parts (layer CUT, mm), from their generators' `gen_dxf()` |

## Parts

Masses are measured from the STEP volumes (`out/mass_budget.json`).

| Part | Qty | Material | Mass each | Notes |
|---|---:|---|---:|---|
| `case` | 1 | 6061-T6 drawn tube | 2234.4 g | seal zones honed Ra ≤ 0.8; 20° × 1.1 O-ring lead-in; 18 × Ø6.4 holes per end (hole 0 offset 0.8°), bore side broken 0.5 × 45° |
| `nozzle_holder` | 1 | 304 stainless bar | 1501.2 g | aft closure; AS568-230 rod gland for the insert; 6 mm retaining lip with an R0.8 root; 18 × M6 tapped; 2 × M6 axial pullers at r 41 |
| `nozzle_insert` | 1 | isomolded graphite (ISO-63 / TTK-4 / IG-43 class) | 311.1 g | 63.50 OD slip fit, no threads, all loads compressive; push face r 26.2–27.0 |
| `nozzle_insulator` | 1 | glass phenolic | 38.8 g | covers the holder face; its bore continues the convergent |
| `nozzle_cap` | 1 | LDPE | 6.6 g | igniter retainer / debris seal, blows out at ignition |
| `oring_insert` | 1 | FKM 90A (Parker V0709-90), AS568-230 | 3.8 g | sacrificial: replace every firing (FFKM is the upgrade) |
| `oring_case` | 4 | FKM 90A, AS568-237 | 5.1 g | two per closure, no back-up rings |
| `liner` | 1 | paper phenolic | 347.5 g | 91.6 / 88.6 × 606.3; floats 0.5 mm short of the forward insulator |
| `grain_spacer` | 5 | linen phenolic | 1.3 g | 3 mm, so both grain ends burn |
| `casting_tube` | 4 | spiral kraft | 30.8 g | inhibits the grain OD |
| `grain` | 4 | APCP 70/16/14, as cast | 1266.8 g | BATES 86.8 / 34.0 × 147.2 |
| `takeup_ring` | 1 | closed-cell silicone sponge | 1.7 g | 88.4 / 80.0; 4.8 free → 3.0 installed |
| `fwd_insulator` | 1 | EPDM | 22.8 g | 3 mm full disc on the forward closure |
| `fwd_closure` | 1 | 6061-T651 bar | 770.5 g | solid, no pocket, no port: flat forward face to the axis (the thrust face); 2 × M6 pullers at r 37.5 |
| `bolt_m6x10` | 18 | ISO 7380-1 M6×10, 010.9 | 3.4 g | nozzle end: 6.0 mm in 304 (1 d) |
| `bolt_m6x16` | 18 | ISO 7380-1 M6×16, 010.9 | 4.7 g | forward end: 12.0 mm in 6061 (2 d) |
| `proof_dummy` | (1) | 304 stainless | — | proof only, never fired: insert OD, 40 bore cup, 15 mm closed end, 1/8-27 NPT fill / bleed port (the motor's only port) |
| **Total** | 63 | | **10.601 kg** loaded / 5.534 kg empty | CG 311 / 279 mm forward of the case's aft face |

The case's revolve seam is turned to 10°, half-way between two bolt holes.  With
the seam on hole 0, the STEP round trip lost hole 0's countersink.

## Ballistics

`srm_ballistics.py` is a lumped-chamber model: 40 burn cells per grain, a
throat-to-exit isentropic nozzle, and erosive burning per cell from the local
mass flux.  The paper's APCP is ρ 1770 kg/m³, c* 1550 m/s, γ 1.21,
r = 3.5 P^0.35 mm/s (P in MPa).  The runs:

| Run | Inputs | Designation | Impulse (N·s) | Burn (s) | Avg / peak thrust (N) | Pc peak (MPa) | Pc at start-up (MPa) | Isp (s) | G aft peak (kg/m²s) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **nominal** | ρ 1718 as cast, c* × 0.95, Mukunda-Paul, 20 °C | **N2203** | 10 495 | 4.76 | 2203 / 2383 | 4.05 | 3.90 | 211.2 | 1135 |
| bound | ρ 1770, c* 1550, Mukunda-Paul, 20 °C | N2523 | 11 504 | 4.56 | 2523 / 2726 | 4.59 | 4.41 | 224.7 | 1218 |
| ideal | as bound, no erosion (OpenMotor's inputs) | N2523 | 11 504 | 4.56 | 2523 / 2700 | 4.55 | 4.07 | 224.7 | 1053 |
| hot | bound, grain at 40 °C (σp 0.2 %/K) | N2695 | 11 559 | 4.29 | 2695 / 2911 | 4.88 | 4.69 | 225.8 | 1291 |
| Lenoir-Robillard | bound, LR erosion, 20 °C | N2552 | 11 483 | 4.50 | 2552 / 2996 | 5.01 at 0.03 s | 5.01 | 224.3 | 1390 |
| Lenoir-Robillard hot | bound, LR erosion, 40 °C | N2724 | 11 539 | 4.24 | 2724 / 3188 | 5.31 at 0.03 s | 5.31 | 225.4 | 1473 |

- **Nominal** is the prediction to fly or fire against.  It uses the as-cast
  density (98 % of theoretical), a 0.95 c* efficiency and erosive burning.
  **Bound** is what the case, closures and seals are sized to.
- **Kn** runs from 247.8 to 281.1, and port/throat is 2.19.  Chamber free
  volume at ignition is 674.5 cm³, giving L* 1.62 m.
- **Erosive burning** is not negligible here.
  - Mukunda-Paul peaks at η 1.54 in the aft core.  The aft grain burns
    through at 4.39 s, against 4.76 s total: that difference is the tail-off.
  - It also gives a start-up hump: 3.90 MPa nominal and 4.41 MPa bound, before
    the neutral mid-burn peak.
  - Lenoir-Robillard is harsher: η 1.85, and its peak *is* the start-up
    spike, at 5.0 MPa.
  - The aft mass flux stays below the 1406 kg/m²s (2 lb/in²s) rule of thumb in
    every run except Lenoir-Robillard hot.
- **MEOP basis:** bound peak Pc at the hottest grain × 1.3 ≤ MEOP.  Mukunda-Paul
  hot gives 4.88 × 1.3 = 6.34 MPa, which passes.  Lenoir-Robillard hot gives
  5.31 MPa, a margin of 1.32 ≥ 1.3, which also passes.
- **Expansion** is 5.11 against an optimum of 5.58 at the nominal average
  pressure.  That is a deliberately short divergent: C_F 1.407 delivered.

**OpenMotor 0.6.2 vs the ideal run** (identical inputs, no erosion):

| | `srm_ballistics.py` ideal | OpenMotor |
|---|---:|---:|
| Designation | N2523 | N2484 |
| Total impulse | 11 504 N·s | 11 276 N·s (−2.0 %) |
| Burn time | 4.56 s | 4.53 s |
| Average / peak thrust | 2523 / 2700 N | 2484 / 2660 N |
| Peak chamber pressure | 4.548 MPa | 4.566 MPa (+0.4 %) |
| Kn initial → peak | 247.8 → 279.5 | 247.8 → 279.5 |
| Isp | 224.7 s | 220.2 s |
| Peak mass flux, aft port | 1053 kg/m²s | 1053 kg/m²s |
| Alerts | — | none |

The 2 % impulse gap is OpenMotor's throat-length loss and 0.99 skin factor, which
the lumped model does not apply.  Pressure, Kn and propellant mass agree.

### Burn-rate sensitivity

The burn-rate coefficient is the least certain number in the motor.  Sweeping it
on the bound inputs (Mukunda-Paul, 20 °C):

| a × | Peak Pc (MPa) | Impulse (N·s) | Burn (s) | MEOP / Pc | G aft peak (kg/m²s) |
|---:|---:|---:|---:|---:|---:|
| 0.8 | 3.26 | 11 130 | 6.43 | 2.15 | 881 |
| 0.9 | 3.91 | 11 344 | 5.36 | 1.79 | 1046 |
| 1.0 | 4.59 | 11 504 | 4.56 | 1.53 | 1218 |
| 1.1 | 5.31 | 11 629 | 3.94 | 1.32 | 1399 |
| 1.2 | 6.06 | 11 728 | 3.45 | 1.15 | 1587 ⚑ |
| 1.3 | 6.85 | 11 807 | 3.05 | 1.02 | 1782 ⚑ |
| 1.4 | 7.67 | 11 873 | 2.72 | **0.91** | 1984 ⚑ |

⚑ means the aft mass flux is over the 1406 kg/m²s rule of thumb.  Past that
point the erosive correlation is being extrapolated.

The burn-rate multiplier at which peak Pc reaches MEOP:

| Erosion model | 20 °C | 40 °C |
|---|---:|---:|
| none | 1.325 | — |
| Mukunda-Paul | 1.319 | 1.267 |
| Lenoir-Robillard | 1.257 | **1.207** |

So in the worst case modelled (hot, Lenoir-Robillard), a batch that burns 21 %
faster than the paper's curve reaches MEOP.  **Measure the burn rate of the actual
batch (strand burner or a sub-scale motor), put the measured a and n into
`srm_params.py`, and re-run both simulations before loading this motor.**

## Structure

Allowables are guaranteed minimums, not the paper's typical values:
- 6061-T6 tube: Fty 240 / Ftu 260 MPa (the lower of drawn and extruded).
- 304 annealed: Fty 205 / Ftu 515 MPa.
- 10.9 bolt: Fu 1040 MPa.

Every row below comes from `self_check()` unless marked.

| Check at MEOP 7.0 MPa | Value | Margin |
|---|---:|---:|
| Case hoop (paper t = P r / (Fty/2)) | 84.0 MPa; wall 4.0 ≥ 2.68 required | FoS 2.86 on yield |
| Bolt load | 46.5 kN / 18 = 2.59 kN each | |
| Case bearing on d3 over 3.5 mm (the 0.5 bore break removed) | 155 MPa | FoS 2.49 on Fbry |
| … at the thinnest accepted wall 3.8 / bore 92.1 | 164 MPa | FoS 2.35 |
| Case bearing on d (wet pin) | 123 MPa | FoS 2.82 on 0.9 Fbry |
| Case shear-out, e/D 2.03 | 33.0 MPa | FoS 4.20 on shear yield |
| Bolt shear on d3 | 144 MPa | FoS 4.32 on ultimate |
| Case net section | 62.4 MPa | FoS 3.85 |
| Proof 10.5 MPa: bearing on d3 | 232 MPa < Fty 240; thin wall 247 < Fbry/1.25 = 309 | holes do not set |
| Tapped threads, fwd, 11.97 mm in 6061 | strip 22.1 kN = 2.43 × the 9.09 kN from 6 N·m at K 0.11; shear 0.49 × yield | > screw proof load 16.7 kN |
| Tapped threads, aft, 5.97 mm in 304 | strip 18.7 kN = 3.53 × the 5.30 kN from 3.5 N·m at K 0.11; shear 0.74 × yield | > screw proof load 16.7 kN |
| Metal left under the tapped holes | 2.71 mm over the insert bore (aft); the fwd holes end at r 28.50 in solid metal, 4.51 mm apart at the closest pair | ≥ 2.0 |
| Forward closure thickness (hand calc, not in `self_check`) | 44 mm solid; 12.4 needed for a simply supported plate at FoS 2 | |
| Graphite on the holder lip | 19.3 kN on 663 mm² = 29 MPa | FoS 3.1 on crush |
| Holder lip shear / bending at the R0.8 root | 16 / 47 MPa | FoS 7.4 / 4.37 on yield |
| Proof on the dummy (closed, whole gland area) | 33.3 kN on the lip: bending 81 MPa, shear 27.7 MPa | × 2.53 / FoS 4.27 |
| Proof dummy end plate, 15 mm | 42 MPa | FoS 4.9 |
| Insert transient interference 0.14 mm | contact 17.5 MPa, graphite bore hoop −40 MPa, holder hoop 49 MPa | FoS 2.2 on crush |

**Hole pattern.**
- The closest bolt pitch is 16.01 mm, at the offset hole, which is ≥ 2.5 hole
  diameters.  The closest button heads are 6.18 mm apart.
- Hole 0 is turned 0.8° off the 20° pitch.  A closure clocked one hole off misses
  by 0.64 mm, more than twice the 0.2 mm hole float, so a match-drilled pair only
  goes together one way.
- Both ends carry the same pattern, so a case turned end-for-end presents the
  mirror image and misses by at least as much.

**Failure order** (the ultimate pressure of each mode):

| Mode | MPa | × MEOP |
|---|---:|---:|
| barrel hoop burst | 21.7 | 3.1 |
| case net tension | 29.2 | 4.2 |
| bolt shear | 31.2 | 4.5 |
| case tear-out | 35.0 | 5.0 |

Nothing fails below 3 × MEOP.  There is no designed weak link: the barrel goes
first, so the motor fails radially rather than by ejecting a closure.

## Seals

| Gland | Ring | Squeeze, nominal / tolerance band | Other |
|---|---|---|---|
| 4 × case piston, groove 86.33 × 4.80, bottom R0.4, top edges R0.10 | AS568-237 FKM 90A | 19.7 % / 16.3–21.9 % | stretch 0.42–1.91 %; fill ≤ 76.1 %; extrusion gap 0.225 mm at MEOP, including 0.115 of case breathing, vs 0.47 (× 2.08); at proof 0.283 vs 0.357 (× 1.26), so no back-up rings; bore lead-in 1.1 > ring protrusion 0.80 |
| insert rod gland, groove 69.14 × 4.80 | AS568-230 FKM 90A | 20.1 % / 16.3–22.3 % | stretch ≤ 1.47 %; insert clearance 0.080–0.155 mm; extrusion gap 0.222 mm at MEOP, including 0.067 of dilation, vs 0.47 (× 2.12); at proof on the dummy 0.166 vs 0.357; fill ≤ 76.5 % |

- **Placement.** The O-rings sit inboard of the bolt rows, so the bolt holes are
  on the dry side of the seals and never see chamber gas.  Grooves are ≥ 3 mm
  past the bolt holes, ≥ 4 mm apart, and ≥ 5 mm from the plug nose.  The insert
  groove at z −3 is clear of the aft tapped holes at z 13.
- **Hot insert ring.** The insert ring seals on graphite, which heats through
  during the burn.  The review's 1-D model puts that face past FKM's 204 °C
  rating about 2 s in.  This design runs 90A FKM as a sacrificial ring, replaced
  every firing.
  - If it comes out hard, cut or extruded, move to FFKM.
  - If it still fails, bond a 2.0 mm glass-phenolic sleeve on a 59.50 mm
    graphite OD.  The sleeve OD stays 63.50, so the gland does not change.  This
    is not modelled.

## Validation actually run

**`python -c "import srm_params as P; P.self_check()"`**: 0 failures.  It covers:
- the paper rules: core/OD 0.392, Kn0 247.8, Pc 3.80–4.57 MPa, peak × 1.3 = 5.94 ≤
  MEOP (6.31 with the grain at 40 °C), Ap/At 2.19, L/D 6.78, ε 5.11, 35° / 15°;
- the case, joint, thread, gland and stack checks tabulated above.  For the stack:
  case length 690.8 closes exactly; take-up 37.5 % compressed nominal, 27.1–47.9 %
  over the ± 0.50 stack; liner float 0.5; radial fits 92.0 > 91.6 / 88.6 > 88.4;
  the proof dip tube (1.0 mm air annulus in the dummy's passage, 102 mm above
  the port when resting on the forward closure).

**`python srm_verify.py`**: 0 failures.  It measures the 63 placed STEP solids.
- **Interference.** 1953 pairs; the 164 whose boxes meet were intersected, and
  none interferes unexpectedly.
- **Thread engagement.** From the bolt/closure overlaps: aft 5.97 mm (1.00 d) and
  fwd 11.97 mm (2.00 d), all 18 at each end.
- **Thread overlap volume** against closed form: aft 48.993 vs 48.994 mm³, fwd
  100.830 vs 100.830 mm³.
- **Tapped holes.** A Ø4.8 probe down every core is clear in all 36 tapped
  holes, which proves they exist and are clocked to the case holes.
- **Glands**, probed through each placed ring: 2.835 mm / 19.7 % (case) and
  2.820 mm / 20.1 % (insert).
- **Stack.**
  - 14 axial contacts close to 3.6e-13 mm, with a contact footprint of at
    least 0.40 mm (spacer on grain).
  - The liner floats 0.500 mm.
  - Both flanges bear on the case ends.
- **Flow path.**
  - Throat 23.000, exit 52.0 at the exit plane (ε 5.11).
  - Insulator-to-graphite step 1.4 µm.
  - The insert bears on the lip over 3.66 mm radially.
  - Free radius 17.0 / 43.0 / 40.0 at the cores, spacers and take-up.  The
    axis is open from the exit to the forward insulator, and solid from there
    to the closure's forward face (47.0 mm: no port, no pocket).  0.25 mm under
    that face the closure is solid from the axis to r 49: the thrust face is
    whole.
- **Propellant.** 2949.6 cm³: 5.221 kg at 1770, 5.067 kg as cast, matching the
  parameters.
- **Envelope and mass.**
  - Length 749.5 mm; head sweep Ø106.04, inside the Ø108 keep-out.
  - Mass and CG as in the parts table.
- **Proof build.**
  - 45 parts, 990 pairs, no interference.
  - The dummy bears on the lip over 3.66 mm.
  - All five glands are identical to the motor's, and the insert ring runs on
    the dummy at 20.1 %.
- **`.eng`.**
  - 32 points (Douglas-Peucker), starting at (0, 0) and ending at F = 0.
  - Impulse 10 482 vs 10 495 N·s (−0.12 %, inside the 0.5 % assert).
  - The propellant mass matches the nominal run.

**text-to-cad.**
- Every part and all three assemblies were generated with `scripts/step` and
  checked with `scripts/inspect refs --facts --planes --positioning`: all ok, no
  warnings.
- Every generator was re-run and compared with its STEP: face, edge and solid
  counts and volume all survive the round trip.
- All are viewable in CAD Explorer.

**Ballistics.** `srm_ballistics.py` and `srm_openmotor_check.py`, as tabulated above.

## Build, inspection and assembly

**Case**
- Hone each seal zone to the smallest diameter that cleans up, A, and hold the
  zone to A +0.030/0, Ra 0.4 (0.8 max), circumferential lay.  A is the smallest
  reading in the zone; record it per zone.  Accept 92.000 ≤ A ≤ 92.070, so the
  zone never passes 92.10.  Accept the tube only with a wall ≥ 3.80 and a bore
  ≤ 92.10 anywhere: `self_check` runs the joint at those limits.
- Cut both plugs to the measured bore: groove = A − 5.67, land = A − 0.06.
- **Match-drill** each case end with its closure in place, hole 0 at the 0.8°
  offset.
  - Ream the case holes to **6.40 +0.03/0** and tap the closure.
  - Serialise the pair and scribe a clocking line across both.
- Break every bolt hole 0.5 × 45° on the bore side and polish it.
- Measure and record the **hole baseline** for all 36 case holes, keyed to the
  serialised pair:
  - the axial length of each hole;
  - the ligament from the case end face to the hole edge, nominal 13.0 − 3.2 =
    9.80 mm, with a depth-caliper blade or a small-hole gauge oriented axially.
- Take a **hardness / conductivity baseline** on each case end after the first
  proof: HRB or Webster, and eddy-current %IACS, at 4 azimuths at z 5–25 and at
  z = 100.  6061-T6 is about 95 HB (about 60 HRB), Webster B ≥ 15, about
  40–46 % IACS.  Compare later readings on the same instrument and scale.

**Closures and nozzle**
- Buy the forward closure as AMS 4117 / 6061-T651 bar and the holder as 304 bar.
- Make the insert from isomolded graphite, not extruded rod.  Hold the throat to
  23.00 +0.05/0.
- The holder's lip root is R0.8.  Do not let it be cut sharp: it is the lip's
  bending root.

**Fasteners**
- Use new ISO 7380-1 010.9 screws every firing.
- **Forward (6061):** 4–6 N·m with Loctite 243.
- **Aft (304):** **3.0–3.5 N·m** with nickel anti-seize on the threads only,
  head face dry.  With anti-seize, 6 N·m would yield the annealed 304 threads.
- Do not mix the two lengths up.  An M6×16 in the holder bottoms with its head
  proud; an M6×10 in the forward closure engages only 1 d of aluminium.

**Assembly**
1. Lube the O-rings with a thin film of Parker Super O-Lube or DC-55.  Grease
   the liner OD and the insulator edges the same way.  Bond the EPDM disc to
   the forward closure: abrade, IPA wipe, SS4004P silicone primer, RTV106 or
   equal, bondline 0.1–0.2, cure 24 h.
2. **Hole plugs.** Before each closure goes in, push 18 flat-ended acetal (Delrin)
   plugs, Ø6.35 × 3.85 with an outside head, into that end's holes.
   - Their ends sit about 0.15 mm shy of the bore, so no O-ring is dragged across
     an open hole edge.
   - Pull each plug as its screw goes in.
3. **Liner.** Cut it to the measured cavity, nozzle-insulator face to
   forward-insulator face, minus 0.5 mm.  The liner carries no axial load.  A
   feeler cannot reach the gap once the closure is in, so depth-gauge it: from
   the case forward end face, the liner's forward end must lie ≥ 0.30 mm deeper
   than the closure's measured plug + EPDM depth t (SRM100-000 sheet 3).
4. **Take-up ring.** Measure the gap from the top of the grain stack to the
   forward insulator, then pick the sheet:

   | Gap | Material |
   |---|---|
   | 1.6–2.4 mm | 3.2 mm sheet |
   | 2.4–3.6 mm (nominal 3.0) | 4.8 mm sheet |
   | 3.2–4.8 mm | 6.4 mm sheet |

   The bands overlap: accept any sheet whose measured free thickness t_s gives
   0.50 ≤ gap / t_s ≤ 0.75, i.e. 25–50 % compression (SRM100-108).

The forward closure has no port and no pocket.  The motor is fired without a
chamber transducer, so the closure is solid and the EPDM disc is whole: no leak
path, and no plug to forget.  The forward face is one flat surface to the axis,
the thrust face for a horizontal load cell, broken only by the two M6 puller
holes at r 37.5.  Filling the old Ø50 × 26 lightening pocket cost 137 g.
Adding a transducer later needs a new, ported closure and a re-proof.

**Extraction** (never lever or knock: MIT cracked a graphite insert that way)
- **Closures.** Read and record the temperature labels first.  A split clamp
  collar with a 100.0 bore goes on the case OD ≥ 50 mm from the end, clear of
  the heads at z 13 (Ø106.04 sweep), the labels and the marking at z 20–45.
  Add a bridge and 2 × M6 draw screws into the closure's puller threads
  (holder r 41, forward closure r 37.5; M6×1-6H 8 deep, Ø5 drill 10 deep).  Or
  react against the test stand's thrust plate.
- **Insert.** With the holder out, support it on its forward face in an arbor
  press.  Push the graphite out forward with a sleeve, 52.4 ID × 53.8 OD, through
  the lip bore onto the insert's push face (r 26.2–27.0).  About 117 mm²: 3 kN
  gives 26 MPa, against a graphite crush strength of about 90.

## Hydrostatic proof (before the first firing, and after any repair)

Build `srm_proof_assembly`: the flight case, both closures, all five O-rings and
all 36 screws, with the **304 proof dummy in the insert's gland**.
- No graphite: it must stay dry, and a cracked one is scrap.
- No insulators, liner or propellant.

The dummy is closed, so it loads the holder's lip harder than a firing does
(33 kN vs 19 kN).

1. Water-fill with the motor vertical, **aft end up**.  The dummy's 1/8-27 NPT
   port is the motor's only port, and the cup floor above it is the cavity's
   highest point.  The dummy's and the holder's forward faces make one flat
   ceiling at z 38 out to the bore, so tilting drives bubbles outward, away from
   the port.  Fill from the bottom instead:
   - Pass a Ø4 × 800 PE or nylon dip tube, end cut at 45°, down the port and
     the Ø6 passage until it rests on the forward closure's face (about 100 mm
     stays above the port).  Fill slowly through it so the water rises level;
     the air leaves through the 1 mm annulus round the tube.
   - Withdraw the tube and top up until the port overflows.  Fit the rig tee:
     bleed valve on top, pump line on the side branch.  Pump slowly with the
     bleed open until only water comes out, then close it.
   - Air left in the bore corner, well under 1 cm³, stores about 0.2 J per cm³
     at 10.5 MPa.  The 4.2 L of water stores about 100 J.
2. Set the pump's relief valve to **11 MPa** before pressurising.  Stand behind
   a barrier while the motor is under pressure.
3. Pressurise in steps: **3.5 → 7.0 → 10.5 MPa**, holding **300 s** at each.
   - **Accept** a hold if the pressure decays ≤ 2 % over it and there is no
     visible leak or weep.
4. Measure the case OD at marked stations before and after.  **Accept** a
   permanent set ≤ 0.02 mm at every station.
5. Re-gauge every bolt hole against its baseline.  **Retire** the end if any
   hole's axial length has grown by more than 0.05 mm, or its ligament has
   shrunk by more than 0.05 mm, from its own baseline.  (An in-tolerance new case
   can start at 12.9 − 3.215 = 9.685, so an absolute limit would be wrong.)
6. **Re-proof** after any repair, any retired-and-replaced part, or a
   temperature label reading ≥ 232 °C.

## Static-fire procedure

**Igniter**
- 3 g of BKNO3 granules or pyrogen in a paper tube, at most Ø10 × 40, on a
  dual-bridge e-match.
- The firing box must deliver ≥ 2 × the match's all-fire current.
- Push the igniter through the throat about 615 mm from the nozzle exit, to the
  middle of the forward grain's core, with both leads out through the cap's
  Ø3 hole.

**Stand**
- Fire vertical nozzle-up, or horizontal into a steel deflector.
- The stand and load cell must be rated ≥ 10 kN: 3 × the highest simulated peak,
  3.2 kN (Lenoir-Robillard hot).
- The forward closure's forward face is the thrust face.  It is flat and solid
  from the axis to the Ø100 edge, broken only by the two M6 puller holes at
  r 37.5 (SRM100-103).  A load cell, load button or thrust plate can bear
  anywhere on it; centre a button on the axis, clear of the puller holes.

**Sequence**
1. The motor comes to the stand with no igniter in it, and is secured.
2. Clear the range.
   - Personnel stand at least at the N row of the NFPA 1127 / Tripoli
     minimum-distance table: 1000 ft (≈ 305 m).
   - The review used 1500 ft (≈ 460 m) for spectators.
   - The site RSO's rules govern.
3. The **igniter goes in last**, at the stand, with its leads shunted.  The cap
   has been on since assembly as the debris seal: take it off only to insert
   the igniter, lead it out through the cap's Ø3 hole, refit the cap and
   re-tape it with new tape.
4. From the firing point: continuity check, arm, count, fire.
5. **Accept** ignition if Pc reaches 90 % of its initial value within **0.5 s**
   of the fire signal.
6. **Misfire:** disarm, and wait ≥ 60 s before approaching (5 min advised for
   an N motor).  Then remove the igniter.

**After burnout**
- Start remote cooling about 5 s after burnout: a fan, CO2 or a water spray
  aimed at motor z 0–40.  The aft case end heat-soaks from the holder.

**Temperature labels**
- Fit irreversible temperature labels (177 / 204 / 232 / 260 °C strips) at
  assembly, new for every firing: on the case OD at z 20–35 at θ 90° and 270°,
  clear of the head sweep, and on the holder's aft body (SRM100-102), clear of
  the cap tape.
- If a label shows **≥ 232 °C**, retire the case end or re-proof it.

**Post-fire handling**
- Handle the post-fire FKM O-rings with nitrile gloves: degraded FKM can carry
  HF.

**FMEA / PHA** (one line each; the mitigation is what this design does about it)

| Failure | Cause | Mitigation |
|---|---|---|
| Over-pressure / CATO | fast batch, erosive burning, hot grain, blocked throat | MEOP on the bound run × 1.3 at 40 °C; critical-a table; burn-rate measurement before loading; case bursts radially first |
| Joint / screw failure | under-engaged or stripped thread, wrong screw, elongated hole | 1 d / 2 d engagement, per-end torque, two screw lengths, hole baseline and 0.05 mm retirement, proof |
| Seal blow-by | cut or extruded O-ring, open hole edge, missing lube | inboard rings, hole plugs, lead-ins, extrusion margins ≥ 2 at MEOP, new rings every firing |
| Insert crack or ejection | levered extraction, wet graphite, thermal shock | lip retention (FoS 3.1 crush, 4.4 bending), dry-only (proof on the dummy), push-out sleeve |
| Misfire / hang-fire | open match, weak firing box, damp pyrogen | dual-bridge match, 2 × all-fire, continuity check, ≥ 60 s wait |
| Proof-test stored energy | trapped air, over-pressure | water, bottom fill by dip tube, bleed at the high point, 11 MPa relief, barrier |

## After every firing

- Measure the throat.  Re-use the insert while the throat is ≤ 23.9 mm and the
  insert is uncracked.  Enter the measured throat as `THROAT_D` for the next
  simulation.
- Replace every O-ring and all 36 screws.
- Replace the single-use parts: nozzle insulator, nozzle cap, forward insulator,
  liner, casting tubes, spacers and take-up ring (the grains go with them).
- Read the temperature labels.  Re-measure hardness and conductivity on the aft
  case end.  **Reject** the end if conductivity is above the 6061-T6 band
  (about 46 % IACS), or hardness is more than 10 % below its baseline on the
  same instrument and scale.
- Re-gauge every bolt hole against its baseline, as in the proof.

## Design review

A five-lens review (structural, seals/thermal, CAD geometry, ballistics,
manufacturing/safety) raised 25 findings.
- Each was adversarially re-checked: none was dropped, and 5 areas were
  confirmed sound.
- After re-check, 2 findings stayed **major**.  Both are fixed:
  - **CAD-1**, the over-constrained stack.  The liner now floats, the take-up is
    re-sized, and the liner is cut to the cavity.
  - **MS-1**, the proof could not be run.  There is now a proof dummy, a proof
    assembly and a proof procedure.

| ID | Finding | Outcome |
|---|---|---|
| S1 | aft torque yields the 304 threads | **fixed**: aft torque 3.0–3.5 N·m; `self_check` now checks thread shear against yield |
| S2 | holder lip bending root not checked | **fixed**: R0.8 root, lip bending check |
| SEAL-1 | insert ring face overheats | documented: sacrificial 90A FKM, FFKM upgrade, phenolic-sleeve option |
| SEAL-2 | insert gland ignores dilation | **fixed**: 90A ring, dilation term in the gap |
| SEAL-3 | O-rings dragged over open bolt holes | procedure: acetal hole plugs |
| SEAL-4 | bearing on the full wall ignores the break | **fixed**: 18 bolts, bearing on 3.5 mm |
| SEAL-5 / MS-5 | heat soak without temperatures or acceptance | procedure: labels, remote cooling, hardness / %IACS baseline and limits |
| SEAL-6 | sharp groove edges | **fixed**: R0.10 top edges |
| CAD-1 | stack over-constrained | **fixed**: liner float 0.5, take-up 4.8 → 3.0, liner cut to the cavity |
| CAD-2 | verify could not see missing tapped holes | **fixed**: overlap-volume and core-probe checks |
| CAD-3 | pattern symmetric, no clocking | **fixed**: hole 0 at 0.8° |
| CAD-4 | no push-out face on the insert | documented: push face r 26.2–27.0 plus a push-out sleeve.  The pin holes were not added, which keeps the full lip seat |
| CAD-5 / MS-8 | nothing to pull against | procedure: clamp collar and bridge ground-support equipment |
| F1 | igniter undesigned | **fixed** in the parameters: charge, tube, placement, acceptance, hang-fire |
| F2 | erosive burning dismissed | **fixed**: Mukunda-Paul and Lenoir-Robillard runs, mass-flux flag |
| F3 | no temperature sensitivity | **fixed**: σp and the hot runs in the MEOP basis |
| F4 | N-class claim on ideal c* | **fixed**: c* × 0.95, as-cast density, N2203 nominal, M/N borderline label |
| MS-1 | proof cannot be run | **fixed**: proof dummy, proof assembly, procedure |
| MS-2 | pin gauging cannot see elongation | procedure: ream 6.40 +0.03/0, per-hole baseline, 0.05 mm retirement |
| MS-3 | thin-wall checks at the nominal wall | **fixed**: `self_check` at wall 3.80 / bore 92.10 |
| MS-4 | liner datum, take-up too small | **fixed** with CAD-1 |
| MS-6 | static-fire ops missing | procedure: static-fire section and FMEA above |
| MS-7 | `.eng` under-reports impulse; CG datum | **fixed**: Douglas-Peucker with a ΔI assert; CG measured from the case's aft face |

## Tripoli / L3 notes

- An N-class research motor needs a Tripoli Level 3 flyer working under the
  Tripoli Research program and its safety code, at a research launch or static
  test site.  The nominal N2203 is only 2.5 % into N.  Treat it as N for
  distances and paperwork, and let the static fire settle the class.
- The motor is designed to be static-fired first: the forward closure's flat
  forward face is the thrust face.  There is no chamber transducer, so the load cell is the only
  record: Pc follows from F / (Cf · At).  Static firing needs remote ignition,
  the standoff distances above, and a pressure-logged proof history.
- The 304 aft closure follows the paper ("steel, not aluminium, behind the
  graphite").  Confirm with the TAP / RSO that it is acceptable under the current
  research rules on ferrous components.
- For flight, the airframe needs a Ø108 keep-out for the button heads, and a
  thrust ring or a forward-closure thrust path.
- Benchmarks consulted for proportions: MIT Rocket Team Phoenix / Medusa motors,
  Georgia Tech GTXR, R. Nakka's Kappa / Lambda motors, Kosmos FMEA practice.

## Thrust curve

`out/SRM100_N2203.eng` is the nominal run in RASP format, 32 points, for
simulators.  Its comment lines name the run, the bound designation, and the
burn-rate caveat:

```
SRM100-N2203 100 750 P 5.0674 10.6013 RESEARCH
```

## Caveats

- **Not a structural certification.** The checks are hand calculations and closed
  form (hoop, Lamé, bearing, shear-out, plate, thread shear), not FEA.  The motor
  must pass the hydrostatic proof above before it is fired.
- **The burn rate must be characterised** on the actual propellant batch.  At
  40 °C with Lenoir-Robillard erosion, +21 % on a reaches MEOP.
- **Graphite and seal thermal life** are estimated from practice and a 1-D
  model, not analysed in detail.  Inspect after every firing.
- **The class is not settled.** N2203 predicted, M/N borderline: only a
  static fire with a load cell measures it.
- **N-class:** Tripoli L3 and research rules, a qualified supervisor, and
  local-law compliance are the builder's responsibility.
