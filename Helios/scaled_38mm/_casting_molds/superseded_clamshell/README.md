# Helios 38 mm — casting molds for one BATES segment

Three printed molds make the three silicone pieces a segment is cast in:

| Silicone piece | What it does | Mold STL |
|---|---|---|
| **Base** | cup under the casting tube; its 13.8 hole grips the sleeve and centres the core at the bottom | `base_mold.stl` |
| **Sleeve** | plain Ø14 tube cast on the aluminium rod: forms the port | `sleeve_mold.stl` (all 4 parts on one plate) — or `sleeve_mold_half.stl` (**print 2**), `sleeve_mold_stand.stl`, `sleeve_mold_rod_guide.stl` |
| **End cap** | cup over the tube top; centres the core at the top, 5 × Ø4 vents let the excess out | `end_cap_mold.stl` |

The grain's OD is cast straight into the 0.2 mm liner (the casting tube). Both grain faces form on silicone, flush with the tube ends, so **segment length = tube length**. The same set works for 67.5 and 70 mm tubes.

## Check these before you print

| Assumed | Value | If yours differs |
|---|---|---|
| Core rod diameter | **10.0 mm** (`D_ROD`) | Measure it and set `D_ROD`. The rod seat and guide are sized from it. |
| Core rod length | **≥ 110 mm** | A longer rod is fine. It just sticks up further above the guide. |
| Liner wall | 0.2 mm, so tube OD 34.8 (`T_TUBE`) | Set `T_TUBE`. The base and cap sockets are sized from it. |
| Printer | vertical holes print 0.15 small, lying grooves 0.10 (`HOLE_COMP`, `GROOVE_COMP`) | Typical for a 0.4 nozzle. |

To regenerate after changing `mold_params.py`, run these from this folder:

```
python mold_params.py                     # self-check
python ~/.claude/skills/cad/scripts/step base_mold.py --stl base_mold.stl
python ~/.claude/skills/cad/scripts/step end_cap_mold.py --stl end_cap_mold.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold.py --stl sleeve_mold.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_half.py --stl sleeve_mold_half.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_stand.py --stl sleeve_mold_stand.stl
python ~/.claude/skills/cad/scripts/step sleeve_mold_rod_guide.py --stl sleeve_mold_rod_guide.stl
python mold_verify.py                     # must end "ALL CHECKS PASSED"
```

## Printing

- **Material and supports.** PLA is fine, because no printed part touches the propellant. No supports: every part is already in its print orientation, and nothing overhangs past 45°.
- **Sleeve mold halves:**
  - Print with **no brim**, and turn on elephant-foot compensation at about 0.15–0.2 mm.
  - Their bed edges are chamfered 0.6 mm, so a little squish won't jam them in the stand.
  - Use 0.1–0.12 mm layers (or adaptive layers) over the groove for a smoother port.
  - Use 5 or more top layers. Ironing on the parting face is optional.
- **Cup molds (base, cap):**
  - Use 6 or more top layers: the boss tops form the silicone that forms the grain faces.
  - The cap mold needs 3 or more perimeters, so the Ø4 vent pins print solid.
- **Single-plate sleeve file.** If you use `sleeve_mold.stl`, "split to objects" in the slicer to set the above per part.
- **Platinum-cure silicone.** It can be inhibited by some filaments. Test a drop on a scrap print first. Tin-cure isn't affected.

## Hardware (sleeve mold)

**6 × M3×30 bolts, 6 nuts, 12 washers. These are required, not optional.** The stand and guide only *locate* the ends (0.25 mm play per side). The bolts hold the seam shut. The bolt stack is 24 mm of mold plus a washer on each side plus the nut, about 27.4 mm, so 30 mm bolts fit. Tighten them snug, not crushing.

## Silicone

- **Type:** a mold-making silicone, tin- or platinum-cure, around Shore 25–40A.
- **Heat:** it must be rated well above the KNSB pour temperature (about 130–140 °C). Most are.
- **Viscosity:** 10,000 cP or less; 5,000 cP or less is better for the sleeve. Degas it if you can.

| Piece | Volume | Mass (at 1.1–1.2 g/ml) |
|---|---|---|
| Base | 14.8 ml | 16–18 g |
| Cap | 10.8 ml | 12–13 g |
| Sleeve (with the rod in) | 6.8 ml | 7.5–8.2 g |

Mix one batch of **at least 45 g** and **fill the sleeve first**, because it's the slow one. Let everything reach its **full datasheet cure** before the first KNSB pour. Post-cure only if the datasheet allows it.

## Casting the sleeve

