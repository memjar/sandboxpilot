"""Sandbox Pilot CLI.

  $ sandboxpilot serve [--config PATH] [--port N] [--host H]
  $ sandboxpilot health [--url URL]
  $ sandboxpilot validate --config PATH
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from . import __version__
from .config import load


def cmd_serve(args):
    import uvicorn
    from .server import build_app
    cfg = load(Path(args.config) if args.config else None)
    if args.port:
        cfg.server.port = args.port
    if args.host:
        cfg.server.host = args.host
    print(f"Sandbox Pilot v{__version__}")
    print(f"  brand:        {cfg.brand.name}")
    print(f"  config:       {cfg.config_path or '(defaults)'}")
    print(f"  inference:    {cfg.server.inference_url}")
    print(f"  default model:{cfg.server.default_model or '(unset)'}")
    print(f"  surfaces:     {', '.join(cfg.surfaces.keys()) or '(none)'}")
    print(f"  bunker:       {cfg.capture.bunker_dir}")
    print(f"  listening on  http://{cfg.server.host}:{cfg.server.port}")
    app = build_app(cfg)
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_level="info")


def cmd_health(args):
    import httpx
    url = args.url or "http://localhost:8094"
    r = httpx.get(url + "/healthz", timeout=5)
    print(json.dumps(r.json(), indent=2))


def cmd_validate(args):
    cfg = load(Path(args.config))
    print(json.dumps({
        "config_path": str(cfg.config_path) if cfg.config_path else None,
        "brand": cfg.brand.name,
        "surfaces": list(cfg.surfaces.keys()),
        "guard_patterns_brand_leak": len(cfg.guard.brand_leak_patterns),
        "guard_patterns_harmful": len(cfg.guard.harmful_patterns),
        "cors_origins": len(cfg.cors.allowed_origins),
        "rate_limit_enabled": cfg.rate_limit.enabled,
        "valid": True,
    }, indent=2))


def main():
    p = argparse.ArgumentParser(prog="sandboxpilot", description="Sandbox Pilot · sandboxed AI pilot for any web property")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("serve", help="Run the pilot HTTP server")
    s.add_argument("--config", help="Path to config TOML")
    s.add_argument("--port", type=int, help="Port override")
    s.add_argument("--host", help="Host override")
    s.set_defaults(func=cmd_serve)

    h = sub.add_parser("health", help="Probe a running pilot")
    h.add_argument("--url", help="Pilot URL (default localhost:8094)")
    h.set_defaults(func=cmd_health)

    v = sub.add_parser("validate", help="Load and validate a config file")
    v.add_argument("--config", required=True, help="Path to config TOML")
    v.set_defaults(func=cmd_validate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
