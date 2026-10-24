"""
Body Tube — base structural geometry.
Derived from: BodyTube:Body Tube, TrapezoidFinSet:Fins (fused),
              CenteringRing:Forward (absorbed), CenteringRing:Aft (absorbed)
Pass 1 (generate-structures): base shell only, no modifications.
"""
import math
from build123d import *
from build123d import import_svg
from pathlib import Path

# --- Parameters (from manifest) ---
LENGTH_MM = 800.0
OD_MM = 127.0
ID_MM = 101.6

# Fin parameters (fused, from TrapezoidFinSet)
FIN_COUNT = 4
FIN_ROOT_MM = 280.0
FIN_TIP_MM = 100.0
FIN_SPAN_MM = 120.0
FIN_SWEEP_MM = 180.0
FIN_THICK_MM = 12.7  # dfam_thickness_mm (printed thickness)
FIN_FILLET_MM = 3.0  # root fillet
FIN_EDGE_FILLET_MM = 1.0  # leading/trailing/tip edge rounding
FIN_ROOT_INSET_MM = 1.0  # fin root penetrates wall by this much

# Wall thickening parameters (absorbed centering rings)
# Motor mount tube: 355mm long, 41.529mm OD, positioned at aft end
MOTOR_MOUNT_OD_MM = 41.529  # 1.635" per user spec
MOTOR_MOUNT_LEN_MM = 355.0
RING_THICKNESS_MM = 6.0  # centering ring thickness
# Motor mount region starts at this Z (fore=0, aft=LENGTH)
MOUNT_Z_START = LENGTH_MM - MOTOR_MOUNT_LEN_MM  # 445mm
# Forward ring: at start of motor mount region
FWD_RING_Z = MOUNT_Z_START
# Aft ring: at aft end of body tube
AFT_RING_Z = LENGTH_MM - RING_THICKNESS_MM

# Baffle parameters
BAFFLE_HEIGHT_MM = 38.1  # 1.5 inches
BAFFLE_OD_MM = ID_MM  # fills the body tube bore (101.6mm)
BAFFLE_Z_START = MOUNT_Z_START - BAFFLE_HEIGHT_MM  # sits just forward of motor mount wall
EYEBOLT_HOLE_DIA_MM = 8.5  # clearance hole for 5/16"-18 eyebolt
EYEBOLT_THREAD_LEN_MM = 23.876  # 0.94 inches
# Arc slot parameters
SLOT_COUNT = 3
SLOT_INNER_R_MM = 12.0  # inner radius of arc slots
SLOT_OUTER_R_MM = MOTOR_MOUNT_OD_MM / 2  # outer radius matches motor mount bore (20.76mm)
SLOT_ARC_DEG = 80.0  # each slot spans 80 degrees

# Rail button heat-set insert holes
HEAT_INSERT_DIA_MM = 4.8  # slightly under 5mm OD for press-in
HEAT_INSERT_DEPTH_MM = 4.0  # M3 5x4 insert length
# Rail button Z positions in body tube frame (body tube starts 350mm from nose)
RAIL_FWD_Z_MM = 875.0 - 350.0  # 525mm
RAIL_AFT_Z_MM = 1115.0 - 350.0  # 765mm
RAIL_HOLE_ANGLES = [45, 135, 225, 315]  # between fins (fins at 0/90/180/270)

# Channel parameters — runs axially between rail button rows
# Angular extent: between adjacent fins, 5mm clearance from each fillet
# At OD/2=63.5mm, fin+fillet spans ~8.5° each side. 5mm clearance ≈ 4.5°.
# So channel spans from ~13° to ~77° (centered at 45°), about 64° wide.
CHANNEL_HALF_ARC_DEG = 32.0  # half of the channel angular width
CHANNEL_INNER_R_MM = MOTOR_MOUNT_OD_MM / 2 + 0.5  # just touching motor mount, not cutting in
CHANNEL_OUTER_R_MM = OD_MM / 2  # from outer surface
CHANNEL_Z_PAD_MM = 25.0  # padding around heat insert holes
CHANNEL_ANGLES = [45, 225]  # opposite sides of the body tube

# --- Resolve output path ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STEP_DIR = PROJECT_ROOT / "cadsmith" / "step"
OUTPUT = STEP_DIR / "body_tube.step"

