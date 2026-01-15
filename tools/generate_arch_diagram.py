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
    background: str = "transparent"  # transparent | white
    fontname: str = "Helvetica-Bold"
    graph_fontsize: int = 12
    node_fontsize: int = 9
    node_width: float = 0.7
    node_height: float = 0.7
    edge_color: str = "#8D96A77B"
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
        except Exception:  # nosec B110
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
                import sys
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
            return f'xlink:href="data:{mime};base64,{b64}"'
        except Exception:
            return m.group(0)

    updated = re.sub(r'xlink:href="([^"]+)"', replace_match, content)
    if updated != content:
        try:
            svg_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"Debug: Failed to write updated SVG: {e}")


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


def _determine_optimal_direction(
    complexity: DiagramComplexity,
    grouped_data: dict[str, dict[str, list[str]]],
    layout: str,
) -> str:
    """Intelligently determine the best diagram direction based on architecture characteristics.
    
    Returns 'LR' (horizontal) or 'TB' (vertical) based on:
    - Number of lanes/clusters (wide architectures → LR)
    - Node distribution (many providers → LR, deep nesting → TB)
    - Overall complexity (large diagrams often better horizontal)
    - Edge patterns (highly connected → TB for clarity)
    """
    
    # Count lanes and providers
    lane_count = len(grouped_data)
    provider_count = complexity.provider_count
    
    # Calculate cluster width (avg resources per cluster)
    total_resources = complexity.node_count
    avg_resources_per_cluster = total_resources / max(complexity.cluster_count, 1)
    
    # Decision factors (scoring system)
    lr_score = 0
    tb_score = 0
    
    # Factor 1: Wide architectures (many lanes/providers) work better horizontally
    if lane_count >= 4 or provider_count >= 3:
        lr_score += 2
    elif lane_count <= 2 and provider_count <= 2:
        tb_score += 1
    
    # Factor 2: Deep nesting suggests vertical layout for clarity
    if complexity.max_cluster_depth >= 3:
        tb_score += 2
    else:
        lr_score += 1
    
    # Factor 3: Large node counts (>30) often benefit from horizontal spread
    if complexity.node_count > 30:
        lr_score += 2
    elif complexity.node_count < 15:
        tb_score += 1
    
    # Factor 4: High edge density benefits from vertical to reduce crossings
    if complexity.avg_edges_per_node > 3.0:
        tb_score += 1
    elif complexity.avg_edges_per_node < 2.0:
        lr_score += 1
    
    # Factor 5: Many small clusters → horizontal, few large clusters → vertical
    if avg_resources_per_cluster < 5 and complexity.cluster_count > 5:
        lr_score += 1
    elif avg_resources_per_cluster > 10:
        tb_score += 1
    
    # Factor 6: Provider-based layout tends to work better vertically
    if layout == "providers":
        tb_score += 1
    else:
        lr_score += 1
    
    # Make decision based on scores
    if lr_score > tb_score:
        direction = "LR"
        reason = "horizontal (wide architecture)"
    elif tb_score > lr_score:
        direction = "TB"
        reason = "vertical (deep nesting)"
    else:
        # Tie-breaker: default to LR for most cloud architectures
        direction = "LR"
        reason = "horizontal (default for cloud)"
    
    # Debug output
    if os.getenv("AUTO_ARCH_DEBUG"):
        print(f"[Auto Direction] Scores: LR={lr_score}, TB={tb_score}")
        print(f"[Auto Direction] Selected: {direction} ({reason})")
        print(f"[Auto Direction] Factors: lanes={lane_count}, providers={provider_count}, "
              f"nodes={complexity.node_count}, depth={complexity.max_cluster_depth}, "
              f"edges/node={complexity.avg_edges_per_node:.1f}")
    
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
    nodesep_value = render.min_nodesep * multipliers["nodesep"] * 0.7  # Compact node separation
    ranksep_value = render.min_ranksep * multipliers["ranksep"] * 0.7  # Tight rank separation
    
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
        except Exception:  # nosec B110
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


