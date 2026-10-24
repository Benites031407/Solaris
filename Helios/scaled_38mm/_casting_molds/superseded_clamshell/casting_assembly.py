"""One BATES segment set up for casting, as used (z = 0 on the table).  Reference only.

  silicone base on the table, sleeve pushed up through it until flush with its underside,
  casting tube in the base (bottom end on the floor), grain, silicone cap over the tube top
  and the sleeve; aluminium rod down the sleeve, standing on the table.
The sleeve comes out of its mold with the rod 16 mm proud of the pour end (the mold seats
the rod's foot below the molded tip): slide the rod through the sleeve until it's flush with
the pour end, so it stands 22 mm out of the tip.  That's the position modelled here.
The base and cap holes grip the sleeve with 0.1 radial interference: that overlap is the
fit, not a clash.
"""

import mold_params as P
from build123d import Compound
from mold_build import finish, tube
from silicone_pieces import Z_GRAIN0, base_piece, cap_piece, sleeve_piece

GRIP = {frozenset(("silicone_base", "silicone_sleeve")), frozenset(("silicone_cap", "silicone_sleeve"))}


def parts(seg=P.L_SEG):
    z1 = Z_GRAIN0 + seg
    return {
        "silicone_base": (base_piece(), (0.85, 0.30, 0.30)),
        "silicone_sleeve": (sleeve_piece(), (0.90, 0.45, 0.35)),
        "casting_tube": (tube(P.D_GRAIN / 2.0, P.R_BOSS, Z_GRAIN0, z1), (0.75, 0.62, 0.40)),
        "grain": (tube(P.D_CORE / 2.0, P.D_GRAIN / 2.0, Z_GRAIN0, z1), (0.95, 0.95, 0.85)),
        "silicone_cap": (cap_piece(z1), (0.85, 0.30, 0.30)),
        "core_rod": (tube(0.0, P.D_ROD / 2.0, 0.0, P.L_ROD_MIN), (0.70, 0.72, 0.75)),
    }


def gen_step():
    kids = [finish(s, name, rgb) for name, (s, rgb) in parts().items()]
    return Compound(children=kids, label="bates_segment_casting")


if __name__ == "__main__":
    for seg in (P.L_SEG, P.L_SEG_MAX):
        ps = {k: v[0] for k, v in parts(seg).items()}
        names = list(ps)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                v = ps[a].intersect(ps[b])
                vol = sum(s.volume for s in v.solids()) if v else 0.0
                if vol > 1e-3:
                    tag = "grip" if frozenset((a, b)) in GRIP else "INTERFERENCE"
                    print(f"L {seg}: {tag} {a} x {b}: {vol:.1f} mm3")
        stick = P.L_SLEEVE - (Z_GRAIN0 + seg + P.CAP_TOP)
        print(f"L {seg}: grain {ps['grain'].volume / 1000:.2f} cm3 = {P.grain_mass_g(seg):.1f} g, "
              f"sleeve {stick:.1f} mm above the cap")
