# Helios

A 65.52 mm rocket for a 38 mm KNSB motor, printed in five sections that slide together on spigots.

- The files at the top of this folder (`cone.stl`, `Mbody.stl`, `Lower_Body.stl`, `Tail.stl`, …) are the original design, as received (`fwd3drocketfiles`).
- `scaled_38mm/` is that design scaled for a 38 mm motor (`rocket_assembled_boattail.stl` is the assembled airframe) and everything added to it.

| Folder | What it is |
|---|---|
| [`scaled_38mm/_nose_door/`](scaled_38mm/_nose_door/README.md) | Side-door nose: a TowerPro MG90S latch holds a door that two springs kick off at apogee. Housing, door and servo keeper, with checks and a video. |
| [`scaled_38mm/_nose_simple/`](scaled_38mm/_nose_simple/README.md) | Clamshell nose: two hinged halves held shut by one servo turning one bar. |
| [`scaled_38mm/_avionics/`](scaled_38mm/_avionics/README.md) | Avionics bay for an ESP32 and a BMP280 on a sliding plate. |
| [`scaled_38mm/_casting_molds/`](scaled_38mm/_casting_molds/README.md) | Molds for the silicone pieces one BATES grain segment is cast in. |
| [`scaled_38mm/_srm100/`](scaled_38mm/_srm100/README.md) | SRM-100: a 100 mm reloadable research motor (drawings and STEP). |
| [`scaled_38mm/teststand/`](scaled_38mm/teststand/README.md) | Horizontal static test stand for the 38 mm motor with a load cell. |
| `scaled_38mm/_explainer/` | Interactive explainer of the whole flight (`helios.html`, `helios-light.html`) and printable A4 sheets (`helios-*-a4.pdf`). Build with `node build.mjs` (needs the anatomy skill). |
| `scaled_38mm/brag-output/` | A short launch video (`brag.mp4`) and its composition. |
