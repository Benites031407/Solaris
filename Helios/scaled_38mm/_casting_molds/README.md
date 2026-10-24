# Helios 38 mm — casting molds for one BATES segment

Three printed molds make the three silicone pieces a segment is cast in:

| Silicone piece | What it is | Mold STL |
|---|---|---|
| **Base** | Ø41.8 × 15 cylinder. On top, a 6 mm socket the casting tube sits in, down on its shoulder; in the middle, a Ø13.8 × 6 blind pocket the core's end plugs into | `base_mold.stl` |
| **Sleeve** | plain Ø14 silicone tube, 87 long, cured onto the aluminium rod: forms the port | `sleeve_mold.stl` (all 4 parts on one plate) — or `sleeve_mold_outer_cylinder.stl`, `sleeve_mold_foot.stl`, `sleeve_mold_top_guide.stl`, `sleeve_mold_inner_cylinder.stl` (optional, see below) |
| **End cap** | Ø34.8 × 6 disc with a Ø13.8 hole. Sits on the tube's rim, edge flush with the tube | `end_cap_mold.stl` |

The **sleeve mold** is an inner cylinder inside a bigger cylinder:
- **Outer cylinder:** its Ø14 bore forms the sleeve's OD. It's open at both ends and the same either way up.
- **Foot:** a wide flange with a collar the outer cylinder slips into. Its floor forms the sleeve's bottom end, and a 3 mm seat in the middle takes the rod's end.
- **Top guide:** sits on the outer cylinder's top and holds the rod on the axis. Through its two windows you watch the level.
- **Inner cylinder:** your **aluminium rod**, so the sleeve cures straight onto it. The printed Ø10 pin can stand in for it, but see step 5 of the sleeve procedure.

The grain's OD is cast straight into the 0.2 mm liner (the casting tube). Both grain faces form on silicone, flush with the tube ends, so **segment length = tube length**. The same set works for 67.5 and 70 mm tubes.

## Check these before you print

| Assumed | Value | If yours differs |
|---|---|---|
| Core rod diameter | **10.0 mm** (`D_ROD`) | Measure it (calipers, in 2–3 places) and set `D_ROD`. The foot's seat, the guide's bore and the printed pin are sized from it. The base mold, the cap mold and the outer cylinder don't depend on it, so you can print those now. |
| Core rod length | **110 mm**; at least 104 | A longer rod is fine; it just stands higher above the guide. |
| Liner wall | 0.2 mm, so tube OD 34.8 (`T_TUBE`) | Set `T_TUBE`. The base socket and the cap are sized from it. |
| Printer | vertical holes print 0.15 small (`HOLE_COMP`) | Typical for a 0.4 nozzle. |

To regenerate after changing `mold_params.py`, run these from this folder:

```
python mold_params.py                     # self-check
python ~/.claude/skills/cad/scripts/step base_mold.py --stl base_mold.stl
python ~/.claude/skills/cad/scripts/step end_cap_mold.py --stl end_cap_mold.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold.py --stl sleeve_mold.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_foot.py --stl sleeve_mold_foot.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_outer_cylinder.py --stl sleeve_mold_outer_cylinder.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_top_guide.py --stl sleeve_mold_top_guide.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_inner_cylinder.py --stl sleeve_mold_inner_cylinder.stl
python mold_verify.py                     # must end "ALL CHECKS PASSED"
```

## Printing

- **Material and supports.** PLA is fine, because no printed part touches the propellant. No supports: every part is already in its print orientation, and nothing overhangs past 45°.
- **Outer cylinder:**
  - Its bore forms the sleeve's OD, and that forms the port. Print it at **0.12 mm layers**.
  - Its end edges are chamfered 0.6 mm, so a little elephant's foot won't jam it in the foot or the guide.
- **Foot, base mold and cap mold:**
  - Print at **100 % infill**. They're small (8.8, 18.4 and 7.1 cm³).
  - Their top faces form silicone surfaces, and the foot floor also seals the bottom of the sleeve column. A thin top skin over sparse infill can let silicone in.
  - If you don't want solid parts, use at least 6 top layers, and degas the silicone in the cup, not in the mold.
- **Printed pin (optional):** print it at **100 % infill** with a brim. It's 110 mm tall on a Ø10 footprint.
- **Platinum-cure silicone.** It can be inhibited by some filaments. Test a drop on a scrap print first. Tin-cure isn't affected.

No hardware is needed, just tape.

## Silicone

- **Type:** a mold-making silicone, tin- or platinum-cure, around Shore 25–40A.
- **Heat:** it must be rated well above the KNSB pour temperature (about 130–140 °C). Most are.
- **Viscosity:** 10,000 cP or less. Degas it in the cup if you can.

| Mold | Silicone to fill it | Mass (at SG 1.1–1.2) |
|---|---|---|
| Base mold, to the rim | 14.1 ml | 15.5–16.9 g |
| Cap mold, to the rim | 4.9 ml | 5.3–5.8 g |
| Sleeve mold, with the rod | 6.9 ml | 7.6–8.3 g |
| **Total** | **25.8 ml** | **28.4–31.0 g** |

Mix one batch of **about 40 g**. Pour **the sleeve first**, because it's the slow one. Let everything reach its **full datasheet cure** before the first KNSB pour. Post-cure only if the datasheet allows it.

