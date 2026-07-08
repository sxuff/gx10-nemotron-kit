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
container_name="${VLLM_CONTAINER_NAME:-vllm-nemotron-puzzle}"

if docker ps --format '{{.Names}}' | grep -qx "$container_name"; then
  printf 'Container %s is already running. Stop it first:\n' "$container_name" >&2
  printf '  docker rm -f %s\n' "$container_name" >&2
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$container_name"; then
  docker rm "$container_name" >/dev/null
fi

vllm_args=(
  "$MODEL_ID"
  --served-model-name "${SERVED_MODEL_NAME:-nemotron-puzzle-75b-nvfp4}"
  --trust-remote-code
  --max-model-len "${MAX_MODEL_LEN:-131072}"
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.85}"
  --max-num-seqs "${MAX_NUM_SEQS:-2}"
  --reasoning-parser nemotron_v3
)

if [ -n "${API_SERVER_COUNT:-}" ]; then
  vllm_args+=(--api-server-count "$API_SERVER_COUNT")
fi

if [ -n "${SPECULATIVE_CONFIG:-}" ]; then
  vllm_args+=(--speculative-config "$SPECULATIVE_CONFIG")
elif [ -n "${MTP_K:-}" ]; then
  vllm_args+=(--speculative-config "{\"method\":\"mtp\",\"num_speculative_tokens\":${MTP_K}}")
fi

docker run --rm -it \
  --name "$container_name" \
  --ipc=host \
  --gpus all \
  -p "${PORT:-8000}:8000" \
  -e HF_TOKEN="$HF_TOKEN" \
  -v "${HF_HOME:-$HOME/.cache/huggingface}:/root/.cache/huggingface" \
  vllm/vllm-openai:cu130-nightly \
  "${vllm_args[@]}"
