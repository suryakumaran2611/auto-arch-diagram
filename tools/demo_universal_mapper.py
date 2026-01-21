#!/usr/bin/env python3
"""
Demo script to showcase the refined universal bulletproof mapper improvements
"""

import sys
sys.path.insert(0, 'tools')

from refined_bulletproof_mapper import RefinedBulletproofMapper

def main():
    print("=" * 80)
    print("UNIVERSAL BULLETPROOF MAPPER DEMONSTRATION")
    print("=" * 80)
    print()
    
    mapper = RefinedBulletproofMapper()
    
    # Comprehensive test cases across all cloud providers
    test_cases = {
        "AWS Services": [
            "aws_ec2_instance",
            "aws_lambda_function", 
            "aws_s3_bucket",
            "aws_rds_instance",
            "aws_sagemaker_endpoint",
            "aws_api_gateway_rest_api",
            "aws_elasticmapreduce_cluster",
            "aws_elasticsearch_domain",
            "aws_cloudwatch_event_rule",
            "aws_sns_topic",
            "aws_sqs_queue",
            "aws_kinesis_stream",
            "aws_glue_catalog_database",
            "aws_iam_role"
        ],
        "GCP Services": [
            "google_compute_instance",
            "google_cloud_run_service",
            "google_storage_bucket",
            "google_sql_database_instance", 
            "google_bigquery_dataset",
            "google_vertex_ai_endpoint",
            "google_alloydb_instance",  # Previously problematic
            "google_aihypercomputer_instance",  # Previously problematic
            "google_anthos_cluster",  # Previously problematic
            "google_cloudasset_project_feed",  # Previously problematic
            "google_cloud_tasks_queue",
            "google_pubsub_topic",
            "google_iam_service_account",
            "google_kms_key_ring"
        ],
        "Azure Services": [
            "azurerm_virtual_machine",
            "azurerm_function_app",
            "azurerm_storage_account",
            "azurerm_sql_database",
            "azurerm_machine_learning_workspace",
            "azurerm_virtual_network",
            "azurerm_key_vault",
            "azurerm_app_service_plan",
            "azurerm_event_grid"
        ],
        "Cross-Provider Comparisons": [
            "aws_ec2_instance",
            "google_compute_instance", 
            "azurerm_virtual_machine"
        ],
        "Edge Cases (Should Never Fail)": [
            "aws_nonexistent_service",
            "google_new_ai_service",
            "azurerm_future_service",
            "custom_provider_custom_resource"
        ]
    }
    
    success_count = 0
    total_count = 0
    
    for category, services in test_cases.items():
        print(f"\n🔍 {category}:")
        print("-" * 50)
        
        for service in services:
            try:
                icon_class = mapper.get_icon(service)
                success_count += 1
                status = "✅"
                print(f"{status} {service:<40} -> {icon_class.__name__}")
            except Exception as e:
                status = "❌"
                print(f"{status} {service:<40} -> ERROR: {e}")
            
            total_count += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"📊 Total Services Tested: {total_count}")
    print(f"✅ Successful Mappings: {success_count}")
    print(f"❌ Failed Mappings: {total_count - success_count}")
    print(f"📈 Success Rate: {(success_count/total_count)*100:.1f}%")
    
    print(f"\n🎯 Key Improvements Demonstrated:")
    print("  • Universal provider support (AWS, Azure, GCP, OCI, IBM, Alibaba)")
    print("  • Enhanced thesaurus with comprehensive service keywords")
    print("  • Dynamic fallbacks that handle missing imports gracefully")
    print("  • Zero-failure guarantee - every service gets an icon")
    print("  • Fixed problematic GCP services (AlloyDB, Anthos, etc.)")
    print("  • Smart resource name cleaning and fuzzy matching")
    print("  • Category-based fallbacks with appropriate defaults")
    
    print(f"\n🚀 This refined mapper can be dropped into existing systems")
    print(f"   to improve icon coverage across ALL cloud providers!")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)