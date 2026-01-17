# Basic Single Implant Example

Simple single tooth replacement with vertical implant placement.

## Clinical Scenario

- **Tooth**: #36 (lower right first molar)
- **Indication**: Single tooth replacement
- **Implant**: 4.1mm × 10mm
- **Direction**: Vertical (straight down)
- **Complexity**: Beginner

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
Loaded 1 implant site(s)

Generating surgical guide...

✓ Guide generated successfully!
  Output: guide.stl
  Volume: ~14,500-15,000 mm³
  Faces: ~200-300
  Watertight: True
```

## Configuration Details

### Implant Site #36

```json
{
  "site_id": "36",
  "position": [0.0, 0.0, 8.0],           // Centered, 8mm height
  "direction": [0.0, 0.0, -1.0],         // Straight vertical
  "implant_diameter": 4.1,               // Standard posterior size
  "implant_length": 10.0,                // Medium length
  "sleeve_outer_diameter": 5.0,          // 5mm sleeve
  "sleeve_inner_diameter": 4.0,          // 4mm drill guide
  "sleeve_height": 5.0,                  // 5mm guidance length
  "clearance": 0.05                      // 50μm clearance
}
```

### Clinical Notes

- **Position**: Centered at origin for simplicity
- **Direction**: [0, 0, -1] means straight down (vertical)
- **Sleeve size**: Standard 5mm outer diameter
- **Clearance**: 50μm per Van Assche et al. (2012)

## Customization Examples

### Larger guide body

```bash
surgical-guide --implants implants.json --output guide.stl \
  --extents 60 40 12
```

### Thicker guide shell

```bash
surgical-guide --implants implants.json --output guide.stl \
  --thickness 3.0
```

### Different tissue gap

```bash
surgical-guide --implants implants.json --output guide.stl \
  --tissue-gap 0.2
```

### Export as 3MF

```bash
surgical-guide --implants implants.json --output guide.3mf
```

### Verbose output

```bash
surgical-guide --implants implants.json --output guide.stl --verbose
```

## Python API Usage

```python
from surgical_guide_generator import generate_surgical_guide, ImplantSite, SleeveSpec

# Define implant site programmatically
site = ImplantSite(
    site_id="36",
    position=[0.0, 0.0, 8.0],
    direction=[0.0, 0.0, -1.0],
    sleeve_spec=SleeveSpec(
        outer_diameter=5.0,
        inner_diameter=4.0,
        height=5.0,
    ),
)

# Generate guide
result = generate_surgical_guide(
    guide_body_extents=[50, 30, 10],
    implant_sites=[site],
    output_path="guide.stl",
)

print(f"Success: {result.success}")
print(f"Volume: {result.metrics['final_volume_mm3']:.1f} mm³")
```

## What You'll Get

### Guide Features

- ✅ Precisely positioned sleeve channel at [0, 0, 8]
- ✅ 5mm outer diameter sleeve
- ✅ 4mm inner drill guide diameter
- ✅ 5mm guidance height
- ✅ Watertight mesh ready for 3D printing

### No Inspection Windows

Single implant guides typically don't need inspection windows since there's only one reference point.

To force windows anyway:
```bash
surgical-guide --implants implants.json --output guide.stl \
  --window-width 12.0
```

## Expected Results

### Geometric Properties

- **Guide dimensions**: 50mm × 30mm × 10mm (default)
- **Guide volume**: ~14,500-15,000 mm³
- **Mesh complexity**: ~200-300 faces
- **Watertight**: Yes (guaranteed)

### File Size

- **STL**: ~15-30 KB
- **3MF**: ~10-20 KB (compressed)

## Validation

The generated guide will be automatically validated for:

- ✅ Watertight mesh (required for 3D printing)
- ✅ Positive volume
- ✅ No self-intersections
- ✅ Proper face orientation
- ✅ Valid geometry

## 3D Printing

### Recommended Settings

- **Layer height**: 0.1-0.2mm
- **Infill**: 100%
- **Material**: Biocompatible resin (surgical grade)
- **Support**: Usually not needed (flat base)

### Slicing

Import `guide.stl` into your slicer:
- PrusaSlicer
- Cura
- ChituBox (for resin printers)

### Post-Processing

1. Remove support material (if any)
2. Clean in IPA (for resin prints)
3. UV cure (for resin prints)
4. Sterilize per clinical protocol

## Next Steps

1. **Try customization**: Modify the JSON or use CLI parameters
2. **View the mesh**: Open in MeshLab or Blender
3. **Try more complex examples**: See `bilateral_implants/` or `full_arch/`

## Troubleshooting

### Guide too small/large
Adjust extents:
```bash
--extents 60 40 12  # Larger guide
--extents 40 25 8   # Smaller guide
```

### Need different sleeve size
Edit `implants.json` and change:
```json
"sleeve_outer_diameter": 6.0,  // Larger sleeve
"sleeve_inner_diameter": 5.0,  // Larger drill guide
```

### Direction vector confusion
- [0, 0, -1] = straight down
- [0, 0, 1] = straight up
- [0.1, 0, -0.995] = slight angle (auto-normalized)

## References

- Van Assche et al. (2012) - Accuracy of computer-aided implant placement
- [USAGE.md](../../docs/USAGE.md) - Complete CLI reference
- [Project README](../../SURGICAL_GUIDE_README.md) - Full documentation
