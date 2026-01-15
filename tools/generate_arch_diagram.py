from __future__ import annotations

import argparse
import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

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


@dataclass(frozen=True)
class RenderConfig:
    # "lanes" (category-first) tends to produce more readable, professional diagrams.
    # "providers" groups primarily by provider.
    layout: str = "lanes"  # lanes | providers

    # The order of lanes when layout == "lanes".
    lanes: tuple[str, ...] = ("Network", "Security", "Containers", "Compute", "Data", "Storage", "Other")

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
    
    # Minimum spacing constraints (used when auto-calculating)
    min_pad: float = 0.3
    min_nodesep: float = 0.25
    min_ranksep: float = 0.65
    
    # Complexity multipliers for auto-spacing
    complexity_scale: float = 1.5  # How much to scale spacing based on complexity
    edge_density_scale: float = 1.2  # Additional scaling for high edge density

    # Styling
    background: str = "transparent"  # transparent | white
    fontname: str = "Helvetica"
    graph_fontsize: int = 18
    node_fontsize: int = 9
    node_width: float = 0.85
    node_height: float = 0.85
    edge_color: str = "#6B7280"
    edge_penwidth: float = 0.9
    edge_arrowsize: float = 0.65


@dataclass(frozen=True)
class PublishPaths:
    enabled: bool = False
    md: str | None = None
    mmd: str | None = None
    png: str | None = None
    jpg: str | None = None
    svg: str | None = None


@dataclass(frozen=True)
class Limits:
    max_files: int = 25
    max_bytes_per_file: int = 30000