## Casting the sleeve

The silicone goes in **before** the rod. Pouring into the 2 mm gap around a rod that's already in traps air, because that gap is 87 mm deep and closed at the bottom.

1. **Prepare the parts.**
   - Wipe a thin film of release agent (petroleum jelly, or a spray release) inside the outer cylinder's bore and on the foot floor.
   - Put a trace on the cylinder's bottom end face too. That's the joint that holds back the silicone.
2. **Prepare the rod.**
   - Chamfer the end that goes into the seat, 0.5–1 mm, so it finds the seat.
   - Leave the rod clean, or give it at most a very thin film: the sleeve should come out of the mold riding on it.
   - **Mark it 99 mm from the chamfered end.** When the mark is level with the guide's top face, the rod is bottomed in its seat.
3. **Assemble the foot.** Push the outer cylinder into the foot's collar; either end is fine. Tape round the outside of the joint. Stand it on a level table.
4. **Pour and insert the rod (the displacement method).**
   1. Pour **6.9 ml** into the open bore in a thin stream down one side. Weigh it on the mold: 6.9 × SG grams, so about 7.6–8.3 g.
   2. The level stands about **42 mm above the foot floor**, 45 mm below the top face. Give the bubbles a minute to rise.
   3. Fit the guide on the top.
   4. Dip the rod's lower 20 mm in the leftover silicone, so its end doesn't carry an air bubble down.
   5. Push the rod slowly down through the guide's hub, 0.5 mm/s at most. Go slower over the last few mm, because the silicone in the seat has to get out past the rod.
   6. You'll feel it drop into the seat. It's seated when your mark is level with the guide's top face: a 110 mm rod then stands **11 mm** above the guide. If it's 14 mm, it isn't in the seat.
   7. The rod brings the level up to the top face. Check it through the windows and top up with a syringe if it's low.
5. **Using the printed pin instead of the rod.** It must be printed solid. At normal infill it's lighter than the silicone and floats up out of the seat. Even when it's solid, tape its top down to the guide, and tape the guide to the cylinder.
6. **Cure.** Tap the mold for about a minute, then leave it for the full cure.
7. **Demold.**
   - Lift off the guide and pull off the foot.
   - Hold the cylinder and pull the rod up, or push it down. The sleeve comes out with it.
   - Don't push on the sleeve's end: it squashes and jams in the bore.
8. **Trim.** Trim the thin silicone skin on the rod below the sleeve's bottom end; it forms in the seat's clearance. Trim any flash on that end too.
9. **Slide the rod.** Slide it **3 mm** through the sleeve until the bottom ends are **flush**. A drop of soapy water or IPA helps. The rod then stands 23 mm out of the sleeve's top.

## Casting the base and the cap

- **Pour order.** Pour at one point into the lowest part of the cavity: the ring round the boss in the base mold, the ring round the pin in the cap mold. It fills from the bottom and pushes the air ahead. Fill to the rim and tap.
- **Base mold.** It holds the base upside down: the surface you pour to is the base's underside.
- **Cap mold.** It holds the cap as used: the surface you pour to is the cap's top. The pin stands 1 mm proud of the rim, so the hole comes out open.
- **Topping off.** Top off level with the rim just before the silicone gels.

## Casting a grain

1. **Place the base.** Stand the base on the table, socket up.
2. **Insert the core.** Push the core (the sleeve on its rod, flush end first) into the centre pocket with a slight twist until it bottoms. The Ø13.8 pocket grips the Ø14 sleeve.
3. **Insert the tube.** Push the casting tube into the socket until it's 6 mm deep, bottom end on the shoulder. It's a light squeeze fit (Ø34.7 on Ø34.8).
4. **Pour.** Pour the KNSB level with the tube rim. Keep it off the rim and the tube's outside.
5. **Seat the cap.** Slide the cap down the sleeve and press it evenly onto the rim.
   - Run a fingertip round the edge until the cap is **flush with the tube all the way round**. That's what centres the top of the core.
   - While the KNSB is still soft, wipe any squeeze-out off the tube's outside. The tube only has 0.1 mm per side in the case.
   - The cap top is **82.5 mm** above the table with a 67.5 tube, or **85.0 mm** with a 70 tube. The sleeve stands 7.5 or 5.0 mm above it.
6. **Check the first port.** It should come out at 14.0–14.1 mm. If it's over 14.1, reduce `D_CORE` a little and regenerate.

Segment mass is 91.5 g at 67.5 mm, or 94.9 g at 70 mm (ideal density).

## Files

- **`mold_params.py`:** every number, plus a self-check.
- **Mold generators:** `base_mold.py`, `end_cap_mold.py` and `sleeve_mold.py`, with `sleeve_mold_*.py` for one part each.
- **Reference geometry (not printed):**
  - `silicone_pieces.py`: the three silicone pieces.
  - `casting_assembly.py`: a segment set up for casting. Running it reports the fits and any interference.
- **`mold_verify.py`:** checks the STLs.
  - Watertight, on the bed, through-hole counts, not stale.
  - Exact cavity = piece + print allowance; the sleeve-mold parts and the rod don't clash.
  - Sliced sizes; no support needed.
  - It also prints the fill volume and the fill height.
- **`superseded_clamshell/`:** the earlier two-half sleeve mold, kept for reference.
