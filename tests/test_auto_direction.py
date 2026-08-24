"""Unit tests for intelligent AUTO layout direction determination."""

import pytest
from tools.generate_arch_diagram import DiagramComplexity, _determine_optimal_direction


def test_auto_direction_multi_tier_cloud():
    """Verify standard 3-tier cloud architecture defaults to professional horizontal LR."""
    complexity = DiagramComplexity(
        node_count=12,
        edge_count=15,
        cluster_count=3,
        max_cluster_depth=2,
        avg_edges_per_node=1.25,
        max_label_length=20,
        provider_count=1,
    )
    grouped_data = {
        "Network": {"aws": ["aws_vpc.main", "aws_subnet.public"]},
        "Compute": {"aws": ["aws_ecs_service.web", "aws_ecs_task_definition.web"]},
        "Database": {"aws": ["aws_rds_cluster.primary", "aws_rds_cluster_instance.i1"]},
    }
    direction = _determine_optimal_direction(complexity, grouped_data, layout="lanes")
    assert direction == "LR"


def test_auto_direction_multi_cloud():
    """Verify multi-cloud architectures (AWS + GCP + Azure) use horizontal LR."""
    complexity = DiagramComplexity(
        node_count=8,
        edge_count=10,
        cluster_count=3,
        max_cluster_depth=2,
        avg_edges_per_node=1.25,
        max_label_length=18,
        provider_count=2,
    )
    grouped_data = {
        "Compute": {"aws": ["aws_instance.app"], "gcp": ["google_compute_instance.app"]},
        "Storage": {"aws": ["aws_s3_bucket.data"], "gcp": ["google_storage_bucket.data"]},
    }
    direction = _determine_optimal_direction(complexity, grouped_data, layout="providers")
    assert direction == "LR"


def test_auto_direction_serverless_pipeline():
    """Verify event-driven / serverless pipelines use horizontal LR."""
    complexity = DiagramComplexity(
        node_count=6,
        edge_count=7,
        cluster_count=2,
        max_cluster_depth=1,
        avg_edges_per_node=1.16,
        max_label_length=15,
        provider_count=1,
    )
    grouped_data = {
        "Integration": {"aws": ["aws_api_gateway_rest_api.api", "aws_sqs_queue.events"]},
        "Compute": {"aws": ["aws_lambda_function.worker"]},
        "Database": {"aws": ["aws_dynamodb_table.records"]},
    }
    direction = _determine_optimal_direction(complexity, grouped_data, layout="lanes")
    assert direction == "LR"


def test_auto_direction_strictly_linear_single_lane():
    """Verify only strictly linear 1-column single-resource hierarchies return TB."""
    complexity = DiagramComplexity(
        node_count=2,
        edge_count=1,
        cluster_count=1,
        max_cluster_depth=4,
        avg_edges_per_node=0.1,
        max_label_length=10,
        provider_count=1,
    )
    grouped_data = {
        "Compute": {"aws": ["aws_instance.single"]},
    }
    direction = _determine_optimal_direction(complexity, grouped_data, layout="lanes")
    assert direction == "TB"
