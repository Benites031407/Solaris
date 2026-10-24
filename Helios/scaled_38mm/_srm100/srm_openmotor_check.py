"""Run OpenMotor's own solver on out/srm100.ric and compare it with srm_ballistics.py.

The paper asks for dual verification with OpenMotor.  srm_ballistics.py is the
independent half; this is the OpenMotor half, run headless on the SAME .ric that
srm_ballistics.py writes, so both see identical inputs.  The .ric is srm_ballistics'
IDEAL run (density 1770, ideal c*, no erosive term), because OpenMotor's BATES
solver carries neither a c* efficiency nor erosive burning; that is the run this
compares against.  The nominal and MEOP-bound runs add those effects on top.

Needs an OpenMotor source checkout (github.com/reilleya/openMotor, 0.6.x) and an
interpreter with its requirements (numpy, scipy, scikit-fmm, pyyaml).  Point at it:

    set OPENMOTOR_SRC=D:\\srm100_scratch\\openmotor_src
    D:\\srm100_scratch\\openmotor_venv\\Scripts\\python.exe srm_openmotor_check.py

OpenMotor's one compiled helper (mathlib._find_perimeter_cy) is only used by FMM
grains and the GUI's face images, never by BATES, so if it has not been built it is
replaced by a stub that raises if anything ever does call it.

WHAT AGREEMENT LOOKS LIKE
-------------------------
Pressure and Kn must agree to well under 1 %: both solve the same equilibrium, and the
only difference is that srm_ballistics.py also fills and empties the free volume.
Impulse will NOT agree exactly: OpenMotor multiplies Cf by a throat-length loss
(0.99 - 0.0333 L/Dt = 0.984 here) and a fixed 0.99 skin term that srm_ballistics.py
does not carry, so OpenMotor lands ~2.5 % lower.  Both numbers are reported.
"""

from __future__ import annotations

import json
import os
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def load_openmotor():
    src = os.environ.get("OPENMOTOR_SRC", r"D:\srm100_scratch\openmotor_src")
    if not Path(src, "motorlib").is_dir():
        raise SystemExit(f"OpenMotor source not found at {src!r}; set OPENMOTOR_SRC")
    sys.path.insert(0, src)
    try:
        import mathlib._find_perimeter_cy  # noqa: F401
    except ImportError:
        stub = types.ModuleType("mathlib._find_perimeter_cy")

        def _get_perimeter(*_a, **_k):
            raise NotImplementedError("compiled perimeter helper not built; BATES never needs it")

        stub._get_perimeter = _get_perimeter
        sys.modules["mathlib._find_perimeter_cy"] = stub
    import motorlib.motor
    return motorlib.motor


def read_ric(path: Path) -> dict:
    """The .ric carries two python-tagged keys OpenMotor's GUI needs; the solver only
    needs 'data', so the tags are ignored rather than constructed."""
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor("tag:yaml.org,2002:python/",
                                 lambda loader, suffix, node: None)
    return yaml.load(path.read_text(), Loader=Loader)["data"]


def main() -> None:
    warnings.filterwarnings("ignore")
    motor_mod = load_openmotor()
    ric = OUT / "srm100.ric"
    ours_path = OUT / "srm_ballistics.json"
    if not ric.exists() or not ours_path.exists():
        raise SystemExit("run srm_ballistics.py first")
    r = motor_mod.Motor(read_ric(ric)).runSimulation()
    if not r.success:
        raise SystemExit(f"OpenMotor simulation failed: {[a.description for a in r.alerts]}")
    om = {
        "designation": r.getDesignation(),
        "impulse_ns": r.getImpulse(),
        "burn_time_s": r.getBurnTime(),
        "avg_thrust_n": r.getAverageForce(),
        "peak_thrust_n": r.channels["force"].getMax(),
        "pc_peak_mpa": r.getMaxPressure() / 1e6,
        "kn_initial": r.getInitialKN(),
        "kn_peak": r.getPeakKN(),
        "isp_s": r.getISP(),
        "prop_mass_kg": r.getPropellantMass(),
        "G_aft_peak_kg_m2s": r.getPeakMassFlux(),
        "port_throat": r.getPortRatio(),
        "alerts": [f"{a.level.name}: {a.description}" for a in r.alerts],
    }
    js = json.loads(ours_path.read_text())
    ours = js["runs"]["ideal"]
    print(f"{'':22s} {'OpenMotor':>12s} {'ideal run':>15s} {'delta':>8s}")
    for k in ("impulse_ns", "burn_time_s", "avg_thrust_n", "peak_thrust_n", "pc_peak_mpa",
              "kn_initial", "kn_peak", "isp_s", "prop_mass_kg", "G_aft_peak_kg_m2s", "port_throat"):
        a, b = om[k], ours[k]
        print(f"{k:22s} {a:12.4g} {b:15.4g} {100.0 * (b - a) / a:+7.2f}%")
    print(f"{'designation':22s} {om['designation']:>12s} {ours['designation']:>15s}")
    print("OpenMotor alerts:", om["alerts"] or "none")
    nom = js["runs"]["nominal"]
    print(f"(for reference, the nominal run -- as-cast density, c* x {js['model']['cstar_eff']:.2f}, "
          f"Mukunda-Paul -- is {nom['designation']}, {nom['impulse_ns']:.0f} N s, Pc peak {nom['pc_peak_mpa']:.2f} MPa)")
    (OUT / "srm_openmotor_check.json").write_text(json.dumps(
        {"openmotor": om, "compared_with": "srm_ballistics runs.ideal",
         "ideal": {k: ours[k] for k in om if k in ours}}, indent=2))
    bad = [k for k in ("pc_peak_mpa", "kn_initial", "kn_peak", "prop_mass_kg")
           if abs(ours[k] - om[k]) / om[k] > 0.01]
    if bad:
        raise SystemExit(f"disagreement above 1 % in {bad}")
    print("pressure, Kn and propellant mass agree within 1 %")


if __name__ == "__main__":
    main()
