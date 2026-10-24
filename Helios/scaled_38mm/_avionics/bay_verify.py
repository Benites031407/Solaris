"""Verification of the EXPORTED bay -- both printed parts -- against the airframe.

Everything in `bay_support.py`, `bay_plate.py` and `bay_params.py` is checked
against the numbers that built it, and `bay_assembly.py` checks the pair as
SOLIDS.  That catches arithmetic, and `bay_build.one_solid()` catches a boolean
that shattered, but none of them can catch an export that lost a feature, a
parameter table that has drifted away from the mesh it was measured off, or a
part that simply will not go down the tube.  So this module loads
`out/bay_support.stl`, `out/bay_plate.stl` and `../scaled_38mm/Mbody.stl` back in
and asks questions whose answers were decided elsewhere:

    1. is each part a closed, positive-volume, single body whose mesh volume
       agrees with its own CAD solid
    2. does `bay_params.free_radius()` -- the table the whole design rests on --
       still agree with Mbody's own mesh, row by row through the bead and sector
       by sector through the cord duct
    3. for every feature: probe where it IS and where it should MISS.  A slot
       that was never cut passes half of that pair.
    4. THE SLIDE, on the two meshes: the pocket measured as a void BETWEEN two
       rails, the plate's chord measured inside it, and the three clearances
       (SLIDE_CLR_X twice, SLIDE_CLR_R once) read off the meshes rather than
       taken from the parameters that drew them
    5. does the support actually GO IN: a full insertion sweep, its measured
       radial envelope against the tube's measured free radius, at every
       insertion depth rather than only at the final position -- and does the
       PLATE clear the tube over its own travel, which is what proves the lugs
       miss the cord duct
    6. does the support SEAT where it was designed to, and can it fall through
    7. does it JAM when installed 180 degrees out -- which has to be a FAILING
       sweep, because the two screws are symmetric under 180 degrees and cannot
       catch that error.  The duct clash is the only thing that can.
    8. do the payload cells actually exist as voids in the plate, and does the
       plate still pass the bead with all of them full
    9. does the print-orientation claim survive contact with the mesh -- for the
       support in the CAD pose, and for the plate ROTATED INTO ITS FLAT POSE,
       which is a different question about the same solid
   10. do the two M3s reach: airframe wall, air gap, boss, and now the plate's
       LUG as well -- measured on the SEATED plate, which is the only state in
       which the two pilots are collinear

(5) and (7) are a pair and neither is optional.  Checking only the final
assembled position is the mistake that lets a part which cannot be inserted pass
verification: the support's tail sweeps the entire length of the duct on its way
home, so the interesting collisions all happen at insertion depths that the
assembled position never visits.

THE TWO PARTS, AND WHICH MESH ANSWERS WHICH QUESTION
----------------------------------------------------
The bay used to be one printed part.  It is now a SUPPORT that stays in the
airframe and a PLATE that slides into it from the forward end, tail first, fully
populated -- so there are two insertions, nested, and they fail in different ways:

    the support into the TUBE      the old question, unchanged.  Crown into the
                                   bead, trough opening against the cord duct,
                                   and it must not pass the throat.
    the plate into the SUPPORT     answered exactly, on solids, by
                                   bay_assembly.py -- the support intersected
                                   with the plate's swept envelope.  A binned
                                   mesh sweep CANNOT do that job: the clearances
                                   are 0.30 and 0.40 mm and the sweep's own
                                   station grid is 0.5 mm.  What the mesh adds
                                   is (4): direct spans, walked at 0.05 mm,
                                   where the section is constant along z.
    the plate through the TUBE      not redundant with either.  The support is a
                                   C, open at x > 4.0, so the tube's cord duct
                                   intrudes THROUGH that opening into the space
                                   the plate travels down.  The plate's lugs
                                   stand to x +3.0.  That is a 1.0 mm margin
                                   between two features on different parts, and
                                   (5) measures it on the meshes.

A NOTE ON WHAT A MESH SWEEP CAN AND CANNOT RESOLVE
--------------------------------------------------
NBIN 144 is 2.5 deg of azimuth and ZSTEP is 0.5 mm of station.  That is ample for
a 1.96 mm support-to-bore gap and useless for a 0.30 mm rail-to-plate gap.  Rather
than pretend otherwise, the slide's clearances are measured by MARCHED SPANS at
0.05 mm along a single ray -- radially for SLIDE_CLR_R, along x for SLIDE_CLR_X --
at stations where every feature involved is constant in z, which is what makes a
single ray a valid measurement of the whole length.  The faceting error on those
spans is the sagitta at r 27, which is 0.006 mm, fifty times smaller than the
clearance being read.

(7) has to FAIL to pass.  An earlier version of this reasoning assumed the
screws keyed the rotation.  They do not: SCREW_THETA is (90, 270), which maps to
itself under a half turn, so a support installed backwards still lines its bosses
up with the airframe's holes.  Everything about that error is invisible except
the duct.

HOW THE TWO ENVELOPES ARE MEASURED, AND WHICH WAY EACH ONE ERRS
---------------------------------------------------------------
Both come from z sections, binned by azimuth, densified along every segment so
that a bin between two vertices cannot read as empty:

    the tube's FREE radius   MIN radius per bin, over all loops in the section.
                             A faceted circle's chords lie inside the true
                             circle, so this UNDER-reads -- the tube is reported
                             tighter than it is.
    the part's ENVELOPE      MAX radius per bin.  A faceted circle's vertices
                             sit ON the true circle, so this reads true.

Both errors point the same way, which is the point: the sweep can only be
pessimistic.  A clearance it reports is real; a foul it reports might be
faceting, which is why FACET_ALLOW is computed from each mesh's own angular
resolution and printed rather than assumed.

Taking MIN per bin, rather than the min over the whole section, is what makes
the duct measurable at all.  The duct is a 24 degree intrusion: a section-wide
minimum reports it as if the whole ring had closed to r 21.1, and a section-wide
minimum outside the duct reports the bore.  Neither answers the question the
support asks, which is per-azimuth.

STATIONS ARE INTERPOLATED, NEVER SNAPPED
----------------------------------------
The maps are built on a ZSTEP grid and the tables they are checked against are
not.  BEAD_FLANK is tabulated at 0.25 mm, so snapping its rows to the nearest
0.5 mm map row compares every alternate row against the mesh a quarter of a
millimetre away from itself -- and on a flank falling 0.40 mm of radius per mm of
station, that is 0.115 mm of radius.  This file duly reported the datum table as
wrong by 0.1176 mm at s 27.75, and it was the measurement that was wrong.  So
bore_at() interpolates.  Where a threshold still has to absorb the grid -- the
seat, whose sweep IS on the grid -- it is built from ZSTEP times the local slope
and the arithmetic is printed in the passing message, because a threshold whose
derivation nobody can see is the next version of the same bug.

Two corollaries that cost real time here.  A tolerance that fails should be
diagnosed before it is widened: three of this file's first seven failures were
mis-aimed probes, one was a grid artefact, and only one was a defect.  And a
tolerance term should be measured before it is added: a draft of the flank check
padded its allowance with the socket's non-cylindricity, which then measured
0.0007 mm and was not where the worst row was.

WHAT THIS FILE ACTUALLY CAUGHT
------------------------------
One defect, and it was not in any number.  The screw pilot was bored from exactly
R_BOSS_I -- the boss's own inner cylinder -- so the cut laid a circular seam on
the very face it started from.  The result was one valid solid, of the right
volume, that passed every check in the one-piece bay_sled.py of the time -- kept
now as _scratch/_bay_sled_one_piece.py -- and an STL with 8 non-manifold
faces at r 23.0.  That is why check (1) exists and why its failure message says
out loud that a mesh which is not watertight invalidates every containment probe
below it: without that sentence the run looks like six unrelated small problems.
The cure was FUSE_MERGE at the cutter's start, i.e. the overlap-volumetrically
rule that one_solid() enforces for fuses, applied to a cut.

Run:  python bay_verify.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import trimesh

import bay_params as P

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
# HERE is _avionics/, so HERE.parent IS scaled_38mm/ -- naming it again gave
# scaled_38mm/scaled_38mm/Mbody.stl, which does not exist, so main() took its
# `missing ...` early return and this file has never actually run.  There are two
# Mbody.stl in the tree with the SAME byte count (221884) and different md5s, so
# the fix was measured rather than guessed: this one is 262.069 long, r_od 32.759,
# bead throat 29.882 -- bay_params' committed table to within 0.031 mm.  The other
# (../../Mbody.stl) is the pre-scaling original: 200.0 long, r_od 25.0, a
# different rocket.  Do not "simplify" this to a search that picks either.
MBODY = HERE.parent / "Mbody.stl"

# CAD volumes in cm3, straight off `python bay_support.py` and `python
# bay_plate.py`.  Literals on purpose: importing the modules to ask them would
# make the comparison tautological, and the point is to catch a tessellation or
# export fault by checking each mesh against a number that came from its own
# SOLID.  Re-read them by hand when a part changes.
CAD_VOL_SUPPORT_CM3 = 39.6426
CAD_VOL_PLATE_CM3 = 18.1363

NBIN = 144                # azimuth bins: 2.5 deg, five bins across the duct
ZSTEP = 0.5               # station step for both envelopes
DENSIFY = 0.15            # max gap between samples along a section segment
DSTEP = 0.5               # insertion-depth step for the sweep
D_MAX = 215.0             # far enough out that the part is clear of the tube
CHUNK = 900               # points per containment call -- see inside()
OVERHANG_DEG = 44.0       # a face inclined at least this much from horizontal
                          # prints unsupported.  44 and not 45 because the ramps
                          # in this part are drawn AT 45.0 and 45.3 degrees, and
                          # a threshold set exactly on the design value is
                          # decided by float noise rather than by geometry.
                          #
                          # MEASURED, and the margin is thinner than "float
                          # noise" suggests: the boss ramp is drawn at 45.29 deg
                          # and its EXPORTED facets read 44.40 -- 0.4 deg inside
                          # this threshold, not 1.3.  The bias is tessellation,
                          # not noise, and it has a direction: the boss sector is
                          # 18 deg wide and comes out in only a facet or two
                          # across, and a facet's horizontal chord runs further
                          # out in radius than the cone it samples, so the facet
                          # is always SHALLOWER than the surface.  Which means a
                          # coarser export could push the ramp through 44.0 and
                          # this file would report a support that needs support.
                          # _scratch/_shallow.py is what measures it; if that
                          # ever fails, re-tessellate before widening this.
BRIDGE_MAX = 6.0          # a downward-facing region whose NARROW dimension is
                          # this short is a bridge, not an overhang

# THE PLATE'S PRINT POSE, as a transform rather than as a claim.
# bay_plate.py prints FLAT: the deck's underside on the bed, so the part's own x
# becomes build Z.  verify_printability() reads "down" as -Z of the mesh it is
# handed, so the plate has to be laid over before it is asked -- (x,y,z) -> (y,z,x),
# which is the cyclic permutation, determinant +1.  A permutation with determinant
# -1 is a MIRROR: it would still put the right face on the bed, and every overhang
# angle would still measure the same, and the part it described would be the
# unprintable enantiomer of the one in the STL.  So the sign is checked below, not
# eyeballed.
FLAT = np.array([[0.0, 1.0, 0.0, 0.0],
                 [0.0, 0.0, 1.0, 0.0],
                 [1.0, 0.0, 0.0, 0.0],
                 [0.0, 0.0, 0.0, 1.0]])

# The SIZE of the net, asserted and not merely reported.  main() ended with
# `all {len(...)} checks passed` computed at runtime, so a check that quietly
# stopped running -- a helper returning early, a guard that lost its call site,
# a loop whose range collapsed -- printed a smaller number inside the same
# cheerful sentence and failed nothing.  Pinning it makes shrinkage loud.
# Changing this number is meant to be a deliberate act with a reason.
#
# 150 as of the split, re-derived by running the file rather than by adding up the
# diff.  It was 105 for the one-piece sled.  The 45 new ones are, roughly: a
# second part through verify_basics (8), the slide's own section (6), the plate
# down the tube (3), the plate's flat pose through verify_printability (3) plus
# the determinant of the transform that gets it there (1), the four probe groups
# in verify_features that the rails, the stop, the pocket's mirror and the lugs
# needed (16), the second loaded-insertion limit (1), and the fasteners' reach
# into the lug measured on the seated mesh (6).
EXPECT_CHECKS = 150

FAILS: list[str] = []
NOTES: list[str] = []


# --------------------------------------------------------------------- helpers

def check(cond: bool, ok_msg: str, bad_msg: str) -> bool:
    """Record a pass or a failure without aborting -- one run, all the news.

    Both messages are built by the caller before this is entered, so a broken
    f-string in the failure branch cannot hide behind a passing test.
    """
    if cond:
        NOTES.append(f"  ok   {ok_msg}")
    else:
        FAILS.append(bad_msg)
        NOTES.append(f"  FAIL {bad_msg}")
    return bool(cond)


def note(msg: str) -> None:
    NOTES.append(f"  --   {msg}")


def load(path: Path) -> trimesh.Trimesh:
    m = trimesh.load(str(path), force="mesh")
    if not isinstance(m, trimesh.Trimesh):
        raise TypeError(f"{path} did not load as a single mesh: {type(m)}")
    return m


def cyl(r: float, theta_deg: float, z: float) -> tuple[float, float, float]:
    t = math.radians(theta_deg)
    return (r * math.cos(t), r * math.sin(t), z)


def inside(mesh: trimesh.Trimesh, pts) -> np.ndarray:
    """Point-in-mesh, in chunks.

    There is no embree here, so trimesh builds a ray x triangle candidate array
    in pure numpy; a few thousand points against a mesh this size asks for
    hundreds of MiB in one block and raises.  Chunking is free and keeps the
    peak flat regardless of mesh size or sample count.
    """
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    if len(pts) <= CHUNK:
        return mesh.contains(pts)
    return np.concatenate([mesh.contains(pts[i:i + CHUNK])
                           for i in range(0, len(pts), CHUNK)])


def expect_points(mesh, label: str, cases) -> None:
    """cases: [(point, want_solid, why), ...].  One containment call for all."""
    pts = [c[0] for c in cases]
    got = inside(mesh, pts)
    for (p, want, why), g in zip(cases, got):
        state = "SOLID" if g else "void"
        wanted = "SOLID" if want else "void"
        check(bool(g) == want,
              f"{label}: {why} -- {state} at ({p[0]:7.2f},{p[1]:7.2f},{p[2]:7.2f})",
              f"{label}: {why} -- wanted {wanted}, got {state} at "
              f"({p[0]:.2f},{p[1]:.2f},{p[2]:.2f})")


def facet_count(mesh: trimesh.Trimesh, z: float) -> int:
    """Distinct azimuths in one z section -- the surface's angular resolution."""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return 64
    v = np.asarray(sec.vertices)
    th = np.unique(np.round(np.degrees(np.arctan2(v[:, 1], v[:, 0])), 2))
    return max(24, int(len(th)))


