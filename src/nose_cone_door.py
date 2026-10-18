"""Side door for the side-door nose; print standing on its floor block (use a brim)."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_nose_door

MESH_TOL = 1e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/nose_cone_door.step")
@stl(out="../STL/nose_cone_door.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/nose_cone_door.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def nose_cone_door():
    return make_nose_door()


if __name__ == "__main__":
    nose_cone_door()
