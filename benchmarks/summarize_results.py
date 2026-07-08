#!/usr/bin/env python3
import argparse
import collections
import json
import statistics


def mean(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return statistics.fmean(values)


def fmt(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description="Summarize benchmark JSONL results.")
    parser.add_argument("results_jsonl")
    args = parser.parse_args()

    rows = []
    with open(args.results_jsonl) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    groups = collections.defaultdict(list)
    for row in rows:
        key = (row["context_words"], row["max_tokens"], row["temperature"])
        groups[key].append(row)

    print("| context_words | max_tokens | temperature | runs | avg_prompt_tokens | avg_ttft_s | avg_tok_s | avg_elapsed_s |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for key in sorted(groups):
        items = groups[key]
        context_words, max_tokens, temperature = key
        print(
            "| "
            + " | ".join(
                [
                    str(context_words),
                    str(max_tokens),
                    str(temperature),
                    str(len(items)),
                    fmt(mean(item.get("prompt_tokens") for item in items), 0),
                    fmt(mean(item.get("ttft_s") for item in items), 3),
                    fmt(mean(item.get("completion_tokens_per_s") for item in items), 2),
                    fmt(mean(item.get("elapsed_s") for item in items), 2),
                ]
            )
            + " |"
        )


if __name__ == "__main__":
    main()
