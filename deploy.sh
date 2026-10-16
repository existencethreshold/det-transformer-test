#!/usr/bin/env bash
# Deploy the DET probe to a remote host (any SSH host, e.g. a cloud GPU pod).
# Environment:
#   DET_HOST  — IP/hostname (required)
#   DET_USER  — SSH user (default: the local user)
#   DET_PORT  — SSH port (default 22)
#   DET_PATH  — remote path
#   DET_KEY   — SSH key path (optional)
set -euo pipefail
cd "$(dirname "$0")"

TARGET_HOST="${DET_HOST:?set DET_HOST to the target host}"
TARGET_USER="${DET_USER:-$(id -un)}"
TARGET_PORT="${DET_PORT:-22}"
TARGET_PATH="${DET_PATH:-det-transformer-test}"
KEY_ARG=""
if [ -n "${DET_KEY:-}" ]; then
  KEY_ARG="-i ${DET_KEY}"
fi

SSH_CMD="ssh -p ${TARGET_PORT} ${KEY_ARG}"
RSYNC_SSH="ssh -p ${TARGET_PORT} ${KEY_ARG}"

echo "deploying to ${TARGET_USER}@${TARGET_HOST}:${TARGET_PORT} -> ${TARGET_PATH}"
${SSH_CMD} "${TARGET_USER}@${TARGET_HOST}" "mkdir -p ${TARGET_PATH}/results"
rsync -av -e "${RSYNC_SSH}" \
    --exclude='.venv' --exclude='__pycache__' --exclude='results/*.jsonl' \
    ./ "${TARGET_USER}@${TARGET_HOST}:${TARGET_PATH}/"

cat <<EOF

deployed. on remote:
  ssh -p ${TARGET_PORT} ${TARGET_USER}@${TARGET_HOST}
  cd ${TARGET_PATH}
  python experiment.py        # (on NixOS: nix-shell --run "python experiment.py")

env overrides for runs:
  DET_MODEL="Qwen/Qwen2.5-1.5B-Instruct"
  DET_DTYPE="float16"
  DET_CHECKPOINTS="500,2000,8000,16000,32000"
EOF
