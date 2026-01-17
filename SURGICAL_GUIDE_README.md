# Surgical Guide Generator

**Automated pipeline for generating 3D-printable dental implant surgical guides**

[![Tests](https://img.shields.io/badge/tests-110%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-90%25-green)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()

## Overview

This project generates precision surgical guides for dental implant placement. It creates 3D-printable STL/3MF files with:

- ✅ **Sleeve Channels** - Precisely positioned drill guide channels
- ✅ **Inspection Windows** - Visual verification openings for multi-implant cases
- ✅ **Validation** - Automatic quality checking (watertight, volume, etc.)
- ✅ **Export** - STL and 3MF format support with comprehensive metrics

## Quick Start

### Installation

```bash
pip install -e .
```

### Generate a Guide

```bash
# Create example configuration
surgical-guide --create-example my-implants.json

# Generate guide
surgical-guide --implants my-implants.json --output guide.stl
```

### Output

```
Loading implant sites from: my-implants.json
Loaded 2 implant site(s)

Generating surgical guide...
✓ Guide generated successfully!
  Output: guide.stl
  Volume: 14924.9 mm³
  Faces: 288
  Watertight: True
```

## Features

### Implemented (10/13 modules - 110 tests passing)

| Module | Tests | Status | Description |
|--------|-------|--------|-------------|
| Configuration | 14 | ✅ | Type-safe config with validation |
| Mesh I/O | 12 | ✅ | Load/export STL/3MF files |
| Validation | 13 | ✅ | Mesh quality checking |
| Repair | 9 | ✅ | Automatic mesh fixing |
| Sleeve Channels | 13 | ✅ | Precise cylinder positioning |
| Boolean Operations | 14 | ✅ | manifold3d integration |
| Inspection Windows | 10 | ✅ | Multi-implant verification |
| Main Pipeline | 11 | ✅ | End-to-end orchestration |
| CLI Interface | 14 | ✅ | Command-line tool |

### In Development

- **SDF Offset Algorithm** - Replace box placeholder with anatomical shell
- **Integration Tests** - End-to-end scenarios
- **Advanced Documentation** - API reference

## Architecture

### Tech Stack

- **Language**: Python 3.8+
- **Mesh Processing**: trimesh, manifold3d
- **Geometry**: numpy, scipy
- **Testing**: pytest (110 tests, 100% passing)
- **Quality**: Full type hints, TDD approach

### Module Structure

```
surgical_guide_generator/
├── config.py              # Type-safe configuration
├── mesh_io.py             # Load/export operations
├── validation.py          # Quality checking
├── repair.py              # Mesh fixing
├── sleeve_channels.py     # Channel geometry
├── boolean_ops.py         # CSG operations
├── inspection_windows.py  # Window features
├── generator.py           # Main pipeline
└── cli.py                 # Command-line interface
```

### Design Principles

1. **Test-Driven Development** - All code written test-first
2. **Type Safety** - Full type hints on all functions
3. **Defensive Programming** - Comprehensive input validation
4. **Structured Results** - Dataclasses for all outputs
5. **Clean Architecture** - No circular dependencies

## Usage

### Command Line

```bash
# Basic usage
surgical-guide --implants sites.json --output guide.stl

# With custom parameters
surgical-guide \
  --implants sites.json \
  --output guide.3mf \
  --extents 60 35 12 \
  --thickness 3.0 \
  --window-width 12.0 \
  --verbose
```

### Python API

```python
from surgical_guide_generator import (
    generate_surgical_guide,
    ImplantSite,
    SleeveSpec,
    GuideConfig,
)

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

result = generate_surgical_guide(
    guide_body_extents=[50, 30, 10],
    implant_sites=sites,
    output_path="guide.stl",
)
```

### JSON Input Format

```json
{
  "implant_sites": [
    {
      "site_id": "36",
      "position": [25.5, -12.3, 8.7],
      "direction": [0.0, 0.1, -0.995],
      "sleeve_outer_diameter": 5.0,
      "sleeve_inner_diameter": 4.0,
      "sleeve_height": 5.0
    }
  ]
}
```

## Documentation

- **[USAGE.md](docs/USAGE.md)** - Complete usage guide
- **[Claude.md](docs/Claude.md)** - Development guidelines (TDD, best practices)
- **[project_plan.md](docs/project_plan.md)** - Technical specification
- **[implementation_progress.md](docs/implementation_progress.md)** - Status tracking

## Testing

```bash
# Run all tests
pytest surgical_guide_generator/tests/

# Run with coverage
pytest --cov=surgical_guide_generator

# Run specific module
pytest surgical_guide_generator/tests/test_generator.py -v
```

**Current Status**: 110/110 tests passing (100%)

## Clinical Parameters

Based on published research:

| Parameter | Value | Reference |
|-----------|-------|-----------|
| Drill-to-sleeve clearance | 50-150μm | Van Assche et al., 2012 |
| Sleeve length | 5-7mm | Longer = less angular deviation |
| Guide thickness | 2.0-3.0mm | Structural integrity |
| Tissue gap | 0.1-0.2mm | Seating compensation |
| Expected accuracy | 3-5° angular, 1-1.5mm positional | System-dependent |

## Current Limitations

- **Guide Body**: Uses simple box placeholder (SDF algorithm pending)
- **No IOS Input**: Cannot load intraoral scan meshes yet
- **Manual Planning**: Implant positions must be pre-determined

## Roadmap

- [ ] SDF-based offset algorithm for anatomical shells
- [ ] IOS mesh loading and processing
- [ ] Integration tests with realistic data
- [ ] Performance optimization for large meshes
- [ ] GUI for interactive planning

## Contributing

This project follows strict TDD practices:

1. **Write tests first** - Define behavior before implementation
2. **Full type hints** - All functions are fully typed
3. **Defensive programming** - Validate all inputs
4. **Clean code** - Follow PEP 8, use meaningful names
5. **Documentation** - Docstrings with examples

See [Claude.md](docs/Claude.md) for detailed guidelines.

## License

MIT License - See LICENSE file

## References

- **Trimesh**: https://trimsh.org/
- **Manifold3D**: https://github.com/elalish/manifold
- Van Assche et al. (2012) - Accuracy of computer-aided implant placement

## Contact

For questions or contributions, see the issues page.

---

**Project Stats**: 110 tests | 10 modules | ~3,000 lines of code | 90% coverage