def _detect_edge_type(from_res: str, to_res: str, all_resources: dict[str, dict[str, Any]]) -> str:
    """Detect the type of connection between two resources for intelligent edge styling.
    Returns: 'security', 'data', 'dependency', or 'network'
    """
    from_type = from_res.split(".", 1)[0].lower()
    to_type = to_res.split(".", 1)[0].lower()
    
    # Security connections (firewall, security groups, IAM, etc.)
    security_keywords = ["security", "firewall", "iam", "kms", "key", "policy", "role", "nsg", "nacl", "waf"]
    if any(k in from_type or k in to_type for k in security_keywords):
        return "security"
    
    # Data flow connections (databases, storage, queues, streams)
    data_keywords = ["db", "database", "rds", "dynamodb", "sql", "storage", "bucket", "s3", "blob",
                     "queue", "stream", "kinesis", "eventgrid", "pubsub", "cosmos", "redis", "elasticache"]
    if any(k in from_type or k in to_type for k in data_keywords):
        return "data"
    
    # Check for cross-provider connections (should be dotted for logical dependency)
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
    elif edge_type == "data":
        # Bold lines for data flow
        base_attrs["style"] = render.edge_style_data
        base_attrs["color"] = "#BFDDF697"  # Blue for data
        base_attrs["penwidth"] = str(render.edge_penwidth * 1.5)
    elif edge_type == "dependency":
        # Dotted lines for logical dependencies (cross-cloud, cross-region)
        base_attrs["style"] = render.edge_style_dependency
        base_attrs["color"] = "#9E9E9E9D"  # Gray for dependencies
    else:  # network
        # Solid lines for network connections (default)
        base_attrs["style"] = render.edge_style_network
    
    return base_attrs


def _get_provider_icon_path(provider: str) -> str | None:
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
    
    # Default professional light gray
    return "#F8F9FA"


def _detect_edge_type(from_res: str, to_res: str, all_resources: dict[str, dict[str, Any]]) -> str:
    """Detect the type of connection between two resources for intelligent edge styling.
    Returns: 'security', 'data', 'dependency', or 'network'
    """
    from_type = from_res.split(".", 1)[0].lower()
    to_type = to_res.split(".", 1)[0].lower()
    
    # Security connections (firewall, security groups, IAM, etc.)
    security_keywords = ["security", "firewall", "iam", "kms", "key", "policy", "role", "nsg", "nacl"]
    if any(k in from_type or k in to_type for k in security_keywords):
        return "security"
    
    # Data flow connections (databases, storage, queues, streams)
    data_keywords = ["db", "database", "rds", "dynamodb", "sql", "storage", "bucket", "s3", "blob",
                     "queue", "stream", "kinesis", "eventgrid", "pubsub", "cosmos", "redis"]
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
    elif edge_type == "data":
        # Bold lines for data flow
        base_attrs["style"] = render.edge_style_data
        base_attrs["color"] = "#2196F3"  # Blue for data
        base_attrs["penwidth"] = str(render.edge_penwidth * 1.5)
    elif edge_type == "dependency":
        # Dotted lines for logical dependencies (cross-cloud, cross-region)
        base_attrs["style"] = render.edge_style_dependency
        base_attrs["color"] = "#9E9E9E"  # Gray for dependencies
    else:  # network
        # Solid lines for network connections (default)
        base_attrs["style"] = render.edge_style_network
    
    return base_attrs


def _is_vpc_or_network(resource_type: str) -> bool:
    """Check if a resource is a VPC/VNet/Network container."""
    t = resource_type.lower()
    # Check if it's a VPC/VNet/Network AND not a subnet or interface
    is_network = any(k in t for k in ["vpc", "vnet", "vcn", "virtual_network"])
    is_not_subnet = "subnet" not in t and "interface" not in t
    return is_network and is_not_subnet


