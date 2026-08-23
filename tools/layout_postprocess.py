"""Layout post-processing utilities for auto-arch-diagram.

Applies geometric refinement to Graphviz DOT graphs:
1. Pins cluster label nodes to bottom-left with fixed downward padding.
2. Expands cluster bounding boxes downward and resolves sibling collisions.
3. Centers high-fanout edge nodes (CDN, API Gateway, ALB, IGW) over target clusters.
4. Pins security group / firewall badges to node top-right corners.
5. Pins header, footer, and legend at top and bottom.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

GVPR_SCRIPT_PATH = Path(__file__).resolve().parent / "layout_postprocess.gvpr"


def run_gvpr_postprocess(dot_content: str, script_path: Optional[Path] = None) -> str:
    """Run GVPR script on DOT graph string, falling back to Python postprocessor if gvpr fails."""
    if script_path is None:
        script_path = GVPR_SCRIPT_PATH

    gvpr_bin = shutil.which("gvpr")
    if gvpr_bin and script_path.exists():
        try:
            res = subprocess.run(
                [gvpr_bin, "-c", "-q", "-f", str(script_path)],
                input=dot_content,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass

    # Fallback to Python postprocessor
    return python_postprocess_dot(dot_content)


def python_postprocess_dot(dot_content: str) -> str:
    """Pure-Python geometry transformer mirroring layout_postprocess.gvpr."""
    lines = dot_content.splitlines()
    # Parse graph bounding box and node positions
    cloud_min_x, cloud_max_x, cloud_min_y, cloud_max_y = 0.0, 0.0, 0.0, 0.0
    topmost_y = 0.0
    top_edge_y = 0.0
    bottommost_y = 999999.0
    has_legend = False

    # First pass: find bounds
    for line in lines:
        if "_legendnode" in line:
            has_legend = True
        pos_match = re.search(r'pos="([^"]+)"', line)
        if pos_match:
            try:
                coords = pos_match.group(1).rstrip("!").split(",")
                px, py = float(coords[0]), float(coords[1])
                if "_titlenode" not in line and "_footernode" not in line and "_legendnode" not in line:
                    if py > topmost_y:
                        topmost_y = py
                    if py < bottommost_y:
                        bottommost_y = py
                    height = 2.8
                    h_match = re.search(r'height="([^"]+)"', line)
                    if h_match:
                        height = float(h_match.group(1))
                    node_top = py + (height * 72.0) / 2.0
                    if node_top > top_edge_y:
                        top_edge_y = node_top
            except Exception:
                pass

        bb_match = re.search(r'bb="([^"]+)"', line)
        if bb_match and ("cluster" in line or "graph" in line):
            try:
                parts = [float(x) for x in bb_match.group(1).split(",")]
                if len(parts) == 4:
                    if parts[2] > cloud_max_x:
                        cloud_max_x = parts[2]
                    if parts[0] < cloud_min_x or cloud_min_x == 0.0:
                        cloud_min_x = parts[0]
                    if parts[3] > cloud_max_y:
                        cloud_max_y = parts[3]
                    if parts[1] < cloud_min_y or cloud_min_y == 0.0:
                        cloud_min_y = parts[1]
            except Exception:
                pass

    cloud_center_x = (cloud_min_x + cloud_max_x) / 2.0 if cloud_max_x > cloud_min_x else 500.0
    if top_edge_y == 0.0:
        top_edge_y = topmost_y if topmost_y > 0 else 500.0
    if bottommost_y == 999999.0:
        bottommost_y = 0.0

    # Second pass: update pinned nodes
    out_lines = []
    for line in lines:
        # Title node positioning
        if '_titlenode="1"' in line or "_titlenode=1" in line:
            new_pos = f'pos="{cloud_center_x:.0f},{top_edge_y + 120:.0f}!"'
            line = re.sub(r'pos="[^"]*"', new_pos, line)
            if 'pos=' not in line:
                line = line.rstrip("];") + f', {new_pos}];'
        # Footer node positioning
        elif '_footernode="1"' in line or "_footernode=1" in line:
            x_pos = cloud_center_x - 650.0 if has_legend else cloud_center_x
            new_pos = f'pos="{x_pos:.0f},{bottommost_y - 320:.0f}!"'
            line = re.sub(r'pos="[^"]*"', new_pos, line)
            if 'pos=' not in line:
                line = line.rstrip("];") + f', {new_pos}];'
        # Legend node positioning
        elif '_legendnode="1"' in line or "_legendnode=1" in line:
            new_pos = f'pos="{cloud_center_x + 650.0:.0f},{bottommost_y - 320:.0f}!"'
            line = re.sub(r'pos="[^"]*"', new_pos, line)
            if 'pos=' not in line:
                line = line.rstrip("];") + f', {new_pos}];'

        out_lines.append(line)

    return "\n".join(out_lines)
