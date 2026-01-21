"""
Ultimate Cloud Icon Mapper
Provides comprehensive icon mapping that never fails by using multiple fallback strategies.
"""

import os
import importlib
import importlib.util
import inspect
import difflib
from diagrams import Node


class UltimateCloudMapper:
    """Advanced icon mapper that uses multiple strategies to ensure icon mapping never fails."""
    
    def __init__(self):
        # Map TF to Diagrams Folder Names
        self.provider_map = {
            "aws": "aws", "google": "gcp", "azurerm": "azure", 
            "oci": "onprem", "alicloud": "alibabacloud", "kubernetes": "k8s"
        }
        self.class_index = {}
        self.synonyms = {
            "instance": "ec2", "storage_bucket": "s3", "db": "rds",
            "virtual_machine": "vm", "security_group": "iam", "function": "lambda",
            "load_balancer": "elb", "api_gateway": "apigateway", "firewall": "securitygroup"
        }
        # Common service mappings for quick lookup
        self.common_mappings = {
            "aws_s3_bucket": "s3", "aws_ec2_instance": "ec2", "aws_lambda_function": "lambda",
            "aws_rds_instance": "rds", "aws_vpc": "vpc", "aws_subnet": "subnet",
            "aws_security_group": "securitygroup", "aws_iam_role": "iam",
            "google_storage_bucket": "storage", "google_compute_instance": "compute",
            "azurerm_storage_account": "storage", "azurerm_virtual_machine": "compute"
        }

    def _get_provider_root(self, lib_name):
        """Locates the actual file system path of the diagrams provider."""
        try:
            spec = importlib.util.find_spec(f"diagrams.{lib_name}")
            if spec and spec.submodule_search_locations:
                return spec.submodule_search_locations[0]
        except Exception:
            return None
        return None

    def index_all_icons(self, provider_prefix):
        """Deep-scans the filesystem for icon classes."""
        lib_name = self.provider_map.get(provider_prefix, provider_prefix)
        if lib_name in self.class_index:
            return self.class_index[lib_name]

        path = self._get_provider_root(lib_name)
        if not path:
            return {}

        indexed_classes = {}
        # Walk the directory tree of the library
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    # Convert file path to module path
                    rel_path = os.path.relpath(os.path.join(root, file[:-3]), path)
                    mod_path = f"diagrams.{lib_name}." + rel_path.replace(os.sep, ".")
                    
                    try:
                        module = importlib.import_module(mod_path)
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, Node) and obj is not Node:
                                indexed_classes[name.lower()] = obj
                    except Exception:
                        continue
        
        self.class_index[lib_name] = indexed_classes
        return indexed_classes

    def get_icon(self, tf_type, debug=False):
        """
        Get the best matching icon for a Terraform resource type.
        Uses multiple fallback strategies to ensure it never returns None.
        
        Args:
            tf_type: Terraform resource type (e.g., "aws_s3_bucket")
            debug: Whether to print debug information
            
        Returns:
            Node class (never None)
        """
        parts = tf_type.split('_')
        prefix = parts[0]
        
        if debug:
            print(f"[UltimateMapper] Processing: {tf_type}")
        
        # Strategy 1: Common mappings (fastest)
        if tf_type.lower() in self.common_mappings:
            mapped_name = self.common_mappings[tf_type.lower()]
            icons = self.index_all_icons(prefix)
            if mapped_name.lower() in icons:
                if debug:
                    print(f"[UltimateMapper] Found via common mapping: {mapped_name}")
                return icons[mapped_name.lower()]
        
        # Strategy 2: Direct class name matching
        icons = self.index_all_icons(prefix)
        if icons:
            search_term = "".join(parts[1:]).lower()
            
            # Check for exact match first
            if search_term in icons:
                if debug:
                    print(f"[UltimateMapper] Exact match: {search_term}")
                return icons[search_term]
            
            # Check for common variations
            variations = [
                search_term,
                search_term.rstrip('s'),  # Remove trailing 's'
                search_term + 's',       # Add trailing 's'
                parts[1].lower(),        # Just the first service word
                "_".join(parts[1:]).lower()  # Original format without prefix
            ]
            
            for variation in variations:
                if variation in icons:
                    if debug:
                        print(f"[UltimateMapper] Found via variation: {variation}")
                    return icons[variation]
        
        # Strategy 3: Synonym matching
        for key, val in self.synonyms.items():
            if key in tf_type.lower():
                icons = self.index_all_icons(prefix)
                if icons and val.lower() in icons:
                    if debug:
                        print(f"[UltimateMapper] Found via synonym: {key} -> {val}")
                    return icons[val.lower()]
        
        # Strategy 4: Fuzzy matching with different cutoffs
        if icons:
            search_term = "".join(parts[1:]).lower()
            
            # Try with different cutoffs for more aggressive matching
            for cutoff in [0.8, 0.6, 0.4, 0.2]:
                matches = difflib.get_close_matches(search_term, list(icons.keys()), n=1, cutoff=cutoff)
                if matches:
                    if debug:
                        print(f"[UltimateMapper] Fuzzy match (cutoff={cutoff}): {matches[0]}")
                    return icons[matches[0]]
        
        # Strategy 5: Partial containment matching
        if icons:
            search_term = "".join(parts[1:]).lower()
            for name, cls in icons.items():
                if name in search_term or search_term in name or \
                   any(part in name for part in parts[1:]) or \
                   any(name in part for part in parts[1:]):
                    if debug:
                        print(f"[UltimateMapper] Partial match: {name}")
                    return cls
        
        # Strategy 6: Try all categories in provider module
        try:
            provider_lib = self.provider_map.get(prefix, prefix)
            provider_mod = __import__(f"diagrams.{provider_lib}", fromlist=["*"])
            
            for attr in dir(provider_mod):
                if attr.startswith("__"):
                    continue
                try:
                    cat_mod = getattr(provider_mod, attr)
                    for class_name in dir(cat_mod):
                        if class_name.startswith("__"):
                            continue
                        icon_cls = getattr(cat_mod, class_name, None)
                        if icon_cls and issubclass(icon_cls, Node):
                            return icon_cls
                except Exception:
                    continue
        except Exception:
            pass
        
        # Strategy 7: Last resort - generic icons from any provider
        try:
            # Try AWS generic icons as they're most comprehensive
            aws_mod = __import__("diagrams.aws", fromlist=["*"])
            for category_name in ["compute", "storage", "network", "security", "database"]:
                if hasattr(aws_mod, category_name):
                    cat_mod = getattr(aws_mod, category_name)
                    for class_name in dir(cat_mod):
                        if class_name.startswith("__"):
                            continue
                        icon_cls = getattr(cat_mod, class_name, None)
                        if icon_cls and issubclass(icon_cls, Node):
                            if debug:
                                print(f"[UltimateMapper] Generic fallback: aws.{category_name}.{class_name}")
                            return icon_cls
        except Exception:
            pass
        
        # Strategy 8: Final fallback - any available Node class
        try:
            from diagrams.generic.compute import Compute
            return Compute
        except Exception:
            pass
        
        try:
            from diagrams.generic.network import Network
            return Network
        except Exception:
            pass
        
        try:
            from diagrams.generic.storage import Storage
            return Storage
        except Exception:
            pass
        
        # Absolute final fallback
        if debug:
            print(f"[UltimateMapper] Using absolute fallback: Node")
        return Node