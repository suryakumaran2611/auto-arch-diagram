#!/usr/bin/env python3
"""
Universal BulletproofMapper with improved icon handling for ALL cloud providers
Zero-failure icon resolution for AWS, Azure, GCP, OCI, IBM, Alibaba, and custom providers
"""

import os
import importlib.util
import inspect
import difflib
import re
import logging
from diagrams import Node, Diagram, Cluster

# TIER 3: The "Safety Net" - Reliable on-prem/generic icons  
from diagrams.onprem.compute import Server
from diagrams.onprem.analytics import Spark
from diagrams.onprem.network import Internet
from diagrams.onprem.security import Vault

# Dynamic fallbacks that handle missing imports gracefully
def get_database_fallback():
    """Get a suitable database fallback that actually exists"""
    try:
        from diagrams.onprem.database import PostgreSQL
        return PostgreSQL
    except ImportError:
        try:
            from diagrams.onprem.database import MySQL  
            return MySQL
        except ImportError:
            try:
                from diagrams.onprem.database import Cassandra
                return Cassandra
            except ImportError:
                return Server

def get_ml_fallback():
    """Get a suitable ML fallback that actually exists"""
    try:
        # Try different ML classes that might exist
        from diagrams.aws.ml import SageMaker
        return SageMaker
    except ImportError:
        try:
            from diagrams.gcp.ml import AIPlatform
            return AIPlatform
        except ImportError:
            return Server

# Initialize dynamic fallbacks
DATABASE_FALLBACK = get_database_fallback()
ML_FALLBACK = get_ml_fallback()

