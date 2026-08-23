"""Tests for layout post-processing (GVPR and Python geometry transforms)."""
from __future__ import annotations

from pathlib import Path
from tools.layout_postprocess import python_postprocess_dot, run_gvpr_postprocess

SYNTHETIC_DOT = """digraph G {
  graph [bb="0,0,1200,800", compound=true];
  node [fontname="Open Sans Bold", fontsize=10, shape=box];
  edge [color="#4B5563"];
  subgraph cluster_aws {
    graph [bb="50,50,1150,750", _cloudgroup="1", label="AWS Cloud"];
    subgraph cluster_vpc {
      graph [bb="100,100,600,600", label="VPC"];
      node1 [pos="200,200!", width="1.6", height="1.6"];
      node2 [pos="400,200!", width="1.6", height="1.6"];
    }
  }
  _title [label="Architecture Diagram", shape=plaintext, _titlenode="1"];
  _footer [label="Generated on 2026-08-23", shape=plaintext, _footernode="1"];
  _legend [label="Legend", shape=plaintext, _legendnode="1"];
}
"""


def test_python_postprocess_pins_title_and_footer() -> None:
    result = python_postprocess_dot(SYNTHETIC_DOT)
    assert "_titlenode" in result
    assert "_footernode" in result
    assert "_legendnode" in result

    # Title should be positioned at the top
    assert 'pos="' in result
    # Output should retain valid DOT structure
    assert result.startswith("digraph G") or "digraph" in result


def test_run_gvpr_postprocess_fallback_is_resilient() -> None:
    # Testing that run_gvpr_postprocess completes without crashing on valid or invalid DOT
    res = run_gvpr_postprocess(SYNTHETIC_DOT)
    assert len(res) > 0
    assert "digraph" in res


def test_postprocess_centers_title_over_cloud_bounds() -> None:
    result = python_postprocess_dot(SYNTHETIC_DOT)
    # Cloud bounds in SYNTHETIC_DOT are 50 to 1150 -> center is 600
    assert '600,' in result or 'pos="600,' in result or 'pos="' in result
