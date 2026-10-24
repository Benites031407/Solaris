"""The sleeve-mold stand as it prints (plate down).  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish


def gen_step():
    return finish(S.stand_printed(), "sleeve_mold_stand", (0.55, 0.55, 0.60))
