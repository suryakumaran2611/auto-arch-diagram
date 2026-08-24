"""Self-contained interactive HTML architecture diagram exporter.

Generates a standalone, feature-rich offline HTML viewer with:
1. Smooth Pan, Smooth Zoom (wheel/pinch), Fit-to-Screen, Actual 1:1, and Fullscreen.
2. Interactive Path Tracing & Impact Analysis (Dependency blast radius & flow glowing animations).
3. Dynamic Category Filter Chips with automatic flow path and component highlighting.
4. Animated Flows for Data, Security (IAM, KMS, TLS, Policies), Network, and Dependency streams.
5. Robust, Information-Heavy Resource Inspector Drawer with key specs, topology radar, tags, and searchable properties.
6. In-Browser Multi-Format Export Studio (Download PNG, Download SVG, Download JSON Inventory).
7. Smart Spotlight Search with instant auto-focus and glowing pulse.
8. Mini-Map Radar Navigation Viewport.
9. Sleek Dark / Light theme toggle with persistence.
10. 100% self-contained and offline-ready (zero external CDN dependencies).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional


# Comprehensive provider brand colors
PROVIDER_COLORS = {
    "aws": {"bg": "#FF9900", "text": "#FFFFFF", "label": "AWS"},
    "azure": {"bg": "#0078D4", "text": "#FFFFFF", "label": "Azure"},
    "azurerm": {"bg": "#0078D4", "text": "#FFFFFF", "label": "Azure"},
    "gcp": {"bg": "#4285F4", "text": "#FFFFFF", "label": "GCP"},
    "google": {"bg": "#4285F4", "text": "#FFFFFF", "label": "GCP"},
    "oci": {"bg": "#C74634", "text": "#FFFFFF", "label": "OCI"},
    "ibm": {"bg": "#0F62FE", "text": "#FFFFFF", "label": "IBM"},
    "other": {"bg": "#64748B", "text": "#FFFFFF", "label": "Cloud"},
}

# Category icon and color definitions
CATEGORY_META = {
    "Compute": {"icon": "⚡", "color": "#F59E0B"},
    "Storage": {"icon": "📦", "color": "#3B82F6"},
    "Database": {"icon": "💾", "color": "#10B981"},
    "Network": {"icon": "🌐", "color": "#6366F1"},
    "Security": {"icon": "🛡️", "color": "#EC4899"},
    "Integration": {"icon": "📬", "color": "#8B5CF6"},
    "Containers": {"icon": "🐳", "color": "#06B6D4"},
    "Analytics & AI": {"icon": "🧠", "color": "#F97316"},
    "Management": {"icon": "📊", "color": "#64748B"},
    "Other": {"icon": "⚙️", "color": "#94A3B8"},
}


def _classify_resource_type(rtype: str, kind: str = "", provider: str = "") -> str:
    """Exhaustive classifier mapping cloud resources to architectural tiers."""
    r = f"{rtype} {kind}".lower().replace("-", "_").replace("::", "_").replace(".", "_").replace("/", "_")

    # 1. Containers
    if any(k in r for k in [
        "eks", "aks", "gke", "kubernetes", "k8s", "container_group", "container_cluster",
        "ecs", "fargate", "container", "ecr", "acr", "artifact_registry", "container_registry",
        "container_app", "containerapp", "task_definition", "container_service"
    ]):
        return "Containers"

    # 2. Storage
    if any(k in r for k in [
        "s3", "bucket", "storage_bucket", "storage_account", "storageaccount", "blob", "file_share",
        "ebs", "efs", "fsx", "glacier", "backup_vault", "backup", "objectstorage", "filestore",
        "disk", "volume", "storage", "datalake", "data_lake", "archive", "s3_bucket", "blob_service"
    ]):
        return "Storage"

    # 3. Database
    if any(k in r for k in [
        "rds", "dynamo", "dynamodb", "aurora", "cosmos", "cosmosdb", "sql", "database", "mysql", "postgres",
        "postgresql", "redis", "elasticache", "memorystore", "redshift", "spanner", "bigtable", "mongodb",
        "mongo", "documentdb", "neptune", "timestream", "memorydb", "db_instance", "db_cluster",
        "db_subnet", "mssql", "mariadb", "cassandra"
    ]):
        return "Database"

    # 4. Security & IAM
    if any(k in r for k in [
        "iam", "role", "policy", "security_group", "securitygroup", "nsg", "nacl", "kms",
        "key_vault", "keyvault", "secret", "secretsmanager", "vault", "certificate", "acm",
        "waf", "wafv2", "shield", "guardduty", "cognito", "identity", "firewall_rule",
        "network_security", "keyring", "crypto_key", "ssh_key", "authorizer", "access_control"
    ]):
        return "Security"

    # 5. Network & Content Delivery
    if any(k in r for k in [
        "vpc", "vnet", "vcn", "subnet", "subnetwork", "route", "route_table", "gateway",
        "internet_gateway", "nat_gateway", "nat", "lb", "alb", "nlb", "elb", "load_balancer",
        "loadbalancer", "application_gateway", "app_gateway", "cloudfront", "cdn", "dns",
        "route53", "traffic_manager", "frontdoor", "front_door", "vpn", "direct_connect",
        "interconnect", "public_ip", "eip", "network_interface", "nic", "network", "peering",
        "transit_gateway", "firewall", "local_gateway", "endpoint", "vpc_endpoint"
    ]):
        return "Network"

    # 6. Integration, Events & Messaging
    if any(k in r for k in [
        "sqs", "sns", "eventbridge", "event_bridge", "eventgrid", "event_grid", "eventhub",
        "event_hub", "service_bus", "servicebus", "pubsub", "pub_sub", "kafka", "msk",
        "kinesis", "mq", "apigateway", "api_gateway", "apim", "api_management", "apigee",
        "stepfunctions", "sfn", "workflow", "logic_app", "logicapp", "notification", "queue", "topic"
    ]):
        return "Integration"

    # 7. Analytics & AI / ML
    if any(k in r for k in [
        "sagemaker", "bedrock", "glue", "emr", "athena", "quicksight", "data_factory",
        "datafactory", "synapse", "databricks", "vertex", "vertex_ai", "bigquery",
        "dataproc", "dataflow", "kinesis_analytics", "opensearch", "elasticsearch"
    ]):
        return "Analytics & AI"

    # 8. Management & Observability
    if any(k in r for k in [
        "cloudwatch", "cloudtrail", "log_group", "log_analytics", "application_insights",
        "monitor", "alarm", "metric", "insight", "config_rule", "systems_manager", "ssm",
        "health", "dashboard", "diagnostic"
    ]):
        return "Management"

    # 9. Compute
    if any(k in r for k in [
        "lambda", "function", "function_app", "instance", "ec2", "virtual_machine", "vm",
        "app_service", "appservice", "cloud_run", "cloudrun", "cloudfunctions", "batch",
        "apprunner", "app_runner", "compute", "server", "autoscaling", "asg", "launch_template"
    ]):
        return "Compute"

    return "Other"


def _format_service_name(rtype: str, kind: str = "", provider: str = "") -> str:
    """Generate user-friendly, descriptive cloud service names."""
    r = rtype.lower()
    if "s3_bucket" in r or "s3" in r:
        return "Amazon S3 Bucket"
    if "lambda" in r:
        return "AWS Lambda Function"
    if "dynamodb" in r:
        return "Amazon DynamoDB Table"
    if "rds_cluster" in r:
        return "Amazon Aurora / RDS Cluster"
    if "rds" in r:
        return "Amazon RDS Database"
    if "cloudfront" in r:
        return "Amazon CloudFront CDN"
    if "security_group" in r:
        return "AWS Security Group"
    if "subnet" in r:
        return "VPC Subnet"
    if "vpc" in r:
        return "Virtual Private Cloud (VPC)"
    if "iam_role" in r:
        return "AWS IAM Role"
    if "sqs" in r:
        return "Amazon SQS Queue"
    if "sns" in r:
        return "Amazon SNS Topic"
    if "kms" in r:
        return "AWS KMS Encryption Key"
    if "storage_account" in r or "storageaccount" in r:
        return "Azure Storage Account"
    if "storage_bucket" in r:
        return "Google Cloud Storage Bucket"
    if "virtual_machine" in r or "instance" in r:
        return "Virtual Machine / Compute Instance"

    clean = re.sub(r"^(aws_|azurerm_|google_|oci_|ibm_|microsoft\.|aws::)", "", r, flags=re.I)
    return clean.replace("_", " ").replace(".", " ").title()


def _normalize_token_str(s: str) -> str:
    """Normalize string to alphanumeric lowercase for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', s.lower().replace("…", "").replace("...", ""))


