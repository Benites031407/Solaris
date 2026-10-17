# Models

| Script | Output | Purpose |
| --- | --- | --- |
| nose_cone_hook.py | STEP/STL/3MF nose_cone_hook | Nose cone, closed base with a screw-hook boss (used in the assembly) |
| nose_cone_open.py | STEP/STL/3MF nose_cone_open | Nose cone, open base with a shock-cord bar |
| coupler.py | STEP/STL/3MF coupler | Body-tube coupler band with 1010 rail guide and 1/4 in launch lug |
| fin_can.py | STEP/STL/3MF fin_can | Fin can: 3 external fin housings, motor bore, engine stop, aft guide + lug, cord anchor, detent-grooved stub |
| fin.py | STEP/STL/3MF fin | One fin with T-rail root (print 3) |
| fin_lock_ring.py | STEP/STL/3MF fin_lock_ring | Twist-lock ring that holds the fins in their housings |
| plate_fins_x3.py | STL/3MF plate_fins_x3 | The 3 fins pre-arranged on one plate |
| retainer_male.py | STEP/STL/3MF retainer_male | Threaded male motor retainer (glued on the motor tube) |
| retainer_female.py | STEP/STL/3MF retainer_female | Knurled screw-on retainer cap |
| fit_gauge.py | STEP/STL/3MF fit_gauge | Stepped gauge for the body-tube ID and motor-tube OD |
| scorpio_assembly.py | STEP/scorpio_assembly.step | Whole rocket preview with the non-printed tubes |

Shared dimensions live in `lib/params.py`; geometry factories in `lib/rocket_parts.py`.
Both nose models call `make_nose_cone(mount=...)` on the same shell. To preview the open
version in the assembly, import `nose_cone_open` in `scorpio_assembly.py` instead.

Build from the project root (`CG` is the pinned text-to-cad runtime):

```bash
CG="uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.21"
for m in nose_cone_hook nose_cone_open coupler fin_can fin fin_lock_ring plate_fins_x3 retainer_male retainer_female fit_gauge scorpio_assembly; do
  $CG python src/$m.py
done
$CG python checks/check_parts.py   # soundness, dimensions, fits, interference
$CG python checks/stability.py     # Barrowman CP / CG estimate
```

Unchanged models are a no-op; after editing `lib/params.py` the affected models rebuild.
