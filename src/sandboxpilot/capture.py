"""Sandbox Pilot capture layer — every interaction goes to bunker JSONL.

Optionally fan out to a team memory CLI (e.g. AXE's axe-memory) so captures
are searchable cross-fleet. Mike-audience captures route to a separate file
to keep tenant data isolated by default.
"""
from __future__ import annotations
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from .config import CaptureConfig


class Capture:
    def __init__(self, cfg: CaptureConfig):
        self.cfg = cfg
        self.bunker = Path(cfg.bunker_dir).expanduser()
        self.bunker.mkdir(parents=True, exist_ok=True)
        self.path_internal = self.bunker / cfg.interactions_file
        self.path_external = self.bunker / "external_interactions.jsonl"
        self.path_guard    = self.bunker / cfg.guard_events_file

    def write(self, record: Dict[str, Any]) -> None:
        if not self.cfg.enabled:
            return
        record["captured_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        # Tenancy isolation: any non-internal audience routes to a separate file
        audience = (record.get("audience") or "internal").lower()
        is_external = audience and audience != "internal" and audience != "general"
        path = self.path_external if is_external else self.path_internal
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")
        # Optional fan-out to team memory CLI (only for non-external captures
        # and only if --share is explicitly configured)
        if (
            not is_external
            and self.cfg.team_memory_cli
            and self.cfg.team_memory_share
        ):
            self._team_memory_save(record)

    def stats(self) -> Dict[str, Any]:
        def c(p: Path) -> int:
            return sum(1 for _ in open(p)) if p.exists() else 0
        return {
            "internal_interactions": c(self.path_internal),
            "external_interactions": c(self.path_external),
            "guard_events": c(self.path_guard),
            "bunker_dir": str(self.bunker),
        }

    def _team_memory_save(self, rec: Dict[str, Any]) -> None:
        try:
            q = (rec.get("messages", [{}])[-1] or {}).get("content", "")[:120]
            a = (rec.get("answer") or "")[:200]
            text = f"Pilot interaction · {rec.get('surface','?')} · {rec.get('page_url','?')} · Q: {q} · A: {a}"
            tags = "sandboxpilot," + rec.get("surface", "unknown").replace(".", "-")
            subprocess.run(
                [self.cfg.team_memory_cli, "save", text, "--kind", "note", "--tags", tags, "--share"],
                timeout=5, capture_output=True, text=True,
            )
        except Exception:
            pass
