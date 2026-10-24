"""EPDM forward insulator: protects the aluminium forward closure's face.

Frame: z = 0 at its aft face (on the liner end), +Z toward the closure.
Covers the liner end and the whole closure face: a full disc (the closure has no port).
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(0.0, P.FWD_INSUL_OD / 2.0, 0.0, P.FWD_INSUL_T)
    return finish(shape, "fwd_insulator", (0.08, 0.08, 0.09))


def gen_dxf():
    """Flat cutting profile (drawing SRM100-107): the OD as one closed circle on
    layer CUT, mm, centred on the origin, seen from forward."""
    import ezdxf
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 4                      # millimetres
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT", color=7)
    msp = doc.modelspace()
    msp.add_circle((0.0, 0.0), P.FWD_INSUL_OD / 2.0, dxfattribs={"layer": "CUT"})
    return doc
