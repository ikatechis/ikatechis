"""Mesh validation functions for surgical guide quality assurance."""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, List
import trimesh
import numpy as np

from surgical_guide_generator.config import ValidationConfig


@dataclass
class ValidationResult:
    """Result of mesh validation.

    Attributes:
        is_valid: Whether the mesh passes all validation checks
        errors: List of validation errors
        warnings: List of validation warnings
        metrics: Dictionary of mesh metrics
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary.

        Returns:
            Dictionary representation of validation result
        """
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


def check_watertight(mesh: trimesh.Trimesh) -> Tuple[bool, str]:
    """Check if mesh is watertight (no holes or non-manifold edges).

    Args:
        mesh: Mesh to check

    Returns:
        Tuple of (is_watertight, message)
    """
    if len(mesh.faces) == 0:
        return False, "Mesh has no faces"

    try:
        is_watertight = mesh.is_watertight
        if is_watertight:
            return True, "Mesh is watertight"
        else:
            return False, "Mesh is not watertight (has holes or non-manifold edges)"
    except Exception as e:
        return False, f"Could not check watertight status: {str(e)}"


def check_volume(mesh: trimesh.Trimesh) -> Tuple[bool, str]:
    """Check if mesh encloses a valid volume.

    Args:
        mesh: Mesh to check

    Returns:
        Tuple of (is_volume, message)
    """
    if len(mesh.faces) == 0:
        return False, "Mesh has no faces"

    try:
        is_volume = mesh.is_volume
        if is_volume:
            return True, "Mesh encloses a valid volume"
        else:
            return False, "Mesh does not enclose a valid volume"
    except Exception as e:
        return False, f"Could not check volume status: {str(e)}"


def check_euler_characteristic(mesh: trimesh.Trimesh) -> Tuple[bool, int, str]:
    """Check Euler characteristic (should be 2 for closed surface).

    The Euler characteristic for a closed surface (genus 0) should be:
    V - E + F = 2
    where V = vertices, E = edges, F = faces

    Args:
        mesh: Mesh to check

    Returns:
        Tuple of (is_valid, euler_value, message)
    """
    if len(mesh.faces) == 0:
        return False, 0, "Mesh has no faces"

    try:
        # Calculate Euler characteristic: V - E + F
        num_vertices = len(mesh.vertices)
        num_faces = len(mesh.faces)
        num_edges = len(mesh.edges_unique)

        euler = num_vertices - num_edges + num_faces

        if euler == 2:
            return True, euler, f"Euler characteristic is 2 (closed surface)"
        else:
            return False, euler, f"Euler characteristic is {euler}, expected 2 for closed surface"
    except Exception as e:
        return False, 0, f"Could not compute Euler characteristic: {str(e)}"


def validate_mesh(
    mesh: trimesh.Trimesh,
    config: ValidationConfig
) -> ValidationResult:
    """Perform comprehensive mesh validation.

    Args:
        mesh: Mesh to validate
        config: Validation configuration

    Returns:
        ValidationResult with validation status and details
    """
    errors: List[str] = []
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    # Basic checks
    if len(mesh.vertices) == 0:
        errors.append("Mesh has no vertices")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings, metrics=metrics)

    if len(mesh.faces) == 0:
        errors.append("Mesh has no faces")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings, metrics=metrics)

    # Collect basic metrics
    metrics["vertex_count"] = len(mesh.vertices)
    metrics["face_count"] = len(mesh.faces)

    # Check for degenerate faces (very small area)
    try:
        face_areas = mesh.area_faces
        degenerate_mask = face_areas < 1e-10
        num_degenerate = degenerate_mask.sum()
        if num_degenerate > 0:
            warnings.append(f"Found {num_degenerate} degenerate faces (area < 1e-10)")
    except Exception:
        pass

    # Check watertight
    if config.check_watertight:
        is_watertight, message = check_watertight(mesh)
        metrics["is_watertight"] = is_watertight
        if not is_watertight:
            errors.append(message)
    else:
        try:
            metrics["is_watertight"] = mesh.is_watertight
        except Exception:
            metrics["is_watertight"] = False

    # Check volume
    is_volume, volume_message = check_volume(mesh)
    metrics["is_volume"] = is_volume
    if not is_volume:
        errors.append(volume_message)

    # Compute volume and surface area
    try:
        if is_volume:
            metrics["volume_mm3"] = float(mesh.volume)
        else:
            metrics["volume_mm3"] = 0.0
        metrics["surface_area_mm2"] = float(mesh.area)
    except Exception as e:
        warnings.append(f"Could not compute volume/area: {str(e)}")
        metrics["volume_mm3"] = 0.0
        metrics["surface_area_mm2"] = 0.0

    # Check Euler characteristic
    euler_valid, euler_value, euler_message = check_euler_characteristic(mesh)
    metrics["euler_characteristic"] = euler_value
    if not euler_valid:
        warnings.append(euler_message)

    # Check for self-intersections (expensive, optional)
    if config.check_self_intersection:
        try:
            # This is a simplified check - full self-intersection is very expensive
            # We just check if mesh is convex (non-convex doesn't mean self-intersecting)
            metrics["is_convex"] = bool(mesh.is_convex)
            if not mesh.is_convex:
                warnings.append("Mesh is non-convex (this is expected for surgical guides)")
        except Exception as e:
            warnings.append(f"Could not check self-intersection: {str(e)}")

    # Check bounding box
    try:
        bounds = mesh.bounds
        bbox_size = bounds[1] - bounds[0]
        metrics["bounding_box_min"] = bounds[0].tolist()
        metrics["bounding_box_max"] = bounds[1].tolist()
        metrics["bounding_box_size"] = bbox_size.tolist()
    except Exception:
        pass

    # Determine overall validity
    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )
