"""
Surgical Guide Generator

Automated pipeline for generating 3D-printable dental implant surgical guides.
"""

__version__ = "0.1.0"

from surgical_guide_generator.generator import generate_surgical_guide, GenerationResult
from surgical_guide_generator.config import (
    ImplantSite,
    SleeveSpec,
    GuideConfig,
    ValidationConfig,
)

__all__ = [
    "generate_surgical_guide",
    "GenerationResult",
    "ImplantSite",
    "SleeveSpec",
    "GuideConfig",
    "ValidationConfig",
]
