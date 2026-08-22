"""Logic-driven draw.io (diagrams.net) exporter.

Converts the same parsed IaC graph (resources + edges) used by the PNG/SVG
renderers into a fully editable .drawio file. Everything is derived from the
input architecture - no architecture-specific hardcoding:

- Grouping reuses the existing VPC/subnet hierarchy, compute subclusters,
  provider and category detection from generate_arch_diagram.
- Icons reuse the exact same resolution pipeline; PNG bytes are located via
  the resolved `diagrams` classes (`_icon_dir`/`_icon`) or the custom icon
  directories, then embedded as base64 data URIs.
- Sizes and spacing derive from RenderConfig.
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

_PROVIDER_BORDER_COLORS = {
    "AWS": "#FFE7C4",
    "AZURERM": "#9BD0F9",
    "AZURE": "#A7D6FB",
    "GOOGLE": "#C0D3F3",
    "GCP": "#AAC7F5",
    "OCI": "#FFCCCC",
    "IBM": "#BBCEF2",
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
    "security": "#F44336",
    "data": "#2196F3",
    "dependency": "#9E9E9E",
    "network": "#4B5563",
}


def _repo_icons_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "icons"


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
        self.node_w = max(float(self.render.node_width) * 160, 150.0)
        self.node_h = max(float(self.render.node_height) * 130, 110.0)
        self.gap = self.node_w * 0.35
        self.provider_gap = self.node_w * 0.8
        # id -> record; coordinates are relative to the parent cell.
        self.cells: dict[str, dict[str, Any]] = {}
        self._seq = 0

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

    def _icon_png_path(
        self, rid: str, r_type: str, attrs: dict[str, Any]
    ) -> str | None:
        from generate_arch_diagram import (  # noqa: PLC0415
            _guess_provider,
            _icon_class_for,
            _resolve_iac_icon,
        )

        diagrams_pkg = __import__("diagrams")
        # diagrams classes store _icon_dir like "resources/aws/network"
        # (already includes the resources/ prefix), so the root is the
        # site-packages directory containing the `resources` tree.
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
        return "data:image/png," + base64.b64encode(data).decode("ascii")

    def _node_style(self, rid: str, r_type: str, attrs: dict[str, Any]) -> str:
        from generate_arch_diagram import _guess_provider  # noqa: PLC0415

        border = _PROVIDER_BORDER_COLORS.get(
            _guess_provider(r_type).upper(), "#6C757D"
        )
        style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor=#FFFFFF;"
            f"strokeColor={border};strokeWidth=1;fontSize=11;"
            "verticalLabelPosition=bottom;verticalAlign=top;"
        )
        uri = self._png_data_uri(self._icon_png_path(rid, r_type, attrs))
        if uri:
            style += f"imageAspect=0;aspect=fixed;image={uri};"
        return style

    @staticmethod
    def _cluster_style(border: str, fill: str) -> str:
        return (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=6;verticalAlign=top;"
            f"fontSize=13;fontStyle=1;fillColor={fill};strokeColor={border};"
            "strokeWidth=2;container=1;collapsible=0;"
        )

    @staticmethod
    def _edge_style(edge_type: str) -> str:
        base = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;"
            "orthogonalLoop=1;"
        )
        color = _EDGE_COLORS.get(edge_type, "#4B5563")
        width = {"security": 1.5, "data": 2.0, "dependency": 1.0}.get(edge_type, 1.2)
        dashed = "dashed=1;" if edge_type in {"security", "dependency"} else ""
        return f"{base}strokeColor={color};strokeWidth={width};{dashed}"

    # ------------------------------------------------------------ grid pack
    def _grid_dims(self, count: int) -> tuple[int, int]:
        if count <= 0:
            return 0, 0
        cols = int(math.ceil(math.sqrt(count)))
        return cols, int(math.ceil(count / cols))

    def place_nodes_grid(
        self, rids: list[str], parent: str, ox: float, oy: float
    ) -> tuple[float, float]:
        """Place nodes in a grid inside `parent`; returns (width, height)."""
        cols, rows = self._grid_dims(len(rids))
        for idx, rid in enumerate(sorted(rids)):
            r, c = divmod(idx, cols)
            r_type = rid.split(".", 1)[0]
            self._add(
                self._safe_id(rid),
                rid,
                self._node_style(rid, r_type, self.resources.get(rid, {}) or {}),
                parent,
                ox + c * (self.node_w + self.gap),
                oy + r * (self.node_h + self.gap),
                self.node_w,
                self.node_h,
            )
        if not rids:
            return 0.0, 0.0
        used_cols = min(cols, len(rids))
        last_rows = math.ceil(len(rids) / used_cols)
        w = used_cols * self.node_w + (used_cols - 1) * self.gap
        h = last_rows * self.node_h + (last_rows - 1) * self.gap
        return w, h

    # -------------------------------------------------------------- clusters
    def layout_subnet(
        self, subnet_name: str, subnet_rids: list[str], parent: str, ox: float, oy: float
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
        border = "#28A745" if is_public else "#FFC107"
        fill = "#F8FFF8" if is_public else "#FFFEF8"
        pad = self.gap * 0.6
        label_y = 26.0
        cid = self._next_id("subnet")
        self._add(
            cid,
            _tf_node_label(subnet_name) + (" (Public)" if is_public else " (Private)"),
            self._cluster_style(border, fill),
            parent,
            ox,
            oy,
            10,
            10,
        )
        # Subnet node itself first, then contained resources.
        nx, ny = pad, pad + label_y
        r_type = subnet_name.split(".", 1)[0]
        self._add(
            self._safe_id(subnet_name),
            subnet_name,
            self._node_style(subnet_name, r_type, attrs),
            cid,
            nx,
            ny,
            self.node_w,
            self.node_h,
        )
        inner_x = nx
        inner_y = ny + self.node_h + self.gap
        by_cat: dict[str, list[str]] = {}
        for rid in subnet_rids:
            by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        w, h = self.node_w, inner_y - ny
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, cid, inner_x, inner_y)
            w = max(w, gw)
            inner_y += gh + self.gap * 0.6
            h = inner_y - ny
        rec = self.cells[cid]
        rec["w"] = round(w + 2 * pad, 1)
        rec["h"] = round(h + pad, 1)
        return rec["w"], rec["h"]

    def layout_vpc(
        self, vpc_name: str, subnets: dict[str, list[str]], parent: str, ox: float, oy: float
    ) -> tuple[float, float]:
        from generate_arch_diagram import _tf_node_label  # noqa: PLC0415

        pad = self.gap * 0.6
        label_y = 26.0
        cid = self._next_id("vpc")
        self._add(
            cid,
            _tf_node_label(vpc_name),
            self._cluster_style("#5DADE2", "#F8FCFF"),
            parent,
            ox,
            oy,
            10,
            10,
        )
        # VPC node itself.
        nx, ny = pad, pad + label_y
        r_type = vpc_name.split(".", 1)[0]
        self._add(
            self._safe_id(vpc_name),
            vpc_name,
            self._node_style(vpc_name, r_type, self.resources.get(vpc_name, {}) or {}),
            cid,
            nx,
            ny,
            self.node_w,
            self.node_h,
        )
        y = ny + self.node_h + self.gap
        w = self.node_w
        other_rids = list(subnets.get("other", []))
        if other_rids:
            gw, gh = self.place_nodes_grid(other_rids, cid, nx, y)
            w = max(w, gw)
            y += gh + self.gap * 0.6
        for subnet_name, subnet_rids in sorted(subnets.items()):
            if subnet_name == "other":
                continue
            sw, sh = self.layout_subnet(subnet_name, subnet_rids, cid, pad, y)
            w = max(w, sw)
            y += sh + self.gap * 0.6
        rec = self.cells[cid]
        rec["w"] = round(w + 2 * pad, 1)
        rec["h"] = round(y - oy + pad * 0.2, 1)
        return rec["w"], rec["h"]

    def layout_category(
        self, category: str, cat_rids: list[str], parent: str, ox: float, oy: float
    ) -> tuple[float, float]:
        from generate_arch_diagram import (  # noqa: PLC0415
            _get_cluster_color,
            _tf_category,
        )

        pad = self.gap * 0.6
        label_y = 26.0
        cid = self._next_id("cat")
        self._add(
            cid,
            category,
            self._cluster_style("#CCCCCC", _get_cluster_color(category, self.render)),
            parent,
            ox,
            oy,
            10,
            10,
        )
        by_cat: dict[str, list[str]] = {}
        for rid in cat_rids:
            by_cat.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
        x = pad
        y = pad + label_y
        w = 0.0
        for lane in _LANE_ORDER:
            group = sorted(by_cat.get(lane, []))
            if not group:
                continue
            gw, gh = self.place_nodes_grid(group, cid, x, y)
            w = max(w, gw)
            y += gh + self.gap * 0.6
        rec = self.cells[cid]
        rec["w"] = round(max(w, 10) + 2 * pad, 1)
        rec["h"] = round(y - oy - self.gap * 0.6 + pad, 1)
        return rec["w"], rec["h"]

    # ---------------------------------------------------------------- export
    def export(self, out_path: Path, title: str) -> dict[str, Any]:
        from generate_arch_diagram import (  # noqa: PLC0415
            _build_subgraph_render_map,
            _detect_edge_type,
            _guess_provider,
            _tf_category,
        )

        vpc_hierarchy, compute_subclusters, compute_children, resources_in_vpcs = (
            _build_subgraph_render_map(self.resources, self.edges)
        )

        providers: dict[str, list[str]] = {}
        for rid in self.resources:
            providers.setdefault(_guess_provider(rid.split(".", 1)[0]), []).append(rid)

        offset_x = 0.0
        max_h = 0.0
        for provider in sorted(providers):
            pw_pad = self.gap * 0.8
            pcid = self._next_id("provider")
            self._add(
                pcid,
                f"{provider} Cloud",
                self._cluster_style(
                    _PROVIDER_BORDER_COLORS.get(provider.upper(), "#6C757D"),
                    "#FFFFFF",
                ),
                "1",
                offset_x + pw_pad,
                pw_pad + 26,
                10,
                10,
            )
            x = pw_pad
            y = pw_pad + 26
            inner_w = 0.0

            handled: set[str] = set()

            provider_vpcs = {
                v: sub
                for v, sub in vpc_hierarchy.items()
                if _guess_provider(v.split(".", 1)[0]) == provider
            }
            for vpc_name, subnets in sorted(provider_vpcs.items()):
                vw, vh = self.layout_vpc(vpc_name, subnets, pcid, x, y)
                handled.add(vpc_name)
                for s in subnets:
                    handled.add(s)
                    handled.update(subnets[s])
                inner_w = max(inner_w, vw)
                y += vh + self.gap * 0.6

            remaining = [
                rid
                for rid in providers[provider]
                if rid not in handled
                and rid not in resources_in_vpcs
                and rid not in compute_children
                and rid not in vpc_hierarchy
            ]

            # Compute cluster heads nest their children in a dedicated cluster.
            for head, kids in sorted(compute_subclusters.items()):
                if head not in remaining:
                    continue
                cw, ch = self.layout_category(
                    _tf_category(head.split(".", 1)[0]), [head], pcid, x, y
                )
                # Place children next to the head inside same provider area.
                kw, kh = self.place_nodes_grid(sorted(kids), pcid, x + cw + self.gap, y)
                inner_w = max(inner_w, cw + self.gap + kw)
                y += max(ch, kh) + self.gap * 0.6

            lanes_left: dict[str, list[str]] = {}
            for rid in remaining:
                if rid in compute_subclusters:
                    continue
                lanes_left.setdefault(_tf_category(rid.split(".", 1)[0]), []).append(rid)
            for lane in _LANE_ORDER:
                group = lanes_left.get(lane) or []
                if not group:
                    continue
                lw, lh = self.layout_category(lane, group, pcid, x, y)
                inner_w = max(inner_w, lw)
                y += lh + self.gap * 0.6

            prec = self.cells[pcid]
            prec["w"] = round(inner_w + 2 * pw_pad, 1)
            prec["h"] = round(y - pw_pad - 26 + pw_pad, 1)
            offset_x += prec["w"] + self.provider_gap
            max_h = max(max_h, prec["h"])

        edge_count = 0
        for src, dst in sorted(self.edges):
            src_id, dst_id = self._safe_id(src), self._safe_id(dst)
            if src_id not in self.cells or dst_id not in self.cells:
                continue
            edge_type = _detect_edge_type(src, dst, self.resources)
            ecid = self._next_id("edge")
            self._add(ecid, "", self._edge_style(edge_type), "1", 0, 0, 0, 0)
            rec = self.cells[ecid]
            rec["edge"] = True
            rec["source"] = src_id
            rec["target"] = dst_id
            edge_count += 1

        _write_mxfile(out_path, title, self.cells)
        return {
            "nodes": len(self.resources),
            "edges": edge_count,
            "providers": len(providers),
            "clusters": sum(
                1 for c in self.cells.values() if "container=1" in c["style"]
            ),
            "path": str(out_path),
        }

    @staticmethod
    def _safe_id(raw: str) -> str:
        out = []
        for ch in raw.replace(" ", "_").replace(".", "_"):
            out.append(ch if ch.isalnum() or ch in "_-" else "_")
        s = "".join(out)
        return s or "n"


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
            "grid": "0",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1169",
            "pageHeight": "826",
            "math": "0",
            "shadow": "0",
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