def _load_config(repo_root: Path) -> tuple[str, str, str, Limits, PublishPaths, RenderConfig]:
    config_path = repo_root / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return ("LR", DEFAULT_MODE, DEFAULT_MODEL, Limits(), PublishPaths(), RenderConfig())

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    direction = (((config.get("diagram") or {}).get("direction")) or "LR").strip()
    mode = (((config.get("generator") or {}).get("mode")) or DEFAULT_MODE).strip().lower()
    model = (((config.get("model") or {}).get("name")) or DEFAULT_MODEL).strip()
    limits_cfg = (config.get("limits") or {})
    limits = Limits(
        max_files=int(limits_cfg.get("max_files", 25)),
        max_bytes_per_file=int(limits_cfg.get("max_bytes_per_file", 30000)),
    )

    publish_cfg = (config.get("publish") or {})
    publish_paths_cfg = (publish_cfg.get("paths") or {})
    publish = PublishPaths(
        enabled=bool(publish_cfg.get("enabled", False)),
        md=publish_paths_cfg.get("md"),
        mmd=publish_paths_cfg.get("mmd"),
        png=publish_paths_cfg.get("png"),
        jpg=publish_paths_cfg.get("jpg"),
        svg=publish_paths_cfg.get("svg"),
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

    render = RenderConfig(
        layout=str(render_cfg.get("layout", RenderConfig().layout)).strip().lower(),
        lanes=lanes_tuple,
        pad=_parse_spacing_value(graph_cfg.get("pad"), RenderConfig().pad),
        nodesep=_parse_spacing_value(graph_cfg.get("nodesep"), RenderConfig().nodesep),
        ranksep=_parse_spacing_value(graph_cfg.get("ranksep"), RenderConfig().ranksep),
        splines=str(graph_cfg.get("splines", RenderConfig().splines)).strip(),
        concentrate=bool(graph_cfg.get("concentrate", RenderConfig().concentrate)),
        edge_routing=str(graph_cfg.get("edge_routing", RenderConfig().edge_routing)).strip(),
        overlap_removal=str(graph_cfg.get("overlap_removal", RenderConfig().overlap_removal)).strip(),
        min_pad=float(graph_cfg.get("min_pad", RenderConfig().min_pad)),
        min_nodesep=float(graph_cfg.get("min_nodesep", RenderConfig().min_nodesep)),
        min_ranksep=float(graph_cfg.get("min_ranksep", RenderConfig().min_ranksep)),
        complexity_scale=float(graph_cfg.get("complexity_scale", RenderConfig().complexity_scale)),
        edge_density_scale=float(graph_cfg.get("edge_density_scale", RenderConfig().edge_density_scale)),
        background=str(render_cfg.get("background", RenderConfig().background)).strip().lower(),
        fontname=str(render_cfg.get("fontname", RenderConfig().fontname)).strip(),
        graph_fontsize=int(render_cfg.get("graph_fontsize", RenderConfig().graph_fontsize)),
        node_fontsize=int(node_cfg.get("fontsize", RenderConfig().node_fontsize)),
        node_width=float(node_cfg.get("width", RenderConfig().node_width)),
        node_height=float(node_cfg.get("height", RenderConfig().node_height)),
        edge_color=str(render_cfg.get("edge_color", RenderConfig().edge_color)).strip(),
        edge_penwidth=float(render_cfg.get("edge_penwidth", RenderConfig().edge_penwidth)),
        edge_arrowsize=float(render_cfg.get("edge_arrowsize", RenderConfig().edge_arrowsize)),
    )

    return (direction, mode, model, limits, publish, render)


def _write_bytes_if_changed(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            if path.read_bytes() == content:
                return False
        except Exception:
            pass
    path.write_bytes(content)
    return True


def _write_text_if_changed(path: Path, content: str) -> bool:
    return _write_bytes_if_changed(path, content.encode("utf-8"))


def _embed_images_in_svg(svg_path: Path) -> None:
    """Replace xlink:href file references with embedded base64 data URIs.

    This ensures icons render when the SVG is viewed outside the build host.
    """

    if not svg_path.exists():
        return
    try:
        content = svg_path.read_text(encoding="utf-8")
    except Exception:
        return

    # Find all xlink:href="..." patterns that point to PNG files.
    def replace_match(m: re.Match[str]) -> str:
        ref = m.group(1)
        # Skip if it's already a data URI or external URL.
        if ref.startswith(("data:", "http:", "https:")):
            return m.group(0)
        img_path = svg_path.parent / ref
        if not img_path.exists():
            return m.group(0)
        try:
            img_bytes = img_path.read_bytes()
            b64 = base64.b64encode(img_bytes).decode("ascii")
            # We assume PNG for diagrams; adjust if needed.
            return f'xlink:href="data:image/png;base64,{b64}"'
        except Exception:
            return m.group(0)

    updated = re.sub(r'xlink:href="([^"]+)"', replace_match, content)
    if updated != content:
        svg_path.write_text(updated, encoding="utf-8")


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
        edge_density = min(self.avg_edges_per_node / 4.0, 1.0)  # 4+ edges/node = high density
        cluster_complexity = min(self.cluster_count / 10.0, 1.0)  # 10+ clusters = complex
        depth_complexity = min(self.max_cluster_depth / 3.0, 1.0)  # 3+ levels = deep nesting
        label_complexity = min(self.max_label_length / 40.0, 1.0)  # 40+ chars = long labels
        provider_diversity = min(self.provider_count / 3.0, 1.0)  # 3+ providers = diverse
        
        # Weighted average of complexity factors
        overall_complexity = (
            node_complexity * 0.25 +
            edge_density * 0.25 +
            cluster_complexity * 0.15 +
            depth_complexity * 0.15 +
            label_complexity * 0.10 +
            provider_diversity * 0.10
        )
        
        # Calculate multipliers (1.0 = minimum, increases with complexity)
        # Use exponential scaling for better distribution
        pad_multiplier = 1.0 + (overall_complexity ** 0.7) * 0.8
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


def _calculate_dynamic_spacing(
    complexity: DiagramComplexity,
    render: RenderConfig,
    direction: str,
) -> dict[str, Any]:
    """Calculate optimal spacing parameters based on diagram complexity."""
    
    multipliers = complexity.calculate_spacing_multiplier()
    
    # Apply multipliers to base values with complexity scaling
    pad_value = render.min_pad * multipliers["pad"] * render.complexity_scale
    nodesep_value = render.min_nodesep * multipliers["nodesep"] * render.complexity_scale
    ranksep_value = render.min_ranksep * multipliers["ranksep"] * render.complexity_scale
    
    # Direction-specific adjustments
    if direction in ("LR", "RL"):
        # Left-right layouts need more horizontal spacing
        nodesep_value *= 1.2
    else:
        # Top-bottom layouts need more vertical spacing
        ranksep_value *= 1.2
    
    # Additional edge density scaling
    if complexity.avg_edges_per_node > 2.5:
        nodesep_value *= render.edge_density_scale
        ranksep_value *= render.edge_density_scale
        pad_value *= 1.1
    
    return {
        "pad": round(pad_value, 2),
        "nodesep": round(nodesep_value, 2),
        "ranksep": round(ranksep_value, 2),
    }

    def _replace(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith("data:"):
            return match.group(0)
        try:
            data = Path(href).read_bytes()
        except Exception:
            return match.group(0)
        mime = "image/png"
        lower = href.lower()
        if lower.endswith(".jpg") or lower.endswith(".jpeg"):
            mime = "image/jpeg"
        b64 = base64.b64encode(data).decode("ascii")
        return f'xlink:href="data:{mime};base64,{b64}"'

    new_content = re.sub(r'xlink:href="([^"]+)"', _replace, content)
    if new_content != content:
        try:
            svg_path.write_text(new_content, encoding="utf-8")
        except Exception:
            pass


def _maybe_publish_outputs(
    repo_root: Path,
    publish: PublishPaths,
    *,
    out_md: Path,
    out_mmd: Path,
    out_png: Path | None,
    out_jpg: Path | None,
    out_svg: Path | None,
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
        did_change = _write_bytes_if_changed(dst, data) if binary else _write_text_if_changed(dst, data)
        if did_change:
            changed.append(str(dst.relative_to(repo_root)).replace("\\", "/"))

    publish_file(out_md, publish.md, binary=False)
    publish_file(out_mmd, publish.mmd, binary=False)
    publish_file(out_png, publish.png, binary=True)
    publish_file(out_jpg, publish.jpg, binary=True)
    publish_file(out_svg, publish.svg, binary=False)

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


_TF_REF_RE = re.compile(r"(?<![\w-])([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9_]+)*")


def _extract_tf_resource_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    for item in _walk(value):
        if isinstance(item, str):
            for m in _TF_REF_RE.finditer(item):
                refs.add(f"{m.group(1)}.{m.group(2)}")
    return refs


def _terraform_resources_from_hcl(parsed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    resources: dict[str, dict[str, Any]] = {}
    blocks = parsed.get("resource")
    if not blocks:
        return resources

    # python-hcl2 returns resource blocks as a list of dicts.
    for block in blocks:
        if not isinstance(block, dict):
            continue
        for r_type, r_body in block.items():
            if isinstance(r_body, dict):
                # { "aws_vpc": {"main": {...}} }
                for name, attrs in r_body.items():
                    if isinstance(attrs, dict):
                        resources[f"{r_type}.{name}"] = attrs
            elif isinstance(r_body, list):
                # Sometimes: { "aws_vpc": [ {"main": {...}} ] }
                for entry in r_body:
                    if not isinstance(entry, dict):
                        continue
                    for name, attrs in entry.items():
                        if isinstance(attrs, dict):
                            resources[f"{r_type}.{name}"] = attrs
    return resources


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

    if any(k in t for k in ["vpc", "vnet", "vcn", "subnet", "route", "gateway", "internet", "nat", "network", "firewall", "lb", "load_balancer"]):
        return "Network"
    if any(k in t for k in ["security", "nsg", "security_group", "iam", "policy", "role", "key", "kms"]):
        return "Security"
    if any(k in t for k in ["eks", "aks", "gke", "kubernetes", "container", "cluster"]):
        return "Containers"
    if any(k in t for k in ["instance", "vm", "virtual_machine", "compute", "ec2", "app_service", "function", "lambda"]):
        return "Compute"
    if any(k in t for k in ["db", "database", "sql", "rds", "dynamodb", "cosmos", "redis", "elasticache"]):
        return "Data"
    if any(k in t for k in ["bucket", "storage", "objectstorage", "blob", "s3"]):
        return "Storage"
    return "Other"


def _wrap_text(text: str, *, max_width: int = 14, max_lines: int = 2) -> str:
    """Wrap/shorten labels so Graphviz doesn't overflow outside node tiles."""

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
    parts = [p if p.isupper() or p in {"VPC", "VNet", "VCN", "NSG", "EKS", "AKS", "GKE", "VM", "IAM", "SQL"} else p.title() for p in parts]
    return " ".join(parts)


def _tf_node_label(res_id: str) -> str:
    # res_id is like "aws_vpc.main".
    try:
        r_type, name = res_id.split(".", 1)
    except ValueError:
        return _wrap_text(res_id)
    kind = _tf_pretty_kind(r_type)
    # Wrap kind and keep name on its own line.
    kind_wrapped = _wrap_text(kind, max_width=14, max_lines=1)
    name_wrapped = _wrap_text(name, max_width=14, max_lines=1)
    return f"{kind_wrapped}\n{name_wrapped}".strip()


def _import_node_class(module_path: str, class_name: str):
    try:
        mod = __import__(module_path, fromlist=[class_name])
        return getattr(mod, class_name)
    except Exception:
        return None


def _guess_provider(resource_type: str) -> str:
    """Extract provider name from Terraform resource type."""
    t = resource_type.lower()
    if t.startswith("aws_"):
        return "AWS"
    if t.startswith("azurerm_"):
        return "AZURERM"
    if t.startswith("google_"):
        return "GOOGLE"
    if t.startswith("oci_"):
        return "OCI"
    if t.startswith("ibm_"):
        return "IBM"
    return "OTHER"


def _load_custom_icon(terraform_resource_type: str):
    """Load a custom icon from the icons/ directory if available.
    
    Returns a Custom node class that uses the icon file, or None if not found.
    """
    if Diagram is None:
        return None
        
    # Get repo root (tools/ is one level down)
    repo_root = Path(__file__).resolve().parents[1]
    icons_dir = repo_root / "icons"
    
    # Determine provider directory
    provider = _guess_provider(terraform_resource_type).lower()
    if provider == "azurerm":
        provider = "azure"
    elif provider == "other":
        return None
    
    # Remove provider prefix from resource type for filename
    t = terraform_resource_type.lower()
    for prefix in ("aws_", "azurerm_", "google_", "oci_", "ibm_"):
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    
    # Look for PNG icon
    icon_path = icons_dir / provider / f"{t}.png"
    if not icon_path.exists():
        return None
    
    try:
        # Import Custom node class from diagrams
        Custom = _import_node_class("diagrams", "Custom")
        if Custom is None:
            return None
        
        # Return a wrapper that creates Custom nodes with our icon
        def custom_icon_wrapper(label: str = ""):
            return Custom(label, str(icon_path))
        
        return custom_icon_wrapper
    except Exception:
        return None


def _ensure_generic_fallback_icons() -> None:
    global Blank, Rack, SQL, Firewall, Router, Switch, Storage, Compute, LoadBalancer
    if Diagram is None:
        return

    # Availability varies across diagrams versions; keep all of these optional.
    if Blank is None:
        Blank = _import_node_class("diagrams.generic.blank", "Blank")
    if Rack is None:
        Rack = _import_node_class("diagrams.generic.compute", "Rack")
    if SQL is None:
        SQL = _import_node_class("diagrams.generic.database", "SQL")
    if Firewall is None:
        Firewall = _import_node_class("diagrams.generic.network", "Firewall")
    if Router is None:
        Router = _import_node_class("diagrams.generic.network", "Router")
    if Switch is None:
        Switch = _import_node_class("diagrams.generic.network", "Switch")
    if Storage is None:
        Storage = _import_node_class("diagrams.generic.storage", "Storage")

    # Aliases used by helper functions
    if Compute is None:
        Compute = Rack or Blank
    if LoadBalancer is None:
        LoadBalancer = Switch or Blank


def _icon_class_for(terraform_resource_type: str):
    """Best-effort mapping from TF resource type to a provider service icon.

    This aims for "professional" official-style icons via the `diagrams` library.
    If a specific icon isn't known, falls back to generic nodes.
    
    Resolution order:
    1. Custom icons in icons/{provider}/ directory
    2. Built-in diagrams library icons
    3. Generic fallback icons
    """
    
    # First, try loading a custom icon
    custom_icon = _load_custom_icon(terraform_resource_type)
    if custom_icon is not None:
        return custom_icon

    t = terraform_resource_type.lower()

    # AWS
    if t.startswith("aws_"):
        mapping = {
            "aws_vpc": ("diagrams.aws.network", "VPC"),
            "aws_subnet": ("diagrams.aws.network", "PrivateSubnet"),
            "aws_internet_gateway": ("diagrams.aws.network", "InternetGateway"),
            "aws_nat_gateway": ("diagrams.aws.network", "NATGateway"),
            "aws_route_table": ("diagrams.aws.network", "RouteTable"),
            "aws_security_group": ("diagrams.aws.security", "SecurityGroup"),
            "aws_lb": ("diagrams.aws.network", "ELB"),
            "aws_alb": ("diagrams.aws.network", "ELB"),
            "aws_elb": ("diagrams.aws.network", "ELB"),
            "aws_instance": ("diagrams.aws.compute", "EC2"),
            "aws_autoscaling_group": ("diagrams.aws.compute", "AutoScaling"),
            "aws_eks_cluster": ("diagrams.aws.compute", "EKS"),
            "aws_ecs_cluster": ("diagrams.aws.compute", "ECS"),
            "aws_lambda_function": ("diagrams.aws.compute", "Lambda"),
            "aws_s3_bucket": ("diagrams.aws.storage", "S3"),
            "aws_dynamodb_table": ("diagrams.aws.database", "Dynamodb"),
            "aws_db_instance": ("diagrams.aws.database", "RDS"),
            "aws_rds_cluster": ("diagrams.aws.database", "RDS"),
            "aws_elasticache_cluster": ("diagrams.aws.database", "ElastiCache"),
            "aws_cloudfront_distribution": ("diagrams.aws.network", "CloudFront"),
        }
        module_path, class_name = mapping.get(t, ("diagrams.aws.general", "General"))
        return _import_node_class(module_path, class_name)

    # Azure
    if t.startswith("azurerm_"):
        mapping = {
            "azurerm_resource_group": ("diagrams.azure.general", "Resourcegroups"),
            "azurerm_virtual_network": ("diagrams.azure.network", "VirtualNetworks"),
            "azurerm_subnet": ("diagrams.azure.network", "Subnets"),
            "azurerm_network_security_group": ("diagrams.azure.security", "SecurityCenter"),
            "azurerm_public_ip": ("diagrams.azure.network", "PublicIpAddresses"),
            "azurerm_load_balancer": ("diagrams.azure.network", "LoadBalancers"),
            "azurerm_linux_virtual_machine": ("diagrams.azure.compute", "VirtualMachines"),
            "azurerm_windows_virtual_machine": ("diagrams.azure.compute", "VirtualMachines"),
            "azurerm_kubernetes_cluster": ("diagrams.azure.compute", "KubernetesServices"),
            "azurerm_app_service": ("diagrams.azure.compute", "AppServices"),
            "azurerm_storage_account": ("diagrams.azure.storage", "StorageAccounts"),
            "azurerm_sql_server": ("diagrams.azure.database", "SQLDatabases"),
            "azurerm_sql_database": ("diagrams.azure.database", "SQLDatabases"),
            "azurerm_cosmosdb_account": ("diagrams.azure.database", "CosmosDb"),
        }
        module_path, class_name = mapping.get(t, ("diagrams.azure.general", "General"))
        return _import_node_class(module_path, class_name)

    # GCP
    if t.startswith("google_"):
        mapping = {
            "google_compute_network": ("diagrams.gcp.network", "VPC"),
            "google_compute_subnetwork": ("diagrams.gcp.network", "Router"),
            "google_compute_firewall": ("diagrams.gcp.network", "FirewallRules"),
            "google_compute_instance": ("diagrams.gcp.compute", "ComputeEngine"),
            "google_container_cluster": ("diagrams.gcp.compute", "GKE"),
            "google_cloudfunctions_function": ("diagrams.gcp.compute", "Functions"),
            "google_storage_bucket": ("diagrams.gcp.storage", "GCS"),
            "google_sql_database_instance": ("diagrams.gcp.database", "SQL"),
        }
        module_path, class_name = mapping.get(t, ("diagrams.gcp.general", "General"))
        return _import_node_class(module_path, class_name)

    # Oracle
    if t.startswith("oci_"):
        # Icon coverage varies; fall back to Oracle general if specific isn't found.
        mapping = {
            "oci_core_vcn": ("diagrams.oracle.network", "VCN"),
            "oci_core_subnet": ("diagrams.oracle.network", "Subnet"),
            "oci_core_instance": ("diagrams.oracle.compute", "Compute"),
            "oci_objectstorage_bucket": ("diagrams.oracle.storage", "ObjectStorage"),
        }
        module_path, class_name = mapping.get(t, ("diagrams.oracle.general", "General"))
        return _import_node_class(module_path, class_name)

    # IBM
    if t.startswith("ibm_"):
        mapping = {
            "ibm_is_vpc": ("diagrams.ibm.network", "VPC"),
            "ibm_is_instance": ("diagrams.ibm.compute", "VPC"),
            "ibm_resource_instance": ("diagrams.ibm.general", "Cloud"),
        }
        module_path, class_name = mapping.get(t, ("diagrams.ibm.general", "General"))
        return _import_node_class(module_path, class_name)

    return None


def _generic_icon_for_kind(kind: str):
    if Diagram is None:
        return None
    _ensure_generic_fallback_icons()
    kind = kind.lower()
    if kind in {"compute", "vm", "instance", "node"}:
        return Compute or Blank
    if kind in {"db", "database", "sql"}:
        return SQL or Blank
    if kind in {"storage", "bucket"}:
        return Storage or Blank
    if kind in {"lb", "loadbalancer"}:
        return LoadBalancer or Blank
    if kind in {"fw", "firewall", "security"}:
        return Firewall or Blank
    if kind in {"router", "network"}:
        return Router or Blank
    return Compute or Blank


def _render_icon_diagram_from_terraform(
    all_resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    *,
    out_path: Path,
    title: str,
    direction: str,
    render: RenderConfig,
):
    if Diagram is None or Cluster is None:
        raise RuntimeError("Missing dependency diagrams. Install it and Graphviz to enable icon rendering.")

    _ensure_generic_fallback_icons()

    # diagrams expects filename without extension; it appends based on outformat.
    outformat = out_path.suffix.lstrip(".").lower() or "png"
    filename_no_ext = str(out_path.with_suffix(""))

    node_by_res: dict[str, Any] = {}

    layout = (os.getenv("AUTO_ARCH_RENDER_LAYOUT") or render.layout or "lanes").strip().lower()
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
    
    # Calculate optimal spacing parameters
    spacing = _calculate_dynamic_spacing(complexity, render, direction)
    
    # Determine final spacing values (use auto-calculated or manual values)
    final_pad = spacing["pad"] if render.pad == "auto" else float(render.pad)
    final_nodesep = spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
    final_ranksep = spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
    
    # Print spacing info for debugging
    if os.getenv("AUTO_ARCH_DEBUG"):
        print(f"[Diagram Complexity] Nodes: {complexity.node_count}, Edges: {complexity.edge_count}")
        print(f"[Diagram Complexity] Clusters: {complexity.cluster_count}, Depth: {complexity.max_cluster_depth}")
        print(f"[Diagram Complexity] Avg edges/node: {complexity.avg_edges_per_node:.2f}")
        print(f"[Spacing] pad={final_pad}, nodesep={final_nodesep}, ranksep={final_ranksep}")

    # Graphviz tuning to reduce crossings and avoid oversized icon boxes.
    # Keep PNG/SVG transparent by default; JPEG cannot be transparent.
    desired_bg = (os.getenv("AUTO_ARCH_RENDER_BG") or render.background or "transparent").strip().lower()
    desired_bg = "transparent" if desired_bg not in {"transparent", "white"} else desired_bg
    bgcolor = "white" if outformat in {"jpg", "jpeg"} else desired_bg
    
    # Enhanced graph attributes with intelligent edge routing
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
        # Advanced overlap and separation controls
        "overlap": render.overlap_removal,
        "overlap_scaling": "-4" if render.overlap_removal != "false" else "0",
        "sep": f"+{int(final_nodesep * 20)}",  # Dynamic cluster separation
        "esep": f"+{int(final_nodesep * 10)}",  # Dynamic edge separation
        "labelloc": "t",
        "labeljust": "c",
        # Edge routing improvements
        "smoothing": "spring" if complexity.edge_count > 10 else "none",
        "mclimit": "2.0",  # Limit mincross iterations for performance
        "nslimit": "2.0",  # Limit network simplex iterations
        "remincross": "true",  # Remove edge crossings
        "searchsize": "50",  # Larger search space for better layouts
    }

    # Make icon tiles smaller and remove the white filled box behind icons.
    node_attr = {
        "fontname": render.fontname,
        "fontsize": str(render.node_fontsize),
        "labelloc": "b",
        "labeljust": "c",
        "imagescale": "true",
        "fixedsize": "true",
        "width": str(render.node_width),
        "height": str(render.node_height),
        "shape": "box",
        # Draw a subtle tile border so edges visibly terminate at node boundary.
        "style": "rounded",
        "margin": "0.05",
        "fillcolor": bgcolor if outformat in {"jpg", "jpeg"} else "transparent",
        "color": "#D1D5DB",
        "penwidth": "1",
    }

    edge_attr = {
        "color": render.edge_color,
        "penwidth": str(render.edge_penwidth),
        "arrowsize": str(render.edge_arrowsize),
        # Intelligent edge styling based on complexity
        "constraint": "true",  # Maintain hierarchical structure
        "minlen": "2" if complexity.edge_count > 20 else "1",  # Longer edges for complex diagrams
        "weight": "1",  # Default edge weight
    }

    with Diagram(
        title,
        show=False,
        direction=direction,
        outformat=outformat,
        filename=filename_no_ext,
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        if layout == "providers":
            # Provider-first: AWS/Azure/GCP/... with category sub-clusters.
            for provider, categories in sorted(grouped_providers.items()):
                with Cluster(provider):
                    for lane in lanes:
                        resources = categories.get(lane)
                        if not resources:
                            continue
                        with Cluster(lane):
                            for res in sorted(resources):
                                r_type, _name = res.split(".", 1)
                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                node_by_res[res] = Icon(_tf_node_label(res))
        else:
            # Category lanes (industry-friendly default): Network -> Security -> Compute -> Data...
            for lane in lanes:
                providers = grouped_lanes.get(lane) or {}
                if not providers:
                    continue
                with Cluster(lane):
                    for provider, resources in sorted(providers.items()):
                        with Cluster(provider):
                            for res in sorted(resources):
                                r_type, _name = res.split(".", 1)
                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                node_by_res[res] = Icon(_tf_node_label(res))

        for src_res, dst_res in sorted(edges):
            if src_res in node_by_res and dst_res in node_by_res:
                node_by_res[src_res] >> node_by_res[dst_res]

    if outformat == "svg":
        _embed_images_in_svg(out_path)


def _static_terraform_mermaid(files: list[Path], direction: str, limits: Limits) -> tuple[str, str, str]:
    if hcl2 is None:
        raise RuntimeError("Missing dependency python-hcl2. Install it to enable Terraform static diagrams.")

    all_resources: dict[str, dict[str, Any]] = {}
    for f in files:
        if f.suffix not in {".tf", ".hcl"}:
            continue
        try:
            text = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
            parsed = hcl2.loads(text)
        except Exception:
            # Skip unparseable files to keep the workflow resilient.
            continue
        all_resources.update(_terraform_resources_from_hcl(parsed))

    if not all_resources:
        raise RuntimeError("No Terraform resources parsed from the changed files.")

    node_id_by_res: dict[str, str] = {res: _safe_node_id(f"tf_{res}") for res in all_resources.keys()}
    groups: dict[str, list[str]] = {}
    edges: set[tuple[str, str]] = set()

    for res, attrs in all_resources.items():
        r_type, _name = res.split(".", 1)
        provider = _guess_provider(r_type)
        groups.setdefault(provider, []).append(res)

        refs = set()
        refs |= _extract_tf_resource_refs(attrs)
        depends_on = attrs.get("depends_on")
        if depends_on is not None:
            refs |= _extract_tf_resource_refs(depends_on)

        for ref in sorted(refs):
            if ref == res:
                continue
            if ref in all_resources:
                edges.add((node_id_by_res[ref], node_id_by_res[res]))

    lines: list[str] = [f"flowchart {direction}"]

    for provider, resources in sorted(groups.items()):
        lines.append(f"subgraph {provider}[{provider}]")
        for res in sorted(resources):
            label = res
            lines.append(f"  {node_id_by_res[res]}[\"{label}\"]")
        lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{src} --> {dst}")

    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a dependency-oriented Terraform diagram from changed resources."
    assumptions = "Connections represent inferred references (including depends_on and attribute references)."
    return mermaid, summary, assumptions


def _static_terraform_graph(files: list[Path], limits: Limits) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    if hcl2 is None:
        raise RuntimeError("Missing dependency python-hcl2. Install it to enable Terraform static diagrams.")

    all_resources: dict[str, dict[str, Any]] = {}
    for f in files:
        if f.suffix not in {".tf", ".hcl"}:
            continue
        try:
            text = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
            parsed = hcl2.loads(text)
        except Exception:
            continue
        all_resources.update(_terraform_resources_from_hcl(parsed))

    if not all_resources:
        raise RuntimeError("No Terraform resources parsed from the changed files.")

    edges: set[tuple[str, str]] = set()
    for res, attrs in all_resources.items():
        refs = set()
        refs |= _extract_tf_resource_refs(attrs)
        depends_on = attrs.get("depends_on")
        if depends_on is not None:
            refs |= _extract_tf_resource_refs(depends_on)
        for ref in sorted(refs):
            if ref in all_resources and ref != res:
                edges.add((ref, res))
    return all_resources, edges


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
                for m in re.finditer(r"\$\{([A-Za-z0-9]+)(?:\.[^\}]+)?\}", item["Fn::Sub"]):
                    refs.add(m.group(1))
        elif isinstance(item, str):
            for m in re.finditer(r"\$\{([A-Za-z0-9]+)(?:\.[^\}]+)?\}", item):
                refs.add(m.group(1))
    return refs


def _static_cloudformation_mermaid(files: list[Path], direction: str, limits: Limits) -> tuple[str, str, str]:
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
                templates.append(yaml.safe_load(raw) or {})
        except Exception:
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

    node_id_by_res: dict[str, str] = {rid: _safe_node_id(f"cfn_{rid}") for rid in resources.keys()}
    groups: dict[str, list[str]] = {}
    edges: set[tuple[str, str]] = set()

    for rid, body in resources.items():
        rtype = body.get("Type")
        service = "CFN"
        if isinstance(rtype, str) and "::" in rtype:
            parts = rtype.split("::")
            if len(parts) >= 2:
                service = parts[1]
        groups.setdefault(service, []).append(rid)

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

    for service, rids in sorted(groups.items()):
        lines.append(f"subgraph {service}[{service}]")
        for rid in sorted(rids):
            rtype = resources[rid].get("Type")
            label = f"{rid}\\n{rtype}" if isinstance(rtype, str) else rid
            lines.append(f"  {node_id_by_res[rid]}[\"{label}\"]")
        lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{src} --> {dst}")

    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a dependency-oriented CloudFormation diagram from changed resources."
    assumptions = "Connections represent inferred references via Ref/GetAtt/Sub and DependsOn."
    return mermaid, summary, assumptions


def _static_cloudformation_graph(files: list[Path], limits: Limits) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
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
                templates.append(yaml.safe_load(raw) or {})
        except Exception:
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


def _static_bicep_graph(files: list[Path], limits: Limits) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    resources: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()

    # Very small, best-effort parser:
    # - resource <symbol> '<type>@<api>' = { ... }
    # - dependsOn: [ <symbol> ... ]
    # - parent: <symbol>
    res_re = re.compile(r"^\s*resource\s+(?P<sym>[A-Za-z_][A-Za-z0-9_]*)\s+'(?P<type>[^']+)'", re.IGNORECASE)
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


def _static_pulumi_yaml_graph(files: list[Path], limits: Limits) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    stacks: list[dict[str, Any]] = []
    for f in files:
        name = f.name
        if name not in {"Pulumi.yaml", "Pulumi.yml"} and not name.lower().endswith(".pulumi.yaml") and not name.lower().endswith(".pulumi.yml"):
            continue
        raw = _read_file_limited(f, max_bytes=limits.max_bytes_per_file)
        try:
            stacks.append(yaml.safe_load(raw) or {})
        except Exception:
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
        refs |= _pulumi_yaml_extract_refs(b.get("properties") if isinstance(b, dict) else None)
        if isinstance(depends_on, str):
            refs.add(depends_on)
        elif isinstance(depends_on, list):
            refs |= {x for x in depends_on if isinstance(x, str)}

        for ref in sorted(refs):
            if ref in resources and ref != name:
                edges.add((ref, name))

    return resources, edges


def _static_bicep_mermaid(files: list[Path], direction: str, limits: Limits) -> tuple[str, str, str]:
    resources, edges = _static_bicep_graph(files, limits)
    node_id_by_res: dict[str, str] = {rid: _safe_node_id(f"bicep_{rid}") for rid in resources.keys()}

    lines: list[str] = [f"flowchart {direction}", "subgraph Azure[Azure]"]
    for rid in sorted(resources.keys()):
        rtype = resources[rid].get("Type")
        label = f"{rid}\\n{rtype}" if isinstance(rtype, str) else rid
        lines.append(f"  {node_id_by_res[rid]}[\"{label}\"]")
    lines.append("end")

    for src, dst in sorted(edges):
        lines.append(f"{node_id_by_res[src]} --> {node_id_by_res[dst]}")

    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a best-effort Bicep dependency diagram (dependsOn/parent)."
    assumptions = "Connections represent explicit dependsOn/parent references; implicit property references are not fully resolved."
    return mermaid, summary, assumptions


def _static_pulumi_yaml_mermaid(files: list[Path], direction: str, limits: Limits) -> tuple[str, str, str]:
    resources, edges = _static_pulumi_yaml_graph(files, limits)
    node_id_by_res: dict[str, str] = {rid: _safe_node_id(f"pulumi_{rid}") for rid in resources.keys()}
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
            lines.append(f"  {node_id_by_res[rid]}[\"{label}\"]")
        lines.append("end")
    for src, dst in sorted(edges):
        lines.append(f"{node_id_by_res[src]} --> {node_id_by_res[dst]}")
    mermaid = "\n".join(lines) + "\n"
    summary = "Generated a Pulumi YAML diagram from resources and dependsOn/reference expressions."
    assumptions = "Connections represent options.dependsOn and ${resource.property} references in YAML."
    return mermaid, summary, assumptions


def _static_markdown(
    changed_paths: list[Path],
    direction: str,
    limits: Limits,
    *,
    out_png: Path | None,
    out_jpg: Path | None,
    out_svg: Path | None,
    render: RenderConfig,
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

    try:
        tf_resources, tf_edges = _static_terraform_graph(changed_paths, limits)
        mermaid, summary, assumptions = _static_terraform_mermaid(changed_paths, direction, limits)
        diag_kind = "terraform"
    except Exception:
        pass

    if mermaid is None:
        try:
            cfn_resources, cfn_edges = _static_cloudformation_graph(changed_paths, limits)
            mermaid, summary, assumptions = _static_cloudformation_mermaid(changed_paths, direction, limits)
            diag_kind = "cloudformation"
        except Exception as exc:
            # try bicep
            try:
                bicep_resources, bicep_edges = _static_bicep_graph(changed_paths, limits)
                mermaid, summary, assumptions = _static_bicep_mermaid(changed_paths, direction, limits)
                diag_kind = "bicep"
            except Exception:
                try:
                    pulumi_resources, pulumi_edges = _static_pulumi_yaml_graph(changed_paths, limits)
                    mermaid, summary, assumptions = _static_pulumi_yaml_mermaid(changed_paths, direction, limits)
                    diag_kind = "pulumi"
                except Exception:
                    reason = str(exc) or "No supported IaC parsers produced a diagram."
                    return (_fallback_markdown([p.as_posix() for p in changed_paths], reason), "")

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
        except Exception:
            # Keep Mermaid output even if Graphviz/diagrams fails.
            pass

    # For CloudFormation, we don't have provider-wide icon mapping yet; render a generic diagram.
    if diag_kind == "cloudformation" and cfn_resources is not None and cfn_edges is not None:
        try:
            if Diagram is not None and Cluster is not None and out_png is not None:
                outformat = out_png.suffix.lstrip(".").lower() or "png"
                filename_no_ext = str(out_png.with_suffix(""))
                node_by_id: dict[str, Any] = {}
                
                # Analyze CloudFormation diagram complexity
                grouped_simple = {"CloudFormation": {"AWS": list(cfn_resources.keys())}}
                cfn_complexity = _analyze_diagram_complexity(cfn_resources, cfn_edges, grouped_simple)
                cfn_spacing = _calculate_dynamic_spacing(cfn_complexity, render, direction)
                
                # Use auto-calculated spacing or manual overrides
                cfn_pad = cfn_spacing["pad"] if render.pad == "auto" else float(render.pad)
                cfn_nodesep = cfn_spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
                cfn_ranksep = cfn_spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
                
                # Determine background color
                desired_bg = (os.getenv("AUTO_ARCH_RENDER_BG") or render.background or "transparent").strip().lower()
                desired_bg = "transparent" if desired_bg not in {"transparent", "white"} else desired_bg
                bgcolor = "white" if outformat in {"jpg", "jpeg"} else desired_bg
                
                graph_attr = {
                    "bgcolor": bgcolor,
                    "pad": str(cfn_pad),
                    "nodesep": str(cfn_nodesep),
                    "ranksep": str(cfn_ranksep),
                    "splines": render.edge_routing,
                    "concentrate": "true" if render.concentrate else "false",
                    "fontname": render.fontname,
                    "fontsize": str(render.graph_fontsize),
                    "outputorder": "edgesfirst",
                    "overlap": render.overlap_removal,
                    "overlap_scaling": "-4" if render.overlap_removal != "false" else "0",
                    "sep": f"+{int(cfn_nodesep * 20)}",
                    "esep": f"+{int(cfn_nodesep * 10)}",
                    "labelloc": "t",
                    "labeljust": "c",
                    "smoothing": "spring" if cfn_complexity.edge_count > 10 else "none",
                    "mclimit": "2.0",
                    "nslimit": "2.0",
                    "remincross": "true",
                    "searchsize": "50",
                }
                node_attr = {
                    "fontname": render.fontname,
                    "fontsize": str(render.node_fontsize),
                    "labelloc": "b",
                    "labeljust": "c",
                    "imagescale": "true",
                    "fixedsize": "true",
                    "width": str(render.node_width),
                    "height": str(render.node_height),
                    "shape": "box",
                    "style": "rounded",
                    "margin": "0.05",
                    "fillcolor": bgcolor if outformat in {"jpg", "jpeg"} else "transparent",
                    "color": "#D1D5DB",
                    "penwidth": "1",
                }
                edge_attr = {
                    "color": render.edge_color,
                    "penwidth": str(render.edge_penwidth),
                    "arrowsize": str(render.edge_arrowsize),
                    "constraint": "true",
                    "minlen": "2" if cfn_complexity.edge_count > 20 else "1",
                    "weight": "1",
                }
                with Diagram(
                    "Architecture (CloudFormation)",
                    show=False,
                    direction=direction,
                    outformat=outformat,
                    filename=filename_no_ext,
                    graph_attr=graph_attr,
                    node_attr=node_attr,
                    edge_attr=edge_attr,
                ):
                    with Cluster("CloudFormation"):
                        for rid in sorted(cfn_resources.keys()):
                            label = _wrap_text(rid, max_width=14, max_lines=2)
                            node_by_id[rid] = (_generic_icon_for_kind("compute") or (lambda x: x))(label)
                    for src, dst in sorted(cfn_edges):
                        if src in node_by_id and dst in node_by_id:
                            node_by_id[src] >> node_by_id[dst]
                rendered_any = True
                if outformat == "svg":
                    _embed_images_in_svg(out_png)
        except Exception:
            pass

    md = (
        f"{COMMENT_MARKER}\n\n"
        f"## Architecture Diagram (Auto)\n\n"
        f"Summary: {summary}\n\n"
        f"```mermaid\n{mermaid}```\n\n"
        f"Assumptions: {assumptions}\n\n"
        f"Rendered diagram: {'available as workflow artifact' if rendered_any else 'not available (icons require Graphviz + diagrams)'}\n"
    )
    return (md, mermaid)


def _split_changed_files(changed_files_raw: str) -> list[str]:
    if not changed_files_raw:
        return []
    # tj-actions/changed-files returns a space-separated list by default.
    parts = [p.strip() for p in re.split(r"\s+", changed_files_raw) if p.strip()]
    # Normalize path separators for repo-local reads.
    return [p.replace("\\", "/") for p in parts]


_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?ix)"
    r"(password|passwd|secret|token|access[_-]?key|secret[_-]?key|private[_-]?key)"
    r"\s*([:=])\s*"
    r"(\"[^\"]*\"|'[^']*'|[^\s\n\r#]+)"
)


def _redact_likely_secrets(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        key, sep = m.group(1), m.group(2)
        return f"{key}{sep}<REDACTED>"

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


def _build_prompt(changed_files: list[Path], direction: str, file_snippets: dict[str, str]) -> list[dict[str, str]]:
    file_list = "\n".join(f"- {p.as_posix()}" for p in changed_files)
    snippets = []
    for filename, contents in file_snippets.items():
        snippets.append(
            f"FILE: {filename}\n" f"---\n{contents}\n---\n"
        )
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
    m = re.search(r"```mermaid\s*(.*?)\s*```", markdown, flags=re.DOTALL | re.IGNORECASE)
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
    parser = argparse.ArgumentParser(description="Generate a Mermaid architecture diagram from changed IaC files")
    parser.add_argument("--changed-files", default="", help="Space/newline-separated list of changed IaC files")
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
    args = parser.parse_args()

    repo_root = Path.cwd()
    direction, config_mode, config_model, limits, publish, render = _load_config(repo_root)

    # Direction override: CLI arg > env var > config.
    direction_override = (args.direction or os.getenv("AUTO_ARCH_DIRECTION") or "").strip().upper()
    if direction_override:
        if direction_override not in {"LR", "RL", "TB", "BT"}:
            direction_override = "LR"
        direction = direction_override

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
        )

    mode = (os.getenv("AUTO_ARCH_MODE") or config_mode or DEFAULT_MODE).strip().lower()
    model = (os.getenv("AUTO_ARCH_MODEL") or config_model or DEFAULT_MODEL).strip()
    changed_files = _split_changed_files(args.changed_files)

    iac_root = (repo_root / args.iac_root).resolve()

    out_md = repo_root / args.out_md
    out_mmd = repo_root / args.out_mmd

    out_png_raw = (args.out_png or "").strip()
    out_jpg_raw = (args.out_jpg or "").strip()
    out_svg_raw = (args.out_svg or "").strip()
    out_png = (repo_root / out_png_raw) if out_png_raw else None
    out_jpg = (repo_root / out_jpg_raw) if out_jpg_raw else None
    out_svg = (repo_root / out_svg_raw) if out_svg_raw else None

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_mmd.parent.mkdir(parents=True, exist_ok=True)
    if out_png is not None:
        out_png.parent.mkdir(parents=True, exist_ok=True)
    if out_jpg is not None:
        out_jpg.parent.mkdir(parents=True, exist_ok=True)
    if out_svg is not None:
        out_svg.parent.mkdir(parents=True, exist_ok=True)

    if not changed_files:
        out_md.write_text(_fallback_markdown([], "No IaC file changes detected."), encoding="utf-8")
        out_mmd.write_text("", encoding="utf-8")
        if out_png is not None:
            out_png.write_bytes(b"")
        if out_jpg is not None:
            out_jpg.write_bytes(b"")
        if out_svg is not None:
            out_svg.write_text("", encoding="utf-8")
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
        out_md.write_text(_fallback_markdown([], "No valid IaC file paths after sanitization."), encoding="utf-8")
        out_mmd.write_text("", encoding="utf-8")
        if out_png is not None:
            out_png.write_bytes(b"")
        if out_jpg is not None:
            out_jpg.write_bytes(b"")
        if out_svg is not None:
            out_svg.write_text("", encoding="utf-8")
        return 0

    if mode != "ai":
        md, mermaid = _static_markdown(
            changed_paths,
            direction,
            limits,
            out_png=out_png,
            out_jpg=out_jpg,
            out_svg=out_svg,
            render=render,
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
        )
        return 0

    file_snippets: dict[str, str] = {}
    for p in changed_paths:
        if not p.exists() or not p.is_file():
            file_snippets[p.as_posix()] = "<ERROR: file not found in checkout>"
            continue
        file_snippets[p.as_posix()] = _read_file_limited(p, max_bytes=limits.max_bytes_per_file)

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key or OpenAI is None:
        reason = "Missing OPENAI_API_KEY (or OpenAI client unavailable). Set it as a repo secret to enable generation."
        out_md.write_text(_fallback_markdown(selected, reason), encoding="utf-8")
        out_mmd.write_text("", encoding="utf-8")
        return 0

    client = OpenAI(api_key=api_key)
    messages = _build_prompt(changed_paths, direction, file_snippets)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        markdown = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        out_md.write_text(_fallback_markdown(selected, f"OpenAI request failed: {exc}"), encoding="utf-8")
        out_mmd.write_text("", encoding="utf-8")
        return 0

    if COMMENT_MARKER not in markdown:
        markdown = f"{COMMENT_MARKER}\n\n" + markdown

    mermaid = _extract_mermaid(markdown)
    if mermaid is None:
        out_md.write_text(_fallback_markdown(selected, "Model response did not contain a Mermaid code block."), encoding="utf-8")
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
