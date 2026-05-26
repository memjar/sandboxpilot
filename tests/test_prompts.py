from sandboxpilot.prompts import build
from sandboxpilot.config import BrandConfig

BRAND = BrandConfig(name="Acme", identity_name="Acme AI", identity_lab="Acme Corp")

def test_default_template():
    p = build({"surface": "docs.acme.com", "audience": "developer",
               "page": {"title": "API Reference", "url": "/api"}}, BRAND)
    assert "Acme AI" in p
    assert "API Reference" in p
    assert "Acme Corp" in p

def test_mike_template_branch():
    p = build({"surface": "live.pulseai.my", "audience": "mike",
               "page": {"title": "Home", "url": "/"}}, BRAND)
    assert "120 words or fewer" in p
    assert "Mike" in p

def test_brand_lock():
    p = build({"surface": "test", "audience": "internal", "page": {}}, BRAND)
    assert "Qwen" in p  # locked-against list
    assert "Acme AI" in p
