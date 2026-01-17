"""Boolean operations wrapper using manifold3d for reliable CSG.

This module provides a clean interface to Boolean operations (difference, union,
intersection) using the manifold3d engine through trimesh. The manifold3d engine
is critical for producing guaranteed manifold (watertight) output.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import trimesh
import numpy as np


@dataclass
class BooleanResult:
    """Result of a Boolean operation.

    Attributes:
        success: Whether the operation completed successfully
        operation: Name of the operation performed
        result_mesh: The resulting mesh (None if failed)
        metrics: Dictionary of operation metrics
        error_message: Error message if operation failed
        warnings: List of warning messages
    """

    success: bool
    operation: str
    result_mesh: Optional[trimesh.Trimesh] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    warnings: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary (excluding mesh).

        Returns:
            Dictionary representation of the result
        """
        return {
            "success": self.success,
            "operation": self.operation,
            "metrics": self.metrics,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }


def boolean_difference(
    mesh_a: trimesh.Trimesh,
    mesh_b: trimesh.Trimesh,
    engine: str = "manifold",
) -> BooleanResult:
    """Compute Boolean difference (A - B).

    Subtracts mesh_b from mesh_a. This is used for creating channels by
    subtracting cylinders from the guide body.

    Args:
        mesh_a: Base mesh
        mesh_b: Mesh to subtract from base
        engine: Boolean engine to use (default: 'manifold' for guaranteed watertight)

    Returns:
        BooleanResult with the difference mesh

    Example:
        >>> guide_body = trimesh.creation.box(extents=[50, 30, 10])
        >>> channel = trimesh.creation.cylinder(radius=2.5, height=15)
        >>> result = boolean_difference(guide_body, channel)
        >>> guide_with_hole = result.result_mesh
    """
    # Record original metrics
    original_volume = float(mesh_a.volume) if mesh_a.is_volume else 0.0

    try:
        # Perform Boolean difference using manifold engine
        result_mesh = mesh_a.difference(mesh_b, engine=engine)

        # Check if result is valid
        if result_mesh is None or len(result_mesh.faces) == 0:
            return BooleanResult(
                success=False,
                operation="difference",
                error_message="Boolean difference produced empty result",
            )

        # Compute metrics
        result_volume = float(result_mesh.volume) if result_mesh.is_volume else 0.0
        metrics = {
            "original_volume": original_volume,
            "result_volume": result_volume,
            "volume_removed": original_volume - result_volume,
            "is_watertight": bool(result_mesh.is_watertight),
            "face_count": len(result_mesh.faces),
            "vertex_count": len(result_mesh.vertices),
        }

        warnings = []
        if not result_mesh.is_watertight:
            warnings.append("Result mesh is not watertight")

        return BooleanResult(
            success=True,
            operation="difference",
            result_mesh=result_mesh,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return BooleanResult(
            success=False,
            operation="difference",
            error_message=f"Boolean difference failed: {str(e)}",
        )


def boolean_union(
    mesh_a: trimesh.Trimesh,
    mesh_b: trimesh.Trimesh,
    engine: str = "manifold",
) -> BooleanResult:
    """Compute Boolean union (A ∪ B).

    Combines mesh_a and mesh_b into a single mesh. This is used for combining
    inner and outer surfaces into a guide shell.

    Args:
        mesh_a: First mesh
        mesh_b: Second mesh
        engine: Boolean engine to use (default: 'manifold')

    Returns:
        BooleanResult with the union mesh

    Example:
        >>> inner_surface = create_offset_surface(ios_mesh, offset=0.15)
        >>> outer_surface = create_offset_surface(ios_mesh, offset=2.5)
        >>> result = boolean_union(inner_surface, outer_surface)
        >>> guide_shell = result.result_mesh
    """
    # Record original metrics
    volume_a = float(mesh_a.volume) if mesh_a.is_volume else 0.0
    volume_b = float(mesh_b.volume) if mesh_b.is_volume else 0.0

    try:
        # Perform Boolean union using manifold engine
        result_mesh = mesh_a.union(mesh_b, engine=engine)

        # Check if result is valid
        if result_mesh is None or len(result_mesh.faces) == 0:
            return BooleanResult(
                success=False,
                operation="union",
                error_message="Boolean union produced empty result",
            )

        # Compute metrics
        result_volume = float(result_mesh.volume) if result_mesh.is_volume else 0.0
        metrics = {
            "volume_a": volume_a,
            "volume_b": volume_b,
            "result_volume": result_volume,
            "overlap_volume": (volume_a + volume_b) - result_volume,
            "is_watertight": bool(result_mesh.is_watertight),
            "face_count": len(result_mesh.faces),
            "vertex_count": len(result_mesh.vertices),
        }

        warnings = []
        if not result_mesh.is_watertight:
            warnings.append("Result mesh is not watertight")

        return BooleanResult(
            success=True,
            operation="union",
            result_mesh=result_mesh,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return BooleanResult(
            success=False,
            operation="union",
            error_message=f"Boolean union failed: {str(e)}",
        )


def boolean_intersection(
    mesh_a: trimesh.Trimesh,
    mesh_b: trimesh.Trimesh,
    engine: str = "manifold",
) -> BooleanResult:
    """Compute Boolean intersection (A ∩ B).

    Returns only the volume where mesh_a and mesh_b overlap.

    Args:
        mesh_a: First mesh
        mesh_b: Second mesh
        engine: Boolean engine to use (default: 'manifold')

    Returns:
        BooleanResult with the intersection mesh
    """
    # Record original metrics
    volume_a = float(mesh_a.volume) if mesh_a.is_volume else 0.0
    volume_b = float(mesh_b.volume) if mesh_b.is_volume else 0.0

    try:
        # Perform Boolean intersection using manifold engine
        result_mesh = mesh_a.intersection(mesh_b, engine=engine)

        # Check if result is valid
        if result_mesh is None or len(result_mesh.faces) == 0:
            # Non-overlapping meshes produce empty intersection
            # This is valid, not necessarily an error
            return BooleanResult(
                success=True,
                operation="intersection",
                result_mesh=result_mesh,
                metrics={
                    "volume_a": volume_a,
                    "volume_b": volume_b,
                    "result_volume": 0.0,
                    "is_watertight": False,
                    "face_count": 0,
                    "vertex_count": 0,
                },
                warnings=["Meshes do not overlap - empty intersection"],
            )

        # Compute metrics
        result_volume = float(result_mesh.volume) if result_mesh.is_volume else 0.0
        metrics = {
            "volume_a": volume_a,
            "volume_b": volume_b,
            "result_volume": result_volume,
            "is_watertight": bool(result_mesh.is_watertight),
            "face_count": len(result_mesh.faces),
            "vertex_count": len(result_mesh.vertices),
        }

        warnings = []
        if not result_mesh.is_watertight:
            warnings.append("Result mesh is not watertight")

        return BooleanResult(
            success=True,
            operation="intersection",
            result_mesh=result_mesh,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return BooleanResult(
            success=False,
            operation="intersection",
            error_message=f"Boolean intersection failed: {str(e)}",
        )
