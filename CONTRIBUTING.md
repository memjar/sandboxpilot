# Contributing to Sandbox Pilot

## Quick dev loop

```sh
git clone https://github.com/memjar/sandboxpilot
cd sandboxpilot
pip install -e .[dev]
pytest tests/ -v
```

## Running locally

```sh
# 1 · Start an OpenAI-compatible inference backend (any of these works)
python3 -m mlx_lm.server --model your/model --port 8095 &
# or:
ollama serve &

# 2 · Run Sandbox Pilot
sandboxpilot serve --config examples/minimal/config.toml
```

## What to contribute

- **New examples** in `examples/<your-org>/` — copy `examples/axe/` and adapt
- **New audience templates** in `src/sandboxpilot/prompts.py`
- **Improved guard patterns** in `src/sandboxpilot/guard.py` (please add tests)
- **Inference backend adapters** for backends that aren't OpenAI-compatible
- **Documentation** in `docs/`

## Code style

- Python 3.9+ (use `typing.Optional` not `X | None`)
- Type hints on public APIs
- No emojis in code
- Apache 2.0 contributions

## Reporting issues

Open an issue at https://github.com/memjar/sandboxpilot/issues with:
- Steps to reproduce
- Expected vs actual behavior
- Pilot version (`sandboxpilot --version`)
- Inference backend + version
