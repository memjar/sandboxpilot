# Sandbox Pilot · Incident runbook

## Symptom: visitors report widget not loading

1. `curl -sI http://<pilot-host>:8094/widget/embed.js` → expect HTTP 200
2. Check the relevant page's `Content-Security-Policy` for script-src restrictions
3. Check pilot health: `sandboxpilot health --url http://<pilot-host>:8094`
4. If 502: inference backend likely down. Restart MLX / Ollama / vLLM as appropriate.

## Symptom: high guard rejection rate

1. `tail -50 ~/.axe/bunker/pilot_guard_events.jsonl | jq .reason | sort | uniq -c`
2. If `brand_leak` spike: the model is identifying as Qwen/Claude. Check the
   system prompt is being applied. Common cause: regression in `prompts.py`
   build template.
3. If `harmful_intent` spike: visitors actively probing. Consider IP block.
4. If `input_too_long` spike: someone scripting; consider rate-limit lowering.

## Symptom: capture file growing fast

1. `du -h ~/.axe/bunker/*.jsonl`
2. Daily rotate: `mv pilot_interactions.jsonl pilot_interactions.$(date +%Y%m%d).jsonl`
3. The LoRA pipeline reads any `pilot_interactions*.jsonl` glob (see
   `build_sft_pairs.py`).

## Symptom: heartbeat to observer fails

1. `curl https://axe.observer/api/health` → expect 200
2. Pilot's heartbeat is best-effort and degrades silently; no action needed
   unless observer is genuinely down.

## Symptom: rate limit blocking legit traffic

1. Operators should send `X-AXE-Key: <key>` header where key is in
   `cfg.rate_limit.bypass_keys`
2. To temporarily disable: set `[rate_limit] enabled = false` in config and
   restart.
