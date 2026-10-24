"""SRM-100 drawing kit: ISO-style manufacturing sheets drawn from the STEP files.

Sheets follow ISO conventions: ISO 5457 frame, ISO 7200 title block, first-angle
projection, millimetres, ISO 128 line types and ISO 129 dimensioning.  Matplotlib
draws them straight to vector PDF.

Views come off the solids through OCCT's exact hidden-line removal (HLRBRep), so
every outline on a sheet is the model's own.  Section hatching is the solid's real
intersection with the cutting plane.

Dimensions attach to MODEL coordinates of a view.  Unless a sheet overrides the
text, the printed number is computed from those coordinates, so a dimension cannot
disagree with the geometry it points at.  Sheet scripts take the coordinates from
srm_params and the part generators' section() paths: the same numbers the STEP was
built from.

Coordinates
-----------
paper       mm from the sheet's lower-left corner; the axes span the sheet 1:1.
view (u, v) the model projected into the view plane, in model mm:
  look="side"  viewer on +Y, u = model z (forward to the RIGHT), v = model x (up)
  look="fwd"   seen from forward (+Z): u = x, v = y; theta counter-clockwise, as in
               srm_params
  look="aft"   seen from aft (-Z): u = -x, v = y
View.pt(u, v) maps a view point to paper; every View method takes view points.

Line widths: 0.5 thick (visible outlines), 0.25 thin (dimensions, hatching, centre
lines, tangent edges), 0.7 frame.  Text is ISO 3098-style (ISOCPEUR), 2.5 mm for
dimensions and notes, 3.5 for view labels, 5 / 7 in the title block.

HLR results are cached on D: (SRM_DWG_SCRATCH/hlr_cache), keyed on the STEP files'
size and mtime, so re-running a sheet script costs seconds.
"""

from __future__ import annotations

import hashlib
import math
import os
import pickle
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import (  # noqa: E402
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import polygonize, unary_union  # noqa: E402

HERE = Path(__file__).resolve().parent            # _srm100/drawings
ROOT = HERE.parent                                 # _srm100
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRATCH = Path(os.environ.get("SRM_DWG_SCRATCH", r"D:\srm100_scratch\dwg"))
CACHE = SCRATCH / "hlr_cache"

# -----------------------------------------------------------------------------
# drafting constants
# -----------------------------------------------------------------------------
SIZES = {"A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0),
         "A1": (841.0, 594.0)}
PT = 72.0 / 25.4                 # points per mm
THICK, THIN, FRAME = 0.5, 0.25, 0.7
H = 2.5                          # dimension / note text height (cap height), mm
ARROW_L, ARROW_W = 2.5, 0.9      # closed filled arrowhead
DOT_R = 0.6                      # leader end dot (leader ending inside a surface)
EXT_GAP, EXT_OVER = 1.0, 2.0     # extension line: gap to the feature, overshoot
TEXT_GAP = 0.8                   # dimension text baseline above its line
DIM_STEP = 8.0                   # recommended spacing between stacked dimension lines
HATCH_SPACING = 2.0
DASH = {"hidden": (3.0, 1.0), "center": (10.0, 1.5, 1.5, 1.5),
        "phantom": (10.0, 1.5, 1.5, 1.5, 1.5, 1.5)}
FONT = ["ISOCPEUR", "Segoe UI Symbol", "DejaVu Sans"]
DATE = "2026-09-23"
DIA = "\u2300"                   # diameter sign
DEG = "\u00b0"
PM = "\u00b1"
TIMES = "\u00d7"
DEPTH = "\u21a7"                 # ISO 129 depth symbol
CBORE = "\u2334"
CSINK = "\u2335"
# geometric characteristic symbols (ISO 1101), rendered through the fallback font
GDT = {"straightness": "\u23e4", "flatness": "\u23e5", "circularity": "\u25cb",
       "cylindricity": "\u232d", "profile_line": "\u2312", "profile_surface": "\u2313",
       "parallelism": "\u2225", "perpendicularity": "\u27c2", "angularity": "\u2220",
       "position": "\u2316", "coaxiality": "\u25ce", "concentricity": "\u25ce",
       "symmetry": "\u232f", "runout": "\u2197", "total_runout": "\u2330"}

matplotlib.rcParams.update({
    "pdf.fonttype": 42,
    "lines.scale_dashes": False,
    "path.simplify": False,
    "font.family": FONT,
    "hatch.linewidth": THIN * PT,
})


def _cap_ratio() -> float:
    """Cap height / font size of the drawing font (glyph outline of 'H'), so text
    heights are true mm."""
    from matplotlib.textpath import TextPath
    v = TextPath((0, 0), "H", size=100, prop=FontProperties(family=FONT)).vertices
    return (v[:, 1].max() - v[:, 1].min()) / 100.0


CAP = _cap_ratio()


def fprop(h: float = H, bold: bool = False, italic: bool = False) -> FontProperties:
    return FontProperties(family=FONT, size=h * PT / CAP,
                          weight="bold" if bold else "normal",
                          style="italic" if italic else "normal")


def fmt(x: float, dec: int = 2) -> str:
    """ISO 129 number: round to `dec` places, strip trailing zeros ('38', '45.21')."""
    s = f"{x:.{dec}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _unit(v):
    v = np.asarray(v, float)
    n = np.hypot(*v)
    return v / n if n > 0 else v


def _perp(v):
    return np.array([-v[1], v[0]])


def _rot(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


# -----------------------------------------------------------------------------
# geometry: loading, HLR, sections
# -----------------------------------------------------------------------------
LOOKS = {
    # name: (N toward the viewer, paper-right direction); paper-up = N x right
    "side": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "fwd": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    "aft": ((0.0, 0.0, -1.0), (-1.0, 0.0, 0.0)),
}
BIG = 3000.0


def _uv_basis(look):
    n, vx = (np.array(a, float) for a in LOOKS[look])
    return vx, np.cross(n, vx)


_LOADED = {}


def load(src):
    """A STEP path (relative to _srm100 or absolute) or a build123d shape -> Solid/Compound."""
    from build123d import Compound, import_step
    if not isinstance(src, (str, Path)):
        return src
    p = Path(src)
    if not p.is_absolute():
        p = ROOT / p
    k = str(p.resolve())
    if k not in _LOADED:
        solids = import_step(str(p)).solids()
        _LOADED[k] = solids[0] if len(solids) == 1 else Compound(solids)
    return _LOADED[k]


def _src_key(src) -> str:
    if isinstance(src, (str, Path)):
        p = Path(src)
        if not p.is_absolute():
            p = ROOT / p
        st = p.stat()
        return f"{p.name}:{st.st_size}:{int(st.st_mtime)}"
    return f"shape:{id(src)}"


class Part:
    """One solid in a view.

    src      STEP path relative to _srm100 (or a build123d shape; uncached)
    trsf     16-float row-major 4x4 (srm_assembly.placements()), or None = identity
    hatch    Hatch for its section face, or None = not hatched
    cut      False: shown unsectioned in a section view (ISO 128-44: bolts, pins, shafts),
             drawn whole in front of or through the cutting plane
    occlude  its silhouette is cut out of every other part's hatching (for cut=False
             parts that sit in the cutting plane, e.g. a screw through a section)
    name     label, for balloons / debugging
    """

    def __init__(self, src, trsf=None, hatch=None, cut=True, occlude=None, name=None):
        self.src, self.trsf, self.cut = src, trsf, cut
        self.hatch = hatch if hatch is not None else Hatch()
        self.occlude = (not cut) if occlude is None else occlude
        self.name = name or (Path(src).stem if isinstance(src, (str, Path)) else "shape")

    def key(self):
        return (_src_key(self.src), tuple(np.round(self.trsf, 9)) if self.trsf is not None else None,
                self.cut, self.occlude)


class Hatch:
    """Section hatching: `angle` deg, `spacing` paper mm; solid=True fills black
    (ISO 128-50 thin sections, e.g. O-rings, gaskets); cross=True adds the 90 deg
    set; offset shifts the lines so adjacent parts do not line up."""

    def __init__(self, angle=45.0, spacing=HATCH_SPACING, solid=False, cross=False, offset=0.0,
                 lw=THIN, none=False):
        self.angle, self.spacing, self.solid, self.cross = angle, spacing, solid, cross
        self.offset, self.lw, self.none = offset, lw, none


def _edge_points(edge, defl=0.004):
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_TangentialDeflection
    from OCP.GeomAbs import GeomAbs_Line
    c = BRepAdaptor_Curve(edge)
    t0, t1 = c.FirstParameter(), c.LastParameter()
    if c.GetType() == GeomAbs_Line:
        ps = [c.Value(t0), c.Value(t1)]
    else:
        td = GCPnts_TangentialDeflection(c, t0, t1, 0.03, defl, 2, 1e-9, 0.0)
        ps = [td.Value(i) for i in range(1, td.NbPoints() + 1)]
    return np.array([[p.X(), p.Y(), p.Z()] for p in ps])


def _edges_of(shape):
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    out = []
    ex = TopExp_Explorer(shape, TopAbs_EDGE)
    while ex.More():
        out.append(TopoDS.Edge_s(ex.Current()))
        ex.Next()
    return out


def _hlr(wrapped, look):
    """Exact HLR -> {category: [polyline (n,2) in view (u, v)]}."""
    from OCP.BRepLib import BRepLib
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
    from OCP.HLRAlgo import HLRAlgo_Projector
    from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    n, vx = LOOKS[look]
    algo = HLRBRep_Algo()
    algo.Add(wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*vx))))
    algo.Update()
    algo.Hide()
    shp = HLRBRep_HLRToShape(algo)
    cats = {"vis": [shp.VCompound(), shp.OutLineVCompound()],
            "smooth": [shp.Rg1LineVCompound()],
            "hid": [shp.HCompound(), shp.OutLineHCompound()],
            "hid_smooth": [shp.Rg1LineHCompound()]}
    out = {}
    for cat, comps in cats.items():
        polys = []
        for comp in comps:
            if comp.IsNull():
                continue
            for e in _edges_of(comp):
                BRepLib.BuildCurves3d_s(e, 1e-6)
                p = _edge_points(e)
                if len(p) >= 2:
                    polys.append(p[:, :2])
        out[cat] = _chain(polys)
    return out


