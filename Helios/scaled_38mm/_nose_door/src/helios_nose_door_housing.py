"""Helios side-door nose housing (shoulder, band, half-shell, tip, servo mount); print upright, shoulder down."""

from cadgen import step, stl, threemf

from lib.door_parts import make_nose_door_housing

MESH_TOL = 8e-5  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/helios_nose_door_housing.step")
@stl(out="../STL/helios_nose_door_housing.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/helios_nose_door_housing.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def helios_nose_door_housing():
    return make_nose_door_housing()


if __name__ == "__main__":
    helios_nose_door_housing()
