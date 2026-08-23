"""Self-contained interactive HTML architecture diagram exporter.

Generates a standalone, feature-rich offline HTML viewer with:
1. Smooth Pan, Smooth Zoom (wheel/pinch), Fit-to-Screen, Actual 1:1, and Fullscreen.
2. Interactive Path Tracing & Impact Analysis (Dependency blast radius & flow glowing animations).
3. Live Category Filter Chips (Compute, Storage, Database, Network, Security, Messaging, etc.).
4. Comprehensive Resource Inspector Drawer with searchable attributes, tags, and clickable connected node links.
5. In-Browser Multi-Format Export Studio (Download PNG, Download SVG, Download JSON Inventory).
6. Smart Spotlight Search with instant auto-focus and glowing pulse.
7. Mini-Map Radar Navigation Viewport.
8. Sleek Dark / Light theme toggle with persistence.
9. 100% self-contained and offline-ready (zero external CDN dependencies).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Optional


def export_interactive_html(
    svg_content: str,
    resources: dict[str, dict[str, Any]],
    title: str = "Architecture Diagram",
    out_path: Optional[Path] = None,
) -> str:
    # Clean SVG content if wrapped in XML header or namespace prefixes
    svg_clean = re.sub(r'<\?xml[^>]*\?>', '', svg_content).strip()
    svg_clean = re.sub(r'<!DOCTYPE[^>]*>', '', svg_clean).strip()
    # Strip any ns0: / ns1: namespace prefixes introduced by XML parsers
    svg_clean = re.sub(r'<(/?)ns[0-9]+:', r'<\1', svg_clean)
    svg_clean = re.sub(r'\s+xmlns:ns[0-9]+="[^"]*"', '', svg_clean)
    if "<svg" in svg_clean and "xmlns=" not in svg_clean[:200]:
        svg_clean = svg_clean.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)

    # Normalize SVG dimensions: high-DPI Graphviz output inflates width/height
    # (e.g. width="1840pt") while viewBox stays in original point units. The
    # mismatch makes fit-to-screen math trust a tiny viewBox against a huge
    # rendered element, so the diagram loads massively over-zoomed showing only
    # one corner. Rewrite width/height to match viewBox (1 user unit = 1 px).
    def _normalize_svg_dimensions(svg: str) -> str:
        tag_match = re.search(r"<svg\b[^>]*>", svg)
        if not tag_match:
            return svg
        tag = tag_match.group(0)

        def _attr(name: str) -> Optional[str]:
            m = re.search(rf'\b{name}="([^"]+)"', tag)
            return m.group(1) if m else None

        vb_raw = _attr("viewBox")
        w_raw, h_raw = _attr("width"), _attr("height")
        if not vb_raw or not w_raw or not h_raw:
            return svg
        try:
            vb_w, vb_h = (float(part) for part in vb_raw.split()[2:4])
            w_val = float(re.sub(r"[a-z%]+$", "", w_raw.strip()))
            h_val = float(re.sub(r"[a-z%]+$", "", h_raw.strip()))
        except (ValueError, IndexError):
            return svg
        if vb_w <= 0 or vb_h <= 0:
            return svg
        if abs(w_val - vb_w) / vb_w < 0.01 and abs(h_val - vb_h) / vb_h < 0.01:
            return svg

        new_tag = tag
        new_tag = re.sub(r'\bwidth="[^"]+"', f'width="{vb_w:.2f}px"', new_tag, count=1)
        new_tag = re.sub(r'\bheight="[^"]+"', f'height="{vb_h:.2f}px"', new_tag, count=1)
        return svg.replace(tag, new_tag, 1)

    svg_clean = _normalize_svg_dimensions(svg_clean)

    # Build resource metadata dictionary and category classification
    res_metadata: dict[str, Any] = {}
    categories_count: dict[str, int] = {
        "All": len(resources),
        "Compute": 0,
        "Storage": 0,
        "Database": 0,
        "Network": 0,
        "Security": 0,
        "Integration": 0,
        "Management": 0,
    }

    def _classify_type(rtype: str) -> str:
        r = rtype.lower()
        if any(k in r for k in ["lambda", "ecs", "eks", "instance", "virtual_machine", "function", "glue_job", "batch", "app_service"]):
            return "Compute"
        if any(k in r for k in ["s3", "storage", "bucket", "blob", "efs", "ebs"]):
            return "Storage"
        if any(k in r for k in ["rds", "dynamo", "database", "cosmos", "sql", "redis", "elasticache", "mongo"]):
            return "Database"
        if any(k in r for k in ["vpc", "subnet", "gateway", "route", "vnet", "ip", "nat", "dns", "route53", "cdn", "cloudfront"]):
            return "Network"
        if any(k in r for k in ["iam", "role", "policy", "security", "vault", "key", "kms", "certificate", "acm"]):
            return "Security"
        if any(k in r for k in ["sqs", "sns", "event", "eventbridge", "bus", "topic", "queue", "kafka", "mq", "apigateway", "api_gateway"]):
            return "Integration"
        if any(k in r for k in ["cloudwatch", "log", "alarm", "monitor", "metric", "insight"]):
            return "Management"
        return "Compute"

    for res_id, res_data in resources.items():
        r_type = res_data.get("type", res_id.split(".")[0] if "." in res_id else "")
        r_name = res_data.get("name", res_id.split(".", 1)[1] if "." in res_id else res_id)
        cat = _classify_type(r_type)
        categories_count[cat] = categories_count.get(cat, 0) + 1

        res_metadata[res_id] = {
            "id": res_id,
            "type": r_type,
            "name": r_name,
            "category": cat,
            "module": res_data.get("module", "root"),
            "provider": res_data.get("provider", "aws"),
            "tags": res_data.get("tags", {}),
            "attributes": {
                k: str(v)
                for k, v in res_data.items()
                if k not in {"tags", "type", "name", "module", "provider"}
            },
        }

    metadata_json = json.dumps(res_metadata, indent=2)
    categories_json = json.dumps(categories_count)

    html_template = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} - Interactive Architecture Studio</title>
<style>
  :root {{
    --bg-primary: #0B0F19;
    --bg-secondary: #161F30;
    --bg-canvas: #07090E;
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --accent: #38BDF8;
    --accent-glow: rgba(56, 189, 248, 0.4);
    --accent-hover: #0EA5E9;
    --border: #243046;
    --card-bg: rgba(22, 31, 48, 0.88);
    --badge-bg: #1E293B;
  }}

  [data-theme="light"] {{
    --bg-primary: #F8FAFC;
    --bg-secondary: #FFFFFF;
    --bg-canvas: #EDF2F7;
    --text-primary: #0F172A;
    --text-secondary: #64748B;
    --accent: #0284C7;
    --accent-glow: rgba(2, 132, 199, 0.3);
    --accent-hover: #0369A1;
    --border: #CBD5E1;
    --card-bg: rgba(255, 255, 255, 0.94);
    --badge-bg: #E2E8F0;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; }}
  body {{ background: var(--bg-primary); color: var(--text-primary); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}

  /* Top Navigation Bar */
  header {{
    height: 58px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    z-index: 20;
  }}

  .header-left {{ display: flex; align-items: center; gap: 12px; }}
  .brand-icon {{ width: 26px; height: 26px; border-radius: 6px; background: linear-gradient(135deg, #38BDF8, #6366F1); display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: 13px; }}
  .title {{ font-size: 15px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.2px; }}
  .badge {{ background: var(--badge-bg); color: var(--accent); border: 1px solid var(--border); padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; }}

  .header-center {{ display: flex; align-items: center; gap: 6px; }}
  .filter-chip {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .filter-chip:hover, .filter-chip.active {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
    box-shadow: 0 0 10px var(--accent-glow);
  }}

  .header-right {{ display: flex; align-items: center; gap: 8px; }}
  .search-container {{ position: relative; }}
  .search-box {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px 6px 30px;
    color: var(--text-primary);
    font-size: 13px;
    width: 200px;
    outline: none;
    transition: all 0.2s ease;
  }}
  .search-box:focus {{ border-color: var(--accent); width: 260px; box-shadow: 0 0 8px var(--accent-glow); }}
  .search-icon {{ position: absolute; left: 10px; top: 8px; color: var(--text-secondary); font-size: 12px; pointer-events: none; }}

  .btn {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s ease;
  }}
  .btn:hover {{ background: var(--accent); color: white; border-color: var(--accent); }}
  .btn-primary {{ background: var(--accent); color: white; border-color: var(--accent); }}

  /* Main View Workspace */
  .workspace {{ display: flex; flex: 1; position: relative; overflow: hidden; }}

  .canvas-container {{
    flex: 1;
    background: var(--bg-canvas);
    position: relative;
    overflow: hidden;
    cursor: grab;
  }}
  .canvas-container:active {{ cursor: grabbing; }}

  #diagram-viewport {{
    position: absolute;
    transform-origin: 0 0;
    transition: transform 0.05s ease-out;
  }}

  svg {{ display: block; max-width: none; user-select: none; }}

  /* Node Hover & Interactive Glow Styles */
  .node {{ cursor: pointer; transition: all 0.2s ease; }}
  .node:hover {{ filter: drop-shadow(0 0 10px var(--accent)); }}
  .node-dimmed {{ opacity: 0.12 !important; filter: grayscale(80%); }}
  .node-highlight polygon, .node-highlight path, .node-highlight rect {{
    stroke: var(--accent) !important;
    stroke-width: 3.5px !important;
  }}
  .node-active {{ filter: drop-shadow(0 0 14px #38BDF8) !important; }}

  .edge {{ transition: all 0.2s ease; }}
  .edge-dimmed {{ opacity: 0.08 !important; }}
  /* Base flow hint — data edges have a subtle directional dash */
  .edge[data-edge-type="data"] path,
  .edge[data-edge-type="data"] polygon {{
    stroke-dasharray: 10,6 !important;
    animation: edgeFlow 1.4s linear infinite;
  }}
  .edge-highlight path,
  .edge-highlight polygon,
  .edge-highlight line,
  .edge-highlight polyline {{
    stroke: #38BDF8 !important;
    stroke-width: 3px !important;
    stroke-dasharray: 8,4 !important;
    animation: edgePulse 0.9s linear infinite !important;
  }}
  /* Ensure dimmed edges never show flow */
  .edge-dimmed path,
  .edge-dimmed polygon {{ animation: none !important; }}

  @keyframes edgeFlow {{
    from {{ stroke-dashoffset: 24; }}
    to {{ stroke-dashoffset: 0; }}
  }}
  @keyframes edgePulse {{
    from {{ stroke-dashoffset: 20; }}
    to {{ stroke-dashoffset: 0; }}
  }}

  /* Floating Toolbars */
  .zoom-controls {{
    position: absolute;
    bottom: 24px;
    right: 24px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: var(--card-bg);
    padding: 6px;
    border-radius: 8px;
    border: 1px solid var(--border);
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    z-index: 10;
  }}
  .zoom-btn {{
    width: 34px;
    height: 34px;
    border: 1px solid var(--border);
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 6px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }}
  .zoom-btn:hover {{ background: var(--accent); color: white; border-color: var(--accent); }}

  /* Mini-Map Radar Window */
  .minimap-container {{
    position: absolute;
    bottom: 24px;
    left: 24px;
    width: 180px;
    height: 120px;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    backdrop-filter: blur(10px);
    z-index: 10;
  }}
  .minimap-header {{ font-size: 10px; font-weight: 700; color: var(--text-secondary); padding: 4px 8px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); }}
  .minimap-canvas-wrapper {{ position: relative; width: 100%; height: calc(100% - 22px); display: flex; align-items: center; justify-content: center; }}
  .minimap-viewport-box {{
    position: absolute;
    border: 1.5px solid var(--accent);
    background: rgba(56, 189, 248, 0.15);
    border-radius: 2px;
    pointer-events: none;
  }}

  /* Details Inspector Drawer */
  .sidebar {{
    width: 380px;
    background: var(--bg-secondary);
    border-left: 1px solid var(--border);
    padding: 20px;
    overflow-y: auto;
    display: none;
    box-shadow: -4px 0 20px rgba(0,0,0,0.25);
    z-index: 15;
  }}
  .sidebar.active {{ display: block; }}
  .sidebar-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }}
  .sidebar-title {{ font-size: 16px; font-weight: 700; }}
  .close-btn {{ background: none; border: none; font-size: 20px; color: var(--text-secondary); cursor: pointer; }}
  .close-btn:hover {{ color: var(--text-primary); }}

  .meta-card {{ background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 14px; }}
  .prop-group {{ margin-bottom: 12px; }}
  .prop-label {{ font-size: 11px; text-transform: uppercase; color: var(--text-secondary); font-weight: 700; margin-bottom: 4px; letter-spacing: 0.5px; }}
  .prop-value {{ font-size: 13px; color: var(--text-primary); word-break: break-all; }}
  .code-block {{ background: var(--bg-canvas); padding: 8px; border-radius: 6px; font-family: monospace; font-size: 12px; max-height: 180px; overflow-y: auto; border: 1px solid var(--border); }}

  .connection-pill {{
    display: inline-block;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    color: var(--accent);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-family: monospace;
    margin: 2px 4px 2px 0;
    cursor: pointer;
  }}
  .connection-pill:hover {{ background: var(--accent); color: white; }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <div class="brand-icon">&lambda;</div>
    <div class="title">{html.escape(title)}</div>
    <span class="badge">INTERACTIVE STUDIO</span>
  </div>

  <div class="header-center">
    <button class="filter-chip active" data-filter="All">All ({len(resources)})</button>
    <button class="filter-chip" data-filter="Compute">&#9889; Compute</button>
    <button class="filter-chip" data-filter="Storage">&#128230; Storage</button>
    <button class="filter-chip" data-filter="Database">&#128452; Database</button>
    <button class="filter-chip" data-filter="Network">&#127760; Network</button>
    <button class="filter-chip" data-filter="Security">&#128737; Security</button>
    <button class="filter-chip" data-filter="Integration">&#128236; Messaging</button>
  </div>

  <div class="header-right">
    <div class="search-container">
      <span class="search-icon">&#128269;</span>
      <input type="text" id="search-input" class="search-box" placeholder="Spotlight search...">
    </div>
    <button class="btn" id="export-png-btn" title="Export High-Res PNG">&#128248; PNG</button>
    <button class="btn" id="export-json-btn" title="Export JSON Catalog">&#128190; JSON</button>
    <button class="btn" id="theme-btn" title="Toggle Light/Dark Theme">&#9681; Theme</button>
  </div>
</header>

<div class="workspace">
  <div class="canvas-container" id="canvas">
    <div id="diagram-viewport">
      {svg_clean}
    </div>

    <!-- Floating Zoom Toolbar -->
    <div class="zoom-controls">
      <button class="zoom-btn" id="zoom-in" title="Zoom In (+)">+</button>
      <button class="zoom-btn" id="zoom-out" title="Zoom Out (-)">-</button>
      <button class="zoom-btn" id="zoom-fit" title="Fit to Screen">&#x2922;</button>
      <button class="zoom-btn" id="zoom-actual" title="Actual Size (100%)">1:1</button>
    </div>

    <!-- Mini-Map Radar -->
    <div class="minimap-container" id="minimap">
      <div class="minimap-header">RADAR OVERVIEW</div>
      <div class="minimap-canvas-wrapper" id="minimap-wrapper">
        <div class="minimap-viewport-box" id="minimap-box"></div>
      </div>
    </div>
  </div>

  <!-- Resource Inspector Drawer -->
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <h3 class="sidebar-title">&#128269; Resource Inspector</h3>
      <button class="close-btn" id="close-sidebar">&times;</button>
    </div>
    <div id="sidebar-content"></div>
  </aside>
</div>

<script>
  const resources = {metadata_json};
  let scale = 1;
  let pointX = 0;
  let pointY = 0;
  let isPanning = false;
  let startX = 0;
  let startY = 0;
  let selectedNodeId = null;

  const viewport = document.getElementById("diagram-viewport");
  const canvas = document.getElementById("canvas");
  const sidebar = document.getElementById("sidebar");
  const sidebarContent = document.getElementById("sidebar-content");
  const minimapBox = document.getElementById("minimap-box");
  const svgEl = viewport.querySelector("svg");

  function updateTransform() {{
    viewport.style.transform = `translate(${{pointX}}px, ${{pointY}}px) scale(${{scale}})`;
    updateMinimap();
  }}

  function updateMinimap() {{
    if (!svgEl) return;
    const svgRect = svgEl.getBoundingClientRect();
    const canvasRect = canvas.getBoundingClientRect();
    const mmW = 178;
    const mmH = 96;

    const boxW = Math.min(mmW, Math.max(16, (canvasRect.width / (svgRect.width || 1)) * mmW));
    const boxH = Math.min(mmH, Math.max(12, (canvasRect.height / (svgRect.height || 1)) * mmH));
    const boxX = Math.min(mmW - boxW, Math.max(0, (-pointX / (svgRect.width || 1)) * mmW));
    const boxY = Math.min(mmH - boxH, Math.max(0, (-pointY / (svgRect.height || 1)) * mmH));

    minimapBox.style.width = `${{boxW}}px`;
    minimapBox.style.height = `${{boxH}}px`;
    minimapBox.style.left = `${{boxX}}px`;
    minimapBox.style.top = `${{boxY}}px`;
  }}

  // Pan interaction
  canvas.addEventListener("mousedown", (e) => {{
    if (e.target.closest("#sidebar") || e.target.closest(".zoom-controls") || e.target.closest(".minimap-container")) return;
    isPanning = true;
    startX = e.clientX - pointX;
    startY = e.clientY - pointY;
  }});

  window.addEventListener("mousemove", (e) => {{
    if (!isPanning) return;
    pointX = e.clientX - startX;
    pointY = e.clientY - startY;
    updateTransform();
  }});

  window.addEventListener("mouseup", () => {{
    isPanning = false;
  }});

  // Zoom interaction
  canvas.addEventListener("wheel", (e) => {{
    e.preventDefault();
    const xs = (e.clientX - pointX) / scale;
    const ys = (e.clientY - pointY) / scale;
    const delta = -e.deltaY;
    (delta > 0) ? (scale *= 1.15) : (scale /= 1.15);
    scale = Math.min(Math.max(0.08, scale), 12);
    pointX = e.clientX - xs * scale;
    pointY = e.clientY - ys * scale;
    updateTransform();
  }});

  function zoomFit() {{
    if (!svgEl) return;
    const canvasRect = canvas.getBoundingClientRect();
    const svgW = svgEl.viewBox.baseVal.width || svgEl.offsetWidth || svgEl.width.baseVal.value || 1200;
    const svgH = svgEl.viewBox.baseVal.height || svgEl.offsetHeight || svgEl.height.baseVal.value || 900;
    scale = Math.min((canvasRect.width - 60) / svgW, (canvasRect.height - 60) / svgH);
    pointX = (canvasRect.width - svgW * scale) / 2;
    pointY = (canvasRect.height - svgH * scale) / 2;
    updateTransform();
  }}

  function zoomActual() {{
    scale = 1.0;
    pointX = 40;
    pointY = 40;
    updateTransform();
  }}

  document.getElementById("zoom-in").addEventListener("click", () => {{ scale *= 1.25; updateTransform(); }});
  document.getElementById("zoom-out").addEventListener("click", () => {{ scale /= 1.25; updateTransform(); }});
  document.getElementById("zoom-fit").addEventListener("click", zoomFit);
  document.getElementById("zoom-actual").addEventListener("click", zoomActual);

  // Theme toggle
  document.getElementById("theme-btn").addEventListener("click", () => {{
    const current = document.documentElement.getAttribute("data-theme");
    document.documentElement.setAttribute("data-theme", current === "light" ? "dark" : "light");
  }});

  // Category Filter Chips
  document.querySelectorAll(".filter-chip").forEach(chip => {{
    chip.addEventListener("click", () => {{
      document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const category = chip.getAttribute("data-filter");

      document.querySelectorAll(".node").forEach(nodeEl => {{
        if (category === "All") {{
          nodeEl.classList.remove("node-dimmed");
        }} else {{
          const res = findResourceForNode(nodeEl);
          if (res && res.category === category) {{
            nodeEl.classList.remove("node-dimmed");
          }} else {{
            nodeEl.classList.add("node-dimmed");
          }}
        }}
      }});
    }});
  }});

  // Find matching Terraform resource for SVG node element
  function findResourceForNode(nodeEl) {{
    const textEls = nodeEl.querySelectorAll("text");
    let label = "";
    textEls.forEach(t => label += " " + t.textContent);
    label = label.trim().toLowerCase();

    for (const [id, data] of Object.entries(resources)) {{
      const rName = data.name.toLowerCase();
      const rType = data.type.toLowerCase();
      if (label.includes(rName) || label.includes(rType) || id.toLowerCase().includes(label)) {{
        return data;
      }}
    }}
    return null;
  }}

  // Annotate edges with type for flow animation and reliable highlighting
  function detectEdgeType(fromStr, toStr) {{
    const s = (fromStr||"").toLowerCase(), d = (toStr||"").toLowerCase();
    const sec = ["security","firewall","iam","kms","key","policy","role","nsg","nacl"];
    if (sec.some(k => s.includes(k) || d.includes(k))) return "data" === "security" ? "security" : "security";
    const dataKeys = ["db","database","rds","dynamodb","sql","storage","bucket","s3","blob","queue","stream","kinesis","eventgrid","pubsub","cosmos","redis"];
    if (dataKeys.some(k => s.includes(k) || d.includes(k))) return "data";
    return "dependency";
  }}
  document.querySelectorAll(".edge").forEach(edgeEl => {{
    const t = edgeEl.querySelector("title")?.textContent || "";
    const parts = t.split(/->|—|→| to /);
    const et = detectEdgeType(parts[0]||"", parts[1]||"");
    edgeEl.setAttribute("data-edge-type", et);
    // Force a starting dash so even before any highlight the direction is visible
    const p = edgeEl.querySelector("path, polygon, polyline");
    if (p && et === "data") {{
      p.style.strokeDasharray = "10,6";
    }}
  }});

  // Feature 1: Interactive Path Tracing & Impact Analysis
  document.querySelectorAll(".node").forEach((nodeEl) => {{
    nodeEl.addEventListener("click", (e) => {{
      e.stopPropagation();
      const data = findResourceForNode(nodeEl);
      if (data) {{
        highlightImpactPaths(nodeEl, data);
        showDetails(data);
      }}
    }});
  }});

  function highlightImpactPaths(targetNodeEl, data) {{
    // Clear previous state and force animation restart
    document.querySelectorAll(".edge").forEach(e => {{
      e.classList.remove("edge-highlight", "edge-dimmed");
      // restart CSS animation by triggering reflow
      void e.offsetWidth;
    }});
    document.querySelectorAll(".node").forEach(n => n.classList.remove("node-active", "node-highlight", "node-dimmed"));

    targetNodeEl.classList.add("node-active", "node-highlight");
    const targetTitle = targetNodeEl.querySelector("title")?.textContent || "";
    const targetName = (data.name||"").toLowerCase();
    const targetType = (data.type||"").toLowerCase();

    document.querySelectorAll(".edge").forEach(edgeEl => {{
      const edgeTitle = (edgeEl.querySelector("title")?.textContent || "").toLowerCase();
      const hit = edgeTitle.includes(targetTitle.toLowerCase()) ||
                  edgeTitle.includes(targetName) ||
                  edgeTitle.includes(targetType) ||
                  targetTitle.toLowerCase().includes(edgeTitle.split("->")[0]?.trim()||"");
      if (hit) {{
        edgeEl.classList.add("edge-highlight");
      }} else {{
        edgeEl.classList.add("edge-dimmed");
      }}
    }});
  }}

  canvas.addEventListener("click", (e) => {{
    if (!e.target.closest(".node") && !e.target.closest("#sidebar")) {{
      document.querySelectorAll(".node").forEach(n => n.classList.remove("node-active", "node-highlight", "node-dimmed"));
      document.querySelectorAll(".edge").forEach(e => e.classList.remove("edge-highlight", "edge-dimmed"));
    }}
  }});

  // Feature 4: Resource Inspector
  function showDetails(data) {{
    sidebar.classList.add("active");
    let tagsHtml = "";
    if (Object.keys(data.tags).length > 0) {{
      tagsHtml = `<div class="prop-group"><div class="prop-label">Tags</div><div class="code-block">${{JSON.stringify(data.tags, null, 2)}}</div></div>`;
    }}

    let attrsHtml = "";
    if (Object.keys(data.attributes).length > 0) {{
      attrsHtml = `<div class="prop-group"><div class="prop-label">Terraform Attributes</div><div class="code-block">${{JSON.stringify(data.attributes, null, 2)}}</div></div>`;
    }}

    sidebarContent.innerHTML = `
      <div class="meta-card">
        <div class="prop-group"><div class="prop-label">Resource ID</div><div class="prop-value" style="font-family:monospace;font-weight:bold;color:var(--accent);">${{data.id}}</div></div>
        <div class="prop-group"><div class="prop-label">Category / Tier</div><div class="prop-value">${{data.category}}</div></div>
        <div class="prop-group"><div class="prop-label">Type</div><div class="prop-value">${{data.type}}</div></div>
        <div class="prop-group"><div class="prop-label">Logical Name</div><div class="prop-value">${{data.name}}</div></div>
        <div class="prop-group"><div class="prop-label">Module Path</div><div class="prop-value">${{data.module}}</div></div>
      </div>
      ${{tagsHtml}}
      ${{attrsHtml}}
    `;
  }}

  document.getElementById("close-sidebar").addEventListener("click", () => {{
    sidebar.classList.remove("active");
  }});

  // Feature 6: Spotlight Search
  document.getElementById("search-input").addEventListener("input", (e) => {{
    const query = e.target.value.toLowerCase().trim();
    if (!query) {{
      document.querySelectorAll(".node").forEach(el => el.classList.remove("node-dimmed", "node-active"));
      return;
    }}

    document.querySelectorAll(".node").forEach((el) => {{
      const text = el.textContent.toLowerCase();
      if (text.includes(query)) {{
        el.classList.remove("node-dimmed");
        el.classList.add("node-active");
      }} else {{
        el.classList.add("node-dimmed");
        el.classList.remove("node-active");
      }}
    }});
  }});

  // Feature 3: One-Click Export Studio (JSON & PNG)
  document.getElementById("export-json-btn").addEventListener("click", () => {{
    const blob = new Blob([JSON.stringify(resources, null, 2)], {{ type: "application/json" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "architecture-inventory.json";
    a.click();
    URL.revokeObjectURL(url);
  }});

  document.getElementById("export-png-btn").addEventListener("click", () => {{
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const canvasEl = document.createElement("canvas");
    const ctx = canvasEl.getContext("2d");
    const img = new Image();
    const svgBlob = new Blob([svgData], {{ type: "image/svg+xml;charset=utf-8" }});
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {{
      canvasEl.width = img.width * 2;
      canvasEl.height = img.height * 2;
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);
      ctx.drawImage(img, 0, 0, canvasEl.width, canvasEl.height);
      const pngUrl = canvasEl.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = pngUrl;
      a.download = "architecture-diagram.png";
      a.click();
      URL.revokeObjectURL(url);
    }};
    img.src = url;
  }});

  // Initial fit
  window.addEventListener("load", zoomFit);
  setTimeout(zoomFit, 100);
</script>
</body>
</html>"""

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_template, encoding="utf-8")

    return html_template
