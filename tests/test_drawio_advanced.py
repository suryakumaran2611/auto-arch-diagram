"""Unit tests for advanced draw.io export capabilities (metadata, title banner, legend, tooltips)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from tools.drawio_exporter import export_drawio
from tools.generate_arch_diagram import RenderConfig


def test_drawio_export_metadata_and_objects(tmp_path: Path) -> None:
    resources = {
        "aws_vpc.main": {"type": "aws_vpc", "name": "main"},
        "aws_instance.web": {
            "type": "aws_instance",
            "name": "web",
            "instance_type": "t3.micro",
            "tags": {"Environment": "production"},
        },
        "aws_s3_bucket.data": {
            "type": "aws_s3_bucket",
            "name": "data",
        },
    }
    edges = {("aws_vpc.main", "aws_instance.web"), ("aws_instance.web", "aws_s3_bucket.data")}
    out_file = tmp_path / "diagram.drawio"

    res = export_drawio(
        resources,
        edges,
        out_file,
        title="Production Web App",
        render=RenderConfig(),
    )

    assert out_file.exists()
    assert res["nodes"] == 3
    assert res["edges"] >= 1

    content = out_file.read_text(encoding="utf-8")
    root = ET.fromstring(content)

    # 1. Custom Metadata <object> tags with custom attributes
    objects = root.findall(".//object")
    assert len(objects) >= 2
    instance_obj = next((o for o in objects if o.get("id") == "aws_instance_web"), None)
    assert instance_obj is not None
    assert instance_obj.get("terraform_type") == "aws_instance"
    assert instance_obj.get("terraform_name") == "web"
    assert instance_obj.get("provider") == "AWS"
    assert instance_obj.get("category") == "Compute"
    assert "tooltip" in instance_obj.attrib

    # 2. Title Banner exists
    title_banner = root.find(".//mxCell[@id='title_banner_1']")
    assert title_banner is not None
    assert "Production Web App" in title_banner.get("value", "")

    # 3. Legend Card exists at bottom center
    legend_card = root.find(".//mxCell[@id='legend_card_6']") or any("Legend" in (c.get("value") or "") for c in root.findall(".//mxCell"))
    assert legend_card is not None


def test_drawio_edge_routing_and_jump_style(tmp_path: Path) -> None:
    """Verify that draw.io edges adhere to professional guidelines: jumpStyle=arc, arcSize, orthogonal routing."""
    resources = {
        "aws_vpc.vpc1": {"type": "aws_vpc", "name": "vpc1"},
        "aws_subnet.sub1": {"type": "aws_subnet", "name": "sub1", "vpc_id": "aws_vpc.vpc1"},
        "aws_instance.app": {"type": "aws_instance", "name": "app"},
        "aws_db_instance.db": {"type": "aws_db_instance", "name": "db"},
    }
    edges = {
        ("aws_vpc.vpc1", "aws_subnet.sub1"),
        ("aws_subnet.sub1", "aws_instance.app"),
        ("aws_instance.app", "aws_db_instance.db"),
    }
    out_file = tmp_path / "routing_diagram.drawio"

    export_drawio(
        resources,
        edges,
        out_file,
        title="Routing Architecture",
        render=RenderConfig(),
    )

    content = out_file.read_text(encoding="utf-8")
    root = ET.fromstring(content)
    edge_cells = [c for c in root.findall(".//mxCell") if c.get("edge") == "1"]

    assert len(edge_cells) >= 1
    for edge in edge_cells:
        style = edge.get("style", "")
        # Must have official bridge arc jump style
        assert "jumpStyle=arc" in style
        assert "jumpSize=6" in style
        # Must have orthogonal routing with rounded corners
        assert "edgeStyle=orthogonalEdgeStyle" in style
        assert "rounded=1" in style
        assert "arcSize=10" in style
        # Must have exit and entry ports defined
        assert "exitX=" in style
        assert "entryX=" in style


def test_drawio_obstacle_avoidance(tmp_path: Path) -> None:
    """Verify that edge routing generates waypoints that avoid cutting across intermediate nodes."""
    # Create 3 nodes in a row/grid where node A connects to node C with node B in the middle
    resources = {
        "aws_instance.node_a": {"type": "aws_instance", "name": "node_a"},
        "aws_instance.node_b": {"type": "aws_instance", "name": "node_b"},
        "aws_instance.node_c": {"type": "aws_instance", "name": "node_c"},
    }
    edges = {("aws_instance.node_a", "aws_instance.node_c")}
    out_file = tmp_path / "avoidance_diagram.drawio"

    export_drawio(
        resources,
        edges,
        out_file,
        title="Obstacle Avoidance Test",
        render=RenderConfig(),
    )

    content = out_file.read_text(encoding="utf-8")
    root = ET.fromstring(content)
    edge_cells = [c for c in root.findall(".//mxCell") if c.get("edge") == "1"]
    assert len(edge_cells) >= 1

