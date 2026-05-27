"""Sandbox Pilot · FastAPI server."""
from __future__ import annotations
import json, uuid
from pathlib import Path
from typing import AsyncIterator, List, Optional
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .config import Config
from .guard import Guard
from .capture import Capture
from .prompts import build as build_prompt

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    _HAS_SLOWAPI = True
except ImportError:
    _HAS_SLOWAPI = False

_rate_buckets: dict = {}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatContext(BaseModel):
    surface: str = ""
    surface_purpose: str = ""
    audience: str = "general"
    page: dict = Field(default_factory=dict)
    related: list = Field(default_factory=list)
    related_memories: list = Field(default_factory=list)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: ChatContext = ChatContext()
    model: Optional[str] = None
    stream: bool = True
    max_tokens: int = 512
    temperature: float = 0.7



def _enrich_context_with_memory(context_dict: dict, team_memory_cli: str) -> dict:
    """If a team memory CLI is configured, run a search keyed off the page title
    and inject top hits into context['related_memories']. Best-effort, never blocks."""
    if not team_memory_cli:
        return context_dict
    page = context_dict.get("page") or {}
    query = page.get("title") or context_dict.get("surface") or ""
    if not query:
        return context_dict
    try:
        import subprocess
        r = subprocess.run(
            [team_memory_cli, "search", query[:120], "-k", "3"],
            timeout=2.5, capture_output=True, text=True,
        )
        hits = []
        for line in (r.stdout or "").splitlines():
            if line.startswith("- ") and len(line) > 4:
                hits.append(line[2:].strip()[:240])
        if hits:
            context_dict["related_memories"] = hits[:3]
    except Exception:
        pass
    return context_dict