def arc_facets(mesh: trimesh.Trimesh, z: float, r_lo: float,
               r_hi: float) -> int:
    """Equivalent FULL-circle facet count, measured on a PARTIAL arc.

    facet_count() counts distinct azimuths across a whole section, which is the
    right measure for the support: its section is a ring, so every facet of it is
    in there.  It is the wrong measure for the plate.  The plate's section is a
    chord, and its curved edge spans 4.39 degrees of the circle -- so however
    finely that arc is tessellated, the count comes back at facet_count's floor
    of 24, and sagitta() then reports a quarter of a millimetre of faceting on a
    plate whose real error is a hundredth.  A tolerance built out of that number
    would be wider than the 0.40 mm clearance it exists to bound, which is the
    same class of mistake as a check that passes when it cannot evaluate itself.

    So the PITCH is measured where the arc actually is -- the azimuths of the
    section's vertices lying between r_lo and r_hi, over the angle they span --
    and then reported as the full-circle count that pitch corresponds to, which
    is what sagitta() wants.  Only the +y half is taken: the section has a
    matching arc at -y, and the two together would read as one 154 degree span
    with a handful of vertices in it.
    """
    sec = mesh.section(plane_origin=[0, 0, float(z)], plane_normal=[0, 0, 1])
    if sec is None:
        return 24
    v = np.asarray(sec.vertices)
    r = np.hypot(v[:, 0], v[:, 1])
    sel = (r >= r_lo) & (r <= r_hi) & (v[:, 1] > 0.0)
    th = np.unique(np.round(np.degrees(np.arctan2(v[sel, 1], v[sel, 0])), 4))
    if len(th) < 2:
        return 24
    pitch = float(th.max() - th.min()) / (len(th) - 1)
    if pitch <= 0.0:
        return 24
    return max(24, int(round(360.0 / pitch)))


def sagitta(r: float, n_facets: int) -> float:
    """How far inside the true circle at r a faceted chord can lie."""
    return r * (1.0 - math.cos(math.pi / n_facets))


# ------------------------------------------------------- section-based mapping

def _dense_section_xy(mesh: trimesh.Trimesh, z: float):
    """All points of a z section, densified so no azimuth bin can read empty.

    Raw section vertices are sparse -- a 2.5 degree bin at r 29 is a 1.27 mm
    arc, and a facet edge can easily span several bins with no vertex inside
    them.  For a MIN map that reads as "no material here", which is exactly the
    false negative that would let the sweep pass a part that fouls.
    """
    sec = mesh.section(plane_origin=[0, 0, float(z)], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    v = np.asarray(sec.vertices)
    a_list, b_list = [], []
    for ent in sec.entities:
        idx = np.asarray(ent.points)
        if len(idx) < 2:
            continue
        a_list.append(v[idx[:-1], :2])
        b_list.append(v[idx[1:], :2])
    if not a_list:
        return v[:, :2]
    a = np.vstack(a_list)
    b = np.vstack(b_list)
    seg = np.linalg.norm(b - a, axis=1)
    n = int(min(32, max(1, math.ceil(float(seg.max()) / DENSIFY))))
    t = np.linspace(0.0, 1.0, n + 1).reshape(-1, 1, 1)
    pts = a[None, :, :] + (b - a)[None, :, :] * t
    return pts.reshape(-1, 2)


def radius_map(mesh: trimesh.Trimesh, z0: float, z1: float, mode: str):
    """(stations, nbin) map of min or max radius per azimuth bin.

    mode "min" -> the innermost material boundary, i.e. the FREE radius
    mode "max" -> the outermost material, i.e. the ENVELOPE
    Empty bins come back as +inf (min) or 0.0 (max), both meaning "no
    constraint from this bin", which is what an empty bin actually means.
    """
    zs = np.arange(z0, z1 + 1e-9, ZSTEP)
    fill = np.inf if mode == "min" else 0.0
    out = np.full((len(zs), NBIN), fill)
    width = 360.0 / NBIN
    for i, z in enumerate(zs):
        pts = _dense_section_xy(mesh, float(z))
        if pts is None or len(pts) == 0:
            continue
        r = np.hypot(pts[:, 0], pts[:, 1])
        th = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) % 360.0
        b = np.clip((th / width).astype(int), 0, NBIN - 1)
        if mode == "min":
            np.minimum.at(out[i], b, r)
        else:
            np.maximum.at(out[i], b, r)
    return zs, out


def bin_centres() -> np.ndarray:
    width = 360.0 / NBIN
    return (np.arange(NBIN) + 0.5) * width


def in_duct_bins() -> np.ndarray:
    th = bin_centres()
    d = np.abs((th - P.DUCT_THETA + 180.0) % 360.0 - 180.0)
    return d <= P.DUCT_HALF_ANG


# ------------------------------------------------------------------- 1. basics

def verify_basics(m: trimesh.Trimesh, label: str, cad_cm3: float,
                  s_fwd: float, s_aft: float, s_fwd_why: str,
                  s_aft_why: str) -> None:
    """The checks every exported part owes, run once per part.

    Parameterised rather than duplicated, and the two callers pass DIFFERENT
    station bounds and different reasons for them -- the support's forward face is
    where the nose spigot's clearance was computed from, the plate's is flush with
    it and its aft face is SLIDE_GAP_Z short of the stop on purpose.  A copy of
    this function per part would let those two stories drift.
    """
    check(m.is_watertight,
          f"{label}: watertight, {len(m.faces)} facets",
          f"{label}: NOT watertight -- "
          f"{len(trimesh.repair.broken_faces(m))} broken faces, so no "
          f"containment probe below can be trusted")
    check(m.volume > 0.0,
          f"{label}: positive volume {m.volume/1000:.3f} cm3",
          f"{label}: volume is {m.volume:.3f} mm3 -- inverted normals")
    n_body = len(m.split(only_watertight=False))
    check(n_body == 1,
          f"{label}: one connected body",
          f"{label}: splits into {n_body} bodies -- a stray shell from a failed "
          f"boolean reads as extra volume and prints as debris")

    v_mesh = m.volume / 1000.0
    check(abs(v_mesh - cad_cm3) < 0.02 * cad_cm3,
          f"{label}: mesh volume {v_mesh:.4f} cm3 agrees with the CAD solid's "
          f"{cad_cm3:.4f} ({100*(v_mesh-cad_cm3)/cad_cm3:+.2f}%, "
          f"tessellation)",
          f"{label}: mesh volume {v_mesh:.4f} cm3 disagrees with the CAD "
          f"solid's {cad_cm3:.4f} by more than tessellation explains -- the "
          f"export lost or gained a feature")
    note(f"{label}: mass {v_mesh * 1.04:.1f} g in ABS at "
         f"{P.ABS_RHO*1000:.2f} g/cm3")

    # The bed check is orientation-free -- all three extents against BED -- which
    # is why it can be shared by a part printed in the CAD pose and one that has
    # to be laid over first.  Whether each part's chosen pose actually PRINTS is
    # verify_printability()'s question, and it is asked in the pose.
    e = m.extents
    check(all(x <= P.BED for x in e),
          f"{label}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm fits the "
          f"{P.BED:.0f} mm bed",
          f"{label}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm does not fit a "
          f"{P.BED:.0f} mm bed")

    lo, hi = m.bounds
    check(abs(lo[2] - s_fwd) < 0.01,
          f"{label}: forward face at s {lo[2]:.3f} = {s_fwd:.3f}, {s_fwd_why}",
          f"{label}: forward face at s {lo[2]:.3f}, not the {s_fwd:.3f} "
          f"expected -- {s_fwd_why}")
    check(abs(hi[2] - s_aft) < 0.01,
          f"{label}: aft face at s {hi[2]:.3f} = {s_aft:.3f}, {s_aft_why}",
          f"{label}: aft face at s {hi[2]:.3f}, not the {s_aft:.3f} "
          f"expected -- {s_aft_why}")


# ------------------------------------------- 2. free_radius() against the mesh

def bore_at(free, tzs, s: float, bins, stat: str = "min") -> float:
    """The tube's free radius at station s over `bins`, INTERPOLATED in station.

    THE INTERPOLATION IS THE POINT, and it is not a refinement.  This used to
    snap to the nearest row of a ZSTEP = 0.5 mm map, and BEAD_FLANK is tabulated
    at 0.25 mm -- so every other row of the datum table was compared against the
    mesh a quarter of a millimetre away from itself.  On a flank falling
    0.46 mm of radius per mm of station that snap IS 0.115 mm of radius, and it
    duly reported the table as wrong by 0.1176 mm at s 27.75.  Measured at the
    stations the table actually names, the table agrees to 0.037 mm everywhere.
    A grid-snap error looks exactly like a data error and is not one; the fix is
    to stop snapping, not to widen the tolerance until the snap fits inside it.

    `stat` picks the azimuthal reduction, which is a separate question:

      MIN     the conservative envelope, and what every clearance question wants:
              a faceted chord lies inside the true circle, so a min-over-azimuth
              UNDER-reads the bore and the tube can only look tighter than it is.
      MEDIAN  what _bead_probe.py used to tabulate BEAD_FLANK, one nanmedian per
              station.  Compared like-for-like here so the table is checked with
              the statistic it was built with.

    On this mesh the two differ by only 0.007 mm across the flank -- measured,
    not assumed -- so the choice happens not to matter here.  It is still made
    explicitly, because on a coarser mesh it would.
    """
    x = (s - tzs[0]) / ZSTEP
    i0 = max(0, min(len(tzs) - 2, int(np.floor(x))))
    f = min(1.0, max(0.0, x - i0))

    def reduce_row(i: int) -> float:
        row = free[i][bins]
        return float(np.min(row)) if stat == "min" else float(np.median(row))

    return (1.0 - f) * reduce_row(i0) + f * reduce_row(i0 + 1)


def flank_scatter(free, tzs, bins, near=None, span: float = 1.0):
    """How far MIN runs below MEDIAN over the bead's forward flank, and where.

    The flank's own azimuthal scatter.  It bears on the seat because a crown
    lands on the TIGHTEST azimuth rather than the typical one, so a mesh seat sits
    slightly forward of what a median-derived table predicts -- but on this mesh
    it turns out to be the SMALLEST of the seat's three error terms, not the
    largest, which is only knowable by measuring it.  Its real value here is as
    evidence that the flank is a ring: 0.007 mm of scatter is what makes the seat
    a radial datum instead of a three-point stop.  `near` restricts the window to
    the stations that actually decide the seat.
    """
    worst, worst_s = 0.0, None
    for s, _ in P.BEAD_FLANK:
        if near is not None and abs(s - near) > span:
            continue
        d = (bore_at(free, tzs, s, bins, "median")
             - bore_at(free, tzs, s, bins, "min"))
        if d > worst:
            worst, worst_s = d, float(s)
    return worst, worst_s


def flank_slope(s: float, span: float = 1.0) -> float:
    """|dr/ds| of the bead's forward flank near station s, straight off BEAD_FLANK.

    Needed because the seat's uncertainty is dominated by the STATION grid rather
    than by faceting: on a flank this steep, ZSTEP of station is worth
    ZSTEP*slope of radius, which is thirty times the faceting allowance.
    """
    rows = [(z, r) for z, r in P.BEAD_FLANK if abs(z - s) <= span]
    if len(rows) < 2:
        return 0.0
    z = np.array([a for a, _ in rows], float)
    r = np.array([b for _, b in rows], float)
    return abs(float(np.polyfit(z, r, 1)[0]))