# --- Build ---
# Fin geometry: trailing edge flush with aft end of body tube.
# Fore face at Z=0, aft face at Z=LENGTH_MM.
# Fin root trailing edge at Z=LENGTH_MM, root leading edge at Z=LENGTH_MM - FIN_ROOT_MM.
# Sweep is applied to the leading edge of the tip chord.
FIN_Z_START = LENGTH_MM - FIN_ROOT_MM  # leading edge root Z position
FIN_R_ROOT = OD_MM / 2 - FIN_ROOT_INSET_MM  # root sits slightly inside wall
FIN_R_TIP = OD_MM / 2 + FIN_SPAN_MM  # tip at full span from OD

# Fin profile points (in XZ plane, X=radial, Z=axial)
# Walk: root leading edge -> tip leading edge -> tip trailing edge -> root trailing edge -> close
fin_profile = [
    (FIN_R_ROOT, FIN_Z_START),                              # root leading edge
    (FIN_R_TIP, FIN_Z_START + FIN_SWEEP_MM),                # tip leading edge
    (FIN_R_TIP, FIN_Z_START + FIN_SWEEP_MM + FIN_TIP_MM),   # tip trailing edge
    (FIN_R_ROOT, FIN_Z_START + FIN_ROOT_MM),                 # root trailing edge
]

