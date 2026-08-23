"""Configuration loader and schema validator for cloud provider render configs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import yaml

_CONFIG_DIR = Path(__file__).resolve().parent
_CONFIG_CACHE: dict[str, dict[str, Any]] = {}


def load_provider_config(provider: str) -> dict[str, Any]:
    """Load and validate provider configuration YAML."""
    prov_key = provider.strip().lower()
    if prov_key in {"azurerm", "azure"}:
        prov_key = "azure"
    elif prov_key in {"google", "gcp"}:
        prov_key = "gcp"
    elif prov_key not in {"aws", "azure", "gcp", "oci", "ibm"}:
        prov_key = "default"

    if prov_key in _CONFIG_CACHE:
        return _CONFIG_CACHE[prov_key]

    cfg_file = _CONFIG_DIR / f"{prov_key}.yaml"
    if not cfg_file.exists():
        cfg_file = _CONFIG_DIR / "default.yaml"

    data: dict[str, Any] = {}
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}

    # Defaults
    data.setdefault("provider_name", prov_key.upper())
    data.setdefault("draw_order", ["outer_nodes", "edge_nodes", "group_nodes", "consolidated_nodes", "default"])
    data.setdefault("outer_nodes", [])
    data.setdefault("edge_nodes", [])
    data.setdefault("group_nodes", [])
    data.setdefault("auto_annotations", [])
    data.setdefault("node_variants", {})
    data.setdefault("reverse_arrow_list", [])
    data.setdefault("bidirectional_nodes", [])
    data.setdefault("always_draw_line", [])
    data.setdefault("never_draw_line", [])
    data.setdefault("shared_services", [])
    data.setdefault("hide_nodes", [])
    data.setdefault("group_links", [])

    _CONFIG_CACHE[prov_key] = data
    return data
