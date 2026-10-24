"""Knurled female retainer cap; print lip down."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_retainer_female

MESH_TOL = 3e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/retainer_female.step")
@stl(out="../STL/retainer_female.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/retainer_female.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def retainer_female():
    return make_retainer_female()


if __name__ == "__main__":
    retainer_female()
