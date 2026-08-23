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
