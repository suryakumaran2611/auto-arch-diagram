from __future__ import annotations


import argparse
import base64
import html
import json
import math
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml
import requests

# Import dynamic cloud service loader

# Ensure tools/ is in sys.path for script/subprocess execution
import sys

repo_root = Path(__file__).resolve().parents[1]
tools_dir = repo_root / "tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))
from cloud_services_util import load_cloud_services

# Import icon path loader
from cloud_icons_util import load_cloud_icons, load_public_cloud_icons

# Layout post-processing, HTML export, and render config loader
from layout_postprocess import run_gvpr_postprocess, python_postprocess_dot
from html_exporter import export_interactive_html
from render_config import load_provider_config

# Import the BulletproofMapper for improved icon mapping
from refined_bulletproof_mapper import RefinedBulletproofMapper as BulletproofMapper

try:
    from openai import OpenAI  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import hcl2  # type: ignore
except Exception:  # pragma: no cover
    hcl2 = None  # type: ignore

try:
    from diagrams import Diagram, Cluster  # type: ignore
except Exception:  # pragma: no cover
    Diagram = None  # type: ignore
    Cluster = None  # type: ignore

# Generic fallbacks are imported lazily via _import_node_class (defined below).
Blank = None
Rack = None
SQL = None

# Global provider mapping
provider_map = {
    "aws": "AWS",
    "azurerm": "Azure", 
    "google": "GCP",
    "oci": "OCI",
    "ibm": "IBM",
}

# Global instance of the BulletproofMapper for improved icon mapping
_ultimate_mapper = None


def _map_to_diagrams_category(
    terraform_resource_type: str, provider: str
) -> Optional[str]:
    """Map Terraform resource type to diagrams category."""
    t = terraform_resource_type.lower()

    # Remove provider prefix
    for pfx in provider_map.keys():
        if t.startswith(f"{pfx}_"):
            t = t[len(pfx) + 1 :]
            break

    # Comprehensive category mappings for ALL AWS services
    category_mappings = {
        "aws": {
            # Compute
            "lambda": "compute",
            "ec2": "compute",
            "instance": "compute",
            "eks": "compute",
            "ecs": "compute",
            "batch": "compute",
            # Storage
            "s3": "storage",
            "ebs": "storage",
            "efs": "storage",
            "fsx": "storage",
            # Network & CDN
            "vpc": "network",
            "subnet": "network",
            "route": "network",
            "gateway": "network",
            "nat": "network",
            "vpn": "network",
            "elb": "network",
            "alb": "network",
            "nlb": "network",
            "cloudfront": "network",
            "cdn": "network",
            "originaccesscontrol": "network",  # CloudFront OAC
            # Database & Analytics
            "rds": "database",
            "dynamodb": "database",
            "aurora": "database",
            "neptune": "database",
            "redshift": "database",
            "glue": "database",
            "athena": "database",
            "elasticache": "database",
            # Integration & Messaging
            "sqs": "integration",
            "sns": "integration",
            "kinesis": "integration",
            "eventbridge": "integration",
            "api": "integration",
            "step": "integration",
            "mq": "integration",
            # Security & Identity
            "iam": "security",
            "kms": "security",
            "secretsmanager": "security",
            "cloudtrail": "security",
            "guardduty": "security",
            "waf": "security",
            "cognitoidentity": "security",
            "cognitouserpool": "security",
            # Management & Monitoring
            "cloudwatch": "management",
            "xray": "management",
            "trustedadvisor": "management",
            "autoscaling": "management",
            "elasticbeanstalk": "management",
            # Additional Services
            "elastictranscoder": "management",
            "elasticmapreduce": "management",
            "datapipeline": "management",
            "emr": "management",
            "batch": "management",
            "elasticache": "database",  # Can be database or management
            "dax": "database",  # DynamoDB Accelerator
        },
        "azure": {
            "virtual_machine": "compute",
            "function_app": "compute",
            "storage_account": "storage",
            "key_vault": "security",
            "sql_database": "database",
            "load_balancer": "network",
        },
        "gcp": {
            "compute_engine": "compute",
            "cloud_functions": "compute",
            "cloud_storage": "storage",
            "cloud_sql": "database",
            "vpc": "network",
        },
    }

    if provider in category_mappings:
        for service, category in category_mappings[provider].items():
            if service in t:
                return category

    return None


def _find_service_class(
    category_mod: Any, terraform_resource_type: str, provider: str
) -> Optional[Any]:
    """Find the appropriate service class in a diagrams category module."""
    t = terraform_resource_type.lower()

    # Remove provider prefix
    for pfx in provider_map.keys():
        if t.startswith(f"{pfx}_"):
            t = t[len(pfx) + 1 :]
            break

    # Common service class mappings
    service_class_mappings = {
        "aws": {
            "lambda": "Lambda",
            "ec2": "EC2",
            "eks": "EKS",
            "ecs": "ECS",
            "rds": "RDS",
            "s3": "SimpleStorageServiceS3",
            "iam": "IAM",
            "vpc": "VPC",
            "cloudwatch": "CloudWatch",
            "sqs": "SQS",
            "sns": "SNS",
        },
        "azure": {
            "virtual_machine": "VirtualMachine",
            "function_app": "FunctionApp",
            "storage_account": "StorageAccount",
        },
        "gcp": {
            "compute_engine": "ComputeEngine",
            "cloud_functions": "CloudFunctions",
            "cloud_storage": "Storage",
            "sql_database": "SQL",
        },
    }

    if provider in service_class_mappings:
        for service, class_name in service_class_mappings[provider].items():
            if service in t:
                if hasattr(category_mod, class_name):
                    return getattr(category_mod, class_name)

    # Try to find by heuristics if no exact match
    if hasattr(category_mod, "__all__"):
        for attr_name in category_mod.__all__:
            attr = getattr(category_mod, attr_name)
            if attr_name.lower() in t or t in attr_name.lower():
                return attr

    return None


Firewall = None
Router = None
Switch = None
Storage = None
Compute = None
LoadBalancer = None


DEFAULT_CONFIG_PATH = ".auto-arch-diagram.yml"
DEFAULT_MODEL = "gpt-4o-mini"
COMMENT_MARKER = "<!-- auto-arch-diagram -->"
DEFAULT_MODE = "static"  # static | ai

# --- Confluence Publishing ---

_CONFLUENCE_TIMEOUT_SECONDS = 30


def _publish_to_confluence(
    confluence_url: str,
    confluence_user: str,
    confluence_token: str,
    page_id: str,
    diagram_path: Path,
    drawio_path: Path | None = None,
    replace: bool = True,
    image_marker: str | None = None,
    debug: bool = False,
    unique_filename: bool = False,
) -> bool:
    """Publish or robustly replace a specific image in a Confluence page via REST API with optional draw.io attachment."""
    def _log(msg: str) -> None:
        if debug:
            print(msg, flush=True)

    def _info(msg: str) -> None:
        print(msg, flush=True)

    if not diagram_path.exists():
        print(f"Confluence publish: diagram file not found: {diagram_path}")
        return False
    _info("Confluence publish: starting")
    _info(f"Confluence publish: url={confluence_url} page_id={page_id}")
    # Get current page content
    api_url = f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage,version"
    auth = (confluence_user, confluence_token)
    _info("Confluence publish: fetching page content")
    resp = requests.get(api_url, auth=auth, timeout=_CONFLUENCE_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        print(f"Confluence publish: failed to fetch page: {resp.text}")
        return False
    page = resp.json()
    version = page["version"]["number"]
    title = page["title"]
    body = page["body"]["storage"]["value"]
    _info(f"Confluence publish: page found title={title!r} version={version}")
    # Prepare new image tag
    ext = diagram_path.suffix.lower()
    mime = (
        "image/png"
        if ext == ".png"
        else "image/svg+xml"
        if ext == ".svg"
        else "image/jpeg"
    )
    base_filename = diagram_path.name
    filename = base_filename
    if unique_filename:
        import hashlib
        from datetime import datetime, timezone

        diagram_bytes = diagram_path.read_bytes()
        digest = hashlib.sha256(diagram_bytes).hexdigest()[:8]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"{diagram_path.stem}-{timestamp}-{digest}{ext}"
        _info(
            "Confluence publish: using unique filename "
            f"base={base_filename} unique={filename}"
        )
    # Add marker as comment for robust replacement
    marker_comment = (
        f"<!-- auto-arch-diagram:{base_filename} -->"
        if image_marker is None
        else image_marker
    )
    _log(f"Confluence publish: marker={marker_comment!r}")
    img_tag = f'{marker_comment}<ac:image><ri:attachment ri:filename="{filename}" /></ac:image>'

    def _upload_attachment(path_to_upload: Path, target_name: str, target_mime: str) -> bool:
        upload_url = f"{confluence_url}/rest/api/content/{page_id}/child/attachment"
        headers = {"X-Atlassian-Token": "no-check"}
        params = {"minorEdit": "true"}
        _info(f"Confluence publish: uploading attachment {target_name}")
        with path_to_upload.open("rb") as f:
            files = {"file": (target_name, f, target_mime)}
            resp = requests.post(
                upload_url,
                auth=auth,
                headers=headers,
                params=params,
                files=files,
                timeout=_CONFLUENCE_TIMEOUT_SECONDS,
            )
        if resp.status_code not in (200, 201):
            print(f"Confluence publish: failed to upload attachment {target_name}: {resp.text}")
            return False
        _info(f"Confluence publish: attachment {target_name} uploaded successfully")
        return True

    if not _upload_attachment(diagram_path, filename, mime):
        return False

    # Also upload draw.io vector diagram if present
    if drawio_path and drawio_path.exists():
        drawio_name = drawio_path.name
        _upload_attachment(drawio_path, drawio_name, "application/xml")

    new_body = body
    replaced = False
    if replace:
        # Try to replace the first image after the marker comment.
        marker_pat = re.escape(marker_comment) + r"[\s\S]*?<ac:image[\s\S]*?</ac:image>"
        new_body, count = re.subn(marker_pat, img_tag, body, count=1)
        _info(f"Confluence publish: marker replace count={count}")
        if count > 0:
            replaced = True
        # If not found, try by filename in <ri:attachment>
        if not replaced:
            filename_pat = (
                rf'<ac:image[\s\S]*?<ri:attachment[^>]*ri:filename="{re.escape(filename)}"'
                r"[\s\S]*?</ac:image>"
            )
            new_body, count = re.subn(filename_pat, img_tag, new_body)
            _info(f"Confluence publish: filename replace count={count}")
            if count > 0:
                replaced = True
        # If still not found, replace first image
        if not replaced:
            new_body, count = re.subn(
                r"<ac:image[\s\S]*?</ac:image>", img_tag, new_body, count=1
            )
            _info(f"Confluence publish: first-image replace count={count}")
            if count > 0:
                replaced = True
        # If nothing replaced, prepend image
        if not replaced:
            _info("Confluence publish: no match found; prepending image")
            new_body = img_tag + new_body
    else:
        new_body = body + "\n" + img_tag
    # Update page
    update_url = f"{confluence_url}/rest/api/content/{page_id}"
    _info("Confluence publish: updating page")
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "body": {"storage": {"value": new_body, "representation": "storage"}},
        "version": {"number": version + 1},
    }
    resp = requests.put(
        update_url, auth=auth, json=payload, timeout=_CONFLUENCE_TIMEOUT_SECONDS
    )
    if resp.status_code not in (200, 201):
        print(f"Confluence publish: failed to update page: {resp.text}")
        return False
    print(
        f"Confluence publish: diagram uploaded to page {page_id} (filename: {filename})"
    )
    _log("Confluence publish: done")
    return True


# Official cloud-provider brand accents used for cluster borders, with
# matching ultra-light tints for fills so everything stays on a white canvas
# (per AWS/Azure/GCP/OCI/IBM architecture design guidelines).
PROVIDER_ACCENT_COLORS: dict[str, str] = {
    "AWS": "#FF9900",  # AWS orange (Squid Ink palette primary)
    "AZURERM": "#0078D4",  # Microsoft Azure blue
    "AZURE": "#0078D4",
    "GOOGLE": "#4285F4",  # Google Blue 500
    "GCP": "#4285F4",
    "OCI": "#C74634",  # Oracle Red
    "IBM": "#0F62FE",  # IBM Blue 60
}
PROVIDER_TINT_COLORS: dict[str, str] = {
    "AWS": "#FFF6E8",
    "AZURERM": "#EAF3FB",
    "AZURE": "#EAF3FB",
    "GOOGLE": "#EDF2FE",
    "GCP": "#EDF2FE",
    "OCI": "#FDF0EE",
    "IBM": "#ECF2FD",
}


def _provider_accent(provider: str) -> str | None:
    """Official brand accent color for a provider name (None if unknown)."""
    return PROVIDER_ACCENT_COLORS.get(provider.strip().upper())


def _provider_tint(provider: str) -> str | None:
    """Ultra-light brand tint fill color for a provider name (None if unknown)."""
    return PROVIDER_TINT_COLORS.get(provider.strip().upper())


@dataclass(frozen=True)
class RenderConfig:
    # "providers" groups primarily by provider on a single clean canvas.
    # "lanes" groups by category lanes.
    layout: str = "providers"  # providers | lanes
    # The order of lanes when layout == "lanes".
    lanes: tuple[str, ...] = (
        "Network",
        "Security",
        "Containers",
        "Compute",
        "Data",
        "Storage",
        "Other",
    )

    # Graph tuning (Graphviz)
    # Set to "auto" for dynamic spacing based on diagram complexity
    # Or use specific values for manual control
    pad: float | str = "auto"
    nodesep: float | str = "auto"
    ranksep: float | str = "auto"
    splines: str = "ortho"
    concentrate: bool = False

    # Advanced layout controls for edge routing
    edge_routing: str = "ortho"  # ortho | spline | polyline | curved
    overlap_removal: str = "prism"  # prism | scalexy | compress | vpsc | ipsep | false

    # Edge styling for different connection types (architecture best practices)
    edge_style_security: str = "dashed"  # Security group / firewall connections
    edge_style_data: str = "bold"  # Data flow connections
    edge_style_dependency: str = "dotted"  # Logical dependencies
    edge_style_network: str = "solid"  # Network connections (default)

    # Cloud provider colors (white backgrounds with colored borders only)
    color_aws: str = "#FFFFFF"  # White background
    color_azure: str = "#FFFFFF"  # White background
    color_gcp: str = "#FFFFFF"  # White background
    color_oci: str = "#FFFFFF"  # White background
    color_ibm: str = "#FFFFFF"  # White background

    # VPC/Network colors (very light subtle backgrounds)
    color_vpc: str = "#F8FCFF"  # Very light blue tint for VPC
    color_public_subnet: str = "#F8FFF8"  # Very light green tint for public
    color_private_subnet: str = "#FFFEF8"  # Very light yellow tint for private
    color_security: str = "#FFF8F8"  # Very light red tint for security

    # Minimum spacing constraints (used when auto-calculating) - compact layout
    min_pad: float = 0.2
    min_nodesep: float = 0.2
    min_ranksep: float = 0.2

    # Complexity multipliers for auto-spacing
    complexity_scale: float = 1.5  # How much to scale spacing based on complexity
    edge_density_scale: float = 1.2  # Additional scaling for high edge density

    # Styling
    background: str = "white"  # white | transparent
    fontname: str = "Open Sans Bold"
    graph_fontsize: int = 12
    node_fontsize: int = 9
    node_width: float = 0.7
    node_height: float = 0.7
    edge_color: str = "#4B5563"
    edge_penwidth: float = 1.3
    edge_arrowsize: float = 0.8

    # Rendering engine and layout pipeline
    render_engine: str = "auto"  # auto | neato | dot
    fontsize: Optional[int] = None
    iconsize: Optional[int] = None
    simplified: bool = False
    expand_badges: bool = False
    no_consolidate: bool = False
    planfile: str = ""
    graphfile: str = ""
    varfiles: tuple[str, ...] = ()
    workspace: str = "default"
    annotate: str = ""
    ai_backend: str = "openrouter"
    ollama_model: str = "llama3"


@dataclass(frozen=True)
class PublishPaths:
    enabled: bool = False
    md: str | None = None
    mmd: str | None = None
    png: str | None = None
    jpg: str | None = None
    svg: str | None = None
    drawio: str | None = None
    html: str | None = None


@dataclass(frozen=True)
class Limits:
    max_files: int = 25
    max_bytes_per_file: int = 30000


def _load_config(
    repo_root: Path,
) -> tuple[str, str, str, Limits, PublishPaths, RenderConfig]:
    config_path = repo_root / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return (
            "LR",
            DEFAULT_MODE,
            DEFAULT_MODEL,
            Limits(),
            PublishPaths(),
            RenderConfig(),
        )

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    direction = (((config.get("diagram") or {}).get("direction")) or "LR").strip()
    mode = (
        (((config.get("generator") or {}).get("mode")) or DEFAULT_MODE).strip().lower()
    )
    model = (((config.get("model") or {}).get("name")) or DEFAULT_MODEL).strip()
    limits_cfg = config.get("limits") or {}
    limits = Limits(
        max_files=int(limits_cfg.get("max_files", 25)),
        max_bytes_per_file=int(limits_cfg.get("max_bytes_per_file", 30000)),
    )

    publish_cfg = config.get("publish") or {}
    publish_paths_cfg = publish_cfg.get("paths") or {}
    publish = PublishPaths(
        enabled=bool(publish_cfg.get("enabled", False)),
        md=publish_paths_cfg.get("md"),
        mmd=publish_paths_cfg.get("mmd"),
        png=publish_paths_cfg.get("png"),
        jpg=publish_paths_cfg.get("jpg"),
        svg=publish_paths_cfg.get("svg"),
        drawio=publish_paths_cfg.get("drawio"),
        html=publish_paths_cfg.get("html"),
    )

    # Optional render overrides (used for PNG/SVG/JPEG icon rendering).
    render_cfg = (config.get("render") or {}) if isinstance(config, dict) else {}
    if not isinstance(render_cfg, dict):
        render_cfg = {}

    node_cfg = render_cfg.get("node") or {}
    if not isinstance(node_cfg, dict):
        node_cfg = {}
    graph_cfg = render_cfg.get("graph") or {}
    if not isinstance(graph_cfg, dict):
        graph_cfg = {}

    lanes = render_cfg.get("lanes")
    if isinstance(lanes, list) and all(isinstance(x, str) for x in lanes):
        lanes_tuple = tuple(x.strip() for x in lanes if x.strip())
    else:
        lanes_tuple = RenderConfig().lanes

    # Helper function to parse spacing values (can be "auto" or numeric)
    def _parse_spacing_value(value, default):
        if isinstance(value, str) and value.strip().lower() == "auto":
            return "auto"
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _parse_float_env(name: str, default: float) -> float:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return float(raw)
        except (ValueError, TypeError):
            return default

    def _parse_str_env(name: str, default: str) -> str:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip() or default

    render = RenderConfig(
        layout=str(render_cfg.get("layout", RenderConfig().layout)).strip().lower(),
        lanes=lanes_tuple,
        pad=_parse_spacing_value(graph_cfg.get("pad"), RenderConfig().pad),
        nodesep=_parse_spacing_value(graph_cfg.get("nodesep"), RenderConfig().nodesep),
        ranksep=_parse_spacing_value(graph_cfg.get("ranksep"), RenderConfig().ranksep),
        splines=str(graph_cfg.get("splines", RenderConfig().splines)).strip(),
        concentrate=bool(graph_cfg.get("concentrate", RenderConfig().concentrate)),
        edge_routing=str(
            graph_cfg.get("edge_routing", RenderConfig().edge_routing)
        ).strip(),
        overlap_removal=str(
            graph_cfg.get("overlap_removal", RenderConfig().overlap_removal)
        ).strip(),
        min_pad=float(graph_cfg.get("min_pad", RenderConfig().min_pad)),
        min_nodesep=float(graph_cfg.get("min_nodesep", RenderConfig().min_nodesep)),
        min_ranksep=float(graph_cfg.get("min_ranksep", RenderConfig().min_ranksep)),
        complexity_scale=float(
            graph_cfg.get("complexity_scale", RenderConfig().complexity_scale)
        ),
        edge_density_scale=float(
            graph_cfg.get("edge_density_scale", RenderConfig().edge_density_scale)
        ),
        background=str(render_cfg.get("background", RenderConfig().background))
        .strip()
        .lower(),
        fontname=str(render_cfg.get("fontname", RenderConfig().fontname)).strip(),
        graph_fontsize=int(
            render_cfg.get("graph_fontsize", RenderConfig().graph_fontsize)
        ),
        node_fontsize=int(node_cfg.get("fontsize", RenderConfig().node_fontsize)),
        node_width=float(node_cfg.get("width", RenderConfig().node_width)),
        node_height=float(node_cfg.get("height", RenderConfig().node_height)),
        edge_color=_parse_str_env(
            "AUTO_ARCH_EDGE_COLOR",
            str(render_cfg.get("edge_color", RenderConfig().edge_color)).strip(),
        ),
        edge_penwidth=float(
            _parse_float_env(
                "AUTO_ARCH_EDGE_PENWIDTH",
                float(render_cfg.get("edge_penwidth", RenderConfig().edge_penwidth)),
            )
        ),
        edge_arrowsize=float(
            _parse_float_env(
                "AUTO_ARCH_EDGE_ARROWSIZE",
                float(
                    render_cfg.get("edge_arrowsize", RenderConfig().edge_arrowsize)
                ),
            )
        ),
    )

    return (direction, mode, model, limits, publish, render)


def _write_bytes_if_changed(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_bytes() == content:
                return False
        except Exception:  # nosec B110
            pass
    path.write_bytes(content)
    return True


def _write_text_if_changed(path: Path, content: str) -> bool:
    return _write_bytes_if_changed(path, content.encode("utf-8"))


# Raster output budgets. 300 DPI on large layouts produced 40-95 MP images
# that are slow to render and too heavy to upload to Confluence.
# Hard caps on dimensions, then a file-size driven shrink loop:
#   <=10 MB absolute max, optimally <=5 MB.
MAX_RASTER_PIXELS = 16_000_000  # ~16 MP dimension cap
MAX_RASTER_DIM = 8_000  # max width/height in px
RASTER_TARGET_BYTES = 5 * 1024 * 1024  # optimal size ceiling
RASTER_MAX_BYTES = 10 * 1024 * 1024  # hard ceiling
RASTER_MIN_LONG_SIDE = 1400  # never shrink below this (keeps labels readable)


def _raster_dpi_for_complexity(node_count: int) -> str:
    """Pick a base DPI that keeps detail crisp without exploding raster sizes."""
    if node_count <= 25:
        return "300"
    if node_count <= 50:
        return "220"
    return "180"


def _downscale_raster_if_needed(
    path: Path,
    max_pixels: int = MAX_RASTER_PIXELS,
    max_dim: int = MAX_RASTER_DIM,
) -> bool:
    """Cap raster dimensions and file size in place; returns True if resized.

    Dimension pass enforces MAX_RASTER_PIXELS/MAX_RASTER_DIM. Then a file-size
    loop downscales toward RASTER_TARGET_BYTES so outputs stay easy to embed
    (e.g. Confluence attachments), stopping at RASTER_MAX_BYTES or when the
    long side reaches RASTER_MIN_LONG_SIDE.
    """
    try:
        if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            return False
        from PIL import Image

        # These are our own generated rasters; we open them solely to shrink
        # them, so disable PIL's DecompressionBomb guard for this workload.
        Image.MAX_IMAGE_PIXELS = None

        def _resize_to(img: Image.Image, new_size: tuple[int, int], is_png: bool) -> None:
            resized = img.resize(new_size, Image.LANCZOS)
            if is_png:
                resized.save(path, format="PNG", optimize=True)
            else:
                rgb_img = Image.new("RGB", new_size, (255, 255, 255))
                rgb_img.paste(resized)
                rgb_img.save(path, format="JPEG", quality=88, subsampling=0)

        changed = False
        is_png = path.suffix.lower() == ".png"

        with Image.open(path) as img:
            width, height = img.size
        if width > max_dim or height > max_dim or width * height > max_pixels:
            scale = min(
                max_dim / max(width, height),
                (max_pixels / (width * height)) ** 0.5,
                1.0,
            )
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            with Image.open(path) as img:
                _resize_to(img, new_size, is_png)
            changed = True

        # File-size pass: iterate downscale toward the optimal budget.
        attempts = 0
        while path.stat().st_size > RASTER_TARGET_BYTES and attempts < 6:
            with Image.open(path) as img:
                width, height = img.size
            long_side = max(width, height)
            if long_side <= RASTER_MIN_LONG_SIDE:
                break  # readability floor reached; accept current size
            factor = 0.85
            new_size = (
                max(1, int(width * factor)),
                max(RASTER_MIN_LONG_SIDE // 2, int(height * factor)),
            )
            if max(new_size) >= long_side:
                break
            with Image.open(path) as img:
                _resize_to(img, new_size, is_png)
            changed = True
            attempts += 1

        if changed:
            print(
                f"[optimize] {path.name} -> "
                f"{Image.open(path).size[0]}x{Image.open(path).size[1]} "
                f"({path.stat().st_size / 1024 / 1024:.2f} MB)"
            )
        return changed
    except Exception as exc:  # nosec B110
        if os.getenv("AUTO_ARCH_DEBUG"):
            print(f"Debug: raster optimization failed for {path}: {exc}")
        return False


def _embed_images_in_svg(svg_path: Path) -> None:
    """Replace xlink:href file references with embedded base64 data URIs.

    This ensures icons render when the SVG is viewed outside the build host.
    Also normalizes SVG dimensions: Graphviz at high DPI emits width/height
    inflated by the DPI factor (e.g. 300 DPI → ×4.17) while viewBox stays in
    original units, and adds a transform="scale(S S)". This normalization
    removes the inflation so 1 user unit = 1 CSS pixel, making the SVG render
    correctly at natural size in browsers and the interactive studio.
    """

    if not svg_path.exists():
        return

    try:
        content = svg_path.read_text(encoding="utf-8")
    except Exception:
        return

    # --- Normalize SVG dimensions (Graphviz high-DPI output) ---
    # Graphviz at high DPI emits width/height inflated by dpi/72 (e.g. ×4.17)
    # and compensates with transform="scale(S S) rotate(R) translate(TX TY)"
    # on <g id="graph0">. The translate is ESSENTIAL (it maps Graphviz's
    # negative-Y layout into the positive-Y viewBox), so we must keep it —
    # only neutralize the DPI scale and divide the translate by it, and set
    # width/height equal to the viewBox so 1 user unit = 1 CSS pixel.
    def _normalize_svg_dimensions(s: str) -> str:
        svg_m = re.search(r"<svg\b[^>]*>", s)
        if not svg_m:
            return s
        tag = svg_m.group(0)
        vb_m = re.search(r'viewBox="([-\d.\s]+)"', tag)
        w_m = re.search(r'\bwidth="([\d.]+)pt"', tag)
        h_m = re.search(r'\bheight="([\d.]+)pt"', tag)
        if not (vb_m and w_m and h_m):
            return s
        parts = vb_m.group(1).split()
        if len(parts) != 4:
            return s
        try:
            vb_w, vb_h = float(parts[2]), float(parts[3])
            w_val, h_val = float(w_m.group(1)), float(h_m.group(1))
        except ValueError:
            return s
        if vb_w <= 0 or vb_h <= 0:
            return s
        k_w, k_h = w_val / vb_w, h_val / vb_h
        if k_w <= 1.05 or abs(k_w - k_h) / max(k_w, k_h) > 0.02:
            return s
        new_tag = re.sub(r'\bwidth="[^"]*"', f'width="{vb_w:.2f}pt"', tag, count=1)
        new_tag = re.sub(r'\bheight="[^"]*"', f'height="{vb_h:.2f}pt"', new_tag, count=1)
        s = s.replace(tag, new_tag, 1)
        g_m = re.search(r'<g id="graph0"[^>]*>', s)
        if not g_m:
            return s
        gtag = g_m.group(0)
        t_m = re.search(
            r'transform="scale\(([\d.]+)[\s,]+[\d.]+\)\s*rotate\(([-\d.]+)\)\s*translate\(([-\d.]+)[\s,]+([-\d.]+)\)"',
            gtag,
        )
        if not t_m:
            return s
        try:
            sc = float(t_m.group(1))
            rot = t_m.group(2)
            tx, ty = float(t_m.group(3)), float(t_m.group(4))
        except ValueError:
            return s
        if sc <= 1.01:
            return s
        new_transform = (
            f'transform="scale(1 1) rotate({rot}) '
            f'translate({tx:.2f} {ty:.2f})"'
        )
        new_gtag = gtag.replace(t_m.group(0), new_transform, 1)
        return s.replace(gtag, new_gtag, 1)

    content = _normalize_svg_dimensions(content)
    # --------------------------------------------------------

    replacement_count = 0

    # Find all xlink:href="..." patterns that point to PNG files.
    def replace_match(m: re.Match[str]) -> str:
        nonlocal replacement_count
        ref = m.group(1)
        # Skip if it's already a data URI or external URL.
        if ref.startswith(("data:", "http:", "https:")):
            return m.group(0)

        img_data = None

        # Strategy 1: Check relative to SVG location
        img_path = svg_path.parent / ref
        if img_path.exists():
            try:
                img_data = img_path.read_bytes()
            except Exception:  # nosec B110
                pass

        # Strategy 2: Try as absolute path directly
        if img_data is None:
            try:
                abs_path = Path(ref)
                if abs_path.exists() and abs_path.is_file():
                    img_data = abs_path.read_bytes()
            except Exception:  # nosec B110
                pass

        # Strategy 3: Extract from site-packages path if it contains 'resources'
        if img_data is None and "resources" in ref:
            try:
                # Look for 'resources/' in the path and extract everything after it
                ref_normalized = ref.replace("\\", "/")
                if "/resources/" in ref_normalized:
                    resource_suffix = ref_normalized.split("/resources/", 1)[1]
                    # Try to find in site-packages
                    for sp in sys.path:
                        sp_path = Path(sp)
                        if sp_path.exists():
                            candidate = sp_path / "resources" / resource_suffix
                            if candidate.exists():
                                img_data = candidate.read_bytes()
                                break
            except Exception as e:
                if os.getenv("AUTO_ARCH_DEBUG"):
                    print(f"Debug: Failed to find icon in site-packages: {e}")

        if img_data is None:
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"Debug: Could not find icon at: {ref}")
            return m.group(0)

        try:
            b64 = base64.b64encode(img_data).decode("ascii")
            # Detect MIME type from extension
            mime = "image/png"
            ref_lower = ref.lower()
            if ref_lower.endswith(".jpg") or ref_lower.endswith(".jpeg"):
                mime = "image/jpeg"
            elif ref_lower.endswith(".svg"):
                mime = "image/svg+xml"
            data_uri = f'xlink:href="data:{mime};base64,{b64}"'
            replacement_count += 1
            return data_uri
        except Exception:
            return m.group(0)

    updated = re.sub(r'xlink:href="([^"]+)"', replace_match, content)
    if updated != content:
        try:
            svg_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"Debug: Failed to write updated SVG: {e}")


