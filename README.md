# GX10 Nemotron Kit

Reproducible local inference, smoke tests, and latency notes for NVIDIA Nemotron Labs 3 Puzzle 75B A9B NVFP4 on GX10 / DGX Spark class hardware.

## Goals

- Clean GX10 setup notes
- vLLM serving recipe
- Smoke tests
- Latency and context-length sweeps
- Public notes useful to the local AI community

## Quick Start

Serve the model:

```bash
./scripts/serve_vllm.sh
```

In a second shell, run a smoke test:

```bash
./scripts/smoke_chat.sh
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
