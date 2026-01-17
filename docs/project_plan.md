# Surgical Guide Generator - Implementation Specification

## Task Overview

Implement an automated pipeline to generate 3D-printable dental implant surgical guides for multi-implant treatments. The system takes IOS (intraoral scan) segmentation meshes and implant planning data as input, and outputs print-ready STL/3MF files.

## Input Data (Already Available)

1. **IOS Segmentation Mesh**: STL file of segmented dental arch (tooth/gingiva surfaces)
2. **Implant Positions**: For each implant site:
   - Position (x, y, z) - implant platform center coordinates
   - Direction (dx, dy, dz) - implant axis unit vector (pointing apical)
   - Implant diameter and length
   - Implant type/system
3. **Sleeve Mount Parameters**: Manufacturer-specific sleeve geometry:
   - Outer diameter, inner diameter, height
   - Collar dimensions (if applicable)
   - Fit type (press-fit vs slip-fit)

## Output Requirements

- Fully closed, manifold, watertight mesh
- Print-ready (no self-intersections, proper normals)
- Integrated sleeve channels with precise tolerances
- 3MF format preferred (includes units), STL as fallback

---

## Technical Architecture

### Recommended Libraries (Python)

| Library | Purpose | Install |
|---------|---------|---------|
| **trimesh** | Mesh I/O, basic operations | `pip install trimesh` |
| **manifold3d** | Boolean CSG (guaranteed manifold output) | `pip install manifold3d` |
| **numpy** | Numerical operations | `pip install numpy` |
| **scipy** | Spatial transforms, interpolation | `pip install scipy` |
| **scikit-image** | Marching cubes for isosurface extraction | `pip install scikit-image` |
| **pymeshlab** | Mesh repair (fallback) | `pip install pymeshlab` |

**Critical**: Use `engine='manifold'` for all Boolean operations in trimesh. The default Blender engine is unreliable.

```python
# Correct Boolean usage
result = mesh_a.difference(mesh_b, engine='manifold')
```

### Alternative: MeshLib (Higher Performance)

For production systems requiring maximum robustness with 100k-500k triangle dental meshes:

```python
import meshlib.mrmeshpy as mr

# MeshLib offers 10x faster Boolean operations than CGAL
# and handles dental mesh degeneracies better
mesh = mr.loadMesh("input.stl")
offset_mesh = mr.offsetMesh(mesh, offset=-2.5)  # SDF-based offset
```

Install: `pip install meshlib`

---

## Pipeline Steps

### Step 1: Load and Validate Input Mesh

```python
import trimesh
import numpy as np

def load_ios_mesh(path: str) -> trimesh.Trimesh:
    """Load and validate IOS segmentation mesh."""
    mesh = trimesh.load_mesh(path)

    # Validation checks
    if not mesh.is_watertight:
        print("Warning: Input mesh not watertight, attempting repair")
        mesh = repair_mesh(mesh)

    # Check for degenerate faces
    mesh.remove_degenerate_faces()
    mesh.remove_duplicate_faces()

    # Ensure consistent winding
    mesh.fix_normals()

    return mesh
```

### Step 2: Generate Guide Body (SDF-Based Offset)

The guide body is created by offsetting the IOS surface to create a shell. Use **signed distance field (SDF)** approach for robustness with complex dental anatomy.

**Why SDF over vertex offset**:
- Vertex-based offset (moving vertices along normals) creates self-intersections at concave regions
- SDF handles sharp cusps and interproximal areas correctly

