"""Generate simple test mesh fixtures for testing."""

import numpy as np
import trimesh
from pathlib import Path


def create_flat_surface(width: float = 60.0, depth: float = 40.0, thickness: float = 2.0) -> trimesh.Trimesh:
    """Create a simple flat rectangular surface.

    Args:
        width: Width in X direction (mm)
        depth: Depth in Y direction (mm)
        thickness: Thickness in Z direction (mm)

    Returns:
        Flat surface mesh
    """
    return trimesh.creation.box(extents=[width, depth, thickness])


def create_curved_ridge(length: float = 60.0, width: float = 12.0, height: float = 8.0,
                       curvature: float = 0.3) -> trimesh.Trimesh:
    """Create a curved ridge shape approximating a dental arch segment.

    Args:
        length: Length along the arch (mm)
        width: Ridge width (buccal-lingual) (mm)
        height: Ridge height (mm)
        curvature: Curvature parameter (0 = straight, 1 = very curved)

    Returns:
        Curved ridge mesh
    """
    # Create a curved path for the ridge
    num_points = 20
    x = np.linspace(-length/2, length/2, num_points)

    # Parabolic curve for arch shape
    y = -curvature * (x ** 2) / (length/2)
    z = np.zeros_like(x)

    # Create cross-section vertices at each point
    vertices = []
    faces = []

    for i, (xi, yi, zi) in enumerate(zip(x, y, z)):
        # Create rectangular cross-section at this point
        # Calculate tangent for orientation
        if i < len(x) - 1:
            dx = x[i+1] - xi
            dy = y[i+1] - yi
        else:
            dx = xi - x[i-1]
            dy = yi - y[i-1]

        # Perpendicular direction (for width)
        norm = np.sqrt(dx**2 + dy**2)
        perp_x = -dy / norm
        perp_y = dx / norm

        # Four corners of cross-section
        vertices.extend([
            [xi + perp_x * width/2, yi + perp_y * width/2, zi],
            [xi - perp_x * width/2, yi - perp_y * width/2, zi],
            [xi + perp_x * width/2, yi + perp_y * width/2, zi + height],
            [xi - perp_x * width/2, yi - perp_y * width/2, zi + height],
        ])

        # Create faces connecting to previous cross-section
        if i > 0:
            base = (i - 1) * 4
            # Bottom face
            faces.append([base, base+1, base+5])
            faces.append([base, base+5, base+4])

            # Top face
            faces.append([base+2, base+6, base+3])
            faces.append([base+3, base+6, base+7])

            # Left side
            faces.append([base, base+4, base+2])
            faces.append([base+2, base+4, base+6])

            # Right side
            faces.append([base+1, base+3, base+5])
            faces.append([base+5, base+3, base+7])

    # Create end caps
    # Front cap
    faces.extend([
        [0, 2, 1],
        [1, 2, 3]
    ])

    # Back cap
    last_base = (num_points - 1) * 4
    faces.extend([
        [last_base, last_base+1, last_base+2],
        [last_base+1, last_base+3, last_base+2]
    ])

    mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))

    # Fix normals and clean up
    mesh.fix_normals()
    mesh.merge_vertices()

    return mesh


def create_curved_arch(radius: float = 40.0, width: float = 12.0, height: float = 8.0,
                      arc_angle: float = 180.0) -> trimesh.Trimesh:
    """Create a curved arch shape.

    Args:
        radius: Radius of the arch curve (mm)
        width: Arch width (buccal-lingual) (mm)
        height: Arch height (mm)
        arc_angle: Angle of arc in degrees

    Returns:
        Curved arch mesh
    """
    num_segments = 30
    angles = np.linspace(-arc_angle/2, arc_angle/2, num_segments) * np.pi / 180

    vertices = []
    faces = []

    for i, angle in enumerate(angles):
        # Position on arc
        x = radius * np.sin(angle)
        y = -radius * np.cos(angle) + radius  # Offset to center

        # Radial direction (outward from center)
        radial_x = np.sin(angle)
        radial_y = -np.cos(angle)

        # Create rectangular cross-section
        vertices.extend([
            [x + radial_x * width/2, y + radial_y * width/2, 0],
            [x - radial_x * width/2, y - radial_y * width/2, 0],
            [x + radial_x * width/2, y + radial_y * width/2, height],
            [x - radial_x * width/2, y - radial_y * width/2, height],
        ])

        # Create faces
        if i > 0:
            base = (i - 1) * 4
            # Similar face construction as curved_ridge
            faces.append([base, base+1, base+5])
            faces.append([base, base+5, base+4])
            faces.append([base+2, base+6, base+3])
            faces.append([base+3, base+6, base+7])
            faces.append([base, base+4, base+2])
            faces.append([base+2, base+4, base+6])
            faces.append([base+1, base+3, base+5])
            faces.append([base+5, base+3, base+7])

    # End caps
    faces.extend([
        [0, 2, 1],
        [1, 2, 3]
    ])

    last_base = (num_segments - 1) * 4
    faces.extend([
        [last_base, last_base+1, last_base+2],
        [last_base+1, last_base+3, last_base+2]
    ])

    mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))
    mesh.fix_normals()
    mesh.merge_vertices()

    return mesh


def main():
    """Generate all test mesh fixtures."""
    output_dir = Path(__file__).parent

    print("Generating test mesh fixtures...")

    # Generate flat surface
    print("  - flat_surface.stl")
    flat = create_flat_surface(width=60.0, depth=40.0, thickness=2.0)
    flat.export(output_dir / "flat_surface.stl")

    # Generate curved ridge
    print("  - curved_ridge.stl")
    ridge = create_curved_ridge(length=60.0, width=12.0, height=8.0, curvature=0.3)
    ridge.export(output_dir / "curved_ridge.stl")

    # Generate curved arch
    print("  - curved_arch.stl")
    arch = create_curved_arch(radius=40.0, width=12.0, height=8.0, arc_angle=120.0)
    arch.export(output_dir / "curved_arch.stl")

    print("\nTest mesh fixtures generated successfully!")
    print(f"  Flat surface: {flat.faces.shape[0]} faces, {flat.volume:.1f} mm³")
    print(f"  Curved ridge: {ridge.faces.shape[0]} faces, {ridge.volume:.1f} mm³")
    print(f"  Curved arch: {arch.faces.shape[0]} faces, {arch.volume:.1f} mm³")


if __name__ == "__main__":
    main()
