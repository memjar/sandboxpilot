"""Verify the tenant-isolation seam: external audiences must NOT write to
the internal interactions file."""
import json, tempfile
from pathlib import Path
from sandboxpilot.config import CaptureConfig
from sandboxpilot.capture import Capture

def test_internal_audience_routes_to_internal_file():
    with tempfile.TemporaryDirectory() as td:
        cap = Capture(CaptureConfig(bunker_dir=td))
        cap.write({"audience": "internal", "messages": [{"role":"user","content":"hi"}], "answer": "hi"})
        internal = Path(td) / "interactions.jsonl"
        external = Path(td) / "external_interactions.jsonl"
        assert internal.exists() and sum(1 for _ in open(internal)) == 1
        assert not external.exists() or sum(1 for _ in open(external)) == 0

def test_mike_audience_routes_to_external_file():
    with tempfile.TemporaryDirectory() as td:
        cap = Capture(CaptureConfig(bunker_dir=td))
        cap.write({"audience": "imi/mike", "messages": [{"role":"user","content":"hi"}], "answer": "hi"})
        internal = Path(td) / "interactions.jsonl"
        external = Path(td) / "external_interactions.jsonl"
        assert external.exists() and sum(1 for _ in open(external)) == 1
        assert not internal.exists() or sum(1 for _ in open(internal)) == 0

def test_isolation_never_crosses():
    """Most important test in the suite: the tenant seam holds across mixed traffic."""
    with tempfile.TemporaryDirectory() as td:
        cap = Capture(CaptureConfig(bunker_dir=td))
        for i in range(5):
            cap.write({"audience": "internal", "messages": [], "answer": f"i{i}"})
            cap.write({"audience": "imi/mike",     "messages": [], "answer": f"m{i}"})
        internal_lines = [json.loads(x) for x in open(Path(td)/"interactions.jsonl")]
        external_lines = [json.loads(x) for x in open(Path(td)/"external_interactions.jsonl")]
        assert all(r["audience"] == "internal" for r in internal_lines)
        assert all(r["audience"] == "imi/mike" for r in external_lines)
        assert len(internal_lines) == 5 and len(external_lines) == 5
