# AXE example · the reference deployment

This is how AXE Technologies actually runs Sandbox Pilot today.

## Layout

- `config.toml` — the production AXE config (6 surfaces, AXE-Guard patterns, axe-memory team capture)
- `capsules/` — per-surface JS context capsules
  - `keep.js`     · keep.axetechnologies.ca (Knox-attested design archive)
  - `intel.js`    · intel.axetechnologies.ca (Hercules-72B OSINT)
  - `observer.js` · axe.observer (Knox control plane)
  - `arena.js`    · arena.axe.onl (model arena)
  - `site.js`     · axetechnologies.ca (marketing)
  - `pulseai.js`  · live.pulseai.my (Mike-audience for IMI)

## Run it locally

```sh
# from the sandboxpilot repo root
sandboxpilot serve --config examples/axe/config.toml
```

## What makes this AXE-specific

- `team_memory_cli` points at `axe-memory` (atlas.axe.observer integration)
- Brand identity locked to "axe-edge / AXE Technologies"
- Allow-origins list includes every AXE-owned surface
- Mike-audience capsule routes to `bunker/external_interactions.jsonl` (tenant isolation)

## To use as your own template

```sh
cp -r examples/axe ./my-org
$EDITOR my-org/config.toml
sandboxpilot serve --config my-org/config.toml
```
