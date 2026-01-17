"""Tests for main generator pipeline."""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from surgical_guide_generator.generator import (
    generate_surgical_guide,
    GenerationResult,
    create_simple_guide_body,
)
from surgical_guide_generator.config import ImplantSite, SleeveSpec, GuideConfig


@pytest.fixture
def implant_sites():
    """Create sample implant sites."""
    return [
        ImplantSite(
            site_id="36",
            position=[10.0, 5.0, 5.0],
            direction=[0.0, 0.1, -0.995],
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        ),
        ImplantSite(
            site_id="46",
            position=[-10.0, 5.0, 5.0],
            direction=[0.0, 0.1, -0.995],
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        ),
    ]


class TestCreateSimpleGuideBody:
    """Test simple guide body creation (placeholder for SDF)."""

    def test_create_simple_body_box(self) -> None:
        """Test creating a simple box guide body."""
        guide = create_simple_guide_body(
            extents=[50, 30, 10]
        )

        import trimesh
        assert isinstance(guide, trimesh.Trimesh)
        assert guide.is_watertight
        assert guide.is_volume
        assert guide.volume > 0

    def test_create_simple_body_centered(self) -> None:
        """Test that guide body is properly centered."""
        guide = create_simple_guide_body(
            extents=[40, 20, 8],
            center=[0, 0, 4]  # Center at Z=4
        )

        bounds = guide.bounds
        # Check that center is approximately correct
        actual_center = (bounds[0] + bounds[1]) / 2
        assert np.allclose(actual_center, [0, 0, 4], atol=0.5)


class TestGenerationResult:
    """Test GenerationResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a generation result."""
        import trimesh
        guide = trimesh.creation.box(extents=[10, 10, 10])

        result = GenerationResult(
            success=True,
            guide_mesh=guide,
            operations_performed=["create_body", "subtract_channels"],
            metrics={"volume": 1000.0},
        )

        assert result.success is True
        assert result.guide_mesh is not None
        assert len(result.operations_performed) == 2

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        import trimesh
        guide = trimesh.creation.box(extents=[10, 10, 10])

        result = GenerationResult(
            success=True,
            guide_mesh=guide,
            operations_performed=["test"],
            metrics={"test": 1},
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "operations_performed" in result_dict
        assert "metrics" in result_dict


class TestGenerateSurgicalGuide:
    """Test main guide generation function."""

    def test_generate_simple_guide(self, implant_sites, tmp_path) -> None:
        """Test generating a simple guide with placeholder body."""
        output_file = tmp_path / "test_guide.stl"
        config = GuideConfig()

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],  # Simple box for now
            implant_sites=implant_sites,
            output_path=str(output_file),
            config=config,
        )

        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.guide_mesh is not None
        assert result.guide_mesh.is_volume

        # Check operations were performed
        assert "create_body" in result.operations_performed
        assert "subtract_channels" in result.operations_performed

        # Output file should exist
        assert output_file.exists()

    def test_generate_guide_with_windows(self, implant_sites, tmp_path) -> None:
        """Test generating guide with inspection windows."""
        output_file = tmp_path / "test_guide_windows.stl"
        config = GuideConfig(add_inspection_windows=True)

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=implant_sites,
            output_path=str(output_file),
            config=config,
        )

        assert result.success is True
        # Windows should be in operations
        assert "add_windows" in result.operations_performed

    def test_generate_guide_without_windows(self, implant_sites, tmp_path) -> None:
        """Test generating guide without inspection windows."""
        output_file = tmp_path / "test_guide_no_windows.stl"
        config = GuideConfig(add_inspection_windows=False)

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=implant_sites,
            output_path=str(output_file),
            config=config,
        )

        assert result.success is True
        # Windows should NOT be in operations
        assert "add_windows" not in result.operations_performed

    def test_generate_guide_metrics(self, implant_sites, tmp_path) -> None:
        """Test that generation includes comprehensive metrics."""
        output_file = tmp_path / "test_guide_metrics.stl"
        config = GuideConfig()

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=implant_sites,
            output_path=str(output_file),
            config=config,
        )

        # Check metrics are present
        assert "final_volume_mm3" in result.metrics
        assert "final_face_count" in result.metrics
        assert "is_watertight" in result.metrics
        assert result.metrics["is_watertight"] is True

    def test_generate_guide_single_implant(self, tmp_path) -> None:
        """Test generating guide for single implant."""
        site = ImplantSite(
            site_id="36",
            position=[0.0, 0.0, 5.0],
            direction=[0.0, 0.0, -1.0],
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        )

        output_file = tmp_path / "single_implant.stl"
        config = GuideConfig()

        result = generate_surgical_guide(
            guide_body_extents=[30, 30, 10],
            implant_sites=[site],
            output_path=str(output_file),
            config=config,
        )

        assert result.success is True
        assert result.guide_mesh.is_watertight

    def test_generate_guide_validation(self, implant_sites, tmp_path) -> None:
        """Test that generated guide is validated."""
        output_file = tmp_path / "validated_guide.stl"
        config = GuideConfig()

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=implant_sites,
            output_path=str(output_file),
            config=config,
        )

        # Validation metrics should be present
        assert "validation" in result.metrics
        assert result.metrics["validation"]["is_valid"] is True

    def test_generate_guide_empty_sites(self, tmp_path) -> None:
        """Test generating guide with no implants (should fail)."""
        output_file = tmp_path / "empty_guide.stl"
        config = GuideConfig()

        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=[],
            output_path=str(output_file),
            config=config,
        )

        # Should fail or warn about no implants
        assert result.success is False or len(result.warnings) > 0
