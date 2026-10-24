"""Contact sheet of a shot at a few instants, to check framing before rendering.

    python preview.py --shot stack --at 0 0.35 0.6 1.0
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

import shots as SH
import stack as S

ap = argparse.ArgumentParser()
ap.add_argument("--shot", default="stack")
ap.add_argument("--at", type=float, nargs="+", default=[0.0, 0.35, 0.7, 1.0])
ap.add_argument("--width", type=int, default=760)
ap.add_argument("--ss", type=int, default=2)
a = ap.parse_args()

SH.TOTAL_Z = S.stations()[-1][4]
secs = SH._sections()
W = a.width
H = int(round(W * 9 / 16))
dur = SH.DURATIONS[a.shot]

ims = []
for frac in a.at:
    t = frac * dur
    if a.shot == "stack":
        bodies, cam, sec = SH.shot_stack(t, dur, secs)
    elif a.shot == "bay":
        bodies, cam, sec = SH.shot_bay(t, dur)
    elif a.shot == "nose":
        bodies, cam, sec = SH.shot_nose(t, dur)
    else:
        bodies, cam, sec = SH.shot_hero(t, dur, secs)
    v, c, ids = SH.tris(bodies, sec)
    img, zb, ib = SH.raster(v, c, ids, cam, W * a.ss, H * a.ss)
    img = SH.outline(img, zb, ib)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    im = im.resize((W, H), Image.LANCZOS)
    ims.append(im)
    print(f"  {a.shot} u={frac}")

cols = 2
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, H * rows), (10, 12, 15))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
p = Path(__file__).resolve().parent / f"_preview_{a.shot}.png"
sheet.save(p)
print("wrote", p, sheet.size)
