#!/usr/bin/env python3
import argparse
import json


def fmt(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description="Summarize concurrency benchmark JSONL.")
    parser.add_argument("results_jsonl")
    args = parser.parse_args()

    rows = []
    with open(args.results_jsonl) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    baseline = None
    for row in rows:
        if row["concurrent_sessions"] == 1:
            baseline = row["cumulative_gen_tok_s"]
            break

    print("| concurrent_sessions | ok/error | cumulative_gen_tok_s | cumulative_decode_tok_s | avg_per_session_tok_s | avg_ttft_s | scale |")
    print("|---:|---:|---:|---:|---:|---:|---:|")
    for row in sorted(rows, key=lambda item: item["concurrent_sessions"]):
        scale = None if not baseline else row["cumulative_gen_tok_s"] / baseline
        print(
            "| "
            + " | ".join(
                [
                    str(row["concurrent_sessions"]),
                    f"{row.get('ok_sessions', '-')}/{row.get('error_sessions', 0)}",
                    fmt(row.get("cumulative_gen_tok_s")),
                    fmt(row.get("cumulative_decode_tok_s")),
                    fmt(row.get("avg_per_session_gen_tok_s")),
                    fmt(row.get("avg_ttft_s"), 3),
                    fmt(scale),
                ]
            )
            + " |"
        )


if __name__ == "__main__":
    main()
