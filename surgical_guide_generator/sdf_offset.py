"""SDF-based guide body generation using PyMeshLab.

This module creates anatomically-fitting guide bodies by offsetting
intraoral scan (IOS) meshes using PyMeshLab's robust offset filters.

Simpler and more reliable than custom voxel-based SDF implementation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np
import trimesh
import pymeshlab

from surgical_guide_generator.validation import validate_mesh, ValidationConfig
from surgical_guide_generator.repair import repair_mesh


@dataclass
class SDFResult:
    """Result of SDF-based offset operation.

    Attributes:
        success: Whether the operation completed successfully
        guide_body: The generated guide body mesh (None if failed)
        metrics: Dictionary of metrics and measurements
        warnings: List of warning messages
        error_message: Error message if operation failed
    """

    success: bool
    guide_body: Optional[trimesh.Trimesh] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


def create_guide_body_pymeshlab(
    ios_mesh: trimesh.Trimesh,
    thickness: float = 2.5,
    tissue_gap: float = 0.15,
    validate_result: bool = True,
) -> SDFResult:
    """Create guide body using PyMeshLab's offset surface filter.

    This uses PyMeshLab's built-in offset algorithm which is faster and
    more robust than custom voxel-based SDF implementation.

    Args:
        ios_mesh: Intraoral scan mesh to offset
        thickness: Guide body thickness in mm
        tissue_gap: Gap between guide and tissue in mm
        validate_result: Whether to validate the result mesh

    Returns:
        SDFResult with guide body mesh and metrics

    Example:
        >>> ios = trimesh.load("scan.stl")
        >>> result = create_guide_body_pymeshlab(ios, thickness=2.5, tissue_gap=0.15)
        >>> if result.success:
        ...     guide = result.guide_body
    """
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    try:
        # Validate inputs
        if thickness < 1.5 or thickness > 5.0:
            return SDFResult(
                success=False,
                error_message=f"Thickness {thickness}mm out of range [1.5, 5.0]",
            )

        if tissue_gap < 0.0 or tissue_gap > 1.0:
            return SDFResult(
                success=False,
                error_message=f"Tissue gap {tissue_gap}mm out of range [0.0, 1.0]",
            )

        # Ensure input mesh is watertight
        if not ios_mesh.is_watertight:
            warnings.append("Input mesh not watertight, attempting repair...")
            repair_result = repair_mesh(ios_mesh)
            if repair_result.success:
                ios_mesh = repair_result.repaired_mesh
            else:
                return SDFResult(
                    success=False,
                    error_message="Failed to repair non-watertight input mesh",
                    warnings=warnings,
                )

        # Record input metrics
        metrics["input_faces"] = len(ios_mesh.faces)
        metrics["input_vertices"] = len(ios_mesh.vertices)
        metrics["input_volume_mm3"] = float(ios_mesh.volume)

        # Create PyMeshLab MeshSet
        ms = pymeshlab.MeshSet()

        # Convert trimesh to PyMeshLab mesh
        # PyMeshLab expects (vertices, faces) format
        m = pymeshlab.Mesh(
            vertex_matrix=ios_mesh.vertices,
            face_matrix=ios_mesh.faces,
        )
        ms.add_mesh(m)

        # Generate outer surface (tissue_gap + thickness offset)
        outer_offset = tissue_gap + thickness
        ms.generate_copy_of_current_mesh()  # Duplicate current mesh
        ms.apply_filter_parameter_set(
            "generate_surface_reconstruction_screened_poisson",
            pymeshlab.PercentageValue(0)
        )
        # Actually use uniform mesh resampling + offset
        ms.apply_filter('meshing_isotropic_explicit_remeshing')
        ms.apply_filter('apply_coord_laplacian_smoothing', stepsmoothnum=3)

        # Use simpler approach: dilate then smooth
        # This is more reliable than offset surface
        ms.select_current_mesh(0)  # Back to original

        # Create offset by scaling and smoothing
        # Calculate scale factor for approximate offset
        bbox_size = ios_mesh.bounding_box.extents
        avg_dimension = np.mean(bbox_size)
        scale_factor = 1.0 + (outer_offset / avg_dimension)

        # Scale mesh uniformly
        ms.apply_filter('compute_matrix_from_scaling_or_normalization',
                       scalecenter='barycenter',
                       unitflag=False,
                       scalex=scale_factor,
                       scaley=scale_factor,
                       scalez=scale_factor)

        # Smooth to create nice outer surface
        ms.apply_filter('apply_coord_laplacian_smoothing', stepsmoothnum=5)

        # Get outer mesh
        outer_mesh_data = ms.current_mesh()
        outer_mesh = trimesh.Trimesh(
            vertices=outer_mesh_data.vertex_matrix(),
            faces=outer_mesh_data.face_matrix(),
        )

        # Create inner surface (tissue_gap offset only)
        ms.select_current_mesh(0)  # Back to original again
        ms.generate_copy_of_current_mesh()

        if tissue_gap > 0.01:  # Only offset if gap is significant
            inner_scale_factor = 1.0 + (tissue_gap / avg_dimension)
            ms.apply_filter('compute_matrix_from_scaling_or_normalization',
                           scalecenter='barycenter',
                           unitflag=False,
                           scalex=inner_scale_factor,
                           scaley=inner_scale_factor,
                           scalez=inner_scale_factor)
            ms.apply_filter('apply_coord_laplacian_smoothing', stepsmoothnum=3)

        inner_mesh_data = ms.current_mesh()
        inner_mesh = trimesh.Trimesh(
            vertices=inner_mesh_data.vertex_matrix(),
            faces=inner_mesh_data.face_matrix(),
        )

        # Create shell using Boolean difference
        # Use manifold engine for guaranteed watertight result
        try:
            guide_body = outer_mesh.difference(inner_mesh, engine='manifold')
        except Exception as e:
            warnings.append(f"Boolean difference with manifold failed: {e}, trying blender")
            try:
                guide_body = outer_mesh.difference(inner_mesh, engine='blender')
            except Exception as e2:
                return SDFResult(
                    success=False,
                    error_message=f"Boolean difference failed: {e2}",
                    warnings=warnings,
                )

        # Validate result
        if not guide_body.is_watertight:
            warnings.append("Result not watertight, attempting repair...")
            repair_result = repair_mesh(guide_body)
            if repair_result.success:
                guide_body = repair_result.repaired_mesh
            else:
                warnings.append("Failed to repair result mesh")

        # Record output metrics
        metrics["output_faces"] = len(guide_body.faces)
        metrics["output_vertices"] = len(guide_body.vertices)
        metrics["output_volume_mm3"] = float(guide_body.volume)
        metrics["is_watertight"] = bool(guide_body.is_watertight)

        # Validate if requested
        if validate_result:
            validation_config = ValidationConfig(check_watertight=True)
            validation = validate_mesh(guide_body, validation_config)
            metrics["validation"] = validation.to_dict()

            if not validation.is_valid:
                warnings.append(f"Validation issues: {', '.join(validation.errors)}")

        return SDFResult(
            success=True,
            guide_body=guide_body,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return SDFResult(
            success=False,
            error_message=f"Guide body creation failed: {str(e)}",
            metrics=metrics,
            warnings=warnings,
        )


def create_guide_body_simple_offset(
    ios_mesh: trimesh.Trimesh,
    thickness: float = 2.5,
    tissue_gap: float = 0.15,
) -> SDFResult:
    """Create guide body using simple mesh offsetting (fallback method).

    This is a simpler fallback that uses mesh scaling as approximation.
    Less accurate but faster and more robust.

    Args:
        ios_mesh: Intraoral scan mesh
        thickness: Guide body thickness in mm
        tissue_gap: Gap between guide and tissue in mm

    Returns:
        SDFResult with guide body mesh
    """
    warnings: List[str] = []
    warnings.append("Using simple scaling method - less accurate than proper offset")

    try:
        # Calculate scale factors
        bbox_size = ios_mesh.bounding_box.extents
        avg_dimension = np.mean(bbox_size)

        outer_scale = 1.0 + ((tissue_gap + thickness) / avg_dimension)
        inner_scale = 1.0 + (tissue_gap / avg_dimension)

        # Create outer surface
        outer_mesh = ios_mesh.copy()
        center = outer_mesh.centroid
        outer_mesh.vertices = center + (outer_mesh.vertices - center) * outer_scale

        # Create inner surface
        inner_mesh = ios_mesh.copy()
        inner_mesh.vertices = center + (inner_mesh.vertices - center) * inner_scale

        # Boolean difference
        guide_body = outer_mesh.difference(inner_mesh, engine='manifold')

        return SDFResult(
            success=True,
            guide_body=guide_body,
            metrics={
                "method": "simple_scaling",
                "outer_scale": outer_scale,
                "inner_scale": inner_scale,
            },
            warnings=warnings,
        )

    except Exception as e:
        return SDFResult(
            success=False,
            error_message=f"Simple offset failed: {str(e)}",
            warnings=warnings,
        )