```python
from skimage import measure

def create_guide_body_sdf(
    ios_mesh: trimesh.Trimesh,
    thickness: float = 2.5,      # Guide shell thickness (mm)
    tissue_gap: float = 0.15,    # Gap for seating (mm)
    voxel_size: float = 0.15     # Resolution (mm)
) -> trimesh.Trimesh:
    """
    Create guide body using SDF-based offset.

    Algorithm:
    1. Create 3D voxel grid encompassing mesh + margins
    2. Compute signed distance from each voxel to mesh surface
    3. Extract isosurfaces at two levels:
       - Inner surface: +tissue_gap (slight gap from tissue)
       - Outer surface: -(thickness - tissue_gap) (external surface)
    4. Combine into closed shell via Boolean union
    """
    bounds = ios_mesh.bounds
    margin = thickness + 2.0

    # Create sampling grid
    x = np.arange(bounds[0, 0] - margin, bounds[1, 0] + margin, voxel_size)
    y = np.arange(bounds[0, 1] - margin, bounds[1, 1] + margin, voxel_size)
    z = np.arange(bounds[0, 2] - margin, bounds[1, 2] + margin, voxel_size)

    # Create grid points
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    grid_points = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

    # Compute signed distance field
    # Negative inside mesh, positive outside
    sdf = compute_sdf(ios_mesh, grid_points)
    sdf_volume = sdf.reshape(len(x), len(y), len(z))

    # Extract inner surface (facing tissue)
    # Level = tissue_gap means surface is tissue_gap away from original
    inner_verts, inner_faces, _, _ = measure.marching_cubes(
        sdf_volume,
        level=tissue_gap,
        spacing=(voxel_size, voxel_size, voxel_size)
    )
    inner_verts += [bounds[0, 0] - margin, bounds[0, 1] - margin, bounds[0, 2] - margin]

    # Extract outer surface
    outer_level = -(thickness - tissue_gap)
    outer_verts, outer_faces, _, _ = measure.marching_cubes(
        sdf_volume,
        level=outer_level,
        spacing=(voxel_size, voxel_size, voxel_size)
    )
    outer_verts += [bounds[0, 0] - margin, bounds[0, 1] - margin, bounds[0, 2] - margin]

    # Flip outer surface normals (marching cubes assumes inside is negative)
    outer_faces = outer_faces[:, ::-1]

    # Create meshes
    inner_mesh = trimesh.Trimesh(vertices=inner_verts, faces=inner_faces)
    outer_mesh = trimesh.Trimesh(vertices=outer_verts, faces=outer_faces)

    # Combine into watertight shell
    # The two surfaces should connect at boundaries
    guide_body = combine_shells(inner_mesh, outer_mesh)

    return guide_body


def compute_sdf(mesh: trimesh.Trimesh, points: np.ndarray) -> np.ndarray:
    """
    Compute signed distance field.

    Uses trimesh proximity queries with sign from winding number.
    """
    # Get closest points and distances
    closest, distances, triangle_ids = mesh.nearest.on_surface(points)

    # Determine sign using winding number (robust for watertight meshes)
    # Points inside mesh have winding number ≈ 1, outside ≈ 0
    contained = mesh.contains(points)

    # Signed distance: negative inside, positive outside
    sdf = distances.copy()
    sdf[contained] *= -1

    return sdf
```

### Step 3: Create Sleeve Channels

For each implant site, create a cylinder aligned to the implant axis and subtract it from the guide body.

```python
from scipy.spatial.transform import Rotation

def create_sleeve_channel(
    position: np.ndarray,
    direction: np.ndarray,
    sleeve_outer_diameter: float,
    sleeve_height: float,
    clearance: float = 0.05,      # 50μm for press-fit
    extension: float = 2.0         # Extra length for clean Boolean cut
) -> trimesh.Trimesh:
    """
    Create cylinder geometry for sleeve channel subtraction.

    Args:
        position: Implant platform center (entry point on guide)
        direction: Implant axis unit vector (pointing into bone)
        sleeve_outer_diameter: External diameter of metal sleeve
        sleeve_height: Sleeve length
        clearance: Gap between sleeve and guide hole (fit tolerance)
        extension: Extra cylinder length beyond sleeve for clean cut

    Returns:
        Cylinder mesh positioned and oriented for Boolean subtraction
    """
    # Normalize direction
    direction = np.asarray(direction, dtype=float)
    direction = direction / np.linalg.norm(direction)

    # Channel dimensions
    channel_radius = (sleeve_outer_diameter / 2) + clearance
    channel_height = sleeve_height + extension

    # Create cylinder along Z-axis (trimesh default)
    cylinder = trimesh.creation.cylinder(
        radius=channel_radius,
        height=channel_height,
        sections=64  # Smooth circle
    )

    # Compute rotation from Z-axis to direction vector
    z_axis = np.array([0, 0, 1])

    if np.allclose(direction, z_axis):
        rotation_matrix = np.eye(3)
    elif np.allclose(direction, -z_axis):
        rotation_matrix = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
    else:
        # Rodrigues rotation
        v = np.cross(z_axis, direction)
        s = np.linalg.norm(v)
        c = np.dot(z_axis, direction)
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        rotation_matrix = np.eye(3) + vx + vx @ vx * ((1 - c) / (s * s + 1e-10))

    # Build 4x4 transform
    transform = np.eye(4)
    transform[:3, :3] = rotation_matrix

    # Position cylinder so it:
    # - Starts slightly above guide surface (for clean entry)
    # - Extends through guide and beyond
    # Cylinder is centered at origin, so offset by half height along direction
    offset_along_axis = (channel_height / 2) - extension / 2
    transform[:3, 3] = position + direction * offset_along_axis

    cylinder.apply_transform(transform)

    return cylinder


def subtract_sleeve_channels(
    guide_body: trimesh.Trimesh,
    implant_sites: list,  # List of dicts with position, direction, sleeve params
    clearance_map: dict = None  # site_id -> clearance override
) -> trimesh.Trimesh:
    """
    Subtract all sleeve channels from guide body.

    Uses sequential Boolean operations with manifold engine.
    """
    result = guide_body.copy()

    for site in implant_sites:
        # Get clearance (default or site-specific)
        clearance = 0.05  # Default press-fit
        if clearance_map and site.get('site_id') in clearance_map:
            clearance = clearance_map[site['site_id']]

        # Create channel
        channel = create_sleeve_channel(
            position=np.array(site['position']),
            direction=np.array(site['direction']),
            sleeve_outer_diameter=site['sleeve_outer_diameter'],
            sleeve_height=site['sleeve_height'],
            clearance=clearance
        )

        # Boolean subtraction
        result = result.difference(channel, engine='manifold')

        if not result.is_volume:
            raise RuntimeError(
                f"Boolean subtraction failed for site {site.get('site_id', 'unknown')}. "
                "Check for overlapping sleeves or invalid geometry."
            )

    return result
```

### Step 4: Add Inspection Windows (Multi-Implant)

For multi-implant guides, add windows to verify seating during surgery.

```python
def add_inspection_windows(
    guide: trimesh.Trimesh,
    implant_sites: list,
    window_width: float = 10.0,
    window_depth: float = 5.0,
    margin_from_sleeve: float = 3.0
) -> trimesh.Trimesh:
    """
    Add inspection windows near sleeve positions.

    Windows are placed on the buccal/labial side of each implant
    to allow visual verification of guide seating.
    """
    result = guide.copy()

    for site in implant_sites:
        position = np.array(site['position'])
        direction = np.array(site['direction'])

        # Determine window position (offset from sleeve)
        # Place window perpendicular to implant axis, towards buccal
        # This is simplified - in production, use actual buccal direction from mesh

        # Find a perpendicular direction
        if abs(direction[2]) < 0.9:
            perp = np.cross(direction, [0, 0, 1])
        else:
            perp = np.cross(direction, [1, 0, 0])
        perp = perp / np.linalg.norm(perp)

        # Window center position
        window_center = position + perp * (site['sleeve_outer_diameter']/2 + margin_from_sleeve + window_width/2)

        # Create window box
        window_box = trimesh.creation.box(
            extents=[window_width, window_width, window_depth]
        )

        # Align box to implant direction
        transform = np.eye(4)
        transform[:3, 3] = window_center
        window_box.apply_transform(transform)

        # Subtract window
        result = result.difference(window_box, engine='manifold')

    return result
```

### Step 5: Mesh Validation and Repair

```python
def validate_guide(mesh: trimesh.Trimesh) -> dict:
    """
    Comprehensive validation for print-readiness.

    Returns dict with validation results and any issues found.
    """
    results = {
        'is_valid': True,
        'issues': [],
        'warnings': [],
        'metrics': {}
    }

    # 1. Watertight check (critical)
    if not mesh.is_watertight:
        results['is_valid'] = False
        results['issues'].append("Mesh is not watertight")

    # 2. Volume check
    if not mesh.is_volume:
        results['is_valid'] = False
        results['issues'].append("Mesh does not enclose a valid volume")

    # 3. Self-intersection check
    # Note: This can be slow for large meshes
    # trimesh doesn't have built-in self-intersection check
    # Use convex decomposition as proxy
    if not mesh.is_convex:
        # Not necessarily an issue, but flag for review
        results['warnings'].append("Mesh is non-convex (expected for surgical guide)")

    # 4. Degenerate faces
    degen_mask = mesh.area_faces < 1e-10
    if degen_mask.any():
        results['warnings'].append(f"Found {degen_mask.sum()} degenerate faces")

    # 5. Euler characteristic (should be 2 for closed surface)
    euler = len(mesh.vertices) - len(mesh.edges_unique) + len(mesh.faces)
    results['metrics']['euler_characteristic'] = euler
    if euler != 2:
        results['issues'].append(f"Euler characteristic is {euler}, expected 2")

    # 6. Minimum wall thickness (approximate)
    # Sample points on inner surface and check distance to nearest outer point
    # This is a simplified check
    results['metrics']['bounding_box'] = mesh.bounds.tolist()
    results['metrics']['volume_mm3'] = float(mesh.volume)
    results['metrics']['surface_area_mm2'] = float(mesh.area)
    results['metrics']['face_count'] = len(mesh.faces)
    results['metrics']['vertex_count'] = len(mesh.vertices)

    return results


def repair_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Attempt to repair non-manifold mesh using PyMeshLab.
    """
    try:
        import pymeshlab
    except ImportError:
        raise ImportError("PyMeshLab required for mesh repair: pip install pymeshlab")

    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))

    # Repair sequence
    ms.meshing_repair_non_manifold_edges()
    ms.meshing_repair_non_manifold_vertices()
    ms.meshing_close_holes(maxholesize=50)
    ms.meshing_remove_duplicate_faces()
    ms.meshing_remove_duplicate_vertices()

    # Optional: light smoothing to fix artifacts
    ms.apply_coord_laplacian_smoothing(stepsmoothnum=1, cotangentweight=False)

    repaired = ms.current_mesh()
    return trimesh.Trimesh(
        vertices=repaired.vertex_matrix(),
        faces=repaired.face_matrix()
    )
```