def _chain(polys, tol=1e-4):
    """Join polylines that share end points, so dash patterns run continuously."""
    polys = [np.asarray(p, float) for p in polys if len(p) >= 2]
    used = [False] * len(polys)
    out = []

    def close(a, b):
        return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol

    for i, p in enumerate(polys):
        if used[i]:
            continue
        used[i] = True
        cur = p
        grown = True
        while grown:
            grown = False
            for j, q in enumerate(polys):
                if used[j]:
                    continue
                if close(cur[-1], q[0]):
                    cur = np.vstack([cur, q[1:]])
                elif close(cur[-1], q[-1]):
                    cur = np.vstack([cur, q[::-1][1:]])
                elif close(cur[0], q[-1]):
                    cur = np.vstack([q, cur[1:]])
                elif close(cur[0], q[0]):
                    cur = np.vstack([q[::-1], cur[1:]])
                else:
                    continue
                used[j] = True
                grown = True
        out.append(cur)
    return out


def _face_polys(face_wrapped, basis):
    """A planar face -> shapely polygon in view (u, v)."""
    from OCP.BRepTools import BRepTools, BRepTools_WireExplorer
    from OCP.TopAbs import TopAbs_REVERSED, TopAbs_WIRE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    vx, vy = basis

    def ring(wire):
        pts = []
        ex = BRepTools_WireExplorer(wire, face_wrapped)
        while ex.More():
            p = _edge_points(ex.Current(), defl=0.002)
            if ex.Orientation() == TopAbs_REVERSED:
                p = p[::-1]
            pts.extend(p if not pts else p[1:])
            ex.Next()
        a = np.array(pts)
        return np.c_[a @ vx, a @ vy] if len(a) else a

    outer = BRepTools.OuterWire_s(face_wrapped)
    shell, holes = ring(outer), []
    ex = TopExp_Explorer(face_wrapped, TopAbs_WIRE)
    while ex.More():
        w = TopoDS.Wire_s(ex.Current())
        if not w.IsSame(outer):
            holes.append(ring(w))
        ex.Next()
    try:
        poly = Polygon(shell, [h for h in holes if len(h) >= 3]).buffer(0)
    except Exception:
        poly = Polygon()
    if poly.is_empty or poly.area < 1e-9:
        # fall back: polygonize every edge and keep the even-odd region
        lines = [LineString(r) for r in [shell, *holes] if len(r) >= 2]
        region = Polygon()
        for pg in polygonize(unary_union(lines)):
            region = region.symmetric_difference(pg)
        poly = region
    return poly


def _drop_on_axis(polys, tol=1e-3):
    """Split polylines where they run along v = 0 and drop those runs."""
    out = []
    for p in polys:
        on = (np.abs(p[:-1, 1]) < tol) & (np.abs(p[1:, 1]) < tol)
        run = [p[0]]
        for k in range(len(p) - 1):
            if on[k]:
                if len(run) >= 2:
                    out.append(np.array(run))
                run = [p[k + 1]]
            else:
                run.append(p[k + 1])
        if len(run) >= 2:
            out.append(np.array(run))
    return out


def _cut_tool(section, z_cut=None, keep="below"):
    from build123d import Align, Box, Location
    if section == "half":        # remove the quadrant facing the viewer, upper half
        return Box(BIG, BIG, 2 * BIG, align=(Align.MIN, Align.MIN, Align.CENTER))
    if section == "full":        # remove everything toward the viewer
        return Box(2 * BIG, BIG, 2 * BIG, align=(Align.CENTER, Align.MIN, Align.CENTER))
    if section == "transverse":  # remove the side toward the viewer
        if keep == "below":
            return Box(2 * BIG, 2 * BIG, BIG, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
                Location((0, 0, z_cut)))
        return Box(2 * BIG, 2 * BIG, BIG, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
            Location((0, 0, z_cut)))
    raise ValueError(section)


def _section_face(section, z_cut=None):
    from build123d import Face, Vector, Wire
    if section == "half":
        pts = [(0, 0, -BIG), (BIG, 0, -BIG), (BIG, 0, BIG), (0, 0, BIG)]
    elif section == "full":
        pts = [(-BIG, 0, -BIG), (BIG, 0, -BIG), (BIG, 0, BIG), (-BIG, 0, BIG)]
    else:
        pts = [(-BIG, -BIG, z_cut), (BIG, -BIG, z_cut), (BIG, BIG, z_cut), (-BIG, BIG, z_cut)]
    return Face(Wire.make_polygon([Vector(*p) for p in pts], close=True))


def _place(shape, trsf, rot):
    from build123d import Axis
    from srm_build import location
    if trsf is not None:
        shape = shape.moved(location(trsf))
    if rot:
        shape = shape.rotate(Axis.Z, rot)
    return shape


