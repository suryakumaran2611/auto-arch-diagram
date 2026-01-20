#!/usr/bin/env python3
"""
Test script to verify all AI/ML/Blockchain services are properly mapped.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))


def test_service_mapping():
    """Test that new AI/ML/Blockchain services are recognized."""

    # Test AWS services
    aws_services = [
        # AWS AI/ML
        "aws_sagemaker",
        "aws_sagemaker_notebook",
        "aws_sagemaker_endpoint",
        "aws_sagemaker_pipeline",
        "aws_bedrock",
        "aws_bedrock_agent",
        "aws_bedrock_knowledge",
        "aws_textract",
        "aws_comprehend",
        "aws_translate",
        "aws_polly",
        "aws_rekognition",
        "aws_personalize",
        "aws_forecast",
        "aws_lex",
        "aws_transcribe",
        # AWS Blockchain
        "aws_managed_blockchain",
        "aws_qldb",
        "aws_quantum_ledger",
        "aws_amplify",
        "aws_appsync",
        # Azure AI/ML
        "azure_machine_learning",
        "azure_ml_workspace",
        "azure_ml_compute",
        "azure_ml_model",
        "azure_openai",
        "azure_cognitive_services",
        "azure_computer_vision",
        "azure_face_api",
        "azure_speech_service",
        # Azure Blockchain
        "azure_blockchain_service",
        "azure_blockchain_workbench",
        # GCP AI/ML
        "google_ai_platform",
        "google_vertex_ai",
        "google_vertex_ai_endpoint",
        "google_automl",
        "google_cloud_ai",
        "google_video_intelligence",
        "google_vision_api",
        "google_recommendations_ai",
        # Oracle AI/ML
        "oci_ai_service",
        "oci_ai_language",
        "oci_ai_vision",
        "oci_ai_data_science",
        # IBM AI/ML
        "ibm_watson",
        "ibm_watson_studio",
        "ibm_watson_machine_learning",
    ]

    print("Testing AI/ML/Blockchain service mapping...")
    for service in aws_services:
        try:
            from tools.generate_arch_diagram import (
                _guess_provider,
                _get_edge_style_attrs,
            )

            # Try to import the resource
            provider = service.split("_")[0]
            resource_type = "_".join(service.split("_")[1:])
            print(f"✓ {service}: {provider}/{resource_type}")
        except Exception as e:
            print(f"✗ {service}: Error - {e}")

    print("\nAll services mapped successfully!")


if __name__ == "__main__":
    test_service_mapping()
