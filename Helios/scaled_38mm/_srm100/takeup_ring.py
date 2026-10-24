"""Closed-cell silicone sponge ring: the stack's axial take-up.

Frame: z = 0 at its aft face, which sits on the forwardmost spacer.
Drawn at its nominal INSTALLED thickness (TAKEUP_T 3.0); cut from TAKEUP_FREE_T
(4.8) sheet.  It keeps the segments from rattling under boost and absorbs the
+/-0.50 mm worst-case stack of 4 grains faced to +/-0.10 and 5 spacers at +/-0.02,
staying inside silicone sponge's 25 - 50 % compression band.  Its forward face
bears on the EPDM forward insulator.  At assembly: measure the gap (cavity - stack);
use any 3.2 / 4.8 / 6.4 sheet that gives gap / free thickness 0.50 - 0.75; no shims.
"""

import srm_params as P
from srm_build import finish, tube


def gen_step():
    shape = tube(P.TAKEUP_ID / 2.0, P.TAKEUP_OD / 2.0, 0.0, P.TAKEUP_T)
    return finish(shape, "takeup_ring", (0.85, 0.30, 0.20))


def gen_dxf():
    """Flat cutting profile (drawing SRM100-108): OD and ID as two closed circles on
    layer CUT, mm, centred on the origin.  The profile does not depend on the
    thickness: it is cut from the free (TAKEUP_FREE_T) sheet."""
    import ezdxf
    doc = ezdxf.new("R2010", setup=False)
    doc.header["$INSUNITS"] = 4                      # millimetres
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("CUT", color=7)
    msp = doc.modelspace()
    for r in (P.TAKEUP_OD / 2.0, P.TAKEUP_ID / 2.0):
        msp.add_circle((0.0, 0.0), r, dxfattribs={"layer": "CUT"})
    return doc