### Step 6: Export

```python
def export_guide(
    mesh: trimesh.Trimesh,
    output_path: str,
    validate: bool = True
) -> dict:
    """
    Export guide mesh with validation.

    Supports: .stl, .3mf, .ply
    Prefer .3mf as it includes units (mm) and is more compact.
    """
    if validate:
        validation = validate_guide(mesh)
        if not validation['is_valid']:
            raise ValueError(f"Guide validation failed: {validation['issues']}")

    # Ensure normals are outward-facing
    mesh.fix_normals()

    # Export
    mesh.export(output_path)

    return {
        'output_path': output_path,
        'validation': validation if validate else None
    }
```

---

## Complete Pipeline Function

```python
def generate_surgical_guide(
    ios_mesh_path: str,
    implant_sites: list,
    output_path: str,
    config: dict = None
) -> dict:
    """
    Main entry point for surgical guide generation.

    Args:
        ios_mesh_path: Path to segmented IOS mesh (STL)
        implant_sites: List of implant specifications, each containing:
            - position: [x, y, z] coordinates
            - direction: [dx, dy, dz] axis vector
            - sleeve_outer_diameter: float (mm)
            - sleeve_height: float (mm)
            - site_id: str (optional, e.g., FDI number)
        output_path: Output file path (.stl or .3mf)
        config: Optional configuration overrides

    Returns:
        Dict with output path, validation results, and metrics
    """
    # Default configuration
    cfg = {
        'thickness': 2.5,
        'tissue_gap': 0.15,
        'sleeve_clearance': 0.05,
        'voxel_size': 0.15,
        'add_inspection_windows': True,
        'window_width': 10.0,
    }
    if config:
        cfg.update(config)

    print(f"Loading IOS mesh from {ios_mesh_path}...")
    ios_mesh = load_ios_mesh(ios_mesh_path)
    print(f"  Loaded: {len(ios_mesh.vertices)} vertices, {len(ios_mesh.faces)} faces")

    print("Generating guide body (SDF offset)...")
    guide_body = create_guide_body_sdf(
        ios_mesh,
        thickness=cfg['thickness'],
        tissue_gap=cfg['tissue_gap'],
        voxel_size=cfg['voxel_size']
    )
    print(f"  Guide body: {len(guide_body.vertices)} vertices, {len(guide_body.faces)} faces")

    print(f"Subtracting {len(implant_sites)} sleeve channels...")
    guide = subtract_sleeve_channels(
        guide_body,
        implant_sites,
        clearance_map=None  # Use default clearance for all
    )

    if cfg.get('add_inspection_windows') and len(implant_sites) > 1:
        print("Adding inspection windows...")
        guide = add_inspection_windows(
            guide,
            implant_sites,
            window_width=cfg['window_width']
        )

    print("Validating guide mesh...")
    validation = validate_guide(guide)

    if not validation['is_valid']:
        print("  Attempting mesh repair...")
        guide = repair_mesh(guide)
        validation = validate_guide(guide)

    print(f"Exporting to {output_path}...")
    export_guide(guide, output_path, validate=False)

    print("Done!")
    return {
        'output_path': output_path,
        'validation': validation,
        'config_used': cfg
    }
```

---

## Clinical Parameters Reference

### Tolerances (Based on Published Research)

| Parameter | Value | Reference |
|-----------|-------|-----------|
| Drill-to-sleeve clearance | 50-150μm | Van Assche et al., 2012 |
| Sleeve length (recommended) | 5-7mm | Longer = less angular deviation |
| Guide thickness | 2.0-3.0mm | Structural integrity |
| Tissue gap | 0.1-0.2mm | Seating compensation |
| Min wall between sleeves | 3.0mm | Prevent fracture |
| Expected angular accuracy | 3-5° | With proper tolerances |
| Expected positional accuracy | 1.0-1.5mm at entry | System-dependent |

