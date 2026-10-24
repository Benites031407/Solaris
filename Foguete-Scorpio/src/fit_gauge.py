"""Fit gauge for the body-tube ID and motor-tube OD; print first."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_fit_gauge

MESH_TOL = 2.5e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/fit_gauge.step")
@stl(out="../STL/fit_gauge.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/fit_gauge.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def fit_gauge():
    return make_fit_gauge()


if __name__ == "__main__":
    fit_gauge()
