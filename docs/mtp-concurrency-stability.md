# MTP Concurrency Stability Note

Date: 2026-07-08

Observed setup:

- Model: `nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4`
- vLLM image: `vllm/vllm-openai:cu130-nightly`
- vLLM version in log: `v0.19.2rc1.dev134+gfe9c3d6c5`
- Speculative decoding: `{"method":"mtp","num_speculative_tokens":3}`
- Benchmark shape: concurrent requests, forced 1,500-token generations

Result:

- MTP improved cumulative throughput versus no MTP.
- A forced long-output run failed at higher concurrency with a fatal EngineCore error.
- The failure occurred with 4 running requests after each had generated roughly 1.2k-1.4k output tokens.
- Later `MTP_K=3` runs completed successfully; see `docs/mtp-k3-concurrency-run.md`.

Primary failure signature:

```text
torch.AcceleratorError: CUDA error: an illegal memory access was encountered
vllm.v1.engine.exceptions.EngineDeadError: EngineCore encountered an issue.
```

The stack points into vLLM's FlashInfer attention metadata path:

```text
vllm/v1/attention/backends/flashinfer.py
```

Recommended follow-up checks:

```bash
# Baseline, no MTP
docker rm -f vllm-nemotron-puzzle
MAX_NUM_SEQS=8 ./scripts/serve_vllm.sh

# MTP k=1
docker rm -f vllm-nemotron-puzzle
MAX_NUM_SEQS=8 MTP_K=1 ./scripts/serve_vllm.sh

# MTP k=3
docker rm -f vllm-nemotron-puzzle
MAX_NUM_SEQS=8 MTP_K=3 ./scripts/serve_vllm.sh

# MTP k=3, attention backend A/B
docker rm -f vllm-nemotron-puzzle
MAX_NUM_SEQS=8 MTP_K=3 ATTENTION_BACKEND=auto ./scripts/serve_vllm.sh
```

Use the same client benchmark each time:

```bash
./benchmarks/run_concurrency.py \
  --concurrency 1,2,4,7 \
  --max-tokens 1500 \
  --prompt-words 29 \
  --warmup-requests 2 \
  --warmup-tokens 256
```

If a run fails, preserve the container logs before removing the container:

```bash
docker logs vllm-nemotron-puzzle > runs/vllm-failure.log 2>&1
```
