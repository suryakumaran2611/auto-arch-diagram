"""
Bulletproof Cloud Icon Mapper
Zero-failure icon mapping using advanced multi-tier resolution with comprehensive thesaurus.
"""

import os
import importlib.util
import inspect
import difflib
from diagrams import Node, Diagram, Cluster

# TIER 3: The "Safety Net" - Reliable on-prem/generic icons
from diagrams.onprem.compute import Server
from diagrams.onprem.analytics import Spark
from diagrams.onprem.database import _Database as Database
from diagrams.onprem.network import Internet
from diagrams.onprem.security import Vault

class BulletproofMapper:
    def __init__(self):
        self.provider_map = {
            "aws": "aws", "google": "gcp", "azurerm": "azure",
            "oci": "onprem", "ibm": "ibm", "alicloud": "alibabacloud",
            "kubernetes": "k8s"
        }

        # 1. THE ULTIMATE THESAURUS
        # Maps every possible cloud keyword to a Diagram "Category"
        self.thesaurus = {
            "ai_ml": ["ml", "ai", "sagemaker", "vertex", "intelligence", "learning", "rekognition", "tensor", "brain", "bot", "comprehend", "forecast"],
            "blockchain": ["blockchain", "ledger", "managedblockchain", "ethereum", "fabric", "besu", "quantumledger"],
            "iot": ["iot", "iotcore", "greengrass", "telemetry", "mqtt", "thing", "iotevents"],
            "analytics": ["analytics", "redshift", "bigquery", "dataflow", "glue", "athena", "kinesis", "spark", "hadoop", "dataproc", "synapse"],
            "database": ["db", "sql", "rds", "dynamo", "cosmos", "aurora", "nosql", "redis", "memcached", "spanner", "firestore", "mongodb"],
            "compute": ["instance", "vm", "ec2", "server", "computeengine", "virtualmachine", "node", "batch", "apprunner"],
            "storage": ["bucket", "s3", "gcs", "blob", "storage", "efs", "fsx", "volume", "filestore", "disks"],
            "networking": ["vpc", "vnet", "network", "route", "gateway", "dns", "lb", "loadbalancer", "cdn", "frontdoor"],
            "security": ["iam", "policy", "role", "guardduty", "shield", "armor", "kms", "vault", "secrets", "identity", "cognito", "ad"]
        }
        
        # 2. CATEGORY FALLBACKS
        # If cloud library is missing a specific AI icon, use these
        self.category_fallbacks = {
            "ai_ml": Server, 
            "blockchain": Server, 
            "analytics": Spark, 
            "database": Database,
            "networking": Internet,
            "security": Vault,
            "compute": Server,
            "storage": Server,
            "iot": Server
        }
        
        self.class_index = {}

    def get_icon(self, tf_type):
        """
        The Zero-Failure Resolution Logic:
        Tier 1: Search provider for branded match (e.g. SageMaker)
        Tier 2: Search provider for category match (e.g. any ML icon)
        Tier 3: Use generic category fallback (e.g. a generic Server/Brain)
        Tier 4: Absolute fallback to Node
        """
        parts = tf_type.lower().split('_')
        provider = parts[0]
        resource_body = "".join(parts[1:])
        
        # Deep scan library on WSL disk
        icons = self._index_provider(provider)
        
        # --- PHASE 1: Semantic Search ---
        for category, keywords in self.thesaurus.items():
            if any(key in resource_body for key in keywords):
                # A: Try to find a branded match
                for icon_name, icon_cls in icons.items():
                    if any(key in icon_name for key in keywords):
                        return icon_cls
                
                # B: If branded fails, use category default
                return self.category_fallbacks.get(category, Node)

        # --- PHASE 2: Tokenized Fuzzy Match ---
        if icons:
            matches = difflib.get_close_matches(resource_body, icons.keys(), n=1, cutoff=0.25)
            if matches: return icons[matches[0]]

        return Node

    def _index_provider(self, provider_prefix):
        """WSL-optimized filesystem crawler."""
        lib_name = self.provider_map.get(provider_prefix, provider_prefix)
        if lib_name in self.class_index: return self.class_index[lib_name]

        spec = importlib.util.find_spec(f"diagrams.{lib_name}")
        if not spec or not spec.submodule_search_locations: return {}

        path = spec.submodule_search_locations[0]
        indexed = {}
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    rel_path = os.path.relpath(os.path.join(root, file[:-3]), path)
                    mod_path = f"diagrams.{lib_name}." + rel_path.replace(os.sep, ".")
                    try:
                        module = importlib.import_module(mod_path)
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, Node) and obj is not Node:
                                indexed[name.lower()] = obj
                    except: continue
        self.class_index[lib_name] = indexed
        return indexed


# Backward compatibility aliases
UltimateCloudMapper = BulletproofMapper
UniversalCloudMapper = BulletproofMapper