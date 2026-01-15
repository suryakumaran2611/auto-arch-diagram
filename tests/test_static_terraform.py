from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from tools.generate_arch_diagram import Limits
from tools.generate_arch_diagram import _static_terraform_graph
from tools.generate_arch_diagram import _static_terraform_mermaid
from tools.generate_arch_diagram import _render_icon_diagram_from_terraform
from tools.generate_arch_diagram import Diagram
from tools.generate_arch_diagram import RenderConfig


def test_static_terraform_graph_parses_resources_and_edges(tmp_path: Path) -> None:
    tf = tmp_path / "main.tf"
    tf.write_text(
                """resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
    vpc_id     = aws_vpc.main.id
    cidr_block = "10.0.1.0/24"
}
""",
        encoding="utf-8",
    )

    resources, edges = _static_terraform_graph([tf], Limits(max_files=25, max_bytes_per_file=30000))

    assert "aws_vpc.main" in resources
    assert "aws_subnet.public" in resources
    # subnet depends on vpc
    assert ("aws_vpc.main", "aws_subnet.public") in edges


def test_static_terraform_mermaid_contains_flowchart_direction(tmp_path: Path) -> None:
    tf = tmp_path / "main.tf"
    tf.write_text(
                """resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
    vpc_id     = aws_vpc.main.id
    cidr_block = "10.0.1.0/24"
}
""",
        encoding="utf-8",
    )

    mermaid, summary, assumptions = _static_terraform_mermaid([tf], "LR", Limits())
    assert mermaid.startswith("flowchart LR")
    assert "aws_vpc.main" in mermaid
    assert summary
    assert assumptions


@pytest.mark.skipif(Diagram is None, reason="diagrams library not installed")
def test_icon_rendering_produces_png(tmp_path: Path) -> None:
    if shutil.which("dot") is None:
        pytest.skip("Graphviz 'dot' not available")

    tf = tmp_path / "main.tf"
    tf.write_text(
                """resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
    vpc_id     = aws_vpc.main.id
    cidr_block = "10.0.1.0/24"
}
""",
        encoding="utf-8",
    )

    resources, edges = _static_terraform_graph([tf], Limits())
    out_png = tmp_path / "arch.png"

    _render_icon_diagram_from_terraform(
        resources,
        edges,
        out_path=out_png,
        title="Test",
        direction="LR",
        render=RenderConfig(),
    )

    assert out_png.exists()
    assert out_png.stat().st_size > 0
