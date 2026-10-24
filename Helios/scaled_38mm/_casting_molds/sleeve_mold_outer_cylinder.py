"""Outer cylinder of the sleeve mold: its bore forms the sleeve's OD.  Either end up.  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish

NAME, MAKE, _, RGB = next(p for p in S.PARTS if p[0] == "sleeve_mold_outer_cylinder")


def gen_step():
    return finish(MAKE(), NAME, RGB)
