"""Nose cone with an open base and a bar to tie the shock cord (room for clay nose weight); print tip-up."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_nose_cone

MESH_TOL = 8e-5  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/nose_cone_open.step")
@stl(out="../STL/nose_cone_open.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/nose_cone_open.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def nose_cone_open():
    return make_nose_cone(mount="open")


if __name__ == "__main__":
    nose_cone_open()
