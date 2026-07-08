#!/usr/bin/env bash
set -euo pipefail

if ! docker info >/dev/null 2>&1; then
  current_user="$(id -un)"
  if getent group docker | grep -qE "(:|,)${current_user}(,|$)"; then
    printf 'Docker is available through the docker group; re-running with sg docker.\n' >&2
    printf -v quoted '%q ' "$0" "$@"
    exec sg docker -c "$quoted"
  fi

  printf 'Docker is not accessible. Reconnect SSH or add %s to the docker group.\n' "$current_user" >&2
  exit 1
fi

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
