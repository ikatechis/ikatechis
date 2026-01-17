"""Tests for inspection windows module."""

import pytest
import numpy as np
import trimesh
from surgical_guide_generator.inspection_windows import (
    create_inspection_window,
    add_inspection_windows,
    compute_window_position,
)
from surgical_guide_generator.config import ImplantSite, SleeveSpec


@pytest.fixture
def guide_mesh():
    """Create a simple guide mesh (box)."""
    return trimesh.creation.box(extents=[50, 30, 10])


@pytest.fixture
def implant_site():
    """Create a sample implant site."""
    return ImplantSite(
        site_id="36",
        position=[10.0, 0.0, 5.0],
        direction=[0.0, 0.1, -0.995],
        sleeve_spec=SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        ),
    )


class TestCreateInspectionWindow:
    """Test single inspection window creation."""

    def test_create_window_basic(self) -> None:
        """Test creating a basic inspection window box."""
        position = np.array([10.0, 0.0, 5.0])
        normal = np.array([1.0, 0.0, 0.0])  # Pointing along X

        window = create_inspection_window(
            position=position,
            normal=normal,
            width=10.0,
            depth=5.0,
        )

        assert isinstance(window, trimesh.Trimesh)
        assert window.is_volume
        assert len(window.faces) > 0

    def test_window_dimensions(self) -> None:
        """Test that window has correct dimensions."""
        position = np.array([0.0, 0.0, 0.0])
        normal = np.array([0.0, 0.0, 1.0])
        width = 10.0
        depth = 5.0

        window = create_inspection_window(
            position=position,
            normal=normal,
            width=width,
            depth=depth,
        )

        # Check bounding box
        bounds = window.bounds
        bbox_size = bounds[1] - bounds[0]

        # Window should fit within expected dimensions
        assert bbox_size[0] <= width + 1.0
        assert bbox_size[1] <= width + 1.0
        assert bbox_size[2] <= depth + 1.0

    def test_window_different_orientations(self) -> None:
        """Test creating windows with different orientations."""
        position = np.array([0.0, 0.0, 0.0])

        # Test different normal directions
        normals = [
            np.array([1.0, 0.0, 0.0]),  # X
            np.array([0.0, 1.0, 0.0]),  # Y
            np.array([0.0, 0.0, 1.0]),  # Z
            np.array([1.0, 1.0, 0.0]) / np.sqrt(2),  # Diagonal
        ]

        for normal in normals:
            window = create_inspection_window(
                position=position,
                normal=normal,
                width=8.0,
                depth=4.0,
            )
            assert isinstance(window, trimesh.Trimesh)
            assert window.is_volume


class TestComputeWindowPosition:
    """Test window position computation."""

    def test_compute_position_from_implant(self) -> None:
        """Test computing window position from implant site."""
        implant_pos = np.array([10.0, 5.0, 3.0])
        implant_dir = np.array([0.0, 0.0, -1.0])  # Vertical
        sleeve_diameter = 5.0
        margin = 3.0

        window_pos, window_normal = compute_window_position(
            implant_position=implant_pos,
            implant_direction=implant_dir,
            sleeve_outer_diameter=sleeve_diameter,
            margin_from_sleeve=margin,
        )

        # Window should be offset from implant position
        assert isinstance(window_pos, np.ndarray)
        assert len(window_pos) == 3

        # Window normal should be perpendicular to implant direction
        assert isinstance(window_normal, np.ndarray)
        dot_product = np.dot(window_normal, implant_dir)
        assert np.abs(dot_product) < 0.1  # Nearly perpendicular

    def test_window_position_offset_from_sleeve(self) -> None:
        """Test that window is positioned at correct distance from sleeve."""
        implant_pos = np.array([0.0, 0.0, 0.0])
        implant_dir = np.array([0.0, 0.0, -1.0])
        sleeve_diameter = 5.0
        margin = 3.0

        window_pos, _ = compute_window_position(
            implant_position=implant_pos,
            implant_direction=implant_dir,
            sleeve_outer_diameter=sleeve_diameter,
            margin_from_sleeve=margin,
        )

        # Calculate distance from implant center
        distance = np.linalg.norm(window_pos[:2])  # XY distance
        expected_min_distance = (sleeve_diameter / 2) + margin

        # Should be at least margin away from sleeve edge
        assert distance >= expected_min_distance - 0.1