def _wrap_into_grid(group_dot: Any, node_ids: list[str], per_row: int = 3, rank_rows: bool = True) -> None:
    """Wrap node_ids into rows of per_row, joined by invisible column edges."""
    if len(node_ids) <= per_row or group_dot is None:
        return
    try:
        from graphviz import Digraph
        rows = [node_ids[i : i + per_row] for i in range(0, len(node_ids), per_row)]
        for row in rows:
            if rank_rows and len(row) > 1:
                rank_sub = Digraph()
                rank_sub.attr(rank="same")
                for nid in row:
                    rank_sub.node(nid)
                group_dot.subgraph(rank_sub)
        for r in range(len(rows) - 1):
            for col in range(min(len(rows[r]), len(rows[r + 1]))):
                group_dot.edge(rows[r][col], rows[r + 1][col], style="invis")
    except Exception:
        pass


def _align_provider_clusters(
    diag_dot: Any,
    provider_anchor_ids: list[str],
    direction: str = "LR",
    max_per_row: int = 2,
) -> None:
    """Align multi-cloud provider clusters into a balanced, professional grid."""
    if len(provider_anchor_ids) <= 1 or diag_dot is None:
        return
    try:
        from graphviz import Digraph

        # If only 2 or 3 providers in LR mode, layout side-by-side on 1 row
        per_row = 3 if (direction == "LR" and len(provider_anchor_ids) <= 3) else max_per_row
        rows = [
            provider_anchor_ids[i : i + per_row]
            for i in range(0, len(provider_anchor_ids), per_row)
        ]

        if direction == "LR":
            # In LR: chain items in the same row with invisible edges
            for row in rows:
                for c in range(len(row) - 1):
                    diag_dot.edge(row[c], row[c + 1], style="invis", weight="10")
            # Connect the first elements of successive rows to stack row 2 under row 1
            for r in range(len(rows) - 1):
                col_limit = min(len(rows[r]), len(rows[r + 1]))
                for c in range(col_limit):
                    diag_dot.edge(rows[r][c], rows[r + 1][c], style="invis", weight="1")
        else:
            # In TB: items in the same row share rank="same"
            for row in rows:
                if len(row) > 1:
                    rank_sub = Digraph()
                    rank_sub.attr(rank="same")
                    for nid in row:
                        rank_sub.node(nid)
                    diag_dot.subgraph(rank_sub)
            # Edge between rows
            for r in range(len(rows) - 1):
                diag_dot.edge(rows[r][0], rows[r + 1][0], style="invis", weight="10")
    except Exception:
        pass


def _handle_git_source(source_url: str) -> tuple[Path, Optional[tempfile.TemporaryDirectory]]:
    """Clone remote Git source repo to temporary directory."""
    if not any(source_url.startswith(pfx) for pfx in ("http://", "https://", "git@", "git://")):
        return Path(source_url), None
    temp_dir = tempfile.TemporaryDirectory()
    repo_part, _, subfolder = source_url.partition("//")
    subprocess.run(["git", "clone", "--depth", "1", repo_part, temp_dir.name], check=True, capture_output=True)
    res_path = Path(temp_dir.name) / subfolder if subfolder else Path(temp_dir.name)
    return res_path, temp_dir


