# Full Arch Restoration Example

Multiple implants for full arch restoration with varied angulations.

## Clinical Scenario

- **Teeth**: #33, #36, #43, #46 (bilateral canines and molars)
- **Indication**: 4-implant supported denture (All-on-4 style)
- **Implants**: 2× 3.5mm (anterior) + 2× 4.1mm (posterior)
- **Direction**: Varied angulations (5-8°)
- **Complexity**: Advanced
- **Features**: Multiple inspection windows, mixed implant sizes

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
Loaded 4 implant site(s)

Generating surgical guide...

✓ Guide generated successfully!
  Output: guide.stl
  Volume: ~11,000-12,500 mm³
  Faces: ~800-1200
  Watertight: True
```

## Configuration Details

### Implant Site #33 (Right Canine)

```json
{
  "site_id": "33",
  "position": [15.2, 6.5, 9.5],          // Anterior right
  "direction": [0.05, -0.08, -0.995],    // ~5° mesial, ~5° buccal
  "implant_diameter": 3.5,               // Narrow anterior implant
  "implant_length": 11.5,                // Longer for anterior
  "sleeve_outer_diameter": 4.5,
  "sleeve_inner_diameter": 3.5,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Implant Site #36 (Right Molar)

```json
{
  "site_id": "36",
  "position": [25.5, -12.3, 8.7],        // Posterior right
  "direction": [0.0, 0.1, -0.995],       // ~6° buccal
  "implant_diameter": 4.1,               // Standard posterior
  "implant_length": 10.0,
  "sleeve_outer_diameter": 5.0,
  "sleeve_inner_diameter": 4.0,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Implant Site #43 (Left Canine)

```json
{
  "site_id": "43",
  "position": [-15.8, 5.9, 9.3],         // Anterior left
  "direction": [-0.05, -0.07, -0.996],   // ~5° distal, ~4° buccal
  "implant_diameter": 3.5,
  "implant_length": 11.5,
  "sleeve_outer_diameter": 4.5,
  "sleeve_inner_diameter": 3.5,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Implant Site #46 (Left Molar)

```json
{
  "site_id": "46",
  "position": [-24.8, -11.9, 9.1],       // Posterior left
  "direction": [0.0, 0.08, -0.997],      // ~5° buccal
  "implant_diameter": 4.1,
  "implant_length": 10.0,
  "sleeve_outer_diameter": 5.0,
  "sleeve_inner_diameter": 4.0,
  "sleeve_height": 5.0,
  "clearance": 0.05
}
```

### Clinical Notes

- **Distribution**: Classic quad configuration (canines + molars)
- **Mixed sizes**: Smaller diameter anteriorly (3.5mm), larger posteriorly (4.1mm)
- **Angulations**: Varied to follow arch anatomy (5-8°)
- **Separation**: Realistic spacing for full arch support
- **Inspection windows**: 4 windows (one between each pair)

## Key Features

### Multiple Implant Sizes

This example demonstrates handling different implant diameters:

- **Anterior (3.5mm)**: Narrower for limited bone width
- **Posterior (4.1mm)**: Standard diameter for molar sites

Each has corresponding sleeve sizes:
- Anterior: 4.5mm outer / 3.5mm inner
- Posterior: 5.0mm outer / 4.0mm inner

### Complex Angulations

Each implant has unique angulation:

```
Site #33:  5° mesial  + 5° buccal  (multi-planar)
Site #36:  0° mesial  + 6° buccal  (single plane)
Site #43:  5° distal  + 4° buccal  (multi-planar)
Site #46:  0° mesial  + 5° buccal  (single plane)
```

### Inspection Windows

With 4 implants, multiple windows are created:
- Between #33 and #36 (right side)
- Between #43 and #46 (left side)
- Potentially between #33 and #43 (anterior)
- Potentially between #36 and #46 (posterior)

## Customization Examples

### Larger guide for full arch coverage

```bash
surgical-guide --implants implants.json --output guide.stl \
  --extents 65 40 12
```

### Maximum thickness for strength

```bash
surgical-guide --implants implants.json --output guide.stl \
  --thickness 3.5
```

### Adjust window size for better visualization

```bash
surgical-guide --implants implants.json --output guide.stl \
  --window-width 15.0
```

### Disable windows (not recommended for multiple implants)

```bash
surgical-guide --implants implants.json --output guide.stl \
  --no-windows
```

### Full verbose output

```bash
surgical-guide --implants implants.json --output guide.stl --verbose
```

Output includes all 4 sites:
```
Loaded 4 implant site(s)
  - Site 33: position=[15.2, 6.5, 9.5]
  - Site 36: position=[25.5, -12.3, 8.7]
  - Site 43: position=[-15.8, 5.9, 9.3]
  - Site 46: position=[-24.8, -11.9, 9.1]
```

## Python API Usage

```python
from surgical_guide_generator import generate_surgical_guide, GuideConfig
from surgical_guide_generator.cli import load_implant_sites_from_json

# Load all 4 sites
sites = load_implant_sites_from_json("implants.json")

# Configure for full arch
config = GuideConfig(
    thickness=3.0,              # Thicker for strength
    tissue_gap=0.15,
    add_inspection_windows=True,
    window_width=12.0,
)

# Generate with larger extents
result = generate_surgical_guide(
    guide_body_extents=[65, 40, 12],  # Full arch coverage
    implant_sites=sites,
    output_path="guide.stl",
    config=config,
)

# Detailed metrics
print(f"Implants: {len(sites)}")
print(f"Volume: {result.metrics['final_volume_mm3']:.1f} mm³")
print(f"Faces: {result.metrics['final_face_count']}")
print(f"Operations: {', '.join(result.operations_performed)}")
```

## What You'll Get

### Guide Features

- ✅ Four precisely positioned sleeve channels
- ✅ Mixed sleeve sizes (4.5mm and 5.0mm)
- ✅ Multiple inspection windows
- ✅ Complex multi-planar angulations
- ✅ Full arch coverage
- ✅ Watertight mesh ready for 3D printing

### Geometric Properties

- **Guide dimensions**: 50mm × 30mm × 10mm (default, recommend larger)
- **Recommended**: 65mm × 40mm × 12mm
- **Guide volume**: ~11,000-12,500 mm³
- **Mesh complexity**: ~800-1200 faces
- **Watertight**: Yes (guaranteed)
- **Inspection windows**: 3-4 (depending on spacing)

## Clinical Workflow - All-on-4

### 1. Pre-operative Planning

- **CBCT scan**: Full arch with bone density mapping
- **Virtual planning**: Position 4 implants for optimal support
  - Anterior: Canine regions (straight or slightly angled)
  - Posterior: Molar regions (angled to avoid sinus/nerve)
- **Extract coordinates**: Use planning software
- **Create JSON**: Input positions, directions, and implant specs

### 2. Guide Generation

```bash
surgical-guide --implants implants.json --output guide.stl \
  --extents 65 40 12 --thickness 3.0 --verbose
```

### 3. Quality Verification

Check metrics:
- Volume: Should be 11,000-13,000 mm³
- Watertight: Must be True
- Face count: 800-1200 faces is good

### 4. 3D Printing

**Critical for full arch**:
- Material: Medical-grade biocompatible resin
- Layer height: 0.05-0.1mm (high precision)
- Infill: 100%
- Support: May be needed for complex geometry
- Orientation: Flat base down

### 5. Post-processing

- Remove all supports carefully
- Clean thoroughly (IPA)
- UV cure completely
- Inspect all 4 sleeve channels
- Verify inspection windows are clear
- Sterilize per clinical protocol

### 6. Surgical Procedure

1. Seat guide on tissue (verify through windows)
2. Drill sequential sites (follow depth protocol)
3. Use inspection windows to verify guide stability between drills
4. Place all 4 implants
5. Verify final positions
6. Apply immediate provisional prosthesis

## Understanding the Geometry

### Arch Layout

```
        Anterior
          |
    #33   |   #43
     •    |    •      Canine region
          |
    #36   |   #46
     •    |    •      Molar region
          |
       Posterior

Left <----+----> Right
```

### Position Coordinates (mm)

```
Site #33: [ 15.2,   6.5,  9.5]  Right anterior
Site #36: [ 25.5, -12.3,  8.7]  Right posterior
Site #43: [-15.8,   5.9,  9.3]  Left anterior
Site #46: [-24.8, -11.9,  9.1]  Left posterior
```

### Spacing

- **Anterior-Posterior**: ~20-25mm between canine and molar
- **Left-Right**: ~30-31mm between canines, ~50mm between molars
- **Vertical**: 8.7-9.5mm (slight variation for arch curvature)

## Expected Results

### File Sizes

- **STL**: ~60-100 KB
- **3MF**: ~40-70 KB (compressed)

### Processing Time

- **Generation**: 5-10 seconds (4 implants + windows)
- **Validation**: 1-2 seconds
- **Export**: <1 second
- **Total**: 7-13 seconds

### Validation Checks

All automatically performed:

- ✅ Watertight mesh (critical)
- ✅ Positive volume
- ✅ No self-intersections
- ✅ All 4 channels correctly positioned
- ✅ All inspection windows clear
- ✅ Sleeve sizes correct

## Troubleshooting

### Guide too small for full arch

Increase extents:
```bash
--extents 70 45 15  # Larger full arch coverage
```

### Sleeves overlapping

Edit positions in JSON to increase separation:
```json
"position": [30.0, -15.0, 8.5],  // Move posterior implant back
```

### Windows blocking sleeves

Decrease window width:
```bash
--window-width 8.0  # Smaller windows
```

### Complex angulation errors

Check direction vectors are unit vectors (or close):
```python
import numpy as np
direction = [0.05, -0.08, -0.995]
norm = np.linalg.norm(direction)
print(norm)  # Should be ~1.0
```

System auto-normalizes but good to verify.

### Guide doesn't match anatomy

Current limitation: Simple box placeholder doesn't follow tissue contours.

**Future**: SDF-based anatomical shell generation will solve this.

**Workaround**: Adjust guide extents and thickness to approximate anatomy.

## Advanced Modifications

### Add 5th implant (All-on-5)

Add central incisor implant:
```json
{
  "site_id": "41",
  "position": [0.0, 10.5, 10.0],
  "direction": [0.0, -0.1, -0.995],
  "implant_diameter": 3.3,
  "implant_length": 13.0,
  "sleeve_outer_diameter": 4.5,
  "sleeve_inner_diameter": 3.5,
  "sleeve_height": 5.5,
  "clearance": 0.05
}
```

### Change to All-on-6

Add two more implants at lateral incisor positions (#12, #22).

### Increase angulation

For tilted implants (e.g., 30° All-on-4):
```json
"direction": [0.0, 0.5, -0.866],  // 30° buccal tilt
```

### Use different implant systems

Edit diameters and lengths to match your preferred system:
- Nobel Biocare
- Straumann
- Zimmer Biomet
- etc.

## Performance Considerations

### Mesh Complexity

4 implants → ~800-1200 faces → Good balance of detail and file size

### Memory Usage

Minimal (<50MB RAM) for this complexity

### Generation Time

~7-13 seconds total (depends on CPU)

## Quality Assurance Checklist

Before 3D printing:

- [ ] All 4 implant positions verified in planning software
- [ ] Direction vectors point apically (negative Z)
- [ ] Sleeve sizes match drill protocol
- [ ] Guide extents cover all implants with margin
- [ ] Generated mesh is watertight (check output)
- [ ] Inspection windows are clear
- [ ] STL file opens in slicer without errors

## Next Steps

1. **Test the guide**: Generate and inspect in MeshLab/Blender
2. **Modify parameters**: Experiment with extents, thickness, windows
3. **3D print trial**: Use standard resin for test fit
4. **Clinical printing**: Use biocompatible resin for surgery
5. **Document workflow**: Record your settings for reproducibility

## References

- Maló et al. (2003) - All-on-4 concept
- Van Assche et al. (2012) - Accuracy of computer-aided implant placement
- [USAGE.md](../../docs/USAGE.md) - Complete CLI reference
- [Project README](../../SURGICAL_GUIDE_README.md) - Full documentation
- [Basic Single Example](../basic_single_implant/) - Simpler case
- [Bilateral Example](../bilateral_implants/) - Intermediate case
