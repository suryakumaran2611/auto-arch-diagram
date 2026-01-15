from __future__ import annotations

from pathlib import Path

from tools.generate_arch_diagram import Limits
from tools.generate_arch_diagram import _static_cloudformation_graph
from tools.generate_arch_diagram import _static_cloudformation_mermaid


def test_static_cloudformation_graph_detects_dependencies(tmp_path: Path) -> None:
    tpl = tmp_path / "template.yaml"
    tpl.write_text(
        """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Bucket:
    Type: AWS::S3::Bucket
  FunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
  Func:
    Type: AWS::Lambda::Function
    Properties:
      Role:
        Fn::GetAtt: [FunctionRole, Arn]
      Code:
        ZipFile: |
          exports.handler = async () => { return 'ok'; };
      Handler: index.handler
      Runtime: nodejs18.x
""",
        encoding="utf-8",
    )

    resources, edges = _static_cloudformation_graph([tpl], Limits())
    assert "Func" in resources
    assert "FunctionRole" in resources
    assert ("FunctionRole", "Func") in edges


def test_static_cloudformation_mermaid_contains_flowchart_direction(tmp_path: Path) -> None:
    tpl = tmp_path / "template.yaml"
    tpl.write_text(
        """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Bucket:
    Type: AWS::S3::Bucket
""",
        encoding="utf-8",
    )

    mermaid, summary, assumptions = _static_cloudformation_mermaid([tpl], "TB", Limits())
    assert mermaid.startswith("flowchart TB")
    assert "Bucket" in mermaid
    assert summary
    assert assumptions
