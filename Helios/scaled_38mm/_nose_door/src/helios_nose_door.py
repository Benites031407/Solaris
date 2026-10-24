"""Side door for the Helios side-door nose; print standing on its floor block (use a brim)."""

from cadgen import step, stl, threemf

from lib.door_parts import make_nose_door

MESH_TOL = 1e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/helios_nose_door.step")
@stl(out="../STL/helios_nose_door.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/helios_nose_door.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def helios_nose_door():
    return make_nose_door()


if __name__ == "__main__":
    helios_nose_door()
