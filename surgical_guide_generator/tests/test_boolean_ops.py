"""Tests for Boolean operations module."""

import pytest
import numpy as np
import trimesh
from surgical_guide_generator.boolean_ops import (
    boolean_difference,
    boolean_union,
    boolean_intersection,
    BooleanResult,
)


@pytest.fixture
def cube_mesh():
    """Create a cube mesh."""
    return trimesh.creation.box(extents=[10, 10, 10])


@pytest.fixture
def sphere_mesh():
    """Create a sphere mesh."""
    return trimesh.creation.icosphere(subdivisions=2, radius=6.0)


@pytest.fixture
def cylinder_mesh():
    """Create a cylinder mesh."""
    return trimesh.creation.cylinder(radius=3.0, height=12.0)


class TestBooleanDifference:
    """Test Boolean difference operation."""

    def test_difference_cube_minus_sphere(self, cube_mesh, sphere_mesh) -> None:
        """Test subtracting a sphere from a cube."""
        result = boolean_difference(cube_mesh, sphere_mesh)

        assert isinstance(result, BooleanResult)
        assert result.success is True
        assert result.result_mesh is not None
        assert result.result_mesh.is_volume
        # Result should have less volume than original cube
        assert result.result_mesh.volume < cube_mesh.volume

    def test_difference_cube_minus_cylinder(self, cube_mesh, cylinder_mesh) -> None:
        """Test subtracting a cylinder from a cube (like drilling a hole)."""
        result = boolean_difference(cube_mesh, cylinder_mesh)

        assert result.success is True
        assert result.result_mesh is not None
        assert result.result_mesh.is_watertight
        # Result should be watertight after subtraction
        assert result.result_mesh.is_volume

    def test_difference_non_overlapping(self) -> None:
        """Test difference of non-overlapping meshes."""
        cube1 = trimesh.creation.box(extents=[5, 5, 5])
        cube1.apply_translation([0, 0, 0])

        cube2 = trimesh.creation.box(extents=[5, 5, 5])
        cube2.apply_translation([20, 20, 20])  # Far away

        result = boolean_difference(cube1, cube2)

        # Should succeed, result should be similar to original
        assert result.success is True
        assert result.result_mesh is not None
        # Volume should be approximately the same
        assert np.isclose(result.result_mesh.volume, cube1.volume, rtol=0.1)

    def test_difference_returns_metrics(self, cube_mesh, sphere_mesh) -> None:
        """Test that difference returns operation metrics."""
        result = boolean_difference(cube_mesh, sphere_mesh)

        assert "original_volume" in result.metrics
        assert "result_volume" in result.metrics
        assert "volume_removed" in result.metrics
        assert result.metrics["volume_removed"] > 0


class TestBooleanUnion:
    """Test Boolean union operation."""

    def test_union_two_cubes(self) -> None:
        """Test union of two overlapping cubes."""
        cube1 = trimesh.creation.box(extents=[10, 10, 10])
        cube1.apply_translation([-3, 0, 0])

        cube2 = trimesh.creation.box(extents=[10, 10, 10])
        cube2.apply_translation([3, 0, 0])

        result = boolean_union(cube1, cube2)

        assert result.success is True
        assert result.result_mesh is not None
        assert result.result_mesh.is_volume
        # Union should have less volume than sum (due to overlap)
        assert result.result_mesh.volume < (cube1.volume + cube2.volume)
        # But more than either individual cube
        assert result.result_mesh.volume > cube1.volume

    def test_union_cube_and_sphere(self, cube_mesh, sphere_mesh) -> None:
        """Test union of cube and sphere."""
        result = boolean_union(cube_mesh, sphere_mesh)

        assert result.success is True
        assert result.result_mesh is not None
        assert result.result_mesh.is_watertight

    def test_union_non_overlapping(self) -> None:
        """Test union of non-overlapping meshes."""
        cube1 = trimesh.creation.box(extents=[5, 5, 5])
        cube2 = trimesh.creation.box(extents=[5, 5, 5])
        cube2.apply_translation([10, 0, 0])  # Touching but not overlapping

        result = boolean_union(cube1, cube2)

        assert result.success is True
        # Volume should be approximately sum of both
        expected_volume = cube1.volume + cube2.volume
        assert np.isclose(result.result_mesh.volume, expected_volume, rtol=0.1)