with BuildPart() as airframe:
    # 1. Hollow cylinder
    with BuildSketch(Plane.XY):
        Circle(OD_MM / 2)
        Circle(ID_MM / 2, mode=Mode.SUBTRACT)
    extrude(amount=LENGTH_MM)

    # 2. Integrated fins — build one, polar array
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline(*fin_profile, close=True)
        make_face()
    extrude(amount=FIN_THICK_MM / 2, both=True, mode=Mode.ADD)

    # Polar array the fin (we built one, need 3 more)
    fin_solid = airframe.solids()[-1]  # the just-extruded fin
    for i in range(1, FIN_COUNT):
        add(fin_solid.rotate(Axis.Z, i * 360 / FIN_COUNT), mode=Mode.ADD)

    # 3. Baffle — solid disc just forward of motor mount region
    with BuildSketch(Plane.XY.offset(BAFFLE_Z_START)):
        Circle(BAFFLE_OD_MM / 2)
    extrude(amount=BAFFLE_HEIGHT_MM, mode=Mode.ADD)

    # 4. Wall thickening — continuous thick wall in motor mount region
    # One solid annulus from body ID down to motor mount OD, spanning
    # the full motor mount length (445mm to 800mm)
    with BuildSketch(Plane.XY.offset(MOUNT_Z_START)):
        Circle(ID_MM / 2)
        Circle(MOTOR_MOUNT_OD_MM / 2, mode=Mode.SUBTRACT)
    extrude(amount=MOTOR_MOUNT_LEN_MM, mode=Mode.ADD)

    # 4. All fin fillets in a single pass to avoid OCC topology conflicts
    body_r = OD_MM / 2
    root_fillet_r = min(FIN_FILLET_MM, min(FIN_THICK_MM / 2 * 0.9, 3.0))

    # Root edges: Z-parallel edges on the body OD surface within fin Z range
    z_parallel_edges = airframe.edges().filter_by(Axis.Z)
    fin_root_edges = [
        e for e in z_parallel_edges
        if abs(math.sqrt(e.center().X ** 2 + e.center().Y ** 2) - body_r) < 0.5
        and FIN_Z_START < e.center().Z < FIN_Z_START + FIN_ROOT_MM
        and 1.0 < e.length < FIN_ROOT_MM
    ]

    # Outer edges: leading, trailing, tip edges well beyond the body tube
    all_edges = airframe.edges()
    fin_outer_edges = [
        e for e in all_edges
        if math.sqrt(e.center().X ** 2 + e.center().Y ** 2) > body_r + 10.0
        and e.length > 50.0
    ]

    # Apply root fillets
    if fin_root_edges:
        fillet(fin_root_edges, radius=root_fillet_r)

    # Apply edge fillets separately with chamfer as fallback
    if fin_outer_edges:
        try:
            fillet(fin_outer_edges, radius=FIN_EDGE_FILLET_MM)
        except ValueError:
            chamfer(fin_outer_edges, length=FIN_EDGE_FILLET_MM)

    # 7. Baffle center hole — clearance for 5/16"-18 eyebolt
    with BuildSketch(Plane.XY.offset(BAFFLE_Z_START)):
        Circle(EYEBOLT_HOLE_DIA_MM / 2)
    extrude(amount=BAFFLE_HEIGHT_MM, mode=Mode.SUBTRACT)

    # 8. Baffle arc slots — 3 annular sector gas-through openings
    for i in range(SLOT_COUNT):
        angle_start = i * (360.0 / SLOT_COUNT) + 10  # 10° offset from webs
        angle_end = angle_start + SLOT_ARC_DEG
        a0 = math.radians(angle_start)
        a1 = math.radians(angle_end)
        amid = math.radians((angle_start + angle_end) / 2)
        # Four corners of the annular sector
        ir, orr = SLOT_INNER_R_MM, SLOT_OUTER_R_MM
        with BuildSketch(Plane.XY.offset(BAFFLE_Z_START)):
            with BuildLine():
                # Inner arc (start to end)
                ThreePointArc(
                    (ir * math.cos(a0), ir * math.sin(a0)),
                    (ir * math.cos(amid), ir * math.sin(amid)),
                    (ir * math.cos(a1), ir * math.sin(a1)),
                )
                # Radial line: inner end to outer end
                Line(
                    (ir * math.cos(a1), ir * math.sin(a1)),
                    (orr * math.cos(a1), orr * math.sin(a1)),
                )
                # Outer arc (end back to start)
                ThreePointArc(
                    (orr * math.cos(a1), orr * math.sin(a1)),
                    (orr * math.cos(amid), orr * math.sin(amid)),
                    (orr * math.cos(a0), orr * math.sin(a0)),
                )
                # Radial line: outer start to inner start (close)
                Line(
                    (orr * math.cos(a0), orr * math.sin(a0)),
                    (ir * math.cos(a0), ir * math.sin(a0)),
                )
            make_face()
        extrude(amount=BAFFLE_HEIGHT_MM, mode=Mode.SUBTRACT)

    # 9. Rail button heat-set insert holes — radial blind holes at both Z positions, 4 sides
    for z_pos in [RAIL_FWD_Z_MM, RAIL_AFT_Z_MM]:
        for angle_deg in RAIL_HOLE_ANGLES:
            angle_rad = math.radians(angle_deg)
            # Normal pointing inward (radial direction)
            nx = math.cos(angle_rad)
            ny = math.sin(angle_rad)
            # Sketch plane on the outer surface, normal pointing inward
            hole_plane = Plane(
                origin=(nx * OD_MM / 2, ny * OD_MM / 2, z_pos),
                x_dir=(0, 0, 1),
                z_dir=(-nx, -ny, 0),
            )
            with BuildSketch(hole_plane):
                Circle(HEAT_INSERT_DIA_MM / 2)
            extrude(amount=HEAT_INSERT_DEPTH_MM, mode=Mode.SUBTRACT)

    # 10. Rectangular channels between rail button rows — 45° and 135° only
    channel_z_start = 650.0
    channel_z_len = 175.0
    # Channel width: span between adjacent fins minus 5mm clearance each side
    # At OD surface, fin+fillet spans ~17mm wide. Gap between fins at 45° ≈
    # 2 * OD/2 * sin(45°) - 17mm ≈ 90 - 17 = 73mm. Minus 10mm clearance = 63mm.
    # Use a fixed width that's safe.
    CHANNEL_WIDTH_MM = 60.0
    CHANNEL_DEPTH_MM = CHANNEL_OUTER_R_MM - CHANNEL_INNER_R_MM  # radial depth
    for angle_deg in CHANNEL_ANGLES:
        angle_rad = math.radians(angle_deg)
        # Sketch plane on the outer surface, normal pointing inward
        nx = math.cos(angle_rad)
        ny = math.sin(angle_rad)
        # Plane oriented: Z points inward radially, X points along the tube axis
        channel_plane = Plane(
            origin=(nx * CHANNEL_OUTER_R_MM, ny * CHANNEL_OUTER_R_MM, channel_z_start),
            x_dir=(0, 0, 1),
            z_dir=(-nx, -ny, 0),
        )
        with BuildSketch(channel_plane):
            # Slot shape: semicircular forward end, flat aft end (clips past body tube)
            # Extend aft by half-width so the aft semicircle is past the aft face
            SlotOverall(channel_z_len + CHANNEL_WIDTH_MM / 2, CHANNEL_WIDTH_MM,
                        rotation=0)
            # Shift aft so forward arc starts at channel_z_start
            # SlotOverall is centered, so shift by +CHANNEL_WIDTH_MM/4
        extrude(amount=CHANNEL_DEPTH_MM, mode=Mode.SUBTRACT)

