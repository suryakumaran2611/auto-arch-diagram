#!/usr/bin/env python3
"""
Regenerate draw.io XML files for all examples.

Usage:
    python tools/regenerate_drawio.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    base_path = Path("/mnt/c/Users/surya/OneDrive/Documents/GitHub/auto-arch-diagram")
    svg_files = list((base_path / "examples").rglob("architecture-diagram.svg"))

    print(f"Found {len(svg_files)} SVG files to convert\n")

    success = 0
    failed = 0

    for svg_path in sorted(svg_files):
        output_path = svg_path.with_suffix(".drawio.xml")
        rel_path = svg_path.relative_to(base_path)

        print(f"Converting: {rel_path}")

        try:
            result = subprocess.run(
                [
                    "python3",
                    str(base_path / "tools" / "svg_to_drawio.py"),
                    str(svg_path),
                    "-o",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"  -> {output_path.name}")
                success += 1
            else:
                print(f"  ERROR: {result.stderr}")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Total: {len(svg_files)}")
    print(f"Success: {success}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
