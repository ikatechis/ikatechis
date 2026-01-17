"""Tests for configuration module."""

import pytest
from dataclasses import asdict
from surgical_guide_generator.config import (
    GuideConfig,
    ImplantSite,
    SleeveSpec,
    ValidationConfig,
)


class TestSleeveSpec:
    """Test SleeveSpec dataclass."""

    def test_sleeve_spec_creation(self) -> None:
        """Test creating a sleeve specification."""
        sleeve = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
            clearance=0.05,
        )
        assert sleeve.outer_diameter == 5.0
        assert sleeve.inner_diameter == 4.0
        assert sleeve.height == 5.0
        assert sleeve.clearance == 0.05

    def test_sleeve_spec_defaults(self) -> None:
        """Test default values for sleeve specification."""
        sleeve = SleeveSpec(
            outer_diameter=5.0,
            inner_diameter=4.0,
            height=5.0,
        )
        assert sleeve.clearance == 0.05  # Default value

    def test_sleeve_spec_validation(self) -> None:
        """Test that sleeve dimensions are validated."""
        with pytest.raises(ValueError, match="Outer diameter.*must be greater than.*inner diameter"):
            SleeveSpec(
                outer_diameter=4.0,
                inner_diameter=5.0,  # Invalid: inner > outer
                height=5.0,
            )

    def test_sleeve_spec_positive_dimensions(self) -> None:
        """Test that dimensions must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            SleeveSpec(
                outer_diameter=-5.0,
                inner_diameter=4.0,
                height=5.0,
            )


class TestImplantSite:
    """Test ImplantSite dataclass."""

    def test_implant_site_creation(self) -> None:
        """Test creating an implant site."""
        site = ImplantSite(
            site_id="36",
            position=[25.5, -12.3, 8.7],
            direction=[0.0, 0.1, -0.995],
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        )
        assert site.site_id == "36"
        assert len(site.position) == 3
        assert len(site.direction) == 3

    def test_implant_site_direction_normalization(self) -> None:
        """Test that direction vector is normalized."""
        site = ImplantSite(
            site_id="36",
            position=[25.5, -12.3, 8.7],
            direction=[0.0, 2.0, -2.0],  # Not normalized
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        )
        # After normalization, the direction should have unit length
        import numpy as np
        assert np.allclose(np.linalg.norm(site.direction), 1.0)

    def test_implant_site_invalid_position(self) -> None:
        """Test that position must have 3 coordinates."""
        with pytest.raises(ValueError, match="Position must have 3 coordinates"):
            ImplantSite(
                site_id="36",
                position=[25.5, -12.3],  # Only 2 coordinates
                direction=[0.0, 0.1, -0.995],
                sleeve_spec=SleeveSpec(
                    outer_diameter=5.0,
                    inner_diameter=4.0,
                    height=5.0,
                ),
            )

    def test_implant_site_to_dict(self) -> None:
        """Test conversion to dictionary."""
        site = ImplantSite(
            site_id="36",
            position=[25.5, -12.3, 8.7],
            direction=[0.0, 0.1, -0.995],
            sleeve_spec=SleeveSpec(
                outer_diameter=5.0,
                inner_diameter=4.0,
                height=5.0,
            ),
        )
        site_dict = asdict(site)
        assert site_dict["site_id"] == "36"
        assert "position" in site_dict
        assert "sleeve_spec" in site_dict


class TestGuideConfig:
    """Test GuideConfig dataclass."""

    def test_guide_config_defaults(self) -> None:
        """Test default configuration values."""
        config = GuideConfig()
        assert config.thickness == 2.5
        assert config.tissue_gap == 0.15
        assert config.voxel_size == 0.15
        assert config.add_inspection_windows is True
        assert config.window_width == 10.0

    def test_guide_config_custom_values(self) -> None:
        """Test custom configuration values."""
        config = GuideConfig(
            thickness=3.0,
            tissue_gap=0.2,
            voxel_size=0.1,
            add_inspection_windows=False,
        )
        assert config.thickness == 3.0
        assert config.tissue_gap == 0.2
        assert config.voxel_size == 0.1
        assert config.add_inspection_windows is False

    def test_guide_config_validation_thickness(self) -> None:
        """Test that thickness is validated."""
        with pytest.raises(ValueError, match="Thickness must be between"):
            GuideConfig(thickness=0.5)  # Too thin

        with pytest.raises(ValueError, match="Thickness must be between"):
            GuideConfig(thickness=6.0)  # Too thick

    def test_guide_config_validation_voxel_size(self) -> None:
        """Test that voxel size is validated."""
        with pytest.raises(ValueError, match="Voxel size must be between"):
            GuideConfig(voxel_size=0.05)  # Too small

        with pytest.raises(ValueError, match="Voxel size must be between"):
            GuideConfig(voxel_size=1.0)  # Too large


class TestValidationConfig:
    """Test ValidationConfig dataclass."""

    def test_validation_config_defaults(self) -> None:
        """Test default validation configuration."""
        config = ValidationConfig()
        assert config.check_watertight is True
        assert config.check_self_intersection is False
        assert config.min_wall_thickness == 2.0
        assert config.repair_if_needed is True

    def test_validation_config_custom(self) -> None:
        """Test custom validation configuration."""
        config = ValidationConfig(
            check_watertight=True,
            check_self_intersection=True,
            min_wall_thickness=2.5,
            repair_if_needed=False,
        )
        assert config.check_self_intersection is True
        assert config.min_wall_thickness == 2.5
        assert config.repair_if_needed is False
