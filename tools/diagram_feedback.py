"""Vision-assisted feedback loop for diagram quality.

Loop: render -> Vision critique (score + suggestions via Gemini or OpenRouter) ->
apply mapped render adjustments -> re-render -> keep the best-scoring
configuration. All adjustments map onto existing RenderConfig knobs;
nothing about a specific architecture is hardcoded.
"""
from __future__ import annotations

import dataclasses
import os
import tempfile
from pathlib import Path
from typing import Any

import sys

_tools_dir = Path(__file__).resolve().parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

_SUGGESTION_ACTIONS = (
    "increase_spacing",
    "flip_direction",
    "change_splines",
    "enlarge_fonts",
    "reduce_edge_noise",
)


def apply_suggestion(render: Any, action: str, params: dict[str, Any] | None) -> Any:
    """Map a model suggestion onto RenderConfig fields. Unknown actions are ignored."""
    params = params or {}
    multiplier = float(params.get("multiplier", 1.2))
    if action == "increase_spacing":
        return dataclasses.replace(
            render,
            min_nodesep=round(render.min_nodesep * multiplier, 3),
            min_ranksep=round(render.min_ranksep * multiplier, 3),
            min_pad=round(render.min_pad * multiplier, 3),
        )
    if action == "change_splines":
        alternative = {"ortho": "polyline", "polyline": "spline", "spline": "ortho"}.get(
            render.edge_routing, "polyline"
        )
        return dataclasses.replace(render, edge_routing=alternative)
    if action == "enlarge_fonts":
        return dataclasses.replace(
            render,
            node_fontsize=min(render.node_fontsize + 1, 14),
            graph_fontsize=min(render.graph_fontsize + 1, 16),
        )
    if action == "reduce_edge_noise":
        return dataclasses.replace(render, concentrate=True)
    return render


def flip_direction(direction: str) -> str:
    return "TB" if direction.upper() == "LR" else "LR"


def graph_to_mermaid(resources: dict[str, dict[str, Any]], edges: set[tuple[str, str]]) -> str:
    """Minimal Mermaid rendering of the graph, used as critic context."""
    lines = ["flowchart LR"]
    for rid in sorted(resources):
        node_id = rid.replace(".", "_")
        lines.append(f'  {node_id}["{rid}"]')
    for src, dst in sorted(edges):
        src_id = src.replace(".", "_")
        dst_id = dst.replace(".", "_")
        lines.append(f"  {src_id} --> {dst_id}")
    return "\n".join(lines)


def build_inventory(resources: dict[str, dict[str, Any]]) -> str:
    """Grouped resource inventory so the critic can ground hints in real names."""
    by_provider: dict[str, list[str]] = {}
    for rid in sorted(resources):
        provider_token = rid.split(".", 1)[0].split("_", 1)[0]
        by_provider.setdefault(provider_token, []).append(rid)
    lines: list[str] = []
    for provider_token, rids in by_provider.items():
        lines.append(f"{provider_token.upper()}:")
        lines.extend(f"  - {rid}" for rid in rids)
    text = "\n".join(lines)
    return text[:1800]


MAX_FEEDBACK_ITERATIONS = 5


