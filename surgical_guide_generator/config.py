"""Configuration dataclasses for surgical guide generation."""

from dataclasses import dataclass, field
from typing import List, Sequence
import numpy as np
import numpy.typing as npt


@dataclass
class SleeveSpec:
    """Specification for a metal sleeve to be mounted in the surgical guide.

    Attributes:
        outer_diameter: External diameter of the sleeve in mm
        inner_diameter: Internal diameter (drill clearance) in mm
        height: Sleeve length in mm
        clearance: Gap between sleeve and guide hole for fit tolerance in mm
    """

    outer_diameter: float
    inner_diameter: float
    height: float
    clearance: float = 0.05  # 50μm press-fit default

    def __post_init__(self) -> None:
        """Validate sleeve specifications."""
        if self.outer_diameter <= 0 or self.inner_diameter <= 0 or self.height <= 0:
            raise ValueError("All sleeve dimensions must be positive")

        if self.outer_diameter <= self.inner_diameter:
            raise ValueError(
                f"Outer diameter ({self.outer_diameter}mm) must be greater than "
                f"inner diameter ({self.inner_diameter}mm)"
            )

        if self.clearance < 0:
            raise ValueError("Clearance must be non-negative")


@dataclass
class ImplantSite:
    """Specification for a single implant site.

    Attributes:
        site_id: Identifier for the implant site (e.g., FDI tooth number)
        position: [x, y, z] coordinates of implant platform center in mm
        direction: [dx, dy, dz] implant axis unit vector (pointing apical)
        sleeve_spec: Sleeve specifications for this site
        implant_diameter: Implant body diameter in mm (optional, for documentation)
        implant_length: Implant length in mm (optional, for documentation)
    """

    site_id: str
    position: List[float]
    direction: List[float]
    sleeve_spec: SleeveSpec
    implant_diameter: float = 0.0
    implant_length: float = 0.0

    def __post_init__(self) -> None:
        """Validate and normalize implant site data."""
        # Validate position
        if len(self.position) != 3:
            raise ValueError(
                f"Position must have 3 coordinates, got {len(self.position)}"
            )

        # Validate direction
        if len(self.direction) != 3:
            raise ValueError(
                f"Direction must have 3 coordinates, got {len(self.direction)}"
            )

        # Normalize direction vector
        direction_array = np.array(self.direction, dtype=float)
        norm = np.linalg.norm(direction_array)
        if norm < 1e-10:
            raise ValueError("Direction vector cannot be zero")

        direction_array = direction_array / norm
        self.direction = direction_array.tolist()


@dataclass
class GuideConfig:
    """Configuration parameters for surgical guide generation.

    Attributes:
        thickness: Guide shell thickness in mm (2.0-5.0mm recommended)
        tissue_gap: Gap from tissue surface for seating compensation in mm
        voxel_size: SDF voxel resolution in mm (smaller = more accurate but slower)
        add_inspection_windows: Add windows for visual seating verification
        window_width: Width of inspection windows in mm
        window_depth: Depth of inspection windows in mm
        margin_from_sleeve: Minimum distance from sleeve to window in mm
        extension: Extra cylinder length for clean Boolean cuts in mm
    """

    thickness: float = 2.5
    tissue_gap: float = 0.15
    voxel_size: float = 0.15
    add_inspection_windows: bool = True
    window_width: float = 10.0
    window_depth: float = 5.0
    margin_from_sleeve: float = 3.0
    extension: float = 2.0

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not (2.0 <= self.thickness <= 5.0):
            raise ValueError(
                f"Thickness must be between 2.0 and 5.0 mm, got {self.thickness}"
            )

        if not (0.1 <= self.voxel_size <= 0.5):
            raise ValueError(
                f"Voxel size must be between 0.1 and 0.5 mm, got {self.voxel_size}"
            )

        if self.tissue_gap < 0:
            raise ValueError("Tissue gap must be non-negative")

        if self.window_width <= 0 or self.window_depth <= 0:
            raise ValueError("Window dimensions must be positive")


@dataclass
class ValidationConfig:
    """Configuration for mesh validation and repair.

    Attributes:
        check_watertight: Verify mesh is watertight (closed)
        check_self_intersection: Check for self-intersecting faces (slow)
        min_wall_thickness: Minimum acceptable wall thickness in mm
        repair_if_needed: Attempt automatic repair if validation fails
        max_hole_size: Maximum hole size to close during repair
    """

    check_watertight: bool = True
    check_self_intersection: bool = False  # Expensive check
    min_wall_thickness: float = 2.0
    repair_if_needed: bool = True
    max_hole_size: int = 50

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.min_wall_thickness < 0:
            raise ValueError("Minimum wall thickness must be non-negative")

        if self.max_hole_size < 0:
            raise ValueError("Maximum hole size must be non-negative")
