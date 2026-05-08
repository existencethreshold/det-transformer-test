#!/usr/bin/env bash
# Frame-asymmetry control. Same probes, same models, same harness — only
# difference vs run_tiered.sh is DET_FRAME=instruct_no_repeat (drops the
# "Repeat: id = answer" line from the instruction-frame preamble).
# Discriminates the framing imperative from the answer-binding template
# in the cross-frame inversion result.
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
  TAG="$(echo "$M" | tr '/' '_')_${MODE}_instruct_no_repeat"
  echo "=== $M ($MODE, instruct_no_repeat-frame) ==="
  DET_MODEL="$M" DET_DTYPE=bfloat16 \
    DET_CHECKPOINTS="$CKPTS" DET_ATTN_IMPL=chunked_eager \
    DET_ANCHOR_MODE="$MODE" \
    DET_FRAME=instruct_no_repeat \
    HF_TOKEN="$HF_TOKEN" \
    python3 -u experiment.py 2>&1 | tee "results/${TAG}.log"
  echo "--- done $M ---"
done
echo "=== ALL DONE ==="
ls -la results/*_instruct_no_repeat.jsonl | tail -10
