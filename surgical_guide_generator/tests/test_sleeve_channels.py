"""Tests for sleeve channel geometry creation."""

import pytest
import numpy as np
import trimesh
from surgical_guide_generator.sleeve_channels import (
    create_sleeve_channel,
    compute_rotation_matrix,
    align_cylinder_to_direction,
)
from surgical_guide_generator.config import ImplantSite, SleeveSpec


class TestComputeRotationMatrix:
    """Test rotation matrix computation."""

    def test_rotation_z_to_z(self) -> None:
        """Test rotation from Z to Z (identity)."""
        direction = np.array([0, 0, 1])
        rotation = compute_rotation_matrix(direction)

        # Should be close to identity matrix
        assert np.allclose(rotation, np.eye(3))

    def test_rotation_z_to_minus_z(self) -> None:
        """Test rotation from Z to -Z (180 degrees)."""
        direction = np.array([0, 0, -1])
        rotation = compute_rotation_matrix(direction)

        # Apply rotation to Z-axis should give -Z
        z_axis = np.array([0, 0, 1])
        result = rotation @ z_axis
        assert np.allclose(result, direction)

    def test_rotation_z_to_x(self) -> None:
        """Test rotation from Z to X axis."""
        direction = np.array([1, 0, 0])
        rotation = compute_rotation_matrix(direction)

        # Apply rotation to Z-axis should give X
        z_axis = np.array([0, 0, 1])
        result = rotation @ z_axis
        assert np.allclose(result, direction, atol=1e-6)

    def test_rotation_preserves_length(self) -> None:
        """Test that rotation matrix preserves vector length."""
        direction = np.array([1, 1, 1]) / np.sqrt(3)  # Normalized
        rotation = compute_rotation_matrix(direction)

        # Rotation matrix should be orthogonal (preserve lengths)
        test_vector = np.array([1, 2, 3])
        rotated = rotation @ test_vector
        assert np.allclose(np.linalg.norm(rotated), np.linalg.norm(test_vector))

    def test_rotation_is_orthogonal(self) -> None:
        """Test that rotation matrix is orthogonal."""
        direction = np.array([1, 2, 3])
        direction = direction / np.linalg.norm(direction)
        rotation = compute_rotation_matrix(direction)

        # R @ R.T should be identity
        assert np.allclose(rotation @ rotation.T, np.eye(3), atol=1e-6)


class TestCreateSleeveChannel:
    """Test sleeve channel creation."""

    def test_create_channel_vertical(self) -> None:
        """Test creating a vertical channel (along Z)."""
        position = np.array([0, 0, 10])
        direction = np.array([0, 0, -1])  # Pointing down
        sleeve_spec = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        )

        channel = create_sleeve_channel(
            position=position,
            direction=direction,
            sleeve_spec=sleeve_spec,
        )

        assert isinstance(channel, trimesh.Trimesh)
        assert channel.is_volume
        assert len(channel.vertices) > 0
        assert len(channel.faces) > 0

    def test_create_channel_angled(self) -> None:
        """Test creating an angled channel."""
        position = np.array([10, 10, 10])
        direction = np.array([1, 0, -1])
        direction = direction / np.linalg.norm(direction)  # Normalize
        sleeve_spec = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        )

        channel = create_sleeve_channel(
            position=position,
            direction=direction,
            sleeve_spec=sleeve_spec,
        )

        assert isinstance(channel, trimesh.Trimesh)
        assert channel.is_volume

    def test_channel_dimensions(self) -> None:
        """Test that channel has correct dimensions."""
        position = np.array([0, 0, 0])
        direction = np.array([0, 0, 1])
        sleeve_spec = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
            clearance=0.1,
        )

        channel = create_sleeve_channel(
            position=position,
            direction=direction,
            sleeve_spec=sleeve_spec,
        )

        # Channel radius should be outer_diameter/2 + clearance
        expected_radius = (sleeve_spec.outer_diameter / 2) + sleeve_spec.clearance

        # Check bounding box includes the expected radius
        bounds = channel.bounds
        bbox_size = bounds[1] - bounds[0]

        # The cylinder should fit within a box of size 2*expected_radius
        assert bbox_size[0] <= 2 * expected_radius + 0.1
        assert bbox_size[1] <= 2 * expected_radius + 0.1

    def test_channel_with_extension(self) -> None:
        """Test channel creation with extension."""
        position = np.array([0, 0, 0])
        direction = np.array([0, 0, 1])
        sleeve_spec = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        )

        extension = 3.0
        channel = create_sleeve_channel(
            position=position,
            direction=direction,
            sleeve_spec=sleeve_spec,
            extension=extension,
        )

        # Channel should be longer than sleeve height due to extension
        bounds = channel.bounds
        bbox_size = bounds[1] - bounds[0]

        # Height along z-axis should be approximately sleeve_height + extension
        # (approximate because of discretization and positioning)
        assert bbox_size[2] >= sleeve_spec.height

    def test_channel_from_implant_site(self) -> None:
        """Test creating channel from ImplantSite configuration."""
        site = ImplantSite(
            site_id="36",
            position=[25.5, -12.3, 8.7],
            direction=[0.0, 0.1, -0.995],  # Will be normalized
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        )

        channel = create_sleeve_channel(
            position=np.array(site.position),
            direction=np.array(site.direction),
            sleeve_spec=site.sleeve_spec,
        )

        assert isinstance(channel, trimesh.Trimesh)
        assert channel.is_volume
        assert len(channel.faces) > 0

    def test_channel_different_clearances(self) -> None:
        """Test that different clearances produce different sized channels."""
        position = np.array([0, 0, 0])
        direction = np.array([0, 0, 1])

        sleeve_spec_tight = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
            clearance=0.05,  # Tight fit
        )

        sleeve_spec_loose = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
            clearance=0.15,  # Loose fit
        )

        channel_tight = create_sleeve_channel(position, direction, sleeve_spec_tight)
        channel_loose = create_sleeve_channel(position, direction, sleeve_spec_loose)

        # Loose channel should have larger volume
        assert channel_loose.volume > channel_tight.volume


class TestAlignCylinderToDirection:
    """Test cylinder alignment function."""

    def test_align_cylinder_to_vertical(self) -> None:
        """Test aligning cylinder to vertical direction."""
        cylinder = trimesh.creation.cylinder(radius=2.5, height=5.0)
        position = np.array([0, 0, 10])
        direction = np.array([0, 0, 1])

        aligned = align_cylinder_to_direction(cylinder, position, direction)

        assert isinstance(aligned, trimesh.Trimesh)
        # Centroid should be near the position
        centroid = aligned.centroid
        assert np.linalg.norm(centroid - position) < 5.0  # Within reasonable distance

    def test_align_cylinder_to_horizontal(self) -> None:
        """Test aligning cylinder to horizontal direction."""
        cylinder = trimesh.creation.cylinder(radius=2.5, height=5.0)
        position = np.array([0, 0, 0])
        direction = np.array([1, 0, 0])  # Along X-axis

        aligned = align_cylinder_to_direction(cylinder, position, direction)

        assert isinstance(aligned, trimesh.Trimesh)
        assert len(aligned.faces) == len(cylinder.faces)