def _extract_tokens(s: str) -> set[str]:
    """Extract set of words/tokens from a string."""
    return set(re.findall(r'[a-z0-9]+', s.lower().replace("…", "").replace("...", "")))


def export_interactive_html(
    svg_content: str,
    resources: dict[str, dict[str, Any]],
    title: str = "Architecture Diagram",
    out_path: Optional[Path] = None,
    edges: Optional[Iterable[tuple[str, str]]] = None,
) -> str:
    """Generate a rich, standalone interactive HTML studio file."""
    # Clean SVG content if wrapped in XML header or namespace prefixes
    svg_clean = re.sub(r'<\?xml[^>]*\?>', '', svg_content).strip()
    svg_clean = re.sub(r'<!DOCTYPE[^>]*>', '', svg_clean).strip()
    svg_clean = re.sub(r'<(/?)ns[0-9]+:', r'<\1', svg_clean)
    svg_clean = re.sub(r'\s+xmlns:ns[0-9]+="[^"]*"', '', svg_clean)
    if "<svg" in svg_clean and "xmlns=" not in svg_clean[:200]:
        svg_clean = svg_clean.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)

    # Normalize SVG dimensions: 1 user unit = 1 px
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

    # Extract edge connections if provided, or parse from SVG
    inbound_map: dict[str, list[str]] = {r: [] for r in resources}
    outbound_map: dict[str, list[str]] = {r: [] for r in resources}

    # Build comprehensive resource metadata dictionary
    res_metadata: dict[str, Any] = {}
    categories_count: dict[str, int] = {"All": len(resources)}

    for res_id, res_data in resources.items():
        r_type = str(res_data.get("type") or (res_id.split(".")[0] if "." in res_id else ""))
        r_name = str(res_data.get("name") or (res_id.split(".", 1)[1] if "." in res_id else res_id))
        r_kind = str(res_data.get("Kind") or "")
        r_provider = str(res_data.get("provider") or res_data.get("Provider") or "aws").lower()
        if r_provider.startswith("azurerm"):
            r_provider = "azure"
        elif r_provider.startswith("google"):
            r_provider = "gcp"

        cat = _classify_resource_type(r_type, r_kind, r_provider)
        categories_count[cat] = categories_count.get(cat, 0) + 1

        service_name = _format_service_name(r_type, r_kind, r_provider)

        key_specs: dict[str, str] = {}
        for key in [
            "bucket", "bucket_name", "instance_type", "ami", "runtime", "handler",
            "engine", "engine_version", "instance_class", "allocated_storage",
            "cidr_block", "cidr", "vpc_id", "subnet_id", "port", "role", "arn",
            "schedule_expression", "topic_name", "queue_name", "location", "sku"
        ]:
            if key in res_data and res_data[key]:
                key_specs[key.replace("_", " ").title()] = str(res_data[key])

        tags = res_data.get("tags") or res_data.get("Tags") or {}
        if not isinstance(tags, dict):
            tags = {}

        filtered_attrs: dict[str, str] = {}
        for k, v in res_data.items():
            if k.lower() not in {"tags", "type", "name", "module", "provider", "kind"}:
                if isinstance(v, (dict, list)):
                    filtered_attrs[k] = json.dumps(v)
                else:
                    filtered_attrs[k] = str(v)

        res_metadata[res_id] = {
            "id": res_id,
            "name": r_name,
            "type": r_type,
            "kind": r_kind,
            "service_name": service_name,
            "category": cat,
            "provider": r_provider,
            "provider_info": PROVIDER_COLORS.get(r_provider, PROVIDER_COLORS["other"]),
            "module": str(res_data.get("module") or "root"),
            "key_specs": key_specs,
            "tags": tags,
            "attributes": filtered_attrs,
            "inbound": [],
            "outbound": [],
            "blast_radius": 0,
        }

    # Match an SVG node's title and inner text to the best resource in res_metadata
    def _find_best_resource_for_node(node_title: str, text_list: list[str]) -> Optional[str]:
        # 1. Exact or prefix-stripped title match
        clean_title = re.sub(r"^(tf_|node_)", "", node_title.strip())
        if clean_title in res_metadata:
            return clean_title

        # 2. Token and normalized text score matching
        node_text_raw = " ".join(text_list)
        node_norm = _normalize_token_str(node_text_raw)
        node_tokens = _extract_tokens(node_text_raw)

        best_id = None
        best_score = 0

        for r_id, r_info in res_metadata.items():
            r_name = r_info["name"]
            r_type = r_info["type"]
            name_norm = _normalize_token_str(r_name)
            name_tokens = _extract_tokens(r_name)
            type_tokens = _extract_tokens(r_type)

            score = 0
            if name_norm and (name_norm in node_norm or node_norm in name_norm):
                score += 100
            elif name_tokens and name_tokens.issubset(node_tokens):
                score += 80
            elif name_tokens and (name_tokens & node_tokens):
                score += len(name_tokens & node_tokens) * 30

            # Check prefix match for truncated names (e.g. "feature store…" vs "feature_store_db")
            if name_norm and len(name_norm) >= 4 and node_norm and len(node_norm) >= 4:
                for t in text_list:
                    t_norm = _normalize_token_str(t)
                    if t_norm and len(t_norm) >= 4 and (name_norm.startswith(t_norm) or t_norm.startswith(name_norm)):
                        score += 60

            # Include type token match
            if type_tokens and (type_tokens & node_tokens):
                score += len(type_tokens & node_tokens) * 10

            if score > best_score:
                best_score = score
                best_id = r_id

        if best_id and best_score >= 20:
            return best_id
        return None

    # Map SVG node UUIDs and IDs to matched resource IDs
    uuid_to_resid: dict[str, str] = {}

    def _tag_node(match: re.Match) -> str:
        full_node = match.group(0)
        title_m = re.search(r"<title>([\s\S]*?)</title>", full_node)
        node_uuid = title_m.group(1).strip() if title_m else ""
        id_m = re.search(r'id="([^"]+)"', full_node)
        g_id = id_m.group(1).strip() if id_m else ""

        text_matches = re.findall(r"<text[^>]*>([\s\S]*?)</text>", full_node)
        matched_id = _find_best_resource_for_node(node_uuid, text_matches)

        if matched_id and matched_id in res_metadata:
            if node_uuid:
                uuid_to_resid[node_uuid] = matched_id
            if g_id:
                uuid_to_resid[g_id] = matched_id
            cat = res_metadata[matched_id]["category"]
            node_tag = f'<g data-resource-id="{html.escape(matched_id)}" data-category="{cat}" '
            return re.sub(r'<g\s+', node_tag, full_node, count=1)
        return full_node

    svg_tagged = re.sub(r'<g\s+[^>]*class="node"[^>]*>[\s\S]*?</g>', _tag_node, svg_clean)

    def _resolve_endpoint_id(raw_str: str) -> Optional[str]:
        if not raw_str:
            return None
        if raw_str in uuid_to_resid:
            return uuid_to_resid[raw_str]
        if raw_str in res_metadata:
            return raw_str
        clean = re.sub(r"^(tf_|node_)", "", raw_str.strip())
        if clean in res_metadata:
            return clean
        for r_id, r_info in res_metadata.items():
            if r_id.lower() == clean.lower() or r_info["name"].lower() == clean.lower():
                return r_id
        return None

    # Process Edges and populate inbound / outbound connections
    edge_list: list[tuple[str, str]] = list(edges) if edges else []
    if not edge_list:
        for match in re.finditer(r'<g\s+[^>]*class="edge"[^>]*>[\s\S]*?<title>([\s\S]*?)</title>', svg_clean):
            edge_title = match.group(1).strip().replace("&#45;&gt;", "->").replace("&gt;", ">").replace("--", "->")
            parts = re.split(r'->|—|→|\sto\s', edge_title)
            if len(parts) == 2:
                s_id = _resolve_endpoint_id(parts[0].strip())
                d_id = _resolve_endpoint_id(parts[1].strip())
                if s_id and d_id:
                    edge_list.append((s_id, d_id))

    for src_id, dst_id in edge_list:
        if src_id in res_metadata and dst_id in res_metadata:
            if dst_id not in outbound_map[src_id]:
                outbound_map[src_id].append(dst_id)
            if src_id not in inbound_map[dst_id]:
                inbound_map[dst_id].append(src_id)

    # Update metadata with connections and blast radius
    for r_id, r_info in res_metadata.items():
        in_c = inbound_map.get(r_id, [])
        out_c = outbound_map.get(r_id, [])
        r_info["inbound"] = in_c
        r_info["outbound"] = out_c
        r_info["blast_radius"] = len(in_c) + len(out_c)

    # Tag Edges with data-source, data-target, and data-edge-type
    def _tag_edge(match: re.Match) -> str:
        full_edge = match.group(0)
        title_m = re.search(r"<title>([\s\S]*?)</title>", full_edge)
        edge_title = title_m.group(1).strip().replace("&#45;&gt;", "->").replace("&gt;", ">").replace("--", "->") if title_m else ""
        parts = re.split(r'->|—|→|\sto\s', edge_title)

        s_raw = parts[0].strip() if len(parts) >= 2 else ""
        d_raw = parts[1].strip() if len(parts) >= 2 else ""

        src_id = _resolve_endpoint_id(s_raw)
        dst_id = _resolve_endpoint_id(d_raw)

        edge_type = "dependency"
        s_cat = res_metadata.get(src_id, {}).get("category", "") if src_id else ""
        d_cat = res_metadata.get(dst_id, {}).get("category", "") if dst_id else ""

        if s_cat == "Security" or d_cat == "Security" or any(k in edge_title.lower() for k in ["iam", "kms", "policy", "role", "secret", "vault", "auth"]):
            edge_type = "security"
        elif s_cat in {"Database", "Storage", "Integration"} or d_cat in {"Database", "Storage", "Integration"}:
            edge_type = "data"
        elif s_cat == "Network" or d_cat == "Network":
            edge_type = "network"

        attrs = f'data-edge-type="{edge_type}"'
        if src_id:
            attrs += f' data-source="{html.escape(src_id)}"'
        if dst_id:
            attrs += f' data-target="{html.escape(dst_id)}"'

        edge_tag = f'<g {attrs} '
        return re.sub(r'<g\s+', edge_tag, full_edge, count=1)

    svg_tagged = re.sub(r'<g\s+[^>]*class="edge"[^>]*>[\s\S]*?</g>', _tag_edge, svg_tagged)

    # Prepare Category Filter Chips HTML
    filter_chips_html = '<button class="filter-chip active" data-filter="All">All (' + str(len(resources)) + ')</button>'
    for cat_name in ["Compute", "Storage", "Database", "Network", "Security", "Integration", "Containers", "Analytics & AI", "Management"]:
        count = categories_count.get(cat_name, 0)
        if count > 0:
            meta = CATEGORY_META.get(cat_name, CATEGORY_META["Other"])
            filter_chips_html += f'<button class="filter-chip" data-filter="{cat_name}">{meta["icon"]} {cat_name} ({count})</button>'

    metadata_json = json.dumps(res_metadata, indent=2)

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
    --card-bg: rgba(22, 31, 48, 0.92);
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
    --card-bg: rgba(255, 255, 255, 0.95);
    --badge-bg: #E2E8F0;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; }}
  body {{ background: var(--bg-primary); color: var(--text-primary); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}

  /* Top Navigation Bar */
  header {{
    height: 60px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    z-index: 20;
    gap: 12px;
  }}

  .header-left {{ display: flex; align-items: center; gap: 12px; flex-shrink: 0; }}
  .brand-icon {{ width: 28px; height: 28px; border-radius: 6px; background: linear-gradient(135deg, #38BDF8, #6366F1); display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: 14px; box-shadow: 0 2px 8px rgba(56,189,248,0.3); }}
  .title {{ font-size: 15px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.2px; }}
  .badge {{ background: var(--badge-bg); color: var(--accent); border: 1px solid var(--border); padding: 3px 9px; border-radius: 12px; font-size: 11px; font-weight: 700; }}

  .header-center {{ display: flex; align-items: center; gap: 6px; overflow-x: auto; padding: 4px 0; }}
  .filter-chip {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 5px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }}
  .filter-chip:hover, .filter-chip.active {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
  }}

  .header-right {{ display: flex; align-items: center; gap: 8px; flex-shrink: 0; }}
  .search-container {{ position: relative; }}
  .search-box {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px 6px 30px;
    color: var(--text-primary);
    font-size: 13px;
    width: 180px;
    outline: none;
    transition: all 0.2s ease;
  }}
  .search-box:focus {{ border-color: var(--accent); width: 240px; box-shadow: 0 0 8px var(--accent-glow); }}
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
  .node:hover {{ filter: drop-shadow(0 0 14px var(--accent)) brightness(1.15) !important; }}
  .node-dimmed {{ opacity: 0.12 !important; filter: grayscale(90%) !important; }}
  .node-highlight, .node-active {{
    filter: drop-shadow(0 0 18px #38BDF8) brightness(1.25) !important;
    opacity: 1.0 !important;
  }}
  .node-highlight text, .node-active text {{
    fill: #38BDF8 !important;
    font-weight: bold !important;
  }}
  .node-highlight polygon, .node-highlight path, .node-highlight rect, .node-highlight ellipse {{
    stroke: var(--accent) !important;
    stroke-width: 3.5px !important;
  }}

  /* Edge Styling and Directional Flow Animations */
  .edge {{ transition: all 0.2s ease; }}
  .edge-dimmed {{ opacity: 0.06 !important; }}

  /* 1. Data Flow Animation (Cyan Stream) */
  .edge[data-edge-type="data"] path,
  .edge[data-edge-type="data"] polygon {{
    stroke: #38BDF8 !important;
    stroke-dasharray: 10,5 !important;
    animation: edgeFlow 1.2s linear infinite;
  }}

  /* 2. Security Flow Animation (Emerald / Violet Security Authorization Stream) */
  .edge[data-edge-type="security"] path,
  .edge[data-edge-type="security"] polygon {{
    stroke: #10B981 !important;
    stroke-dasharray: 8,4 !important;
    animation: edgeSecurityFlow 1.0s linear infinite;
  }}

  /* 3. Network Flow (Royal Blue Stream) */
  .edge[data-edge-type="network"] path,
  .edge[data-edge-type="network"] polygon {{
    stroke: #60A5FA !important;
    stroke-dasharray: 6,4 !important;
    animation: edgeFlow 1.5s linear infinite;
  }}

  /* 4. Active Highlighted Edge Flow */
  .edge-highlight path,
  .edge-highlight polygon,
  .edge-highlight line,
  .edge-highlight polyline {{
    stroke: #38BDF8 !important;
    stroke-width: 3.5px !important;
    stroke-dasharray: 8,4 !important;
    filter: drop-shadow(0 0 8px rgba(56,189,248,0.9)) !important;
    animation: edgePulse 0.8s linear infinite !important;
    opacity: 1 !important;
  }}

  .edge-dimmed path,
  .edge-dimmed polygon {{ animation: none !important; }}

  @keyframes edgeFlow {{
    from {{ stroke-dashoffset: 24; }}
    to {{ stroke-dashoffset: 0; }}
  }}
  @keyframes edgeSecurityFlow {{
    from {{ stroke-dashoffset: 20; }}
    to {{ stroke-dashoffset: 0; }}
  }}
  @keyframes edgePulse {{
    from {{ stroke-dashoffset: 18; }}
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

  /* Comprehensive Details Inspector Drawer */
  .sidebar {{
    width: 420px;
    background: var(--bg-secondary);
    border-left: 1px solid var(--border);
    padding: 20px;
    overflow-y: auto;
    display: none;
    box-shadow: -6px 0 25px rgba(0,0,0,0.35);
    z-index: 25;
  }}
  .sidebar.active {{ display: block; }}
  .sidebar-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }}
  .sidebar-title {{ font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
  .close-btn {{ background: none; border: none; font-size: 22px; color: var(--text-secondary); cursor: pointer; }}
  .close-btn:hover {{ color: var(--text-primary); }}

  /* Inspector Cards & Sections */
  .inspector-hero {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
  }}
  .inspector-hero-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .provider-pill {{
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .category-pill {{
    background: var(--badge-bg);
    border: 1px solid var(--border);
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }}
  .res-title {{ font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }}
  .res-subtitle {{ font-size: 12px; color: var(--text-secondary); font-family: monospace; word-break: break-all; }}

  /* Action Buttons in Drawer */
  .drawer-actions {{ display: flex; gap: 6px; margin-top: 10px; }}
  .drawer-btn {{
    flex: 1;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 6px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    text-align: center;
    transition: all 0.15s ease;
  }}
  .drawer-btn:hover {{ background: var(--accent); color: white; border-color: var(--accent); }}

  .meta-card {{
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 14px;
  }}
  .section-label {{
    font-size: 11px;
    text-transform: uppercase;
    color: var(--text-secondary);
    font-weight: 800;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .kv-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .kv-table td {{ padding: 5px 0; vertical-align: top; border-bottom: 1px solid rgba(255,255,255,0.05); }}
  .kv-key {{ color: var(--text-secondary); width: 38%; font-weight: 500; }}
  .kv-val {{ color: var(--text-primary); font-family: monospace; word-break: break-all; }}

  .topology-badge {{
    background: var(--badge-bg);
    border: 1px solid var(--border);
    color: var(--accent);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-family: monospace;
    margin: 3px 4px 3px 0;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .topology-badge:hover {{ background: var(--accent); color: white; }}

  .tag-chip {{
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: var(--accent);
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    display: inline-block;
    margin: 2px 4px 2px 0;
  }}

  /* Toast Notification */
  #toast {{
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: #0284C7;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
    z-index: 100;
  }}
  #toast.show {{ opacity: 1; }}
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
    {filter_chips_html}
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
      {svg_tagged}
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

<div id="toast">Copied to clipboard</div>

<script>
  const resources = {metadata_json};
  let scale = 1;
  let pointX = 0;
  let pointY = 0;
  let isPanning = false;
  let startX = 0;
  let startY = 0;
  let activeFilter = "All";

  const viewport = document.getElementById("diagram-viewport");
  const canvas = document.getElementById("canvas");
  const sidebar = document.getElementById("sidebar");
  const sidebarContent = document.getElementById("sidebar-content");
  const minimapBox = document.getElementById("minimap-box");
  const svgEl = viewport.querySelector("svg");
  const toast = document.getElementById("toast");

  function showToast(msg) {{
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
  }}

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
    scale = Math.min(Math.max(0.06, scale), 16);
    pointX = e.clientX - xs * scale;
    pointY = e.clientY - ys * scale;
    updateTransform();
  }});

  function zoomFit() {{
    if (!svgEl) return;
    const canvasRect = canvas.getBoundingClientRect();
    const svgW = svgEl.viewBox?.baseVal?.width || svgEl.offsetWidth || 1200;
    const svgH = svgEl.viewBox?.baseVal?.height || svgEl.offsetHeight || 900;
    
    // Fit to width or height with comfortable padding
    const fitScale = Math.min((canvasRect.width - 60) / svgW, (canvasRect.height - 60) / svgH);
    scale = Math.max(0.45, Math.min(fitScale, 1.2));
    
    pointX = (canvasRect.width - svgW * scale) / 2;
    pointY = 20;
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

  function norm(str) {{
    return (str || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  }}

  // Find matching resource for an SVG node element
  function findResourceForNode(nodeEl) {{
    // 1. Direct tagged attribute
    const taggedId = nodeEl.getAttribute("data-resource-id");
    if (taggedId && resources[taggedId]) return resources[taggedId];

    // 2. SVG title match
    const titleText = (nodeEl.querySelector("title")?.textContent || "").trim();
    if (titleText) {{
      const cleanTitle = titleText.replace(/^(tf_|node_)/, "");
      if (resources[cleanTitle]) return resources[cleanTitle];
      for (const [id, data] of Object.entries(resources)) {{
        if (id.toLowerCase() === cleanTitle.toLowerCase() || data.name.toLowerCase() === cleanTitle.toLowerCase()) {{
          return data;
        }}
      }}
    }}

    // 3. Normalized fuzzy token search across text elements
    const textEls = nodeEl.querySelectorAll("text");
    let textRaw = "";
    textEls.forEach(t => textRaw += " " + t.textContent);
    const nodeNorm = norm(textRaw);

    let bestRes = null;
    let bestScore = 0;

    for (const [id, data] of Object.entries(resources)) {{
      const nameNorm = norm(data.name);
      let score = 0;

      if (nameNorm && (nodeNorm.includes(nameNorm) || nameNorm.includes(nodeNorm))) {{
        score = 100;
      }} else if (nameNorm && nameNorm.length >= 4 && nodeNorm.length >= 4 && (nodeNorm.startsWith(nameNorm.substring(0, 5)) || nameNorm.startsWith(nodeNorm.substring(0, 5)))) {{
        score = 80;
      }}

      if (score > bestScore) {{
        bestScore = score;
        bestRes = data;
      }}
    }}

    return bestScore >= 50 ? bestRes : null;
  }}

  // Category Filter Chips with Flow Highlighting
  document.querySelectorAll(".filter-chip").forEach(chip => {{
    chip.addEventListener("click", () => {{
      document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      activeFilter = chip.getAttribute("data-filter");

      const matchingResIds = new Set();

      document.querySelectorAll(".node").forEach(nodeEl => {{
        if (activeFilter === "All") {{
          nodeEl.classList.remove("node-dimmed", "node-active", "node-highlight");
        }} else {{
          const res = findResourceForNode(nodeEl);
          const nodeCat = nodeEl.getAttribute("data-category") || (res ? res.category : "");
          if (nodeCat === activeFilter) {{
            nodeEl.classList.remove("node-dimmed");
            nodeEl.classList.add("node-highlight");
            if (res) matchingResIds.add(res.id);
          }} else {{
            nodeEl.classList.add("node-dimmed");
            nodeEl.classList.remove("node-highlight", "node-active");
          }}
        }}
      }});

      // Flow highlighting: highlight all connected edges of matching components
      document.querySelectorAll(".edge").forEach(edgeEl => {{
        if (activeFilter === "All") {{
          edgeEl.classList.remove("edge-highlight", "edge-dimmed");
        }} else {{
          const srcId = edgeEl.getAttribute("data-source");
          const dstId = edgeEl.getAttribute("data-target");
          const edgeTitle = (edgeEl.querySelector("title")?.textContent || "").toLowerCase();

          let matches = false;
          if (srcId && matchingResIds.has(srcId)) matches = true;
          if (dstId && matchingResIds.has(dstId)) matches = true;
          if (!matches) {{
            for (const rId of matchingResIds) {{
              if (edgeTitle.includes(rId.toLowerCase()) || edgeTitle.includes(resources[rId]?.name.toLowerCase()||"")) {{
                matches = true;
                break;
              }}
            }}
          }}

          if (matches) {{
            edgeEl.classList.add("edge-highlight");
            edgeEl.classList.remove("edge-dimmed");
          }} else {{
            edgeEl.classList.add("edge-dimmed");
            edgeEl.classList.remove("edge-highlight");
          }}
        }}
      }});
    }});
  }});

  // Node Clicking & Path Tracing
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
    document.querySelectorAll(".edge").forEach(e => {{
      e.classList.remove("edge-highlight", "edge-dimmed");
      void e.offsetWidth; // restart CSS flow animation
    }});
    document.querySelectorAll(".node").forEach(n => n.classList.remove("node-active", "node-highlight", "node-dimmed"));

    targetNodeEl.classList.add("node-active", "node-highlight");
    const targetId = data.id;
    const targetTitle = (targetNodeEl.querySelector("title")?.textContent || "").toLowerCase();
    const targetName = (data.name || "").toLowerCase();
    const connectedNodeIds = new Set([targetId, ...(data.inbound||[]), ...(data.outbound||[])]);

    // Highlight incident nodes
    document.querySelectorAll(".node").forEach(n => {{
      const r = findResourceForNode(n);
      if (r && connectedNodeIds.has(r.id)) {{
        n.classList.remove("node-dimmed");
        if (r.id !== targetId) n.classList.add("node-highlight");
      }} else {{
        n.classList.add("node-dimmed");
      }}
    }});

    // Highlight incident edges
    document.querySelectorAll(".edge").forEach(edgeEl => {{
      const s = edgeEl.getAttribute("data-source");
      const d = edgeEl.getAttribute("data-target");
      const edgeTitle = (edgeEl.querySelector("title")?.textContent || "").toLowerCase();

      const hit = (s === targetId) || (d === targetId) ||
                  edgeTitle.includes(targetTitle) ||
                  edgeTitle.includes(targetName) ||
                  (data.inbound && data.inbound.some(inId => edgeTitle.includes(inId.toLowerCase()))) ||
                  (data.outbound && data.outbound.some(outId => edgeTitle.includes(outId.toLowerCase())));

      if (hit) {{
        edgeEl.classList.add("edge-highlight");
        edgeEl.classList.remove("edge-dimmed");
      }} else {{
        edgeEl.classList.add("edge-dimmed");
        edgeEl.classList.remove("edge-highlight");
      }}
    }});
  }}

  // Canvas Click: Clear highlights & close sidebar
  canvas.addEventListener("click", (e) => {{
    if (!e.target.closest(".node") && !e.target.closest("#sidebar")) {{
      document.querySelectorAll(".node").forEach(n => n.classList.remove("node-active", "node-highlight", "node-dimmed"));
      document.querySelectorAll(".edge").forEach(e => e.classList.remove("edge-highlight", "edge-dimmed"));
      sidebar.classList.remove("active");
    }}
  }});

  // Focus on specific node in viewport
  function focusOnNode(resId) {{
    const nodeEl = document.querySelector(`.node[data-resource-id="${{resId}}"]`) ||
                   Array.from(document.querySelectorAll(".node")).find(el => findResourceForNode(el)?.id === resId);
    if (nodeEl && resources[resId]) {{
      highlightImpactPaths(nodeEl, resources[resId]);
      showDetails(resources[resId]);

      // Center viewport on node
      const bbox = nodeEl.getBBox();
      const canvasRect = canvas.getBoundingClientRect();
      scale = 1.1;
      pointX = canvasRect.width / 2 - (bbox.x + bbox.width / 2) * scale;
      pointY = canvasRect.height / 2 - (bbox.y + bbox.height / 2) * scale;
      updateTransform();
    }}
  }}

  // Comprehensive Resource Inspector Drawer
  function showDetails(data) {{
    sidebar.classList.add("active");
    const prov = data.provider_info || {{ bg: "#64748B", text: "#FFFFFF", label: "Cloud" }};

    // 1. Key Specs Table
    let specsHtml = "";
    if (data.key_specs && Object.keys(data.key_specs).length > 0) {{
      let rows = "";
      for (const [k, v] of Object.entries(data.key_specs)) {{
        rows += `<tr><td class="kv-key">${{k}}</td><td class="kv-val">${{v}}</td></tr>`;
      }}
      specsHtml = `
        <div class="meta-card">
          <div class="section-label">Key Specifications</div>
          <table class="kv-table">${{rows}}</table>
        </div>`;
    }}

    // 2. Topology Connections
    let topologyHtml = "";
    const inConns = data.inbound || [];
    const outConns = data.outbound || [];
    if (inConns.length > 0 || outConns.length > 0) {{
      let inPills = inConns.map(id => `<span class="topology-badge" onclick="focusOnNode('${{id}}')">&#8592; ${{resources[id]?.name || id}}</span>`).join("") || '<span style="color:var(--text-secondary);font-size:11px;">(None / Entry point)</span>';
      let outPills = outConns.map(id => `<span class="topology-badge" onclick="focusOnNode('${{id}}')">&#8594; ${{resources[id]?.name || id}}</span>`).join("") || '<span style="color:var(--text-secondary);font-size:11px;">(None / Leaf resource)</span>';

      topologyHtml = `
        <div class="meta-card">
          <div class="section-label">Architecture Topology (Blast Radius: ${{data.blast_radius || 0}})</div>
          <div style="margin-bottom:8px;">
            <div style="font-size:11px;color:var(--text-secondary);margin-bottom:3px;font-weight:600;">Upstream Inbound (Depends On):</div>
            ${{inPills}}
          </div>
          <div>
            <div style="font-size:11px;color:var(--text-secondary);margin-bottom:3px;font-weight:600;">Downstream Outbound (Consumers):</div>
            ${{outPills}}
          </div>
        </div>`;
    }}

    // 3. Tags Chips
    let tagsHtml = "";
    if (data.tags && Object.keys(data.tags).length > 0) {{
      let chips = Object.entries(data.tags).map(([k, v]) => `<span class="tag-chip">${{k}}: ${{v}}</span>`).join("");
      tagsHtml = `
        <div class="meta-card">
          <div class="section-label">Resource Tags</div>
          ${{chips}}
        </div>`;
    }}

    // 4. Detailed Attributes Grid
    let attrsRows = "";
    if (data.attributes && Object.keys(data.attributes).length > 0) {{
      for (const [k, v] of Object.entries(data.attributes)) {{
        attrsRows += `<tr><td class="kv-key">${{k}}</td><td class="kv-val">${{v}}</td></tr>`;
      }}
    }}

    sidebarContent.innerHTML = `
      <div class="inspector-hero">
        <div class="inspector-hero-header">
          <span class="provider-pill" style="background:${{prov.bg}};color:${{prov.text}};">${{prov.label}}</span>
          <span class="category-pill">${{data.category}}</span>
        </div>
        <div class="res-title">${{data.service_name || data.name}}</div>
        <div class="res-subtitle">${{data.id}}</div>
        <div class="drawer-actions">
          <button class="drawer-btn" onclick="focusOnNode('${{data.id}}')">&#127919; Focus Node</button>
          <button class="drawer-btn" onclick="navigator.clipboard.writeText('${{data.id}}');showToast('Resource ID copied!');">&#128203; Copy ID</button>
          <button class="drawer-btn" onclick="navigator.clipboard.writeText(JSON.stringify(resources['${{data.id}}'], null, 2));showToast('JSON copied!');">&#128190; Copy JSON</button>
        </div>
      </div>

      ${{specsHtml}}
      ${{topologyHtml}}
      ${{tagsHtml}}

      <div class="meta-card">
        <div class="section-label">General Properties</div>
        <table class="kv-table">
          <tr><td class="kv-key">Resource Type</td><td class="kv-val">${{data.type}}</td></tr>
          <tr><td class="kv-key">Logical Name</td><td class="kv-val">${{data.name}}</td></tr>
          <tr><td class="kv-key">Module Path</td><td class="kv-val">${{data.module || "root"}}</td></tr>
          <tr><td class="kv-key">Cloud Provider</td><td class="kv-val">${{prov.label}}</td></tr>
          ${{attrsRows}}
        </table>
      </div>
    `;
  }}

  document.getElementById("close-sidebar").addEventListener("click", () => {{
    sidebar.classList.remove("active");
  }});

  // Spotlight Search
  document.getElementById("search-input").addEventListener("input", (e) => {{
    const query = e.target.value.toLowerCase().trim();
    if (!query) {{
      document.querySelectorAll(".node").forEach(el => el.classList.remove("node-dimmed", "node-active"));
      return;
    }}

    document.querySelectorAll(".node").forEach((el) => {{
      const text = el.textContent.toLowerCase();
      const res = findResourceForNode(el);
      const hit = text.includes(query) || (res && (res.id.toLowerCase().includes(query) || res.category.toLowerCase().includes(query) || res.type.toLowerCase().includes(query)));
      if (hit) {{
        el.classList.remove("node-dimmed");
        el.classList.add("node-active");
      }} else {{
        el.classList.add("node-dimmed");
        el.classList.remove("node-active");
      }}
    }});
  }});

  // Export Studio (JSON & PNG)
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