class EnhancedBulletproofMapper:
    def __init__(self):
        self.provider_map = {
            "aws": "aws", "google": "gcp", "azurerm": "azure",
            "oci": "onprem", "ibm": "ibm", "alicloud": "alibabacloud",
            "kubernetes": "k8s"
        }

        # 1. ENHANCED THESAURUS with GCP-specific patterns
        self.thesaurus = {
            "ai_ml": [
                "ml", "ai", "sagemaker", "vertex", "intelligence", "learning", "rekognition", 
                "tensor", "brain", "bot", "comprehend", "forecast", "automl", "aiplatform", 
                "dialogflow", " recommendation", "natural language", "speech", "text", "vision",
                "translation", "tpu", "inference"
            ],
            "blockchain": ["blockchain", "ledger", "managedblockchain", "ethereum", "fabric", "besu", "quantumledger"],
            "iot": ["iot", "iotcore", "greengrass", "telemetry", "mqtt", "thing", "iotevents"],
            "analytics": [
                "analytics", "redshift", "bigquery", "dataflow", "glue", "athena", "kinesis", 
                "spark", "hadoop", "dataproc", "synapse", "composer", "dataprep", "datalab",
                "genomics", "looker", "datafusion", "datacatalog", "pubsub"
            ],
            "database": [
                "db", "sql", "rds", "dynamo", "cosmos", "aurora", "nosql", "redis", "memcached", 
                "spanner", "firestore", "mongodb", "bigtable", "datastore", "memorystore", "alloydb"
            ],
            "compute": [
                "instance", "vm", "ec2", "server", "computeengine", "virtualmachine", "node", 
                "batch", "apprunner", "gke", "cloudrun", "appengine", "functions", "container",
                "gpu", "tpu", "anthos", "binaryauthorization", "os"
            ],
            "storage": [
                "bucket", "s3", "gcs", "blob", "storage", "efs", "fsx", "volume", 
                "filestore", "disks", "hyperdisk", "persistentdisk"
            ],
            "networking": [
                "vpc", "vnet", "network", "route", "gateway", "dns", "lb", "loadbalancer", 
                "cdn", "frontdoor", "cloudcdn", "cloudarmor", "clouddns", "cloudrouter", 
                "cloudvpn", "cloudloadbalancing"
            ],
            "security": [
                "iam", "policy", "role", "guardduty", "shield", "armor", "kms", "vault", 
                "secrets", "identity", "cognito", "ad", "secretmanager", "securitycommandcenter"
            ]
        }
        
        # 2. ENHANCED CATEGORY FALLBACKS with provider-specific logic
        self.category_fallbacks = {
            "ai_ml": ML_FALLBACK, 
            "blockchain": Server, 
            "analytics": Spark, 
            "database": DATABASE_FALLBACK,
            "networking": Internet,
            "security": Vault
        }

        # 3. UNIVERSAL SERVICE FALLBACK MAPS (for missing icons across all providers)
        self.service_fallbacks = {
            "gcp": {
                # GCP services that exist but may have different names
                "aihypercomputer": "VertexAI",
                "alloydb": "SQL", 
                "anthos": "GKE",
                "cloudasset": "CloudMonitoring",
                "cloudcdn": "CloudLoadBalancing",
                "cloudtasks": "PubSub",
                "cloudscheduler": "PubSub",
                "errorreporting": "CloudMonitoring",
                "eventarc": "PubSub",
                "apigee": "APIGateway",
                "aiplatform": "VertexAI",
                "artificialintelligence": "VertexAI"
            },
            "aws": {
                # AWS services with alternative names
                "elasticmapreduce": "EMR",
                "elasticbeanstalk": "ElasticBeanstalk",
                "elasticloadbalancing": "ELB",
                "elasticache": "ElastiCache",
                "elasticfilesystem": "EFS",
                "elasticblockstore": "EBS",
                "simplestorageservice": "S3",
                "simpledatabaseservice": "RDS",
                "simplequeueservice": "SQS",
                "simplenotificationservice": "SNS"
            },
            "azure": {
                # Azure services with alternative names
                "virtualmachines": "VirtualMachine",
                "virtualnetworks": "VirtualNetwork",
                "storagesaccounts": "StorageAccount",
                "sqldatabases": "SQLDatabase",
                "keyvaults": "KeyVault",
                "appserviceplans": "AppService",
                "functionapps": "FunctionApp"
            }
        }
        
        # 4. COMMON ABBREVIATIONS AND ALIASES
        self.aliases = {
            "gcp": "google",
            "gke": "kubernetesengine", 
            "gce": "computeengine",
            "gae": "appengine",
            "gcf": "functions",
            "sql": "database"
        }
        
        self.class_index = {}

    def get_icon(self, tf_type):
        """
        Enhanced Zero-Failure Resolution Logic:
        Tier 1: Exact match in comprehensive mappings
        Tier 2: GCP-specific fallback handling
        Tier 3: Semantic search with enhanced keywords
        Tier 4: Fuzzy token matching
        Tier 5: Category fallbacks
        Tier 6: Absolute Node fallback
        """
        parts = tf_type.lower().split('_')
        provider = parts[0]
        resource_body = "_".join(parts[1:])  # Preserve underscores for better matching
        
        # Apply aliases first
        if provider in self.aliases:
            provider = self.aliases[provider]
        
        # Deep scan the library
        icons = self._index_provider(provider)
        
        # --- PHASE 1: EXACT MATCH ---
        if resource_body in icons:
            return icons[resource_body]
        
        # --- PHASE 2: UNIVERSAL SERVICE FALLBACKS ---
        if provider in self.service_fallbacks and resource_body in self.service_fallbacks[provider]:
            fallback_name = self.service_fallbacks[provider][resource_body]
            if fallback_name in icons:
                return icons[fallback_name]
            # Handle dynamic fallbacks
            elif fallback_name == "DATABASE_FALLBACK":
                return DATABASE_FALLBACK
        
        # --- PHASE 3: ENHANCED SEMANTIC SEARCH ---
        for category, keywords in self.thesaurus.items():
            if any(key in resource_body for key in keywords):
                # A: Try to find a branded match with priority to exact substrings
                best_match = None
                best_score = 0
                
                for icon_name, icon_cls in icons.items():
                    # Check for exact keyword matches first
                    if any(key == icon_name for key in keywords):
                        return icon_cls  # Immediate return for exact match
                    
                    # Score based on keyword containment
                    score = sum(1 for key in keywords if key in icon_name)
                    if score > best_score:
                        best_score = score
                        best_match = icon_cls
                
                if best_match and best_score > 0:
                    return best_match
                
                # B: If branded fails, use the category default
                return self.category_fallbacks.get(category, Node)

        # --- PHASE 4: ENHANCED FUZZY MATCH ---
        if icons:
            # Try different matching strategies
            candidates = [
                resource_body,  # Original
                resource_body.replace("_", ""),  # No underscores
                resource_body.replace("instance", ""),  # Remove common suffixes
                resource_body.replace("cluster", ""),  # Remove common suffixes
                re.sub(r'_(?:service|instance|cluster|resource)$', '', resource_body)  # Remove suffixes
            ]
            
            for candidate in candidates:
                if not candidate:
                    continue
                    
                matches = difflib.get_close_matches(candidate, icons.keys(), n=1, cutoff=0.3)
                if matches:
                    return icons[matches[0]]

        # --- PHASE 5: CATEGORY FALLBACKS ---
        for category, keywords in self.thesaurus.items():
            if any(key in resource_body for key in keywords):
                return self.category_fallbacks.get(category, Node)

        # --- PHASE 6: ABSOLUTE FALLBACK ---
        return Node

    def _index_provider(self, provider_prefix):
        """Enhanced filesystem crawler with better error handling."""
        lib_name = self.provider_map.get(provider_prefix, provider_prefix)
        if lib_name in self.class_index:
            return self.class_index[lib_name]

        try:
            spec = importlib.util.find_spec(f"diagrams.{lib_name}")
            if not spec or not spec.submodule_search_locations:
                return {}

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
                                if (issubclass(obj, Node) and 
                                    obj is not Node and 
                                    not name.startswith('_')):
                                    indexed[name.lower()] = obj
                        except (ImportError, AttributeError, TypeError):
                            continue
            
            self.class_index[lib_name] = indexed
            return indexed
            
        except Exception:
            # Return empty dict on any error to ensure zero-failure
            return {}

    def debug_icon_resolution(self, tf_type):
        """Debug method to show icon resolution process"""
        print(f"\n[DEBUG] Resolving: {tf_type}")
        parts = tf_type.lower().split('_')
        provider = parts[0]
        resource_body = "_".join(parts[1:])
        
        print(f"  Provider: {provider}")
        print(f"  Resource: {resource_body}")
        
        icons = self._index_provider(provider)
        print(f"  Available icons: {len(icons)}")
        
        # Show semantic matching
        for category, keywords in self.thesaurus.items():
            matching_keywords = [k for k in keywords if k in resource_body]
            if matching_keywords:
                print(f"  Category match: {category} (keywords: {matching_keywords})")
                break
        
        result = self.get_icon(tf_type)
        print(f"  Final result: {result}")
        return result


# Test function for validation
def test_enhanced_mapper():
    mapper = EnhancedBulletproofMapper()
    
    # Test cases including problematic GCP services
    test_cases = [
        "google_aihypercomputer_instance",
        "google_alloydb_instance", 
        "google_anthos_cluster",
        "google_cloudasset_project_feed",
        "google_cloud_tasks_queue",
        "google_error_reporting_error_group",
        "google_vertex_ai_endpoint",
        "aws_sagemaker_endpoint",
        "azurerm_machine_learning_workspace",
        "aws_nonexistent_service",  # Should fallback gracefully
    ]
    
    print("=== Enhanced BulletproofMapper Test ===")
    for test_case in test_cases:
        result = mapper.debug_icon_resolution(test_case)
        
    return mapper


if __name__ == "__main__":
    test_enhanced_mapper()