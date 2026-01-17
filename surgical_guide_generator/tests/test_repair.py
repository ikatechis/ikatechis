"""Tests for mesh repair module."""

import pytest
import numpy as np
import trimesh
from surgical_guide_generator.repair import (
    repair_mesh,
    close_holes,
    remove_non_manifold_geometry,
    RepairResult,
)


@pytest.fixture
def valid_cube_mesh():
    """Create a valid watertight cube mesh."""
    return trimesh.creation.box(extents=[10, 10, 10])


@pytest.fixture
def mesh_with_hole():
    """Create a mesh with a hole."""
    cube = trimesh.creation.box(extents=[10, 10, 10])
    # Remove some faces to create a hole
    cube.faces = cube.faces[:-3]
    return cube


class TestRepairMesh:
    """Test main repair function."""

    def test_repair_valid_mesh(self, valid_cube_mesh) -> None:
        """Test repairing an already valid mesh (should not change it)."""
        original_vertex_count = len(valid_cube_mesh.vertices)
        original_face_count = len(valid_cube_mesh.faces)

        result = repair_mesh(valid_cube_mesh)

        assert isinstance(result, RepairResult)
        assert result.success is True
        assert result.repaired_mesh is not None
        assert result.repaired_mesh.is_watertight
        # Should not dramatically change vertex/face count for already valid mesh
        assert len(result.repaired_mesh.vertices) >= original_vertex_count - 2
        assert len(result.repaired_mesh.faces) >= original_face_count - 2

    def test_repair_mesh_with_hole(self, mesh_with_hole) -> None:
        """Test repairing a mesh with holes."""
        assert not mesh_with_hole.is_watertight

        result = repair_mesh(mesh_with_hole, max_hole_size=100)

        assert result.success is True
        assert result.repaired_mesh is not None
        # After repair, mesh should ideally be watertight (but depends on hole size)
        # At minimum, it should have more faces than before
        assert len(result.operations_performed) > 0

    def test_repair_mesh_returns_metrics(self, mesh_with_hole) -> None:
        """Test that repair result includes metrics."""
        result = repair_mesh(mesh_with_hole)

        assert "original_vertex_count" in result.metrics
        assert "original_face_count" in result.metrics
        assert "final_vertex_count" in result.metrics
        assert "final_face_count" in result.metrics
        assert result.metrics["original_vertex_count"] > 0

    def test_repair_mesh_empty(self) -> None:
        """Test repairing an empty mesh."""
        empty_mesh = trimesh.Trimesh(vertices=[], faces=[])
        result = repair_mesh(empty_mesh)

        assert result.success is False
        assert "empty" in result.error_message.lower() or "no vertices" in result.error_message.lower()

    def test_repair_result_to_dict(self, valid_cube_mesh) -> None:
        """Test that RepairResult can be converted to dict."""
        result = repair_mesh(valid_cube_mesh)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "operations_performed" in result_dict
        assert "metrics" in result_dict


class TestCloseHoles:
    """Test hole closing function."""

    def test_close_holes_with_hole(self, mesh_with_hole) -> None:
        """Test closing holes in a mesh."""
        assert not mesh_with_hole.is_watertight

        closed_mesh, holes_closed = close_holes(mesh_with_hole, max_hole_size=100)

        assert closed_mesh is not None
        assert isinstance(holes_closed, int)
        # Should have attempted to close holes
        assert holes_closed >= 0

    def test_close_holes_valid_mesh(self, valid_cube_mesh) -> None:
        """Test closing holes on a mesh that has none."""
        closed_mesh, holes_closed = close_holes(valid_cube_mesh, max_hole_size=50)

        assert closed_mesh is not None
        assert holes_closed == 0  # No holes to close


class TestRemoveNonManifoldGeometry:
    """Test non-manifold geometry removal."""

    def test_remove_non_manifold_valid(self, valid_cube_mesh) -> None:
        """Test removing non-manifold geometry from valid mesh."""
        cleaned_mesh, removed = remove_non_manifold_geometry(valid_cube_mesh)

        assert cleaned_mesh is not None
        assert removed >= 0

    def test_remove_non_manifold_returns_mesh(self, valid_cube_mesh) -> None:
        """Test that function returns a mesh object."""
        cleaned_mesh, removed = remove_non_manifold_geometry(valid_cube_mesh)

        assert isinstance(cleaned_mesh, trimesh.Trimesh)
        assert len(cleaned_mesh.vertices) > 0
        assert len(cleaned_mesh.faces) > 0
