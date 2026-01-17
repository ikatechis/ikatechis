# Surgical Guide Generator - Examples

Complete end-to-end examples demonstrating the surgical guide generator.

## Available Examples

### 1. Basic Single Implant
**Directory**: `basic_single_implant/`

Simple single tooth replacement with vertical implant placement.

- **Clinical scenario**: Lower right first molar (#36)
- **Complexity**: Beginner
- **Features**: Basic guide with one sleeve channel
- **Estimated time**: 2-3 minutes

[View example →](basic_single_implant/)

### 2. Bilateral Implants
**Directory**: `bilateral_implants/`

Two posterior implants with slight angulation and inspection windows.

- **Clinical scenario**: Bilateral molar replacement (#36, #46)
- **Complexity**: Intermediate
- **Features**: Multiple sleeves, inspection windows, angulated placements
- **Estimated time**: 3-5 minutes

[View example →](bilateral_implants/)

### 3. Full Arch Restoration
**Directory**: `full_arch/`

Multiple implants for full arch restoration with varied angulations.

- **Clinical scenario**: 4-implant supported denture
- **Complexity**: Advanced
- **Features**: Multiple implants, varied sizes, inspection windows
- **Estimated time**: 5-8 minutes

[View example →](full_arch/)

## Quick Start

Each example can be run with a single command:

```bash
# Navigate to example directory
cd examples/basic_single_implant

# Generate guide
surgical-guide --implants implants.json --output guide.stl
```

Or from the project root:

```bash
surgical-guide --implants examples/basic_single_implant/implants.json --output output/guide.stl
```

## Understanding the Output

After generation, you'll see output like:

```
Loading implant sites from: implants.json
Loaded 1 implant site(s)

Generating surgical guide...

✓ Guide generated successfully!
  Output: guide.stl
  Volume: 14924.9 mm³
  Faces: 288
  Watertight: True
```

### Key Metrics

- **Volume**: Guide body volume in mm³ (cubic millimeters)
- **Faces**: Number of triangular faces in the mesh
- **Watertight**: Must be True for 3D printing

### Output Files

The STL file can be:
- Imported into slicing software (PrusaSlicer, Cura, etc.)
- Viewed in mesh viewers (MeshLab, Blender)
- Sent directly to 3D printers
- Further processed in CAD software

## Customizing Parameters

All examples support command-line customization:

```bash
# Custom guide dimensions
surgical-guide --implants implants.json --output guide.stl \
  --extents 60 40 12

# Custom thickness and tissue gap
surgical-guide --implants implants.json --output guide.stl \
  --thickness 3.0 --tissue-gap 0.2

# Disable inspection windows
surgical-guide --implants implants.json --output guide.stl \
  --no-windows

# Verbose output for debugging
surgical-guide --implants implants.json --output guide.stl \
  --verbose
```

## File Format Support

Guides can be exported in multiple formats:

```bash
# STL format (most common)
surgical-guide --implants implants.json --output guide.stl

# 3MF format (includes color and metadata)
surgical-guide --implants implants.json --output guide.3mf
```

## Programmatic Usage

Examples can also be run via Python:

```python
from surgical_guide_generator import generate_surgical_guide
from surgical_guide_generator.cli import load_implant_sites_from_json

# Load implant sites
sites = load_implant_sites_from_json("examples/basic_single_implant/implants.json")

# Generate guide
result = generate_surgical_guide(
    guide_body_extents=[50, 30, 10],
    implant_sites=sites,
    output_path="output/guide.stl"
)

if result.success:
    print(f"Guide generated: {result.metrics['final_volume_mm3']:.1f} mm³")
else:
    print(f"Error: {result.error_message}")
```

## Creating Your Own Examples

To create your own implant configuration:

1. **Generate template**:
   ```bash
   surgical-guide --create-example my-implants.json
   ```

2. **Edit JSON file** with your implant positions and specifications

3. **Generate guide**:
   ```bash
   surgical-guide --implants my-implants.json --output my-guide.stl
   ```

### JSON Structure

```json
{
  "implant_sites": [
    {
      "site_id": "36",                    // Tooth number or identifier
      "position": [25.5, -12.3, 8.7],     // X, Y, Z coordinates (mm)
      "direction": [0.0, 0.1, -0.995],    // Direction vector (normalized)
      "implant_diameter": 4.1,            // Implant diameter (mm)
      "implant_length": 10.0,             // Implant length (mm)
      "sleeve_outer_diameter": 5.0,       // Sleeve outer diameter (mm)
      "sleeve_inner_diameter": 4.0,       // Drill guide diameter (mm)
      "sleeve_height": 5.0,               // Sleeve height (mm)
      "clearance": 0.05                   // Drill-to-sleeve gap (mm)
    }
  ]
}
```

## Clinical Parameters

Examples use realistic clinical parameters based on published research:

| Parameter | Value | Reference |
|-----------|-------|-----------|
| Drill-to-sleeve clearance | 50μm | Van Assche et al., 2012 |
| Sleeve length | 5-5.5mm | Optimal guidance |
| Guide thickness | 2.5mm | Structural integrity |
| Tissue gap | 0.15mm | Seating compensation |

## Troubleshooting

### Guide won't generate
- Check JSON syntax (use `--verbose` for details)
- Ensure implant positions are within guide extents
- Verify direction vectors are normalized (or let auto-normalize)

### Guide not watertight
- This should not happen with default settings
- If it does, report as a bug

### Wrong orientation
- Check that direction vectors point in the intended direction
- Convention: negative Z typically means "into the bone"

## Next Steps

- Review the [USAGE.md](../docs/USAGE.md) for complete CLI reference
- Read [SURGICAL_GUIDE_README.md](../SURGICAL_GUIDE_README.md) for project overview
- Check [Claude.md](../docs/Claude.md) for development practices

## Support

For issues or questions, please file an issue on the project repository.
