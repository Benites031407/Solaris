"""Foot of the sleeve mold: the outer cylinder's bottom end pushes into its collar.  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish

NAME, MAKE, _, RGB = next(p for p in S.PARTS if p[0] == "sleeve_mold_foot")


def gen_step():
    return finish(MAKE(), NAME, RGB)
