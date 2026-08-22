# Testing Guide

This document provides instructions for running tests locally and understanding the CI/CD test configuration.

## Prerequisites

- Python 3.11 or higher
- Graphviz (for icon rendering tests)

### Installing Graphviz

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
Download from: https://graphviz.org/download/

## Local Testing Setup

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Run Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=tools --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_golden_examples.py -v
```

## Test Structure

### Unit Tests

- **test_golden_examples.py**: Tests the golden example matching between generated diagrams and expected output
  - `test_golden_mermaid_matches_example_terraform`: Validates that the generated Mermaid diagram matches the golden file
  - `test_cli_generates_expected_mermaid_file`: Tests the CLI tool end-to-end

- **test_static_cloudformation.py**: Tests CloudFormation parsing and diagram generation
  - `test_static_cloudformation_graph_detects_dependencies`: Validates dependency detection
  - `test_static_cloudformation_mermaid_contains_flowchart_direction`: Ensures proper Mermaid syntax

- **test_static_terraform.py**: Tests Terraform parsing and diagram generation
  - `test_static_terraform_graph_parses_resources_and_edges`: Validates resource and dependency parsing
  - `test_static_terraform_mermaid_contains_flowchart_direction`: Ensures proper Mermaid syntax
  - `test_icon_rendering_produces_png`: Tests icon-based diagram rendering (requires Graphviz)

- **test_ai_enhancement.py**: Tests the AI enhancement stack (no network required - all API calls are mocked)
  - OpenRouter client: free-model enforcement (`ranked_free_vision_models` filtering/ranking/override validation), key resolution, model fallback on 429/5xx, JSON critique parsing
  - Feedback loop: render suggestion mapping (`apply_suggestion`), plateau/target early-stop behavior, no-key no-op path, insights markdown rendering
  - Label overrides: `_sanitize_label` rules, `_extract_label_overrides` matching (full id + name part), `_tf_node_label` override application
  - Guide + stitching: standalone legend render (`_render_guide_png`), PIL raster stitch with white matte, SVG canvas extension with embedded data URI
  - Palette: official provider accents/tints constants, white-canvas default, draw.io exporter mirroring

### Golden Files

Golden files are reference outputs stored in `tests/golden/` directory:
- `aws-basic.mmd`: Expected Mermaid output for the aws-basic example

## Security Scanning

The CI pipeline includes security scanning tools:

### 1. pip-audit (Dependency Vulnerability Scanning)

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

### 2. bandit (Static Security Analysis)

```bash
pip install bandit
bandit -q -r tools --severity-level medium --confidence-level medium
```

## CI/CD Testing

The repository uses GitHub Actions for automated testing. See `.github/workflows/python-tests.yml`.

### Test Workflow Steps:

1. **Checkout**: Clones the repository
2. **Setup Python**: Installs Python 3.11
3. **Install Graphviz**: Installs system dependencies
4. **Install Dependencies**: Installs Python packages
5. **Security Scans**: Runs pip-audit and bandit
6. **Unit Tests**: Runs pytest

### Running CI Tests Locally

To replicate the CI environment locally:

```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install pip-audit bandit

# Run security scans
pip-audit -r requirements.txt
bandit -q -r tools --severity-level medium --confidence-level medium

# Run unit tests
pytest
```

## Troubleshooting

### Issue: "No module named pytest"
**Solution**: Ensure you're in the virtual environment and have installed requirements-dev.txt:
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Issue: "Graphviz 'dot' not found"
**Solution**: Install Graphviz system package (see Prerequisites section)

### Issue: Tests fail with "ModuleNotFoundError"
**Solution**: Ensure the project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```
Or the conftest.py should handle this automatically.

### Issue: "externally-managed-environment" error
**Solution**: Use a virtual environment instead of system Python:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Adding New Tests

1. Create test file in `tests/` directory with `test_` prefix
2. Import necessary modules and fixtures
3. Name test functions with `test_` prefix
4. Use pytest assertions (`assert`)
5. Update this documentation with new test descriptions

## Test Coverage

To measure test coverage:

```bash
pip install pytest-cov
pytest --cov=tools --cov-report=term-missing
```

To generate HTML coverage report:

```bash
pytest --cov=tools --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Continuous Integration

All pull requests automatically run:
- Unit tests
- Security scans (pip-audit, bandit)
- Code quality checks (CodeQL)
- Dependency review

Ensure all tests pass before merging.
