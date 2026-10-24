"""One sleeve-mold half as it prints (parting face up).  Print TWO.  Geometry lives in sleeve_mold.py."""

import sleeve_mold as S
from mold_build import finish


def gen_step():
    return finish(S.half_printed(), "sleeve_mold_half", (0.20, 0.55, 0.85))
