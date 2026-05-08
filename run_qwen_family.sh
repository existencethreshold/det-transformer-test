#!/usr/bin/env bash
# Qwen-family replication of the §3.7 binding-template result.
# Sweeps Qwen2.5-{1.5B,3B,14B}-Instruct under all three frames on
# mixed_tiered probes at 5 checkpoints. Tests whether the Qwen-7B×T4
# binding-template-load-bearing finding is a family architectural
# property or specific to the 7B-Instruct tuning.
#
# Skipping Qwen-32B on H100 80GB — bf16 weights alone are ~64GB, the
# KV cache + chunked-attention transients push past 80GB at 32K context.
# Run 32B separately on MI300X if needed.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results

: "${HF_TOKEN:?need HF_TOKEN}"

CKPTS="${DET_CHECKPOINTS:-500,2000,8000,16000,32000}"
MODE="mixed_tiered"

MODELS=(
  "Qwen/Qwen2.5-1.5B-Instruct"
  "Qwen/Qwen2.5-3B-Instruct"
  "Qwen/Qwen2.5-14B-Instruct"
)

FRAMES=(instruct instruct_no_repeat verify)

for M in "${MODELS[@]}"; do
  for F in "${FRAMES[@]}"; do
    if [ "$F" = "instruct" ]; then
      TAG="$(echo "$M" | tr '/' '_')_${MODE}"
    else
      TAG="$(echo "$M" | tr '/' '_')_${MODE}_${F}"
    fi
    echo "=== $M ($MODE, $F frame) ==="
    DET_MODEL="$M" DET_DTYPE=bfloat16 \
      DET_CHECKPOINTS="$CKPTS" DET_ATTN_IMPL=chunked_eager \
      DET_ANCHOR_MODE="$MODE" \
      DET_FRAME="$F" \
      HF_TOKEN="$HF_TOKEN" \
      python3 -u experiment.py 2>&1 | tee "results/${TAG}.log"
    echo "--- done $M $F ---"
  done
done
echo "=== ALL DONE ==="
ls -la results/*Qwen2.5-1.5B*mixed_tiered* results/*Qwen2.5-3B*mixed_tiered* results/*Qwen2.5-14B*mixed_tiered* 2>/dev/null | tail -20
