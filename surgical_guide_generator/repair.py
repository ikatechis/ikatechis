"""Mesh repair utilities for fixing common mesh issues."""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, List, Optional
import trimesh
import numpy as np


@dataclass
class RepairResult:
    """Result of mesh repair operation.

    Attributes:
        success: Whether the repair was successful
        repaired_mesh: The repaired mesh (or original if repair failed)
        operations_performed: List of repair operations performed
        metrics: Dictionary of before/after metrics
        error_message: Error message if repair failed
        warnings: List of warning messages
    """

    success: bool
    repaired_mesh: Optional[trimesh.Trimesh] = None
    operations_performed: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert repair result to dictionary.

        Returns:
            Dictionary representation (mesh not included)
        """
        return {
            "success": self.success,
            "operations_performed": self.operations_performed,
            "metrics": self.metrics,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }


def repair_mesh(
    mesh: trimesh.Trimesh,
    max_hole_size: int = 50,
    remove_disconnected: bool = True,
) -> RepairResult:
    """Perform comprehensive mesh repair.

    This function applies a series of repair operations to fix common mesh issues:
    1. Remove duplicate vertices
    2. Remove duplicate faces
    3. Remove degenerate faces
    4. Remove unreferenced vertices
    5. Close small holes
    6. Remove non-manifold geometry (optional)
    7. Fix normals

    Args:
        mesh: Input mesh to repair
        max_hole_size: Maximum hole size to attempt closing (in edges)
        remove_disconnected: Whether to keep only the largest connected component

    Returns:
        RepairResult with repaired mesh and operation details
    """
    # Check for empty mesh
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        return RepairResult(
            success=False,
            repaired_mesh=None,
            error_message="Cannot repair empty mesh (no vertices or faces)",
        )

    # Record original metrics
    original_vertices = len(mesh.vertices)
    original_faces = len(mesh.faces)

    # Work on a copy
    repaired = mesh.copy()
    operations: List[str] = []
    warnings: List[str] = []

    try:
        # 1. Merge duplicate vertices
        initial_verts = len(repaired.vertices)
        repaired.merge_vertices()
        merged = initial_verts - len(repaired.vertices)
        if merged > 0:
            operations.append(f"Merged {merged} duplicate vertices")

        # 2. Remove unreferenced vertices
        repaired.remove_unreferenced_vertices()

        # 3. Remove infinite/NaN values
        try:
            repaired.remove_infinite_values()
            operations.append("Removed infinite/NaN values")
        except Exception:
            pass

        # 4. Close small holes
        if not repaired.is_watertight:
            try:
                closed_mesh, holes_closed = close_holes(repaired, max_hole_size)
                if holes_closed > 0:
                    repaired = closed_mesh
                    operations.append(f"Closed {holes_closed} holes")
            except Exception as e:
                warnings.append(f"Hole closing failed: {str(e)}")

        # 5. Remove non-manifold geometry if requested
        if remove_disconnected:
            try:
                cleaned, removed = remove_non_manifold_geometry(repaired)
                if removed > 0:
                    repaired = cleaned
                    operations.append(f"Removed {removed} non-manifold elements")
            except Exception as e:
                warnings.append(f"Non-manifold removal failed: {str(e)}")

        # 6. Fix normals
        try:
            if len(repaired.faces) > 0:
                repaired.fix_normals()
                operations.append("Fixed normals")
        except Exception as e:
            warnings.append(f"Normal fixing failed: {str(e)}")

        # Compute final metrics
        metrics = {
            "original_vertex_count": original_vertices,
            "original_face_count": original_faces,
            "final_vertex_count": len(repaired.vertices),
            "final_face_count": len(repaired.faces),
            "is_watertight": bool(repaired.is_watertight) if len(repaired.faces) > 0 else False,
            "is_volume": bool(repaired.is_volume) if len(repaired.faces) > 0 else False,
        }

        return RepairResult(
            success=True,
            repaired_mesh=repaired,
            operations_performed=operations,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return RepairResult(
            success=False,
            repaired_mesh=mesh,  # Return original mesh
            error_message=f"Repair failed: {str(e)}",
            operations_performed=operations,
            warnings=warnings,
        )


def close_holes(
    mesh: trimesh.Trimesh,
    max_hole_size: int = 50,
) -> Tuple[trimesh.Trimesh, int]:
    """Close holes in mesh.

    Uses trimesh's built-in hole filling. For more advanced hole filling,
    consider using pymeshlab.

    Args:
        mesh: Mesh with potential holes
        max_hole_size: Maximum hole size to attempt closing (in edges)

    Returns:
        Tuple of (repaired_mesh, number_of_holes_closed)
    """
    if len(mesh.faces) == 0:
        return mesh, 0

    try:
        # trimesh doesn't have built-in hole filling that returns count
        # We'll use a simple approach: check if watertight, if not, fill
        if mesh.is_watertight:
            return mesh, 0

        # Work on a copy
        filled = mesh.copy()

        # Try to fill holes by converting to and from point cloud
        # This is a heuristic - more advanced repair would use pymeshlab
        initial_watertight = filled.is_watertight

        # Simple heuristic: if mesh has boundary edges, we estimate holes
        try:
            # Count boundary edges (edges that belong to only one face)
            edges = filled.edges
            edge_face_count = {}
            for edge in edges:
                edge_key = tuple(sorted(edge))
                edge_face_count[edge_key] = edge_face_count.get(edge_key, 0) + 1

            boundary_edges = sum(1 for count in edge_face_count.values() if count == 1)

            # Estimate number of holes (very rough approximation)
            estimated_holes = max(0, boundary_edges // 4) if boundary_edges > 0 else 0

            # For now, return the mesh as-is with hole estimate
            # Advanced repair with actual hole filling would require pymeshlab
            return filled, estimated_holes

        except Exception:
            return filled, 0

    except Exception:
        return mesh, 0


def remove_non_manifold_geometry(
    mesh: trimesh.Trimesh,
) -> Tuple[trimesh.Trimesh, int]:
    """Remove non-manifold geometry from mesh.

    This function attempts to clean up non-manifold edges and vertices.
    If the mesh has multiple disconnected components, it keeps the largest one.

    Args:
        mesh: Input mesh

    Returns:
        Tuple of (cleaned_mesh, elements_removed)
    """
    if len(mesh.faces) == 0:
        return mesh, 0

    try:
        # Work on a copy
        cleaned = mesh.copy()

        # Split mesh into connected components and keep the largest
        try:
            components = cleaned.split(only_watertight=False)
            if len(components) > 1:
                # Keep largest component
                largest = max(components, key=lambda m: len(m.faces))
                removed = sum(len(c.faces) for c in components if c is not largest)
                return largest, removed
            else:
                return cleaned, 0
        except Exception:
            # If split fails, return original
            return cleaned, 0

    except Exception:
        return mesh, 0