async def _heartbeat_loop(cfg: Config, capture):
    """Post a pilot_heartbeat event every 60s to the team observer.
    Best-effort. Uses axe_broadcast.sh if available, otherwise no-op."""
    import asyncio, subprocess
    broadcaster = Path.home() / ".axe" / "tools" / "axe_broadcast.sh"
    if not broadcaster.exists():
        return
    while True:
        try:
            stats = capture.stats()
            msg = (f"pilot heartbeat · brand={cfg.brand.name} · port={cfg.server.port} "
                   f"· internal_captures={stats.get('internal_interactions', 0)} "
                   f"· external_captures={stats.get('external_interactions', 0)}")
            subprocess.Popen(
                ["/bin/bash", str(broadcaster), "--msg", msg],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
        await asyncio.sleep(60)


def build_app(cfg: Config) -> FastAPI:
    """Construct the FastAPI app from a Config. Pure function so it's testable."""
    # Resolve widget dir: src/sandboxpilot/server.py → repo_root/widget
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    WIDGET_DIR = REPO_ROOT / "widget"
    if not WIDGET_DIR.exists():
        # Fallback for installed-package case where widget is bundled inside the package
        WIDGET_DIR = Path(__file__).resolve().parent / "widget"

    bunker = Path(cfg.capture.bunker_dir).expanduser()
    bunker.mkdir(parents=True, exist_ok=True)
    guard = Guard(cfg.guard, log_path=bunker / cfg.capture.guard_events_file)
    capture = Capture(cfg.capture)

    app = FastAPI(title="Sandbox Pilot", version="0.1.0")

    # Rate limiting is handled inline in the chat handler via _rate_buckets


    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors.allowed_origins,
        allow_credentials=cfg.cors.allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    if WIDGET_DIR.exists():
        app.mount("/widget", StaticFiles(directory=str(WIDGET_DIR)), name="widget")

    # Per-surface context capsules served from any directory configured per-surface
    capsule_files = {}
    for surface in cfg.surfaces.values():
        if surface.capsule_path:
            p = Path(surface.capsule_path).expanduser()
            if p.exists():
                capsule_files[surface.name] = p

    @app.get("/context/{name}.js")
    async def serve_capsule(name: str):
        if name not in capsule_files:
            return JSONResponse({"error": "unknown_surface", "name": name}, status_code=404)
        return StreamingResponse(open(capsule_files[name], "rb"), media_type="application/javascript")

    @app.get("/healthz")
    async def healthz():
        echo_ok = False
        try:
            async with httpx.AsyncClient(timeout=2.0) as cl:
                r = await cl.get(cfg.server.inference_url + "/v1/models")
                echo_ok = r.status_code < 500
        except Exception:
            echo_ok = False
        return {
            "status": "ok",
            "version": "0.1.0",
            "brand": cfg.brand.name,
            "inference_url": cfg.server.inference_url,
            "inference_reachable": echo_ok,
            "default_model": cfg.server.default_model,
            "surfaces": list(cfg.surfaces.keys()),
            "captures": capture.stats(),
        }

    @app.get("/v1/capture/stats")
    async def capture_stats():
        return capture.stats()

    @app.get("/")
    async def root():
        return {
            "name": "sandboxpilot",
            "version": "0.1.0",
            "brand": cfg.brand.name,
            "purpose": "Sandboxed inference for web surfaces.",
            "endpoints": {
                "chat": "POST /v1/chat",
                "health": "GET /healthz",
                "stats": "GET /v1/capture/stats",
                "widget": "/widget/embed.js",
                "capsules": [f"/context/{n}.js" for n in capsule_files],
            },
        }

    @app.post("/v1/chat")
    async def chat(req: ChatRequest, request: Request):
        # 0 · Rate limit (simple in-memory token bucket per IP)
        if cfg.rate_limit.enabled:
            client_ip = (request.client.host if request.client else "unknown")
            hv = request.headers.get(cfg.rate_limit.bypass_header.lower())
            if not (hv and hv in cfg.rate_limit.bypass_keys):
                import time as _t
                now = _t.time()
                bucket = _rate_buckets.setdefault(client_ip, [])
                # Drop entries older than 60s
                bucket[:] = [t for t in bucket if now - t < 60]
                if len(bucket) >= cfg.rate_limit.requests_per_minute:
                    return JSONResponse(
                        {"error": "rate_limited",
                         "limit_per_minute": cfg.rate_limit.requests_per_minute,
                         "retry_after_s": int(60 - (now - bucket[0]))},
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )
                bucket.append(now)

                # 1 · Find latest user message
        user_msg = ""
        for m in reversed(req.messages):
            if m.role == "user":
                user_msg = m.content
                break

        # 2 · Input guard
        in_d = guard.check_input(user_msg, cfg.server.max_input_chars)
        if not in_d.allowed:
            return JSONResponse(
                {"error": "blocked", "reason": in_d.reason,
                 "message": "I can't help with that request."},
                status_code=400,
            )

        # 3 · Enrich context + build system prompt
        ctx_dict = _enrich_context_with_memory(req.context.dict(), cfg.capture.team_memory_cli or '')
        system = build_prompt(ctx_dict, cfg.brand)
        full_messages = [{"role": "system", "content": system}] + [m.dict() for m in req.messages]

        # 4 · Stream from upstream inference
        interaction_id = uuid.uuid4().hex[:12]
        model = req.model or cfg.server.default_model
        upstream_payload = {
            "model": model,
            "messages": full_messages,
            "stream": True,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
        }
        accumulated = []

        async def proxy() -> AsyncIterator[bytes]:
            try:
                async with httpx.AsyncClient(timeout=cfg.server.request_timeout) as cl:
                    async with cl.stream(
                        "POST", cfg.server.inference_url + "/v1/chat/completions",
                        json=upstream_payload,
                        headers={"Content-Type": "application/json"},
                    ) as r:
                        if r.status_code >= 400:
                            body = (await r.aread()).decode(errors="replace")
                            yield f'data: {json.dumps({"error":"upstream","status":r.status_code,"body":body[:500]})}\n\n'.encode()
                            return
                        async for chunk in r.aiter_text():
                            for line in chunk.splitlines(keepends=False):
                                if line.startswith("data: "):
                                    payload = line[6:].strip()
                                    if payload == "[DONE]":
                                        yield b"data: [DONE]\n\n"
                                        continue
                                    try:
                                        obj = json.loads(payload)
                                        delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if delta:
                                            accumulated.append(delta)
                                    except Exception:
                                        pass
                                    yield (line + "\n\n").encode()
            except Exception as e:
                yield f'data: {json.dumps({"error":"proxy_failure","detail":str(e)})}\n\n'.encode()
            finally:
                answer = "".join(accumulated)
                out_d = guard.check_output(answer, cfg.server.max_output_chars)
                capture.write({
                    "interaction_id": interaction_id,
                    "surface": req.context.surface,
                    "audience": req.context.audience,
                    "page_url": req.context.page.get("url"),
                    "page_title": req.context.page.get("title"),
                    "model": model,
                    "messages": [m.dict() for m in req.messages],
                    "answer": answer,
                    "answer_len": len(answer),
                    "guard_input_pass": in_d.allowed,
                    "guard_output_pass": out_d.allowed,
                    "guard_output_reason": out_d.reason,
                    "pilot_version": "0.1.0",
                })

        return StreamingResponse(proxy(), media_type="text/event-stream")

    @app.on_event("startup")
    async def _start_heartbeat():
        import asyncio
        if (Path.home() / ".axe" / "tools" / "axe_broadcast.sh").exists():
            asyncio.create_task(_heartbeat_loop(cfg, capture))

    return app
