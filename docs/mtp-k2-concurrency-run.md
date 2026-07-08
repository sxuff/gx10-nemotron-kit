# MTP k=2 Concurrency Run

Date: 2026-07-08

Model:

- `nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4`
- Served as `nemotron-puzzle-75b-nvfp4`

Benchmark:

```bash
./benchmarks/run_concurrency.py \
  --concurrency 1,2,4,7 \
  --max-tokens 1500 \
  --prompt-words 29 \
  --warmup-requests 2 \
  --warmup-tokens 256
```

Run metadata:

- Result path: `runs/concurrency-20260708-194519Z/results.jsonl`
- Repeat result path: `runs/concurrency-20260708-200152Z/results.jsonl`
- Prompt tokens per request: 54
- Completion tokens per request: 1,500
- Natural EOS disabled: yes
- Errors: none

Summary, first run:

| concurrent_sessions | ok/error | cumulative_gen_tok_s | cumulative_decode_tok_s | avg_per_session_tok_s | avg_ttft_s | scale |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1/0 | 22.75 | 22.86 | 22.75 | 0.314 | 1.00 |
| 2 | 2/0 | 39.61 | 40.53 | 19.80 | 1.493 | 1.74 |
| 4 | 4/0 | 66.04 | 66.42 | 16.51 | 0.608 | 2.90 |
| 7 | 7/0 | 88.85 | 89.34 | 12.69 | 0.630 | 3.91 |

Summary, repeat run:

| concurrent_sessions | ok/error | cumulative_gen_tok_s | cumulative_decode_tok_s | avg_per_session_tok_s | avg_ttft_s | scale |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1/0 | 23.77 | 23.89 | 23.77 | 0.335 | 1.00 |
| 2 | 2/0 | 41.43 | 42.24 | 20.71 | 1.387 | 1.74 |
| 4 | 4/0 | 69.39 | 69.77 | 17.35 | 0.467 | 2.92 |
| 7 | 7/0 | 85.88 | 86.24 | 12.27 | 0.504 | 3.61 |

Notes:

- This run completed all 10,500 requested completion tokens at 7 concurrent sessions.
- vLLM speculative decoding logs showed two draft positions, consistent with `MTP_K=2`.
- Compared with the earlier `MTP_K=3` crash note, `MTP_K=2` appears more stable on this GX10/vLLM nightly setup for forced long-output concurrency.
- Across two 7-session runs, cumulative generation throughput was 85.88-88.85 tokens/sec with zero failed sessions.
