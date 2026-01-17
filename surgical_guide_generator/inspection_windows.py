"""Inspection window features for multi-implant surgical guides.

Inspection windows are cutouts in the guide that allow the surgeon to
visually verify proper seating on the tissue during placement.
"""

from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import trimesh

from surgical_guide_generator.config import ImplantSite
from surgical_guide_generator.boolean_ops import boolean_difference


def compute_window_position(
    implant_position: npt.NDArray[np.float64],
    implant_direction: npt.NDArray[np.float64],
    sleeve_outer_diameter: float,
    margin_from_sleeve: float = 3.0,
    preferred_side: str = "buccal",
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Compute position and orientation for an inspection window.

    Windows are placed on the buccal/labial side of the implant to allow
    visual verification of guide seating.

    Args:
        implant_position: Implant platform center coordinates
        implant_direction: Implant axis unit vector (pointing apical)
        sleeve_outer_diameter: Outer diameter of sleeve in mm
        margin_from_sleeve: Minimum distance from sleeve edge to window in mm
        preferred_side: Preferred side for window ("buccal" or "lingual")

    Returns:
        Tuple of (window_position, window_normal)
        - window_position: Center of the window
        - window_normal: Normal vector pointing outward from guide

    Example:
        >>> pos = np.array([10.0, 5.0, 3.0])
        >>> dir = np.array([0.0, 0.0, -1.0])
        >>> window_pos, normal = compute_window_position(pos, dir, 5.0)
    """
    # Normalize direction
    direction = np.asarray(implant_direction, dtype=np.float64)
    direction = direction / np.linalg.norm(direction)

    # Find a perpendicular direction for window placement
    # We want a vector perpendicular to the implant axis
    # Prefer the +X direction (buccal) if available

    # If direction is mostly vertical, use X as perpendicular
    if np.abs(direction[2]) > 0.9:
        perpendicular = np.array([1.0, 0.0, 0.0])
    else:
        # Otherwise, cross with Z to get a horizontal perpendicular
        perpendicular = np.cross(direction, np.array([0.0, 0.0, 1.0]))
        perpendicular = perpendicular / np.linalg.norm(perpendicular)

    # For lingual side, reverse the perpendicular
    if preferred_side == "lingual":
        perpendicular = -perpendicular

    # Calculate window center position
    # Place it at: sleeve_radius + margin + window_width/2
    # For simplicity, we'll place it at sleeve_radius + margin
    offset_distance = (sleeve_outer_diameter / 2.0) + margin_from_sleeve

    window_position = implant_position + perpendicular * offset_distance

    # Window normal is the same as the perpendicular direction
    window_normal = perpendicular

    return window_position, window_normal


def create_inspection_window(
    position: npt.NDArray[np.float64],
    normal: npt.NDArray[np.float64],
    width: float = 10.0,
    depth: float = 5.0,
) -> trimesh.Trimesh:
    """Create a box-shaped inspection window.

    Args:
        position: Center position of the window
        normal: Normal vector (direction the window faces)
        width: Width of the window opening in mm
        depth: Depth of the window (how far it extends into guide) in mm

    Returns:
        Box mesh positioned and oriented for Boolean subtraction

    Example:
        >>> pos = np.array([15.0, 0.0, 5.0])
        >>> normal = np.array([1.0, 0.0, 0.0])
        >>> window = create_inspection_window(pos, normal, width=10.0, depth=5.0)
    """
    # Normalize normal vector
    normal = np.asarray(normal, dtype=np.float64)
    normal = normal / np.linalg.norm(normal)

    # Create a box
    # The box will be width x width x depth
    box = trimesh.creation.box(extents=[width, width, depth])

    # Compute rotation to align box's Z-axis with the normal
    # Box default orientation has Z pointing up
    z_axis = np.array([0.0, 0.0, 1.0])

    # Check if normal is already aligned with Z
    if np.allclose(normal, z_axis):
        rotation = np.eye(3)
    elif np.allclose(normal, -z_axis):
        # 180-degree rotation around X
        rotation = np.array([
            [1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0]
        ])
    else:
        # Rodrigues' rotation formula
        v = np.cross(z_axis, normal)
        s = np.linalg.norm(v)
        c = np.dot(z_axis, normal)

        vx = np.array([
            [0.0, -v[2], v[1]],
            [v[2], 0.0, -v[0]],
            [-v[1], v[0], 0.0]
        ])

        rotation = np.eye(3) + vx + (vx @ vx) * ((1 - c) / (s * s + 1e-10))

    # Create transformation matrix
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = position

    # Apply transformation
    box.apply_transform(transform)

    return box


def add_inspection_windows(
    guide_mesh: trimesh.Trimesh,
    implant_sites: List[ImplantSite],
    window_width: float = 10.0,
    window_depth: float = 5.0,
    margin_from_sleeve: float = 3.0,
    add_windows: bool = True,
) -> trimesh.Trimesh:
    """Add inspection windows to a surgical guide mesh.

    Windows are added near each implant site to allow visual verification
    of proper guide seating during surgery.

    Args:
        guide_mesh: The guide body mesh
        implant_sites: List of implant site specifications
        window_width: Width of each window opening in mm
        window_depth: Depth of each window in mm
        margin_from_sleeve: Minimum distance from sleeve edge to window in mm
        add_windows: Whether to add windows (can be disabled for single implants)

    Returns:
        Guide mesh with windows subtracted

    Example:
        >>> guide = create_guide_body(...)
        >>> sites = [ImplantSite(...), ImplantSite(...)]
        >>> guide_with_windows = add_inspection_windows(guide, sites)
    """
    # If no windows requested or no implants, return original
    if not add_windows or len(implant_sites) == 0:
        return guide_mesh

    # For single implant, windows are typically not needed
    # But we'll add them if explicitly requested
    if len(implant_sites) == 1 and not add_windows:
        return guide_mesh

    # Work on a copy
    result = guide_mesh.copy()

    # Add window for each implant site
    for site in implant_sites:
        # Compute window position and orientation
        window_pos, window_normal = compute_window_position(
            implant_position=np.array(site.position),
            implant_direction=np.array(site.direction),
            sleeve_outer_diameter=site.sleeve_spec.outer_diameter,
            margin_from_sleeve=margin_from_sleeve,
        )

        # Create window box
        window = create_inspection_window(
            position=window_pos,
            normal=window_normal,
            width=window_width,
            depth=window_depth,
        )

        # Subtract window from guide
        bool_result = boolean_difference(result, window)

        if bool_result.success and bool_result.result_mesh is not None:
            result = bool_result.result_mesh
        else:
            # If Boolean operation failed, continue without this window
            # This could happen if window doesn't intersect guide
            pass

    return result
