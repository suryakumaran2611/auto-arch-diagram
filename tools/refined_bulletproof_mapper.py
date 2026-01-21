#!/usr/bin/env python3
"""
Refined Universal BulletproofMapper 
Simplified, robust icon resolution for ALL cloud providers
"""

import os
import importlib.util
import inspect
import difflib
from diagrams import Node

# Generic on-prem defaults for Tier 3 fallbacks
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Internet

class RefinedBulletproofMapper:
    def __init__(self):
        self.provider_map = {
            "aws": "aws", "google": "gcp", "azurerm": "azure",
            "oci": "onprem", "ibm": "ibm", "alicloud": "alibabacloud",
            "kubernetes": "k8s"
        }

        # 1. ENHANCED Thesaurus with discovered classes across ALL providers
        self.thesaurus = {
            "compute": [
                # AWS
                "ec2", "lambda", "ecs", "eks", "batch", "elasticbeanstalk", "lightsail",
                # GCP
                "computeengine", "gce", "gke", "kubernetesengine", "functions", "gcf", 
                "cloudrun", "appengine", "gae", "container", "gpu", "tpu", "anthos",
                # Azure
                "virtualmachine", "functionapp", "appservice", "containerinstances", "kubernetesservice",
                # Common
                "instance", "vm", "server", "node", "batch"
            ],
            "database": [
                # AWS
                "rds", "dynamodb", "aurora", "neptune", "redshift", "elasticache", "documentdb", "timestream",
                # GCP
                "sql", "spanner", "firestore", "bigtable", "memorystore", "datastore", "alloydb",
                # Azure
                "sqldatabase", "cosmosdb", "databaseforpostgresql", "databaseformysql", "cache",
                # Common
                "db", "nosql", "redis", "memcached", "mongodb"
            ],
            "ml": [
                # AWS
                "sagemaker", "comprehend", "rekognition", "textract", "translate", "transcribe", 
                "polly", "forecast", "personalize", "lex", "bedrock",
                # GCP
                "vertexai", "aiplatform", "automl", "dialogflow", "speechtotext", "visionapi", 
                "aihypercomputer", "translationapi", "naturalanguageapi",
                # Azure
                "machinelearning", "cognitiveservices", "botservices",
                # Common
                "ml", "ai", "intelligence", "learning", "tensor", "brain", "bot", "inference"
            ],
            "analytics": [
                # AWS
                "glue", "athena", "emr", "kinesis", "kinesisanalytics", "quicksight", "datapipeline",
                # GCP
                "bigquery", "dataflow", "dataproc", "composer", "dataprep", "datalab", 
                "looker", "datafusion", "datacatalog", "pubsub",
                # Azure
                "datafactory", "databricks", "hdinsight", "streamanalytics", "synapseanalytics", "analysiservices",
                # Common
                "analytics", "spark", "hadoop", "synapse"
            ],
            "storage": [
                # AWS
                "s3", "ebs", "efs", "fsx", "storagegateway", "backup",
                # GCP
                "gcs", "storage", "bucket", "filestore", "persistentdisk", "hyperdisk",
                # Azure
                "storageaccount", "blob", "file", "disk",
                # Common
                "volume", "filestore", "disks"
            ],
            "network": [
                # AWS
                "vpc", "elb", "alb", "nlb", "cloudfront", "route53", "apigateway", "cloudmap",
                # GCP
                "loadbalancing", "network", "firewall", "armor", "dns", "router", "cloudcdn", 
                "clouddns", "cloudrouter", "cloudvpn", "cloudloadbalancing", "vpc",
                # Azure
                "virtualnetwork", "loadbalancer", "applicationgateway", "cdn", "frontdoor", 
                "trafficmanager", "dns",
                # Common
                "route", "gateway", "lb", "loadbalancer", "cdn", "url", "proxy", "certificate"
            ],
            "security": [
                # AWS
                "iam", "kms", "secretsmanager", "cloudtrail", "guardduty", "waf", "shield", 
                "inspector", "macie", "config", "organizations",
                # GCP
                "iam", "kms", "secretmanager", "securitycommandcenter",
                # Azure
                "keyvault", "activedirectory", "securitycenter", "informationprotection", "sentinel",
                # Common
                "policy", "role", "secrets", "identity", "vault"
            ],
            "integration": [
                # AWS
                "sqs", "sns", "eventbridge", "stepfunctions", "mq", "appsync", "connect",
                # GCP
                "pubsub", "cloudtasks", "cloudscheduler", "eventarc", "apigee",
                # Azure
                "servicebus", "eventgrid", "eventhubs", "apimanagement", "logicapps",
                # Common
                "queue", "message", "event", "workflow"
            ]
        }

        # 2. Category Fallbacks - use your approach
        self.category_defaults = {
            "compute": Server, 
            "database": PostgreSQL, 
            "ml": Server, 
            "analytics": Server,
            "storage": Server,
            "network": Internet,
            "security": Internet,
            "integration": Server
        }

        self.class_index = {}

        # 3. UNIVERSAL SERVICE FALLBACK MAPS (for missing icons across all providers)
        self.service_fallbacks = {
            "gcp": {
                # GCP services that exist but may have different names
                "aihypercomputer": "VertexAI",
                "alloydb": "SQL", 
                "anthos": "GKE",
                "cloudasset": "CloudAssetInventory",
                "cloudcdn": "CloudLoadBalancing",
                "cloudtasks": "PubSub",
                "cloudscheduler": "PubSub",
                "errorreporting": "CloudMonitoring",
                "eventarc": "PubSub",
                "apigee": "APIGateway",
                "aiplatform": "VertexAI",
                "artificialintelligence": "VertexAI",
                # GCP Compute services - improved mappings
                "computesecuritypolicy": "IAP",
                "computebackendbucket": "CloudRun",  # Backend bucket is like Cloud Run
                "computeurlmap": "AppEngine",      # URL maps are like App Engine routing
                "computetargethttpsproxy": "AppEngine", # HTTPS proxy is for App Engine
                "computeglobalforwardingrule": "CloudLoadBalancing", # Forwarding rules are for load balancing
                "computemanagedsslcertificate": "CertificateManager",  # SSL certificates
                # Additional mappings for better coverage
                "forwardingrule": "CloudLoadBalancing",
                "targethttpsproxy": "AppEngine",
                "managedsslcertificate": "CertificateManager"
            }
        }

    def _get_provider_path(self, lib_name):
        """Your clean approach to get provider path"""
        try:
            spec = importlib.util.find_spec(f"diagrams.{lib_name}")
            return spec.submodule_search_locations[0] if spec else None
        except: 
            return None

    def index_provider(self, provider_prefix):
        """Your simplified indexing approach"""
        lib_name = self.provider_map.get(provider_prefix, provider_prefix)
        if lib_name in self.class_index: 
            return self.class_index[lib_name]

        path = self._get_provider_path(lib_name)
        if not path: 
            return {}

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
                    except: 
                        continue
        self.class_index[lib_name] = indexed
        return indexed

    def get_icon(self, tf_type):
        """
        Your refined logic:
        1. Clean TF Name (google_compute_instance -> computeengine)
        2. Direct Library Lookup  
        3. Thesaurus Semantic Match
        4. Category Default Fallback
        """
        parts = tf_type.lower().split('_')
        provider = parts[0]
        
        # Clean the body: remove common prefixes/suffixes for better matching
        resource_body = "_".join(parts[1:])  # Keep underscores for better matching
        
        # Apply common cleaning rules
        resource_body = resource_body.replace("_instance", "").replace("_cluster", "").replace("_service", "")
        resource_body = resource_body.replace("_database", "").replace("_table", "").replace("_bucket", "")
        
        icons = self.index_provider(provider)
        if not icons: 
            return Node

        # --- STEP 1: Direct Match ---
        if resource_body in icons:
            return icons[resource_body]

        # --- STEP 1.5: Service Fallbacks ---
        if provider in self.service_fallbacks and resource_body in self.service_fallbacks[provider]:
            fallback_name = self.service_fallbacks[provider][resource_body]
            if fallback_name in icons:
                return icons[fallback_name]

        # --- STEP 2: Direct/Thesaurus Match ---
        for category, synonyms in self.thesaurus.items():
            if any(syn in resource_body for syn in synonyms):
                # Search for any synonym in the actual icon pool
                for syn in synonyms:
                    if syn in icons: 
                        return icons[syn]
                # Return category-specific generic icon if no branded match
                return self.category_defaults.get(category, Node)

        # --- STEP 3: Fuzzy Logic ---
        matches = difflib.get_close_matches(resource_body, icons.keys(), n=1, cutoff=0.3)
        if matches: 
            match = icons[matches[0]]
            # Avoid returning internal classes that start with _
            if not match.__name__.startswith('_'):
                return match

        return Node

    def debug_resolution(self, tf_type):
        """Debug the resolution process"""
        parts = tf_type.lower().split('_')
        provider = parts[0]
        resource_body = "_".join(parts[1:])
        
        print(f"\n[DEBUG] Resolving: {tf_type}")
        print(f"  Provider: {provider}")
        print(f"  Resource body: {resource_body}")
        
        icons = self.index_provider(provider)
        print(f"  Available icons: {len(icons)}")
        
        # Show category matching
        for category, synonyms in self.thesaurus.items():
            matches = [s for s in synonyms if s in resource_body]
            if matches:
                print(f"  Category: {category} (matches: {matches})")
                break
        
        result = self.get_icon(tf_type)
        print(f"  Final result: {result}")
        return result


# Test function
def test_refined_mapper():
    mapper = RefinedBulletproofMapper()
    
    # Test problematic services across providers
    test_cases = [
        # GCP problematic cases
        "google_alloydb_instance",
        "google_aihypercomputer_instance", 
        "google_anthos_cluster",
        "google_cloudasset_project_feed",
        "google_vertex_ai_endpoint",
        
        # AWS cases
        "aws_sagemaker_endpoint",
        "aws_elasticmapreduce_cluster",
        "aws_elasticbeanstalk_app",
        
        # Azure cases
        "azurerm_machine_learning_workspace",
        "azurerm_virtual_network",
        
        # Edge cases
        "aws_nonexistent_service",
        "google_new_ai_service",
        "custom_provider_service"
    ]
    
    print("=== Refined BulletproofMapper Test ===")
    for test_case in test_cases:
        mapper.debug_resolution(test_case)
    
    return mapper


if __name__ == "__main__":
    test_refined_mapper()