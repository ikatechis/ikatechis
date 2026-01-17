"""Tests for mesh I/O functions."""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from surgical_guide_generator.mesh_io import (
    load_mesh,
    export_mesh,
    ExportResult,
)


@pytest.fixture
def simple_cube_mesh():
    """Create a simple cube mesh for testing."""
    import trimesh
    return trimesh.creation.box(extents=[10, 10, 10])


@pytest.fixture
def temp_stl_file(simple_cube_mesh):
    """Create a temporary STL file."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.stl', delete=False) as f:
        simple_cube_mesh.export(f.name)
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


class TestLoadMesh:
    """Test mesh loading functionality."""

    def test_load_valid_stl(self, temp_stl_file) -> None:
        """Test loading a valid STL file."""
        mesh = load_mesh(temp_stl_file)
        assert mesh is not None
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0

    def test_load_nonexistent_file(self) -> None:
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_mesh("/nonexistent/file.stl")

    def test_load_invalid_extension(self, tmp_path) -> None:
        """Test loading file with invalid extension raises error."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not a mesh file")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_mesh(str(invalid_file))

    def test_load_mesh_validation(self, temp_stl_file) -> None:
        """Test that loaded mesh is validated."""
        mesh = load_mesh(temp_stl_file, validate=True)
        # A simple cube should be watertight
        assert mesh.is_watertight
        assert mesh.is_volume

    def test_load_mesh_auto_repair(self, tmp_path) -> None:
        """Test that mesh auto-repair can be disabled."""
        # This test just verifies the parameter is accepted
        import trimesh
        cube = trimesh.creation.box(extents=[10, 10, 10])
        stl_file = tmp_path / "cube.stl"
        cube.export(str(stl_file))

        mesh = load_mesh(str(stl_file), auto_repair=False)
        assert mesh is not None


class TestExportMesh:
    """Test mesh export functionality."""

    def test_export_stl(self, simple_cube_mesh, tmp_path) -> None:
        """Test exporting to STL format."""
        output_file = tmp_path / "output.stl"
        result = export_mesh(simple_cube_mesh, str(output_file))

        assert isinstance(result, ExportResult)
        assert result.success is True
        assert output_file.exists()
        assert result.file_path == str(output_file)
        assert "vertices" in result.metrics
        assert "faces" in result.metrics

    def test_export_3mf(self, simple_cube_mesh, tmp_path) -> None:
        """Test exporting to 3MF format."""
        output_file = tmp_path / "output.3mf"
        result = export_mesh(simple_cube_mesh, str(output_file))

        assert result.success is True
        assert output_file.exists()

    def test_export_with_validation(self, simple_cube_mesh, tmp_path) -> None:
        """Test exporting with validation enabled."""
        output_file = tmp_path / "output.stl"
        result = export_mesh(simple_cube_mesh, str(output_file), validate=True)

        assert result.success is True
        assert result.validation_passed is True

    def test_export_invalid_mesh(self, tmp_path) -> None:
        """Test exporting invalid mesh with strict validation."""
        import trimesh
        # Create a mesh with no faces (invalid)
        invalid_mesh = trimesh.Trimesh(vertices=[[0, 0, 0], [1, 1, 1]], faces=[])
        output_file = tmp_path / "output.stl"

        # Should fail even without validation (trimesh can't export empty mesh)
        result = export_mesh(invalid_mesh, str(output_file), validate=False)
        assert result.success is False
        assert len(result.warnings) > 0

        # Should fail with validation
        with pytest.raises(ValueError, match="Mesh validation failed"):
            export_mesh(invalid_mesh, str(output_file), validate=True)

    def test_export_unsupported_format(self, simple_cube_mesh, tmp_path) -> None:
        """Test exporting to unsupported format raises error."""
        output_file = tmp_path / "output.txt"
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_mesh(simple_cube_mesh, str(output_file))

    def test_export_result_metrics(self, simple_cube_mesh, tmp_path) -> None:
        """Test that export result contains correct metrics."""
        output_file = tmp_path / "output.stl"
        result = export_mesh(simple_cube_mesh, str(output_file))

        assert result.metrics["vertices"] == len(simple_cube_mesh.vertices)
        assert result.metrics["faces"] == len(simple_cube_mesh.faces)
        assert "volume_mm3" in result.metrics
        assert "surface_area_mm2" in result.metrics
        assert result.metrics["is_watertight"] is True

    def test_export_fixes_normals(self, tmp_path) -> None:
        """Test that export fixes mesh normals."""
        import trimesh
        cube = trimesh.creation.box(extents=[10, 10, 10])
        output_file = tmp_path / "output.stl"

        # Export should call fix_normals internally
        result = export_mesh(cube, str(output_file), fix_normals=True)
        assert result.success is True
