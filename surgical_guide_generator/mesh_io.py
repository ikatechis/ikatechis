"""Mesh I/O functions for loading and exporting 3D meshes."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import trimesh
import numpy as np


# Supported file formats
SUPPORTED_LOAD_FORMATS = {'.stl', '.ply', '.obj', '.3mf'}
SUPPORTED_EXPORT_FORMATS = {'.stl', '.ply', '.3mf'}


@dataclass
class ExportResult:
    """Result of a mesh export operation.

    Attributes:
        success: Whether the export was successful
        file_path: Path to the exported file
        validation_passed: Whether validation passed (if enabled)
        metrics: Dictionary of mesh metrics (vertex count, face count, etc.)
        warnings: List of warning messages
    """

    success: bool
    file_path: str
    validation_passed: Optional[bool] = None
    metrics: Dict[str, Any] = None
    warnings: list = None

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.metrics is None:
            self.metrics = {}
        if self.warnings is None:
            self.warnings = []


def load_mesh(
    file_path: str,
    validate: bool = True,
    auto_repair: bool = True,
) -> trimesh.Trimesh:
    """Load a mesh from file with validation and optional repair.

    Args:
        file_path: Path to the mesh file
        validate: Whether to validate the loaded mesh
        auto_repair: Whether to attempt automatic repair of common issues

    Returns:
        Loaded and optionally repaired mesh

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file format is not supported or mesh is invalid
    """
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"Mesh file not found: {file_path}")

    # Check file format
    if path.suffix.lower() not in SUPPORTED_LOAD_FORMATS:
        raise ValueError(
            f"Unsupported file format: {path.suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_LOAD_FORMATS)}"
        )

    # Load mesh
    try:
        mesh = trimesh.load_mesh(str(path))
    except Exception as e:
        raise ValueError(f"Failed to load mesh from {file_path}: {str(e)}")

    # Ensure we have a Trimesh object, not a Scene
    if isinstance(mesh, trimesh.Scene):
        # If it's a scene with a single geometry, extract it
        if len(mesh.geometry) == 1:
            mesh = list(mesh.geometry.values())[0]
        else:
            raise ValueError(
                f"File contains multiple geometries ({len(mesh.geometry)}). "
                "Please provide a file with a single mesh."
            )

    # Auto-repair if enabled
    if auto_repair:
        mesh = _basic_repair(mesh)

    # Validate if requested
    if validate:
        _validate_loaded_mesh(mesh, file_path)

    return mesh


def _basic_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Perform basic mesh repair operations.

    Args:
        mesh: Input mesh

    Returns:
        Repaired mesh
    """
    # Skip repair if mesh has no faces
    if len(mesh.faces) == 0:
        return mesh

    # Merge duplicate vertices (helps with watertight check)
    mesh.merge_vertices()

    # Remove infinite values if any
    mesh.remove_infinite_values()

    # Remove NaN values if any
    mesh.remove_unreferenced_vertices()

    # Fix normals (make them consistent and outward-facing)
    try:
        mesh.fix_normals()
    except Exception:
        # If fix_normals fails, continue anyway
        pass

    return mesh


def _validate_loaded_mesh(mesh: trimesh.Trimesh, file_path: str) -> None:
    """Validate that a loaded mesh has basic required properties.

    Args:
        mesh: Mesh to validate
        file_path: Path to the file (for error messages)

    Raises:
        ValueError: If mesh validation fails
    """
    if len(mesh.vertices) == 0:
        raise ValueError(f"Mesh from {file_path} has no vertices")

    if len(mesh.faces) == 0:
        raise ValueError(f"Mesh from {file_path} has no faces")

    # Check for valid face indices
    max_vertex_index = len(mesh.vertices) - 1
    if mesh.faces.max() > max_vertex_index:
        raise ValueError(
            f"Mesh from {file_path} has invalid face indices "
            f"(max index: {mesh.faces.max()}, max valid: {max_vertex_index})"
        )


def export_mesh(
    mesh: trimesh.Trimesh,
    file_path: str,
    validate: bool = False,
    fix_normals: bool = True,
) -> ExportResult:
    """Export a mesh to file with optional validation.

    Args:
        mesh: Mesh to export
        file_path: Output file path
        validate: Whether to validate the mesh before export
        fix_normals: Whether to fix normals before export

    Returns:
        ExportResult with success status and metrics

    Raises:
        ValueError: If validation fails or format is not supported
    """
    path = Path(file_path)

    # Check file format
    if path.suffix.lower() not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format: {path.suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_EXPORT_FORMATS)}"
        )

    # Create parent directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Fix normals if requested
    if fix_normals and len(mesh.faces) > 0:
        mesh = mesh.copy()
        try:
            mesh.fix_normals()
        except Exception:
            # If fix_normals fails, continue without fixing
            pass

    # Validate if requested
    validation_passed = None
    if validate:
        try:
            _validate_export_mesh(mesh)
            validation_passed = True
        except ValueError as e:
            raise ValueError(f"Mesh validation failed: {str(e)}")

    # Collect metrics (with safe checks for empty meshes)
    metrics = {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
    }

    # Only compute these metrics if mesh has faces
    if len(mesh.faces) > 0:
        try:
            metrics["is_watertight"] = bool(mesh.is_watertight)
            metrics["is_volume"] = bool(mesh.is_volume)
            metrics["volume_mm3"] = float(mesh.volume) if metrics["is_volume"] else 0.0
            metrics["surface_area_mm2"] = float(mesh.area)
        except Exception:
            # If any metric computation fails, use safe defaults
            metrics["is_watertight"] = False
            metrics["is_volume"] = False
            metrics["volume_mm3"] = 0.0
            metrics["surface_area_mm2"] = 0.0
    else:
        metrics["is_watertight"] = False
        metrics["is_volume"] = False
        metrics["volume_mm3"] = 0.0
        metrics["surface_area_mm2"] = 0.0

    # Export
    try:
        mesh.export(str(path))
    except Exception as e:
        return ExportResult(
            success=False,
            file_path=str(path),
            validation_passed=validation_passed,
            metrics=metrics,
            warnings=[f"Export failed: {str(e)}"],
        )

    return ExportResult(
        success=True,
        file_path=str(path),
        validation_passed=validation_passed,
        metrics=metrics,
    )


def _validate_export_mesh(mesh: trimesh.Trimesh) -> None:
    """Validate mesh before export.

    Args:
        mesh: Mesh to validate

    Raises:
        ValueError: If mesh is not valid for export
    """
    if len(mesh.vertices) == 0:
        raise ValueError("Mesh has no vertices")

    if len(mesh.faces) == 0:
        raise ValueError("Mesh has no faces")

    if not mesh.is_volume:
        raise ValueError("Mesh does not enclose a valid volume")

    if not mesh.is_watertight:
        raise ValueError("Mesh is not watertight (has holes or non-manifold edges)")
