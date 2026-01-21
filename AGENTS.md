
# Auto-Arch-Diagram Project Environment Setup

## WSL Environment Configuration
Always use WSL Ubuntu with virtual environment activated for this project.

### Command Template:
```bash
wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && [YOUR_COMMAND]"
```

### Environment Details:
- Distribution: Ubuntu (WSL)
- Project Path: `/home/suryakumaran/GitHub/auto-arch-diagram`
- Virtual Environment: `.venv` (Python 3.12.3)
- Activation: `source .venv/bin/activate`

### Quick Setup Commands:
```bash
# Check environment
wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && python --version"

# Install dependencies
wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && pip install -r requirements.txt"

# Run tests
wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && pytest"
```

## Icon Mapping & Custom Icon Architecture

### Key Components & Files

#### **Core Architecture Generation**
- **`tools/generate_arch_diagram.py`** - Main file that handles:
  - Icon mapping logic (`_icon_class_for()` function)
  - Custom icon loading (`_load_custom_icon()` function)  
  - Processing Terraform `Icon` tags via global override system (`_CURRENT_ICON_OVERRIDE`)
  - SVG generation with embedded icons (`_embed_images_in_svg()`)

#### **Service Mapping Files**
- **`tools/comprehensive_service_mappings.py`** - Comprehensive mappings for AWS, Azure, GCP services to diagrams library categories and classes
- **`icons/comprehensive_mappings.json`** - Maps service names to actual icon file paths

#### **Icon Library Management**
- **`tools/icon_library.py`** - Downloads and manages complete icon libraries from diagrams GitHub repo
- **`tools/cloud_icons_util.py`** - Loads cloud icon catalogs
- **`tools/cloud_services_util.py`** - Loads dynamic cloud service lists

#### **Custom Icon Processing**
- **`icons/custom/generate_icons.py`** - Generates custom programmatic icons for data processing services
- **`icons/custom/`** - Directory for storing custom icons

### Current Icon Resolution Order
1. Comprehensive service mappings (diagrams library)
2. Custom icons in icons/{provider}/ directory  
3. Built-in diagrams library icons
4. Generic fallback icons

### Known Issues (CRITICAL)
1. **Custom Icon Override System Broken**: `_CURRENT_ICON_OVERRIDE` is set but never used in `_load_custom_icon()`
2. **Custom:// Scheme Missing**: URI scheme parsing not implemented
3. **Default Icon Gaps**: Services like API Gateway, ElasticSearch, Glue missing proper mappings
4. **SVG Image Embedding**: Custom icons not being embedded in generated SVGs

### Custom Icon Tags in Terraform
```hcl
tags = {
  Icon = "custom://datapipeline"    # Should load icons/custom/datapipeline.png
  Icon = "custom://messagequeue"    # Should load icons/custom/messagequeue.png
}
```

### Debug Tools
- **`tools/debug_icon_mapping.py`** - Comprehensive icon mapping debugger (NEW)
- **`tools/debug_icon_loading.py`** - Test icon loading for specific services
- **`tools/verify_icon_coverage.py`** - Verify icon coverage for services

## Agent Instructions:

### Environment Setup (ALWAYS REQUIRED)
When working on this project, ALWAYS:
1. Use WSL Ubuntu distribution
2. Navigate to the project directory
3. Activate the virtual environment
4. Execute commands within the activated environment

### Icon Mapping Workflows

#### For Debugging Icon Issues:
1. **Run comprehensive debugger first**:
   ```bash
   wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && python tools/debug_icon_mapping.py"
   ```
2. **Check specific Terraform example**:
   ```bash
   wsl -d Ubuntu bash -c "cd /home/suryakumaran/GitHub/auto-arch-diagram && source .venv/bin/activate && python tools/generate_arch_diagram.py examples/terraform/custom-icons-demo/"
   ```

#### For Fixing Custom Icons:
1. **Priority 1**: Fix `_load_custom_icon()` to process `custom://` scheme
2. **Priority 2**: Implement `_CURRENT_ICON_OVERRIDE` usage
3. **Priority 3**: Generate missing custom icons using `icons/custom/generate_icons.py`
4. **Priority 4**: Add missing default service mappings

#### Key Files to Modify for Icon Fixes:
- `tools/generate_arch_diagram.py` - Fix custom icon loading logic
- `tools/comprehensive_service_mappings.py` - Add missing service mappings
- `icons/custom/generate_icons.py` - Generate missing custom icons

### Testing Changes:
1. Always test with `examples/terraform/custom-icons-demo/main.tf`
2. Verify SVG generation and icon embedding
3. Check that custom `Icon` tags are respected
4. Run debug tool to validate fixes

## Agent Update Policy

- Agents must always review the latest version of this AGENTS.md file and all related documentation (README.md, TESTING.md, USER_GUIDE.md, and any new docs) before making changes, implementing features, or running workflows.
- When a new feature, enhancement, or command is added to the project, agents must:
  1. Read all updated or new documentation files.
  2. Update their internal instructions and workflows to reflect the latest changes.
  3. Ensure that all new or modified commands, features, or enhancements are tested according to the latest best practices and testing instructions.
  4. Communicate/document any new requirements or changes in this file for future agents.
