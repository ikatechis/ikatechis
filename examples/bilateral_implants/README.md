# Bilateral Implants Example

Two posterior implants with slight angulation and inspection windows.

## Clinical Scenario

- **Teeth**: #36 and #46 (bilateral first molars)
- **Indication**: Bilateral molar replacement
- **Implants**: 2× (4.1mm × 10mm)
- **Direction**: Slight buccal angulation (~6-8°)
- **Complexity**: Intermediate
- **Features**: Inspection windows for multi-implant verification

## Files

- `implants.json` - Implant site configuration
- `README.md` - This file

## Quick Start

### Generate the guide

```bash
surgical-guide --implants implants.json --output guide.stl
```

### Expected output

```
Loading implant sites from: implants.json
Loaded 2 implant site(s)

Generating surgical guide...

✓ Guide generated successfully!
  Output: guide.stl
  Volume: ~13,000-14,000 mm³
  Faces: ~400-600
  Watertight: True
```

## Configuration Details

### Implant Site #36 (Right)

```json
{
  "site_id": "36",
  "position": [25.5, -12.3, 8.7],        // Right posterior
  "direction": [0.0, 0.1, -0.995],       // ~6° buccal angle
  "implant_diameter": 4.1,
  "implant_length": 10.0,
  "sleeve_outer_diameter": 5.0,
  "sleeve_inner_diameter": 4.0,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Implant Site #46 (Left)

```json
{
  "site_id": "46",
  "position": [-24.8, -11.9, 9.1],       // Left posterior
  "direction": [0.0, 0.08, -0.997],      // ~5° buccal angle
  "implant_diameter": 4.1,
  "implant_length": 10.0,
  "sleeve_outer_diameter": 5.0,
  "sleeve_inner_diameter": 4.0,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Clinical Notes

- **Separation**: ~50mm between implants (realistic molar spacing)
- **Angulation**: Slight buccal tilt (6-8°) for anatomical considerations
- **Symmetry**: Nearly symmetric but with slight variations
- **Inspection windows**: Automatically added between implants

## Key Features

### Inspection Windows

With multiple implants, the generator automatically adds inspection windows between sites for visual verification during surgery.

**Purpose**:
- Verify proper seating on tissue surface
- Check guide stability
- Confirm correct positioning during drilling

**Location**: Perpendicular to implant axis, on buccal side

### Disable windows

```bash
surgical-guide --implants implants.json --output guide.stl --no-windows
```

### Adjust window size

```bash
surgical-guide --implants implants.json --output guide.stl --window-width 15.0
```

## Customization Examples

### Larger guide for better stability

```bash
surgical-guide --implants implants.json --output guide.stl \
  --extents 60 35 12
```

### Thicker guide for strength

```bash
surgical-guide --implants implants.json --output guide.stl \
  --thickness 3.0
```

### Custom tissue gap

```bash
surgical-guide --implants implants.json --output guide.stl \
  --tissue-gap 0.2
```

### Verbose output

```bash
surgical-guide --implants implants.json --output guide.stl --verbose
```

Output includes:
```
Configuration:
  Thickness: 2.5mm
  Tissue gap: 0.15mm
  Inspection windows: True
  Guide extents: [50.0, 30.0, 10.0]

  - Site 36: position=[25.5, -12.3, 8.7]
  - Site 46: position=[-24.8, -11.9, 9.1]
```

## Python API Usage

```python
from surgical_guide_generator import generate_surgical_guide, GuideConfig
from surgical_guide_generator.cli import load_implant_sites_from_json

# Load sites from JSON
sites = load_implant_sites_from_json("implants.json")

# Custom configuration
config = GuideConfig(
    thickness=3.0,
    tissue_gap=0.2,
    add_inspection_windows=True,
    window_width=12.0,
)

# Generate guide
result = generate_surgical_guide(
    guide_body_extents=[60, 35, 12],
    implant_sites=sites,
    output_path="guide.stl",
    config=config,
)

if result.success:
    print(f"Generated guide with {len(sites)} implants")
    print(f"Volume: {result.metrics['final_volume_mm3']:.1f} mm³")
    print(f"Watertight: {result.metrics['is_watertight']}")
```

## What You'll Get

### Guide Features

- ✅ Two precisely positioned sleeve channels
- ✅ Inspection windows between implants
- ✅ Anatomically realistic spacing (~50mm)
- ✅ Slight angulation (6-8° buccal)
- ✅ Watertight mesh ready for 3D printing

### Geometric Properties

- **Guide dimensions**: 50mm × 30mm × 10mm (default)
- **Guide volume**: ~13,000-14,000 mm³
- **Mesh complexity**: ~400-600 faces
- **Watertight**: Yes (guaranteed)
- **Inspection windows**: 2 (default)

## Clinical Workflow

### 1. Pre-operative Planning
- CBCT scan acquisition
- Virtual implant planning
- Extract positions and directions
- Create JSON configuration

### 2. Guide Generation
```bash
surgical-guide --implants implants.json --output guide.stl --verbose
```

### 3. 3D Printing
- Import STL to slicer
- Use biocompatible resin
- 0.1mm layer height
- 100% infill

### 4. Post-processing
- Remove supports
- Clean and cure
- Sterilize per protocol

### 5. Surgical Use
- Seat guide on tissue
- Verify through inspection windows
- Sequential drilling at both sites
- Place implants

## Understanding the Geometry

### Position Coordinates

```
Site #36: [25.5, -12.3, 8.7]
Site #46: [-24.8, -11.9, 9.1]

X-axis: Left (-) to Right (+)
Y-axis: Posterior (-) to Anterior (+)
Z-axis: Inferior (0) to Superior (+)
```

### Direction Vectors

```
Site #36: [0.0, 0.1, -0.995]  →  ~6° buccal angulation
Site #46: [0.0, 0.08, -0.997] →  ~5° buccal angulation

Components:
- X: Medial-lateral tilt
- Y: Anterior-posterior tilt (slight buccal)
- Z: Vertical component (negative = apical direction)
```

Vectors are automatically normalized by the system.

## Expected Results

### File Sizes

- **STL**: ~30-50 KB
- **3MF**: ~20-35 KB (compressed)

### Processing Time

- **Generation**: 2-5 seconds
- **Validation**: <1 second
- **Export**: <1 second
- **Total**: 3-7 seconds

### Validation Checks

All automatically performed:

- ✅ Watertight mesh
- ✅ Positive volume
- ✅ No self-intersections
- ✅ Proper face orientation
- ✅ Valid channel placement
- ✅ Window geometry correct

## Troubleshooting

### Implants too close together
Edit positions in `implants.json` to increase separation:
```json
"position": [30.0, -12.3, 8.7],  // Increase X distance
```

### Windows too small/large
Adjust window width:
```bash
--window-width 15.0  # Larger windows
--window-width 8.0   # Smaller windows
```

### Guide doesn't fit anatomy
This example uses a simple box placeholder. Future versions will support:
- IOS mesh loading
- SDF-based anatomical shell generation

For now, adjust guide extents:
```bash
--extents 70 40 15  # Larger guide body
```

### Wrong angulation
Check direction vectors in JSON:
- Should be unit vectors (auto-normalized)
- Negative Z component for apical direction
- Small Y component for buccal tilt

## Advanced Modifications

### Change implant sizes

Edit `implants.json`:
```json
{
  "site_id": "36",
  "implant_diameter": 4.8,              // Wide implant
  "sleeve_outer_diameter": 5.5,         // Matching sleeve
  "sleeve_inner_diameter": 4.5,         // Matching drill guide
  ...
}
```

### Add third implant

Add to `implant_sites` array:
```json
{
  "site_id": "37",
  "position": [30.0, -18.5, 8.5],
  "direction": [0.0, 0.09, -0.996],
  "implant_diameter": 4.1,
  "implant_length": 8.0,
  "sleeve_outer_diameter": 5.0,
  "sleeve_inner_diameter": 4.0,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

## Next Steps

1. **Try the full arch example**: See `../full_arch/` for 4-implant case
2. **Modify positions**: Edit JSON to match your anatomy
3. **Experiment with parameters**: Try different thickness, gaps, window sizes
4. **3D print**: Use the STL in your slicer software

## References

- Van Assche et al. (2012) - Accuracy of computer-aided implant placement
- [USAGE.md](../../docs/USAGE.md) - Complete CLI reference
- [Project README](../../SURGICAL_GUIDE_README.md) - Full documentation
- [Full Arch Example](../full_arch/) - More complex case
