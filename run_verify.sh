#!/usr/bin/env bash
# Verify-frame counter-experiment. Same probes as run_tiered.sh, but the
# anchor preamble explicitly licenses disagreement and warns that some
# claims may be inconsistent or wrong. Tests parrot-vs-derivation:
# if compliance and derivation are prompt-gated, T3+T4 lies should be
# rejected here despite being parroted in instruct-frame.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results

: "${HF_TOKEN:?need HF_TOKEN}"

CKPTS="${DET_CHECKPOINTS:-500,2000,8000,16000,32000}"
MODE="${DET_ANCHOR_MODE:-mixed_tiered}"

MODELS=(
  "Qwen/Qwen2.5-7B-Instruct"
  "meta-llama/Llama-3.1-8B-Instruct"
  "mistralai/Mistral-7B-Instruct-v0.3"
)

for M in "${MODELS[@]}"; do
  TAG="$(echo "$M" | tr '/' '_')_${MODE}_verify"
  echo "=== $M ($MODE, verify-frame) ==="
  DET_MODEL="$M" DET_DTYPE=bfloat16 \
    DET_CHECKPOINTS="$CKPTS" DET_ATTN_IMPL=chunked_eager \
    DET_ANCHOR_MODE="$MODE" \
    DET_FRAME=verify \
    HF_TOKEN="$HF_TOKEN" \
    python3 -u experiment.py 2>&1 | tee "results/${TAG}.log"
  echo "--- done $M ---"
done
echo "=== ALL DONE ==="
ls -la results/*_verify.jsonl | tail -10
