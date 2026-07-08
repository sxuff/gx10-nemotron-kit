# GX10 Nemotron Kit

Reproducible local inference, quick checks, and latency notes for NVIDIA Nemotron Labs 3 Puzzle 75B A9B NVFP4 on GX10 / DGX Spark class hardware.

## Goals

- Clean GX10 setup notes
- vLLM serving recipe
- Quick checks
- Latency and context-length sweeps
- Public notes useful to the local AI community

## Quick Start

Serve the model:

```bash
./scripts/serve_vllm.sh
```

In a second shell, run a quick chat check:

```bash
./scripts/quick_chat.sh
```

Run the benchmark matrix:

```bash
./benchmarks/run_matrix.py
```

The matrix writes JSONL results and metadata under `runs/matrix-*`.

For a quick check:

```bash
./benchmarks/run_matrix.py --max-tokens 64 --temperatures 0.2 --context-words 0
```

Summarize a run:

```bash
latest_results="$(ls -td runs/matrix-*/results.jsonl | head -1)"
./benchmarks/summarize_results.py "$latest_results"
```

Run a cumulative throughput test:

```bash
./benchmarks/run_concurrency.py --concurrency 1,2,4,7 --max-tokens 1500 --prompt-words 29
latest_concurrency="$(ls -td runs/concurrency-*/results.jsonl | head -1)"
./benchmarks/summarize_concurrency.py "$latest_concurrency"
```

For higher concurrency, restart the server with a larger sequence cap:

```bash
MAX_NUM_SEQS=8 ./scripts/serve_vllm.sh
```

To test native MTP speculative decoding, restart the server with:

```bash
MAX_NUM_SEQS=8 MTP_K=3 ./scripts/serve_vllm.sh
```
