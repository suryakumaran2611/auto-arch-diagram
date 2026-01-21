#!/usr/bin/env python3
"""
Robust Dynamic Icon Mapper
Intelligently discovers and maps all available icons from diagrams library
using dynamic discovery and fuzzy matching.
"""

import importlib
import pkgutil
import difflib
import sys
from pathlib import Path
from typing import Dict, Optional, List


try:
    from diagrams import Node
except ImportError:
    print("[ERROR] diagrams library not found. Please install: pip install diagrams")
    sys.exit(1)


class RobustDynamicMapper:
    """Robust dynamic icon mapping system using intelligent class discovery"""
    
    def __init__(self):
        self._cache = {}
        # Maps TF prefixes to actual diagrams library module names
        self.provider_alias = {
            "aws": "aws",
            "google": "gcp",
            "azurerm": "azure", 
            "alicloud": "alibabacloud",
            "digitalocean": "digitalocean",
            "oci": "onprem",  # OCI is often under onprem
            "ibm": "ibm",
            "kubernetes": "k8s",
            "oracle": "oracle"
        }
        
        # Cache for discovered classes by provider
        self.available_classes = {}
    
    def get_node_classes(self, provider_path: str) -> Dict[str, type]:
        """Recursively finds all Node classes in a given diagrams provider module."""
        if provider_path in self.available_classes:
            return self.available_classes[provider_path]
            
        classes = {}
        try:
            root_mod = importlib.import_module(f"diagrams.{provider_path}")
            print(f"[DEBUG] Loading provider: diagrams.{provider_path}")
            
            for loader, modname, ispkg in pkgutil.walk_packages(root_mod.__path__, root_mod.__name__ + "."):
                if not ispkg:
                    continue
                    
                try:
                    sub_mod = importlib.import_module(modname)
                    
                    for attr_name in dir(sub_mod):
                        obj = getattr(sub_mod, attr_name)
                        # Check if it's a class and a subclass of Node (but not Node itself)
                        if isinstance(obj, type) and obj is not Node:
                            try:
                                if issubclass(obj, Node) and not attr_name.startswith('_'):
                                    # Store both class and its simplified name for matching
                                    classes[attr_name.lower()] = obj
                            except TypeError:
                                # obj is not a class or can't be checked with issubclass
                                continue
                                
                except ImportError as e:
                    print(f"[DEBUG] Could not import module {modname}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Could not load provider diagrams.{provider_path}: {e}")
            return {}
        
        self.available_classes[provider_path] = classes
        print(f"[SUCCESS] Found {len(classes)} icon classes in diagrams.{provider_path}")
        return classes
    
    def find_match(self, tf_resource_type: str) -> Optional[type]:
        """Find best matching diagrams class for a Terraform resource type"""
        if tf_resource_type in self._cache:
            return self._cache[tf_resource_type]

        parts = tf_resource_type.split('_')
        tf_prefix = parts[0].lower()
        
        # Clean resource name (e.g., 'aws_s3_bucket' -> 's3bucket')
        search_term = "".join(parts[1:]).lower()
        
        # Also try variations
        search_variations = [
            search_term,
            "_".join(parts[1:]).lower(),  # s3_bucket
            search_term.replace("instance", ""),  # Remove 'instance' suffix
            search_term.replace("service", ""),   # Remove 'service' suffix
        ]

        lib_provider = self.provider_alias.get(tf_prefix, tf_prefix)
        available_classes = self.get_node_classes(lib_provider)

        if not available_classes:
            return None

        # Try each search variation
        for variation in search_variations:
            # Logic: Fuzzy Match against all discovered class names
            matches = difflib.get_close_matches(variation, available_classes.keys(), n=1, cutoff=0.3)
            
            if matches:
                best_match_name = matches[0]
                matched_cls = available_classes[best_match_name]
                self._cache[tf_resource_type] = matched_cls
                print(f"[SUCCESS] {tf_resource_type} -> {best_match_name} (search term: {variation})")
                return matched_cls
        
        # Try progressive partial matching
        for i in range(len(parts[1:]), 0, -1):
            partial_term = "_".join(parts[1:i+1]).lower()
            if partial_term in available_classes:
                matched_cls = available_classes[partial_term]
                self._cache[tf_resource_type] = matched_cls
                print(f"[SUCCESS] {tf_resource_type} -> {partial_term} (partial match)")
                return matched_cls
        
        # Try individual word matching
        for part in parts[1:]:
            if part in available_classes:
                matched_cls = available_classes[part]
                self._cache[tf_resource_type] = matched_cls
                print(f"[SUCCESS] {tf_resource_type} -> {part} (word match)")
                return matched_cls

        print(f"[FAIL] {tf_resource_type} -> NOT FOUND")
        return None
    
    def test_common_resources(self) -> float:
        """Test mapper with common Terraform resources"""
        test_resources = [
            'aws_elasticsearch_domain',
            'aws_security_group', 
            'aws_api_gateway_rest_api',
            'aws_cloudwatch_event_rule',
            'aws_dynamodb_table',
            'aws_lambda_function',
            'aws_s3_bucket',
            'aws_vpc',
            'aws_ec2_instance',
            'google_compute_instance',
            'google_storage_bucket',
            'azurerm_storage_account',
            'azurerm_virtual_machine',
            'oci_core_instance'
        ]
        
        print("\n[TEST] Testing robust dynamic mapping:")
        matches = 0
        total = len(test_resources)
        
        for resource in test_resources:
            match = self.find_match(resource)
            
            if match:
                print(f"✓ {resource} -> {match.__module__}.{match.__name__}")
                matches += 1
            else:
                print(f"✗ {resource} -> NOT FOUND")
        
        success_rate = matches / total
        print(f"\n[RESULTS] {matches}/{total} resources matched ({success_rate*100:.1f}%)")
        return success_rate
    
    def test_aws_specific(self):
        """Test AWS-specific resources that were failing"""
        aws_resources = [
            'aws_elasticsearch_domain',
            'aws_security_group',
            'aws_api_gateway_rest_api', 
            'aws_api_gateway_method',
            'aws_api_gateway_resource',
            'aws_cloudwatch_event_rule',
            'aws_cloudwatch_event_target',
            'aws_cloudwatch_log_group',
            'aws_cloudwatch_metric_alarm',
            'aws_dynamodb_table'
        ]
        
        print("\n[TEST] AWS-specific failing resources:")
        matches = 0
        for resource in aws_resources:
            match = self.find_match(resource)
            if match:
                print(f"✓ {resource}")
                matches += 1
            else:
                print(f"✗ {resource}")
        
        print(f"AWS Results: {matches}/{len(aws_resources)} matched")
        return matches


def main():
    """Main function to test robust dynamic mapper"""
    mapper = RobustDynamicMapper()
    
    # Test AWS specifically (most common)
    aws_success = mapper.test_aws_specific()
    
    # Test broader set
    overall_success = mapper.test_common_resources()
    
    print(f"\n[DONE] Robust Dynamic Icon Mapper Test Completed!")
    print(f"[INFO] AWS Success Rate: {aws_success}/{len(['aws_elasticsearch_domain','aws_security_group','aws_api_gateway_rest_api','aws_api_gateway_method','aws_api_gateway_resource','aws_cloudwatch_event_rule','aws_cloudwatch_event_target','aws_cloudwatch_log_group','aws_cloudwatch_metric_alarm','aws_dynamodb_table'])} matched")
    print(f"[INFO] Overall Success Rate: {overall_success*100:.1f}%")
    
    return mapper


if __name__ == "__main__":
    main()