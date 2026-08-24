from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python_cmd(repo: Path) -> list[str]:
    # Prefer repo venv if present; fall back to current interpreter.
    # Check for Windows venv first, then Unix
    venv_py_win = repo / ".venv" / "Scripts" / "python.exe"
    venv_py_unix = repo / ".venv" / "bin" / "python"
    if venv_py_win.exists():
        return [str(venv_py_win), "-u"]
    elif venv_py_unix.exists():
        return [str(venv_py_unix), "-u"]
    return [sys.executable, "-u"]


def _generate_for_example(repo: Path, entry_file: Path, *, ai_enhance: bool = False) -> None:
    if not entry_file.exists():
        return

    example_dir = entry_file.parent
    if example_dir.name == "integration_example":
        docs_dir = example_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        out_md = docs_dir / "architecture.md"
        out_mmd = docs_dir / "architecture.mmd"
        out_png = docs_dir / "architecture.png"
        out_jpg = docs_dir / "architecture.jpg"
        out_svg = docs_dir / "architecture.svg"
        out_drawio = docs_dir / "architecture.drawio"
        out_html = docs_dir / "architecture.html"
    else:
        # Always regenerate outputs to keep examples consistent with current renderer.
        out_md = example_dir / "architecture-diagram.md"
        out_mmd = example_dir / "architecture-diagram.mmd"
        out_png = example_dir / "architecture-diagram.png"
        out_jpg = example_dir / "architecture-diagram.jpg"
        out_svg = example_dir / "architecture-diagram.svg"
        out_drawio = example_dir / "architecture-diagram.drawio"
        out_html = example_dir / "architecture-diagram.html"

    env = dict(os.environ)
    # Don't publish into docs/ paths when regenerating examples.
    env["AUTO_ARCH_PUBLISH_ENABLED"] = "false"

    cmd = _python_cmd(repo) + [
        "tools/generate_arch_diagram.py",
        "--changed-files",
        str(entry_file.relative_to(repo)),
        "--out-md",
        str(out_md.relative_to(repo)),
        "--out-mmd",
        str(out_mmd.relative_to(repo)),
        "--out-png",
        str(out_png.relative_to(repo)),
        "--out-jpg",
        str(out_jpg.relative_to(repo)),
        "--out-svg",
        str(out_svg.relative_to(repo)),
        "--out-drawio",
        str(out_drawio.relative_to(repo)),
        "--out-html",
        str(out_html.relative_to(repo)),
    ]
    if ai_enhance:
        cmd.append("--ai-enhance")

    # Stream generator output (progress, [ai-enhance] logs) instead of
    # capturing it - silent capture hid enhancement failures.
    res = subprocess.run(cmd, cwd=str(repo), env=env)  # nosec B603
    if res.returncode != 0:
        raise RuntimeError(f"Failed generating for {example_dir}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Regenerate all example diagrams")
    parser.add_argument(
        "--ai-enhance",
        action="store_true",
        help="Pass --ai-enhance through to the generator for each terraform example",
    )
    args = parser.parse_args()

    repo = _repo_root()
    examples_root = repo / "examples"

    entries: list[Path] = []
    integration_main = repo / "integration_example" / "main.tf"
    if integration_main.exists():
        entries.append(integration_main)

    entries += sorted(examples_root.rglob("main.tf"))
    entries += sorted(examples_root.rglob("main.bicep"))
    entries += sorted(examples_root.rglob("template.yml"))
    entries += sorted(examples_root.rglob("template.yaml"))
    entries += sorted(examples_root.rglob("Pulumi.yaml"))
    entries += sorted(examples_root.rglob("Pulumi.yml"))

    if not entries:
        print("No examples found.")
        return 0

    for entry in entries:
        # Skip CDK examples (not statically parsed).
        if entry.suffix.lower() in {".ts", ".py"} and entry.name.endswith(".cdk.ts"):
            continue
        print(f"Generating: {entry.parent.relative_to(repo)} (from {entry.name})", flush=True)
        _generate_for_example(repo, entry, ai_enhance=args.ai_enhance)

    print("Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
