"""Publish already-generated architecture artifacts to Confluence."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from tools.generate_arch_diagram import (
    Limits,
    _static_terraform_graph,
    _terraform_resources_from_files,
)
from tools.smart_confluence import (
    ConfluenceArtifacts,
    analyze_architecture_for_confluence,
    publish_smart_confluence_page,
)


def _first(out_dir: Path, pattern: str) -> Path | None:
    matches = sorted(out_dir.glob(pattern))
    return matches[0] if matches else None


def _base_artifact(out_dir: Path, suffix: str) -> Path | None:
    """Find the deterministic artifact without selecting an AI variant."""
    exact = out_dir / f"architecture-diagram{suffix}"
    if exact.exists():
        return exact
    candidates = [
        path for path in sorted(out_dir.glob(f"architecture-*{suffix}"))
        if "-ai" not in path.stem
    ]
    return candidates[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish generated diagrams to Confluence")
    parser.add_argument("--iac-root", default=".")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--smart", default="true")
    parser.add_argument("--replace", default="true")
    parser.add_argument("--marker", default="")
    parser.add_argument("--unique-filename", default="false")
    parser.add_argument("--backend", default="auto")
    args = parser.parse_args()

    def as_bool(value: str) -> bool:
        return value.lower() in {"1", "true", "yes", "y", "on"}

    url = os.getenv("CONFLUENCE_URL", "")
    user = os.getenv("CONFLUENCE_USER", "")
    token = os.getenv("CONFLUENCE_TOKEN", "")
    missing = [name for name, value in {
        "CONFLUENCE_URL": url,
        "CONFLUENCE_USER": user,
        "CONFLUENCE_TOKEN": token,
        "CONFLUENCE_PAGE_ID": args.page_id,
    }.items() if not value]
    if missing:
        print("Confluence publish requested but configuration is missing: " + ", ".join(missing), flush=True)
        return 1

    out_dir = Path(args.out_dir)
    artifacts = ConfluenceArtifacts(
        png=_base_artifact(out_dir, ".png"),
        jpg=_base_artifact(out_dir, ".jpg"),
        svg=_base_artifact(out_dir, ".svg"),
        drawio=_base_artifact(out_dir, ".drawio"),
        html=_base_artifact(out_dir, ".html"),
        md=_base_artifact(out_dir, ".md"),
        mmd=_base_artifact(out_dir, ".mmd"),
        ai_png=_first(out_dir, "*-ai.png"),
        ai_svg=_first(out_dir, "*-ai.svg"),
        ai_html=_first(out_dir, "*-ai.html"),
        ai_drawio=_first(out_dir, "*-ai.drawio"),
        ai_md=_first(out_dir, "*-ai.md"),
    )
    if as_bool(args.smart):
        iac_root = Path(args.iac_root).resolve()
        iac_files = sorted(iac_root.rglob("*.tf"))
        limits = Limits()
        parsed = _terraform_resources_from_files(iac_files, limits, Path.cwd())
        resource_map, edge_set = _static_terraform_graph(
            iac_files, limits, parsed_inputs=parsed
        )
        resources = [
            {
                "id": resource_id,
                "type": resource_id.split(".", 1)[0],
                "name": resource_id.split(".", 1)[1] if "." in resource_id else resource_id,
                "category": "Other",
            }
            for resource_id in resource_map
        ]
        edges = list(edge_set)
        report = analyze_architecture_for_confluence(
            resources=resources,
            edges=edges,
            png_path=artifacts.ai_png or artifacts.png,
            backend=args.backend,
        )
        published = publish_smart_confluence_page(
            confluence_url=url,
            confluence_user=user,
            confluence_token=token,
            page_id=args.page_id,
            report=report,
            artifacts=artifacts,
            resources=resources,
            full_page=as_bool(args.replace),
            debug=True,
        )
    else:
        from tools.generate_arch_diagram import _publish_to_confluence

        image = artifacts.png or artifacts.svg or artifacts.jpg
        published = bool(image) and _publish_to_confluence(
            url, user, token, args.page_id, image,
            drawio_path=artifacts.drawio,
            replace=as_bool(args.replace),
            image_marker=args.marker or None,
            debug=True,
            unique_filename=as_bool(args.unique_filename),
        )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())