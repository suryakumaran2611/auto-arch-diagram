"""Logic-driven draw.io (diagrams.net) exporter.

Converts the same parsed IaC graph (resources + edges) used by the PNG/SVG
renderers into a fully editable .drawio file that follows the official
draw.io AWS diagram conventions (drawio.com docs and the jgraph/
drawio-diagrams example library):

- Nested group frames use native ``mxgraph.aws4.group`` shapes with the
  official ``grIcon`` glyphs (AWS Cloud / VPC / security-group frames), so
  clusters render and behave exactly like hand-authored draw.io diagrams.
- Resources render as compact 48px icons with short wrapped labels placed
  underneath (``verticalLabelPosition=bottom``) - never raw Terraform
  addresses.
- Grid slots are sized to fit each label, so node labels never overlap a
  neighbouring node or label.
- Connectors are orthogonal with exit/entry hints derived from the final
  geometry, keeping edge routing tidy even on dense diagrams.

Everything is derived from the input architecture - no architecture-specific
hardcoding:

- Grouping reuses the existing VPC/subnet hierarchy, compute subclusters,
  provider and category detection from generate_arch_diagram.
- Icons reuse the exact same resolution pipeline; PNG bytes are located via
  the resolved `diagrams` classes (`_icon_dir`/`_icon`) or the custom icon
  directories, then embedded as base64 data URIs.
"""
from __future__ import annotations

import base64
import math
import uuid
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import sys

_tools_dir = Path(__file__).resolve().parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from drawio_native_shapes import native_icon_size, native_style_for

# Official cloud-provider brand accents (mirrors generate_arch_diagram).
_PROVIDER_BORDER_COLORS = {
    "AWS": "#FF9900",
    "AZURERM": "#0078D4",
    "AZURE": "#0078D4",
    "GOOGLE": "#4285F4",
    "GCP": "#4285F4",
    "OCI": "#C74634",
    "IBM": "#0F62FE",
}

# Ultra-light brand tints for provider group fills on a white canvas
# (mirrors generate_arch_diagram.PROVIDER_TINT_COLORS).
_PROVIDER_TINT_COLORS = {
    "AWS": "#FFF6E8",
    "AZURERM": "#EAF3FB",
    "AZURE": "#EAF3FB",
    "GOOGLE": "#EDF2FE",
    "GCP": "#EDF2FE",
    "OCI": "#FDF0EE",
    "IBM": "#ECF2FD",
}

_LANE_ORDER = (
    "Network",
    "Security",
    "Containers",
    "Compute",
    "Data",
    "Storage",
    "Integration",
    "Management",
    "Other",
)

# Canonical lane order for reference — used to keep deterministic fallback
_LANE_ORDER_INDEX = {name: i for i, name in enumerate(_LANE_ORDER)}


def _optimized_lane_order(
    lanes: list[str],
    lane_edges: dict[tuple[str, str], int],
) -> list[str]:
    """Reorder lanes so heavily-connected lanes are adjacent, minimizing
    long edge crossings. Greedy: start with most-connected lane, then
    repeatedly pick the remaining lane with strongest connection to the
    already-placed set. Falls back to canonical order for stability."""
    if len(lanes) <= 2:
        return sorted(lanes, key=lambda x: _LANE_ORDER_INDEX.get(x, 99))
    # Score each lane by total incident edges
    incident: dict[str, int] = {l: 0 for l in lanes}
    for (a, b), c in lane_edges.items():
        if a in incident:
            incident[a] += c
        if b in incident:
            incident[b] += c
    # Start with most incident
    ordered: list[str] = [max(lanes, key=lambda x: incident[x])]
    remaining = set(lanes) - set(ordered)
    while remaining:
        # Pick lane with max connection to already ordered set
        best = max(
            remaining,
            key=lambda x: sum(
                lane_edges.get((min(x, o), max(x, o)), 0)
                + lane_edges.get((o, x), 0)
                + lane_edges.get((x, o), 0)
                for o in ordered
            ),
        )
        # Tie-break by canonical order for determinism
        candidates = [r for r in remaining if sum(lane_edges.get((min(r, o), max(r, o)), 0) for o in ordered) == sum(lane_edges.get((min(best, o), max(best, o)), 0) for o in ordered)]
        if len(candidates) > 1:
            best = min(candidates, key=lambda x: _LANE_ORDER_INDEX.get(x, 99))
        ordered.append(best)
        remaining.remove(best)
    return ordered

_EDGE_COLORS = {
    "security": "#C62828",
    "data": "#1565C0",
    "dependency": "#9E9E9E",
    "network": "#455A64",
}

# Official draw.io AWS palette used by the aws4 group shapes.
_AWS_SQUID_INK = "#232F3E"
_VPC_GREEN = "#248814"
_SUBNET_BLUE = "#147EBA"
_PUBLIC_SUBNET_FILL = "#E9F3E6"
_PRIVATE_SUBNET_FILL = "#E6F2F8"

# Geometry constants — adaptive to diagram complexity for universally clean layouts.
_ICON_SIZE = 48.0  # resource icon square (px)
_LABEL_FONT = 11  # node label font size (pt)
_CHAR_PX = 6.4  # approx rendered px per character at _LABEL_FONT
_LINE_PX = 14.0  # label line height (px)
_COL_GAP_BASE = 62.0  # base horizontal gap between node slots
_ROW_GAP_BASE = 44.0  # base vertical gap between node rows
_CLUSTER_GAP_BASE = 42.0  # base gap between adjacent cluster frames
_FRAME_PAD = 36.0  # padding inside container frames
_TITLE_H = 44.0  # height reserved for container header
_MAX_COLS = 6  # cap grid columns to keep diagrams readable