def verify_free_radius(free, tzs, n_tube: int) -> None:
    """The parameter table the whole design rests on, row by row."""
    sag = sagitta(P.R_WORK, n_tube)
    tol = 3.0 * sag + 0.02
    note(f"Mbody's sections resolve {n_tube} azimuths, so a chord can lie "
         f"{sag:.4f} mm inside the true circle; free_radius() is checked to "
         f"{tol:.4f} mm")

    def measured(s: float, bins, stat: str = "min") -> float:
        return bore_at(free, tzs, s, bins, stat)

    clear = ~in_duct_bins()
    duct = in_duct_bins()

    # --- the plain cylinders.  Away from the duct, min-over-clear-bins is the
    # bore, and it should match the table to within faceting.
    for s, want, what in ((10.0, P.R_SOCKET, "the nose socket"),
                          (20.0, P.R_SOCKET, "the nose socket"),
                          (P.S_BEAD_THROAT, P.R_BEAD_THROAT, "the bead throat"),
                          (100.0, P.R_WORK, "the working bore"),
                          (150.0, P.R_WORK, "the working bore"),
                          (205.0, P.R_WORK, "the working bore"),
                          (240.0, P.R_AFT_BORE, "the aft bore"),
                          (255.0, P.R_AFT_BORE, "the aft bore")):
        got = measured(s, clear)
        check(abs(got - want) <= tol,
              f"free_radius({s:.1f}) = {want:.3f} and {what} measures "
              f"{got:.3f} ({got-want:+.4f})",
              f"free_radius({s:.1f}) claims {want:.3f} for {what} but the mesh "
              f"measures {got:.3f} ({got-want:+.4f}, beyond {tol:.4f})")

    # --- the bead's forward flank, all 22 rows.  This is the datum, so it is
    # the table that most deserves to be re-derived from the mesh rather than
    # trusted.  Checked at the same azimuths the crown seats on, i.e. all of
    # them: the flank's whole value is that it is a full ring.
    # Compared MEDIAN against median, the statistic these rows were built with,
    # and at the stations the rows actually name -- see bore_at() for why the
    # second half of that sentence was worth 0.12 mm.
    #
    # Measured against plain `tol`, with no extra allowance.  Once the snap is
    # gone the rows need none: the worst of the 22 is well inside faceting.  An
    # earlier draft of this check added a term for the socket's non-cylindricity,
    # on the theory that the first row inherits R_SOCKET and would be out by it.
    # The term measured 0.0007 mm and the worst row was not the first one, so the
    # theory was wrong and the term is gone rather than left in to pad a
    # threshold with something that turned out to be nothing.
    worst, worst_s = 0.0, None
    for s, want in P.BEAD_FLANK:
        got = measured(s, clear, "median")
        if abs(got - want) > worst:
            worst, worst_s = abs(got - want), s
    check(worst <= tol,
          f"the bead's forward flank: all {len(P.BEAD_FLANK)} rows of "
          f"BEAD_FLANK agree with the mesh, worst {worst:.4f} mm at "
          f"s {worst_s:.2f}, inside the {tol:.4f} faceting allowance",
          f"BEAD_FLANK disagrees with the mesh by {worst:.4f} mm at "
          f"s {worst_s:.2f}, beyond {tol:.4f} -- the crown's seat station "
          f"is computed from this table")

    # Whether the socket is straight, kept as a measurement.  Worth having
    # because a raw min-over-section-vertices at s 27.50 reads 31.284, which
    # suggested a bore belling out 0.04 mm towards the fillet; measured on the
    # densified per-bin map, which resamples segments instead of relying on where
    # vertices happen to fall, it is straight to well under a facet.  The sparse
    # reading was the artefact, not the bell -- the same lesson DENSIFY exists
    # for.  A future part that is a press fit in the socket can use R_SOCKET.
    sock = [measured(float(s), clear) for s in
            np.arange(8.0, P.S_SOCKET_END + 1e-9, 0.5)]
    check(max(sock) - min(sock) < 0.05,
          f"the nose socket is straight to {max(sock)-min(sock):.4f} mm over "
          f"s 8..{P.S_SOCKET_END:.1f} (r {min(sock):.3f}..{max(sock):.3f}), so "
          f"R_SOCKET {P.R_SOCKET:.3f} describes the whole of it and not just a "
          f"station",
          f"the nose socket varies {max(sock)-min(sock):.4f} mm along its "
          f"length, so R_SOCKET {P.R_SOCKET:.3f} is not one number")

    # The table's actual JOB is to answer one question: at what station does a
    # circle of diameter 2*R_CROWN touch this flank.  So ask it in those units as
    # well.  A tolerance in millimetres of radius says nothing about how far a
    # table error would move the seat; a tolerance in millimetres of station says
    # exactly that, and this is the number the whole datum rests on.
    s_tab = P.bead_seat_station(2.0 * P.R_CROWN)
    xs = np.arange(P.S_SOCKET_END, P.S_BEAD_END + 1e-9, 0.05)
    rr = np.array([measured(float(s), clear) for s in xs])
    hit = np.where(rr <= P.R_CROWN)[0]
    s_mesh = float(xs[hit[0]]) if len(hit) else float("nan")
    check(abs(s_mesh - s_tab) <= 0.35,
          f"inverted the way it is used: BEAD_FLANK puts the crown's seat at "
          f"s {s_tab:.3f} and the mesh's own bore first reaches r "
          f"{P.R_CROWN:.2f} at s {s_mesh:.3f} ({s_mesh-s_tab:+.3f} mm) -- the "
          f"table is right about the only thing it is asked",
          f"BEAD_FLANK puts the seat at s {s_tab:.3f} but the mesh reaches r "
          f"{P.R_CROWN:.2f} at s {s_mesh:.3f} ({s_mesh-s_tab:+.3f} mm) -- "
          f"S_CROWN, S_HEAD_FWD and S_HEAD_AFT all follow from this")

    scat, scat_s = flank_scatter(free, tzs, clear)
    slope = flank_slope(P.S_CROWN)
    check(scat < 0.20,
          f"the flank's azimuthal scatter (median - min over clear bins) peaks "
          f"at only {scat:.4f} mm, at s {scat_s:.2f} -- so the crown meets it as "
          f"a ring and not at three points, which is the entire reason the seat "
          f"is a radial datum rather than just a stop",
          f"the flank scatters {scat:.4f} mm around the azimuth at s "
          f"{scat_s:.2f} -- too much for a crown to seat on it as a ring")
    note(f"the flank drops {slope:.3f} mm of radius per mm of station near "
         f"S_CROWN.  That slope, times the sweep's ZSTEP of {ZSTEP:.1f} mm, is "
         f"the DOMINANT uncertainty in the seat check below -- {ZSTEP*slope:.3f} "
         f"mm, against {3.0*sag:.4f} mm of faceting and {scat:.4f} of azimuthal "
         f"scatter.  A seat threshold set at faceting alone fails a part that "
         f"is seated correctly.")

    # --- the AFT flank, which the table models as a straight line between the
    # throat and the bore with the comment "linear is close enough".  Close
    # enough for what, exactly, is worth measuring rather than asserting: a
    # model that OVER-states the free radius here is optimistic in the one
    # region the support's body sweeps past on its way in.  The insertion sweep
    # below runs on the mesh and is unaffected either way; this is about whether
    # free_radius() can be quoted on its own.
    aft_worst, aft_s, aft_sign = 0.0, None, 0.0
    for s in np.arange(P.S_BEAD_THROAT, P.S_BEAD_END + 1e-9, 0.25):
        want = P.free_radius(float(s))
        got = measured(float(s), clear)
        if abs(got - want) > aft_worst:
            aft_worst, aft_s, aft_sign = abs(got - want), float(s), got - want
    optimistic = aft_sign < 0.0
    check(aft_worst <= 0.45,
          f"the bead's aft flank: the linear model tracks the mesh to "
          f"{aft_worst:.3f} mm (worst at s {aft_s:.2f}, model "
          f"{'over' if optimistic else 'under'}-states the free radius), which "
          f"is coarse but is never the binding number -- the support is r "
          f"{P.R_SHELL_O:.2f} here against a measured "
          f"{measured(aft_s, clear):.3f}",
          f"the bead's aft flank: the linear model is out by {aft_worst:.3f} mm "
          f"at s {aft_s:.2f} -- too far to quote free_radius() through the aft "
          f"flank at all")
    if optimistic:
        note(f"free_radius() is OPTIMISTIC by up to {aft_worst:.3f} mm over the "
             f"bead's aft flank, s {P.S_BEAD_THROAT:.2f}..{P.S_BEAD_END:.1f}, "
             f"because the real flank is a fillet and the table draws a chord "
             f"across it.  Nothing in this design is sized off that region "
             f"(the seat is on the FORWARD flank and the body clears by "
             f"{measured(aft_s, clear) - P.R_SHELL_O:.2f} mm), but a future "
             f"feature that lands between s {P.S_BEAD_THROAT:.1f} and "
             f"{P.S_BEAD_END:.1f} must be checked against the mesh and not "
             f"against the table.")

    # --- the flank really is a full RING, which is what makes it self-centring.
    i_thr = int(round((P.S_BEAD_THROAT - tzs[0]) / ZSTEP))
    spread = float(np.max(free[i_thr][clear]) - np.min(free[i_thr][clear]))
    check(spread < 0.10,
          f"the bead throat varies only {spread:.4f} mm around the azimuth, so "
          f"it is a true ring: no keyway defeats it, and a crown seating on it "
          f"is centred in both axes",
          f"the bead throat varies {spread:.4f} mm around the azimuth -- it is "
          f"not the full ring the datum argument depends on")

    # --- the duct.  Per-azimuth is the only way to see this: the intrusion is
    # 24 degrees wide, so any section-wide statistic either misses it entirely
    # or reports it as a closed ring.
    r_duct = min(measured(s, duct) for s in
                 np.arange(P.S_DUCT_START, P.S_DUCT_END + 1e-9, 0.5))
    check(abs(r_duct - P.R_DUCT_INNER) <= 0.20,
          f"R_DUCT_INNER = {P.R_DUCT_INNER:.2f} and the duct's deepest "
          f"intrusion measures r {r_duct:.3f} over s "
          f"{P.S_DUCT_START:.0f}..{P.S_DUCT_END:.0f}",
          f"R_DUCT_INNER claims {P.R_DUCT_INNER:.2f} but the duct reaches "
          f"r {r_duct:.3f} -- the support's keep-out is drawn from this")

    # ...and the sector really is no wider than DUCT_HALF_ANG, because the
    # trough's opening was sized from it.
    i_seal = int(round((58.0 - tzs[0]) / ZSTEP))
    tight = free[i_seal] < 0.5 * (P.R_DUCT_INNER + P.R_WORK)
    th = bin_centres()[tight]
    if len(th):
        d = np.abs((th - P.DUCT_THETA + 180.0) % 360.0 - 180.0)
        half = float(d.max()) + 0.5 * 360.0 / NBIN
    else:
        half = 0.0
    check(0.0 < half <= P.DUCT_HALF_ANG + 1.5,
          f"at s 58 the intrusion spans +/-{half:.1f} deg about theta "
          f"{P.DUCT_THETA:.0f}, inside the +/-{P.DUCT_HALF_ANG:.0f} deg "
          f"DUCT_HALF_ANG the trough's opening was sized against",
          f"at s 58 the intrusion spans +/-{half:.1f} deg, against "
          f"DUCT_HALF_ANG {P.DUCT_HALF_ANG:.0f} -- the opening is sized from "
          f"the wrong sector")

    # --- and the two bottlenecks the design is capped by
    fwd = min(measured(s, clear) for s in np.arange(0.0, 33.0, 0.5))
    aft = min(measured(s, clear) for s in np.arange(213.5, 260.0, 0.5))
    check(abs(fwd - P.R_ENTRY_FWD) <= tol and abs(aft - P.R_ENTRY_AFT) <= tol,
          f"the two entries measure r {fwd:.3f} forward and {aft:.3f} aft, so "
          f"the forward end really is the roomier one ({fwd-aft:+.3f} mm) as "
          f"well as the end that opens",
          f"the entries measure r {fwd:.3f} forward and {aft:.3f} aft against "
          f"R_ENTRY_FWD {P.R_ENTRY_FWD:.3f} / R_ENTRY_AFT {P.R_ENTRY_AFT:.3f}")


# ---------------------------------------------------------------- 3. features

def y_at(r: float, x: float) -> float:
    """The y that puts a point at radius `r` on the plane of constant `x`.

    Probes in this file want to sit at a known RADIUS -- in the bore, mid-wall,
    outside the OD -- but they are written at a fixed x (a deck face, mid-slab).
    Writing y down as a literal silently ties it to whatever x was current when it
    was chosen, so moving the deck moves the probe's radius and it starts asking a
    different question.  Derive it instead.

    Raises if the requested radius cannot be reached at that x, which is the honest
    outcome: a probe that cannot exist should stop the run, not quietly clamp to
    the nearest point and report on somewhere else.
    """
    d = r * r - x * x
    if d <= 0.0:
        raise ValueError(f"no point at radius {r:.3f} on the plane x = {x:.3f} "
                         f"(|x| already exceeds r) -- the probe is unreachable")
    return math.sqrt(d)


