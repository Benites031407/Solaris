"""Top guide of the sleeve mold, as it prints (plate down).  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish

NAME, MAKE, _, RGB = next(p for p in S.PARTS if p[0] == "sleeve_mold_top_guide")


def gen_step():
    return finish(MAKE(), NAME, RGB)
