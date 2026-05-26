# Sandbox Pilot

A drop-in sandboxed AI pilot for any web property. **Three sandboxes in one**:

- **Security sandbox** — input/output filtering, no shell, no egress, configurable identity-leak prevention.
- **Playground sandbox** — deploy on real surfaces with bounded blast radius. Failures don't damage anything important.
- **Learning sandbox** — every visitor interaction becomes a captured training pair for fine-tuning your own model on your own distribution.

Built by [AXE Technologies](https://axetechnologies.ca). Configurable for any organization.

```sh
pip install sandboxpilot
sandboxpilot serve --config examples/axe/config.toml
```

Then drop one script tag in any page:

```html
<script src="https://your-pilot-host/widget/embed.js" defer></script>
<script>
  window.SANDBOX_CONTEXT = {
    surface: "your-domain.com",
    surface_purpose: "your product line",
    audience: "your visitors",
    page: { url: location.pathname, title: document.title, summary: "..." },
  };
</script>
```

A floating chat bubble appears. It knows where it is. It captures every
interaction for future training. It refuses harmful requests and never claims
to be Claude or GPT.

---

## What's interesting about this

### "Where it lives" awareness

Each surface ships a JS *context capsule* that tells the pilot its purpose, its
audience, and what's on the current page. The model isn't just a chatbot —
it's a resident of a specific place. It speaks differently on a marketing page
than on a documentation page than on an internal dashboard.

### Capture for fine-tuning, not for OpenAI

Every `(context, question, answer)` tuple is appended to a local JSONL file
you own. Use it to train a per-surface LoRA on your own base model. The pilot
gets better at being *your* assistant on *your* surfaces with every visit.

### Brand persona enforcement

Configure the identity. If your pilot accidentally says "I'm Qwen" or "I'm
Claude" (the underlying model leaking through), the guard catches it before
the visitor sees it. The pilot is *your* AI, not someone else's.

### Bring your own inference

Sandbox Pilot doesn't run inference — it routes to whatever OpenAI-compatible
backend you configure: Ollama, MLX, llama.cpp, vLLM, LM Studio, even cloud
providers. You control where the bytes go.

---

## Architecture

```
   visitor's browser
   ┌────────────────────────────────────┐
   │ SANDBOX_CONTEXT (capsule.js)       │
   │   surface · page · audience · ...  │
   └────────────────────────────────────┘
                  ↓
   ┌────────────────────────────────────┐
   │ widget/embed.js (floating UI)      │
   └────────────────┬───────────────────┘
                    │  POST /v1/chat (SSE)
                    ▼
   ┌────────────────────────────────────┐
   │ Sandbox Pilot server               │
   │   ┌─────────┐                      │
   │   │  Guard  │ ← input filter      │
   │   └─────────┘                      │
   │   ┌─────────┐                      │
   │   │ Prompt  │ ← system prompt    │
   │   │ Builder │   from capsule     │
   │   └─────────┘                      │
   │   ┌─────────┐                      │
   │   │  Proxy  │ ← stream upstream  │
   │   └─────────┘                      │
   │   ┌─────────┐                      │
   │   │  Guard  │ ← output filter    │
   │   └─────────┘                      │
   │   ┌─────────┐                      │
   │   │ Capture │ → bunker JSONL     │
   │   └─────────┘                      │
   └────────────────────────────────────┘
                    ↓
   ┌────────────────────────────────────┐
   │ Your inference backend             │
   │  · Ollama  · MLX  · llama.cpp      │
   │  · vLLM    · LM Studio · OpenAI    │
   └────────────────────────────────────┘
```

---

## Quick start

```sh
# 1 · Install
pip install -e .

# 2 · Start an OpenAI-compatible inference server
python3 -m mlx_lm.server --model your/model/path --port 8095 &

# 3 · Configure
cp examples/axe/config.toml ./pilot.toml
$EDITOR ./pilot.toml

# 4 · Serve
sandboxpilot serve --config ./pilot.toml
# → http://localhost:8094

# 5 · Embed
# Drop this in any page:
#   <script src="http://localhost:8094/widget/embed.js" defer></script>
```

---

## Configuration

See [`docs/CONFIG.md`](docs/CONFIG.md) for the full schema. Minimal config:

```toml
[brand]
name = "Acme Corp"
identity_name = "Acme's AI assistant"
identity_lab = "Acme Corp"

[server]
inference_url = "http://localhost:8095"
default_model = "your/model/path"

[capture]
bunker_dir = "./bunker"

[surfaces.docs]
url = "docs.acme.com"
purpose = "Acme product documentation"
audience = "developer"
```

---

## Built-in examples

| Example | Description |
|---|---|
| [`examples/axe/`](examples/axe/) | The reference configuration — AXE Technologies' internal deployment with 5 surfaces (Keep / Intel / Observer / Arena / Marketing) |
| [`examples/minimal/`](examples/minimal/) | Smallest possible config — one surface, default guard |

---

## Three sandboxes, in detail

### 1 · Security sandbox

- AXE-Guard input filter (configurable regex patterns, length caps)
- AXE-Guard output filter (brand-leak detection, identity enforcement)
- No shell exec, no eval, no arbitrary fs writes
- CORS allowlist limits origins to configured surfaces
- Optional rate limiting via [`slowapi`](https://slowapi.readthedocs.io/)
- Optional Ed25519 signature on capture records ([Knox-style attestation](docs/ATTESTATION.md))

### 2 · Playground sandbox

Deploy on real surfaces with bounded blast radius. The pilot only knows what
its context capsule tells it. It can't look up your CRM. It can't trigger
actions. It answers questions about where it lives, nothing more.

When you want it to grow tools, add them explicitly to the capsule. The
contract is: the pilot can only do what the capsule lets it know about.

### 3 · Learning sandbox

Every interaction is captured to `bunker/interactions.jsonl`:

```json
{
  "interaction_id": "...", "surface": "docs.acme.com",
  "page_url": "/api-reference", "page_title": "API Reference",
  "messages": [{"role": "user", "content": "..."}],
  "answer": "...",
  "guard_input_pass": true, "guard_output_pass": true,
  "captured_at": "2026-05-26T..."
}
```

Use the included `tools/build_sft_pairs.py` to convert these into
per-surface SFT JSONL ready for `mlx_lm.lora` or any standard fine-tuning
pipeline. The model becomes *yours* on *your* distribution.

---

## Why "Sandbox" Pilot?

The word "sandbox" does triple duty here, and that's deliberate.

- **Security sandbox** is what protects you from the model.
- **Children's sandbox** is the playground where you can deploy without fear.
- **Learning sandbox** is the place where the model figures out where it is.

A model deployed without all three is either dangerous, brittle, or static.
Sandbox Pilot makes them work together.

---

## Production checklist

See [`docs/DEPLOY.md`](docs/DEPLOY.md). Highlights:

- [ ] Configure rate limits for your traffic profile
- [ ] Set up monitoring (heartbeat → your observability stack)
- [ ] Set up secrets rotation for inference backend keys
- [ ] Configure CORS allowlist for your production surfaces
- [ ] Set up error paging (Pushover, PagerDuty, your channel)
- [ ] Run synthetic traffic for soak testing
- [ ] Decide capture privacy posture (which audiences contribute to training)

---

## License

Apache 2.0 · See [LICENSE](LICENSE).

## Related

- [The Keep](https://github.com/axe-ai/axe-keep) — Knox-attested design archive, Sandbox Pilot's reference deployment surface
- [AXE Technologies](https://axetechnologies.ca) — the company behind this
