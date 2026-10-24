"""Side-door nose preview: housing, door closed, SG90 envelope latched, springs compressed.

The door is printed standing on its floor block, so the assembly lifts it onto the band.
"""

from cadgen import build123d as bd
from cadgen import step

from lib.rocket_parts import door_levels, make_servo_dummy, make_spring_dummies
from nose_cone_door import nose_cone_door
from nose_cone_door_housing import nose_cone_door_housing


@step(out="../STEP/nose_cone_door_assembly.step")
def nose_cone_door_assembly():
    z_d0, _ = door_levels()
    door = nose_cone_door().moved(bd.Pos(0, 0, z_d0))
    door.label = "nose_cone_door"
    return bd.Compound(children=[nose_cone_door_housing(), door, make_servo_dummy(0.0), *make_spring_dummies()],
                       label="nose_cone_door_assembly")


if __name__ == "__main__":
    nose_cone_door_assembly()
