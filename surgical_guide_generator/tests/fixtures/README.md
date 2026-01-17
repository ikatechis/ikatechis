# Test Fixtures

This directory contains test data and fixtures for the surgical guide generator.

## JSON Configuration Files

Example implant site configurations for different clinical scenarios:

### `single_implant.json`
- **Use case**: Single tooth replacement
- **Site**: #36 (lower right first molar)
- **Direction**: Vertical (0, 0, -1)
- **Implant**: 4.1mm diameter, 10mm length
- **Position**: Centered at origin

### `bilateral_implants.json`
- **Use case**: Bilateral posterior implants
- **Sites**: #36 (right) and #46 (left) molars
- **Direction**: Slight buccal angulation
- **Implant**: 4.1mm diameter, 10mm length
- **Separation**: ~50mm apart

### `full_arch_4implants.json`
- **Use case**: Full arch restoration with 4 implants
- **Sites**: #33, #36, #43, #46 (canines and molars)
- **Direction**: Varied angulations
- **Implants**: Mixed sizes (3.5mm and 4.1mm diameter)
- **Distribution**: Evenly spaced across arch

### `anterior_implant.json`
- **Use case**: Front tooth replacement
- **Site**: #11 (upper right central incisor)
- **Direction**: Angled palatal (typical anterior angulation)
- **Implant**: 3.3mm diameter, 13mm length (narrow, long)
- **Position**: Anterior region with more pronounced angle

## Test Mesh Files

Simple geometric meshes for testing:

### `flat_surface.stl`
- **Description**: Flat rectangular surface
- **Dimensions**: 60mm × 40mm × 2mm
- **Faces**: 12
- **Volume**: 4,800 mm³
- **Use**: Basic geometric testing, simple surface operations

### `curved_ridge.stl`
- **Description**: Curved ridge approximating dental arch segment
- **Dimensions**: 60mm length, 12mm width, 8mm height
- **Faces**: ~156
- **Volume**: ~6,083 mm³
- **Curvature**: Parabolic (0.3 curvature parameter)
- **Use**: Testing on curved anatomical-like surfaces

### `curved_arch.stl`
- **Description**: Curved arch shape (120° arc)
- **Dimensions**: 40mm radius, 12mm width, 8mm height
- **Faces**: ~236
- **Volume**: ~8,035 mm³
- **Arc**: 120° semicircular arch
- **Use**: Full arch testing, multi-implant scenarios

## Generating Test Meshes

Test meshes can be regenerated using:

```bash
python surgical_guide_generator/tests/fixtures/generate_test_meshes.py
```

This script creates the STL files using trimesh with precise geometric specifications.

## Usage Examples

### Loading a fixture in tests:

```python
from pathlib import Path
import json

# Load JSON configuration
fixtures_dir = Path(__file__).parent / "fixtures"
with open(fixtures_dir / "single_implant.json") as f:
    config = json.load(f)

# Load test mesh
from surgical_guide_generator.mesh_io import load_mesh
mesh = load_mesh(str(fixtures_dir / "curved_ridge.stl"))
```

### Using in integration tests:

```python
from surgical_guide_generator import generate_surgical_guide
from surgical_guide_generator.cli import load_implant_sites_from_json

sites = load_implant_sites_from_json("fixtures/bilateral_implants.json")
result = generate_surgical_guide(
    guide_body_extents=[50, 30, 10],
    implant_sites=sites,
    output_path="output/guide.stl"
)
```

## Clinical Validity

The implant configurations use realistic clinical parameters:

- **Positions**: Based on typical dental anatomy
- **Angulations**: Within normal surgical planning ranges (0-15°)
- **Diameters**: Standard implant sizes (3.3-4.1mm)
- **Lengths**: Common implant lengths (10-13mm)
- **Sleeve clearances**: 50μm (per Van Assche et al., 2012)

These fixtures are suitable for:
- Unit testing
- Integration testing
- Performance benchmarking
- Example demonstrations
- Documentation screenshots
