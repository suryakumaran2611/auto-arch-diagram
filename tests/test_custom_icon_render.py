import pytest
from pathlib import Path
from tools.generate_arch_diagram import _render_icon_diagram_from_terraform, RenderConfig
import shutil

def test_custom_icon_render(tmp_path):
    # Example resource with custom icon
    resources = {
        "aws_lambda_function.my_function": {
            "tags": {
                "Name": "my-function",
                "Icon": "custom://datapipeline"
            }
        },
        "aws_sqs_queue.my_queue": {
            "tags": {
                "Name": "my-queue",
                "Icon": "custom://messagequeue"
            }
        },
        "aws_dynamodb_table.my_table": {
            "tags": {
                "Name": "my-table",
                # No Icon tag, should use default
            }
        }
    }
    edges = set()
    out_dir = tmp_path / "test-output"
    out_dir.mkdir(exist_ok=True)
    png_path = out_dir / "custom-icon-diagram.png"
    svg_path = out_dir / "custom-icon-diagram.svg"
    # Render PNG
    _render_icon_diagram_from_terraform(
        resources, edges, out_path=png_path, title="Custom Icon Test", direction="LR", render=RenderConfig()
    )
    # Render SVG
    _render_icon_diagram_from_terraform(
        resources, edges, out_path=svg_path, title="Custom Icon Test", direction="LR", render=RenderConfig()
    )
    # Copy to project test-output for download
    project_out = Path("test-output")
    project_out.mkdir(exist_ok=True)
    shutil.copy2(png_path, project_out / "custom-icon-diagram.png")
    shutil.copy2(svg_path, project_out / "custom-icon-diagram.svg")
    assert png_path.exists() and svg_path.exists()