- Agents should regularly check for updates in the documentation and codebase, especially after merges, releases, or major changes.
- If any ambiguity or missing information is found, agents must clarify or update the documentation to ensure future consistency.

**This policy ensures that all agents remain in sync with the latest project state and best practices.**

## Additional Agent Best Practices and Testing/Development Instructions

### Environment & Setup
- Always use WSL Ubuntu with the Python virtual environment activated.
- Project root: `/home/suryakumaran/GitHub/auto-arch-diagram`
- Activate the environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`
- For Graphviz (required for icon rendering):
  - Ubuntu: `sudo apt-get install -y graphviz`
  - macOS: `brew install graphviz`
  - Windows: Download from https://graphviz.org/download/

### Testing
- Run all tests: `pytest`
- Run with coverage: `pytest --cov=tools --cov-report=html`
- Run specific test: `pytest tests/test_golden_examples.py -v`
- Security scans:
  - `pip install pip-audit bandit`
  - `pip-audit -r requirements.txt`
  - `bandit -q -r tools --severity-level medium --confidence-level medium`
- Ensure the project root is in `PYTHONPATH` if you see import errors.

### Test Structure
- All new tests go in the `tests/` directory with a `test_` prefix.
- Use pytest assertions (`assert`).
- Update documentation with new test descriptions.
- Golden files for output validation are in `tests/golden/`.

### CI/CD & Quality
- All pull requests must pass:
  - Unit tests
  - Security scans (pip-audit, bandit)
  - Code quality checks (CodeQL)
  - Dependency review
- Replicate CI locally by following the steps in `TESTING.md`.

### Development Best Practices
- Use the provided virtual environment and dependency files.
- Follow the configuration and usage patterns in `docs/USER_GUIDE.md`.
- Use the CLI for local diagram generation and testing.
- For advanced/experimental features (AI mode, integrations), refer to the latest documentation and do not use in production.
- Always check logs and documentation for troubleshooting.

### Documentation & Help
- Refer to `README.md`, `TESTING.md`, and `docs/USER_GUIDE.md` for up-to-date instructions.
- For issues, check logs, verify configuration, and consult the GitHub repository's issues/discussions.

**Agents must always follow these practices to ensure consistency, reliability, and maintainability in development and testing for this project.**

## Key Project Commands and Arguments

### 1. Generate Architecture Diagrams
- **Script:** `tools/generate_arch_diagram.py`
- **Functionality:** Generates Mermaid, PNG, SVG, JPG, and Markdown architecture diagrams from IaC files.
- **Supported Arguments:**
  - `--changed-files <files>`: Space/newline-separated list of changed IaC files
  - `--iac-root <dir>`: Root directory to read IaC files from
  - `--direction <LR|RL|TB|BT|AUTO>`: Diagram direction override
  - `--out-md <file>`: Output Markdown file path
  - `--out-mmd <file>`: Output Mermaid file path
  - `--out-png <file>`: Output PNG file path
  - `--out-jpg <file>`: Output JPG file path
  - `--out-svg <file>`: Output SVG file path
- **Example:**
  ```bash
  python tools/generate_arch_diagram.py --changed-files examples/terraform/custom-icons-demo/main.tf --out-png artifacts/architecture-diagram.png --direction AUTO
  ```

### 2. Regenerate All Example Diagrams
- **Script:** `tools/regenerate_examples.py`
- **Functionality:** Recursively finds all example IaC files and regenerates their diagrams using the main generator.
- **Arguments:** None (auto-discovers examples)
- **Example:**
  ```bash
  python tools/regenerate_examples.py
  ```

### 3. Update GitHub Pages Images
- **Script:** `update_github_pages_images.py`
- **Functionality:** Regenerates all example diagrams and updates documentation images for GitHub Pages. Verifies icon counts and provides a summary.
- **Arguments:** None
- **Example:**
  ```bash
  python update_github_pages_images.py
  ```

### 4. Icon Library Management
- **Script:** `tools/icon_library.py`
- **Functionality:** Downloads, updates, and manages icon libraries for all cloud providers. Generates and updates icon mappings.
- **Supported Commands:**
  - `download-all [--force]`: Download all icons for all providers
  - `download-missing [<provider>] [--force]`: Download only missing/new icons (optionally for a specific provider)
  - `download <provider> [--force]`: Download all icons for a specific provider
  - `update`: Update icons
  - `mappings`: Generate icon mappings
  - `stats`: Show icon statistics
- **Example:**
  ```bash
  python tools/icon_library.py download oci
  python tools/icon_library.py download-all --force
  ```

### 5. Icon Mapping Debugging
- **Script:** `tools/debug_icon_mapping.py`
- **Functionality:** Analyzes Terraform configs and icon mappings. Identifies missing icons, mapping issues, and provides fix recommendations.
- **Arguments:** None
- **Example:**
  ```bash
  python tools/debug_icon_mapping.py
  ```

### 6. Other Utilities
- **`tools/debug_icon_loading.py`**: Test icon loading for specific services.
- **`tools/verify_icon_coverage.py`**: Verify icon coverage for services.
- **`icons/custom/generate_icons.py`**: Generate custom programmatic icons for data processing services.

**Agents should use this section as a reference for all supported project commands and their arguments.**