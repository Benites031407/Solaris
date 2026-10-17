"""Hollow tangent-ogive nose cone; print tip-up (shoulder on the bed)."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_nose_cone

MESH_TOL = 8e-5  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/nose_cone.step")
@stl(out="../STL/nose_cone.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/nose_cone.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def nose_cone():
    return make_nose_cone()


if __name__ == "__main__":
    nose_cone()
