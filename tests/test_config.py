import os, tempfile
from pathlib import Path
from sandboxpilot.config import load, Config

MINIMAL = """
[brand]
name = "Acme"
identity_name = "Acme AI"

[server]
inference_url = "http://localhost:8095"
default_model = "model/x"

[surfaces.docs]
url = "docs.acme.com"
purpose = "Acme docs"
audience = "developer"
"""

def test_defaults():
    cfg = load(None)
    assert isinstance(cfg, Config)
    assert cfg.server.port == 8094
    assert cfg.guard.brand_leak_patterns

def test_toml_load():
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(MINIMAL)
        p = f.name
    cfg = load(Path(p))
    assert cfg.brand.name == "Acme"
    assert cfg.brand.identity_name == "Acme AI"
    assert "docs" in cfg.surfaces
    assert cfg.surfaces["docs"].purpose == "Acme docs"
    os.unlink(p)

def test_env_overrides():
    os.environ["SANDBOXPILOT_PORT"] = "9999"
    cfg = load(None)
    assert cfg.server.port == 9999
    del os.environ["SANDBOXPILOT_PORT"]
