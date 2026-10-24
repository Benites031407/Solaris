"""Servo keeper for the Helios side-door nose: fills the slot under the MG90S so it can't
drop out of the shoulder base. Print on its tabs (the face on the bed is the one that
faces the shoulder base); two M2 x 8 self-tappers go up through it into the housing.

Its meshes come from OCCT's own mesher: cadgen's tessellator leaves open edges on this
outline (a cross of boxes, with four corners on a line)."""

from pathlib import Path

from cadgen import build123d as bd
from cadgen import step

from lib.door_parts import make_servo_keeper

HERE = Path(__file__).resolve().parent


@step(out="../STEP/helios_nose_servo_keeper.step")
def helios_nose_servo_keeper():
    return make_servo_keeper()


def write_meshes() -> None:
    part = make_servo_keeper()
    bd.export_stl(part, str(HERE.parent / "STL" / "helios_nose_servo_keeper.stl"), tolerance=0.01, angular_tolerance=0.1)
    mesher = bd.Mesher()
    mesher.add_shape(part, linear_deflection=0.01, angular_deflection=0.1)
    mesher.write(str(HERE.parent / "3MF" / "helios_nose_servo_keeper.3mf"))


if __name__ == "__main__":
    helios_nose_servo_keeper()
    write_meshes()