def compute_geometry(parts, look="side", section=None, rot=0.0, z_cut=None, keep="below",
                     use_cache=True):
    """Project `parts` -> dict(lines={cat: [polylines]}, faces=[(part_index, polygon)],
    occluders=[polygon], bounds=(u0, v0, u1, v1)); cached on D:."""
    from build123d import Compound
    key = hashlib.sha1(repr(([p.key() for p in parts], look, section, round(rot, 9),
                             z_cut, keep, 6)).encode()).hexdigest()[:20]
    cache = CACHE / f"{key}.pkl"
    if use_cache and cache.exists() and all(isinstance(p.src, (str, Path)) for p in parts):
        try:
            with open(cache, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass                          # torn or stale entry: recompute
    basis = _uv_basis(look)
    sec_kind = "transverse" if z_cut is not None else section
    placed, faces, occluders = [], [], []
    for i, part in enumerate(parts):
        s = _place(load(part.src), part.trsf, rot)
        if sec_kind and part.cut:
            face = _section_face(sec_kind, z_cut)
            try:
                inter = s.intersect(face)
                fl = inter.faces() if inter is not None else []
            except Exception:
                fl = []
            for f in fl:
                pg = _face_polys(f.wrapped, basis)
                if not pg.is_empty and part.hatch is not None and not part.hatch.none:
                    faces.append((i, pg))
            s = s - _cut_tool(sec_kind, z_cut, keep)
        elif sec_kind:
            # unsectioned part: dropped when it lies wholly in the removed material,
            # drawn whole when the cutting plane passes through it or it lies behind
            rem = s - _cut_tool(sec_kind, z_cut, keep)
            if not rem.solids() or sum(x.volume for x in rem.solids()) < 1e-6:
                continue
        if part.occlude:
            lines = _hlr(s.wrapped, look)
            ls = [LineString(p) for c in ("vis", "hid") for p in lines[c] if len(p) >= 2]
            sil = unary_union([pg for pg in polygonize(unary_union(ls))]) if ls else Polygon()
            occluders.append(sil.buffer(0.05))
        placed.extend(s.solids())
    comp = Compound(placed)
    lines = _hlr(comp.wrapped, look)
    allp = [p for c in lines.values() for p in c]
    if allp:
        a = np.vstack(allp)
        bounds = (a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())
    else:
        bounds = (0, 0, 0, 0)
    geo = {"lines": lines, "faces": faces, "occluders": occluders, "bounds": bounds}
    if all(isinstance(p.src, (str, Path)) for p in parts):
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_suffix(f".{os.getpid()}.tmp")
        with open(tmp, "wb") as f:
            pickle.dump(geo, f)
        os.replace(tmp, cache)            # atomic: sheet scripts may run in parallel
    return geo


# -----------------------------------------------------------------------------
# the sheet
# -----------------------------------------------------------------------------
class Sheet:
    """One drawing sheet.  Frame, zones and title block are drawn on creation.

    number    'SRM100-104'
    title     'NOZZLE INSERT'
    subtitle  supplementary title, one line
    material  material + stock spec, one or two lines ('\\n')
    mass_g    finished mass, g (None -> '-')
    scale     main scale string '2:1'
    sheet     (this sheet, of N)
    doc_type  'DETAIL DRAWING' | 'ASSEMBLY DRAWING' | ...
    tol       general tolerance line
    finish    general surface texture, e.g. 'Ra 3.2'  (None -> field shows '-')
    edges     edge condition per ISO 13715
    """

    def __init__(self, number, title, subtitle="", size="A3", material="", mass_g=None,
                 scale="1:1", sheet=(1, 1), rev="A", doc_type="DETAIL DRAWING",
                 tol="ISO 2768-mK", finish="Ra 3.2", edges="ISO 13715  -0.3 / +0.3",
                 status="NOT CHECKED - FOR REVIEW", owner="HELIOS  |  SRM-100 SOLID ROCKET MOTOR",
                 created="text-to-cad / Claude", approved="-", portrait=False):
        self.W, self.H = SIZES[size]
        if portrait:
            self.W, self.H = self.H, self.W
        self.size, self.number, self.title, self.sheet = size, number, title, sheet
        self.fig = plt.figure(figsize=(self.W / 25.4, self.H / 25.4), dpi=100)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(0, self.W)
        self.ax.set_ylim(0, self.H)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self._renderer = self.fig.canvas.get_renderer()
        self.texts = []
        self.frame = (20.0, 10.0, self.W - 10.0, self.H - 10.0)   # x0, y0, x1, y1
        self._draw_frame()
        self.tb = self._title_block(title, subtitle, material, mass_g, scale, rev, doc_type,
                                    tol, finish, edges, status, owner, created, approved)

    # ---- low level -------------------------------------------------------
    def line(self, pts, lw=THIN, style="solid", color="k", z=3, cap="round"):
        pts = np.asarray(pts, float)
        ls = (0, tuple(d * PT for d in DASH[style])) if style in DASH else "solid"
        self.ax.plot(pts[:, 0], pts[:, 1], lw=lw * PT, color=color, linestyle=ls,
                     solid_capstyle=cap, dash_capstyle="butt", solid_joinstyle="round", zorder=z)

    def lines(self, polys, lw=THIN, style="solid", color="k", z=3):
        if not polys:
            return
        ls = (0, tuple(d * PT for d in DASH[style])) if style in DASH else "solid"
        lc = LineCollection([np.asarray(p) for p in polys], linewidths=lw * PT, colors=color,
                            linestyles=[ls], capstyle="round", joinstyle="round", zorder=z)
        self.ax.add_collection(lc)

    def circle(self, c, r, lw=THIN, style="solid", n=180, a0=0.0, a1=360.0, z=3):
        t = np.radians(np.linspace(a0, a1, max(8, int(n * abs(a1 - a0) / 360.0) + 2)))
        self.line(np.c_[c[0] + r * np.cos(t), c[1] + r * np.sin(t)], lw, style, z=z)

    def fill(self, pts, color="k", z=4, lw=0.0):
        self.ax.add_patch(MplPolygon(np.asarray(pts), closed=True, fc=color, ec=color,
                                     lw=lw * PT, zorder=z))

    def text(self, x, y, s, h=H, ha="left", va="baseline", rot=0.0, bold=False, italic=False,
             color="k", z=6, track=True):
        t = self.ax.text(x, y, s, fontproperties=fprop(h, bold, italic), ha=ha, va=va,
                         rotation=rot, rotation_mode="anchor", color=color, zorder=z)
        if track:
            self.texts.append(t)
        return t

    def text_width(self, s, h=H, bold=False):
        t = Text(0, 0, s, fontproperties=fprop(h, bold))
        t.set_figure(self.fig)
        bb = t.get_window_extent(self._renderer)
        return bb.width / self.fig.dpi * 25.4

    def arrow(self, tip, direction, filled=True):
        """Arrowhead with its tip at `tip`, pointing along `direction` (paper)."""
        d = _unit(direction)
        n = _perp(d)
        b = np.asarray(tip, float) - d * ARROW_L
        pts = [tip, b + n * ARROW_W / 2, b - n * ARROW_W / 2]
        if filled:
            self.fill(pts, lw=0.05)
        else:
            self.line([pts[1], tip, pts[2]], THIN)

    def dot(self, p, r=DOT_R):
        self.fill(np.c_[p[0] + r * np.cos(np.linspace(0, 2 * np.pi, 24)),
                        p[1] + r * np.sin(np.linspace(0, 2 * np.pi, 24))])

    # ---- frame and title block -------------------------------------------
    def _draw_frame(self):
        x0, y0, x1, y1 = self.frame
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], FRAME, cap="projecting")
        self.line([(0.2, 0.2), (self.W - 0.2, 0.2), (self.W - 0.2, self.H - 0.2), (0.2, self.H - 0.2),
                   (0.2, 0.2)], 0.1, color="0.6")     # trimmed-sheet edge
        # centring marks (ISO 5457)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for a, b in (((cx, 0), (cx, y0 + 5)), ((cx, self.H), (cx, y1 - 5)),
                     ((0, cy), (x0 + 5, cy)), ((self.W, cy), (x1 - 5, cy))):
            self.line([a, b], FRAME)
        # grid reference zones: 50 mm fields from the centring marks (ISO 5457)
        nx = max(2, int(round((x1 - x0) / 50.0 / 2)) * 2)
        ny = max(2, int(round((y1 - y0) / 50.0 / 2)) * 2)
        xs = np.linspace(x0, x1, nx + 1)
        ys = np.linspace(y0, y1, ny + 1)
        for i, x in enumerate(xs[1:-1], 1):
            for yb, yt in ((y0 - 5, y0), (y1, y1 + 5)):
                self.line([(x, yb), (x, yt)], THIN)
        for j, y in enumerate(ys[1:-1], 1):
            for xa, xb in ((x0 - 5, x0), (x1, x1 + 5)):
                self.line([(xa, y), (xb, y)], THIN)
        for i in range(nx):
            xm = (xs[i] + xs[i + 1]) / 2
            for y in (y0 - 3.7, y1 + 1.3):
                self.text(xm, y, str(i + 1), 2.5, ha="center", track=False)
        letters = "ABCDEFGHJKLMNP"
        for j in range(ny):
            ym = (ys[ny - j] + ys[ny - j - 1]) / 2
            for x in (x0 - 2.5 if x0 > 12 else x0 - 2.5, x1 + 2.5):
                self.text(x, ym - 1.25, letters[j], 2.5, ha="center", track=False)
        self.zones = (xs, ys)

    def _cell(self, x, y, w, h, label, value="", vh=3.5, bold=False, align="left"):
        self.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], THIN)
        if label:
            self.text(x + 1.2, y + h - 2.6, label, 1.8, color="0.25", track=False)
        if value != "":
            lines = str(value).split("\n")
            n = len(lines)
            gap = vh * 1.45
            top = y + (h - 2.6) / 2 + (n - 1) * gap / 2 - vh / 2 + (0.3 if label else 1.3)
            for k, s in enumerate(lines):
                if align == "center":
                    self.text(x + w / 2, top - k * gap, s, vh, ha="center", bold=bold, track=False)
                else:
                    self.text(x + 2.0, top - k * gap, s, vh, bold=bold, track=False)

    def projection_symbol(self, x, y, h=3.5):
        """ISO 128 / ISO 5456-2 first-angle symbol, lower-left corner at (x, y)."""
        d = 2 * h
        # truncated cone, narrow end left; its end view (two circles) to the RIGHT = first angle
        self.line([(x, y + h / 2), (x + 2 * h, y), (x + 2 * h, y + d), (x, y + d - h / 2),
                   (x, y + h / 2)], THIN)
        cx = x + 2 * h + 1.0 * h + d / 2
        self.circle((cx, y + d / 2), d / 2, THIN)
        self.circle((cx, y + d / 2), h / 2, THIN)
        self.line([(x - 0.7 * h, y + d / 2), (cx + d / 2 + 0.7 * h, y + d / 2)], THIN, "center")
        self.line([(cx, y - 0.7 * h), (cx, y + d + 0.7 * h)], THIN, "center")

    def _title_block(self, title, subtitle, material, mass_g, scale, rev, doc_type, tol, finish,
                     edges, status, owner, created, approved):
        x1, y0 = self.frame[2], self.frame[1]
        W = 180.0
        x0 = x1 - W
        rows = [10.0, 16.0, 10.0, 10.0]     # bottom -> top
        ys = np.cumsum([y0] + rows)
        # row 0: identification
        self._cell(x0, ys[0], 40, rows[0], "CREATED BY", created, 2.5)
        self._cell(x0 + 40, ys[0], 20, rows[0], "APPROVED BY", approved, 2.5)
        self._cell(x0 + 60, ys[0], 24, rows[0], "DATE OF ISSUE", DATE, 2.5)
        self._cell(x0 + 84, ys[0], 58, rows[0], "IDENTIFICATION NUMBER", self.number, 5.0, bold=True)
        self._cell(x0 + 142, ys[0], 12, rows[0], "REV", rev, 3.5, align="center")
        self._cell(x0 + 154, ys[0], 26, rows[0], "SHEET",
                   f"{self.sheet[0]} / {self.sheet[1]}", 3.5, align="center")
        # row 1: owner + title
        self._cell(x0, ys[1], 60, rows[1], "LEGAL OWNER", owner.replace("  |  ", "\n"), 2.5)
        self._cell(x0 + 60, ys[1], 120, rows[1], "TITLE, SUPPLEMENTARY TITLE", "")
        self.text(x0 + 62, ys[1] + 7.2, title, 5.0, bold=True, track=False)
        if subtitle:
            self.text(x0 + 62, ys[1] + 2.4, subtitle, 2.5, track=False)
        # row 2: document type / status / scale / projection
        self._cell(x0, ys[2], 40, rows[2], "DOCUMENT TYPE", doc_type, 2.5)
        self._cell(x0 + 40, ys[2], 58, rows[2], "DOCUMENT STATUS", status, 2.5)
        self._cell(x0 + 98, ys[2], 22, rows[2], "SCALE", scale, 3.5, align="center")
        self._cell(x0 + 120, ys[2], 34, rows[2], "PROJECTION", "")
        self.projection_symbol(x0 + 126.0, ys[2] + 1.2, 2.3)
        self._cell(x0 + 154, ys[2], 26, rows[2], "UNITS", "mm", 3.5, align="center")
        # row 3: material / mass / general tolerances / finish / edges
        self._cell(x0, ys[3], 62, rows[3], "MATERIAL", material, 2.5)
        self._cell(x0 + 62, ys[3], 22, rows[3], "MASS",
                   "-" if mass_g is None else (f"{mass_g:.1f} g" if mass_g < 10000 else
                                               f"{mass_g / 1000:.2f} kg"), 2.5)
        self._cell(x0 + 84, ys[3], 30, rows[3], "GENERAL TOLERANCES", tol, 2.5)
        self._cell(x0 + 114, ys[3], 28, rows[3], "SURFACE TEXTURE", finish or "-", 2.5)
        self._cell(x0 + 142, ys[3], 38, rows[3], "EDGES", edges, 2.2)
        top = ys[-1]
        self.line([(x0, y0), (x0, top), (x1, top)], FRAME)
        return (x0, y0, x1, top)

    # ---- blocks ------------------------------------------------------------
    def notes(self, x, y_top, items, width, title="NOTES", h=H, numbered=True, gap=1.55):
        """Numbered notes, wrapped to `width` mm; returns the y below the last line."""
        y = y_top
        if title:
            self.text(x, y - 3.5, title, 3.5, bold=True)
            y -= 3.5 + h * 1.9
        cw = self.text_width("M" * 20, h) / 20 * 0.78         # mean char width
        chars = max(20, int(width / cw))
        for k, item in enumerate(items, 1):
            tag = f"{k}." if numbered else "-"
            indent = self.text_width("00. ", h) if numbered else self.text_width("- ", h)
            wrapped = textwrap.wrap(item, max(10, int((width - indent) / cw))) or [""]
            self.text(x, y, tag, h)
            for s in wrapped:
                self.text(x + indent, y, s, h)
                y -= h * gap
            y -= h * 0.45
        return y

    def table(self, x, y_top, widths, rows, h=H, row_h=None, header=1, align=None, bold_header=True,
              lw_outer=THICK):
        """Rows of cells, top-down; returns the table's bottom y.  `align` per column:
        'l', 'c', 'r'."""
        row_h = row_h or h * 2.4
        align = align or ["l"] * len(widths)
        xs = np.cumsum([x] + list(widths))
        y = y_top
        for r, row in enumerate(rows):
            nl = max(len(str(c).split("\n")) for c in row)
            rh = row_h + (nl - 1) * h * 1.5
            for c, cell in enumerate(row):
                lines = str(cell).split("\n")
                for k, s in enumerate(lines):
                    ty = y - (rh - (len(lines) - 1) * h * 1.5) / 2 - h / 2 - k * h * 1.5
                    a = align[c]
                    tx = {"l": xs[c] + 1.2, "c": (xs[c] + xs[c + 1]) / 2, "r": xs[c + 1] - 1.2}[a]
                    self.text(tx, ty, s, h, ha={"l": "left", "c": "center", "r": "right"}[a],
                              bold=bold_header and r < header)
            self.line([(x, y - rh), (xs[-1], y - rh)], THICK if r == header - 1 else THIN)
            y -= rh
        for k, xx in enumerate(xs):
            self.line([(xx, y_top), (xx, y)], lw_outer if k in (0, len(xs) - 1) else THIN)
        self.line([(x, y_top), (xs[-1], y_top)], lw_outer)
        self.line([(x, y), (xs[-1], y)], lw_outer)
        return y

    def general_finish(self, x, y, value="Ra 3.2", others=True):
        """ISO 1302 general surface-texture note next to the title block:
        the symbol with the general value, then (symbol) = 'unless otherwise stated'."""
        w = self.finish_symbol((x + 2.2, y), value, removal=True)
        if others:
            xx = x + w + 4
            self.text(xx, y + 2.0, "(", 5.0)
            self.finish_symbol((xx + 3.6, y + 0.8), "", removal=True, small=True)
            self.text(xx + 7.0, y + 2.0, ")", 5.0)

    def finish_symbol(self, tip, value="", removal=True, angle=0.0, small=False, lay=None):
        """ISO 1302 surface texture symbol; `tip` touches the surface (paper), the symbol
        stands on it at `angle` deg (0 = upright on a horizontal surface below it).
        Returns the symbol's width."""
        k = 0.7 if small else 1.0
        h1, h2 = 3.5 * k, 7.5 * k
        t60 = math.tan(math.radians(60))
        p0 = np.array([0.0, 0.0])
        ps = np.array([-h1 / t60, h1])
        pl = np.array([h2 / t60, h2])
        tw = self.text_width(value, H) if value else 0.0
        tr = lambda p: np.asarray(tip) + _rot(p, angle)
        self.line([tr(ps), tr(p0), tr(pl)], THIN)
        if removal:
            self.line([tr(ps), tr(np.array([h1 / t60, h1]))], THIN)
        if value:
            end = pl + np.array([tw + 1.5, 0.0])
            self.line([tr(pl), tr(end)], THIN)
            tp = tr(np.array([pl[0] + 0.2, h2 - 1.2 - H]))
            self.text(tp[0], tp[1], value, H, rot=angle)
        if lay:
            tp = tr(np.array([pl[0] + 0.3, h1 - 0.2]))
            self.text(tp[0], tp[1], lay, H, rot=angle)
        return pl[0] + tw + 1.5 + h1 / t60

    def fcf(self, x, y, cells, h=H, leader=None, leader_end="arrow"):
        """ISO 1101 feature control frame, lower-left corner at (x, y).
        cells: [characteristic key or symbol, tolerance text, datum, datum, ...].
        leader: paper point on the feature (arrow there), drawn from the frame's nearest
        end.  Returns (x0, y0, x1, y1)."""
        ch = h * 2.6
        xs = [x]
        items = []
        for k, c in enumerate(cells):
            s = GDT.get(c, c) if k == 0 else c
            w = ch if k == 0 else max(ch, self.text_width(s, h) + 2.4)
            items.append((s, w))
            xs.append(xs[-1] + w)
        for k, (s, w) in enumerate(items):
            self.line([(xs[k], y), (xs[k] + w, y), (xs[k] + w, y + ch), (xs[k], y + ch), (xs[k], y)],
                      THIN)
            self.text(xs[k] + w / 2, y + (ch - h) / 2, s, h * (1.2 if k == 0 else 1.0), ha="center")
        box = (x, y, xs[-1], y + ch)
        if leader is not None:
            lp = np.asarray(leader, float)
            start = np.array([x, y + ch / 2]) if lp[0] < x else np.array([xs[-1], y + ch / 2])
            if x <= lp[0] <= xs[-1]:
                start = np.array([lp[0], y if lp[1] < y else y + ch])
            self.line([start, lp], THIN)
            if leader_end == "arrow":
                self.arrow(lp, lp - start)
        return box

    def datum(self, foot, letter, direction, length=6.0):
        """ISO 5459 datum feature indicator: filled triangle standing on the feature at
        `foot` (paper), a line along `direction` to the square with the letter."""
        d = _unit(direction)
        n = _perp(d)
        base = np.asarray(foot, float)
        apex = base + d * 2.2
        self.fill([base + n * 1.5, base - n * 1.5, apex])
        s = 6.0
        c = base + d * (length + s / 2)
        self.line([apex, base + d * length], THIN)
        self.line([c + (-s / 2, -s / 2), c + (s / 2, -s / 2), c + (s / 2, s / 2), c + (-s / 2, s / 2),
                   c + (-s / 2, -s / 2)], THIN)
        self.text(c[0], c[1] - H / 2, letter, H * 1.2, ha="center")

    def balloon(self, target, number, at, r=4.0, end="dot"):
        """Item reference (ISO 6433): circle with the item number at paper `at`, leader
        to paper `target` ending in a dot (inside a part) or an arrow (on an edge)."""
        at, target = np.asarray(at, float), np.asarray(target, float)
        d = _unit(target - at)
        self.line([at + d * r, target], THIN)
        if end == "dot":
            self.dot(target)
        elif end == "arrow":
            self.arrow(target, d)
        self.circle(at, r, THIN)
        self.text(at[0], at[1] - 1.75, str(number), 3.5, ha="center")

    def label(self, x, y, s, h=3.5, ha="center"):
        return self.text(x, y, s, h, ha=ha)

    # ---- output ------------------------------------------------------------
    def lint(self, verbose=True):
        """Report text boxes that overlap each other or leave the drawing frame."""
        bbs = []
        for t in self.texts:
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(self._renderer).transformed(self.ax.transData.inverted())
            bbs.append((t.get_text(), bb))
        issues = []
        x0, y0, x1, y1 = self.frame
        for i, (s, b) in enumerate(bbs):
            if b.x0 < x0 or b.x1 > x1 or b.y0 < y0 or b.y1 > y1:
                issues.append(f"outside frame: {s!r}")
            for s2, b2 in bbs[i + 1:]:
                ox = min(b.x1, b2.x1) - max(b.x0, b2.x0)
                oy = min(b.y1, b2.y1) - max(b.y0, b2.y0)
                if ox > 0.3 and oy > 0.3:
                    issues.append(f"overlap: {s!r} / {s2!r}")
            tx0, ty0, tx1, ty1 = self.tb
            ox = min(b.x1, tx1) - max(b.x0, tx0)
            oy = min(b.y1, ty1) - max(b.y0, ty0)
            if ox > 0.3 and oy > 0.3:
                issues.append(f"on title block: {s!r}")
        if verbose:
            for s in issues:
                print("LINT", s)
        return issues

    def save(self, stem=None, png=True, dpi=150):
        """Write drawings/<number>[_shN]_<stem>.pdf and a PNG preview on D:."""
        stem = stem or self.title.lower().replace(" ", "_")
        tag = f"_sh{self.sheet[0]}" if self.sheet[1] > 1 else ""
        pdf = HERE / f"{self.number}{tag}_{stem}.pdf"
        self.fig.savefig(pdf, format="pdf")
        plt.close(self.fig)
        out = [pdf]
        if png:
            SCRATCH.mkdir(parents=True, exist_ok=True)
            out.append(render_png(pdf, SCRATCH / (pdf.stem + ".png"), dpi))
        print("wrote", *out)
        return out


