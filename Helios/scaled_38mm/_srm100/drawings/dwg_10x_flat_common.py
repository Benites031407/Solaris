"""Local drawing primitives shared by the flat-part sheets SRM100-107 / -108 / -109.

Nothing here edits srm_dwg; everything is built from Sheet.line / Sheet.text /
Sheet.fill / Sheet.lines and View attributes.

  notes_block      numbered notes like Sheet.notes, but numbering can continue from
                   `start` (a notes list split over two columns)
  phantom_parts    adjacent parts (ISO 128-2 type 05.1, long-dashed double-dotted,
                   thin, no hatching) in a partial side section, clipped to `window`
  part_view        the part itself in the same partial section, hatched, no axis
  mask             white box under a text that sits on hatching
  placed           srm_assembly.placements() rows by name
  clear_centring_mark   kit workaround: A4-portrait bottom centring mark through
                   the identification number
  zig_window       break lines on the open sides of a partial view window
  lint_marks       local lint: text on the ISO 5457 centring marks
"""

import textwrap

import numpy as np

import srm_dwg as D
from srm_dwg import H, THIN, Part, View


def notes_block(sh, x, y_top, items, width, start=1, title="NOTES", h=H, gap=1.55):
    """Sheet.notes with numbering from `start`; returns the y below the last line."""
    y = y_top
    if title:
        sh.text(x, y - 3.5, title, 3.5, bold=True)
        y -= 3.5 + h * 1.9
    cw = sh.text_width("M" * 20, h) / 20 * 0.78
    indent = sh.text_width("00. ", h)
    for k, item in enumerate(items, start):
        wrapped = textwrap.wrap(item, max(10, int((width - indent) / cw))) or [""]
        sh.text(x, y, f"{k}.", h)
        for s in wrapped:
            sh.text(x + indent, y, s, h)
            y -= h * gap
        y -= h * 0.45
    return y


def placed(names):
    """{name: (step, trsf)} for the named srm_assembly.placements() rows."""
    import srm_assembly as A
    rows = {n: (st, tr) for _, n, st, tr in A.placements()}
    return {n: rows[n] for n in names}


def silhouette(v):
    """Paper polygon covered by a (drawn or undrawn) side view's parts: the faces
    bounded by its visible and hidden edges."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    ls = [LineString(v.pts(p)) for c in ("vis", "hid") for p in v.geo["lines"][c] if len(p) >= 2]
    return unary_union(list(polygonize(unary_union(ls)))) if ls else None


def phantom_parts(sh, parts, origin, scale, window, section="full", occluders=()):
    """Adjacent parts: visible edges of the section as thin phantom lines (ISO 128-2
    type 05.1), clipped to the view window, no hatching.  `occluders`: Parts drawn
    separately in front of them (the detailed part): the phantom lines are cut out
    of their silhouette, since an HLR run without them cannot know they hide those
    edges.  Returns the (undrawn) View for its mapping."""
    from shapely.geometry import LineString
    v = View(sh, parts, origin, scale, look="side", section=section, window=window,
             draw=False)
    polys = v._clip_lines([v.pts(p) for p in v.geo["lines"]["vis"]])
    if occluders:
        ov = View(sh, list(occluders), origin, scale, look="side", section=section, draw=False)
        sil = silhouette(ov)
        if sil is not None and not sil.is_empty:
            sil = sil.buffer(-0.05)
            out = []
            for p in polys:
                g = LineString(p).difference(sil)
                for ln in getattr(g, "geoms", [g]):
                    if isinstance(ln, LineString) and not ln.is_empty and ln.length > 0.05:
                        out.append(np.asarray(ln.coords))
            polys = out
    sh.lines(polys, THIN, "phantom", z=3)
    return v


def part_view(sh, part, origin, scale, window, section="full"):
    """The part itself in the same partial section (hatched, thick outline)."""
    return View(sh, part, origin, scale, look="side", section=section, window=window,
                axis=False)


def mask(sh, x0, y0, x1, y1, z=2.5):
    """White box over hatching (hatching is drawn at z 2), under outlines and text."""
    sh.fill([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], color="w", z=z)


def text_box(sh, x, y, s, h=H, ha="left", pad=0.6):
    """Paper bbox (x0, y0, x1, y1) of a text drawn with Sheet.text at (x, y)."""
    w = sh.text_width(s, h)
    x0 = x if ha == "left" else (x - w / 2 if ha == "center" else x - w)
    return (x0 - pad, y - pad - 0.2 * h, x0 + w + pad, y + h + pad)


def clear_centring_mark(sh):
    """Kit workaround (Sheet._draw_frame): on A4 portrait the bottom centring mark at
    x = frame centre runs 5 mm up into the title block's IDENTIFICATION NUMBER cell and
    strikes through the number.  White-out the part inside the frame (z 5: above the
    lines, below the text at z 6); the mark outside the frame is kept."""
    x0, y0, x1, y1 = sh.frame
    tx0, ty0, tx1, ty1 = sh.tb
    cx = (x0 + x1) / 2
    if tx0 < cx < tx1:
        mask(sh, cx - 0.45, y0 + 0.36, cx + 0.45, y0 + 5.3, z=5)


def lint_marks(sh, clear=0.5):
    """Local lint (Sheet.lint does not check it): text boxes that touch an ISO 5457
    centring mark where it runs 5 mm into the drawing area, or reach into the
    title block's frame line.  Prints 'LINT-LOCAL ...' and returns the list."""
    x0, y0, x1, y1 = sh.frame
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    marks = [(x0, cy - clear, x0 + 5.0 + clear, cy + clear),
             (x1 - 5.0 - clear, cy - clear, x1, cy + clear),
             (cx - clear, y1 - 5.0 - clear, cx + clear, y1)]
    inv = sh.ax.transData.inverted()
    out = []
    for t in sh.texts:
        s = t.get_text().strip()
        if not s:
            continue
        b = t.get_window_extent(sh._renderer).transformed(inv)
        for m in marks:
            if b.x0 < m[2] and b.x1 > m[0] and b.y0 < m[3] and b.y1 > m[1]:
                out.append(f"text on centring mark: {s!r}")
    for s in out:
        print("LINT-LOCAL", s)
    return out


def zig_window(v, window, sides, n=None):
    """Break lines (ISO 128-2 type 01.1 freehand-straight with zig-zags) on the named
    open sides of a partial view window: any of 'left', 'right', 'bottom', 'top'."""
    u0, w0, u1, w1 = window
    seg = {"left": ((u0, w0), (u0, w1)), "right": ((u1, w0), (u1, w1)),
           "bottom": ((u0, w0), (u1, w0)), "top": ((u0, w1), (u1, w1))}
    for s in sides:
        a, b = seg[s]
        v.zigzag(a, b, n=n, ext=0.0)


def paper(v, u, w):
    return np.asarray(v.pt(u, w), float)
