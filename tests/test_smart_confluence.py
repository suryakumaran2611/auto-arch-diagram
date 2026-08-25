"""Unit tests for Smart Confluence AI-enhanced architecture portal publishing."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.smart_confluence import (
    ConfluenceArtifacts,
    CostDriver,
    FinOpsRecommendation,
    ImprovementItem,
    SmartConfluenceReport,
    analyze_architecture_for_confluence,
    build_smart_confluence_xhtml,
    publish_smart_confluence_page,
)


def test_build_smart_confluence_xhtml(tmp_path: Path):
    """Verify Confluence XHTML storage format construction and macro presence."""
    png_file = tmp_path / "architecture.png"
    html_file = tmp_path / "architecture.html"
    drawio_file = tmp_path / "architecture.drawio"
    svg_file = tmp_path / "architecture.svg"

    png_file.write_text("fake-png")
    html_file.write_text("fake-html")
    drawio_file.write_text("fake-drawio")
    svg_file.write_text("fake-svg")

    artifacts = ConfluenceArtifacts(
        png=png_file,
        html=html_file,
        drawio=drawio_file,
        svg=svg_file,
    )

    report = SmartConfluenceReport(
        title="Enterprise Scalable MLOps Platform",
        subtitle="Automated inference and ETL pipelines on AWS",
        workload_overview="Ingress routes through CloudFront into ECS and Aurora MySQL Multi-AZ.",
        provider="AWS",
        environment="Production",
        iac_tool="Terraform",
        cost_drivers=[
            CostDriver("EKS GPU Nodes", "Compute", "p3.2xlarge", "High", "ML Training cluster"),
            CostDriver("Aurora MySQL Multi-AZ", "Database", "db.r6g.xlarge", "High", "Persistence layer"),
        ],
        finops_recommendations=[
            FinOpsRecommendation("Purchase Compute Savings Plans", "High", "Easy", "35% compute reduction"),
            FinOpsRecommendation("Enable S3 Intelligent-Tiering", "Medium", "Easy", "40% archive savings"),
        ],
        estimated_monthly_range="$2,000 - $4,500 / mo",
        security_highlights=[
            "KMS CMK envelope encryption on all databases and buckets",
            "Private subnet segregation with strict security group isolation",
        ],
        reliability_highlights=[
            "Multi-AZ active/standby database failover",
            "Dead-Letter Queues (DLQ) on all asynchronous event streams",
        ],
        improvements=[
            ImprovementItem("P1 - High", "Add AWS WAF to ALB", "Security", "Public ALB lacks rate-limiting", "Attach aws_wafv2_web_acl_association"),
        ],
    )

    resources = [
        {"type": "aws_eks_cluster", "name": "ml_cluster", "category": "Compute", "id": "aws_eks_cluster.ml_cluster"},
        {"type": "aws_rds_cluster", "name": "aurora_db", "category": "Database", "id": "aws_rds_cluster.aurora_db"},
        {"type": "aws_s3_bucket", "name": "lake_curated", "category": "Storage", "id": "aws_s3_bucket.lake_curated"},
    ]

    xhtml = build_smart_confluence_xhtml(
        report=report,
        artifacts=artifacts,
        resources=resources,
        git_commit="abcdef123456",
        branch="main",
    )

    # Assertions on Confluence storage format macros
    assert "<!-- smart-confluence:start -->" in xhtml
    assert "<!-- smart-confluence:end -->" in xhtml
    assert '<ac:structured-macro ac:name="info">' in xhtml
    assert '<ac:structured-macro ac:name="status">' in xhtml
    assert '<ac:structured-macro ac:name="tip">' in xhtml
    assert '<ac:structured-macro ac:name="expand">' in xhtml
    assert '<ac:image' in xhtml
    assert 'ac:width="900"' in xhtml
    assert 'ri:filename="architecture.png"' in xhtml
    assert "Enterprise Scalable MLOps Platform" in xhtml
    assert "EKS GPU Nodes" in xhtml
    assert "Purchase Compute Savings Plans" in xhtml
    assert "35% compute reduction" in xhtml
    assert "KMS CMK envelope encryption" in xhtml
    assert "Multi-AZ active/standby database failover" in xhtml
    assert "aws_eks_cluster" in xhtml
    assert "Open / Download HTML Studio" in xhtml
    assert "Download .drawio Vector File" in xhtml


def test_analyze_architecture_rule_based_fallback():
    """Verify heuristic analysis engine generates rich insights when offline."""
    resources = [
        {"type": "aws_eks_cluster", "name": "eks_cluster", "category": "Compute"},
        {"type": "aws_sagemaker_endpoint", "name": "inference_endpoint", "category": "AI/ML"},
        {"type": "aws_rds_cluster", "name": "aurora_mysql", "category": "Database"},
        {"type": "aws_s3_bucket", "name": "lake_raw", "category": "Storage"},
        {"type": "aws_s3_bucket", "name": "lake_curated", "category": "Storage"},
        {"type": "aws_kms_key", "name": "storage_cmk", "category": "Security"},
    ]
    edges = [("aws_eks_cluster.eks_cluster", "aws_rds_cluster.aurora_mysql")]

    report = analyze_architecture_for_confluence(
        resources=resources,
        edges=edges,
        png_path=None,
        backend="rule-based",
        provider="AWS",
    )

    assert "MLOps" in report.title or "AWS" in report.title
    assert len(report.cost_drivers) >= 2
    assert len(report.finops_recommendations) >= 2
    assert len(report.security_highlights) >= 2
    assert len(report.improvements) >= 2


@patch("tools.smart_confluence.requests.get")
@patch("tools.smart_confluence.requests.post")
@patch("tools.smart_confluence.requests.put")
def test_publish_smart_confluence_page(mock_put, mock_post, mock_get, tmp_path: Path):
    """Verify REST API calls and payload structure for Smart Confluence publishing."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "title": "Architecture Hub",
        "version": {"number": 3},
        "body": {"storage": {"value": "<p>Old architecture content</p>"}},
    }

    mock_post.return_value.status_code = 200
    mock_put.return_value.status_code = 200

    png_file = tmp_path / "architecture.png"
    drawio_file = tmp_path / "architecture.drawio"
    png_file.write_text("png-data")
    drawio_file.write_text("drawio-data")

    artifacts = ConfluenceArtifacts(png=png_file, drawio=drawio_file)
    report = SmartConfluenceReport(
        title="Microservices Cloud Platform",
        subtitle="Containerized services on AWS",
        workload_overview="Web layer to database cluster.",
    )
    resources = [{"type": "aws_instance", "name": "web", "category": "Compute"}]

    success = publish_smart_confluence_page(
        confluence_url="https://company.atlassian.net/wiki",
        confluence_user="architect@company.com",
        confluence_token="secret-token-123",
        page_id="12345678",
        report=report,
        artifacts=artifacts,
        resources=resources,
        full_page=True,
    )

    assert success is True
    assert mock_get.called
    assert mock_post.called  # Attachments uploaded
    assert mock_put.called   # Page updated
    assert mock_post.call_args.kwargs["params"]["allowDuplicated"] == "true"

    # Inspect page update payload
    put_args, put_kwargs = mock_put.call_args
    payload = put_kwargs.get("json", {})
    assert payload["version"]["number"] == 4
    assert "Microservices Cloud Platform" in payload["body"]["storage"]["value"]


