#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import os
import pathlib
import socket
import statistics
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_csv(value, cast=int):
    return [cast(item.strip()) for item in value.split(",") if item.strip()]


def mean(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return statistics.fmean(values)


def percentile(values, pct):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    index = round((len(values) - 1) * pct)
    return values[index]


def make_prompt(target_words):
    base = (
        "Write a detailed but direct explanation of why local open-model "
        "inference matters for builders using workstation-class NVIDIA "
        "hardware. Cover reproducibility, privacy, debugging, benchmark "
        "honesty, and iteration speed."
    )
    words = base.split()
    if target_words <= len(words):
        return " ".join(words[:target_words])
    return base


def stream_chat(
    url,
    model,
    prompt,
    max_tokens,
    temperature,
    timeout,
    session_index,
    force_tokens,
):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if force_tokens:
        body["ignore_eos"] = True
        body["min_tokens"] = max_tokens
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )

    start = time.time()
    first_token_at = None
    usage = {}
    finish_reason = None

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
                if delta.get("content") or delta.get("reasoning"):
                    if first_token_at is None:
                        first_token_at = time.time()

    end = time.time()
    completion_tokens = usage.get("completion_tokens") or 0
    ttft = None if first_token_at is None else first_token_at - start
    decode_s = None if first_token_at is None else max(end - first_token_at, 0.000001)
    return {
        "session_index": session_index,
        "elapsed_s": end - start,
        "ttft_s": ttft,
        "decode_s": decode_s,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": completion_tokens,
        "total_tokens": usage.get("total_tokens"),
        "finish_reason": finish_reason,
    }


def run_group(url, model, prompt, max_tokens, temperature, concurrency, timeout, force_tokens):
    group_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(
                stream_chat,
                url,
                model,
                prompt,
                max_tokens,
                temperature,
                timeout,
                session_index,
                force_tokens,
            )
            for session_index in range(concurrency)
        ]
        sessions = [future.result() for future in concurrent.futures.as_completed(futures)]
    group_elapsed = time.time() - group_start
    sessions.sort(key=lambda item: item["session_index"])

    completion_tokens = sum(item["completion_tokens"] for item in sessions)
    prompt_tokens = sum(item.get("prompt_tokens") or 0 for item in sessions)
    decode_denominator = max((item.get("decode_s") or 0 for item in sessions), default=0)
    cumulative_decode_tok_s = None
    if decode_denominator > 0:
        cumulative_decode_tok_s = completion_tokens / decode_denominator

    return {
        "concurrent_sessions": concurrency,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "wall_s": group_elapsed,
        "cumulative_gen_tok_s": completion_tokens / group_elapsed,
        "cumulative_decode_tok_s": cumulative_decode_tok_s,
        "avg_per_session_gen_tok_s": (completion_tokens / group_elapsed) / concurrency,
        "completion_tokens": completion_tokens,
        "prompt_tokens": prompt_tokens,
        "avg_ttft_s": mean(item.get("ttft_s") for item in sessions),
        "p50_ttft_s": percentile((item.get("ttft_s") for item in sessions), 0.50),
        "p90_ttft_s": percentile((item.get("ttft_s") for item in sessions), 0.90),
        "sessions": sessions,
    }


def main():
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Benchmark cumulative throughput under concurrent sessions.")
    parser.add_argument("--host", default=os.getenv("VLLM_HOST", "localhost"))
    parser.add_argument("--port", default=os.getenv("PORT", "8000"))
    parser.add_argument("--model", default=os.getenv("SERVED_MODEL_NAME", "nemotron-puzzle-75b-nvfp4"))
    parser.add_argument("--concurrency", default="1,2,4,7")
    parser.add_argument("--max-tokens", type=int, default=1500)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--prompt-words", type=int, default=29)
    parser.add_argument("--warmup-requests", type=int, default=1)
    parser.add_argument("--warmup-tokens", type=int, default=128)
    parser.add_argument(
        "--allow-eos",
        action="store_true",
        help="Let requests stop naturally before max_tokens.",
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()
    force_tokens = not args.allow_eos

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else ROOT / "runs" / f"concurrency-{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "results.jsonl"
    metadata_path = out_dir / "metadata.json"

    prompt = make_prompt(args.prompt_words)
    url = f"http://{args.host}:{args.port}/v1/chat/completions"
    metadata = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "model": args.model,
        "url": url,
        "concurrency": parse_csv(args.concurrency),
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "prompt_words_requested": args.prompt_words,
        "warmup_requests": args.warmup_requests,
        "warmup_tokens": args.warmup_tokens,
        "force_tokens": force_tokens,
        "prompt": prompt,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    for warmup_index in range(args.warmup_requests):
        stream_chat(
            url=url,
            model=args.model,
            prompt=prompt,
            max_tokens=min(args.warmup_tokens, args.max_tokens),
            temperature=args.temperature,
            timeout=args.timeout,
            session_index=warmup_index,
            force_tokens=force_tokens,
        )

    with open(output_path, "w") as out:
        for concurrency in metadata["concurrency"]:
            record = {
                "run_id": run_id,
                **run_group(
                    url=url,
                    model=args.model,
                    prompt=prompt,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    concurrency=concurrency,
                    timeout=args.timeout,
                    force_tokens=force_tokens,
                ),
            }
            line = json.dumps(record)
            print(line, flush=True)
            out.write(line + "\n")
            out.flush()

    print(json.dumps({"results": str(output_path), "metadata": str(metadata_path)}))


if __name__ == "__main__":
    main()