def _parse_terraform_plan_json(
    plan_file: Path, graph_file: Optional[Path] = None
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Parse resources and dependencies directly from terraform show -json plan and terraform graph DOT."""
    all_resources: dict[str, dict[str, Any]] = {}
    module_ref_maps: dict[str, dict[str, str]] = {}
    env_ref_maps: dict[str, dict[str, str]] = {}

    try:
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to parse plan JSON {plan_file}: {exc}")

    def _extract_module_resources(mod_data: dict[str, Any], mod_prefix: str = ""):
        for res in mod_data.get("resources", []):
            r_type = res.get("type", "")
            r_name = res.get("name", "")
            if not r_type or not r_name:
                continue
            full_key = f"{mod_prefix}{r_type}.{r_name}" if mod_prefix else f"{r_type}.{r_name}"
            vals = res.get("values") or {}
            vals["type"] = r_type
            vals["name"] = r_name
            all_resources[full_key] = vals

        for child in mod_data.get("child_modules", []):
            child_name = child.get("address", "").replace("module.", "")
            _extract_module_resources(child, f"module.{child_name}.")

    planned = plan_data.get("planned_values", {}).get("root_module", {})
    if planned:
        _extract_module_resources(planned)

    return all_resources, module_ref_maps, env_ref_maps


def _simplify_architecture_graph(
    all_resources: dict[str, dict[str, Any]], edges: set[tuple[str, str]]
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    """Simplify diagram for high-level executive view by stripping implementation plumbing.

    Only strips pure configuration/attachment resources. Security groups, firewalls,
    EIPs, and ACLs are kept because they define the security posture.
    """
    plumbing_types = {
        "aws_route_table",
        "aws_route_table_association",
        "aws_route",
        "aws_vpc_dhcp_options",
        "aws_vpc_dhcp_options_association",
        "aws_iam_instance_profile",
        "aws_default_route_table",
        "aws_default_network_acl",
        "aws_default_security_group",        # Default override resource (not a real SG)
        # Security group RULES are plumbing — the security group itself is kept
        "aws_security_group_rule",
        "aws_vpc_security_group_egress_rule",
        "aws_vpc_security_group_ingress_rule",
        # NSG rules are plumbing — the NSG itself is kept
        "azurerm_network_security_rule",
        "azurerm_subnet_network_security_group_association",
        "azurerm_subnet_route_table_association",
        # google_compute_route is implementation detail; firewall is kept
        "google_compute_route",
    }
    filtered_resources = {
        k: v
        for k, v in all_resources.items()
        if k.split(".", 1)[0] not in plumbing_types
    }
    filtered_edges = {
        (s, d)
        for s, d in edges
        if s in filtered_resources and d in filtered_resources
    }
    return filtered_resources, filtered_edges


def _apply_flow_annotations(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    annotate_file: Path,
) -> list[dict[str, Any]]:
    """Load user flow annotations from YAML and return flow definitions."""
    if not annotate_file.exists():
        return []
    try:
        data = yaml.safe_load(annotate_file.read_text(encoding="utf-8")) or {}
        return data.get("flows", [])
    except Exception:
        return []


def _render_postprocessed_diagram(
    dot_source: str,
    out_path: Path,
    outformat: str,
    render_engine: str = "auto",
) -> bool:
    """Run 3-stage post-processing (dot -Tdot -> gvpr/python -> neato -n2) to render final diagram."""
    dot_bin = shutil.which("dot")
    neato_bin = shutil.which("neato")

    if render_engine == "dot" or not neato_bin or not dot_bin:
        if dot_bin:
            try:
                subprocess.run(
                    [dot_bin, f"-T{outformat}", "-o", str(out_path)],
                    input=dot_source,
                    text=True,
                    check=True,
                    capture_output=True,
                )
                return True
            except Exception:
                pass
        return False

    try:
        # Stage 1 & 2: Calculate initial geometry via dot -Tdot
        dot_res = subprocess.run(
            [dot_bin, "-Tdot"],
            input=dot_source,
            text=True,
            capture_output=True,
            check=True,
        )
        geom_dot = dot_res.stdout

        # Stage 3: Geometry transformation via GVPR / Python
        post_dot = run_gvpr_postprocess(geom_dot)

        # Stage 4: Re-render with neato preserving coordinates (neato -n2)
        out_flag = f"-T{outformat}"
        subprocess.run(
            [neato_bin, "-n2", out_flag, "-o", str(out_path)],
            input=post_dot,
            text=True,
            check=True,
            capture_output=True,
        )
        return True
    except Exception as exc:
        _debug(f"[DEBUG] 3-stage postprocess failed ({exc}), falling back to dot.")
        if dot_bin:
            try:
                subprocess.run(
                    [dot_bin, f"-T{outformat}", "-o", str(out_path)],
                    input=dot_source,
                    text=True,
                    check=True,
                    capture_output=True,
                )
                return True
            except Exception:
                pass
        return False


@dataclass
class DiagramComplexity:
    """Metrics for analyzing diagram complexity and calculating optimal spacing."""

    node_count: int
    edge_count: int
    cluster_count: int
    max_cluster_depth: int
    avg_edges_per_node: float
    max_label_length: int
    provider_count: int

    def calculate_spacing_multiplier(self) -> dict[str, float]:
        """Calculate dynamic spacing multipliers based on complexity metrics."""

        # Base complexity score (0-1 scale)
        node_complexity = min(self.node_count / 50.0, 1.0)  # 50+ nodes = max complexity
        edge_density = min(
            self.avg_edges_per_node / 4.0, 1.0
        )  # 4+ edges/node = high density
        cluster_complexity = min(
            self.cluster_count / 10.0, 1.0
        )  # 10+ clusters = complex
        depth_complexity = min(
            self.max_cluster_depth / 3.0, 1.0
        )  # 3+ levels = deep nesting
        label_complexity = min(
            self.max_label_length / 40.0, 1.0
        )  # 40+ chars = long labels
        provider_diversity = min(
            self.provider_count / 3.0, 1.0
        )  # 3+ providers = diverse

        # Weighted average of complexity factors
        overall_complexity = (
            node_complexity * 0.25
            + edge_density * 0.25
            + cluster_complexity * 0.15
            + depth_complexity * 0.15
            + label_complexity * 0.10
            + provider_diversity * 0.10
        )

        # Calculate multipliers (1.0 = minimum, increases with complexity)
        # Use exponential scaling for better distribution
        pad_multiplier = 1.0 + (overall_complexity**0.7) * 0.8
        nodesep_multiplier = 1.0 + (node_complexity + edge_density) * 0.6
        ranksep_multiplier = 1.0 + (depth_complexity + cluster_complexity) * 0.8

        # Extra boost for high edge density to prevent overlaps
        if edge_density > 0.7:
            nodesep_multiplier *= 1.3
            ranksep_multiplier *= 1.2

        # Extra boost for deep nesting
        if self.max_cluster_depth > 2:
            ranksep_multiplier *= 1.4

        return {
            "pad": pad_multiplier,
            "nodesep": nodesep_multiplier,
            "ranksep": ranksep_multiplier,
        }


def _analyze_diagram_complexity(
    resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    grouped_data: dict[str, dict[str, list[str]]],
) -> DiagramComplexity:
    """Analyze infrastructure diagram to determine complexity metrics."""

    node_count = len(resources)
    edge_count = len(edges)

    # Count clusters and determine max depth
    cluster_count = 0
    max_depth = 0
    for outer_key, inner_dict in grouped_data.items():
        if inner_dict:
            cluster_count += len(inner_dict)
            # Each provider within a lane creates nested clusters
            for inner_key, resource_list in inner_dict.items():
                if resource_list:
                    current_depth = 2  # lane + provider
                    max_depth = max(max_depth, current_depth)

    # Calculate edge density
    avg_edges = edge_count / max(node_count, 1)

    # Find longest label
    max_label_len = 0
    for res_name in resources.keys():
        max_label_len = max(max_label_len, len(res_name))

    # Count unique providers
    providers = set()
    for res_name in resources.keys():
        r_type = res_name.split(".", 1)[0]
        provider = _guess_provider(r_type)
        providers.add(provider)

    return DiagramComplexity(
        node_count=node_count,
        edge_count=edge_count,
        cluster_count=cluster_count,
        max_cluster_depth=max_depth,
        avg_edges_per_node=avg_edges,
        max_label_length=max_label_len,
        provider_count=len(providers),
    )


def _determine_optimal_direction(
    complexity: DiagramComplexity,
    grouped_data: dict[str, dict[str, list[str]]],
    layout: str,
) -> str:
    """Intelligently determine the best diagram direction following enterprise cloud architecture standards.

    Professional Cloud Architecture Standards (AWS, Azure, GCP Well-Architected):
    - Horizontal (LR: Left-to-Right) is the universal industry standard for cloud architectures:
      User / Ingress (Left) -> Application / Compute (Center) -> Data / Storage / Persistence (Right).
    - Horizontal layouts optimally utilize widescreen displays (16:9, 16:10), Markdown READMEs,
      and Confluence pages, avoiding tall 'vertical tower' scrolling.
    - Vertical (TB: Top-to-Bottom) is reserved strictly for 1-dimensional single-column DAGs.
    """

    # Count lanes and providers
    lane_count = len(grouped_data)
    provider_count = complexity.provider_count

    # Baseline: Strong preference for horizontal (LR) in modern cloud architecture
    lr_score = 10
    tb_score = 0

    # Factor 1: Multi-cloud / multi-provider architectures require horizontal lane isolation
    if provider_count >= 2:
        lr_score += 6
    elif lane_count >= 2:
        lr_score += 4

    # Factor 2: Multi-tier infrastructure (Ingress -> Compute -> Persistence)
    if complexity.node_count >= 4:
        lr_score += 5

    # Factor 3: Connected service graphs benefit from horizontal dataflow progression
    if complexity.avg_edges_per_node > 0.3:
        lr_score += 4

    # Factor 4: Only penalize LR if it is a strictly linear, single-lane 1D hierarchy
    if lane_count <= 1 and provider_count <= 1 and complexity.node_count <= 3 and complexity.max_cluster_depth >= 4:
        tb_score += 12

    # Decision based on scores (strongly defaults to LR)
    if lr_score >= tb_score:
        direction = "LR"
        reason = "horizontal (industry standard cloud architecture: Ingress -> Compute -> Storage)"
    else:
        direction = "TB"
        reason = "vertical (strictly linear 1D hierarchy)"

    # Debug output
    if os.getenv("AUTO_ARCH_DEBUG"):
        print(f"[Auto Direction] Scores: LR={lr_score}, TB={tb_score}")
        print(f"[Auto Direction] Selected: {direction} ({reason})")
        print(
            f"[Auto Direction] Factors: lanes={lane_count}, providers={provider_count}, "
            f"nodes={complexity.node_count}, depth={complexity.max_cluster_depth}, "
            f"edges/node={complexity.avg_edges_per_node:.1f}"
        )

    return direction


def _calculate_dynamic_spacing(
    complexity: DiagramComplexity,
    render: RenderConfig,
    direction: str,
) -> dict[str, Any]:
    """Calculate optimal spacing parameters based on diagram complexity following professional architecture best practices."""

    multipliers = complexity.calculate_spacing_multiplier()

    # Apply multipliers to base values with compact professional scaling
    # Best practice: conservative scaling for tight, readable diagrams
    pad_value = render.min_pad * multipliers["pad"] * 0.8  # Minimal padding scale
    nodesep_value = (
        render.min_nodesep * multipliers["nodesep"] * 0.7
    )  # Compact node separation
    ranksep_value = (
        render.min_ranksep * multipliers["ranksep"] * 0.7
    )  # Tight rank separation

    # Direction-specific adjustments - compact professional ratios
    if direction in ("LR", "RL"):
        # Horizontal layouts: tight horizontal spacing for compact left-right flow
        nodesep_value *= 1.2
        ranksep_value *= 1.1
    else:
        # Vertical layouts: compact vertical spacing for efficient hierarchy
        ranksep_value *= 1.0
        nodesep_value *= 1.0

    # Additional edge density scaling - prevent crowding in complex diagrams
    if complexity.avg_edges_per_node > 2.5:
        nodesep_value *= 1.0  # Reduced from render.edge_density_scale (1.2)
        ranksep_value *= 1.15
        pad_value *= 1.08  # Slight padding increase

    return {
        "pad": round(pad_value, 2),
        "nodesep": round(nodesep_value, 2),
        "ranksep": round(ranksep_value, 2),
    }


def _maybe_publish_outputs(
    repo_root: Path,
    publish: PublishPaths,
    *,
    out_md: Path,
    out_mmd: Path,
    out_png: Path | None,
    out_jpg: Path | None,
    out_svg: Path | None,
    out_drawio: Path | None = None,
    out_html: Path | None = None,
) -> list[str]:
    """Copy generated outputs into user-configured repo paths (for committing in a follow-up PR)."""

    if not publish.enabled:
        return []

    changed: list[str] = []

    def publish_file(src: Path | None, dst_rel: str | None, *, binary: bool) -> None:
        nonlocal changed
        if not dst_rel:
            return
        if src is None:
            return
        dst = (repo_root / dst_rel).resolve()
        if not src.exists():
            return
        data = src.read_bytes() if binary else src.read_text(encoding="utf-8")
        did_change = (
            _write_bytes_if_changed(dst, data)
            if binary
            else _write_text_if_changed(dst, data)
        )
        if did_change:
            changed.append(str(dst.relative_to(repo_root)).replace("\\", "/"))

    publish_file(out_md, publish.md, binary=False)
    publish_file(out_mmd, publish.mmd, binary=False)
    publish_file(out_png, publish.png, binary=True)
    publish_file(out_jpg, publish.jpg, binary=True)
    publish_file(out_svg, publish.svg, binary=False)
    publish_file(out_drawio, publish.drawio, binary=False)
    publish_file(out_html, publish.html, binary=False)

    return changed


def _parse_env_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _safe_node_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "node"
    if cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _walk(obj: Any) -> Iterable[Any]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
        return
    if isinstance(obj, list):
        yield obj
        for v in obj:
            yield from _walk(v)
        return
    yield obj


_TF_REF_RE = re.compile(
    r"(?<![\w-])([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9_]+)*"
)
_TF_INTERP_RE = re.compile(
    r"\$\{\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)(?:\.[^\}]*)?\s*\}"
)


def _extract_tf_resource_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    for item in _walk(value):
        if isinstance(item, str):
            # Terraform interpolation form: ${aws_vpc.main.id}
            for m in _TF_INTERP_RE.finditer(item):
                refs.add(f"{m.group(1)}.{m.group(2)}")
            # Plain references present in parsed HCL strings.
            for m in _TF_REF_RE.finditer(item):
                refs.add(f"{m.group(1)}.{m.group(2)}")
    return refs


def _terraform_resources_from_hcl(
    parsed: dict[str, Any], name_prefix: str = ""
) -> dict[str, dict[str, Any]]:
    resources: dict[str, dict[str, Any]] = {}
    blocks = parsed.get("resource")
    if not blocks:
        return resources

    # python-hcl2 returns resource blocks as a list of dicts.
    for block in blocks:
        if not isinstance(block, dict):
            continue
        for r_type, r_body in block.items():
            if r_type.startswith("null_"):
                continue
            if isinstance(r_body, dict):
                # { "aws_vpc": {"main": {...}} }
                for name, attrs in r_body.items():
                    if isinstance(attrs, dict):
                        resources[f"{r_type}.{name_prefix}{name}"] = attrs
            elif isinstance(r_body, list):
                # Sometimes: { "aws_vpc": [ {"main": {...}} ] }
                for entry in r_body:
                    if not isinstance(entry, dict):
                        continue
                    for name, attrs in entry.items():
                        if isinstance(attrs, dict):
                            resources[f"{r_type}.{name_prefix}{name}"] = attrs
    return resources


def _terraform_modules_from_hcl(parsed: dict[str, Any]) -> list[tuple[str, str]]:
    modules: list[tuple[str, str]] = []
    blocks = parsed.get("module")
    if not blocks:
        return modules

    for block in blocks:
        if not isinstance(block, dict):
            continue
        for name, attrs in block.items():
            module_attrs = attrs
            if isinstance(attrs, list) and attrs:
                module_attrs = attrs[0]
            if not isinstance(module_attrs, dict):
                continue
            source = module_attrs.get("source")
            if isinstance(source, list) and source:
                source = source[0]
            if isinstance(source, str) and source.strip():
                modules.append((name, source.strip()))
    return modules


def _resolve_local_module_dir(
    source: str, base_dir: Path, repo_root: Path
) -> Path | None:
    if not source:
        return None
    if source.startswith("git::") or "://" in source:
        return None

    candidate: Path
    if source.startswith("/"):
        candidate = Path(source).resolve()
    elif source.startswith("./") or source.startswith("../"):
        candidate = (base_dir / source).resolve()
    else:
        return None

    try:
        candidate.relative_to(repo_root)
    except ValueError:
        return None
    if not candidate.is_dir():
        return None
    return candidate


def _module_prefix_for_resource(res_name: str) -> str | None:
    try:
        _rtype, rname = res_name.split(".", 1)
    except ValueError:
        return None
    base_name = rname
    env_prefix = None
    if "__" in rname:
        prefix, rest = rname.split("__", 1)
        if _is_known_env(prefix):
            env_prefix = prefix
            base_name = rest
    if base_name.startswith("module_") and "__" in base_name:
        module_prefix = base_name.split("__", 1)[0] + "__"
        if env_prefix:
            return f"{env_prefix}__{module_prefix}"
        return module_prefix
    return None


_KNOWN_ENV_NAMES = {
    "dev",
    "development",
    "preprod",
    "pre-prod",
    "prod",
    "production",
    "stage",
    "staging",
    "qa",
    "test",
    "uat",
    "sandbox",
    "shared",
}

_ENV_DIR_EXCLUDE = {
    "modules",
    "module",
    "account_config",
    "accounts",
    "artifacts",
    "templates",
    "template",
    "img",
    "images",
    "cloud_formation",
    "config",
    "configs",
}


def _is_known_env(name: str) -> bool:
    return name.strip().lower() in _KNOWN_ENV_NAMES


def _normalize_env_name(name: str | None) -> str | None:
    if not name:
        return None
    return name.strip().lower()


def _format_env_label(name: str) -> str:
    return name.replace("-", " ").title()


def _detect_environment_from_path(path: Path, repo_root: Path) -> str | None:
    try:
        rel = path.relative_to(repo_root)
        parts = rel.parts
    except Exception:
        parts = path.parts

    parts_lower = [p.lower() for p in parts]
    for idx, part in enumerate(parts_lower):
        if part == "terraform" and idx + 1 < len(parts_lower):
            candidate = parts[idx + 1]
            candidate_lower = candidate.lower()
            if _is_known_env(candidate_lower):
                return candidate_lower
            if candidate_lower not in _ENV_DIR_EXCLUDE:
                return candidate_lower

    for part in parts_lower:
        if _is_known_env(part):
            return part
    return None


def _apply_env_prefix_to_res_id(res_id: str, env: str) -> str:
    r_type, name = res_id.split(".", 1)
    return f"{r_type}.{env}__{name}"


def _strip_env_prefix_from_name(name: str) -> str:
    if "__" in name:
        prefix, rest = name.split("__", 1)
        if _is_known_env(prefix):
            return rest
    return name


def _group_resources_by_env(
    resources: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for res, attrs in resources.items():
        env = _normalize_env_name(attrs.get("_auto_arch_env")) if attrs else None
        env_key = env or "shared"
        groups.setdefault(env_key, []).append(res)
    return groups


def _filter_resources_and_edges(
    resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    resource_ids: set[str],
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    filtered_resources = {rid: resources[rid] for rid in resource_ids}
    filtered_edges = {
        (src, dst)
        for (src, dst) in edges
        if src in resource_ids and dst in resource_ids
    }
    return filtered_resources, filtered_edges


def _fallback_chain_edges(resources: dict[str, dict[str, Any]]) -> set[tuple[str, str]]:
    """Create simple chain edges when no explicit refs are found."""
    groups: dict[str, list[str]] = {}
    for res in resources.keys():
        prefix = _module_prefix_for_resource(res) or ""
        groups.setdefault(prefix, []).append(res)

    edges: set[tuple[str, str]] = set()
    for res_list in groups.values():
        ordered = sorted(res_list)
        for src, dst in zip(ordered, ordered[1:]):
            edges.add((src, dst))
    return edges


_HCL2_META_KEYS = {"__is_block__", "__comments__"}


def _strip_wrapping_quotes(value: str) -> str:
    """Remove a single layer of wrapping double quotes (hcl2 v8 style)."""
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _normalize_hcl2_output(obj: Any) -> Any:
    """Normalize python-hcl2 output across major versions.

    hcl2 v7 returns unquoted keys/values; v8 quotes block-label keys
    ('"aws_vpc"'), wraps scalar values in quotes and adds __is_block__ /
    __comments__ metadata. Normalizing to the v7 shape keeps the rest of the
    pipeline identical regardless of the installed hcl2 major.
    """
    if isinstance(obj, dict):
        return {
            _strip_wrapping_quotes(k) if isinstance(k, str) else k: _normalize_hcl2_output(v)
            for k, v in obj.items()
            if k not in _HCL2_META_KEYS
        }
    if isinstance(obj, list):
        return [_normalize_hcl2_output(item) for item in obj]
    if isinstance(obj, str):
        return _strip_wrapping_quotes(obj)
    return obj


def _parse_hcl_text(text: str) -> dict[str, Any]:
    if hcl2 is None:
        raise RuntimeError(
            "Missing dependency python-hcl2. Install it to enable Terraform static diagrams."
        )
    return _normalize_hcl2_output(hcl2.loads(text))


def _terraform_resources_from_files(
    files: list[Path], limits: Limits, repo_root: Path
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    resources: dict[str, dict[str, Any]] = {}
    module_ref_maps: dict[str, dict[str, str]] = {}
    env_ref_maps: dict[str, dict[str, str]] = {}

    envs_in_files = {
        _normalize_env_name(_detect_environment_from_path(f, repo_root))
        for f in files
        if f.suffix in {".tf", ".hcl"}
    }
    envs_in_files.discard(None)
    env_prefix_enabled = len(envs_in_files) > 1

    for f in files:
        if f.suffix not in {".tf", ".hcl"}:
            continue

        env = _normalize_env_name(_detect_environment_from_path(f, repo_root))
        if env_prefix_enabled and env is None:
            env = "shared"

        try:
            text = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
            parsed = _parse_hcl_text(text)
        except Exception:  # nosec B112
            continue

        base_resources = _terraform_resources_from_hcl(parsed)
        for res_id, attrs in base_resources.items():
            final_res_id = (
                _apply_env_prefix_to_res_id(res_id, env)
                if env_prefix_enabled and env
                else res_id
            )
            attrs_copy = dict(attrs)
            attrs_copy["_auto_arch_env"] = env
            attrs_copy["_auto_arch_logical_id"] = res_id
            attrs_copy["_auto_arch_source_file"] = f.as_posix()
            resources[final_res_id] = attrs_copy
            if env_prefix_enabled and env:
                env_ref_maps.setdefault(env, {})[res_id] = final_res_id

        for module_name, source in _terraform_modules_from_hcl(parsed):
            module_dir = _resolve_local_module_dir(source, f.parent, repo_root)
            if module_dir is None:
                continue
            module_prefix = f"module_{module_name}__"
            env_module_prefix = (
                f"{env}__{module_prefix}" if env_prefix_enabled and env else module_prefix
            )
            module_files = sorted(module_dir.glob("*.tf")) + sorted(
                module_dir.glob("*.hcl")
            )
            for module_file in module_files:
                try:
                    text = _read_file_limited(
                        module_file, max_bytes=limits.max_bytes_per_file
                    )
                    parsed_module = _parse_hcl_text(text)
                except Exception:  # nosec B112
                    continue
                base_module_resources = _terraform_resources_from_hcl(parsed_module)
                module_resources = _terraform_resources_from_hcl(
                    parsed_module, name_prefix=env_module_prefix
                )
                ref_map = module_ref_maps.setdefault(env_module_prefix, {})
                for ref in base_module_resources.keys():
                    r_type, r_name = ref.split(".", 1)
                    ref_map[ref] = f"{r_type}.{env_module_prefix}{r_name}"
                for res_id, attrs in module_resources.items():
                    attrs_copy = dict(attrs)
                    attrs_copy["_auto_arch_env"] = env
                    attrs_copy["_auto_arch_logical_id"] = res_id
                    attrs_copy["_auto_arch_source_file"] = module_file.as_posix()
                    resources[res_id] = attrs_copy
                    if env_prefix_enabled and env:
                        env_ref_maps.setdefault(env, {})[res_id] = res_id

    return resources, module_ref_maps, env_ref_maps


def _guess_provider(resource_type: str) -> str:
    # Terraform types are usually like aws_vpc, azurerm_subnet, google_compute_network.
    prefix = resource_type.split("_", 1)[0].lower()
    known = {
        "aws": "AWS",
        "azurerm": "Azure",
        "google": "GCP",
        "oci": "OCI",
        "ibm": "IBM",
    }
    return known.get(prefix, prefix.upper())


def _tf_category(resource_type: str) -> str:
    t = resource_type.lower()

    if any(
        k in t
        for k in [
            "vpc",
            "vnet",
            "vcn",
            "subnet",
            "route",
            "gateway",
            "internet",
            "nat",
            "network",
            "firewall",
            "lb",
            "load_balancer",
        ]
    ):
        return "Network"
    if any(
        k in t
        for k in [
            "security",
            "nsg",
            "security_group",
            "iam",
            "policy",
            "role",
            "key",
            "kms",
        ]
    ):
        return "Security"
    if any(k in t for k in ["eks", "aks", "gke", "kubernetes", "container", "cluster"]):
        return "Containers"
    if any(
        k in t
        for k in [
            "instance",
            "vm",
            "virtual_machine",
            "compute",
            "ec2",
            "app_service",
            "function",
            "lambda",
        ]
    ):
        return "Compute"
    if any(
        k in t
        for k in [
            "db",
            "database",
            "sql",
            "rds",
            "dynamodb",
            "cosmos",
            "redis",
            "elasticache",
        ]
    ):
        return "Data"
    if any(k in t for k in ["bucket", "storage", "objectstorage", "blob", "s3"]):
        return "Storage"
    return "Other"


def _is_vpc_or_network(resource_type: str) -> bool:
    """Get cloud provider logo icon path if available."""
    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"

    provider_lower = provider.lower()

    # Map provider names to icon filenames
    icon_mapping = {
        "aws": "aws/arch_aws_cloud_64@5x.png",
        "azurerm": "azure/00559_icon_service_azure_cloud_shell.png",
        "azure": "azure/00559_icon_service_azure_cloud_shell.png",
        "google": "gcp/cloud.png",
        "gcp": "gcp/cloud.png",
    }

    # Try to find icon
    icon_rel_path = icon_mapping.get(provider_lower)
    if icon_rel_path:
        icon_path = icons_dir / icon_rel_path
        if icon_path.exists():
            return str(icon_path)

    return None


def _get_cluster_color(cluster_name: str, render: RenderConfig) -> str:
    """Get appropriate color for cluster based on its type and cloud provider."""
    name_lower = cluster_name.lower()

    # Cloud provider colors
    if "aws" in name_lower:
        return render.color_aws
    if "azure" in name_lower or "azurerm" in name_lower:
        return render.color_azure
    if "gcp" in name_lower or "google" in name_lower:
        return render.color_gcp
    if "oracle" in name_lower or "oci" in name_lower:
        return render.color_oci
    if "ibm" in name_lower:
        return render.color_ibm

    # Network/VPC colors
    if any(k in name_lower for k in ["vpc", "vnet", "vcn", "network"]):
        return render.color_vpc
    if "public" in name_lower:
        return render.color_public_subnet
    if "private" in name_lower:
        return render.color_private_subnet
    if "security" in name_lower:
        return render.color_security

    # Default subtle color
    return "#F5F5F5"


def _detect_edge_type(
    from_res: str, to_res: str, all_resources: dict[str, dict[str, Any]]
) -> str:
    """Detect the type of connection between two resources for intelligent edge styling.
    Returns: 'security', 'data', 'dependency', or 'network'
    """
    from_type = from_res.split(".", 1)[0].lower()
    to_type = to_res.split(".", 1)[0].lower()

    # Security connections (firewall, security groups, IAM, etc.)
    security_keywords = [
        "security",
        "firewall",
        "iam",
        "kms",
        "key",
        "policy",
        "role",
        "nsg",
        "nacl",
    ]
    if any(k in from_type or k in to_type for k in security_keywords):
        return "security"

    # Data flow connections (databases, storage, queues, streams)
    data_keywords = [
        "db",
        "database",
        "rds",
        "dynamodb",
        "sql",
        "storage",
        "bucket",
        "s3",
        "blob",
        "queue",
        "stream",
        "kinesis",
        "eventgrid",
        "pubsub",
        "cosmos",
        "redis",
    ]
    if any(k in from_type or k in to_type for k in data_keywords):
        return "data"

    # Check for cross-provider or cross-region connections (should be dotted for logical dependency)
    from_provider = _guess_provider(from_type)
    to_provider = _guess_provider(to_type)
    if from_provider != to_provider:
        return "dependency"

    # Default to network connection
    return "network"


def _get_edge_style_attrs(edge_type: str, render: RenderConfig) -> dict[str, str]:
    """Get edge styling attributes based on connection type following architecture best practices."""
    base_attrs = {
        "color": render.edge_color,
        "penwidth": str(render.edge_penwidth),
        "arrowsize": str(render.edge_arrowsize),
    }

    if edge_type == "security":
        # Dashed lines for security boundaries and policies
        base_attrs["style"] = render.edge_style_security
        base_attrs["color"] = "#F44336"  # Red for security
        base_attrs["penwidth"] = str(render.edge_penwidth * 1.2)
        base_attrs["constraint"] = "false"
    elif edge_type == "data":
        # Bold lines for data flow
        base_attrs["style"] = render.edge_style_data
        base_attrs["color"] = "#2196F3"  # Blue for data
        base_attrs["penwidth"] = str(render.edge_penwidth * 1.5)
        base_attrs["constraint"] = "true"
    elif edge_type == "dependency":
        # Dotted lines for logical dependencies (cross-cloud, cross-region)
        base_attrs["style"] = render.edge_style_dependency
        base_attrs["color"] = "#9E9E9E"  # Gray for dependencies
        base_attrs["constraint"] = "false"
    else:  # network
        # Solid lines for network connections (default)
        base_attrs["style"] = render.edge_style_network
        base_attrs["constraint"] = "true"

    return base_attrs


def _is_vpc_or_network(resource_type: str) -> bool:
    """Check if a resource is a VPC/VNet/Network container."""
    t = resource_type.lower()
    tokens = set(t.split("_"))

    # Many Terraform resources contain "vpc" but are not network containers.
    non_container_patterns = (
        "vpc_peering",
        "vpc_endpoint",
        "vpc_security",
        "vpc_dhcp",
        "vpc_ipam",
        "vpc_flow",
        "vpc_block",
        "vpc_access",
    )
    if any(pattern in t for pattern in non_container_patterns):
        return False

    # Explicit network container patterns across providers.
    explicit_container_patterns = (
        "vpc",
        "vnet",
        "vcn",
        "virtual_network",
        "compute_network",
    )
    if any(pattern in t for pattern in explicit_container_patterns):
        return "subnet" not in t and "subnetwork" not in t

    # Generic "network" token can represent a container, but exclude common non-container resources.
    if "network" not in tokens:
        return False
    if "subnet" in tokens or "subnetwork" in tokens:
        return False

    non_container_tokens = {
        "interface",
        "interfaces",
        "acl",
        "firewall",
        "gateway",
        "security",
        "watcher",
        "rule",
        "profile",
        "endpoint",
        "load",
        "balancer",
        "policy",
    }
    return not any(token in tokens for token in non_container_tokens)


def _is_subnet(resource_type: str) -> bool:
    """Check if a resource is a subnet."""
    t = resource_type.lower()
    non_subnet_patterns = (
        "subnet_group",
        "subnetgroup",
        "db_subnet_group",
        "elasticache_subnet_group",
        "subnet_route_table_association",
        "subnet_network_security_group_association",
        "subnet_nat_gateway_attachment",
    )
    if any(pattern in t for pattern in non_subnet_patterns):
        return False
    return "subnet" in t or "subnetwork" in t


def _is_public_subnet(resource_name: str, resource_attrs: dict[str, Any]) -> bool:
    """Detect if a subnet is public based on name or attributes."""
    name_lower = resource_name.lower()
    if "public" in name_lower or "dmz" in name_lower or "external" in name_lower:
        return True
    # Check attributes for public indicators
    if isinstance(resource_attrs, dict):
        map_public_ip = resource_attrs.get("map_public_ip_on_launch")
        if map_public_ip is True or str(map_public_ip).lower() == "true":
            return True
    return False


def _infer_subnet_to_vpc(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    vpcs: dict[str, dict[str, Any]],
    subnets: dict[str, dict[str, Any]],
) -> dict[str, str]:
    subnet_to_vpc: dict[str, str] = {}

    for src, dst in sorted(edges):
        if src in vpcs and dst in subnets:
            subnet_to_vpc[dst] = src
        elif dst in vpcs and src in subnets:
            subnet_to_vpc[src] = dst

    for subnet_name, subnet_attrs in subnets.items():
        if subnet_name in subnet_to_vpc or not isinstance(subnet_attrs, dict):
            continue
        vpc_ref = None
        for key in ["vpc_id", "virtual_network_name", "vcn_id", "network"]:
            if key not in subnet_attrs:
                continue
            refs = _extract_tf_resource_refs(subnet_attrs[key])
            for ref in refs:
                if ref in vpcs:
                    vpc_ref = ref
                    break
            if vpc_ref:
                break
        if vpc_ref:
            subnet_to_vpc[subnet_name] = vpc_ref

    return subnet_to_vpc


def _infer_resource_to_subnets(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    vpcs: dict[str, dict[str, Any]],
    subnets: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    """Infer subnet membership from direct refs and subnet-group indirection."""

    resource_to_subnets: dict[str, set[str]] = {}

    for src, dst in sorted(edges):
        if src in subnets and dst not in vpcs and dst not in subnets:
            resource_to_subnets.setdefault(dst, set()).add(src)
        elif dst in subnets and src not in vpcs and src not in subnets:
            resource_to_subnets.setdefault(src, set()).add(dst)

    for res_name, res_attrs in all_resources.items():
        if res_name in vpcs or res_name in subnets or not isinstance(res_attrs, dict):
            continue
        for key in ["subnet_id", "subnet_ids", "subnet", "subnets", "subnetwork"]:
            if key not in res_attrs:
                continue
            refs = _extract_tf_resource_refs(res_attrs[key])
            for ref in refs:
                if ref in subnets:
                    resource_to_subnets.setdefault(res_name, set()).add(ref)

    changed = True
    while changed:
        changed = False
        for res_name, res_attrs in all_resources.items():
            if res_name in vpcs or res_name in subnets or not isinstance(res_attrs, dict):
                continue
            previous_count = len(resource_to_subnets.get(res_name, set()))
            for key, value in res_attrs.items():
                if not isinstance(key, str) or "subnet_group" not in key:
                    continue
                refs = _extract_tf_resource_refs(value)
                for ref in refs:
                    inherited_subnets = resource_to_subnets.get(ref)
                    if inherited_subnets:
                        resource_to_subnets.setdefault(res_name, set()).update(
                            inherited_subnets
                        )
            if len(resource_to_subnets.get(res_name, set())) > previous_count:
                changed = True

    return resource_to_subnets


def _resource_prefers_private_subnet_placement(
    resource_name: str,
    resource_attrs: dict[str, Any],
) -> bool:
    resource_type = resource_name.split(".", 1)[0]
    if resource_type in {
        "aws_eks_cluster",
        "azurerm_kubernetes_cluster",
        "google_container_cluster",
        "oci_containerengine_cluster",
        "ibm_container_cluster",
    }:
        return True
    if not isinstance(resource_attrs, dict):
        return False
    return any("subnet_group" in str(key) for key in resource_attrs)


def _consolidate_plumbing_resources(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    expand_badges: bool = False,
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    """Consolidate attachment and connector resources to produce clean architectural flows.

    Plumbing = attachment/config/rule resources with no standalone architectural meaning.
    NEVER add first-class architectural boundary nodes (SGs, ACLs, Firewalls, EIPs) here.
    """
    PLUMBING_TYPES = {
        # S3 configuration attachments (config sub-resources, not standalone nodes)
        "aws_s3_bucket_versioning",
        "aws_s3_bucket_public_access_block",
        "aws_s3_bucket_ownership_controls",
        "aws_s3_bucket_server_side_encryption_configuration",
        "aws_s3_bucket_lifecycle_configuration",
        "aws_s3_bucket_policy",
        "aws_s3_bucket_acl",
        "aws_s3_bucket_cors_configuration",
        "aws_s3_bucket_website_configuration",
        # IAM attachments (policy bindings, not standalone nodes)
        "aws_iam_role_policy",
        "aws_iam_role_policy_attachment",
        "aws_iam_policy_attachment",
        "aws_iam_instance_profile",
        # Network sub-resource attachments (implementation details, not arch nodes)
        # NOTE: aws_network_acl, aws_eip, google_compute_firewall are architectural
        #       boundary nodes and must NOT be listed here.
        "aws_network_acl_rule",              # Rule attachment only (the ACL itself is kept)
        "aws_vpc_peering_connection_accepter",  # Accepter half of a peering pair
        "aws_lb_target_group_attachment",
        "aws_alb_target_group_attachment",
        "aws_lb_listener_rule",
        "aws_route_table",
        "aws_route_table_association",
        "aws_route",
        "aws_main_route_table_association",
        "aws_default_route_table",
        "aws_default_network_acl",
        "aws_default_security_group",        # Default SG override (not the real SG)
        "aws_dms_replication_subnet_group",  # DMS config attachment only
        "aws_sqs_queue_policy",
        "aws_sns_topic_policy",
        "aws_cloudwatch_log_resource_policy",
        "azurerm_storage_container",
        "azurerm_subnet_network_security_group_association",  # NSG→Subnet link (not the NSG)
        "azurerm_subnet_route_table_association",
        "google_compute_route",
        # Connector types bridged into direct service-to-service edges
        "aws_sns_topic_subscription",
        "aws_lambda_event_source_mapping",
        "aws_cloudwatch_event_target",
        "aws_lambda_permission",
        "aws_api_gateway_integration",
        "aws_api_gateway_route",
        "azurerm_role_assignment",
    }
    if not expand_badges:
        PLUMBING_TYPES.update({
            # Security group RULES are plumbing; the aws_security_group itself
            # is an architectural boundary node and must always be rendered.
            "aws_security_group_rule",
            "aws_vpc_security_group_egress_rule",
            "aws_vpc_security_group_ingress_rule",
            # azurerm_network_security_rule is a rule attachment; the NSG itself is kept.
            "azurerm_network_security_rule",
        })

    bridged_edges = set(edges)

    # Extract explicit connector bridges directly from resource attributes
    for res_name, attrs in all_resources.items():
        r_type = res_name.split(".", 1)[0]
        if not isinstance(attrs, dict):
            continue

        # SNS to SQS / Lambda subscription
        if r_type == "aws_sns_topic_subscription":
            topic_refs = _extract_tf_resource_refs(attrs.get("topic_arn") or attrs.get("topic") or "")
            endpoint_refs = _extract_tf_resource_refs(attrs.get("endpoint") or "")
            for s in topic_refs:
                for d in endpoint_refs:
                    if s in all_resources and d in all_resources:
                        bridged_edges.add((s, d))

        # SQS / DynamoDB / Kinesis to Lambda mapping
        elif r_type == "aws_lambda_event_source_mapping":
            src_refs = _extract_tf_resource_refs(attrs.get("event_source_arn") or "")
            dst_refs = _extract_tf_resource_refs(attrs.get("function_name") or "")
            for s in src_refs:
                for d in dst_refs:
                    if s in all_resources and d in all_resources:
                        bridged_edges.add((s, d))

        # EventBridge to Lambda / Target
        elif r_type == "aws_cloudwatch_event_target":
            rule_refs = _extract_tf_resource_refs(attrs.get("rule") or "")
            target_refs = _extract_tf_resource_refs(attrs.get("arn") or "")
            for s in rule_refs:
                for d in target_refs:
                    if s in all_resources and d in all_resources:
                        bridged_edges.add((s, d))

        # Lambda Permission
        elif r_type == "aws_lambda_permission":
            src_refs = _extract_tf_resource_refs(attrs.get("source_arn") or "")
            dst_refs = _extract_tf_resource_refs(attrs.get("function_name") or "")
            for s in src_refs:
                for d in dst_refs:
                    if s in all_resources and d in all_resources:
                        bridged_edges.add((s, d))

        # VPC Peering Connection: bridge primary VPC to peer VPC
        elif r_type == "aws_vpc_peering_connection":
            vpc_refs = _extract_tf_resource_refs(attrs.get("vpc_id") or "")
            peer_refs = _extract_tf_resource_refs(attrs.get("peer_vpc_id") or "")
            for s in vpc_refs:
                for d in peer_refs:
                    if s in all_resources and d in all_resources:
                        bridged_edges.add((s, d))

        # Step Functions State Machine definition references
        elif r_type == "aws_sfn_state_machine":
            def_str = str(attrs.get("definition") or "")
            for other_res in all_resources:
                if other_res != res_name:
                    o_name = other_res.split(".", 1)[1]
                    if o_name in def_str or other_res in def_str:
                        bridged_edges.add((res_name, other_res))

        # SageMaker references to training data / model registry
        elif r_type == "aws_sagemaker_notebook_instance":
            for other_res in all_resources:
                if "training_data" in other_res or "model_artifacts" in other_res or "feature_store" in other_res:
                    bridged_edges.add((res_name, other_res))

        # CloudWatch Logs, KMS, SNS alerts associated with ML / Compute workflows
        elif r_type in {"aws_cloudwatch_log_group", "aws_kms_key", "aws_sns_topic"}:
            for other_res in all_resources:
                if "sfn_state_machine" in other_res or "lambda_function" in other_res or "sagemaker" in other_res:
                    bridged_edges.add((res_name, other_res))

    filtered_res = {
        k: v
        for k, v in all_resources.items()
        if k.split(".", 1)[0] not in PLUMBING_TYPES
    }

    # Producers emit events/messages to downstream consumers (reverse inverted HCL references)
    REVERSE_ORIGINS = {
        "aws_cloudwatch_event_rule",
        "aws_sns_topic",
    }

    final_edges: set[tuple[str, str]] = set()
    for s, d in bridged_edges:
        if s in filtered_res and d in filtered_res and s != d:
            s_type = s.split(".", 1)[0]
            d_type = d.split(".", 1)[0]
            if d_type in REVERSE_ORIGINS and s_type not in REVERSE_ORIGINS:
                final_edges.add((d, s))
            else:
                final_edges.add((s, d))

    return filtered_res, final_edges


def _filter_architectural_edges(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Suppress structurally true but visually misleading network edges."""

    vpcs: dict[str, dict[str, Any]] = {}
    subnets: dict[str, dict[str, Any]] = {}
    for res_name, res_attrs in all_resources.items():
        resource_type = res_name.split(".", 1)[0]
        if _is_vpc_or_network(resource_type):
            vpcs[res_name] = res_attrs
        elif _is_subnet(resource_type):
            subnets[res_name] = res_attrs

    resource_to_subnets = _infer_resource_to_subnets(all_resources, edges, vpcs, subnets)
    filtered_edges = set(edges)

    for res_name, attached_subnets in sorted(resource_to_subnets.items()):
        resource_type = res_name.split(".", 1)[0]
        if resource_type not in {
            "aws_eks_cluster",
            "azurerm_kubernetes_cluster",
            "google_container_cluster",
            "oci_containerengine_cluster",
            "ibm_container_cluster",
        }:
            continue

        private_subnets = {
            subnet_name
            for subnet_name in attached_subnets
            if not _is_public_subnet(subnet_name, all_resources.get(subnet_name, {}))
        }
        public_subnets = set(attached_subnets) - private_subnets
        if not private_subnets or not public_subnets:
            continue

        filtered_edges = {
            (src, dst)
            for src, dst in filtered_edges
            if not (
                (src == res_name and dst in public_subnets)
                or (dst == res_name and src in public_subnets)
            )
        }

    # ------------------------------------------------------------------
    # Bundle dense data-flow highways — universal, density-aware.
    # When a diagram has many parallel data edges between the same
    # category pair (e.g. Storage → Compute with 8+ edges), keep a
    # small representative set so the diagram stays readable for any
    # architecture. Activates only for dense diagrams.
    # ------------------------------------------------------------------
    try:
        from collections import defaultdict

        total = len(filtered_edges)
        # Universal highway bundling — any edge type (data, security,
        # dependency, network) can form a dense parallel bundle that
        # makes the diagram look like spaghetti. Activate for any dense
        # diagram and collapse each overfull directed category pair.
        from collections import Counter

        type_counts = Counter(
            _detect_edge_type(s, d, all_resources) for s, d in filtered_edges
        )
        should_bundle = total > 28 or any(c > 10 for c in type_counts.values())
        if should_bundle:
            by_pair: dict[tuple[str, str, str], list[tuple[str, str]]] = defaultdict(list)
            for s, d in filtered_edges:
                et = _detect_edge_type(s, d, all_resources)
                sc = _tf_category(s.split(".", 1)[0])
                dc = _tf_category(d.split(".", 1)[0])
                # Directed triple so Storage→Compute:data vs :security are distinct
                by_pair[(sc, dc, et)].append((s, d))

            keep: set[tuple[str, str]] = set()
            drop: set[tuple[str, str]] = set()
            for triple, lst in by_pair.items():
                if len(lst) <= 2:
                    keep.update(lst)
                    continue
                lst_sorted = sorted(lst)
                # Ultra-aggressive for readability: any highway >2 collapses
                # to a single representative for dense diagrams, 2 otherwise.
                # Ensures any architecture — even 39-resource multi-region —
                # stays clean and professional.
                if total > 30 or len(lst) > 4:
                    keep_n = 1
                elif len(lst) > 3:
                    keep_n = 2
                else:
                    keep_n = 2
                keep.update(lst_sorted[:keep_n])
                drop.update(lst_sorted[keep_n:])

            if drop:
                filtered_edges = (filtered_edges - drop) | keep
                # For debugging: print(f"[bundle] {len(drop)} edges bundled ({type_counts}) -> {len(filtered_edges)} remain")
        # Global clarity cap — universal: no diagram should have more than
        # 28-32 edges or it becomes unreadable for any architecture. Keep
        # most architecturally significant (security > data > dependency).
        if len(filtered_edges) > 28:
            prio = {"security": 0, "data": 1, "dependency": 2, "network": 3}
            def _rank(e: tuple[str, str]) -> tuple[int, str, str]:
                et = _detect_edge_type(e[0], e[1], all_resources)
                return (prio.get(et, 99), e[0], e[1])
            filtered_edges = set(sorted(filtered_edges, key=_rank)[:28])
    except Exception:
        pass

    return filtered_edges


def _build_vpc_hierarchy(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> dict[str, dict[str, list[str]]]:
    """Build VPC/network hierarchy showing which resources belong to which VPC/subnets.

    Returns: {vpc_name: {subnet_name: [resources...], 'other': [resources...]}}
    """
    vpc_hierarchy: dict[str, dict[str, list[str]]] = {}

    # Find all VPCs and subnets
    vpcs: dict[str, dict[str, Any]] = {}
    subnets: dict[str, dict[str, Any]] = {}

    for res_name, res_attrs in all_resources.items():
        r_type = res_name.split(".", 1)[0]
        if _is_vpc_or_network(r_type):
            vpcs[res_name] = res_attrs
        elif _is_subnet(r_type):
            subnets[res_name] = res_attrs

    subnet_to_vpc = _infer_subnet_to_vpc(all_resources, edges, vpcs, subnets)
    resource_to_subnets = _infer_resource_to_subnets(all_resources, edges, vpcs, subnets)

    # Track direct VPC attachments for non-subnet resources.
    # Resources attached to multiple VPCs (for example, VPC peering links) are rendered
    # outside individual VPC containers to avoid duplication and preserve topology.
    resource_to_vpcs: dict[str, set[str]] = {}
    for src, dst in sorted(edges):
        if src in vpcs and dst not in vpcs and dst not in subnets:
            resource_to_vpcs.setdefault(dst, set()).add(src)
        elif dst in vpcs and src not in vpcs and src not in subnets:
            resource_to_vpcs.setdefault(src, set()).add(dst)

    # Derive final placements.
    resource_to_subnet: dict[str, str] = {}
    vpc_multi_subnet_resources: dict[str, set[str]] = {}
    for res_name, attached_subnets_set in sorted(resource_to_subnets.items()):
        attached_subnets = sorted(attached_subnets_set)
        if len(attached_subnets) == 1:
            resource_to_subnet[res_name] = attached_subnets[0]
            continue
        if len(attached_subnets) > 1:
            if _resource_prefers_private_subnet_placement(
                res_name, all_resources.get(res_name, {})
            ):
                private_subnets = sorted(
                    s for s in attached_subnets
                    if not _is_public_subnet(s, all_resources.get(s, {}))
                )
                if private_subnets:
                    resource_to_subnet[res_name] = private_subnets[0]
                    continue
            parent_vpcs = {
                subnet_to_vpc[subnet_name]
                for subnet_name in attached_subnets
                if subnet_name in subnet_to_vpc
            }
            if len(parent_vpcs) == 1:
                vpc_name = next(iter(parent_vpcs))
                vpc_multi_subnet_resources.setdefault(vpc_name, set()).add(res_name)

    # Build the hierarchy
    for vpc_name in vpcs:
        vpc_hierarchy[vpc_name] = {}
        # Find subnets in this VPC
        for subnet_name, parent_vpc in subnet_to_vpc.items():
            if parent_vpc == vpc_name:
                vpc_hierarchy[vpc_name][subnet_name] = []
                # Find resources in this subnet
                for res_name, parent_subnet in sorted(resource_to_subnet.items()):
                    if parent_subnet == subnet_name:
                        vpc_hierarchy[vpc_name][subnet_name].append(res_name)

        # Add "other" category for VPC-level resources not in subnets
        other_resources: list[str] = []
        seen_other: set[str] = set()

        for res_name in sorted(vpc_multi_subnet_resources.get(vpc_name, set())):
            other_resources.append(res_name)
            seen_other.add(res_name)

        for src, dst in sorted(edges):
            if src == vpc_name and dst not in subnets and dst not in vpcs:
                if (
                    dst not in resource_to_subnet
                    and dst not in seen_other
                    and resource_to_vpcs.get(dst, {vpc_name}) == {vpc_name}
                ):
                    other_resources.append(dst)
                    seen_other.add(dst)
            elif dst == vpc_name and src not in subnets and src not in vpcs:
                if (
                    src not in resource_to_subnet
                    and src not in seen_other
                    and resource_to_vpcs.get(src, {vpc_name}) == {vpc_name}
                ):
                    other_resources.append(src)
                    seen_other.add(src)
        if other_resources:
            vpc_hierarchy[vpc_name]["other"] = other_resources

    return vpc_hierarchy


def _build_compute_subclusters(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> dict[str, list[str]]:
    """Identify compute cluster parent→child groupings for visual nesting.

    Real-world architectures:
    - aws_eks_cluster → [aws_eks_node_group, aws_eks_fargate_profile]
    - aws_ecs_cluster → [aws_ecs_service]
    - azurerm_kubernetes_cluster → [azurerm_kubernetes_cluster_node_pool]
    - google_container_cluster → [google_container_node_pool]

    Returns: {parent_resource: [child_resources]}
    """
    # Maps child resource type → (expected parent type, attribute pointing to parent)
    _child_to_parent: dict[str, tuple[str, str]] = {
        "aws_eks_node_group": ("aws_eks_cluster", "cluster_name"),
        "aws_eks_fargate_profile": ("aws_eks_cluster", "cluster_name"),
        "aws_ecs_service": ("aws_ecs_cluster", "cluster"),
        "azurerm_kubernetes_cluster_node_pool": (
            "azurerm_kubernetes_cluster", "kubernetes_cluster_id"
        ),
        "google_container_node_pool": ("google_container_cluster", "cluster"),
        "oci_containerengine_node_pool": ("oci_containerengine_cluster", "cluster_id"),
    }

    parent_child: dict[str, list[str]] = {}

    # Build lookup: resource_name → resource_type
    res_to_type = {r: r.split(".", 1)[0] for r in all_resources}

    for child_res, child_attrs in all_resources.items():
        child_type = res_to_type[child_res]
        if child_type not in _child_to_parent:
            continue
        expected_parent_type, parent_attr = _child_to_parent[child_type]

        matched_parent: str | None = None

        # 1. Check the child's attribute for a direct reference to the parent
        if isinstance(child_attrs, dict) and parent_attr in child_attrs:
            refs = _extract_tf_resource_refs(child_attrs[parent_attr])
            for ref in refs:
                if ref in all_resources and res_to_type.get(ref) == expected_parent_type:
                    matched_parent = ref
                    break

        # 2. Fall back to checking edges: child → parent or parent → child
        if matched_parent is None:
            for src, dst in edges:
                if src == child_res and res_to_type.get(dst) == expected_parent_type:
                    matched_parent = dst
                    break
                if dst == child_res and res_to_type.get(src) == expected_parent_type:
                    matched_parent = src
                    break

        if matched_parent is not None:
            if child_res not in parent_child.get(matched_parent, []):
                parent_child.setdefault(matched_parent, []).append(child_res)

    return parent_child


_REGION_PATTERN = re.compile(r"\b[a-z]{2}(?:-[a-z]+)+-\d\b", re.IGNORECASE)


def _extract_region_from_value(value: Any) -> Optional[str]:
    """Extract cloud region token from free-form Terraform values."""
    if isinstance(value, str):
        match = _REGION_PATTERN.search(value)
        return match.group(0).lower() if match else None

    if isinstance(value, list):
        for item in value:
            region = _extract_region_from_value(item)
            if region:
                return region
        return None

    if isinstance(value, dict):
        for nested_value in value.values():
            region = _extract_region_from_value(nested_value)
            if region:
                return region
        return None

    return None


def _infer_resource_regions(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> dict[str, str]:
    """Infer resource-to-region assignments for multi-region diagram grouping."""
    resource_regions: dict[str, str] = {}

    for res_name, res_attrs in all_resources.items():
        if not isinstance(res_attrs, dict):
            continue

        region: Optional[str] = None

        provider_hint = res_attrs.get("provider")
        if provider_hint is not None:
            region = _extract_region_from_value(provider_hint)

        if not region:
            for key in (
                "region",
                "location",
                "peer_region",
                "secondary_region",
                "destination_region",
            ):
                if key in res_attrs:
                    region = _extract_region_from_value(res_attrs[key])
                    if region:
                        break

        if not region:
            tags = res_attrs.get("tags")
            if isinstance(tags, dict):
                for tag_key in ("Region", "region", "Location", "location"):
                    if tag_key in tags:
                        region = _extract_region_from_value(tags[tag_key])
                        if region:
                            break

        if region:
            resource_regions[res_name] = region

    changed = True
    while changed:
        changed = False
        for src, dst in sorted(edges):
            src_region = resource_regions.get(src)
            dst_region = resource_regions.get(dst)
            if src_region and not dst_region:
                resource_regions[dst] = src_region
                changed = True
            elif dst_region and not src_region:
                resource_regions[src] = dst_region
                changed = True

    return resource_regions


def _build_region_hierarchy(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> dict[str, list[str]]:
    """Build region-to-resources mapping used for multi-region rendering."""
    resource_regions = _infer_resource_regions(all_resources, edges)
    if not resource_regions:
        return {}

    grouped: dict[str, list[str]] = {}
    for res_name in sorted(all_resources.keys()):
        region = resource_regions.get(res_name)
        if region:
            grouped.setdefault(region, []).append(res_name)

    # Activate region clusters only when there are multiple distinct regions.
    return grouped if len(grouped) >= 2 else {}


def _build_subgraph_render_map(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
) -> tuple[
    dict[str, dict[str, list[str]]],
    dict[str, list[str]],
    set[str],
    set[str],
]:
    """Precompute placement/grouping information reused by icon and Mermaid renderers."""

    filtered_edges = _filter_architectural_edges(all_resources, edges)
    vpc_hierarchy = _build_vpc_hierarchy(all_resources, filtered_edges)
    compute_subclusters = _build_compute_subclusters(all_resources, filtered_edges)
    compute_children: set[str] = {
        child for children in compute_subclusters.values() for child in children
    }

    resources_in_vpcs: set[str] = set()
    for vpc_name, subnets_dict in vpc_hierarchy.items():
        resources_in_vpcs.add(vpc_name)
        for subnet_name, subnet_resources in subnets_dict.items():
            if subnet_name != "other":
                resources_in_vpcs.add(subnet_name)
            resources_in_vpcs.update(subnet_resources)

    return vpc_hierarchy, compute_subclusters, compute_children, resources_in_vpcs


def _wrap_text(text: str, *, max_width: int = 20, max_lines: int = 2) -> str:
    """Wrap/shorten labels so Graphviz doesn't overflow outside node tiles.

    Width is generous enough to keep full service names readable, matching
    professional architecture-diagram conventions (labels should rarely be
    truncated).
    """

    text = (text or "").strip()
    if not text:
        return ""

    # Normalize separators and split into tokens.
    tokens = re.split(r"[\s_\-]+", text)
    tokens = [t for t in tokens if t]
    if not tokens:
        return text[:max_width]

    lines: list[str] = []
    current = ""
    for tok in tokens:
        if not current:
            current = tok
            continue
        if len(current) + 1 + len(tok) <= max_width:
            current = f"{current} {tok}"
        else:
            lines.append(current)
            current = tok
            if len(lines) >= max_lines:
                break
    if len(lines) < max_lines and current:
        lines.append(current)

    # Truncate last line if still too long.
    if lines:
        last = lines[-1]
        if len(last) > max_width:
            lines[-1] = last[: max_width - 1] + "…"

    # If we had to drop tokens, indicate truncation.
    used_tokens = set(" ".join(lines).split())
    if len(used_tokens) < len(tokens) and lines:
        last = lines[-1]
        if not last.endswith("…"):
            if len(last) >= max_width:
                lines[-1] = last[: max_width - 1] + "…"
            else:
                lines[-1] = last + "…"

    return "\n".join(lines[:max_lines])


def _tf_pretty_kind(terraform_resource_type: str) -> str:
    t = terraform_resource_type.lower()
    for prefix in ("aws_", "azurerm_", "google_", "oci_", "ibm_"):
        if t.startswith(prefix):
            t = t[len(prefix) :]
            break

    # Common acronyms
    replacements = {
        "vpc": "VPC",
        "vnet": "VNet",
        "vcn": "VCN",
        "nsg": "NSG",
        "eks": "EKS",
        "aks": "AKS",
        "gke": "GKE",
        "vm": "VM",
        "iam": "IAM",
        "sql": "SQL",
    }
    parts = [replacements.get(p, p) for p in t.split("_") if p]
    # Title-case non-acronym parts
    parts = [
        p
        if p.isupper()
        or p in {"VPC", "VNet", "VCN", "NSG", "EKS", "AKS", "GKE", "VM", "IAM", "SQL"}
        else p.title()
        for p in parts
    ]
    return " ".join(parts)


def _tf_node_label(res_id: str) -> str:
    # res_id is like "aws_vpc.main".
    override = _CURRENT_LABEL_OVERRIDES.get(res_id)
    if override is None and "." in res_id:
        override = _CURRENT_LABEL_OVERRIDES.get(res_id.split(".", 1)[1])
    if override:
        return _wrap_text(override, max_width=20, max_lines=2)
    try:
        r_type, name = res_id.split(".", 1)
    except ValueError:
        return _wrap_text(res_id)
    name = _strip_env_prefix_from_name(name)
    kind = _tf_pretty_kind(r_type)
    # Wrap kind and keep name on its own line.
    kind_wrapped = _wrap_text(kind, max_width=20, max_lines=1)
    name_wrapped = _wrap_text(name, max_width=20, max_lines=1)
    return f"{kind_wrapped}\n{name_wrapped}".strip()


def _create_node_with_xlabel(icon_cls, label: str):
    """Create a compact node with centered label below icon."""
    # Use native label with height that accommodates icon + label
    return icon_cls(label, height="1.2", labelloc="b", imagepos="tc")


def _import_node_class(module_path: str, class_name: str):
    try:
        mod = __import__(module_path, fromlist=[class_name])
        return getattr(mod, class_name)
    except Exception:
        return None


def _debug(msg: str) -> None:
    """Print diagnostic output only when AUTO_ARCH_DEBUG is enabled."""
    if os.getenv("AUTO_ARCH_DEBUG"):
        print(msg)


def _load_custom_icon(terraform_resource_type: str, resource_attrs: dict[str, Any] | None = None):
    """Load custom icon from Icon tag or icons/ directory.
    
    Resolution order:
    1. Check resource tags for Icon field with custom:// scheme
    2. Check icons/custom/ directory
    3. Check icons/{provider}/ directory
    4. Return None (fall back to diagrams library)
    """
    
    if Diagram is None:
        return None
    
    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"
    
    # === STEP 1: Check Icon tag in resource attributes ===
    if resource_attrs and isinstance(resource_attrs, dict):
        tags = resource_attrs.get("tags", {})
        if isinstance(tags, dict):
            icon_tag = tags.get("Icon", "").strip()
            
            if icon_tag.startswith("custom://"):
                # Extract custom icon name
                custom_name = icon_tag.replace("custom://", "").strip()
                if not custom_name:
                    if os.getenv("AUTO_ARCH_DEBUG"):
                        print(f"[WARN] Empty custom:// icon reference in tags for {terraform_resource_type}")
                    return None
                
                # Try icons/custom/{custom_name}.png
                custom_icon_path = icons_dir / "custom" / f"{custom_name}.png"
                if custom_icon_path.exists():
                    Custom = _import_node_class("diagrams.custom", "Custom")
                    if Custom:
                        def custom_icon_wrapper(label: str = ""):
                            return Custom(label, str(custom_icon_path))
                        if os.getenv("AUTO_ARCH_DEBUG"):
                            print(f"[DEBUG] Using Icon tag custom:// path: {custom_icon_path}")
                        return custom_icon_wrapper
                else:
                    if os.getenv("AUTO_ARCH_DEBUG"):
                        print(f"[WARN] Icon tag references missing file: {custom_icon_path}")
                    return None
    
    # === STEP 2: Standard directory search (no Icon tag or not custom://) ===
    t = terraform_resource_type.lower()
    provider = None
    
    for pfx in ("aws", "azurerm", "google", "oci", "ibm"):
        if t.startswith(f"{pfx}_"):
            provider = pfx
            t_no_prefix = t[len(pfx) + 1 :]
            break
    else:
        t_no_prefix = t
    
    # Try icons/custom/ directory by service name
    custom_icon_path = icons_dir / "custom" / f"{t_no_prefix}.png"
    if custom_icon_path.exists():
        Custom = _import_node_class("diagrams.custom", "Custom")
        if Custom:
            def custom_icon_wrapper(label: str = ""):
                return Custom(label, str(custom_icon_path))
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"[DEBUG] Using custom icon from directory: {custom_icon_path}")
            return custom_icon_wrapper
    
    # Try icons/{provider}/ directory
    if provider:
        provider_icon_path = icons_dir / provider / f"{t_no_prefix}.png"
        if provider_icon_path.exists():
            Custom = _import_node_class("diagrams.custom", "Custom")
            if Custom:
                def custom_icon_wrapper(label: str = ""):
                    return Custom(label, str(provider_icon_path))
                if os.getenv("AUTO_ARCH_DEBUG"):
                    print(f"[DEBUG] Using provider icon: {provider_icon_path}")
                return custom_icon_wrapper
    
    # No custom icon found
    return None


@lru_cache(maxsize=1)
def _load_comprehensive_mappings() -> Optional[dict[str, Any]]:
    """Load the comprehensive service-mappings JSON once per process."""
    path = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "comprehensive_service_mappings.json"
    )
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _icon_class_for(
    terraform_resource_type: str, resource_attrs: dict[str, Any] | None = None
):
    """Best-effort mapping from TF resource type to a provider service icon.

    This aims for "professional" official-style icons via the `diagrams` library.
    If a specific icon isn't known, falls back to generic nodes.

    Resolution order:
    0. Icon tag override in resource tags (custom:// scheme or icon path/name)
    1. Comprehensive service mappings (diagrams library priority)
    2. Custom icons in icons/{provider}/ directory
    3. Built-in diagrams library icons (legacy)
    4. Generic fallback icons
    """
    # Explicit per-resource Icon tags take precedence over static type mapping.
    # Results are cached per resource type; the tag check runs first because it
    # varies per resource instance.
    if isinstance(resource_attrs, dict):
        tags = resource_attrs.get("tags")
        if isinstance(tags, dict) and str(tags.get("Icon", "")).strip():
            override = _load_custom_icon(terraform_resource_type, resource_attrs)
            if override is not None:
                return override

        # Check attribute-based variants (e.g. RDS engine, LB type, ECS launch type)
        r_low = terraform_resource_type.lower()
        if r_low == "aws_lb":
            lb_type = str(resource_attrs.get("load_balancer_type", "")).lower()
            if "network" in lb_type:
                nlb_icon = _resolve_icon_class_cached("aws_nlb")
                if nlb_icon:
                    return nlb_icon
            else:
                alb_icon = _resolve_icon_class_cached("aws_alb")
                if alb_icon:
                    return alb_icon
        elif r_low in {"aws_db_instance", "aws_rds_cluster", "aws_rds"}:
            engine = str(resource_attrs.get("engine", "")).lower()
            if "aurora" in engine:
                aurora_icon = _import_node_class("diagrams.aws.database", "Aurora")
                if aurora_icon:
                    return aurora_icon
        elif r_low == "aws_ecs_service":
            launch_type = str(resource_attrs.get("launch_type", "")).upper()
            if "FARGATE" in launch_type:
                fargate_icon = _import_node_class("diagrams.aws.compute", "Fargate")
                if fargate_icon:
                    return fargate_icon

    return _resolve_icon_class_cached(terraform_resource_type)

@lru_cache(maxsize=1024)
def _resolve_icon_class_cached(terraform_resource_type: str):
    """Heavy icon-resolution pipeline, cached per Terraform resource type.

    The comprehensive mappings JSON is loaded once per process and resolution
    results (including import lookups) are memoized, so rendering large IaC
    repos stays fast.
    """
    service_mappings = _load_comprehensive_mappings()

    # Normalize provider
    resource_provider = _guess_provider(terraform_resource_type).lower()
    if resource_provider == "azurerm":
        resource_provider = "azure"
    elif resource_provider == "google":
        resource_provider = "gcp"
    provider_normalized = resource_provider

    t_clean = terraform_resource_type.lower()
    for prefix in ("aws_", "azurerm_", "google_", "oci_", "ibm_"):
        if t_clean.startswith(prefix):
            t_clean = t_clean[len(prefix) :]
            break
    parts = t_clean.split("_")

    # 1. Try comprehensive mapping file (longest match first)
    if service_mappings and provider_normalized in service_mappings:
        mappings_for_provider = service_mappings[provider_normalized]
        for n in range(len(parts), 0, -1):
            candidate = "_".join(parts[:n])
            if candidate in mappings_for_provider:
                info = mappings_for_provider[candidate]
                category = info["category"]
                cls = info["class"]
                mod_path = f"diagrams.{provider_normalized}.{category}"
                icon_cls = _import_node_class(mod_path, cls)
                if icon_cls:
                    _debug(f"[DEBUG] Using diagrams class (mapping): {mod_path}.{cls}")
                    return icon_cls
                _debug(f"[DEBUG] Mapping diagrams import failed: {mod_path}.{cls}")
                break

    # 2. Improved normalization/heuristics for multi-word services
    # e.g. aws_cloudwatch_event_target -> diagrams.aws.management.CloudwatchEventTarget
    tried_classes: set[str] = set()
    for i in range(1, len(parts)):
        category = parts[0] if i == 1 else "_".join(parts[:i])
        class_parts = parts[i:]
        if not class_parts:
            continue
        # CamelCase for class name
        class_guess = "".join([p.title() for p in class_parts])
        mod_path = f"diagrams.{provider_normalized}.{category}"
        for variant in [class_guess, class_guess + "s", class_guess.rstrip("s")]:
            if not variant or variant in tried_classes:
                continue
            tried_classes.add(variant)
            icon_cls = _import_node_class(mod_path, variant)
            if icon_cls:
                _debug(
                    f"[DEBUG] Using diagrams class (normalized): {mod_path}.{variant}"
                )
                return icon_cls

    # 3. Fuzzy/partial match across all categories in the provider module
    try:
        provider_mod = __import__(f"diagrams.{provider_normalized}", fromlist=["*"])
        resource_camel = (
            "".join([p.title() for p in parts[1:]])
            if len(parts) > 1
            else "".join([p.title() for p in parts])
        )
        resource_lower = resource_camel.lower()
        for attr in dir(provider_mod):
            if attr.startswith("__"):
                continue
            try:
                cat_mod = getattr(provider_mod, attr)
                for class_name in dir(cat_mod):
                    if class_name.startswith("__"):
                        continue
                    if resource_lower and resource_lower in class_name.lower():
                        icon_cls = getattr(cat_mod, class_name, None)
                        if icon_cls:
                            _debug(
                                "[DEBUG] Using diagrams class (fuzzy/partial): "
                                f"diagrams.{provider_normalized}.{attr}.{class_name}"
                            )
                            return icon_cls
            except Exception:
                continue
    except Exception as e:
        _debug(f"[DEBUG] Fuzzy diagrams provider scan failed: {e}")

    # 4. Fallback to PNG/custom icon directory search
    custom_icon = _load_custom_icon(terraform_resource_type)
    if custom_icon is not None:
        _debug(f"[WARN] Falling back to PNG icon for {terraform_resource_type}")
        return custom_icon

    # 5. Ultimate fallback: BulletproofMapper for guaranteed mapping
    global _ultimate_mapper
    if _ultimate_mapper is None:
        _ultimate_mapper = BulletproofMapper()

    try:
        ultimate_icon = _ultimate_mapper.get_icon(terraform_resource_type)
        if ultimate_icon:
            _debug(f"[INFO] BulletproofMapper found icon for {terraform_resource_type}")
            return ultimate_icon
    except Exception as e:
        _debug(f"[DEBUG] BulletproofMapper failed: {e}")

    # 6. Absolute final fallback to diagrams.generic.blank.Blank
    _debug(
        f"[ERROR] All mapping failed for {terraform_resource_type}, "
        "using diagrams.generic.blank.Blank"
    )
    blank_cls = _import_node_class("diagrams.generic.blank", "Blank")
    if blank_cls:
        return blank_cls
    return None

def _ensure_generic_fallback_icons():
    """Ensure generic fallback icons are imported and available."""
    # This function ensures that basic icons are available as fallbacks
    # It's called early in the diagram rendering process
    try:
        # Try to import some basic icons to ensure they're available
        from diagrams.generic.blank import Blank
        from diagrams.aws.compute import EC2

        # If we get here, the imports work
        return True
    except Exception:
        # If imports fail, we'll use text labels as fallbacks
        return False


def _generic_icon_for_kind(kind: str):
    """Get a generic icon class for a given resource kind."""
    # This is a fallback when specific service icons aren't available
    kind = kind.lower().strip()

    # Map common kinds to generic icons
    icon_map = {
        "instance": "EC2",
        "bucket": "S3",
        "database": "RDS",
        "function": "Lambda",
        "network": "VPC",
        "security": "IAM",
        "storage": "EBS",
        "compute": "EC2",
        "container": "ECS",
        "serverless": "Lambda",
    }

    generic_kind = icon_map.get(kind, "EC2")  # Default to EC2

    try:
        return _import_node_class("diagrams.aws.compute", generic_kind)
    except Exception:
        # If AWS EC2 fails, try a basic generic icon
        try:
            from diagrams.generic.blank import Blank

            return Blank
        except Exception:
            return None


def _render_icon_diagram_from_terraform(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    *,
    out_path: Path,
    title: str,
    direction: str,
    render: RenderConfig,
    ai_hints: tuple[str, ...] | None = None,
    ai_subtitle: str | None = None,
):
    if Diagram is None or Cluster is None:
        raise RuntimeError(
            "Missing dependency diagrams. Install it and Graphviz to enable icon rendering."
        )

    if not getattr(render, "no_consolidate", False):
        all_resources, edges = _consolidate_plumbing_resources(all_resources, edges)

    edges = _filter_architectural_edges(all_resources, edges)

    _ensure_generic_fallback_icons()

    # diagrams expects filename without extension; it appends based on outformat.
    outformat = out_path.suffix.lstrip(".").lower() or "png"
    if outformat in {"jpg", "jpeg"}:
        diag_outformat = "png"
        render_filename_no_ext = str(out_path.with_name(f"{out_path.stem}__tmp_convert"))
    else:
        diag_outformat = outformat
        render_filename_no_ext = str(out_path.with_suffix(""))

    node_by_res: dict[str, Any] = {}

    layout = (
        (os.getenv("AUTO_ARCH_RENDER_LAYOUT") or render.layout or "lanes")
        .strip()
        .lower()
    )
    lanes = list(render.lanes)

    # Prepare groups depending on layout style.
    grouped_lanes: dict[str, dict[str, list[str]]] = {lane: {} for lane in lanes}
    grouped_providers: dict[str, dict[str, list[str]]] = {}

    for res in all_resources.keys():
        r_type, _name = res.split(".", 1)
        provider = _guess_provider(r_type)
        lane = _tf_category(r_type)
        grouped_lanes.setdefault(lane, {}).setdefault(provider, []).append(res)
        grouped_providers.setdefault(provider, {}).setdefault(lane, []).append(res)

    # Select the appropriate grouping based on layout
    grouped_data = grouped_lanes if layout == "lanes" else grouped_providers

    # Analyze diagram complexity for dynamic spacing
    complexity = _analyze_diagram_complexity(all_resources, edges, grouped_data)

    # Skip extremely complex diagrams that may cause performance issues
    max_allowed_nodes = 120  # Allow larger diagrams before skipping render
    if complexity.node_count > max_allowed_nodes:
        env_groups = _group_resources_by_env(all_resources)
        if len(env_groups) > 1:
            print(
                f"⚠️  Diagram too large ({complexity.node_count} > {max_allowed_nodes}). Splitting by environment."
            )
            for env_key, res_list in sorted(env_groups.items()):
                res_set = set(res_list)
                if not res_set:
                    continue
                sub_resources, sub_edges = _filter_resources_and_edges(
                    all_resources, edges, res_set
                )
                if not sub_resources:
                    continue
                env_suffix = env_key or "shared"
                sub_out_path = out_path.with_name(
                    f"{out_path.stem}-{env_suffix}{out_path.suffix}"
                )
                env_label = _format_env_label(env_suffix)
                sub_title = f"{title} - {env_label}"
                _render_icon_diagram_from_terraform(
                    sub_resources,
                    sub_edges,
                    out_path=sub_out_path,
                    title=sub_title,
                    direction=direction,
                    render=render,
                )
            return

        print(
            f"⚠️  Skipping diagram generation: Too many resources ({complexity.node_count} > {max_allowed_nodes})"
        )
        print(f"   This diagram is too complex for the current implementation.")
        print(f"   Consider splitting into smaller, more focused diagrams.")
        return  # Skip diagram generation

    # Auto-detect optimal direction if set to "auto"
    original_direction = direction
    if direction.upper() == "AUTO":
        direction = _determine_optimal_direction(complexity, grouped_data, layout)
        if os.getenv("AUTO_ARCH_DEBUG"):
            print(f"[Auto Direction] Changed from 'auto' to '{direction}'")

    # Calculate optimal spacing parameters
    spacing = _calculate_dynamic_spacing(complexity, render, direction)

    # Determine final spacing values (use auto-calculated or manual values)
    final_pad = spacing["pad"] if render.pad == "auto" else float(render.pad)
    final_nodesep = (
        spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
    )
    final_ranksep = (
        spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
    )

    # Print spacing info for debugging
    if os.getenv("AUTO_ARCH_DEBUG"):
        print(
            f"[Diagram Complexity] Nodes: {complexity.node_count}, Edges: {complexity.edge_count}"
        )
        print(
            f"[Diagram Complexity] Clusters: {complexity.cluster_count}, Depth: {complexity.max_cluster_depth}"
        )
        print(
            f"[Diagram Complexity] Avg edges/node: {complexity.avg_edges_per_node:.2f}"
        )
        print(
            f"[Spacing] pad={final_pad}, nodesep={final_nodesep}, ranksep={final_ranksep}"
        )

    # Graphviz tuning to reduce crossings and avoid oversized icon boxes.
    # Keep PNG/SVG transparent by default; JPEG cannot be transparent.
    desired_bg = (
        (os.getenv("AUTO_ARCH_RENDER_BG") or render.background or "transparent")
        .strip()
        .lower()
    )
    desired_bg = (
        "transparent" if desired_bg not in {"transparent", "white"} else desired_bg
    )
    bgcolor = "white" if outformat in {"jpg", "jpeg"} else desired_bg

    # Legend HTML table for bottom center of canvas with crisp readable typography
    legend_rows = [
        '<TR><TD COLSPAN="6" ALIGN="CENTER"><FONT POINT-SIZE="13" COLOR="#1E293B"><B>Diagram Legend &amp; Connectors</B></FONT></TD></TR>',
        '<TR>',
        '<TD BGCOLOR="#2196F3" WIDTH="32" HEIGHT="6" STYLE="ROUNDED"></TD>',
        '<TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#334155"><B>Data Flow</B></FONT></TD>',
        '<TD BGCOLOR="#9E9E9E" WIDTH="32" HEIGHT="6" STYLE="ROUNDED"></TD>',
        '<TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#334155"><B>Dependency</B></FONT></TD>',
        '<TD BGCOLOR="#F44336" WIDTH="32" HEIGHT="6" STYLE="ROUNDED"></TD>',
        '<TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#334155"><B>Security / Access</B></FONT></TD>',
        '</TR>',
    ]
    if ai_hints:
        legend_rows.append('<TR><TD COLSPAN="6" ALIGN="LEFT"><FONT POINT-SIZE="12" COLOR="#0369A1"><B>AI Architectural Context &amp; Operational Hints</B></FONT></TD></TR>')
        for h in ai_hints[:5]:
            clean_h = html.escape(h.strip())
            legend_rows.append(f'<TR><TD COLSPAN="6" ALIGN="LEFT"><FONT POINT-SIZE="10.5" COLOR="#334155">&#8226; {clean_h}</FONT></TD></TR>')

    legend_html = f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="6" CELLPADDING="6" BGCOLOR="#F8FAFC" STYLE="ROUNDED" COLOR="#CBD5E1">{"".join(legend_rows)}</TABLE>>'

    # Enhanced graph attributes with intelligent edge routing, adaptive DPI
    # (300 small / 220 medium / 180 large layouts) and centered bottom legend
    graph_attr = {
        "bgcolor": bgcolor,
        "dpi": _raster_dpi_for_complexity(complexity.node_count),
        "pad": str(final_pad),
        "nodesep": str(final_nodesep),
        "ranksep": str(final_ranksep),
        "splines": render.edge_routing,
        "concentrate": "true" if render.concentrate else "false",
        "fontname": render.fontname,
        "fontsize": str(render.graph_fontsize),
        "outputorder": "edgesfirst",
        # Advanced overlap and separation controls
        # NOTE: sep/esep are in INCHES. Values above ~1 inch add huge voids
        # inside every nested cluster (compounded per nesting level) and
        # inflate renders to 40-95 MP. Keep them sub-inch.
        "overlap": render.overlap_removal,
        "overlap_scaling": "-4" if render.overlap_removal != "false" else "0",
        "sep": f"+{min(0.75, final_nodesep * 0.5):.2f}",  # cluster margin (inches)
        "esep": f"+{min(0.40, final_nodesep * 0.25):.2f}",  # edge margin (inches)
        "labelloc": "b",
        "labeljust": "c",
        "label": legend_html,
        # Professional edge routing from centers
        "smoothing": "spring" if complexity.edge_count > 10 else "none",
        "mclimit": "2.0",
        "nslimit": "2.0",
        "remincross": "true",
        "compound": "true",
        "newrank": "true",
    }

    # AWS-specific enhancements
    # Use the layout or provider string to check for AWS
    # If needed, pass the resource type as a parameter to this function
    # Example fix: skip this block or use a correct variable
    # Compact icons - imagepos positions icon at top, label at bottom
    node_attr = {
        "fontname": render.fontname,
        "fontsize": str(render.node_fontsize),
        "height": "0.8",
        "width": "0.8",
        "imagepos": "tc",
        "labelloc": "b",
        "imagescale": "true",
    }

    # Base edge attributes with professional center-based connections
    edge_attr = {
        "color": render.edge_color,
        "penwidth": str(render.edge_penwidth),
        "arrowsize": str(render.edge_arrowsize),
        "style": render.edge_style_network,  # Default style
        # Professional edge routing from center of borders
        "constraint": "true",  # Maintain hierarchical structure
        "minlen": "2.0",
        "weight": "1",
        "dir": "forward",
        # Center-based edge connections
        "headclip": "true",  # Clip at node boundary
        "tailclip": "true",  # Clip at node boundary
        "arrowhead": "normal",  # Standard arrowhead
        "arrowtail": "none",
        # Smooth routing
        "decorate": "false",
        "labeldistance": "1.5",
        "labelangle": "0",
    }

    # Resource type to icon mapping (for use elsewhere, not in edge_attr)
    resource_type_icon_map = {
        "aws_glue_catalog_database": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_catalog_table": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_crawler": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_job": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_trigger": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_workflow": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_connection": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_classifier": ("diagrams.aws.analytics", "Glue"),
        "aws_glue_ml_transform": ("diagrams.aws.analytics", "Glue"),
        # AWS AI/ML edge resources
        "aws_sagemaker_notebook_instance": ("diagrams.aws.ml", "SageMaker"),
        "aws_sagemaker_endpoint": ("diagrams.aws.ml", "SageMaker"),
        "aws_sagemaker_model": ("diagrams.aws.ml", "SageMaker"),
        "aws_sagemaker_pipeline": ("diagrams.aws.ml", "SageMaker"),
        "aws_bedrock_agent": ("diagrams.aws.ml", "Bedrock"),
        "aws_bedrock_knowledge_base": ("diagrams.aws.ml", "Bedrock"),
        "aws_textract_document": ("diagrams.aws.ml", "Textract"),
        "aws_comprehend_entity": ("diagrams.aws.ml", "Comprehend"),
        "aws_translate_text": ("diagrams.aws.ml", "Translate"),
        "aws_polly_speech": ("diagrams.aws.ml", "Polly"),
        "aws_rekognition_image": ("diagrams.aws.ml", "Rekognition"),
        "aws_personalize_campaign": ("diagrams.aws.ml", "Personalize"),
        "aws_forecast_dataset": ("diagrams.aws.ml", "Forecast"),
        "aws_lex_bot": ("diagrams.aws.ml", "Lex"),
        "aws_transcribe_job": ("diagrams.aws.ml", "Transcribe"),
        # AWS Blockchain edge resources
        "aws_managed_blockchain_node": ("diagrams.aws.blockchain", "ManagedBlockchain"),
        "aws_qldb_ledger": ("diagrams.aws.blockchain", "QLDB"),
        "aws_amplify_api": ("diagrams.aws.database", "Amplify"),
        "aws_appsync_graphql": ("diagrams.aws.database", "AppSync"),
        # CloudWatch management resources
        "aws_cloudwatch_log_group": ("diagrams.aws.management", "Cloudwatch"),
        "aws_cloudwatch_log_stream": ("diagrams.aws.management", "Cloudwatch"),
        "aws_cloudwatch_metric_alarm": ("diagrams.aws.management", "Cloudwatch"),
        "aws_cloudwatch_event_rule": ("diagrams.aws.management", "Cloudwatch"),
        "aws_cloudwatch_event_target": ("diagrams.aws.management", "Cloudwatch"),
        "aws_cloudwatch_dashboard": ("diagrams.aws.management", "Cloudwatch"),
    }

    region_hierarchy = _build_region_hierarchy(all_resources, edges)

    # Multi-region diagrams are easier to read in provider-first layout.
    effective_layout = "providers" if region_hierarchy else layout

    vpc_hierarchy, compute_subclusters, compute_children, resources_in_vpcs = (
        _build_subgraph_render_map(all_resources, edges)
    )

    with Diagram(
        title,
        show=False,
        direction=direction,
        outformat=diag_outformat,
        filename=render_filename_no_ext,
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ) as diag:
        # Helper function to render provider icon + label cluster
        def render_provider_cluster(provider: str, penwidth: str = "1.2"):
            # Official cloud-provider brand accents on a white canvas.
            accent = _provider_accent(provider) or "#6C757D"
            tint = _provider_tint(provider) or "#FFFFFF"

            provider_label = f"{provider} Cloud"
            provider_cluster_attrs = {
                "bgcolor": tint,
                "fillcolor": tint,  # Ultra-light brand tint fill
                "style": "rounded,filled",
                "penwidth": penwidth,
                "fontsize": "12",
                "fontname": "Helvetica-Bold",
                "color": accent,  # Official brand accent border
                "labelloc": "t",
                "labeljust": "l",
            }
            return Cluster(provider_label, graph_attr=provider_cluster_attrs)

        # Kubernetes/compute cluster visual styling (official Kubernetes blue)
        _k8s_cluster_attrs = {
            "bgcolor": "#EBF1FA",  # Ultra-light Kubernetes blue tint
            "fillcolor": "#EBF1FA",
            "style": "rounded,filled",
            "penwidth": "1.5",
            "color": "#326CE5",  # Official Kubernetes blue border
            "fontsize": "10",
            "fontname": "Helvetica-Bold",
        }

        def render_resource_node(res: str) -> None:
            """Render a single resource node, or a compute cluster with nested children."""
            if res in compute_children:
                return  # will be rendered inside parent's cluster box
            r_type, _name = res.split(".", 1)
            resource_attrs = all_resources.get(res, {})
            Icon = _icon_class_for(r_type, resource_attrs) or \
                _generic_icon_for_kind("compute")

            children = compute_subclusters.get(res, [])
            if children:
                # Render this compute cluster head + its children in a nested box
                with Cluster(_tf_node_label(res), graph_attr=_k8s_cluster_attrs):
                    node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
                    for child_res in sorted(children):
                        child_type = child_res.split(".", 1)[0]
                        child_attrs = all_resources.get(child_res, {})
                        ChildIcon = _icon_class_for(child_type, child_attrs) or \
                            _generic_icon_for_kind("compute")
                        node_by_res[child_res] = _create_node_with_xlabel(
                            ChildIcon, _tf_node_label(child_res)
                        )
            else:
                node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))

        if effective_layout == "providers":
            def _render_provider_contents(
                provider: str,
                categories: dict[str, list[str]],
                allowed_resources: Optional[set[str]] = None,
                parent_cluster: Optional[Any] = None,
            ) -> None:
                provider_vpcs = {
                    vpc: data
                    for vpc, data in vpc_hierarchy.items()
                    if _guess_provider(vpc.split(".", 1)[0]) == provider
                    and (
                        allowed_resources is None
                        or vpc in allowed_resources
                        or any(
                            subnet_name in allowed_resources
                            or any(child in allowed_resources for child in subnet_children)
                            for subnet_name, subnet_children in data.items()
                        )
                    )
                }

                for vpc_name, subnets_dict in sorted(provider_vpcs.items()):
                    vpc_label = _tf_node_label(vpc_name)
                    vpc_attrs = {
                        "bgcolor": render.color_vpc,
                        "fillcolor": render.color_vpc,  # Ultra-light blue tint
                        "style": "rounded,filled",
                        "penwidth": "1.5",
                        "color": "#5DADE2",  # VPC blue border
                        "fontsize": "11",
                        "fontname": "Helvetica-Bold",
                    }
                    with Cluster(vpc_label, graph_attr=vpc_attrs):
                        r_type, _name = vpc_name.split(".", 1)
                        vpc_resource_attrs = all_resources.get(vpc_name, {})
                        Icon = _icon_class_for(
                            r_type, vpc_resource_attrs
                        ) or _generic_icon_for_kind("network")
                        node_by_res[vpc_name] = _create_node_with_xlabel(
                            Icon, _tf_node_label(vpc_name)
                        )

                        for subnet_name, subnet_resources in sorted(
                            subnets_dict.items()
                        ):
                            if subnet_name == "other":
                                for res in sorted(subnet_resources):
                                    if (
                                        allowed_resources is None
                                        or res in allowed_resources
                                    ):
                                        render_resource_node(res)
                            else:
                                if (
                                    allowed_resources is not None
                                    and subnet_name not in allowed_resources
                                    and not any(
                                        res in allowed_resources
                                        for res in subnet_resources
                                    )
                                ):
                                    continue
                                subnet_attrs_dict = all_resources.get(
                                    subnet_name, {}
                                )
                                is_public = _is_public_subnet(
                                    subnet_name, subnet_attrs_dict
                                )
                                subnet_color = (
                                    render.color_public_subnet
                                    if is_public
                                    else render.color_private_subnet
                                )
                                subnet_label = _tf_node_label(subnet_name) + (
                                    " (Public)" if is_public else " (Private)"
                                )
                                subnet_attrs = {
                                    "bgcolor": subnet_color,
                                    "fillcolor": subnet_color,  # Ultra-light tint
                                    "style": "rounded,filled,dashed"
                                    if is_public
                                    else "rounded,filled",
                                    "penwidth": "1.5",
                                    "color": "#28A745"
                                    if is_public
                                    else "#FFC107",  # Green for public, amber for private
                                }
                                with Cluster(subnet_label, graph_attr=subnet_attrs):
                                    r_type, _name = subnet_name.split(".", 1)
                                    subnet_attrs_dict = all_resources.get(subnet_name, {})
                                    Icon = _icon_class_for(r_type, subnet_attrs_dict) or \
                                        _generic_icon_for_kind("network")
                                    node_by_res[subnet_name] = _create_node_with_xlabel(
                                        Icon, _tf_node_label(subnet_name)
                                    )

                                    for res in sorted(subnet_resources):
                                        if (
                                            allowed_resources is None
                                            or res in allowed_resources
                                        ):
                                            render_resource_node(res)

                # Render non-VPC resources into structured category clusters
                categories_with_res = []
                for lane in lanes:
                    res_list = [
                        r
                        for r in (categories.get(lane) or [])
                        if r not in resources_in_vpcs
                        and r not in compute_children
                        and (allowed_resources is None or r in allowed_resources)
                    ]
                    if res_list:
                        categories_with_res.append((lane, res_list))

                if len(categories_with_res) > 1:
                    cat_anchors = []
                    for lane, res_list in categories_with_res:
                        lane_attrs = {
                            "bgcolor": "#FFFFFF",
                            "fillcolor": "#FFFFFF",
                            "style": "rounded,filled",
                            "penwidth": "1.0",
                            "color": "#CBD5E1",
                            "fontsize": "11",
                            "fontname": "Helvetica-Bold",
                        }
                        with Cluster(lane, graph_attr=lane_attrs):
                            for res in sorted(res_list):
                                render_resource_node(res)
                        for res in sorted(res_list):
                            if res in node_by_res and hasattr(node_by_res[res], "_id"):
                                cat_anchors.append(node_by_res[res]._id)
                                break
                    if len(cat_anchors) > 1 and hasattr(diag, "dot") and direction == "LR":
                        for i in range(len(cat_anchors) - 1):
                            diag.dot.edge(cat_anchors[i], cat_anchors[i + 1], style="invis", weight="5")
                else:
                    for lane, res_list in categories_with_res:
                        for res in sorted(res_list):
                            render_resource_node(res)

            def _render_provider_scope(
                provider: str,
                categories: dict[str, list[str]],
                allowed_resources: Optional[set[str]] = None,
            ) -> None:
                with render_provider_cluster(provider, penwidth="1.5") as prov_clust:
                    _render_provider_contents(
                        provider,
                        categories,
                        allowed_resources=allowed_resources,
                        parent_cluster=prov_clust,
                    )

            if region_hierarchy:
                for provider, categories in sorted(grouped_providers.items()):
                    with render_provider_cluster(provider, penwidth="1.5"):
                        provider_resources = {
                            res
                            for category_resources in categories.values()
                            for res in category_resources
                        }
                        rendered_resources: set[str] = set()
                        region_anchor_ids: list[str] = []
                        for region_name, region_resources in sorted(region_hierarchy.items()):
                            scoped_resources = provider_resources.intersection(
                                set(region_resources)
                            )
                            if not scoped_resources:
                                continue
                            region_attrs = {
                                "bgcolor": "#F8F9FA",
                                "fillcolor": "#F8F9FA",
                                "style": "rounded,filled",
                                "penwidth": "1.5",
                                "color": "#6C757D",
                                "fontsize": "13",
                                "fontname": "Helvetica-Bold",
                            }
                            with Cluster(
                                f"Region: {region_name}", graph_attr=region_attrs
                            ) as reg_clust:
                                _render_provider_contents(
                                    provider,
                                    categories,
                                    allowed_resources=scoped_resources,
                                    parent_cluster=reg_clust,
                                )
                            for r in sorted(scoped_resources):
                                if r in node_by_res and hasattr(node_by_res[r], "_id"):
                                    region_anchor_ids.append(node_by_res[r]._id)
                                    break
                            rendered_resources.update(scoped_resources)

                        if len(region_anchor_ids) > 1:
                            _align_provider_clusters(diag.dot, region_anchor_ids, direction=direction, max_per_row=2)
                        # If a provider has resources without region hints, wrap into a clean Global / Shared Services cluster
                        unscoped_resources = provider_resources - rendered_resources
                        if unscoped_resources:
                            shared_attrs = {
                                "bgcolor": "#F8F9FA",
                                "fillcolor": "#F8F9FA",
                                "style": "rounded,filled",
                                "penwidth": "1.2",
                                "color": "#78909C",
                                "fontsize": "12",
                                "fontname": "Helvetica-Bold",
                            }
                            with Cluster("Global / Shared Services", graph_attr=shared_attrs) as shared_clust:
                                _render_provider_contents(
                                    provider,
                                    categories,
                                    allowed_resources=unscoped_resources,
                                    parent_cluster=shared_clust,
                                )
            else:
                provider_anchor_ids: list[str] = []
                for provider, categories in sorted(grouped_providers.items()):
                    _render_provider_scope(provider, categories)
                    for cat_resources in categories.values():
                        found = False
                        for r in sorted(cat_resources):
                            if r in node_by_res and hasattr(node_by_res[r], "_id"):
                                provider_anchor_ids.append(node_by_res[r]._id)
                                found = True
                                break
                        if found:
                            break
                if len(provider_anchor_ids) > 1:
                    _align_provider_clusters(diag.dot, provider_anchor_ids, direction=direction, max_per_row=2)
        else:
            # Category lanes (industry-friendly default): Network -> Security -> Compute -> Data...
            for lane in lanes:
                providers = grouped_lanes.get(lane) or {}
                if not providers:
                    continue
                # Single-provider lanes carry that provider's official accent;
                # mixed-provider lanes stay neutral on the white canvas.
                lane_provider_names = sorted(providers.keys())
                lane_accent = (
                    _provider_accent(lane_provider_names[0])
                    if len(lane_provider_names) == 1
                    else None
                )
                lane_tint = (
                    _provider_tint(lane_provider_names[0])
                    if len(lane_provider_names) == 1
                    else None
                )
                lane_cluster_attrs = {
                    "bgcolor": "#FFFFFF",  # White canvas
                    "fillcolor": lane_tint or "#FFFFFF",
                    "style": "rounded,filled",
                    "penwidth": "1.2",
                    "fontsize": "14",
                    "fontname": "Helvetica-Bold",
                    "color": lane_accent or "#CCCCCC",  # Brand accent border
                }
                with Cluster(lane, graph_attr=lane_cluster_attrs):
                    for provider, resources in sorted(providers.items()):
                        # Filter out resources already in VPCs
                        provider_resources = [
                            r for r in resources if r not in resources_in_vpcs
                        ]

                        # Get VPCs for this provider in this lane
                        provider_vpcs = {
                            vpc: data
                            for vpc, data in vpc_hierarchy.items()
                            if vpc in resources
                            and _guess_provider(vpc.split(".", 1)[0]) == provider
                        }

                        if not provider_resources and not provider_vpcs:
                            continue

                        with render_provider_cluster(provider, penwidth="1.0"):
                            # First render VPCs with their hierarchies
                            for vpc_name, subnets_dict in sorted(provider_vpcs.items()):
                                vpc_label = _tf_node_label(vpc_name)
                                vpc_attrs = {
                                    "bgcolor": render.color_vpc,
                                    "fillcolor": render.color_vpc,  # Ultra-light blue tint
                                    "style": "rounded,filled",
                                    "penwidth": "1.5",
                                    "color": "#5DADE2",  # VPC blue border
                                    "fontsize": "11",
                                    "fontname": "Helvetica-Bold",
                                }
                                with Cluster(vpc_label, graph_attr=vpc_attrs):
                                    r_type, _name = vpc_name.split(".", 1)
                                    vpc_attrs_dict = all_resources.get(vpc_name, {})
                                    Icon = _icon_class_for(r_type, vpc_attrs_dict) or \
                                        _generic_icon_for_kind("network")
                                    node_by_res[vpc_name] = _create_node_with_xlabel(
                                        Icon, _tf_node_label(vpc_name)
                                    )

                                    # Render subnets within VPC
                                    for subnet_name, subnet_resources in sorted(
                                        subnets_dict.items()
                                    ):
                                        if subnet_name == "other":
                                            # VPC-level resources
                                            for res in sorted(subnet_resources):
                                                render_resource_node(res)
                                        else:
                                            # Subnet cluster
                                            subnet_attrs_dict = all_resources.get(
                                                subnet_name, {}
                                            )
                                            is_public = _is_public_subnet(
                                                subnet_name, subnet_attrs_dict
                                            )
                                            subnet_color = (
                                                render.color_public_subnet
                                                if is_public
                                                else render.color_private_subnet
                                            )
                                            subnet_label = _tf_node_label(
                                                subnet_name
                                            ) + (
                                                " (Public)"
                                                if is_public
                                                else " (Private)"
                                            )
                                            subnet_attrs = {
                                                "bgcolor": subnet_color,
                                                "fillcolor": subnet_color,  # Ultra-light tint
                                                "style": "rounded,filled,dashed"
                                                if is_public
                                                else "rounded,filled",
                                                "penwidth": "1.5",
                                                "color": "#28A745"
                                                if is_public
                                                else "#FFC107",  # Green for public, amber for private
                                            }
                                            with Cluster(
                                                subnet_label, graph_attr=subnet_attrs
                                            ):
                                                r_type, _name = subnet_name.split(
                                                    ".", 1
                                                )
                                                Icon = _icon_class_for(
                                                    r_type, subnet_attrs_dict
                                                ) or _generic_icon_for_kind("network")
                                                node_by_res[subnet_name] = (
                                                    _create_node_with_xlabel(
                                                        Icon,
                                                        _tf_node_label(subnet_name),
                                                    )
                                                )

                                                # Resources in subnet
                                                for res in sorted(subnet_resources):
                                                    render_resource_node(res)

                            # Then render remaining resources not in VPCs
                            for res in sorted(provider_resources):
                                if res not in compute_children:
                                    render_resource_node(res)

        for src_res, dst_res in sorted(edges):
            if src_res in node_by_res and dst_res in node_by_res:
                # Detect edge type and apply intelligent styling
                edge_type = _detect_edge_type(src_res, dst_res, all_resources)
                edge_style_attrs = _get_edge_style_attrs(edge_type, render)

                # Try to apply custom styling using Edge object
                try:
                    from diagrams import Edge

                    (
                        node_by_res[src_res]
                        >> Edge(**edge_style_attrs)
                        >> node_by_res[dst_res]
                    )
                except (ImportError, TypeError, AttributeError):
                    # Fallback to simple connection if Edge styling not supported
                    node_by_res[src_res] >> node_by_res[dst_res]



    # Cap oversized rasters before SVG embedding / JPEG conversion
    if outformat in {"png", "jpg", "jpeg"}:
        _downscale_raster_if_needed(Path(render_filename_no_ext + ".png"))
        _downscale_raster_if_needed(out_path)

    # Embed images in SVG after the diagram has been generated
    if outformat == "svg":
        _embed_images_in_svg(out_path)

    # Convert high-resolution PNG to pristine 300 DPI JPEG with Pillow
    if outformat in {"jpg", "jpeg"}:
        try:
            from PIL import Image

            tmp_png = Path(render_filename_no_ext + ".png")
            if tmp_png.exists():
                with Image.open(tmp_png) as img:
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img.paste(img)
                    rgb_img.save(out_path, format="JPEG", quality=95, subsampling=0)
                tmp_png.unlink(missing_ok=True)
        except Exception:
            pass


def _static_terraform_mermaid(
    files: list[Path],
    direction: str,
    limits: Limits,
    parsed_inputs: tuple[
        dict[str, dict[str, Any]],
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
    ]
    | None = None,
) -> tuple[str, str, str]:
    if hcl2 is None:
        raise RuntimeError(
            "Missing dependency python-hcl2. Install it to enable Terraform static diagrams."
        )

    if parsed_inputs is None:
        parsed_inputs = _terraform_resources_from_files(files, limits, Path.cwd())
    all_resources, module_ref_maps, env_ref_maps = parsed_inputs

    if not all_resources:
        raise RuntimeError("No Terraform resources parsed from the changed files.")

    node_id_by_res: dict[str, str] = {
        res: _safe_node_id(f"tf_{res}") for res in all_resources.keys()
    }
    groups: dict[str, dict[str, list[str]]] = {}
    edges: set[tuple[str, str]] = set()

    env_groups = _group_resources_by_env(all_resources)
    use_env_grouping = len(env_groups) > 1

    for res, attrs in all_resources.items():
        r_type, _name = res.split(".", 1)
        provider = _guess_provider(r_type)
        env = _normalize_env_name(attrs.get("_auto_arch_env")) if attrs else None
        env_key = env or "shared"
        if use_env_grouping:
            groups.setdefault(env_key, {}).setdefault(provider, []).append(res)
        else:
            groups.setdefault("_all", {}).setdefault(provider, []).append(res)

        refs = set()
        refs |= _extract_tf_resource_refs(attrs)
        depends_on = attrs.get("depends_on")
        if depends_on is not None:
            refs |= _extract_tf_resource_refs(depends_on)
        module_prefix = _module_prefix_for_resource(res)
        if module_prefix and module_prefix in module_ref_maps:
            ref_map = module_ref_maps[module_prefix]
            refs = {ref_map.get(r, r) for r in refs}
        if env and env in env_ref_maps:
            env_map = env_ref_maps[env]
            refs = {env_map.get(r, r) for r in refs}

        for ref in sorted(refs):
            if ref == res:
                continue
            if ref in all_resources:
                edges.add((node_id_by_res[ref], node_id_by_res[res]))

    if not edges:
        fallback_edges = _fallback_chain_edges(all_resources)
        if fallback_edges:
            print("[WARN] No explicit Terraform references found; using heuristic edges.")
        for src, dst in sorted(fallback_edges):
            if src in node_id_by_res and dst in node_id_by_res:
                edges.add((node_id_by_res[src], node_id_by_res[dst]))

    raw_edges: set[tuple[str, str]] = set()
    for src, dst in edges:
        src_res = next((res for res, node_id in node_id_by_res.items() if node_id == src), None)
        dst_res = next((res for res, node_id in node_id_by_res.items() if node_id == dst), None)
        if src_res and dst_res:
            raw_edges.add((src_res, dst_res))

    raw_edges = _filter_architectural_edges(all_resources, raw_edges)
    edges = {
        (node_id_by_res[src], node_id_by_res[dst])
        for src, dst in raw_edges
        if src in node_id_by_res and dst in node_id_by_res
    }

    vpc_hierarchy, compute_subclusters, compute_children, resources_in_vpcs = (
        _build_subgraph_render_map(all_resources, raw_edges)
    )

    lines: list[str] = [f"flowchart {direction}"]

    def _append_node(lines_out: list[str], res: str, indent: str) -> None:
        label = all_resources.get(res, {}).get("_auto_arch_logical_id") or res
        lines_out.append(f'{indent}{node_id_by_res[res]}["{label}"]')

    def _append_resource(lines_out: list[str], res: str, indent: str) -> None:
        if res in compute_children:
            return
        children = sorted(compute_subclusters.get(res, []))
        if children:
            cluster_id = _safe_node_id(f"cluster_{res}")
            lines_out.append(f"{indent}subgraph {cluster_id}[{_tf_node_label(res)}]")
            _append_node(lines_out, res, indent + "  ")
            for child in children:
                _append_node(lines_out, child, indent + "  ")
            lines_out.append(f"{indent}end")
            return
        _append_node(lines_out, res, indent)

    for env_key, providers in sorted(groups.items()):
        if use_env_grouping:
            env_label = _format_env_label(env_key)
            env_id = _safe_node_id(f"env_{env_key}")
            lines.append(f"subgraph {env_id}[{env_label}]")
        for provider, resources in sorted(providers.items()):
            provider_id = _safe_node_id(f"{env_key}_{provider}")
            provider_indent = "  " if use_env_grouping else ""
            lines.append(f"{provider_indent}subgraph {provider_id}[{provider}]")

            provider_vpcs = {
                vpc: data
                for vpc, data in vpc_hierarchy.items()
                if _guess_provider(vpc.split(".", 1)[0]) == provider
            }

            for vpc_name, subnets_dict in sorted(provider_vpcs.items()):
                vpc_indent = provider_indent + "  "
                vpc_id = _safe_node_id(f"vpc_{vpc_name}")
                lines.append(f"{vpc_indent}subgraph {vpc_id}[{_tf_node_label(vpc_name)}]")
                _append_node(lines, vpc_name, vpc_indent + "  ")

                for subnet_name, subnet_resources in sorted(subnets_dict.items()):
                    if subnet_name == "other":
                        for res in sorted(subnet_resources):
                            _append_resource(lines, res, vpc_indent + "  ")
                        continue

                    subnet_indent = vpc_indent + "  "
                    subnet_attrs = all_resources.get(subnet_name, {})
                    subnet_id = _safe_node_id(f"subnet_{subnet_name}")
                    subnet_label = _tf_node_label(subnet_name) + (
                        " (Public)"
                        if _is_public_subnet(subnet_name, subnet_attrs)
                        else " (Private)"
                    )
                    lines.append(f"{subnet_indent}subgraph {subnet_id}[{subnet_label}]")
                    _append_node(lines, subnet_name, subnet_indent + "  ")
                    for res in sorted(subnet_resources):
                        _append_resource(lines, res, subnet_indent + "  ")
                    lines.append(f"{subnet_indent}end")

                lines.append(f"{vpc_indent}end")

            for res in sorted(resources):
                if res in resources_in_vpcs or res in compute_children:
                    continue
                _append_resource(lines, res, provider_indent + "  ")

            lines.append(f"{provider_indent}end")
        if use_env_grouping:
            lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{src} --> {dst}")

    mermaid = "\n".join(lines) + "\n"
    summary = (
        "Generated a dependency-oriented Terraform diagram from changed resources."
    )
    assumptions = "Connections represent inferred references (including depends_on and attribute references)."
    if not edges:
        assumptions = "No explicit references found; connections are heuristic to show grouping."
    return mermaid, summary, assumptions


def _static_terraform_graph(
    files: list[Path],
    limits: Limits,
    parsed_inputs: tuple[
        dict[str, dict[str, Any]],
        dict[str, dict[str, str]],
        dict[str, dict[str, str]],
    ]
    | None = None,
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    if hcl2 is None:
        raise RuntimeError(
            "Missing dependency python-hcl2. Install it to enable Terraform static diagrams."
        )

    if parsed_inputs is None:
        parsed_inputs = _terraform_resources_from_files(files, limits, Path.cwd())
    all_resources, module_ref_maps, env_ref_maps = parsed_inputs

    if not all_resources:
        raise RuntimeError("No Terraform resources parsed from the changed files.")

    edges: set[tuple[str, str]] = set()
    for res, attrs in all_resources.items():
        refs = set()
        refs |= _extract_tf_resource_refs(attrs)
        depends_on = attrs.get("depends_on")
        if depends_on is not None:
            refs |= _extract_tf_resource_refs(depends_on)
        module_prefix = _module_prefix_for_resource(res)
        if module_prefix and module_prefix in module_ref_maps:
            ref_map = module_ref_maps[module_prefix]
            refs = {ref_map.get(r, r) for r in refs}
        env = _normalize_env_name(attrs.get("_auto_arch_env")) if attrs else None
        if env and env in env_ref_maps:
            env_map = env_ref_maps[env]
            refs = {env_map.get(r, r) for r in refs}
        for ref in sorted(refs):
            if ref in all_resources and ref != res:
                edges.add((ref, res))
    if not edges:
        edges = _fallback_chain_edges(all_resources)
        if edges:
            print("[WARN] No explicit Terraform references found; using heuristic edges.")
    return all_resources, edges


# CloudFormation intrinsic function handlers for YAML
def _cfn_tag_constructor(
    loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node
) -> dict[str, Any]:
    """Generic constructor for CloudFormation intrinsic functions like !Ref, !GetAtt, etc."""
    # Convert tag like '!Ref' to 'Ref', '!GetAtt' to 'Fn::GetAtt'
    if tag_suffix == "Ref":
        key = "Ref"
    elif tag_suffix.startswith("Fn::"):
        key = tag_suffix
    else:
        key = f"Fn::{tag_suffix}"

    # Handle scalar nodes
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
        return {key: value}
    # Handle sequence nodes
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
        return {key: value}
    # Handle mapping nodes
    elif isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node)
        return {key: value}
    else:
        return {key: None}


def _create_cfn_loader() -> type[yaml.SafeLoader]:
    """Create a custom YAML loader that handles CloudFormation intrinsic functions."""
    loader = type("CFNLoader", (yaml.SafeLoader,), {})

    # Register constructors for common CloudFormation intrinsic functions
    cfn_tags = [
        "Ref",
        "GetAtt",
        "Join",
        "Sub",
        "Select",
        "Split",
        "GetAZs",
        "Base64",
        "ImportValue",
        "FindInMap",
        "Cidr",
        "Transform",
        "If",
        "Equals",
        "Not",
        "And",
        "Or",
        "Condition",
    ]

    for tag in cfn_tags:
        yaml_tag = f"!{tag}"
        loader.add_constructor(
            yaml_tag, lambda l, n, t=tag: _cfn_tag_constructor(l, t, n)
        )

    # Also handle the Fn:: prefix forms
    for tag in cfn_tags:
        if tag != "Ref":  # Ref doesn't have Fn:: form
            yaml_tag = f"!Fn::{tag}"
            loader.add_constructor(
                yaml_tag, lambda l, n, t=f"Fn::{tag}": _cfn_tag_constructor(l, t, n)
            )

    return loader


def _extract_cfn_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    for item in _walk(value):
        if isinstance(item, dict):
            if "Ref" in item and isinstance(item["Ref"], str):
                refs.add(item["Ref"])
            if "Fn::GetAtt" in item:
                ga = item["Fn::GetAtt"]
                if isinstance(ga, list) and ga and isinstance(ga[0], str):
                    refs.add(ga[0])
                if isinstance(ga, str):
                    # 'Resource.Attribute'
                    refs.add(ga.split(".", 1)[0])
            if "Fn::Sub" in item and isinstance(item["Fn::Sub"], str):
                # ${LogicalId} or ${LogicalId.Attribute}
                for m in re.finditer(
                    r"\$\{([A-Za-z0-9]+)(?:\.[^\}]+)?\}", item["Fn::Sub"]
                ):
                    refs.add(m.group(1))
        elif isinstance(item, str):
            for m in re.finditer(r"\$\{([A-Za-z0-9]+)(?:\.[^\}]+)?\}", item):
                refs.add(m.group(1))
    return refs


def _static_cloudformation_mermaid(
    files: list[Path], direction: str, limits: Limits
) -> tuple[str, str, str]:
    templates: list[dict[str, Any]] = []
    for f in files:
        name = f.name.lower()
        if not (
            name.endswith(".cfn.yml")
            or name.endswith(".cfn.yaml")
            or name.endswith(".cfn.json")
            or name in {"template.yml", "template.yaml"}
        ):
            continue

        raw = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
        try:
            if f.suffix.lower() == ".json" or name.endswith(".cfn.json"):
                templates.append(json.loads(raw))
            else:
                # Use custom loader for CloudFormation YAML with intrinsic functions
                # CFNLoader extends SafeLoader - safe for untrusted input
                CFNLoader = _create_cfn_loader()
                templates.append(yaml.load(raw, Loader=CFNLoader) or {})  # nosec B506
        except Exception:  # nosec B112
            continue

    if not templates:
        raise RuntimeError("No CloudFormation templates parsed from changed files.")

    resources: dict[str, dict[str, Any]] = {}
    for t in templates:
        r = t.get("Resources")
        if isinstance(r, dict):
            for logical_id, body in r.items():
                if isinstance(body, dict):
                    resources[logical_id] = body

    if not resources:
        raise RuntimeError("No CloudFormation Resources found in parsed templates.")

    node_id_by_res: dict[str, str] = {
        rid: _safe_node_id(f"cfn_{rid}") for rid in resources.keys()
    }
    edges: set[tuple[str, str]] = set()

    # Group resources by category for better alignment
    groups: dict[str, list[str]] = {
        "Network": [],
        "Security": [],
        "Compute": [],
        "Data": [],
        "Storage": [],
        "Integration": [],
        "Management": [],
        "Other": [],
    }

    def _cfn_category(service: str) -> str:
        """Categorize CloudFormation services for better diagram organization."""
        service_lower = service.lower()
        if any(
            k in service_lower
            for k in [
                "vpc",
                "subnet",
                "route",
                "gateway",
                "nat",
                "vpn",
                "elb",
                "alb",
                "nlb",
                "cloudfront",
                "cdn",
            ]
        ):
            return "Network"
        if any(
            k in service_lower
            for k in [
                "iam",
                "kms",
                "secrets",
                "cloudtrail",
                "guardduty",
                "waf",
                "security",
            ]
        ):
            return "Security"
        if any(
            k in service_lower
            for k in ["lambda", "ec2", "instance", "eks", "ecs", "batch", "function"]
        ):
            return "Compute"
        if any(
            k in service_lower
            for k in [
                "rds",
                "dynamodb",
                "aurora",
                "neptune",
                "redshift",
                "sql",
                "database",
                "glue",
            ]
        ):
            return "Data"
        if any(
            k in service_lower
            for k in ["s3", "ebs", "efs", "fsx", "storage", "bucket", "volume"]
        ):
            return "Storage"
        if any(
            k in service_lower
            for k in [
                "sqs",
                "sns",
                "kinesis",
                "eventbridge",
                "api",
                "sns",
                "sqs",
                "step",
            ]
        ):
            return "Integration"
        if any(
            k in service_lower
            for k in ["cloudwatch", "xray", "trustedadvisor", "monitor", "logs"]
        ):
            return "Management"
        return "Other"

    for rid, body in resources.items():
        rtype = body.get("Type")
        service = "CFN"
        if isinstance(rtype, str) and "::" in rtype:
            parts = rtype.split("::")
            if len(parts) >= 2:
                service = parts[1]

        # Categorize the service
        category = _cfn_category(service)
        groups[category].append(rid)

        depends_on = body.get("DependsOn")
        refs = _extract_cfn_refs(body.get("Properties"))
        if isinstance(depends_on, str):
            refs.add(depends_on)
        elif isinstance(depends_on, list):
            refs |= {x for x in depends_on if isinstance(x, str)}

        for ref in sorted(refs):
            if ref in resources and ref != rid:
                edges.add((node_id_by_res[ref], node_id_by_res[rid]))

    lines: list[str] = [f"flowchart {direction}"]

    # Create subgraphs by category for better alignment
    for category, rids in sorted(groups.items()):
        if not rids:  # Skip empty categories
            continue
        lines.append(f"subgraph {category.replace(' ', '')}[{category}]")
        for rid in sorted(rids):
            rtype = resources[rid].get("Type")
            # Show service name instead of full type for cleaner display
            service_name = (
                rtype.split("::")[-1]
                if isinstance(rtype, str) and "::" in rtype
                else rtype
            )
            label = f"{rid}\\n{service_name}" if service_name else rid
            lines.append(f'  {node_id_by_res[rid]}["{label}"]')
        lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{src} --> {dst}")

    mermaid = "\n".join(lines) + "\n"
    summary = (
        "Generated a dependency-oriented CloudFormation diagram from changed resources."
    )
    assumptions = (
        "Connections represent inferred references via Ref/GetAtt/Sub and DependsOn."
    )
    return mermaid, summary, assumptions


def _static_cloudformation_graph(
    files: list[Path], limits: Limits
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    templates: list[dict[str, Any]] = []
    for f in files:
        name = f.name.lower()
        if not (
            name.endswith(".cfn.yml")
            or name.endswith(".cfn.yaml")
            or name.endswith(".cfn.json")
            or name in {"template.yml", "template.yaml"}
        ):
            continue

        raw = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
        try:
            if f.suffix.lower() == ".json" or name.endswith(".cfn.json"):
                templates.append(json.loads(raw))
            else:
                # Use custom loader for CloudFormation YAML with intrinsic functions
                # CFNLoader extends SafeLoader - safe for untrusted input
                CFNLoader = _create_cfn_loader()
                templates.append(yaml.load(raw, Loader=CFNLoader) or {})  # nosec B506
        except Exception:  # nosec B112
            continue

    if not templates:
        raise RuntimeError("No CloudFormation templates parsed from the changed files.")

    resources: dict[str, dict[str, Any]] = {}
    for t in templates:
        r = t.get("Resources")
        if isinstance(r, dict):
            for logical_id, body in r.items():
                if isinstance(body, dict):
                    resources[logical_id] = body

    if not resources:
        raise RuntimeError("No CloudFormation Resources found in parsed templates.")

    edges: set[tuple[str, str]] = set()
    for rid, body in resources.items():
        depends_on = body.get("DependsOn")
        refs = _extract_cfn_refs(body.get("Properties"))
        if isinstance(depends_on, str):
            refs.add(depends_on)
        elif isinstance(depends_on, list):
            refs |= {x for x in depends_on if isinstance(x, str)}
        for ref in sorted(refs):
            if ref in resources and ref != rid:
                edges.add((ref, rid))

    return resources, edges


def _static_bicep_graph(
    files: list[Path], limits: Limits
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    resources: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()

    # Very small, best-effort parser:
    # - resource <symbol> '<type>@<api>' = { ... }
    # - dependsOn: [ <symbol> ... ]
    # - parent: <symbol>
    res_re = re.compile(
        r"^\s*resource\s+(?P<sym>[A-Za-z_][A-Za-z0-9_]*)\s+'(?P<type>[^']+)'",
        re.IGNORECASE,
    )
    sym_ref_re = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

    for f in files:
        if f.suffix.lower() != ".bicep":
            continue
        raw = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
        lines = raw.splitlines()

        current_sym: str | None = None
        bracket_depth = 0
        in_depends = False

        for line in lines:
            m = res_re.match(line)
            if m:
                current_sym = m.group("sym")
                rtype = m.group("type")
                resources[current_sym] = {
                    "Type": rtype.split("@", 1)[0],
                    "RawType": rtype,
                    "Provider": "azure",
                    "Kind": "bicep",
                }
                bracket_depth = 0

            # Track basic block depth so we only attach dependsOn/parent within a resource body.
            bracket_depth += line.count("{") - line.count("}")
            if current_sym and bracket_depth <= 0 and line.strip().startswith("}"):
                current_sym = None
                continue

            if not current_sym:
                continue

            # parent: someSymbol
            if re.search(r"^\s*parent\s*:\s*", line):
                after = line.split(":", 1)[1]
                mm = sym_ref_re.search(after)
                if mm:
                    parent = mm.group(1)
                    if parent in resources and parent != current_sym:
                        edges.add((parent, current_sym))

            # dependsOn: [ ... ] (often multi-line)
            if re.search(r"^\s*dependsOn\s*:\s*\[", line):
                in_depends = True

            if in_depends:
                refs = set(sym_ref_re.findall(line))
                for ref in sorted(refs):
                    if ref in resources and ref != current_sym:
                        edges.add((ref, current_sym))
                if "]" in line:
                    in_depends = False

    if not resources:
        raise RuntimeError("No Bicep resources parsed from the changed files.")
    return resources, edges


def _pulumi_yaml_extract_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    for item in _walk(value):
        if isinstance(item, str):
            for m in re.finditer(r"\$\{([A-Za-z0-9_-]+)\.[^\}]+\}", item):
                refs.add(m.group(1))
    return refs


def _static_pulumi_yaml_graph(
    files: list[Path], limits: Limits
) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    stacks: list[dict[str, Any]] = []
    for f in files:
        name = f.name
        if (
            name not in {"Pulumi.yaml", "Pulumi.yml"}
            and not name.lower().endswith(".pulumi.yaml")
            and not name.lower().endswith(".pulumi.yml")
        ):
            continue
        raw = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
        try:
            stacks.append(yaml.safe_load(raw) or {})
        except Exception:  # nosec B112
            continue

    if not stacks:
        raise RuntimeError("No Pulumi YAML stacks parsed from the changed files.")

    resources: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()

    for s in stacks:
        r = s.get("resources")
        if not isinstance(r, dict):
            continue
        for name, body in r.items():
            if not isinstance(name, str) or not isinstance(body, dict):
                continue
            rtype = body.get("type")
            provider = None
            if isinstance(rtype, str) and ":" in rtype:
                provider = rtype.split(":", 1)[0]
            resources[name] = {
                "Type": rtype,
                "Provider": (provider or "pulumi"),
                "Kind": "pulumi",
                "Body": body,
            }

    if not resources:
        raise RuntimeError("No Pulumi resources found in parsed YAML stacks.")

    for name, body in resources.items():
        b = body.get("Body") or {}
        options = b.get("options") if isinstance(b, dict) else None
        depends_on = None
        if isinstance(options, dict):
            depends_on = options.get("dependsOn")
        refs = set()
        refs |= _pulumi_yaml_extract_refs(
            b.get("properties") if isinstance(b, dict) else None
        )
        if isinstance(depends_on, str):
            refs.add(depends_on)
        elif isinstance(depends_on, list):
            refs |= {x for x in depends_on if isinstance(x, str)}

        for ref in sorted(refs):
            if ref in resources and ref != name:
                edges.add((ref, name))

    return resources, edges


def _static_bicep_mermaid(
    files: list[Path], direction: str, limits: Limits
) -> tuple[str, str, str]:
    resources, edges = _static_bicep_graph(files, limits)
    node_id_by_res: dict[str, str] = {
        rid: _safe_node_id(f"bicep_{rid}") for rid in resources.keys()
    }

    lines: list[str] = [f"flowchart {direction}", "subgraph Azure[Azure]"]
    for rid in sorted(resources.keys()):
        rtype = resources[rid].get("Type")
        label = f"{rid}\\n{rtype}" if isinstance(rtype, str) else rid
        lines.append(f'  {node_id_by_res[rid]}["{label}"]')
    lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{node_id_by_res[src]} --> {node_id_by_res[dst]}")

    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a best-effort Bicep dependency diagram (dependsOn/parent)."
    assumptions = "Connections represent explicit dependsOn/parent references; implicit property references are not fully resolved."
    return mermaid, summary, assumptions


def _static_pulumi_yaml_mermaid(
    files: list[Path], direction: str, limits: Limits
) -> tuple[str, str, str]:
    resources, edges = _static_pulumi_yaml_graph(files, limits)
    node_id_by_res: dict[str, str] = {
        rid: _safe_node_id(f"pulumi_{rid}") for rid in resources.keys()
    }
    groups: dict[str, list[str]] = {}
    for rid, body in resources.items():
        provider = body.get("Provider")
        g = provider if isinstance(provider, str) else "pulumi"
        groups.setdefault(g, []).append(rid)
    lines: list[str] = [f"flowchart {direction}"]
    for g, rids in sorted(groups.items()):
        title = g.upper() if g.islower() else g
        lines.append(f"subgraph {title}[{title}]")
        for rid in sorted(rids):
            rtype = resources[rid].get("Type")
            label = f"{rid}\\n{rtype}" if isinstance(rtype, str) else rid
            lines.append(f'  {node_id_by_res[rid]}["{label}"]')
        lines.append("end")
    for src, dst in sorted(edges):
        lines.append(f"{node_id_by_res[src]} --> {node_id_by_res[dst]}")
    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions."
    assumptions = "Connections represent options.dependsOn and ${resource.property} references in YAML."
    return mermaid, summary, assumptions


def _create_cfn_node(
    rid: str, cfn_resources: dict, node_by_res: dict, render: Any
) -> None:
    """Create a CloudFormation node with proper icon mapping."""
    resource_body = cfn_resources[rid]
    resource_type = resource_body.get("Type", "")
    terraform_resource_name = _cfn_to_terraform_resource_name(resource_type)

    Icon = _icon_class_for(terraform_resource_name)
    if not Icon:
        # Use service-specific icons
        if "S3" in resource_type:
            Icon = _icon_class_for("aws_s3_bucket")
        elif "WAF" in resource_type:
            Icon = _icon_class_for("aws_wafv2_web_acl")
        elif "CloudFront" in resource_type:
            Icon = _icon_class_for("aws_cloudfront_distribution")
        else:
            # Extract category from resource for generic icon
            category = "Other"
            if "::" in resource_type:
                service = resource_type.split("::")[1].lower()
                category_map = {
                    "s3": "Storage",
                    "wafv2": "Security",
                    "cloudfront": "Network",
                    "iam": "Security",
                    "lambda": "Compute",
                    "apigateway": "Other",
                    "logs": "Other",
                }
                category = category_map.get(service, "Other")
            Icon = _generic_icon_for_kind(category.lower())

    # Use professional node creation like Terraform
    if Icon:
        node_by_res[rid] = _create_node_with_xlabel(
            Icon, _wrap_text(rid, max_width=20, max_lines=2)
        )
    else:
        # Fallback to text node with professional styling
        from diagrams.generic.blank import Blank

        node_by_res[rid] = Blank(
            _wrap_text(rid, max_width=20, max_lines=2), height="1.2", labelloc="b"
        )


def _cfn_to_terraform_resource_name(cfn_resource_type: str) -> str:
    """Convert CloudFormation resource type to Terraform-style resource name for icon lookup."""
    if not cfn_resource_type or "::" not in cfn_resource_type:
        return ""

    # Extract service and resource from AWS::Service::Resource, Azure::Service::Resource, etc.
    parts = cfn_resource_type.split("::")
    if len(parts) < 3:
        return ""

    provider = parts[0].lower()  # AWS, Azure, Google
    service = parts[1].lower()
    resource = parts[2].lower()

    # Map CloudFormation resource types to Terraform resource names
    cfn_to_tf_map = {
        # AWS mappings
        ("aws", "s3", "bucket"): "aws_s3_bucket",
        ("aws", "s3", "bucketpublicaccessblock"): "aws_s3_bucket_public_access_block",
        ("aws", "wafv2", "webacl"): "aws_wafv2_web_acl",
        ("aws", "cloudfront", "distribution"): "aws_cloudfront_distribution",
        (
            "aws",
            "cloudfront",
            "originaccesscontrol",
        ): "aws_cloudfront_origin_access_control",
        ("aws", "iam", "role"): "aws_iam_role",
        ("aws", "lambda", "function"): "aws_lambda_function",
        ("aws", "apigateway", "restapi"): "aws_api_gateway_rest_api",
        ("aws", "dynamodb", "table"): "aws_dynamodb_table",
        ("aws", "rds", "dbinstance"): "aws_db_instance",
        ("aws", "ec2", "instance"): "aws_instance",
        ("aws", "vpc", "vpc"): "aws_vpc",
        ("aws", "vpc", "subnet"): "aws_subnet",
        ("aws", "elb", "loadbalancer"): "aws_lb",
        ("aws", "logs", "loggroup"): "aws_cloudwatch_log_group",
        # Azure mappings (Azure CloudFormation uses different service names)
        ("azure", "storage", "storageaccount"): "azurerm_storage_account",
        ("azure", "network", "virtualnetwork"): "azurerm_virtual_network",
        ("azure", "network", "subnet"): "azurerm_subnet",
        ("azure", "network", "networksecuritygroup"): "azurerm_network_security_group",
        ("azure", "network", "publicip"): "azurerm_public_ip",
        ("azure", "network", "applicationgateway"): "azurerm_application_gateway",
        (
            "azure",
            "containerservice",
            "kubernetescluster",
        ): "azurerm_kubernetes_cluster",
        ("azure", "containerregistry", "registry"): "azurerm_container_registry",
        ("azure", "cosmosdb", "account"): "azurerm_cosmosdb_account",
        ("azure", "redis", "cache"): "azurerm_redis_cache",
        (
            "azure",
            "monitor",
            "loganalyticsworkspace",
        ): "azurerm_log_analytics_workspace",
        ("azure", "appservice", "functionapp"): "azurerm_function_app",
        ("azure", "appservice", "plan"): "azurerm_app_service_plan",
        ("azure", "resources", "resourcegroup"): "azurerm_resource_group",
        # GCP mappings (Google CloudFormation uses different service names)
        ("google", "storage", "bucket"): "google_storage_bucket",
        ("google", "compute", "network"): "google_compute_network",
        ("google", "compute", "subnetwork"): "google_compute_subnetwork",
        ("google", "compute", "firewall"): "google_compute_firewall",
        ("google", "bigquery", "dataset"): "google_bigquery_dataset",
        ("google", "bigquery", "table"): "google_bigquery_table",
        ("google", "dataflow", "job"): "google_dataflow_job",
        ("google", "pubsub", "topic"): "google_pubsub_topic",
        ("google", "pubsub", "subscription"): "google_pubsub_subscription",
        ("google", "cloudfunctions", "function"): "google_cloudfunctions_function",
        ("google", "vpcaccess", "connector"): "google_vpc_access_connector",
        ("google", "notebooks", "instance"): "google_notebooks_instance",
        ("google", "redis", "instance"): "google_redis_instance",
        ("google", "monitoring", "alertpolicy"): "google_monitoring_alert_policy",
        (
            "google",
            "monitoring",
            "notificationchannel",
        ): "google_monitoring_notification_channel",
        ("google", "serviceaccount", "account"): "google_service_account",
    }

    # Try exact match first
    result = cfn_to_tf_map.get((provider, service, resource))
    if result:
        return result

    # Fallback: construct Terraform-style name
    if provider == "aws":
        return f"aws_{resource}"
    elif provider == "azure":
        return f"azurerm_{resource}"
    elif provider == "google":
        return f"google_{resource}"

    return f"{provider}_{resource}"


def _render_cfn_diagram(
    cfn_resources: dict[str, dict[str, Any]],
    cfn_edges: set[tuple[str, str]],
    out_path: Path,
    cfn_direction: str,
    cfn_pad: float,
    cfn_nodesep: float,
    cfn_ranksep: float,
    cfn_complexity: Any,
    render: Any,
) -> None:
    """Render CloudFormation diagram with same professional quality as Terraform."""
    outformat = out_path.suffix.lstrip(".").lower() or "png"
    filename_no_ext = str(out_path.with_suffix(""))

    # Determine background color
    desired_bg = (
        (os.getenv("AUTO_ARCH_RENDER_BG") or render.background or "transparent")
        .strip()
        .lower()
    )
    desired_bg = (
        "transparent" if desired_bg not in {"transparent", "white"} else desired_bg
    )
    bgcolor = "white" if outformat in {"jpg", "jpeg"} else desired_bg

    # Select layout based on complexity (same as Terraform)
    layout = "lanes"  # Default layout
    if cfn_complexity.node_count > 30 or cfn_complexity.provider_count > 2:
        layout = "providers"  # Use providers layout for complex multi-provider diagrams

    # Use same dynamic spacing calculations as Terraform
    spacing = _calculate_dynamic_spacing(cfn_complexity, render, cfn_direction)

    # Determine final spacing values (use auto-calculated or manual values)
    final_pad = spacing["pad"] if render.pad == "auto" else float(render.pad)
    final_nodesep = (
        spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
    )
    final_ranksep = (
        spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
    )

    # Enhanced graph attributes with intelligent edge routing (same as Terraform)
    graph_attr = {
        "bgcolor": bgcolor,
        "pad": str(final_pad),
        "nodesep": str(final_nodesep),
        "ranksep": str(final_ranksep),
        "splines": render.edge_routing,
        "concentrate": "true" if render.concentrate else "false",
        "fontname": render.fontname,
        "fontsize": str(render.graph_fontsize),
        "outputorder": "edgesfirst",
        # Advanced overlap and separation controls (sep/esep in inches - keep sub-inch)
        "overlap": render.overlap_removal,
        "overlap_scaling": "-4" if render.overlap_removal != "false" else "0",
        "sep": f"+{min(0.75, final_nodesep * 0.5):.2f}",  # cluster margin (inches)
        "esep": f"+{min(0.40, final_nodesep * 0.25):.2f}",  # edge margin (inches)
        "labelloc": "t",
        "labeljust": "c",
        # Professional edge routing from centers
        "smoothing": "spring" if cfn_complexity.edge_count > 10 else "none",
        "mclimit": "2.0",
        "nslimit": "2.0",
        "remincross": "true",
        "searchsize": "50",
    }

    node_by_res: dict[str, Any] = {}

    with Diagram(
        "Architecture (CloudFormation)",
        show=False,
        direction=cfn_direction,
        outformat=outformat,
        filename=filename_no_ext,
        graph_attr=graph_attr,
    ):
        # Group resources by category for professional clustering like Terraform
        grouped_resources: dict[str, list[str]] = {}

        for rid in cfn_resources.keys():
            resource_body = cfn_resources[rid]
            resource_type = resource_body.get("Type", "")

            # Map CloudFormation resource types to categories
            category = "Other"  # Default category
            if "::" in resource_type:
                service = resource_type.split("::")[1].lower()
                category_map = {
                    "s3": "Storage",
                    "wafv2": "Security",
                    "cloudfront": "Network",
                    "iam": "Security",
                    "lambda": "Compute",
                    "apigateway": "Other",
                    "logs": "Other",
                    "ssm": "Other",
                }
                category = category_map.get(service, "Other")

            if category not in grouped_resources:
                grouped_resources[category] = []
            grouped_resources[category].append(rid)

        # Create clusters based on layout selection
        if layout == "providers":
            # Provider-based layout for complex multi-provider diagrams
            for provider in ["aws", "azure", "google"]:
                provider_resources = {}
                for category, resources in grouped_resources.items():
                    for rid in resources:
                        resource_body = cfn_resources[rid]
                        resource_type = resource_body.get("Type", "")
                        if resource_type.startswith(provider.upper() + "::"):
                            if category not in provider_resources:
                                provider_resources[category] = []
                            provider_resources[category].append(rid)

                if provider_resources:
                    provider_name = {
                        "aws": "AWS",
                        "azure": "Azure",
                        "google": "Google",
                    }[provider]
                    with Cluster(
                        f"{provider_name} Cloud",
                        graph_attr={
                            "bgcolor": _provider_tint(provider_name) or "#f8f9fa",
                            "fillcolor": _provider_tint(provider_name) or "#f8f9fa",
                            "style": "rounded,filled",
                            "penwidth": "1.5",
                            "color": _provider_accent(provider_name) or "#6c757d",
                            "fontsize": "14",
                            "fontname": render.fontname,
                        },
                    ):
                        # Category sub-clusters within provider
                        for category in [
                            "Network",
                            "Security",
                            "Storage",
                            "Compute",
                            "Other",
                        ]:
                            if category in provider_resources:
                                with Cluster(
                                    category,
                                    graph_attr={
                                        "bgcolor": "#FFFFFF",
                                        "fillcolor": "#e9ecef",
                                        "style": "rounded,filled",
                                        "penwidth": "1.5",
                                        "color": "#adb5bd",
                                        "fontsize": "12",
                                        "fontname": render.fontname,
                                    },
                                ):
                                    for rid in sorted(provider_resources[category]):
                                        _create_cfn_node(
                                            rid, cfn_resources, node_by_res, render
                                        )
        else:
            # Category-based layout (default for simpler diagrams)
            for category in ["Network", "Security", "Storage", "Compute", "Other"]:
                if category in grouped_resources and grouped_resources[category]:
                    # Professional cluster styling like Terraform
                    cluster_attrs = {
                        "bgcolor": "#FFFFFF",
                        "fillcolor": "#F8F9FA",
                        "style": "rounded,filled",
                        "penwidth": "1.2",
                        "color": "#aeb6be",
                        "fontsize": "14",
                        "fontname": render.fontname,
                    }

                    with Cluster(category, graph_attr=cluster_attrs):
                        for rid in sorted(grouped_resources[category]):
                            _create_cfn_node(rid, cfn_resources, node_by_res, render)

        # Create edges with intelligent styling like Terraform
        for src, dst in sorted(cfn_edges):
            if src in node_by_res and dst in node_by_res:
                # Detect edge type and apply intelligent styling like Terraform
                edge_type = _detect_edge_type(src, dst, cfn_resources)
                edge_style_attrs = _get_edge_style_attrs(edge_type, render)

                # Try to apply custom styling using Edge object
                try:
                    from diagrams import Edge

                    node_by_res[src] >> Edge(**edge_style_attrs) >> node_by_res[dst]
                except (ImportError, TypeError, AttributeError):
                    node_by_res[src] >> node_by_res[dst]

    # Embed images in SVG files
    if outformat == "svg":
        _embed_images_in_svg(out_path)
    elif outformat in {"png", "jpg", "jpeg"}:
        _downscale_raster_if_needed(out_path)


_IAC_PROVIDER_LABELS = {
    "aws": "AWS",
    "azurerm": "Azure",
    "azure": "Azure",
    "azuread": "Azure AD",
    "google": "GCP",
    "gcp": "GCP",
    "oci": "OCI",
    "ibm": "IBM",
    "kubernetes": "Kubernetes",
    "helm": "Helm",
    "docker": "Docker",
    "random": "Random",
}


def _camel_to_snake(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _singularize_tokens(name: str) -> str:
    return "_".join(
        p[:-1] if len(p) > 3 and p.endswith("s") and not p.endswith("ss") else p
        for p in name.split("_")
    )


def _derive_tf_resource_name(kind: str, res_type: Any) -> str:
    """Map a Bicep/Pulumi resource type to a Terraform-style name for icon lookup.

    Examples:
      bicep  "Microsoft.Storage/storageAccounts@2022-09-01" -> azurerm_storage_accounts
      pulumi "aws:s3:Bucket"                                -> aws_s3_bucket
      pulumi "gcp:storage:Bucket"                           -> google_storage_bucket
    """
    if not isinstance(res_type, str) or not res_type.strip():
        return "generic_resource"

    if kind == "bicep":
        base = res_type.split("@", 1)[0]
        segments = [s for s in base.split("/") if s]
        provider_token = segments[0].split(".")[0].lower() if segments else "microsoft"
        resource_token = segments[-1] if segments else base
        prefix = "azurerm" if provider_token in {"microsoft", "windows"} else provider_token
        return f"{prefix}_{_camel_to_snake(resource_token)}"

    if kind == "pulumi":
        segments = [s for s in res_type.split(":") if s]
        if not segments:
            return "generic_resource"
        provider = segments[0].lower()
        prefix = _IAC_PROVIDER_LABELS.get(provider, provider).lower()
        if prefix in {"aws", "azurerm", "google", "oci", "ibm"} and len(segments) >= 3:
            service, resource = segments[1], segments[-1]
            return f"{prefix}_{_camel_to_snake(service)}_{_camel_to_snake(resource)}"
        return _camel_to_snake(segments[-1])

    return _camel_to_snake(res_type.replace("/", "_"))


def _resolve_iac_icon(kind: str, res_type: str):
    """Resolve an icon class for a Bicep/Pulumi resource type.

    Tries increasingly generic Terraform-style names (most specific first) so
    e.g. "Microsoft.Cdn/profiles" resolves via azurerm_cdn_profile before the
    vaguer azurerm_profiles guess. Returns (icon_cls_or_None, matched_name).
    """
    tf_name = _derive_tf_resource_name(kind, res_type)
    candidates = [tf_name]

    singular = _singularize_tokens(tf_name)
    if singular != tf_name:
        candidates.append(singular)

    # Less-specific fallback: drop the service segment (bicep), keeping
    # provider + resource, e.g. azurerm_cdn_profiles -> azurerm_profiles.
    parts = tf_name.split("_")
    if kind == "bicep" and len(parts) > 2:
        short = "_".join([parts[0]] + parts[2:])
        candidates.append(_singularize_tokens(short))
        candidates.append(short)

    for candidate in candidates:
        icon = _icon_class_for(candidate)
        if icon is not None:
            return icon, candidate
    return None, tf_name


def _render_generic_iac_diagram(
    resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    *,
    out_path: Path,
    title: str,
    direction: str,
    render: RenderConfig,
) -> None:
    """Render an icon-based architecture diagram for Bicep/Pulumi YAML graphs.

    Mirrors the Terraform/CloudFormation rendering quality: provider clusters,
    category sub-clusters, official icons where resolvable, and typed edges.
    """
    if Diagram is None or Cluster is None:
        raise RuntimeError(
            "Missing dependency diagrams. Install it and Graphviz to enable icon rendering."
        )

    outformat = out_path.suffix.lstrip(".").lower() or "png"
    filename_no_ext = str(out_path.with_suffix(""))

    desired_bg = (
        (os.getenv("AUTO_ARCH_RENDER_BG") or render.background or "transparent")
        .strip()
        .lower()
    )
    desired_bg = (
        "transparent" if desired_bg not in {"transparent", "white"} else desired_bg
    )
    bgcolor = "white" if outformat in {"jpg", "jpeg"} else desired_bg

    grouped_simple = {"IaC": {"Mixed": list(resources.keys())}}
    complexity = _analyze_diagram_complexity(resources, edges, grouped_simple)
    if direction.upper() == "AUTO":
        direction = _determine_optimal_direction(complexity, grouped_simple, "providers")
    spacing = _calculate_dynamic_spacing(complexity, render, direction)
    final_pad = spacing["pad"] if render.pad == "auto" else float(render.pad)
    final_nodesep = (
        spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
    )
    final_ranksep = (
        spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
    )

    graph_attr = {
        "bgcolor": bgcolor,
        "pad": str(final_pad),
        "nodesep": str(final_nodesep),
        "ranksep": str(final_ranksep),
        "splines": render.edge_routing,
        "concentrate": "true" if render.concentrate else "false",
        "fontname": render.fontname,
        "fontsize": str(render.graph_fontsize),
        "outputorder": "edgesfirst",
        "overlap": render.overlap_removal,
        "overlap_scaling": "-4" if render.overlap_removal != "false" else "0",
        "labelloc": "t",
        "labeljust": "c",
        "remincross": "true",
    }

    # Resolve providers and Terraform-style names up front.
    providers: dict[str, list[str]] = {}
    tf_names: dict[str, str] = {}
    icons: dict[str, Any] = {}
    for rid, body in resources.items():
        kind = str((body or {}).get("Kind", ""))
        res_type = (body or {}).get("Type", "")
        icon, tf_name = _resolve_iac_icon(kind, res_type)
        tf_names[rid] = tf_name
        icons[rid] = icon
        provider = str((body or {}).get("Provider") or "other").lower()
        providers.setdefault(provider, []).append(rid)

    category_order = [
        "Network",
        "Security",
        "Containers",
        "Compute",
        "Data",
        "Storage",
        "Integration",
        "Management",
        "Other",
    ]

    node_by_res: dict[str, Any] = {}

    with Diagram(
        title,
        show=False,
        direction=direction,
        outformat=outformat,
        filename=filename_no_ext,
        graph_attr=graph_attr,
    ):
        for provider in sorted(providers):
            provider_label = _IAC_PROVIDER_LABELS.get(
                provider, provider.replace("_", " ").title() or "Other"
            )
            provider_attrs = {
                "bgcolor": _provider_tint(provider_label) or "#FFFFFF",
                "fillcolor": _provider_tint(provider_label) or "#FFFFFF",
                "style": "rounded,filled",
                "penwidth": "1.5",
                "fontsize": "12",
                "fontname": "Helvetica-Bold",
                "color": _provider_accent(provider_label) or "#6C757D",
                "labelloc": "t",
                "labeljust": "l",
            }
            with Cluster(provider_label, graph_attr=provider_attrs):
                by_category: dict[str, list[str]] = {}
                for rid in providers[provider]:
                    by_category.setdefault(_tf_category(tf_names[rid]), []).append(rid)

                for category in category_order:
                    rids = sorted(by_category.get(category, []))
                    if not rids:
                        continue
                    category_attrs = {
                        "bgcolor": "#FFFFFF",
                        "fillcolor": _get_cluster_color(category, render),
                        "style": "rounded,filled",
                        "penwidth": "1.0",
                        "fontsize": "11",
                        "fontname": "Helvetica-Bold",
                        "color": "#CCCCCC",
                    }
                    with Cluster(category, graph_attr=category_attrs):
                        for rid in rids:
                            icon = icons.get(rid) or _generic_icon_for_kind(
                                category.lower()
                            )
                            label = _wrap_text(rid, max_width=20, max_lines=2)
                            node_by_res[rid] = _create_node_with_xlabel(icon, label)

        for src, dst in sorted(edges):
            if src in node_by_res and dst in node_by_res:
                edge_type = _detect_edge_type(src, dst, resources)
                edge_style_attrs = _get_edge_style_attrs(edge_type, render)
                try:
                    from diagrams import Edge

                    node_by_res[src] >> Edge(**edge_style_attrs) >> node_by_res[dst]
                except (ImportError, TypeError, AttributeError):
                    node_by_res[src] >> node_by_res[dst]

    if outformat == "svg":
        _embed_images_in_svg(out_path)
    elif outformat in {"png", "jpg", "jpeg"}:
        _downscale_raster_if_needed(out_path)


# Contextual display-label overrides applied ONLY to AI-refined renders.
# Keyed by full resource id or its name part; populated from validated model
# suggestions and cleared right after the refined render completes.
_CURRENT_LABEL_OVERRIDES: dict[str, str] = {}


def _sanitize_label(text: Any, max_len: int = 32) -> str | None:
    """Normalize a model-proposed label to a safe single-line string."""
    if not isinstance(text, str):
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"[^\w\s\-+()/&.:]", "", cleaned)
    if not cleaned or not any(ch.isalnum() for ch in cleaned):
        return None
    return cleaned[:max_len].rstrip()


def _extract_label_overrides(
    critique: dict[str, Any], resources: dict[str, dict[str, Any]]
) -> dict[str, str]:
    """Validate model-suggested labels against real resource ids."""
    proposed = critique.get("labels")
    if not isinstance(proposed, dict):
        return {}
    overrides: dict[str, str] = {}
    resource_ids = list(resources.keys())
    for key, value in list(proposed.items())[:24]:
        clean_value = _sanitize_label(value)
        if not clean_value or not isinstance(key, str):
            continue
        key = key.strip()
        matches = [rid for rid in resource_ids if rid == key]
        if not matches:
            matches = [rid for rid in resource_ids if rid.split(".", 1)[-1] == key]
        if not matches:
            continue
        for rid in matches:
            overrides[rid] = clean_value
    return overrides


def _build_ai_annotations(critique: dict[str, Any]) -> tuple[str, ...]:
    """Distill an AI critique into short on-diagram hint lines.

    Hints are IaC-contextual (functional roles, secret flows, encryption
    scope) rather than visual commentary, so the diagram is self-explanatory.
    """
    hints: list[str] = []
    for h in (critique.get("hints") or [])[:6]:
        if not isinstance(h, dict):
            continue
        tag = str(h.get("tag", "general")).strip().upper() or "INFO"
        text = str(h.get("text", "")).strip()
        if text:
            hints.append(f"[{tag}] {text}")
    if not hints:  # legacy fallback for models that skip the hints array
        insights = str(critique.get("insights_md") or "").strip()
        if insights:
            first_lines = [
                ln.strip().lstrip("-* ")
                for ln in insights.splitlines()
                if ln.strip() and not ln.strip().startswith(("#", "```"))
            ]
            hints.extend(first_lines[:2])
        for s in (critique.get("strengths") or [])[:2]:
            hints.append(f"+ {s}")
        for i in (critique.get("issues") or [])[:2]:
            hints.append(f"! [{i.get('type', 'general')}] {i.get('detail', '')}")
    return tuple(h for h in hints if h)[:6]


def _wrap_hint(text: str, width: int = 46) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if len(candidate) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return "\n".join(lines)


def _render_guide_png(
    render: RenderConfig,
    ai_annotations: tuple[str, ...],
    out_path: Path,
) -> bool:
    """Render a COMPACT standalone guide (legend + AI review hints).

    The guide must stay tiny relative to the diagram: two legend columns sit
    side by side (edge samples left, zone chips right), fonts are small and
    spacing tight. Callers additionally cap its stitched area at
    _MAX_GUIDE_AREA_FRACTION of the page.
    """
    try:
        import graphviz  # type: ignore[import-not-found]
    except ImportError:
        return False

    entry_font = "7"
    title_font = "8"
    font = "Helvetica"

    g = graphviz.Digraph(
        "guide",
        graph_attr={
            "rankdir": "TB",
            "bgcolor": "#FFFFFF",
            "pad": "0.08",
            "nodesep": "0.12",
            "ranksep": "0.14",
            "newrank": "true",  # allow rank=same pairing across clusters
        },
    )

    # ------------------------------------------- horizontal single-row legend
    # All edge samples share one graphviz rank so they align side by side;
    # same-rank endpoints make each sample arrow draw horizontally.
    samples = [
        ("Security / boundary", "security"),
        ("Data flow", "data"),
        ("Dependency", "dependency"),
        ("Network link", "network"),
    ]
    zones = [
        ("VPC boundary", render.color_vpc, "#5DADE2"),
        ("Public subnet", render.color_public_subnet, "#28A745"),
        ("Private subnet", render.color_private_subnet, "#FFC107"),
        ("Security zone", render.color_security, "#F44336"),
    ]

    with g.subgraph(name="cluster_legend") as leg:
        leg.attr(
            label="Legend",
            style="rounded,filled",
            fillcolor="#FFFFFF",
            color="#CCCCCC",
            fontsize=title_font,
            fontname="Helvetica-Bold",
            labelloc="t",
            margin="0.08",
        )
        sample_ids: list[str] = []
        chain_prev: str | None = None
        for row, (name, edge_type) in enumerate(samples):
            sid, did = f"lg_s{row}", f"lg_d{row}"
            leg.node(
                sid,
                "",
                shape="point",
                width="0.03",
                height="0.03",
                fixedsize="true",
            )
            leg.node(
                did,
                name,
                shape="box",
                style="rounded,filled",
                fillcolor="#FFFFFF",
                color="#B9BEC6",
                fontsize=entry_font,
                fontname=font,
                height="0.16",
                margin="0.02,0.01",
            )
            edge_attrs = _get_edge_style_attrs(edge_type, render)
            edge_attrs["arrowsize"] = "0.5"
            leg.edge(sid, did, **edge_attrs)
            if chain_prev:
                leg.edge(chain_prev, sid, style="invis")
            chain_prev = did
            sample_ids.extend([sid, did])

        zone_first: str | None = None
        zone_ids: list[str] = []
        for row, (name, fill, border) in enumerate(zones):
            zid = f"lg_z{row}"
            leg.node(
                zid,
                name,
                shape="box",
                style="rounded,filled",
                fillcolor=fill,
                color=border,
                fontsize=entry_font,
                fontname=font,
                height="0.16",
                margin="0.02,0.01",
            )
            if chain_prev:
                leg.edge(chain_prev, zid, style="invis")
            chain_prev = zid
            zone_ids.append(zid)
        # One shared rank => every entry sits side by side in a single strip.
        if sample_ids or zone_ids:
            with g.subgraph() as same_rank:
                same_rank.attr(rank="same")
                for nid in sample_ids + zone_ids:
                    same_rank.node(nid)

    # --------------------------------------------- compact AI hints panel
    if ai_annotations:
        with g.subgraph(name="cluster_hints") as hints:
            hints.attr(
                label="AI Review Hints",
                style="rounded,filled",
                fillcolor="#FFFDF0",
                color="#D8C689",
                fontsize=title_font,
                fontname="Helvetica-Bold",
                labelloc="t",
                margin="0.06",
            )
            prev_hint: str | None = None
            for row, hint in enumerate(ai_annotations[:4]):
                hid = f"hint{row}"
                hints.node(
                    hid,
                    _wrap_hint(hint, width=40),
                    shape="plaintext",
                    fontsize=entry_font,
                    fontname=font,
                )
                if prev_hint:
                    hints.edge(prev_hint, hid, style="invis")
                prev_hint = hid

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        g.render(str(out_path.with_suffix("")), format="png", cleanup=True)
        rendered = out_path.with_suffix(".png")
        if rendered.exists() and rendered != out_path:
            shutil.move(str(rendered), str(out_path))
        return out_path.exists()
    except Exception:  # nosec B112 - guide is best-effort
        return False


def _flatten_on_white(img: Any) -> Any:
    """Composite a possibly-transparent image onto a solid white RGB canvas."""
    from PIL import Image  # type: ignore[import-not-found]  # noqa: PLC0415

    rgba = img.convert("RGBA")
    flattened = Image.new("RGB", rgba.size, "#FFFFFF")
    flattened.paste(rgba, (0, 0), rgba)
    return flattened


# The stitched guide (legend + hints) must stay a footnote on the page:
# at most 8% of the final canvas area (diagram + gap + guide).
_MAX_GUIDE_AREA_FRACTION = 0.08
_BUDGET_FACTOR = _MAX_GUIDE_AREA_FRACTION / (1 - _MAX_GUIDE_AREA_FRACTION)


def _guide_area_scale(
    diagram_w: float, diagram_h: float, guide_w: float, guide_h: float
) -> float:
    """Scale factor shrinking the guide into the page-area budget (<=1.0)."""
    diagram_area = diagram_w * diagram_h
    guide_area = guide_w * guide_h
    if diagram_area <= 0 or guide_area <= 0:
        return 1.0
    max_guide_area = diagram_area * _BUDGET_FACTOR
    if guide_area <= max_guide_area:
        return 1.0
    return math.sqrt(max_guide_area / guide_area)


def _stitch_guide_below(diagram_path: Path, guide_path: Path) -> bool:
    """Append the standalone guide image below a rendered diagram, in place.

    Raster formats are stitched with PIL on a white canvas; SVGs get their
    canvas extended downward with the guide embedded as a data URI.
    """
    if not diagram_path.exists() or not guide_path.exists():
        return False

    suffix = diagram_path.suffix.lower()
    if suffix == ".svg":
        return _append_guide_to_svg(diagram_path, guide_path)
    if suffix not in {".png", ".jpg", ".jpeg"}:
        return False

    try:
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError:
        return False

    try:
        with Image.open(guide_path) as guide_src:
            guide = _flatten_on_white(guide_src)
        with Image.open(diagram_path) as diagram_src:
            diagram = _flatten_on_white(diagram_src)

        if guide.width > diagram.width > 0:
            scale = diagram.width / guide.width
            guide = guide.resize(
                (diagram.width, max(1, round(guide.height * scale))),
                getattr(Image, "LANCZOS", Image.BICUBIC),
            )
        # Keep the guide a footnote: cap it at 8% of the final page area.
        shrink = _guide_area_scale(
            diagram.width, diagram.height, guide.width, guide.height
        )
        if shrink < 1.0:
            guide = guide.resize(
                (
                    max(1, round(guide.width * shrink)),
                    max(1, round(guide.height * shrink)),
                ),
                getattr(Image, "LANCZOS", Image.BICUBIC),
            )
        gap = max(8, round(diagram.width * 0.005))
        x_off = max(0, (diagram.width - guide.width) // 2)
        canvas = Image.new(
            "RGB",
            (diagram.width, diagram.height + gap + guide.height),
            "#FFFFFF",
        )
        canvas.paste(diagram, (0, 0))
        canvas.paste(guide, (x_off, diagram.height + gap))

        save_kwargs: dict[str, Any] = {}
        if suffix in {".jpg", ".jpeg"}:
            save_kwargs["quality"] = 92
        canvas.save(diagram_path, **save_kwargs)
        return True
    except Exception:  # nosec B112 - stitching is best-effort
        return False


def _append_guide_to_svg(svg_path: Path, guide_png_path: Path) -> bool:
    """Extend an SVG canvas downward and embed the guide PNG as a data URI."""
    import struct

    from xml.etree import ElementTree as ET  # noqa: PLC0415

    svg_ns = "http://www.w3.org/2000/svg"
    xlink_ns = "http://www.w3.org/1999/xlink"
    ET.register_namespace("", svg_ns)
    ET.register_namespace("xlink", xlink_ns)

    def _length(value: Any) -> float | None:
        match = re.match(r"(-?[0-9]*\.?[0-9]+)", str(value or "").strip())
        return float(match.group(1)) if match else None

    try:
        png_bytes = guide_png_path.read_bytes()
        if len(png_bytes) < 24 or not png_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return False
        guide_w, guide_h = struct.unpack(">II", png_bytes[16:24])
        if guide_w <= 0 or guide_h <= 0:
            return False

        tree = ET.parse(svg_path)
        root = tree.getroot()
        svg_w = _length(root.get("width"))
        svg_h = _length(root.get("height"))
        viewBox = (root.get("viewBox") or "").replace(",", " ").split()
        if svg_w is None and len(viewBox) == 4:
            svg_w = _length(viewBox[2])
        if svg_h is None and len(viewBox) == 4:
            svg_h = _length(viewBox[3])
        if svg_w is None or svg_h is None:
            return False

        gap = max(8.0, svg_w * 0.005)
        # Cap the embedded guide at 8% of the final page area, then center it.
        # The scale factor applies to the GUIDE's native size, not the canvas.
        shrink = _guide_area_scale(svg_w, svg_h, guide_w, guide_h)
        display_w = min(float(svg_w), guide_w * shrink)
        scaled_guide_h = display_w * (guide_h / guide_w)
        total_h = svg_h + gap + scaled_guide_h

        root.set("width", f"{svg_w:.0f}pt")
        root.set("height", f"{total_h:.0f}pt")
        if len(viewBox) == 4:
            root.set("viewBox", f"0 0 {svg_w:g} {total_h:g}")

        image_el = ET.SubElement(root, f"{{{svg_ns}}}image")
        image_el.set("x", f"{max(0.0, (svg_w - display_w) / 2):g}")
        image_el.set("y", f"{svg_h + gap:g}")
        image_el.set("width", f"{display_w:g}")
        image_el.set("height", f"{scaled_guide_h:g}")
        image_el.set("preserveAspectRatio", "xMidYMin meet")
        data_uri = "data:image/png;base64," + base64.b64encode(png_bytes).decode(
            "ascii"
        )
        image_el.set(f"{{{xlink_ns}}}href", data_uri)

        tree.write(svg_path, encoding="utf-8", xml_declaration=False)
        return True
    except Exception:  # nosec B110 - embedding is best-effort
        return False


def _static_markdown(
    changed_paths: list[Path],
    direction: str,
    limits: Limits,
    *,
    out_png: Path | None,
    out_jpg: Path | None,
    out_svg: Path | None,
    out_md: Path | None = None,
    out_drawio: Path | None = None,
    out_html: Path | None = None,
    render: RenderConfig,
    ai_enhance: bool = False,
    ai_backend: str = "auto",
    gemini_model: str | None = None,
    openrouter_model: str | None = None,
) -> tuple[str, str]:
    # Prefer Terraform first, then CloudFormation, then Bicep, then Pulumi YAML.
    mermaid = None
    summary = None
    assumptions = None

    diag_kind = None
    tf_resources: dict[str, dict[str, Any]] | None = None
    tf_edges: set[tuple[str, str]] | None = None
    cfn_resources: dict[str, dict[str, Any]] | None = None
    cfn_edges: set[tuple[str, str]] | None = None
    bicep_resources: dict[str, dict[str, Any]] | None = None
    bicep_edges: set[tuple[str, str]] | None = None
    pulumi_resources: dict[str, dict[str, Any]] | None = None
    pulumi_edges: set[tuple[str, str]] | None = None

    # Pre-generated plan support
    if render.planfile:
        try:
            plan_path = Path(render.planfile)
            graph_path = Path(render.graphfile) if render.graphfile else None
            parsed_tf = _parse_terraform_plan_json(plan_path, graph_path)
            all_res, _, _ = parsed_tf
            tf_resources = all_res
            tf_edges = set()
            mermaid = "graph LR\n" + "\n".join(f"  {r}" for r in all_res.keys())
            summary = f"{len(all_res)} resources parsed from plan file."
            assumptions = "Parsed from pre-generated plan JSON."
            diag_kind = "terraform"
        except Exception as exc:
            _debug(f"[DEBUG] Plan file parse error: {exc}")

    if diag_kind is None:
        try:
            # Parse the Terraform files once and share the result between the
            # graph builder and the Mermaid renderer.
            parsed_tf = _terraform_resources_from_files(changed_paths, limits, Path.cwd())
            tf_resources, tf_edges = _static_terraform_graph(
                changed_paths, limits, parsed_inputs=parsed_tf
            )
            mermaid, summary, assumptions = _static_terraform_mermaid(
                changed_paths, direction, limits, parsed_inputs=parsed_tf
            )
            diag_kind = "terraform"
        except Exception:  # nosec B110
            pass

    if mermaid is None:
        try:
            cfn_resources, cfn_edges = _static_cloudformation_graph(
                changed_paths, limits
            )
            mermaid, summary, assumptions = _static_cloudformation_mermaid(
                changed_paths, direction, limits
            )
            diag_kind = "cloudformation"
        except Exception as exc:
            # try bicep
            try:
                bicep_resources, bicep_edges = _static_bicep_graph(
                    changed_paths, limits
                )
                mermaid, summary, assumptions = _static_bicep_mermaid(
                    changed_paths, direction, limits
                )
                diag_kind = "bicep"
            except Exception:
                try:
                    pulumi_resources, pulumi_edges = _static_pulumi_yaml_graph(
                        changed_paths, limits
                    )
                    mermaid, summary, assumptions = _static_pulumi_yaml_mermaid(
                        changed_paths, direction, limits
                    )
                    diag_kind = "pulumi"
                except Exception:
                    reason = str(exc) or "No supported IaC parsers produced a diagram."
                    return (
                        _fallback_markdown(
                            [p.as_posix() for p in changed_paths], reason
                        ),
                        "",
                    )

    # Simplified view filtering if requested
    if render.simplified and tf_resources is not None and tf_edges is not None:
        tf_resources, tf_edges = _simplify_architecture_graph(tf_resources, tf_edges)

    # Render icon-based diagrams if requested and dependencies exist.
    rendered_any = False
    if diag_kind == "terraform" and tf_resources is not None and tf_edges is not None:
        try:
            if out_png is not None:
                _render_icon_diagram_from_terraform(
                    tf_resources,
                    tf_edges,
                    out_path=out_png,
                    title="Architecture (Terraform)",
                    direction=direction,
                    render=render,
                )
                rendered_any = True
            if out_jpg is not None:
                _render_icon_diagram_from_terraform(
                    tf_resources,
                    tf_edges,
                    out_path=out_jpg,
                    title="Architecture (Terraform)",
                    direction=direction,
                    render=render,
                )
                rendered_any = True
            if out_svg is not None:
                _render_icon_diagram_from_terraform(
                    tf_resources,
                    tf_edges,
                    out_path=out_svg,
                    title="Architecture (Terraform)",
                    direction=direction,
                    render=render,
                )
                rendered_any = True
        except Exception:  # nosec B110
            # Keep Mermaid output even if Graphviz/diagrams fails.
            pass

    # Vision-assisted feedback loop (OpenRouter, free models only): critique
    # the rendered diagram and refine render settings when it improves.
    # AI-refined renders go to unique *-ai.* files (with legend + hints) so
    # the deterministic base outputs are never overwritten.
    ai_critique: dict[str, Any] = {}
    ai_history: list[dict[str, Any]] = []
    ai_model_id = ""
    ai_refined_files: list[str] = []
    if (
        ai_enhance
        and diag_kind == "terraform"
        and tf_resources is not None
        and tf_edges is not None
        and Diagram is not None
    ):
        try:
            from diagram_feedback import format_insights_markdown, run_feedback_loop

            best_render, best_direction, ai_critique, ai_history = run_feedback_loop(
                tf_resources,
                tf_edges,
                direction=direction,
                render=render,
                title="Architecture (Terraform)",
                backend=ai_backend,
                gemini_model=gemini_model,
                openrouter_model=openrouter_model,
            )
            if ai_critique:
                ai_model_id = str(
                    ai_history[0]["model"] if ai_history else os.getenv("OPENROUTER_MODEL", "")
                )
                ai_hints = _build_ai_annotations(ai_critique)
                label_overrides = _extract_label_overrides(ai_critique, tf_resources)
                if label_overrides:
                    _CURRENT_LABEL_OVERRIDES.clear()
                    _CURRENT_LABEL_OVERRIDES.update(label_overrides)
                ai_title = str(ai_critique.get("title") or "Architecture (Terraform, AI-refined)")
                ai_subtitle = str(ai_critique.get("subtitle") or "")
                try:
                    # 1. Render raster and vector images
                    ai_svg_path: Path | None = None
                    for out in (out_png, out_jpg, out_svg):
                        if out is None:
                            continue
                        ai_out = out.with_name(f"{out.stem}-ai{out.suffix}")
                        try:
                            _render_icon_diagram_from_terraform(
                                tf_resources,
                                tf_edges,
                                out_path=ai_out,
                                title=ai_title,
                                direction=best_direction,
                                render=best_render,
                                ai_hints=ai_hints,
                                ai_subtitle=ai_subtitle,
                            )
                            if ai_out.suffix == ".svg":
                                ai_svg_path = ai_out
                            ai_refined_files.append(ai_out.name)
                        except Exception as render_err:
                            _debug(f"[DEBUG] AI render failed for {ai_out}: {render_err}")
                            continue

                    # 2. Render AI-enhanced interactive HTML studio
                    ai_html = (out_html.with_name(f"{out_html.stem}-ai{out_html.suffix}") if out_html else 
                               (ai_svg_path.with_suffix(".html") if ai_svg_path else None))
                    if ai_html is not None and ai_svg_path is not None and ai_svg_path.exists():
                        try:
                            ai_svg_data = ai_svg_path.read_text(encoding="utf-8")
                            export_interactive_html(
                                ai_svg_data,
                                tf_resources,
                                title=ai_title,
                                out_path=ai_html,
                                edges=tf_edges,
                            )
                            ai_refined_files.append(ai_html.name)
                        except Exception:
                            pass

                    # 3. Render AI-enhanced draw.io (.drawio)
                    if out_drawio is not None:
                        try:
                            from drawio_exporter import export_drawio
                            ai_drawio = out_drawio.with_name(f"{out_drawio.stem}-ai{out_drawio.suffix}")
                            clean_res, clean_edges = _consolidate_plumbing_resources(tf_resources, tf_edges)
                            export_drawio(clean_res, clean_edges, out_path=ai_drawio, title=ai_title)
                            ai_refined_files.append(ai_drawio.name)
                        except Exception:
                            pass

                    # 4. Render AI-enhanced Markdown report
                    if out_md is not None:
                        try:
                            ai_md = out_md.with_name(f"{out_md.stem}-ai{out_md.suffix}")
                            ai_md_content = format_insights_markdown(
                                ai_critique,
                                best_direction,
                                best_render,
                                tf_resources,
                                tf_edges,
                                model=ai_model_id,
                            )
                            ai_md.write_text(ai_md_content, encoding="utf-8")
                            ai_refined_files.append(ai_md.name)
                        except Exception:
                            pass

                finally:
                    # Contextual labels apply to AI renders only; the
                    # deterministic base outputs keep their generic labels.
                    _CURRENT_LABEL_OVERRIDES.clear()
        except Exception as exc:  # nosec B110 - enhancement is strictly optional
            _debug(f"[DEBUG] AI enhancement skipped: {exc}")

    # For CloudFormation, we don't have provider-wide icon mapping yet; render a generic diagram.
    if (
        diag_kind == "cloudformation"
        and cfn_resources is not None
        and cfn_edges is not None
    ):
        # Analyze CloudFormation diagram complexity once
        grouped_simple = {"CloudFormation": {"AWS": list(cfn_resources.keys())}}
        cfn_complexity = _analyze_diagram_complexity(
            cfn_resources, cfn_edges, grouped_simple
        )

        # Auto-detect optimal direction if set to "auto"
        cfn_direction = direction
        if cfn_direction.upper() == "AUTO":
            cfn_direction = _determine_optimal_direction(
                cfn_complexity, grouped_simple, "lanes"
            )
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"[Auto Direction CFN] Changed from 'auto' to '{cfn_direction}'")

        cfn_spacing = _calculate_dynamic_spacing(cfn_complexity, render, cfn_direction)

        # Use auto-calculated spacing or manual overrides
        cfn_pad = cfn_spacing["pad"] if render.pad == "auto" else float(render.pad)
        cfn_nodesep = (
            cfn_spacing["nodesep"]
            if render.nodesep == "auto"
            else float(render.nodesep)
        )
        cfn_ranksep = (
            cfn_spacing["ranksep"]
            if render.ranksep == "auto"
            else float(render.ranksep)
        )

        try:
            # Render PNG
            if Diagram is not None and Cluster is not None and out_png is not None:
                _render_cfn_diagram(
                    cfn_resources,
                    cfn_edges,
                    out_png,
                    cfn_direction,
                    cfn_pad,
                    cfn_nodesep,
                    cfn_ranksep,
                    cfn_complexity,
                    render,
                )
                rendered_any = True

            # Render JPG
            if Diagram is not None and Cluster is not None and out_jpg is not None:
                _render_cfn_diagram(
                    cfn_resources,
                    cfn_edges,
                    out_jpg,
                    cfn_direction,
                    cfn_pad,
                    cfn_nodesep,
                    cfn_ranksep,
                    cfn_complexity,
                    render,
                )
                rendered_any = True

            # Render SVG
            if Diagram is not None and Cluster is not None and out_svg is not None:
                _render_cfn_diagram(
                    cfn_resources,
                    cfn_edges,
                    out_svg,
                    cfn_direction,
                    cfn_pad,
                    cfn_nodesep,
                    cfn_ranksep,
                    cfn_complexity,
                    render,
                )
                rendered_any = True
        except Exception:  # nosec B110
            pass

    # Bicep and Pulumi YAML graphs get the same icon-based rendering quality.
    if diag_kind in {"bicep", "pulumi"}:
        gen_resources = bicep_resources if diag_kind == "bicep" else pulumi_resources
        gen_edges = bicep_edges if diag_kind == "bicep" else pulumi_edges
        if gen_resources and gen_edges is not None and Diagram is not None:
            gen_title = f"Architecture ({diag_kind.capitalize()})"
            for out in (out_png, out_jpg, out_svg):
                if out is None:
                    continue
                try:
                    _render_generic_iac_diagram(
                        gen_resources,
                        gen_edges,
                        out_path=out,
                        title=gen_title,
                        direction=direction,
                        render=render,
                    )
                    rendered_any = True
                except Exception:  # nosec B110
                    pass

    # draw.io export works for every supported IaC kind: it reuses the same
    # parsed graph and icon pipeline, so the .drawio output mirrors the
    # rendered diagrams exactly.
    if out_drawio is not None:
        drawio_graphs = {
            "terraform": (tf_resources, tf_edges),
            "cloudformation": (cfn_resources, cfn_edges),
            "bicep": (bicep_resources, bicep_edges),
            "pulumi": (pulumi_resources, pulumi_edges),
        }
        drawio_resources, drawio_edges = drawio_graphs.get(diag_kind, (None, None))
        if drawio_resources and drawio_edges is not None:
            if diag_kind == "terraform" and not getattr(render, "no_consolidate", False):
                drawio_resources, drawio_edges = _consolidate_plumbing_resources(
                    drawio_resources,
                    drawio_edges,
                    expand_badges=getattr(render, "expand_badges", False),
                )
            try:
                from drawio_exporter import export_drawio  # noqa: PLC0415

                export_drawio(
                    drawio_resources,
                    drawio_edges,
                    out_drawio,
                    title=f"Architecture ({diag_kind.capitalize()})",
                    render=render,
                )
                rendered_any = True
            except Exception as exc:  # nosec B110
                _debug(f"[DEBUG] draw.io export failed: {exc}")

    # Interactive HTML export works for every supported IaC kind if SVG was generated.
    if out_html is not None or (out_svg is not None and out_svg.exists()):
        html_graphs = {
            "terraform": (tf_resources, tf_edges),
            "cloudformation": (cfn_resources, cfn_edges),
            "bicep": (bicep_resources, bicep_edges),
            "pulumi": (pulumi_resources, pulumi_edges),
        }
        html_resources, html_edges = html_graphs.get(diag_kind, (None, None))
        if html_resources is not None:
            try:
                target_html = (
                    out_html
                    if out_html is not None
                    else (out_svg.with_suffix(".html") if out_svg else None)
                )
                if target_html is not None and out_svg is not None and out_svg.exists():
                    svg_data = out_svg.read_text(encoding="utf-8")
                    export_interactive_html(
                        svg_data,
                        html_resources,
                        title=f"Architecture ({diag_kind.capitalize() if diag_kind else 'IaC'})",
                        out_path=target_html,
                        edges=html_edges,
                    )
                    rendered_any = True
            except Exception as exc:  # nosec B110
                _debug(f"[DEBUG] Interactive HTML export failed: {exc}")

    md = (
        f"{COMMENT_MARKER}\n\n"
        f"## Architecture Diagram (Auto)\n\n"
        f"Summary: {summary}\n\n"
        f"```mermaid\n{mermaid}```\n\n"
        f"Assumptions: {assumptions}\n\n"
        f"Rendered diagram: {'available as workflow artifact' if rendered_any else 'not available (icons require Graphviz + diagrams)'}\n"
    )
    if ai_critique:
        try:
            from diagram_feedback import format_insights_markdown

            md += format_insights_markdown(ai_critique, ai_history, ai_model_id)
            if ai_refined_files:
                md += (
                    "\n**AI-refined diagram files** (include legend and review "
                    f"hints): {', '.join(ai_refined_files)}\n"
                )
        except Exception:  # nosec B110
            pass
    return (md, mermaid)


def _split_changed_files(changed_files_raw: str) -> list[str]:
    if not changed_files_raw:
        return []
    # tj-actions/changed-files returns a space-separated list by default.
    parts = [p.strip() for p in re.split(r"\s+", changed_files_raw) if p.strip()]
    # Normalize path separators for repo-local reads.
    return [p.replace("\\", "/") for p in parts]


def _normalize_mermaid_direction(direction: str) -> str:
    d = (direction or "").strip().upper()
    if d == "AUTO" or d not in {"LR", "RL", "TB", "BT"}:
        return "LR"
    return d


_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?ix)"
    r"(password|passwd|secret|token|access[_-]?key|secret[_-]?key|private[_-]?key)"
    r"\s*([:=])\s*"
    r"(\"[^\"]*\"|'[^']*'|[^\s\n\r#]+)"
)


def _redact_likely_secrets(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        key, sep = m.group(1), m.group(2)
        # Use quoted string to maintain valid HCL/YAML syntax
        return f'{key}{sep}"REDACTED"'

    return _SECRET_ASSIGNMENT_RE.sub(repl, text)


def _read_file_limited(path: Path, *, max_bytes: int) -> str:
    try:
        data = path.read_bytes()
    except Exception as exc:
        return f"<ERROR: failed to read file: {exc}>"

    if len(data) > max_bytes:
        data = data[:max_bytes]
        suffix = "\n\n<TRUNCATED: file exceeded size limit>\n"
    else:
        suffix = ""

    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = data.decode(errors="replace")

    # Normalize newlines to improve parser compatibility (e.g., HCL parsing on CRLF files).
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return _redact_likely_secrets(text) + suffix


def _build_prompt(
    changed_files: list[Path], direction: str, file_snippets: dict[str, str]
) -> list[dict[str, str]]:
    file_list = "\n".join(f"- {p.as_posix()}" for p in changed_files)
    snippets = []
    for filename, contents in file_snippets.items():
        snippets.append(f"FILE: {filename}\n---\n{contents}\n---\n")
    snippets_text = "\n".join(snippets)

    system = (
        "You are a senior cloud architect. "
        "Create a professional architecture diagram from Infrastructure-as-Code snippets. "
        "Use only information present in the snippets; when unsure, make explicit assumptions. "
        "Do NOT include any secrets. "
        "Output must be valid GitHub-flavored Markdown. "
        "Include exactly one Mermaid diagram fenced code block. "
        "Prefer clear grouping using Mermaid subgraphs (e.g., VPC/VNet, subnets, resource groups, clusters)."
    )

    user = (
        f"Generate an architecture diagram for these changed IaC files:\n{file_list}\n\n"
        f"Requirements:\n"
        f"- Mermaid diagram must start with `flowchart {direction}`\n"
        f"- Show key resources and connections (ingress, egress, dependencies)\n"
        f"- Keep it readable; avoid listing every minor attribute\n"
        f"- Add a short 'Summary' section and an 'Assumptions' section\n\n"
        f"IaC snippets (redacted + may be truncated):\n\n{snippets_text}"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _extract_mermaid(markdown: str) -> str | None:
    m = re.search(
        r"```mermaid\s*(.*?)\s*```", markdown, flags=re.DOTALL | re.IGNORECASE
    )
    if not m:
        return None
    return m.group(1).strip() + "\n"


def _fallback_markdown(changed_files: list[str], reason: str) -> str:
    files = "\n".join(f"- {p}" for p in changed_files) if changed_files else "- (none)"
    return (
        f"{COMMENT_MARKER}\n\n"
        f"## Architecture Diagram (Auto)\n\n"
        f"Summary: Unable to generate diagram automatically.\n\n"
        f"Reason: {reason}\n\n"
        f"Changed IaC files:\n{files}\n"
    )


def _safe_path_under(root: Path, rel: str) -> Path | None:
    # Prevent path traversal when consuming file lists from PR APIs/actions.
    rel_raw = (rel or "").strip()
    if not rel_raw:
        return None

    # Normalize separators. GitHub APIs generally return forward slashes, but local
    # runs/tests may pass absolute paths.
    rel_norm = rel_raw.replace("\\", "/")
    candidate = Path(rel_norm)

    if candidate.is_absolute():
        p = candidate.resolve()
    else:
        rel_norm = rel_norm.lstrip("/")
        p = (root / rel_norm).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    return p


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Mermaid architecture diagram from changed IaC files"
    )
    parser.add_argument(
        "--changed-files",
        default="",
        help="Space/newline-separated list of changed IaC files",
    )
    parser.add_argument(
        "--iac-root",
        default=".",
        help="Root directory to read IaC files from (useful when PR content is checked out into a subfolder)",
    )
    parser.add_argument(
        "--direction",
        default="",
        help="Override Mermaid/Graph direction (LR|RL|TB|BT). If omitted, uses AUTO_ARCH_DIRECTION or config.",
    )
    parser.add_argument("--out-md", default="artifacts/architecture-diagram.md")
    parser.add_argument("--out-mmd", default="artifacts/architecture-diagram.mmd")
    parser.add_argument("--out-png", default="artifacts/architecture-diagram.png")
    parser.add_argument("--out-jpg", default="artifacts/architecture-diagram.jpg")
    parser.add_argument("--out-svg", default="artifacts/architecture-diagram.svg")
    parser.add_argument(
        "--out-drawio",
        default="",
        help="Output draw.io (.drawio) file path; empty string disables export",
    )
    parser.add_argument(
        "--render-engine",
        default="auto",
        choices=["auto", "neato", "dot"],
        help="Rendering engine: auto (3-stage neato layout pipeline), neato, or dot",
    )
    parser.add_argument(
        "--out-html",
        default="",
        help="Output standalone interactive HTML diagram with pan/zoom and metadata inspection",
    )
    parser.add_argument(
        "--fontsize",
        type=int,
        default=None,
        help="Diagram font size scaling override",
    )
    parser.add_argument(
        "--iconsize",
        type=int,
        default=None,
        help="Diagram icon size scaling override (in px)",
    )
    parser.add_argument(
        "--simplified",
        action="store_true",
        help="Generate high-level simplified executive view (stripping plumbing)",
    )
    parser.add_argument(
        "--planfile",
        default="",
        help="Path to pre-generated Terraform plan JSON (terraform show -json)",
    )
    parser.add_argument(
        "--graphfile",
        default="",
        help="Path to pre-generated Terraform graph DOT (terraform graph)",
    )
    parser.add_argument(
        "--varfile",
        action="append",
        default=[],
        help="Path to .tfvars variables file (can be repeated)",
    )
    parser.add_argument(
        "--workspace",
        default="default",
        help="Terraform workspace name",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Source files location or remote Git repository URL (https://host/repo.git//subfolder)",
    )
    parser.add_argument(
        "--annotate",
        default="",
        help="Path to custom flow annotations YAML file",
    )
    parser.add_argument(
        "--expand-badges",
        action="store_true",
        help="Render security groups/NSGs as standalone nodes instead of corner badges",
    )
    parser.add_argument(
        "--no-consolidate",
        action="store_true",
        help="Disable automatic consolidation of repeated resource instances",
    )
    parser.add_argument(
        "--ai-backend",
        default="auto",
        choices=["auto", "gemini", "openrouter", "ollama", "bedrock", "restapi"],
        help="AI vision enhancement backend (auto, gemini, openrouter)",
    )
    parser.add_argument(
        "--gemini-model",
        default="gemini-3.1-flash-lite",
        help="Google Gemini vision model name (default: gemini-3.1-flash-lite)",
    )
    parser.add_argument(
        "--openrouter-model",
        default=None,
        help="OpenRouter vision model override",
    )
    parser.add_argument(
        "--ollama-model",
        default="llama3",
        help="Ollama model name when using --ai-backend ollama",
    )
    parser.add_argument(
        "--ai-enhance",
        action="store_true",
        help="Enable vision-assisted refinement (Gemini or OpenRouter free models)",
    )
    parser.add_argument(
        "--confluence-smart",
        action="store_true",
        help="Enable Smart Confluence AI-enhanced architecture portal (workload narrative, FinOps cost analysis, Well-Architected review, draw.io + HTML studio attachments)",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    direction, config_mode, config_model, limits, publish, render = _load_config(
        repo_root
    )

    # Direction override: CLI arg > env var > config.
    direction_override = (
        (args.direction or os.getenv("AUTO_ARCH_DIRECTION") or "").strip().upper()
    )
    if direction_override:
        if direction_override not in {"LR", "RL", "TB", "BT", "AUTO"}:
            direction_override = "LR"
        direction = direction_override

    # Merge CLI parameters into RenderConfig
    render = RenderConfig(
        layout=render.layout,
        lanes=render.lanes,
        pad=render.pad,
        nodesep=render.nodesep,
        ranksep=render.ranksep,
        splines=render.splines,
        concentrate=render.concentrate,
        edge_routing=render.edge_routing,
        overlap_removal=render.overlap_removal,
        edge_style_security=render.edge_style_security,
        edge_style_data=render.edge_style_data,
        edge_style_dependency=render.edge_style_dependency,
        edge_style_network=render.edge_style_network,
        color_aws=render.color_aws,
        color_azure=render.color_azure,
        color_gcp=render.color_gcp,
        color_oci=render.color_oci,
        color_ibm=render.color_ibm,
        color_vpc=render.color_vpc,
        color_public_subnet=render.color_public_subnet,
        color_private_subnet=render.color_private_subnet,
        color_security=render.color_security,
        min_pad=render.min_pad,
        min_nodesep=render.min_nodesep,
        min_ranksep=render.min_ranksep,
        complexity_scale=render.complexity_scale,
        edge_density_scale=render.edge_density_scale,
        background=render.background,
        fontname=render.fontname,
        graph_fontsize=render.graph_fontsize,
        node_fontsize=render.node_fontsize,
        node_width=render.node_width,
        node_height=render.node_height,
        edge_color=render.edge_color,
        edge_penwidth=render.edge_penwidth,
        edge_arrowsize=render.edge_arrowsize,
        render_engine=args.render_engine,
        fontsize=args.fontsize,
        iconsize=args.iconsize,
        simplified=args.simplified,
        expand_badges=args.expand_badges,
        no_consolidate=args.no_consolidate,
        planfile=args.planfile,
        graphfile=args.graphfile,
        varfiles=tuple(args.varfile),
        workspace=args.workspace,
        annotate=args.annotate,
        ai_backend=args.ai_backend,
        ollama_model=args.ollama_model,
    )

    # Allow env override for publish mode (useful for local/example generation).
    publish_override = _parse_env_bool(os.getenv("AUTO_ARCH_PUBLISH_ENABLED"))
    if publish_override is not None:
        publish = PublishPaths(
            enabled=publish_override,
            md=publish.md,
            mmd=publish.mmd,
            png=publish.png,
            jpg=publish.jpg,
            svg=publish.svg,
            drawio=publish.drawio,
            html=publish.html,
        )

    mode = (os.getenv("AUTO_ARCH_MODE") or config_mode or DEFAULT_MODE).strip().lower()
    model = (os.getenv("AUTO_ARCH_MODEL") or config_model or DEFAULT_MODEL).strip()
    changed_files = _split_changed_files(args.changed_files)

    # Handle remote git source if specified
    temp_git_dir = None
    if args.source:
        source_path, temp_git_dir = _handle_git_source(args.source)
        iac_root = source_path.resolve()
        if not changed_files:
            # Auto-discover IaC files in cloned source
            changed_files = [
                str(p.relative_to(iac_root))
                for p in sorted(iac_root.rglob("*.tf"))
            ]
    else:
        iac_root = (repo_root / args.iac_root).resolve()

    out_md = repo_root / args.out_md
    out_mmd = repo_root / args.out_mmd

    out_png_raw = (args.out_png or "").strip()
    out_jpg_raw = (args.out_jpg or "").strip()
    out_svg_raw = (args.out_svg or "").strip()
    out_drawio_raw = (args.out_drawio or "").strip()
    out_html_raw = (args.out_html or "").strip()
    out_png = (repo_root / out_png_raw) if out_png_raw else None
    out_jpg = (repo_root / out_jpg_raw) if out_jpg_raw else None
    out_svg = (repo_root / out_svg_raw) if out_svg_raw else None
    out_drawio = (repo_root / out_drawio_raw) if out_drawio_raw else None
    out_html = (repo_root / out_html_raw) if out_html_raw else None

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_mmd.parent.mkdir(parents=True, exist_ok=True)
    if out_png is not None:
        out_png.parent.mkdir(parents=True, exist_ok=True)
    if out_jpg is not None:
        out_jpg.parent.mkdir(parents=True, exist_ok=True)
    if out_svg is not None:
        out_svg.parent.mkdir(parents=True, exist_ok=True)
    if out_drawio is not None:
        out_drawio.parent.mkdir(parents=True, exist_ok=True)
    if out_html is not None:
        out_html.parent.mkdir(parents=True, exist_ok=True)

    if not changed_files:
        out_md.write_text(
            _fallback_markdown([], "No IaC file changes detected."), encoding="utf-8"
        )
        out_mmd.write_text("", encoding="utf-8")
        if out_png is not None:
            out_png.write_bytes(b"")
        if out_jpg is not None:
            out_jpg.write_bytes(b"")
        if out_svg is not None:
            out_svg.write_text("", encoding="utf-8")
        if out_drawio is not None:
            out_drawio.write_text("", encoding="utf-8")
        if out_html is not None:
            out_html.write_text("", encoding="utf-8")
        return 0

    selected = changed_files[: limits.max_files]
    safe_selected: list[str] = []
    changed_paths: list[Path] = []
    for rel in selected:
        safe_path = _safe_path_under(iac_root, rel)
        if safe_path is None:
            continue
        safe_selected.append(rel)
        changed_paths.append(safe_path)
    selected = safe_selected

    if not changed_paths:
        out_md.write_text(
            _fallback_markdown([], "No valid IaC file paths after sanitization."),
            encoding="utf-8",
        )
        out_mmd.write_text("", encoding="utf-8")
        if out_png is not None:
            out_png.write_bytes(b"")
        if out_jpg is not None:
            out_jpg.write_bytes(b"")
        if out_svg is not None:
            out_svg.write_text("", encoding="utf-8")
        if out_drawio is not None:
            out_drawio.write_text("", encoding="utf-8")
        if out_html is not None:
            out_html.write_text("", encoding="utf-8")
        return 0

    mermaid_direction = _normalize_mermaid_direction(direction)

    if mode != "ai":
        ai_enhance_enabled = args.ai_enhance or bool(
            _parse_env_bool(os.getenv("AUTO_ARCH_AI_ENHANCE"))
        )
        md, mermaid = _static_markdown(
            changed_paths,
            mermaid_direction,
            limits,
            out_png=out_png,
            out_jpg=out_jpg,
            out_svg=out_svg,
            out_md=out_md,
            out_drawio=out_drawio,
            out_html=out_html,
            render=render,
            ai_enhance=ai_enhance_enabled,
            ai_backend=args.ai_backend,
            gemini_model=args.gemini_model,
            openrouter_model=args.openrouter_model,
        )
        out_md.write_text(md, encoding="utf-8")
        out_mmd.write_text(mermaid, encoding="utf-8")

        _maybe_publish_outputs(
            repo_root,
            publish,
            out_md=out_md,
            out_mmd=out_mmd,
            out_png=out_png,
            out_jpg=out_jpg,
            out_svg=out_svg,
            out_drawio=out_drawio,
            out_html=out_html,
        )
        return 0

    file_snippets: dict[str, str] = {}
    for p in changed_paths:
        if not p.exists() or not p.is_file():
            file_snippets[p.as_posix()] = "<ERROR: file not found in checkout>"
            continue
        file_snippets[p.as_posix()] = _read_file_limited(
            p, max_bytes=limits.max_bytes_per_file
        )

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key or OpenAI is None:
        reason = "Missing OPENAI_API_KEY (or OpenAI client unavailable). Set it as a repo secret to enable generation."
        out_md.write_text(_fallback_markdown(selected, reason), encoding="utf-8")
        out_mmd.write_text("", encoding="utf-8")
        return 0

    client = OpenAI(api_key=api_key)
    messages = _build_prompt(changed_paths, mermaid_direction, file_snippets)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        markdown = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        out_md.write_text(
            _fallback_markdown(selected, f"OpenAI request failed: {exc}"),
            encoding="utf-8",
        )
        out_mmd.write_text("", encoding="utf-8")
        return 0

    if COMMENT_MARKER not in markdown:
        markdown = f"{COMMENT_MARKER}\n\n" + markdown

    mermaid = _extract_mermaid(markdown)
    if mermaid is None:
        out_md.write_text(
            _fallback_markdown(
                selected, "Model response did not contain a Mermaid code block."
            ),
            encoding="utf-8",
        )
        out_mmd.write_text("", encoding="utf-8")
        return 0

    out_md.write_text(markdown + "\n", encoding="utf-8")
    out_mmd.write_text(mermaid, encoding="utf-8")

    _maybe_publish_outputs(
        repo_root,
        publish,
        out_md=out_md,
        out_mmd=out_mmd,
        out_png=out_png,
        out_jpg=out_jpg,
        out_svg=out_svg,
        out_drawio=out_drawio,
        out_html=out_html,
    )
    return 0


if __name__ == "__main__":
    # Check for Confluence publishing env/config
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_user = os.getenv("CONFLUENCE_USER")
    confluence_token = os.getenv("CONFLUENCE_TOKEN")
    confluence_page_id = os.getenv("CONFLUENCE_PAGE_ID")
    confluence_replace = os.getenv("CONFLUENCE_REPLACE", "true").lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    confluence_image_marker = os.getenv("CONFLUENCE_IMAGE_MARKER")
    confluence_unique_filename = os.getenv("CONFLUENCE_UNIQUE_FILENAME", "").lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    confluence_smart = os.getenv("CONFLUENCE_SMART_PAGE", "true").lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    confluence_debug = os.getenv("AUTO_ARCH_DEBUG", "").lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    # Run main diagram generation
    exit_code = main()
    # If Confluence config is set, publish diagram
    if confluence_url and confluence_user and confluence_token and confluence_page_id:
        repo_root = Path.cwd()
        
        # Check if Smart Confluence is requested
        if confluence_smart:
            try:
                from tools.smart_confluence import (
                    ConfluenceArtifacts,
                    analyze_architecture_for_confluence,
                    publish_smart_confluence_page,
                )

                # Collect all available artifacts
                def _find_file(pattern: str) -> Path | None:
                    matches = list(repo_root.glob(pattern))
                    return matches[0] if matches else None

                artifacts = ConfluenceArtifacts(
                    png=_find_file("artifacts/*.png") or _find_file("docs/*.png"),
                    jpg=_find_file("artifacts/*.jpg") or _find_file("docs/*.jpg"),
                    svg=_find_file("artifacts/*.svg") or _find_file("docs/*.svg"),
                    drawio=_find_file("artifacts/*.drawio") or _find_file("docs/*.drawio"),
                    html=_find_file("artifacts/*.html") or _find_file("docs/*.html"),
                    md=_find_file("artifacts/*.md") or _find_file("docs/*.md"),
                    mmd=_find_file("artifacts/*.mmd") or _find_file("docs/*.mmd"),
                    ai_png=_find_file("artifacts/*-ai.png") or _find_file("docs/*-ai.png"),
                    ai_svg=_find_file("artifacts/*-ai.svg") or _find_file("docs/*-ai.svg"),
                    ai_html=_find_file("artifacts/*-ai.html") or _find_file("docs/*-ai.html"),
                    ai_drawio=_find_file("artifacts/*-ai.drawio") or _find_file("docs/*-ai.drawio"),
                    ai_md=_find_file("artifacts/*-ai.md") or _find_file("docs/*-ai.md"),
                )

                # Scan IaC files to build resource inventory
                iac_files = _find_iac_files(repo_root)
                resources, edges = _parse_iac_to_graph(iac_files)

                # Perform deep architectural & FinOps analysis
                ai_backend = os.getenv("AUTO_ARCH_AI_BACKEND", "auto")
                report = analyze_architecture_for_confluence(
                    resources=resources,
                    edges=edges,
                    png_path=artifacts.ai_png or artifacts.png,
                    backend=ai_backend,
                )

                # Publish rich Smart Confluence architecture portal
                publish_smart_confluence_page(
                    confluence_url=confluence_url,
                    confluence_user=confluence_user,
                    confluence_token=confluence_token,
                    page_id=confluence_page_id,
                    report=report,
                    artifacts=artifacts,
                    resources=resources,
                    full_page=confluence_replace,
                    debug=confluence_debug,
                )
            except Exception as smart_exc:
                print(f"[smart-confluence] Error executing Smart Confluence: {smart_exc}; falling back to standard publish...", flush=True)
                confluence_smart = False

        if not confluence_smart:
            # Fallback to standard single-image replacement + optional draw.io upload
            png_path = repo_root / "artifacts/architecture-diagram.png"
            svg_path = repo_root / "artifacts/architecture-diagram.svg"
            drawio_path = repo_root / "artifacts/architecture-diagram.drawio"
            if not drawio_path.exists():
                drawio_matches = list(repo_root.glob("docs/*.drawio")) or list(repo_root.glob("artifacts/*.drawio"))
                drawio_path = drawio_matches[0] if drawio_matches else None

            published = False
            for path in [png_path, svg_path]:
                if path.exists():
                    published = _publish_to_confluence(
                        confluence_url,
                        confluence_user,
                        confluence_token,
                        confluence_page_id,
                        path,
                        drawio_path=drawio_path,
                        replace=confluence_replace,
                        image_marker=confluence_image_marker,
                        debug=confluence_debug,
                        unique_filename=confluence_unique_filename,
                    )
                    if published:
                        break
            if not published:
                print("Confluence publish: no diagram file found to upload.")
    raise SystemExit(exit_code)
