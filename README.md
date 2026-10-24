# Solaris

Three model rockets, their printable parts and the tools around them.

| Rocket | Folder | What it is |
|---|---|---|
| **Scorpio** | [`Foguete-Scorpio/`](Foguete-Scorpio/README.md) | 3D-printable ABS replica of the Estes Pro Series II Scorpio 3D (2 in body, 29 mm motor): fin can with twist-lock fins, coupler, retainers, and three nose cones (screw hook, open bar, side door with a servo latch and spring-ejected door). |
| **Big Heavy** | [`Big-Heavy-main/`](Big-Heavy-main/big_heavy_1/README.md) | Designs for additively manufactured high-power rockets, by Peter Myung-Won Pak: SolidWorks and STEP parts, OpenRocket files and simulations, and a second version (`big_heavy_2`) with a parts viewer. |
| **Helios** | [`Helios/`](Helios/README.md) | 65.5 mm rocket for a 38 mm KNSB motor, printed in five sections: side-door and clamshell noses, an ESP32/BMP280 avionics bay, motor and casting molds, a static test stand, and an interactive explainer of the whole flight. |

## Licences and sources

- `Big-Heavy-main/` is © 2023 Peter Myung-Won Pak under the MIT licence: see [`Big-Heavy-main/LICENSE`](Big-Heavy-main/LICENSE), which must stay with it.
- `Helios/` builds on a set of rocket STLs received as `fwd3drocketfiles` (the files at the top of `Helios/`); `Helios/scaled_38mm/` is that design scaled to 38 mm plus the parts and tools added to it.
- `Foguete-Scorpio/` keeps its own history: it was merged in from its former repository with all of its commits.

## Working on the CAD

The CAD is Python (build123d) run with [text-to-cad](https://github.com/earthtojake/text-to-cad) (`cadgen 0.7.21`); each project's README gives its build and check commands. Generated STEP, STL and 3MF files are committed next to their sources. CAD Explorer's hidden `.*.step.glb` sidecars are not: regenerate them with the CAD skill's `scripts/step` before opening a model in the viewer.
