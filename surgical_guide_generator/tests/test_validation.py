"""Tests for mesh validation module."""

import pytest
import numpy as np
import trimesh
from surgical_guide_generator.validation import (
    validate_mesh,
    ValidationResult,
    check_watertight,
    check_volume,
    check_euler_characteristic,
)
from surgical_guide_generator.config import ValidationConfig


@pytest.fixture
def valid_cube_mesh():
    """Create a valid watertight cube mesh."""
    return trimesh.creation.box(extents=[10, 10, 10])


@pytest.fixture
def non_watertight_mesh():
    """Create a mesh with a hole (non-watertight)."""
    # Create a cube and remove some faces
    cube = trimesh.creation.box(extents=[10, 10, 10])
    # Remove last two faces to create a hole
    cube.faces = cube.faces[:-2]
    return cube


class TestCheckWatertight:
    """Test watertight checking."""

    def test_check_watertight_valid(self, valid_cube_mesh) -> None:
        """Test that a valid cube is detected as watertight."""
        is_watertight, message = check_watertight(valid_cube_mesh)
        assert is_watertight is True
        assert message == "Mesh is watertight"

    def test_check_watertight_invalid(self, non_watertight_mesh) -> None:
        """Test that a mesh with holes is detected as non-watertight."""
        is_watertight, message = check_watertight(non_watertight_mesh)
        assert is_watertight is False
        assert "not watertight" in message.lower()


class TestCheckVolume:
    """Test volume checking."""

    def test_check_volume_valid(self, valid_cube_mesh) -> None:
        """Test that a valid mesh has a valid volume."""
        is_volume, message = check_volume(valid_cube_mesh)
        assert is_volume is True
        assert message == "Mesh encloses a valid volume"

    def test_check_volume_invalid(self) -> None:
        """Test that a mesh with no faces has no volume."""
        invalid_mesh = trimesh.Trimesh(vertices=[[0, 0, 0], [1, 1, 1]], faces=[])
        is_volume, message = check_volume(invalid_mesh)
        assert is_volume is False
        assert "no faces" in message.lower()


class TestCheckEulerCharacteristic:
    """Test Euler characteristic checking."""

    def test_euler_characteristic_valid(self, valid_cube_mesh) -> None:
        """Test Euler characteristic for a valid closed surface (should be 2)."""
        is_valid, euler, message = check_euler_characteristic(valid_cube_mesh)
        assert euler == 2
        assert is_valid is True
        assert "Euler characteristic is 2" in message

    def test_euler_characteristic_invalid(self, non_watertight_mesh) -> None:
        """Test Euler characteristic for a mesh with holes."""
        is_valid, euler, message = check_euler_characteristic(non_watertight_mesh)
        # A mesh with holes will have different Euler characteristic
        assert euler != 2 or is_valid is False


class TestValidateMesh:
    """Test main validation function."""

    def test_validate_valid_mesh(self, valid_cube_mesh) -> None:
        """Test validation of a valid mesh."""
        config = ValidationConfig()
        result = validate_mesh(valid_cube_mesh, config)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metrics["vertex_count"] == 8
        assert result.metrics["face_count"] == 12
        assert result.metrics["is_watertight"] is True
        assert result.metrics["is_volume"] is True
        assert result.metrics["euler_characteristic"] == 2

    def test_validate_non_watertight_mesh(self, non_watertight_mesh) -> None:
        """Test validation of a non-watertight mesh."""
        config = ValidationConfig(check_watertight=True)
        result = validate_mesh(non_watertight_mesh, config)

        assert result.is_valid is False
        assert any("watertight" in error.lower() for error in result.errors)

    def test_validate_skip_watertight_check(self, non_watertight_mesh) -> None:
        """Test that watertight check can be skipped."""
        config = ValidationConfig(check_watertight=False)
        result = validate_mesh(non_watertight_mesh, config)

        # Should not fail on watertight check
        watertight_errors = [e for e in result.errors if "watertight" in e.lower()]
        assert len(watertight_errors) == 0

    def test_validate_mesh_with_warnings(self, valid_cube_mesh) -> None:
        """Test that validation can produce warnings."""
        config = ValidationConfig()
        result = validate_mesh(valid_cube_mesh, config)

        # A simple cube might have some warnings but should still be valid
        assert result.is_valid is True
        # Warnings are optional
        assert isinstance(result.warnings, list)

    def test_validation_result_to_dict(self, valid_cube_mesh) -> None:
        """Test that ValidationResult can be converted to dict."""
        config = ValidationConfig()
        result = validate_mesh(valid_cube_mesh, config)

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "is_valid" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict
        assert "metrics" in result_dict

    def test_validate_empty_mesh(self) -> None:
        """Test validation of an empty mesh."""
        empty_mesh = trimesh.Trimesh(vertices=[], faces=[])
        config = ValidationConfig()
        result = validate_mesh(empty_mesh, config)

        assert result.is_valid is False
        assert any("no vertices" in error.lower() or "no faces" in error.lower()
                   for error in result.errors)

    def test_validate_mesh_metrics(self, valid_cube_mesh) -> None:
        """Test that validation includes comprehensive metrics."""
        config = ValidationConfig()
        result = validate_mesh(valid_cube_mesh, config)

        # Check all expected metrics are present
        assert "vertex_count" in result.metrics
        assert "face_count" in result.metrics
        assert "volume_mm3" in result.metrics
        assert "surface_area_mm2" in result.metrics
        assert "is_watertight" in result.metrics
        assert "is_volume" in result.metrics
        assert "euler_characteristic" in result.metrics

        # Check metric values are reasonable
        assert result.metrics["volume_mm3"] > 0
        assert result.metrics["surface_area_mm2"] > 0