def _is_subnet(resource_type: str) -> bool:
    """Check if a resource is a subnet."""
    return "subnet" in resource_type.lower()


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
    
    # Build subnet-to-VPC mapping from edges
    subnet_to_vpc: dict[str, str] = {}
    for src, dst in edges:
        if src in vpcs and dst in subnets:
            subnet_to_vpc[dst] = src
        elif dst in vpcs and src in subnets:
            subnet_to_vpc[src] = dst
    
    # Also check subnet attributes for VPC references
    for subnet_name, subnet_attrs in subnets.items():
        if subnet_name in subnet_to_vpc:
            continue
        if isinstance(subnet_attrs, dict):
            # Check for vpc_id reference
            vpc_ref = None
            for key in ["vpc_id", "virtual_network_name", "vcn_id"]:
                if key in subnet_attrs:
                    ref_val = subnet_attrs[key]
                    if isinstance(ref_val, str):
                        # Extract VPC reference (e.g., "aws_vpc.main" from "${aws_vpc.main.id}")
                        refs = _extract_tf_resource_refs(ref_val)
                        for ref in refs:
                            if ref in vpcs:
                                vpc_ref = ref
                                break
            if vpc_ref:
                subnet_to_vpc[subnet_name] = vpc_ref
    
    # Build resource-to-subnet mapping
    resource_to_subnet: dict[str, str] = {}
    for src, dst in edges:
        if src in subnets and dst not in vpcs and dst not in subnets:
            resource_to_subnet[dst] = src
        elif dst in subnets and src not in vpcs and src not in subnets:
            resource_to_subnet[src] = dst
    
    # Check resource attributes for subnet references
    for res_name, res_attrs in all_resources.items():
        if res_name in vpcs or res_name in subnets:
            continue
        if res_name in resource_to_subnet:
            continue
        if isinstance(res_attrs, dict):
            subnet_ref = None
            for key in ["subnet_id", "subnet_ids", "subnet", "subnets"]:
                if key in res_attrs:
                    refs = _extract_tf_resource_refs(res_attrs[key])
                    for ref in refs:
                        if ref in subnets:
                            subnet_ref = ref
                            break
            if subnet_ref:
                resource_to_subnet[res_name] = subnet_ref
    
    # Build the hierarchy
    for vpc_name in vpcs:
        vpc_hierarchy[vpc_name] = {}
        # Find subnets in this VPC
        for subnet_name, parent_vpc in subnet_to_vpc.items():
            if parent_vpc == vpc_name:
                vpc_hierarchy[vpc_name][subnet_name] = []
                # Find resources in this subnet
                for res_name, parent_subnet in resource_to_subnet.items():
                    if parent_subnet == subnet_name:
                        vpc_hierarchy[vpc_name][subnet_name].append(res_name)
        
        # Add "other" category for VPC-level resources not in subnets
        other_resources = []
        for src, dst in edges:
            if src == vpc_name and dst not in subnets and dst not in vpcs:
                if dst not in resource_to_subnet:
                    other_resources.append(dst)
            elif dst == vpc_name and src not in subnets and src not in vpcs:
                if src not in resource_to_subnet:
                    other_resources.append(src)
        if other_resources:
            vpc_hierarchy[vpc_name]["other"] = other_resources
    
    return vpc_hierarchy


