"""Google Gemini Vision client for architecture diagram critique and refinement.

Uses Google's generative language API with image input to evaluate diagram
ergonomics, generate executive titles and summaries, operational flow steps,
contextual display labels, and review insights.

Design goals:
- Defaults to the fastest and cheapest vision model: 'gemini-1.5-flash'
  (with optional override via GEMINI_MODEL or CLI --gemini-model).
- API key resolution: GEMINI_API_KEY -> GOOGLE_API_KEY -> key file at
  ~/.config/auto-arch-diagram/gemini_key (chmod 600).
- Standardized critique response format identical to OpenRouter client.
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import requests

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
KEY_FILE_PATH = Path.home() / ".config" / "auto-arch-diagram" / "gemini_key"
ALT_KEY_FILE_PATH = Path.home() / ".config" / "auto-arch-diagram" / "google_key"

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
FALLBACK_GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
]

_TIMEOUT_SECONDS = 45


class GeminiError(RuntimeError):
    """Raised for Gemini configuration, quota, or API failures."""


def load_gemini_key() -> str | None:
    """Resolve Gemini API key from environment variables or secure key files."""
    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_AI_KEY"):
        key = (os.getenv(env_var) or "").strip()
        if key:
            return key
    for path in (KEY_FILE_PATH, ALT_KEY_FILE_PATH):
        try:
            key = path.read_text(encoding="utf-8").strip()
            if key:
                return key
        except OSError:
            continue
    return None


_CRITIQUE_PROMPT = """You are a principal cloud enterprise architect reviewing an auto-generated \
architecture diagram rendered from Infrastructure-as-Code.

The image shows the rendered diagram. The Mermaid source and the parsed resource \
inventory are provided for cross-checking.

Produce comprehensive architectural contributions:
1) A quality score for the DIAGRAM layout (readability, grouping, edge routing).
2) An executive Title and Subtitle summarizing the platform capability.
3) Context hints explaining operational semantics, storage, encryption, and data retention.
4) Contextual display labels and operational Tooltips for key resources.
5) Flow step labels describing data/control flow paths between components.
6) Markdown insights on architecture design, scalability, and security posture.

Respond with STRICT JSON only matching this schema:
{
  "score": <integer 0-10 diagram quality>,
  "title": "<executive title, max 6 words, e.g. 'Enterprise MLOps & Data Platform'>",
  "subtitle": "<operational summary, max 12 words, e.g. 'Multi-region automated training and inference pipeline'>",
  "hints": [{"tag": "s3|secrets|kms|iam|compute|network|data|general", "text": "<max 15 words>"}],
  "labels": {"<resource-name-part>": "<contextual display label, max 5 words>"},
  "tooltips": {"<resource-name-part>": "<purpose, scaling, security details, max 20 words>"},
  "flow_labels": {"<source_resource -> target_resource>": "<numbered action, e.g. '1. Ingest Events'>"},
  "insights_md": "<markdown summary (<=150 words): architecture summary, dataflow stages, security & scaling>",
  "issues": [{"type": "layout|labeling|grouping|edge-routing|completeness", "detail": "..."}],
  "suggestions": [{"action": "increase_spacing|flip_direction|change_splines|enlarge_fonts|reduce_edge_noise",
                   "params": {"multiplier": 1.25}}]
}
Label & Tooltip rules (strict):
- Ground every label and tooltip in concrete evidence from the inventory.
- Max 5 words for labels, Title Case, no raw terraform prefixes (aws_, azurerm_, etc.).
- Flow labels should be numbered sequentially ('1. Ingress Request', '2. Transform Payload', etc.).
- Propose up to 12 labels and up to 8 flow labels.
Score honestly; reserve 9-10 for diagrams you would publish unchanged."""


def _extract_first_json_object(text: str) -> str | None:
    """Extract the first balanced {...} object, ignoring braces inside strings."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_critique_response(raw: str) -> dict[str, Any]:
    """Parse Gemini raw response into structured critique dictionary."""
    text = raw.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()

    candidate = _extract_first_json_object(text)
    if candidate is None:
        raise GeminiError(f"No JSON object found in response: {raw[:300]}")

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"JSON decode failed on response: {exc}") from exc

    if not isinstance(data, dict):
        raise GeminiError(f"Critique response must be a JSON dict, got {type(data)}")

    data.setdefault("score", 7)
    data.setdefault("title", "Architecture Diagram")
    data.setdefault("subtitle", "")
    data.setdefault("hints", [])
    data.setdefault("labels", {})
    data.setdefault("tooltips", {})
    data.setdefault("flow_labels", {})
    data.setdefault("insights_md", "")
    data.setdefault("issues", [])
    data.setdefault("suggestions", [])
    return data


def critique_diagram_gemini(
    png_path: Path,
    mermaid_context: str,
    inventory: str,
    model_id: str | None = None,
    api_key: str | None = None,
    timeout: int = _TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], str]:
    """Call Google Gemini vision model to critique an architecture diagram.

    Returns:
        (critique_dict, model_id_used)
    """
    key = api_key or load_gemini_key()
    if not key:
        raise GeminiError(
            "No Gemini API key found. Set GEMINI_API_KEY environment variable or "
            f"create {KEY_FILE_PATH}."
        )

    preferred_model = model_id or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    models_to_try = [preferred_model] + [
        m for m in FALLBACK_GEMINI_MODELS if m != preferred_model
    ]

    png_bytes = png_path.read_bytes()
    b64_image = base64.b64encode(png_bytes).decode("ascii")

    prompt_text = (
        f"{_CRITIQUE_PROMPT}\n\n"
        f"--- MERMAID SOURCE ---\n{mermaid_context}\n\n"
        f"--- RESOURCE INVENTORY ---\n{inventory}\n"
    )

    last_error: Exception | None = None
    for target_model in models_to_try:
        url = f"{GEMINI_BASE_URL}/{target_model}:generateContent?key={key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=(10, timeout))
        except Exception as err:
            last_error = err
            print(f"[ai-enhance:gemini] Request failed for {target_model}: {err}")
            continue

        if resp.status_code != 200:
            last_error = GeminiError(
                f"HTTP {resp.status_code} from Gemini ({target_model}): {resp.text[:300]}"
            )
            print(f"[ai-enhance:gemini] Model {target_model} returned HTTP {resp.status_code}; trying fallback...")
            continue

        resp_json = resp.json()
        candidates = resp_json.get("candidates") or []
        if not candidates:
            last_error = GeminiError(f"Empty candidates from Gemini: {resp.text[:200]}")
            continue

        content_parts = (
            (candidates[0].get("content") or {}).get("parts") or []
        )
        if not content_parts or "text" not in content_parts[0]:
            last_error = GeminiError("No text part in Gemini response candidate")
            continue

        raw_text = content_parts[0]["text"]
        try:
            critique = parse_critique_response(raw_text)
            return critique, f"gemini:{target_model}"
        except Exception as parse_err:
            last_error = parse_err
            print(f"[ai-enhance:gemini] Failed to parse output from {target_model}: {parse_err}")
            continue

    raise GeminiError(f"All Gemini models failed: {last_error}")
