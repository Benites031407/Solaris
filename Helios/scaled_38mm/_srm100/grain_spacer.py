"""Phenolic grain spacer ring, 3 mm: holds the segments apart so both ends burn.

Frame: z = 0 at the ring's aft face.  Five instances: aft of segment 1, between
each pair, forward of segment 4 (srm_params.spacer_z()).
It bears on the casting-tube ends, covering only 0.4 mm of each grain face.
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(P.SPACER_ID / 2.0, P.SPACER_OD / 2.0, 0.0, P.SPACER_T)
    return finish(shape, "grain_spacer", (0.45, 0.25, 0.10))


def gen_dxf():
    """Flat cutting profile (drawing SRM100-109): OD and ID as two closed circles on
    layer CUT, mm, centred on the origin (nominal sizes: the router / lathe program
    applies the tolerance mid-points of the drawing)."""
    import ezdxf
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 4                      # millimetres
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT", color=7)
    msp = doc.modelspace()
    for r in (P.SPACER_OD / 2.0, P.SPACER_ID / 2.0):
        msp.add_circle((0.0, 0.0), r, dxfattribs={"layer": "CUT"})
    return doc
