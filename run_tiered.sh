#!/usr/bin/env bash
# Tiered-difficulty lies sweep. Mixed_tiered = 2 each from T1/T2/T3/T4.
# Tests whether harder lies destabilize models that look stable on T1.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results

: "${HF_TOKEN:?need HF_TOKEN}"

CKPTS="${DET_CHECKPOINTS:-500,2000,8000,16000,32000}"
MODE="${DET_ANCHOR_MODE:-mixed_tiered}"

# Models in cheap-to-expensive order so an early failure costs less.
MODELS=(
  "Qwen/Qwen2.5-7B-Instruct"
  "meta-llama/Llama-3.1-8B-Instruct"
  "mistralai/Mistral-7B-Instruct-v0.3"
)

for M in "${MODELS[@]}"; do
  TAG="$(echo "$M" | tr '/' '_')_${MODE}"
  echo "=== $M ($MODE) ==="
  DET_MODEL="$M" DET_DTYPE=bfloat16 \
    DET_CHECKPOINTS="$CKPTS" DET_ATTN_IMPL=chunked_eager \
    DET_ANCHOR_MODE="$MODE" \
    HF_TOKEN="$HF_TOKEN" \
    python3 -u experiment.py 2>&1 | tee "results/${TAG}.log"
  echo "--- done $M ---"
done
echo "=== ALL DONE ==="
ls -la results/*.jsonl | tail -10
