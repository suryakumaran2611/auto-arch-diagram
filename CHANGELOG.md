# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added
- **3-Stage Layout Pipeline**: Integrated Graphviz geometry computation (`dot -Tdot`), GVPR layout transformation (`layout_postprocess.gvpr` and Python fallback `layout_postprocess.py`), and `neato -n2` rendering for visual alignment.
- **Provider Render Configurations**: Added declarative YAML configs in `tools/render_config/` (`aws.yaml`, `azure.yaml`, `gcp.yaml`, `default.yaml`) defining draw orders, edge/outer nodes, auto annotations, and attribute-based node variants.
- **Grid Wrapping**: Automatic wrapping of nodes inside clusters to max 3 nodes per row (`MAX_NODES_PER_ROW = 3`) via `rank="same"` and invisible column edges.
- **Interactive Offline HTML Export (`--out-html`)**: Zero-dependency standalone HTML diagrams with smooth pan/zoom, node metadata drawer, real-time resource search/filter, and theme toggle.
- **Pre-Generated Plan Support (`--planfile`, `--graphfile`)**: Ingests `terraform show -json` plan and `terraform graph` DOT outputs directly without requiring cloud credentials or local Terraform.
- **Simplified Executive View (`--simplified`)**: Strips low-level network plumbing resources while bridging compute-to-gateway flows.
- **Model Context Protocol (MCP) Server (`tools/mcp_server.py`)**: Stdio JSON-RPC 2.0 interface exposing `list_resources`, `explain_graph`, and `generate_diagram` tools for AI pair programmers.
- **Flow Annotations (`--annotate`)**: Step-by-step numbered data flow badges on nodes and edges with an interactive legend.
- **Remote Git Source (`--source`)**: Shallow clone and direct diagramming of remote git repositories.
- **Multi-Cloud Excellence**: Single-canvas multi-cloud diagrams (AWS, Azure, GCP, OCI, IBM) with brand accents and tint backgrounds.

### Changed
- Node cards standardized with uniform dimensions and proportional font/icon scaling via `--fontsize` and `--iconsize`.
- Security groups rendered as unobtrusive top-right corner shield badges (`_badgenode="1"`), with an `--expand-badges` escape hatch.
- Cluster labels pinned to bottom-left with downward box expansion (`labelPad = 95pt`) and sibling collision resolution.

## [1.0.0] - 2026-01-15

- Initial public release of the reusable IaC-to-diagram GitHub Actions workflow.