@patch("tools.generate_arch_diagram.requests.get")
@patch("tools.generate_arch_diagram.requests.post")
@patch("tools.generate_arch_diagram.requests.put")
def test_publish_standard_confluence_with_drawio(mock_put, mock_post, mock_get, tmp_path: Path):
    """Verify regular non-AI Confluence image replacement also uploads draw.io attachment."""
    from tools.generate_arch_diagram import _publish_to_confluence

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "title": "Standard Wiki Page",
        "version": {"number": 1},
        "body": {"storage": {"value": "<p>Existing wiki content</p>"}},
    }
    mock_post.return_value.status_code = 200
    mock_put.return_value.status_code = 200

    png_file = tmp_path / "architecture.png"
    drawio_file = tmp_path / "architecture.drawio"
    png_file.write_text("png-bytes")
    drawio_file.write_text("drawio-xml")

    success = _publish_to_confluence(
        confluence_url="https://company.atlassian.net/wiki",
        confluence_user="dev@company.com",
        confluence_token="token-xyz",
        page_id="998877",
        diagram_path=png_file,
        drawio_path=drawio_file,
        replace=True,
    )

    assert success is True
    assert mock_get.called
    assert mock_post.call_count == 2  # 1 for PNG + 1 for Draw.io
    assert mock_put.called


@patch("tools.smart_confluence.requests.get")
@patch("tools.smart_confluence.requests.post")
@patch("tools.smart_confluence.requests.put")
def test_smart_confluence_existing_attachment_data_update(mock_put, mock_post, mock_get, tmp_path: Path):
    """Verify that when an attachment already exists (HTTP 400), it updates via /{att_id}/data."""
    # First GET for page metadata, second GET for attachment lookup by filename
    mock_get.side_effect = [
        MagicMock(status_code=200, json=lambda: {
            "title": "Existing Architecture",
            "version": {"number": 5},
            "body": {"storage": {"value": "<p>Existing content</p>"}},
        }),
        MagicMock(status_code=200, json=lambda: {
            "results": [{"id": "att-existing-999", "title": "architecture.png"}]
        }),
    ]

    # First POST returns 400 (duplicate filename), second POST updates /{att_id}/data (200 OK)
    mock_post.side_effect = [
        MagicMock(
            status_code=400,
            text='{"message": "Cannot add a new attachment with same file name as an existing attachment: architecture.png"}',
        ),
        MagicMock(status_code=200, json=lambda: {"id": "att-existing-999"}),
    ]
    mock_put.return_value = MagicMock(status_code=200, json=lambda: {"version": {"number": 6}})

    png_file = tmp_path / "architecture.png"
    png_file.write_text("png-data-update")

    artifacts = ConfluenceArtifacts(png=png_file)
    report = SmartConfluenceReport(
        title="Updated Platform",
        subtitle="Testing attachment deduplication",
        workload_overview="Web to DB",
    )

    success = publish_smart_confluence_page(
        confluence_url="https://company.atlassian.net/wiki",
        confluence_user="architect@company.com",
        confluence_token="secret-token-123",
        page_id="589825",
        report=report,
        artifacts=artifacts,
        resources=[],
        full_page=True,
    )

    assert success is True
    # Verify second POST was to the /{attachmentId}/data endpoint
    second_post_url = mock_post.call_args_list[1][0][0]
    assert second_post_url.endswith("/child/attachment/att-existing-999/data")