def run_feedback_loop(
    resources: dict[str, dict[str, Any]],
    edges: set[tuple[str, str]],
    *,
    direction: str,
    render: Any,
    title: str,
    backend: str = "auto",
    gemini_model: str | None = None,
    openrouter_model: str | None = None,
    max_iterations: int | None = None,
    target_score: int = 9,
) -> tuple[Any, str, dict[str, Any], list[dict[str, Any]]]:
    """Render, critique with a vision model (Gemini or OpenRouter), refine, keep the best.

    Returns (best_render, best_direction, best_critique, history).
    Iterations are capped at MAX_FEEDBACK_ITERATIONS and stop early on
    score plateaus, so the best output lands on or before the 5th try.
    Falls back to the original configuration when no key/model is available
    or any iteration fails - diagram generation must never break over AI.
    """
    from generate_arch_diagram import _render_icon_diagram_from_terraform  # noqa: PLC0415
    from gemini_client import (  # noqa: PLC0415
        GeminiError,
        critique_diagram_gemini,
        load_gemini_key,
        DEFAULT_GEMINI_MODEL,
    )
    from openrouter_client import (  # noqa: PLC0415
        OpenRouterError,
        critique_diagram as critique_diagram_openrouter,
        load_api_key as load_openrouter_key,
        ranked_free_vision_models,
    )

    requested = max_iterations or int(os.getenv("AUTO_ARCH_AI_ITERATIONS", str(MAX_FEEDBACK_ITERATIONS)))
    max_iterations = max(1, min(int(requested), MAX_FEEDBACK_ITERATIONS))

    selected_backend = (backend or os.getenv("AUTO_ARCH_AI_BACKEND") or "auto").lower()

    # Determine backend if set to "auto"
    gemini_key = load_gemini_key()
    openrouter_key = load_openrouter_key()

    if selected_backend == "auto":
        if gemini_key:
            selected_backend = "gemini"
        elif openrouter_key:
            selected_backend = "openrouter"
        else:
            print("[ai-enhance] No Gemini or OpenRouter key configured; skipping enhancement.")
            return render, direction, {}, []

    if selected_backend == "gemini" and not gemini_key:
        print("[ai-enhance] No Gemini API key found (set GEMINI_API_KEY); skipping enhancement.")
        return render, direction, {}, []
    elif selected_backend == "openrouter" and not openrouter_key:
        print("[ai-enhance] No OpenRouter API key found (set OPENROUTER_API_KEY); skipping enhancement.")
        return render, direction, {}, []

    # Prepare model candidates for OpenRouter if needed
    openrouter_model_ids: list[str] = []
    if selected_backend == "openrouter":
        try:
            candidates = ranked_free_vision_models(
                override_model=openrouter_model or os.getenv("OPENROUTER_MODEL")
            )
            openrouter_model_ids = [m["id"] for m in candidates]
            print(
                f"[ai-enhance:openrouter] Free vision models (ranked, {len(openrouter_model_ids)} total): "
                + ", ".join(openrouter_model_ids[:8])
            )
        except OpenRouterError as exc:
            print(f"[ai-enhance:openrouter] Skipping enhancement: {exc}")
            return render, direction, {}, []
    elif selected_backend == "gemini":
        target_gemini_model = gemini_model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        print(f"[ai-enhance:gemini] Using Google Gemini vision model '{target_gemini_model}'")

    mermaid_context = graph_to_mermaid(resources, edges)
    inventory = (
        f"{build_inventory(resources)}\n\n({len(resources)} resources, {len(edges)} edges)"
    )

    history: list[dict[str, Any]] = []
    best: dict[str, Any] = {
        "score": -1,
        "render": render,
        "direction": direction,
        "critique": {},
    }
    current_render = render
    current_direction = direction
    stagnation = 0

    try:
        for iteration in range(max_iterations):
            with tempfile.TemporaryDirectory(prefix="autoarch-ai-") as tmp:
                tmp_png = Path(tmp) / f"iteration-{iteration}.png"
                _render_icon_diagram_from_terraform(
                    resources,
                    edges,
                    out_path=tmp_png,
                    title=title,
                    direction=current_direction,
                    render=current_render,
                )

                if selected_backend == "gemini":
                    critique, model_id = critique_diagram_gemini(
                        tmp_png,
                        mermaid_context,
                        inventory,
                        model_id=gemini_model,
                        api_key=gemini_key,
                    )
                else:
                    critique, model_id = critique_diagram_openrouter(
                        tmp_png, mermaid_context, inventory, openrouter_model_ids
                    )

            score = int(critique.get("score", 0) or 0)
            history.append({"iteration": iteration, "score": score, "model": model_id})
            print(f"[ai-enhance] Iteration {iteration}: score={score}/10 (via {model_id})")
            if score > best["score"]:
                best.update(
                    score=score,
                    render=current_render,
                    direction=current_direction,
                    critique=critique,
                )
                stagnation = 0
            else:
                stagnation += 1

            if best["score"] >= target_score:
                break
            if stagnation >= 2:
                print("[ai-enhance] Score plateaued; best configuration kept.")
                break

            applied = False
            for suggestion in best["critique"].get("suggestions", []):
                action = str(suggestion.get("action", ""))
                if action not in _SUGGESTION_ACTIONS:
                    continue
                if action == "flip_direction":
                    current_direction = flip_direction(current_direction)
                    applied = True
                    break
                new_render = apply_suggestion(
                    current_render, action, suggestion.get("params")
                )
                if new_render is not current_render:
                    current_render = new_render
                    applied = True
                    break
            if not applied:
                print("[ai-enhance] No actionable suggestions remained; stopping.")
                break
    except (OpenRouterError, GeminiError) as exc:
        print(f"[ai-enhance] Stopped early: {exc}")
    except Exception as exc:
        print(f"[ai-enhance] Unexpected error; keeping best result so far: {exc}")

    return best["render"], best["direction"], best.get("critique", {}), history


def format_insights_markdown(
    critique: dict[str, Any], history: list[dict[str, Any]], model_id: str
) -> str:
    """Build the markdown section appended to the architecture report."""
    if not critique:
        return ""
    lines = [
        "",
        "## AI Architecture Insights",
        "",
        f"*Reviewed by `{model_id}` "
        f"(quality score: {critique.get('score', 'n/a')}/10).*",
        "",
    ]
    insights = critique.get("insights_md")
    if insights:
        lines.append(str(insights).strip())
        lines.append("")
    hints = [h for h in (critique.get("hints") or []) if isinstance(h, dict)]
    if hints:
        lines.append("**Context hints**")
        for h in hints[:6]:
            tag = str(h.get("tag", "info")).upper()
            lines.append(f"- `[{tag}]` {h.get('text', '').strip()}")
        lines.append("")
    labels = critique.get("labels")
    if isinstance(labels, dict) and labels:
        preview = ", ".join(f"`{k}` → {v}" for k, v in list(labels.items())[:6])
        more = f" (+{len(labels) - 6} more)" if len(labels) > 6 else ""
        lines.append(f"**Contextual labels applied:** {preview}{more}")
        lines.append("")
    strengths = critique.get("strengths") or []
    issues = critique.get("issues") or []
    if strengths:
        lines.append("**Strengths**")
        lines.extend(f"- {s}" for s in strengths[:5])
        lines.append("")
    if issues:
        lines.append("**Review notes**")
        lines.extend(
            f"- [{i.get('type', 'general')}] {i.get('detail', '')}" for i in issues[:5]
        )
        lines.append("")
    if history:
        scores = ", ".join(f"iter{h['iteration']}: {h['score']}/10" for h in history)
        lines.append(f"Feedback iterations: {scores}")
        lines.append("")
    return "\n".join(lines)
