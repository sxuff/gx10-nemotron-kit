# First Matrix Run

Date: 2026-07-08

Hardware:

- NVIDIA GB10 on GX10
- Ubuntu 24.04.4 LTS aarch64
- NVIDIA driver 580.159.03
- CUDA 13.0

Model:

- `nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4`
- Served as `nemotron-puzzle-75b-nvfp4`

Serving image:

- `vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`

Command:

```bash
./benchmarks/run_matrix.py
```

Summary:

| context_words | max_tokens | temperature | runs | avg_prompt_tokens | avg_ttft_s | avg_tok_s | avg_elapsed_s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 64 | 0.0 | 2 | 51 | 0.165 | 16.49 | 4.05 |
| 0 | 64 | 0.2 | 2 | 51 | 0.159 | 16.38 | 4.07 |
| 0 | 128 | 0.0 | 2 | 51 | 0.162 | 16.30 | 8.01 |
| 0 | 128 | 0.2 | 2 | 51 | 0.159 | 16.27 | 8.02 |
| 1024 | 64 | 0.0 | 2 | 1564 | 1.117 | 16.45 | 5.01 |
| 1024 | 64 | 0.2 | 2 | 1564 | 0.640 | 16.34 | 4.56 |
| 1024 | 128 | 0.0 | 2 | 1564 | 0.637 | 16.32 | 8.48 |
| 1024 | 128 | 0.2 | 2 | 1564 | 0.638 | 16.24 | 8.52 |

Notes:

- The benchmark uses streaming responses and records TTFT from the first streamed content or reasoning delta.
- The synthetic 1024-word context produced about 1.56k prompt tokens.
- Decode throughput stayed near 16.2-16.5 completion tokens/sec across this small matrix.
