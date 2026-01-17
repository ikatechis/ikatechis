"""Sleeve channel geometry creation for surgical guides."""

from typing import Tuple
import numpy as np
import numpy.typing as npt
import trimesh

from surgical_guide_generator.config import SleeveSpec


def compute_rotation_matrix(direction: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Compute rotation matrix to align Z-axis to given direction.

    Uses Rodrigues' rotation formula to compute the rotation matrix that
    transforms the Z-axis [0, 0, 1] to the given direction vector.

    Args:
        direction: Target direction vector (will be normalized)

    Returns:
        3x3 rotation matrix

    References:
        Rodrigues' rotation formula: https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
    """
    # Normalize direction
    direction = np.asarray(direction, dtype=np.float64)
    direction = direction / np.linalg.norm(direction)

    # Z-axis is the default cylinder orientation in trimesh
    z_axis = np.array([0.0, 0.0, 1.0])

    # Check if direction is already aligned with Z-axis
    if np.allclose(direction, z_axis):
        return np.eye(3)

    # Check if direction is opposite to Z-axis (-Z)
    if np.allclose(direction, -z_axis):
        # 180-degree rotation around X-axis
        return np.array([
            [1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0]
        ])

    # General case: use Rodrigues' formula
    # Rotation axis: cross product of z_axis and direction
    v = np.cross(z_axis, direction)
    s = np.linalg.norm(v)  # sine of angle
    c = np.dot(z_axis, direction)  # cosine of angle

    # Skew-symmetric cross-product matrix of v
    vx = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0]
    ])

    # Rodrigues' formula: R = I + vx + vx^2 * ((1-c)/s^2)
    rotation = np.eye(3) + vx + (vx @ vx) * ((1 - c) / (s * s + 1e-10))

    return rotation


def align_cylinder_to_direction(
    cylinder: trimesh.Trimesh,
    position: npt.NDArray[np.float64],
    direction: npt.NDArray[np.float64],
    offset_along_axis: float = 0.0,
) -> trimesh.Trimesh:
    """Align a cylinder mesh to a specific position and direction.

    Args:
        cylinder: Cylinder mesh (oriented along Z-axis by default)
        position: Position to place the cylinder
        direction: Direction to align the cylinder axis
        offset_along_axis: Offset along the direction axis (positive = further along direction)

    Returns:
        Transformed cylinder mesh
    """
    # Compute rotation matrix
    rotation = compute_rotation_matrix(direction)

    # Create 4x4 transformation matrix
    transform = np.eye(4)
    transform[:3, :3] = rotation

    # Position includes offset along direction
    direction_normalized = np.asarray(direction, dtype=np.float64)
    direction_normalized = direction_normalized / np.linalg.norm(direction_normalized)

    final_position = position + direction_normalized * offset_along_axis
    transform[:3, 3] = final_position

    # Apply transformation to cylinder
    aligned = cylinder.copy()
    aligned.apply_transform(transform)

    return aligned


def create_sleeve_channel(
    position: npt.NDArray[np.float64],
    direction: npt.NDArray[np.float64],
    sleeve_spec: SleeveSpec,
    extension: float = 2.0,
    sections: int = 64,
) -> trimesh.Trimesh:
    """Create a cylindrical channel for sleeve placement.

    Creates a cylinder mesh aligned to the implant axis for Boolean subtraction
    from the guide body. The cylinder includes clearance for the sleeve fit.

    Args:
        position: Implant platform center (entry point on guide surface)
        direction: Implant axis unit vector (pointing apical/into bone)
        sleeve_spec: Sleeve specifications including dimensions and clearance
        extension: Extra cylinder length beyond sleeve for clean Boolean cut (mm)
        sections: Number of faces around cylinder circumference (higher = smoother)

    Returns:
        Cylinder mesh positioned and oriented for Boolean subtraction

    Example:
        >>> spec = SleeveSpec(outer_diameter=5.0, inner_diameter=4.0, height=5.0)
        >>> position = np.array([25.0, -12.0, 8.0])
        >>> direction = np.array([0.0, 0.1, -0.995])
        >>> channel = create_sleeve_channel(position, direction, spec)
    """
    # Calculate channel dimensions
    # Channel diameter = sleeve outer diameter + clearance (on each side)
    channel_radius = (sleeve_spec.outer_diameter / 2.0) + sleeve_spec.clearance
    channel_height = sleeve_spec.height + extension

    # Create cylinder along Z-axis (trimesh default orientation)
    cylinder = trimesh.creation.cylinder(
        radius=channel_radius,
        height=channel_height,
        sections=sections
    )

    # Calculate offset along axis
    # Position cylinder so it:
    # 1. Starts slightly above guide surface (by extension/2)
    # 2. Extends through guide and beyond
    # Since cylinder is centered at origin, we offset by half its height
    # minus half the extension (so extension is at the top)
    offset = (channel_height / 2.0) - (extension / 2.0)

    # Align and position cylinder
    aligned = align_cylinder_to_direction(
        cylinder=cylinder,
        position=position,
        direction=direction,
        offset_along_axis=offset
    )

    return aligned
