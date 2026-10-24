"""Body-tube coupler with 1010 rail guide and 1/4 in launch lug; print upright."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_coupler

MESH_TOL = 1.5e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/coupler.step")
@stl(out="../STL/coupler.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/coupler.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def coupler():
    return make_coupler()


if __name__ == "__main__":
    coupler()