class TestBooleanIntersection:
    """Test Boolean intersection operation."""

    def test_intersection_overlapping_cubes(self) -> None:
        """Test intersection of two overlapping cubes."""
        cube1 = trimesh.creation.box(extents=[10, 10, 10])
        cube1.apply_translation([-3, 0, 0])

        cube2 = trimesh.creation.box(extents=[10, 10, 10])
        cube2.apply_translation([3, 0, 0])

        result = boolean_intersection(cube1, cube2)

        assert result.success is True
        assert result.result_mesh is not None
        # Intersection should be smaller than either cube
        assert result.result_mesh.volume < cube1.volume
        assert result.result_mesh.volume < cube2.volume

    def test_intersection_cube_and_sphere(self, cube_mesh, sphere_mesh) -> None:
        """Test intersection of cube and sphere."""
        result = boolean_intersection(cube_mesh, sphere_mesh)

        assert result.success is True
        assert result.result_mesh is not None
        # Intersection should be smaller than both
        assert result.result_mesh.volume < cube_mesh.volume
        assert result.result_mesh.volume < sphere_mesh.volume

    def test_intersection_non_overlapping(self) -> None:
        """Test intersection of non-overlapping meshes."""
        cube1 = trimesh.creation.box(extents=[5, 5, 5])
        cube2 = trimesh.creation.box(extents=[5, 5, 5])
        cube2.apply_translation([20, 0, 0])  # Far away

        result = boolean_intersection(cube1, cube2)

        # Intersection of non-overlapping should either fail or produce empty/tiny mesh
        if result.success:
            # If it succeeds, volume should be very small or zero
            assert result.result_mesh.volume < 0.1


class TestBooleanResult:
    """Test BooleanResult dataclass."""

    def test_result_to_dict(self, cube_mesh, sphere_mesh) -> None:
        """Test conversion of result to dictionary."""
        result = boolean_difference(cube_mesh, sphere_mesh)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "operation" in result_dict
        assert "metrics" in result_dict
        assert "error_message" in result_dict

    def test_result_includes_operation_name(self, cube_mesh, sphere_mesh) -> None:
        """Test that result includes the operation name."""
        result_diff = boolean_difference(cube_mesh, sphere_mesh)
        result_union = boolean_union(cube_mesh, sphere_mesh)

        assert result_diff.operation == "difference"
        assert result_union.operation == "union"


class TestBooleanOperationsReliability:
    """Test reliability and edge cases."""

    def test_operations_preserve_watertightness(self, cube_mesh) -> None:
        """Test that Boolean ops preserve watertight property."""
        # Subtract a smaller sphere from the center
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=3.0)

        result = boolean_difference(cube_mesh, sphere)

        assert result.success is True
        assert result.result_mesh.is_watertight

    def test_sequential_operations(self, cube_mesh) -> None:
        """Test multiple Boolean operations in sequence."""
        # Create two cylinders to subtract
        cyl1 = trimesh.creation.cylinder(radius=2.0, height=15.0)
        cyl1.apply_translation([3, 0, 0])

        cyl2 = trimesh.creation.cylinder(radius=2.0, height=15.0)
        cyl2.apply_translation([-3, 0, 0])

        # First subtraction
        result1 = boolean_difference(cube_mesh, cyl1)
        assert result1.success is True

        # Second subtraction
        result2 = boolean_difference(result1.result_mesh, cyl2)
        assert result2.success is True
        assert result2.result_mesh.is_watertight
        # Should have less volume after two subtractions
        assert result2.result_mesh.volume < result1.result_mesh.volume
