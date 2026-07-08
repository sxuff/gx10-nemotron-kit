# Nemotron Puzzle Notes

Model: `nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4`

Track these for every run:

- model revision
- vLLM image tag or digest
- launch flags
- cold start time
- TTFT
- decode tokens/sec
- memory headroom
- max stable context

Initial public angle:

- Can a single GX10 serve the new Nemotron Puzzle NVFP4 checkpoint?
- What vLLM flags are stable?
- What latency does it get at short, medium, and long context?
- What breaks, and how do we fix it cleanly?