def _adaptive_gaps(n_resources: int, n_edges: int) -> tuple[float, float, float]:
    """Scale gaps with diagram density so sparse diagrams stay compact and dense ones breathe."""
    density = n_resources + n_edges * 0.4
    # 0–80 resources → factor 1.0–1.55
    factor = 1.0 + min(0.55, density / 90.0)
    return _COL_GAP_BASE * factor, _ROW_GAP_BASE * factor, _CLUSTER_GAP_BASE * factor


# Back-compat aliases for any external importers.
_COL_GAP = _COL_GAP_BASE
_ROW_GAP = _ROW_GAP_BASE
_CLUSTER_GAP = _CLUSTER_GAP_BASE

_GROUP_POINTS = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],"
    "[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];"
)


def _repo_icons_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "icons"


def _aws_group_style(
    *,
    gr_icon: str,
    stroke: str,
    font_color: str,
    fill: str = "none",
    gr_stroke: int | None = None,
) -> str:
    """Official ``mxgraph.aws4.group`` frame style (jgraph AWS samples)."""
    parts = [
        _GROUP_POINTS,
        "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;",
        f"fontSize=12;fontStyle=0;shape=mxgraph.aws4.group;grIcon={gr_icon};",
    ]
    if gr_stroke is not None:
        parts.append(f"grStroke={gr_stroke};")
    parts += [
        f"strokeColor={stroke};fillColor={fill};fontColor={font_color};dashed=0;",
        "verticalAlign=top;align=left;spacingLeft=34;container=1;collapsible=0;",
    ]
    return "".join(parts)


_AWS_CLOUD_STYLE = _aws_group_style(
    gr_icon="mxgraph.aws4.group_aws_cloud_alt", stroke="#FF9900",
    font_color=_AWS_SQUID_INK,
)
_AWS_VPC_STYLE = _aws_group_style(
    gr_icon="mxgraph.aws4.group_vpc", stroke=_VPC_GREEN, font_color=_VPC_GREEN
)
_AWS_PUBLIC_SUBNET_STYLE = _aws_group_style(
    gr_icon="mxgraph.aws4.group_security_group",
    stroke="#7AA116",
    font_color="#248814",
    fill="#E9F3D2",
    gr_stroke=0,
)
_AWS_PRIVATE_SUBNET_STYLE = _aws_group_style(
    gr_icon="mxgraph.aws4.group_security_group",
    stroke="#00A4A6",
    font_color="#147EBA",
    fill="#E6F6F7",
    gr_stroke=0,
)

_GENERIC_FRAME_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;arcSize=4;verticalAlign=top;align=left;"
    "spacingLeft=10;fontSize=12;fontStyle=1;container=1;collapsible=0;"
)

# Official draw.io shape libraries are resolved via drawio_native_shapes
# (mxgraph.aws4 / azure2 / mxgraph.gcp2); unknown types fall back to the
# embedded PNG icon pipeline below.


