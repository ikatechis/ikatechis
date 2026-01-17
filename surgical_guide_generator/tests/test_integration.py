"""Integration tests for end-to-end surgical guide generation.

Tests the complete pipeline from JSON input to STL output using realistic fixtures.
"""

import pytest
import json
import tempfile
from pathlib import Path
import trimesh

from surgical_guide_generator import generate_surgical_guide, GuideConfig
from surgical_guide_generator.cli import (
    load_implant_sites_from_json,
    create_example_config,
    main,
    parse_args,
)
from surgical_guide_generator.mesh_io import load_mesh
from surgical_guide_generator.validation import validate_mesh


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEndToEndGeneration:
    """Test complete guide generation from fixtures."""

    def test_single_implant_full_pipeline(self, tmp_path) -> None:
        """Test complete pipeline with single implant fixture."""
        # Load fixture
        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Generate guide
        output_path = tmp_path / "single_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        # Verify success
        assert result.success is True
        assert result.error_message is None
        assert result.guide_mesh is not None

        # Verify file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify mesh quality
        assert result.metrics["is_watertight"] is True
        assert result.metrics["final_volume_mm3"] > 0
        assert result.metrics["final_face_count"] > 0

        # Load and validate exported mesh
        loaded_mesh = load_mesh(str(output_path))
        assert loaded_mesh.is_watertight
        assert loaded_mesh.is_volume

    def test_bilateral_implants_full_pipeline(self, tmp_path) -> None:
        """Test complete pipeline with bilateral implants fixture."""
        fixture_path = FIXTURES_DIR / "bilateral_implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Generate with inspection windows
        output_path = tmp_path / "bilateral_guide.stl"
        config = GuideConfig(add_inspection_windows=True)

        result = generate_surgical_guide(
            guide_body_extents=[60, 35, 10],
            implant_sites=sites,
            output_path=str(output_path),
            config=config,
        )

        # Verify success
        assert result.success is True
        assert len(sites) == 2

        # Verify operations
        assert "create_body" in result.operations_performed
        assert "subtract_channels" in result.operations_performed
        assert "add_windows" in result.operations_performed

        # Verify watertight
        assert result.metrics["is_watertight"] is True

    def test_full_arch_4implants_pipeline(self, tmp_path) -> None:
        """Test complete pipeline with full arch (4 implants) fixture."""
        fixture_path = FIXTURES_DIR / "full_arch_4implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Generate with custom config
        output_path = tmp_path / "full_arch_guide.stl"
        config = GuideConfig(
            thickness=3.0,
            tissue_gap=0.2,
            add_inspection_windows=True,
            window_width=12.0,
        )

        result = generate_surgical_guide(
            guide_body_extents=[70, 40, 12],
            implant_sites=sites,
            output_path=str(output_path),
            config=config,
        )

        # Verify success
        assert result.success is True
        assert len(sites) == 4

        # Verify all operations performed
        assert "create_body" in result.operations_performed
        assert "subtract_channels" in result.operations_performed
        assert "add_windows" in result.operations_performed

        # Verify mesh is valid
        validation = result.metrics["validation"]
        assert validation["is_valid"] is True

    def test_anterior_implant_pipeline(self, tmp_path) -> None:
        """Test complete pipeline with anterior implant (angled) fixture."""
        fixture_path = FIXTURES_DIR / "anterior_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "anterior_guide.stl"

        result = generate_surgical_guide(
            guide_body_extents=[40, 25, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True
        assert result.guide_mesh.is_watertight

        # Verify file created
        assert output_path.exists()


class TestCLIIntegration:
    """Test CLI interface with fixtures."""

    def test_cli_single_implant(self, tmp_path, monkeypatch) -> None:
        """Test CLI with single implant fixture."""
        fixture_path = FIXTURES_DIR / "single_implant.json"
        output_path = tmp_path / "cli_guide.stl"

        # Simulate command line arguments
        args = [
            "--implants", str(fixture_path),
            "--output", str(output_path),
        ]

        # Parse arguments
        parsed = parse_args(args)
        assert parsed.implants == str(fixture_path)
        assert parsed.output == str(output_path)

    def test_cli_with_custom_parameters(self, tmp_path) -> None:
        """Test CLI with custom parameters."""
        fixture_path = FIXTURES_DIR / "bilateral_implants.json"
        output_path = tmp_path / "custom_guide.stl"

        args = [
            "--implants", str(fixture_path),
            "--output", str(output_path),
            "--extents", "60", "35", "12",
            "--thickness", "3.0",
            "--tissue-gap", "0.2",
            "--window-width", "15.0",
            "--verbose",
        ]

        parsed = parse_args(args)
        assert parsed.extents == [60.0, 35.0, 12.0]
        assert parsed.thickness == 3.0
        assert parsed.tissue_gap == 0.2
        assert parsed.window_width == 15.0
        assert parsed.verbose is True

    def test_cli_create_example(self, tmp_path) -> None:
        """Test CLI example creation."""
        output_path = tmp_path / "example.json"

        create_example_config(str(output_path))

        # Verify file created
        assert output_path.exists()

        # Verify it's valid JSON
        with open(output_path) as f:
            data = json.load(f)

        assert "implant_sites" in data
        assert len(data["implant_sites"]) == 2

    def test_cli_no_windows_flag(self, tmp_path) -> None:
        """Test CLI with --no-windows flag."""
        fixture_path = FIXTURES_DIR / "bilateral_implants.json"
        output_path = tmp_path / "no_windows_guide.stl"

        args = [
            "--implants", str(fixture_path),
            "--output", str(output_path),
            "--no-windows",
        ]

        parsed = parse_args(args)
        assert parsed.no_windows is True


class TestFileFormats:
    """Test different input/output file formats."""

    def test_export_stl_format(self, tmp_path) -> None:
        """Test exporting to STL format."""
        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True
        assert output_path.exists()
        assert output_path.suffix == ".stl"

        # Verify it's loadable as STL
        mesh = trimesh.load(str(output_path))
        assert isinstance(mesh, trimesh.Trimesh)

    def test_export_3mf_format(self, tmp_path) -> None:
        """Test exporting to 3MF format."""
        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "guide.3mf"
        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True
        assert output_path.exists()
        assert output_path.suffix == ".3mf"


class TestQualityMetrics:
    """Test quality metrics in integration scenarios."""

    def test_metrics_completeness(self, tmp_path) -> None:
        """Test that all expected metrics are present."""
        fixture_path = FIXTURES_DIR / "bilateral_implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "metrics_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[60, 35, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        # Check required metrics
        required_metrics = [
            "final_volume_mm3",
            "final_face_count",
            "is_watertight",
            "validation",
        ]

        for metric in required_metrics:
            assert metric in result.metrics

    def test_validation_integration(self, tmp_path) -> None:
        """Test that validation is integrated into pipeline."""
        fixture_path = FIXTURES_DIR / "full_arch_4implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "validated_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[70, 40, 12],
            implant_sites=sites,
            output_path=str(output_path),
        )

        # Check validation was performed
        assert "validation" in result.metrics
        validation = result.metrics["validation"]

        assert "is_valid" in validation
        assert validation["is_valid"] is True


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_json_path(self) -> None:
        """Test handling of non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            load_implant_sites_from_json("nonexistent.json")

    def test_invalid_json_format(self, tmp_path) -> None:
        """Test handling of invalid JSON format."""
        invalid_json = tmp_path / "invalid.json"
        with open(invalid_json, "w") as f:
            f.write("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            load_implant_sites_from_json(str(invalid_json))

    def test_missing_implant_sites_key(self, tmp_path) -> None:
        """Test handling of JSON without 'implant_sites' key."""
        invalid_json = tmp_path / "no_sites.json"
        with open(invalid_json, "w") as f:
            json.dump({"wrong_key": []}, f)

        with pytest.raises(ValueError, match="must contain 'implant_sites'"):
            load_implant_sites_from_json(str(invalid_json))

    def test_empty_implant_sites(self, tmp_path) -> None:
        """Test handling of empty implant sites list."""
        empty_json = tmp_path / "empty.json"
        with open(empty_json, "w") as f:
            json.dump({"implant_sites": []}, f)

        sites = load_implant_sites_from_json(str(empty_json))
        assert len(sites) == 0

        # Generate guide with empty sites (should fail or warn)
        output_path = tmp_path / "empty_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        # Should either fail or have warnings
        assert result.success is False or len(result.warnings) > 0


class TestRealisticScenarios:
    """Test realistic clinical scenarios."""

    def test_narrow_anterior_implant(self, tmp_path) -> None:
        """Test generation with narrow anterior implant."""
        fixture_path = FIXTURES_DIR / "anterior_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Verify it's a narrow implant
        assert sites[0].implant_diameter == 3.3
        assert sites[0].sleeve_spec.outer_diameter == 4.5

        output_path = tmp_path / "narrow_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[40, 25, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True
        assert result.metrics["is_watertight"] is True

    def test_mixed_implant_sizes(self, tmp_path) -> None:
        """Test generation with mixed implant sizes (full arch)."""
        fixture_path = FIXTURES_DIR / "full_arch_4implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Verify we have different sizes
        diameters = [site.implant_diameter for site in sites]
        assert 3.5 in diameters  # Anterior
        assert 4.1 in diameters  # Posterior

        output_path = tmp_path / "mixed_sizes_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[70, 40, 12],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True

    def test_symmetric_bilateral_placement(self, tmp_path) -> None:
        """Test bilateral symmetric placement."""
        fixture_path = FIXTURES_DIR / "bilateral_implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        # Verify symmetric placement (X coordinates should be opposite)
        assert len(sites) == 2
        x_positions = [site.position[0] for site in sites]

        # Should be roughly symmetric around midline
        assert abs(abs(x_positions[0]) - abs(x_positions[1])) < 1.0

        output_path = tmp_path / "symmetric_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[60, 35, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True


class TestPerformance:
    """Test performance characteristics."""

    def test_generation_time_single_implant(self, tmp_path) -> None:
        """Test single implant generation time (basic timing)."""
        import time

        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))
        output_path = tmp_path / "bench_single.stl"

        start = time.time()
        result = generate_surgical_guide(
            guide_body_extents=[50, 30, 10],
            implant_sites=sites,
            output_path=str(output_path),
        )
        elapsed = time.time() - start

        assert result.success is True
        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10.0

    def test_generation_time_full_arch(self, tmp_path) -> None:
        """Test generation time for full arch (4 implants)."""
        import time

        fixture_path = FIXTURES_DIR / "full_arch_4implants.json"
        sites = load_implant_sites_from_json(str(fixture_path))
        output_path = tmp_path / "bench_full_arch.stl"

        start = time.time()
        result = generate_surgical_guide(
            guide_body_extents=[70, 40, 12],
            implant_sites=sites,
            output_path=str(output_path),
        )
        elapsed = time.time() - start

        assert result.success is True
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30.0


class TestRobustness:
    """Test robustness to edge cases."""

    def test_very_small_guide_extents(self, tmp_path) -> None:
        """Test with very small guide dimensions."""
        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "small_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[20, 15, 5],  # Very small
            implant_sites=sites,
            output_path=str(output_path),
        )

        # Should still work (though may have warnings)
        assert result.success is True or len(result.warnings) > 0

    def test_very_large_guide_extents(self, tmp_path) -> None:
        """Test with very large guide dimensions."""
        fixture_path = FIXTURES_DIR / "single_implant.json"
        sites = load_implant_sites_from_json(str(fixture_path))

        output_path = tmp_path / "large_guide.stl"
        result = generate_surgical_guide(
            guide_body_extents=[100, 80, 20],  # Very large
            implant_sites=sites,
            output_path=str(output_path),
        )

        assert result.success is True
        # Volume should be large
        assert result.metrics["final_volume_mm3"] > 50000
