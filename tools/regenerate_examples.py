from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python_cmd(repo: Path) -> list[str]:
    # Prefer repo venv if present; fall back to current interpreter.
    venv_py = repo / ".venv" / "bin" / "python"
    if venv_py.exists():
        return [str(venv_py)]
    return [sys.executable]


def _generate_for_example(repo: Path, entry_file: Path) -> None:
    if not entry_file.exists():
        return

    example_dir = entry_file.parent

    # Always regenerate outputs to keep examples consistent with current renderer.
    out_md = example_dir / "architecture-diagram.md"
    out_mmd = example_dir / "architecture-diagram.mmd"
    out_png = example_dir / "architecture-diagram.png"
    out_jpg = example_dir / "architecture-diagram.jpg"
    out_svg = example_dir / "architecture-diagram.svg"

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
    ]

    res = subprocess.run(cmd, cwd=str(repo), env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed generating for {example_dir}:\n{res.stderr}\n{res.stdout}")


def main() -> int:
    repo = _repo_root()
    examples_root = repo / "examples"

    entries: list[Path] = []
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
        print(f"Generating: {entry.parent.relative_to(repo)} (from {entry.name})")
        _generate_for_example(repo, entry)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
