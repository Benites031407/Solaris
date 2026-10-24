"""Helios side-door nose preview: housing, door closed, servo envelope latched in its
slot with the keeper under it, springs compressed, and the two airframe screws.

The door is printed standing on its floor block, so the assembly lifts it onto the band.
"""

from cadgen import build123d as bd
from cadgen import step

from helios_nose_door import helios_nose_door
from helios_nose_door_housing import helios_nose_door_housing
from helios_nose_servo_keeper import helios_nose_servo_keeper
from lib.door_parts import door_levels, keeper_lift, make_screw_dummies, make_servo_dummy, make_spring_dummies


@step(out="../STEP/helios_nose_door_assembly.step")
def helios_nose_door_assembly():
    z_d0, _ = door_levels()
    door = helios_nose_door().moved(bd.Pos(0, 0, z_d0))
    door.label = "helios_nose_door"
    keeper = helios_nose_servo_keeper().moved(bd.Pos(0, 0, keeper_lift()))
    keeper.label = "helios_nose_servo_keeper"
    return bd.Compound(children=[helios_nose_door_housing(), door, keeper, make_servo_dummy(0.0), *make_spring_dummies(),
                                 *make_screw_dummies()], label="helios_nose_door_assembly")


if __name__ == "__main__":
    helios_nose_door_assembly()
