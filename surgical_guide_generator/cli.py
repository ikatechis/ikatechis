"""Command-line interface for surgical guide generator."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from surgical_guide_generator.generator import generate_surgical_guide
from surgical_guide_generator.config import ImplantSite, SleeveSpec, GuideConfig


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of arguments (for testing). Uses sys.argv if None.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Generate 3D-printable dental implant surgical guides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate guide from implants JSON file
  surgical-guide --implants sites.json --output guide.stl

  # Generate with custom guide dimensions
  surgical-guide --implants sites.json --output guide.3mf \\
                 --extents 50 30 10

  # Generate with custom parameters
  surgical-guide --implants sites.json --output guide.stl \\
                 --thickness 3.0 --tissue-gap 0.2 --no-windows

  # Create example configuration file
  surgical-guide --create-example example.json
        """
    )

    # Main arguments
    parser.add_argument(
        '--implants',
        type=str,
        help='Path to JSON file containing implant site specifications',
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path (.stl or .3mf)',
    )

    # Guide body dimensions
    parser.add_argument(
        '--extents',
        type=float,
        nargs=3,
        default=[50.0, 30.0, 10.0],
        metavar=('LENGTH', 'WIDTH', 'HEIGHT'),
        help='Guide body extents in mm (default: 50 30 10)',
    )

    # Configuration options
    parser.add_argument(
        '--thickness',
        type=float,
        default=2.5,
        help='Guide shell thickness in mm (default: 2.5)',
    )

    parser.add_argument(
        '--tissue-gap',
        type=float,
        default=0.15,
        help='Gap from tissue surface in mm (default: 0.15)',
    )

    parser.add_argument(
        '--no-windows',
        action='store_true',
        help='Disable inspection windows',
    )

    parser.add_argument(
        '--window-width',
        type=float,
        default=10.0,
        help='Inspection window width in mm (default: 10.0)',
    )

    # Utility options
    parser.add_argument(
        '--create-example',
        type=str,
        metavar='FILE',
        help='Create an example implants JSON file and exit',
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output',
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0',
    )

    return parser.parse_args(args)


def load_implant_sites_from_json(json_path: str) -> List[ImplantSite]:
    """Load implant sites from JSON file.

    Args:
        json_path: Path to JSON file

    Returns:
        List of ImplantSite objects

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If JSON structure is invalid

    Example JSON format:
        {
          "implant_sites": [
            {
              "site_id": "36",
              "position": [25.5, -12.3, 8.7],
              "direction": [0.0, 0.1, -0.995],
              "sleeve_outer_diameter": 5.0,
              "sleeve_inner_diameter": 4.0,
              "sleeve_height": 5.0
            }
          ]
        }
    """
    path = Path(json_path)

    if not path.exists():
        raise FileNotFoundError(f"Implants file not found: {json_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    if 'implant_sites' not in data:
        raise ValueError("JSON must contain 'implant_sites' key")

    sites = []
    for site_data in data['implant_sites']:
        # Create SleeveSpec
        sleeve_spec = SleeveSpec(
            outer_diameter=site_data['sleeve_outer_diameter'],
            inner_diameter=site_data['sleeve_inner_diameter'],
            height=site_data['sleeve_height'],
            clearance=site_data.get('clearance', 0.05),
        )

        # Create ImplantSite
        site = ImplantSite(
            site_id=site_data['site_id'],
            position=site_data['position'],
            direction=site_data['direction'],
            sleeve_spec=sleeve_spec,
            implant_diameter=site_data.get('implant_diameter', 0.0),
            implant_length=site_data.get('implant_length', 0.0),
        )

        sites.append(site)

    return sites


def create_example_config(output_path: str) -> None:
    """Create an example implants JSON configuration file.

    Args:
        output_path: Where to write the example file
    """
    example = {
        "implant_sites": [
            {
                "site_id": "36",
                "position": [25.5, -12.3, 8.7],
                "direction": [0.0, 0.1, -0.995],
                "implant_diameter": 4.1,
                "implant_length": 10.0,
                "sleeve_outer_diameter": 5.0,
                "sleeve_inner_diameter": 4.0,
                "sleeve_height": 5.0,
                "clearance": 0.05
            },
            {
                "site_id": "46",
                "position": [-24.8, -11.9, 9.1],
                "direction": [0.0, 0.08, -0.997],
                "implant_diameter": 4.1,
                "implant_length": 10.0,
                "sleeve_outer_diameter": 5.0,
                "sleeve_inner_diameter": 4.0,
                "sleeve_height": 5.0,
                "clearance": 0.05
            }
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(example, f, indent=2)

    print(f"Example configuration written to: {output_path}")


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        args = parse_args()

        # Handle --create-example
        if args.create_example:
            create_example_config(args.create_example)
            return 0

        # Validate required arguments
        if not args.implants or not args.output:
            print("Error: --implants and --output are required", file=sys.stderr)
            print("Use --help for usage information", file=sys.stderr)
            sys.exit(1)

        # Load implant sites
        if args.verbose:
            print(f"Loading implant sites from: {args.implants}")

        sites = load_implant_sites_from_json(args.implants)

        if args.verbose:
            print(f"Loaded {len(sites)} implant site(s)")
            for site in sites:
                print(f"  - Site {site.site_id}: position={site.position}")

        # Create configuration
        config = GuideConfig(
            thickness=args.thickness,
            tissue_gap=args.tissue_gap,
            add_inspection_windows=not args.no_windows,
            window_width=args.window_width,
        )

        if args.verbose:
            print(f"\nConfiguration:")
            print(f"  Thickness: {config.thickness}mm")
            print(f"  Tissue gap: {config.tissue_gap}mm")
            print(f"  Inspection windows: {config.add_inspection_windows}")
            print(f"  Guide extents: {args.extents}")

        # Generate guide
        print(f"\nGenerating surgical guide...")

        result = generate_surgical_guide(
            guide_body_extents=args.extents,
            implant_sites=sites,
            output_path=args.output,
            config=config,
        )

        if result.success:
            print(f"\n✓ Guide generated successfully!")
            print(f"  Output: {args.output}")
            print(f"  Volume: {result.metrics['final_volume_mm3']:.1f} mm³")
            print(f"  Faces: {result.metrics['final_face_count']}")
            print(f"  Watertight: {result.metrics['is_watertight']}")

            if result.warnings:
                print(f"\nWarnings:")
                for warning in result.warnings:
                    print(f"  ! {warning}")

            return 0
        else:
            print(f"\n✗ Guide generation failed: {result.error_message}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
