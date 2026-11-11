"""Static validation for the GitLab CI/CD integration.

These tests keep the reusable GitLab pipeline (component + include template),
its helper scripts, and the documentation in sync. They do not run the diagram
generator; generation is covered by the existing golden/static example tests.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_TEMPLATE = REPO_ROOT / "templates" / "auto-arch-diagram" / "template.yml"
INCLUDE_TEMPLATE = REPO_ROOT / "ci" / "gitlab" / "auto-arch-diagram.gitlab-ci.yml"
GENERATE_SCRIPT = REPO_ROOT / "ci" / "gitlab" / "auto-arch-diagram.sh"
COMMENT_SCRIPT = REPO_ROOT / "ci" / "gitlab" / "comment_on_merge_request.sh"
GITLAB_DOCS = REPO_ROOT / "docs" / "GITLAB_CI.md"
EXAMPLES_DIR = REPO_ROOT / "examples" / "gitlab-ci"
EXAMPLE_PIPELINE = EXAMPLES_DIR / ".gitlab-ci.yml"

EXPECTED_INPUTS = {
    "job-prefix",
    "stage",
    "image",
    "install-system-packages",
    "job-tags",
    "tool-repository",
    "tool-ref",
    "changed-files",
    "iac-globs",
    "iac-root",
    "out-dir",
    "image-formats",
    "out-md",
    "out-mmd",
    "out-png",
    "out-jpg",
    "out-svg",
    "out-drawio",
    "out-html",
    "direction",
    "render-layout",
    "render-bg",
    "edge-color",
    "edge-penwidth",
    "edge-arrowsize",
    "fontsize",
    "iconsize",
    "render-engine",
    "simplified",
    "expand-badges",
    "no-consolidate",
    "planfile",
    "graphfile",
    "varfile",
    "workspace",
    "source",
    "annotate",
    "ai-enhance",
    "ai-backend",
    "gemini-model",
    "openrouter-model",
    "ollama-model",
    "ai-iterations",
    "force-full",
    "always-run",
    "mr-comment",
    "artifacts-expire-in",
}

ADVANCED_VARIABLES = (
    "AUTO_ARCH_RENDER_ENGINE",
    "AUTO_ARCH_SIMPLIFIED",
    "AUTO_ARCH_EXPAND_BADGES",
    "AUTO_ARCH_NO_CONSOLIDATE",
    "AUTO_ARCH_PLANFILE",
    "AUTO_ARCH_GRAPHFILE",
    "AUTO_ARCH_VARFILE",
    "AUTO_ARCH_WORKSPACE",
    "AUTO_ARCH_SOURCE",
    "AUTO_ARCH_ANNOTATE",
)

SCENARIO_PIPELINES = sorted(EXAMPLES_DIR.glob("*/.gitlab-ci.yml"))

# Global keywords are explicitly discouraged in CI/CD components because they
# leak into every job of the consumer pipeline.
FORBIDDEN_COMPONENT_KEYWORDS = {
    "variables",
    "default",
    "stages",
    "include",
    "before_script",
    "after_script",
    "image",
    "services",
    "cache",
}


def _load_yaml_documents(path: Path) -> list[dict]:
    return [doc for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")) if doc]


def _component_documents() -> tuple[dict, dict]:
    documents = _load_yaml_documents(COMPONENT_TEMPLATE)
    assert len(documents) == 2, "component template must contain a spec header and a jobs document"
    spec, jobs = documents
    return spec, jobs


def test_component_template_declares_expected_inputs():
    spec, _ = _component_documents()
    inputs = spec["spec"]["inputs"]
    missing = EXPECTED_INPUTS - set(inputs)
    assert not missing, f"missing component inputs: {sorted(missing)}"


def test_component_template_only_references_declared_inputs():
    spec, _ = _component_documents()
    declared = set(spec["spec"]["inputs"])
    referenced = set(re.findall(r"\$\[\[\s*inputs\.([A-Za-z0-9_-]+)", COMPONENT_TEMPLATE.read_text(encoding="utf-8")))
    unknown = referenced - declared
    assert not unknown, f"component references undeclared inputs: {sorted(unknown)}"


def test_component_template_defines_generate_and_comment_jobs():
    _, jobs = _component_documents()
    job_names = {name for name in jobs if not name.startswith(".")}
    assert "$[[ inputs.job-prefix ]]" in job_names
    assert "$[[ inputs.job-prefix ]]-comment" in job_names


def test_component_template_avoids_global_keywords():
    _, jobs = _component_documents()
    offending = FORBIDDEN_COMPONENT_KEYWORDS.intersection(jobs)
    assert not offending, f"component must not define global keywords: {sorted(offending)}"


def test_component_generate_job_publishes_artifacts_and_dotenv():
    _, jobs = _component_documents()
    generate = jobs["$[[ inputs.job-prefix ]]"]
    artifacts = generate["artifacts"]
    assert artifacts["paths"] == ["$[[ inputs.out-dir ]]/"]
    assert artifacts["reports"]["dotenv"] == "$[[ inputs.out-dir ]]/ci.env"
    assert artifacts["when"] == "always"

    script = "\n".join(generate["script"])
    assert "ci/gitlab/auto-arch-diagram.sh" in script


def test_component_comment_job_needs_generate_and_is_non_blocking():
    _, jobs = _component_documents()
    comment = jobs["$[[ inputs.job-prefix ]]-comment"]
    assert comment["allow_failure"] is True
    assert comment["needs"][0]["job"] == "$[[ inputs.job-prefix ]]"
    assert "ci/gitlab/comment_on_merge_request.sh" in "\n".join(comment["script"])


def test_include_template_defines_variables_and_jobs():
    config = yaml.safe_load(INCLUDE_TEMPLATE.read_text(encoding="utf-8"))
    assert ".auto-arch-diagram-base" in config
    assert "auto-arch-diagram:generate" in config
    assert "auto-arch-diagram:comment" in config

    base_variables = config[".auto-arch-diagram-vars"]["variables"]
    assert base_variables["AUTO_ARCH_TOOL_REPOSITORY"].endswith("auto-arch-diagram.git")
    assert base_variables["GIT_DEPTH"] == "0"
    assert config[".auto-arch-diagram-base"]["extends"] == ".auto-arch-diagram-vars"
    for variable in ADVANCED_VARIABLES:
        assert variable in base_variables, f"include template is missing {variable}"

    generate = config["auto-arch-diagram:generate"]
    assert generate["artifacts"]["reports"]["dotenv"] == "$AUTO_ARCH_OUT_DIR/ci.env"

    comment = config["auto-arch-diagram:comment"]
    assert comment["allow_failure"] is True
    assert comment["needs"] == [{"job": "auto-arch-diagram:generate", "artifacts": True}]


def test_include_template_contains_no_component_input_syntax():
    text = INCLUDE_TEMPLATE.read_text(encoding="utf-8")
    assert "$[[ inputs." not in text, "include templates cannot use component inputs; use variables instead"


@pytest.mark.parametrize("script_path", [GENERATE_SCRIPT, COMMENT_SCRIPT])
def test_gitlab_scripts_have_shebang_and_strict_mode(script_path: Path):
    assert script_path.is_file(), f"missing script: {script_path}"
    text = script_path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text


@pytest.mark.parametrize("script_path", [GENERATE_SCRIPT, COMMENT_SCRIPT])
def test_gitlab_scripts_parse_with_bash(script_path: Path):
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash is not available on this platform")

    if os.name == "nt":
        # Windows-only control: the bundled WSL bash cannot resolve Windows
        # drive-letter paths, so pass a repo-relative POSIX path instead.
        result = subprocess.run(
            [bash, "-n", script_path.relative_to(REPO_ROOT).as_posix()],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    else:
        # Linux/macOS path is unchanged.
        result = subprocess.run(
            [bash, "-n", str(script_path)], capture_output=True, text=True
        )
    assert result.returncode == 0, result.stderr


def test_generate_script_supports_key_configuration():
    text = GENERATE_SCRIPT.read_text(encoding="utf-8")
    for variable in (
        "AUTO_ARCH_CHANGED_FILES",
        "AUTO_ARCH_IAC_ROOT",
        "AUTO_ARCH_IAC_GLOBS",
        "AUTO_ARCH_OUT_DIR",
        "AUTO_ARCH_IMAGE_FORMATS",
        "AUTO_ARCH_DIRECTION",
        "AUTO_ARCH_AI_ENHANCE",
        "AUTO_ARCH_FORCE_FULL",
        *ADVANCED_VARIABLES,
    ):
        assert variable in text
    for flag in (
        "--render-engine",
        "--simplified",
        "--expand-badges",
        "--no-consolidate",
        "--planfile",
        "--graphfile",
        "--varfile",
        "--workspace",
        "--source",
        "--annotate",
    ):
        assert flag in text
    assert "CI_MERGE_REQUEST_DIFF_BASE_SHA" in text
    assert "ci.env" in text


def test_documentation_and_example_exist():
    assert GITLAB_DOCS.is_file()
    docs = GITLAB_DOCS.read_text(encoding="utf-8")
    assert "include:" in docs
    assert "AUTO_ARCH_GITLAB_TOKEN" in docs
    assert "auto-arch-diagram.gitlab-ci.yml" in docs

    assert EXAMPLE_PIPELINE.is_file()
    example = yaml.safe_load(EXAMPLE_PIPELINE.read_text(encoding="utf-8"))
    include = example["include"]
    assert any(
        "auto-arch-diagram.gitlab-ci.yml" in entry.get("remote", "")
        for entry in include
        if isinstance(entry, dict)
    ), "example pipeline should include the remote GitLab template"


def test_example_gallery_covers_all_scenarios():
    scenarios = sorted(path for path in EXAMPLES_DIR.iterdir() if path.is_dir())
    assert len(scenarios) >= 12, f"expected at least 12 scenarios, found {len(scenarios)}"

    for scenario in scenarios:
        assert (scenario / ".gitlab-ci.yml").is_file(), f"{scenario.name} has no pipeline"
        assert (scenario / "README.md").is_file(), f"{scenario.name} has no README"

    index = (EXAMPLES_DIR / "README.md").read_text(encoding="utf-8")
    for scenario in scenarios:
        assert scenario.name in index, f"{scenario.name} is missing from the gallery index"


@pytest.mark.parametrize(
    "pipeline", SCENARIO_PIPELINES, ids=[path.parent.name for path in SCENARIO_PIPELINES]
)
def test_scenario_pipelines_parse_and_include_a_template(pipeline: Path):
    config = yaml.safe_load(pipeline.read_text(encoding="utf-8"))
    assert isinstance(config, dict), f"{pipeline} is not a YAML mapping"

    includes = config.get("include")
    assert includes, f"{pipeline} does not include a template"
    for entry in includes:
        assert isinstance(entry, dict), f"{pipeline} include entries must be mappings"
        assert {"remote", "component", "local", "project"}.intersection(entry), (
            f"{pipeline} has an unsupported include entry: {entry}"
        )

    text = pipeline.read_text(encoding="utf-8")
    assert "$[[ inputs." not in text, "consumer pipelines must not use component interpolation"


def test_component_inputs_are_documented():
    spec, _ = _component_documents()
    docs = GITLAB_DOCS.read_text(encoding="utf-8")
    missing = [
        name for name in spec["spec"]["inputs"] if f"`{name}`" not in docs
    ]
    assert not missing, f"component inputs missing from docs/GITLAB_CI.md: {sorted(missing)}"


def test_component_maps_advanced_inputs_to_variables():
    _, jobs = _component_documents()
    generate = jobs["$[[ inputs.job-prefix ]]"]
    variables = generate["variables"]

    expected_mapping = {
        "render-engine": "AUTO_ARCH_RENDER_ENGINE",
        "simplified": "AUTO_ARCH_SIMPLIFIED",
        "expand-badges": "AUTO_ARCH_EXPAND_BADGES",
        "no-consolidate": "AUTO_ARCH_NO_CONSOLIDATE",
        "planfile": "AUTO_ARCH_PLANFILE",
        "graphfile": "AUTO_ARCH_GRAPHFILE",
        "varfile": "AUTO_ARCH_VARFILE",
        "workspace": "AUTO_ARCH_WORKSPACE",
        "source": "AUTO_ARCH_SOURCE",
        "annotate": "AUTO_ARCH_ANNOTATE",
    }
    for input_name, variable in expected_mapping.items():
        assert variables[variable] == f"$[[ inputs.{input_name} ]]"