def _get_cluster_color(cluster_name: str, render: RenderConfig) -> str:
    """Get appropriate color for cluster based on its type and cloud provider."""
    name_lower = cluster_name.lower()
    
    # Cloud provider colors
    if "aws" in name_lower:
        return render.color_aws
    if "azure" in name_lower:
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

    # AWS - Enhanced mapping with comprehensive networking and security icons
    if t.startswith("aws_"):
        mapping = {
            # Network resources
            "aws_vpc": ("diagrams.aws.network", "VPC"),
            "aws_subnet": ("diagrams.aws.network", "PrivateSubnet"),
            "aws_internet_gateway": ("diagrams.aws.network", "InternetGateway"),
            "aws_nat_gateway": ("diagrams.aws.network", "NATGateway"),
            "aws_route_table": ("diagrams.aws.network", "RouteTable"),
            "aws_route53_zone": ("diagrams.aws.network", "Route53"),
            "aws_route53_record": ("diagrams.aws.network", "Route53"),
            "aws_vpn_gateway": ("diagrams.aws.network", "VpnGateway"),
            "aws_vpn_connection": ("diagrams.aws.network", "VpnConnection"),
            "aws_customer_gateway": ("diagrams.aws.network", "CustomerGateway"),
            "aws_vpc_peering_connection": ("diagrams.aws.network", "VPCPeering"),
            "aws_transit_gateway": ("diagrams.aws.network", "TransitGateway"),
            "aws_network_interface": ("diagrams.aws.network", "ElasticNetworkInterface"),
            "aws_cloudfront_distribution": ("diagrams.aws.network", "CloudFront"),
            "aws_api_gateway_rest_api": ("diagrams.aws.network", "APIGateway"),
            
            # Load balancers
            "aws_lb": ("diagrams.aws.network", "ELB"),
            "aws_alb": ("diagrams.aws.network", "ApplicationLoadBalancer"),
            "aws_elb": ("diagrams.aws.network", "ElasticLoadBalancing"),
            "aws_network_load_balancer": ("diagrams.aws.network", "NetworkLoadBalancer"),
            
            # Security resources
            "aws_security_group": ("diagrams.aws.security", "SecurityGroup"),
            "aws_network_acl": ("diagrams.aws.security", "NetworkAccessControlList"),
            "aws_iam_role": ("diagrams.aws.security", "IAMRole"),
            "aws_iam_policy": ("diagrams.aws.security", "IAMPermissions"),
            "aws_iam_user": ("diagrams.aws.security", "IAM"),
            "aws_iam_group": ("diagrams.aws.security", "IAM"),
            "aws_kms_key": ("diagrams.aws.security", "KMS"),
            "aws_waf_web_acl": ("diagrams.aws.security", "WAF"),
            "aws_shield_protection": ("diagrams.aws.security", "Shield"),
            "aws_secrets_manager_secret": ("diagrams.aws.security", "SecretsManager"),
            
            # Compute resources
            "aws_instance": ("diagrams.aws.compute", "EC2"),
            "aws_autoscaling_group": ("diagrams.aws.compute", "AutoScaling"),
            "aws_eks_cluster": ("diagrams.aws.compute", "EKS"),
            "aws_ecs_cluster": ("diagrams.aws.compute", "ECS"),
            "aws_ecs_service": ("diagrams.aws.compute", "ECS"),
            "aws_lambda_function": ("diagrams.aws.compute", "Lambda"),
            "aws_batch_job_queue": ("diagrams.aws.compute", "Batch"),
            
            # Storage resources
            "aws_s3_bucket": ("diagrams.aws.storage", "S3"),
            "aws_ebs_volume": ("diagrams.aws.storage", "EBS"),
            "aws_efs_file_system": ("diagrams.aws.storage", "EFS"),
            "aws_fsx_windows_file_system": ("diagrams.aws.storage", "Fsx"),
            
            # Database resources
            "aws_dynamodb_table": ("diagrams.aws.database", "Dynamodb"),
            "aws_db_instance": ("diagrams.aws.database", "RDS"),
            "aws_rds_cluster": ("diagrams.aws.database", "Aurora"),
            "aws_elasticache_cluster": ("diagrams.aws.database", "ElastiCache"),
            "aws_elasticache_replication_group": ("diagrams.aws.database", "ElasticacheForRedis"),
            "aws_redshift_cluster": ("diagrams.aws.database", "Redshift"),
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
        # Professional edge routing from centers
        "smoothing": "spring" if complexity.edge_count > 10 else "none",
        "mclimit": "2.0",
        "nslimit": "2.0",
        "remincross": "true",
        "searchsize": "50",
        # Center-based edge connections
        "center": "true",
        "forcelabels": "true",  # Force xlabels to show
    }
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
        "minlen": "2" if complexity.edge_count > 20 else "1",
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

    # Build VPC hierarchy for best-practice network grouping
    vpc_hierarchy = _build_vpc_hierarchy(all_resources, edges)
    
    # Track which resources are already rendered in VPCs
    resources_in_vpcs: set[str] = set()
    for vpc_name, subnets_dict in vpc_hierarchy.items():
        resources_in_vpcs.add(vpc_name)
        for subnet_name, subnet_resources in subnets_dict.items():
            if subnet_name != "other":
                resources_in_vpcs.add(subnet_name)
            resources_in_vpcs.update(subnet_resources)
    
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
        # Helper function to render provider icon + label cluster
        def render_provider_cluster(provider: str, cluster_color: str, penwidth: str = "0.5"):
            # Create provider label with colored border
            provider_icon_path = _get_provider_icon_path(provider)
            if provider_icon_path:
                # Use Custom node for provider badge with icon
                try:
                    Custom = _import_node_class("diagrams", "Custom")
                    if Custom:
                        # Create invisible provider badge node
                        provider_badge = Custom("", provider_icon_path)
                except Exception:  # nosec B110
                    pass
            
            # Map provider to border color
            border_colors = {
                "AWS": "#FFE7C4B6",  # AWS orange
                "AZURERM": "#9BD0F9B5",  # Azure blue
                "AZURE": "#A7D6FBAF",  # Azure blue
                "GOOGLE": "#C0D3F3BA",  # GCP blue
                "GCP": "#AAC7F596",  # GCP blue
                "OCI": "#FFCCCC",  # Oracle red
                "IBM": "#BBCEF2AE",  # IBM blue
            }
            border_color = border_colors.get(provider.upper(), "#6C757D")
            
            provider_label = f"{provider} Cloud"
            provider_cluster_attrs = {
                "bgcolor": "#FFFFFF",  # White background
                "style": "rounded,filled",
                "penwidth": "2.5",  # Thicker border for visibility
                "fontsize": "12",
                "fontname": "Helvetica-Bold",
                "color": border_color,  # Colored border
                "labelloc": "t",
                "labeljust": "l",
            }
            return Cluster(provider_label, graph_attr=provider_cluster_attrs)
        
        if layout == "providers":
            # Provider-first: AWS/Azure/GCP/... with category sub-clusters and VPC grouping.
            for provider, categories in sorted(grouped_providers.items()):
                cluster_color = _get_cluster_color(provider, render)
                with render_provider_cluster(provider, cluster_color, penwidth="1.5"):
                    # First render VPC hierarchies for this provider
                    provider_vpcs = {vpc: data for vpc, data in vpc_hierarchy.items() 
                                    if _guess_provider(vpc.split(".", 1)[0]) == provider}
                    
                    for vpc_name, subnets_dict in sorted(provider_vpcs.items()):
                        vpc_label = _tf_node_label(vpc_name)
                        vpc_attrs = {
                            "bgcolor": render.color_vpc,
                            "style": "rounded,filled",
                            "penwidth": "2.0",
                            "color": "#5DADE2",  # AWS VPC blue border
                            "fontsize": "11",
                            "fontname": "Helvetica-Bold",
                        }
                        with Cluster(vpc_label, graph_attr=vpc_attrs):
                            r_type, _name = vpc_name.split(".", 1)
                            Icon = _icon_class_for(r_type) or _generic_icon_for_kind("network")
                            node_by_res[vpc_name] = _create_node_with_xlabel(Icon, _tf_node_label(vpc_name))
                            
                            # Render subnets within VPC
                            for subnet_name, subnet_resources in sorted(subnets_dict.items()):
                                if subnet_name == "other":
                                    # VPC-level resources not in subnets
                                    for res in sorted(subnet_resources):
                                        r_type, _name = res.split(".", 1)
                                        Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                        node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
                                else:
                                    # Subnet cluster
                                    subnet_attrs_dict = all_resources.get(subnet_name, {})
                                    is_public = _is_public_subnet(subnet_name, subnet_attrs_dict)
                                    subnet_color = render.color_public_subnet if is_public else render.color_private_subnet
                                    subnet_label = _tf_node_label(subnet_name) + (" (Public)" if is_public else " (Private)")
                                    subnet_attrs = {
                                        "bgcolor": subnet_color,
                                        "style": "rounded,filled,dashed" if is_public else "rounded,filled",
                                        "penwidth": "1.5",
                                        "color": "#28A745" if is_public else "#FFC107",  # Green for public, amber for private
                                    }
                                    with Cluster(subnet_label, graph_attr=subnet_attrs):
                                        r_type, _name = subnet_name.split(".", 1)
                                        Icon = _icon_class_for(r_type) or _generic_icon_for_kind("network")
                                        node_by_res[subnet_name] = _create_node_with_xlabel(Icon, _tf_node_label(subnet_name))
                                        
                                        # Resources in subnet
                                        for res in sorted(subnet_resources):
                                            r_type, _name = res.split(".", 1)
                                            Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                            node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
                    
                    # Then render category lanes for non-VPC resources
                    for lane in lanes:
                        resources = [r for r in (categories.get(lane) or []) if r not in resources_in_vpcs]
                        if not resources:
                            continue
                        lane_color = _get_cluster_color(lane, render)
                        lane_cluster_attrs = {
                            "bgcolor": lane_color,
                            "style": "rounded,filled",
                            "penwidth": "0.5",
                            "color": "#CCCCCC",
                        }
                        with Cluster(lane, graph_attr=lane_cluster_attrs):
                            for res in sorted(resources):
                                r_type, _name = res.split(".", 1)
                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
        else:
            # Category lanes (industry-friendly default): Network -> Security -> Compute -> Data...
            for lane in lanes:
                providers = grouped_lanes.get(lane) or {}
                if not providers:
                    continue
                lane_color = _get_cluster_color(lane, render)
                lane_cluster_attrs = {
                    "bgcolor": "#FFFFFF",  # White background
                    "style": "rounded,filled",
                    "penwidth": "1.0",
                    "fontsize": "14",
                    "fontname": "Helvetica-Bold",
                    "color": "#CCCCCC",  # Light gray border
                }
                with Cluster(lane, graph_attr=lane_cluster_attrs):
                    for provider, resources in sorted(providers.items()):
                        # Filter out resources already in VPCs
                        provider_resources = [r for r in resources if r not in resources_in_vpcs]
                        
                        # Get VPCs for this provider in this lane
                        provider_vpcs = {vpc: data for vpc, data in vpc_hierarchy.items()
                                        if vpc in resources and _guess_provider(vpc.split(".", 1)[0]) == provider}
                        
                        if not provider_resources and not provider_vpcs:
                            continue
                        
                        cluster_color = _get_cluster_color(provider, render)
                        with render_provider_cluster(provider, cluster_color, penwidth="0.5"):
                            # First render VPCs with their hierarchies
                            for vpc_name, subnets_dict in sorted(provider_vpcs.items()):
                                vpc_label = _tf_node_label(vpc_name)
                                vpc_attrs = {
                                    "bgcolor": render.color_vpc,
                                    "style": "rounded,filled",
                                    "penwidth": "2.0",
                                    "color": "#5DADE2",  # AWS VPC blue border
                                    "fontsize": "11",
                                    "fontname": "Helvetica-Bold",
                                }
                                with Cluster(vpc_label, graph_attr=vpc_attrs):
                                    r_type, _name = vpc_name.split(".", 1)
                                    Icon = _icon_class_for(r_type) or _generic_icon_for_kind("network")
                                    node_by_res[vpc_name] = _create_node_with_xlabel(Icon, _tf_node_label(vpc_name))
                                    
                                    # Render subnets within VPC
                                    for subnet_name, subnet_resources in sorted(subnets_dict.items()):
                                        if subnet_name == "other":
                                            # VPC-level resources
                                            for res in sorted(subnet_resources):
                                                r_type, _name = res.split(".", 1)
                                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                                node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
                                        else:
                                            # Subnet cluster
                                            subnet_attrs_dict = all_resources.get(subnet_name, {})
                                            is_public = _is_public_subnet(subnet_name, subnet_attrs_dict)
                                            subnet_color = render.color_public_subnet if is_public else render.color_private_subnet
                                            subnet_label = _tf_node_label(subnet_name) + (" (Public)" if is_public else " (Private)")
                                            subnet_attrs = {
                                                "bgcolor": subnet_color,
                                                "style": "rounded,filled,dashed" if is_public else "rounded,filled",
                                                "penwidth": "1.5",
                                                "color": "#28A745" if is_public else "#FFC107",  # Green for public, amber for private
                                            }
                                            with Cluster(subnet_label, graph_attr=subnet_attrs):
                                                r_type, _name = subnet_name.split(".", 1)
                                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("network")
                                                node_by_res[subnet_name] = _create_node_with_xlabel(Icon, _tf_node_label(subnet_name))
                                                
                                                # Resources in subnet
                                                for res in sorted(subnet_resources):
                                                    r_type, _name = res.split(".", 1)
                                                    Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                                    node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))
                            
                            # Then render remaining resources not in VPCs
                            for res in sorted(provider_resources):
                                r_type, _name = res.split(".", 1)
                                Icon = _icon_class_for(r_type) or _generic_icon_for_kind("compute")
                                node_by_res[res] = _create_node_with_xlabel(Icon, _tf_node_label(res))

        for src_res, dst_res in sorted(edges):
            if src_res in node_by_res and dst_res in node_by_res:
                # Detect edge type and apply intelligent styling
                edge_type = _detect_edge_type(src_res, dst_res, all_resources)
                edge_style_attrs = _get_edge_style_attrs(edge_type, render)
                
                # Try to apply custom styling using Edge object
                try:
                    from diagrams import Edge
                    node_by_res[src_res] >> Edge(**edge_style_attrs) >> node_by_res[dst_res]
                except (ImportError, TypeError, AttributeError):
                    # Fallback to simple connection if Edge styling not supported
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
        except Exception:  # nosec B112
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
        except Exception:  # nosec B112
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


