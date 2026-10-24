"""Nose cone with a closed base and a boss for a screw hook / screw eye; print tip-up (base on the bed)."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_nose_cone

MESH_TOL = 8e-5  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/nose_cone_hook.step")
@stl(out="../STL/nose_cone_hook.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/nose_cone_hook.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def nose_cone_hook():
    return make_nose_cone(mount="hook")


if __name__ == "__main__":
    nose_cone_hook()
