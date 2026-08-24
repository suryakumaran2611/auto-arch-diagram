"""Tests for self-contained interactive HTML export."""
from __future__ import annotations

from pathlib import Path
from tools.html_exporter import export_interactive_html

SAMPLE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="500" height="400" viewBox="0 0 500 400">
  <g id="node1" class="node">
    <text text-anchor="middle" x="250" y="200">aws_instance.web</text>
  </g>
</svg>"""

SAMPLE_RESOURCES = {
    "aws_instance.web": {
        "type": "aws_instance",
        "name": "web",
        "ami": "ami-12345",
        "instance_type": "t3.micro",
        "tags": {"Environment": "production", "Project": "web-app"},
    }
}


def test_export_interactive_html_embeds_svg_and_metadata(tmp_path: Path) -> None:
    out_html = tmp_path / "diagram.html"
    html_str = export_interactive_html(
        SAMPLE_SVG,
        SAMPLE_RESOURCES,
        title="Test Architecture",
        out_path=out_html,
    )

    assert out_html.exists()
    assert "<svg" in html_str
    assert "aws_instance.web" in html_str
    assert "ami-12345" in html_str
    assert "INTERACTIVE" in html_str
    assert "zoom-controls" in html_str
    # 6 Advanced features verified
    assert "minimap" in html_str
    assert "filter-chip" in html_str
    assert "export-png-btn" in html_str
    assert "export-json-btn" in html_str
    assert "highlightImpactPaths" in html_str
    assert "search-input" in html_str
    # Zero external CDN script tags
    assert "src=\"http" not in html_str
    assert "href=\"http" not in html_str or "xmlns" in html_str


def test_export_interactive_html_generic_iac(tmp_path: Path) -> None:
    out_html = tmp_path / "diagram.html"
    bicep_resources = {
        "siteStorage": {
            "Kind": "StorageAccount",
            "Type": "Microsoft.Storage/storageAccounts",
            "Provider": "azure",
        },
        "cdnProfile": {
            "Kind": "Profile",
            "Type": "Microsoft.Cdn/profiles",
            "Provider": "azure",
        },
    }
    html_str = export_interactive_html(
        SAMPLE_SVG,
        bicep_resources,
        title="Architecture (Bicep)",
        out_path=out_html,
    )
    assert out_html.exists()
    assert "<svg" in html_str
    assert "siteStorage" in html_str
    assert "Architecture (Bicep)" in html_str
    assert "Storage" in html_str


def test_export_interactive_html_security_flows_and_inspector(tmp_path: Path) -> None:
    svg_with_edges = """<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
  <g id="node1" class="node">
    <title>aws_security_group.web_sg</title>
    <text>web_sg</text>
  </g>
  <g id="node2" class="node">
    <title>aws_s3_bucket.data_bucket</title>
    <text>data_bucket</text>
  </g>
  <g id="edge1" class="edge">
    <title>aws_security_group.web_sg->aws_s3_bucket.data_bucket</title>
    <path d="M10,10 L100,100"/>
  </g>
</svg>"""

    resources = {
        "aws_security_group.web_sg": {
            "type": "aws_security_group",
            "name": "web_sg",
            "description": "Allow TLS inbound",
            "vpc_id": "vpc-0123456789",
            "ingress": [{"from_port": 443, "to_port": 443, "protocol": "tcp"}],
            "tags": {"Environment": "prod", "Tier": "Security"},
        },
        "aws_s3_bucket.data_bucket": {
            "type": "aws_s3_bucket",
            "name": "data_bucket",
            "bucket": "company-lake-data",
            "versioning": True,
            "tags": {"Environment": "prod", "Tier": "Storage"},
        },
    }

    edges = [("aws_security_group.web_sg", "aws_s3_bucket.data_bucket")]
    out_html = tmp_path / "security_diagram.html"

    html_str = export_interactive_html(
        svg_with_edges,
        resources,
        title="Secured Cloud Architecture",
        out_path=out_html,
        edges=edges,
    )

    assert out_html.exists()
    # 1. Pre-tagged node data attributes
    assert 'data-resource-id="aws_security_group.web_sg"' in html_str
    assert 'data-category="Security"' in html_str
    assert 'data-resource-id="aws_s3_bucket.data_bucket"' in html_str
    assert 'data-category="Storage"' in html_str

    # 2. Tagged edge data attributes & security flow
    assert 'data-edge-type="security"' in html_str
    assert 'data-source="aws_security_group.web_sg"' in html_str
    assert 'data-target="aws_s3_bucket.data_bucket"' in html_str
    assert "edgeSecurityFlow" in html_str

    # 3. Dynamic category filter chips
    assert "Security (1)" in html_str
    assert "Storage (1)" in html_str

    # 4. Rich inspector specs
    assert "company-lake-data" in html_str
    assert "vpc-0123456789" in html_str
    assert "Blast Radius" in html_str
    assert "focusOnNode" in html_str



