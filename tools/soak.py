#!/usr/bin/env python3
"""soak.py · synthetic load generator for pre-launch soak testing.

Usage:
    python3 tools/soak.py --rps 1 --duration 3600 --url http://localhost:8094

Cycles through audiences + surfaces to exercise the tenant-isolation seam
under load. Outputs a JSON summary every minute.
"""
import argparse, json, random, time, urllib.request, urllib.error
from collections import Counter

SCENARIOS = [
    {"surface": "keep.axetechnologies.ca", "audience": "internal",
     "page": {"url": "/", "title": "The Keep", "summary": "design archive"},
     "questions": ["where am I?", "what is The Keep?", "list the artifacts", "what is in the Captain Roadmap?"]},
    {"surface": "live.pulseai.my", "audience": "imi/mike",
     "page": {"url": "/", "title": "IMI Live", "summary": "Mike workspace"},
     "questions": ["what is this page?", "tell me about The Keep", "how do I verify a roadmap?"]},
    {"surface": "intel.axetechnologies.ca", "audience": "operator",
     "page": {"url": "/", "title": "AXE Intel", "summary": "OSINT synthesis"},
     "questions": ["how do I run a query?", "what is intel?"]},
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8094")
    p.add_argument("--rps", type=float, default=0.5)
    p.add_argument("--duration", type=int, default=3600)
    p.add_argument("--no-bypass", action="store_true")
    args = p.parse_args()

    interval = 1.0 / args.rps
    deadline = time.time() + args.duration
    counters = Counter()
    last_summary = time.time()
    print(f"Soak start rps={args.rps} duration={args.duration}s url={args.url}")

    while time.time() < deadline:
        sc = random.choice(SCENARIOS)
        q = random.choice(sc["questions"])
        body = json.dumps({
            "messages": [{"role": "user", "content": q}],
            "context": {"surface": sc["surface"], "audience": sc["audience"],
                        "surface_purpose": "synthetic-soak", "page": sc["page"]},
            "max_tokens": 30,
        }).encode()
        req = urllib.request.Request(args.url + "/v1/chat", data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        if not args.no_bypass:
            req.add_header("X-AXE-Key", "soak-bypass-key")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                counters[r.status] += 1
                while True:
                    chunk = r.read(4096)
                    if not chunk:
                        break
        except urllib.error.HTTPError as e:
            counters[e.code] += 1
        except Exception as e:
            counters[f"err:{type(e).__name__}"] += 1

        if time.time() - last_summary >= 60:
            print(json.dumps({"ts": int(time.time()), "counts": dict(counters)}))
            last_summary = time.time()
        time.sleep(interval)

    print(json.dumps({"FINAL": True, "ts": int(time.time()), "counts": dict(counters)}))

if __name__ == "__main__":
    main()
