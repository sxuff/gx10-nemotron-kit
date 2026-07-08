#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import socket
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS = ROOT / "benchmarks" / "prompts" / "matrix.jsonl"


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_csv(value, cast):
    return [cast(item.strip()) for item in value.split(",") if item.strip()]


def load_prompts(path):
    prompts = []
    with open(path) as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
    return prompts


def context_block(words):
    if words <= 0:
        return ""
    sentence = (
        "GX10 local inference benchmark context: open models, reproducible "
        "serving flags, prompt tokens, completion throughput, TTFT, and "
        "operator notes all matter for useful public reports. "
    )
    tokens = sentence.split()
    repeated = []
    while len(repeated) < words:
        repeated.extend(tokens)
    text = " ".join(repeated[:words])
    return (
        "Use the following synthetic context for the benchmark. "
        "Do not quote it unless useful.\n\n"
        f"{text}\n\n"
    )


def stream_chat(url, model, prompt, max_tokens, temperature, timeout):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )

    start = time.time()
    first_token_at = None
    usage = {}
    finish_reason = None
    text_parts = []

    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            payload = line.removeprefix("data: ").strip()
            if payload == "[DONE]":
                break
            data = json.loads(payload)
            if data.get("usage"):
                usage = data["usage"]
            for choice in data.get("choices", []):
                finish_reason = choice.get("finish_reason") or finish_reason
                delta = choice.get("delta") or {}
                piece = delta.get("content") or delta.get("reasoning") or ""
                if piece:
                    if first_token_at is None:
                        first_token_at = time.time()
                    text_parts.append(piece)

    elapsed = time.time() - start
    ttft = None if first_token_at is None else first_token_at - start
    completion_tokens = usage.get("completion_tokens")
    prompt_tokens = usage.get("prompt_tokens")
    decode_time = None
    tokens_per_s = None
    if completion_tokens is not None:
        decode_time = elapsed if ttft is None else max(elapsed - ttft, 0.000001)
        tokens_per_s = completion_tokens / decode_time

    return {
        "elapsed_s": elapsed,
        "ttft_s": ttft,
        "decode_s": decode_time,
        "completion_tokens_per_s": tokens_per_s,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": usage.get("total_tokens"),
        "finish_reason": finish_reason,
        "response_chars": len("".join(text_parts)),
    }


def main():
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Run a small vLLM benchmark matrix.")
    parser.add_argument("--host", default=os.getenv("VLLM_HOST", "localhost"))
    parser.add_argument("--port", default=os.getenv("PORT", "8000"))
    parser.add_argument("--model", default=os.getenv("SERVED_MODEL_NAME", "nemotron-puzzle-75b-nvfp4"))
    parser.add_argument("--prompts", default=str(DEFAULT_PROMPTS))
    parser.add_argument("--max-tokens", default="64,128")
    parser.add_argument("--temperatures", default="0.0,0.2")
    parser.add_argument("--context-words", default="0,1024")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    max_tokens_values = parse_csv(args.max_tokens, int)
    temperature_values = parse_csv(args.temperatures, float)
    context_word_values = parse_csv(args.context_words, int)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else ROOT / "runs" / f"matrix-{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "results.jsonl"
    metadata_path = out_dir / "metadata.json"

    metadata = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "model": args.model,
        "url": f"http://{args.host}:{args.port}/v1/chat/completions",
        "prompts": str(pathlib.Path(args.prompts)),
        "max_tokens": max_tokens_values,
        "temperatures": temperature_values,
        "context_words": context_word_values,
        "repeats": args.repeats,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    url = metadata["url"]
    with open(output_path, "w") as out:
        for repeat in range(args.repeats):
            for context_words in context_word_values:
                prefix = context_block(context_words)
                for max_tokens in max_tokens_values:
                    for temperature in temperature_values:
                        for item in prompts:
                            prompt = prefix + item["prompt"]
                            result = stream_chat(
                                url=url,
                                model=args.model,
                                prompt=prompt,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                timeout=args.timeout,
                            )
                            record = {
                                "run_id": run_id,
                                "repeat": repeat,
                                "prompt_name": item["name"],
                                "context_words": context_words,
                                "max_tokens": max_tokens,
                                "temperature": temperature,
                                **result,
                            }
                            line = json.dumps(record)
                            print(line, flush=True)
                            out.write(line + "\n")
                            out.flush()

    print(json.dumps({"results": str(output_path), "metadata": str(metadata_path)}))


if __name__ == "__main__":
    main()