def verify_features(m_sup: trimesh.Trimesh, m_pl: trimesh.Trimesh,
                    n_sup: int, n_pl: int) -> None:
    """Every feature probed where it IS and where it should MISS.

    ONE function over TWO meshes, in the order the part is built rather than
    grouped by which file drew it: head and trough (support), then the deck and
    everything mounted on it (plate), then the bosses and their pilots (support),
    then the rails, the stop and the lugs -- which are the slide, and the only
    features here that need BOTH meshes to say anything.

    Each block names its own mesh, `m_sup` or `m_pl`.  Splitting this into two
    functions was the obvious alternative and it is worse: the pair of probes that
    matters most -- the pocket in the support and the chord in the plate that has
    to fit it -- would end up in different functions with the comparison between
    them written down nowhere.
    """
    sag = sagitta(P.R_SHELL_O, n_sup)
    mid = 0.5 * (P.R_SHELL_I + P.R_SHELL_O)      # mid-wall, immune to faceting
    x_deck = 0.5 * (P.DECK_X_BOT + P.DECK_X_TOP)  # mid-deck, likewise
    note(f"the support's sections resolve {n_sup} azimuths and the plate's "
         f"{n_pl} (sagitta {sag:.4f} mm at r {P.R_SHELL_O:.2f}); every probe "
         f"below sits at a mid-wall or mid-slab coordinate so faceting cannot "
         f"reach it")
    m = m_sup                    # the head and the trough are the support's

    # --- the head is a COMPLETE ring.  This is the one claim in the docstring
    # that a partial-arc head would still satisfy at three of these azimuths, so
    # it is probed at eight including theta 0, which is where the trough opens.
    z_head = 0.5 * (P.S_HEAD_FWD + P.S_CROWN)
    r_probe = P.R_CROWN - 2.0 * sagitta(P.R_CROWN, n_sup) - 0.05
    expect_points(m, "head ring", [
        (cyl(r_probe, th, z_head), True,
         f"the head is solid at r {r_probe:.2f}, theta {th:.0f}")
        for th in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
    ])

    expect_points(m, "trough", [
        # the opening exists aft of the head, and only aft of it
        (cyl(mid, 0.0, 100.0), False,
         "at theta 0 the shell is cut away, which is what the cord duct needs"),
        (cyl(mid, 40.0, 100.0), False,
         "at theta 40 the shell is still cut away (x = r cos40 > X_OPEN)"),
        (cyl(mid, 90.0, 100.0), True,
         "at theta 90 the shell is present"),
        (cyl(mid, 180.0, 100.0), True,
         "at theta 180 the shell is present"),
        (cyl(mid, 270.0, 100.0), True,
         "at theta 270 the shell is present"),
        ((P.X_OPEN + 1.0, 29.0, 100.0), False,
         "1 mm outboard of the opening plane there is no material"),
        ((P.X_OPEN - 1.0, 28.6, 100.0), True,
         "1 mm inboard of the opening plane there is"),
        # the interior of the trough is empty -- it is a C, not a rod
        ((0.0, 0.0, 100.0), False, "the axis is open all the way through"),
    ])

    # --- the deck, WHICH IS NOW A SEPARATE PART WITH A FREE EDGE.  That inverts
    # the probe this block used to make.  On the one-piece sled the deck's curved
    # edge was buried FUSE_MERGE deep in the shell wall, so material ran
    # CONTINUOUSLY from the centreline out to the OD and there was no void out
    # there to find -- the honest statement was that the deck had no free edge.
    # Now it has nothing but a free edge, at r R_PLATE, with SLIDE_CLR_R of air
    # outside it, and the pair of probes below is the interesting one BECAUSE it
    # spans two meshes: the same two radii are solid-then-void in the plate and
    # void-then-solid in the support.
    #
    # The y values stay DERIVED from the radii at the probe's own x.  They were
    # literals (24.0, 27.0, 26.2) picked when the deck sat at x -14..-12, and a
    # literal y means a different RADIUS at every deck height: raising the deck by
    # 6 mm moved y 27.0 from outside the OD (r 29.96, void) to inside the shell
    # wall (r 27.89, solid), so the probe asked the opposite question and failed
    # while the part was correct.  Two of four still passed by luck while quoting
    # a half-width that had changed.
    m = m_pl                     # everything on the deck is the plate's
    y_in = y_at(P.R_PLATE - 0.1, x_deck)
    y_out = y_at(P.R_PLATE + 0.2, x_deck)
    expect_points(m, "deck", [
        ((x_deck, 0.0, 100.0), True, "the deck is solid on the centreline"),
        ((x_deck, 20.0, 100.0), True, "and out at y 20"),
        ((x_deck, y_in, 100.0), True,
         f"and still solid at y {y_in:.2f} (r {P.R_PLATE - 0.1:.2f}), a tenth of "
         f"a millimetre inside its clip radius"),
        ((x_deck, y_out, 100.0), False,
         f"and gone by y {y_out:.2f} (r {P.R_PLATE + 0.2:.2f}) -- so the edge is "
         f"where R_PLATE {P.R_PLATE:.2f} puts it, not out at the bore"),
        ((P.DECK_X_TOP + 1.0, 0.0, 100.0), False, "nothing above the deck"),
        ((P.DECK_X_BOT - 1.0, 0.0, 100.0), False, "nothing below it"),
        ((x_deck, 0.0, P.S_PLATE_FWD + 0.5), True,
         "the deck runs right to its forward face, so it can be pushed flush "
         "with the support's"),
        ((x_deck, 0.0, P.S_PLATE_AFT - 0.5), True,
         "and right to its aft face, which is the face that lands on the stop"),
    ])
    expect_points(m_sup, "the pocket, at the same two radii", [
        ((x_deck, y_out, 100.0), False,
         f"y {y_out:.2f} (r {P.R_PLATE + 0.2:.2f}) is open in the SUPPORT too -- "
         f"the plate's {P.SLIDE_CLR_R:.2f} mm of radial clearance is air, not "
         f"somewhere the support puts material"),
        ((x_deck, y_at(P.R_SHELL_I + 0.5, x_deck), 100.0), True,
         f"and y {y_at(P.R_SHELL_I + 0.5, x_deck):.2f} (r "
         f"{P.R_SHELL_I + 0.5:.2f}) is the shell wall that closes it off"),
        ((x_deck, 0.0, 100.0), False,
         "with the support empty on the centreline at the deck's own height, "
         "which is the space the plate goes into"),
    ])
    m = m_pl

    expect_points(m, "ESP32 pin slots", [
        ((x_deck, P.PIN_SLOT_Y, 100.0), False,
         "the +y slot is open where the headers land"),
        ((x_deck, -P.PIN_SLOT_Y, 100.0), False, "and the -y slot too"),
        ((x_deck, 0.0, 100.0), True,
         "the deck between the slots is intact -- they are two slots, not one"),
        ((x_deck, P.PIN_SLOT_Y, P.S_PIN_SLOT_0 - 2.0), True,
         "the slot has not started 2 mm forward of S_PIN_SLOT_0"),
        ((x_deck, P.PIN_SLOT_Y, P.S_PIN_SLOT_1 + 2.0), True,
         "and has ended 2 mm aft of S_PIN_SLOT_1"),
        ((P.DECK_X_BOT - 1.5, P.PIN_SLOT_Y, 100.0), False,
         "under the slot is open, so a 3.5 mm header pin has somewhere to go"),
    ])

    x_rib = P.DECK_X_TOP + 0.5 * P.RIB_H_BMP
    expect_points(m, "BMP280 ribs", [
        ((x_rib, P.RIB_Y_BMP, 50.0), True, "the +y rib stands off the deck"),
        ((x_rib, -P.RIB_Y_BMP, 50.0), True, "and the -y rib"),
        ((x_rib, 0.0, 50.0), False,
         "between them is open, which is where the board sits"),
        ((x_rib, P.RIB_Y_BMP, 100.0), False,
         "there is no rib out at the ESP32's station"),
        # the ramp: at 1 mm aft of the rib's start the rib has risen 1 mm and
        # no more, which is the 45 degree ramp that lets it print
        ((P.DECK_X_TOP + 0.4, P.RIB_Y_BMP, P.S_RIB_BMP_0 + 1.0), True,
         "1 mm into the ramp the rib is 0.4 mm tall"),
        ((P.DECK_X_TOP + 1.6, P.RIB_Y_BMP, P.S_RIB_BMP_0 + 1.0), False,
         "...and not yet 1.6 mm, so it really does ramp rather than step"),
        ((P.DECK_X_TOP + 1.6, P.RIB_Y_BMP, P.S_RIB_BMP_0 + 4.0), True,
         "4 mm in it is at full height"),
    ])

    expect_points(m, "BMP280 static ports", [
        ((x_deck, 0.0, P.BMP_PORT_STATIONS[1]), False,
         f"the port at s {P.BMP_PORT_STATIONS[1]:.0f} is open"),
        ((x_deck, 0.0, P.BMP_PORT_STATIONS[1] + 3.0), True,
         "and the deck 3 mm aft of it is not"),
        ((x_deck, 4.0, P.BMP_PORT_STATIONS[1]), True,
         "the ports are on the centreline, so 4 mm off it is solid"),
    ])

    expect_points(m, "cable-tie slots", [
        ((x_deck, P.STRAP_Y_BMP, P.STRAP_STATIONS_BMP[0]), False,
         "the BMP280's tie slot is open"),
        ((x_deck, -P.STRAP_Y_BMP, P.STRAP_STATIONS_BMP[0]), False,
         "on both sides"),
        ((x_deck, P.STRAP_Y_MAIN, P.STRAP_STATIONS_ESP32[0]), False,
         "the ESP32's forward tie slot is open"),
        ((x_deck, P.STRAP_Y_MAIN, P.STRAP_STATIONS_BATT[1]), False,
         "the battery's aft tie slot is open"),
        ((x_deck, P.STRAP_Y_MAIN, P.STRAP_STATIONS_BATT[1] + 6.0), True,
         "and the deck 6 mm aft of it is solid, so it is a slot and not a "
         "channel running the whole length"),
        # Probed at the BATTERY's station, not the ESP32's.  y 13 at s 78 is
        # inside the ESP32's PIN slot (PIN_SLOT_Y 12.7 +/- 1.8 spans y 10.9..14.5
        # over s 68..126), so the original probe read void and blamed the tie
        # slots for a hole that another feature had correctly made.
        ((x_deck, P.STRAP_Y_BMP, P.STRAP_STATIONS_BATT[0]), True,
         "the BMP's tie radius y 13.0 is not repeated further aft, where the "
         "ties move out to y 18 -- the two radii are distinct features"),
    ])

    expect_points(m, "deck vents", [
        ((x_deck, P.VENT_Y, P.VENT_STATIONS[0]), False,
         f"the vent at s {P.VENT_STATIONS[0]:.0f} is open"),
        ((x_deck, -P.VENT_Y, P.VENT_STATIONS[1]), False,
         f"and the one at s {P.VENT_STATIONS[1]:.0f}"),
        ((x_deck, P.VENT_Y, P.VENT_STATIONS[0] + 5.0), True,
         "and the deck 5 mm aft of it is solid"),
    ])

    # --- the screw bosses and their pilots, measured as radial spans rather
    # than probed as points: the number that matters is how much thread the
    # screw gets, and that is a length, not a yes/no.
    m = m_sup                    # back to the support for the bosses
    for th in P.SCREW_THETA:
        span = solid_span(m, th, P.S_BOSS_0 + 3.0, 20.0, 31.0)
        want = P.R_SHELL_O - P.R_BOSS_I
        check(span is not None and abs(span[2] - want) < 0.25,
              f"boss at theta {th:.0f}: solid from r {fmt(span, 0)} to "
              f"{fmt(span, 1)} = {fmt(span, 2)} mm of thread, against the "
              f"{want:.2f} designed",
              f"boss at theta {th:.0f}: the radial solid span is "
              f"{fmt(span, 2)} mm, not the {want:.2f} mm of thread the screw "
              f"needs")

        # How far off the boss's centre to probe.  This has now been wrong TWICE in
        # the same way, so the reasoning is written out rather than the answer.
        #
        # It began as the literal 17.0, chosen to clear the boss's 9 deg edge while
        # staying "inboard of the deck's 115 degree one" -- true for a deck at
        # x -14..-12, whose clipped edge sat at azimuth 114.1.  At DECK_RISE 6 that
        # edge moved in to 102.4, so a 17 deg ray walked through the DECK and read
        # 6.85 mm of continuous solid: a boss reported 3x too wide, from a part that
        # was correct.  So it was derived from DECK_X_TOP instead.
        #
        # THEN THE DECK LEFT THIS MESH.  The support has no deck any more; what it
        # has at negative x is the two RAILS, and the first one the ray meets is the
        # LOWER rail, whose top face is at POCKET_X_BOT -- 2.30 mm FURTHER OUT than
        # the deck's top face was.  Derived from the deck the window came out
        # (9.0, 12.4) and the check still passed, by luck: the upper rail ends at
        # S_RAIL_U_1 188.0 and this probe is at s 197, so the material the old
        # formula was avoiding was not there to hit.  Move S_RAIL_U_1 aft and the
        # same passing check starts reading rail as boss.
        #
        # The window is therefore (BOSS_HALF_ANG, th_rail - 90): far enough off
        # centre that the boss is gone, near enough that the ray stays INBOARD of
        # the lower rail's x-band over the whole radial band the rail occupies.
        # The binding radius is the rail's OUTER one, since that is where the ray
        # has swung furthest in x by the time it gets there.
        th_rail = math.degrees(math.acos(max(-1.0, P.POCKET_X_BOT / P.R_RAIL_O)))
        d_lo, d_hi = P.BOSS_HALF_ANG, th_rail - 90.0
        if d_hi - d_lo < 1.0:
            raise ValueError(
                f"no azimuth left between the boss's edge ({d_lo:.2f} deg off "
                f"centre) and the lower rail's ({d_hi:.2f} deg) -- a radial span "
                f"cannot tell boss from rail, so measure the boss's ANGULAR width "
                f"directly instead of inferring it from one ray")
        d_off = 0.5 * (d_lo + d_hi)
        th_c = th + (d_off if th < 180.0 else -d_off)
        span = solid_span(m, th_c, P.S_BOSS_0 + 3.0, 20.0, 31.0)
        check(span is not None and abs(span[2] - P.SHELL_T) < 0.25,
              f"boss at theta {th:.0f}: {d_off:.1f} deg away (in the "
              f"{d_lo:.0f}..{d_hi:.1f} window between its own edge and the lower "
              f"rail's) it is gone and only the {P.SHELL_T:.1f} mm shell remains "
              f"({fmt(span, 2)} mm) -- the boss is local, not a full ring",
              f"boss at theta {th:.0f}: {d_off:.1f} deg away the radial "
              f"span is {fmt(span, 2)} mm, not the shell's {P.SHELL_T:.1f} -- "
              f"the boss is wider than BOSS_HALF_ANG says")

        span = solid_span(m, th, P.S_SCREW, 20.0, 31.0)
        check(span is None,
              f"screw pilot at theta {th:.0f}: the radial ray at s "
              f"{P.S_SCREW:.1f} is open from r 20 to 31 -- the pilot goes all "
              f"the way through boss and shell",
              f"screw pilot at theta {th:.0f}: the ray at s {P.S_SCREW:.1f} "
              f"still hits solid at r {fmt(span, 0)}..{fmt(span, 1)} -- the "
              f"pilot did not go through")

    expect_points(m, "boss ramp", [
        (cyl(26.5, P.SCREW_THETA[0], P.S_BOSS_RAMP + 2.0), True,
         "2 mm into the ramp the boss has reached r 26.5"),
        (cyl(25.0, P.SCREW_THETA[0], P.S_BOSS_RAMP + 2.0), False,
         "...and not yet r 25.0, so it ramps in instead of stepping"),
        (cyl(25.0, P.SCREW_THETA[0], P.S_BOSS_0 + 3.0), True,
         "and is at full depth 3 mm past S_BOSS_0"),
        (cyl(25.0, P.SCREW_THETA[0], P.S_BOSS_RAMP - 3.0), False,
         "3 mm forward of the ramp's foot there is no boss at all"),
    ])

    # --- THE RAILS AND THE STOP: the support's half of the slide, probed as points.
    # The three CLEARANCES are lengths and are measured in verify_slide() instead --
    # a containment probe cannot report 0.30 mm, it can only report which side of a
    # face it fell on.
    #
    # Every y below is DERIVED by y_at() from a radius, because these features are
    # bounded by RADII on one axis (the rails live in the annulus R_RAIL_I..R_RAIL_O)
    # and by X on the other (each rail is an x-band).  A literal y is a different
    # radius at every x, which is the mistake the deck block above records.
    r_rail = 0.5 * (P.R_RAIL_I + P.R_SHELL_I)        # 26.75: inside the rails' band
                                                     # and inboard of the bore, so a
                                                     # probe here reads rail or air
    x_lo = 0.5 * (P.RAIL_L_X_BOT + P.POCKET_X_BOT)   # -9.30, mid lower rail
    # The upper rail's x-band runs -5.70..-3.70 and the BOSSES reach |x| <= r sin 9
    # deg = 4.18 at this radius, so the two overlap over |x| 3.70..4.18 -- which is
    # exactly why bay_support stops the upper rail forward of them.  Probe the part
    # of the band no boss can ever reach, or the "gone aft of S_RAIL_U_1" probe below
    # reads a boss and calls it a rail.
    x_boss = r_rail * math.sin(math.radians(P.BOSS_HALF_ANG))
    x_up = 0.5 * (P.POCKET_X_TOP - x_boss)           # -4.94
    y_pk = y_at(r_rail, x_deck)
    expect_points(m, "the rails", [
        ((x_up, y_at(r_rail, x_up), 100.0), True,
         f"the upper rail is solid at x {x_up:.2f}, r {r_rail:.2f} -- "
         f"{-x_boss - x_up:.2f} mm outboard of the furthest a boss reaches in x"),
        ((x_up, y_at(r_rail, x_up), P.S_RAIL_U_1 + 7.0), False,
         f"and gone by s {P.S_RAIL_U_1 + 7.0:.0f}, aft of S_RAIL_U_1 "
         f"{P.S_RAIL_U_1:.0f} -- which is what leaves the bosses' azimuth to the "
         f"bosses.  The two M3s hold the plate down over that last "
         f"{P.S_TAIL - P.S_RAIL_U_1:.0f} mm"),
        ((x_lo, y_at(r_rail, x_lo), 100.0), True,
         f"the lower rail is solid at x {x_lo:.2f}, r {r_rail:.2f}"),
        ((x_lo, y_at(r_rail, x_lo), P.S_TAIL - 1.0), True,
         "and still there a millimetre from the tail: it runs the whole length, "
         "because it is the plate's floor AND the stop's own floor"),
        ((x_deck, y_pk, 100.0), False,
         f"and between them, at the deck's own x and r {r_rail:.2f}, the pocket "
         f"is open -- which is the space the plate slides down"),
    ])

    # The stop is the entire answer to "make sure it only slides in one way", so it
    # gets probed on all three of its faces: filled aft, open forward, and open
    # INBOARD -- the last is what keeps its own forward face over the lower rail
    # instead of bridging the bore, and it is the printability claim as well as the
    # geometry one.
    expect_points(m, "the aft stop, the one-way part", [
        ((x_deck, y_pk, P.S_STOP + 2.0), True,
         f"the pocket is FILLED at s {P.S_STOP + 2.0:.0f}, aft of S_STOP "
         f"{P.S_STOP:.0f}"),
        ((x_deck, y_pk, P.S_STOP - 2.0), False,
         f"and open at s {P.S_STOP - 2.0:.0f}, forward of it -- so the plate runs "
         f"free to the stop and no further, and cannot continue out of an aft end "
         f"{P.S_TAIL:.0f} mm down a 38 mm tube"),
        ((x_deck, y_at(P.R_RAIL_I - 0.25, x_deck), P.S_STOP + 2.0), False,
         f"the stop reaches only in to r {P.R_RAIL_I:.2f}: a quarter of a "
         f"millimetre inboard of that it is air, so its forward face lands on the "
         f"lower rail and the shell rather than bridging the bore"),
    ])

    # --- and the one thing the pocket does NOT do, recorded because it is a real
    # gap in the design rather than a check of it.  A plate inserted 180 degrees out
    # lands its chord at x +6..+8, and there is nothing there at all: that is where
    # bay_support CUTS THE TROUGH OPEN for the shock cord.  See the note below.
    expect_points(m, "the pocket's mirror image", [
        ((-x_deck, y_pk, 100.0), False,
         f"x {-x_deck:+.1f}, r {r_rail:.2f} is open -- the mirror of the pocket "
         f"is the trough's opening, cut away for x > X_OPEN {P.X_OPEN:.1f}"),
        ((-x_deck, 0.0, 100.0), False, "and open on the centreline too"),
    ])
    note(f"THERE IS NO HARD KEY AGAINST INSERTING THE PLATE 180 DEGREES OUT, and "
         f"the two probes above are why: rotated, the plate's chord sits at "
         f"x {-P.DECK_X_TOP:+.1f}..{-P.DECK_X_BOT:+.1f}, inside the trough's "
         f"opening, where it engages NEITHER rail and misses the stop -- so it "
         f"would not jam, it would drop through to the tube's aft end.  Its lugs "
         f"still clear the bosses and its pilots are still on x = 0, so it could "
         f"even be screwed down.  Unlike the SUPPORT's half turn, which the cord "
         f"duct catches (see the keying check), nothing in the geometry catches "
         f"this one.  Deliberately not fixed yet: it wants an asymmetric feature "
         f"on the plate, which is a design change and not a verification.")

    # --- the two screw lugs, which are the plate's half of the retention
    m = m_pl
    y_lug = P.LUG_Y_O - 0.5 * P.LUG_DEPTH            # 19.0, mid-lug in y
    z_lug = P.S_LUG_0 + 1.5                          # 199.0: in the lug, and clear
                                                     # of its own pilot at 201.0
    expect_points(m, "the screw lugs", [
        ((0.0, y_lug, z_lug), True,
         f"the lug crosses x = 0 at y {y_lug:.1f}, s {z_lug:.1f}"),
        ((P.LUG_X_TOP - 0.3, y_lug, z_lug), True,
         f"and stands to x {P.LUG_X_TOP:+.1f}, {P.LUG_X_TOP - P.DECK_X_TOP:.1f} mm "
         f"off the deck's top face -- which is what puts the screw ABOVE the deck "
         f"instead of trying to thread its 2 mm thickness"),
        ((P.LUG_X_TOP + 0.5, y_lug, z_lug), False,
         f"and stops there, {P.X_OPEN - P.LUG_X_TOP:.1f} mm inboard of the "
         f"support's opening plane at x {P.X_OPEN:.1f}"),
        ((0.0, y_lug, P.S_LUG_0 - 2.0), False,
         f"nothing forward of S_LUG_0 {P.S_LUG_0:.1f}"),
        ((0.0, y_lug, P.S_LUG_PILOT), False,
         f"and the pilot is open on the screw's own axis at s "
         f"{P.S_LUG_PILOT:.1f} -- drawn {P.SLIDE_GAP_Z:.1f} mm forward of the "
         f"boss's {P.S_SCREW:.1f}, so the two line up only once the plate has "
         f"slid home"),
        ((0.0, -y_lug, P.S_LUG_PILOT), False, "on both sides"),
    ])


