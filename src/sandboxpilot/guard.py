"""Sandbox Pilot guard layer.

Two-stage filtering:
  · Input  — pre-flight check on user message (length + harmful intent)
  · Output — post-stream check on model answer (brand-leak detection)

All patterns are configurable per-deployment via Config.guard.
"""
from __future__ import annotations
import json, re, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List
from .config import GuardConfig


@dataclass
class GuardDecision:
    allowed: bool
    reason: Optional[str] = None
    latency_ms: float = 0.0
    classifier_used: bool = False


class Guard:
    def __init__(self, cfg: GuardConfig, log_path: Optional[Path] = None):
        self.cfg = cfg
        self.log_path = log_path
        self._brand_patterns = [re.compile(p, re.I) for p in cfg.brand_leak_patterns]
        self._harm_patterns  = [re.compile(p, re.I) for p in cfg.harmful_patterns]
        self._classifier_failures = 0
        self._classifier_disabled_until = 0.0

    def check_input(self, text: str, max_chars: int) -> GuardDecision:
        t0 = time.perf_counter()
        if len(text) > max_chars:
            return self._log("input_blocked", text, "input_too_long", t0)
        for pat in self._harm_patterns:
            if pat.search(text):
                return self._log("input_blocked", text, "harmful_intent", t0)
        return GuardDecision(True, latency_ms=(time.perf_counter() - t0) * 1000)

    def check_output(self, text: str, max_chars: int) -> GuardDecision:
        t0 = time.perf_counter()
        if len(text) > max_chars:
            return self._log("output_truncated", text, "output_too_long", t0)
        for pat in self._brand_patterns:
            if pat.search(text):
                return self._log("output_blocked", text, "brand_leak", t0)
        return GuardDecision(True, latency_ms=(time.perf_counter() - t0) * 1000)

    def _log(self, event: str, text: str, reason: str, t0: float) -> GuardDecision:
        if self.log_path is not None:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                rec = {
                    "event": event,
                    "reason": reason,
                    "text_preview": text[:200],
                    "text_len": len(text),
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(rec) + "\n")
            except Exception:
                pass
        return GuardDecision(False, reason=reason, latency_ms=(time.perf_counter() - t0) * 1000)
