#!/usr/bin/env bash
set -euo pipefail

source .env 2>/dev/null || true

curl -sS "http://localhost:${PORT:-8000}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${SERVED_MODEL_NAME:-nemotron-puzzle-75b-nvfp4}\",
    \"messages\": [
      {\"role\":\"user\",\"content\":\"In one short paragraph, explain what makes Nemotron Puzzle 75B interesting.\"}
    ],
    \"max_tokens\": 160,
    \"temperature\": 0.2
  }" | python3 -m json.tool