def solid_span(m: trimesh.Trimesh, theta: float, z: float,
               r0: float, r1: float, step: float = 0.05):
    """First solid run met walking outward along a radial ray: (r_in, r_out, t).

    None when the ray never enters material.  A marched span rather than a
    bisection, because these rays are not monotonic: at the screw stations the
    ray crosses boss, then pilot, then shell again, and a bisection between a
    void point and a solid one lands wherever the first sign change happens to
    be rather than at the boundary asked for.
    """
    rs = np.arange(r0, r1 + 1e-9, step)
    pts = np.array([cyl(float(r), theta, z) for r in rs])
    ins = inside(m, pts)
    if not ins.any():
        return None
    i = int(np.argmax(ins))
    j = i
    while j < len(ins) and ins[j]:
        j += 1
    a, b = float(rs[i]), float(rs[min(j, len(rs) - 1)])
    return a, b, b - a


def fmt(span, i: int) -> str:
    """Format one element of a possibly-absent span.

    check() builds BOTH its messages before it looks at the condition, so an
    unguarded span[1] in the PASSING message crashes on the run where the span
    is None -- which is exactly the run where the failure message was the whole
    point.  This is how that happened once already.
    """
    return "nothing" if span is None else f"{span[i]:.2f}"


# --------------------------------------------------------------- 4. the slide

def half_step(v: float, step: float) -> float:
    """A grid origin at or below v, offset half a step from every design face.

    Every marched grid in the slide checks starts at one of these, and the
    reason is one line long: a sample that lands exactly ON a design face is
    decided by whatever mesh.contains() does at a surface, which is nothing in
    particular.  A 0.30 mm clearance read off such a grid is then decided by
    which way a coincident point happened to round.

    Every design face in this bay is a multiple of 0.05 mm -- the parameter
    table is written in hundredths -- so an origin at an ODD multiple of half a
    step keeps every sample half a step clear of all of them.  It also makes
    that half step CANCEL in the difference of two samples, which is how the
    clearances below come out exact rather than merely within a step.
    """
    return (math.floor(v / step) + 0.5) * step


def x_faces(m: trimesh.Trimesh, y: float, z: float, x_seed: float,
            want: bool, x0: float, x1: float, step: float = 0.05):
    """Walk both ways along x from a seed and report where the state stops.

    Returns (x_lo, x_hi): the first sample BELOW the seed and the first sample
    ABOVE it whose containment differs from `want`, or None on a side that never
    flips before the grid runs out.  The whole row is probed in one inside()
    call, so the two meshes below are read on IDENTICAL coordinates.

    Why a walk and not a bisection, and why the grid starts where it does:

    A bisection would have to be told which side is which, and the pocket has
    material on both sides of it.  More importantly, every number this returns
    is used as the DIFFERENCE of two samples, and that only works if both come
    off the same grid.  The grid is deliberately offset by half a step from the
    design faces (x0 carries a -0.5*step), so no sample can land ON a face --
    mesh.contains() is undefined there and would decide a 0.30 mm clearance by
    which way a coincident point rounded.  Each returned sample therefore sits
    half a step outside the face it brackets, and in a difference of two of them
    that half step CANCELS.  What is left is smaller than one step, which is
    why every threshold below is one step and not something invented.

    A seed in the wrong state is raised, not returned.  This file's history is
    mostly mis-aimed probes reported as defects: a seed that is already solid
    when the caller thinks it is in the pocket would return the pocket's far
    side twice and call it a width.
    """
    xs = np.arange(x0, x1 + 1e-9, step)
    i = int((x_seed - x0) / step + 0.5)
    if not 0 <= i < len(xs):
        raise ValueError(
            f"the seed x {x_seed:.3f} is outside the probed range "
            f"{x0:.3f}..{x1:.3f}")
    ins = inside(m, np.array([(float(x), y, z) for x in xs]))
    if bool(ins[i]) != want:
        raise ValueError(
            f"the seed at x {xs[i]:+.3f}, y {y:.3f}, s {z:.2f} is "
            f"{'SOLID' if ins[i] else 'VOID'} and the caller expected "
            f"{'SOLID' if want else 'VOID'} -- the probe is in the wrong place, "
            f"so nothing measured from it means anything")
    lo = hi = None
    for k in range(i - 1, -1, -1):
        if bool(ins[k]) != want:
            lo = float(xs[k])
            break
    for k in range(i + 1, len(xs)):
        if bool(ins[k]) != want:
            hi = float(xs[k])
            break
    return lo, hi


def verify_slide(m_sup: trimesh.Trimesh, m_pl: trimesh.Trimesh,
                 n_sup: int, n_pl: int) -> None:
    """The three clearances of the slide, measured on the two exported meshes.

    bay_assembly.py already proves the slide on the SOLIDS, exactly, by
    intersecting the support with the plate's swept envelope.  This does not
    repeat that -- it cannot, at 0.5 mm of station grid -- it answers the
    question that boolean does not: what are the clearances, as NUMBERS, on the
    meshes that will actually be printed.  A boolean that comes out empty says
    the parts do not touch; it does not say whether they miss by 0.30 mm or by
    3.0, and 3.0 would be a plate that rattles.

    Everything here is measured where the geometry is CONSTANT ALONG z, which is
    what lets a single ray stand for the whole length.  The station is derived
    from that requirement rather than picked.
    """
    step = 0.05

    # THE STATION.  Aft of the head (so the bore is the shell's), aft of the
    # rails' start, forward of the upper rail's end and forward of the bosses'
    # ramp, and inside the plate's own span.  Anywhere in that window reads the
    # same section, so take the middle of it.
    z_lo = max(P.S_HEAD_AFT, P.S_RAIL_0, P.S_PLATE_FWD)
    z_hi = min(P.S_RAIL_U_1, P.S_BOSS_RAMP, P.S_PLATE_AFT)
    z = 0.5 * (z_lo + z_hi)

    # THE y OF THE x-WALK, and it is the tightest placement in this file: a
    # window 0.42 mm wide.  One ray has to cross, in order, the lower rail, the
    # pocket, the plate's chord and the upper rail -- so it must be far enough
    # out in y that the UPPER RAIL still exists at its own bottom face
    # (POCKET_X_TOP is only 5.70 mm off centre, so the rail's inner radius has
    # nearly all of its y there), and far enough IN that the plate's chord has
    # not yet been clipped away by its own curved edge at DECK_X_BOT, 8.30 mm
    # off centre.  Those two pull opposite ways and the window between them
    # exists only because RAIL_ENGAGE (R_PLATE - R_RAIL_I) is wide enough to
    # pay for the 2.60 mm of x between the two features.
    y_lo = math.sqrt(P.R_RAIL_I ** 2 - P.POCKET_X_TOP ** 2)
    y_hi = math.sqrt(P.R_PLATE ** 2 - P.DECK_X_BOT ** 2)
    if y_hi - y_lo < 4.0 * step:
        raise ValueError(
            f"no y left for the x-walk: the upper rail needs y >= {y_lo:.3f} "
            f"and the plate's chord ends by y = {y_hi:.3f}.  One ray can no "
            f"longer cross all four features, so measure the pocket and the "
            f"chord on SEPARATE rays instead of pretending this one still "
            f"reads both")
    y = 0.5 * (y_lo + y_hi)

    x_deck = 0.5 * (P.DECK_X_BOT + P.DECK_X_TOP)      # in the pocket, in the plate
    x0 = half_step(P.RAIL_L_X_BOT - 1.0, step)        # below the lower rail's own
    x1 = P.X_OPEN                                     # bottom face, and off-grid
    a_sup, b_sup = x_faces(m_sup, y, z, x_deck, False, x0, x1, step)
    a_pl, b_pl = x_faces(m_pl, y, z, x_deck, True, x0, x1, step)
    if None in (a_sup, b_sup, a_pl, b_pl):
        raise ValueError(
            f"the x-walk at y {y:.3f}, s {z:.2f} did not find all four faces: "
            f"support {a_sup} / {b_sup}, plate {a_pl} / {b_pl} -- a rail or the "
            f"chord is missing from a mesh, which is a bigger problem than a "
            f"clearance")

    note(f"the slide is measured at s {z:.2f} (constant section from "
         f"{z_lo:.2f} to {z_hi:.2f}) on one x-walk at y {y:.3f}, which is the "
         f"middle of the only {y_hi - y_lo:.2f} mm of y where a single ray "
         f"crosses lower rail, pocket, chord and upper rail.  Samples land half "
         f"a step off every design face on purpose, and each clearance below is "
         f"a DIFFERENCE of two of them, so that offset cancels.")

    # (a) the pocket, as a VOID between two rails.  b - a spans one step more
    # than the void does -- half a step of grid outside each face -- so the
    # unbiased width is b - a - step, good to better than one step.
    w_pocket = (b_sup - a_sup) - step
    w_want = P.POCKET_X_TOP - P.POCKET_X_BOT
    check(abs(w_pocket - w_want) <= step,
          f"pocket: {w_pocket:.3f} mm of void between the rails at s {z:.2f} "
          f"(samples {a_sup:+.3f}..{b_sup:+.3f}), against POCKET_X_TOP - "
          f"POCKET_X_BOT {w_want:.3f}",
          f"pocket: the void between the rails measures {w_pocket:.3f} mm "
          f"against the {w_want:.3f} it was drawn at -- a rail is in the wrong "
          f"place, or the export moved one")

    # (b) the plate's chord, in the same walk, so its thickness and the pocket's
    # width come off one grid and can be subtracted from each other.
    t_deck = (b_pl - a_pl) - step
    check(abs(t_deck - P.DECK_T) <= step,
          f"plate: its chord measures {t_deck:.3f} mm thick at the same y and s "
          f"(samples {a_pl:+.3f}..{b_pl:+.3f}), against DECK_T {P.DECK_T:.3f} "
          f"-- and it is 2.00 mm of SOLID there, so none of the deck's slots, "
          f"vents or ports reaches this far out in y",
          f"plate: its chord measures {t_deck:.3f} mm against DECK_T "
          f"{P.DECK_T:.3f} at y {y:.3f}, s {z:.2f} -- either the deck is the "
          f"wrong thickness or a slot has been cut out to the curved edge")

    # (c) and (d) THE TWO x CLEARANCES.  This is the pair that decides whether
    # the plate slides or has to be forced, and each is the difference of two
    # samples off the one grid: the plate's own face against the rail's.
    for meas, want, lbl, rail, faces in (
            (a_pl - a_sup, P.SLIDE_CLR_X, "under the plate", "lower",
             f"{a_pl:+.3f} - {a_sup:+.3f}"),
            (b_sup - b_pl, P.SLIDE_CLR_X, "over the plate", "upper",
             f"{b_sup:+.3f} - {b_pl:+.3f}")):
        check(abs(meas - want) <= step,
              f"slide: {meas:.3f} mm of clearance {lbl}, between its chord and "
              f"the {rail} rail ({faces}), against SLIDE_CLR_X {want:.2f}",
              f"slide: {meas:.3f} mm of clearance {lbl} against SLIDE_CLR_X "
              f"{want:.2f} -- {'the plate is a press fit in the pocket' if meas < want else 'the plate rattles in the pocket'}")

    # (e) THE RADIAL CLEARANCE, which needs a radial ray and a different
    # azimuth: the ray has to leave the plate through its CURVED EDGE, i.e. at
    # r = R_PLATE, which only happens where that circle is inside the chord's
    # own x-band.  Outside that window the ray leaves through a flat face
    # instead and reads the chord's thickness in disguise.
    th_r0 = math.degrees(math.acos(P.DECK_X_TOP / P.R_PLATE))
    th_r1 = math.degrees(math.acos(P.DECK_X_BOT / P.R_PLATE))
    th_edge = 0.5 * (th_r0 + th_r1)
    # Same half-step offset as the x-walk, for the same reason, and the SAME r0
    # for both meshes so the two spans are subtractable.
    r0 = half_step(0.5 * (P.R_BOSS_I + P.R_RAIL_I), step)
    span_pl = solid_span(m_pl, th_edge, z, r0, P.R_SHELL_I - 0.1, step)
    span_sup = solid_span(m_sup, th_edge, z, r0, P.R_SHELL_O + 1.0, step)
    # Faceting matters here and did not above: these two faces are CYLINDERS,
    # and a tessellated cylinder's flats lie inside it.  Both are read the same
    # way round, so the terms are added rather than allowed to cancel.
    tol = step + 2.0 * sagitta(P.R_PLATE, n_pl) + 2.0 * sagitta(P.R_SHELL_I,
                                                                n_sup)
    gap_r = (None if span_pl is None or span_sup is None
             else span_sup[0] - span_pl[1])
    check(gap_r is not None and abs(gap_r - P.SLIDE_CLR_R) <= tol,
          f"slide: {gap_r if gap_r is None else f'{gap_r:.3f}'} mm of RADIAL "
          f"clearance at theta {th_edge:.2f} -- the plate's curved edge at "
          f"r {fmt(span_pl, 1)} against the support's bore at "
          f"{fmt(span_sup, 0)}, and the shell {fmt(span_sup, 2)} mm thick "
          f"behind it -- against SLIDE_CLR_R {P.SLIDE_CLR_R:.2f} "
          f"(tolerance {tol:.3f})",
          f"slide: the radial clearance measures "
          f"{gap_r if gap_r is None else f'{gap_r:.3f}'} mm at theta "
          f"{th_edge:.2f} against SLIDE_CLR_R {P.SLIDE_CLR_R:.2f} -- plate edge "
          f"{fmt(span_pl, 1)}, bore {fmt(span_sup, 0)}.  The plate has to pass "
          f"the head ring's bore, so this one is not slop, it is fit")

    # (f) RAIL ENGAGEMENT: how much of the plate's edge is actually under the
    # upper rail.  It needs a THIRD azimuth, and the reason is the whole
    # architecture: the rails stand PROUD of the plate in x, so no single ray
    # can see both the plate's curved edge and the rail's inner face -- at any
    # azimuth where the ray enters the rail, the chord's x-band is already
    # behind it.  So the rail's inner radius is measured where the ray does
    # enter it at r = R_RAIL_I, and compared against the plate's outer radius
    # measured in (e).  Both are circles about the axis, so the comparison is
    # legitimate at different azimuths -- and both samples sit half a step
    # outside their own face, so the difference is unbiased.
    th_e0 = math.degrees(math.acos(P.RAIL_U_X_TOP / P.R_RAIL_I))
    th_e1 = math.degrees(math.acos(P.POCKET_X_TOP / P.R_RAIL_I))
    th_rail_in = 0.5 * (th_e0 + th_e1)
    span_rail = solid_span(m_sup, th_rail_in, z, r0, P.R_SHELL_O + 1.0, step)
    eng = (None if span_rail is None or span_pl is None
           else span_pl[1] - span_rail[0])
    check(eng is not None and abs(eng - P.RAIL_ENGAGE) <= tol,
          f"capture: the upper rail's inner face is at r {fmt(span_rail, 0)} "
          f"(theta {th_rail_in:.2f}, continuous out to {fmt(span_rail, 1)} "
          f"where it merges into the shell), so the plate's edge stands "
          f"{eng if eng is None else f'{eng:.3f}'} mm under it -- against "
          f"RAIL_ENGAGE {P.RAIL_ENGAGE:.2f}.  That is what makes it a pocket "
          f"and not a channel",
          f"capture: the rail engages the plate's edge by "
          f"{eng if eng is None else f'{eng:.3f}'} mm against RAIL_ENGAGE "
          f"{P.RAIL_ENGAGE:.2f} (rail inner {fmt(span_rail, 0)}, plate edge "
          f"{fmt(span_pl, 1)}) -- the plate could lift out of the pocket in x")
    note(f"the three azimuths above are all different and each is derived, not "
         f"chosen: theta {th_edge:.2f} is the middle of "
         f"{th_r0:.2f}..{th_r1:.2f}, where r = R_PLATE lies inside the chord's "
         f"x-band; theta {th_rail_in:.2f} is the middle of "
         f"{th_e0:.2f}..{th_e1:.2f}, where r = R_RAIL_I lies inside the upper "
         f"rail's.  The two windows do not overlap, which is not an "
         f"inconvenience -- it is the statement that the rails stand proud of "
         f"the plate.")