# CloudFormation intrinsic function handlers for YAML
def _cfn_tag_constructor(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node) -> dict[str, Any]:
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
    loader = type('CFNLoader', (yaml.SafeLoader,), {})
    
    # Register constructors for common CloudFormation intrinsic functions
    cfn_tags = [
        'Ref', 'GetAtt', 'Join', 'Sub', 'Select', 'Split', 'GetAZs',
        'Base64', 'ImportValue', 'FindInMap', 'Cidr', 'Transform',
        'If', 'Equals', 'Not', 'And', 'Or', 'Condition'
    ]
    
    for tag in cfn_tags:
        yaml_tag = f'!{tag}'
        loader.add_constructor(yaml_tag, lambda l, n, t=tag: _cfn_tag_constructor(l, t, n))
    
    # Also handle the Fn:: prefix forms
    for tag in cfn_tags:
        if tag != 'Ref':  # Ref doesn't have Fn:: form
            yaml_tag = f'!Fn::{tag}'
            loader.add_constructor(yaml_tag, lambda l, n, t=f'Fn::{tag}': _cfn_tag_constructor(l, t, n))
    
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
    """Helper function to render CloudFormation diagram in specified format."""
    outformat = out_path.suffix.lstrip(".").lower() or "png"
    filename_no_ext = str(out_path.with_suffix(""))
    node_by_id: dict[str, Any] = {}
    
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
        direction=cfn_direction,
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
    
    # Embed images in SVG files
    if outformat == "svg":
        _embed_images_in_svg(out_path)


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
    except Exception:  # nosec B110
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
        except Exception:  # nosec B110
            # Keep Mermaid output even if Graphviz/diagrams fails.
            pass

    # For CloudFormation, we don't have provider-wide icon mapping yet; render a generic diagram.
    if diag_kind == "cloudformation" and cfn_resources is not None and cfn_edges is not None:
        # Analyze CloudFormation diagram complexity once
        grouped_simple = {"CloudFormation": {"AWS": list(cfn_resources.keys())}}
        cfn_complexity = _analyze_diagram_complexity(cfn_resources, cfn_edges, grouped_simple)
        
        # Auto-detect optimal direction if set to "auto"
        cfn_direction = direction
        if cfn_direction.upper() == "AUTO":
            cfn_direction = _determine_optimal_direction(cfn_complexity, grouped_simple, "lanes")
            if os.getenv("AUTO_ARCH_DEBUG"):
                print(f"[Auto Direction CFN] Changed from 'auto' to '{cfn_direction}'")
        
        cfn_spacing = _calculate_dynamic_spacing(cfn_complexity, render, cfn_direction)
        
        # Use auto-calculated spacing or manual overrides
        cfn_pad = cfn_spacing["pad"] if render.pad == "auto" else float(render.pad)
        cfn_nodesep = cfn_spacing["nodesep"] if render.nodesep == "auto" else float(render.nodesep)
        cfn_ranksep = cfn_spacing["ranksep"] if render.ranksep == "auto" else float(render.ranksep)
        
        try:
            # Render PNG
            if Diagram is not None and Cluster is not None and out_png is not None:
                _render_cfn_diagram(
                    cfn_resources, cfn_edges, out_png, cfn_direction, 
                    cfn_pad, cfn_nodesep, cfn_ranksep, cfn_complexity, render
                )
                rendered_any = True
            
            # Render JPG
            if Diagram is not None and Cluster is not None and out_jpg is not None:
                _render_cfn_diagram(
                    cfn_resources, cfn_edges, out_jpg, cfn_direction,
                    cfn_pad, cfn_nodesep, cfn_ranksep, cfn_complexity, render
                )
                rendered_any = True
            
            # Render SVG
            if Diagram is not None and Cluster is not None and out_svg is not None:
                _render_cfn_diagram(
                    cfn_resources, cfn_edges, out_svg, cfn_direction,
                    cfn_pad, cfn_nodesep, cfn_ranksep, cfn_complexity, render
                )
                rendered_any = True
        except Exception:  # nosec B110
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
        if direction_override not in {"LR", "RL", "TB", "BT", "AUTO"}:
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
