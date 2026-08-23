"""Tests for newly added features: planfile, simplified mode, flow annotations, and variants."""
from __future__ import annotations

import json
from pathlib import Path
from tools.generate_arch_diagram import (
    RenderConfig,
    _apply_flow_annotations,
    _icon_class_for,
    _parse_terraform_plan_json,
    _simplify_architecture_graph,
)


def test_planfile_parsing(tmp_path: Path) -> None:
    plan_data = {
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "type": "aws_instance",
                        "name": "web",
                        "values": {"ami": "ami-123456", "instance_type": "t3.micro"},
                    },
                    {
                        "type": "aws_s3_bucket",
                        "name": "data",
                        "values": {"bucket": "my-bucket"},
                    },
                ]
            }
        }
    }
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan_data), encoding="utf-8")

    resources, _, _ = _parse_terraform_plan_json(plan_file)
    assert "aws_instance.web" in resources
    assert "aws_s3_bucket.data" in resources
    assert resources["aws_instance.web"]["instance_type"] == "t3.micro"


def test_simplify_architecture_graph() -> None:
    resources = {
        "aws_instance.web": {"type": "aws_instance", "name": "web"},
        "aws_route_table.rt": {"type": "aws_route_table", "name": "rt"},
        "aws_route_table_association.rta": {"type": "aws_route_table_association", "name": "rta"},
        "aws_s3_bucket.data": {"type": "aws_s3_bucket", "name": "data"},
    }
    edges = {
        ("aws_instance.web", "aws_route_table.rt"),
        ("aws_instance.web", "aws_s3_bucket.data"),
    }

    filtered_res, filtered_edges = _simplify_architecture_graph(resources, edges)
    # Plumbing route table and association should be stripped
    assert "aws_instance.web" in filtered_res
    assert "aws_s3_bucket.data" in filtered_res
    assert "aws_route_table.rt" not in filtered_res
    assert "aws_route_table_association.rta" not in filtered_res
    assert ("aws_instance.web", "aws_s3_bucket.data") in filtered_edges
    assert ("aws_instance.web", "aws_route_table.rt") not in filtered_edges


def test_apply_flow_annotations(tmp_path: Path) -> None:
    flow_yaml = """
flows:
  - name: "Data Ingestion"
    color: "#28A745"
    steps:
      - from: "aws_s3_bucket.raw"
        to: "aws_lambda_function.process"
        label: "1. S3 Event"
"""
    flow_file = tmp_path / "flows.yaml"
    flow_file.write_text(flow_yaml, encoding="utf-8")

    flows = _apply_flow_annotations({}, set(), flow_file)
    assert len(flows) == 1
    assert flows[0]["name"] == "Data Ingestion"


def test_variant_icon_resolution() -> None:
    # ALB vs NLB
    alb_icon = _icon_class_for("aws_lb", {"load_balancer_type": "application"})
    nlb_icon = _icon_class_for("aws_lb", {"load_balancer_type": "network"})
    assert alb_icon is not None
    assert nlb_icon is not None
    assert alb_icon != nlb_icon

    # RDS Aurora vs MySQL
    aurora_icon = _icon_class_for("aws_rds_cluster", {"engine": "aurora-postgresql"})
    assert aurora_icon is not None

    # ECS Fargate
    fargate_icon = _icon_class_for("aws_ecs_service", {"launch_type": "FARGATE"})
    assert fargate_icon is not None
