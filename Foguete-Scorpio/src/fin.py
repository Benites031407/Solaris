"""Swept fin with T-rail root; print 3, standing on the trailing edge."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_fin

MESH_TOL = 1.4e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/fin.step")
@stl(out="../STL/fin.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/fin.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def fin():
    return make_fin()


if __name__ == "__main__":
    fin()
