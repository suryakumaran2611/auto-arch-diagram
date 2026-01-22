#!/usr/bin/env python3
"""
SVG to Draw.io XML Converter

Converts Graphviz-generated SVG architecture diagrams into editable Draw.io XML format.
Preserves node positions, edge waypoints, and enables drag-and-drop editing in Draw.io.

Features:
- Y-axis flipping (Graphviz uses bottom-up, Draw.io uses top-down)
- Native Draw.io/AWS icon mapping via mxgraph.aws4.* shapes
- Smart label positioning (icons at bottom, containers at top-left)
- Orthogonal edge routing for professional cloud diagrams
- Waypoint preservation from original layout

Usage:
    python tools/svg_to_drawio.py input.svg -o output.drawio.xml
    python tools/svg_to_drawio.py input.svg --preview
"""

import argparse
import re
import sys
import uuid
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from xml.etree import ElementTree as ET


# Native Draw.io/AWS icon mappings for professional looking diagrams
ICON_MAPPINGS = {
    # AWS Core Infrastructure
    "vpc": {
        "style": "shape=mxgraph.aws4.vpc;fillColor=none;strokeColor=#248814;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=30;spacingTop=10;",
    },
    "subnet": {
        "style": "shape=mxgraph.aws4.subnet;fillColor=none;strokeColor=#00A4A6;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=5;",
    },
    "availability zone": {
        "style": "shape=mxgraph.aws4.availability_zone;fillColor=none;strokeColor=#248814;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=5;",
    },
    "region": {
        "style": "shape=mxgraph.aws4.region;fillColor=none;strokeColor=#248814;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=5;",
    },
    "aws cloud": {
        "style": "shape=mxgraph.aws4.aws_cloud;fillColor=none;strokeColor=#248814;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=5;",
    },
    # Compute
    "ec2": {
        "style": "shape=mxgraph.aws4.ec2;fillColor=#F58534;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "lambda": {
        "style": "shape=mxgraph.aws4.lambda;fillColor=#D05C28;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "elastic beanstalk": {
        "style": "shape=mxgraph.aws4.elastic_beanstalk;fillColor=#F58534;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "ecs": {
        "style": "shape=mxgraph.aws4.ecs;fillColor=#F58534;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "eks": {
        "style": "shape=mxgraph.aws4.eks;fillColor=#F58534;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Storage
    "s3": {
        "style": "shape=mxgraph.aws4.s3;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "efs": {
        "style": "shape=mxgraph.aws4.efs;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "fsx": {
        "style": "shape=mxgraph.aws4.fsx;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Database
    "rds": {
        "style": "shape=mxgraph.aws4.rds;fillColor=#3334B9;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "dynamodb": {
        "style": "shape=mxgraph.aws4.dynamodb;fillColor=#3334B9;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "aurora": {
        "style": "shape=mxgraph.aws4.aurora;fillColor=#3334B9;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "elasticache": {
        "style": "shape=mxgraph.aws4.elasticache;fillColor=#3334B9;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Networking
    "internet gateway": {
        "style": "shape=mxgraph.aws4.internet_gateway;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "nat gateway": {
        "style": "shape=mxgraph.aws4.nat_gateway;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "vpc endpoint": {
        "style": "shape=mxgraph.aws4.vpc_endpoint;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "api gateway": {
        "style": "shape=mxgraph.aws4.api_gateway;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "alb": {
        "style": "shape=mxgraph.aws4.alb;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "nlb": {
        "style": "shape=mxgraph.aws4.nlb;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "cloudfront": {
        "style": "shape=mxgraph.aws4.cloudfront;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "route53": {
        "style": "shape=mxgraph.aws4.route_53;fillColor=#8C4FFF;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Security
    "security group": {
        "style": "shape=mxgraph.aws4.security_group;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "iam": {
        "style": "shape=mxgraph.aws4.iam;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "kms": {
        "style": "shape=mxgraph.aws4.kms;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "waf": {
        "style": "shape=mxgraph.aws4.waf;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Analytics
    "redshift": {
        "style": "shape=mxgraph.aws4.redshift;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "athena": {
        "style": "shape=mxgraph.aws4.athena;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "emr": {
        "style": "shape=mxgraph.aws4.emr;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "glue": {
        "style": "shape=mxgraph.aws4.glue;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "kinesis": {
        "style": "shape=mxgraph.aws4.kinesis;fillColor=#3B48CC;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Integration
    "sqs": {
        "style": "shape=mxgraph.aws4.sqs;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "sns": {
        "style": "shape=mxgraph.aws4.sns;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "mq": {
        "style": "shape=mxgraph.aws4.amazon_mq;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "eventbridge": {
        "style": "shape=mxgraph.aws4.amazon_eventbridge;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    "step functions": {
        "style": "shape=mxgraph.aws4.step_functions;fillColor=#DF3312;strokeColor=none;",
        "is_container": False,
        "label_position": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    },
    # Generic containers (fallback)
    "network": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
    "compute": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
    "data": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
    "storage": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
    "security": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
    "other": {
        "style": "shape=rect;fillColor=#cccccc;strokeColor=#aeb6be;",
        "is_container": True,
        "label_position": "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
    },
}

DEFAULT_ICON_STYLE = "shape=rect;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#aeb6be;strokeWidth=1;rounded=0;"
DEFAULT_CONTAINER_STYLE = "shape=rect;whiteSpace=wrap;html=1;fillColor=#ffe7c4;strokeColor=#aeb6be;strokeWidth=2;dashed=0;rounded=0;"


class SVGPathParser:
    """Parses SVG path d attribute into waypoints."""

    COMMAND_PATTERN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
    NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

    @classmethod
    def parse(cls, d: str, y_flip: float = 0) -> List[Tuple[float, float]]:
        """Parse SVG path into list of (x, y) waypoints."""
        if not d:
            return []

        points: List[Tuple[float, float]] = []
        current_x, current_y = 0.0, 0.0

        i = 0
        while i < len(d):
            char = d[i]

            if char.isalpha():
                command = char
                i += 1
                numbers = []
                while i < len(d):
                    num_match = cls.NUMBER_PATTERN.match(d, i)
                    if num_match:
                        numbers.append(float(num_match.group()))
                        i = num_match.end()
                    else:
                        i += 1
            else:
                i += 1
                continue

            if command in ("M", "m"):
                for j in range(0, len(numbers), 2):
                    if j + 1 < len(numbers):
                        dx, dy = numbers[j], numbers[j + 1]
                        if command == "m":
                            current_x += dx
                            current_y += dy
                        else:
                            current_x = dx
                            current_y = dy
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("L", "l"):
                for j in range(0, len(numbers), 2):
                    if j + 1 < len(numbers):
                        dx, dy = numbers[j], numbers[j + 1]
                        if command == "l":
                            current_x += dx
                            current_y += dy
                        else:
                            current_x = dx
                            current_y = dy
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("H", "h"):
                for x in numbers:
                    if command == "h":
                        current_x += x
                    else:
                        current_x = x
                    if y_flip > 0:
                        current_y = y_flip - current_y
                    points.append((current_x, current_y))

            elif command in ("V", "v"):
                for y in numbers:
                    if command == "v":
                        current_y += y
                    else:
                        current_y = y
                    if y_flip > 0:
                        current_y = y_flip - current_y
                    points.append((current_x, current_y))

            elif command in ("C", "c"):
                for j in range(0, len(numbers), 6):
                    if j + 5 < len(numbers):
                        x1, y1, x2, y2, end_x, end_y = numbers[j : j + 6]
                        if command == "c":
                            current_x += end_x
                            current_y += end_y
                        else:
                            current_x = end_x
                            current_y = end_y
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("S", "s"):
                for j in range(0, len(numbers), 4):
                    if j + 3 < len(numbers):
                        x2, y2, end_x, end_y = numbers[j : j + 4]
                        if command == "s":
                            current_x += end_x
                            current_y += end_y
                        else:
                            current_x = end_x
                            current_y = end_y
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("Q", "q"):
                for j in range(0, len(numbers), 4):
                    if j + 3 < len(numbers):
                        end_x, end_y = numbers[j], numbers[j + 1]
                        if command == "q":
                            current_x += end_x
                            current_y += end_y
                        else:
                            current_x = end_x
                            current_y = end_y
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("T", "t"):
                for j in range(0, len(numbers), 2):
                    if j + 1 < len(numbers):
                        end_x, end_y = numbers[j], numbers[j + 1]
                        if command == "t":
                            current_x += end_x
                            current_y += end_y
                        else:
                            current_x = end_x
                            current_y = end_y
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("A", "a"):
                for j in range(0, len(numbers), 7):
                    if j + 6 < len(numbers):
                        _, _, _, _, _, end_x, end_y = numbers[j : j + 7]
                        if command == "a":
                            current_x += end_x
                            current_y += end_y
                        else:
                            current_x = end_x
                            current_y = end_y
                        if y_flip > 0:
                            current_y = y_flip - current_y
                        points.append((current_x, current_y))

            elif command in ("Z", "z"):
                if points:
                    first_point = points[0]
                    current_x, current_y = first_point
                    points.append((current_x, current_y))

        return points

    @classmethod
    def get_bounds(cls, d: str) -> Tuple[float, float, float, float]:
        """Extract bounding box from path d attribute without Y flipping."""
        if not d:
            return (0, 0, 0, 0)

        all_coords = []
        tokens = cls.COMMAND_PATTERN.split(d)

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            numbers = [float(n) for n in cls.NUMBER_PATTERN.findall(token)]
            if not numbers:
                continue

            for i in range(0, len(numbers) - 1, 2):
                if i + 1 < len(numbers):
                    all_coords.append((numbers[i], numbers[i + 1]))

        if not all_coords:
            return (0, 0, 0, 0)

        xs = [p[0] for p in all_coords]
        ys = [p[1] for p in all_coords]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        if max_x <= min_x:
            max_x = min_x + 50
        if max_y <= min_y:
            max_y = min_y + 50

        return (min_x, min_y, max_x, max_y)


class SVGToDrawioConverter:
    """Converts Graphviz SVG to Draw.io editable XML."""

    SVG_NS = "http://www.w3.org/2000/svg"

    def __init__(self, svg_path: str):
        self.svg_path = Path(svg_path)
        self.svg_text = self.svg_path.read_text(encoding="utf-8")
        self.tree = ET.fromstring(self.svg_text)
        self.viewbox_height = self._get_viewbox_height()
        self.node_map: Dict[str, Dict[str, Any]] = {}

    def _get_viewbox_height(self) -> float:
        """Extract viewBox height for Y-axis flipping."""
        viewbox = self.tree.get("viewBox", "0 0 0 0")
        parts = viewbox.split()
        if len(parts) >= 4:
            return float(parts[3])
        return 0.0

    def _hex_to_drawio_color(
        self, color: Optional[str], default: str = "#aeb6be"
    ) -> str:
        """Convert SVG color to Draw.io format."""
        if not color:
            return default
        if color.startswith("#") and len(color) == 7:
            return color
        if color.startswith("#") and len(color) == 4:
            return "#" + "".join(c * 2 for c in color[1:])
        return default

    def _extract_title(self, element: ET.Element) -> Optional[str]:
        """Extract text content from title element."""
        title_elem = element.find(f".//{{{self.SVG_NS}}}title")
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return None

    def _parse_edge_title(self, title: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse edge title to extract source and target IDs."""
        if "->" in title:
            parts = title.split("->")
            return parts[0].strip(), parts[1].strip()
        return None, None

    def _get_path_bounds(self, d: str) -> Tuple[float, float, float, float]:
        """Get bounding box from path data."""
        return SVGPathParser.get_bounds(d)

    def _flip_y(self, y: float) -> float:
        """Flip Y coordinate from Graphviz (bottom-up) to Draw.io (top-down)."""
        return self.viewbox_height - y

    def _create_drawio_file(self) -> ET.Element:
        """Create the root Draw.io XML structure."""
        mxfile = ET.Element(
            "mxfile", {"host": "Electron", "version": "26.0.0", "type": "device"}
        )
        diagram = ET.SubElement(
            mxfile, "diagram", {"id": str(uuid.uuid4()), "name": "Architecture"}
        )
        mx_model = ET.SubElement(
            diagram,
            "mxGraphModel",
            {
                "dx": "1422",
                "dy": "794",
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "0",
                "pageScale": "1",
                "math": "0",
                "shadow": "0",
            },
        )
        return mxfile

    def _get_icon_style(self, label: str, is_cluster: bool = False) -> Tuple[str, bool]:
        """Determine the appropriate Draw.io style based on label."""
        label_lower = label.lower()

        for key, mapping in ICON_MAPPINGS.items():
            if key in label_lower:
                style = mapping["style"] + mapping["label_position"]
                return style, mapping["is_container"]

        if is_cluster:
            return (
                DEFAULT_CONTAINER_STYLE
                + "verticalAlign=top;align=left;spacingLeft=20;spacingTop=10;",
                True,
            )

        return (
            DEFAULT_ICON_STYLE
            + "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
            False,
        )

    def _extract_label(self, element: ET.Element) -> str:
        """Extract clean label from SVG element."""
        label_parts = []

        text_elements = element.findall(f".//{{{self.SVG_NS}}}text")
        for text_elem in text_elements:
            if text_elem.text:
                label_parts.append(text_elem.text.strip())

        if label_parts:
            return " ".join(label_parts)

        title = self._extract_title(element)
        if title:
            title_clean = title.replace("cluster_", "").strip()
            if title_clean and not title_clean.startswith("{"):
                return title_clean

        element_id = element.get("id", "")
        if element_id.startswith("clust"):
            return element_id.replace("clust", "Cluster ")
        if element_id.startswith("edge"):
            return ""

        return ""

    def _process_clusters(self, root: ET.Element):
        """Process cluster groups (VPC, Subnet, Network boxes, etc.)."""
        for cluster in self.tree.findall(f".//{{{self.SVG_NS}}}g[@class='cluster']"):
            cluster_id = cluster.get("id")
            if not cluster_id:
                continue

            path = cluster.find(f".//{{{self.SVG_NS}}}path")
            if path is None:
                continue

            d = path.get("d", "")
            if not d:
                continue

            min_x, min_y, max_x, max_y = self._get_path_bounds(d)

            flip_min_y = self._flip_y(max_y)
            flip_max_y = self._flip_y(min_y)

            label = self._extract_label(cluster)
            style, is_container = self._get_icon_style(label, is_cluster=True)

            if is_container:
                style = "swimlane;whiteSpace=wrap;html=1;" + style

            cell = ET.SubElement(
                root,
                "mxCell",
                {
                    "id": cluster_id,
                    "value": label,
                    "style": style,
                    "vertex": "1",
                    "parent": "1",
                },
            )

            ET.SubElement(
                cell,
                "mxGeometry",
                {
                    "x": str(min_x),
                    "y": str(flip_min_y),
                    "width": str(max_x - min_x),
                    "height": str(flip_max_y - flip_min_y),
                    "as": "geometry",
                },
            )

            self.node_map[cluster_id] = {
                "x": min_x,
                "y": flip_min_y,
                "width": max_x - min_x,
                "height": flip_max_y - flip_min_y,
                "is_cluster": True,
            }

    def _process_nodes(self, root: ET.Element):
        """Process node groups (icons like Lambda, S3, etc.)."""
        for node in self.tree.findall(f".//{{{self.SVG_NS}}}g[@class='node']"):
            node_id = node.get("id")
            if not node_id:
                continue

            ellipse = node.find(f".//{{{self.SVG_NS}}}ellipse")
            polygon = node.find(f".//{{{self.SVG_NS}}}polygon")
            path = node.find(f".//{{{self.SVG_NS}}}path")
            image = node.find(f".//{{{self.SVG_NS}}}image")

            shape_element = ellipse or polygon or path
            d = shape_element.get("d", "") if shape_element is not None else ""

            if d:
                min_x, min_y, max_x, max_y = self._get_path_bounds(d)
            elif image is not None:
                img_x = float(image.get("x", 0))
                img_y = float(image.get("y", 0))
                img_width_str = image.get("width", "58px")
                img_height_str = image.get("height", "58px")
                img_width = float(str(img_width_str).replace("px", ""))
                img_height = float(str(img_height_str).replace("px", ""))
                min_x, min_y = img_x, img_y
                max_x, max_y = img_x + img_width, img_y + img_height
            elif shape_element is not None:
                min_x = float(shape_element.get("cx", 0)) - 25
                min_y = float(shape_element.get("cy", 0)) - 15
                max_x = float(shape_element.get("cx", 0)) + 25
                max_y = float(shape_element.get("cy", 0)) + 15
            else:
                continue

            flip_min_y = self._flip_y(max_y)
            flip_max_y = self._flip_y(min_y)
            width = max_x - min_x
            height = flip_max_y - flip_min_y

            label = self._extract_label(node)
            style, _ = self._get_icon_style(label, is_cluster=False)

            if ellipse is not None and "shape=rect" in style:
                style = "ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#aeb6be;strokeWidth=1;verticalLabelPosition=bottom;verticalAlign=top;align=center;"

            if width <= 0 or height <= 0:
                width, height = 50, 50

            cell = ET.SubElement(
                root,
                "mxCell",
                {
                    "id": node_id,
                    "value": label,
                    "style": style,
                    "vertex": "1",
                    "parent": "1",
                },
            )

            ET.SubElement(
                cell,
                "mxGeometry",
                {
                    "x": str(min_x),
                    "y": str(flip_min_y),
                    "width": str(width),
                    "height": str(height),
                    "as": "geometry",
                },
            )

            self.node_map[node_id] = {
                "x": min_x,
                "y": flip_min_y,
                "width": width,
                "height": height,
                "is_cluster": False,
            }

    def _process_edges(self, root: ET.Element):
        """Process edge groups (arrows between resources)."""
        for edge in self.tree.findall(f".//{{{self.SVG_NS}}}g[@class='edge']"):
            edge_id = edge.get("id")
            if not edge_id:
                continue

            path = edge.find(f".//{{{self.SVG_NS}}}path")
            if path is None:
                continue

            d = path.get("d", "")
            if not d:
                continue

            waypoints = SVGPathParser.parse(d, self.viewbox_height)

            if len(waypoints) < 2:
                continue

            edge_title = self._extract_title(edge)
            source_id, target_id = (
                self._parse_edge_title(edge_title) if edge_title else (None, None)
            )

            stroke = path.get("stroke", "#8d96a7")
            stroke_width = path.get("stroke-width", "1")
            dasharray = path.get("stroke-dasharray", "")

            style_parts = [
                "edgeStyle=orthogonalEdgeStyle",
                "rounded=1",
                "orthogonalLoop=1",
                "jettySize=auto",
                "html=1",
                f"strokeColor={self._hex_to_drawio_color(stroke)}",
                f"strokeWidth={stroke_width}",
            ]

            if dasharray:
                style_parts.append("dashed=1")

            style = ";".join(style_parts) + ";"

            edge_cell = ET.SubElement(
                root,
                "mxCell",
                {"id": edge_id, "style": style, "edge": "1", "parent": "1"},
            )

            if source_id and source_id in self.node_map:
                edge_cell.set("source", source_id)

            if target_id and target_id in self.node_map:
                edge_cell.set("target", target_id)

            geometry = ET.SubElement(
                edge_cell, "mxGeometry", {"as": "geometry", "relative": "1"}
            )

            if len(waypoints) > 2:
                points_array = ET.SubElement(geometry, "Array", {"as": "points"})
                for wx, wy in waypoints[1:-1]:
                    ET.SubElement(points_array, "mxPoint", {"x": str(wx), "y": str(wy)})

    def convert(self) -> str:
        """Convert SVG to Draw.io XML and return as string."""
        mxfile = self._create_drawio_file()

        diagram = mxfile.find("diagram")
        if diagram is None:
            raise ValueError("Failed to create diagram element")

        mx_model = diagram.find("mxGraphModel")
        if mx_model is None:
            raise ValueError("Failed to create mxGraphModel element")

        root = ET.SubElement(mx_model, "root")

        ET.SubElement(root, "mxCell", {"id": "0"})

        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

        self._process_clusters(root)
        self._process_nodes(root)
        self._process_edges(root)

        ET.indent(mxfile, space="  ", level=0)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
            mxfile, encoding="unicode"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Convert Graphviz SVG to editable Draw.io XML format"
    )
    parser.add_argument("input", help="Input SVG file path")
    parser.add_argument("-o", "--output", help="Output Draw.io XML file path")
    parser.add_argument(
        "--preview", action="store_true", help="Preview output to stdout"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show conversion statistics"
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        converter = SVGToDrawioConverter(args.input)
        output_xml = converter.convert()

        if args.preview:
            print(output_xml)
        elif args.output:
            Path(args.output).write_text(output_xml, encoding="utf-8")
            print(f"Converted: {args.input} -> {args.output}")
            if args.stats:
                print(f"  Nodes: {len(converter.node_map)}")
                edge_count = len(
                    converter.tree.findall(f".//{{{converter.SVG_NS}}}g[@class='edge']")
                )
                print(f"  Edges: {edge_count}")
        else:
            print(output_xml)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
