"""
Motor Mount Tube — base structural geometry.
Derived from: InnerTube:Motor Mount Tube
Pass 1 (generate-structures): base shell only, no modifications.
"""
from build123d import *
from pathlib import Path

# --- Parameters (from manifest) ---
LENGTH_MM = 355.0
OD_MM = 41.529  # 1.635" per user spec
ID_MM = 38.735  # 1.525" per user spec

# --- Resolve output path ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STEP_DIR = PROJECT_ROOT / "cadsmith" / "step"
OUTPUT = STEP_DIR / "motor_mount_tube.step"

# --- Build ---
with BuildPart() as part:
    with BuildSketch(Plane.XY):
        Circle(OD_MM / 2)
        Circle(ID_MM / 2, mode=Mode.SUBTRACT)
    extrude(amount=LENGTH_MM)

# --- Export ---
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
export_step(part.part, str(OUTPUT))
