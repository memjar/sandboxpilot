# Sandbox Pilot · Configuration

Config is loaded from TOML. Resolution order:

1. `--config PATH` CLI arg
2. `SANDBOXPILOT_CONFIG` env var
3. `./pilot.toml` in cwd
4. Defaults

## Full schema

```toml
[brand]
# What the visitor sees + what the model identifies as
name             = "Acme Corp"
short_name       = "Acme"
accent_color     = "#D4AF37"                 # CSS color for widget UI
font_display     = "Space Grotesk, sans-serif"
font_mono        = "IBM Plex Mono, monospace"
identity_name    = "Acme's resident AI"      # what the model calls itself
identity_lab     = "Acme Corp"               # who built it
tone_rules = [
  "Speak truthfully about what you can and cannot do.",
  # ... add your house rules
]

[server]
host             = "0.0.0.0"
port             = 8094
inference_url    = "http://localhost:8095"   # any OpenAI-compatible backend
default_model    = "your/model/identifier"
request_timeout  = 120.0
max_input_chars  = 4000
max_output_chars = 4000

[capture]
enabled            = true
bunker_dir         = "~/bunker"
interactions_file  = "interactions.jsonl"
guard_events_file  = "guard_events.jsonl"
team_memory_cli    = ""                       # optional · path to e.g. axe-memory
team_memory_share  = false                    # opt-in to fan-out

[guard]
brand_leak_patterns = [
  "\\bI'?m (?:a |an )?(?:Qwen|Claude|GPT|...)\\b",  # add your patterns
]
harmful_patterns = [
  "\\b(?:make|build|synthesize)\\s+(?:a\\s+)?(?:bomb|weapon)\\b",
]

[cors]
allowed_origins   = ["https://your-surface.com"]
allow_credentials = false

[rate_limit]
enabled              = false
requests_per_minute  = 10
burst                = 3
bypass_header        = "X-Sandbox-Key"
bypass_keys          = []   # filled from env SANDBOXPILOT_BYPASS_KEYS

# Per-surface configuration · one section per place you deploy the pilot
[surfaces.<name>]
url          = "your-surface.com"
purpose      = "what this surface is for"
audience     = "internal|operator|public|mike|developer"
capsule_path = "path/to/your/capsule.js"
```

## Environment variable overrides

These override TOML values (useful for secrets + deploy-time config):

| Variable | Sets |
|---|---|
| `SANDBOXPILOT_CONFIG` | Config file path |
| `SANDBOXPILOT_PORT` | `server.port` |
| `SANDBOXPILOT_INFERENCE_URL` | `server.inference_url` |
| `SANDBOXPILOT_DEFAULT_MODEL` | `server.default_model` |
| `SANDBOXPILOT_BUNKER_DIR` | `capture.bunker_dir` |
| `SANDBOXPILOT_BYPASS_KEYS` | `rate_limit.bypass_keys` (comma-separated) |

## Validation

```sh
sandboxpilot validate --config ./pilot.toml
```

Returns a summary or exits non-zero with a clear error.

## Per-audience behaviour

| Audience | Captures go to | System prompt | Notes |
|---|---|---|---|
| `internal`, `general` | `bunker/interactions.jsonl` | Default template | Optionally fan out to team memory |
| `mike`, `imi` | `bunker/external_interactions.jsonl` | Mike template (brief, plain language) | Never fanned out to team memory |
| Any other non-internal value | `bunker/external_interactions.jsonl` | Default template | Tenancy-isolated |

This is the **tenancy isolation seam** — external visitors never contaminate
your internal training corpus by default.
