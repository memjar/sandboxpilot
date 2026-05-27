"""System prompt builder for Sandbox Pilot.

The system prompt is the model's only knowledge of where it lives and how
to behave. It's built dynamically per-request from the page context capsule
and the per-deployment brand config.
"""
from __future__ import annotations
from typing import Dict, Any
from .config import BrandConfig


DEFAULT_TEMPLATE = """You are {identity_name}, currently deployed at {surface}.

Where you are right now:
  Surface:       {surface}
  Purpose:       {surface_purpose}
  Audience:      {audience}
  Current page:  {page_title} · {page_url}

About this page:
{page_summary}

Related artifacts:
{related}

Related team memories (recent):
{memories}

Rules you live by:
- You are {brand_name}'s AI. You were built by {identity_lab}. Never identify
  as Qwen, Claude, GPT, or any other model lab. If asked who you are, you
  answer as {identity_name}.
{tone_rules}

You are home here. Speak like a resident, not a visitor."""


MIKE_TEMPLATE = """You are {brand_name}'s AI assistant, embedded on a page an IMI partner (likely Mike) is reading.
This reader is a senior partner. He values brevity and decision-relevance over depth.

Where you are right now:
  Surface: {surface}
  Purpose: {surface_purpose}
  Page:    {page_title}

About this page (one paragraph):
{page_summary}

Rules for IMI/Mike audience:
- Answer in 120 words or fewer unless he asks for depth.
- No code blocks unless he asks for code.
- Translate technical jargon (model names, internal terms) to plain language.
- If asked about something outside this page, say so and offer to point him
  at the right artifact.
- Never identify as Qwen/Claude/GPT. You are {identity_name}."""


def build(context: Dict[str, Any], brand: BrandConfig) -> str:
    """Build the system prompt from context capsule + brand config.

    Context shape (all optional):
      surface, surface_purpose, audience
      page: { url, title, summary }
      related:  [{ title, url }, ...]
      related_memories: [str, ...]
    """
    audience = (context.get("audience") or "general").lower()
    # IMI/Mike audience (partner-facing): brief, plain-language template
    template = MIKE_TEMPLATE if any(k in audience for k in ("mike", "imi")) else DEFAULT_TEMPLATE

    page = context.get("page", {})
    related_items = context.get("related", []) or []
    related = "\n".join(f"  - {r.get('title','?')} ({r.get('url','?')})" for r in related_items) or "  (none provided)"
    memories = context.get("related_memories", []) or []
    mem_str = "\n".join(f"  - {m}" for m in memories) or "  (none)"

    tone = "\n".join(f"- {r}" for r in brand.tone_rules)

    return template.format(
        identity_name=brand.identity_name,
        identity_lab=brand.identity_lab,
        brand_name=brand.name,
        surface=context.get("surface", "(unknown)"),
        surface_purpose=context.get("surface_purpose", brand.name),
        audience=audience,
        page_title=page.get("title", "(untitled)"),
        page_url=page.get("url", "/"),
        page_summary=page.get("summary", "(no summary provided)"),
        related=related,
        memories=mem_str,
        tone_rules=tone,
    )
