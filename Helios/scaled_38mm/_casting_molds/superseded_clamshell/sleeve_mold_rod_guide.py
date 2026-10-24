"""The sleeve-mold rod guide as it prints (plate down).  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish


def gen_step():
    return finish(S.rod_guide_printed(), "sleeve_mold_rod_guide", (0.95, 0.60, 0.15))
