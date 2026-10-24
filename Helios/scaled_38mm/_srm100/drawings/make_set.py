"""Merge the sheet PDFs into SRM100_drawing_set.pdf, in drawing-number order.

Refuses to merge if a sheet is missing or older than the script that draws it
(re-run that dwg_*.py first).
"""

import re
import sys
from pathlib import Path

import srm_dwg as D

HERE = Path(__file__).resolve().parent
OUT = HERE / "SRM100_drawing_set.pdf"
SHEETS = [
    "000_sh1", "000_sh2", "000_sh3", "001",
    "101", "102_sh1", "102_sh2", "103_sh1", "103_sh2", "104", "105", "106",
    "107", "108", "109", "110", "111", "112", "120",
]
FLAT = {"107", "108", "109"}           # drawn through dwg_10x_flat_common.py


def sources(key):
    num, _, sh = key.partition("_")
    own = sorted(HERE.glob(f"dwg_{num}_{sh}_*.py")) if sh else []
    own = own or sorted(HERE.glob(f"dwg_{num}_*.py"))
    extra = [HERE / "dwg_10x_flat_common.py"] if num in FLAT else []
    return own + extra


def main():
    pdfs, bad = [], []
    for key in SHEETS:
        hits = sorted(HERE.glob(f"SRM100-{key}_*.pdf"))
        hits = [p for p in hits if re.match(rf"SRM100-{key}_[a-z]", p.name)]
        if len(hits) != 1:
            bad.append(f"{key}: {len(hits)} PDFs")
            continue
        pdf = hits[0]
        src = sources(key)
        if not src:
            bad.append(f"{key}: no dwg script")
        for s in src:
            if s.stat().st_mtime > pdf.stat().st_mtime:
                bad.append(f"{pdf.name} is older than {s.name}")
        pdfs.append(pdf)
    if bad:
        sys.exit("not merged:\n  " + "\n  ".join(bad))
    D.merge_pdfs(pdfs, OUT)
    print(f"{OUT.name}: {len(pdfs)} sheets")
    for p in pdfs:
        print("  ", p.name)


if __name__ == "__main__":
    main()