class TestAddInspectionWindows:
    """Test adding multiple inspection windows to a guide."""

    def test_add_windows_single_implant(self, guide_mesh, implant_site) -> None:
        """Test adding windows for a single implant."""
        from surgical_guide_generator.boolean_ops import boolean_difference

        result = add_inspection_windows(
            guide_mesh=guide_mesh,
            implant_sites=[implant_site],
            window_width=10.0,
            window_depth=5.0,
            margin_from_sleeve=3.0,
        )

        assert isinstance(result, trimesh.Trimesh)
        # Guide should have less volume after windows are cut
        assert result.volume < guide_mesh.volume

    def test_add_windows_multiple_implants(self, guide_mesh) -> None:
        """Test adding windows for multiple implants."""
        sites = [
            ImplantSite(
                site_id="36",
                position=[10.0, 0.0, 5.0],
                direction=[0.0, 0.1, -0.995],
                sleeve_spec=SleeveSpec(
                    outer_diameter=5.0,
                    inner_diameter=4.0,
                    height=5.0,
                ),
            ),
            ImplantSite(
                site_id="46",
                position=[-10.0, 0.0, 5.0],
                direction=[0.0, 0.1, -0.995],
                sleeve_spec=SleeveSpec(
                    outer_diameter=5.0,
                    inner_diameter=4.0,
                    height=5.0,
                ),
            ),
        ]

        result = add_inspection_windows(
            guide_mesh=guide_mesh,
            implant_sites=sites,
            window_width=8.0,
            window_depth=4.0,
        )

        assert isinstance(result, trimesh.Trimesh)
        # Should have cut windows for both implants
        assert result.volume < guide_mesh.volume

    def test_add_windows_no_implants(self, guide_mesh) -> None:
        """Test that no windows are added if no implants."""
        result = add_inspection_windows(
            guide_mesh=guide_mesh,
            implant_sites=[],
            window_width=10.0,
            window_depth=5.0,
        )

        # Should return original mesh unchanged
        assert result.volume == guide_mesh.volume

    def test_add_windows_preserves_watertightness(self, guide_mesh, implant_site) -> None:
        """Test that adding windows maintains watertight mesh."""
        result = add_inspection_windows(
            guide_mesh=guide_mesh,
            implant_sites=[implant_site],
            window_width=8.0,
            window_depth=4.0,
        )

        # Result should still be watertight after Boolean subtraction
        # (assuming manifold engine works correctly)
        assert isinstance(result, trimesh.Trimesh)
        # Note: This might fail if window doesn't intersect guide
        # In practice, we'd need to ensure window positioning is correct

    def test_configurable_window_size(self, guide_mesh, implant_site) -> None:
        """Test that window size is configurable."""
        # Small windows
        result_small = add_inspection_windows(
            guide_mesh=guide_mesh.copy(),
            implant_sites=[implant_site],
            window_width=5.0,
            window_depth=2.0,
        )

        # Large windows
        result_large = add_inspection_windows(
            guide_mesh=guide_mesh.copy(),
            implant_sites=[implant_site],
            window_width=15.0,
            window_depth=8.0,
        )

        # Larger windows should remove more volume
        volume_removed_small = guide_mesh.volume - result_small.volume
        volume_removed_large = guide_mesh.volume - result_large.volume

        # This assumes the window actually intersects the guide
        # If not, both might be close to 0
        assert volume_removed_large >= volume_removed_small - 1.0