def render_png(pdf, png, dpi=150, clip_mm=None):
    """PDF page -> PNG (optionally a paper-mm window x0, y0, x1, y1, origin lower-left)."""
    import fitz
    doc = fitz.open(str(pdf))
    page = doc[0]
    kw = {}
    if clip_mm:
        x0, y0, x1, y1 = clip_mm
        hpt = page.rect.height
        kw["clip"] = fitz.Rect(x0 * PT, hpt - y1 * PT, x1 * PT, hpt - y0 * PT)
    pix = page.get_pixmap(dpi=dpi, **kw)
    pix.save(str(png))
    doc.close()
    return Path(png)


# -----------------------------------------------------------------------------
# views
# -----------------------------------------------------------------------------
class View:
    """A projected view of one or more parts placed on a sheet.

    parts    Part, list of Part, or a STEP path
    origin   paper point where view (0, 0) lands
    scale    paper mm per model mm (2.0 for 2:1)
    look     'side' | 'fwd' | 'aft'
    section  None (outside view) | 'half' (upper half sectioned, lower half outside;
             the dividing line is the axis, drawn as a centre line) | 'full'
    z_cut    transverse section at this model z (look 'fwd'/'aft'); `keep` 'below'
             keeps z < z_cut (look 'fwd'), 'above' keeps z > z_cut (look 'aft')
    rot      rotate the parts about the motor axis first (deg), e.g. to bring a hole
             into the cutting plane
    hidden   draw hidden edges (thin dashed)
    smooth   draw tangent (G1) edges thin; False omits them
    axis     draw the view's centre line (side views)
    window   (u0, v0, u1, v1): partial view, geometry clipped to this view-coordinate
             box; mark the open sides with View.zigzag (ISO 128-30 break lines)
    """

    def __init__(self, sheet, parts, origin, scale, look="side", section=None, z_cut=None,
                 keep="below", rot=0.0, hidden=False, smooth=True, axis=True, draw=True,
                 window=None):
        if isinstance(parts, (str, Path)):
            parts = [Part(parts)]
        elif isinstance(parts, Part):
            parts = [parts]
        self.sheet, self.parts = sheet, parts
        self.origin = np.asarray(origin, float)
        self.scale, self.look, self.section, self.z_cut = scale, look, section, z_cut
        self.hidden, self.smooth = hidden, smooth
        self.geo = compute_geometry(parts, look, section, rot, z_cut, keep)
        self.clip = None
        self.window = window
        if window is not None:
            p0, p1 = self.pt(window[0], window[1]), self.pt(window[2], window[3])
            self.clip = Polygon([(p0[0], p0[1]), (p1[0], p0[1]), (p1[0], p1[1]), (p0[0], p1[1])])
        if draw:
            self.draw(axis)

    # ---- mapping -----------------------------------------------------------
    def pt(self, u, v=None):
        if v is None:
            u, v = u
        return self.origin + self.scale * np.array([u, v], float)

    def pts(self, uv):
        return np.array([self.pt(*p) for p in uv])

    def model_bounds(self):
        return self.geo["bounds"]

    def bbox(self):
        """Paper bbox of the drawn geometry (x0, y0, x1, y1)."""
        u0, v0, u1, v1 = self.geo["bounds"]
        a, b = self.pt(u0, v0), self.pt(u1, v1)
        return (a[0], a[1], b[0], b[1])

    def _paper_poly(self, pg):
        return affinity.affine_transform(pg, [self.scale, 0, 0, self.scale,
                                              self.origin[0], self.origin[1]])

    def _clip_lines(self, polys):
        if self.clip is None:
            return polys
        out = []
        for p in polys:
            if len(p) < 2:
                continue
            g = LineString(p).intersection(self.clip)
            for ln in getattr(g, "geoms", [g]):
                if isinstance(ln, LineString) and not ln.is_empty:
                    out.append(np.asarray(ln.coords))
        return out

    # ---- drawing -----------------------------------------------------------
    def draw(self, axis=True):
        g = self.geo
        vis = g["lines"]["vis"]
        if self.section == "half":        # the axis between the halves is a centre line
            vis = _drop_on_axis(vis)
        tr = lambda polys: self._clip_lines([self.pts(p) for p in polys])
        occl = unary_union([self._paper_poly(o) for o in g["occluders"]]) if g["occluders"] else None
        for i, pg in g["faces"]:
            hatch = self.parts[i].hatch
            ppg = self._paper_poly(pg)
            if occl is not None:
                ppg = ppg.difference(occl)
            if self.clip is not None:
                ppg = ppg.intersection(self.clip)
            self._hatch(ppg, hatch)
        self.sheet.lines(tr(vis), THICK, z=5)
        if self.smooth:
            self.sheet.lines(tr(g["lines"]["smooth"]), THIN, z=4)
        if self.hidden:
            self.sheet.lines(tr(g["lines"]["hid"]), THIN, "hidden", z=3)
        if axis and self.look == "side":
            u0, _, u1, _ = g["bounds"]
            if self.window is not None:
                u0, u1 = max(u0, self.window[0]), min(u1, self.window[2])
            self.centerline((u0, 0), (u1, 0))

    def _hatch(self, ppg, hatch):
        polys = [ppg] if isinstance(ppg, Polygon) else [
            q for q in getattr(ppg, "geoms", []) if isinstance(q, Polygon)]
        for pg in polys:
            if pg.is_empty or pg.area < 1e-6:
                continue
            if hatch.solid:
                self.sheet.ax.add_patch(MplPolygon(np.asarray(pg.exterior.coords), closed=True,
                                                   fc="k", ec="none", zorder=2))
                for ring in pg.interiors:
                    self.sheet.ax.add_patch(MplPolygon(np.asarray(ring.coords), closed=True,
                                                       fc="w", ec="none", zorder=2.1))
                continue
            for ang in ([hatch.angle, hatch.angle + 90.0] if hatch.cross else [hatch.angle]):
                self._hatch_lines(pg, ang, hatch.spacing, hatch.offset, hatch.lw)

    def _hatch_lines(self, pg, ang, spacing, offset, lw):
        x0, y0, x1, y1 = pg.bounds
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        R = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
        d = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
        n = _perp(d)
        # lines on a sheet-fixed lattice, so neighbouring views of one part match
        k0 = math.floor((np.dot(c, n) - R) / spacing)
        k1 = math.ceil((np.dot(c, n) + R) / spacing)
        segs = []
        for k in range(k0, k1 + 1):
            off = (k + offset) * spacing
            base = n * off + d * np.dot(c, d)
            ln = LineString([base - d * R * 1.5, base + d * R * 1.5])
            gi = ln.intersection(pg)
            for s in getattr(gi, "geoms", [gi]):
                if isinstance(s, LineString) and not s.is_empty:
                    segs.append(np.asarray(s.coords))
        self.sheet.lines(segs, lw, z=2)

    # ---- annotation primitives (all in view coordinates) --------------------
    def line(self, uv, lw=THIN, style="solid"):
        self.sheet.line(self.pts(uv), lw, style)

    def circle(self, c, r, lw=THIN, style="solid", a0=0.0, a1=360.0):
        self.sheet.circle(self.pt(*c), r * self.scale, lw, style, a0=a0, a1=a1)

    def centerline(self, a, b, ext=3.0):
        """Chain line through view points a, b, extended `ext` paper mm past each."""
        pa, pb = self.pt(*a), self.pt(*b)
        d = _unit(pb - pa)
        self.sheet.line([pa - d * ext, pb + d * ext], THIN, "center")

    def center_mark(self, c, r, ext=2.0, angle=0.0):
        """Crossed centre lines over a circle of view radius r (e.g. a hole)."""
        pc = self.pt(*c)
        R = r * self.scale + ext
        for a in (angle, angle + 90.0):
            d = _rot(np.array([1.0, 0.0]), a)
            self.sheet.line([pc - d * R, pc + d * R], THIN, "center" if R > 6 else "solid")

    def zigzag(self, a, b, n=None, amp=1.6, ext=2.0):
        """ISO 128-30 break line (thin, with zig-zags) from view point a to b,
        running `ext` paper mm past both ends."""
        pa, pb = self.pt(*a), self.pt(*b)
        d = _unit(pb - pa)
        nn = _perp(d)
        pa, pb = pa - d * ext, pb + d * ext
        L = np.hypot(*(pb - pa))
        n = n or max(1, int(L // 30))
        pts = [pa]
        for k in range(n):
            m = pa + d * L * (k + 0.5) / n
            pts += [m - d * 1.2, m + nn * amp, m - nn * amp, m + d * 1.2]
        pts.append(pb)
        self.sheet.line(pts, THIN)

    def text(self, uv, s, h=H, **kw):
        p = self.pt(*uv)
        return self.sheet.text(p[0], p[1], s, h, **kw)

    def label(self, s, where="above", gap=6.0, h=3.5, dx=0.0):
        """View identification ('A-A', 'C (5:1)'), centred above/below the view."""
        x0, y0, x1, y1 = self.bbox() if self.clip is None else self.clip.bounds
        x = (x0 + x1) / 2 + dx
        y = y1 + gap if where == "above" else y0 - gap - h
        return self.sheet.text(x, y, s, h, ha="center")

    # ---- dimensions ----------------------------------------------------------
    def _dimtext(self, pos, ang, main, tol=None, h=H, anchor="center"):
        """Dimension text with optional tolerance: tol = '±0.1' | ('+0.025', '0') | 'H7'.
        pos is the baseline anchor in paper mm; ang the reading angle."""
        s = self.sheet
        w1 = s.text_width(main, h)
        th = h * 0.72
        if isinstance(tol, (tuple, list)):
            up, lo = (str(t) for t in tol)
            wt = max(s.text_width(up, th), s.text_width(lo, th)) + 0.6
        elif tol:
            wt = s.text_width(" " + str(tol), h)
        else:
            wt = 0.0
        W = w1 + wt
        d = _rot(np.array([1.0, 0.0]), ang)
        n = _perp(d)
        start = np.asarray(pos, float) - (d * W / 2 if anchor == "center" else
                                          (d * W if anchor == "right" else 0.0))
        s.text(start[0], start[1], main, h, rot=ang)
        if isinstance(tol, (tuple, list)):
            p_up = start + d * (w1 + 0.6) + n * (h * 0.62)
            p_lo = start + d * (w1 + 0.6) - n * (h * 0.18)
            s.text(p_up[0], p_up[1], up, th, rot=ang)
            s.text(p_lo[0], p_lo[1], lo, th, rot=ang)
        elif tol:
            p = start + d * w1
            s.text(p[0], p[1], " " + str(tol), h, rot=ang)
        return W

    def _linear(self, a, b, m, line_pt, main, tol=None, where="auto", shift=0.0, h=H,
                ext=(True, True), boxed=False, arrows=(True, True)):
        """Core linear dimension in paper coordinates."""
        s = self.sheet
        a, b, line_pt = (np.asarray(x, float) for x in (a, b, line_pt))
        m = _unit(m)
        ang = math.degrees(math.atan2(m[1], m[0]))
        if ang <= -90.0 + 1e-6 or ang > 90.0 + 1e-6:
            m = -m
            ang = math.degrees(math.atan2(m[1], m[0]))
        n = _perp(m)
        la = line_pt + m * np.dot(a - line_pt, m)
        lb = line_pt + m * np.dot(b - line_pt, m)
        if np.dot(lb - la, m) < 0:
            a, b, la, lb = b, a, lb, la
            ext, arrows = ext[::-1], arrows[::-1]
        for f, l, e in ((a, la, ext[0]), (b, lb, ext[1])):
            v = l - f
            dist = np.hypot(*v)
            if e and dist > EXT_GAP + 0.3:
                u = v / dist
                s.line([f + u * EXT_GAP, l + u * EXT_OVER], THIN)
        L = np.dot(lb - la, m)
        tw = s.text_width(main, h) + (s.text_width("+0.000", h * 0.72) if isinstance(tol, (tuple, list))
                                      else (s.text_width(" " + str(tol), h) if tol else 0))
        if where == "auto":
            where = "in" if L >= 2 * ARROW_L + tw + 2.0 else "out"
        mid = (la + lb) / 2
        if where == "in":
            s.line([la, lb], THIN)
            if arrows[0]:
                s.arrow(la, -m)
            if arrows[1]:
                s.arrow(lb, m)
            tpos = mid + m * shift + n * TEXT_GAP
        else:
            tail = ARROW_L + 2.5
            if arrows[0]:
                s.arrow(la, m)
            if arrows[1]:
                s.arrow(lb, -m)
            if L >= tw + 1.5 and where != "out_side":
                s.line([la - m * tail, lb + m * tail], THIN)
                tpos = mid + m * shift + n * TEXT_GAP
            else:     # text beyond b, on the extended line
                ext_len = tail + tw + 1.0
                s.line([la - m * tail, lb + m * ext_len], THIN)
                tpos = lb + m * (tail + 0.5 + tw / 2 + shift) + n * TEXT_GAP
        W = self._dimtext(tpos, ang, main, tol, h)
        if boxed:       # theoretically exact dimension (ISO 1101)
            d, nn = m, n
            c0 = tpos - d * (W / 2 + 0.7) - nn * 0.7
            c1 = tpos + d * (W / 2 + 0.7) + nn * (h + 0.7)
            s.line([c0, c0 + d * np.dot(c1 - c0, d), c1, c0 + nn * np.dot(c1 - c0, nn), c0], THIN)
        return la, lb

    def _value(self, x, dec):
        return fmt(abs(x), dec)

    def dim_h(self, a, b, off=None, at=None, text=None, tol=None, pre="", suf="", dec=2,
              where="auto", shift=0.0, ref=False, boxed=False, ext=(True, True),
              arrows=(True, True)):
        """Horizontal dimension between view points a, b.  The dimension line sits `off`
        paper mm above (off > 0) the higher point / below (off < 0) the lower one, or at
        view v = `at`.  The value is |a.u - b.u| unless `text` is given."""
        pa, pb = self.pt(*a), self.pt(*b)
        if at is not None:
            y = self.pt(0, at)[1]
        else:
            off = DIM_STEP if off is None else off
            y = (max(pa[1], pb[1]) + off) if off >= 0 else (min(pa[1], pb[1]) + off)
        val = text if text is not None else pre + self._value(a[0] - b[0], dec) + suf
        if ref:
            val = f"({val})"
        return self._linear(pa, pb, (1, 0), (0, y), val, tol, where, shift, ext=ext, boxed=boxed,
                            arrows=arrows)

    def dim_v(self, a, b, off=None, at=None, text=None, tol=None, pre="", suf="", dec=2,
              where="auto", shift=0.0, ref=False, boxed=False, ext=(True, True),
              arrows=(True, True)):
        """Vertical dimension between view points a, b; line `off` paper mm right (> 0)
        of the rightmost point / left (< 0) of the leftmost, or at view u = `at`."""
        pa, pb = self.pt(*a), self.pt(*b)
        if at is not None:
            x = self.pt(at, 0)[0]
        else:
            off = DIM_STEP if off is None else off
            x = (max(pa[0], pb[0]) + off) if off >= 0 else (min(pa[0], pb[0]) + off)
        val = text if text is not None else pre + self._value(a[1] - b[1], dec) + suf
        if ref:
            val = f"({val})"
        return self._linear(pa, pb, (0, 1), (x, 0), val, tol, where, shift, ext=ext, boxed=boxed,
                            arrows=arrows)

    def dim_al(self, a, b, off=8.0, text=None, tol=None, pre="", suf="", dec=2, where="auto",
               shift=0.0):
        """Aligned dimension, line parallel to a-b, offset `off` paper mm to its left."""
        pa, pb = self.pt(*a), self.pt(*b)
        m = _unit(pb - pa)
        n = _perp(m)
        val = text if text is not None else pre + fmt(np.hypot(*(np.subtract(a, b))), dec) + suf
        return self._linear(pa, pb, m, pa + n * off, val, tol, where, shift)

    def dim_dia(self, u, r, off=None, at=None, text=None, tol=None, pre="", suf="", dec=2,
                where="auto", shift=0.0, ref=False, v0=None, arrows=(True, True)):
        """Diameter across the axis in a side view: a vertical dimension from (u, -r) to
        (u, r) (or from (u, v0) when v0 is given), at u = `at` or `off` paper mm from u.
        Text 'Ø<2r>'."""
        val = text if text is not None else pre + DIA + fmt(2 * r, dec) + suf
        if ref:
            val = f"({val})"
        return self.dim_v((u, -r if v0 is None else v0), (u, r), off=off, at=at, text=val, tol=tol,
                          where=where, shift=shift, arrows=arrows)

    def dim_dia_half(self, u, r, at=None, off=None, text=None, tol=None, pre="", suf="", dec=2,
                     beyond=3.0, text_at=None):
        """Half-dimension of a diameter (ISO 129: section views of symmetrical parts):
        one arrow on the feature at radius r, the line runs through the axis and
        `beyond` paper mm past it, with no second arrow."""
        s = self.sheet
        x = self.pt(at, 0)[0] if at is not None else self.pt(u, 0)[0] + (off or 0.0)
        tip = np.array([x, self.pt(0, r)[1]])
        foot = self.pt(u, r)
        if abs(foot[0] - x) > EXT_GAP + 0.3:
            sg = np.sign(x - foot[0])
            s.line([(foot[0] + sg * EXT_GAP, foot[1]), (x + sg * EXT_OVER, foot[1])], THIN)
        axis_y = self.pt(0, 0)[1]
        sgn = -np.sign(tip[1] - axis_y)
        end = np.array([x, axis_y + sgn * beyond])
        s.line([tip, end], THIN)
        s.arrow(tip, tip - end)
        val = text if text is not None else pre + DIA + fmt(2 * abs(r), dec) + suf
        ty = text_at if text_at is not None else (tip[1] + axis_y) / 2
        self._dimtext((x - TEXT_GAP, ty), 90.0, val, tol)

    def dim_rad(self, center, r, ang, length=8.0, text=None, pre="", dec=2, inside=False,
                tol=None, from_center=False):
        """Radius (ISO 129): one arrow on the arc at polar angle `ang` (deg, view frame)
        about `center`.  Default: the leader comes from the convex side (away from the
        centre) `length` paper mm, then a reference line with 'R<r>' on it.
        from_center: the line runs from the centre to the arc (arrow outward) and on
        `length` beyond it."""
        s = self.sheet
        c = self.pt(*center)
        d = _rot(np.array([1.0, 0.0]), ang)
        p = c + d * r * self.scale
        q = p + d * length
        if from_center or inside:
            s.line([c, q], THIN)
            s.arrow(p, d)
        else:
            s.line([p, q], THIN)
            s.arrow(p, -d)
        val = text if text is not None else pre + "R" + fmt(r, dec)
        sg = 1.0 if d[0] >= 0 else -1.0
        w = s.text_width(val, H) + (s.text_width("+0.00", H * 0.72) if tol else 0) + 1.6
        e = q + np.array([sg * w, 0.0])
        s.line([q, e], THIN)
        self._dimtext((q[0] + sg * 0.8, q[1] + TEXT_GAP), 0.0, val, tol,
                      anchor="left" if sg > 0 else "right")
        return e

    def dim_ang(self, vertex, a1, a2, radius, text=None, dec=1, ext=True, ext_from=0.0,
                text_r=None, text_dx=0.0, text_dy=0.0):
        """Angle between rays from view point `vertex` at a1 -> a2 (deg, CCW), drawn as
        an arc of `radius` paper mm.  ext: extension lines along both rays from
        `ext_from` paper mm out to the arc + 2."""
        s = self.sheet
        c = self.pt(*vertex)
        sweep = (a2 - a1) % 360.0
        t = np.radians(np.linspace(a1, a1 + sweep, max(12, int(sweep * 2))))
        arcp = np.c_[c[0] + radius * np.cos(t), c[1] + radius * np.sin(t)]
        s.line(arcp, THIN)
        p1, p2 = arcp[0], arcp[-1]
        t1 = _rot(np.array([1.0, 0.0]), a1 - 90.0)
        t2 = _rot(np.array([1.0, 0.0]), a1 + sweep + 90.0)
        arc_len = math.radians(sweep) * radius
        if arc_len > 2.4 * ARROW_L:
            s.arrow(p1, t1)
            s.arrow(p2, t2)
        else:
            s.arrow(p1, -t1)
            s.arrow(p2, -t2)
            for pp, tt in ((p1, t1), (p2, t2)):
                s.line([pp, pp - tt * (ARROW_L + 2.5)], THIN)
        if ext:
            for a in (a1, a1 + sweep):
                d = _rot(np.array([1.0, 0.0]), a)
                s.line([c + d * ext_from, c + d * (radius + 2.0)], THIN)
        val = text if text is not None else fmt(sweep, dec) + DEG
        am = math.radians(a1 + sweep / 2)
        tr_ = text_r if text_r is not None else radius + 1.2
        tp = c + np.array([math.cos(am), math.sin(am)]) * tr_ + (text_dx, text_dy)
        ha = "left" if math.cos(am) > 0.3 else ("right" if math.cos(am) < -0.3 else "center")
        va = "bottom" if math.sin(am) > 0.3 else ("top" if math.sin(am) < -0.3 else "center")
        t = s.text(tp[0], tp[1], val, H, ha=ha, va=va)
        return t

    def leader(self, at, dx, dy, lines, end="arrow", h=H, gap=1.6):
        """Leader from view point `at` to paper offset (dx, dy), then a horizontal
        reference line as long as the text, with the text lines (str or list, top
        first) standing on it (ISO 128-22).  end: 'arrow' (on an outline), 'dot'
        (inside a surface), 'none'.  Returns the reference line's far end."""
        s = self.sheet
        p = self.pt(*at)
        q = p + np.array([dx, dy], float)
        lines = [lines] if isinstance(lines, str) else list(lines)
        w = max(s.text_width(ln, h) for ln in lines) + 1.6
        sg = 1.0 if dx >= 0 else -1.0
        e = q + np.array([sg * w, 0.0])
        s.line([p, q, e], THIN)
        if end == "arrow":
            s.arrow(p, p - q)
        elif end == "dot":
            s.dot(p)
        x = q[0] + sg * 0.8
        n = len(lines)
        for k, ln in enumerate(lines):
            s.text(x, q[1] + TEXT_GAP + (n - 1 - k) * h * gap, ln, h, ha="left" if sg > 0 else "right")
        return e

    def finish(self, at, value, angle=0.0, leader=None):
        """Surface texture symbol on the surface at view point `at`: standing on it at
        `angle` (0 = on a horizontal upper surface), or on a leader (paper dx, dy)."""
        s = self.sheet
        p = self.pt(*at)
        if leader is None:
            s.finish_symbol(p, value, angle=angle)
            return
        q = p + np.array(leader, float)
        s.line([p, q], THIN)
        s.arrow(p, p - q)
        sg = 1.0 if leader[0] >= 0 else -1.0
        w = 7.5 / math.tan(math.radians(60)) + s.text_width(value, H) + 1.5 + 3.5 / math.tan(math.radians(60))
        s.line([q, q + (sg * (w + 2.0), 0)], THIN)
        s.finish_symbol(q + (sg * 2.0 + (0 if sg > 0 else -w), 0), value)

    def datum(self, at, letter, direction, length=6.0):
        """Datum feature indicator on view point `at`, flag along paper `direction`."""
        self.sheet.datum(self.pt(*at), letter, direction, length)

    def fcf(self, at, dx, dy, cells, end="arrow"):
        """Feature control frame at paper offset (dx, dy) from view point `at`, with a
        leader to it (end 'arrow'), or placed with no leader (end None) e.g. under a
        dimension text.  Returns the frame box."""
        p = self.pt(*at)
        return self.sheet.fcf(p[0] + dx, p[1] + dy, cells, leader=p if end else None)

    def cut_line(self, a, b, letter, look_dir, ext=4.0):
        """Cutting-plane indication (ISO 128-44): thin chain from view point a to b with
        thick ends, arrows along paper `look_dir` and the letter at each end."""
        s = self.sheet
        pa, pb = self.pt(*a), self.pt(*b)
        d = _unit(pb - pa)
        pa, pb = pa - d * ext, pb + d * ext
        s.line([pa, pb], THIN, "center")
        L = _unit(look_dir)
        for p, sgn in ((pa, 1), (pb, -1)):
            s.line([p, p + d * sgn * 5.0], 0.7)
            q = p - d * sgn * 1.0
            s.line([q, q + L * 7.0], THIN)
            s.arrow(q + L * 7.0, L)
            t = q + L * 9.0 - d * sgn * 1.5
            s.text(t[0], t[1] - 1.75, letter, 3.5, ha="center")

    def detail(self, center, radius, scale, origin, letter, label_gap=5.0, circle_label_ang=45.0,
               smooth=None, hidden=None):
        """Detail view: circle of view radius `radius` about `center` on this view,
        the same geometry re-drawn at `scale` with `center` landing on paper `origin`,
        clipped to the circle, labelled '<letter> (<scale>)'."""
        s = self.sheet
        self.circle(center, radius, THIN)
        d = _rot(np.array([1.0, 0.0]), circle_label_ang)
        tp = self.pt(*center) + d * (radius * self.scale + 3.0)
        s.text(tp[0], tp[1] - 1.75, letter, 3.5, ha="center")
        dv = View.__new__(View)
        dv.sheet, dv.parts, dv.geo = s, self.parts, self.geo
        dv.scale, dv.look, dv.section, dv.z_cut = scale, self.look, self.section, self.z_cut
        dv.hidden = self.hidden if hidden is None else hidden
        dv.smooth = self.smooth if smooth is None else smooth
        dv.origin = np.asarray(origin, float) - scale * np.asarray(center, float)
        dv.clip = Point(*np.asarray(origin, float)).buffer(radius * scale, 256)
        dv.draw(axis=False)
        s.circle(origin, radius * scale, THIN)
        ratio = scale_str(scale)
        s.text(origin[0], origin[1] - radius * scale - label_gap - 3.5, f"{letter} ({ratio})", 3.5,
               ha="center")
        # the axis, where it crosses the detail
        if self.look == "side":
            ay = dv.pt(0, 0)[1]
            if abs(ay - origin[1]) < radius * scale:
                half = math.sqrt((radius * scale) ** 2 - (ay - origin[1]) ** 2)
                s.line([(origin[0] - half, ay), (origin[0] + half, ay)], THIN, "center")
        return dv


def scale_str(scale: float) -> str:
    if scale >= 1:
        return f"{fmt(scale, 2)}:1"
    return f"1:{fmt(1.0 / scale, 2)}"


def merge_pdfs(pdfs, out):
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs:
        w.append(str(p))
    with open(out, "wb") as f:
        w.write(f)
    return Path(out)