1. **Check the parting faces.** Lay a straightedge on each face, beside the cones. If light shows, sand between the cones. Wipe a trace of petroleum jelly on the faces, staying at least 1 mm away from the groove.
2. **Close the halves.** They only go together one way, because the keys are staggered: a half turned end-for-end sits on its cones and won't close. Bolt all 6 bolts with washers, snug. Tape the outside seams, including the bottom end face.
3. **Stand it up.** Put the closed mold into the stand, **funnel end down**. That's the end where the groove narrows to the rod seat.
4. **Prepare the rod.**
   - Chamfer one end 0.5–1 mm: that end goes into the seat.
   - Wipe the rod with a thin film of petroleum jelly, wiped almost dry, so the sleeve can slide on it later.
   - **Mark it 104 mm from the chamfered end.** When the mark is level with the guide's top face, the rod is bottomed in its seat.
5. **Pour (method A).** Pour **6.8 ml (about 8 g)** into the bore in a thin stream down one side. That fills to about half height, roughly 47 mm below the top face.
6. **Insert the rod.**
   - Fit the rod guide on the top.
   - Brush a thin coat of silicone on the rod's lower 20 mm so it doesn't carry an air bubble down.
   - Push the rod slowly through the guide, at 0.5 mm/s at most. Take the **last 6 mm at 0.3 mm/s or slower**, because the silicone in the seat has to get out past the rod.
   - The level rises to the top face. Look through the windows and top up with a syringe if it's low.
7. **Tap and cure.** Tap the mold for about a minute, then cure.
8. **Demold.**
   - Lift off the guide, pull off the stand, unbolt the halves and split them.
   - Trim any seam flash.
   - Trim the thin (0.25 mm) silicone skin that forms on the rod below the bevelled tip; it comes from the rod-seat clearance.
9. **Slide the rod.** Slide it about 16 mm through the sleeve so it's **flush with the flat (pour) end**. It then sticks out about 22 mm past the bevelled tip. The pour end stands on the table in use.

**Method B (alternative, low-viscosity silicone only):**

1. Seat the rod first, with the stand on and the guide off.
2. Fill the 2 mm annulus from one point with a syringe, and let the air leave from the other side.
3. Slide the guide down over the rod.

Nothing acts as a piston in this method, but filling is slow.

## Casting the base and the cap

- **Pour order.** Pour into the ring channel at one point first, so it fills from the bottom and pushes the air ahead. Then flood over the boss from the same side, fill to the rim, and tap.
- **Base mold.** It holds the base upside down: the surface you pour to is the base's underside.
- **Cap mold.** It holds the cap as used: the surface you pour to is the cap's top.
- **Topping off.** Top off level with the rim just before the silicone gels.

## Casting a grain

1. **Place the base.** Stand the sleeve (with its rod) on the table, flat pour end down. Lower the base over the sleeve's bevelled tip, underside first (that's the side with the chamfered hole), and push the base down to the table. The sleeve's end is now flush with the base underside.
2. **Insert the tube.** Push the liner tube into the base socket until it's 12 mm deep, bottom end on the floor.
3. **Pour.** Pour the KNSB level with the tube rim. Keep it off the rim.
4. **Clean the top.** Wipe the top 12 mm of the liner's outside clean.
5. **Seat the cap.** Lower it over the sleeve tip and the tube. Press it down slowly and evenly, using something ring-shaped that **leaves the vents free**: the vents sit at r 10–14, so use an ID of at least 30 mm and an OD of about 42 mm. The excess comes out through the vents. The cap is fully seated when its top is **80.5 mm** above the table with a 67.5 tube, or **83.0 mm** with a 70 tube.
6. **Trim the vents.** Slice the overflow flush with the cap while the KNSB is still plastic. When it's cool, lift the cap straight up and trim the vent stubs off the grain face.
7. **Check the first port.** It should come out at 14.0–14.1 mm. If it's over 14.1, reduce `D_CORE` a little and regenerate.

Segment mass is 91.5 g at 67.5 mm, or 94.9 g at 70 mm (ideal density).

## Files

- **`mold_params.py`:** every number, plus a self-check.
- **Mold generators:** `base_mold.py`, `end_cap_mold.py` and `sleeve_mold.py`, with `sleeve_mold_*.py` for one part each.
- **Reference geometry (not printed):**
  - `silicone_pieces.py`: the three silicone pieces.
  - `casting_assembly.py`: a segment set up for casting. Running it reports interferences.
- **`mold_verify.py`:** checks the STLs.
  - Watertight, on the bed, through-hole counts, not stale.
  - Exact cavity = piece; the halves close only the right way.
  - Sliced sizes; no support needed.
