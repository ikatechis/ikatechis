# Surgical Guide Generator - Usage Guide

## Installation

```bash
pip install -e .
```

## Quick Start

### 1. Create an Example Configuration

```bash
surgical-guide --create-example my-implants.json
```

This creates a JSON file with the following structure:

```json
{
  "implant_sites": [
    {
      "site_id": "36",
      "position": [25.5, -12.3, 8.7],
      "direction": [0.0, 0.1, -0.995],
      "implant_diameter": 4.1,
      "implant_length": 10.0,
      "sleeve_outer_diameter": 5.0,
      "sleeve_inner_diameter": 4.0,
      "sleeve_height": 5.0,
      "clearance": 0.05
    }
  ]
}
```

### 2. Generate a Surgical Guide

```bash
surgical-guide --implants my-implants.json --output guide.stl
```

This will:
- Load implant sites from JSON
- Generate guide body (currently a simple box placeholder)
- Subtract sleeve channels
- Add inspection windows (for multi-implant cases)
- Validate the result
- Export to STL format

### 3. Customize Parameters

```bash
surgical-guide \
  --implants my-implants.json \
  --output guide.3mf \
  --extents 60 35 12 \
  --thickness 3.0 \
  --tissue-gap 0.2 \
  --window-width 12.0 \
  --verbose
```

## Command-Line Options

### Required Arguments

- `--implants FILE` - Path to JSON file with implant specifications
- `--output FILE` - Output file path (.stl or .3mf)

### Guide Body Options

- `--extents L W H` - Guide body dimensions in mm (default: 50 30 10)
  - Currently uses a simple box placeholder
  - Will be replaced with SDF-based anatomical shell

### Configuration Options

- `--thickness N` - Guide shell thickness in mm (default: 2.5)
- `--tissue-gap N` - Gap from tissue surface in mm (default: 0.15)
- `--window-width N` - Inspection window width in mm (default: 10.0)
- `--no-windows` - Disable inspection windows

### Utility Options

- `--create-example FILE` - Create example JSON configuration
- `--verbose`, `-v` - Enable verbose output
- `--version` - Show version number
- `--help`, `-h` - Show help message

## JSON Input Format

### Required Fields

Each implant site must have:

```json
{
  "site_id": "36",              # Tooth number or identifier
  "position": [x, y, z],        # Platform center in mm
  "direction": [dx, dy, dz],    # Axis vector (will be normalized)
  "sleeve_outer_diameter": 5.0, # Outer diameter in mm
  "sleeve_inner_diameter": 4.0, # Inner diameter in mm
  "sleeve_height": 5.0          # Sleeve length in mm
}
```

### Optional Fields

```json
{
  "implant_diameter": 4.1,   # For documentation
  "implant_length": 10.0,    # For documentation
  "clearance": 0.05          # Sleeve fit tolerance (default: 0.05mm)
}
```

## Examples

### Single Implant Guide

```bash
# Create config for single implant
cat > single.json << EOF
{
  "implant_sites": [{
    "site_id": "36",
    "position": [0, 0, 5],
    "direction": [0, 0, -1],
    "sleeve_outer_diameter": 5.0,
    "sleeve_inner_diameter": 4.0,
    "sleeve_height": 5.0
  }]
}
EOF

# Generate guide (no inspection windows for single implant)
surgical-guide --implants single.json --output single-guide.stl
```

### Multi-Implant Guide with Windows

```bash
# Use example generator
surgical-guide --create-example multi.json

# Generate with windows
surgical-guide \
  --implants multi.json \
  --output multi-guide.3mf \
  --extents 50 30 10 \
  --verbose
```

### Custom Fit Parameters

```bash
# Tighter fit, thicker guide
surgical-guide \
  --implants my-implants.json \
  --output tight-guide.stl \
  --thickness 3.0 \
  --tissue-gap 0.1 \
  --window-width 8.0
```

## Output Formats

### STL (Binary)
```bash
surgical-guide --implants sites.json --output guide.stl
```
- Universal format
- Supported by all slicers
- No unit information (assumes mm)

### 3MF (Recommended)
```bash
surgical-guide --implants sites.json --output guide.3mf
```
- Includes unit information (mm)
- Smaller file size
- Better metadata support

## Programmatic Usage

You can also use the library directly in Python:

```python
from surgical_guide_generator import (
    generate_surgical_guide,
    ImplantSite,
    SleeveSpec,
    GuideConfig,
)

# Define implant sites
sites = [
    ImplantSite(
        site_id="36",
        position=[25.5, -12.3, 8.7],
        direction=[0.0, 0.1, -0.995],
        sleeve_spec=SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        ),
    )
]

# Generate guide
result = generate_surgical_guide(
    guide_body_extents=[50, 30, 10],
    implant_sites=sites,
    output_path="guide.stl",
    config=GuideConfig(thickness=2.5),
)

if result.success:
    print(f"Guide saved: {result.metrics}")
else:
    print(f"Error: {result.error_message}")
```

## Workflow

1. **Plan Implants** - Use dental planning software to determine positions
2. **Export Data** - Create JSON with implant specifications
3. **Generate Guide** - Run surgical-guide command
4. **Validate** - Check output in MeshLab or slicer
5. **3D Print** - Use SLA/DLP printer (50-100μm resolution)
6. **Post-Process** - Clean, cure, sterilize

## Clinical Parameters

### Recommended Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| Thickness | 2.5-3.0mm | Structural integrity |
| Tissue Gap | 0.1-0.2mm | Seating compensation |
| Clearance | 0.05-0.10mm | 50-100μm for press-fit |
| Window Width | 8-12mm | Visual verification |

### Print Settings (SLA/DLP)

| Parameter | Value |
|-----------|-------|
| Layer Height | 50-100μm |
| XY Resolution | 25-75μm |
| Print Angle | 30-45° |
| Support Density | Medium |

## Troubleshooting

### "Mesh is not watertight"
- Check that guide body extents are large enough
- Verify implant positions are within guide bounds
- Ensure sleeve channels don't overlap

### "Boolean subtraction failed"
- Implants may be too close together
- Try increasing guide body size
- Check for invalid direction vectors

### "Validation failed"
- Output may still be usable
- Check warnings for specific issues
- Use MeshLab to repair if needed

## Current Limitations

- **Guide Body**: Currently uses a simple box placeholder
  - SDF-based anatomical shell coming soon
  - For now, adjust `--extents` to fit your case

- **No IOS Input**: Cannot load intraoral scan meshes yet
  - SDF algorithm will enable this

- **Manual Positioning**: Implant positions must be pre-determined
  - No interactive planning interface

## Next Steps

After generating a guide:

1. **Inspect** - Open in MeshLab or slicer software
2. **Verify** - Check sleeve alignment and clearances
3. **Slice** - Prepare for 3D printing
4. **Test Print** - Verify fit with physical model
5. **Production** - Print final guide in biocompatible resin
6. **Sterilize** - Follow appropriate sterilization protocol

## Support

For issues or questions:
- Check the test files for usage examples
- Review `docs/project_plan.md` for technical details
- See `docs/Claude.md` for development guidelines
