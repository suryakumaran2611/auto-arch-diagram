import pytest
from pathlib import Path
from tools.generate_arch_diagram import _static_cloudformation_mermaid, Limits

def test_cloudformation_example_diagram(tmp_path):
    # Copy example template to temp dir
    src = Path("examples/serverless-website/aws/cloudformation/template.yaml")
    dst = tmp_path / "template.yaml"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    mermaid, summary, assumptions = _static_cloudformation_mermaid([dst], "LR", Limits())
    assert mermaid.startswith("flowchart LR")
    assert "SiteBucket" in mermaid
    assert "WafAcl" in mermaid
    assert "CloudFront" in mermaid or "WAFv2" in mermaid
    assert summary
    assert assumptions
