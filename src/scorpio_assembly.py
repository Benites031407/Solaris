"""Whole-rocket preview: the printed parts in flight position on the purchased tubes.

Z = 0 is the fin-can aft face, +Z forward. Tubes are labelled *_not_printed.
"""

from cadgen import build123d as bd
from cadgen import step

from coupler import coupler
from fin import fin
from fin_can import fin_can
from fin_lock_ring import fin_lock_ring
from lib import params as p
from lib.rocket_parts import LOCK_ANGLE, cap_engaged_angle, engine_stop_z, fin_housing_radii, make_tube
from nose_cone import nose_cone
from retainer_female import retainer_female
from retainer_male import retainer_male


@step(out="../STEP/scorpio_assembly.step")
def scorpio_assembly():
    _, _, housing_top = fin_housing_radii()
    retainer_len = p.MALE_BAND_LEN + p.MALE_THREAD_LEN
    z_lower_bottom = p.FIN_CAN_LEN + p.LOCK_RING_THICKNESS  # tube end rests on the lock ring
    z_lower_top = z_lower_bottom + p.LOWER_TUBE_LEN
    z_upper_bottom = z_lower_top + p.COUPLER_BAND_LEN
    z_upper_top = z_upper_bottom + p.UPPER_TUBE_LEN

    children = [fin_can()]
    blade = fin()
    for i in range(p.FIN_COUNT):
        angle = p.FIN_ANGLE0 + i * 360.0 / p.FIN_COUNT
        # Pushed aft against the housing stop, 0.2 mm short of the ring at the front.
        placed = blade.moved(bd.Rot(0, 0, angle) * bd.Pos(housing_top, 0, p.FIN_HOUSING_AFT_STOP + 0.2))
        placed.label = f"fin:{i + 1}"
        children.append(placed)
    # Lock ring on the stub, turned to the locked position (notches between fins).
    children.append(fin_lock_ring().moved(bd.Pos(0, 0, p.FIN_CAN_LEN) * bd.Rot(0, 0, p.FIN_ANGLE0 + LOCK_ANGLE)))
    # Male retainer flips band-forward against the fin-can aft face; the cap is
    # screwed on until it seats on the band, phased so the threads interleave.
    children.append(retainer_male().moved(bd.Rot(180, 0, 0)))
    cap_z = -(p.MALE_BAND_LEN + p.CAP_LIP + p.CAP_THREAD_LEN)
    children.append(retainer_female().moved(bd.Pos(0, 0, cap_z) * bd.Rot(0, 0, cap_engaged_angle())))
    children.append(
        make_tube(p.MOTOR_TUBE_OD, p.MOTOR_TUBE_ID, engine_stop_z() + retainer_len,
                  "motor_tube_not_printed", p.MOTOR_TUBE_COLOR).moved(bd.Pos(0, 0, -retainer_len))
    )
    children.append(
        make_tube(p.BODY_OD, p.BODY_ID, p.LOWER_TUBE_LEN, "lower_tube_not_printed", p.TUBE_COLOR)
        .moved(bd.Pos(0, 0, z_lower_bottom))
    )
    children.append(coupler().moved(bd.Pos(0, 0, z_lower_top - p.COUPLER_STUB_LEN)))
    children.append(
        make_tube(p.BODY_OD, p.BODY_ID, p.UPPER_TUBE_LEN, "upper_tube_not_printed", p.TUBE_COLOR)
        .moved(bd.Pos(0, 0, z_upper_bottom))
    )
    children.append(nose_cone().moved(bd.Pos(0, 0, z_upper_top - p.NOSE_SHOULDER_LEN)))
    return bd.Compound(children=children, label="scorpio_assembly")


if __name__ == "__main__":
    scorpio_assembly()