class _DrawioExporter:
    def __init__(
        self,
        resources: dict[str, dict[str, Any]],
        edges: set[tuple[str, str]],
        render: Any,
    ):
        from generate_arch_diagram import RenderConfig  # noqa: PLC0415

        self.resources = resources
        self.edges = edges
        self.render = render or RenderConfig()
        self.cells: dict[str, dict[str, Any]] = {}
        self._seq = 0
        self._ids_by_raw: dict[str, str] = {}
        self._used_ids: set[str] = set()
        self._cursor_x = 0.0
        self._max_h = 0.0
        # Adaptive spacing so any architecture — from 3 nodes to 100+ — stays readable.
        self._col_gap, self._row_gap, self._cluster_gap = _adaptive_gaps(
            len(resources), len(edges)
        )

    # --------------------------------------------------------------- helpers
    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq}"

    def _add(
        self,
        cid: str,
        label: str,
        style: str,
        parent: str,
        x: float,
        y: float,
        w: float,
        h: float,
    ) -> dict[str, Any]:
        rec = {
            "id": cid,
            "label": label,
            "style": style,
            "parent": parent,
            "x": round(x, 1),
            "y": round(y, 1),
            "w": round(w, 1),
            "h": round(h, 1),
        }
        self.cells[cid] = rec
        return rec

    def _safe_id(self, raw: str) -> str:
        cached = self._ids_by_raw.get(raw)
        if cached:
            return cached
        out = []
        for ch in raw.replace(" ", "_").replace(".", "_"):
            out.append(ch if ch.isalnum() or ch in "_-" else "_")
        base = "".join(out) or "n"
        sid = base
        suffix = 2
        while sid in self._used_ids:
            sid = f"{base}_{suffix}"
            suffix += 1
        self._used_ids.add(sid)
        self._ids_by_raw[raw] = sid
        return sid

    def _icon_png_path(
        self, rid: str, r_type: str, attrs: dict[str, Any]
    ) -> str | None:
        from generate_arch_diagram import (  # noqa: PLC0415
            _guess_provider,
            _icon_class_for,
            _resolve_iac_icon,
        )

        diagrams_pkg = __import__("diagrams")
        site_packages_root = Path(diagrams_pkg.__file__).resolve().parent.parent

        kind = str((attrs or {}).get("Kind", "terraform"))
        raw_type = (attrs or {}).get("Type")

        # 1) Custom icon sources: custom:// tags and icons/ directories.
        tags = (attrs or {}).get("tags")
        if isinstance(tags, dict):
            icon_tag = str(tags.get("Icon", "")).strip()
            if icon_tag.startswith("custom://"):
                name = icon_tag.replace("custom://", "").strip()
                if name:
                    p = _repo_icons_dir() / "custom" / f"{name}.png"
                    if p.exists():
                        return str(p)
        if kind == "terraform":
            t = r_type.lower()
            provider = None
            for pfx in ("aws", "azurerm", "google", "oci", "ibm"):
                if t.startswith(f"{pfx}_"):
                    provider, t = pfx, t[len(pfx) + 1 :]
                    break
            candidates = [_repo_icons_dir() / "custom" / f"{t}.png"]
            if provider:
                candidates.append(_repo_icons_dir() / provider / f"{t}.png")
            for cand in candidates:
                if cand.exists():
                    return str(cand)

        # 2) Shared resolution pipeline -> diagrams class icon path.
        if kind in {"bicep", "pulumi"} and raw_type:
            icon_cls, _ = _resolve_iac_icon(kind, raw_type)
        else:
            icon_cls = _icon_class_for(r_type, attrs or {})
        if icon_cls is not None:
            icon_file = getattr(icon_cls, "_icon", None)
            icon_dir = getattr(icon_cls, "_icon_dir", None)
            if icon_file and icon_dir:
                candidate = site_packages_root / icon_dir / icon_file
                if candidate.exists():
                    return str(candidate)
                alt = (
                    site_packages_root
                    / "resources"
                    / _guess_provider(r_type).lower()
                    / icon_file
                )
                if alt.exists():
                    return str(alt)
        return None

    @staticmethod
    def _png_data_uri(path: str | None) -> str:
        if not path:
            return ""
        try:
            data = Path(path).read_bytes()
        except Exception:
            return ""
        # draw.io/browsers require the explicit ;base64 marker.
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    # ------------------------------------------------------------- vertices
    def _open_frame(self, title: str, style: str, x: float, y: float) -> str:
        cid = self._next_id("grp")
        self._add(cid, title, style, "1", x, y, 10, 10)
        return cid

    @staticmethod
    def _close_frame(cid_rec: dict[str, Any], w: float, h: float) -> tuple[float, float]:
        cid_rec["w"] = round(w, 1)
        cid_rec["h"] = round(h, 1)
        return cid_rec["w"], cid_rec["h"]

    def _node_label(self, rid: str) -> str:
        from generate_arch_diagram import _tf_node_label  # noqa: PLC0415

        return _tf_node_label(rid)

    def _node_metrics(self, rid: str) -> tuple[str, float, float, float]:
        label = self._node_label(rid)
        lines = [ln for ln in label.split("\n") if ln] or [rid]
        widest = max(len(ln) for ln in lines)
        icon = float(native_icon_size(rid.split(".", 1)[0]))
        w = max(icon + 22, widest * _CHAR_PX + 14)
        h = icon + 8 + len(lines) * _LINE_PX
        return label, w, h, icon

    def _add_resource_node(
        self,
        rid: str,
        parent: str,
        x: float,
        y: float,
        label: str,
        icon_size: float | None = None,
    ) -> str:
        from generate_arch_diagram import _guess_provider, _tf_category  # noqa: PLC0415

        r_type = rid.split(".", 1)[0]
        r_name = rid.split(".", 1)[1] if "." in rid else rid
        attrs = self.resources.get(rid, {}) or {}
        cid = self._safe_id(rid)
        size = float(icon_size) if icon_size else float(native_icon_size(r_type))
        native = native_style_for(r_type)
        if native:
            style = f"{native}fontSize={_LABEL_FONT};labelBackgroundColor=#FFFFFF;"
        else:
            uri = self._png_data_uri(self._icon_png_path(rid, r_type, attrs))
            if uri:
                style = (
                    "shape=image;html=1;verticalLabelPosition=bottom;"
                    "verticalAlign=top;"
                    f"imageAspect=0;aspect=fixed;image={uri};"
                    f"fontSize={_LABEL_FONT};fontColor={_AWS_SQUID_INK};"
                    "labelBackgroundColor=#FFFFFF;"
                )
            else:
                style = (
                    "rounded=1;whiteSpace=wrap;html=1;arcSize=18;fillColor=#EEF2F7;"
                    "strokeColor=#94A3B8;verticalLabelPosition=bottom;"
                    "verticalAlign=top;"
                    f"fontSize={_LABEL_FONT};fontColor=#334155;"
                )
        rec = self._add(cid, label, style, parent, x, y, size, size)
        rec["metadata"] = {
            "terraform_type": r_type,
            "terraform_name": r_name,
            "provider": _guess_provider(r_type),
            "category": _tf_category(r_type),
            "tooltip": f"{rid} ({r_type})",
        }
        return cid

    # ------------------------------------------------------------- grid pack
    def place_nodes_grid(
        self, rids: list[str], parent: str, ox: float, oy: float
    ) -> tuple[float, float]:
        """Pack nodes left-to-right/top-to-bottom in label-sized slots."""
        rids = sorted(rids)
        count = len(rids)
        if not count:
            return 0.0, 0.0
        cols = min(max(1, int(math.ceil(math.sqrt(count)))), _MAX_COLS, count)
        rows = int(math.ceil(count / cols))
        metrics = [self._node_metrics(r) for r in rids]
        col_w = [0.0] * cols
        row_h = [0.0] * rows
        for i, (_, w, h, _icon) in enumerate(metrics):
            r, c = divmod(i, cols)
            col_w[c] = max(col_w[c], w)
            row_h[r] = max(row_h[r], h)
        col_x = [sum(col_w[:c]) + c * self._col_gap for c in range(cols)]
        row_y = [sum(row_h[:r]) + r * self._row_gap for r in range(rows)]
        total_w = sum(col_w) + (cols - 1) * self._col_gap
        total_h = sum(row_h) + (rows - 1) * self._row_gap
        for i, rid in enumerate(rids):
            label, _, _, icon = metrics[i]
            r, c = divmod(i, cols)
            x = ox + col_x[c] + (col_w[c] - icon) / 2
            y = oy + row_y[r]
            self._add_resource_node(rid, parent, x, y, label, icon)
        return total_w, total_h

    # -------------------------------------------------------------- clusters
    def layout_subnet(
        self,
        subnet_name: str,
        subnet_rids: list[str],
        parent: str,
        ox: float,
        oy: float,
        provider_upper: str,
    ) -> tuple[float, float]:
        from generate_arch_diagram import (  # noqa: PLC0415
            _is_public_subnet,
            _tf_category,
            _tf_node_label,
        )

        attrs = self.resources.get(subnet_name, {}) or {}
        is_public = (
            _is_public_subnet(subnet_name.split(".", 1)[-1], attrs)
            if "." in subnet_name
            else "public" in subnet_name.lower()
        )
        if provider_upper == "AWS":
            style = _AWS_PUBLIC_SUBNET_STYLE if is_public else _AWS_PRIVATE_SUBNET_STYLE
        elif is_public:
            style = (
                f"{_GENERIC_FRAME_STYLE}fillColor={self.render.color_public_subnet};"
                "strokeColor=#28A745;fontColor=#248814;"
            )
        else:
            style = (
                f"{_GENERIC_FRAME_STYLE}fillColor={self.render.color_private_subnet};"
                "strokeColor=#FFC107;fontColor=#8D6E00;"
            )
        title = _tf_node_label(subnet_name) + (
            " (Public)" if is_public else " (Private)"
        )
        rec = self._add(
            self._next_id("subnet"), title, style, parent, ox, oy, 10, 10
        )
        # Register subnet id so edges pointing to/from subnet resolve to container
        self._ids_by_raw[subnet_name] = rec["id"]

        pad_x = _FRAME_PAD * 0.55
        y = _TITLE_H + 10.0
        by_cat: dict[str, list[str]] = {}
        for rid in subnet_rids:
            if rid != subnet_name:
                by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        w = 120.0
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + self._cluster_gap * 0.6
        return self._close_frame(rec, w + 2 * pad_x, y + _FRAME_PAD * 0.4)

    def layout_vpc(
        self,
        vpc_name: str,
        subnets: dict[str, list[str]],
        parent: str,
        ox: float,
        oy: float,
        provider_upper: str,
    ) -> tuple[float, float]:
        from generate_arch_diagram import _tf_node_label  # noqa: PLC0415

        if provider_upper == "AWS":
            style = _AWS_VPC_STYLE
        else:
            style = (
                f"{_GENERIC_FRAME_STYLE}fillColor={self.render.color_vpc};"
                "strokeColor=#5DADE2;fontColor=#1F618D;"
            )
        rec = self._add(
            self._next_id("vpc"),
            _tf_node_label(vpc_name),
            style,
            parent,
            ox,
            oy,
            10,
            10,
        )
        # Register VPC id so edges pointing to/from VPC resolve to container
        self._ids_by_raw[vpc_name] = rec["id"]

        pad_x = _FRAME_PAD * 0.55
        y = _TITLE_H + 12.0
        w = 140.0
        other_rids = [r for r in subnets.get("other", []) if r != vpc_name]
        if other_rids:
            gw, gh = self.place_nodes_grid(other_rids, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + self._cluster_gap * 0.6
        active_subnets = [
            (s_name, s_rids)
            for s_name, s_rids in sorted(subnets.items())
            if s_name != "other"
        ]
        if active_subnets:
            sub_cols = 2 if len(active_subnets) >= 2 else 1
            cur_x = pad_x
            row_y = y
            row_h = 0.0
            col_idx = 0
            for subnet_name, subnet_rids in active_subnets:
                if col_idx >= sub_cols:
                    col_idx = 0
                    cur_x = pad_x
                    row_y += row_h + self._cluster_gap * 0.6
                    row_h = 0.0
                sw, sh = self.layout_subnet(
                    subnet_name, subnet_rids, rec["id"], cur_x, row_y, provider_upper
                )
                cur_x += sw + self._cluster_gap * 0.6
                row_h = max(row_h, sh)
                col_idx += 1
                w = max(w, cur_x - pad_x - self._cluster_gap * 0.6)
            y = row_y + row_h
        return self._close_frame(rec, w + 2 * pad_x, y + _FRAME_PAD * 0.4)

    def layout_category(
        self,
        category: str,
        cat_rids: list[str],
        parent: str,
        ox: float,
        oy: float,
        accent: str | None = None,
        tint: str = "#F8F9FA",
    ) -> tuple[float, float]:
        from generate_arch_diagram import _tf_category  # noqa: PLC0415

        border = accent or "#CED4DA"
        font = accent or "#495057"
        style = (
            f"{_GENERIC_FRAME_STYLE}fillColor={tint};strokeColor={border};"
            f"fontColor={font};"
        )
        rec = self._add(
            self._next_id("cat"), category, style, parent, ox, oy, 10, 10
        )

        pad_x = _FRAME_PAD * 0.55
        y = _TITLE_H + 10.0
        by_cat: dict[str, list[str]] = {}
        for rid in cat_rids:
            by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        w = 100.0
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + self._cluster_gap * 0.6
        return self._close_frame(rec, max(w, 100) + 2 * pad_x, y + _FRAME_PAD * 0.4)

    # ---------------------------------------------------------------- export
    def export(self, out_path: Path, title: str) -> dict[str, Any]:
        from generate_arch_diagram import (  # noqa: PLC0415
            _build_subgraph_render_map,
            _detect_edge_type,
            _filter_architectural_edges,
            _guess_provider,
            _tf_category,
        )

        vpc_hierarchy, compute_subclusters, compute_children, resources_in_vpcs = (
            _build_subgraph_render_map(self.resources, self.edges)
        )

        known_providers: dict[str, list[str]] = {}
        unknown_rids: list[str] = []
        for rid in self.resources:
            provider = _guess_provider(rid.split(".", 1)[0])
            if provider.upper() in _PROVIDER_BORDER_COLORS:
                known_providers.setdefault(provider, []).append(rid)
            else:
                unknown_rids.append(rid)

        blocks: list[tuple[str, str | None, str, list[str], bool]] = []
        for provider in sorted(known_providers):
            provider_upper = provider.upper()
            blocks.append(
                (
                    f"{provider} Cloud",
                    _PROVIDER_BORDER_COLORS.get(provider_upper, "#6C757D"),
                    _PROVIDER_TINT_COLORS.get(provider_upper, "#FFFFFF"),
                    known_providers[provider],
                    True,
                )
            )
        if unknown_rids:
            blocks.append(("Other Resources", None, "#F8F9FA", unknown_rids, False))

        # 1. Title Banner
        title_text = f"<b style='font-size:15px;'>{title}</b><br/><span style='font-size:11px;color:#5A6C86;'>Generated by auto-arch-diagram &bull; {len(self.resources)} resources</span>"
        title_style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#F8FAFC;"
            "strokeColor=#CBD5E1;strokeWidth=1;align=left;spacingLeft=16;verticalAlign=middle;"
        )
        self._add(
            self._next_id("title_banner"),
            title_text,
            title_style,
            "1",
            _FRAME_PAD,
            _FRAME_PAD,
            460.0,
            54.0,
        )

        offset_x = _FRAME_PAD
        start_y = _FRAME_PAD + 75.0
        for heading, accent, tint, rids, is_cloud in blocks:
            pw_pad = _FRAME_PAD
            if heading == "AWS Cloud":
                frame_style = _AWS_CLOUD_STYLE
            elif accent:
                frame_style = (
                    f"{_GENERIC_FRAME_STYLE}fontSize=13;fillColor={tint};"
                    f"strokeColor={accent};fontColor={accent};"
                )
            else:
                frame_style = (
                    f"{_GENERIC_FRAME_STYLE}fillColor={tint};"
                    "strokeColor=#CED4DA;fontColor=#495057;"
                )
            prec = self._add(
                self._next_id("provider"),
                heading,
                frame_style,
                "1",
                offset_x,
                start_y,
                10,
                10,
            )
            provider_key = heading.split()[0]

            x, y = pw_pad, pw_pad + _TITLE_H * 0.8
            inner_w = 0.0
            handled: set[str] = set()

            provider_vpcs = {
                v: sub
                for v, sub in vpc_hierarchy.items()
                if _guess_provider(v.split(".", 1)[0]) == provider_key
            }
            # Multi-VPC: place side-by-side so inter-VPC edges are short
            # horizontal, not long vertical walls. Single VPC stays vertical.
            if len(provider_vpcs) >= 2:
                cur_x = x
                max_h = 0.0
                for vpc_name, subnets in sorted(provider_vpcs.items()):
                    vw, vh = self.layout_vpc(
                        vpc_name, subnets, prec["id"], cur_x, y, provider_key.upper()
                    )
                    handled.add(vpc_name)
                    for s in subnets:
                        handled.add(s)
                        handled.update(subnets[s])
                    cur_x += vw + self._cluster_gap
                    max_h = max(max_h, vh)
                inner_w = max(inner_w, cur_x - x - self._cluster_gap)
                y += max_h + self._cluster_gap
            else:
                for vpc_name, subnets in sorted(provider_vpcs.items()):
                    vw, vh = self.layout_vpc(
                        vpc_name, subnets, prec["id"], x, y, provider_key.upper()
                    )
                    handled.add(vpc_name)
                    for s in subnets:
                        handled.add(s)
                        handled.update(subnets[s])
                    inner_w = max(inner_w, vw)
                    y += vh + self._cluster_gap

            remaining = [
                rid
                for rid in rids
                if rid not in handled
                and rid not in resources_in_vpcs
                and rid not in compute_children
                and rid not in vpc_hierarchy
            ]

            for head, kids in sorted(compute_subclusters.items()):
                if head not in remaining:
                    continue
                cw, ch = self.layout_category(
                    _tf_category(head.split(".", 1)[0]),
                    [head],
                    prec["id"],
                    x,
                    y,
                    accent=accent,
                )
                kw, kh = self.place_nodes_grid(sorted(kids), prec["id"], x + cw + self._col_gap, y)
                inner_w = max(inner_w, cw + self._col_gap + kw)
                y += max(ch, kh) + self._cluster_gap

            lanes_left: dict[str, list[str]] = {}
            for rid in remaining:
                if rid in compute_subclusters:
                    continue
                lanes_left.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
            # Optimize lane order so heavily-connected lanes are adjacent — mirrors
            # the PNG lane logic and keeps any architecture's highways short.
            lane_edges: dict[tuple[str, str], int] = {}
            for s, d in self.edges:
                if s not in remaining or d not in remaining:
                    continue
                sc = _tf_category(s.split(".", 1)[0])
                dc = _tf_category(d.split(".", 1)[0])
                if sc in lanes_left and dc in lanes_left:
                    a, b = sorted([sc, dc])
                    lane_edges[(a, b)] = lane_edges.get((a, b), 0) + 1
            ordered = _optimized_lane_order(list(lanes_left.keys()), lane_edges)
            active_lanes = [(lane, lanes_left[lane]) for lane in ordered]
            if active_lanes:
                cat_cols = 3 if len(active_lanes) >= 5 else (2 if len(active_lanes) >= 2 else 1)
                cur_x = x
                row_y = y
                row_h = 0.0
                col_idx = 0
                for lane, group in active_lanes:
                    if col_idx >= cat_cols:
                        col_idx = 0
                        cur_x = x
                        row_y += row_h + self._cluster_gap
                        row_h = 0.0
                    lw, lh = self.layout_category(
                        lane, group, prec["id"], cur_x, row_y, accent=accent
                    )
                    cur_x += lw + self._cluster_gap
                    row_h = max(row_h, lh)
                    col_idx += 1
                    inner_w = max(inner_w, cur_x - x - self._cluster_gap)
                y = row_y + row_h

            fw, fh = self._close_frame(prec, inner_w + 2 * pw_pad, y + pw_pad * 0.4)
            self._max_h = max(self._max_h, start_y + fh)
            offset_x += fw + _FRAME_PAD * 1.6
        # 2. Legend Card (centered at the bottom below all provider frames)
        legend_w = 460.0
        legend_h = 54.0
        legend_x = max(_FRAME_PAD, (offset_x - _FRAME_PAD - legend_w) / 2)
        legend_y = self._max_h + 30.0
        legend_html = (
            "<b style='font-size:11px;'>Diagram Legend &amp; Connectors:</b><br/>"
            "<span style='color:#1565C0;'>&bull; Solid Blue: Data Flow</span> &nbsp;|&nbsp; "
            "<span style='color:#455A64;'>&bull; Gray: Dependency</span> &nbsp;|&nbsp; "
            "<span style='color:#C62828;'>&bull; Dashed Red: Security / Access</span>"
        )
        legend_style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#F8FAFC;"
            "strokeColor=#CBD5E1;strokeWidth=1;fontSize=10;fontColor=#475569;"
            "align=left;spacingLeft=12;spacingRight=12;verticalAlign=middle;"
        )
        self._add(
            self._next_id("legend_card"),
            legend_html,
            legend_style,
            "1",
            legend_x,
            legend_y,
            legend_w,
            legend_h,
        )

        edge_count = self._export_edges(_filter_architectural_edges, _detect_edge_type)

        _write_mxfile(out_path, title, self.cells)
        return {
            "nodes": len(self.resources),
            "edges": edge_count,
            "providers": len(blocks),
            "clusters": sum(
                1 for c in self.cells.values() if "container=1" in c["style"]
            ),
            "path": str(out_path),
        }

    # ------------------------------------------------------------------ edges
    def _abs_top_left(self, cid: str) -> tuple[float, float]:
        x = 0.0
        y = 0.0
        cur: str | None = cid
        while cur and cur not in {"0", "1"}:
            rec = self.cells.get(cur)
            if rec is None:
                break
            x += float(rec["x"])
            y += float(rec["y"])
            cur = rec["parent"]
        return x, y

    def _abs_center(self, cid: str) -> tuple[float, float]:
        x, y = self._abs_top_left(cid)
        rec = self.cells[cid]
        return x + rec["w"] / 2, y + rec["h"] / 2

    @staticmethod
    def _edge_style(
        edge_type: str,
        exit_pt: tuple[float, float],
        entry_pt: tuple[float, float],
        exit_dx: float = 0,
        exit_dy: float = 0,
        entry_dx: float = 0,
        entry_dy: float = 0,
    ) -> str:
        # Data flows get directional flow animation; other types stay static dashed.
        # draw.io honors `flowAnimation` / `dashed` with `fixDash` for animated dashes.
        if edge_type == "data":
            base = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;arcSize=10;html=1;jettySize=14;"
                "orthogonalLoop=1;curved=0;dashed=1;dashPattern=8 8;fixDash=1;flowAnimation=1;"
            )
            color, width, dashed = "#1565C0", 1.8, ""
        elif edge_type == "security":
            base = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;arcSize=10;html=1;jettySize=14;"
                "orthogonalLoop=1;curved=0;"
            )
            color, width, dashed = "#C62828", 1.4, "dashed=1;dashPattern=8 6;fixDash=1;"
        elif edge_type == "dependency":
            base = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;arcSize=10;html=1;jettySize=14;"
                "orthogonalLoop=1;curved=0;"
            )
            color, width, dashed = "#9E9E9E", 1.0, "dashed=1;dashPattern=4 6;fixDash=1;"
        else:
            base = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;arcSize=10;html=1;jettySize=14;"
                "orthogonalLoop=1;curved=0;"
            )
            color, width, dashed = _EDGE_COLORS.get(edge_type, "#455A64"), 1.2, ""
        ex, ey = exit_pt
        nx, ny = entry_pt
        return (
            f"{base}strokeColor={color};strokeWidth={width};{dashed}"
            "endArrow=block;endFill=1;endArrowSize=5;"
            f"exitX={ex:g};exitY={ey:g};exitDx={exit_dx:g};exitDy={exit_dy:g};"
            f"entryX={nx:g};entryY={ny:g};entryDx={entry_dx:g};entryDy={entry_dy:g};"
        )

    def _export_edges(self, filter_fn, detect_fn) -> int:
        from collections import defaultdict

        filtered = set(filter_fn(self.resources, set(self.edges)))
        # Collect unique directed edges with geometry for port-distribution
        seen: set[tuple[str, str]] = set()
        infos: list[tuple[str, str, str, str, tuple[float, float], tuple[float, float], str]] = []
        out_groups: dict[tuple[str, tuple[float, float]], list[int]] = defaultdict(list)
        in_groups: dict[tuple[str, tuple[float, float]], list[int]] = defaultdict(list)

        for src, dst in sorted(filtered):
            if src == dst or (dst, src) in seen:
                continue
            seen.add((src, dst))
            src_id = self._ids_by_raw.get(src)
            dst_id = self._ids_by_raw.get(dst)
            if not src_id or not dst_id or src_id not in self.cells or dst_id not in self.cells:
                continue
            sx, sy = self._abs_center(src_id)
            tx, ty = self._abs_center(dst_id)
            dx = tx - sx
            dy = ty - sy
            if abs(dx) >= abs(dy):
                if dx >= 0:
                    exit_pt, entry_pt = (1.0, 0.5), (0.0, 0.5)
                else:
                    exit_pt, entry_pt = (0.0, 0.5), (1.0, 0.5)
            else:
                if dy >= 0:
                    exit_pt, entry_pt = (0.5, 1.0), (0.5, 0.0)
                else:
                    exit_pt, entry_pt = (0.5, 0.0), (0.5, 1.0)
            edge_type = detect_fn(src, dst, self.resources)
            idx = len(infos)
            infos.append((src, dst, src_id, dst_id, exit_pt, entry_pt, edge_type))
            out_groups[(src_id, exit_pt)].append(idx)
            in_groups[(dst_id, entry_pt)].append(idx)

        # Geometric bundling: universal — for any diagram where spatially
        # overlapping highways converge in the same grid cell, keep a single
        # representative per cell so the diagram stays readable at any scale.
        if len(infos) > 22:
            grid: dict[tuple[int, int], list[int]] = defaultdict(list)
            for i, (_, _, s_id, d_id, _, _, _) in enumerate(infos):
                sx, sy = self._abs_center(s_id)
                tx, ty = self._abs_center(d_id)
                mx, my = (sx + tx) / 2, (sy + ty) / 2
                cell = (int(mx // 120), int(my // 120))
                grid[cell].append(i)
            drop_geo: set[int] = set()
            for cell, lst in grid.items():
                if len(lst) <= 1:
                    continue
                prio = {"security": 0, "data": 1, "dependency": 2, "network": 3}
                lst_sorted = sorted(lst, key=lambda ii: (prio.get(infos[ii][6], 99), infos[ii][0], infos[ii][1]))
                # Keep one per spatial cell — the most significant highway
                drop_geo.update(lst_sorted[1:])
            if drop_geo:
                infos = [info for i, info in enumerate(infos) if i not in drop_geo]
                out_groups.clear()
                in_groups.clear()
                for new_idx, (_, _, s_id, d_id, ex_pt, en_pt, _) in enumerate(infos):
                    out_groups[(s_id, ex_pt)].append(new_idx)
                    in_groups[(d_id, en_pt)].append(new_idx)

        count = 0
        for idx, (src, dst, src_id, dst_id, exit_pt, entry_pt, edge_type) in enumerate(infos):
            # Distribute parallel edges sharing the same port (10 px stagger)
            out_list = out_groups[(src_id, exit_pt)]
            pos_out = out_list.index(idx)
            offset_out = (pos_out - (len(out_list) - 1) / 2) * 10.0
            in_list = in_groups[(dst_id, entry_pt)]
            pos_in = in_list.index(idx)
            offset_in = (pos_in - (len(in_list) - 1) / 2) * 10.0

            if exit_pt[0] == 0.5:  # vertical side (top/bottom) → stagger in X
                exit_dx, exit_dy = offset_out, 0
            else:  # horizontal side → stagger in Y
                exit_dx, exit_dy = 0, offset_out
            if entry_pt[0] == 0.5:
                entry_dx, entry_dy = offset_in, 0
            else:
                entry_dx, entry_dy = 0, offset_in

            # Smart waypoints: for long edges, add a midpoint detour that
            # routes around the dense centre, staggering waypoints so parallel
            # highways don't collapse onto the same orthogonal segment.
            waypoints: list[tuple[float, float]] | None = None
            sx, sy = self._abs_center(src_id)
            tx, ty = self._abs_center(dst_id)
            length = ((tx - sx) ** 2 + (ty - sy) ** 2) ** 0.5
            if length > 220:
                mx, my = (sx + tx) / 2, (sy + ty) / 2
                # Perpendicular offset spreads parallel highways
                # Horizontal-dominant edges offset vertically, vertical-dominant horizontally
                is_horiz = abs(tx - sx) >= abs(ty - sy)
                spread = (idx % 5 - 2) * 18  # -36, -18, 0, 18, 36
                if is_horiz:
                    my += spread
                else:
                    mx += spread
                # Nudge away from any node that the straight segment would cut through
                # (simple AABB check against all other nodes)
                for oid, rec2 in self.cells.items():
                    if oid in (src_id, dst_id) or rec2.get("edge"):
                        continue
                    ox, oy = self._abs_top_left(oid)
                    ow, oh = rec2["w"], rec2["h"]
                    # Expand hitbox slightly
                    pad = 14
                    if (min(sx, tx) - pad < ox + ow and max(sx, tx) + pad > ox and
                        min(sy, ty) - pad < oy + oh and max(sy, ty) + pad > oy):
                        # If midpoint inside this node's box, push waypoint outside
                        if ox < mx < ox + ow and oy < my < oy + oh:
                            my = oy + oh + 28 if is_horiz else oy - 28
                            break
                waypoints = [(round(mx, 1), round(my, 1))]

            ecid = self._next_id("edge")
            rec = self._add(
                ecid,
                "",
                self._edge_style(edge_type, exit_pt, entry_pt, exit_dx, exit_dy, entry_dx, entry_dy),
                "1",
                0,
                0,
                0,
                0,
            )
            rec["edge"] = True
            rec["source"] = src_id
            rec["target"] = dst_id
            if waypoints:
                rec["waypoints"] = waypoints
            count += 1
        return count


def export_drawio(
    resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    out_path: Path,
    *,
    title: str = "Architecture",
    render: Any = None,
) -> dict[str, Any]:
    """Export a parsed IaC graph to an editable draw.io (.drawio) file."""
    exporter = _DrawioExporter(resources, edges, render)
    return exporter.export(Path(out_path), title)


def _write_mxfile(out_path: Path, title: str, cells: dict[str, dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    mxfile = ET.Element("mxfile", {"host": "auto-arch-diagram"})
    diagram_el = ET.SubElement(
        mxfile,
        "diagram",
        {"id": uuid.uuid4().hex[:12], "name": (title or "Architecture")[:60]},
    )
    model = ET.SubElement(
        diagram_el,
        "mxGraphModel",
        {
            "dx": "1400",
            "dy": "900",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1654",
            "pageHeight": "1169",
            "math": "0",
            "shadow": "0",
            "background": "#FFFFFF",
        },
    )
    root_el = ET.SubElement(model, "root")
    ET.SubElement(root_el, "mxCell", {"id": "0"})
    ET.SubElement(root_el, "mxCell", {"id": "1", "parent": "0"})

    for rec in cells.values():
        if rec.get("edge"):
            cell = ET.SubElement(
                root_el,
                "mxCell",
                {
                    "id": rec["id"],
                    "value": rec.get("label", ""),
                    "style": rec["style"],
                    "edge": "1",
                    "parent": "1",
                    "source": rec["source"],
                    "target": rec["target"],
                },
            )
            geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            wps = rec.get("waypoints")
            if wps:
                arr = ET.SubElement(geom, "Array", {"as": "points"})
                for wx, wy in wps:
                    ET.SubElement(arr, "mxPoint", {"x": str(wx), "y": str(wy)})
        else:
            metadata = rec.get("metadata")
            if metadata:
                obj_attribs = {
                    "id": rec["id"],
                    "label": rec["label"],
                    "tooltip": metadata.get("tooltip", rec["label"]),
                    "terraform_type": metadata.get("terraform_type", ""),
                    "terraform_name": metadata.get("terraform_name", ""),
                    "provider": metadata.get("provider", ""),
                    "category": metadata.get("category", ""),
                }
                obj_el = ET.SubElement(root_el, "object", obj_attribs)
                cell = ET.SubElement(
                    obj_el,
                    "mxCell",
                    {
                        "value": rec["label"],
                        "style": rec["style"],
                        "vertex": "1",
                        "parent": rec["parent"],
                    },
                )
                ET.SubElement(
                    cell,
                    "mxGeometry",
                    {
                        "x": str(rec["x"]),
                        "y": str(rec["y"]),
                        "width": str(rec["w"]),
                        "height": str(rec["h"]),
                        "as": "geometry",
                    },
                )
            else:
                cell = ET.SubElement(
                    root_el,
                    "mxCell",
                    {
                        "id": rec["id"],
                        "value": rec["label"],
                        "style": rec["style"],
                        "vertex": "1",
                        "parent": rec["parent"],
                    },
                )
                ET.SubElement(
                    cell,
                    "mxGeometry",
                    {
                        "x": str(rec["x"]),
                        "y": str(rec["y"]),
                        "width": str(rec["w"]),
                        "height": str(rec["h"]),
                        "as": "geometry",
                    },
                )

    xml_bytes = ET.tostring(mxfile, encoding="unicode").encode("utf-8")
    out_path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes + b"\n"
    )