# ----------------------------------------------- 5-7. the insertion sweep

def sweep(env, zs, free, tzs, rows, rot_bins: int = 0,
          d_lo: float = 0.0, d_hi: float = D_MAX):
    """Worst (free radius - envelope) over every insertion depth.

    The part enters from the front, tail first, so at insertion depth d the
    part's own station z sits at tube station s = z - d, and d runs from large
    down to 0.  Rotating the part by rot_bins bins is the same as rolling the
    tube's azimuth map the other way, which keeps the part's envelope -- the
    expensive thing to compute -- untouched.

    Returns (worst gap, d, part z, theta).
    """
    fr = np.roll(free, -rot_bins, axis=1)
    best = (np.inf, None, None, None)
    th = bin_centres()
    for d in np.arange(d_lo, d_hi + 1e-9, DSTEP):
        s = zs - d
        idx = np.rint((s - tzs[0]) / ZSTEP).astype(int)
        ok = (idx >= 0) & (idx < len(tzs)) & rows
        if not ok.any():
            continue
        g = fr[np.clip(idx, 0, len(tzs) - 1)] - env
        g = np.where((env > 0.0) & ok[:, None] & np.isfinite(g), g, np.inf)
        k = int(np.argmin(g))
        j, b = divmod(k, NBIN)
        if g[j, b] < best[0]:
            best = (float(g[j, b]), float(d), float(zs[j]), float(th[b]))
    return best


def first_jam(env, zs, free, tzs, rows, rot_bins: int):
    """The largest insertion depth at which the part already fouls, or None.

    Largest, not smallest: the part comes in from large d, so the first foul it
    meets is at the largest d where one exists.  That is where it stops.
    """
    for d in np.arange(D_MAX, -1e-9, -DSTEP):
        g, dd, z, th = sweep(env, zs, free, tzs, rows, rot_bins, d, d)
        if g < 0.0:
            return float(d), g, z, th
    return None


def verify_insertion(env, zs, free, tzs, allow: float) -> None:
    head = zs <= P.S_HEAD_AFT + 1e-9
    body = ~head

    note(f"faceting allowance for the sweep: {allow:.4f} mm, from both meshes' "
         f"own angular resolution.  A gap smaller than this is not a "
         f"measurement, which is why the thresholds below are set at it rather "
         f"than at zero.")

    # --- the body must never touch anything, at any depth.  This is the check
    # that the assembled position cannot make: the tail sweeps the whole duct.
    g, d, z, th = sweep(env, zs, free, tzs, body)
    check(g > allow,
          f"insertion: the support's body clears the tube at EVERY depth from "
          f"{D_MAX:.0f} mm out to home -- worst approach {g:.3f} mm, at "
          f"insertion depth {d:.1f} (support station {z:.1f}, theta {th:.0f}, "
          f"i.e. tube station {z-d:.1f})",
          f"insertion: the support's body fouls the tube by {-g:.3f} mm at "
          f"insertion depth {d:.1f}, support station {z:.1f}, theta {th:.0f} "
          f"(tube station {z-d:.1f}) -- it will not go in")

    # --- the head must clear too, right up until it seats
    g, d, z, th = sweep(env, zs, free, tzs, head, d_lo=1.0)
    check(g > allow,
          f"insertion: the head clears until the last millimetre -- worst "
          f"approach {g:.3f} mm at depth {d:.1f}",
          f"insertion: the head fouls by {-g:.3f} mm at depth {d:.1f}, support "
          f"station {z:.1f}, theta {th:.0f} -- it jams before it can seat")

    # --- and then it seats, on the bead's forward flank, where it was designed
    g, d, z, th = sweep(env, zs, free, tzs, head, d_lo=0.0, d_hi=0.0)
    # The seat's threshold is NOT `allow`.  Faceting is the SMALLEST of three
    # error terms here, and using it alone failed this check at -0.041 mm -- a
    # match reported as a defect.  Measured, in descending order:
    #   ZSTEP x flank slope   ~0.20 mm.  The flank drops ~0.40 mm of radius per
    #                         mm of station and the sweep resolves stations only
    #                         to ZSTEP, so its radius is good to no better
    #   azimuthal scatter     ~0.007 mm, the tightest azimuth against the typical
    #   faceting              `allow`, ~0.007 mm -- thirty times smaller than the
    #                         station term, which is why it cannot be the whole
    #                         threshold
    # Same mistake bay_params.self_check() made once when it reported the crown
    # "fouls by 0.002 mm": a threshold set at zero on a quantity whose grid
    # cannot resolve zero.  A negative gap of a fraction of ZSTEP*slope is what a
    # seated convex crown in a concave fillet is SUPPOSED to measure -- and the
    # station it seats at is self-selecting, so a tenth of a millimetre of
    # disagreement with the table moves the seat a tenth of a millimetre and
    # changes nothing else about the part.
    slope = flank_slope(P.S_CROWN)
    scat, _ = flank_scatter(free, tzs, ~in_duct_bins(), near=P.S_CROWN)
    seat_allow = allow + ZSTEP * slope + scat
    check(abs(g) <= seat_allow and abs(z - P.S_CROWN) <= 1.0,
          f"seat: at home the head's closest approach to the bead is "
          f"{g:+.3f} mm at station {z:.2f}, against the designed S_CROWN "
          f"{P.S_CROWN:.2f} -- it lands on the flank, not on air and not on "
          f"the throat (threshold {seat_allow:.3f} = {allow:.3f} faceting + "
          f"{ZSTEP*slope:.3f} station grid + {scat:.3f} azimuthal scatter)",
          f"seat: at home the head's closest approach is {g:+.3f} mm at "
          f"station {z:.2f}, against S_CROWN {P.S_CROWN:.2f} and a "
          f"{seat_allow:.3f} mm threshold -- the crown does not seat where "
          f"bead_seat_station() says it does")

    # --- it cannot fall through, which is the other half of the datum's job
    r_head = float(np.max(env[head]))
    r_body = float(np.max(env[body]))
    check(r_head > P.R_BEAD_THROAT,
          f"retention: the head measures r {r_head:.3f} against the bead's "
          f"throat at {P.R_BEAD_THROAT:.3f}, so it overlaps the ring by "
          f"{r_head - P.R_BEAD_THROAT:.3f} mm and the support cannot be lost aft "
          f"into the tube",
          f"retention: the head measures only r {r_head:.3f} against the "
          f"bead's {P.R_BEAD_THROAT:.3f} -- it will pass straight through")
    check(r_body < P.R_BEAD_THROAT,
          f"retention: everything aft of the head measures r {r_body:.3f}, "
          f"{P.R_BEAD_THROAT - r_body:.3f} mm inside the throat, so the body "
          f"passes while the head does not",
          f"retention: something aft of the head measures r {r_body:.3f}, past "
          f"the throat's {P.R_BEAD_THROAT:.3f} -- the body cannot pass")

    # --- withdrawal: forward, through the socket, which is the roomier end
    check(r_head < P.R_SOCKET,
          f"service: the head measures r {r_head:.3f} against the socket's "
          f"{P.R_SOCKET:.3f}, so the support withdraws forwards through it "
          f"({P.R_SOCKET - r_head:.3f} mm clear) once the nose is off",
          f"service: the head measures r {r_head:.3f} and the socket is "
          f"{P.R_SOCKET:.3f} -- the support cannot be taken out either end")


def verify_plate_through_tube(penv, pzs, free, tzs, allow: float) -> None:
    """The PLATE against the airframe -- which check (4) does not cover.

    (4) measures the plate against the support, and that is the fit that decides
    whether it slides.  It is not the whole question, because the support is a C:
    it is cut open for every x > X_OPEN 4.0, and the tube's shock-cord duct
    bulges inward to r 21.10 over s 46..63 -- THROUGH that opening, into the very
    space the plate travels down.  Nothing in bay_support.py or bay_plate.py can
    see that: it is a feature of the airframe against a feature of the plate,
    with the support's missing wall in between.

    The plate's lugs are the only part of it that crosses x = 0, standing to
    x +3.0, so the margin is 1.0 mm of x against the opening plane -- and the
    duct is beyond that.  What actually saves it is AZIMUTH, not radius, and that
    is worth being explicit about: the duct occupies +/-12 degrees about theta 0
    and the nearest plate material is some 67 degrees away from its edge.  A
    radial margin would be the wrong thing to quote, because in the duct's own
    sector the plate has no radius at all.
    """
    duct = in_duct_bins()
    r_duct = float(np.max(penv[:, duct]))
    check(r_duct <= 0.0,
          f"plate vs duct: the plate has NO material in any of the "
          f"{int(duct.sum())} bins the duct occupies "
          f"(+/-{P.DUCT_HALF_ANG:.0f} deg about theta {P.DUCT_THETA:.0f}), at "
          f"any of its {len(pzs)} stations -- so it cannot foul the duct at any "
          f"insertion depth, and the 1.0 mm of x between the lugs and the "
          f"opening plane is not what saves it",
          f"plate vs duct: the plate reaches r {r_duct:.3f} inside the duct's "
          f"sector, where the duct itself comes in to "
          f"{P.R_DUCT_INNER:.2f} -- the lugs are in the cord's way")

    # How far away IS the nearest material, and is it the feature we think?  The
    # first check would also pass on a plate that had lost its lugs entirely, so
    # this one names the corner that is nearest and puts it where it belongs.
    th = bin_centres()
    has = penv.max(axis=0) > 0.0
    off = np.abs((th - P.DUCT_THETA + 180.0) % 360.0 - 180.0)
    near = float(np.min(off[has])) if has.any() else float("nan")
    y_in = P.LUG_Y_O - P.LUG_DEPTH
    want = math.degrees(math.atan2(y_in, P.LUG_X_TOP))
    width = 360.0 / NBIN
    check(abs(near - want) <= width,
          f"plate vs duct: its nearest material to theta 0 sits {near:.2f} deg "
          f"off it -- {near - P.DUCT_HALF_ANG:.1f} deg clear of the duct's own "
          f"edge -- and that is the LUG's inboard corner, x {P.LUG_X_TOP:+.1f}, "
          f"y {y_in:.1f}, which is at {want:.2f} deg.  The nearest feature is "
          f"the one the design says it is",
          f"plate vs duct: its nearest material to theta 0 is at {near:.2f} deg "
          f"and the lug's inboard corner is at {want:.2f} -- something else on "
          f"the plate now reaches further round than the lugs do, and the duct "
          f"margin was reasoned about the wrong feature")

    # And the sweep itself, for completeness: the plate down the BARE tube, at
    # every depth.  Strictly the support is already installed when the plate goes
    # in, so this is the looser of the two constraints -- (4)(e) is the one that
    # decides the fit.  It is here because it is the only check that covers the
    # plate's whole envelope against the whole airframe at once, and because the
    # number it returns is the one to quote if the support is ever taken out and
    # the plate is offered to the tube alone.
    rows = np.ones(len(pzs), bool)
    g, d, z, t = sweep(penv, pzs, free, tzs, rows)
    want_gap = P.R_BEAD_THROAT - P.R_PLATE
    check(g > allow,
          f"plate insertion: the plate clears the bare tube at EVERY depth -- "
          f"worst approach {g:.3f} mm at insertion depth {d:.1f} (plate station "
          f"{z:.1f}, theta {t:.0f}, tube station {z-d:.1f}), against the "
          f"{want_gap:.3f} mm the bead throat {P.R_BEAD_THROAT:.3f} leaves a "
          f"plate of r {P.R_PLATE:.2f}",
          f"plate insertion: the plate fouls the bare tube by {-g:.3f} mm at "
          f"insertion depth {d:.1f}, plate station {z:.1f}, theta {t:.0f} -- so "
          f"it cannot be offered to the tube at all, with or without the "
          f"support in place")


