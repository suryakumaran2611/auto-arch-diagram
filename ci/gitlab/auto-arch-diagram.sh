#!/usr/bin/env bash
# Auto Architecture Diagram - GitLab CI/CD runner
#
# Generates architecture diagrams (Markdown, Mermaid, PNG, JPEG, SVG, draw.io and
# interactive HTML) for changed IaC files, then writes a dotenv report so later
# jobs and pipeline consumers can locate the generated artifacts.
#
# Normally invoked by one of the reusable GitLab templates:
#   - templates/auto-arch-diagram/template.yml        (CI/CD component)
#   - ci/gitlab/auto-arch-diagram.gitlab-ci.yml       (include: remote / project)
#
# Every option is an AUTO_ARCH_* environment variable. See docs/GITLAB_CI.md.
set -euo pipefail

log()  { printf '\033[0;34m[auto-arch-diagram]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[auto-arch-diagram] WARNING:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[0;31m[auto-arch-diagram] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

is_true() {
  case "$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TOOL_ROOT="${AUTO_ARCH_TOOL_DIR:-$(cd -- "${SCRIPT_DIR}/../.." >/dev/null 2>&1 && pwd)}"
PYTHON="${PYTHON:-python3}"

[ -f "${TOOL_ROOT}/tools/generate_arch_diagram.py" ] \
  || die "Generator not found under ${TOOL_ROOT}. Set AUTO_ARCH_TOOL_DIR to the auto-arch-diagram checkout."

command -v "${PYTHON}" >/dev/null 2>&1 \
  || die "Python interpreter '${PYTHON}' not found. Set the PYTHON environment variable."

command -v git >/dev/null 2>&1 \
  || die "git is required for change detection."

WORKSPACE="${CI_PROJECT_DIR:-$(pwd)}"
cd "${WORKSPACE}"

# ---------------------------------------------------------------------------
# Configuration (all optional unless noted)
# ---------------------------------------------------------------------------
if [ -z "${AUTO_ARCH_IAC_GLOBS:-}" ]; then
  AUTO_ARCH_IAC_GLOBS='**/*.tf
**/*.tfvars
**/*.hcl
**/*.bicep
**/*.cfn.yaml
**/*.cfn.yml
**/*.cfn.json
**/template.yaml
**/template.yml
**/Pulumi.*.yaml
**/Pulumi.*.yml
**/Pulumi.yaml
**/Pulumi.yml
**/Pulumi.*.json
**/Pulumi.*.ts
**/Pulumi.*.py
**/*.cdk.ts
**/*.cdk.py'
fi

: "${AUTO_ARCH_IAC_ROOT:=.}"
: "${AUTO_ARCH_OUT_DIR:=artifacts}"
: "${AUTO_ARCH_IMAGE_FORMATS:=png,jpg,svg}"
: "${AUTO_ARCH_DIRECTION:=AUTO}"
: "${AUTO_ARCH_RENDER_LAYOUT:=lanes}"
: "${AUTO_ARCH_RENDER_BG:=transparent}"
: "${AUTO_ARCH_EDGE_COLOR:=#4B5563}"
: "${AUTO_ARCH_EDGE_PENWIDTH:=1.3}"
: "${AUTO_ARCH_EDGE_ARROWSIZE:=0.8}"
: "${AUTO_ARCH_AI_BACKEND:=auto}"

export AUTO_ARCH_IAC_ROOT AUTO_ARCH_IAC_GLOBS
export AUTO_ARCH_DIRECTION AUTO_ARCH_RENDER_LAYOUT AUTO_ARCH_RENDER_BG
export AUTO_ARCH_EDGE_COLOR AUTO_ARCH_EDGE_PENWIDTH AUTO_ARCH_EDGE_ARROWSIZE
export PYTHONPATH="${TOOL_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
for optional_var in AUTO_ARCH_AI_ITERATIONS GEMINI_MODEL OPENROUTER_MODEL; do
  if [ -n "${!optional_var:-}" ]; then
    export "${optional_var?}"
  fi
done

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/auto-arch-diagram.XXXXXX")"
cleanup() { rm -rf "${TMP_DIR}"; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
resolve_diff_base() {
  local candidate=""

  if [ -n "${CI_MERGE_REQUEST_DIFF_BASE_SHA:-}" ]; then
    candidate="${CI_MERGE_REQUEST_DIFF_BASE_SHA}"
  elif [ -n "${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-}" ] \
    && git rev-parse --verify --quiet "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}^{commit}" >/dev/null; then
    candidate="$(git merge-base HEAD "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME}" 2>/dev/null || true)"
  elif [ -n "${CI_COMMIT_BEFORE_SHA:-}" ] \
    && [ "${CI_COMMIT_BEFORE_SHA}" != "0000000000000000000000000000000000000000" ]; then
    candidate="${CI_COMMIT_BEFORE_SHA}"
  fi

  if [ -n "${candidate}" ] && git cat-file -e "${candidate}^{commit}" 2>/dev/null; then
    printf '%s' "${candidate}"
  fi
}

write_dotenv() {
  local has_changes="$1"
  local dotenv="${AUTO_ARCH_OUT_DIR}/ci.env"

  {
    echo "AUTO_ARCH_HAS_CHANGES=${has_changes}"
    echo "AUTO_ARCH_OUT_DIR=${AUTO_ARCH_OUT_DIR}"
    echo "AUTO_ARCH_SUMMARY_FILE=${SUMMARY_FILE}"
    echo "AUTO_ARCH_CHANGED_FILES=${CHANGED_IAC_FILES:-}"
    if [ -n "${OUT_MD:-}" ]; then echo "AUTO_ARCH_MD=${OUT_MD}"; fi
    if [ -n "${OUT_MMD:-}" ]; then echo "AUTO_ARCH_MMD=${OUT_MMD}"; fi
    if [ -n "${OUT_PNG:-}" ]; then echo "AUTO_ARCH_PNG=${OUT_PNG}"; fi
    if [ -n "${OUT_JPG:-}" ]; then echo "AUTO_ARCH_JPG=${OUT_JPG}"; fi
    if [ -n "${OUT_SVG:-}" ]; then echo "AUTO_ARCH_SVG=${OUT_SVG}"; fi
    if [ -n "${OUT_DRAWIO:-}" ]; then echo "AUTO_ARCH_DRAWIO=${OUT_DRAWIO}"; fi
    if [ -n "${OUT_HTML:-}" ]; then echo "AUTO_ARCH_HTML=${OUT_HTML}"; fi
  } > "${dotenv}"

  log "Wrote dotenv report: ${dotenv}"
}

mkdir -p "${AUTO_ARCH_OUT_DIR}"
SUMMARY_FILE="${AUTO_ARCH_OUT_DIR}/gitlab-ci-summary.md"
CHANGED_IAC_FILES=""

# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------
raw_list="${TMP_DIR}/raw-files"
explicit_list=false
full_scan=false
diff_base=""

if is_true "${AUTO_ARCH_FORCE_FULL:-false}"; then
  log "force_full enabled - scanning every tracked IaC file"
  git ls-files > "${raw_list}"
  full_scan=true
elif [ -n "${AUTO_ARCH_CHANGED_FILES:-}" ]; then
  log "Using file list supplied through AUTO_ARCH_CHANGED_FILES"
  printf '%s' "${AUTO_ARCH_CHANGED_FILES}" \
    | tr ',;' '\n\n' \
    | tr -s '[:space:]' '\n' \
    | sed '/^$/d' > "${raw_list}"
  explicit_list=true
else
  diff_base="$(resolve_diff_base)"
  if [ -n "${diff_base}" ]; then
    log "Detecting IaC changes against ${diff_base}"
    git diff --name-only --diff-filter=ACMR "${diff_base}...HEAD" > "${raw_list}" 2>/dev/null || true
  else
    warn "No git diff base available (shallow clone or new branch) - scanning all tracked IaC files"
    git ls-files > "${raw_list}"
    full_scan=true
  fi
fi

if [ "${explicit_list}" = true ]; then
  filter_mode="strip"
else
  filter_mode="filter"
fi

selected="${TMP_DIR}/selected-files"
"${PYTHON}" - "${raw_list}" "${selected}" "${filter_mode}" <<'PY'
import fnmatch
import os
import sys

source, destination, mode = sys.argv[1], sys.argv[2], sys.argv[3]

root = (os.environ.get("AUTO_ARCH_IAC_ROOT") or ".").replace("\\", "/").strip()
root = root.lstrip("./").strip("/")
if root == ".":
    root = ""

patterns = []
for raw_pattern in (os.environ.get("AUTO_ARCH_IAC_GLOBS") or "").splitlines():
    pattern = raw_pattern.strip()
    if not pattern:
        continue
    patterns.append(pattern.lower())
    if pattern.startswith("**/"):
        patterns.append(pattern[3:].lower())

selected = []
seen = set()

with open(source, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        path = line.strip().replace("\\", "/")
        if not path:
            continue
        path = path.lstrip("./")
        if not path:
            continue
        if root:
            if path != root and not path.startswith(root + "/"):
                continue
            if path == root:
                continue
            path = path[len(root) + 1:]

        if mode == "filter":
            lowered = path.lower()
            if not any(fnmatch.fnmatch(lowered, pattern) for pattern in patterns):
                continue

        if path not in seen:
            seen.add(path)
            selected.append(path)

with open(destination, "w", encoding="utf-8") as handle:
    handle.write("\n".join(selected))

print(f"{len(selected)} IaC file(s) selected")
PY

file_count=""
CHANGED_IAC_FILES=""
if [ -n "${AUTO_ARCH_SOURCE:-}" ]; then
  log "AUTO_ARCH_SOURCE is set - the generator will clone and scan ${AUTO_ARCH_SOURCE}"
  CHANGE_SUMMARY="the remote source \`${AUTO_ARCH_SOURCE}\`"
  export CHANGED_IAC_FILES
else
  file_count="$(grep -c . "${selected}" 2>/dev/null || true)"
  file_count="${file_count:-0}"

  if [ "${file_count}" = "0" ]; then
    log "No IaC changes detected - skipping diagram generation"
    cat > "${SUMMARY_FILE}" <<EOF
# Architecture diagram

No IaC files matched this pipeline's change set, so no diagram was generated.

- IaC root: \`${AUTO_ARCH_IAC_ROOT}\`
- Diff base: \`${diff_base:-none (full scan)}\`
- Pipeline: ${CI_PIPELINE_URL:-local run}
EOF
    write_dotenv false
    exit 0
  fi

  CHANGED_IAC_FILES="$(tr '\n' ' ' < "${selected}" | sed 's/[[:space:]]*$//')"
  export CHANGED_IAC_FILES
  CHANGE_SUMMARY="${file_count} changed IaC file(s)"

  log "Changed IaC files (${file_count}):"
  printf '%s\n' "${CHANGED_IAC_FILES}" | tr ' ' '\n' | sed '/^$/d; s/^/  - /'
fi

# ---------------------------------------------------------------------------
# Resolve output paths
# ---------------------------------------------------------------------------
formats="$(printf '%s' "${AUTO_ARCH_IMAGE_FORMATS}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
want_png=false
want_jpg=false
want_svg=false
case ",${formats}," in *,png,*) want_png=true ;; esac
case ",${formats}," in *,jpg,*) want_jpg=true ;; esac
case ",${formats}," in *,svg,*) want_svg=true ;; esac

OUT_MD="${AUTO_ARCH_OUT_MD:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.md}"
OUT_MMD="${AUTO_ARCH_OUT_MMD:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.mmd}"
OUT_PNG=""
OUT_JPG=""
OUT_SVG=""
if [ "${want_png}" = true ]; then OUT_PNG="${AUTO_ARCH_OUT_PNG:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.png}"; fi
if [ "${want_jpg}" = true ]; then OUT_JPG="${AUTO_ARCH_OUT_JPG:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.jpg}"; fi
if [ "${want_svg}" = true ]; then OUT_SVG="${AUTO_ARCH_OUT_SVG:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.svg}"; fi

OUT_DRAWIO="${AUTO_ARCH_OUT_DRAWIO:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.drawio}"
OUT_HTML="${AUTO_ARCH_OUT_HTML:-${AUTO_ARCH_OUT_DIR}/architecture-diagram.html}"
if [ "${OUT_DRAWIO}" = "__disabled__" ]; then OUT_DRAWIO=""; fi
if [ "${OUT_HTML}" = "__disabled__" ]; then OUT_HTML=""; fi

mkdir -p "$(dirname "${OUT_MD}")" "$(dirname "${OUT_MMD}")"

args=(
  --changed-files "${CHANGED_IAC_FILES}"
  --iac-root "${AUTO_ARCH_IAC_ROOT}"
  --out-md "${OUT_MD}"
  --out-mmd "${OUT_MMD}"
  --direction "${AUTO_ARCH_DIRECTION}"
)
if [ -n "${OUT_PNG}" ]; then args+=(--out-png "${OUT_PNG}"); fi
if [ -n "${OUT_JPG}" ]; then args+=(--out-jpg "${OUT_JPG}"); fi
if [ -n "${OUT_SVG}" ]; then args+=(--out-svg "${OUT_SVG}"); fi
if [ -n "${OUT_DRAWIO}" ]; then args+=(--out-drawio "${OUT_DRAWIO}"); fi
if [ -n "${OUT_HTML}" ]; then args+=(--out-html "${OUT_HTML}"); fi

if [ -n "${AUTO_ARCH_FONTSIZE:-}" ]; then
  if [[ "${AUTO_ARCH_FONTSIZE}" =~ ^[0-9]+$ ]]; then
    args+=(--fontsize "${AUTO_ARCH_FONTSIZE}")
  else
    warn "Ignoring non-numeric AUTO_ARCH_FONTSIZE='${AUTO_ARCH_FONTSIZE}'"
  fi
fi
if [ -n "${AUTO_ARCH_ICONSIZE:-}" ]; then
  if [[ "${AUTO_ARCH_ICONSIZE}" =~ ^[0-9]+$ ]]; then
    args+=(--iconsize "${AUTO_ARCH_ICONSIZE}")
  else
    warn "Ignoring non-numeric AUTO_ARCH_ICONSIZE='${AUTO_ARCH_ICONSIZE}'"
  fi
fi
if [ -n "${AUTO_ARCH_RENDER_ENGINE:-}" ]; then
  case "${AUTO_ARCH_RENDER_ENGINE}" in
    auto|neato|dot) args+=(--render-engine "${AUTO_ARCH_RENDER_ENGINE}") ;;
    *) warn "Ignoring unsupported AUTO_ARCH_RENDER_ENGINE='${AUTO_ARCH_RENDER_ENGINE}' (auto|neato|dot)" ;;
  esac
fi
if is_true "${AUTO_ARCH_SIMPLIFIED:-false}"; then
  args+=(--simplified)
fi
if is_true "${AUTO_ARCH_EXPAND_BADGES:-false}"; then
  args+=(--expand-badges)
fi
if is_true "${AUTO_ARCH_NO_CONSOLIDATE:-false}"; then
  args+=(--no-consolidate)
fi
if [ -n "${AUTO_ARCH_PLANFILE:-}" ]; then args+=(--planfile "${AUTO_ARCH_PLANFILE}"); fi
if [ -n "${AUTO_ARCH_GRAPHFILE:-}" ]; then args+=(--graphfile "${AUTO_ARCH_GRAPHFILE}"); fi
if [ -n "${AUTO_ARCH_VARFILE:-}" ]; then
  while IFS= read -r varfile; do
    if [ -n "${varfile}" ]; then args+=(--varfile "${varfile}"); fi
  done < <(printf '%s' "${AUTO_ARCH_VARFILE}" | tr ',;' '\n\n' | tr -s '[:space:]' '\n')
fi
if [ -n "${AUTO_ARCH_WORKSPACE:-}" ]; then
  args+=(--workspace "${AUTO_ARCH_WORKSPACE}")
fi
if [ -n "${AUTO_ARCH_SOURCE:-}" ]; then
  args+=(--source "${AUTO_ARCH_SOURCE}")
fi
if [ -n "${AUTO_ARCH_ANNOTATE:-}" ]; then args+=(--annotate "${AUTO_ARCH_ANNOTATE}"); fi

if is_true "${AUTO_ARCH_AI_ENHANCE:-false}"; then
  log "AI enhancement enabled via backend '${AUTO_ARCH_AI_BACKEND}'"
  args+=(--ai-enhance --ai-backend "${AUTO_ARCH_AI_BACKEND}")
  if [ -n "${AUTO_ARCH_GEMINI_MODEL:-}" ]; then args+=(--gemini-model "${AUTO_ARCH_GEMINI_MODEL}"); fi
  if [ -n "${AUTO_ARCH_OPENROUTER_MODEL:-}" ]; then args+=(--openrouter-model "${AUTO_ARCH_OPENROUTER_MODEL}"); fi
  if [ "${AUTO_ARCH_AI_BACKEND}" = "ollama" ] && [ -n "${AUTO_ARCH_OLLAMA_MODEL:-}" ]; then
    args+=(--ollama-model "${AUTO_ARCH_OLLAMA_MODEL}")
  fi
fi

log "Output directory: ${AUTO_ARCH_OUT_DIR}"
log "Formats: md, mmd${OUT_PNG:+, png}${OUT_JPG:+, jpg}${OUT_SVG:+, svg}${OUT_DRAWIO:+, drawio}${OUT_HTML:+, html}"

"${PYTHON}" "${TOOL_ROOT}/tools/generate_arch_diagram.py" "${args[@]}"

# ---------------------------------------------------------------------------
# Validate and annotate outputs
# ---------------------------------------------------------------------------
[ -f "${OUT_MD}" ] || die "Markdown output missing: ${OUT_MD}"
[ -f "${OUT_MMD}" ] || die "Mermaid output missing: ${OUT_MMD}"
[ -s "${OUT_MD}" ] || die "Markdown output is empty: ${OUT_MD}"

pipeline_url="${CI_PIPELINE_URL:-}"
if [ -n "${pipeline_url}" ]; then
  {
    echo ""
    echo "Rendered PNG/JPEG/SVG/Draw.io/HTML are attached to this GitLab pipeline as job artifacts."
    echo ""
    echo "Pipeline: ${pipeline_url}"
  } >> "${OUT_MD}"
fi

for generated in "${OUT_PNG}" "${OUT_JPG}" "${OUT_SVG}" "${OUT_DRAWIO}" "${OUT_HTML}"; do
  if [ -n "${generated}" ] && [ -f "${generated}" ]; then
    log "Generated $(basename "${generated}") -> ${generated}"
  fi
done

cat > "${SUMMARY_FILE}" <<EOF
# Architecture diagram

Generated $(date -u +"%Y-%m-%dT%H:%M:%SZ") from ${CHANGE_SUMMARY}.

- IaC root: \`${AUTO_ARCH_IAC_ROOT}\`
- Direction: \`${AUTO_ARCH_DIRECTION}\`
- Pipeline: ${pipeline_url:-local run}

## Outputs

$(for generated in "${OUT_MD}" "${OUT_MMD}" "${OUT_PNG}" "${OUT_JPG}" "${OUT_SVG}" "${OUT_DRAWIO}" "${OUT_HTML}"; do
  if [ -n "${generated}" ]; then echo "- \`${generated}\`"; fi
done)
EOF

write_dotenv true
log "Diagram generation complete"
