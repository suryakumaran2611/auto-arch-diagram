"""Unit tests for Google Gemini Vision integration."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "tools"))

from gemini_client import (
    DEFAULT_GEMINI_MODEL,
    GeminiError,
    critique_diagram_gemini,
    load_gemini_key,
    parse_critique_response,
)
from diagram_feedback import run_feedback_loop


def test_load_gemini_key(monkeypatch, tmp_path):
    # Test env var resolution
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-123")
    assert load_gemini_key() == "test-gemini-key-123"

    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-456")
    assert load_gemini_key() == "test-google-key-456"

    # Test file resolution
    monkeypatch.delenv("GOOGLE_API_KEY")
    key_file = tmp_path / "gemini_key"
    key_file.write_text("file-secret-key-789\n", encoding="utf-8")
    with patch("gemini_client.KEY_FILE_PATH", key_file):
        assert load_gemini_key() == "file-secret-key-789"


def test_parse_critique_response_valid():
    raw = json.dumps({
        "score": 9,
        "title": "Enterprise Cloud Architecture",
        "subtitle": "High-availability multi-tier platform",
        "hints": [{"tag": "kms", "text": "Customer managed KMS keys"}],
        "labels": {"web": "Public Ingress"},
        "tooltips": {"web": "ALB with AWS WAF protection"},
        "flow_labels": {"web -> app": "1. Forward HTTPS traffic"},
        "insights_md": "Production-grade resilience with multi-AZ replication.",
        "issues": [],
        "suggestions": [{"action": "increase_spacing", "params": {"multiplier": 1.2}}]
    })
    critique = parse_critique_response(raw)
    assert critique["score"] == 9
    assert critique["title"] == "Enterprise Cloud Architecture"
    assert critique["hints"][0]["tag"] == "kms"
    assert critique["labels"]["web"] == "Public Ingress"


def test_parse_critique_response_with_markdown_fences():
    raw = """```json
{
  "score": 8,
  "title": "Serverless Pipeline",
  "subtitle": "Event-driven ETL",
  "hints": [],
  "labels": {},
  "tooltips": {},
  "flow_labels": {},
  "insights_md": "Event ingestion via SQS."
}
```"""
    critique = parse_critique_response(raw)
    assert critique["score"] == 8
    assert critique["title"] == "Serverless Pipeline"
    assert critique["insights_md"] == "Event ingestion via SQS."


def test_parse_critique_response_invalid():
    with pytest.raises(GeminiError):
        parse_critique_response("This is not valid JSON at all")


def test_critique_diagram_gemini_mocked(tmp_path):
    dummy_png = tmp_path / "diagram.png"
    dummy_png.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "score": 9,
                                "title": "Gemini AI Architecture",
                                "subtitle": "Analyzed by Google Gemini Vision",
                                "hints": [{"tag": "compute", "text": "Auto-scaling EKS compute cluster"}],
                                "labels": {"eks": "Container Cluster"},
                                "tooltips": {"eks": "Managed Kubernetes cluster"},
                                "flow_labels": {"ingress -> eks": "1. Route Traffic"},
                                "insights_md": "High availability verified by Gemini.",
                                "issues": [],
                                "suggestions": []
                            })
                        }
                    ]
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        critique, model_used = critique_diagram_gemini(
            dummy_png,
            mermaid_context="flowchart LR",
            inventory="AWS:\n - aws_instance.web",
            model_id="gemini-1.5-flash",
            api_key="mock-gemini-key",
        )
        assert critique["score"] == 9
        assert critique["title"] == "Gemini AI Architecture"
        assert model_used == "gemini:gemini-1.5-flash"
        assert mock_post.called
        # Verify endpoint used key
        call_url = mock_post.call_args[0][0]
        assert "gemini-1.5-flash:generateContent?key=mock-gemini-key" in call_url


def test_run_feedback_loop_gemini_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    import gemini_client
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(gemini_client, "load_gemini_key", lambda: None)

    from generate_arch_diagram import RenderConfig

    render = RenderConfig()
    resources = {"aws_instance.web": {"type": "aws_instance"}}
    edges = set()

    # When no key is configured, run_feedback_loop returns base config gracefully
    res_render, res_dir, critique, history = run_feedback_loop(
        resources,
        edges,
        direction="LR",
        render=render,
        title="Test Architecture",
        backend="gemini",
    )
    assert res_render == render
    assert res_dir == "LR"
    assert critique == {}
    assert history == []
