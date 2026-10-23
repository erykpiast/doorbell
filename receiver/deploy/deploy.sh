#!/usr/bin/env bash
# Copy the receiver code to the Raspberry Pi and (re)install the service.
# Usage: deploy.sh [host]   (default: erykpiast@doorbell.local)
# Override the remote directory with DOORBELL_DIR (default: ~/doorbell).
set -euo pipefail

HOST="${1:-erykpiast@doorbell.local}"
REMOTE_DIR="${DOORBELL_DIR:-doorbell}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Copy receiver code to $HOST:$REMOTE_DIR ==="
ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
# leave out the tools that run on this computer, not on the Pi
rsync -av --delete \
  --exclude '__pycache__' --exclude 'sound_tools/' \
  --exclude 'deploy/deploy.sh' --exclude 'deploy/simulate.sh' \
  "$SRC/" "$HOST:$REMOTE_DIR/"

echo "=== Install service ==="
ssh -t "$HOST" "cd '$REMOTE_DIR' && bash deploy/install.sh"
