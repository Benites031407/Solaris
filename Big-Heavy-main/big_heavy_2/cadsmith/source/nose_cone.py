"""
Nose Cone — base structural geometry.
Derived from: NoseCone:Nose Cone
Pass 1 (generate-structures): base shell only, no modifications.
"""
import math
from build123d import *
from pathlib import Path

# --- Parameters (from manifest) ---
NOSE_LEN_MM = 350.0
BASE_OD_MM = 127.0
SHOULDER_OD_MM = 101.6
SHOULDER_LEN_MM = 30.0

# --- Resolve output path ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STEP_DIR = PROJECT_ROOT / "cadsmith" / "step"
OUTPUT = STEP_DIR / "nose_cone.step"

# --- Ellipsoid profile ---
BASE_R_MM = BASE_OD_MM / 2

def outer_r(z_from_base: float) -> float:
    # Half-ellipse: r(z) = R * sqrt(1 - (z/L)^2)
    return BASE_R_MM * math.sqrt(max(1 - (z_from_base / NOSE_LEN_MM) ** 2, 0.0))

N_SAMPLES = 80  # more samples for smoother curve
profile = [(0.0, SHOULDER_LEN_MM), (BASE_R_MM, SHOULDER_LEN_MM)]
for i in range(1, N_SAMPLES + 1):
    # Cosine spacing: denser near the tip (i=N_SAMPLES) where curvature is highest
    t = 0.5 * (1 - math.cos(math.pi * i / N_SAMPLES))
    z_from_base = t * NOSE_LEN_MM
    profile.append((outer_r(z_from_base), SHOULDER_LEN_MM + z_from_base))
profile[-1] = (0.0, SHOULDER_LEN_MM + NOSE_LEN_MM)

# Eyebolt hole parameters
EYEBOLT_HOLE_DIA_MM = 8.5  # clearance for 5/16"-18
EYEBOLT_HOLE_DEPTH_MM = 23.876  # 0.94" thread length

with BuildPart() as nose_cone:
    # 1. Solid shoulder (print-bed face at Z=0)
    with BuildSketch(Plane.XY):
        Circle(SHOULDER_OD_MM / 2)
    extrude(amount=SHOULDER_LEN_MM)
    # 2. Ogive revolved above shoulder
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline(*profile, close=True)
        make_face()
    revolve(axis=Axis.Z, mode=Mode.ADD)
    # 3. Eyebolt hole from the bottom face (Z=0) into the shoulder
    with BuildSketch(Plane.XY):
        Circle(EYEBOLT_HOLE_DIA_MM / 2)
    extrude(amount=EYEBOLT_HOLE_DEPTH_MM, mode=Mode.SUBTRACT)

# --- Export ---
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
export_step(nose_cone.part, str(OUTPUT))
