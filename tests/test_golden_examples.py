from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.generate_arch_diagram import Limits, _static_terraform_mermaid


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_golden_mermaid_matches_example_terraform() -> None:
    repo = _repo_root()
    tf = repo / "examples/terraform/aws-basic/main.tf"
    golden = (repo / "tests/golden/aws-basic.mmd").read_text(encoding="utf-8").strip()

    mermaid, _summary, _assumptions = _static_terraform_mermaid([tf], "LR", Limits())
    assert mermaid.strip() == golden


def test_cli_generates_expected_mermaid_file(tmp_path: Path) -> None:
    repo = _repo_root()
    tf = repo / "examples/terraform/aws-basic/main.tf"

    out_md = tmp_path / "architecture-diagram.md"
    out_mmd = tmp_path / "architecture-diagram.mmd"
    out_png = tmp_path / "architecture-diagram.png"
    out_svg = tmp_path / "architecture-diagram.svg"

    result = subprocess.run(
        [
            sys.executable,
            "tools/generate_arch_diagram.py",
            "--changed-files",
            str(tf),
            "--out-md",
            str(out_md),
            "--out-mmd",
            str(out_mmd),
            "--out-png",
            str(out_png),
            "--out-svg",
            str(out_svg),
        ],
        cwd=str(repo),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert out_md.exists()
    assert "<!-- auto-arch-diagram -->" in out_md.read_text(encoding="utf-8")

    golden = (repo / "tests/golden/aws-basic.mmd").read_text(encoding="utf-8").strip()
    assert out_mmd.exists()
    assert out_mmd.read_text(encoding="utf-8").strip() == golden
