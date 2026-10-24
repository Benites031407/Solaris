"""Fin can with 3 T-slots, motor bore and engine block; print aft face down."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_fin_can

MESH_TOL = 1.2e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/fin_can.step")
@stl(out="../STL/fin_can.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/fin_can.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def fin_can():
    return make_fin_can()


if __name__ == "__main__":
    fin_can()
