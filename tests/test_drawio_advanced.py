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
    }
    edges = {("aws_vpc.main", "aws_instance.web")}
    out_file = tmp_path / "diagram.drawio"

    res = export_drawio(
        resources,
        edges,
        out_file,
        title="Production Web App",
        render=RenderConfig(),
    )

    assert out_file.exists()
    assert res["nodes"] == 2
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
