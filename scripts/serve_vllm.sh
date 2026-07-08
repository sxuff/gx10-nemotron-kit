#!/usr/bin/env bash
set -euo pipefail

source .env

docker run --rm -it \
  --name vllm-nemotron-puzzle \
  --ipc=host \
  --gpus all \
  -p "${PORT:-8000}:8000" \
  -e HF_TOKEN="$HF_TOKEN" \
  -v "${HF_HOME:-$HOME/.cache/huggingface}:/root/.cache/huggingface" \
  vllm/vllm-openai:cu130-nightly \
  vllm serve "$MODEL_ID" \
    --served-model-name "${SERVED_MODEL_NAME:-nemotron-puzzle-75b-nvfp4}" \
    --trust-remote-code \
    --max-model-len 131072 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 2 \
    --reasoning-parser nemotron_v3