# --- Text + Icon debossing — "BIG HEAVY 2" with Clawd icon, vertical on non-slot sides ---
# Wrapped around the cylinder with uniform 1mm depth using shell intersection
TEXT_WORDS = ["BIG", "HEAVY", "2"]
TEXT_FONT_SIZE_MM = 60.0
TEXT_DEBOSS_MM = 1.0
TEXT_ANGLES = [135, 315]
TEXT_Z_CENTER = LENGTH_MM / 2 - 100  # shifted 100mm forward
TEXT_WORD_GAP_MM = 40.0  # gap between words

# Icon parameters
ICON_SVG_PATH = SCRIPT_DIR / "claudecode.svg"
ICON_SIZE_MM = 60.0  # match text height
ICON_SVG_SIZE = 24.0  # SVG viewBox is 24x24
ICON_SCALE = ICON_SIZE_MM / ICON_SVG_SIZE
ICON_GAP_MM = 15.0  # gap between icon and text
# Icon goes above (forward of) the text — lower Z since fore=Z=0
ICON_Z_CENTER = TEXT_Z_CENTER - 255  # 10mm more forward

result = airframe.part

# Build a 1mm thick cylindrical shell for intersection
with BuildPart() as deboss_shell:
    with BuildSketch(Plane.XY):
        Circle(OD_MM / 2 + 0.1)
        Circle(OD_MM / 2 - TEXT_DEBOSS_MM, mode=Mode.SUBTRACT)
    extrude(amount=LENGTH_MM)

for angle_deg in TEXT_ANGLES:
    angle_rad = math.radians(angle_deg)
    nx = math.cos(angle_rad)
    ny = math.sin(angle_rad)

    # --- Text (per-word to avoid boolean artifacts) ---
    # Estimate character width (~0.6 × font_size for proportional font)
    char_w = TEXT_FONT_SIZE_MM * 0.6
    # Calculate total text length including gaps
    word_lengths = [len(w) * char_w for w in TEXT_WORDS]
    total_len = sum(word_lengths) + (len(TEXT_WORDS) - 1) * TEXT_WORD_GAP_MM
    # Starting Z for first word (centered around TEXT_Z_CENTER)
    z_cursor = TEXT_Z_CENTER - total_len / 2

    for word, wlen in zip(TEXT_WORDS, word_lengths):
        word_z = z_cursor + wlen / 2  # center of this word
        word_plane = Plane(
            origin=(0, 0, word_z),
            x_dir=(0, 0, 1),
            z_dir=(nx, ny, 0),
        )
        with BuildPart() as text_block:
            with BuildSketch(word_plane):
                Text(word, font_size=TEXT_FONT_SIZE_MM, font="Hiragino Sans W6",
                     align=(Align.CENTER, Align.CENTER), rotation=0)
            extrude(amount=OD_MM / 2 + 5)
        text_on_surface = text_block.part & deboss_shell.part
        result = result - text_on_surface
        z_cursor += wlen + TEXT_WORD_GAP_MM

    # --- Clawd Icon ---
    icon_plane = Plane(
        origin=(0, 0, ICON_Z_CENTER),
        x_dir=(0, 0, 1),
        z_dir=(nx, ny, 0),
    )
    with BuildPart() as icon_block:
        with BuildSketch(icon_plane):
            icon_faces = import_svg(str(ICON_SVG_PATH))
            for face in icon_faces:
                # Scale and center the icon
                scaled = face.scale(ICON_SCALE)
                # Center it (SVG origin is top-left, shift by -size/2)
                centered = scaled.move(Location((-ICON_SIZE_MM / 2, -ICON_SIZE_MM / 2, 0)))
                add(centered)
        extrude(amount=OD_MM / 2 + 5)
    icon_on_surface = icon_block.part & deboss_shell.part
    result = result - icon_on_surface

# --- Export ---
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
export_step(result, str(OUTPUT))
