#!/usr/bin/env bash
set -euo pipefail

MODEL_ID_OVERRIDE="${MODEL_ID:-}"
HF_HOME_OVERRIDE="${HF_HOME:-}"
HF_TOKEN_OVERRIDE="${HF_TOKEN:-}"
VENV_DIR_OVERRIDE="${VENV_DIR:-}"

set -a
source .env 2>/dev/null || true
set +a

[ -n "$MODEL_ID_OVERRIDE" ] && MODEL_ID="$MODEL_ID_OVERRIDE"
[ -n "$HF_HOME_OVERRIDE" ] && HF_HOME="$HF_HOME_OVERRIDE"
[ -n "$HF_TOKEN_OVERRIDE" ] && HF_TOKEN="$HF_TOKEN_OVERRIDE"
[ -n "$VENV_DIR_OVERRIDE" ] && VENV_DIR="$VENV_DIR_OVERRIDE"

MODEL_ID="${MODEL_ID:-nvidia/NVIDIA-Nemotron-Labs-3-Puzzle-75B-A9B-NVFP4}"
VENV_DIR="${VENV_DIR:-.venv}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install -U pip huggingface_hub
"$VENV_DIR/bin/hf" download "$MODEL_ID" "$@"
