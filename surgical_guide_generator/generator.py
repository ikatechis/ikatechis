"""Main pipeline orchestration for surgical guide generation.

This module integrates all components to generate complete surgical guides.
Currently uses a simple box placeholder for the guide body. The SDF-based
offset algorithm will be integrated once implemented.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import numpy.typing as npt
import trimesh

from surgical_guide_generator.config import ImplantSite, GuideConfig, ValidationConfig
from surgical_guide_generator.sleeve_channels import create_sleeve_channel
from surgical_guide_generator.boolean_ops import boolean_difference
from surgical_guide_generator.inspection_windows import add_inspection_windows
from surgical_guide_generator.validation import validate_mesh
from surgical_guide_generator.mesh_io import export_mesh


@dataclass
class GenerationResult:
    """Result of surgical guide generation.

    Attributes:
        success: Whether generation completed successfully
        guide_mesh: The generated guide mesh (None if failed)
        operations_performed: List of operations that were performed
        metrics: Dictionary of metrics and measurements
        warnings: List of warning messages
        error_message: Error message if generation failed
    """

    success: bool
    guide_mesh: Optional[trimesh.Trimesh] = None
    operations_performed: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary (excluding mesh).

        Returns:
            Dictionary representation
        """
        return {
            "success": self.success,
            "operations_performed": self.operations_performed,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "error_message": self.error_message,
        }


def create_simple_guide_body(
    extents: List[float],
    center: Optional[List[float]] = None,
) -> trimesh.Trimesh:
    """Create a simple box guide body (placeholder for SDF algorithm).

    This is a placeholder for the SDF-based guide body generation.
    In production, this would use the SDF offset algorithm to create
    a shell that follows the dental anatomy.

    Args:
        extents: [length, width, height] of the guide box in mm
        center: Optional center position [x, y, z]

    Returns:
        Simple box mesh as guide body placeholder

    Note:
        This will be replaced with SDF-based offset once implemented.
    """
    # Create box
    guide = trimesh.creation.box(extents=extents)

    # Center if specified
    if center is not None:
        center_array = np.array(center)
        current_center = (guide.bounds[0] + guide.bounds[1]) / 2
        translation = center_array - current_center
        guide.apply_translation(translation)

    return guide


def generate_surgical_guide(
    guide_body_extents: List[float],
    implant_sites: List[ImplantSite],
    output_path: str,
    config: Optional[GuideConfig] = None,
) -> GenerationResult:
    """Generate a complete surgical guide.

    Main orchestration function that integrates all components to create
    a 3D-printable surgical guide.

    Args:
        guide_body_extents: Extents of simple guide body [length, width, height]
                           (placeholder until SDF algorithm is implemented)
        implant_sites: List of implant site specifications
        output_path: Path for output file (.stl or .3mf)
        config: Optional configuration overrides

    Returns:
        GenerationResult with success status and generated mesh

    Example:
        >>> sites = [ImplantSite(...), ImplantSite(...)]
        >>> result = generate_surgical_guide(
        ...     guide_body_extents=[50, 30, 10],
        ...     implant_sites=sites,
        ...     output_path="guide.stl",
        ... )
        >>> if result.success:
        ...     print(f"Guide saved to {output_path}")
    """
    # Use default config if not provided
    if config is None:
        config = GuideConfig()

    operations: List[str] = []
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    try:
        # Validate inputs
        if len(implant_sites) == 0:
            return GenerationResult(
                success=False,
                error_message="No implant sites provided. At least one implant required.",
            )

        # Step 1: Create guide body
        # TODO: Replace with SDF-based offset algorithm
        print("Creating guide body (using placeholder box)...")
        guide = create_simple_guide_body(extents=guide_body_extents)
        operations.append("create_body")
        warnings.append("Using placeholder box for guide body. SDF algorithm not yet implemented.")

        # Record initial metrics
        metrics["initial_volume_mm3"] = float(guide.volume)
        metrics["num_implant_sites"] = len(implant_sites)

        # Step 2: Subtract sleeve channels
        print(f"Adding {len(implant_sites)} sleeve channels...")
        for i, site in enumerate(implant_sites):
            # Create channel
            channel = create_sleeve_channel(
                position=np.array(site.position),
                direction=np.array(site.direction),
                sleeve_spec=site.sleeve_spec,
                extension=config.extension,
            )

            # Subtract from guide
            result = boolean_difference(guide, channel)

            if not result.success:
                return GenerationResult(
                    success=False,
                    error_message=f"Failed to subtract channel for site {site.site_id}: {result.error_message}",
                    operations_performed=operations,
                )

            guide = result.result_mesh
            print(f"  - Site {site.site_id}: channel subtracted")

        operations.append("subtract_channels")
        metrics["volume_after_channels_mm3"] = float(guide.volume)

        # Step 3: Add inspection windows (for multi-implant cases)
        if config.add_inspection_windows and len(implant_sites) > 1:
            print(f"Adding inspection windows...")
            guide = add_inspection_windows(
                guide_mesh=guide,
                implant_sites=implant_sites,
                window_width=config.window_width,
                window_depth=config.window_depth,
                margin_from_sleeve=config.margin_from_sleeve,
            )
            operations.append("add_windows")
            metrics["volume_after_windows_mm3"] = float(guide.volume)

        # Step 4: Validate final guide
        print("Validating guide mesh...")
        validation_config = ValidationConfig(
            check_watertight=True,
            check_self_intersection=False,  # Skip expensive check
        )
        validation = validate_mesh(guide, validation_config)

        if not validation.is_valid:
            warnings.append(f"Validation warnings: {', '.join(validation.errors)}")

        operations.append("validate")
        metrics["validation"] = validation.to_dict()

        # Step 5: Final metrics
        metrics["final_volume_mm3"] = float(guide.volume)
        metrics["final_face_count"] = len(guide.faces)
        metrics["final_vertex_count"] = len(guide.vertices)
        metrics["is_watertight"] = bool(guide.is_watertight)

        # Step 6: Export
        print(f"Exporting to {output_path}...")
        export_result = export_mesh(
            mesh=guide,
            file_path=output_path,
            validate=True,
            fix_normals=True,
        )

        if not export_result.success:
            return GenerationResult(
                success=False,
                guide_mesh=guide,
                error_message=f"Export failed: {export_result.warnings}",
                operations_performed=operations,
                metrics=metrics,
                warnings=warnings,
            )

        operations.append("export")
        metrics["export"] = export_result.metrics

        print(f"✓ Guide generation complete!")
        print(f"  Operations: {', '.join(operations)}")
        print(f"  Output: {output_path}")
        print(f"  Volume: {metrics['final_volume_mm3']:.1f} mm³")
        print(f"  Watertight: {metrics['is_watertight']}")

        return GenerationResult(
            success=True,
            guide_mesh=guide,
            operations_performed=operations,
            metrics=metrics,
            warnings=warnings,
        )

    except Exception as e:
        return GenerationResult(
            success=False,
            error_message=f"Guide generation failed: {str(e)}",
            operations_performed=operations,
            metrics=metrics,
            warnings=warnings,
        )