### Sleeve Specifications by System

**Straumann Fully Guided:**
- Outer diameter: 5.0mm
- Heights: 4.0, 5.0, 6.0mm
- Drill clearance: System-specific

**Nobel Biocare Guided:**
- Outer diameter: 5.0mm
- Heights: 4.0, 5.0mm

**Generic/Custom:**
- Adjust parameters based on manufacturer specs
- Always verify with physical test prints

### 3D Printing Recommendations

| Parameter | SLA/DLP Value | Notes |
|-----------|---------------|-------|
| Layer height | 50-100μm | Finer for better surface |
| XY resolution | 25-75μm | Printer-dependent |
| Print angle | 30-45° | Reduces surface stepping |
| Support density | Medium | Avoid supports in sleeve channels |
| Post-cure shrinkage | 0.5-2% | Calibrate hole diameters |
| Min wall thickness | 2.0mm | Per Formlabs Dental |

---

## File Structure Recommendation

```
surgical_guide_generator/
├── __init__.py
├── config.py              # Configuration dataclasses
├── mesh_io.py             # Load/export functions
├── sdf_offset.py          # SDF computation and offset
├── sleeve_channels.py     # Sleeve geometry creation
├── boolean_ops.py         # Boolean operation wrappers
├── inspection_windows.py  # Window feature generation
├── validation.py          # Mesh validation
├── repair.py              # Mesh repair utilities
├── generator.py           # Main pipeline orchestration
├── cli.py                 # Command-line interface
└── tests/
    ├── test_sdf_offset.py
    ├── test_boolean_ops.py
    ├── test_validation.py
    └── fixtures/
        ├── sample_ios.stl
        └── sample_implants.json
```

---

## Testing Approach

1. **Unit tests** for each component (SDF computation, transforms, validation)
2. **Integration test** with sample IOS mesh and known implant positions
3. **Visual inspection** of output in MeshLab/3D viewer
4. **Physical validation** with test prints and sleeve fit check

### Sample Test Data Format

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
      "sleeve_height": 5.0
    },
    {
      "site_id": "46",
      "position": [-24.8, -11.9, 9.1],
      "direction": [0.0, 0.08, -0.997],
      "implant_diameter": 4.1,
      "implant_length": 10.0,
      "sleeve_outer_diameter": 5.0,
      "sleeve_height": 5.0
    }
  ]
}
```

---

## Edge Cases to Handle

1. **Overlapping sleeve channels**: Check minimum spacing, error if too close
2. **Sleeve outside guide body**: Validate sleeve position intersects guide
3. **Very thin walls**: Warn if wall thickness falls below 2mm
4. **Non-watertight input**: Repair before processing
5. **Large meshes (>500k faces)**: Consider decimation or chunked processing
6. **Extreme implant angles**: Verify Boolean doesn't create artifacts

---

## Dependencies (requirements.txt)

```
numpy>=1.21.0
scipy>=1.7.0
trimesh>=3.21.0
manifold3d>=2.3.0
scikit-image>=0.19.0
pymeshlab>=2022.2
```

---

## Usage Example

```python
from surgical_guide_generator import generate_surgical_guide

implant_sites = [
    {
        "site_id": "36",
        "position": [25.5, -12.3, 8.7],
        "direction": [0.0, 0.1, -0.995],
        "sleeve_outer_diameter": 5.0,
        "sleeve_height": 5.0
    },
    {
        "site_id": "46",
        "position": [-24.8, -11.9, 9.1],
        "direction": [0.0, 0.08, -0.997],
        "sleeve_outer_diameter": 5.0,
        "sleeve_height": 5.0
    }
]

result = generate_surgical_guide(
    ios_mesh_path="patient_ios_segmented.stl",
    implant_sites=implant_sites,
    output_path="surgical_guide.3mf",
    config={
        "thickness": 2.5,
        "tissue_gap": 0.15,
        "sleeve_clearance": 0.05
    }
)

print(f"Guide saved to: {result['output_path']}")
print(f"Validation: {result['validation']}")
```

---

## Notes for Implementation

1. **Start with the SDF offset** - this is the most complex part
2. **Test Boolean operations** with simple geometries first
3. **Validate frequently** - check watertightness after each operation
4. **The manifold3d engine is critical** - don't use default trimesh Booleans
5. **Consider MeshLib** if trimesh SDF approach is too slow or unreliable
6. **Add extensive logging** for debugging failed cases
7. **Keep clinical parameters configurable** - different systems have different specs
