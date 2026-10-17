"""Twist-lock ring that holds the fins in their housings; print aft face (wide side) down."""

from cadgen import step, stl, threemf

from lib.rocket_parts import make_fin_lock_ring

MESH_TOL = 3e-4  # relative chord tolerance (~0.02 mm on this part)
MESH_ANGLE = 0.1  # radians


@step(out="../STEP/fin_lock_ring.step")
@stl(out="../STL/fin_lock_ring.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/fin_lock_ring.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def fin_lock_ring():
    return make_fin_lock_ring()


if __name__ == "__main__":
    fin_lock_ring()