def verify_keying(env, zs, free, tzs) -> None:
    """The half-turn error, and how much rotational tolerance there really is.

    This check has to FAIL to pass.  SCREW_THETA is (90, 270): a half turn maps
    that pair to itself, so a support installed backwards still lines up with the
    airframe's screw holes and nothing about the error is visible at the screws.
    The duct clash is the entire interlock.
    """
    body = zs > P.S_HEAD_AFT
    half = NBIN // 2
    jam = first_jam(env, zs, free, tzs, body, half)
    if jam is None:
        check(False,
              "",
              "keying: installed 180 degrees out the support goes ALL THE WAY IN. "
              "The screws are symmetric under a half turn, so nothing else "
              "catches that error -- the trough's opening must foul the cord "
              "duct and it does not")
        return
    d, g, z, th = jam
    reach = P.S_TAIL - d
    check(d > 100.0,
          f"keying: installed 180 degrees out the shell fouls the cord duct by "
          f"{-g:.2f} mm and stops at insertion depth {d:.1f} -- the tail has "
          f"reached only s {reach:.1f} of {P.S_TAIL:.1f}, so it stands "
          f"{d:.0f} mm proud and cannot be screwed down.  The clash is the "
          f"instruction, and it is the ONLY instruction: SCREW_THETA "
          f"{P.SCREW_THETA} maps to itself under a half turn",
          f"keying: installed 180 degrees out the support still reaches s "
          f"{reach:.1f}, only {d:.1f} mm short -- close enough to force, and "
          f"the screws cannot tell the difference")

    # How much rotational slop is there, really?  The docstring's claim is about
    # the half turn; this is the number it does NOT make, and it matters because
    # the answer is "a lot", which means the duct is a coarse interlock and the
    # fine rotational location is the screws.
    step = max(1, NBIN // 24)
    good = []
    for rb in range(0, NBIN, step):
        g, *_ = sweep(env, zs, free, tzs, body, rb)
        if g > 0.0:
            good.append(rb * 360.0 / NBIN)
    span = [a if a <= 180.0 else a - 360.0 for a in good]
    note(f"the support goes fully home at rotations "
         f"{min(span):+.0f}..{max(span):+.0f} deg about nominal ({len(good)} of "
         f"{NBIN//step} sampled).  So the duct excludes the half turn but not a "
         f"{max(span):.0f} deg misalignment; the two screw holes are what "
         f"locate the rotation finely, and they only bear once the support is "
         f"already close.")


# ------------------------------------------------------------- 8. the payload

CELLS = (
    # (label, x0, x1, y_half, s0, s1) -- the volume each item occupies, sitting
    # on the deck's top face at DECK_X_TOP.  The ESP32's own 3.5 mm of header
    # pin is NOT in its cell; that is the pin-slot volume, checked separately.
    ("BMP280", P.DECK_X_TOP, P.DECK_X_TOP + P.BMP_H,
     P.BMP_W / 2, P.S_BMP_0 + 1.0, P.S_BMP_0 + 1.0 + P.BMP_L),
    ("ESP32", P.DECK_X_TOP, P.DECK_X_TOP + P.ESP32_PCB_T + P.ESP32_H_TOP,
     P.ESP32_W / 2, P.S_ESP32_0 + P.ESP32_CLEAR,
     P.S_ESP32_0 + P.ESP32_CLEAR + P.ESP32_L),
    ("battery", P.DECK_X_TOP, P.DECK_X_TOP + P.BATT_H_MAX,
     P.BATT_W_MAX / 2, P.S_BATT_0, P.S_BATT_0 + P.BATT_L_MAX),
)


def cell_points(x0, x1, y_half, s0, s1, inset=0.4):
    """A grid strictly inside a cell, inset so a coincident face cannot decide it."""
    xs = np.linspace(x0 + inset, x1 - inset, 3)
    ys = np.linspace(-y_half + inset, y_half - inset, 5)
    zs = np.linspace(s0 + inset, s1 - inset, 5)
    return np.array([(x, y, z) for x in xs for y in ys for z in zs])


def verify_payload(m: trimesh.Trimesh) -> None:
    """Each cell is a void the PLATE leaves free, and the loaded plate still fits.

    Every probe here is on the plate's mesh: the payload rides on the plate and
    goes in with it, so the support has nothing to say about whether the ESP32
    fits.  It took an `env, zs` pair when the bay was one part and used neither
    -- the envelope's only appearance was in a check that compared against the
    bead, which was the wrong limit anyway.  See below.
    """
    for label, x0, x1, yh, s0, s1 in CELLS:
        pts = cell_points(x0, x1, yh, s0, s1)
        hit = inside(m, pts)
        n = int(hit.sum())
        where = ("" if n == 0 else
                 f", first at ({pts[hit][0][0]:.1f},{pts[hit][0][1]:.1f},"
                 f"{pts[hit][0][2]:.1f})")
        check(n == 0,
              f"{label}: its {x1-x0:.1f} x {2*yh:.1f} x {s1-s0:.1f} mm cell at "
              f"s {s0:.1f}..{s1:.1f} is clear of plate material "
              f"({len(pts)} points probed)",
              f"{label}: {n} of {len(pts)} points inside its cell hit plate "
              f"material{where} -- the item does not fit where it was placed")

    # The pin-drop volume: the one void doing three jobs.  Probed BELOW the deck,
    # because that is the part of the claim that a slot through the deck alone
    # would not satisfy -- the pins need somewhere to hang.
    pts, why = [], []
    for sign in (-1.0, 1.0):
        y = sign * P.PIN_SLOT_Y
        for x in (P.DECK_X_TOP - 0.4, P.DECK_X_BOT - 1.5, P.DECK_X_BOT - 3.6):
            for z in (P.S_ESP32_0 + 2.0, 100.0, P.S_ESP32_1 - 2.0):
                pts.append((x, y, z))
                why.append(f"pin room at x {x:+.1f}, y {y:+.1f}, s {z:.0f}")
    hit = inside(m, np.array(pts))
    check(not hit.any(),
          f"header pins: all {len(pts)} points in the pin-drop volume are open, "
          f"from the deck's top face down to {P.DECK_X_BOT - 3.6:.1f} -- "
          f"{P.DECK_X_TOP - (P.DECK_X_BOT - 3.6):.1f} mm of room for a "
          f"{P.ESP32_H_BOT:.1f} mm pin, so the board sits flat and the pins are "
          f"not crushed",
          f"header pins: {int(hit.sum())} of {len(pts)} points in the pin-drop "
          f"volume hit material -- the ESP32 cannot sit flat on the deck")

    # ...and the counter-probe, without which the above passes on a deck that
    # was never printed: 4 mm inboard of the slot the deck must be solid.
    expect_points(m, "header pins", [
        ((0.5 * (P.DECK_X_BOT + P.DECK_X_TOP), P.PIN_SLOT_Y - 4.0, 100.0), True,
         "4 mm inboard of the slot the deck is intact, so the slot has edges "
         "for the board to key against"),
    ])

    # LOADED INSERTION, against the two limits it really has.
    #
    # The whole point of loading from the front is that it can be done on the
    # bench.  Raising the deck to DECK_X_TOP -6.0 moved this from comfortable to
    # worth measuring: the tallest item now stands out to x +12.6, three times
    # past the support's opening plane at X_OPEN 4.0.  So a loaded plate is NOT
    # inside the support's C over its whole section -- most of the payload is out
    # in the tube's own bore, through the opening -- and it has to respect two
    # different limits that do not imply one another.
    #
    # This check used to compare against R_BEAD_THROAT, which is the SUPPORT's
    # limit, inherited here by copy when the bay was one part.  The plate is
    # inserted after the support is seated and never meets the bead at all: it
    # goes through the support's HEAD RING, a complete ring of bore R_SHELL_I
    # 27.45, which is 2.42 mm TIGHTER than the bead.  The old check therefore
    # allowed 2.42 mm of payload that would not have gone in.
    tan_d = math.tan(math.radians(P.DUCT_HALF_ANG))
    worst = ("nothing", 0.0, 0.0)          # widest reach overall
    worst_d = ("nothing", 0.0, 0.0, 0.0)   # widest reach INSIDE the duct's sector
    for label, x0, x1, yh, s0, s1 in CELLS:
        r = math.hypot(max(abs(x0), abs(x1)), yh)
        if r > worst[1]:
            worst = (label, r, x1)
        # Within the duct's +/-12 deg the cell is bounded by |y| <= x tan 12, and
        # r grows with both x and |y|, so the extreme point is at the cell's own
        # top face -- where the sector is also widest.  A cell entirely at x <= 0
        # has no point in the sector at all and contributes nothing.
        if x1 > 0.0:
            y_d = min(yh, x1 * tan_d)
            r_d = math.hypot(x1, y_d)
            if r_d > worst_d[1]:
                worst_d = (label, r_d, y_d, x1)

    label, r, x_top = worst
    check(r < P.R_SHELL_I,
          f"loaded insertion: the widest-reaching item is the {label} at "
          f"r {r:.2f} (its far corner, standing to x {x_top:+.1f}, past the "
          f"opening plane at x {P.X_OPEN:.1f}) -- {P.R_SHELL_I - r:.2f} mm "
          f"inside the support's head-ring bore {P.R_SHELL_I:.2f}, which is the "
          f"hole the loaded plate has to pass, so the bay is wired up on the "
          f"bench",
          f"loaded insertion: the {label} reaches r {r:.2f}, past the support's "
          f"head-ring bore {P.R_SHELL_I:.2f} -- the plate will not pass its own "
          f"support's front ring, so the bay would have to be wired up inside "
          f"the tube")

    label_d, r_d, y_d, x_d = worst_d
    check(r_d < P.R_DUCT_INNER,
          f"loaded insertion: inside the duct's +/-{P.DUCT_HALF_ANG:.0f} deg "
          f"the payload reaches only r {r_d:.2f} -- the {label_d}'s top face at "
          f"x {x_d:+.2f}, y {y_d:.2f}, "
          f"where the sector is {2 * y_d:.2f} mm wide -- against the duct's own "
          f"{P.R_DUCT_INNER:.2f}, so {P.R_DUCT_INNER - r_d:.2f} mm clear.  This "
          f"is a SEPARATE limit from the bore above and neither implies the "
          f"other: the item that stands furthest out in x is the one pointing "
          f"straight at the duct",
          f"loaded insertion: the {label_d} reaches r {r_d:.2f} inside the "
          f"duct's sector, against the duct's {P.R_DUCT_INNER:.2f} -- out "
          f"through the support's opening it would hit the shock cord's tunnel "
          f"even though it is well inside the head ring's bore")
    note(f"the plate's own mesh has no material in the duct's sector at all "
         f"(check 5), so the duct margin is entirely a PAYLOAD margin -- it "
         f"lives in this table and in nothing that is drawn, which is why it is "
         f"checked here rather than swept.")

    # And the straps have to clear the items they hold down.
    for label, x0, x1, yh, s0, s1 in CELLS:
        y_slot = (P.STRAP_Y_BMP if label == "BMP280" else P.STRAP_Y_MAIN)
        check(y_slot > yh,
              f"{label}: its tie slots at y +/-{y_slot:.1f} sit outboard of the "
              f"item's own {yh:.2f} mm half-width, so the strap passes over it "
              f"rather than through it",
              f"{label}: its tie slots at y +/-{y_slot:.1f} are inboard of the "
              f"item's {yh:.2f} mm half-width -- the strap cannot get past it")


# --------------------------------------------------------- 9. printability

def verify_printability(m: trimesh.Trimesh, label: str, bed_why: str,
                        area_why: str, total_max: float,
                        ramp_why: str) -> None:
    """The print-orientation claim, checked against the mesh's own normals.

    bay_support.py and bay_plate.py each argue feature by feature that nothing
    overhangs.  That argument is only as good as the geometry that came out, so
    this finds every downward-facing region the mesh actually has, groups the
    connected ones, and asks of each: is it the bed, is it a bridge, or is it an
    overhang that needs support?

    CALLED ONCE PER PART, AND THE PLATE IS HANDED IN ROTATED.  "Downward" here
    means -Z of the mesh as given, so this function only ever answers the
    question about the pose it is shown.  The support prints in the CAD pose --
    forward end down, part axis = build Z -- and is passed straight through.  The
    plate prints FLAT, which is a different solid orientation entirely, so
    main() rotates it first.  Handing the plate in unrotated would ask whether it
    prints standing on its tail, which nobody intends to do and which the answer
    "one 9157 mm2 face on the bed" would hide rather than reveal.

    The three descriptive strings are the part's own account of what SHOULD be
    down there.  They are arguments, not checks, and they are passed in rather
    than written here so that neither part's story can be quietly applied to the
    other -- which is how this function came to tell the support that its first
    layer was "the head's annulus and the deck's forward end" some time after the
    deck had left the part.
    """
    lim = -math.cos(math.radians(OVERHANG_DEG))
    nz = m.face_normals[:, 2]
    dn = nz < lim
    n_dn = int(dn.sum())
    if n_dn == 0:
        check(True, f"{label}: not one downward-facing facet anywhere", "")
        return

    adj = m.face_adjacency
    keep = dn[adj[:, 0]] & dn[adj[:, 1]]
    comps = trimesh.graph.connected_components(adj[keep], nodes=np.where(dn)[0],
                                               min_len=1)
    tri = m.triangles
    area = m.area_faces

    rows = []
    for c in comps:
        c = np.asarray(c)
        v = tri[c].reshape(-1, 3)
        dx = float(v[:, 0].max() - v[:, 0].min())
        dy = float(v[:, 1].max() - v[:, 1].min())
        # span is the NARROW dimension, because that is the direction a slicer
        # bridges in.  The bbox diagonal is the wrong metric here: a D2.5 pilot
        # bored 6.45 mm through a boss has a 6.9 mm diagonal and a 2.5 mm bridge.
        rows.append(dict(n=len(c), area=float(area[c].sum()),
                         span=min(dx, dy), long=max(dx, dy),
                         z0=float(v[:, 2].min()), z1=float(v[:, 2].max())))
    rows.sort(key=lambda d: -d["area"])

    # The bed is whichever region lies wholly on the part's own lowest plane.
    # Partitioned by index rather than by `d not in bed`, which would compare
    # dicts by value and silently drop a second region identical to the first.
    z_bed = float(m.bounds[0, 2])
    on_bed = [i for i, d in enumerate(rows)
              if d["z1"] <= z_bed + 1e-3]
    bed = [rows[i] for i in on_bed]
    rest = [d for i, d in enumerate(rows) if i not in set(on_bed)]

    check(len(bed) == 1,
          f"{label}: one contiguous face on the bed at z {z_bed:.3f}, "
          f"{bed[0]['area'] if bed else 0.0:.1f} mm2 -- {bed_why}",
          f"{label}: {len(bed)} separate regions lie on the bed plane at "
          f"z {z_bed:.3f} -- the part does not have one flat first layer, so it "
          f"has {len(bed)} chances to come off it")

    bad = sorted((d for d in rest if d["span"] > BRIDGE_MAX),
                 key=lambda d: -d["span"])
    total = sum(d["area"] for d in rest)
    # bad[0] is only safe inside the failure branch, and check() builds BOTH
    # messages before it looks at the condition -- so the worst offender is
    # described from a value that exists either way.  See fmt().
    worst = bad[0] if bad else dict(area=0.0, span=0.0, z0=0.0, z1=0.0)
    check(not bad,
          f"{label}: {len(rest)} downward-facing regions off the bed, "
          f"{total:.1f} mm2 in all, and the widest needs a "
          f"{max((d['span'] for d in rest), default=0.0):.2f} mm bridge, inside "
          f"BRIDGE_MAX {BRIDGE_MAX:.1f} -- so it prints with no support at all",
          f"{label}: {len(bad)} downward-facing regions need support -- "
          f"worst is {worst['area']:.1f} mm2 spanning {worst['span']:.1f} mm at "
          f"z {worst['z0']:.1f}..{worst['z1']:.1f}")

    check(total < total_max,
          f"{label}: the total unsupported area is {total:.1f} mm2, under the "
          f"{total_max:.0f} that {area_why}",
          f"{label}: {total:.1f} mm2 of unsupported area is more than the "
          f"{total_max:.0f} that {area_why} -- some surface is overhanging that "
          f"was not meant to")

    # The steepest surface that PASSED, which is the number that says whether the
    # threshold is deciding anything real.  It has to be read off the faces NOT
    # flagged -- nz[dn].min() is what this used to say, and nz.min() is the most
    # NEGATIVE normal in the part (-1.0, a bridge crown), so acos(1.0) reported
    # every ramp as 0.0 deg from horizontal: a note that always printed the same
    # meaningless number no matter what the ramps were drawn at.
    up = nz[(nz >= lim) & (nz < -1e-6)]
    if up.size:
        worst_ok = math.degrees(math.acos(min(1.0, -float(up.min()))))
        note(f"{label}: the shallowest surface that PASSED stands "
             f"{worst_ok:.1f} deg from horizontal -- {ramp_why}.  Nothing at all "
             f"sits between the {OVERHANG_DEG:.0f} deg threshold and that "
             f"{worst_ok:.1f}, so the threshold is not separating this part's "
             f"inclined surfaces from failure by float noise.")
    else:
        note(f"{label}: no surface anywhere is merely inclined -- every facet is "
             f"either upward, vertical, or a flagged bridge")

    for d in rest[:6]:
        note(f"   {label}: bridge {d['area']:6.2f} mm2  span {d['span']:5.2f} x "
             f"{d['long']:5.2f} mm  at build z {d['z0']:7.2f}..{d['z1']:7.2f}")


# ----------------------------------------------------------- 10. the fasteners

def verify_fasteners(free, tzs, n_tube: int, m_seat: trimesh.Trimesh) -> None:
    """What length of screw reaches, through what, and now into WHAT.

    Splitting the bay gave each M3 a second job.  It used to retain the support
    and nothing else, and the only question was whether a stock length crossed
    the airframe, the air gap and the boss.  It now also retains the PLATE, by
    threading into a lug that starts 1.0 mm further in than the boss ends -- so
    the length is decided by the lug, not by the boss, and SCREW_L went from 12
    to 16 for that reason.

    m_seat is the plate translated to WHERE IT ENDS UP.  It has to be, because
    the plate is drawn SLIDE_GAP_Z forward of home and its pilots are drawn at
    S_LUG_PILOT to match: probing the plate as drawn would look for the pilot
    half a millimetre from where the screw is and find solid lug, which is the
    exact failure S_LUG_PILOT exists to prevent, reported as if the pilot were
    missing.
    """
    i = int(round((P.S_SCREW - tzs[0]) / ZSTEP))
    clear = ~in_duct_bins()
    r_bore = float(np.min(free[i][clear]))
    wall = P.R_OD - r_bore
    check(abs(wall - P.WALL_WORK) < 0.15,
          f"screws: at s {P.S_SCREW:.1f} the airframe wall measures "
          f"{wall:.3f} mm, the plain tube's {P.WALL_WORK:.3f} -- not the "
          f"bead's {P.WALL_BEAD_THROAT:.3f} and not the socket's "
          f"{P.WALL_SOCKET:.3f}, which is the wall the shear numbers assume",
          f"screws: at s {P.S_SCREW:.1f} the airframe wall measures "
          f"{wall:.3f} mm against WALL_WORK {P.WALL_WORK:.3f} -- the screw "
          f"lands somewhere other than the plain tube")

    gap = r_bore - P.R_SHELL_O
    grip = P.R_SHELL_O - P.R_BOSS_I
    total = wall + gap + grip
    air = P.R_BOSS_I - P.LUG_Y_O
    to_lug = total + air
    check(abs(to_lug - (P.R_OD - P.LUG_Y_O)) < 0.15,
          f"screws: each M3 crosses {wall:.2f} mm of airframe, {gap:.2f} mm of "
          f"air, {grip:.2f} mm of boss and {air:.2f} mm more air = {to_lug:.2f} "
          f"mm under the head before it reaches the LUG.  An M3 x 12 gets there "
          f"-- it is what the support alone needed -- but with only "
          f"{12.0 - to_lug:.2f} mm left to thread, which is why the plate moved "
          f"SCREW_L to {P.SCREW_L:.0f}",
          f"screws: the measured stack to the lug's outboard face is "
          f"{to_lug:.2f} mm, against the {P.R_OD - P.LUG_Y_O:.2f} mm the "
          f"parameters give -- the airframe wall is not where LUG_Y_O was "
          f"reasoned from")
    note(f"that {gap:.2f} mm of air is real and intended: aft of the bead the "
         f"support is 1.96 mm smaller than the bore, so it is located by the crown "
         f"at the front and these two screws at the back, and by nothing in "
         f"between.  A 2 mm walled trough over 181 mm does not need anything in "
         f"between.")

    # WHERE THE TIP LANDS.  Both of these are one-sided and they oppose each
    # other, which is the only reason the length is interesting: too short and
    # there is no thread in the lug, too long and the tip stands proud of the
    # lug's inboard face into the trough, 16 mm from the ESP32.
    r_tip = P.R_OD - P.SCREW_L
    grip_lug = P.LUG_Y_O - r_tip
    y_in = P.LUG_Y_O - P.LUG_DEPTH
    min_grip = 1.5 * 3.0            # a self-tapper in ABS wants 1.5 diameters
    check(grip_lug >= min_grip,
          f"screws: an M3 x {P.SCREW_L:.0f} puts its tip at r {r_tip:.3f}, so it "
          f"forms {grip_lug:.2f} mm of thread in the lug -- "
          f"{grip_lug/3.0:.1f} diameters, against the {min_grip/3.0:.1f} a "
          f"self-tapper in ABS wants",
          f"screws: an M3 x {P.SCREW_L:.0f} reaches only r {r_tip:.3f} and forms "
          f"{grip_lug:.2f} mm of thread in a lug that starts at "
          f"{P.LUG_Y_O:.1f} -- less than the {min_grip:.1f} mm a self-tapper "
          f"needs, so the plate is held by two screws that will strip")
    check(r_tip > y_in,
          f"screws: and it stops {r_tip - y_in:.2f} mm short of the lug's "
          f"inboard face at r {y_in:.1f} -- the tip stays buried, so nothing "
          f"protrudes into the trough where the boards are",
          f"screws: the tip reaches r {r_tip:.3f}, past the lug's inboard face "
          f"at {y_in:.1f} -- {y_in - r_tip:.2f} mm of M3 stands out into the "
          f"trough.  Shorten SCREW_L or deepen the lug")

    # ...and the same story read off the SEATED mesh, which is the only version
    # of it that can catch a pilot drilled at the wrong station.  Both sides,
    # because a pilot is easy to get right once.
    step = 0.05
    r0 = half_step(y_in - 1.0, step)
    r1 = P.R_BOSS_I - 0.1
    for th in P.SCREW_THETA:
        on_axis = solid_span(m_seat, th, P.S_SCREW, r0, r1, step)
        check(on_axis is None,
              f"screws: at theta {th:.0f}, s {P.S_SCREW:.1f}, the seated plate "
              f"is open along the screw's whole axis from r {r0:.3f} to "
              f"{r1:.2f} -- the lug's pilot, drawn at s {P.S_LUG_PILOT:.1f} and "
              f"arriving here after {P.SLIDE_GAP_Z:.1f} mm of seating, lines up "
              f"with the boss's",
              f"screws: at theta {th:.0f}, s {P.S_SCREW:.1f}, the seated plate "
              f"is SOLID over r {fmt(on_axis, 0)}..{fmt(on_axis, 1)} -- the "
              f"lug's pilot is not on the screw's axis, so the screw would have "
              f"to cut its own way through {fmt(on_axis, 2)} mm of lug")

        # The counter-probe: two millimetres aft, clear of the pilot, the same
        # ray must read the lug's full depth.  Without it the check above also
        # passes on a plate with no lugs at all.
        off = solid_span(m_seat, th, P.S_SCREW + 2.0, r0, r1, step)
        depth = None if off is None else off[2]
        check(depth is not None and abs(depth - P.LUG_DEPTH) <= step,
              f"screws: 2 mm aft of the pilot the same ray reads "
              f"{fmt(off, 0)}..{fmt(off, 1)}, i.e. "
              f"{depth if depth is None else f'{depth:.3f}'} mm of solid lug "
              f"against LUG_DEPTH {P.LUG_DEPTH:.1f} -- so the pilot above is a "
              f"hole in a lug that exists, and the tip's "
              f"{grip_lug:.2f} mm of thread is in material",
              f"screws: 2 mm aft of the pilot the ray reads "
              f"{depth if depth is None else f'{depth:.3f}'} mm of lug against "
              f"LUG_DEPTH {P.LUG_DEPTH:.1f} at theta {th:.0f} -- the lug is not "
              f"the depth the pullout calculation assumed")


# --------------------------------------------------------------------- driver

def main() -> int:
    sup_p, pl_p = OUT / "bay_support.stl", OUT / "bay_plate.stl"
    for p in (sup_p, pl_p, MBODY):
        if not p.exists():
            print(f"missing {p}")
            return 2

    print("=" * 78)
    print("  EXPORTED MESH VERIFICATION -- out/bay_support.stl + "
          "out/bay_plate.stl vs Mbody")
    print("=" * 78)

    sup = load(sup_p)
    plate = load(pl_p)
    tube = load(MBODY)
    tube.apply_translation([0.0, 0.0, -tube.bounds[0, 2]])   # rim at s = 0

    # The plate WHERE IT ENDS UP, which is SLIDE_GAP_Z aft of where it is drawn --
    # the same Pos() bay_assembly.py applies, for the same reason.  Two of the
    # questions below can only be asked in that state: the lug pilots are collinear
    # with the bosses' pilots only when the plate is home, and a probe on the
    # screw's axis through the drawn plate would read the pilot 0.5 mm off and
    # report a missing hole.
    seated = plate.copy()
    seated.apply_translation([0.0, 0.0, P.SLIDE_GAP_Z])

    n_tube = facet_count(tube, 150.0)
    n_sup = facet_count(sup, 100.0)
    # The plate gets arc_facets(), not facet_count(): its section is a chord, so
    # facet_count() would return its floor of 24 and every plate tolerance built
    # from it would be a quarter of a millimetre wide.  See arc_facets().
    n_pl = arc_facets(plate, 100.0, P.R_PLATE - 0.1, P.R_PLATE + 0.1)
    # One allowance per insertion, because the two sweeps are bounded by different
    # surfaces: the support presents its CROWN to the tube, the plate presents its
    # own curved edge at R_PLATE.  Sharing one number would quietly apply the
    # crown's faceting to the plate.
    allow_sup = (2.0 * sagitta(P.R_WORK, n_tube)
                 + 2.0 * sagitta(P.R_CROWN, n_sup))
    allow_pl = (2.0 * sagitta(P.R_WORK, n_tube)
                + 2.0 * sagitta(P.R_PLATE, n_pl))
    note(f"sections resolve {n_tube} azimuths on Mbody, {n_sup} on the support "
         f"and {n_pl} on the plate's curved edge -- so the sweep allowances are "
         f"{allow_sup:.4f} mm for the support and {allow_pl:.4f} for the plate")

    print(f"-- basics, once per printed part")
    verify_basics(sup, "support", CAD_VOL_SUPPORT_CM3, P.S_HEAD_FWD, P.S_TAIL,
                  "the head's forward face, which is where the nose spigot's "
                  "clearance was measured from",
                  "the tail, flush with the end of the trough")
    verify_basics(plate, "plate", CAD_VOL_PLATE_CM3, P.S_PLATE_FWD,
                  P.S_PLATE_AFT,
                  "flush with the support's own forward face, so the plate is "
                  "reachable with a fingernail once it is home",
                  f"SLIDE_GAP_Z {P.SLIDE_GAP_Z:.1f} mm short of the stop at "
                  f"s {P.S_STOP:.1f} ON PURPOSE -- the plate is drawn where it "
                  f"is inserted, not where it seats")

    print(f"-- bay_params.free_radius() against Mbody's own mesh")
    tzs, free = radius_map(tube, 0.0, 260.0, "min")
    verify_free_radius(free, tzs, n_tube)

    print(f"-- features (each probed where it is AND where it is not)")
    verify_features(sup, plate, n_sup, n_pl)

    print(f"-- the slide: the pocket, the chord in it, and the three clearances")
    verify_slide(sup, plate, n_sup, n_pl)

    print(f"-- the support into the tube: insertion, seat and retention")
    zs, env = radius_map(sup, P.S_HEAD_FWD - 0.5, P.S_TAIL + 0.5, "max")
    verify_insertion(env, zs, free, tzs, allow_sup)

    print(f"-- the plate down the tube, past the cord duct")
    pzs, penv = radius_map(plate, P.S_PLATE_FWD - 0.5, P.S_PLATE_AFT + 0.5,
                           "max")
    verify_plate_through_tube(penv, pzs, free, tzs, allow_pl)

    print(f"-- the half-turn error, which has to jam")
    verify_keying(env, zs, free, tzs)

    print(f"-- the payload, which rides on the plate")
    verify_payload(plate)

    print(f"-- the fasteners, into the boss AND the lug")
    verify_fasteners(free, tzs, n_tube, seated)

    print(f"-- printability, once per part IN ITS OWN POSE")
    verify_printability(
        sup, "support print", total_max=50.0,
        bed_why="the head's forward annulus plus the four rail ends, coplanar "
                "with it and overlapping it over r 27.45..27.95 -- that overlap "
                "is what makes it ONE region and not five",
        area_why="the 2 screw pilots' crowns and the stop's two forward faces "
                 "account for",
        ramp_why="the two bosses' ramp cones, drawn at 4.95 mm of radius over "
                 "5.0 mm of station, i.e. 45.3 deg, and reading 0.9 deg "
                 "shallower than that because an 18 deg sector exported in a "
                 "facet or two runs further out in radius than the cone it "
                 "samples -- so the margin here is 0.4 deg of tessellation, not "
                 "1.3 deg of design; see OVERHANG_DEG")

    # Laid over before it is asked, and the transform's determinant is checked
    # rather than trusted -- see FLAT.  A mirrored pose would score identically on
    # every number below and describe the wrong part.
    det = float(np.linalg.det(FLAT[:3, :3]))
    check(abs(det - 1.0) < 1e-12,
          f"the plate's flat pose is a rotation, det {det:+.1f} -- it is the same "
          f"part laid over, not its mirror image",
          f"FLAT has determinant {det:+.1f}: it MIRRORS the plate, so the "
          f"printability result below is about a part that does not exist")
    flat = plate.copy()
    flat.apply_transform(FLAT)
    verify_printability(
        flat, "plate print (flat pose)", total_max=35.0,
        bed_why="the deck's underside, one rectangle 51.7 x 177.2 mm less its "
                "slots -- 9157 mm2 before them",
        area_why="the two lug pilots' crowns account for -- every other hole in "
                 "this part is bored along x, which IS the build axis in this "
                 "pose",
        # Measured, not assumed, and it is NOT the curved edge: _shallow.py puts
        # the shallowest passing facets at part x +0.87, s 200.10 and 201.90,
        # which is x^2 + (s - 201)^2 = 1.25^2 -- the D2.5 lug pilot's own bore,
        # one facet ring outboard of the crown already counted as a bridge above.
        # The curved edge is 738 of the band's 758 mm2 and stands at 72.8..77.2.
        ramp_why="the wall of a lug pilot, one facet ring outboard of the crown "
                 "counted as a bridge above -- this pose has no inclined surface "
                 "of its own at all: the ribs' 45 deg ramps face UP lying flat, "
                 "and the deck's curved edge, which is 738 mm2 of the 758 in the "
                 "band, stands at 72.8..77.2 deg")

    for line in NOTES:
        print(line)
    print("=" * 78)

    n_ok = len([n for n in NOTES if n.startswith("  ok")])
    if n_ok != EXPECT_CHECKS:
        FAILS.append(
            f"the net changed size: {n_ok} checks ran, EXPECT_CHECKS says "
            f"{EXPECT_CHECKS}.  If you added or removed checks on purpose, "
            f"update the constant; if you did not, a check stopped running."
        )

    if FAILS:
        print(f"{len(FAILS)} FAILURES:")
        for f in FAILS:
            print(f"  - {f}")
        return 1
    print(f"all {n_ok} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
