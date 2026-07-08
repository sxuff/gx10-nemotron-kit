#!/usr/bin/env python3
import json, os, time, urllib.request

PORT = os.getenv("PORT", "8000")
MODEL = os.getenv("SERVED_MODEL_NAME", "nemotron-puzzle-75b-nvfp4")
PROMPTS = "benchmarks/prompts/smoke.jsonl"

def post(prompt):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128,
        "temperature": 0.2,
        "stream": False,
    }
    req = urllib.request.Request(
        f"http://localhost:{PORT}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read().decode())
    elapsed = time.time() - start
    usage = data.get("usage", {})
    completion_tokens = usage.get("completion_tokens")
    tokens_per_s = None
    if completion_tokens is not None and elapsed > 0:
        tokens_per_s = completion_tokens / elapsed
    return {
        "elapsed_s": elapsed,
        "completion_tokens_per_s": tokens_per_s,
        "usage": usage,
    }

with open(PROMPTS) as f:
    for line in f:
        item = json.loads(line)
        result = post(item["prompt"])
        print(json.dumps({"name": item["name"], **result}))
