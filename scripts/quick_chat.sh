#!/usr/bin/env bash
set -euo pipefail

source .env 2>/dev/null || true

curl -sS "http://localhost:${PORT:-8000}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${SERVED_MODEL_NAME:-nemotron-puzzle-75b-nvfp4}\",
    \"messages\": [
      {\"role\":\"user\",\"content\":\"In one short paragraph, explain why the NVIDIA Nemotron Labs 3 Puzzle 75B A9B NVFP4 checkpoint is interesting for local inference.\"}
    ],
    \"max_tokens\": 160,
    \"temperature\": 0.2
  }" | python3 -m json.tool
