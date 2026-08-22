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

# Geometry constants tuned to match official draw.io AWS samples.
_ICON_SIZE = 48.0  # resource icon square (px)
_LABEL_FONT = 11  # node label font size (pt)
_CHAR_PX = 6.2  # approx rendered px per character at _LABEL_FONT
_LINE_PX = 13.0  # label line height (px)
_COL_GAP = 36.0  # horizontal gap between node slots
_ROW_GAP = 24.0  # vertical gap between node rows
_FRAME_PAD = 32.0  # padding inside group frames
_TITLE_H = 44.0  # strip reserved for the group title glyph + text
_CLUSTER_GAP = 24.0  # vertical gap between sibling clusters
_MAX_COLS = 6  # cap grid columns to keep diagrams readable

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
        r_type = rid.split(".", 1)[0]
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
        self._add(cid, label, style, parent, x, y, size, size)
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
        col_x = [sum(col_w[:c]) + c * _COL_GAP for c in range(cols)]
        row_y = [sum(row_h[:r]) + r * _ROW_GAP for r in range(rows)]
        total_w = sum(col_w) + (cols - 1) * _COL_GAP
        total_h = sum(row_h) + (rows - 1) * _ROW_GAP
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

        pad_x = _FRAME_PAD * 0.55
        top = _TITLE_H * 0.7
        label, slot_w, slot_h, slot_icon = self._node_metrics(subnet_name)
        self._add_resource_node(
            subnet_name, rec["id"], pad_x, top, label, slot_icon
        )
        y = top + slot_h + _CLUSTER_GAP * 0.6
        by_cat: dict[str, list[str]] = {}
        for rid in subnet_rids:
            by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        w = max(slot_w, _ICON_SIZE + 22)
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + _CLUSTER_GAP * 0.5
        return self._close_frame(rec, w + 2 * pad_x, y + _FRAME_PAD * 0.35)

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

        pad_x = _FRAME_PAD * 0.55
        top = _TITLE_H * 0.7
        label, slot_w, slot_h, slot_icon = self._node_metrics(vpc_name)
        self._add_resource_node(
            vpc_name, rec["id"], pad_x, top, label, slot_icon
        )
        y = top + slot_h + _CLUSTER_GAP * 0.6
        w = max(slot_w, _ICON_SIZE + 22)
        other_rids = list(subnets.get("other", []))
        if other_rids:
            gw, gh = self.place_nodes_grid(other_rids, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + _CLUSTER_GAP * 0.5
        for subnet_name, subnet_rids in sorted(subnets.items()):
            if subnet_name == "other":
                continue
            sw, sh = self.layout_subnet(
                subnet_name, subnet_rids, rec["id"], pad_x, y, provider_upper
            )
            w = max(w, sw)
            y += sh + _CLUSTER_GAP * 0.5
        return self._close_frame(rec, w + 2 * pad_x, y - oy + _FRAME_PAD * 0.3)

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
        top = _TITLE_H * 0.65
        by_cat: dict[str, list[str]] = {}
        for rid in cat_rids:
            by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        y = top
        w = 0.0
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, rec["id"], pad_x, y)
            w = max(w, gw)
            y += gh + _CLUSTER_GAP * 0.5
        return self._close_frame(rec, max(w, 60) + 2 * pad_x, y - oy + _FRAME_PAD * 0.3)

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

        offset_x = _FRAME_PAD
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
                _FRAME_PAD,
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
            for vpc_name, subnets in sorted(provider_vpcs.items()):
                vw, vh = self.layout_vpc(
                    vpc_name, subnets, prec["id"], x, y, provider_key.upper()
                )
                handled.add(vpc_name)
                for s in subnets:
                    handled.add(s)
                    handled.update(subnets[s])
                inner_w = max(inner_w, vw)
                y += vh + _CLUSTER_GAP

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
                kw, kh = self.place_nodes_grid(sorted(kids), prec["id"], x + cw + _COL_GAP, y)
                inner_w = max(inner_w, cw + _COL_GAP + kw)
                y += max(ch, kh) + _CLUSTER_GAP

            lanes_left: dict[str, list[str]] = {}
            for rid in remaining:
                if rid in compute_subclusters:
                    continue
                lanes_left.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
            for lane in _LANE_ORDER:
                group = lanes_left.get(lane) or []
                if not group:
                    continue
                lw, lh = self.layout_category(
                    lane, group, prec["id"], x, y, accent=accent
                )
                inner_w = max(inner_w, lw)
                y += lh + _CLUSTER_GAP

            fw, fh = self._close_frame(prec, inner_w + 2 * pw_pad, y - pw_pad)
            offset_x += fw + _FRAME_PAD * 1.6
            self._max_h = max(self._max_h, fh)

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
    def _edge_style(edge_type: str, exit_pt: tuple[float, float], entry_pt: tuple[float, float]) -> str:
        base = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;arcSize=8;html=1;jettySize=auto;"
            "orthogonalLoop=1;"
        )
        color = _EDGE_COLORS.get(edge_type, "#455A64")
        width = {"security": 1.5, "data": 2.0, "dependency": 1.0}.get(edge_type, 1.2)
        dashed = "dashed=1;" if edge_type in {"security", "dependency"} else ""
        ex, ey = exit_pt
        nx, ny = entry_pt
        return (
            f"{base}strokeColor={color};strokeWidth={width};{dashed}"
            "endArrow=block;endFill=1;"
            f"exitX={ex:g};exitY={ey:g};exitDx=0;exitDy=0;"
            f"entryX={nx:g};entryY={ny:g};entryDx=0;entryDy=0;"
        )

    def _export_edges(self, filter_fn, detect_fn) -> int:
        filtered = set(filter_fn(self.resources, set(self.edges)))
        seen: set[tuple[str, str]] = set()
        count = 0
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
            ecid = self._next_id("edge")
            rec = self._add(
                ecid,
                "",
                self._edge_style(edge_type, exit_pt, entry_pt),
                "1",
                0,
                0,
                0,
                0,
            )
            rec["edge"] = True
            rec["source"] = src_id
            rec["target"] = dst_id
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
                    "value": "",
                    "style": rec["style"],
                    "edge": "1",
                    "parent": "1",
                    "source": rec["source"],
                    "target": rec["target"],
                },
            )
            ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
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
