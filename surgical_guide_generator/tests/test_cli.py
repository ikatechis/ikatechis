"""Tests for CLI interface."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

from surgical_guide_generator.cli import (
    main,
    parse_args,
    load_implant_sites_from_json,
    create_example_config,
)


@pytest.fixture
def sample_implants_json(tmp_path):
    """Create a sample implants JSON file."""
    data = {
        "implant_sites": [
            {
                "site_id": "36",
                "position": [10.0, 5.0, 5.0],
                "direction": [0.0, 0.1, -0.995],
                "sleeve_outer_diameter": 5.0,
                "sleeve_inner_diameter": 4.0,
                "sleeve_height": 5.0,
            },
            {
                "site_id": "46",
                "position": [-10.0, 5.0, 5.0],
                "direction": [0.0, 0.1, -0.995],
                "sleeve_outer_diameter": 5.0,
                "sleeve_inner_diameter": 4.0,
                "sleeve_height": 5.0,
            }
        ]
    }

    json_file = tmp_path / "implants.json"
    json_file.write_text(json.dumps(data, indent=2))
    return str(json_file)


class TestParseArgs:
    """Test argument parsing."""

    def test_parse_args_minimal(self):
        """Test parsing with minimal required arguments."""
        args = parse_args([
            "--implants", "implants.json",
            "--output", "guide.stl",
        ])

        assert args.implants == "implants.json"
        assert args.output == "guide.stl"

    def test_parse_args_with_extents(self):
        """Test parsing with guide body extents."""
        args = parse_args([
            "--implants", "implants.json",
            "--output", "guide.stl",
            "--extents", "50", "30", "10",
        ])

        assert args.extents == [50.0, 30.0, 10.0]

    def test_parse_args_with_config(self):
        """Test parsing with configuration options."""
        args = parse_args([
            "--implants", "implants.json",
            "--output", "guide.stl",
            "--thickness", "3.0",
            "--no-windows",
        ])

        assert args.thickness == 3.0
        assert args.no_windows is True

    def test_parse_args_with_verbose(self):
        """Test parsing with verbose flag."""
        args = parse_args([
            "--implants", "implants.json",
            "--output", "guide.stl",
            "--verbose",
        ])

        assert args.verbose is True


class TestLoadImplantSitesFromJson:
    """Test loading implant sites from JSON."""

    def test_load_valid_json(self, sample_implants_json):
        """Test loading valid implants JSON file."""
        sites = load_implant_sites_from_json(sample_implants_json)

        assert len(sites) == 2
        assert sites[0].site_id == "36"
        assert sites[1].site_id == "46"

    def test_load_json_with_minimal_fields(self, tmp_path):
        """Test loading JSON with only required fields."""
        data = {
            "implant_sites": [
                {
                    "site_id": "36",
                    "position": [10.0, 5.0, 5.0],
                    "direction": [0.0, 0.0, -1.0],
                    "sleeve_outer_diameter": 5.0,
                    "sleeve_inner_diameter": 4.0,
                    "sleeve_height": 5.0,
                }
            ]
        }

        json_file = tmp_path / "minimal.json"
        json_file.write_text(json.dumps(data))

        sites = load_implant_sites_from_json(str(json_file))
        assert len(sites) == 1

    def test_load_json_invalid_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_implant_sites_from_json("/nonexistent/file.json")

    def test_load_json_invalid_format(self, tmp_path):
        """Test loading invalid JSON format."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            load_implant_sites_from_json(str(json_file))


class TestCreateExampleConfig:
    """Test example configuration creation."""

    def test_create_example_config(self, tmp_path):
        """Test creating example configuration file."""
        output_file = tmp_path / "example.json"

        create_example_config(str(output_file))

        assert output_file.exists()

        # Load and verify structure
        with open(output_file) as f:
            data = json.load(f)

        assert "implant_sites" in data
        assert len(data["implant_sites"]) > 0
        assert "site_id" in data["implant_sites"][0]


class TestMainCLI:
    """Test main CLI entry point."""

    def test_main_with_valid_inputs(self, sample_implants_json, tmp_path):
        """Test running CLI with valid inputs."""
        output_file = tmp_path / "guide.stl"

        with patch.object(sys, 'argv', [
            'surgical-guide',
            '--implants', sample_implants_json,
            '--output', str(output_file),
            '--extents', '50', '30', '10',
        ]):
            exit_code = main()

        assert exit_code == 0
        assert output_file.exists()

    def test_main_create_example(self, tmp_path):
        """Test creating example configuration."""
        output_file = tmp_path / "example.json"

        with patch.object(sys, 'argv', [
            'surgical-guide',
            '--create-example', str(output_file),
        ]):
            exit_code = main()

        assert exit_code == 0
        assert output_file.exists()

    def test_main_missing_required_args(self):
        """Test that missing required arguments fails gracefully."""
        with patch.object(sys, 'argv', ['surgical-guide']):
            with pytest.raises(SystemExit):
                main()

    def test_main_verbose_mode(self, sample_implants_json, tmp_path):
        """Test running with verbose output."""
        output_file = tmp_path / "guide.stl"

        with patch.object(sys, 'argv', [
            'surgical-guide',
            '--implants', sample_implants_json,
            '--output', str(output_file),
            '--extents', '50', '30', '10',
            '--verbose',
        ]):
            exit_code = main()

        assert exit_code == 0

    def test_main_with_custom_config(self, sample_implants_json, tmp_path):
        """Test running with custom configuration."""
        output_file = tmp_path / "guide.stl"

        with patch.object(sys, 'argv', [
            'surgical-guide',
            '--implants', sample_implants_json,
            '--output', str(output_file),
            '--extents', '50', '30', '10',
            '--thickness', '3.0',
            '--tissue-gap', '0.2',
            '--no-windows',
        ]):
            exit_code = main()

        assert exit_code == 0
        assert output_file.exists()
