"""Print plate: the 3 fins standing on their trailing edges, 20 mm apart (use a brim)."""

from cadgen import build123d as bd
from cadgen import stl, threemf

from fin import fin

MESH_TOL = 1.4e-4  # relative chord tolerance (~0.02 mm per fin)
MESH_ANGLE = 0.1  # radians
PITCH = 20.0  # mm between fin planes


@stl(out="../STL/plate_fins_x3.stl", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
@threemf(out="../3MF/plate_fins_x3.3mf", mesh_tolerance=MESH_TOL, mesh_angular_tolerance=MESH_ANGLE)
def plate_fins_x3():
    blade = fin()
    fins = []
    for i in range(3):
        placed = blade.moved(bd.Pos(0, (i - 1) * PITCH, 0))
        placed.label = f"fin:{i + 1}"
        fins.append(placed)
    return bd.Compound(children=fins, label="plate_fins_x3")


if __name__ == "__main__":
    plate_fins_x3()
