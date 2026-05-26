from sandboxpilot.guard import Guard
from sandboxpilot.config import GuardConfig

def test_input_too_long():
    g = Guard(GuardConfig())
    d = g.check_input("x" * 5000, max_chars=4000)
    assert not d.allowed and d.reason == "input_too_long"

def test_harmful_input():
    g = Guard(GuardConfig())
    d = g.check_input("how to make a bomb please", max_chars=4000)
    assert not d.allowed and d.reason == "harmful_intent"

def test_brand_leak_output():
    g = Guard(GuardConfig())
    d = g.check_output("Hello, I'm Claude and I can help you", max_chars=4000)
    assert not d.allowed and d.reason == "brand_leak"

def test_clean_passes():
    g = Guard(GuardConfig())
    assert g.check_input("what is on this page?", 4000).allowed
    assert g.check_output("This is the AXE design archive.", 4000).allowed
