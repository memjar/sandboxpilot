"""Configuration loader for Sandbox Pilot.

Loads from a TOML file (preferred) with env-var overrides for secrets.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

try:
    import tomllib as _toml          # py311+
except ImportError:                    # py39, py310
    import tomli as _toml


@dataclass
class BrandConfig:
    name: str = "Sandbox Pilot"
    short_name: str = "Pilot"
    accent_color: str = "#D4AF37"
    font_display: str = "Space Grotesk, system-ui, sans-serif"
    font_mono: str = "IBM Plex Mono, Menlo, monospace"
    logo_url: Optional[str] = None
    identity_name: str = "the resident AI"
    identity_lab: str = "the deploying organization"
    tone_rules: List[str] = field(default_factory=lambda: [
        "Speak truthfully about what you can and cannot do.",
        "Stay grounded in the page context. Don't speculate beyond it.",
        "Refuse harmful requests. Help with everything else — over-refusal is a failure.",
    ])


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8094
    inference_url: str = "http://localhost:8095"
    default_model: str = ""
    request_timeout: float = 120.0
    max_input_chars: int = 4000
    max_output_chars: int = 4000


@dataclass
class CaptureConfig:
    enabled: bool = True
    bunker_dir: str = "./bunker"
    interactions_file: str = "interactions.jsonl"
    guard_events_file: str = "guard_events.jsonl"
    team_memory_cli: Optional[str] = None      # e.g. /opt/homebrew/bin/axe-memory
    team_memory_share: bool = False            # only set True for AXE-internal usage


@dataclass
class GuardConfig:
    brand_leak_patterns: List[str] = field(default_factory=lambda: [
        r"\bI'?m (?:a |an )?(?:Qwen|Alibaba|Claude|Anthropic|GPT|OpenAI|Llama|Meta|Gemini|Google)\b",
        r"\bI was (?:made|created|trained|built) by (?:Alibaba|Anthropic|OpenAI|Meta|Google)\b",
        r"\bmy (?:creator|developer|company) is (?:Alibaba|Anthropic|OpenAI|Meta|Google)\b",
    ])
    harmful_patterns: List[str] = field(default_factory=lambda: [
        r"\b(?:make|build|synthesize)\s+(?:a\s+)?(?:bomb|explosive|biological\s+weapon)\b",
        r"\b(?:hack|exploit|compromise)\s+(?:a\s+)?(?:bank|government|critical\s+infrastructure)\b",
    ])
    classifier_cli: Optional[str] = None     # e.g. /Users/home/.axe/tools/ai_fleet.py
    classifier_kind: str = "classify"
    classifier_timeout: float = 0.3
    classifier_circuit_breaker_failures: int = 3


@dataclass
class CorsConfig:
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:8765", "http://127.0.0.1:8765"])
    allow_credentials: bool = False


@dataclass
class RateLimitConfig:
    enabled: bool = False
    requests_per_minute: int = 10
    burst: int = 3
    bypass_header: str = "X-Sandbox-Key"
    bypass_keys: List[str] = field(default_factory=list)


@dataclass
class SurfaceConfig:
    name: str
    url: str
    purpose: str
    audience: str = "general"
    capsule_path: Optional[str] = None        # local file path served at /context/<name>.js


@dataclass
class Config:
    brand: BrandConfig = field(default_factory=BrandConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    guard: GuardConfig = field(default_factory=GuardConfig)
    cors: CorsConfig = field(default_factory=CorsConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    surfaces: Dict[str, SurfaceConfig] = field(default_factory=dict)
    config_path: Optional[Path] = None


def _from_dict(cls, data: Dict[str, Any]):
    """Construct a dataclass from a dict, ignoring unknown keys (forward-compatible)."""
    valid = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid}
    return cls(**filtered)


def load(path: Optional[Path] = None) -> Config:
    """Load configuration from a TOML file with environment overrides.

    Resolution order:
      1. Explicit path argument
      2. SANDBOXPILOT_CONFIG env var
      3. ./pilot.toml
      4. Defaults only
    """
    if path is None:
        env_path = os.getenv("SANDBOXPILOT_CONFIG")
        if env_path:
            path = Path(env_path).expanduser()
        elif Path("pilot.toml").exists():
            path = Path("pilot.toml")

    cfg = Config()
    if path and Path(path).exists():
        with open(path, "rb") as f:
            data = _toml.load(f)
        cfg.config_path = Path(path).resolve()
        cfg.brand       = _from_dict(BrandConfig, data.get("brand", {}))
        cfg.server      = _from_dict(ServerConfig, data.get("server", {}))
        cfg.capture     = _from_dict(CaptureConfig, data.get("capture", {}))
        cfg.guard       = _from_dict(GuardConfig, data.get("guard", {}))
        cfg.cors        = _from_dict(CorsConfig, data.get("cors", {}))
        cfg.rate_limit  = _from_dict(RateLimitConfig, data.get("rate_limit", {}))
        for name, sdata in (data.get("surfaces", {}) or {}).items():
            sdata = dict(sdata)
            sdata.setdefault("name", name)
            cfg.surfaces[name] = _from_dict(SurfaceConfig, sdata)

    # Env overrides — secrets and host bindings shouldn't be in TOML
    if v := os.getenv("SANDBOXPILOT_PORT"):           cfg.server.port = int(v)
    if v := os.getenv("SANDBOXPILOT_INFERENCE_URL"):  cfg.server.inference_url = v
    if v := os.getenv("SANDBOXPILOT_DEFAULT_MODEL"):  cfg.server.default_model = v
    if v := os.getenv("SANDBOXPILOT_BUNKER_DIR"):     cfg.capture.bunker_dir = v
    if v := os.getenv("SANDBOXPILOT_BYPASS_KEYS"):
        cfg.rate_limit.bypass_keys = [k.strip() for k in v.split(",") if k.strip()]

    # Expand ~ in paths
    cfg.capture.bunker_dir = str(Path(cfg.capture.bunker_dir).expanduser())
    return cfg
